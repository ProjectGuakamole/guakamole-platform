# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas de la interfaz Makefile validadas tras el punto 3.

## Responsabilidad del documento

Recoge reglas de selección de entorno, targets, ayuda y guardas. La evidencia detallada permanece en el histórico Makefile.

## Estado actual

**VALIDADO — punto 3 completado.**

## Cambios realizados

Se mantienen las reglas del punto 2 y se incorporan las guardas vigentes para el rebaseline destructivo del punto 3.

## Justificacion tecnica

La interfaz de comandos debe exigir el contexto correcto antes de modificar datos o esquema. Las guardas convierten esa exigencia en una precondición verificable.

## Decisiones tomadas

### Reglas validadas

- Los targets seleccionan `ENV_FILE` explícitamente; no usan una plantilla de entorno como fallback.
- `.env` es local e ignorado por Git; el fichero de ejemplo no es operativo.
- `backend-test-db` usa exclusivamente `TEST_DATABASE_URL`, exige una base local con sufijo `*_test`, rechaza hosts remotos, reconstruye destructivamente el baseline IAM con confirmación explícita y después ejecuta toda la suite `db or integration`.
- Downgrade se limita a `development` y `test` y mantiene la guarda de migración ante datos dependientes.
- Los seeds tienen guarda de entorno; ayuda y preflight exponen las precondiciones.
- CI genera un `.env.ci` efímero, sin depender del fichero de ejemplo.
- La matriz de `APP_ENV` para `development`, `test`, `staging` y `production` está validada desde el punto de vista de seguridad.
- El rebaseline exige confirmación explícita. En `test` solo se admite `TEST_DATABASE_URL` local dirigido a `*_test`; en desarrollo se exige `REBASELINE_DEVELOPMENT_DATABASE_URL` independiente, local y dirigido a `*_dev` o `*_development`. Se rechazan hosts remotos.
- El seed conserva el preflight de `pgcrypto` y la sincronización de identidades como requisitos operativos.
- El punto 3 no implementa targets Makefile adicionales.

No se implementa un target de bootstrap en este cambio.

## Tests ejecutados

- `make backend-quality`: **OK** (`ruff`, formato sobre **159 archivos** y `mypy` sobre **158 archivos fuente**).
- `make backend-test-unit`: **308 passed, 70 deselected**.
- `make backend-test-db`: **48 passed, 330 deselected** y **2 advertencias de Alembic**.
- `make backend-test-security`: **22 passed, 356 deselected**.
- Suite completa con `TEST_DATABASE_URL` local dedicada: **378 passed** y **2 advertencias de Alembic**.
- Ejecución directa de `pytest` sin URL de pruebas: **330 passed, 48 skipped**.

`backend-test-db` requiere la URL y rebaselinea destructivamente la base local `*_test` antes de las pruebas. Sin URL, la ejecución directa de `pytest` omite los 48 casos de base de datos. Las advertencias de Alembic son un seguimiento no bloqueante; no se documenta una corrección no aplicada.

## Riesgos o deuda tecnica

No existe un target de bootstrap en este alcance.

## Relacion con el backend

Estas reglas hacen que la operación de la base de datos desde el backend requiera una configuración seleccionada y un entorno autorizado.
