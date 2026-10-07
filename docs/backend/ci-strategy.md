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
| `compose` | `Backend Docker Compose` | Validación de Compose y migraciones básicas. |

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

Responsabilidad: ejecutar tests de integración y persistencia contra PostgreSQL real gestionado con Docker Compose del proyecto.

Comandos principales:

```bash
make postgres-up ENV_FILE=.env.example
make db-upgrade ENV_FILE=.env.example
cd backend && uv run pytest -m "db or integration"
make postgres-down ENV_FILE=.env.example
```

Dependencias:

- Docker Compose.
- PostgreSQL levantado con el `Makefile` del repositorio.
- Migraciones Alembic aplicadas.
- No ejecuta seed.

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

Responsabilidad: validar que la configuración de Docker Compose renderiza correctamente y que PostgreSQL permite aplicar y consultar migraciones.

Comandos principales:

```bash
make docker-config ENV_FILE=.env.example
make postgres-up ENV_FILE=.env.example
make db-upgrade ENV_FILE=.env.example
make db-current ENV_FILE=.env.example
make postgres-down ENV_FILE=.env.example
```

Dependencias:

- Docker Compose.
- PostgreSQL levantado con el `Makefile` del repositorio.
- No ejecuta seed.
- No borra volúmenes.

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
| `make backend-seed` | Comando destructivo para insertar seed demo tras truncar tablas gestionadas. |
| `make backend-seed-clear` | Comando destructivo para truncar tablas gestionadas sin reinsertar datos. |

## Docker y PostgreSQL

- Los jobs `db` y `compose` usan Docker Compose y el `Makefile` del repositorio.
- No se usa el servicio `postgres` de GitHub Actions.
- En CI no se ejecuta `docker compose down -v`.
- En CI no se borran volúmenes explícitamente.
- El cleanup estándar de CI es `make postgres-down ENV_FILE=.env.example`.

Los runners de GitHub son efímeros, por lo que no necesitamos destruir volúmenes manualmente para garantizar limpieza entre ejecuciones.

## Seeds destructivos

`backend-seed` y `backend-seed-clear` son comandos destructivos: truncan tablas gestionadas del backend antes de insertar o limpiar datos demo.

No se ejecutan automáticamente en CI. Solo deben ejecutarse manualmente en local o en entornos de demo contra una base de datos que se pueda truncar sin riesgo.

## Ejecución local recomendada

### Sin base de datos

```bash
make backend-quality
make backend-test-unit
make backend-test-security
```

### Con base de datos

```bash
make postgres-up ENV_FILE=.env.example
make db-upgrade ENV_FILE=.env.example
make backend-test-db
make backend-test
make postgres-down ENV_FILE=.env.example
```

Se recomienda ejecutar `make postgres-down ENV_FILE=.env.example` al finalizar las pruebas locales con PostgreSQL como limpieza operativa no destructiva. Este comando no borra volúmenes y no equivale a ejecutar `docker compose down -v`.

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
