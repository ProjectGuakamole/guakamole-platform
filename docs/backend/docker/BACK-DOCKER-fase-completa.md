# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evidencia Docker del punto 2 para la configuración del backend y su contexto de construcción, dentro del alcance de migraciones.

## Responsabilidad del documento

Este histórico trata Compose y el contexto de imagen. No describe el grafo Alembic ni la interfaz operativa de Makefile.

## Estado actual

**VALIDADO — punto 3 aprobado y completado.** Este histórico no declara un cierre global.

## Cambios realizados

- El servicio backend de Compose recibe una lista explícita de variables permitidas; no carga el entorno completo, la contraseña de PostgreSQL ni la base de datos de pruebas.
- La configuración seleccionada es determinista para el servicio.
- Se añadió `.dockerignore` al contexto de construcción de `backend/`: excluye archivos de entorno, Git, cachés, entornos virtuales y pruebas, y conserva aplicación, Alembic, `alembic.ini` y scripts necesarios.
- No se implementa una tarea Docker específica para migraciones.
- El rebaseline documentado en el punto 3 es destructivo y solo admite destinos locales de desarrollo o prueba explícitamente seguros; se rechazan hosts remotos. Esta condición aplica igualmente si en el futuro se orquesta desde un contenedor.
- No se ha creado ni modificado ninguna tarea Docker para ejecutar migraciones o rebaseline.

## Justificacion tecnica

La lista permitida limita la propagación accidental de configuración al contenedor. Reducir el contexto de construcción evita incluir material local no necesario sin retirar los recursos que necesita la imagen.

## Decisiones tomadas

- Mantener la configuración de Compose sin secretos documentados.
- No iniciar migraciones automáticamente con el backend; el trabajo Docker explícito se evaluará en el punto 5.
- No atribuir a Compose la provisión de `pgcrypto`, permisos SQL o sincronización de identidades: son precondiciones operativas del seed y de PostgreSQL, no cambios Docker realizados.
- Conservar en la imagen únicamente los recursos requeridos para ejecutar el backend y Alembic.

## Tests ejecutados

Se validó el renderizado de las configuraciones de Compose para confirmar la selección determinista y la ausencia de secretos en la configuración resultante. La evidencia final es: `make backend-quality` **OK** (`ruff`, formato sobre **159 archivos** y `mypy` sobre **158 archivos fuente**); `make backend-test-unit` **308 passed, 70 deselected**; `make backend-test-db` **48 passed, 330 deselected** y **2 advertencias de Alembic**; `make backend-test-security` **22 passed, 356 deselected**; y suite completa con `TEST_DATABASE_URL` local dedicada **378 passed** y **2 advertencias de Alembic**. La ejecución directa de `pytest` sin URL de pruebas produjo **330 passed, 48 skipped**.

`backend-test-db` exige `TEST_DATABASE_URL`, rechaza hosts remotos y rebaselinea destructivamente una base local `*_test` antes de la suite de base de datos. La ejecución directa de `pytest` omite las 48 pruebas que requieren dicha URL. Las advertencias de Alembic son seguimiento no bloqueante y no se inventa una corrección no aplicada.

## Riesgos o deuda tecnica

- No existe todavía una tarea Docker dedicada de migraciones.
- La orquestación Docker de baseline/rebaseline no se ha implantado y queda fuera de este cambio.

## Relacion con el backend

El backend recibe solo la configuración necesaria al ejecutarse en Compose y su imagen evita incorporar ficheros locales ajenos a la aplicación.
