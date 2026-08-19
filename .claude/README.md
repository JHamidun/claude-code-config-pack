# ~/.claude — конфигурация пака

Это содержимое каталога `~/.claude`, которое ставит инсталлятор пака.
Обзор всего пака, режимы установки и permission model — в корневом `README.md`.

## Что внутри

| Каталог / файл | Что это |
|---|---|
| `settings.json` | Живой конфиг Claude Code: env, permissions, hooks, enabledPlugins, mcpServers |
| `rules/` | 19 правил поведения — авто-загружаются каждую сессию |
| `skills/` | 287 навыков (каталог: `skills/CATALOG.md`) |
| `agents/` | 75 агентов: 58 в корне + 17 воркеров в `health/`, `meta/`, `testing/` |
| `commands/` | 156 slash-команд: 99 в корне + 57 в `gsd/` |
| `hooks/` | 7 hook-скриптов (+1 тест): 2 защитных, 4 GSD, звуковой сигнал Stop |
| `tools/` | 25 универсальных Python-инструментов (почта, Figma, Miro, OSINT…) |
| `scripts/` | Служебные скрипты: `config_lint.py`, `sanitize_config_secrets.py`, `setup_runtime.py`… |
| `mcp.json` | Справочник готовых блоков MCP-серверов (НЕ живой конфиг — копируй в `settings.json`) |
| `config/`, `docs/`, `templates/`, `prompts/`, `schemas/`, `workflows/`, `mcps/`, `get-shit-done/` | Справочники и обвязка, читаются по требованию |
| `.credentials.master.env.example` | Шаблон файла ключей — скопируй в `.credentials.master.env` и заполни нужное |

## Ключи

Все секреты живут в одном файле `~/.claude/.credentials.master.env` (создай его из
`.credentials.master.env.example`). Скрипты читают его через `os.getenv` /
`load_dotenv` — ключи не хардкодятся и не коммитятся. Файл заполняется по мере
надобности: отсутствие ключа выключает один навык, а не пак.

## Защита — что здесь есть на самом деле

Пак работает в `defaultMode: bypassPermissions` (без подтверждения каждой команды),
поэтому защита встроена в конфиг, а не в диалоги:

- **`hooks/bash-guard.js`** — PreToolUse-guard: блокирует однозначно катастрофичные
  shell-команды (`rm -rf /`, `DROP DATABASE` и т.п.), легитимные
  `rm -rf ./subdir` пропускает. Fail-open, лог блокировок в
  `~/.claude/hooks-logs/`. Выключатель: `CC_HOOKS_OFF=1`.
- **`hooks/security-guard.js`** — PreToolUse-guard: следит за обращениями к
  чувствительным путям (`.credentials.master.env`, память, `.claude.json`).
- **`permissions.deny`** в `settings.json` — жёсткий запрет на `rm -rf /`,
  `DROP DATABASE/TABLE/SCHEMA` и подобное независимо от режима.
- **Skill `leak-scan`** — прогон каталога перед публикацией: ищет ПД, ключи,
  внутренние имена. Второй сценарий — проверка чужого скилла перед установкой
  на prompt-injection.
- **Skill `privacy-filter`** — обезличивание текста перед отправкой во внешние модели.
- **`scripts/sanitize_config_secrets.py`** — вычистка секретов из конфига.

Чего здесь НЕТ: обёрток над бинарём Claude (`claude-wrapper.*`), `.claudeignore`
и отдельных чеклистов безопасности. Ранняя версия этого README описывала их —
они так и не были частью пака.

## Установка и проверка

```bash
python ~/.claude/scripts/setup_runtime.py --check   # чего не хватает (браузер Playwright, маркетплейсы, node_modules)
python ~/.claude/scripts/setup_runtime.py           # доустановить (идемпотентно)
python ~/.claude/scripts/config_lint.py             # честные счётчики и связность конфига
```
