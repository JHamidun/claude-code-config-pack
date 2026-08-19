---
name: agent-api-server
description: "Claude по подписке как OpenAI API (/v1/chat/completions поверх claude CLI) для n8n/IDE."
---

# agent-api-server — Claude по подписке как OpenAI API

`~/.claude/tools/agent_api_server.py` — stdlib-only HTTP-сервер, который принимает
запросы в формате OpenAI и обслуживает их локальным `claude -p`. Оплата идёт через
подписку Claude Code (OAuth), `ANTHROPIC_API_KEY` не используется и **намеренно
вырезается** из окружения дочернего процесса.

## Направление трафика — не путать

| Инструмент | Куда | Что делает |
|---|---|---|
| Свой прокси-гейтвей к внешним провайдерам | НАРУЖУ | проксирует OpenAI/Perplexity/Runway; в пак не входит — если нужен, поднимается отдельно (например, LiteLLM) |
| **`agent-api-server`** (127.0.0.1:**8199**) | ВНУТРЬ | отдаёт Claude-по-подписке как OpenAI-совместимый эндпоинт |
| `claude-cli-runner` / `claude_cli.py` | — | разовый вызов из Python-кода, без HTTP |

## Когда использовать

- n8n-нода «OpenAI Chat Model» должна ходить в Claude без покупки API-ключа.
- Скрипт/IDE/чат-фронт (Open WebUI, LibreChat, Cursor-подобные) умеет только OpenAI-протокол.
- Нужен SSE-стрим ответа Claude в стороннее приложение.
- Нужен диалог с состоянием на стороне сервера (заголовок `X-Session-Id`).

Не использовать: когда достаточно `python claude_cli.py "prompt"`; когда нужен агент с
тулзами/памятью/кроном (это Hermes → agent-builder tooling).

## Установка / настройка

```bash
# 1. Зависимости: только Python 3.9+ (stdlib) и claude CLI
claude --version                       # 2.1.207 проверено
npm install -g @anthropic-ai/claude-code   # если CLI нет

# 2. Проверка
python ~/.claude/tools/agent_api_server.py test --model haiku

# 3. Запуск
python ~/.claude/tools/agent_api_server.py serve --port 8199
```

### Env-переменные (значения заполняет владелец; читаются из `~/.claude/.credentials.master.env`)

| Переменная | Обязательна | Смысл |
|---|---|---|
| `AGENT_API_TOKEN` | нет (ДА при host ≠ 127.0.0.1) | Bearer-токен для `/v1/*`; без него сервер на loopback пускает всех |
| `AGENT_API_MODEL` | нет | модель по умолчанию (иначе `sonnet`) |
| `AGENT_API_HOST` | нет | хост по умолчанию (иначе `127.0.0.1`) |
| `AGENT_API_PORT` | нет | порт по умолчанию (иначе `8199`) |
| `AGENT_API_TIMEOUT` | нет | таймаут одного вызова CLI, сек (иначе `600`) |
| `AGENT_API_WORKDIR` | нет | cwd для CLI (иначе `~/.claude/agent-api-workdir`) |
| `AGENT_API_MAX_CONCURRENCY` | нет | сколько CLI-процессов одновременно (иначе `4`) |
| `CLAUDE_CLI_PATH` | нет | путь к `claude`, если не находится в PATH |

## Команды

