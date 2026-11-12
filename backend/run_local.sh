#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

database_url=$(../.venv/bin/python -c '
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy.engine import URL

password = dotenv_values(Path("../deploy/.env")).get("POSTGRES_PASSWORD")
if not password:
    raise SystemExit("Falta POSTGRES_PASSWORD en deploy/.env")

print(URL.create(
    "postgresql+psycopg",
    username="broker",
    password=password,
    host="localhost",
    port=5435,
    database="broker",
).render_as_string(hide_password=False))
')

export DATABASE_URL="$database_url"
exec ../.venv/bin/uvicorn app.main:app --reload