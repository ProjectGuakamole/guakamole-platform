# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas de Alembic vigentes tras la validación del punto 3.

## Responsabilidad del documento

Recoge reglas de migraciones y su acceso a base de datos. No duplica la selección de entornos de Makefile ni el empaquetado Docker.

## Estado actual

**Punto 4 documentado.** Se preserva el baseline DDL del punto 3 y se añade la operación separada de bootstrap, demo y rebaseline.

## Cambios realizados

Se mantienen las reglas del punto 2 y el baseline `iam_baseline` DDL-only para `sch_iam`. En el punto 4, los catálogos IAM aprobados se cargan mediante bootstrap transaccional, fuera de Alembic; la demo se limita a su espacio gestionado y el rebaseline reconstruye el esquema completo antes de aplicar el baseline.

## Justificacion tecnica

Una única fuente de conexión evita que una migración opere contra una base distinta de la seleccionada. La precondición previa a borrados hace explícito el riesgo sobre datos operativos.

## Decisiones tomadas

### Reglas validadas

- Alembic recibe `DATABASE_URL` desde la configuración central explícita.
- Alembic no usa un fallback de configuración en `alembic.ini` ni en una plantilla de entorno.
- Un downgrade histórico con borrados comprueba antes los datos dependientes y rechaza la operación si existen.
- La única revisión vigente es `iam_baseline`: DDL-only, con 11 tablas en `sch_iam` y control de versión en `public.alembic_version` por defecto.
- La revisión no instala `pgcrypto` ni modifica privilegios mediante `GRANT` o `REVOKE`.
- Las identidades de organización y usuario empiezan en 1; `public_id` se genera en Python.
- El esquema preserva integridad tenant en relaciones de departamento, coherencia geográfica y unicidad insensible a mayúsculas mediante `lower(...)`.
- Alembic usa una conexión inyectada y validada; el arranque del backend no migra la base de datos.
- La referencia histórica a un seed con preflight de `pgcrypto` y sincronización de identidades queda sustituida en el punto 4 por bootstrap de catálogos y demo sin esa dependencia.
- El rebaseline es destructivo y solo se autoriza con confirmación explícita: pruebas con `TEST_DATABASE_URL` `*_test`, o desarrollo local separado con `REBASELINE_DEVELOPMENT_DATABASE_URL` `*_dev` o `*_development`.
- Las migraciones no contienen DML de catálogos ni de demo. Tras Alembic o rebaseline, el bootstrap resuelve los catálogos canónicos mediante claves naturales, crea los que falten con identificadores públicos estándar, válidos y deterministas, y valida colisiones; debe completarse antes de la demo. Seed y clear no modifican catálogos.
- El rebaseline elimina `sch_iam` y `public.alembic_version` en un destino validado y vuelve a aplicar `iam_baseline`; no es una limpieza parcial de datos.
- Bootstrap y demo usan destinos dedicados (`TEST_DATABASE_URL` en pruebas y variables específicas en desarrollo), nunca `DATABASE_URL`.

La orquestación Docker de migraciones no forma parte de este cambio.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas. No se documentan validaciones manuales adicionales.

## Riesgos o deuda tecnica

No se admite upgrade directo desde el historial `0001`...`0014`: se necesita una base nueva o reconstruida elegible para el baseline. El rebaseline es necesariamente destructivo. La orquestación Docker de migraciones queda fuera de este cambio.

## Relacion con el backend

Estas reglas protegen la evolución de la persistencia del backend y evitan que Alembic seleccione una conexión no prevista.
