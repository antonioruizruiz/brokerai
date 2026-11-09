from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Company(Base):
    """Una empresa. Puede pertenecer a un índice (`"IBEX35"`, `"DOWJONES"`,
    `"NASDAQ100"`) o a ninguno (acción suelta, `indice=None`). `moneda` es la
    moneda original de cotización (sin convertir: "EUR", "USD", "CHF"...).

    `activa=False` marca una empresa que ya no cotiza de forma independiente
    (fusión, exclusión de bolsa...): sigue apareciendo en Mercado/Ranking/Hoy/
    Dividendos (con su histórico, para Cartera y Fiabilidad), pero la
    sincronización de precios (`app/services/market_sync.py`) deja de intentar
    descargarle datos nuevos de Yahoo Finance."""

    __tablename__ = "companies"

    ticker: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    sector: Mapped[str]
    indice: Mapped[Optional[str]] = mapped_column(default=None)
    moneda: Mapped[str] = mapped_column(default="EUR")
    activa: Mapped[bool] = mapped_column(default=True)
