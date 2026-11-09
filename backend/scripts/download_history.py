"""Descarga 10 años de histórico diario y dividendos de todo el universo de empresas
(IBEX 35 + Dow Jones + Nasdaq-100 + acciones sueltas, incluidas las añadidas a mano
desde la página "Añadir acción") y de los 3 índices de referencia, guardándolo en la
base de datos. Es un proceso que solo hace falta lanzar de vez en cuando (no en cada
arranque del servidor); tarda varios minutos.

También se puede lanzar desde la web (botón en Ajustes, `POST /api/sync/descarga-
completa`): ambos caminos comparten la misma lógica en `app/services/market_sync.py`.

Uso (desde backend/, con el entorno virtual activado):
    python scripts/download_history.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.db import init_db  # noqa: E402
from app.services.market_sync import descargar_historial_completo  # noqa: E402


def main() -> None:
    init_db()
    descargar_historial_completo(on_progreso=print)


if __name__ == "__main__":
    main()
