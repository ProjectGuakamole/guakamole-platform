# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Precisar el alcance de la comprobación Docker de migraciones del punto 5.

## Cambios realizados

- Se documenta que `docker-db-check` valida que la revisión Alembic actual coincide con el `head` empaquetado.
- Se aclara que no invoca deliberadamente `alembic check`, por lo que no ejecuta autogeneración ni comparación de deriva entre modelos ORM y esquema.
- Se deja constancia de que el job Compose de CI ejecuta, en este orden, `docker-db-migrate`, `docker-db-current` y `docker-db-check`.

## Justificacion tecnica

La validación de revisión desplegada y la detección de deriva ORM/esquema son controles distintos. El flujo operativo Docker verifica que la base queda en la revisión empaquetada sin ampliar su responsabilidad a la generación o comparación de migraciones.

## Decisiones tomadas

Se mantiene `docker-db-check` como una comprobación no mutante de revisión actual frente a `head`. La detección de deriva mediante Alembic queda fuera de este comando.

## Tests ejecutados

No se han ejecutado tests para este ajuste exclusivamente documental. Se ha revisado el diff resultante.

## Riesgos o deuda tecnica

El job Compose no detecta por sí mismo deriva entre metadatos ORM y esquema al no ejecutar `alembic check`. Si se requiere ese control, deberá incorporarse como validación separada y explícita.

## Relacion con el backend

La documentación delimita el contrato de migraciones que prepara el esquema consumido por FastAPI y evita atribuir al pipeline CI una comprobación de deriva que no realiza.
