# backend/feature/health-readiness-postgresql

## Objetivo

Documentar el contrato operativo final de los endpoints de health/readiness del backend FastAPI para la rama `backend/feature/health-readiness-postgresql`.

El alcance final es PostgreSQL-only: `GET /api/ready` representa la preparación del backend respecto a PostgreSQL y Redis queda fuera del contrato.

Fecha de documentación: 2026-10-01.

## Cambios realizados

- Se documenta la diferencia entre liveness y readiness.
- Se documenta el contrato de `GET /api/health`.
- Se documenta el contrato de `GET /api/ready` con dependencia única de PostgreSQL.
- Se documenta la compatibilidad temporal de `GET /api/v1/health`.
- Se documenta que Redis queda fuera del alcance de readiness.
- Se documenta la decisión operativa de Docker Compose: el healthcheck del contenedor backend usa `/api/health`, no `/api/ready`.
- Se documentan las restricciones de seguridad aplicables a las respuestas.
- Se documentan las validaciones ejecutadas en tareas previas.
- Se documenta la deuda técnica pendiente del probe real contra PostgreSQL.

## Justificacion tecnica

### Diferencia entre liveness y readiness

`GET /api/health` es el endpoint de **liveness**. Su objetivo es comprobar que el proceso FastAPI está vivo y puede responder peticiones HTTP básicas.

Este endpoint no comprueba PostgreSQL, migraciones, servicios externos ni estado funcional de negocio. Debe ser simple, rápido y estable para evitar reinicios innecesarios del contenedor cuando una dependencia externa todavía no esté disponible.

`GET /api/ready` es el endpoint de **readiness**. Su objetivo es indicar si el backend está preparado para prestar servicio de forma segura teniendo en cuenta sus dependencias operativas. En este contrato, la única dependencia contemplada es PostgreSQL.

### Contrato `GET /api/health`

Respuesta esperada:

```text
HTTP 200 OK
```

```json
{"status": "ok"}
```

Características:

- No comprueba base de datos.
- No comprueba Redis.
- No comprueba servicios externos.
- No expone información interna del entorno.

### Contrato `GET /api/ready`

Caso PostgreSQL disponible:

```text
HTTP 200 OK
```

```json
{"status":"ready","dependencies":{"database":"ok"}}
```

Caso PostgreSQL no disponible o no verificable de forma real:

```text
HTTP 503 Service Unavailable
```

```json
{"status":"not_ready","dependencies":{"database":"failed"}}
```

Características:

- Es PostgreSQL-only.
- No incluye Redis.
- No debe devolver `ready` si PostgreSQL no se ha comprobado de verdad.
- No debe exponer errores internos, trazas, URLs internas ni credenciales.

### Compatibilidad `GET /api/v1/health`

`GET /api/v1/health` sigue disponible como compatibilidad temporal con el endpoint existente. El contrato operativo recomendado para liveness del backend pasa a ser `GET /api/health`.

## Decisiones tomadas

- Redis queda fuera del alcance del contrato final de readiness en esta fase.
- Docker Compose debe usar `/api/health` como healthcheck del backend, no `/api/ready`.
- La justificación de Docker Compose es que `/api/ready` es conservador hasta tener un probe real de PostgreSQL. Usarlo como healthcheck del contenedor podría marcar el backend como unhealthy aunque el proceso FastAPI esté vivo.
- `GET /api/ready` debe responder `not_ready` si no existe una comprobación real de PostgreSQL, para evitar una readiness falsamente positiva.
- La respuesta de readiness se limita a `database` como única dependencia.

## Tests ejecutados

No se han ejecutado tests nuevos en esta tarea documental. Se documentan las validaciones ejecutadas durante las tareas previas aprobadas por QA:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict .
uv run pytest
docker compose --env-file .env.example config
```

Estas validaciones corresponden a calidad backend, tipado estricto, suite de tests y renderizado de Docker Compose realizados en las tareas anteriores del roadmap.

## Riesgos o deuda tecnica

- `_probe_database()` todavía no ejecuta un `SELECT 1` real porque no existe configuración centralizada suficiente de DB/session/engine.
- Por seguridad, readiness no debe devolver `ready` si no hay una base de datos real configurada y comprobada.
- Cuando exista configuración centralizada de PostgreSQL, deberá sustituirse el comportamiento conservador por un probe ligero real, idealmente con timeout corto si el cliente o engine lo permite.
- Hasta entonces, `/api/ready` debe considerarse conservador y no apto como healthcheck de liveness del contenedor.

## Relacion con el backend

Esta documentación fija el contrato operativo backend para monitorización y orquestación:

- Define endpoints operativos para health/readiness.
- Separa liveness (`/api/health`) de readiness (`/api/ready`).
- Sirve como base para el healthcheck de Docker Compose usando `/api/health`.
- Establece el contrato PostgreSQL-only de readiness.
- Evita acoplar readiness a Redis, que queda fuera del alcance.
- Refuerza la seguridad del backend evitando exponer secretos, URLs internas, errores internos o stacktraces.
