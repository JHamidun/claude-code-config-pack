# Dev Process

> TDD, systematic debugging, planning, code review, worktrees, parallel agents.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `parse-git-status` | Разбор вывода git status в структуру: staged, изменённые, ветка, ahead/behind. |
| `rollback-changes` | Откат упавшей фазы воркфлоу по changes-log: восстановление файлов, чистка артефактов, отмена команд. |
| `run-quality-gate` | Прогон quality gate: type-check, build, tests, lint со структурным отчётом. |
| `scaling-stage` | Letterbox wrapper for fixed-size content (video, posters, fixed mockups) — a deck-stage for non-slides. |
| `validate-plan-file` | Проверка plan-файлов оркестратора по JSON-схеме до чтения воркерами. |

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
