# Dev Process

> TDD, systematic debugging, planning, code review, worktrees, parallel agents.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `parse-git-status` | Parse git status into structured data: staged, modified, untracked, branch. |
| `rollback-changes` | Roll back failed workflow phases via changes logs: restore files, clean artifacts, reverse commands. |
| `run-quality-gate` | Run quality gates: type-check, build, tests, lint with configurable blocking. |
| `scaling-stage` | Letterbox wrapper for fixed-size content (video, posters, fixed mockups) — a deck-stage for non-slides. |
| `validate-plan-file` | Validate orchestrator plan files against JSON schema before workers read them. |

### Agents

- `code-reviewer`

### Commands

- `/analyze`
- `/bug-triage`
- `/changelog`
- `/code-review`
- `/parallel-dev`
- `/push`
- `/review`
- `/worktree`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install dev-process@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`dev-core` · `code-health` · `browser-testing` · `gsd`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
