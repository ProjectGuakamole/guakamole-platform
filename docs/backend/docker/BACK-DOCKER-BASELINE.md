# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Preparar las reglas del área Docker para la ejecución de migraciones dentro de la fase coordinada `BACK-DB-MIGRATIONS-AUDIT-001`, sin ampliar el alcance a una auditoría completa de Docker.

## Responsabilidad del documento

Recoger solo criterios de empaquetado, tarea de ejecución de migraciones y configuración de contenedores asociada. El contexto y las evidencias pertenecen al histórico Docker; la estructura de migraciones y la orquestación Makefile pertenecen a sus respectivas áreas.

## Estado actual

**BORRADOR NO VALIDADO.** Las orientaciones no acreditan comportamiento implantado ni comprobado. La intervención es documental y no autoriza continuar el punto 2.

## Cambios realizados

Se crea el baseline del área, sin modificar Dockerfiles, Compose, configuración o comandos de arranque. No se copia ningún baseline hexagonal u OAuth.

## Justificacion tecnica

Una tarea explícita hace visible la operación de migración y permite diferenciarla del arranque del servicio backend. Su conveniencia documental no sustituye a la revisión de la configuración efectiva ni a los tests necesarios.

## Decisiones tomadas

### Organización acordada del área

- Las reglas Docker de este alcance se mantienen en `docs/backend/docker/`.
- El histórico se denomina `BACK-DOCKER-fase-completa.md` y el baseline `BACK-DOCKER-BASELINE.md`.
- No incluir aquí reglas sobre modelos, schema o seeds ni sobre targets, ayuda o guardas de Makefile.
- No reproducir el proceso común, la tabla de reparto ni evidencias de otras áreas.

### Orientación aprobada: propuesta pendiente de implantación y validación

- Ejecutar las migraciones mediante una tarea Docker explícita, diferenciada del arranque del backend.
- No ejecutar migraciones automáticamente al iniciar el servicio backend.
- Delimitar la configuración de contenedores necesaria para esa tarea y documentarla sin secretos.

No se afirma que estas orientaciones estén implantadas. Los detalles de invocación y configuración deben revisarse antes de convertirse en reglas definitivas. No se declara implantado `APP_ENV` ni un cambio de selección de entorno. Las restantes materias Docker no forman parte de este baseline.

## Condición de actualización

Incorporar reglas definitivas tras revisión de `api-architect` y QA y comprobación de exactitud documental por el arquitecto, con evidencia del alcance Docker. Conservar el contexto de aprobación y los tests en el histórico, sin duplicarlos aquí. Mantener **BORRADOR NO VALIDADO** mientras no se complete esa revisión.

## Tests ejecutados

No se han ejecutado tests ni comandos Docker en esta intervención. No hay nueva validación de empaquetado, configuración o arranque.

## Riesgos o deuda tecnica

Confundir la orientación con una capacidad ya disponible podría inducir a ejecutar comandos no verificados. El borrador no certifica contenedores, redes ni servicios fuera del alcance de migraciones.

## Relacion con el backend

El baseline prepara criterios para revisar la ejecución controlada de migraciones en contenedores. No altera el arranque ni la configuración del backend.
