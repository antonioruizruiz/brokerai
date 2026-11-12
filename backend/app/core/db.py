"""Conexión a la base de datos (SQLite en desarrollo, Postgres en producción)."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependencia de FastAPI: abre una sesión de BD y la cierra al terminar la petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def _run_migrations() -> None:
    """Aplica las migraciones pendientes de `backend/alembic/versions/`."""
    cfg = _alembic_config()
    command.upgrade(cfg, "head")


def init_db() -> None:
    """Aplica las migraciones pendientes y siembra las empresas y ajustes de trading
    que falten. Es incremental (no exige la tabla vacía) para que, al ampliar el
    universo de empresas (p. ej. añadir el Dow Jones), no haga falta borrar la base
    de datos: las empresas nuevas se añaden solas y las que ya existían no se tocan."""
    if settings.database_url.startswith("sqlite:///./"):
        Path(settings.database_url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)

    if not inspect(engine).get_table_names():
        from app.models import Base

        Base.metadata.create_all(bind=engine)
        command.stamp(_alembic_config(), "head")
    else:
        _run_migrations()

    _seed_companies_que_falten()
    _seed_trading_settings_if_empty()
    _seed_sync_status_if_empty()


def _seed_companies_que_falten() -> None:
    from app.data.universo import universo_completo
    from app.models.company import Company

    db = SessionLocal()
    try:
        existentes = {t for (t,) in db.query(Company.ticker).all()}
        nuevas = [Company(**c) for c in universo_completo() if c["ticker"] not in existentes]
        if nuevas:
            db.add_all(nuevas)
            db.commit()
    finally:
        db.close()


def _seed_trading_settings_if_empty() -> None:
    from app.models.trading_settings import TradingSettings

    db = SessionLocal()
    try:
        if db.query(TradingSettings).count() == 0:
            db.add(TradingSettings(id=1))
            db.commit()
    finally:
        db.close()


def _seed_sync_status_if_empty() -> None:
    from app.models.sync_status import SyncStatus

    db = SessionLocal()
    try:
        if db.query(SyncStatus).count() == 0:
            db.add(SyncStatus(id=1))
            db.commit()
    finally:
        db.close()
