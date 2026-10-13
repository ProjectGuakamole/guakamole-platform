# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas Docker validadas en el punto 2 y distinguirlas de la operación de migraciones pendiente.

## Responsabilidad del documento

Recoge únicamente reglas de Compose y contexto de construcción del backend dentro de este alcance.

## Estado actual

**VALIDADO PARCIALMENTE — punto 2 completado.** La fase continúa por puntos posteriores.

## Cambios realizados

Se validan la lista permitida explícita de configuración para Compose y la exclusión del material local no necesario mediante `.dockerignore` en `backend/`.

## Justificacion tecnica

Estas reglas reducen la exposición de configuración y el contenido innecesario de la imagen sin afectar a los archivos de ejecución requeridos.

## Decisiones tomadas

### Reglas validadas

- Compose configura el backend mediante una allowlist explícita, sin cargar el entorno completo ni incluir credenciales de PostgreSQL o configuración de pruebas.
- El contexto de `backend/` excluye archivos de entorno, Git, cachés, entornos virtuales y pruebas, y conserva aplicación, Alembic, `alembic.ini` y scripts.

### Propuestas pendientes

- **Punto 5:** crear una tarea Docker explícita para migraciones.
- Mantener prohibida la ejecución automática de migraciones al arrancar el backend hasta que dicha tarea se diseñe y valide.

## Tests ejecutados

La validación de renderizado se conserva en el histórico Docker. Este baseline no duplica evidencias.

## Riesgos o deuda tecnica

La tarea de migración y su validación de ciclo de vida siguen pendientes.

## Relacion con el backend

Las reglas reducen qué configuración y qué ficheros acompañan al backend en contenedor.
