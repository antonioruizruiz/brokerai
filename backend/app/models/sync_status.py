from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SyncStatus(Base):
    """Estado de la sincronización de precios con Yahoo Finance. Fila única (id=1),
    igual que `TradingSettings`.

    `descarga_completa_en_progreso` evita lanzar dos descargas completas a la vez
    (tarda varios minutos, ver `app/services/market_sync.py`). `ultima_actualizacion_
    horaria` la actualiza el job de APScheduler cada hora (`app/jobs/scheduler.py`).
    """

    __tablename__ = "sync_status"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    descarga_completa_en_progreso: Mapped[bool] = mapped_column(default=False)
    descarga_id: Mapped[Optional[str]] = mapped_column(default=None)
    descarga_recuento_precios: Mapped[int] = mapped_column(default=0)
    descarga_ultimo_avance: Mapped[Optional[datetime]] = mapped_column(default=None)
    ultima_descarga_completa: Mapped[Optional[datetime]] = mapped_column(default=None)
    ultima_actualizacion_horaria: Mapped[Optional[datetime]] = mapped_column(default=None)
    ultimo_error: Mapped[Optional[str]] = mapped_column(default=None)
