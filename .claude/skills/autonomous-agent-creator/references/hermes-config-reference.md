# Hermes config.yaml Reference

> Complete field reference for Hermes agent configuration.
> Based on real `hermes-<bot>` deployments.

---

## Model Configuration

```yaml
model:
  default: "openai/gpt-5.2"          # Primary model (provider/model format)
  fallback: "google/gemini-2.5-flash" # Fallback when primary fails or is unavailable

  # Provider auto-detection from base_url:
  # - api.anthropic.com -> anthropic
  # - *.amazonaws.com -> bedrock
  # - anything with /anthropic -> anthropic-compatible
  # - else -> openai-compatible

  # Common model strings:
  # "openai/gpt-5.2"              - GPT-5.2 (best general)
  # "openai/gpt-5-mini"           - GPT-5 Mini (fast, cheap)
  # "google/gemini-2.5-flash"     - Gemini Flash (fast, multimodal)
  # "google/gemini-2.5-pro"       - Gemini Pro (strong reasoning)
  # "anthropic/claude-sonnet-4-5" - Sonnet 4.5 (balanced)
  # "anthropic/claude-opus-4-6"   - Opus 4.6 (max quality)
```

### Custom OpenAI-compatible Providers (incl. RU-friendly)

Any OpenAI-compatible endpoint plugs in as `provider: custom` — only `base_url`/`model`/`api_key`
differ. **Take the exact model id from the provider's `GET /v1/models`, don't guess.**

| Provider | `base_url` | Typical model | Notes |
|----------|-----------|---------------|-------|
| **AITUNNEL** (RU proxy) | `https://api.aitunnel.ru/v1` | `kimi-k2.5` (`owned_by: moonshotai`) | Rubles/СБП, no VPN, from 399₽ — default for RU client/student deploys |
| **Kimi / Moonshot** (direct) | `https://api.moonshot.ai/v1` | `kimi-k2.5`, `moonshot-v1-128k` | May need non-RU network access |
| **DeepSeek** (direct) | `https://api.deepseek.com/v1` | `deepseek-chat`, `deepseek-reasoner` | Docs: api-docs.deepseek.com |

```yaml
model:
  provider: custom
  base_url: https://api.aitunnel.ru/v1
  model: kimi-k2.5
  api_key: "<MODEL_API_KEY>"   # из своего env-файла (имена — в templates/.credentials.master.env.example) — never hardcode
```

### Reasoning Effort

```yaml
reasoning_effort: "medium"  # low | medium | high
# Only affects models that support it (o-series, Claude with extended thinking)
# "low"    = faster responses, less depth
# "medium" = balanced (default)
# "high"   = slower, more thorough reasoning
```

---

## Personality

```yaml
personality:
  default: "main"           # Which personality key to use
  personalities:
    main: |
      Multi-line personality definition.
      Define WHO the agent is, communication style, tone, constraints.
      This is the system prompt core that shapes agent behavior.

    # Optional additional personalities for switching:
    formal: |
      Same agent but in formal mode.
      Used when context requires different tone.
```

### Personality Best Practices

- Keep under 500 words (longer = diluted attention)
- Start with role definition: "Ty - [role]. [Core purpose]."
- Include explicit constraints: what NOT to do
- Define language preference explicitly
- Add safety boundaries for client-facing bots

---

## Platform Toolsets

Restrict which tools are available per platform:

```yaml
platform_toolsets:
  telegram:
    - web              # web_search, web_fetch
    - vision           # image analysis (photos sent by user)
    - image_gen        # generate images
    - tts              # text-to-speech (voice messages)
    - file             # read_file, write_file, list_files
    - skills           # activate custom skills
    - todo             # todo list management
    - cronjob          # cron CRUD (create, list, delete, etc.)
    - memory           # memory_search, memory_write
    - session_search   # cross-session search
    - terminal         # bash execution (DANGEROUS for public bots)
    - delegation       # spawn subagents
    - kanban           # kanban board management
    - hermes-telegram  # full Telegram API (sendPhoto, sendAudio, sendSticker, etc.)
```

