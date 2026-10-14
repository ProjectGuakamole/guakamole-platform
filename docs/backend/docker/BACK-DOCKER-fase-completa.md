# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evidencia Docker del punto 2 para la configuración del backend y su contexto de construcción, dentro del alcance de migraciones.

## Responsabilidad del documento

Este histórico trata Compose y el contexto de imagen. No describe el grafo Alembic ni la interfaz operativa de Makefile.

## Estado actual

**Punto 4 documentado.** Este histórico no declara un cierre global.

## Cambios realizados

- El servicio backend de Compose recibe una lista explícita de variables permitidas; no carga el entorno completo, la contraseña de PostgreSQL ni la base de datos de pruebas.
- La configuración seleccionada es determinista para el servicio.
- Se añadió `.dockerignore` al contexto de construcción de `backend/`: excluye archivos de entorno, Git, cachés, entornos virtuales y pruebas, y conserva aplicación, Alembic, `alembic.ini` y scripts necesarios.
- No se implementa una tarea Docker específica para migraciones.
- El rebaseline documentado en el punto 3 es destructivo y solo admite destinos locales de desarrollo o prueba explícitamente seguros; se rechazan hosts remotos. Esta condición aplica igualmente si en el futuro se orquesta desde un contenedor.
- No se ha creado ni modificado ninguna tarea Docker para ejecutar migraciones o rebaseline.
- El bootstrap de catálogos aprobados, la demo contenida y el rebaseline total siguen siendo operaciones explícitas fuera del arranque Docker y con destinos locales dedicados; `DATABASE_URL` no es su destino. Tras Alembic o rebaseline, el bootstrap resuelve los catálogos por claves naturales y asigna identificadores públicos estándar, válidos y deterministas antes de la demo; seed y clear no modifican catálogos.
- Las migraciones no incorporan DML de catálogo o demo.

## Justificacion tecnica

La lista permitida limita la propagación accidental de configuración al contenedor. Reducir el contexto de construcción evita incluir material local no necesario sin retirar los recursos que necesita la imagen.

## Decisiones tomadas

- Mantener la configuración de Compose sin secretos documentados.
- No iniciar migraciones automáticamente con el backend; el trabajo Docker explícito se evaluará en el punto 5.
- No atribuir a Compose la carga de catálogos, permisos SQL ni la gestión de identidades: son responsabilidades operativas explícitas del backend y de PostgreSQL, no cambios Docker realizados.
- Conservar en la imagen únicamente los recursos requeridos para ejecutar el backend y Alembic.
- No añadir al contenedor una migración automática, bootstrap automático ni una operación demo destructiva.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de deprecación de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas. No se dispone de resultado de renderizado de Compose ni de una suite Docker para este punto.

## Riesgos o deuda tecnica

- No existe todavía una tarea Docker dedicada de migraciones.
- La orquestación Docker de baseline/rebaseline no se ha implantado y queda fuera de este cambio.

## Relacion con el backend

El backend recibe solo la configuración necesaria al ejecutarse en Compose y su imagen evita incorporar ficheros locales ajenos a la aplicación.
