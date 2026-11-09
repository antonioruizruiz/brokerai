"""Sincronización de precios con Yahoo Finance: descarga completa y actualización
horaria incremental. Siempre con un proveedor de prueba (nunca Yahoo Finance de
verdad), y con una base de datos propia en memoria: `descargar_historial_completo`
toca el histórico de TODO el universo de empresas, así que no puede compartir la
base de datos (`db_session`) que usan el resto de tests (p. ej. `test_prices.py`,
`test_ranking_endpoint.py`), o chocaría con los precios que ellos insertan para
las mismas fechas de prueba."""
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.company import Company
from app.models.index_bar import IndexBar
from app.models.price import PriceBar
from app.models.sync_status import SyncStatus
from app.services.market_sync import actualizar_valores_recientes, descargar_historial_completo


@pytest.fixture
def db_aislada():
    """Base de datos en memoria propia de este archivo, sembrada solo con dos
    empresas de prueba (no las ~165 del universo real)."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    db.add_all(
        [
            Company(ticker="ACS.MC", name="ACS", sector="Construcción", indice="IBEX35", moneda="EUR"),
            Company(ticker="SAN.MC", name="Banco Santander", sector="Banca", indice="IBEX35", moneda="EUR"),
        ]
    )
    db.commit()
    try:
        yield db
    finally:
        db.close()


class _ProviderFijo:
    """Siempre devuelve las mismas dos velas, pase lo que pase en `start`."""

    def __init__(self, precio_cierre: float = 10.0):
        self.precio_cierre = precio_cierre

    def get_history(self, ticker, start, end=None):
        return [
            {"date": date(2024, 1, 2), "open": 10.0, "high": 10.5, "low": 9.5, "close": self.precio_cierre, "volume": 1_000},
            {
                "date": date(2024, 1, 3),
                "open": 10.2,
                "high": 10.8,
                "low": 10.0,
                "close": self.precio_cierre + 1,
                "volume": 1_200,
            },
        ]

    def get_dividends(self, ticker, start):
        return [{"date": date(2024, 1, 2), "amount": 0.5}]


def test_descarga_completa_crea_precios_indices_y_marca_estado(db_aislada):
    resultado = descargar_historial_completo(db=db_aislada, provider=_ProviderFijo(), pausa_entre_valores_segundos=0)

    assert resultado["errores"] == {}
    assert db_aislada.query(PriceBar).filter(PriceBar.ticker == "ACS.MC").count() == 2
    assert db_aislada.query(PriceBar).filter(PriceBar.ticker == "SAN.MC").count() == 2
    # 3 índices (IBEX35, DOWJONES, NASDAQ100) x 2 velas (2024-01-02 y 2024-01-03) cada uno.
    assert db_aislada.query(IndexBar).count() == 6
    assert {indice for (indice,) in db_aislada.query(IndexBar.indice).distinct()} == {
        "IBEX35",
        "DOWJONES",
        "NASDAQ100",
    }

    estado = db_aislada.query(SyncStatus).filter(SyncStatus.id == 1).first()
    assert estado is not None
    assert estado.descarga_completa_en_progreso is False
    assert estado.ultima_descarga_completa is not None


def test_actualizacion_horaria_refresca_la_vela_de_hoy_y_no_toca_empresas_sin_historico(db_aislada):
    ticker = "ACS.MC"
    db_aislada.add(PriceBar(ticker=ticker, date=date(2024, 1, 2), open=1, high=1, low=1, close=1, volume=1))
    db_aislada.commit()

    resultado = actualizar_valores_recientes(db=db_aislada, provider=_ProviderFijo(precio_cierre=99.0), pausa_entre_valores_segundos=0)

    assert resultado["errores"] == {}
    velas = db_aislada.query(PriceBar).filter(PriceBar.ticker == ticker).order_by(PriceBar.date).all()
    assert [v.date for v in velas] == [date(2024, 1, 2), date(2024, 1, 3)]
    assert velas[0].close == 99.0  # la vela que ya existía se ha reemplazado, no duplicado

    # SAN.MC no tiene histórico previo en esta base de datos: no debe generar ningún precio.
    assert db_aislada.query(PriceBar).filter(PriceBar.ticker == "SAN.MC").count() == 0

    estado = db_aislada.query(SyncStatus).filter(SyncStatus.id == 1).first()
    assert estado.ultima_actualizacion_horaria is not None


def test_empresas_inactivas_se_saltan_en_ambos_modos(db_aislada):
    san = db_aislada.query(Company).filter(Company.ticker == "SAN.MC").one()
    san.activa = False
    db_aislada.commit()

    resultado_completo = descargar_historial_completo(db=db_aislada, provider=_ProviderFijo(), pausa_entre_valores_segundos=0)
    assert "SAN.MC" not in resultado_completo["empresas"]
    assert db_aislada.query(PriceBar).filter(PriceBar.ticker == "SAN.MC").count() == 0

    # Si ya tenía histórico previo, la actualización horaria tampoco debe tocarlo.
    db_aislada.add(PriceBar(ticker="SAN.MC", date=date(2024, 1, 2), open=1, high=1, low=1, close=1, volume=1))
    db_aislada.commit()

    resultado_horaria = actualizar_valores_recientes(db=db_aislada, provider=_ProviderFijo(precio_cierre=99.0), pausa_entre_valores_segundos=0)
    assert "SAN.MC" not in resultado_horaria["errores"]
    velas_san = db_aislada.query(PriceBar).filter(PriceBar.ticker == "SAN.MC").all()
    assert len(velas_san) == 1
    assert velas_san[0].close == 1  # no se ha refrescado: sigue con el valor sembrado a mano
