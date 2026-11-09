#!/usr/bin/env bash
# Copia de seguridad de la base de datos Postgres (servicio "db" de docker-compose).
# Guarda un volcado comprimido en deploy/backups/ y borra los de más de 14 días.
# Pensado para lanzarse solo, por cron, en el VPS (ver deploy/LEEME.md).
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p backups
fecha="$(date +%Y%m%d_%H%M%S)"
archivo="backups/broker_${fecha}.sql.gz"

docker compose exec -T db pg_dump -U broker broker | gzip > "$archivo"
echo "Copia guardada en $archivo"

find backups -name 'broker_*.sql.gz' -mtime +14 -delete
