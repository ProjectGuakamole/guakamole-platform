# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evidencia de los puntos 2 y 3 sobre la selección de configuración, los targets de base de datos y sus guardas operativas.

## Responsabilidad del documento

Este histórico es la fuente de detalle de configuración de la fase. No reproduce el grafo Alembic ni el contexto de construcción Docker.

## Estado actual

**Punto 4 documentado.** No se declara la implementación global como terminada.

## Cambios realizados

- Los targets Makefile seleccionan `ENV_FILE` de forma explícita y usan `.env` como fichero local.
- `backend-test-db` exige `TEST_DATABASE_URL`, verifica que corresponde a una base local de pruebas mediante el sufijo `*_test`, rechaza hosts remotos, reconstruye destructivamente el baseline IAM confirmado y solo después ejecuta `pytest -m "db or integration"`; no admite fallback.
- Los downgrades están limitados a los entornos `development` y `test`, además de respetar la guarda de migración para datos dependientes.
- El script de seeds incorpora una guarda de entorno.
- Se actualizaron ayuda y preflight para reflejar las precondiciones operativas.
- CI emplea un `.env.ci` efímero; no utiliza el fichero de ejemplo.
- El rebaseline del punto 3 es destructivo y requiere confirmación explícita. En pruebas solo puede usar `TEST_DATABASE_URL` local con destino `*_test`; en desarrollo requiere `REBASELINE_DEVELOPMENT_DATABASE_URL` separado, local y con destino `*_dev` o `*_development`. Se rechazan hosts remotos.
- No se documentan nuevos targets: el punto 3 no crea comandos Makefile.
- Se incorporan `backend-bootstrap`, `backend-seed-demo`, `backend-seed-clear` y `backend-rebaseline-iam` para separar catálogo aprobado, datos demo y reconstrucción total. Tras Alembic o rebaseline, bootstrap resuelve los catálogos por claves naturales y crea los que falten con identificadores públicos estándar, válidos y deterministas; debe completarse antes de la demo. Seed y clear no modifican catálogos.
- Los dos comandos demo requieren los tokens Make `CONFIRM=SEED_DEMO_IAM` y `CONFIRM=CLEAR_DEMO_IAM`; el rebaseline requiere `CONFIRM=REBASELINE_IAM`.
- Estos comandos no usan `DATABASE_URL`: en test usan `TEST_DATABASE_URL` y en desarrollo requieren una URL dedicada, local y con sufijo seguro.

## Justificacion tecnica

La selección explícita elimina ambigüedad entre configuración local, pruebas y CI. La base de pruebas obligatoria y las guardas de downgrade y seeds previenen operaciones destructivas o de carga sobre un entorno no autorizado.

El `.env` local está ignorado por Git. El fichero de ejemplo es una plantilla no operativa y no aporta fallback; `APP_ENV` no contiene valores en esta documentación. Se validó la matriz de seguridad de `APP_ENV` para `development`, `test`, `staging` y `production`.

## Decisiones tomadas

- Requerir `ENV_FILE` explícito en la interfaz Makefile y evitar cualquier fallback a plantillas.
- Reservar `TEST_DATABASE_URL` para operaciones de prueba y comprobar que su destino local termina en `*_test` antes de usarlo.
- Permitir downgrade solo en `development` y `test`, sujeto a la guarda de datos de la migración.
- Mantener las guardas de seeds y los checks previos como parte de la interfaz operativa.
- Mantener bootstrap y demo como operaciones separadas del baseline, sin introducir DML en Alembic.
- No reintroducir un seed genérico o DML en Alembic: el bootstrap y la demo son operaciones separadas.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de deprecación de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas. No se documentan validaciones manuales adicionales.

## Riesgos o deuda tecnica

- La orquestación Docker de baseline/rebaseline queda fuera de este cambio.

## Relacion con el backend

Los comandos operativos del backend seleccionan explícitamente su configuración y reducen el riesgo de ejecutar pruebas, downgrades o seeds contra una base no permitida.
