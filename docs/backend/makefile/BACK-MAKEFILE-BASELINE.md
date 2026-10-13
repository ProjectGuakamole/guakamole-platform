# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas de la interfaz Makefile validadas en el punto 2 y separar la propuesta del punto 4.

## Responsabilidad del documento

Recoge reglas de selección de entorno, targets, ayuda y guardas. La evidencia detallada permanece en el histórico Makefile.

## Estado actual

**VALIDADO PARCIALMENTE — punto 2 completado.** La fase continúa por los puntos pendientes.

## Cambios realizados

Se validan la selección explícita mediante `ENV_FILE`, la base de pruebas exclusiva, las guardas operativas y la configuración efímera de CI.

## Justificacion tecnica

La interfaz de comandos debe exigir el contexto correcto antes de modificar datos o esquema. Las guardas convierten esa exigencia en una precondición verificable.

## Decisiones tomadas

### Reglas validadas

- Los targets seleccionan `ENV_FILE` explícitamente; no usan una plantilla de entorno como fallback.
- `.env` es local e ignorado por Git; el fichero de ejemplo no es operativo.
- `backend-test-db` usa exclusivamente `TEST_DATABASE_URL`, exige el sufijo `test` y exporta el entorno de pruebas.
- Downgrade se limita a `development` y `test` y mantiene la guarda de migración ante datos dependientes.
- Los seeds tienen guarda de entorno; ayuda y preflight exponen las precondiciones.
- CI genera un `.env.ci` efímero, sin depender del fichero de ejemplo.
- La matriz de `APP_ENV` para `development`, `test`, `staging` y `production` está validada desde el punto de vista de seguridad.

### Propuesta pendiente

- **Punto 4:** definir un target de bootstrap futuro. No está implementado ni validado.

## Tests ejecutados

La calidad y las pruebas unitarias, de base de datos y de seguridad se registran una sola vez en el histórico Makefile.

## Riesgos o deuda tecnica

El bootstrap futuro y las validaciones de ciclo de vida posteriores permanecen pendientes.

## Relacion con el backend

Estas reglas hacen que la operación de la base de datos desde el backend requiera una configuración seleccionada y un entorno autorizado.
