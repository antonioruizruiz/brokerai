from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.filters import filtrar_por_indice
from app.api.ranking import cargar_precios, compute_ranking
from app.api.schemas import RecomendacionesOut
from app.api.settings import get_or_create_settings
from app.core.db import get_db
from app.models.company import Company
from app.services.recommendations import generar_recomendacion

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recomendaciones", response_model=RecomendacionesOut)
def get_recomendaciones(indice: str | None = None, db: Session = Depends(get_db)):
    """Recomendaciones de hoy: reglas de entrada (ruptura de máximos con volumen,
    retroceso en tendencia alcista) con su plan de orden límite/stop/objetivo/plazo,
    tamaño de posición según el capital y riesgo de Ajustes, y clasificación de riesgo.

    No consulta la IA de Claude (eso es la Fase 6): es un filtro cuantitativo mecánico,
    igual que el Ranking.
    """
    ajustes = get_or_create_settings(db)
    estabilidad_por_ticker = {fila["ticker"]: fila["estabilidad"] for fila in compute_ranking(db, indice)}

    recomendaciones = []
    vigilancia = []
    companies = filtrar_por_indice(db.query(Company), indice).order_by(Company.ticker).all()
    for company in companies:
        df = cargar_precios(db, company.ticker)
        resultado = generar_recomendacion(df, estabilidad_por_ticker.get(company.ticker), ajustes)
        if resultado is None:
            continue

        fila = {
            "ticker": company.ticker,
            "name": company.name,
            "sector": company.sector,
            "indice": company.indice,
            "moneda": company.moneda,
            "activa": company.activa,
            **resultado,
        }
        if fila.pop("vigilancia", False):
            vigilancia.append(fila)
        else:
            recomendaciones.append(fila)

    recomendaciones.sort(key=lambda fila: fila["beneficio_riesgo_neto"] or 0, reverse=True)
    return {"recomendaciones": recomendaciones, "vigilancia": vigilancia}
