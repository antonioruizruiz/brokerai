from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.filters import filtrar_por_indice
from app.api.schemas import DividendoResumenOut
from app.core.db import get_db
from app.models.company import Company
from app.models.dividend import Dividend
from app.models.price import PriceBar
from app.services.dividends import resumen_dividendos

router = APIRouter(prefix="/api", tags=["dividends"])


@router.get("/dividendos", response_model=list[DividendoResumenOut])
def get_dividendos(indice: str | None = None, db: Session = Depends(get_db)):
    """Rentabilidad por dividendo, historial reciente y fecha estimada del próximo
    pago de cada empresa (filtrable por índice), a partir de los dividendos ya descargados."""
    resultado = []
    companies = filtrar_por_indice(db.query(Company), indice).order_by(Company.ticker).all()
    for company in companies:
        dividendos = (
            db.query(Dividend).filter(Dividend.ticker == company.ticker).order_by(Dividend.date.desc()).all()
        )
        ultimo_precio = (
            db.query(PriceBar).filter(PriceBar.ticker == company.ticker).order_by(PriceBar.date.desc()).first()
        )
        last_price = ultimo_precio.close if ultimo_precio else None

        resultado.append(
            {
                "ticker": company.ticker,
                "name": company.name,
                "sector": company.sector,
                "indice": company.indice,
                "moneda": company.moneda,
                "activa": company.activa,
                "last_price": last_price,
                **resumen_dividendos(dividendos, last_price),
            }
        )

    resultado.sort(key=lambda r: (r["rentabilidad_pct"] is None, -(r["rentabilidad_pct"] or 0)))
    return resultado
