"""Punto de entrada del backend. Arrancar con: uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.cartera import router as cartera_router
from app.api.companies import router as companies_router
from app.api.dividends import router as dividends_router
from app.api.fiabilidad import router as fiabilidad_router
from app.api.indices import router as indices_router
from app.api.ranking import router as ranking_router
from app.api.recommendations import router as recommendations_router
from app.api.settings import router as settings_router
from app.api.sync import router as sync_router
from app.core.db import init_db
from app.jobs.scheduler import detener_scheduler, iniciar_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    iniciar_scheduler()
    yield
    detener_scheduler()


app = FastAPI(title="Broker IBEX 35", version="0.1.0", lifespan=lifespan)

# Permite que el frontend en desarrollo (Vite, puerto 5173) llame a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cartera_router)
app.include_router(companies_router)
app.include_router(dividends_router)
app.include_router(fiabilidad_router)
app.include_router(indices_router)
app.include_router(ranking_router)
app.include_router(recommendations_router)
app.include_router(settings_router)
app.include_router(sync_router)


@app.get("/api/health")
def health():
    """Comprobación rápida de que el backend está vivo."""
    return {"status": "ok"}
