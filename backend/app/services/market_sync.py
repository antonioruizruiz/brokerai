"""Sincroniza precios/dividendos con Yahoo Finance.

Dos modos, que comparten la misma lógica de guardado:
- `descargar_historial_completo`: los 10 años de histórico de todo el universo.
  Tarda varios minutos; se lanza a mano de vez en cuando (botón en Ajustes o
  `scripts/download_history.py`), nunca automáticamente.
- `actualizar_valores_recientes`: solo los últimos días de cada valor. Pensada
  para ejecutarse sola cada hora (`app/jobs/scheduler.py`) y mantener fresca la
  vela de "hoy" mientras el mercado sigue abierto.
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import Callable
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.company import Company
from app.models.dividend import Dividend
from app.models.index_bar import IndexBar
from app.models.price import PriceBar
from app.models.sync_status import SyncStatus
from app.services.market_data import MarketDataProvider, YFinanceProvider

YEARS_HISTORIAL_COMPLETO = 10
PAUSA_ENTRE_VALORES_SEGUNDOS = 1  # para no saturar a Yahoo Finance
MINUTOS_SIN_AVANCE_DESCARGA = 5

# Días hacia atrás que se vuelven a pedir en la actualización horaria: permite que
# la vela de "hoy" se refresque varias veces mientras el mercado sigue abierto, y
# corrige cierres de ayer que Yahoo Finance revise tras el cierre.
DIAS_SOLAPE_ACTUALIZACION = 5

# Ticker de Yahoo Finance del propio índice, por cada índice que seguimos (Fase 5: comparar el backtest).
TICKERS_INDICES = {"IBEX35": "^IBEX", "DOWJONES": "^DJI", "NASDAQ100": "^NDX"}


def _ahora_utc_sin_zona() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _contar_precios(db: Session) -> int:
    return db.query(func.count(PriceBar.id)).scalar() or 0


def comprobar_descarga_atascada(db: Session, ahora: datetime | None = None) -> bool:
    """Libera una descarga si no aumenta el número de velas durante cinco minutos."""
    estado = obtener_o_crear_estado(db)
    if not estado.descarga_completa_en_progreso:
        return False

    ahora = ahora or _ahora_utc_sin_zona()
    recuento = _contar_precios(db)
    if estado.descarga_ultimo_avance is None:
        estado.descarga_recuento_precios = recuento
        estado.descarga_ultimo_avance = ahora
        db.commit()
        return False

    if recuento > estado.descarga_recuento_precios:
        estado.descarga_recuento_precios = recuento
        estado.descarga_ultimo_avance = ahora
        db.commit()
        return False

    if ahora - estado.descarga_ultimo_avance < timedelta(minutes=MINUTOS_SIN_AVANCE_DESCARGA):
        return False

    estado.descarga_completa_en_progreso = False
    estado.descarga_id = None
    estado.ultimo_error = "Descarga liberada automáticamente: no aumentó el histórico durante 5 minutos."
    db.commit()
    return True


def _descarga_sigue_activa(db: Session, estado: SyncStatus, descarga_id: str) -> bool:
    db.refresh(estado)
    return estado.descarga_completa_en_progreso and estado.descarga_id == descarga_id


def _registrar_avance_descarga(db: Session, estado: SyncStatus, descarga_id: str) -> None:
    if not _descarga_sigue_activa(db, estado, descarga_id):
        return
    recuento = _contar_precios(db)
    if recuento > estado.descarga_recuento_precios:
        estado.descarga_recuento_precios = recuento
        estado.descarga_ultimo_avance = _ahora_utc_sin_zona()
        db.commit()


def obtener_o_crear_estado(db: Session) -> SyncStatus:
    estado = db.query(SyncStatus).filter(SyncStatus.id == 1).first()
    if estado is None:
        estado = SyncStatus(id=1)
        db.add(estado)
        db.commit()
        db.refresh(estado)
    return estado


def upsert_prices(db: Session, ticker: str, records: list[dict]) -> int:
    """Añade solo las velas de fechas que todavía no existen (no toca las que ya había)."""
    existentes = {d for (d,) in db.query(PriceBar.date).filter(PriceBar.ticker == ticker).all()}
    nuevos = [PriceBar(ticker=ticker, **r) for r in records if r["date"] not in existentes]
    db.add_all(nuevos)
    return len(nuevos)


def upsert_dividends(db: Session, ticker: str, records: list[dict]) -> int:
    existentes = {d for (d,) in db.query(Dividend.date).filter(Dividend.ticker == ticker).all()}
    nuevos = [Dividend(ticker=ticker, **r) for r in records if r["date"] not in existentes]
    db.add_all(nuevos)
    return len(nuevos)


def upsert_index(db: Session, indice: str, records: list[dict]) -> int:
    existentes = {d for (d,) in db.query(IndexBar.date).filter(IndexBar.indice == indice).all()}
    nuevos = [IndexBar(indice=indice, **r) for r in records if r["date"] not in existentes]
    db.add_all(nuevos)
    return len(nuevos)


def _reemplazar_precios(db: Session, ticker: str, records: list[dict], desde: date) -> int:
    """Borra las velas de `ticker` desde `desde` en adelante y mete las nuevas en su
    lugar. A diferencia de `upsert_prices` (que solo añade fechas que faltan), esto
    permite refrescar la vela de "hoy" aunque ya existiera de una pasada anterior."""
    db.query(PriceBar).filter(PriceBar.ticker == ticker, PriceBar.date >= desde).delete()
    db.add_all(PriceBar(ticker=ticker, **r) for r in records)
    return len(records)


def _reemplazar_index(db: Session, indice: str, records: list[dict], desde: date) -> int:
    db.query(IndexBar).filter(IndexBar.indice == indice, IndexBar.date >= desde).delete()
    db.add_all(IndexBar(indice=indice, **r) for r in records)
    return len(records)


def descargar_historial_completo(
    db: Session | None = None,
    provider: MarketDataProvider | None = None,
    on_progreso: Callable[[str], None] | None = None,
    pausa_entre_valores_segundos: float = PAUSA_ENTRE_VALORES_SEGUNDOS,
) -> dict:
    """Descarga los `YEARS_HISTORIAL_COMPLETO` años de histórico de precios y
    dividendos de todo el universo de empresas (IBEX 35 + Dow Jones + Nasdaq-100 +
    sueltas) y de los 3 índices de referencia. Marca `SyncStatus.descarga_completa_
    en_progreso` mientras dura, para no lanzar dos a la vez: si ya hay una en
    marcha (botón de Ajustes o la tarea diaria de `app/jobs/scheduler.py`
    coincidiendo en el tiempo), esta llamada no hace nada y vuelve al momento."""
    aviso = on_progreso or (lambda _mensaje: None)
    cerrar_db = db is None
    db = db or SessionLocal()
    provider = provider or YFinanceProvider()
    hoy = date.today()
    inicio = date(hoy.year - YEARS_HISTORIAL_COMPLETO, hoy.month, hoy.day)
    resultado: dict = {"indices": {}, "empresas": {}, "errores": {}}

    comprobar_descarga_atascada(db)
    estado = obtener_o_crear_estado(db)
    if estado.descarga_completa_en_progreso:
        aviso("Ya hay una descarga completa en marcha: se omite esta.")
        if cerrar_db:
            db.close()
        return {"omitida": True}

    descarga_id = uuid4().hex
    estado.descarga_completa_en_progreso = True
    estado.descarga_id = descarga_id
    estado.descarga_recuento_precios = _contar_precios(db)
    estado.descarga_ultimo_avance = _ahora_utc_sin_zona()
    estado.ultimo_error = None
    db.commit()

    try:
        for indice, ticker_indice in TICKERS_INDICES.items():
            if not _descarga_sigue_activa(db, estado, descarga_id):
                resultado["cancelada"] = True
                return resultado
            aviso(f"[índice] {indice} ({ticker_indice})...")
            try:
                velas = provider.get_history(ticker_indice, start=inicio)
                if not _descarga_sigue_activa(db, estado, descarga_id):
                    resultado["cancelada"] = True
                    return resultado
                resultado["indices"][indice] = upsert_index(db, indice, velas)
                db.commit()
            except Exception as exc:
                db.rollback()
                resultado["errores"][indice] = str(exc)
                aviso(f"ERROR en {indice}: {exc}")

        empresas = db.query(Company).filter(Company.activa.is_(True)).order_by(Company.ticker).all()
        for i, company in enumerate(empresas, start=1):
            if not _descarga_sigue_activa(db, estado, descarga_id):
                resultado["cancelada"] = True
                return resultado
            ticker = company.ticker
            aviso(f"[{i}/{len(empresas)}] {ticker} ({company.name})...")
            try:
                precios = provider.get_history(ticker, start=inicio)
                dividendos = provider.get_dividends(ticker, start=inicio)
            except Exception as exc:
                resultado["errores"][ticker] = str(exc)
                aviso(f"ERROR en {ticker}: {exc}")
                continue

            if not _descarga_sigue_activa(db, estado, descarga_id):
                resultado["cancelada"] = True
                return resultado

            n_precios = upsert_prices(db, ticker, precios)
            n_dividendos = upsert_dividends(db, ticker, dividendos)
            db.commit()
            _registrar_avance_descarga(db, estado, descarga_id)
            resultado["empresas"][ticker] = {"precios_nuevos": n_precios, "dividendos_nuevos": n_dividendos}

            if pausa_entre_valores_segundos:
                time.sleep(pausa_entre_valores_segundos)

        if not _descarga_sigue_activa(db, estado, descarga_id):
            resultado["cancelada"] = True
            return resultado

        estado.ultima_descarga_completa = datetime.now(timezone.utc)
        if resultado["errores"]:
            estado.ultimo_error = "; ".join(f"{k}: {v}" for k, v in resultado["errores"].items())[:500]
        db.commit()
        aviso("Descarga completada.")
    finally:
        db.rollback()
        db.refresh(estado)
        if estado.descarga_id == descarga_id:
            estado.descarga_completa_en_progreso = False
            estado.descarga_id = None
            estado.descarga_ultimo_avance = None
            db.commit()
        if cerrar_db:
            db.close()

    return resultado


def actualizar_empresa(
    ticker: str,
    db: Session | None = None,
    provider: MarketDataProvider | None = None,
) -> dict:
    """Refresca precios y dividendos de un ticker sin tocar el resto del universo."""
    cerrar_db = db is None
    db = db or SessionLocal()
    provider = provider or YFinanceProvider()

    try:
        company = db.query(Company).filter(Company.ticker == ticker).first()
        if company is None:
            raise LookupError(f"Empresa no encontrada: {ticker}")

        ultima = db.query(func.max(PriceBar.date)).filter(PriceBar.ticker == ticker).scalar()
        hoy = date.today()
        inicio = (
            ultima - timedelta(days=DIAS_SOLAPE_ACTUALIZACION)
            if ultima is not None
            else date(hoy.year - YEARS_HISTORIAL_COMPLETO, hoy.month, hoy.day)
        )

        precios = provider.get_history(ticker, start=inicio)
        dividendos = provider.get_dividends(ticker, start=inicio)

        if ultima is None:
            precios_actualizados = upsert_prices(db, ticker, precios)
        else:
            precios_actualizados = _reemplazar_precios(db, ticker, precios, inicio)
        dividendos_nuevos = upsert_dividends(db, ticker, dividendos)
        db.commit()
        return {
            "ticker": ticker,
            "precios_actualizados": precios_actualizados,
            "dividendos_nuevos": dividendos_nuevos,
            "desde": inicio.isoformat(),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        if cerrar_db:
            db.close()


def actualizar_valores_recientes(
    db: Session | None = None,
    provider: MarketDataProvider | None = None,
    pausa_entre_valores_segundos: float = PAUSA_ENTRE_VALORES_SEGUNDOS,
) -> dict:
    """Actualización ligera: para cada empresa (con histórico previo) e índice,
    solo pide a Yahoo Finance los últimos `DIAS_SOLAPE_ACTUALIZACION` días (no los
    10 años completos) y reemplaza esas velas. Pensada para ejecutarse cada hora
    (ver `app/jobs/scheduler.py`). Las empresas sin ningún histórico todavía se
    saltan: las coge la descarga completa o el alta desde "Añadir acción"."""
    cerrar_db = db is None
    db = db or SessionLocal()
    provider = provider or YFinanceProvider()
    resultado: dict = {"actualizados": 0, "errores": {}}

    try:
        for indice, ticker_indice in TICKERS_INDICES.items():
            ultima = db.query(func.max(IndexBar.date)).filter(IndexBar.indice == indice).scalar()
            if ultima is None:
                continue
            desde = ultima - timedelta(days=DIAS_SOLAPE_ACTUALIZACION)
            try:
                velas = provider.get_history(ticker_indice, start=desde)
                _reemplazar_index(db, indice, velas, desde)
                db.commit()
                resultado["actualizados"] += 1
            except Exception as exc:
                db.rollback()
                resultado["errores"][indice] = str(exc)
            if pausa_entre_valores_segundos:
                time.sleep(pausa_entre_valores_segundos)

        empresas = db.query(Company).filter(Company.activa.is_(True)).order_by(Company.ticker).all()
        for company in empresas:
            ticker = company.ticker
            ultima = db.query(func.max(PriceBar.date)).filter(PriceBar.ticker == ticker).scalar()
            if ultima is None:
                continue
            desde = ultima - timedelta(days=DIAS_SOLAPE_ACTUALIZACION)
            try:
                velas = provider.get_history(ticker, start=desde)
                _reemplazar_precios(db, ticker, velas, desde)
                db.commit()
                resultado["actualizados"] += 1
            except Exception as exc:
                db.rollback()
                resultado["errores"][ticker] = str(exc)

            if pausa_entre_valores_segundos:
                time.sleep(pausa_entre_valores_segundos)

        estado = obtener_o_crear_estado(db)
        estado.ultima_actualizacion_horaria = datetime.now(timezone.utc)
        if resultado["errores"]:
            estado.ultimo_error = "; ".join(f"{k}: {v}" for k, v in resultado["errores"].items())[:500]
        db.commit()
    finally:
        if cerrar_db:
            db.close()

    return resultado
