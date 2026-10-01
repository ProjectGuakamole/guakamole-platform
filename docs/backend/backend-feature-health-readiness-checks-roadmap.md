# backend/feature/health-readiness-checks — Roadmap

## Objetivo

Planificar la implementación de health/readiness checks en el backend FastAPI de Guakamole, manteniendo trazabilidad por tasks y subtasks para poder validar cada fase antes de avanzar.

Este documento sirve como memoria persistente del roadmap acordado. Todo el trabajo se realizará en una única branch y, al finalizar, se preparará un único PR.

## Alcance

Endpoints previstos:

- `GET /api/health` — liveness.
- `GET /api/ready` — readiness.
- `GET /api/v1/health` — compatibilidad temporal.

Restricciones:

- No modificar `frontend/`.
- No modificar `.env`.
- No introducir secretos.
- No exponer detalles internos de PostgreSQL, Redis, URLs, credenciales ni stacktraces.
- No hacer commit ni push hasta autorización final.
- Validar cada task antes de continuar con la siguiente.
- Backend en `backend/`.
- Documentación en `docs/backend/`.

## Contratos API

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
- Redis.
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
    "database": "ok",
    "redis": "ok"
  }
}
```

Fallo parcial o total:

```text
503 Service Unavailable
```

Ejemplo PostgreSQL fallando:

```json
{
  "status": "not_ready",
  "dependencies": {
    "database": "failed",
    "redis": "ok"
  }
}
```

Ejemplo Redis fallando:

```json
{
  "status": "not_ready",
  "dependencies": {
    "database": "ok",
    "redis": "failed"
  }
}
```

Ejemplo fallo total:

```json
{
  "status": "not_ready",
  "dependencies": {
    "database": "failed",
    "redis": "failed"
  }
}
```

## Roadmap por tasks

### Task 0 — Preparación de branch y revisión inicial

Objetivo: preparar la rama única de trabajo y revisar la estructura actual.

Subtasks:

- [x] 0.1 Confirmar rama actual.
- [x] 0.2 Crear la rama única si procede: `backend/feature/health-readiness-checks`.
- [x] 0.3 Revisar `backend/app/main.py`.
- [x] 0.4 Revisar routers existentes.
- [x] 0.5 Localizar endpoint actual `/api/v1/health`.
- [x] 0.6 Revisar tests actuales.
- [x] 0.7 Revisar configuración disponible.
- [x] 0.8 No modificar código todavía.

Validación:

```bash
git status --short
git branch --show-current
```

Criterio para avanzar:

- [x] Rama correcta.
- [x] Estado Git entendido.
- [x] Endpoint actual localizado.
- [x] Sin cambios inesperados.

---

### Task 1 — Schemas Pydantic de health/readiness

Objetivo: crear los modelos de respuesta.

Subtasks:

- [x] 1.1 Crear ubicación siguiendo patrón existente. Recomendado: `backend/app/core/health/schemas.py`.
- [x] 1.2 Definir `HealthStatus`.
- [x] 1.3 Definir `ReadinessStatus`.
- [x] 1.4 Definir `DependencyStatus`.
- [x] 1.5 Definir `HealthResponse`.
- [x] 1.6 Definir `ReadinessDependencies`.
- [x] 1.7 Definir `ReadinessResponse`.
- [x] 1.8 Usar `StrEnum`.
- [x] 1.9 Mantener compatibilidad con `mypy --strict`.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
```

Criterio para avanzar:

- [x] Schemas creados.
- [x] Sin errores de ruff.
- [x] Sin errores de formato.
- [x] Sin errores de mypy.

---

### Task 2 — Abstracción de checks de dependencias

Objetivo: crear lógica aislada para comprobar PostgreSQL y Redis sin meter detalles de infraestructura en el router.

Subtasks:

