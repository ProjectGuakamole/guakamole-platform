# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar el cambio de interfaz operativa del punto 5 manteniendo el histórico de la fase.

## Responsabilidad del documento

Este documento describe los comandos de operador y no sustituye los contratos de Alembic ni de Docker.

## Estado actual

**Punto 5 documentado.** Las afirmaciones anteriores de migración Alembic directa desde el host con `DATABASE_URL` quedan reemplazadas por el migrador Docker.

## Cambios realizados

- `docker-db-migrate` aplica `head` mediante el perfil `migration`.
- `docker-db-current` consulta la revisión y `docker-db-check` verifica que coincide con el `head` empaquetado sin cambiar el esquema. Este último no invoca deliberadamente `alembic check`, por lo que no compara deriva ORM/esquema.
- `docker-deploy` migra antes de levantar el stack base; `docker-up` no migra y sirve para operación manual.
- `docker-up` incorpora el override local para desarrollo y CI; `docker-deploy` ejecuta solo el compose base de staging.
- Se añadió `db-provision-roles` para el caso de volúmenes existentes; en inicializaciones nuevas los roles los prepara PostgreSQL init.

## Justificacion tecnica

Un contrato único de despliegue evita que el estado de migración dependa de herramientas instaladas en el host y mantiene la separación entre privilegios de migración y de aplicación.

## Decisiones tomadas

- No existe `docker-db-downgrade` ni política de downgrade Docker.
- Las variables obligatorias del migrador son `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`.
- La validación aplica allowlists y no expone secretos en comandos, documentación o logs.
- `docker-deploy` es el procedimiento canónico; la readiness posterior exige DB lista y Alembic en `head`.
- `docker-compose.yml` mantiene `backend_internal` como red interna y no publica PostgreSQL, backend ni frontend. Solo el override local la hace no interna y publica esos puertos para el host.
- pgAdmin local se configura con host `localhost`, puerto `POSTGRES_PORT`, base `POSTGRES_DB`, usuario `POSTGRES_USER` y contraseña `POSTGRES_PASSWORD`.
- Las operaciones históricas de bootstrap, demo y rebaseline conservan sus guardas propias y no sustituyen al migrador de despliegue.

## Tests ejecutados

- `docker compose config` válido; roles provisionados; baseline aplicado y segunda migración en `already_at_head`.
- `docker-db-current` y `docker-db-check` correctos.
- Tests de migraciones: **21 passed**. Mypy correcto.
- No se inventa un resultado actualizado de los demás grupos de tests.

## Riesgos o deuda tecnica

La configuración local de Compose publica el puerto de PostgreSQL y la conexión TCP a `localhost:5432` se validó correctamente. La exposición es exclusiva del override local; el Compose base de staging conserva PostgreSQL aislado y sin publicar puertos al host.

## Relacion con el backend

Los operadores pueden preparar y comprobar el esquema antes de ejecutar FastAPI, conservando el proceso de aplicación libre de privilegios de DDL.
