---
name: uptime-kuma-ops
description: "Мониторы Uptime Kuma на your-server через socket.io API: список, добавить, статус. Триггеры: «добавь монитор», «проверь мониторы», «статус-страница»."
---

# Uptime Kuma Operations

Kuma живёт на your-server в контейнере `uptime-kuma`. Публичного адреса у неё сейчас
**нет**: `status.your-domain.com` — мёртвый домен, туда ходить бесполезно.
Рабочий доступ только изнутри your-server.

## API Access

Base URL: `http://127.0.0.1:3002` (с your-server) или `http://127.0.0.1:3001` изнутри
контейнера. Логин/пароль — `UPTIME_KUMA_USERNAME` / `UPTIME_KUMA_PASSWORD`
в `~/.claude/.credentials.master.env`.

**REST API у Kuma нет** — управление идёт по socket.io. Готовый клиент лежит
внутри контейнера, поэтому скрипты удобно запускать оттуда (из `/app`, иначе
`socket.io-client` не резолвится):

```js
// login -> {ok:true}; дальше события: add, editMonitor, getMonitor,
// pauseMonitor, deleteMonitor, addNotification, testNotification
socket.emit("login", {username, password, token: ""}, cb)
```

Push-монитор, созданный через API, приходит с `pushToken: null` (в UI токен
генерирует браузер) — его надо проставить самому через `editMonitor`.

⚠️ **Канал алертов проверять отдельно.** Монитор может краснеть, а сообщение —
никуда не уходить: так и было до 12.08.2026, когда бот-токен отдавал 401 и
молчали все 20 мониторов. После любой замены бота гнать `getMe` и учебное
падение. Разбор и рабочая схема — `/opt/monitoring/README.md` на your-server.

## Operations

### List All Monitors
```bash
# Via the status page (public)
curl -s http://127.0.0.1:3002/api/status-page/heartbeat | python -m json.tool
```

### Check Monitor Status
```bash
# Get public status page data
curl -s http://127.0.0.1:3002/api/push/<monitor-token>
```

### Add Monitor (via Uptime Kuma API)
Requires authenticated session. Use the Push Monitor approach for simple checks:

```bash
# Push-based monitor (simplest)
# Add monitor in UI, get push URL, then ping it from your service:
curl "http://127.0.0.1:3002/api/push/<token>?status=up&msg=OK&ping=100"
```

### Common Monitor Types

| Type | Use Case |
|------|----------|
| HTTP(s) | Web endpoints, APIs |
| TCP Port | Database, Redis, custom services |
| Ping | Server availability |
| DNS | DNS resolution check |
| Push | Services that push their status |
| Docker | Container health |

## Typical Monitors to Set Up

1. **your-domain.com** — HTTP check, interval 60s
2. **course.your-domain.com** — HTTP check, interval 60s
3. **N8N Server** — HTTP http://YOUR_SERVER_IP:5678, interval 120s
4. **N8N Cloud** — HTTP https://your-name.app.n8n.cloud, interval 300s
5. **your-server SSH** — TCP YOUR_SERVER_IP:22, interval 120s
6. **PostgreSQL** — TCP YOUR_SERVER_IP:5432, interval 120s

## Process

1. User asks about monitoring
2. Determine operation (list/add/check/remove)
3. Execute via API or guide through UI setup
4. Verify the monitor is working
5. Report status

## Notes
- For full API access, use the Uptime Kuma REST API with socket.io
- Status page: публичного адреса нет; Kuma доступна только с your-server (http://127.0.0.1:3002)
- Consider using n8n webhook for automated alerting