- [x] 2.1 Crear archivo recomendado: `backend/app/core/health/checks.py`.
- [x] 2.2 Implementar `check_database() -> DependencyStatus`.
- [x] 2.3 Implementar `check_redis() -> DependencyStatus`.
- [x] 2.4 Implementar `get_readiness_status() -> ReadinessResponse`.
- [x] 2.5 `check_database` debe ejecutar check ligero tipo `SELECT 1` cuando haya configuración disponible.
- [x] 2.6 `check_database` debe usar timeout corto si el cliente lo permite.
- [x] 2.7 `check_database` debe capturar excepciones y devolver solo `ok` o `failed`.
- [x] 2.8 `check_redis` debe ejecutar `PING`.
- [x] 2.9 `check_redis` debe usar timeout corto si el cliente lo permite.
- [x] 2.10 `check_redis` debe capturar excepciones y devolver solo `ok` o `failed`.
- [x] 2.11 No exponer host, URL, credenciales, stacktraces ni mensajes internos.
- [x] 2.12 Diseñar la lógica para que sea testeable con mocks.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
```

Criterio para avanzar:

- [x] Checks aislados.
- [x] Errores controlados.
- [x] Sin detalles internos expuestos.
- [x] Sin errores de calidad.

---

### Task 3 — Router `/api/health` y `/api/ready`

Objetivo: añadir endpoints operativos no versionados.

Subtasks:

- [ ] 3.1 Crear router recomendado: `backend/app/api/health.py` o respetar estructura actual.
- [ ] 3.2 Implementar `GET /api/health`.
- [ ] 3.3 Implementar `GET /api/ready`.
- [ ] 3.4 `/api/health` debe devolver HTTP 200.
- [ ] 3.5 `/api/health` debe devolver `{"status": "ok"}`.
- [ ] 3.6 `/api/health` no debe llamar a checks de dependencias.
- [ ] 3.7 `/api/ready` debe llamar a `get_readiness_status`.
- [ ] 3.8 `/api/ready` debe devolver HTTP 200 si todo está OK.
- [ ] 3.9 `/api/ready` debe devolver HTTP 503 si alguna dependencia falla.
- [ ] 3.10 Registrar router en FastAPI con prefijo `/api`.
- [ ] 3.11 Mantener disponible `/api/v1/health`.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Checks manuales opcionales:

```bash
uv run uvicorn app.main:app --reload
curl http://localhost:8000/api/health
curl http://localhost:8000/api/ready
curl http://localhost:8000/api/v1/health
```

Criterio para avanzar:

- [ ] `/api/health` responde contrato correcto.
- [ ] `/api/ready` responde contrato correcto.
- [ ] `/api/v1/health` sigue funcionando.
- [ ] Tests actuales no se rompen.

---

### Task 4 — Tests de contrato y fallos

Objetivo: cubrir liveness, readiness y compatibilidad sin depender de PostgreSQL/Redis reales.

Subtasks:

- [ ] 4.1 Test `/api/health` HTTP 200.
- [ ] 4.2 Test `/api/health` body `{"status": "ok"}`.
- [ ] 4.3 Test para confirmar que `/api/health` no llama a checks de dependencias.
- [ ] 4.4 Test `/api/ready` con database ok y redis ok: HTTP 200 y status `ready`.
- [ ] 4.5 Test `/api/ready` con database failed y redis ok: HTTP 503 y status `not_ready`.
- [ ] 4.6 Test `/api/ready` con database ok y redis failed: HTTP 503 y status `not_ready`.
- [ ] 4.7 Test `/api/ready` con ambos failed: HTTP 503 y status `not_ready`.
- [ ] 4.8 Test `/api/v1/health`: HTTP 200 y body compatible `{"status": "ok"}`.
- [ ] 4.9 Usar mocks/monkeypatch. No requerir servicios reales para estos tests.

Validación:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
```

Criterio para avanzar:

- [ ] Todos los tests nuevos pasan.
- [ ] Tests existentes siguen pasando.
- [ ] No se requieren servicios reales.

---

### Task 5 — Evaluación de Docker Compose

Objetivo: decidir si actualizar el healthcheck del backend para usar `/api/ready`.

Subtasks:

- [ ] 5.1 Revisar healthcheck actual del backend.
- [ ] 5.2 Decidir entre mantener endpoint actual, cambiar a `/api/health` o cambiar a `/api/ready`.
- [ ] 5.3 Justificar la decisión.
- [ ] 5.4 Si se modifica Compose, cambiar solo el endpoint del healthcheck.
- [ ] 5.5 Validar Compose.

Validación si se toca `docker-compose.yml`:

```bash
docker compose --env-file .env.example config
git diff -- docker-compose.yml
```

Criterio para avanzar:

