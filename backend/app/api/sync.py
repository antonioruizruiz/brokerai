"""Sincronización manual de precios con Yahoo Finance: lanzar una descarga
completa del histórico (tarda varios minutos, se ejecuta en segundo plano) y
consultar el estado (si hay una en marcha, cuándo fue la última, si hubo errores)."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import SyncEstadoOut
from app.core.db import get_db
from app.services.market_sync import descargar_historial_completo, obtener_o_crear_estado

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.get("/estado", response_model=SyncEstadoOut)
def get_estado(db: Session = Depends(get_db)):
    """Si hay una descarga completa en marcha y cuándo fue la última actualización
    (completa y horaria), para mostrarlo en la página Ajustes."""
    return obtener_o_crear_estado(db)


@router.post("/descarga-completa", status_code=202)
def lanzar_descarga_completa(tareas: BackgroundTasks, db: Session = Depends(get_db)):
    """Lanza en segundo plano la descarga de los 10 años de histórico completo. Si
    ya hay una en marcha, no lanza otra (409)."""
    estado = obtener_o_crear_estado(db)
    if estado.descarga_completa_en_progreso:
        raise HTTPException(status_code=409, detail="Ya hay una descarga completa en marcha")

    tareas.add_task(descargar_historial_completo)
    return {"detail": "Descarga completa iniciada"}
