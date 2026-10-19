# Estrategia de Backend CI

## Objetivo

Backend CI separa las validaciones del backend en controles independientes de calidad, tests unitarios, tests con base de datos, tests de seguridad y validación de Docker Compose.

Esta reestructuración se ha realizado antes de implementar OAuth2/JWT para que el equipo tenga visibilidad clara sobre fallos de autenticación, autorización, aislamiento multi-tenant y seguridad cuando empiecen a crecer esos módulos.

## Workflow

El workflow estable del backend vive en:

```text
.github/workflows/backend-ci.yml
```

Existe un único workflow con cinco jobs:

| Job | Check visible en GitHub | Responsabilidad |
| --- | --- | --- |
| `quality` | `Backend Quality` | Lint, formato y tipado estricto. |
| `test-unit` | `Backend Test Unit` | Tests sin servicios externos. |
| `db` | `Backend DB Tests` | Tests que requieren PostgreSQL real. |
| `security` | `Backend Security Tests` | Tests de seguridad que no requieren DB. |
| `compose` | `Backend Docker Compose` | Validación de Compose, roles y migrador explícito. |

## Triggers

El workflow se ejecuta en:

- `pull_request` hacia `main`.
- `push` a estas ramas:
  - `main`
  - `feature/**`
  - `fix/**`
  - `chore/**`
  - `docs/**`
  - `spike/**`
  - `backend/**`
  - `refactor/**`

Por ahora no se usan `path filters`. La decisión prioriza simplicidad en el MVP y evita que un cambio backend quede sin validar por una regla de paths mal definida.

## Jobs

### `quality` — Backend Quality

Responsabilidad: validar calidad estática del backend sin depender de PostgreSQL ni de servicios externos.

