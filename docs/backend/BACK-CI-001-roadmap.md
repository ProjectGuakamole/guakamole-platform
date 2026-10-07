# BACK-CI-001 — Roadmap operativo para reestructurar Backend CI

## Objetivo

Reestructurar el CI backend antes de OAuth2/JWT para separar responsabilidades, mejorar diagnóstico de fallos y alinear GitHub Actions, pytest markers, Makefile y Docker Compose.

## Decisiones cerradas

- Usar un único workflow: `.github/workflows/backend-ci.yml`.
- Dividirlo en 5 jobs:
  - `quality`
  - `test-unit`
  - `db`
  - `security`
  - `compose`
- Reorganizar carpetas de tests.
- Añadir pytest markers:
  - `test_unit`
  - `integration`
  - `db`
  - `security`
  - `architecture`
  - `slow`
- No usar path filters por ahora.
- No ejecutar `backend-seed` ni `backend-seed-clear` en CI.
- No añadir comandos `docker-cleanup`/`docker-destroy`.
- Documentación final estable posterior en `docs/backend/ci-strategy.md`.
- Ejecutar esta tarea antes de OAuth2/JWT.

## Task 0 — Preparación de issue y rama

### Subtareas

- Crear issue GitHub: `BACK-CI-001 Reestructurar Backend CI por jobs, markers y Docker Compose`.
- Crear rama desde `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/BACK-CI-001-backend-ci-restructure
```

- Revisar baseline:

```bash
git status
make backend-test
```

### Criterios de aceptación

- Issue creada.
- Rama creada desde `main` actualizado.
- Baseline conocido.

## Task 1 — Añadir pytest markers

### Subtareas

- Añadir markers en `backend/pyproject.toml`:

```toml
markers = [
  "test_unit: tests unitarios sin servicios externos",
  "integration: tests con DB/API/servicios",
  "db: tests que requieren PostgreSQL real",
  "security: tests de seguridad, RBAC, auth y tenant isolation",
  "architecture: tests de límites arquitectónicos",
  "slow: tests lentos o de alto coste",
]
```

- Validar markers:

```bash
cd backend && uv run pytest --markers
```

### Criterios de aceptación

- Pytest reconoce todos los markers.
- No hay warnings de markers desconocidos.

## Task 2 — Reorganizar carpetas de tests

### Estructura objetivo

```text
backend/tests/
├── unit/
├── integration/
├── security/
└── architecture/
```

### Subtareas

- Mover tests unitarios a `tests/unit/`.
- Mover tests DB/integration a `tests/integration/`.
- Mover tests security a `tests/security/`.
- Mantener tests arquitectónicos en `tests/architecture/`.
- Corregir imports/rutas si aparecen.

### Criterios de aceptación

```bash
make backend-test
```

pasa tras mover tests.

## Task 3 — Clasificar tests con markers

### Clasificación inicial

- `test_unit`: tests sin DB ni servicios externos.
- `db` + `integration`: repository, migraciones y tests que requieren PostgreSQL real.
- `security`: RBAC, tenant isolation, auditoría segura, no exposición de datos sensibles.
- `architecture`: límites arquitectónicos.

### Subtareas

- Añadir `pytestmark` por archivo cuando aplique.
- Usar markers por función si el archivo mezcla tipos.
- Ejecutar:

```bash
cd backend && uv run pytest -m "test_unit"
cd backend && uv run pytest -m "db or integration"
cd backend && uv run pytest -m "security"
cd backend && uv run pytest -m "architecture"
```

### Criterios de aceptación

- Cada grupo ejecuta los tests esperados.
- No quedan tests críticos sin clasificación.

## Task 4 — Actualizar Makefile

### Comandos nuevos

```bash
make backend-quality
make backend-test-unit
make backend-test-db
make backend-test-security
```

### Comportamiento esperado

- `backend-quality`: Ruff, format check y mypy strict.
- `backend-test-unit`: tests unitarios y arquitectura sin DB.
- `backend-test-db`: tests `db or integration`, requiere PostgreSQL disponible y migrado.
- `backend-test-security`: tests `security and not db`.
- `backend-test`: agregador de quality + unit + db + security.

