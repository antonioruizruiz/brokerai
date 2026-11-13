from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import CarteraOut, PortfolioEntryIn, PortfolioEntryOut
from app.core.db import get_db
from app.models.company import Company
from app.models.dividend import Dividend
from app.models.portfolio_entry import PortfolioEntry
from app.models.price import PriceBar
from app.services.dividends import resumen_dividendos
from app.services.portfolio import calcular_posicion, evaluar_aviso

router = APIRouter(prefix="/api", tags=["cartera"])


def _ultimo_precio(db: Session, ticker: str) -> PriceBar | None:
    return db.query(PriceBar).filter(PriceBar.ticker == ticker).order_by(PriceBar.date.desc()).first()


def _entrada_a_salida(db: Session, entrada: PortfolioEntry, company: Company) -> dict:
    ultimo_bar = _ultimo_precio(db, entrada.ticker)
    precio_actual = ultimo_bar.close if ultimo_bar else None
    calculo = calcular_posicion(entrada.precio_compra, entrada.cantidad, precio_actual)

    fecha_estimada_proximo = None
    if entrada.tipo == "dividendos":
        dividendos = (
            db.query(Dividend).filter(Dividend.ticker == entrada.ticker).order_by(Dividend.date.desc()).all()
        )
        fecha_estimada_proximo = resumen_dividendos(dividendos, precio_actual)["fecha_estimada_proximo"]

    aviso = evaluar_aviso(entrada.tipo, calculo["ganancia_perdida_pct"], fecha_estimada_proximo)

    return {
        "id": entrada.id,
        "ticker": entrada.ticker,
        "name": company.name,
        "fecha_compra": entrada.fecha_compra,
        "precio_compra": entrada.precio_compra,
        "cantidad": entrada.cantidad,
        "tipo": entrada.tipo,
        "notas": entrada.notas,
        "aviso": aviso,
        "fecha_precio_actual": ultimo_bar.date if ultimo_bar else None,
        **calculo,
    }


@router.get("/cartera", response_model=CarteraOut)
def get_cartera(db: Session = Depends(get_db)):
    entradas = db.query(PortfolioEntry).order_by(PortfolioEntry.fecha_compra.desc()).all()
    companies = {c.ticker: c for c in db.query(Company).all()}

    posiciones = [_entrada_a_salida(db, e, companies[e.ticker]) for e in entradas]

    valor_invertido = sum(p["precio_compra"] * p["cantidad"] for p in posiciones)
    con_precio = [p for p in posiciones if p["valor_actual_euros"] is not None]
    valor_actual = sum(p["valor_actual_euros"] for p in con_precio) if con_precio else None
    ganancia_perdida_euros = (valor_actual - sum(p["precio_compra"] * p["cantidad"] for p in con_precio)) if con_precio else None
    ganancia_perdida_pct = (
        ganancia_perdida_euros / sum(p["precio_compra"] * p["cantidad"] for p in con_precio) * 100
        if con_precio and sum(p["precio_compra"] * p["cantidad"] for p in con_precio)
        else None
    )

    return {
        "posiciones": posiciones,
        "resumen": {
            "valor_invertido_euros": round(valor_invertido, 2),
            "valor_actual_euros": round(valor_actual, 2) if valor_actual is not None else None,
            "ganancia_perdida_euros": round(ganancia_perdida_euros, 2) if ganancia_perdida_euros is not None else None,
            "ganancia_perdida_pct": round(ganancia_perdida_pct, 2) if ganancia_perdida_pct is not None else None,
        },
    }


@router.post("/cartera", response_model=PortfolioEntryOut)
def crear_posicion(datos: PortfolioEntryIn, db: Session = Depends(get_db)):
    company = db.get(Company, datos.ticker)
    if company is None:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    entrada = PortfolioEntry(**datos.model_dump())
    db.add(entrada)
    db.commit()
    db.refresh(entrada)
    return _entrada_a_salida(db, entrada, company)


@router.delete("/cartera/{entrada_id}", status_code=204)
def borrar_posicion(entrada_id: int, db: Session = Depends(get_db)):
    entrada = db.get(PortfolioEntry, entrada_id)
    if entrada is None:
        raise HTTPException(status_code=404, detail="Posición no encontrada")
    db.delete(entrada)
    db.commit()
