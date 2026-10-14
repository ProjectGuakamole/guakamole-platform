# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas Docker validadas y distinguirlas de la operación de migraciones, que queda fuera de este cambio.

## Responsabilidad del documento

Recoge únicamente reglas de Compose y contexto de construcción del backend dentro de este alcance.

## Estado actual

**Punto 4 documentado.** Se preservan las reglas Docker existentes; no se añade una orquestación Docker de migraciones.

## Cambios realizados

Se mantienen las reglas de Compose y contexto del punto 2. El punto 4 documenta que bootstrap, demo y rebaseline se ejecutan contra destinos locales dedicados y no desde `DATABASE_URL`; no introduce cambios Docker.

## Justificacion tecnica

Estas reglas reducen la exposición de configuración y el contenido innecesario de la imagen sin afectar a los archivos de ejecución requeridos.

## Decisiones tomadas

### Reglas validadas

- Compose configura el backend mediante una allowlist explícita, sin cargar el entorno completo ni incluir credenciales de PostgreSQL o configuración de pruebas.
- El contexto de `backend/` excluye archivos de entorno, Git, cachés, entornos virtuales y pruebas, y conserva aplicación, Alembic, `alembic.ini` y scripts.
- No hay ejecución automática de migraciones al arrancar el backend ni target Docker de migración o rebaseline.
- Cualquier futura orquestación Docker del rebaseline deberá exigir confirmación explícita y conservar sus destinos seguros: prueba local `*_test` o desarrollo local separado `*_dev`/`*_development`; se rechazan hosts remotos.
- Bootstrap, seed demo y rebaseline no forman parte del arranque del contenedor. Las migraciones siguen siendo DDL-only; tras Alembic o rebaseline, el bootstrap resuelve los catálogos aprobados por claves naturales y les asigna identificadores públicos estándar, válidos y deterministas antes de la demo. Seed y clear no modifican catálogos.

- No se implementa una tarea Docker para migraciones.
- Se mantiene prohibida la ejecución automática de migraciones al arrancar el backend.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de deprecación de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas. No se ha aportado evidencia de un renderizado de Compose ni de una prueba Docker específica en este punto.

## Riesgos o deuda tecnica

La tarea Docker de migraciones no se ha implantado y queda fuera de este cambio.

## Relacion con el backend

Las reglas reducen qué configuración y qué ficheros acompañan al backend en contenedor.
