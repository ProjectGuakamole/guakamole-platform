# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Preparar el baseline exclusivo del área Alembic para distinguir las reglas propuestas de las que se validen durante la fase coordinada `BACK-DB-MIGRATIONS-AUDIT-001`.

## Responsabilidad del documento

Recoger únicamente reglas del área: migraciones Alembic, modelos, schema, bootstrap y seeds. No sustituye al histórico de decisiones y evidencias ni define reglas de Docker o Makefile.

## Estado actual

**BORRADOR NO VALIDADO.** No constituye una certificación del código existente ni un baseline definitivo. Esta intervención no implanta reglas, no ejecuta migraciones y no reanuda el punto 2.

## Cambios realizados

Se crea este borrador con alcance, organización y criterios iniciales. No se modifica ningún modelo, schema, revisión Alembic, bootstrap o seed. No se incorporan resultados de tests anteriores como validación actual.

## Justificacion tecnica

Separar evolución estructural y carga de datos facilita identificar qué operación transforma el esquema y cuál introduce datos. Una regla escrita no demuestra que las revisiones existentes ya la satisfagan.

## Decisiones tomadas

### Organización acordada del área

- Las reglas de Alembic, modelos, schema, bootstrap y seeds se mantienen en `docs/backend/alembic/`.
- El histórico del área se denomina `BACK-DB-MIGRATIONS-fase-completa.md`; este baseline se denomina `BACK-DB-MIGRATIONS-BASELINE.md`.
- El baseline contiene reglas, no el proceso coordinado ni copias de evidencias o explicaciones de otras áreas.

### Orientación aprobada: propuesta pendiente de implantación y validación

- Tratar Alembic como mecanismo de evolución estructural explícita, sin incorporar seeds como parte de esa operación estructural.
- Diferenciar bootstrap de estructura y carga de seeds, documentando qué responsabilidad corresponde a cada uno.
- Revisar la coherencia entre modelos y schema antes de considerar definitiva una regla de migración.

Estas orientaciones no acreditan una separación ya implantada ni autorizan a reescribir migraciones históricas. La aplicación concreta y sus efectos sobre las revisiones existentes están pendientes de revisión técnica y autorización. No se afirma que `APP_ENV` ni una transición de entorno estén implantados.

## Condición de actualización

Incorporar reglas definitivas solo tras revisión de `api-architect` y QA, evidencia aplicable y revisión de exactitud documental por el arquitecto. Mantener identificadas las propuestas pendientes; registrar el contexto y los resultados en el histórico del área, no duplicarlos aquí. Hasta entonces, conservar el estado **BORRADOR NO VALIDADO**.

## Tests ejecutados

No se han ejecutado tests ni comandos Alembic en esta intervención. No existe nueva evidencia que permita validar este baseline.

## Riesgos o deuda tecnica

El comportamiento actual de migraciones y seeds no se ha auditado en esta tarea. Adoptar el borrador como regla definitiva sin revisión ocultaría posibles diferencias con el historial existente.

## Relacion con el backend

El baseline delimita los criterios pendientes para la evolución de la persistencia. No cambia la base de datos ni el comportamiento de inicialización del backend.
