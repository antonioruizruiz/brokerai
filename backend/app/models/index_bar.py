from datetime import date

from sqlalchemy import BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IndexBar(Base):
    """Vela diaria de un índice (IBEX 35, Dow Jones o Nasdaq-100; `indice` guarda
    cuál es, con los mismos valores que `Company.indice`: "IBEX35", "DOWJONES",
    "NASDAQ100").

    Se guarda aparte de `PriceBar` (que es por empresa) porque un índice no es una
    empresa y así evitamos tocar la clave foránea de `companies`. Se usa para
    comparar el resultado del backtest (Fase 5) con "haberse quedado quieto en el
    índice" de cada empresa filtrada.
    """

    __tablename__ = "index_bars"
    __table_args__ = (UniqueConstraint("indice", "date", name="uq_index_bar_indice_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    indice: Mapped[str]
    date: Mapped[date]
    open: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    close: Mapped[float]
    volume: Mapped[int] = mapped_column(BigInteger)
