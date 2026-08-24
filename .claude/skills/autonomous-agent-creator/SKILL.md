---
name: autonomous-agent-creator
description: "Автономные агенты на Hermes (Python) и OpenClaw (TS): крон, плагины, Docker-деплой. Триггеры: «создай агента», «бот с нуля». НЕ MCP→mcp-builder; операции/дебаг бота→openclaw-ops."
metadata:
  type: guide
  triggers:
    - "создай агента"
    - "новый автономный бот"
    - "autonomous agent"
    - "hermes agent"
    - "openclaw бот"
    - "бот с нуля"
    - "deploy bot"
    - "create bot"
    - "декомпозируй промпт агента"
    - "агент разросся"
    - "промпт агента раздулся"
    - "большие данные в агента"
---

# Autonomous Agent Creator

## Что понадобится

- **Свой VPS** (или локальный Docker) — агент живёт 24/7, ноутбук для этого не годится.
  Подъём с нуля и защита сервера — `references/vps-ssh-hardening.md`.
- **Свой `TELEGRAM_BOT_TOKEN`** от @BotFather — бесплатно.
- **Свой ключ модели.** Дешёвый старт — `GOOGLE_API_KEY` (AI Studio, есть бесплатный лимит),
  каталог моделей — `references/gemini-api-models.md`. Дальше по вкусу: OpenAI, Anthropic,
  локальная модель через OpenAI-совместимый endpoint.
- **Docker + docker compose** на сервере.

Оплату провайдера обходить не надо и нельзя: агент, который живёт на чужой подписке,
живёт до первой проверки. Считай стоимость модели частью стоимости бота.

---

## Decision Tree: Which Engine?

| Factor | Hermes | OpenClaw |
|--------|--------|----------|
| Language | Python | TypeScript |
| Best for | Domain-heavy (fitness, sales, education) | Tool-heavy (browser, MCP, code exec) |
| Plugin system | Python plugins with DB access | TypeScript extensions with TypeBox schemas |
| Browser | Playwright (built-in) | Sandbox-browser (Docker + CDP + noVNC) |
| Cron | Python scheduler (croniter), script-only mode | JSON config, agentTurn payload |
| Memory | MEMORY.md (section delimiter, 2200 char) | Built-in memory_search/write |
| Platforms | 18+ (TG, Discord, WhatsApp, Signal, Email, API server, WeChat, Feishu...) | Telegram primary, API secondary |
| Model support | Any OpenAI-compatible + Anthropic + Bedrock + custom | OpenAI-compatible via auth profiles |
| Docker | s6-overlay PID1, UID remap, skill sync | Simple node container, chown 1000:1000 |
| GitHub stars | 64K | N/A (closed source, commercial) |

**Choose Hermes when:**
- Need custom Python logic (DB queries, ML inference, complex calculations)
- Need 3+ platforms simultaneously
- Want model flexibility (Claude, GPT, Gemini, local)
- Need advanced cron (script-only mode, context chaining)

**Choose OpenClaw when:**
- Need browser automation (LinkedIn, web scraping, e2e testing)
- Want TypeScript + strict typing
- Need sandboxed execution
- Already have OpenClaw infrastructure

---

## Quick Start: Hermes Agent (10 steps)

1. Get Hermes image: `docker pull ghcr.io/hermes-agent/hermes:latest` or build locally
2. Create data volume: `docker volume create hermes-mybot-data`
3. Write config.yaml (see references/hermes-config-reference.md)
4. Write SOUL.md personality file
5. (Optional) Create plugin in `plugins/` directory
6. Write docker-compose.yml (see references/deployment-docker.md)
7. Set env vars (API keys, TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USERS)
8. Start: `docker compose up -d`
9. Verify: `docker logs hermes-mybot --tail 20`
10. Test: send message to bot in Telegram

**Minimal config.yaml (recommended Gemini 3.5 Flash via direct API — no OAuth, no rotation, no quota wars):**
```yaml
model:
  default: gemini-3.5-flash
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta/openai   # OpenAI-compat shim

personality:
  default: "assistant"
  personalities:
    assistant: |
      You are a helpful AI assistant. Direct, concise, no fluff.

platforms:
  telegram:
    reply_to_mode: "first"

verbose: false
```

