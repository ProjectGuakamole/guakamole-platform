# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Establecer el histórico del área Docker dentro de la misma fase coordinada `BACK-DB-MIGRATIONS-AUDIT-001`, limitado al empaquetado y ejecución de migraciones y a la configuración de contenedores necesaria.

## Responsabilidad del documento

Conservar hallazgos, evidencia y decisiones sobre cómo se prepara y ejecuta la tarea de migración en contenedores. No documenta el contenido de las revisiones Alembic ni las reglas de targets Makefile. Tampoco promete una auditoría completa de Docker, redes, servicios o despliegues ajenos a este alcance.

## Estado actual

**EN CURSO — organización documental únicamente.** `fase-completa` es el nombre del histórico permanente, no un veredicto de cierre. El baseline Docker se inicia como **BORRADOR NO VALIDADO**.

El punto 2 permanece detenido. No se dispone de nuevas evidencias de implantación ni de ejecución de migraciones en Docker en esta intervención.

## Cambios realizados

Se crean el histórico y el baseline en `docs/backend/docker/`. El histórico existente `docs/backend/backend-docker-compose-integration.md` permanece intacto en la raíz. Su validación anterior no acredita el resultado de esta fase; cualquier consolidación requiere una tarea futura autorizada.

## Justificacion tecnica

El mecanismo de ejecución en contenedores tiene responsabilidades diferentes del contenido de una migración. Documentarlo por separado permite revisar su configuración y forma de invocación sin atribuirle cambios de schema ni ampliar indebidamente el alcance de la auditoría.

## Decisiones tomadas

### Ubicación y responsabilidad específicas

- El empaquetado y la ejecución Docker de migraciones y la configuración de contenedores asociada se documentan en `docs/backend/docker/`.
- `BACK-DOCKER-fase-completa.md` conserva evidencia y decisiones; `BACK-DOCKER-BASELINE.md` recoge solo reglas del área cuando se validen.
- Una explicación sobre estructura o seeds corresponde al área Alembic; una explicación sobre targets, ayuda o guardas de comandos corresponde al área Makefile.
- Para cambios mixtos se registra aquí solo la parte Docker, sin duplicar explicaciones técnicas ni tests conservados por otra área.

La coordinación pertenece a la fase y backlog únicos de la rama indicada en el título. El acuerdo común está registrado en la sección «Organización documental del proceso» del histórico Alembic; aquí no se reproduce la tabla ni el flujo completo.

Como orientación aprobada, pendiente de implantación y validación en esta fase, se plantea ejecutar migraciones mediante una tarea explícita y no mediante arranque automático del backend. No se declara que esa separación ya esté implantada. Tampoco se afirma implantación de `APP_ENV` ni transición de entorno.

## Condición de actualización

Actualizar este histórico solo cuando un punto autorizado aporte evidencia, hallazgos o decisiones del alcance Docker descrito. Registrar una única vez las comprobaciones propias del área y distinguir propuestas de resultados. Las reglas definitivas pasarán al baseline tras revisión técnica, QA y revisión de exactitud documental por el arquitecto.

## Tests ejecutados

No se han ejecutado comandos Docker, construcciones de imágenes, arranques de contenedores ni migraciones en esta intervención. No se certifica la configuración actual ni se trasladan tests históricos a esta fase.

## Riesgos o deuda tecnica

- El comportamiento actual de arranque y ejecución de migraciones no se ha validado en esta tarea.
- La configuración Docker ajena a las migraciones queda fuera del alcance; este documento no acredita su seguridad ni funcionamiento general.
- La consolidación de históricos y el cierre técnico de la fase quedan pendientes de tareas autorizadas.

## Relacion con el backend

Este histórico delimita cómo documentar la futura revisión de ejecución de migraciones en contenedores. No modifica imágenes, Compose, configuración ni arranque del backend.
