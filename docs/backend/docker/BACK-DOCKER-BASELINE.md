# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar el contrato Docker validado en el punto 5.

## Responsabilidad del documento

Recoge red, imágenes, perfiles y responsabilidades de Compose. No sustituye el procedimiento de Alembic ni la interfaz Makefile.

## Estado actual

**Punto 5 documentado.** Se conserva el histórico de contexto reducido y allowlist de configuración, actualizado con un migrador Docker explícito.

## Cambios realizados

- El servicio `migrate` pertenece al perfil `migration` y reutiliza la imagen del backend.
- La imagen de aplicación y la de migración se ejecutan como usuario no root; el migrador es efímero, de solo lectura y sin capacidades adicionales.
- El stack base no inicia migraciones. `docker-compose.yml` mantiene `backend_internal` con `internal: true` y solo Nginx publica un puerto: PostgreSQL, backend y frontend no se exponen al host.
- `docker-compose.local.yml` es obligatorio exclusivamente para desarrollo local y CI: publica los puertos de PostgreSQL, backend y frontend y redefine `backend_internal` con `internal: false` para clientes del host, como pgAdmin.
- La inicialización de PostgreSQL prepara roles en un volumen nuevo; `db-provision-roles` permite provisionarlos explícitamente en un volumen existente.

## Justificacion tecnica

El perfil evita mutaciones de esquema al levantar servicios normales. Mantener aislado el stack base reduce superficie de red; el override local aporta de forma explícita la conectividad necesaria para desarrollo y CI sin convertirla en comportamiento de staging.

## Decisiones tomadas

- `docker-up` es manual y no migra; `docker-deploy` es canónico y migra antes de levantar el stack base.
- `docker-up` utiliza el override local; `docker-deploy` usa solo el compose base de staging y conserva el aislamiento de `backend_internal`.
- pgAdmin solo se conecta en local mediante el override: host `localhost`, puerto `POSTGRES_PORT`, base `POSTGRES_DB`, usuario `POSTGRES_USER` y contraseña `POSTGRES_PASSWORD`.
- Se usan `docker-db-migrate`, `docker-db-current` y `docker-db-check`; no existe Docker downgrade.
- `docker-db-check` comprueba que la revisión actual es el `head` empaquetado; no ejecuta `alembic check` ni una comparación de deriva ORM/esquema.
- El migrador exige las variables `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`.
- Compose pasa una allowlist de variables a cada servicio. No se documentan secretos ni se permite registrarlos en logs.
- Backend y migrador usan roles distintos: el primero aplica permisos de aplicación y el segundo permisos de migración.
- La readiness requiere PostgreSQL listo y Alembic en `head`.

## Tests ejecutados

- `docker compose config` fue válido con la configuración de validación.
- Se realizó el provisionamiento de roles y el baseline se aplicó con `docker-db-migrate`; la repetición informó `already_at_head`.
- `docker-db-current` y `docker-db-check` finalizaron correctamente.
- Los endpoints de health y ready devolvieron HTTP 200 desde el contenedor backend.

## Riesgos o deuda tecnica

La publicación de puertos del override incrementa la superficie de exposición local; no debe incluirse en staging. La conectividad con clientes del host depende de levantar el stack mediante `docker-up` y su override.

## Relacion con el backend

Docker proporciona a FastAPI una base migrada, con rol de aplicación y red interna; el cambio de esquema permanece separado del proceso de servicio.
