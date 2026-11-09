"""Ficha individual de empresa (GET /api/companies/{ticker}) y marcarla como
activa/inactiva (PATCH /api/companies/{ticker})."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_company_devuelve_la_ficha(db_session):
    r = client.get("/api/companies/ACS.MC")
    assert r.status_code == 200
    datos = r.json()
    assert datos["ticker"] == "ACS.MC"
    assert datos["activa"] is True


def test_get_company_inexistente_404(db_session):
    r = client.get("/api/companies/NOEXISTE.XX")
    assert r.status_code == 404


def test_desactivar_y_reactivar_empresa_de_indice(db_session):
    r = client.patch("/api/companies/ACS.MC", json={"activa": False})
    assert r.status_code == 200
    assert r.json()["activa"] is False

    r_listado = client.get("/api/companies?indice=IBEX35")
    ficha = next(c for c in r_listado.json() if c["ticker"] == "ACS.MC")
    assert ficha["activa"] is False

    r_reactivar = client.patch("/api/companies/ACS.MC", json={"activa": True})
    assert r_reactivar.status_code == 200
    assert r_reactivar.json()["activa"] is True


def test_patch_activa_empresa_inexistente_404(db_session):
    r = client.patch("/api/companies/NOEXISTE.XX", json={"activa": False})
    assert r.status_code == 404
