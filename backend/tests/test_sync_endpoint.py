"""Endpoints de sincronización manual (GET /api/sync/estado, POST /api/sync/
descarga-completa). La tarea en segundo plano se sustituye por un doble de
prueba: no debe llamar nunca a Yahoo Finance de verdad."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func

import app.api.sync as sync_api
from app.main import app
from app.models.sync_status import SyncStatus
from app.models.price import PriceBar

client = TestClient(app)


def _limpiar_estado(db_session) -> SyncStatus:
    estado = db_session.query(SyncStatus).filter(SyncStatus.id == 1).first()
    if estado is None:
        estado = SyncStatus(id=1)
        db_session.add(estado)
    estado.descarga_completa_en_progreso = False
    estado.descarga_id = None
    estado.descarga_ultimo_avance = None
    db_session.commit()
    return estado


def test_estado_inicial_sin_descarga_en_progreso(db_session):
    _limpiar_estado(db_session)

    r = client.get("/api/sync/estado")
    assert r.status_code == 200
    datos = r.json()
    assert datos["descarga_completa_en_progreso"] is False


def test_consultar_estado_libera_descarga_sin_avance_durante_cinco_minutos(db_session):
    estado = _limpiar_estado(db_session)
    recuento = db_session.query(func.count(PriceBar.id)).scalar() or 0
    estado.descarga_completa_en_progreso = True
    estado.descarga_id = "ejecucion-atascada"
    estado.descarga_recuento_precios = recuento
    estado.descarga_ultimo_avance = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=6)
    db_session.commit()

    r = client.get("/api/sync/estado")

    assert r.status_code == 200
    datos = r.json()
    assert datos["descarga_completa_en_progreso"] is False
    assert "5 minutos" in datos["ultimo_error"]


def test_lanzar_descarga_completa_marca_en_progreso(db_session, monkeypatch):
    _limpiar_estado(db_session)
    # Evita que la tarea en segundo plano llegue a llamar a Yahoo Finance de verdad.
    monkeypatch.setattr(sync_api, "descargar_historial_completo", lambda *a, **k: None)

    r = client.post("/api/sync/descarga-completa")
    assert r.status_code == 202


def test_segunda_descarga_mientras_hay_una_en_marcha_devuelve_409(db_session):
    estado = _limpiar_estado(db_session)
    estado.descarga_completa_en_progreso = True
    db_session.commit()

    r = client.post("/api/sync/descarga-completa")
    assert r.status_code == 409

    _limpiar_estado(db_session)


def test_desbloquear_descarga_limpia_bandera(db_session):
    estado = _limpiar_estado(db_session)
    estado.descarga_completa_en_progreso = True
    db_session.commit()

    r = client.post("/api/sync/desbloquear")

    assert r.status_code == 200
    assert db_session.query(SyncStatus).filter(SyncStatus.id == 1).one().descarga_completa_en_progreso is False


def test_desbloquear_sin_descarga_activa_devuelve_409(db_session):
    _limpiar_estado(db_session)

    r = client.post("/api/sync/desbloquear")

    assert r.status_code == 409


def test_actualizar_empresa_devuelve_resultado(monkeypatch, db_session):
    _limpiar_estado(db_session)
    monkeypatch.setattr(
        sync_api,
        "actualizar_empresa",
        lambda ticker, db: {"ticker": ticker, "precios_actualizados": 2, "dividendos_nuevos": 1},
    )

    r = client.post("/api/sync/empresa/ACS.MC/actualizar")

    assert r.status_code == 200
    assert r.json()["ticker"] == "ACS.MC"


def test_actualizar_empresa_rechaza_si_descarga_completa_activa(db_session):
    estado = _limpiar_estado(db_session)
    estado.descarga_completa_en_progreso = True
    db_session.commit()

    r = client.post("/api/sync/empresa/ACS.MC/actualizar")

    assert r.status_code == 409
    _limpiar_estado(db_session)
