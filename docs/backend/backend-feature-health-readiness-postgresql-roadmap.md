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

- [x] 1.1 Actualizar `ReadinessDependencies` para que solo tenga `database: DependencyStatus`.
- [x] 1.2 Eliminar campo `redis` del contrato de readiness.
- [x] 1.3 Mantener `HealthStatus`.
- [x] 1.4 Mantener `ReadinessStatus`.
- [x] 1.5 Mantener `DependencyStatus`.
- [x] 1.6 Mantener `HealthResponse`.
- [x] 1.7 Mantener `ReadinessResponse`.
- [x] 1.8 Actualizar tests de schemas para readiness OK solo con database.
- [x] 1.9 Actualizar tests de schemas para readiness failed solo con database.
- [x] 1.10 Eliminar tests de schema relacionados con Redis.

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

- [x] Schemas PostgreSQL-only.
- [x] Tests actualizados.
- [x] Sin referencias a Redis en schemas/tests de schemas.
- [x] Calidad backend OK.

---

### Task 2 — Refactor de checks PostgreSQL-only

Objetivo: eliminar Redis de la abstracción de readiness.

Archivos previstos:

```text
backend/app/core/health/checks.py
backend/tests/test_health_checks.py
```

Subtasks:

- [x] 2.1 Mantener `check_database() -> DependencyStatus`.
- [x] 2.2 Mantener `get_readiness_status() -> ReadinessResponse`.
- [x] 2.3 Eliminar `check_redis()`.
- [x] 2.4 Eliminar `_probe_redis()`.
- [x] 2.5 Eliminar tests de Redis.
- [x] 2.6 Actualizar `get_readiness_status()` para depender solo de database.
- [x] 2.7 Si database es `OK`, readiness debe ser `READY`.
- [x] 2.8 Si database es `FAILED`, readiness debe ser `NOT_READY`.
- [x] 2.9 Mantener captura de excepciones.
- [x] 2.10 No exponer detalles internos.
- [x] 2.11 Mantener diseño testeable con monkeypatch/mocks.

Tests obligatorios:

- [x] `check_database()` devuelve `OK` si el probe de DB no falla.
- [x] `check_database()` devuelve `FAILED` si el probe de DB falla.
- [x] `get_readiness_status()` devuelve `READY` si DB está OK.
- [x] `get_readiness_status()` devuelve `NOT_READY` si DB falla.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [x] Checks PostgreSQL-only.
- [x] Sin referencias a Redis en checks/tests de checks.
- [x] Calidad backend OK.

---

### Task 3 — Decisión e implementación del probe real de PostgreSQL

Objetivo: evitar readiness falsamente positiva.

Subtasks:

- [x] 3.1 Revisar si existe configuración centralizada de DB/session/engine.
- [ ] 3.2 Si existe configuración suficiente, implementar probe real con consulta equivalente a `SELECT 1`.
- [x] 3.3 Si no existe configuración suficiente, hacer que el probe no devuelva `OK` falsamente.
- [x] 3.4 Definir comportamiento temporal documentado si el probe real queda pendiente.
- [x] 3.5 Asegurar timeout corto cuando el cliente/engine lo permita.
- [x] 3.6 Capturar excepciones y devolver `FAILED` sin exponer detalles.
- [x] 3.7 Añadir/ajustar tests con mocks para OK/fallo.

Decisión recomendada:

- [x] Preferir check real con `SELECT 1` si hay infraestructura mínima.
- [x] Si no hay infraestructura mínima, readiness debe ser conservadora y no devolver `ready` como si la DB estuviera comprobada.

Decisión Task 3:

No existe todavía configuración centralizada suficiente de base de datos,
session o engine en `backend/app/db/` ni en `backend/app/core/`. Por tanto,
no se implementa aún el `SELECT 1`; `_probe_database()` falla de forma
controlada por defecto mediante una excepción interna privada. Cuando se añada
configuración centralizada, el probe deberá sustituirse por una consulta ligera
con timeout corto si el cliente/engine lo permite. Mientras tanto, readiness es
conservadora y no puede devolver `ready` por un placeholder silencioso.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [x] No hay readiness falsamente positiva.
- [x] No se exponen detalles internos.
- [x] Tests cubren OK/fallo.

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

- [x] 4.1 Crear router operativo no versionado si no existe: `backend/app/api/health.py`.
- [x] 4.2 Implementar `GET /api/health`.
- [x] 4.3 Implementar `GET /api/ready`.
- [x] 4.4 Registrar router con prefijo `/api`.
- [x] 4.5 Mantener `GET /api/v1/health`.
- [x] 4.6 `/api/health` debe devolver 200 y `{"status": "ok"}`.
- [x] 4.7 `/api/health` no debe llamar a DB.
- [x] 4.8 `/api/ready` debe devolver 200 si DB está OK.
- [x] 4.9 `/api/ready` debe devolver 503 si DB falla.
- [x] 4.10 `/api/ready` debe devolver contrato PostgreSQL-only.

Tests obligatorios:

- [x] `/api/health` devuelve 200.
- [x] `/api/health` devuelve `{"status": "ok"}`.
- [x] `/api/health` no llama a readiness/check DB.
- [x] `/api/ready` DB OK devuelve 200.
- [x] `/api/ready` DB failed devuelve 503.
- [x] `/api/v1/health` sigue disponible.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [x] Endpoints implementados.
- [x] Compatibilidad conservada.
- [x] Tests de contrato OK.

---

### Task 5 — Evaluación de Docker Compose

Objetivo: decidir endpoint de healthcheck del contenedor backend.

Subtasks:

- [x] 5.1 Revisar healthcheck actual del backend en `docker-compose.yml`.
- [x] 5.2 Si `/api/ready` comprueba PostgreSQL de verdad, valorar usar `/api/ready`.
- [x] 5.3 Si `/api/ready` aún no comprueba PostgreSQL real, usar `/api/health`.
- [x] 5.4 Si se modifica Compose, cambiar solo el endpoint del healthcheck.
- [x] 5.5 Validar Compose.

Decisión Task 5:

`/api/ready` todavía no ejecuta una comprobación real contra PostgreSQL con
`SELECT 1`; por seguridad devuelve `not_ready` de forma conservadora mientras no
exista configuración centralizada de DB. Por tanto, el healthcheck del contenedor
backend debe usar `/api/health` para comprobar únicamente que FastAPI está vivo,
sin marcar el servicio como unhealthy por una readiness todavía pendiente de
integración real con PostgreSQL. Se modifica solo el endpoint del healthcheck del
backend, de `/api/v1/health` a `/api/health`.

Validación si se toca Compose:

```bash
docker compose --env-file .env.example config
```

Criterio para avanzar:

- [x] Decisión justificada.
- [x] Compose renderiza correctamente si se modifica.
- [x] No se reintroduce Redis.

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

### Task 7 — Makefile operativo de backend y entorno local

Objetivo: crear un `Makefile` de ayuda para comandos repetibles de desarrollo, validación y operación local sin esconder lógica crítica ni introducir secretos.

Archivo previsto:

```text
Makefile
```

Subtasks:

- [ ] 7.1 Crear `Makefile` en la raíz del repositorio.
- [ ] 7.2 Añadir target de ayuda, por ejemplo `make help`.
- [ ] 7.3 Añadir targets de calidad backend:
  - `make backend-lint`
  - `make backend-format-check`
  - `make backend-mypy`
  - `make backend-test`
  - `make backend-check`
- [ ] 7.4 Añadir target para levantar servidor FastAPI local, por ejemplo `make backend-run`.
- [ ] 7.5 Añadir targets Docker Compose seguros:
  - `make docker-config`
  - `make docker-up`
  - `make docker-down`
  - `make docker-ps`
  - `make docker-logs`
- [ ] 7.6 Añadir targets específicos para PostgreSQL si aplica:
  - `make postgres-up`
  - `make postgres-logs`
  - `make postgres-down`
- [ ] 7.7 Añadir target para probar health/readiness cuando existan endpoints:
  - `make health-check`
  - `make ready-check`
- [ ] 7.8 Usar `.env.example` en comandos de validación de Compose cuando sea seguro.
- [ ] 7.9 No introducir valores secretos ni depender de `.env` real en comandos documentales.
- [ ] 7.10 Documentar en el propio `Makefile` los targets principales.
- [ ] 7.11 Validar que los targets no modifican `frontend/` ni `.env`.

Validación:

```bash
make help
make backend-check
make docker-config
```

Si se añaden targets que levantan servicios:

```bash
make postgres-up
make docker-ps
make postgres-down
```

Criterio para avanzar:

- [ ] `Makefile` creado.
- [ ] Targets de backend funcionan.
- [ ] Targets Docker/Compose renderizan correctamente.
- [ ] No se introducen secretos.
- [ ] No se modifica `.env`.
- [ ] No se modifica `frontend/`.

---

### Task 8 — Validación final y PR

Objetivo: validar todo antes del commit/push/PR.

Subtasks:

- [ ] 8.1 Revisar estado Git.
- [ ] 8.2 Revisar diff completo.
- [ ] 8.3 Confirmar que no hay cambios en `frontend/`.
- [ ] 8.4 Confirmar que `.env` no se modificó.
- [ ] 8.5 Confirmar que Redis no aparece en contrato/readiness.
- [ ] 8.6 Ejecutar calidad backend.
- [ ] 8.7 Ejecutar tests.
- [ ] 8.8 Validar Compose si se modificó.
- [ ] 8.9 Validar targets principales del `Makefile` si se añadió.
- [ ] 8.10 Preparar commit.
- [ ] 8.11 Crear PR hacia `main`.

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
- [ ] Makefile validado si se añadió.

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
- [ ] `Makefile` disponible para comandos comunes de backend, Docker, PostgreSQL y validación si se implementó Task 7.

## Trabajo posterior fuera de esta branch

La creación de schemas de dominio, modelos ORM, tablas y migraciones debe realizarse en otra branch distinta, por ejemplo:

```text
backend/feature/database-domain-models
```

No mezclar con health/readiness.
