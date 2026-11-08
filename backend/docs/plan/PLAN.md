# Plan del proyecto

> Lo escribe el **leader** tras el discovery y lo revisa **Codex** en cada nivel
> (roadmap → cada phase → cada subtask); el usuario aprueba cada nivel antes de
> empezar el siguiente. El índice del final lo genera `make plan`: no se edita a mano.

## Visión

Backend del Proyecto Guakamole: una plataforma B2B en la que las empresas forman y
evalúan a sus equipos de ciberseguridad con escenarios SOC prácticos y con tiempo
limitado (recibir una alerta → investigar → decidir verdadero/falso positivo →
documentar → cerrar el caso). Este backend gestiona la identidad, las
organizaciones (tenants), el control de acceso y, más adelante, roadmaps,
escenarios y labs. Alcance de producto: `docs/1-architecture/project_charter.md`.

## Objetivos

- Una base IAM multi-tenant (organizaciones, usuarios, departamentos, roles) sobre
  la que se construyen todos los módulos posteriores, con aislamiento de tenant
  garantizado en el servidor.
- Autenticación de navegador con cookie HttpOnly, CSRF, CORS explícito y rate
  limiting, más un endpoint de token OAuth2 separado para Swagger y clientes técnicos.
- Un entorno reproducible (Docker Compose, migrator aislado, CI por jobs y markers)
  que mantiene ruff, `mypy --strict` y pytest en verde en cada cambio.
- Autorización por roles y permisos sobre la identidad autenticada.
- Integración real con el frontend: los formularios de registro de organización y
  de login consumen la API v1, y una suite e2e verifica el sistema completo de
  extremo a extremo.

## Alcance

- **Dentro:** `backend/` (app FastAPI, persistencia IAM, auth, health/readiness,
  Alembic, contratos de Docker/Makefile/CI del backend) y, **solo en la phase 09**,
  la capa de integración de `frontend/` (cliente de la API de auth y los formularios
  de registro y login) junto con la suite e2e en `backend/tests/e2e/`.
- **Fuera:** el resto de `frontend/` (diseño, otras páginas, estado global);
  escenarios SOC, labs y roadmaps (phases posteriores, aún sin planificar); MFA,
  refresh tokens y eventos de auditoría persistentes (deuda documentada).
- **Trabajo existente:** las phases 01-07 registran lo construido antes de este
  harness (`status: baseline`, documentado en `../docs/backend/`), ordenadas por
  dependencia y no por fecha; la phase 08 es el primer trabajo nuevo y la 09 cierra
  la integración con el frontend.

## Visión general de la arquitectura

- **Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x (sesiones síncronas,
  psycopg 3) sobre PostgreSQL 15, Alembic, PyJWT, pwdlib/argon2; uv, ruff,
  `mypy --strict`, pytest con markers (unit, db, security, architecture y, desde la
  phase 09, e2e). Frontend: Vite + React + TypeScript; e2e con Playwright para
  Python sobre pytest.
- **Estructura:** `app/` (no `src/`, una excepción deliberada recogida en
  `docs/architecture.md` y `docs/conventions.md`): `app/api` (routers operativo y
  v1), `app/core` (settings, CORS, rate limit, health, migraciones), `app/db`
  (base, mixins, registro de modelos, sesión), `app/domains/<domain>/<module>`,
  `app/shared` (auditoría); scripts operativos en `scripts/`; migraciones en `alembic/`.
- **Arquitectura:** módulos hexagonales pragmáticos y con la seguridad primero
  (`../docs/backend/hexagonal/`), mapeados sobre las cuatro capas de
  `docs/architecture.md`: domain = `policies.py`/`entities.py` (sin FastAPI ni
  SQLAlchemy); application = `service(s).py` con sus puertos como `Protocol`,
  inyectados por constructor; infrastructure = repositorios (el ORM vive y se mapea
  ahí; los modelos nunca llegan a los servicios), `audit.py`, `app/db`;
  interfaces = routers, schemas y `dependencies.py` (el único punto de
  composición). Los límites se verifican en `tests/architecture/`.
