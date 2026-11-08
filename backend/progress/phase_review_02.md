# Phase review — phase 02

**Verdict:** PHASE_APPROVED

## Analysis
- Coverage: tasks 2.1–2.5 and their nine specs cover IAM ORM models, the DDL baseline, guarded migration and data CLIs, and runtime sessions.
- Scope: all nine specs describe pre-existing `baseline` work. Their declared production evidence exists; the baseline exception permits 2.1.1's six model files and Alembic files outside `app/`. The only file shared by specs, `app/core/migrations.py`, is claimed by 2.3.1 and 2.3.2 with an explicit dependency.
- Dependencies: the graph is acyclic. ORM models precede the Alembic baseline; the baseline precedes migration and data operations. Runtime sessions depend on the models. Phases 03–09 still contain only title and goal.
- Acceptance: each criterion names one existing test function. The criteria describe observable contracts. The supplied `make check` exited 2 only because the phase 02 plan seal requires this re-review; lint, formatting, strict types, 375 tests, plan sync, gate consistency, and documentation passed. The 79 skipped tests include PostgreSQL integration evidence, so those behaviors were checked against code and test definitions but were not executed in this run.

## Per subtask
- 2.1.1: ok — the six declared model modules define eleven `sch_iam` tables; the named tests cover table inventory, case-insensitive indexes, organization-scoped department relations, and revocation JTI constraints.
- 2.2.1: ok — `alembic/versions/iam_baseline.py` has one root revision with schema/table/index DDL; `alembic/env.py` requires an injected connection, and `alembic.ini` has only a placeholder URL. All four named tests exist.
- 2.3.1: ok — `app/core/migrations.py` allowlists commands and validates environment, host, database, and user before creating an engine; `scripts/migrate.py` delegates to it. All five named tests exist.
- 2.3.2: ok — `app/core/migrations.py:136` grants IAM data access and `SELECT` on `public.alembic_version`, without application DDL grants. Both named tests exist.
- 2.4.1: ok — `app/core/iam_bootstrap.py` defines canonical catalogs and conflict-safe insertion; `scripts/bootstrap_iam.py` validates a dedicated target and sanitizes failures. All three named tests exist.
- 2.4.2: ok — `scripts/seed_demo_iam.py` validates its fixture and dedicated target, checks the catalogs, and guards seed and clear operations. The declared fixture and all four named tests exist.
- 2.4.3: ok — `app/core/iam_rebaseline.py` requires confirmation and a local dedicated database in development or test; `scripts/rebaseline_iam.py` is an explicit CLI. All five named tests exist.
- 2.4.4: ok — `app/core/test_database.py` requires an explicit local PostgreSQL URL with an `_test` database name. Both named tests exist.
- 2.5.1: ok — `app/db/session.py:18` caches the engine and session factory, obtains a validated settings URL, and closes the yielded session in `finally`. The named HTTP integration test uses the production database dependency without an override.
