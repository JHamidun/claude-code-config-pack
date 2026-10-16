# Dev Core

> Python/JS/TS dev, database design, API docs, build fix, git workflow, architecture agents.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `api-documentation` | Документация API из кода: OpenAPI/Swagger, Postman, REST/GraphQL/gRPC. |
| `apple-developer` | Подпись Developer ID и нотаризация macOS dmg без Mac (Windows+CI, notarytool). |
| `autocad-com` | Чертежи из кода: DXF/SVG/PDF без CAD (ГОСТ-лист, штамп, альбом) и живой AutoCAD/nanoCAD по COM. |
| `beads` | Beads — git-трекер задач и багов для AI-агентов (команды bd). |
| `build-fix` | Чинит падающую сборку и ошибки типов минимальными правками до зелёного прогона. |
| `changelog-generator` | Changelog из git-коммитов: semver, Keep a Changelog, PR/issues через gh, git tag, GitHub Release. |
| `codegraph` | Граф кода: навигация и impact-анализ кодбазы (CLI codegraph). |
| `construction-agents` | Агенты-расчётчики для стройки: чертёж, раскладка, проверка по СП, смета-вилка. |
| `database-design` | Схема БД, миграции, оптимизация запросов: PostgreSQL, MongoDB, Redis; нормализация, индексы. |
| `deepwiki` | Доки любого GitHub-репо через DeepWiki/gitmcp.io и llms.txt. |
| `git-workflow` | Git: коммиты, ветки, PR, merge-конфликты, анализ истории. |
| `installer-builder` | One-click инсталляторы Windows .exe + macOS .dmg на Electron (без Mac, GitHub Actions). |
| `javascript-typescript-dev` | Разработка на JS/TS: React, Next.js, Node.js, тесты Jest/Vitest/Playwright. |
| `manus` | Автономная облачная задача в Manus (REST API v2, manus_helper.py): research, browsing, код. |
| `openwiki` | Агентная wiki кодбазы CLI openwiki (langchain-ai) + авто-PR доков в CI: openwiki/, AGENTS.md. |
| `project-bootstrap` | Заводит большой проект: интервью, спека, git и GitHub, каркас docs, бэклог bd, CI. |
| `python-fullstack-dev` | Пишет и правит Python: дефолты FastAPI/Django, ruff+mypy, pytest, чеклист N+1 и гонок. |

### Agents

- `backend-dev`
- `error-handler`
- `frontend-dev`
- `legacy-modernizer`
- `ml-specialist`
- `orchestrator`
- `senior-developer`
- `software-architect`
- `system-analyst`
- `tech-lead`

### Commands

- `/add-auth`
- `/beads-init`
- `/deploy`
- `/docs`
- `/estimate`
- `/feature-cycle`
- `/generate-api`
- `/init-project`
- `/manus`
- `/monitor-agents`
- `/orchestrate`
- `/quick-deploy`
- `/scaffold`
- `/setup-db`
- `/start-feature`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install dev-core@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`dev-process` · `code-health` · `browser-testing` · `gsd`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
