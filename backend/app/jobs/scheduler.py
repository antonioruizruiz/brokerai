"""Tareas programadas, dentro del propio proceso del backend (APScheduler, no un
cron de sistema): solo corren mientras `uvicorn` esté encendido. Para la Fase 8
(VPS) seguirá sirviendo igual, ya que allí el backend estará corriendo de forma
continua.

- Cada hora: refresca los valores recientes de precios
  (`actualizar_valores_recientes`), para que la vela de "hoy" no se quede
  desfasada mientras el mercado sigue abierto.
- Una vez al día (23:00 hora de Madrid, con zona horaria fija aunque el
  servidor esté en UTC): vuelve a descargar el histórico completo
  (`descargar_historial_completo`). Hace falta además de la de cada hora
  porque Yahoo Finance revisa a veces precios pasados (splits, dividendos
  ajustados) que la actualización horaria no toca al limitarse a los últimos
  días; se elige una hora después del cierre de todos los mercados que
  seguimos (IBEX 35, Dow Jones, Nasdaq-100), no solo el español."""
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.db import SessionLocal
from app.services.market_sync import (
    actualizar_valores_recientes,
    comprobar_descarga_atascada,
    descargar_historial_completo,
)

logger = logging.getLogger(__name__)

MADRID = ZoneInfo("Europe/Madrid")

scheduler = BackgroundScheduler()


def _job_actualizacion_horaria() -> None:
    try:
        resultado = actualizar_valores_recientes()
        logger.info("Actualización horaria de precios: %s", resultado)
    except Exception:
        logger.exception("Fallo en la actualización horaria de precios")


def _job_descarga_diaria() -> None:
    try:
        resultado = descargar_historial_completo()
        logger.info("Descarga diaria del histórico completo: %s", resultado)
    except Exception:
        logger.exception("Fallo en la descarga diaria del histórico completo")


def _job_vigilar_descarga() -> None:
    db = SessionLocal()
    try:
        if comprobar_descarga_atascada(db):
            logger.warning("Descarga completa liberada por falta de avance durante 5 minutos")
    except Exception:
        logger.exception("Fallo al comprobar el avance de la descarga completa")
    finally:
        db.close()


def iniciar_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            _job_actualizacion_horaria,
            "interval",
            hours=1,
            id="actualizacion_horaria",
            replace_existing=True,
        )
        scheduler.add_job(
            _job_descarga_diaria,
            CronTrigger(hour=23, minute=0, timezone=MADRID),
            id="descarga_diaria",
            replace_existing=True,
        )
        scheduler.add_job(
            _job_vigilar_descarga,
            "interval",
            minutes=1,
            id="vigilar_descarga",
            replace_existing=True,
        )
        scheduler.start()


def detener_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