- **Persistencia:** esquema `sch_iam`, una única revisión baseline solo DDL; la app
  y el migrator usan roles de base de datos distintos; los catálogos y los datos
  demo se cargan con scripts, nunca con migraciones.
- **Runtime:** Docker Compose (postgres, backend, frontend, nginx, redis, worker
  provisional); en el stack base solo se publica nginx, y el override local publica
  puertos para desarrollo y CI. El e2e recorre el camino real navegador → nginx →
  frontend/backend → PostgreSQL.
- **Riesgos clave:** aislamiento de tenant (nunca confiar en un `organization_id`
  enviado por el cliente), secretos fuera del repo, rate limiting en memoria (un
  solo proceso), deriva del contrato entre frontend y backend (hoy el frontend llama
  a `/api/auth/*` en lugar de `/api/v1/...` y no envía CSRF; la phase 09 lo corrige
  y el e2e en CI evita que se repita).

## Idioma del plan

Títulos, goals, criterios de aceptación y descripciones de este plan, de las phases
y de las specs, así como los documentos de cierre de `docs/reference/`, se escriben
en **castellano**. Las claves que lee el harness (`goal`, `layer`, `ticket`,
`status`, `depends`, `files`, `acceptance`), la palabra `Phase` de las cabeceras,
los slugs de los ficheros, el código, los nombres y los comentarios siguen en
**inglés**.

## Cómo funciona esta carpeta

```
docs/plan/
  PLAN.md                                 este fichero (visión… + índice generado)
  phase-NN-<slug>.md                      uno por phase: título, goal y sus tasks N.M
  phase-NN-<slug>/<N.M.K>-<slug>.md       una spec por subtask (micro-tarea)
```

- **Todas las phases existen desde el principio** con su título y goal, para que el
  alcance completo sea visible y revisado (roadmap gate).
- **Una phase cada vez**: la phase N+1 recibe tasks y specs solo cuando la phase N
  está terminada (`make check` lo exige).
- **El estado vive solo en las specs de las subtasks.** El estado de tasks y phases,
  `feature_list.json` y el índice de abajo los deriva `make plan`.
- Los planes aprobados quedan **sellados**: editar lo que Codex aprobó (salvo
  `status`) hace fallar `make check` hasta que el gate apruebe el cambio.
- `make status` muestra el plan completo, el veredicto de cada gate y el siguiente paso.

Ids: phase `NN` · task `N.M` · subtask `N.M.K`. Se usan en todas partes
(`feature_list.json`, `progress/`, `docs/reference/<N.M.K>-<slug>.md`, footer del
commit `Plan: docs/plan/phase-NN-<slug>/<N.M.K>-<slug>.md`).

### Fichero de phase — `docs/plan/phase-01-users.md`

```markdown
# Phase 01 — Usuarios
- goal: los usuarios se registran con un email validado

## 1.1 Entidad usuario
- layer: domain
- ticket: BACK-USERS-001
- goal: value objects del usuario con validación
```

Como `harness.toml` `[git]` usa `{ticket}` (`branch = "feature/{ticket}-{slug}"`),
cada task con trabajo nuevo lleva su id de ticket (`- ticket: BACK-RBAC-001`); una
task cuyas subtasks son todas `baseline` no lo necesita.

### Spec de subtask — `docs/plan/phase-01-users/1.1.1-email-value-object.md`

```markdown
# 1.1.1 Value object Email
- status: pending
- layer: domain
- depends: none
- files:
  - src/<pkg>/domain/email.py          # crea: value object Email
- acceptance:
  - AC1 | rechaza una dirección sin '@' | tests/acceptance/test_1.1.1.py::test_ac1_no_at
  - AC2 | pasa el dominio a minúsculas | tests/acceptance/test_1.1.1.py::test_ac2_lower_domain

## Description
Value object inmutable que valida y normaliza una dirección de email…
```

