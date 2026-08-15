# Rules

> Files in `rules/` are auto-loaded by Claude Code every session.
> Справочные rules вынесены в `config/rules-ref/` — читаются по требованию, не грузят промпт.

## Catalog (авто-load)

| Rule | Description |
|------|-------------|
| `auto-learning` | Save errors, tools, decisions to memory |
| `autonomous-mode` | Work autonomously, don't ask permission |
| `context7` | Always use Context7 MCP for library docs |
| `delegation` | Task complexity levels and agent routing |
| `dont-do` | Forbidden actions and common mistakes |
| `model-selection` | Which model for which task (decision tree) |
| `models` | Указатель: актуальные алиасы Max → канон config/models.md |
| `permissions` | Security boundaries; актуальный режим — только из settings.json / `/context` |
| `personality` | Communication style and priorities |
| `quality-gates` | Mandatory checks after code changes |
| `routing` | Auto-routing: task type to tool/agent |
| `scaling` | Decision tree: when 1 agent, when orchestrator |
| `security` | API key handling, credential safety |
| `security-hardening` | Sandbox, audit logging, commercial deployment |
| `try-before-refusing` | Проверить инструментом, прежде чем сказать «не могу» |
| `user-profile` | User identity, contacts, preferences |

## Перенесено в config/rules-ref/ (справочники, по требованию)

| Rule | Куда | Выжимка-ядро (остаётся действующим) |
|------|------|-------------------------------------|
| `context-management` | → config/rules-ref/context-management.md | /clear при новой теме, замусоренном контексте, 3+ неудачных циклах дебага — перед clear сохранить learnings в память. Plan Mode при 5+ файлах / архитектурных трейдоффах — план переживает compact. Compact НЕ предлагать вслух (канон CLAUDE.md) |
| `headless-ci` | → config/rules-ref/headless-ci.md | claude -p паттерны для CI/CD |
| `hooks` | → config/rules-ref/hooks.md | Принцип «минимум hooks»: Python-хуки на частых событиях крашат Extension Host — не добавлять |
| `onboarding` | → config/rules-ref/onboarding.md | First-time setup (не для рантайма) |
| `plugins-catalog` | → config/rules-ref/plugins-catalog.md | Каталог 38 плагинов |
| `prompt-caching` | → config/rules-ref/prompt-caching.md | Не редактировать rules/ и CLAUDE.md без нужды в сессии (ломает prompt-cache); волатильное — в сообщения, не в системный промпт |
| `worktrees` | → config/rules-ref/worktrees.md | Agent isolation="worktree" для рискованных правок; чистка ТОЛЬКО `git worktree remove` (rm -rf стирает исходники по симлинкам); .env и node_modules НЕ шарятся между worktree |