Comandos principales:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
```

Dependencias:

- Python 3.12.
- Dependencias backend instaladas con `uv sync --all-groups`.
- No requiere base de datos.

### `test-unit` — Backend Test Unit

Responsabilidad: ejecutar tests unitarios y arquitectónicos que no necesitan PostgreSQL.

Comando principal:

```bash
uv run pytest -m "test_unit or architecture"
```

Dependencias:

- Python 3.12.
- Dependencias backend instaladas con `uv sync --all-groups`.
- No requiere base de datos.

### `db` — Backend DB Tests

Responsabilidad: ejecutar tests de integración y persistencia contra PostgreSQL real y una base de pruebas dedicada.

Comandos principales:

```bash
make backend-test-db ENV_FILE=.env
```

Dependencias:

- Docker Compose.
- `TEST_DATABASE_URL` explícita, local y terminada en `*_test`; se rechazan destinos remotos.
- El target valida el destino y ejecuta un rebaseline IAM antes de los tests; por ello es destructivo únicamente sobre esa base de pruebas dedicada.
- No ejecuta bootstrap ni datos demo.

### `security` — Backend Security Tests

Responsabilidad: ejecutar tests de seguridad que no requieren base de datos, como validaciones de autorización, reglas defensivas o comprobaciones de no exposición de información sensible cuando apliquen sin persistencia.

Comando principal:

```bash
uv run pytest -m "security and not db"
```

Dependencias:

- Python 3.12.
- Dependencias backend instaladas con `uv sync --all-groups`.
- No requiere base de datos.

Los tests de seguridad futuros que necesiten PostgreSQL deberán llevar también el marker `db`; en ese caso se ejecutarán dentro del job `db`, no en este job.

### `compose` — Backend Docker Compose

Responsabilidad: validar que la configuración de Docker Compose renderiza correctamente, que PostgreSQL dispone de los roles requeridos y que el migrador aislado puede aplicar migraciones, consultar la revisión y comprobar que coincide con el `head` empaquetado.

Comandos principales:

```bash
make docker-config ENV_FILE=.env.ci
make postgres-up ENV_FILE=.env.ci
make docker-db-migrate ENV_FILE=.env.ci
make docker-db-current ENV_FILE=.env.ci
make docker-db-check ENV_FILE=.env.ci
make postgres-down ENV_FILE=.env.ci
```

Dependencias:

- Docker Compose.
- PostgreSQL levantado con el `Makefile` del repositorio.
- Entorno temporal de CI con `DOCKER_DATABASE_URL` obligatorio para la aplicación en Compose.
- No ejecuta seed ni downgrade Docker.
- No borra volúmenes. En un volumen existente, el provisionamiento de roles es explícito y confirmado.

## Pytest markers

Markers registrados en `backend/pyproject.toml`:

| Marker | Propósito |
| --- | --- |
| `test_unit` | Tests unitarios sin servicios externos. |
| `integration` | Tests con integración entre componentes, API, DB o servicios. |
| `db` | Tests que requieren PostgreSQL real. |
| `security` | Tests de seguridad, RBAC, auth y aislamiento multi-tenant. |
| `architecture` | Tests de límites arquitectónicos y dependencias permitidas. |
| `slow` | Tests lentos o de alto coste, para poder aislarlos si hace falta. |

## Estructura de tests

La estructura objetivo del backend es:

```text
backend/tests/
├── unit/
├── integration/
├── security/
└── architecture/
```

La carpeta ayuda a localizar los tests, pero la selección en CI se hace mediante markers. Si un archivo mezcla responsabilidades, se deben marcar funciones concretas.

## Makefile

Comandos principales relacionados con Backend CI:

| Comando | Uso |
| --- | --- |
| `make backend-quality` | Ejecuta Ruff, comprobación de formato y mypy strict. |
| `make backend-test-unit` | Ejecuta `pytest -m "test_unit or architecture"`. |
| `make backend-test-db` | Ejecuta `pytest -m "db or integration"`; requiere PostgreSQL disponible y migrado. |
| `make backend-test-security` | Ejecuta `pytest -m "security and not db"`. |
| `make backend-test` | Agregador de quality, unit, DB y security. Requiere PostgreSQL disponible para la parte DB. |
| `make backend-bootstrap` | Carga catálogos IAM aprobados en un destino dedicado y protegido. Debe ejecutarse antes de la demo. |
| `make backend-seed-demo CONFIRM=SEED_DEMO_IAM` | Reemplaza exclusivamente datos demo contenidos; requiere `DEMO_SEED_PASSWORD` local no versionada. |
| `make backend-seed-clear CONFIRM=CLEAR_DEMO_IAM` | Elimina exclusivamente datos demo contenidos. |
| `make backend-rebaseline-iam CONFIRM=REBASELINE_IAM` | Reconstruye IAM en un destino local seguro de test o desarrollo. |
| `make docker-db-migrate` | Aplica `head` con el perfil Docker `migration`. |
| `make docker-db-current` | Consulta la revisión mediante el migrador aislado. |
| `make docker-db-check` | Verifica que la revisión Alembic actual coincide con el `head` empaquetado, sin mutar el esquema ni ejecutar `alembic check` (autogeneración o comparación de deriva). |
| `make docker-deploy` | Flujo canónico: migra y levanta el stack base. |

## Docker y PostgreSQL

- Los jobs `db` y `compose` usan Docker Compose y el `Makefile` del repositorio.
- El job `compose` usa el perfil explícito `migration`; no ejecuta Alembic directamente desde el host con `DATABASE_URL`.
- El orden del job `compose` es `docker-db-migrate`, `docker-db-current` y `docker-db-check`. Este último valida únicamente revisión actual frente a `head` empaquetado; deliberadamente no invoca la comprobación de autogeneración o deriva de Alembic.
- El migrador requiere `MIGRATION_DATABASE_URL`, `MIGRATION_ALLOWED_HOSTS`, `MIGRATION_ALLOWED_DATABASES` y `MIGRATION_EXPECTED_DB_USER`. Los valores se inyectan desde el entorno de CI y no se registran.
- Migrador y aplicación usan identidades distintas. La imagen es la misma y se ejecuta sin privilegios root.
- `docker-compose.yml` conserva `backend_internal` con `internal: true` y no expone PostgreSQL, backend ni frontend; solo publica Nginx.
- CI usa obligatoriamente `docker-compose.local.yml`, igual que el desarrollo local: publica los puertos necesarios y redefine `backend_internal` con `internal: false`. El override no forma parte de staging.
- `DOCKER_DATABASE_URL` debe estar definido en el entorno temporal de CI para que el servicio backend en Compose pueda conectar con PostgreSQL; su valor no se registra.
- No se usa el servicio `postgres` de GitHub Actions.
- En CI no se ejecuta `docker compose down -v`.
- En CI no se borran volúmenes explícitamente.
- El cleanup estándar de CI es `make postgres-down ENV_FILE=.env.ci`.

Los runners de GitHub son efímeros, por lo que no necesitamos destruir volúmenes manualmente para garantizar limpieza entre ejecuciones.

## Bootstrap, demo y guardas de destino

El orden operativo es estricto: Alembic o rebaseline, `backend-bootstrap` y, solo después, `backend-seed-demo`. El bootstrap resuelve los catálogos aprobados por sus claves naturales y les asigna identificadores públicos estándar, válidos y deterministas. El seed y el clear no modifican catálogos y se detienen si no pueden atribuir los datos y dependencias al espacio demo gestionado.

Los targets de bootstrap, demo y rebaseline aplican sus guardas de destino. El migrador Docker valida su URL e identidad mediante allowlist; la aplicación recibe únicamente su configuración permitida. Los comandos demo requieren sus tokens Make explícitos y no se ejecutan automáticamente en CI. No se documentan ni versionan secretos.

## Ejecución local recomendada

### Sin base de datos

```bash
make backend-quality
make backend-test-unit
make backend-test-security
```

### Con base de datos

```bash
make backend-test-db ENV_FILE=.env
make backend-test ENV_FILE=.env
```

Las ejecuciones DB deben ser estrictamente secuenciales: cada una reconstruye destructivamente el IAM de la base de pruebas. No se deben lanzar dos `backend-test-db` ni un `backend-test` concurrente contra el mismo destino.

## Evidencia del punto 5

- `docker compose config` fue válido, se provisionaron los roles y se aplicó el baseline con `docker-db-migrate`.
- Una repetición quedó en `already_at_head`; `docker-db-current` y `docker-db-check` finalizaron correctamente.
- Los tests de migración disponibles dieron **21 passed** y mypy finalizó correctamente.
- No se dispone de un recuento actual verificable de la suite completa y no se declara uno.
- Health y readiness devolvieron HTTP 200 dentro del contenedor backend. El override local de Compose fue validado: PostgreSQL publica el puerto `5432` y el acceso TCP mediante `localhost` funciona. Esta evidencia corresponde exclusivamente al entorno local; no implica que staging exponga la base de datos.

## Required checks objetivo

Cuando el workflow esté validado, la protección de `main` debería exigir estos checks:

```text
Backend Quality
Backend Test Unit
Backend DB Tests
Backend Security Tests
Backend Docker Compose
```

## Riesgos y decisiones

- Ejecutar Docker Compose en CI puede ser más lento, pero valida un camino más parecido al entorno real del proyecto.
- No se usan `path filters` por simplicidad durante el MVP.
- Los tests de seguridad con PostgreSQL deberán marcarse como `security` y `db`; se ejecutarán en el job DB por la expresión actual `security and not db` del job de seguridad.
- OAuth2/JWT se beneficiará de checks separados porque los fallos de calidad, unitarios, DB, seguridad y Compose aparecerán de forma independiente.
