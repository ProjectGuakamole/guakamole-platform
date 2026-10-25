# Verification — how to prove it works

> In multi-agent systems you do not evaluate the path, you evaluate the
> destination. Nothing is `done` without **executable** verification.

## Test levels

1. **Acceptance** (`tests/acceptance/test_<N.M.K>.py`, Codex): black box, derived
   from the subtask's acceptance criteria. They are the oracle; Claude does not
   edit them. They must pass.
2. **Unit** (`tests/unit/`, Claude): white box, they guide the design (TDD).

## The contract: `make check`

```
make plan     # regenerate feature_list.json from docs/plan/ (source of truth)
make verify   # uv run ruff check + ruff format --check + mypy src + pytest
make check    # verify + ./harness/check.sh (plan↔index sync + invariants + gate consistency)
```

A subtask is verifiable when:

- `make verify` is green (lint + type + test, including acceptance and unit).
- The Codex code review is `APPROVED` (`progress/review_<N.M.K>.md`).
- The relevant `CHECKPOINTS.md` items are `[x]`.

## Manual verification (when applicable) ‹fill in›

- ‹start the service: `make run` / `docker compose up` and hit the endpoint›
- ‹test data, fixtures, seeds›
