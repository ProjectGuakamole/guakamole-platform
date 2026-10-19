#!/bin/sh
set -eu

# Sólo lo ejecuta la imagen oficial al inicializar un volumen PostgreSQL vacío.
# Nunca se debe montar ni ejecutar manualmente contra una base persistente.
: "${MIGRATION_DB_PASSWORD:?}"
: "${APP_DB_PASSWORD:?}"

psql --set ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set db_name="$POSTGRES_DB" \
  --set migrator_password="$MIGRATION_DB_PASSWORD" \
  --set app_password="$APP_DB_PASSWORD" \
  --file /opt/guakamole-postgres/roles.sql
