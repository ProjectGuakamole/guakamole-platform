# Current session

> This file is emptied when each session closes and its summary is moved to
> `history.md`. Keep it updated **in real time**, not at the end.

- **Current subtask:** _none_   (`N.M.K`)
- **Layer:** _domain | application | infrastructure | interfaces_
- **Start:** _—_
- **Engine/role:** _leader (Claude) | implementer (Claude) | Codex_

## Plan (leader)

_3-6 bullets: which layers it touches, ports/adapters, what crosses the
boundaries. The plan itself lives in docs/plan/; no code until PLAN_APPROVED._

- ...

## Gate status

- [ ] **Plan approved by Codex** → `progress/plan_review_<N.M.K>.md` = `PLAN_APPROVED`
- [ ] **Acceptance tests written** (Codex) → `tests/acceptance/test_<N.M.K>.py` (red)
- [ ] **Implementation** → `progress/impl_<N.M.K>.md`, `make verify` green
- [ ] **Code approved by Codex** → `progress/review_<N.M.K>.md` = `APPROVED`
- [ ] **Closed by Codex** → `docs/reference/<N.M.K>-<name>.md` + `status: done` + single commit

## Log

_Each significant step: decisions, files, blockers._

- ...

## Next step

_If the session is interrupted, the first thing the next session should do._
