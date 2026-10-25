# Makefile — single source of truth for the commands. Always uv.
# Customize it per project (add docker, scraping targets, etc.),
# but keep lint/type/test/verify/check/plan as the contract the harness uses.
.PHONY: lint type test verify check plan status env-check install-dev

# Colored status tags (ok/skip/warn/fail), plain when not on a terminal.
STATUS := ./harness/status.sh

lint:
	uv run ruff check .
	uv run ruff format --check .

type:
	uv run mypy --strict .

# pytest exits 5 when it collects nothing: a fresh project is green, not red.
test:
	@uv run pytest; rc=$$?; \
	if [ $$rc -eq 5 ]; then $(STATUS) ok "no tests yet"; else exit $$rc; fi

# The "all green" the harness requires before approving/closing.
verify: lint type test

# Regenerate the derived feature_list.json from docs/plan/ (source of truth).
plan:
	python3 harness/sync_plan.py

# The whole plan at a glance: done / in progress / pending, gates, next step.
status:
	@python3 harness/plan_status.py

# Single entry point for agent and hooks: toolchain + harness invariants.
# Both halves always run (-k keeps verify going past a red step), so one run
# reports every failure; the result is red if either half is red.
check:
	@rc=0; \
	$(MAKE) --no-print-directory -k verify || rc=1; \
	./harness/check.sh || rc=1; \
	exit $$rc

# Toolchain presence check, used by harness/check.sh (language-agnostic entry point).
env-check:
	@command -v uv >/dev/null 2>&1 || { $(STATUS) fail "uv not found"; exit 1; }
	@$(STATUS) ok "uv -> $$(uv --version)"

install-dev:
	uv sync
