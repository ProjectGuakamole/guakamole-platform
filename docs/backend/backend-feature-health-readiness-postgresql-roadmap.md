# backend/feature/health-readiness-postgresql — Roadmap

## Objetivo

Planificar la implementación definitiva de los endpoints operativos de health/readiness del backend FastAPI usando únicamente PostgreSQL como dependencia de readiness.

Este documento sustituye el alcance anterior que contemplaba Redis. Redis queda fuera del contrato de readiness porque finalmente no se usará como dependencia operativa del backend en esta fase.

Todo el trabajo deberá realizarse en una nueva branch:

```text
backend/feature/health-readiness-postgresql
```

Al finalizar, se preparará un único PR hacia `main`.

## Decisión de arquitectura

La separación queda así:

- `GET /api/health` — liveness: comprueba que FastAPI está vivo.
- `GET /api/ready` — readiness: comprueba que FastAPI puede prestar servicio con PostgreSQL disponible.
- `GET /api/v1/health` — compatibilidad temporal con el endpoint existente.

Redis queda eliminado del contrato de readiness.

## Restricciones generales

- [ ] No modificar `frontend/`.
- [ ] No modificar `.env`.
- [ ] No introducir secretos.
- [ ] No exponer host, URL, credenciales, stacktraces ni mensajes internos de PostgreSQL.
- [ ] No mezclar este trabajo con modelos ORM de dominio.
- [ ] No crear tablas de dominio en esta branch.
- [ ] No crear migraciones de dominio en esta branch.
- [ ] No hacer commit ni push hasta autorización final.
- [ ] Validar cada task antes de continuar con la siguiente.

## Contratos API objetivo

### Liveness — `GET /api/health`

HTTP esperado:

```text
200 OK
```

Respuesta:

```json
{
  "status": "ok"
}
```

No debe comprobar:

- PostgreSQL.
- Migraciones.
- Servicios externos.
- Estado funcional de negocio.

### Readiness — `GET /api/ready`

Caso correcto:

```text
200 OK
```

```json
{
  "status": "ready",
  "dependencies": {
    "database": "ok"
  }
}
```

Caso PostgreSQL no disponible:

```text
503 Service Unavailable
```

```json
{
  "status": "not_ready",
  "dependencies": {
    "database": "failed"
  }
}
```

## Decisión crítica pendiente

Antes de exponer `/api/ready`, debe resolverse cómo se comprobará PostgreSQL:

- Opción A: implementar check real con `SELECT 1`.
- Opción B: si no existe configuración centralizada de DB, devolver `not_ready` hasta que exista check real.

Recomendación estricta:

> No devolver `ready` en `/api/ready` si no se comprueba PostgreSQL de verdad.

## Roadmap por tasks

### Task 0 — Preparación de nueva branch y baseline

Objetivo: partir desde `main`, crear la nueva branch y confirmar el estado del trabajo anterior.

Subtasks:

- [x] 0.1 Confirmar que el PR anterior de groundwork está mergeado en `main`.
- [x] 0.2 Cambiar a `main`.
- [x] 0.3 Actualizar `main` desde remoto.
- [x] 0.4 Crear branch nueva: `backend/feature/health-readiness-postgresql`.
- [x] 0.5 Revisar estado Git limpio salvo documentación de planning si aplica.
- [x] 0.6 Revisar archivos existentes de health:
  - `backend/app/core/health/schemas.py`
  - `backend/app/core/health/checks.py`
  - `backend/tests/test_health_schemas.py`
  - `backend/tests/test_health_checks.py`
- [x] 0.7 Confirmar que Redis aparece en el groundwork anterior y debe eliminarse del alcance.

Validación:

```bash
git status --short
git branch --show-current
```

Criterio para avanzar:

- [x] Branch correcta.
- [x] Baseline entendido.
- [x] No hay cambios inesperados.

---

### Task 1 — Refactor de schemas PostgreSQL-only

Objetivo: adaptar los schemas para que readiness dependa solo de PostgreSQL.

Archivos previstos:

```text
backend/app/core/health/schemas.py
backend/tests/test_health_schemas.py
```

Subtasks:

- [ ] 1.1 Actualizar `ReadinessDependencies` para que solo tenga `database: DependencyStatus`.
- [ ] 1.2 Eliminar campo `redis` del contrato de readiness.
- [ ] 1.3 Mantener `HealthStatus`.
- [ ] 1.4 Mantener `ReadinessStatus`.
- [ ] 1.5 Mantener `DependencyStatus`.
- [ ] 1.6 Mantener `HealthResponse`.
- [ ] 1.7 Mantener `ReadinessResponse`.
- [ ] 1.8 Actualizar tests de schemas para readiness OK solo con database.
- [ ] 1.9 Actualizar tests de schemas para readiness failed solo con database.
- [ ] 1.10 Eliminar tests de schema relacionados con Redis.

