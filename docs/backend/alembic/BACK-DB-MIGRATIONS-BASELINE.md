# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas de Alembic vigentes tras la validación del punto 3.

## Responsabilidad del documento

Recoge reglas de migraciones y su acceso a base de datos. No duplica la selección de entornos de Makefile ni el empaquetado Docker.

## Estado actual

**VALIDADO — punto 3 completado.**

## Cambios realizados

Se mantienen las reglas del punto 2 y se incorpora el baseline `iam_baseline` DDL-only para `sch_iam`.

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
- Los seeds requieren preflight de `pgcrypto` y sincronización de identidades.
- El rebaseline es destructivo y solo se autoriza con confirmación explícita: pruebas con `TEST_DATABASE_URL` `*_test`, o desarrollo local separado con `REBASELINE_DEVELOPMENT_DATABASE_URL` `*_dev` o `*_development`.

La orquestación Docker de migraciones no forma parte de este cambio.

## Tests ejecutados

- `make backend-quality`: **OK** (`ruff`, formato sobre **159 archivos** y `mypy` sobre **158 archivos fuente**).
- `make backend-test-unit`: **308 passed, 70 deselected**.
- `make backend-test-db`: **48 passed, 330 deselected** y **2 advertencias de Alembic**.
- `make backend-test-security`: **22 passed, 356 deselected**.
- Suite completa con `TEST_DATABASE_URL` local dedicada: **378 passed** y **2 advertencias de Alembic**.
- Ejecución directa de `pytest` sin URL de pruebas: **330 passed, 48 skipped**.

`backend-test-db` exige `TEST_DATABASE_URL` y, antes de la suite de base de datos, reconstruye destructivamente el baseline en una base local terminada en `*_test`. Se rechazan hosts remotos. La ejecución directa de `pytest` no dispone de esa URL y por ello omite las 48 pruebas que requieren base de datos.

## Riesgos o deuda tecnica

No se admite upgrade directo desde el historial `0001`...`0014`: se necesita una base nueva o reconstruida elegible para el baseline. Las dos advertencias de Alembic son un seguimiento no bloqueante; no se documenta una corrección porque no se ha aplicado ninguna. La orquestación Docker de migraciones queda fuera de este cambio.

## Relacion con el backend

Estas reglas protegen la evolución de la persistencia del backend y evitan que Alembic seleccione una conexión no prevista.
