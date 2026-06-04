---
name: uptime-kuma-ops
description: Manage Uptime Kuma monitors via API - list, add, update, delete, check status. Use when user asks about "мониторинг", "uptime", or status page management.
---

# Uptime Kuma Operations

Manage monitors on Uptime Kuma instance at https://status.your-domain.com

## API Access

Base URL: `https://status.your-domain.com`
Auth: Login required via API

## Operations

### List All Monitors
```bash
# Via the status page (public)
curl -s https://status.your-domain.com/api/status-page/heartbeat | python -m json.tool
```

### Check Monitor Status
```bash
# Get public status page data
curl -s https://status.your-domain.com/api/push/<monitor-token>
```

### Add Monitor (via Uptime Kuma API)
Requires authenticated session. Use the Push Monitor approach for simple checks:

```bash
# Push-based monitor (simplest)
# Add monitor in UI, get push URL, then ping it from your service:
curl "https://status.your-domain.com/api/push/<token>?status=up&msg=OK&ping=100"
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
- Status page: https://status.your-domain.com
- Consider using n8n webhook for automated alerting