### Safety Matrix

| Bot Type | REMOVE these toolsets |
|----------|----------------------|
| Child-facing | terminal, delegation, kanban |
| Client-facing (open) | terminal, delegation |
| Public (open dmPolicy) | terminal, delegation, kanban, file |
| Monitoring/alerts only | delegation, kanban, file, terminal |
| Personal assistant | (keep all) |

---

## Platforms

```yaml
platforms:
  telegram:
    reply_to_mode: "first"    # "off" | "first" | "all"
    # "off"   = never quote-reply
    # "first" = reply to the first message in a batch
    # "all"   = reply to every message
    extra:
      disable_link_previews: false  # true = no URL previews in messages
```

---

## Skills

```yaml
skills:
  nudge_after_complex_tasks: true   # Remind user after long tool chains
  nudge_every_n_iterations: 12      # Show progress every N iterations

  # Skills are SKILL.md files placed in:
  # /opt/data/skills/<skill-name>/SKILL.md
  # They are auto-discovered and available via the skills toolset
```

---

## Image Generation

```yaml
image_gen:
  provider: "fal"            # Provider name (fal, openai, etc.)
  model: "flux-2-pro"        # Model identifier

  # Available models (speed estimates):
  # flux-2-klein-9b   - <1s, fast drafts
  # flux-2-pro        - ~6s, high quality
  # nano-banana-pro   - ~8s, Gemini-based (best for text on images)
  # gpt-image-1.5     - ~15s, GPT image gen
  # recraft-v4-pro    - ~8s, design-focused
```

---

## Verbose Logging

```yaml
verbose: false  # true = debug logging to container stdout
# Useful for debugging tool calls, model responses, token usage
# WARNING: generates a LOT of output in production
```

---

## Session Reset Policy

```yaml
# Configured in gateway.json or via GatewayConfig overlay:
# Controls when conversation context is wiped

# reset_policy:
#   mode: "both"          # "daily" | "idle" | "both" | "none"
#   at_hour: 4            # Hour for daily reset (0-23, server timezone)
#   idle_minutes: 1440    # Idle timeout in minutes (default 24h = 1440)

# "daily"  = reset at specified hour regardless of activity
# "idle"   = reset after N minutes of no messages
# "both"   = whichever triggers first
# "none"   = never auto-reset (manual only)
```

---

## SOUL.md (Persistent Knowledge)

```yaml
# Not in config.yaml, but placed as /opt/data/SOUL.md
# SOUL.md is injected into every conversation as persistent context.
# Use for: product knowledge, FAQ, procedures, reference data.
# Max recommended size: 8000 tokens (~6000 words)
# Larger SOULs eat into context budget.
```

---

## Environment Variables (Docker)

| Variable | Required | Description |
|----------|----------|-------------|
| `HERMES_HOME` | Yes | Data directory inside container (default: `/opt/data`) |
| `TELEGRAM_BOT_TOKEN` | Yes* | Token from @BotFather |
| `TELEGRAM_ALLOWED_USERS` | Yes* | Comma-separated Telegram user IDs |
| `TELEGRAM_HOME_CHANNEL` | No | Default channel for scheduled deliveries |
| `OPENAI_API_KEY` | Yes** | For OpenAI-compatible models |
| `ANTHROPIC_API_KEY` | No | For Claude models |
| `GOOGLE_API_KEY` | No | For Gemini models |
| `GEMINI_API_KEY` | No | Alias for GOOGLE_API_KEY (some SDKs prefer this) |
| `DEEPGRAM_API_KEY` | No | For STT/transcription of voice messages |
| `PERPLEXITY_API_KEY` | No | For web search tool (Perplexity provider) |
| `FAL_KEY` | No | For FAL image generation |
| `HERMES_UID` | No | Override runtime user UID (default: 10000) |
| `HERMES_GID` | No | Override runtime group GID |
| `HERMES_INFERENCE_PROVIDER` | No | Force provider override (openai/anthropic/gemini) |