- [ ] Decisión justificada.
- [ ] Compose renderiza correctamente si se modifica.
- [ ] No se altera nada no relacionado.

---

### Task 6 — Documentación backend

Objetivo: documentar contrato y uso operativo.

Archivo previsto:

```text
docs/backend/backend-health-readiness-checks.md
```

Subtasks:

- [ ] 6.1 Crear documento en `docs/backend/`.
- [ ] 6.2 Incluir diferencia entre liveness y readiness.
- [ ] 6.3 Documentar `GET /api/health`.
- [ ] 6.4 Documentar `GET /api/ready`.
- [ ] 6.5 Documentar códigos HTTP.
- [ ] 6.6 Documentar ejemplos JSON.
- [ ] 6.7 Documentar comportamiento ante fallos.
- [ ] 6.8 Documentar uso recomendado en Docker Compose.
- [ ] 6.9 Documentar seguridad: no credenciales, no stacktraces, no URLs internas.
- [ ] 6.10 Documentar tests ejecutados.
- [ ] 6.11 Documentar observaciones/deuda técnica.

Validación:

```bash
git status --short
```

Criterio para avanzar:

- [ ] Documento creado.
- [ ] No se modifica `frontend/`.
- [ ] No se modifica `.env`.

---

### Task 7 — Validación final completa

Objetivo: validar todo antes de pedir revisión QA y antes de commit/PR.

Subtasks:

- [ ] 7.1 Revisar estado Git.
- [ ] 7.2 Revisar diff completo.
- [ ] 7.3 Confirmar que no hay cambios en `frontend/`.
- [ ] 7.4 Confirmar que `.env` no se modificó.
- [ ] 7.5 Ejecutar calidad backend.
- [ ] 7.6 Ejecutar tests.
- [ ] 7.7 Validar Compose si se modificó.
- [ ] 7.8 Preparar informe final.

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

Si se modificó Compose:

```bash
docker compose --env-file .env.example config
```

Criterio de cierre:

- [ ] Ruff OK.
- [ ] Format OK.
- [ ] Mypy strict OK.
- [ ] Pytest OK.
- [ ] Compose config OK si aplica.
- [ ] Sin cambios en `frontend/`.
- [ ] `.env` sin modificar.
- [ ] Contratos cumplidos.

## Criterios de aceptación finales

- [ ] `GET /api/health` devuelve HTTP 200.
- [ ] `GET /api/health` devuelve `{"status": "ok"}`.
- [ ] `GET /api/health` no llama PostgreSQL.
- [ ] `GET /api/health` no llama Redis.
- [ ] `GET /api/ready` con todo OK devuelve HTTP 200.
- [ ] `GET /api/ready` con todo OK devuelve `status: ready` y dependencias `ok`.
- [ ] `GET /api/ready` con database failed devuelve HTTP 503.
- [ ] `GET /api/ready` con redis failed devuelve HTTP 503.
- [ ] `GET /api/ready` con ambos failed devuelve HTTP 503.
- [ ] `GET /api/v1/health` sigue disponible.
- [ ] No se devuelven errores internos.
- [ ] No se devuelven credenciales.
- [ ] No se devuelven URLs internas sensibles.
- [ ] No se exponen stacktraces.
- [ ] No se modifica `frontend/`.
- [ ] No se modifica `.env`.
- [ ] No se hace commit ni push sin autorización.

## Formato de respuesta tras cada task

```markdown
## Task X — Nombre

### Subtasks completadas
-

### Archivos modificados
-

### Validación ejecutada
-

### Resultado
-

### Problemas o decisiones
-

### Confirmación para continuar
Task X validada. Esperando autorización para continuar con Task X+1.
```

## Formato de respuesta final

```markdown
## Health y readiness checks

### Branch
-

### Tasks completadas
- Task 0:
- Task 1:
- Task 2:
- Task 3:
- Task 4:
- Task 5:
- Task 6:
- Task 7:

### Cambios realizados
-

### Archivos modificados
-

### Contratos implementados
-

### Tests ejecutados
-

### Resultado
-

### Observaciones
-

### Seguridad
- `.env` no se ha modificado.
- `frontend/` no se ha modificado.
- No se han añadido secretos.
- No se exponen detalles internos.

### Siguiente paso recomendado
Pedir revisión a `qa-tester`.
```
