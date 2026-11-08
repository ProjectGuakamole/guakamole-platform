# Conventions

Code, names, and comments in **English**. Team documentation (`../docs/backend/`)
is written in Spanish.

## Style and toolchain

- **uv** for deps/environment · **ruff** (lint + format) · **mypy** strict · **pytest**.
- Code lives in `app/` and `scripts/` (not `src/`). The harness `Makefile` runs
  `make verify` (ruff, `mypy --strict .`, pytest); the root `Makefile` holds the
  team's Docker, database and test-db targets.
- PEP8 via ruff; do not format by hand.
- **Micro-task discipline**: one subtask = one atomic unit (class/function/method),
  1-3 files under `app/` or `scripts/` declared in the plan's `files:`. Enforced
  by the harness (`harness.toml` `[scope] src_dirs`).

## Naming

- Modules and functions: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE`.
- Names by intent, not by type (`list_organization_users`, not `process_data`).
- Database: schema `sch_iam`, tables `tbl_<name>`, `BIGINT` ids; public ids
  with a prefix (`usr_…`, `org_…`) are the only ids exposed by the API.
- API: versioned under `/api/v1`; operational endpoints under `/api`.

## Errors

- Module-specific exception classes (`exceptions.py`); services raise them,
  routers translate them to HTTP responses.
- Do not catch generic `Exception` except at the boundaries; never silence errors.
- Responses never reveal whether an email, user or another tenant's resource exists.

## Dependency injection

- Through the constructor. Services receive their ports (`Protocol`) as parameters;
  `dependencies.py` builds them for FastAPI.
- No mutable global state.

## Logging and audit

- **Structured** logging (`logging` with `extra=`, `app/shared/audit.py`), never `print()`
  in the application. The provisional worker's startup message is the known exception.
- Do not log secrets or PII (passwords, hashes, tokens, personal data).

## Tests

- Markers (strict): `test_unit`, `integration`, `db`, `security`, `architecture`, `slow`.
  CI runs them as separate jobs (`.github/workflows/backend-ci.yml`).
- Folders: `tests/unit/`, `tests/integration/` (PostgreSQL), `tests/security/`,
  `tests/architecture/` (AST boundary checks), and `tests/acceptance/` (Codex, black box).
- One test per observable behavior; descriptive names.
- No filesystem mocks: use `tmp_path` / `TemporaryDirectory`.
- Database tests use `TEST_DATABASE_URL` and never the application database.