### Mantener

```bash
make backend-seed
make backend-seed-clear
```

### No añadir

```bash
make docker-cleanup
make docker-destroy
```

### Criterios de aceptación

```bash
make help
make backend-quality
make backend-test-unit
make backend-test-security
```

pasan. `backend-test-db` pasa cuando PostgreSQL está disponible.

## Task 5 — Reestructurar GitHub Actions

### Workflow

Archivo único:

```text
.github/workflows/backend-ci.yml
```

### Jobs

```text
quality
test-unit
db
security
compose
```

### Backend Quality

Sin PostgreSQL:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
```

### Backend Test Unit

Sin PostgreSQL:

```bash
uv run pytest -m "test_unit or architecture"
```

### Backend DB Tests

Con Docker Compose/PostgreSQL del proyecto:

```bash
make postgres-up ENV_FILE=.env.example
make db-upgrade ENV_FILE=.env.example
cd backend && uv run pytest -m "db or integration"
make postgres-down ENV_FILE=.env.example
```

No ejecutar seed.

### Backend Security Tests

Sin PostgreSQL inicialmente:

```bash
uv run pytest -m "security and not db"
```

### Backend Docker Compose

Validación Compose y migraciones, sin seed destructivo:

```bash
make docker-config ENV_FILE=.env.example
make postgres-up ENV_FILE=.env.example
make db-upgrade ENV_FILE=.env.example
make db-current ENV_FILE=.env.example
make postgres-down ENV_FILE=.env.example
```

### Criterios de aceptación

En PR aparecen y pasan checks separados:

```text
Backend Quality
Backend Test Unit
Backend DB Tests
Backend Security Tests
Backend Docker Compose
```

## Task 6 — Actualizar branch patterns

### Branches

```yaml
main
feature/**
fix/**
chore/**
docs/**
spike/**
backend/**
refactor/**
```

### Decisión

No usar path filters todavía.

## Task 7 — Documentación estable posterior

Cuando se implemente la issue, crear/actualizar:

```text
docs/backend/ci-strategy.md
```

Debe contener:

- Objetivo del CI.
- Jobs y responsabilidades.
- Markers pytest.
- Comandos Make.
- Requisitos PostgreSQL/Docker.
- Qué comandos destructivos existen y cuáles no se ejecutan en CI.
- Cómo ejecutar validaciones localmente.

## Task 8 — Validación local final

### Comandos mínimos

```bash
make backend-quality
make backend-test-unit
make backend-test-security
make backend-test
make help
```

### Si PostgreSQL está disponible

```bash
make db-upgrade
make backend-test-db
```

### Compose smoke opcional

```bash
make docker-config ENV_FILE=.env.example
make postgres-up ENV_FILE=.env.example
make db-upgrade ENV_FILE=.env.example
make db-current ENV_FILE=.env.example
make postgres-down ENV_FILE=.env.example
```

## Task 9 — QA final

### Validaciones

- Diff completo revisado.
- No cambios funcionales en frontend.
- No modificaciones de migraciones.
- CI dividido en jobs.
- Markers correctos.
- Makefile alineado.
- Documentación estable creada/actualizada.
- No se ejecuta seed destructivo en CI.
- No hay secretos.

### Criterio de aceptación

QA devuelve:

```text
APROBADO PARA PR
```

## Task 10 — PR

### Subtareas

- Commit.
- Push.
- Crear PR.
- Vincular issue con `Closes #XX`.
- Esperar GitHub Actions.
- Confirmar checks separados en verde.

## Required checks objetivo

Cuando el workflow esté validado, configurar branch protection para exigir:

```text
Backend Quality
Backend Test Unit
Backend DB Tests
Backend Security Tests
Backend Docker Compose
```

## Riesgos

- Mover tests puede romper imports/rutas.
- `backend-test-db` requiere PostgreSQL disponible.
- Docker Compose en CI puede ser más lento.
- `postgres-down` no borra volúmenes, pero los runners de GitHub son efímeros.
- Tests pueden quedar mal clasificados inicialmente.
