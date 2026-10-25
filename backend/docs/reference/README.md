# Reference documentation

> Per-feature output documentation, **authored by Codex** at feature close
> (after `APPROVED`). One file per task/subtask, named `<id>-<name>.md`, where
> `<id>` matches the id in `docs/plan/` and `feature_list.json`.

- This is **output** documentation ("reference" in the Diátaxis sense): what was
  built, how it works, design decisions, contracts.
- It is durable and versioned — not session state (that lives in `progress/`).
- Claude does not write here; Codex does, as part of the close.

Examples:

```
docs/reference/1.1-user_registration.md
docs/reference/1.1.2-sqlalchemy_user_adapter.md
```

## Required structure (enforced by `doc_gate`)

Each file is an Obsidian-style note. `make check` blocks the close if the
frontmatter keys or any of the five section anchors are missing:

```markdown
---
id: <N.M.K>
alias:
  - <alias>
tags:
  - <tags>
date: <yyyy-mm-dd HH:MM>
---

<!-- section: concept -->    ## didactic explanation (professor-style, examples/graphics)
<!-- section: planning -->   ## how it was planned
<!-- section: execution -->  ## how it was executed
<!-- section: problems -->   ## problems & resolution
<!-- section: files -->      ## files created/modified (Obsidian [[links]])
```

Keep the `<!-- section: … -->` anchors verbatim. See `.claude/codex/documenter.md`
for the full template. The `concept` section may be as long as needed.