**Minimal docker-compose.yml:**
```yaml
services:
  hermes-mybot:
    image: hermes-agent:local
    container_name: hermes-mybot
    restart: unless-stopped
    network_mode: host
    environment:
      HERMES_HOME: /opt/data
      TELEGRAM_BOT_TOKEN: "${TELEGRAM_BOT_TOKEN}"
      TELEGRAM_ALLOWED_USERS: "${TELEGRAM_ALLOWED_USERS}"
      TELEGRAM_HOME_CHANNEL: "${TELEGRAM_HOME_CHANNEL}"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      GOOGLE_API_KEY: "${GOOGLE_API_KEY}"
    volumes:
      - hermes-mybot-data:/opt/data
    command: ["gateway", "run"]

volumes:
  hermes-mybot-data:
    external: true
```

---

## Quick Start: OpenClaw Agent (10 steps)

1. Create volumes:
   ```bash
   docker volume create openclaw-mybot-config
   docker volume create openclaw-mybot-workspace
   docker run --rm -v openclaw-mybot-config:/data alpine chown -R 1000:1000 /data
   docker run --rm -v openclaw-mybot-workspace:/data alpine chown -R 1000:1000 /data
   ```
2. Write openclaw.json config (see references/openclaw-config-reference.md)
3. Copy config to volume
4. (Optional) Copy SKILL.md files to volume's skills/ dir
5. Start container:
   ```bash
   docker run -d --name openclaw-mybot --init --restart unless-stopped \
     --dns 8.8.8.8 -e HOME=/home/node -e NODE_ENV=production \
     -e OPENAI_API_KEY="..." -e OPENCLAW_GATEWAY_TOKEN="..." \
     -v openclaw-mybot-config:/home/node/.openclaw \
     -v openclaw-mybot-workspace:/home/node/.openclaw/workspace \
     -p 127.0.0.1:18803:18789 -p 127.0.0.1:18804:18790 \
     openclaw:local
   ```
6. Connect to AI Gateway: `docker network connect ai-gateway-network openclaw-mybot`
7. Wait 2-3 min for gateway init
8. Verify: `docker logs openclaw-mybot 2>&1 | grep -E "model|telegram|listen"`
9. Test: send message to bot in Telegram
10. (Optional) Run `docker exec openclaw-mybot node dist/index.js doctor --fix`

**Minimal openclaw.json:**
```json
{
  "auth": {
    "order": {"openai": ["openai-api"]},
    "profiles": {"openai-api": {"provider": "openai", "mode": "api_key"}}
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "BOT_TOKEN_HERE",
      "dmPolicy": "open",
      "allowFrom": ["*"]
    }
  },
  "agents": {
    "defaults": {
      "model": {"primary": "openai/gpt-5.2", "fallbacks": ["openai/gpt-5-mini"]}
    }
  }
}
```

---

---

## Deployment Checklist

- [ ] 1. Personality defined (SOUL.md or inline persona) — WHO is the agent?
- [ ] 2. Model selected (primary + fallback) — matches budget and task complexity
- [ ] 3. Toolsets locked — removed dangerous tools for client-facing bots
- [ ] 4. Platform configured — Telegram token from @BotFather, dmPolicy set
- [ ] 5. Allowed users set — restrict to authorized IDs for private bots
- [ ] 6. Custom plugin/extension — created if domain-specific logic needed
- [ ] 7. Cron jobs — defined for recurring tasks (reminders, signals, reports)
- [ ] 8. Docker compose — written with restart policy, volumes, env vars
- [ ] 9. Volumes created — with correct permissions (chown UID)
- [ ] 10. Container started — logs show no errors, gateway listening
- [ ] 11. Network connected — to ai-gateway-network if using AI Gateway
- [ ] 12. E2E test — send message, get coherent response within 10s

---

## References