*Required for Telegram platform
**Required if using OpenAI models

---

## Key Internals (Read-Only Reference)

| Parameter | Value | Note |
|-----------|-------|------|
| MINIMUM_CONTEXT_LENGTH | 64K tokens | Models below this are rejected |
| max_iterations | 90 | Tool-calling loop limit per turn |
| Memory format | MEMORY.md + USER.md | Section delimiter: `---` |
| Memory char limit | 2200 chars | Per memory entry |
| Compression trigger | 50% context fill | Protects last 20 messages |
| Prompt caching | Auto for Claude | 5min TTL, "system_and_3" strategy |
| Config reload | Per-message | config.yaml re-read each incoming message |
| Iteration budget | Shared | Parent + all subagents share same 90-iteration budget |
| Compression summary | 2K-12K tokens | 20% of compressed content, ceiling 12K |
| Anti-thrashing | 2 consecutive fails | If last 2 compressions saved <10%, skip |

## System Prompt Layers (how personality is assembled)

Hermes builds the system prompt from 8 layers (in order):

1. **SOUL.md** — `~/.hermes/SOUL.md` (max 20K chars, truncated 70:20 head:tail)
2. **Platform Hints** — Telegram=Markdown, WhatsApp=plain text, Cron=headless
3. **Environment** — OS, cwd, docker/ssh/modal detection
4. **Context Files** — `.hermes.md` / `AGENTS.md` / `CLAUDE.md` / `.cursorrules` (each max 20K, threat-scanned)
5. **Skills Index** — markdown table of available skills (LRU-cached, invalidated on SKILL.md mtime change)
6. **Tool Enforcement** — model-specific execution guidance (GPT/Gemini/Claude each have different prompts)
7. **Universal Guidance** — task completion, memory, kanban, session search
8. **Nous Subscription** — Firecrawl/FAL/TTS status (only if managed)

This means: personality in SOUL.md, behavior overrides in `agents_rules_prefix.md`, project context in `.hermes.md`.

## Docker Internals (s6-overlay)

Hermes uses s6-overlay as PID1 (not tini). Boot sequence:

1. `/init` → stage2-hook.sh (as root): UID/GID remap, Docker socket group, targeted chown, config seed, skills_sync.py, Chromium discovery
2. `main-wrapper.sh` (drops to hermes user via `s6-setuidgid`): activates venv, routes CMD args
3. Services: `main-hermes` (sleep placeholder), `dashboard` (optional, OAuth gate)

Key env vars for s6:

- `HERMES_UID` / `PUID` — remap runtime user UID (NAS compatibility)
- `HERMES_GID` / `PGID` — remap group GID
- `HERMES_DASHBOARD=true` — enable web dashboard on port 9119
- `AGENT_BROWSER_EXECUTABLE_PATH` — auto-detected Chromium in Playwright dir

UID remap means: if you set `HERMES_UID=1000` and bind-mount a host volume, files will be owned by UID 1000 on the host too.

---

## Minimal Working Config

```yaml
model:
  default: "google/gemini-2.5-flash"

personality:
  default: "main"
  personalities:
    main: |
      You are a helpful assistant.

platform_toolsets:
  telegram:
    - web
    - memory
    - vision
```

---

## Full Production Config (Template)

```yaml
model:
  default: "openai/gpt-5.2"
  fallback: "google/gemini-2.5-flash"

reasoning_effort: "medium"

personality:
  default: "main"
  personalities:
    main: |
      [PERSONALITY HERE]

platform_toolsets:
  telegram:
    - web
    - vision
    - image_gen
    - tts
    - file
    - skills
    - todo
    - cronjob
    - memory
    - session_search

platforms:
  telegram:
    reply_to_mode: "first"
    extra:
      disable_link_previews: false

skills:
  nudge_after_complex_tasks: true
  nudge_every_n_iterations: 12

image_gen:
  provider: "fal"
  model: "flux-2-pro"

verbose: false
```
