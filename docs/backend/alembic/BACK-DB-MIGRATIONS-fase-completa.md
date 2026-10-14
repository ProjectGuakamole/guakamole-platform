# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Documentar la evidencia de Alembic de los puntos 1, 2 y 3 de la auditoría, sin declarar terminada la fase completa.

## Responsabilidad del documento

Este histórico cubre el grafo de migraciones, su evolución estructural y las garantías operativas de downgrade. La selección de configuración operativa se documenta en Makefile y el empaquetado en Docker.

## Estado actual

**Punto 4 documentado.** El nombre `fase-completa` identifica el histórico, no el cierre global.

## Cambios realizados

- Se incorporó la evidencia del punto 1: grafo lineal `0001` a `0014`, con `DML0012`, `backfill0013` y `DDL0014` diferenciados.
- Se verificó que el objetivo futuro es concentrar los cambios estructurales en una única migración DDL; no está implementado y no se ha reescrito el historial.
- En el punto 2, Alembic obtiene su conexión exclusivamente de `DATABASE_URL` configurada de forma centralizada; no utiliza una alternativa desde el fichero ini.
- El downgrade histórico rechaza primero la existencia de datos dependientes antes de borrar. La cabecera de migraciones se restauró al head tras la comprobación.
- El punto 3 sustituye el histórico anterior por el único revision `iam_baseline`, exclusivamente DDL, que crea las 11 tablas del esquema `sch_iam`. La versión se registra mediante `public.alembic_version` por defecto.
- El baseline no instala `pgcrypto` ni ejecuta `GRANT` o `REVOKE`. Las identidades de organizaciones y usuarios comienzan en 1 y los `public_id` se generan en Python.
- Se documentan las restricciones de integridad tenant en las relaciones de departamento, la coherencia geográfica y las unicidades basadas en `lower(...)`.
- Alembic recibe la conexión inyectada y validada; no ejecuta migraciones durante el arranque del backend.
- La implementación histórica del seed con preflight de `pgcrypto` y sincronización de identidades queda sustituida por la operación separada del punto 4.
- El punto 4 retira esa dependencia operativa del seed: los catálogos y la geografía aprobados se cargan mediante un bootstrap transaccional posterior a Alembic o rebaseline, que resuelve claves naturales y usa identificadores públicos estándar, válidos y deterministas; no hay DML en migraciones. El bootstrap precede siempre a la demo y ni seed ni clear modifican catálogos.
- El rebaseline es total: elimina el esquema IAM y el estado de Alembic del destino validado antes de recrear `iam_baseline`.
- La demo reemplaza o elimina únicamente sus entidades gestionadas tras comprobar su contención y no usa el destino general `DATABASE_URL`.

## Justificacion tecnica

La diferenciación entre DML, backfill y DDL permitió auditar el histórico previo. El baseline DDL-only separa la definición de esquema de extensiones, permisos y carga de datos. Las restricciones de tenant, geografía y unicidad hacen que la integridad se aplique también en PostgreSQL.

## Decisiones tomadas

- Los upgrades directos desde `0001` a `0014` ya no están soportados. `iam_baseline` requiere una base de datos nueva o reconstruida que sea elegible.
- Validar como fuente única de conexión de Alembic la configuración central `DATABASE_URL`, sin fallback del ini.
- Reservar el rebaseline destructivo para desarrollo y pruebas, con confirmación explícita y destino seguro: en pruebas, solo `TEST_DATABASE_URL` terminado en `*_test`; en desarrollo, una `REBASELINE_DEVELOPMENT_DATABASE_URL` separada, local y terminada en `*_dev` o `*_development`.
- No incluir extensiones ni privilegios en la revisión de esquema.
- No se ha implantado una tarea Docker de migraciones en este punto; queda fuera de este cambio.
- Mantener el baseline como DDL-only y separar los catálogos canónicos en bootstrap para que la reconstrucción de esquema no introduzca datos operativos.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas. No se documentan validaciones manuales adicionales.

## Riesgos o deuda tecnica

- La transición exige recrear una base elegible; no existe una ruta de upgrade directo desde el histórico retirado.
- La tarea Docker de migraciones queda fuera de este cambio.
- El downgrade protegido requiere que las futuras migraciones preserven precondiciones equivalentes cuando puedan existir datos dependientes.

## Relacion con el backend

Las migraciones siguen evolucionando el esquema del backend de forma trazable. La conexión centralizada y el rechazo seguro del downgrade refuerzan la operación de PostgreSQL sin exponer configuración alternativa.
