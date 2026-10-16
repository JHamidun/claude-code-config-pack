# Integrations & DevOps

> n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, Home Assistant, webhooks.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `agent-api-server` | Claude по подписке как OpenAI API (/v1/chat/completions поверх claude CLI) для n8n/IDE. |
| `aws-skills` | Разработка под AWS: CDK, Lambda, serverless, S3. |
| `claude-server-auth` | Авторизация Claude CLI на headless-сервере: setup-token в tmux + локальный Playwright-OAuth. |
| `deepl-pro` | Перевод текста и документов (docx/pptx/pdf/xlsx) через DeepL, глоссарии, formality. |
| `home-assistant` | Умный дом Home Assistant через ha_client.py: состояния, сервисы, история, события. |
| `maps-places` | Поиск мест, адресов и геокодинг: 12 провайдеров — Google Places, Yandex Geosearch, 2GIS, OSM, Airbnb. |
| `n8n` | n8n workflow automation: API, ноды, MCP + локальный каталог 2061 готового воркфлоу. |
| `pinecone` | Pinecone vector DB (PINECONE_API_KEY): serverless-индексы, semantic search, RAG. |
| `telegram-bot-toolkit` | Разработка Telegram-ботов: python-telegram-bot, Telethon, деплой; антипаттерн бот-воронки из TG Ads. |
| `webhook-receiver` | Приём вебхуков (GitHub, Stripe, формы) локальным сервером webhook_server.py: HMAC-подписи. |
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
