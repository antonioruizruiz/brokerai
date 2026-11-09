import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.filters import filtrar_por_indice
from app.api.schemas import RankingItemOut
from app.core.db import get_db
from app.models.company import Company
from app.models.price import PriceBar
from app.services.scoring import build_ranking, raw_indicators_from_prices

router = APIRouter(prefix="/api", tags=["ranking"])

CAMPOS_RAW_VACIOS = {
    "momentum_raw": None,
    "tendencia_raw": None,
    "volatilidad_raw": None,
    "distancia_maximo_52_semanas_pct": None,
    "volumen_relativo": None,
    "precio_actual": None,
    "sma50": None,
    "sma200": None,
    "maximo_52_semanas": None,
    "minimo_10_sesiones": None,
    "volumen_actual": None,
    "volumen_medio_20d": None,
}


def cargar_precios(db: Session, ticker: str) -> pd.DataFrame:
    """Histórico (date/close/high/low/volume) de una empresa, ordenado por fecha ascendente."""
    bars = db.query(PriceBar).filter(PriceBar.ticker == ticker).order_by(PriceBar.date).all()
    return pd.DataFrame(
        [{"date": b.date, "close": b.close, "high": b.high, "low": b.low, "volume": b.volume} for b in bars]
    )


def compute_ranking(db: Session, indice: str | None = None) -> list[dict]:
    """Factores 0-100 (momentum, tendencia, estabilidad, fuerza del sector) de cada
    empresa, comparados entre sí. Cada registro también lleva los valores "en crudo"
    (precio, medias, mínimos/máximos...) que usa el servicio de recomendaciones (Fase 4).

    Si se filtra por `indice`, los percentiles y `fuerza_sector` se calculan solo
    frente a esa cesta; si no se filtra, se calculan frente a TODO el universo
    (empresas de distinto tamaño/mercado mezcladas): es una comparación informativa,
    no estrictamente homogénea.
    """
    companies = filtrar_por_indice(db.query(Company), indice).order_by(Company.ticker).all()

    filas = []
    for company in companies:
        df = cargar_precios(db, company.ticker)
        raw = raw_indicators_from_prices(df)

        fila = {
            "ticker": company.ticker,
            "name": company.name,
            "sector": company.sector,
            "indice": company.indice,
            "moneda": company.moneda,
            "activa": company.activa,
        }
        fila.update(raw if raw is not None else CAMPOS_RAW_VACIOS)
        filas.append(fila)

    return build_ranking(filas)


@router.get("/ranking", response_model=list[RankingItemOut])
def get_ranking(indice: str | None = None, db: Session = Depends(get_db)):
    ranking = compute_ranking(db, indice)
    ranking.sort(key=lambda fila: (fila["score_global"] is None, -(fila["score_global"] or 0)))
    return ranking
