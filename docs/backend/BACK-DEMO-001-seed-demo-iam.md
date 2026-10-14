# BACK-DEMO-001 — Bootstrap y demo IAM controlados

## Objetivo

Preparar catálogos IAM aprobados y datos demo ficticios sin introducir DML en migraciones Alembic, sin usar el destino general de la aplicación y sin borrar datos ajenos a la demo gestionada.

## Cambios realizados

El orden es obligatorio: tras aplicar Alembic en un destino local dedicado, debe ejecutarse el bootstrap y solo después puede cargarse la demo. La interfaz no usa `DATABASE_URL`: usa `TEST_DATABASE_URL` con `APP_ENV=test`, o las variables dedicadas de desarrollo local terminadas en `_dev` o `_development`.

```bash
make backend-bootstrap
make backend-seed-demo CONFIRM=SEED_DEMO_IAM
```

La semilla demo necesita además `DEMO_SEED_PASSWORD` configurada localmente y no versionada. Para eliminar exclusivamente la demo que el proceso puede demostrar que gestiona:

```bash
make backend-seed-clear CONFIRM=CLEAR_DEMO_IAM
```

El rebaseline es una operación independiente, total y destructiva, restringida a test o desarrollo local seguro:

```bash
make backend-rebaseline-iam CONFIRM=REBASELINE_IAM
```

Tras el rebaseline hay que ejecutar de nuevo `make backend-bootstrap` antes de cargar la demo.

## Justificacion tecnica

Separar DDL, catálogos canónicos y datos demo mantiene el baseline reproducible y reduce el alcance de una operación de demostración. Las URLs dedicadas, locales y con sufijo seguro impiden que bootstrap, demo o rebaseline seleccionen accidentalmente la base operativa indicada por `DATABASE_URL`.

## Decisiones tomadas

- Los datos son ficticios y no productivos.
- No usar en staging, producción ni en ninguna base de datos con información a conservar.
- El seed y el clear no modifican los catálogos aprobados. Antes de reemplazar o limpiar, el proceso resuelve las entidades mediante claves naturales y comprueba que las organizaciones, usuarios, departamentos, relaciones, identificadores públicos y dependencias pertenecen al espacio demo esperado; ante cualquier discrepancia falla sin limpiar.
- Los emails terminan en `.demo.test`, los slugs empiezan por `demo-` y los nombres demo relevantes empiezan por `Demo `.
- El bootstrap inserta los catálogos y la geografía IAM aprobados mediante resolución por claves naturales, identificadores públicos estándar, válidos y deterministas, y validación de colisiones; es idempotente para valores ya canónicos.
- URLs locales de referencia: API `http://localhost:8000`, Swagger `http://localhost:8000/docs`, frontend `http://localhost:3000` y, si se usa Vite en desarrollo, `http://localhost:5173`.

## Tests ejecutados

- `make backend-quality`: Ruff y comprobación de formato correctos sobre **164** ficheros; mypy en modo estricto correcto sobre **163** ficheros fuente.
- `make backend-test-unit`: **316 passed, 100 deselected**.
- `make backend-test-db`: **78 passed, 338 deselected** y **62 advertencias** conocidas de Alembic relacionadas con `path_separator`.
- `make backend-test-security`: **22 passed, 394 deselected**.
- `make backend-test`: **416 passed, 62 warnings**.

Los comandos que reconstruyen o validan la base de datos de pruebas deben ejecutarse secuencialmente: el rebaseline es destructivo sobre la base local de pruebas. No se ha realizado validación manual de Swagger.

## Riesgos o deuda tecnica

El rebaseline borra por completo el esquema IAM y su estado de Alembic en el destino autorizado. La demo se detiene ante datos o dependencias no reconocidos, por lo que un cambio futuro de modelo puede requerir ampliar explícitamente sus contratos de contención.

## Relacion con el backend

La documentación describe la operación segura de la persistencia IAM del backend: Alembic define el esquema, bootstrap carga catálogos aprobados y la demo aporta únicamente datos controlados para desarrollo y pruebas locales.