Contrato esperado:

```json
{
  "status": "ready",
  "dependencies": {
    "database": "ok"
  }
}
```

```json
{
  "status": "not_ready",
  "dependencies": {
    "database": "failed"
  }
}
```

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [ ] Schemas PostgreSQL-only.
- [ ] Tests actualizados.
- [ ] Sin referencias a Redis en schemas/tests de schemas.
- [ ] Calidad backend OK.

---

### Task 2 — Refactor de checks PostgreSQL-only

Objetivo: eliminar Redis de la abstracción de readiness.

Archivos previstos:

```text
backend/app/core/health/checks.py
backend/tests/test_health_checks.py
```

Subtasks:

- [ ] 2.1 Mantener `check_database() -> DependencyStatus`.
- [ ] 2.2 Mantener `get_readiness_status() -> ReadinessResponse`.
- [ ] 2.3 Eliminar `check_redis()`.
- [ ] 2.4 Eliminar `_probe_redis()`.
- [ ] 2.5 Eliminar tests de Redis.
- [ ] 2.6 Actualizar `get_readiness_status()` para depender solo de database.
- [ ] 2.7 Si database es `OK`, readiness debe ser `READY`.
- [ ] 2.8 Si database es `FAILED`, readiness debe ser `NOT_READY`.
- [ ] 2.9 Mantener captura de excepciones.
- [ ] 2.10 No exponer detalles internos.
- [ ] 2.11 Mantener diseño testeable con monkeypatch/mocks.

Tests obligatorios:

- [ ] `check_database()` devuelve `OK` si el probe de DB no falla.
- [ ] `check_database()` devuelve `FAILED` si el probe de DB falla.
- [ ] `get_readiness_status()` devuelve `READY` si DB está OK.
- [ ] `get_readiness_status()` devuelve `NOT_READY` si DB falla.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [ ] Checks PostgreSQL-only.
- [ ] Sin referencias a Redis en checks/tests de checks.
- [ ] Calidad backend OK.

---

### Task 3 — Decisión e implementación del probe real de PostgreSQL

Objetivo: evitar readiness falsamente positiva.

Subtasks:

- [ ] 3.1 Revisar si existe configuración centralizada de DB/session/engine.
- [ ] 3.2 Si existe configuración suficiente, implementar probe real con consulta equivalente a `SELECT 1`.
- [ ] 3.3 Si no existe configuración suficiente, hacer que el probe no devuelva `OK` falsamente.
- [ ] 3.4 Definir comportamiento temporal documentado si el probe real queda pendiente.
- [ ] 3.5 Asegurar timeout corto cuando el cliente/engine lo permita.
- [ ] 3.6 Capturar excepciones y devolver `FAILED` sin exponer detalles.
- [ ] 3.7 Añadir/ajustar tests con mocks para OK/fallo.

Decisión recomendada:

- [ ] Preferir check real con `SELECT 1` si hay infraestructura mínima.
- [ ] Si no hay infraestructura mínima, readiness debe ser conservadora y no devolver `ready` como si la DB estuviera comprobada.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [ ] No hay readiness falsamente positiva.
- [ ] No se exponen detalles internos.
- [ ] Tests cubren OK/fallo.

---

### Task 4 — Implementar router `/api/health` y `/api/ready`

Objetivo: exponer endpoints operativos no versionados y mantener compatibilidad.

Archivos previstos:

```text
backend/app/api/health.py
backend/app/main.py
backend/tests/test_health.py
```

Subtasks:

- [ ] 4.1 Crear router operativo no versionado si no existe: `backend/app/api/health.py`.
- [ ] 4.2 Implementar `GET /api/health`.
- [ ] 4.3 Implementar `GET /api/ready`.
- [ ] 4.4 Registrar router con prefijo `/api`.
- [ ] 4.5 Mantener `GET /api/v1/health`.
- [ ] 4.6 `/api/health` debe devolver 200 y `{"status": "ok"}`.
- [ ] 4.7 `/api/health` no debe llamar a DB.
- [ ] 4.8 `/api/ready` debe devolver 200 si DB está OK.
- [ ] 4.9 `/api/ready` debe devolver 503 si DB falla.
- [ ] 4.10 `/api/ready` debe devolver contrato PostgreSQL-only.

Tests obligatorios:

