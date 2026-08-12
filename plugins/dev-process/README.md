# Dev Process

> TDD, systematic debugging, planning, code review, worktrees, parallel agents.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `parse-git-status` | Parse git status output into structured data showing staged, modified, and untracked files. |
| `rollback-changes` | Automatically rollback changes from failed workflow phases using changes log files. |
| `run-quality-gate` | Execute quality gate validation with configurable blocking behavior. |
| `scaling-stage` | Letterbox wrapper for fixed-size content (video, posters, fixed mockups) — a deck-stage for non-slides. |
| `validate-plan-file` | Validate that orchestrator plan files conform to expected JSON schema. |

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
