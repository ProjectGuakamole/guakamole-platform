# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Documentar la evidencia de Alembic de los puntos 1, 2 y 3 de la auditoría, sin declarar terminada la fase completa.

## Responsabilidad del documento

Este histórico cubre el grafo de migraciones, su evolución estructural y las garantías operativas de downgrade. La selección de configuración operativa se documenta en Makefile y el empaquetado en Docker.

## Estado actual

**VALIDADO — punto 3 aprobado y completado.** El nombre `fase-completa` identifica el histórico, no el cierre global.

## Cambios realizados

- Se incorporó la evidencia del punto 1: grafo lineal `0001` a `0014`, con `DML0012`, `backfill0013` y `DDL0014` diferenciados.
- Se verificó que el objetivo futuro es concentrar los cambios estructurales en una única migración DDL; no está implementado y no se ha reescrito el historial.
- En el punto 2, Alembic obtiene su conexión exclusivamente de `DATABASE_URL` configurada de forma centralizada; no utiliza una alternativa desde el fichero ini.
- El downgrade histórico rechaza primero la existencia de datos dependientes antes de borrar. La cabecera de migraciones se restauró al head tras la comprobación.
- El punto 3 sustituye el histórico anterior por el único revision `iam_baseline`, exclusivamente DDL, que crea las 11 tablas del esquema `sch_iam`. La versión se registra mediante `public.alembic_version` por defecto.
- El baseline no instala `pgcrypto` ni ejecuta `GRANT` o `REVOKE`. Las identidades de organizaciones y usuarios comienzan en 1 y los `public_id` se generan en Python.
- Se documentan las restricciones de integridad tenant en las relaciones de departamento, la coherencia geográfica y las unicidades basadas en `lower(...)`.
- Alembic recibe la conexión inyectada y validada; no ejecuta migraciones durante el arranque del backend.
- El seed requiere un preflight de `pgcrypto` y sincroniza las secuencias de identidad tras la carga.

## Justificacion tecnica

La diferenciación entre DML, backfill y DDL permitió auditar el histórico previo. El baseline DDL-only separa la definición de esquema de extensiones, permisos y carga de datos. Las restricciones de tenant, geografía y unicidad hacen que la integridad se aplique también en PostgreSQL.

## Decisiones tomadas

- Los upgrades directos desde `0001` a `0014` ya no están soportados. `iam_baseline` requiere una base de datos nueva o reconstruida que sea elegible.
- Validar como fuente única de conexión de Alembic la configuración central `DATABASE_URL`, sin fallback del ini.
- Reservar el rebaseline destructivo para desarrollo y pruebas, con confirmación explícita y destino seguro: en pruebas, solo `TEST_DATABASE_URL` terminado en `*_test`; en desarrollo, una `REBASELINE_DEVELOPMENT_DATABASE_URL` separada, local y terminada en `*_dev` o `*_development`.
- No incluir extensiones ni privilegios en la revisión de esquema; el seed verifica `pgcrypto` antes de depender de ella.
- No se ha implantado una tarea Docker de migraciones en este punto; queda fuera de este cambio.

## Tests ejecutados

- `make backend-quality`: **OK**: `ruff`, formato sobre **159 archivos** y `mypy` sobre **158 archivos fuente**.
- `make backend-test-unit`: **308 passed, 70 deselected**.
- `make backend-test-db`: **48 passed, 330 deselected** y **2 advertencias de Alembic**.
- `make backend-test-security`: **22 passed, 356 deselected**.
- Suite completa con `TEST_DATABASE_URL` local dedicada: **378 passed** y **2 advertencias de Alembic**.
- Ejecución directa de `pytest` sin URL de pruebas: **330 passed, 48 skipped**.

`backend-test-db` exige `TEST_DATABASE_URL`, rechaza hosts remotos y reconstituye destructivamente una base local `*_test` antes de lanzar la suite `db or integration`. La ejecución directa de `pytest` no recibe esa URL y omite las 48 pruebas dependientes de base de datos.

## Riesgos o deuda tecnica

- La transición exige recrear una base elegible; no existe una ruta de upgrade directo desde el histórico retirado.
- La tarea Docker de migraciones queda fuera de este cambio.
- Las dos advertencias de Alembic son un seguimiento no bloqueante. No se ha aplicado ni se presume una corrección.
- El downgrade protegido requiere que las futuras migraciones preserven precondiciones equivalentes cuando puedan existir datos dependientes.

## Relacion con el backend

Las migraciones siguen evolucionando el esquema del backend de forma trazable. La conexión centralizada y el rechazo seguro del downgrade refuerzan la operación de PostgreSQL sin exponer configuración alternativa.
