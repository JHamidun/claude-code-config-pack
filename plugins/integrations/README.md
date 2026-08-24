# Integrations & DevOps

> n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, Home Assistant, webhooks.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `agent-api-server` | OpenAI-compatible HTTP server on top of the local Claude CLI — expose /v1/chat/completions to n8n, SDKs, IDEs, curl. |
| `aws-skills` | Разработка под AWS: CDK, Lambda, serverless, S3. |
| `claude-server-auth` | Авторизация Claude CLI на headless-сервере: setup-token в tmux + локальный Playwright-OAuth. |
| `deepl-pro` | Перевод текста и документов (docx/pptx/pdf/xlsx) через DeepL, глоссарии, formality. |
| `home-assistant` | Home Assistant CLI over REST + WebSocket — entity states, service calls, on/off/toggle, state history, live events. |
| `maps-places` | Places, addresses and geocoding across 11 providers (Google Places, Yandex, 2GIS, HERE, Mapbox, Foursquare, OSM and more). |
| `n8n` | n8n workflow automation: API, ноды, MCP + локальный каталог 2061 готового воркфлоу. |
| `pinecone` | Pinecone vector DB (PINECONE_API_KEY): semantic search, RAG; индексы company-<name>-bot и др. |
| `telegram-bot-toolkit` | Разработка Telegram-ботов: python-telegram-bot, Telethon, деплой; антипаттерн бот-воронки из TG Ads. |
| `webhook-receiver` | Receive webhooks (GitHub, Stripe, GitLab, JIRA, forms) on a local CLI server with HMAC signature validation and a JSONL log. |
| `zoom` | Zoom через Server-to-Server OAuth: создание и правка встреч, записи. |

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
