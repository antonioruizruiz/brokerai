from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.filters import filtrar_por_indice
from app.api.schemas import CompanyActivaIn, CompanyCreateIn, CompanyOut, NewsItemOut, PriceBarOut
from app.core.db import get_db
from app.models.company import Company
from app.models.price import PriceBar
from app.services.company_management import TickerSinDatosError, agregar_empresa_suelta, borrar_empresa_suelta
from app.services.news import get_company_news

router = APIRouter(prefix="/api", tags=["companies"])


def _company_out(db: Session, company: Company) -> dict:
    ultimas = (
        db.query(PriceBar)
        .filter(PriceBar.ticker == company.ticker)
        .order_by(PriceBar.date.desc())
        .limit(2)
        .all()
    )
    last_price = ultimas[0].close if ultimas else None
    last_price_date = ultimas[0].date if ultimas else None
    change_pct = None
    if len(ultimas) == 2 and ultimas[1].close:
        change_pct = (ultimas[0].close - ultimas[1].close) / ultimas[1].close * 100

    return {
        "ticker": company.ticker,
        "name": company.name,
        "sector": company.sector,
        "indice": company.indice,
        "moneda": company.moneda,
        "activa": company.activa,
        "last_price": last_price,
        "change_pct": change_pct,
        "last_price_date": last_price_date,
    }


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(indice: str | None = None, db: Session = Depends(get_db)):
    """Lista de empresas (IBEX 35, Dow Jones, Nasdaq-100 o sueltas, según `indice`),
    con su último precio y variación diaria. Sin `indice`, devuelve todo el universo."""
    companies = filtrar_por_indice(db.query(Company), indice).order_by(Company.ticker).all()
    return [_company_out(db, company) for company in companies]


@router.post("/companies", response_model=CompanyOut, status_code=201)
def crear_empresa_suelta(datos: CompanyCreateIn, db: Session = Depends(get_db)):
    """Añade una acción suelta (sin índice) para hacerle seguimiento: la crea y
    descarga de inmediato su histórico de precios/dividendos desde Yahoo Finance."""
    ticker = datos.ticker.strip().upper()
    if db.get(Company, ticker):
        raise HTTPException(status_code=409, detail="Ya existe una empresa con ese ticker")

    try:
        agregar_empresa_suelta(db, ticker, datos.name.strip(), datos.sector.strip(), datos.moneda.strip().upper())
    except TickerSinDatosError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _company_out(db, db.get(Company, ticker))


@router.get("/companies/{ticker}", response_model=CompanyOut)
def get_company(ticker: str, db: Session = Depends(get_db)):
    """Ficha de una empresa (con su último precio y variación), para la página de detalle."""
    company = db.get(Company, ticker)
    if company is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return _company_out(db, company)


@router.patch("/companies/{ticker}", response_model=CompanyOut)
def actualizar_activa(ticker: str, datos: CompanyActivaIn, db: Session = Depends(get_db)):
    """Marca una empresa como activa/inactiva (p. ej. tras una fusión o exclusión de
    bolsa). Vale para cualquier empresa, de índice o suelta: a diferencia de borrarla,
    conserva todo su histórico (Cartera, Fiabilidad) y solo evita que la sincronización
    de precios (`app/services/market_sync.py`) siga intentando descargarle datos nuevos."""
    company = db.get(Company, ticker)
    if company is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    company.activa = datos.activa
    db.commit()
    db.refresh(company)
    return _company_out(db, company)


@router.delete("/companies/{ticker}", status_code=204)
def borrar_empresa_suelta_endpoint(ticker: str, db: Session = Depends(get_db)):
    """Quita una acción suelta y su histórico. Las empresas de un índice (IBEX 35,
    Dow Jones, Nasdaq-100) no se pueden borrar aquí: se gestionan en `app/data/`."""
    company = db.get(Company, ticker)
    if company is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.indice is not None:
        raise HTTPException(status_code=400, detail="Solo se pueden borrar acciones sueltas (sin índice)")
    borrar_empresa_suelta(db, company)


@router.get("/companies/{ticker}/prices", response_model=list[PriceBarOut])
def get_company_prices(ticker: str, desde: date | None = None, db: Session = Depends(get_db)):
    """Histórico diario (OHLCV) de una empresa, opcionalmente desde una fecha."""
    query = db.query(PriceBar).filter(PriceBar.ticker == ticker)
    if desde is not None:
        query = query.filter(PriceBar.date >= desde)
    return query.order_by(PriceBar.date).all()


@router.get("/companies/{ticker}/news", response_model=list[NewsItemOut])
def get_company_news_endpoint(ticker: str, db: Session = Depends(get_db)):
    """Últimas noticias de prensa relacionadas con la empresa (vía Google News).

    Son titulares de prensa, no hechos verificados: sirven de contexto rápido
    sobre qué pudo mover la cotización, no como fuente única de decisión.
    """
    company = db.query(Company).filter(Company.ticker == ticker).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return get_company_news(company.name, max_items=3)
