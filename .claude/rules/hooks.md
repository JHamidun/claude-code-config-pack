# Hooks Reference

> Документация по всем настроенным hooks в settings.json.
> Последнее обновление: см. git history

## Active Hooks

### PreToolUse (блокировка опасных команд)

| Matcher | Что делает |
|---------|------------|
| `Bash(rm -rf)` | БЛОКИРУЕТ rm -rf команды |
| `Bash(DROP DATABASE)` | БЛОКИРУЕТ DROP DATABASE |
| `Bash(DROP TABLE)` | БЛОКИРУЕТ DROP TABLE |
| `Bash(git commit)` | Напоминает формат Conventional Commits |
| `Write\|Edit` (GSD) | gsd-prompt-guard.js — защита GSD файлов |

### PostToolUse

| Matcher | Что делает |
|---------|------------|
| `Bash\|Edit\|Write\|MultiEdit\|Agent\|Task` | gsd-context-monitor.js — мониторинг контекста GSD |

### SessionStart

| Hook | Что делает |
|------|------------|
| gsd-check-update.js | Проверка обновлений GSD при старте |

### CwdChanged (v2.1.83+, NEW)

| Hook | Что делает |
|------|------------|
| VSCode http hook | Уведомляет IDE о смене рабочей директории |

### FileChanged (v2.1.83+, NEW)

| Hook | Что делает |
|------|------------|
| VSCode http hook | Уведомляет IDE об изменении файлов (реактивное обновление) |

### Stop

| Hook | Что делает |
|------|------------|
| PowerShell beep | Звуковой сигнал окончания сессии (800Hz + 1000Hz) |

## Удалённые хуки (v9.0 оптимизация)

| Хук | Причина удаления |
|-----|-----------------|
| SessionStart (vector_memory.py) | Python + vector store = 5-15с на старт сессии |
| SessionStart (cat session_cache.txt) | Не реализован в settings.json |
| UserPromptSubmit (prompt_router.py) | Python на каждый промпт = latency |
| PostToolUse Write/Edit (git add) | `$FILE` не работает на Windows |
| SubagentStart (PowerShell logger) | +0.5с на каждый субагент |
| SubagentStop (PowerShell logger) | +0.5с на каждый субагент |
| Stop (auto_title_session.py) | Не критичен, добавляет latency |
| Stop (vector_memory.py save) | Тяжёлая операция на каждый Stop |

## Новые hook events в v2.1.83+ (доступны после обновления до v2.1.92)

| Event | Когда срабатывает | Для чего |
|-------|------------------|----------|
| `CwdChanged` | Смена рабочей директории | Реактивная загрузка контекста проекта |
| `FileChanged` | Изменение файлов | Автообновление IDE, hot reload |
| `TaskCreated` | Создание субагента | Логирование и мониторинг субагентов |
| `PermissionDenied` | Auto mode отклонил действие | Можно вернуть `{retry: true}` для повтора |
| `WorktreeCreate` | Создание worktree | Поддерживает `type: "http"` для webhook |

### "defer" в PreToolUse (v2.1.90+)

Headless сессии (`claude -p`) могут паузиться на tool call:
- Hook возвращает `{decision: "defer"}` → сессия приостанавливается
- Возобновление: `claude -p --resume` → hook перевычисляется
- Полезно для CI/CD: пауза на опасных командах, human approval

## Принцип: минимум hooks

После v8.0 → v9.0 оптимизации выяснилось:
- **Python hooks на частые события = Extension Host crashes**
- (removed plugin) плагин отключён по той же причине
- Оставлены только блокировки, GSD мониторинг и beep
- HTTP hooks (VSCode extension, порт VSCODE_PORT) — лёгкие, не вызывают проблем

## Файлы (для ручного использования)

| Файл | Путь | Как использовать |
|------|------|------------------|
| vector_memory.py | `${WORKSPACE}/tools/vector_memory.py` | Вручную: `python ... search/learn/stats` |
| prompt_router.py | `~/.claude/tools/prompt_router.py` | Существует, но не подключён как hook |

## Ручные команды памяти

```bash
# Поиск по памяти
python ${WORKSPACE}/tools/vector_memory.py search "запрос"

# Сохранить знание
python ${WORKSPACE}/tools/vector_memory.py learn "контент" "категория"

# Статистика памяти
python ${WORKSPACE}/tools/vector_memory.py stats
```

## MCP серверы

Глобально активен 1 local MCP сервер: filesystem. chrome-devtools — встроен в VSCode расширение.
10 cloud MCP серверов от подписки Max (Airtable, Canva, Context7, Figma, Gamma, Gmail, Google Calendar, Granola, Mermaid Chart, n8n).
context7 и github — также через плагины. Остальные доступны через `mcp.json`.