- `status` ∈ `pending | in_progress | done | blocked | baseline` (`baseline`: ya construido antes del harness; solo lo revisa el phase gate).
- `layer` ∈ `domain | application | infrastructure | interfaces`.
- `depends`: `none` o ids de subtasks (`1.1.1, 1.2.3`) que deben estar `done` antes.
- `files:` los **1-3 ficheros de producción bajo `app/` o `scripts/`** (y, en la phase
  09, bajo `frontend/src/`) que crea o modifica (el harness bloquea escrituras fuera
  de ellos; una baseline lista sus ficheros de evidencia). Los tests unitarios
  (`tests/unit/`) no se declaran.
- `acceptance:` criterios observables, un test cada uno; Codex escribe esos tests.

<!-- plan:index:start -->
<!-- generated by `make plan` from docs/plan/ — do not edit by hand -->
## Plan index

19 of 20 subtasks done (19 baseline) · 0 in progress · 1 pending · 0 blocked

### Phase 01 — Base del backend · 7/7 done
(baseline) un toolchain reproducible (uv, ruff, mypy --strict, markers de pytest) y el esqueleto modular de la aplicación: create_app(), el router v1 normalizado, el layout app/domains/<domain>/<module> y la base de datos compartida, los mixins y el registro de modelos.

- **1.1 Toolchain de Python** — done
  - [x] [1.1.1 Configuración de uv, ruff y mypy estricto](phase-01-backend-foundation/1.1.1-uv-ruff-mypy-config.md) — baseline
  - [x] [1.1.2 Markers estrictos de pytest y aislamiento de los tests de base de datos](phase-01-backend-foundation/1.1.2-pytest-markers-db-skip.md) — baseline
- **1.2 Esqueleto de la aplicación** — done
  - [x] [1.2.1 Factoría de la aplicación](phase-01-backend-foundation/1.2.1-create-app-factory.md) — baseline
  - [x] [1.2.2 Router v1 normalizado](phase-01-backend-foundation/1.2.2-api-v1-router.md) — baseline
  - [x] [1.2.3 Layout de paquetes de dominio](phase-01-backend-foundation/1.2.3-domains-layout.md) — baseline
- **1.3 Capa de base de datos compartida** — done
  - [x] [1.3.1 Base declarativa y mixin de timestamps](phase-01-backend-foundation/1.3.1-declarative-base-mixins.md) — baseline
  - [x] [1.3.2 Registro central de modelos](phase-01-backend-foundation/1.3.2-model-registry.md) — baseline

### Phase 02 — Persistencia IAM · 9/9 done
(baseline) los modelos ORM de sch_iam, una baseline de Alembic solo DDL, una CLI de migración protegida que solo se ejecuta contra hosts, bases de datos y usuario de migración permitidos, y scripts protegidos para el bootstrap de catálogos, el seed demo y el rebaseline.

- **2.1 Modelos ORM de IAM** — done
  - [x] [2.1.1 Modelos ORM de sch_iam](phase-02-iam-persistence/2.1.1-sch-iam-orm-models.md) — baseline
- **2.2 Baseline de Alembic solo DDL** — done
  - [x] [2.2.1 Revisión iam_baseline de Alembic](phase-02-iam-persistence/2.2.1-alembic-iam-baseline.md) — baseline
- **2.3 CLI de migración protegida** — done
  - [x] [2.3.1 Validación del destino y de los comandos del migrator](phase-02-iam-persistence/2.3.1-migrator-target-and-commands.md) — baseline
  - [x] [2.3.2 Permisos del rol de la aplicación](phase-02-iam-persistence/2.3.2-application-role-grants.md) — baseline
