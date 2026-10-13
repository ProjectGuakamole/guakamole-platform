# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Documentar la evidencia de Alembic de los puntos 1 y 2 de la auditoría, sin declarar terminada la fase completa.

## Responsabilidad del documento

Este histórico cubre el grafo de migraciones, su evolución estructural y las garantías operativas de downgrade. La selección de configuración operativa se documenta en Makefile y el empaquetado en Docker.

## Estado actual

**EN CURSO — punto 2 aprobado y completado.** Quedan puntos posteriores de la fase; el nombre `fase-completa` identifica el histórico, no el cierre global.

## Cambios realizados

- Se incorporó la evidencia del punto 1: grafo lineal `0001` a `0014`, con `DML0012`, `backfill0013` y `DDL0014` diferenciados.
- Se verificó que el objetivo futuro es concentrar los cambios estructurales en una única migración DDL; no está implementado y no se ha reescrito el historial.
- En el punto 2, Alembic obtiene su conexión exclusivamente de `DATABASE_URL` configurada de forma centralizada; no utiliza una alternativa desde el fichero ini.
- El downgrade histórico rechaza primero la existencia de datos dependientes antes de borrar. La cabecera de migraciones se restauró al head tras la comprobación.

## Justificacion tecnica

La diferenciación entre DML, backfill y DDL permite auditar el efecto de cada revisión sin atribuir a una migración estructural una carga de datos. La precondición de downgrade evita pérdida silenciosa de datos operativos dependientes.

## Decisiones tomadas

- Mantener el grafo histórico sin reescritura durante esta fase.
- Validar como fuente única de conexión de Alembic la configuración central `DATABASE_URL`, sin fallback del ini.
- Mantener como objetivo propuesto del punto 3 la separación estructural y la ausencia de DML en migraciones nuevas.
- El ciclo de vida completo de baseline y Docker sigue pendiente; no se ha implantado una tarea Docker de migraciones en este punto.

## Tests ejecutados

La validación completa finalizó correctamente con **508** pruebas. Incluye comprobación de la base de datos de prueba explícita, del downgrade con datos dependientes y de la restauración al head.

## Riesgos o deuda tecnica

- La consolidación futura en una única DDL no está implementada.
- Falta validar el ciclo completo de baseline y Docker.
- El downgrade protegido requiere que las futuras migraciones preserven precondiciones equivalentes cuando puedan existir datos dependientes.

## Relacion con el backend

Las migraciones siguen evolucionando el esquema del backend de forma trazable. La conexión centralizada y el rechazo seguro del downgrade refuerzan la operación de PostgreSQL sin exponer configuración alternativa.
