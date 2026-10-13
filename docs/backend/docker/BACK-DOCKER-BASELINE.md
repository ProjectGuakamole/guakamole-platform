# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas Docker validadas y distinguirlas de la operación de migraciones, que queda fuera de este cambio.

## Responsabilidad del documento

Recoge únicamente reglas de Compose y contexto de construcción del backend dentro de este alcance.

## Estado actual

**VALIDADO — punto 3 completado.**

## Cambios realizados

Se mantienen las reglas de Compose y contexto del punto 2. El punto 3 solo añade implicaciones operativas del baseline, sin cambios Docker.

## Justificacion tecnica

Estas reglas reducen la exposición de configuración y el contenido innecesario de la imagen sin afectar a los archivos de ejecución requeridos.

## Decisiones tomadas

### Reglas validadas

- Compose configura el backend mediante una allowlist explícita, sin cargar el entorno completo ni incluir credenciales de PostgreSQL o configuración de pruebas.
- El contexto de `backend/` excluye archivos de entorno, Git, cachés, entornos virtuales y pruebas, y conserva aplicación, Alembic, `alembic.ini` y scripts.
- No hay ejecución automática de migraciones al arrancar el backend ni target Docker de migración o rebaseline.
- Cualquier futura orquestación Docker del rebaseline deberá exigir confirmación explícita y conservar sus destinos seguros: prueba local `*_test` o desarrollo local separado `*_dev`/`*_development`; se rechazan hosts remotos.

- No se implementa una tarea Docker para migraciones.
- Se mantiene prohibida la ejecución automática de migraciones al arrancar el backend.

## Tests ejecutados

La validación de renderizado se conserva en el histórico Docker. La evidencia final es: `make backend-quality` **OK** (`ruff`, formato sobre **159 archivos** y `mypy` sobre **158 archivos fuente**); `make backend-test-unit`, **308 passed, 70 deselected**; `make backend-test-db`, **48 passed, 330 deselected** y **2 advertencias de Alembic**; `make backend-test-security`, **22 passed, 356 deselected**; y suite completa con `TEST_DATABASE_URL` local dedicada, **378 passed** y **2 advertencias de Alembic**. La ejecución directa de `pytest` sin URL de pruebas produjo **330 passed, 48 skipped**.

`backend-test-db` exige URL de pruebas, rechaza hosts remotos y rebaselinea destructivamente una base local `*_test` antes de su suite. Las advertencias son seguimiento no bloqueante; no se documenta una corrección no aplicada.

## Riesgos o deuda tecnica

La tarea Docker de migraciones no se ha implantado y queda fuera de este cambio.

## Relacion con el backend

Las reglas reducen qué configuración y qué ficheros acompañan al backend en contenedor.