- **2.4 Scripts de datos IAM protegidos** — done
  - [x] [2.4.1 Bootstrap de catálogos canónicos](phase-02-iam-persistence/2.4.1-catalog-bootstrap.md) — baseline
  - [x] [2.4.2 Seed demo de IAM](phase-02-iam-persistence/2.4.2-demo-seed.md) — baseline
  - [x] [2.4.3 Rebaseline de IAM](phase-02-iam-persistence/2.4.3-iam-rebaseline.md) — baseline
  - [x] [2.4.4 Selector de la base de datos de test](phase-02-iam-persistence/2.4.4-test-database-selector.md) — baseline
- **2.5 Sesión de base de datos en runtime** — done
  - [x] [2.5.1 Engine y factoría de sesiones](phase-02-iam-persistence/2.5.1-engine-and-session-factory.md) — baseline

### Phase 03 — Health y readiness · 3/4 done
(baseline) liveness en /api/health y readiness en /api/ready, que solo está lista cuando PostgreSQL responde y Alembic está en la head empaquetada, sin filtrar detalles internos.

- **3.1 Contratos y comprobaciones de readiness** — in progress
  - [x] [3.1.1 Esquemas de health y readiness](phase-03-health-readiness/3.1.1-health-schemas.md) — baseline
  - [x] [3.1.2 Comprobación de PostgreSQL y de la revisión de Alembic](phase-03-health-readiness/3.1.2-database-readiness-check.md) — baseline
  - [ ] [3.1.3 Readiness rechaza una revisión de Alembic distinta de la head](phase-03-health-readiness/3.1.3-readiness-rejects-revision-mismatch.md)
- **3.2 Endpoints operativos** — done
  - [x] [3.2.1 Endpoints de liveness y readiness](phase-03-health-readiness/3.2.1-health-and-ready-endpoints.md) — baseline

### Phase 04 — Entorno Docker · not broken down yet
(baseline) un stack de Docker Compose (postgres, backend, frontend, nginx, redis, worker provisional) con red interna aislada, imágenes sin root, roles de base de datos aprovisionados por servicio, un perfil de migración que ejecuta el migrator, un healthcheck del backend basado en readiness y un override solo para local.

### Phase 05 — CI del backend · not broken down yet
(baseline) tests clasificados con markers estrictos de pytest y un workflow de GitHub Actions dividido en los jobs quality, unit, db, security y compose.

### Phase 06 — Arquitectura hexagonal: piloto de usuarios IAM · not broken down yet
(baseline) el estándar hexagonal pragmático demostrado sobre el listado de usuarios IAM (tenant context, policy, repositorio, servicio, router y auditoría mínima), con los límites entre módulos verificados por tests de arquitectura.

### Phase 07 — Autenticación (OAuth2) · not broken down yet
(baseline) registro de organizaciones, login de navegador con cookie JWT HttpOnly, identidad actual, logout, CSRF, un endpoint de token OAuth2 separado, CORS explícito y rate limiting en los endpoints sensibles, con settings validados al arrancar y organizado como módulos de auth sobre el estándar hexagonal.

### Phase 08 — RBAC y tenant context · not broken down yet
autorización por roles y permisos sobre la identidad autenticada, y un tenant context obligatorio derivado de la sesión en cada endpoint protegido, de forma que ningún endpoint confíe en un organization id enviado por el cliente.

### Phase 09 — Integración con el frontend y e2e · not broken down yet
los formularios de registro de organización y de login del frontend consumen la API v1 real a través de nginx (rutas /api/v1, cookie HttpOnly y CSRF), y una suite e2e con Playwright para Python sobre pytest (marker e2e, `make e2e` y un job e2e en la CI en cada PR) verifica sobre el stack de Docker Compose el flujo completo registro → login → /me → logout, los casos negativos (credenciales incorrectas, email duplicado, petición sin CSRF, rate limit) y la autorización y el tenant context de la phase 08.

<!-- plan:index:end -->
