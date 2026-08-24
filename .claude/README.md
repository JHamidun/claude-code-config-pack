# ~/.claude — конфигурация пака

Это содержимое каталога `~/.claude`, которое ставит инсталлятор пака.
Обзор всего пака, режимы установки и permission model — в корневом `README.md`.

## Что внутри

| Каталог / файл | Что это |
|---|---|
| `settings.json` | Живой конфиг Claude Code: env, permissions, hooks, enabledPlugins, mcpServers |
| `rules/` | 18 правил поведения — авто-загружаются каждую сессию (+ `README.md` с их каталогом) |
| `skills/` | 314 навыков (каталог: `skills/CATALOG.md`) |
| `agents/` | 74 агента: 57 в корне + 17 воркеров в `health/`, `meta/`, `testing/` |
| `commands/` | 155 slash-команд: 98 в корне + 57 в `gsd/` |
| `hooks/` | 8 hook-скриптов (+3 теста): подключён ОДИН — `guard.js`; рядом лежат два файла, из которых он собран, 4 GSD и звуковой сигнал Stop |
| `tools/` | 28 универсальных Python-инструментов (почта, Figma, Miro, OSINT…) |
| `scripts/` | Служебные скрипты: `config_lint.py`, `sanitize_config_secrets.py`, `setup_runtime.py`… |
| `mcp.json` | Справочник готовых блоков MCP-серверов (НЕ живой конфиг — копируй в `settings.json`) |
| `templates/` | Четыре файла, которые **заполняешь собой** — см. ниже. Плюс служебные шаблоны проекта и памяти |
| `config/`, `docs/`, `prompts/`, `schemas/`, `workflows/`, `mcps/`, `get-shit-done/` | Справочники и обвязка, читаются по требованию |

## Что надо заполнить собой

Пак приезжает без чужих данных: в нём нет ни ключей, ни продукта, ни личного
контекста прежнего владельца (авторство пака указано в `LICENSE` и в манифесте
маркетплейса — это атрибуция, а не данные). Четыре шаблона в `templates/` — это
места, куда подставляешь себя. Пока они не заполнены, навыки либо переспрашивают,
либо честно говорят, что данных нет.

| Шаблон | Копировать в | Зачем | Кто читает |
|---|---|---|---|
| `templates/.credentials.master.env.example` | `~/.claude/.credentials.master.env` | Ключи к внешним сервисам | всё, что ходит наружу |
| `templates/author-profile.md` | `~/.claude/author-profile.md` | Кто ты: роль, площадки, о чём НЕ говоришь | навыки текстов от первого лица |
| `templates/voice-sample.md` | `~/.claude/voice-sample.md` | 2-3 твоих текста как образец голоса | те же + `de-ai-ify`, `author-voice` |
| `templates/business-context.md` | `~/.claude/business-context.md` | Продукт, ICP, цены, воронка, CRM | ~30 маркетинговых навыков |

Начни с ключей — без них не работает ничего внешнего. `voice-sample.md` и
`business-context.md` нужны, только когда дойдёшь до контента и маркетинга.

## Ключи

Все секреты живут в одном файле `~/.claude/.credentials.master.env` (создай его из
`templates/.credentials.master.env.example` — там полный каталог переменных с
пометками «где взять» и «что сломается без неё»). Скрипты читают его через
`os.getenv` / `load_dotenv` — ключи не хардкодятся и не коммитятся. Файл
заполняется по мере надобности: отсутствие ключа выключает один навык, а не пак.

## Защита — что здесь есть на самом деле

Пак работает в `defaultMode: bypassPermissions` (без подтверждения каждой команды),
поэтому защита встроена в конфиг, а не в диалоги:

- **`hooks/guard.js`** — ЕДИНСТВЕННЫЙ PreToolUse-хук, подключённый в `settings.json`.
  На Bash/PowerShell блокирует однозначно катастрофичные команды (`rm -rf /`,
  `DROP DATABASE` и т.п.), легитимные `rm -rf ./subdir` пропускает. На
  Write/Edit/MultiEdit применяет второй набор правил: обращения к чувствительным
  путям (`.credentials.master.env`, память, `.claude.json`). Fail-open, лог
  блокировок в `~/.claude/hooks-logs/`. Выключатель: `CC_HOOKS_OFF=1`.
- **`hooks/bash-guard.js`** и **`hooks/security-guard.js`** — два файла, из которых
  `guard.js` собран дословно; лежат рядом ради читаемого `diff` и быстрого отката.
  В `settings.json` они **не подключены**: два процесса node на каждый вызов
  инструмента стоили ~150 мс при ~3 мс самой проверки. Ищешь, где включено, — ищи
  `guard.js`.
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
