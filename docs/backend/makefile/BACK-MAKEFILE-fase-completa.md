# backend/audit/BACK-DB-MIGRATIONS-AUDIT-001

## Objetivo

Registrar la evidencia de los puntos 2 y 3 sobre la selección de configuración, los targets de base de datos y sus guardas operativas.

## Responsabilidad del documento

Este histórico es la fuente de detalle de configuración de la fase. No reproduce el grafo Alembic ni el contexto de construcción Docker.

## Estado actual

**VALIDADO — punto 3 aprobado y completado.** No se declara la implementación global como terminada.

## Cambios realizados

- Los targets Makefile seleccionan `ENV_FILE` de forma explícita y usan `.env` como fichero local.
- `backend-test-db` exige `TEST_DATABASE_URL`, verifica que corresponde a una base local de pruebas mediante el sufijo `*_test`, rechaza hosts remotos, reconstruye destructivamente el baseline IAM confirmado y solo después ejecuta `pytest -m "db or integration"`; no admite fallback.
- Los downgrades están limitados a los entornos `development` y `test`, además de respetar la guarda de migración para datos dependientes.
- El script de seeds incorpora una guarda de entorno.
- Se actualizaron ayuda y preflight para reflejar las precondiciones operativas.
- CI emplea un `.env.ci` efímero; no utiliza el fichero de ejemplo.
- El rebaseline del punto 3 es destructivo y requiere confirmación explícita. En pruebas solo puede usar `TEST_DATABASE_URL` local con destino `*_test`; en desarrollo requiere `REBASELINE_DEVELOPMENT_DATABASE_URL` separado, local y con destino `*_dev` o `*_development`. Se rechazan hosts remotos.
- No se documentan nuevos targets: el punto 3 no crea comandos Makefile.

## Justificacion tecnica

La selección explícita elimina ambigüedad entre configuración local, pruebas y CI. La base de pruebas obligatoria y las guardas de downgrade y seeds previenen operaciones destructivas o de carga sobre un entorno no autorizado.

El `.env` local está ignorado por Git. El fichero de ejemplo es una plantilla no operativa y no aporta fallback; `APP_ENV` no contiene valores en esta documentación. Se validó la matriz de seguridad de `APP_ENV` para `development`, `test`, `staging` y `production`.

## Decisiones tomadas

- Requerir `ENV_FILE` explícito en la interfaz Makefile y evitar cualquier fallback a plantillas.
- Reservar `TEST_DATABASE_URL` para operaciones de prueba y comprobar que su destino local termina en `*_test` antes de usarlo.
- Permitir downgrade solo en `development` y `test`, sujeto a la guarda de datos de la migración.
- Mantener las guardas de seeds y los checks previos como parte de la interfaz operativa.
- Mantener el preflight de `pgcrypto` y la sincronización de identidades como requisitos del seed, sin asumir que los resuelva un target nuevo.
- No implementar un target de bootstrap en este cambio.

## Tests ejecutados

- `make backend-quality`: **OK** (`ruff`, formato sobre **159 archivos** y `mypy` sobre **158 archivos fuente**).
- `make backend-test-unit`: **308 passed, 70 deselected**.
- `make backend-test-db`: **48 passed, 330 deselected** y **2 advertencias de Alembic**.
- `make backend-test-security`: **22 passed, 356 deselected**.
- Suite completa con `TEST_DATABASE_URL` local dedicada: **378 passed** y **2 advertencias de Alembic**.
- Ejecución directa de `pytest` sin URL de pruebas: **330 passed, 48 skipped**.

`backend-test-db` exige la URL, rechaza destinos remotos y rebaselinea destructivamente una base local `*_test` antes de ejecutar las pruebas. Con ello, un esquema de migraciones anteriores no provoca deriva de ordenación en la validación PostgreSQL. La ejecución directa de `pytest` no recibe la URL y omite las 48 pruebas de base de datos. Las advertencias de Alembic son seguimiento no bloqueante; no se ha aplicado ni se presume una corrección.

## Riesgos o deuda tecnica

- No existe un target de bootstrap en este alcance.
- La orquestación Docker de baseline/rebaseline queda fuera de este cambio.

## Relacion con el backend

Los comandos operativos del backend seleccionan explícitamente su configuración y reducen el riesgo de ejecutar pruebas, downgrades o seeds contra una base no permitida.
