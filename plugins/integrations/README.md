# Integrations & DevOps

> n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, server health, monitoring, Outlook.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `aws-skills` | AWS development with CDK, Lambda, serverless patterns, infrastructure |
| `claude-server-auth` | Use when authenticating Claude CLI on a headless server - generates subscription tokens via tmux + local Playwright OAuth flow |
| `deepl-pro` | DeepL professional translation - text, documents, glossaries. |
| `n8n` | n8n workflow automation - API integration, nodes, triggers, expressions, MCP. |
| `pinecone` | Pinecone Vector Database Skill |
| `senior-devops` | Comprehensive DevOps skill for CI/CD, infrastructure automation, containerization, and cloud platforms (AWS, GCP, Azure). |
| `server-health` | Server health checks via SSH - docker, systemctl, disk, memory, logs. |
| `telegram-bot-toolkit` | Comprehensive toolkit for Telegram bot development, testing, debugging, and deployment. |
| `uptime-kuma-ops` | Manage Uptime Kuma monitors via API - list, add, update, delete, check status. |
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

`google-workspace` · `session-tools`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
