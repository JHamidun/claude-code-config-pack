# Integrations & DevOps

> n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, server health, monitoring, Outlook.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `agent-api-server` | OpenAI-compatible HTTP server on top of the local Claude CLI — expose /v1/chat/completions to n8n, SDKs, IDEs, curl. |
| `aws-skills` | AWS development: CDK, Lambda, serverless patterns, S3, infrastructure as code. |
| `claude-server-auth` | Authenticate Claude CLI on a headless server: subscription setup-token via tmux + local Playwright OAuth. |
| `deepl-pro` | DeepL translation of text and documents (docx/pptx/pdf/xlsx), glossaries, formality. |
| `home-assistant` | Home Assistant CLI over REST + WebSocket — entity states, service calls, on/off/toggle, state history, live events. |
| `maps-places` | Places, addresses and geocoding across 11 providers (Google Places, Yandex, 2GIS, HERE, Mapbox, Foursquare, OSM and more). |
| `n8n` | n8n workflow automation: API, nodes, triggers, expressions, MCP, 400+ integrations; Meta CAPI server-side event recipes. |
| `pinecone` | Pinecone vector DB (PINECONE_API_KEY): serverless-индексы, semantic search, RAG, embeddings. |
| `runbook` | Операционные процедуры флота your-server: «бот молчит», рестарт агента, крон не отработал — каждая с точкой отката. |
| `server-health` | Server health via SSH: docker, systemctl, disk, memory, logs. |
| `telegram-bot-toolkit` | Разработка Telegram-ботов: python-telegram-bot, Telethon, деплой; антипаттерн бот-воронки из TG Ads. |
| `uptime-kuma-ops` | Uptime Kuma monitors via API: list, add, update, delete, check status. |
| `webhook-receiver` | Receive webhooks (GitHub, Stripe, GitLab, JIRA, forms) on a local CLI server with HMAC signature validation and a JSONL log. |
| `yandex-forms` | Create Yandex Forms (surveys, questionnaires) programmatically instead of clicking through every question by hand. |
| `zoom` | Zoom meetings management — create, list, update, delete meetings and manage recordings via Server-to-Server OAuth API |

### Agents

- `devops-engineer`
- `integration-dev`

### Commands

- `/bot-debug`
- `/bot-deploy`
- `/bot-test`
- `/domain-dns-ops`
- `/outlook`
- `/translate`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install integrations@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`google-workspace` · `session-tools` · `social-posting`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
