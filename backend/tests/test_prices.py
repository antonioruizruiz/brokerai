from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.models.price import PriceBar

client = TestClient(app)


def test_prices_empty_for_unknown_ticker():
    r = client.get("/api/companies/XXX.MC/prices")
    assert r.status_code == 200
    assert r.json() == []


def test_prices_returns_data(db_session):
    db_session.add(
        PriceBar(ticker="BBVA.MC", date=date(2024, 1, 2), open=9.0, high=9.5, low=8.8, close=9.2, volume=1_000_000)
    )
    db_session.commit()

    r = client.get("/api/companies/BBVA.MC/prices")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["close"] == 9.2


def test_prices_acepta_volumen_superior_a_entero_32_bits(db_session):
    volumen = 2_175_344_000
    db_session.add(
        PriceBar(ticker="NVDA", date=date(2024, 1, 2), open=1, high=1, low=1, close=1, volume=volumen)
    )
    db_session.commit()

    r = client.get("/api/companies/NVDA/prices")

    assert r.status_code == 200
    assert r.json()[0]["volume"] == volumen


def test_prices_filtra_por_desde(db_session):
    db_session.add_all(
        [
            PriceBar(ticker="ITX.MC", date=date(2024, 1, 2), open=1, high=1, low=1, close=1, volume=1),
            PriceBar(ticker="ITX.MC", date=date(2024, 6, 1), open=2, high=2, low=2, close=2, volume=2),
        ]
    )
    db_session.commit()

    r = client.get("/api/companies/ITX.MC/prices", params={"desde": "2024-03-01"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["date"] == "2024-06-01"
