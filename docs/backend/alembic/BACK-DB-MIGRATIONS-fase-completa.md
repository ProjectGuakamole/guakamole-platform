# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar el histórico de Alembic y la evidencia del punto 5 sin declarar cerrada la auditoría global.

## Responsabilidad del documento

Este histórico cubre el baseline y su ejecución. La selección de Compose y los comandos de operador se documentan por separado.

## Estado actual

**Punto 5 documentado.** El nombre `fase-completa` conserva el histórico; no implica el cierre de trabajos posteriores.

## Cambios realizados

- Los puntos anteriores dejaron un único baseline `iam_baseline`, DDL-only, para `sch_iam`.
- El punto 5 sustituye las afirmaciones históricas de migración Alembic directa desde host mediante `DATABASE_URL` por el migrador Docker aislado.
- El perfil `migration` ejecuta explícitamente `upgrade head`, `current` y `check`; el backend no migra durante su arranque.
- La migración se aplica con el rol de migración y la aplicación se conecta con el rol de aplicación.

## Justificacion tecnica

El contrato separa privilegios y artefactos: migrador y aplicación comparten imagen, pero no identidad ni responsabilidad. Evita que la disponibilidad de la API dependa de una migración implícita.

## Decisiones tomadas

- `docker-db-migrate` es la vía de aplicación; `docker-db-current` y `docker-db-check` son las comprobaciones operativas.
- `docker-db-check` contrasta la revisión actual con el `head` empaquetado. No invoca deliberadamente `alembic check`, por lo que no realiza autogeneración ni comparación de deriva ORM/esquema.
- `docker-deploy` es el flujo canónico: migra y después levanta el stack base. `docker-up` es manual y no migra.
- No hay downgrade Docker.
- El migrador exige `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`; sus valores no se documentan ni registran en logs.
- En volúmenes nuevos los roles se crean durante init. Los volúmenes existentes requieren `db-provision-roles` con confirmación explícita.
- La comprobación de disponibilidad requiere base de datos lista y revisión Alembic en `head`.

## Tests ejecutados

- Tras un `docker compose config` válido, se provisionaron roles y se aplicó el baseline con el migrador.
- Una segunda ejecución de migración quedó en `already_at_head`; `current` y `check` se ejecutaron correctamente.
- Tests de migraciones disponibles: **21 passed**. Mypy finalizó correctamente.
- No se documenta un resultado de suite completa porque no se aportó un recuento actual verificable.

## Riesgos o deuda tecnica

La configuración local de Compose publica el puerto de PostgreSQL y la conexión TCP a `localhost:5432` se validó correctamente. Esta exposición queda limitada al override local: el Compose base de staging mantiene PostgreSQL aislado y sin publicar puertos al host.

## Relacion con el backend

El contrato protege el esquema que consume FastAPI: la API usa una identidad de mínimo privilegio y solo se declara lista cuando la base y las migraciones están preparadas.
