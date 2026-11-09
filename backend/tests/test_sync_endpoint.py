"""Endpoints de sincronización manual (GET /api/sync/estado, POST /api/sync/
descarga-completa). La tarea en segundo plano se sustituye por un doble de
prueba: no debe llamar nunca a Yahoo Finance de verdad."""
from fastapi.testclient import TestClient

import app.api.sync as sync_api
from app.main import app
from app.models.sync_status import SyncStatus

client = TestClient(app)


def _limpiar_estado(db_session) -> SyncStatus:
    estado = db_session.query(SyncStatus).filter(SyncStatus.id == 1).first()
    if estado is None:
        estado = SyncStatus(id=1)
        db_session.add(estado)
    estado.descarga_completa_en_progreso = False
    db_session.commit()
    return estado


def test_estado_inicial_sin_descarga_en_progreso(db_session):
    _limpiar_estado(db_session)

    r = client.get("/api/sync/estado")
    assert r.status_code == 200
    datos = r.json()
    assert datos["descarga_completa_en_progreso"] is False


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
