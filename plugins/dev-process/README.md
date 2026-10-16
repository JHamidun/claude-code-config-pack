# Dev Process

> TDD, systematic debugging, planning, code review, worktrees, parallel agents.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `agent-swarm` | Рой из разных моделей на одну задачу: линзы, опровержение находок, Codex воркером. |
| `parse-git-status` | Разбор вывода git status в структуру: staged, изменённые, ветка, ahead/behind. |
| `rollback-changes` | Откат упавшей фазы воркфлоу по changes-log: файлы из бэкапа, revert коммитов, чистка артефактов. |
| `run-quality-gate` | Прогон quality gate: type-check, build, tests, lint со структурным отчётом. |
| `scaling-stage` | Letterbox-обёртка контента фиксированного canvas (1920×1080): вписывается в любой viewport. |
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