| Команда | Что делает |
|---|---|
| `serve` | поднять сервер (блокирующе) |
| `serve --port N --host H` | порт/хост (не-loopback требует `AGENT_API_TOKEN`, иначе exit 2) |
| `serve --model M` | модель по умолчанию: `opus`/`fable`/`sonnet`/`haiku` или полный id |
| `serve --allow-tools` | разрешить агенту тулзы Claude Code (Bash/Read/Edit). По умолчанию ВЫКЛ — чистая генерация текста |
| `serve --timeout 900` | бюджет на один запрос, сек |
| `serve --inherit-anthropic-env` | НЕ вырезать `ANTHROPIC_*` из env дочернего процесса (по умолчанию вырезаются) |
| `serve --quiet` / `--json` | без access-лога / JSON-баннер старта |
| `test` | самопроверка: поднять на свободном порту → `/health`, `/v1/models`, 400 на пустых messages, короткий чат, SSE-стрим → погасить |
| `test --skip-chat` | только HTTP-обвязка, без траты модельного вызова |
| `test --json` | машинный вывод `{ok, checks[]}` |
| `models` / `models --json` | что отдаёт `/v1/models` + найден ли CLI |

### HTTP API

| Метод | Путь | Примечание |
|---|---|---|
| POST | `/v1/chat/completions` | `messages[]`, `model`, `stream` (true → SSE `data: ...` + `[DONE]`) |
| GET | `/v1/models` | список моделей |
| GET | `/health` | без авторизации: `cli_found`, `cli_path`, `cli_version`, `workdir`, `uptime_s` |
| GET | `/` | короткая справка текстом |

Заголовки: `X-Session-Id: <строка ≤128>` — продолжить диалог; в ответе эхо + `X-Claude-Session-Id`
(реальный UUID сессии CLI). `Authorization: Bearer <AGENT_API_TOKEN>` — если токен задан.

## Примеры

**curl (нестримом)**
```bash
curl -X POST http://127.0.0.1:8199/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"haiku","messages":[{"role":"user","content":"Reply with exactly: PONG"}]}'
```

**curl (стрим + сессия)**
```bash
curl -N -X POST http://127.0.0.1:8199/v1/chat/completions \
  -H "Content-Type: application/json" -H "X-Session-Id: n8n-lead-42" \
  -d '{"model":"sonnet","stream":true,"messages":[{"role":"user","content":"Напиши хайку про кэш"}]}'
```

**OpenAI SDK (Python) — проверено живьём**
```python
from openai import OpenAI
c = OpenAI(base_url="http://127.0.0.1:8199/v1", api_key="not-needed")  # или AGENT_API_TOKEN
print(c.chat.completions.create(model="haiku",
      messages=[{"role":"user","content":"Reply with exactly: SDKOK"}]).choices[0].message.content)

for chunk in c.chat.completions.create(model="haiku", stream=True,
        messages=[{"role":"user","content":"Count: one two three"}]):
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**n8n**
- Нода: *OpenAI Chat Model* (или *HTTP Request* на `/v1/chat/completions`).
- Credential «OpenAI»: `Base URL` = `http://127.0.0.1:8199/v1`, `API Key` = значение `AGENT_API_TOKEN`
  (если токен не задан — любая непустая строка, поле в n8n обязательное).
- Model: вписать вручную `sonnet` / `haiku` / `fable` / `opus`.
- ⚠️ n8n в Docker: `127.0.0.1` внутри контейнера — это сам контейнер. Нужен
  `http://host.docker.internal:8199/v1`, а сервер поднимать с `--host 0.0.0.0` + `AGENT_API_TOKEN`
  (**требует проверки на конкретной инсталляции n8n владельца — не тестировалось**).
- n8n Cloud (your-name.app.n8n.cloud) до `127.0.0.1` не дотянется в принципе — нужен туннель.

## Гочи (все найдены/проверены живьём 2026-07-25)

