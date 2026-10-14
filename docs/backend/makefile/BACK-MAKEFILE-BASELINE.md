# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Consolidar las reglas de la interfaz Makefile validadas tras el punto 3.

## Responsabilidad del documento

Recoge reglas de selección de entorno, targets, ayuda y guardas. La evidencia detallada permanece en el histórico Makefile.

## Estado actual

**Punto 4 documentado.**

## Cambios realizados

Se mantienen las reglas del punto 2 y las guardas del rebaseline. El punto 4 añade los targets explícitos de bootstrap y demo, y depreca el target histórico de seed genérico.

## Justificacion tecnica

La interfaz de comandos debe exigir el contexto correcto antes de modificar datos o esquema. Las guardas convierten esa exigencia en una precondición verificable.

## Decisiones tomadas

### Reglas validadas

- Los targets seleccionan `ENV_FILE` explícitamente; no usan una plantilla de entorno como fallback.
- `.env` es local e ignorado por Git; el fichero de ejemplo no es operativo.
- `backend-test-db` usa exclusivamente `TEST_DATABASE_URL`, exige una base local con sufijo `*_test`, rechaza hosts remotos, reconstruye destructivamente el baseline IAM con confirmación explícita y después ejecuta toda la suite `db or integration`.
- Downgrade se limita a `development` y `test` y mantiene la guarda de migración ante datos dependientes.
- Los seeds tienen guarda de entorno; ayuda y preflight exponen las precondiciones.
- CI genera un `.env.ci` efímero, sin depender del fichero de ejemplo.
- La matriz de `APP_ENV` para `development`, `test`, `staging` y `production` está validada desde el punto de vista de seguridad.
- El rebaseline exige confirmación explícita. En `test` solo se admite `TEST_DATABASE_URL` local dirigido a `*_test`; en desarrollo se exige `REBASELINE_DEVELOPMENT_DATABASE_URL` independiente, local y dirigido a `*_dev` o `*_development`. Se rechazan hosts remotos.
- El flujo histórico de seed con preflight de `pgcrypto` y sincronización de identidades queda sustituido por bootstrap y demo controlada.
- El punto 3 no implementa targets Makefile adicionales.
- Tras Alembic o rebaseline, `backend-bootstrap` resuelve únicamente los catálogos IAM aprobados mediante claves naturales y crea los que falten con identificadores públicos estándar, válidos y deterministas, en un destino dedicado y validado; debe completarse antes de la demo.
- `backend-seed-demo` y `backend-seed-clear` exigen los tokens Make `CONFIRM=SEED_DEMO_IAM` y `CONFIRM=CLEAR_DEMO_IAM`, respectivamente; el seed además requiere una contraseña demo no versionada. Ninguno modifica catálogos.
- `backend-rebaseline-iam` exige `CONFIRM=REBASELINE_IAM` y reconstruye por completo IAM en un destino de test o desarrollo local validado.

Los comandos de bootstrap, demo y rebaseline no usan `DATABASE_URL`; en pruebas usan `TEST_DATABASE_URL` y en desarrollo sus variables dedicadas.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de deprecación de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas.

## Riesgos o deuda tecnica

Los comandos destructivos siguen requiriendo una base local aislada y confirmación explícita. La operación demo rechaza datos o dependencias que no pueda atribuir de forma segura a su espacio gestionado.

## Relacion con el backend

Estas reglas hacen que la operación de la base de datos desde el backend requiera una configuración seleccionada y un entorno autorizado.
