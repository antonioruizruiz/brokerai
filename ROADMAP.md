# Hoja de ruta

Marca cada casilla al terminar. No pases de fase sin que la anterior funcione.

## Fase 0 — Preparación (tú) — ver pasos detallados en GUIA_CLAUDE_CODE.md
Desarrollo de momento en **WSL (Ubuntu) local**, dentro de tu PC Windows. El VPS remoto se deja para la Fase 8.
- [x] Node.js 22 instalado (v22.13.1 vía nvm) y npm
- [x] git instalado (2.25.1)
- [x] Claude Code instalado y funcionando
- [x] Python 3.12.7 instalado con `pyenv` (compilado a mano; `deadsnakes` no soporta ya Ubuntu 20.04)
- [x] Recreado `backend/.venv` con Python 3.12 y comprobado `pytest` (2 passed)
- [x] Backend probado (`/api/health` y `/api/companies`) en `http://localhost:8000` (sin túnel SSH)
- [x] Crear repositorio privado en GitHub y subir esta carpeta (`antonioruizruiz/borkerai`)
- [ ] Crear cuenta en console.anthropic.com y una API key (se usará en la Fase 6)
- [ ] (Más adelante, Fase 8) Contratar/activar el VPS Ubuntu, conectar por SSH y desplegar ahí

## Fase 1 — Datos
- [x] Modelos de BD: `Company`, `PriceBar` (diario OHLCV), `Dividend`
- [x] Servicio `MarketDataProvider` + implementación yfinance
- [x] Script para descargar 10 años de histórico de los 35 valores (ejecutado, BD con datos reales)
- [x] Endpoints: `GET /api/companies`, `GET /api/companies/{ticker}/prices?desde=`

## Fase 2 — Frontend básico
- [x] Crear proyecto Vite + React + TS + Tailwind + shadcn/ui (estilo shadcn, componentes propios ligeros)
- [x] Barra superior: Hoy · Ranking · Mercado · Cartera · Dividendos · Fiabilidad · Buscar · Ajustes (solo Mercado con contenido real; el resto "Próximamente")
- [x] Página Mercado: listado del IBEX 35 con precio y variación (`GET /api/companies` ampliado con `last_price`/`change_pct`)
- [x] Ficha de empresa con gráfica de precio (Lightweight Charts) y medias de 50/200
- [x] Fecha de última actualización en Mercado + 3 noticias recientes por empresa (vía RSS de Google News)

## Fase 3 — Puntuación cuantitativa
- [x] Indicadores: medias 50/200, momentum 12-1, volatilidad, máximos de N sesiones, volumen relativo
- [x] Factores 0–100 comparados con el resto del índice (momentum, tendencia, estabilidad, fuerza del sector;
      calidad y valoración quedan para cuando tengamos datos fundamentales)
- [x] Página Ranking + barras "Factores frente al mercado" (gráfica con Recharts)

## Fase 4 — Recomendaciones (página Hoy)
- [x] Reglas de entrada (ruptura de máximos con volumen, retroceso en tendencia alcista)
- [x] Plan: orden límite, stop, objetivo, plazo, beneficio/riesgo neto de costes, acciones según capital y riesgo
      (capital/riesgo/comisiones editables en la página Ajustes, `GET/PUT /api/settings`)
- [x] Clasificación por riesgo (bajo/medio/alto, a partir de la Estabilidad del Ranking) y lista "En vigilancia"

## Fase 5 — Simulación y Fiabilidad
- [x] Backtest de las reglas de la Fase 4 sobre los 10 años de histórico, con comisiones y deslizamiento
      descontados (`app/services/backtest.py`)
- [x] Comparación con el propio IBEX 35 (histórico real del índice descargado, ticker `^IBEX`, tabla `IndexBar`)
- [x] Seguimiento medio D+1/D+5/D+10/D+20 de cada señal histórica
- [x] Página Fiabilidad (`GET /api/fiabilidad`): resumen global, desglose por regla, seguimiento, comparación
      IBEX e historial de operaciones simuladas

## Fase 6 — IA con Claude — **aplazada**
Pendiente de una API key de la API de pago por uso de Anthropic (console.anthropic.com). La cuenta Enterprise de
Antonio solo tiene de momento una licencia "training" de Claude.ai, que es un producto distinto y no da acceso a
esa API. Opciones sobre la mesa: cuenta personal propia, o pedir acceso a IT de la empresa. Se retoma cuando
Antonio tenga la clave.
- [ ] Servicio de revisión: recibe datos + noticias/hechos relevantes → veredicto (APROBAR / PRUDENCIA / DESCARTAR) + texto
- [ ] Registro de tokens y coste; panel en Ajustes

## Fase 7 — Cartera y Dividendos
- [x] Añadir operaciones reales, valor actual, ganancia/pérdida (`GET/POST/DELETE /api/cartera`)
- [x] Revisión según el tipo de posición (corto plazo, largo plazo, dividendos): avisos simples de pérdida/ganancia
      relevante, o próximo dividendo estimado
- [x] Página Dividendos (rentabilidad por dividendo, historial, próxima fecha estimada — `GET /api/dividendos`)

## Fase 8 — Despliegue en VPS Ubuntu
Código listo (`backend/Dockerfile`, `frontend/Dockerfile` + `Caddyfile`, `deploy/`); pendiente de probar de
verdad con `docker compose up --build` (ver `deploy/LEEME.md`) y, más adelante, con el VPS y dominio reales.
- [ ] Dockerfiles backend/frontend + docker-compose con PostgreSQL — código listo, falta probarlo
- [ ] Caddy con dominio y HTTPS — código listo (automático en cuanto `DOMAIN` sea un dominio real), falta probarlo
- [ ] Login (un solo usuario) — `basic_auth` en Caddy delante de toda la app, código listo, falta probarlo
- [ ] Tarea diaria automática tras el cierre del mercado (23:00 Madrid, ya cubre Dow Jones/Nasdaq-100 también) —
      código listo (`app/jobs/scheduler.py`), falta probarlo
- [ ] Copias de seguridad de la BD — `deploy/backup.sh` + cron, código listo, falta probarlo
