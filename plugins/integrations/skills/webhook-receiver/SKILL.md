---
name: webhook-receiver
description: "Приём вебхуков (GitHub, Stripe, формы) локальным сервером webhook_server.py: HMAC-подписи. Триггеры: «поймай вебхук», «лови POST от формы»."
---

# Webhook Receiver

Локальный приёмник вебхуков: `подключился → принял → залогировал → (опционально запустил команду) → вышел`. Без gateway-бота и LLM — чистый stdlib CLI (Python 3.13, зависимостей нет).

## Когда использовать

- Поймать события GitHub (push/PR/issues), Stripe (платежи), GitLab, JIRA, отправку HTML-формы.
- Локальная отладка вебхуков: посмотреть, что реально шлёт провайдер (`tail`).
- Триггер локального скрипта по внешнему событию (payload на stdin).
- Проверить/вычислить HMAC-подпись payload'а (`verify`) — например, при отладке чужого интегратора.

**НЕ использовать для:** production-ботов с ответами через LLM (это Hermes webhook-адаптер → skill agent-builder tooling), исходящих сообщений, cron-задач.

## Установка / настройка

Зависимости: только stdlib (aiohttp НЕ нужен). Файлы:

- Инструмент: `~/.claude/tools/webhook_server.py`
- Конфиг маршрутов: `~/.claude/data/webhooks/routes.json` (создать: `routes --init`)
- Лог событий: `~/.claude/data/webhooks/YYYY-MM-DD.jsonl`

Секреты — ТОЛЬКО из env (`~/.claude/.credentials.master.env`); в routes.json хранится **имя** переменной (`secret_env`), не значение. Env-переменные (владелец заполняет значения сам, из настроек webhook у провайдера):

- `WEBHOOK_GITHUB_SECRET` — secret из GitHub → Settings → Webhooks
- `WEBHOOK_STRIPE_SECRET` — signing secret эндпоинта (`whsec_...`) из Stripe Dashboard → Webhooks
- `WEBHOOK_GITLAB_SECRET` — Secret token вебхука GitLab (если нужен gitlab)
- произвольные имена для generic-маршрутов — любое имя, указанное в `secret_env`

Формат routes.json (ключ = имя маршрута):

```json
{
  "github": {
    "path": "/hooks/github",
    "provider": "github",
    "secret_env": "WEBHOOK_GITHUB_SECRET",
    "action": {"command": "python C:/path/handler.py", "timeout": 30}
  },
  "form": {"path": "/hooks/form", "provider": "none", "action": null}
}
```

Провайдеры: `github` (X-Hub-Signature-256), `stripe` (Stripe-Signature t/v1, толеранс 300с), `gitlab` (X-Gitlab-Token), `generic` (X-Webhook-Signature = hex HMAC-SHA256 тела), `none` (без подписи — формы).

## Команды

| Команда | Что делает |
|---------|-----------|
| `serve [--port 8787] [--host 127.0.0.1] [--routes FILE] [--quiet]` | Поднять сервер (foreground). GET `/health` — статус |
| `test <route> [--payload file.json] [--port N] [--json]` | Послать на работающий сервер корректно подписанный тестовый payload |
| `routes [--init] [--force] [--json]` | Показать конфиг маршрутов; `--init` — создать образец |
| `tail [-n 20] [--route NAME] [--json]` | Последние принятые события из JSONL-лога (и результаты action) |
| `verify <provider> [--payload f] [--secret S \| --secret-env NAME] [--signature SIG] [--json]` | Вычислить заголовок подписи для payload; с `--signature` — проверить чужую подпись |

## Примеры

```bash
# Первый запуск: создать конфиг, заполнить секреты, поднять сервер
python ~/.claude/tools/webhook_server.py routes --init
python ~/.claude/tools/webhook_server.py serve --port 8787

# Smoke-тест из второго терминала (подпись считается автоматически)
python ~/.claude/tools/webhook_server.py test github

# Что прилетело за сегодня
python ~/.claude/tools/webhook_server.py tail -n 30 --route stripe

# Посчитать GitHub-подпись для файла (отладка интеграции)
python ~/.claude/tools/webhook_server.py verify github --payload event.json --secret-env WEBHOOK_GITHUB_SECRET

# Проверить присланную кем-то подпись
python ~/.claude/tools/webhook_server.py verify stripe --payload body.json --secret-env WEBHOOK_STRIPE_SECRET --signature "t=...,v1=..."
```

Action-команда получает: payload на **stdin** (сырые байты тела), env `WEBHOOK_ROUTE` и `WEBHOOK_EVENT`; выполняется в фоне (ответ провайдеру уходит сразу), rc/stdout/stderr пишутся отдельной строкой `kind=action_result` в тот же JSONL.

## Проброс наружу (упоминание, не настроено)

Сервер слушает 127.0.0.1 — чтобы GitHub/Stripe достучались, нужен туннель:

- **cloudflared** (уже используется в хозяйстве, см. companylegal): `cloudflared tunnel --url http://127.0.0.1:8787` — даст временный `https://*.trycloudflare.com`; постоянный hostname — через named tunnel в Cloudflare Zero Trust.
- **ngrok**: `ngrok http 8787`.

URL вебхука у провайдера = `https://<туннель>/hooks/<route>`. Настройка туннеля — отдельная задача, скилл её не выполняет.

## Гочи

- **JIRA**: стандартные admin-вебхуки Jira Cloud подпись НЕ шлют (требует проверки на конкретной инсталляции) — используй `provider: "none"` + секретный путь (`/hooks/jira-8f3a...`) либо `generic`, если на стороне Jira стоит прокси, добавляющий X-Webhook-Signature.
- **Stripe**: подпись считается от `{timestamp}.{raw_body}` — тело нельзя пере-сериализовывать до проверки; толеранс ±300с, при сильно съехавших часах будет `timestamp outside tolerance`.
- **GitHub**: проверяется только `X-Hub-Signature-256` (SHA-256); легаси `X-Hub-Signature` (SHA-1) игнорируется намеренно.
- Маршруты `provider: "none"` на не-loopback хосте сервер **откажется** поднимать без `--allow-insecure-public` — это защита, не баг.
- При невалидной подписи payload в лог НЕ пишется (только факт `signature_valid: false`) — неаутентифицированные данные не сохраняем.
- Значения подписей/секретов в лог не попадают никогда; в `tail` payload обрезается до 120 символов (полный — в `--json`).
- Лимит тела 1 МБ (413 сверх). Rate-limiting НЕТ — при публичном туннеле включай защиту на стороне Cloudflare.
- `serve` — foreground-процесс; для постоянной работы запускай через Task Scheduler / отдельный терминал.
- Дедупликации ретраев нет: провайдеры ретраят при таймауте — action должен быть идемпотентным (delivery id GitHub есть в логе: `headers["X-GitHub-Delivery"]`).

## Чек-лист

- [ ] `routes --init` выполнен, routes.json отредактирован под задачу
- [ ] Секреты добавлены в `~/.claude/.credentials.master.env` (имена — из `secret_env`)
- [ ] `routes` показывает `[set]` у всех секретов
- [ ] `serve` поднят, `curl http://127.0.0.1:8787/health` отвечает
- [ ] `test <route>` возвращает HTTP 200, событие видно в `tail`
- [ ] Негативный тест: POST с битой подписью → 401
- [ ] Если нужен внешний доступ — туннель настроен, URL прописан у провайдера
- [ ] Action-скрипт идемпотентен (ретраи провайдера)
