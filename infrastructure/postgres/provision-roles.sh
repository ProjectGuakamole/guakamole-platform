#!/bin/sh
set -eu

# Operación manual para volúmenes ya existentes. No la invoca Compose ni Alembic.
: "${ADMIN_DATABASE_URL:?}"
: "${ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL:?}"
: "${MIGRATION_DB_PASSWORD:?}"
: "${APP_DB_PASSWORD:?}"
: "${ROLE_PROVISION_ALLOWED_DATABASES:?}"
: "${ROLE_PROVISION_EXPECTED_DB_USER:?}"

[ "$ADMIN_DATABASE_URL" = "$ROLE_PROVISION_EXPECTED_ADMIN_DATABASE_URL" ] || {
  printf 'URL de administrador no autorizada.\n' >&2; exit 1;
}

database_name=$(psql "$ADMIN_DATABASE_URL" --tuples-only --no-align --quiet \
  --command 'SELECT current_database()')
database_user=$(psql "$ADMIN_DATABASE_URL" --tuples-only --no-align --quiet \
  --command 'SELECT current_user')

case ",$ROLE_PROVISION_ALLOWED_DATABASES," in *",$database_name,"*) ;; *)
  printf 'Destino de provisión no autorizado.\n' >&2; exit 1;; esac
[ "$database_user" = "$ROLE_PROVISION_EXPECTED_DB_USER" ] || {
  printf 'Usuario administrador no autorizado.\n' >&2; exit 1;
}

psql "$ADMIN_DATABASE_URL" --set ON_ERROR_STOP=1 \
  --set db_name="$database_name" \
  --set migrator_password="$MIGRATION_DB_PASSWORD" \
  --set app_password="$APP_DB_PASSWORD" \
  --file "$(dirname "$0")/roles.sql"
