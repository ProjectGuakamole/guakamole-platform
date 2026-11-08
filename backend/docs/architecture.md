# Architecture — what "good work" means

**Pragmatic, security-first hexagonal** architecture, organized by domain
modules under `app/` (this project does not use the `src/` layout).
Dependencies point **inward**: HTTP → use case → policy / port → persistence.

The authoritative team standard is `../docs/backend/hexagonal/BACK-ARCH-HEX-BASELINE.md`
(with `module-structure.md`, `security-and-tenant-rules.md` and
`testing-strategy.md` in the same folder). This file maps it onto the harness
vocabulary; when they disagree, the team standard wins and this file is fixed.

## Layout

```
app/
  main.py                 create_app(): middleware + routers (composition root)
  api/                    operational routers (/api/health, /api/ready) + api/v1/router.py
  core/                   settings, CORS, rate limit, health checks, migrations guard
  db/                     Base, mixins, model_registry, session (engine/session factory)
  shared/                 stable cross-domain pieces (structured audit)
  domains/<domain>/<module>/
    router(s).py          interfaces: HTTP, schemas, dependencies, delegation
    schemas.py            interfaces: Pydantic v2 contracts (extra="forbid" where applicable)
    dependencies.py       composition: builds services with their collaborators
    service(s).py         application: the use case; defines its ports as Protocol
    policies.py           domain/application rules: authorization, reusable invariants
    repository|repositories.py  infrastructure: the port implementation over the ORM
    models.py             infrastructure: SQLAlchemy ORM models
    entities.py           domain data the use case works with (when ORM rows must not leak)
    audit.py              infrastructure: audit adapter for the use case's audit port
scripts/                  operational CLIs (migrate, bootstrap, demo seed, rebaseline)
alembic/                  the DDL-only baseline revision
```

## Harness layers ↔ this layout

| Harness layer | Here | May import |
|---------------|------|------------|
| **domain** | `policies.py`, `entities.py`, value types in a module | stdlib, typing; no FastAPI, no SQLAlchemy |
| **application** | `service(s).py` + its `Protocol` ports | domain; never FastAPI, `HTTPException`, `Request`, SQLAlchemy or ORM models |
| **infrastructure** | `repository`/`repositories.py`, `models.py`, `audit.py`, `app/db`, `app/core` adapters | SQLAlchemy, `app.db`, the ORM models it needs |
| **interfaces** | `router(s).py`, `schemas.py`, `dependencies.py`, `app/api`, `scripts/` | application + the dependencies that compose it |

## Dependency rules (verified by Codex and by `tests/architecture/`)

- Routers translate HTTP and delegate: no business rules, no SQLAlchemy, no
  direct repository access.
- Services define the ports they need as `Protocol` and receive them through
  the **constructor**; `dependencies.py` is the only place that wires concrete
  implementations. No global singletons beyond cached settings/engine factories.
- **ORM models do not reach services**: repositories map rows to the
  schemas/entities the use case returns. A model crosses the persistence
  boundary only inside a repository.
- No imports of another domain's routers, services or HTTP dependencies.
  Neutral `app.db`, `app.shared` and the ORM models a repository needs are allowed.
- `__init__.py` holds at most a package docstring: no imports, exports or logic.
- Adapters exist only to integrate an external provider (mail, queues, remote
  access), never to wrap internal code.

## Security and multi-tenancy

- The `TenantContext` comes from the authenticated identity and its membership;
  an `organization_id` sent by the client never authorizes an operation.
- Two levels: the policy checks identity, role and scope first; the repository
  filters by organization defensively in every operational query and mutation.
- Errors avoid cross-tenant enumeration; sensitive actions emit sanitized,
  non-blocking audit events (no tokens, passwords, secrets or needless PII).
- Auth: HS256 JWT with a secret of at least 32 bytes, `Secure` + `HttpOnly`
  cookies, CSRF on cookie-authenticated mutations, explicit CORS origins,
  bearer only for the separate `/auth/token` flow.

## Project-specific decisions

- ORM: **SQLAlchemy 2.x with sync sessions** (psycopg 3) on PostgreSQL; IAM lives
  in schema `sch_iam` with `tbl_*` tables and public ids (`usr_…`, `org_…`).
- Migrations: one DDL-only Alembic baseline; the app and the migrator use
  different database roles; catalogs and demo data are loaded by `scripts/`.
- Bounded contexts: `domains/iam` (organizations, users, departments, geography,
  access, registration) and `domains/auth` (login, logout, me, csrf, token, shared).
- External integrations today: PostgreSQL, Redis (provisioned, no consumer yet).
