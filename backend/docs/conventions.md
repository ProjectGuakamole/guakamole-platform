# Conventions

Code, names, and comments in **English**.

## Style and toolchain

- **uv** for deps/environment · **ruff** (lint + format) · **mypy** strict · **pytest** (`pytest-asyncio` for async).
- `src/` layout. Everything goes through the `Makefile` (`make lint`, `make type`, `make test`).
- PEP8 via ruff; do not format by hand.
- **Clean-code caps enforced by ruff** (C90 + PLR09xx in `pyproject.toml`): bounded
  complexity, function length, args and branches. A monster function fails `make verify`.
- **Micro-task discipline**: one subtask = one atomic unit (class/function/method),
  1-3 files declared in the plan's `files:`. Enforced by the harness.

## Naming

- Modules and functions: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE`.
- Names by intent, not by type (`send_invoice`, not `process_data`).

## Errors

- Domain-specific exception hierarchy (`DomainError` base).
- Do not catch generic `Exception` except at the boundaries; never silence errors.
- In `interfaces/`, translate domain exceptions to HTTP responses/exit codes.

## Dependency injection

- Through the constructor. Use cases receive their ports as parameters.
- No mutable global state and no singletons.

## Logging

- **Structured** logging (`structlog` or `logging` with `extra=`), never `print()`.
- Do not log secrets or PII (passwords, tokens, personal data).

## Tests

- `tests/unit/` (Claude, inner TDD) and `tests/acceptance/` (Codex, black box).
- One test per observable behavior; descriptive names.
- No filesystem mocks: use `tmp_path` / `TemporaryDirectory`.

## ‹Project additions›

- ‹endpoint conventions, table naming, API versioning…›
