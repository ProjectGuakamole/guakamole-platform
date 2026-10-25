# CHECKPOINTS — Final-state evaluation

> Objective criteria that Codex walks through marking `[x]`/`[ ]` before closing
> a subtask `N.M.K`. It rejects the close if any box in C1–C6 is left empty.

## C1 — The harness is complete
- [ ] Base files: `AGENTS.md`, `CLAUDE.md`, `Makefile`, `CHECKPOINTS.md`, `docs/plan/PLAN.md`.
- [ ] Docs: `docs/architecture.md`, `docs/conventions.md`, `docs/verification.md`.
- [ ] Symlinks installed: `.claude/agents`, `.claude/codex`, `harness/`; dirs `docs/plan`, `docs/reference`.
- [ ] `make check` finishes with exit 0 (includes plan↔feature_list sync).

## C2 — The state is consistent
- [ ] At most one leaf `in_progress` in the plan.
- [ ] `feature_list.json` is in sync with `docs/plan/` (`make plan` not pending).
- [ ] The worked subtask has `plan_review_<N.M.K>.md` = `PLAN_APPROVED`.
- [ ] Every `done` leaf has `review_<N.M.K>.md` = `APPROVED`.
- [ ] `progress/current.md` describes the active session (no leftover junk).

## C3 — The hexagonal architecture is respected
- [ ] `src/.../domain/` does not import FastAPI/Django/SQLAlchemy/infra-Pydantic/external clients.
- [ ] Ports in `application/` (`Protocol`/ABC); adapters in `infrastructure/`.
- [ ] DI through the constructor; no global singletons.
- [ ] The ORM model is not used as a domain entity (there is mapping in infra).

## C4 — Quality and security
- [ ] `make verify` green (ruff + strict mypy + pytest).
- [ ] **SOLID / clean code**: single responsibility; no monster functions (ruff
      C90/PLR09xx caps pass); **DRY** — no duplicated logic, reuses what exists.
- [ ] **Micro-task scope**: only the subtask's declared `files:` (1-3) were touched.
- [ ] No debug `print()`; structured logging.
- [ ] Boundary validation (Pydantic v2 / serializers).
- [ ] No concatenated SQL, no secrets in code, no logging of PII/tokens.

## C5 — Verification is real
- [ ] `tests/acceptance/test_<N.M.K>.py` exists, derives from the subtask's acceptance, and passes.
- [ ] **1:1 traceability**: each criterion `ACn` has its `test_ac<n>_<slug>`. No orphan criterion.
- [ ] There are `tests/unit/` covering the design; they are not trivial.
- [ ] Tests use `tmp_path`/`TemporaryDirectory`, not fs mocks.

## C6 — The close is correct
- [ ] `docs/reference/<N.M.K>-<name>.md` written with the required structure:
      frontmatter (`id`, `alias`, `tags`, `date`) + the five `<!-- section: … -->`
      anchors (concept/planning/execution/problems/files). `doc_gate` must pass.
- [ ] `status: done` set in `docs/plan/`; `feature_list.json` regenerated.
- [ ] `progress/history.md` has an entry for the subtask.
- [ ] Single commit: `<type>(<scope>): <what> [N.M.K]` + `Plan:` footer, **no agent attribution**.