1. **`ANTHROPIC_API_KEY` + `ANTHROPIC_CUSTOM_HEADERS` из `.credentials.master.env` ломают CLI.**
   Симптом: `API Error: Invalid header name: '{"anthropic-beta"'`, HTTP 502. Причина: `load_env()`
   тянет весь файл в окружение, а дочерний `claude` его наследует. Сервер вырезает `ANTHROPIC_*`
   (+ `CLAUDE_CODE_USE_BEDROCK/YOUR_SERVER`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION`).
   Побочный эффект того же фикса: биллинг гарантированно идёт по подписке, а не по API-ключу.
   Ломать защиту только осознанно: `--inherit-anthropic-env`.
2. **`claude_cli.py` (существующая обёртка) шлёт несуществующие флаги.** `--system` и `--max-tokens`
   в `claude` 2.1.207 нет: правильные — `--system-prompt` (замена) / `--append-system-prompt`
   (добавка), лимита токенов флагом нет. Отсюда взято только обнаружение CLI, а не сборка argv.
3. **Windows: `claude` резолвится в `claude.CMD`.** `CreateProcess` не запускает `.cmd` напрямую —
   сервер сам оборачивает в `cmd.exe /c`.
4. **Стрим требует трёх флагов сразу:** `--output-format stream-json --include-partial-messages --verbose`.
   Без `--verbose` CLI не отдаёт `stream_event`.
5. **`thinking_delta` в стрим не отдаётся** — наружу идёт только `text_delta`, иначе клиент увидит
   рассуждения как ответ.
6. **`usage.prompt_tokens` большой (десятки тысяч) даже на «привет».** Это не баг: каждый запуск CLI
   прогревает системный промпт + CLAUDE.md (cache_creation). Считать по нему деньги нельзя.
7. **Холодный старт ~8-12 с на запрос** (спавн Node-процесса + прогрев контекста). Для чат-UI это
   заметно; для n8n/бэкграунда нормально. Уменьшить: `--model haiku`.
8. **CLAUDE.md и хуки владельца всё равно подгружаются** (user-level). Отвязать полностью можно было
   бы через `--bare`, но он требует API-ключ и убивает смысл подписки. `AGENT_API_WORKDIR` управляет
   только проектным контекстом.
9. **Тулзы по умолчанию отключены** (`--tools ""`): в неинтерактивном режиме запрос разрешения
   некому подтвердить. `--allow-tools` включает их — это значит, что HTTP-клиент получает право
   выполнять Bash на машине владельца. Включать только с `AGENT_API_TOKEN`.
10. **Сессии живут в CLI, не в сервере.** `X-Session-Id` → UUIDv5 → `--session-id` (1-й ход) /
    `--resume` (далее); реестр `~/.claude/agent_api_sessions.json`. Если удалить реестр — следующий
    ход снова пойдёт как первый и потеряет историю (сама сессия CLI при этом останется на диске).
11. **В stateful-режиме на бэкенд уходит только последнее user-сообщение** — историю держит CLI.
    В stateless-режиме весь `messages[]` схлопывается в один промпт с префиксом «Conversation so far».
12. **Картинки/файлы не поддерживаются** — multimodal-части заменяются маркером
    `[image input not supported by claude-cli backend]`.
13. **Параллелизм ограничен 4** (`AGENT_API_MAX_CONCURRENCY`); при переполнении — HTTP 429 через 10 с
    ожидания. Каждый запрос — отдельный Node-процесс, не поднимать лимит бездумно.
14. **Не-loopback хост без токена = отказ стартовать** (exit 2). Это осознанно.

## Чек-лист

- [ ] `claude --version` отвечает (иначе `npm install -g @anthropic-ai/claude-code`)
- [ ] `python ~/.claude/tools/agent_api_server.py test --model haiku` → ALL CHECKS PASSED
- [ ] Порт свободен (`serve` печатает понятную ошибку и выходит с кодом 2, если занят)
- [ ] Если наружу/в Docker — задан `AGENT_API_TOKEN` и хост не loopback
- [ ] Клиент шлёт `model` из `/v1/models` (`sonnet`/`haiku`/`fable`/`opus`), а не `gpt-4o`
- [ ] Для диалога с памятью клиент шлёт стабильный `X-Session-Id`
- [ ] `--allow-tools` включён ТОЛЬКО вместе с токеном и осознанно
- [ ] Сервер не оставлен висеть после отладки (`TaskStop` / `Stop-Process`)
