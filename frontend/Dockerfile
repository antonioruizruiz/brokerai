# Etapa 1: compilar el frontend (Vite) a archivos estáticos
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Vacío en producción: las llamadas a la API van a rutas relativas /api/... que
# este mismo Caddy reenvía al backend (mismo origen, sin problemas de CORS).
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# Etapa 2: servir el estático y hacer de proxy + HTTPS automático con Caddy
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile
