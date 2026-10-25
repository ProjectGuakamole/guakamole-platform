# AGENTS.md — Navigation map for agents

> Entry point for any agent (Claude or Codex). It is NOT a rulebook: it is a
> **map**. Read only what you need, when you need it (progressive disclosure).

## 1. Before starting (mandatory)

1. Run `make check`. If it fails, **stop** and fix the harness before touching anything.
   Exception — **plan gate**: once Codex has written the acceptance tests for the
   subtask, they are intentionally **red**, so `make verify`/`make check` are
   expected to fail on *those* tests. That is the correct state at the plan phase,
   not a harness failure. Green is required at session start, the code gate, and close.
2. Read `progress/current.md` (where the last session left off).
3. Run `make status`: the whole plan, every gate verdict and the **next step**.

## 2. Model in one line

The plan lives in `docs/plan/` (source of truth): `PLAN.md` + one file per phase +
one spec per subtask. `feature_list.json` and the PLAN.md index are **generated**
(`make plan`). Claude plans and implements; Codex reviews every plan level and
every subtask, documents, and closes (single commit). The unit of work is the
**subtask `N.M.K`**.

## 3. Repository map

| File / folder                | What it contains                                   | When to read it |
|------------------------------|----------------------------------------------------|-----------------|
| `docs/plan/PLAN.md`          | Vision, goals, scope, architecture + generated index | Always, at start |
| `docs/plan/phase-NN-<slug>.md` | One phase: title, goal, its tasks `N.M`          | Planning |
| `docs/plan/phase-NN-<slug>/` | One spec per subtask `N.M.K` (status lives here)   | Before a subtask |
| `feature_list.json`          | Generated index of the plan (do not hand-edit)     | Read-only |
| `progress/roadmap_review.md`, `progress/phase_review_<NN>.md` | Codex plan verdicts | Gate status |
| `progress/current.md`        | Current session + gate status                      | Always, at start |
| `progress/history.md`        | Append-only log                                    | Historical context |
| `docs/architecture.md`       | What "good work" means: hexagonal layers           | Before planning/implementing |
| `docs/conventions.md`        | Style, naming, errors, DI                          | Before writing code |
| `docs/verification.md`       | How to prove it works                              | Before declaring `done` |
| `docs/reference/<id>-<name>.md` | Per-subtask output docs (Codex authors)         | Reference |
| `CHECKPOINTS.md`             | Objective criteria for "correct final state"       | For review |
| `.claude/agents/`            | Claude roles (leader, implementer)                 | If you orchestrate |
| `.claude/codex/`             | Codex roles (reviewer, documenter & close)         | If you review/close |
| `harness/`                   | Harness scripts (check, gate, sync_plan, review_with_codex) | Operation |
| `src/`                       | Code (hexagonal layers)                            | To implement |
| `tests/unit/`                | Unit tests (Claude, inner TDD)                     | To implement |
| `tests/acceptance/`          | Acceptance tests (Codex, **read-only for Claude**) | Target to satisfy |

## 4. Hard rules (non-negotiable)

- **One subtask `N.M.K` at a time.** At most one leaf `in_progress`.
- **One phase at a time.** A phase is broken down only once the previous one is done.
- **Plan lives in `docs/plan/`.** Never hand-edit `feature_list.json`; run `make plan`.
- **Codex gates:** no phase breakdown without `ROADMAP_APPROVED`; no subtask without
  `PHASE_APPROVED`; no implementing without `PLAN_APPROVED`; no closing without
  `APPROVED`. Approved plans are sealed: changing them needs the gate again.
- **`tests/acceptance/` belongs to Codex.** Claude never edits it.
- **Close + commit belong to Codex.** Claude does not set `done` or commit.
- **`done` only with `make check` green.**

## 5. Flow (summary)

```
[leader: discovery, one question at a time] → PLAN.md + every phase (title + goal)
   → [Codex roadmap] → ROADMAP_APPROVED → user OK
   → [leader: break down the current phase: tasks + one spec per subtask]
   → [Codex phase NN] → PHASE_APPROVED → user OK
spec pending N.M.K
   → [leader: in_progress + make plan]
   → [Codex plan: review + write tests/acceptance/test_N.M.K.py] → PLAN_APPROVED
   → [implementer: inner TDD] → make verify
   → [Codex code: review] → APPROVED
   → [Codex close: docs/reference + status done + make plan + progress + ONE commit]
   → make status → user OK → next N.M.K (phase done → break down the next phase)
```

## 6. If you get stuck

Re-read the relevant section of `docs/`. If a tool does not do what you expect,
**do not invent a workaround**: document the blocker in `progress/current.md`
with status `blocked` and stop the session.
