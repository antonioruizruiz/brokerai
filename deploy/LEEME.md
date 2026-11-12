# Despliegue (Fase 8) — VPS Ubuntu

Docker Compose con tres servicios:
- `db`: PostgreSQL 16, con sus datos en un volumen Docker (`db_data`) para que sobrevivan a `docker compose down`.
- `backend`: la API FastAPI (imagen construida desde `backend/Dockerfile`). Al arrancar aplica solas las
  migraciones y siembra los datos iniciales (`init_db()`, igual que en desarrollo), solo que contra Postgres.
- `frontend`: el frontend ya compilado (`npm run build`) servido por **Caddy**, que además hace de proxy de
  `/api/*` hacia `backend` y de servidor HTTPS (certificado automático de Let's Encrypt en cuanto le pongas un
  dominio real en `DOMAIN`).

Solo `frontend` (puertos 80/443) queda accesible desde fuera. `backend` (8000) y `db` (puerto local 5435) se
publican exclusivamente en `127.0.0.1`, por lo que no quedan accesibles desde otros equipos. Se usa 5435 para
no interferir con posibles instalaciones locales que ya ocupen el 5432. Dentro de Docker el backend sigue
conectando a `db:5432`; desde el backend ejecutado localmente, el lanzador usa `localhost:5435`.

## Desarrollo local con Postgres en Docker

Este modo ejecuta solo Postgres en Docker y arranca el backend y el frontend con sus comandos de desarrollo.
No levantes a la vez los servicios `backend` y `frontend` del Compose: ocuparían los mismos puertos locales.

Prepara `deploy/.env` y establece `POSTGRES_PASSWORD`. Si ya existe el volumen `db_data`, conserva la contraseña
con la que se creó; cambiarla en el archivo no cambia la contraseña dentro de una base ya inicializada. No hace
falta configurar el hash de acceso si solo vas a iniciar `db`.

```bash
cd /mnt/d/GIT/proyectos_propios/broker/deploy
cp .env.example .env        # solo la primera vez
docker compose up -d db
```

Arranca el backend desde `backend/`. El lanzador toma la contraseña de `deploy/.env`, la codifica para la URL y
fuerza la conexión a `localhost:5435` aunque la terminal tenga otra variable `DATABASE_URL`:

```bash
cd /mnt/d/GIT/proyectos_propios/broker/backend
bash run_local.sh
```

En otra terminal, prepara `frontend/.env` desde su ejemplo (ya apunta a `http://localhost:8000`) y arranca Vite:

```bash
cd /mnt/d/GIT/proyectos_propios/broker/frontend
cp .env.example .env        # solo la primera vez
npm run dev
```

Abre `http://localhost:5173`. Para detener Postgres sin borrar sus datos: `docker compose stop db`. Los datos
siguen guardados en el volumen `db_data`.

## Probarlo en local (sin VPS ni dominio todavía)

Hace falta Docker y el plugin `docker compose` en tu WSL (`docker --version` y `docker compose version` para
comprobar si ya los tienes instalados).

```bash
cd /mnt/d/GIT/proyectos_propios/broker/deploy
cp .env.example .env        # solo la primera vez
```

Antes de arrancar, genera el hash de tu contraseña de acceso (usuario único) y ponlo en `deploy/.env`
(`BASIC_AUTH_USER` y `BASIC_AUTH_HASH`), junto con `POSTGRES_PASSWORD`:

```bash
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'tu-contraseña'
```

Copia el resultado (empieza por `$2a$` o parecido) tal cual en `BASIC_AUTH_HASH`. Luego:

```bash
docker compose up --build
```

Espera a que los tres servicios digan que están listos (el backend tarda un poco la primera vez: aplica las
migraciones y siembra el universo de empresas). Abre `http://localhost`: el navegador pedirá usuario y
contraseña (el login, vía Caddy) y después debería verse la misma app que con `npm run dev`, pero ahora contra
Postgres en vez de SQLite.

Para pararlo: `docker compose down` (los datos de Postgres se conservan). Para borrar también los datos y empezar
de cero: `docker compose down -v`.

## Tarea diaria automática

Ya forma parte del propio backend (`app/jobs/scheduler.py`): además de la actualización horaria, cada día a las
23:00 hora de Madrid vuelve a descargar los 10 años de histórico completo (igual que el botón de Ajustes), para
que splits o dividendos que Yahoo Finance ajuste con efecto retroactivo también lleguen solos, sin pulsar nada.
No hace falta configurar nada aparte: corre mientras el contenedor `backend` esté encendido.

## Copias de seguridad de la base de datos

`deploy/backup.sh` hace un volcado comprimido de Postgres en `deploy/backups/` (ya excluido de git) y borra los
de más de 14 días. Pruébalo a mano:

```bash
cd /mnt/d/GIT/proyectos_propios/broker/deploy
bash backup.sh
```

En el VPS, para que se haga sola todas las noches, añade una línea con `crontab -e`:

```
0 4 * * * cd /ruta/al/proyecto/deploy && bash backup.sh >> backup.log 2>&1
```

Para restaurar un volcado (p. ej. tras un fallo): `gunzip -c deploy/backups/broker_XXXXXXXX.sql.gz | docker compose exec -T db psql -U broker broker`.

## Cuando tengas el VPS y un dominio

1. Apunta el dominio (registro DNS tipo A) a la IP del VPS.
2. En el VPS: clona el repositorio, copia `deploy/.env.example` a `deploy/.env`, rellena los valores (incluido el
   hash de la contraseña, como arriba) y pon en `DOMAIN` el dominio real.
3. `docker compose up --build -d` (el `-d` lo deja en segundo plano). Caddy pedirá solo el certificado HTTPS la
   primera vez que alguien entre por ese dominio.
4. Añade la tarea de `crontab` de copias de seguridad de arriba.