- [ ] `/api/health` devuelve 200.
- [ ] `/api/health` devuelve `{"status": "ok"}`.
- [ ] `/api/health` no llama a readiness/check DB.
- [ ] `/api/ready` DB OK devuelve 200.
- [ ] `/api/ready` DB failed devuelve 503.
- [ ] `/api/v1/health` sigue disponible.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [ ] Endpoints implementados.
- [ ] Compatibilidad conservada.
- [ ] Tests de contrato OK.

---

### Task 5 — Evaluación de Docker Compose

Objetivo: decidir endpoint de healthcheck del contenedor backend.

Subtasks:

- [ ] 5.1 Revisar healthcheck actual del backend en `docker-compose.yml`.
- [ ] 5.2 Si `/api/ready` comprueba PostgreSQL de verdad, valorar usar `/api/ready`.
- [ ] 5.3 Si `/api/ready` aún no comprueba PostgreSQL real, usar `/api/health`.
- [ ] 5.4 Si se modifica Compose, cambiar solo el endpoint del healthcheck.
- [ ] 5.5 Validar Compose.

Validación si se toca Compose:

```bash
docker compose --env-file .env.example config
```

Criterio para avanzar:

- [ ] Decisión justificada.
- [ ] Compose renderiza correctamente si se modifica.
- [ ] No se reintroduce Redis.

---

### Task 6 — Documentación final backend

Objetivo: documentar contrato final PostgreSQL-only.

Archivo previsto:

```text
docs/backend/backend-health-readiness-checks.md
```

Subtasks:

- [ ] 6.1 Documentar diferencia entre liveness y readiness.
- [ ] 6.2 Documentar que Redis queda fuera del alcance.
- [ ] 6.3 Documentar `GET /api/health`.
- [ ] 6.4 Documentar `GET /api/ready` PostgreSQL-only.
- [ ] 6.5 Documentar códigos HTTP.
- [ ] 6.6 Documentar JSON OK/fallo.
- [ ] 6.7 Documentar decisión de Docker Compose.
- [ ] 6.8 Documentar seguridad: no secretos, no stacktraces, no URLs internas.
- [ ] 6.9 Documentar tests ejecutados.
- [ ] 6.10 Documentar deuda técnica si el probe DB real no queda completo.

Validación:

```bash
git status --short
```

Criterio para avanzar:

- [ ] Documentación completa.
- [ ] Sin cambios en `frontend/`.
- [ ] Sin cambios en `.env`.

---

### Task 7 — Validación final y PR

Objetivo: validar todo antes del commit/push/PR.

Subtasks:

- [ ] 7.1 Revisar estado Git.
- [ ] 7.2 Revisar diff completo.
- [ ] 7.3 Confirmar que no hay cambios en `frontend/`.
- [ ] 7.4 Confirmar que `.env` no se modificó.
- [ ] 7.5 Confirmar que Redis no aparece en contrato/readiness.
- [ ] 7.6 Ejecutar calidad backend.
- [ ] 7.7 Ejecutar tests.
- [ ] 7.8 Validar Compose si se modificó.
- [ ] 7.9 Preparar commit.
- [ ] 7.10 Crear PR hacia `main`.

Comandos obligatorios:

```bash
git status --short
git diff
git status --short -- frontend .env

cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Si se modifica Compose:

```bash
docker compose --env-file .env.example config
```

Criterio de cierre:

- [ ] Ruff OK.
- [ ] Format OK.
- [ ] Mypy strict OK.
- [ ] Pytest OK.
- [ ] Compose OK si aplica.
- [ ] Sin cambios prohibidos.
- [ ] PR creado.

## Criterios de aceptación finales

- [ ] `GET /api/health` devuelve HTTP 200.
- [ ] `GET /api/health` devuelve `{"status": "ok"}`.
- [ ] `GET /api/health` no llama PostgreSQL.
- [ ] `GET /api/ready` devuelve HTTP 200 si PostgreSQL está OK.
- [ ] `GET /api/ready` devuelve HTTP 503 si PostgreSQL falla.
- [ ] `GET /api/ready` usa contrato PostgreSQL-only.
- [ ] `GET /api/v1/health` sigue disponible.
- [ ] Redis no aparece en contratos de readiness.
- [ ] No se devuelven errores internos.
- [ ] No se devuelven credenciales.
- [ ] No se devuelven URLs internas sensibles.
- [ ] No se exponen stacktraces.
- [ ] No se modifica `frontend/`.
- [ ] No se modifica `.env`.

## Trabajo posterior fuera de esta branch

La creación de schemas de dominio, modelos ORM, tablas y migraciones debe realizarse en otra branch distinta, por ejemplo:

```text
backend/feature/database-domain-models
```

No mezclar con health/readiness.
