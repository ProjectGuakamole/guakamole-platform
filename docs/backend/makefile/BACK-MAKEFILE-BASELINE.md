# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar la interfaz Makefile vigente tras el punto 5.

## Responsabilidad del documento

Recoge comandos y guardas operativas. La implementación de Compose y Alembic se documenta en sus áreas correspondientes.

## Estado actual

**Punto 5 documentado.** Se preservan las guardas históricas de pruebas, bootstrap y demo; la migración operativa pasa a ser Docker explícito.

## Cambios realizados

- Se incorporan `docker-db-migrate`, `docker-db-current` y `docker-db-check` como interfaz del migrador aislado.
- `docker-db-check` valida la revisión actual contra el `head` empaquetado; no invoca deliberadamente `alembic check` ni compara la deriva entre ORM y esquema.
- `docker-deploy` ejecuta la migración y después levanta el stack base; `docker-up` solo levanta el entorno manual.
- `docker-up` usa obligatoriamente `docker-compose.local.yml` en desarrollo local y CI; `docker-deploy` usa únicamente `docker-compose.yml` para staging.
- `db-provision-roles CONFIRM=PROVISION_DATABASE_ROLES` permite aplicar explícitamente roles y privilegios sobre un volumen PostgreSQL ya existente.
- Los comandos host históricos de Alembic no constituyen la vía Docker de migración y no se admite downgrade Docker.

## Justificacion tecnica

Los nombres separan consultas, validación y mutación de esquema. La confirmación para roles evita que una operación administrativa sobre un volumen persistente se ejecute de forma accidental.

## Decisiones tomadas

- Antes de migrar se requiere una configuración `ENV_FILE` explícita.
- El migrador exige `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`.
- La aplicación usa el rol de aplicación y el migrador el rol de migración; no se intercambian sus responsabilidades.
- No se imprimen URLs ni secretos. Compose limita las variables entregadas a cada servicio mediante allowlist.
- La interfaz Docker no ofrece downgrade.
- El compose base conserva `backend_internal` con `internal: true` y no publica PostgreSQL, backend ni frontend. El override local publica esos puertos y redefine la red como no interna para clientes del host, como pgAdmin.
- La conexión pgAdmin local usa host `localhost`, puerto `POSTGRES_PORT`, base `POSTGRES_DB`, usuario `POSTGRES_USER` y contraseña `POSTGRES_PASSWORD`.
- `backend-check` comprueba health y readiness; esta última requiere base de datos lista y revisión en `head`.
- Init provisiona los roles de un volumen nuevo. Para un volumen existente debe usarse el target explícito de provisionamiento.

## Tests ejecutados

- La configuración Compose se validó correctamente.
- Se ejecutaron provisionamiento de roles, migración del baseline, repetición en `already_at_head`, `docker-db-current` y `docker-db-check`.
- Tests de migraciones disponibles: **21 passed**. Mypy finalizó correctamente.
- No hay evidencia actual suficiente para declarar un resultado de suite completa.

## Riesgos o deuda tecnica

La configuración local de Compose publica el puerto de PostgreSQL y la conexión TCP a `localhost:5432` se validó correctamente. La exposición es exclusiva del override local; el Compose base de staging conserva PostgreSQL aislado y sin publicar puertos al host.

## Relacion con el backend

Makefile establece un camino repetible para dejar la base lista antes de servir FastAPI, sin incorporar migraciones al arranque normal.
