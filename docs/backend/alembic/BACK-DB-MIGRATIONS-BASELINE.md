# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar el contrato vigente de migraciones tras el punto 5 de la auditoría.

## Responsabilidad del documento

Recoge las reglas operativas de Alembic. El detalle de Compose y de los targets está en los documentos Docker y Makefile.

## Estado actual

**Punto 5 documentado.** Se conserva el histórico del baseline `iam_baseline` DDL-only y queda sustituida la operación directa de Alembic desde el host por un migrador Docker explícito.

## Cambios realizados

- El baseline sigue siendo la única revisión vigente y no incorpora DML de catálogos ni demo.
- Alembic se ejecuta mediante el perfil Compose `migration`, con los comandos `docker-db-migrate`, `docker-db-current` y `docker-db-check`.
- `docker-db-check` valida que la revisión Alembic actual coincide con el `head` empaquetado; deliberadamente no ejecuta `alembic check` ni compara deriva con los modelos ORM.
- El migrador recibe una URL de migración separada y validada; la aplicación usa su propia identidad y URL de aplicación.
- El arranque normal no aplica migraciones y no existe flujo Docker de downgrade.

## Justificacion tecnica

Separar la identidad que cambia el esquema de la identidad de ejecución reduce privilegios y evita que un proceso de aplicación migre accidentalmente una base de datos. El perfil explícito hace visible una operación que modifica estado.

## Decisiones tomadas

- El contrato anterior de ejecutar Alembic directamente en el host con `DATABASE_URL` queda reemplazado para la operación Docker.
- Son obligatorias para el migrador `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`.
- La URL y la identidad de migración se validan contra allowlists antes de ejecutar la operación; no se muestran secretos en salida ni en esta documentación.
- `migrate` solo acepta `upgrade`, `current` y `check`; no se ofrece downgrade en Docker.
- La migración utiliza la misma imagen no root que el backend, con las restricciones del servicio de migración.
- La disponibilidad operativa exige PostgreSQL listo y revisión en `head`; la readiness de la API depende de ambas condiciones.
- La inicialización de PostgreSQL provisiona los roles en un volumen nuevo. Para un volumen existente, el provisionamiento de roles es una operación explícita y confirmada mediante `db-provision-roles`.

## Tests ejecutados

- Evidencia del punto 5: se aplicó el baseline con `docker-db-migrate`; después `docker-db-migrate` informó que ya estaba en `head`, y `docker-db-current` y `docker-db-check` finalizaron correctamente.
- Se ejecutaron los tests de migraciones disponibles: **21 passed**.
- Mypy se ejecutó correctamente. No se dispone de recuento actual consolidado de la suite completa.

## Riesgos o deuda tecnica

La configuración local de Compose publica el puerto de PostgreSQL y la conexión TCP a `localhost:5432` se validó correctamente. Esta exposición queda limitada al override local: el Compose base de staging mantiene PostgreSQL aislado y sin publicar puertos al host.

## Relacion con el backend

El backend arranca con permisos de aplicación y consulta una base ya migrada. La evolución de esquema queda aislada, trazable y no forma parte del arranque automático.
