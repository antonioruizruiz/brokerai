"""Tarea programada: cada hora, refresca los valores recientes de precios
(`app.services.market_sync.actualizar_valores_recientes`).

Corre dentro del propio proceso del backend (APScheduler), no es un cron de
sistema: solo descarga mientras `uvicorn` esté encendido. Para la Fase 8 (VPS)
seguirá sirviendo igual, ya que allí el backend estará corriendo de forma
continua."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.market_sync import actualizar_valores_recientes

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _job_actualizacion_horaria() -> None:
    try:
        resultado = actualizar_valores_recientes()
        logger.info("Actualización horaria de precios: %s", resultado)
    except Exception:
        logger.exception("Fallo en la actualización horaria de precios")


def iniciar_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            _job_actualizacion_horaria,
            "interval",
            hours=1,
            id="actualizacion_horaria",
            replace_existing=True,
        )
        scheduler.start()


def detener_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
