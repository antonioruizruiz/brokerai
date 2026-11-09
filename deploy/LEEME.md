# Despliegue (Fase 8) — VPS Ubuntu

Docker Compose con tres servicios:
- `db`: PostgreSQL 16, con sus datos en un volumen Docker (`db_data`) para que sobrevivan a `docker compose down`.
- `backend`: la API FastAPI (imagen construida desde `backend/Dockerfile`). Al arrancar aplica solas las
  migraciones y siembra los datos iniciales (`init_db()`, igual que en desarrollo), solo que contra Postgres.
- `frontend`: el frontend ya compilado (`npm run build`) servido por **Caddy**, que además hace de proxy de
  `/api/*` hacia `backend` y de servidor HTTPS (certificado automático de Let's Encrypt en cuanto le pongas un
  dominio real en `DOMAIN`).

Solo `frontend` (puertos 80/443) queda accesible desde fuera. `backend` y `db` solo son visibles dentro de la
red interna de Docker (o por túnel SSH a `127.0.0.1:8000`, para depurar con `/docs`), tal y como pide CLAUDE.md.

## Probarlo en local (sin VPS ni dominio todavía)

Hace falta Docker y el plugin `docker compose` en tu WSL (`docker --version` y `docker compose version` para
comprobar si ya los tienes instalados).

```bash
cd /mnt/d/GIT/proyectos_propios/broker/deploy
cp .env.example .env        # solo la primera vez; cambia al menos POSTGRES_PASSWORD
docker compose up --build
```

Espera a que los tres servicios digan que están listos (el backend tarda un poco la primera vez: aplica las
migraciones y siembra el universo de empresas). Luego abre `http://localhost` en el navegador: debería verse la
misma app que con `npm run dev`, pero ahora contra Postgres en vez de SQLite.

Para pararlo: `docker compose down` (los datos de Postgres se conservan). Para borrar también los datos y empezar
de cero: `docker compose down -v`.

## Cuando tengas el VPS y un dominio

1. Apunta el dominio (registro DNS tipo A) a la IP del VPS.
2. En el VPS: clona el repositorio, copia `deploy/.env.example` a `deploy/.env` y pon en `DOMAIN` el dominio real.
3. `docker compose up --build -d` (el `-d` lo deja en segundo plano). Caddy pedirá solo el certificado HTTPS la
   primera vez que alguien entre por ese dominio.
4. Pendiente todavía (no incluido en este primer paso): login de un solo usuario, tarea diaria automática tras el
   cierre del mercado, y copia de seguridad periódica de la base de datos.
