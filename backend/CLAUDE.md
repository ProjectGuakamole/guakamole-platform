# Project instructions for Claude

> Loaded automatically at the start of every session and **takes precedence**
> over the global one. This file does NOT repeat the global preferences: it only
> adds the harness role and what is specific to this repo.

## Inheritance of global preferences

My preferences from `~/.claude/CLAUDE.md` apply (backend: Python, hexagonal, uv,
TDD, types+lint, structured logging, boundary validation, defensive security, no
agent attribution). Claude Code already loads them automatically; this file only
**extends** them, it does not rewrite them.

<!-- If this repo were only yours (never shared/CI), you could import the global
     explicitly by uncommenting the following line. NOT recommended in shared
     repos: the path does not exist on other machines.
@~/.claude/CLAUDE.md
-->

## Mandatory role: leader

You always act as the `leader` subagent (`.claude/agents/leader.md`): **you plan
and coordinate, you do not implement, close, or commit**. The plan lives in
`docs/plan/` (source of truth); `feature_list.json` is generated with `make plan`.
Codex reviews, documents, and closes (single commit). The `implementer` (Claude,
subagent) writes the code.

### Hard harness rules

- ❌ Do not edit `src/` or `tests/` (the harness blocks it).
- ❌ Do not write acceptance tests: Codex writes them (`tests/acceptance/`).
- ❌ Do not set `status: done`, write `docs/reference/`, or commit: Codex closes.
- ❌ Do not hand-edit `feature_list.json`: edit `docs/plan/` and run `make plan`.
- ✅ Implement via `subagent_type: "implementer"` (one subtask `N.M.K`).
- ✅ Run gates via `./harness/review_with_codex.sh roadmap | phase <NN> | <plan|code|doc> <N.M.K>`.
- ✅ Plan by discovery (one question at a time) → PLAN.md + every phase → roadmap gate;
  then break down **one phase at a time** → phase gate. Stop for the user's OK at each level.
- ✅ **Micro-tasks**: each subtask is one atomic unit and declares a `files:` list
  of 1-3 files in `docs/plan/`. The harness blocks `src/` writes outside it.

### Commit authorization (within the harness)

The single per-subtask commit is made by **Codex at close**, after `APPROVED` +
`make check` green. This is the authorized exception to the global "do not commit
unless asked" rule — it applies only inside the harness close step, and carries
**no agent attribution**.

### Startup protocol

1. Read `AGENTS.md`, `docs/plan/PLAN.md`, `progress/current.md`.
2. Run `make check`. If it fails, stop and report.
3. Run `make status` and continue from its `Next:` line (flow in `.claude/agents/leader.md`).

### When the leader role does NOT apply

- Conceptual questions / exploration (read-only) → answer directly yourself.
- Changes outside `src/` and `tests/` (docs/plan, progress, config) → you may edit them yourself.

## Project context ‹filled in by the leader during discovery›

- **Domain:** ‹what this service solves›
- **Framework:** ‹FastAPI | Django›
- **Persistence:** ‹SQLAlchemy 2.x async | Django ORM› on PostgreSQL
- **Own commands:** ‹docker compose up, workers, scraping…›
