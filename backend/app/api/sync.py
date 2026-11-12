"""Sincronización manual de precios con Yahoo Finance: lanzar una descarga
completa del histórico (tarda varios minutos, se ejecuta en segundo plano) y
consultar el estado (si hay una en marcha, cuándo fue la última, si hubo errores)."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import SyncEstadoOut
from app.core.db import get_db
from app.services.market_sync import (
    actualizar_empresa,
    comprobar_descarga_atascada,
    descargar_historial_completo,
    obtener_o_crear_estado,
)

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.get("/estado", response_model=SyncEstadoOut)
def get_estado(db: Session = Depends(get_db)):
    """Si hay una descarga completa en marcha y cuándo fue la última actualización
    (completa y horaria), para mostrarlo en la página Ajustes."""
    comprobar_descarga_atascada(db)
    return obtener_o_crear_estado(db)


@router.post("/descarga-completa", status_code=202)
def lanzar_descarga_completa(tareas: BackgroundTasks, db: Session = Depends(get_db)):
    """Lanza en segundo plano la descarga de los 10 años de histórico completo. Si
    ya hay una en marcha, no lanza otra (409)."""
    comprobar_descarga_atascada(db)
    estado = obtener_o_crear_estado(db)
    if estado.descarga_completa_en_progreso:
        raise HTTPException(status_code=409, detail="Ya hay una descarga completa en marcha")

    tareas.add_task(descargar_historial_completo)
    return {"detail": "Descarga completa iniciada"}


@router.post("/desbloquear")
def desbloquear_descarga(db: Session = Depends(get_db)):
    """Libera la bandera persistida después de confirmar que la tarea ya se detuvo."""
    estado = obtener_o_crear_estado(db)
    if not estado.descarga_completa_en_progreso:
        raise HTTPException(status_code=409, detail="No hay ninguna descarga bloqueada")

    estado.descarga_completa_en_progreso = False
    estado.descarga_id = None
    estado.descarga_ultimo_avance = None
    db.commit()
    return {"detail": "Bloqueo de descarga liberado"}


@router.post("/empresa/{ticker}/actualizar")
def actualizar_una_empresa(ticker: str, db: Session = Depends(get_db)):
    """Refresca solo precios y dividendos de una empresa."""
    comprobar_descarga_atascada(db)
    estado = obtener_o_crear_estado(db)
    if estado.descarga_completa_en_progreso:
        raise HTTPException(
            status_code=409,
            detail="No se puede actualizar una empresa mientras se descarga el histórico completo",
        )

    try:
        return actualizar_empresa(ticker, db=db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudieron descargar datos de {ticker}") from exc
