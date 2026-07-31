# Integrations & DevOps

> n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, server health, monitoring, Outlook.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `agent-api-server` | OpenAI-compatible HTTP server on top of the local Claude CLI — expose /v1/chat/completions to n8n, SDKs, IDEs, curl. |
| `aws-skills` | AWS development with CDK, Lambda, serverless patterns, infrastructure |
| `claude-server-auth` | Use when authenticating Claude CLI on a headless server - generates subscription tokens via tmux + local Playwright OAuth flow |
| `deepl-pro` | DeepL professional translation - text, documents, glossaries. |
| `home-assistant` | Home Assistant CLI over REST + WebSocket — entity states, service calls, on/off/toggle, state history, live events. |
| `maps-places` | Places, addresses and geocoding across 11 providers (Google Places, Yandex, 2GIS, HERE, Mapbox, Foursquare, OSM and more). |
| `n8n` | n8n workflow automation — API integration, nodes, triggers, expressions, MCP, 400+ integrations. |
| `pinecone` | Pinecone vector DB (PINECONE_API_KEY): serverless-индексы, semantic search, RAG; текущие индексы company-tm-bot, company-plus-bot и др. |
| `server-health` | Server health checks via SSH - docker, systemctl, disk, memory, logs. |
| `telegram-bot-toolkit` | Comprehensive toolkit for Telegram bot development, testing, debugging, and deployment. |
| `uptime-kuma-ops` | Manage Uptime Kuma monitors via API - list, add, update, delete, check status. |
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
