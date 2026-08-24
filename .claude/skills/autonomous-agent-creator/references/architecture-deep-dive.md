# Архитектура Hermes и OpenClaw — разбор

Устройство обоих движков: слои, конфиги, память, планировщик, платформы, как они склеены. Читай, когда надо понять, почему движок ведёт себя так, а не когда просто разворачиваешь бота по чеклисту.

## Оглавление

- Architecture Deep Dive
- Personality
- Model Selection
- Platform Config
- Toolset Management
- Memory
- Cron Jobs

---

## Architecture Deep Dive

### Personality

**Hermes:** SOUL.md file (max 20K chars, loaded fresh each message) OR inline in config.yaml `personality.personalities.<name>`

**OpenClaw:** Skill SKILL.md loaded as system prompt context. No dedicated personality file — personality IS the skill.

Key principles:
- Define WHO the agent is, not WHAT it does (tools handle that)
- Include constraints (what NOT to do)
- Set tone and formatting expectations
- For child bots: add safety rules (soft refusal + alert on dangerous topics)

### Model Selection

**Recommended baseline (2026-06): Gemini 3.5 Flash via direct AI Studio API.**
- Stable, fast (1-3s normal turns), cheap, high quotas
- No OAuth rotation conflict (unlike Codex subscription)
- Multimodal native (vision + audio)
- 272K context — enough for long persona + history
- API-key auth → no per-bot OAuth dance

**Hermes config.yaml (Gemini primary, recommended):**
```yaml
model:
  default: gemini-3.5-flash
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta/openai
  # NOTE: must be /v1beta/openai shim, NOT bare /v1beta — Hermes uses chat_completions api_mode
```

Available Gemini models via public API key (as of 2026-06, full list in `references/gemini-api-models.md`):
- `gemini-3.5-flash` — current recommended primary
- `gemini-3.1-pro-preview` — slower, higher quality
- `gemini-3.1-flash-lite` — cheapest, lowest latency
- `gemini-flash-latest` — alias to newest stable flash
- `gemini-2.5-flash` / `gemini-2.5-pro` — stable fallbacks
- `gemini-3.1-flash-image-preview` — Nano Banana 3.1 (image-gen, separate model)

**Hermes config.yaml (OpenAI/Codex — DEPRECATED unless single-client):**
```yaml
model:
  default: openai-codex/gpt-5.4
  provider: openai-codex
  base_url: https://chatgpt.com/backend-api/codex
```
Risk: ChatGPT subscription has rotating refresh tokens. Any second client (codex CLI, VS Code extension, another Hermes bot) consuming the refresh invalidates ALL others. Multi-bot stack on one ChatGPT account = guaranteed outage within days. Only safe if exactly ONE process uses the refresh token.

**Hermes config.yaml (Anthropic direct):**
```yaml
model:
  default: claude-sonnet-5      # full id, not an alias: the API takes ids only.
                                # Check it against ~/.claude/config/models.md — a stale
                                # id returns 200 and last year's model, never an error.
  provider: anthropic
  base_url: https://api.anthropic.com
```
Risk: organisation can be disabled overnight (we hit this in May 2026 — single API key gave 400 "organization has been disabled" on all bots simultaneously). Have backup provider ready.

**OpenClaw openclaw.json:**
```json
"agents": {
  "defaults": {
    "model": {"primary": "openai/gpt-5.2", "fallbacks": ["openai/gpt-5-mini"]}
  }
}
```

Known models in OpenClaw v2026.2.18: gpt-4o, gpt-4o-mini, gpt-5, gpt-5-mini, gpt-5-nano, gpt-5.1-codex, gpt-5.2, gpt-5.2-codex, gpt-5.3-codex. NOT supported: gpt-5.4+.

### Platform Config

**Hermes** supports 18+ platforms via adapters. Key env vars per platform:
- Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_HOME_CHANNEL`
- Discord: `DISCORD_BOT_TOKEN`
- WhatsApp: via WhatsApp Business API
- API Server: built-in HTTP endpoint

**OpenClaw** primarily Telegram:
```json
"channels": {
  "telegram": {
    "enabled": true,
    "botToken": "...",
    "dmPolicy": "open|pairing|allowlist|disabled",
    "allowFrom": ["*"] or ["user_id_1", "user_id_2"],
    "groups": {"*": {"requireMention": true}}
  }
}
```

### Toolset Management

**Hermes** — lock per platform:
```yaml
platform_toolsets:
  telegram: [web, vision, image_gen, tts, file, skills, todo, cronjob, memory, session_search]
```
Remove `terminal` for client-facing bots. Remove `delegation` for simple bots.

**OpenClaw** — via skills allowBundled:
```json
"skills": {
  "load": {"extraDirs": ["/home/node/.openclaw/skills"]},
  "allowBundled": ["github", "notion", "obsidian"]
}
```

### Memory

**Hermes:** MEMORY.md file, sections separated by `§\n`, max 2200 chars total. Auto-compressed. Tools: memory_search, memory_write.

**OpenClaw:** Built-in memory with similar search/write tools. Stored in workspace volume.

### Cron Jobs

See `references/cron-patterns.md` for full patterns.

**Hermes cronjob tool** (7 actions): create, list, update, pause, resume, remove, run.
Schedule formats: "30m", "every 2h", "0 9 * * *", "2026-06-01T09:00:00".
Delivery: "origin", "local", "all", "platform:chat_id:thread_id".

**OpenClaw cron config:**
```json
"cron": {
  "jobs": [{
    "name": "daily-check",
    "schedule": {"kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow"},
    "payload": {"kind": "agentTurn", "message": "Do X", "toolsAllow": ["web_fetch"]},
    "delivery": {"mode": "announce", "channel": "telegram"}
  }]
}
```

---