- Skill `llm-evals` — golden-set, грейдеры, baseline и вердикт keep/rollback. Обязателен к применению при декомпозиции монолитного промпта: каждое решение (снять инструмент / включить скилл / ввести контракт) проверяется прогоном подмножества задач, а не на глаз
- `references/architecture-deep-dive.md` — устройство обоих движков: слои, конфиги, память, планировщик, платформы. Читать, когда надо понять поведение движка, а не просто развернуть бота
- `references/multi-agent-architectures.md` — бриф на агента из 6 вопросов (включая «почему нельзя без агента»), 7 многоагентных архитектур с составом ролей и правилом выбора, Decision/Error Hook, функциональная архитектура. Читать при проектировании системы из нескольких агентов, до выбора движка
- `references/prompt-decomposition.md` — разрезание разросшегося системного промпта на слои: что в файлы, что в инструменты, чем мерить. Триггеры «агент разросся», «промпт раздулся»
- `references/large-data-sandbox-grep.md` — объёмы, не влезающие в контекст: файлы в песочнице + поиск инструментами вместо чтения
- `references/use-case-recipes.md` — готовые сборки бота под задачу клиента: инструменты, крон, состав
- `references/gotchas-top53-table.md` — таблица «симптом → починка» на 53 строки; разборы 15 частых — в gotchas-and-fixes.md
- `references/engine-quickrefs.md` — короткие выжимки: плагин Hermes, расширение OpenClaw, миграция, каскад провайдеров, модели Gemini, петля Telethon, эксплуатация OpenClaw, failover AI Gateway
- `references/hermes-config-reference.md` — Full config.yaml field reference
- `references/openclaw-config-reference.md` — Full openclaw.json field reference
- `references/hermes-plugin-howto.md` — Step-by-step Hermes plugin creation
- `references/openclaw-extension-howto.md` — Step-by-step OpenClaw extension creation
- `references/personality-patterns.md` — 8 personality examples for different roles
- `references/toolset-catalog.md` — All available toolsets and when to use them
- `references/deployment-docker.md` — Docker compose patterns
- `references/deployment-vps-baremetal.md` — Hermes on bare-metal VPS without Docker: official installer, systemd 24/7, `/root/.hermes/` layout, `GATEWAY_ALLOW_ALL_USERS=false`, host timezone before cron, AITUNNEL/Moonshot/DeepSeek custom providers
- `references/vps-ssh-hardening.md` — SSH hardening playbook for any fresh VPS: key → fail2ban → ufw → password off, with lockout/50-cloud-init/ufw self-cutoff gotchas
- `references/gotchas-and-fixes.md` — Detailed solutions for common problems
- `references/cron-patterns.md` — Cron job examples for both engines
- `references/openclaw-ops-monitoring.md` — Operations runbook: health checks, log patterns, emergency procedures, fleet inventory
- `references/hermes-migration-from-openclaw.md` — Step-by-step migration playbook with commands, gotcha catalog, rollback recipes (from 2 prod migrations May 2026)
- `references/hermes-provider-resolution-cascade.md` — Source-code-level analysis of the 5-layer provider resolver. Where Hermes reads provider from and how to override every layer
- `references/gemini-api-models.md` — Current catalog of Gemini models available via public AI Studio API key, including 3.5-flash, 3.1-pro-preview, image-gen variants. Discovery curl pattern
- `references/telethon-smoke-test-loop.md` — Autonomous bot testing via Telethon CLI. Multi-bot fleet patterns, retry-until-real-reply, error filtering
- `references/multi-tenant-content-agent.md` — мультиарендный контент-агент: один движок на несколько клиентов, изоляция данных и лимитов
- `references/custom-sales-bot-patterns.md` — Custom TypeScript sales bot architecture (Grammy + MCP + PostgreSQL). Zod config, dual-bot notifications, proactive dedup, tripwire tools, value nurture cron, tool-hint injection, security hardening
- `references/eve-filesystem-agent-pattern.md` — alternative agent-structure pattern from vercel/eve (agent = directory: `instructions.md`/`tools/`/`skills/`/`channels/`/`schedules/`, Zod-typed tools). Not adopted as engine — comparison table vs Hermes/OpenClaw + concrete takeaway for plugin/extension file layout when a plugin grows past ~3-4 tools
- `references/adversarial-agent-pairs-pattern.md` — coordination pattern from shenhao-stu/openclaw-agents (built on OpenClaw): antagonistic **Ideator↔Critic** pair + quantified **SHARP** veto gate (S/H/A/R/P each 1-5, /25, pass ≥18, else return with 3 harshest critiques). Four fail-fast checkpoints + dual entry/exit gates. How to wire it on an existing fleet and into adversarial multi-agent reviews; engine-agnostic (OpenClaw `soul.md` / Hermes `SOUL.md` snippet). Complements cross-*model* validation by varying *role/stance* instead of model

## Scripts

- `scripts/gateway-diagnostic.py` — AI Gateway diagnostic: checks providers, circuit breakers and cron health across all OpenClaw bots
- `scripts/openclaw-fleet-test.sh` — Sends test messages to all bots via telethon and verifies responses. Pre-demo warmup script
