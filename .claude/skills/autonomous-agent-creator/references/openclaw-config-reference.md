# OpenClaw openclaw.json Reference

> Complete field reference for OpenClaw agent configuration.
> Based on real deployments (assistant bot, RAG bot over a document corpus, coaching bot).
> Version: v2026.2.18

---

## Auth Configuration

```json
{
  "auth": {
    "order": {
      "openai": ["openai-api"],
      "anthropic": ["anthropic-api"],
      "google": ["google-api"]
    },
    "profiles": {
      "openai-api": {
        "provider": "openai",
        "mode": "api_key"
      },
      "anthropic-api": {
        "provider": "anthropic",
        "mode": "api_key"
      },
      "google-api": {
        "provider": "google",
        "mode": "api_key"
      }
    }
  }
}
```

API keys are passed as environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`.

**IMPORTANT:** Do NOT use `"baseUrl"` inside auth profiles. It is invalid in v2026.2.18 and causes silent failures. Use AI Gateway network routing instead.

---

## Gateway

```json
{
  "gateway": {
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "RANDOM_TOKEN_HERE"
    },
    "controlUi": {
      "enabled": true,
      "allowInsecureAuth": true
    }
  }
}
```

| Field | Values | Description |
|-------|--------|-------------|
| `mode` | `"local"` | Only local mode supported for self-hosted |
| `bind` | `"loopback"` / `"all"` | `loopback` = 127.0.0.1 only (recommended) |
| `auth.mode` | `"token"` / `"none"` | `token` requires matching `OPENCLAW_GATEWAY_TOKEN` env var |
| `controlUi.enabled` | bool | Enables web control panel on port 18790 |

---

## Channels (Telegram)

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "TOKEN_FROM_BOTFATHER",
      "dmPolicy": "open",
      "allowFrom": ["*"],
      "groups": {
        "*": {
          "requireMention": true
        }
      }
    }
  }
}
```

### DM Policies

| Policy | Effect | Use Case |
|--------|--------|----------|
| `open` | Anyone can DM the bot | Public bots, support |
| `pairing` | Must pair via code first | Personal assistants |
| `allowlist` | Only listed user IDs | Private bots |
| `disabled` | No DMs at all | Group-only bots |

### Group Configuration

```json
"groups": {
  "*": {
    "requireMention": true
  },
  "-100GROUPID": {
    "requireMention": false,
    "personality": "support"
  }
}
```

- `"*"` = default for all groups
- Specific group ID overrides default
- `requireMention: true` = bot only responds when @mentioned in groups

---

## Model Configuration

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai/gpt-5.2",
        "fallbacks": ["openai/gpt-5-mini"]
      }
    }
  }
}
```

**CRITICAL:** Model MUST be an object with `primary` + `fallbacks` array. A plain string will fail silently.

### Known Models (v2026.2.18)

| Model ID | Notes |
|----------|-------|
| `openai/gpt-4o` | Legacy, still works |
| `openai/gpt-4o-mini` | Legacy mini |
| `openai/gpt-5` | GPT-5 base |
| `openai/gpt-5-mini` | Fast, cheap |
| `openai/gpt-5-nano` | Fastest, cheapest |
| `openai/gpt-5.1-codex` | Code-focused |
| `openai/gpt-5.2` | Latest, best general |
| `openai/gpt-5.2-codex` | Latest code-focused |
| `openai/gpt-5.3-codex` | Newest codex |
| `anthropic/claude-sonnet-4-5` | Balanced Claude |
| `anthropic/claude-opus-4-6` | Max quality Claude |
| `google/gemini-2.5-flash` | Fast Gemini |
| `google/gemini-2.5-pro` | Strong Gemini |

---

## Personality (via Agent Defaults)

```json
{
  "agents": {
    "defaults": {
      "model": { ... },
      "personality": "You are a helpful assistant. ..."
    }
  }
}
```

Or use SOUL.md file at `/home/node/.openclaw/SOUL.md` for longer personality definitions.

---

## Skills

```json
{
  "skills": {
    "load": {
      "extraDirs": ["/home/node/.openclaw/skills"]
    },
    "allowBundled": ["github", "notion", "obsidian"]
  }
}
```

### Custom Skills

Place `SKILL.md` files in `/home/node/.openclaw/skills/<skill-name>/SKILL.md`.

Skills are auto-discovered at startup.

### Bundled Skills

| Skill | What It Does |
|-------|-------------|
| `github` | GitHub operations (issues, PRs, repos) |
| `notion` | Notion database queries, page creation |
| `obsidian` | Obsidian vault operations |

---

## Plugins (Extensions)

```json
{
  "plugins": {
    "entries": {
      "my-extension": {
        "enabled": true,
        "config": {
          "key": "value"
        }
      }
    }
  }
}
```

Extensions are TypeScript modules placed in `/home/node/.openclaw/extensions/`.

---

## Browser / Sandbox

```json
{
  "browser": {
    "enabled": true,
    "headless": true,
    "noSandbox": true
  },
  "agents": {
    "defaults": {
      "sandbox": {
        "browser": {
          "enabled": true,
          "headless": false,
          "enableNoVnc": true,
          "autoStart": true
        }
      }
    }
  }
}
```

| Field | Description |
|-------|-------------|
| `browser.enabled` | Enable Playwright-based browser |
| `browser.headless` | Run without display |
| `browser.noSandbox` | Required in Docker containers |
| `sandbox.browser.enableNoVnc` | VNC viewer for debugging (port 6901) |
| `sandbox.browser.autoStart` | Start browser on agent init |

---

## Cron Jobs

```json
{
  "cron": {
    "enabled": true,
    "jobs": [
      {
        "name": "morning-briefing",
        "enabled": true,
        "schedule": {
          "kind": "cron",
          "expr": "0 9 * * *",
          "tz": "Europe/Moscow"
        },
        "sessionTarget": "isolated",
        "wakeMode": "now",
        "payload": {
          "kind": "agentTurn",
          "message": "Generate morning briefing with today's tasks and weather.",
          "toolsAllow": ["web_fetch", "memory_search", "memory_write"]
        },
        "delivery": {
          "mode": "announce",
          "channel": "telegram"
        }
      }
    ]
  }
}
```

### Schedule Kinds

| Kind | Example | Description |
|------|---------|-------------|
| `cron` | `{"kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow"}` | Standard cron expression |
| `every` | `{"kind": "every", "everyMs": 60000}` | Every N milliseconds |
| `at` | `{"kind": "at", "at": "2026-06-01T09:00:00Z"}` | One-shot at specific time |

### Session Targets

| Target | Behavior |
|--------|----------|
| `isolated` | Fresh session for each cron run |
| `default` | Use the default/main session |

### Delivery Modes

| Mode | Behavior |
|------|----------|
| `announce` | Send result to specified channel |
| `silent` | Execute but don't send output |

---

## Environment Variables (Docker)

| Variable | Required | Description |
|----------|----------|-------------|
| `HOME` | Yes | Must be `/home/node` |
| `NODE_ENV` | Yes | `production` for deployed bots |
| `OPENAI_API_KEY` | Yes* | For OpenAI models |
| `OPENCLAW_GATEWAY_TOKEN` | Yes | Must match `gateway.auth.token` in config |
| `GOOGLE_API_KEY` | No | For Gemini models |
| `ANTHROPIC_API_KEY` | No | For Claude models |
| `PERPLEXITY_API_KEY` | No | For Perplexity web search |

*Required if using OpenAI models as primary

---

## Docker Details

| Parameter | Value |
|-----------|-------|
| Image | `openclaw:local` (or pinned image ID) |
| Config path (container) | `/home/node/.openclaw/openclaw.json` |
| Workspace path | `/home/node/.openclaw/workspace/` |
| Skills path | `/home/node/.openclaw/skills/` |
| Internal gateway port | 18789 |
| Internal control port | 18790 |
| Node user UID | 1000 |
| Required flags | `--init` (prevents zombies), `--restart unless-stopped` |
| DNS | `--dns 8.8.8.8 --dns 1.1.1.1` (Docker DNS can be unreliable) |

---

## Minimal Working Config

```json
{
  "auth": {
    "order": {"openai": ["openai-api"]},
    "profiles": {
      "openai-api": {"provider": "openai", "mode": "api_key"}
    }
  },
  "gateway": {
    "mode": "local",
    "bind": "loopback",
    "auth": {"mode": "token", "token": "CHANGE_ME"}
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
      "model": {
        "primary": "openai/gpt-5.2",
        "fallbacks": ["openai/gpt-5-mini"]
      }
    }
  }
}
```

---

## Media Understanding (Audio/Image/Video)

```json
{
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "language": "ru",
        "models": [
          { "type": "provider", "provider": "deepgram", "model": "nova-3" }
        ]
      }
    }
  }
}
```

### Audio Provider Auto-Detection

When `models` is omitted, OpenClaw auto-detects by checking API keys in this order:
`openai → groq → deepgram → google`

**Gotcha:** If OPENAI_API_KEY is set, OpenAI Whisper will be used even when Deepgram would work better for Russian. Always set `models` explicitly for production bots with voice input.

| Provider | Model | Best For |
|----------|-------|----------|
| `deepgram` | `nova-3` | Russian, real-time, reliable |
| `openai` | `gpt-4o-mini-transcribe` | English, multimodal context |
| `groq` | `whisper-large-v3-turbo` | Fast, free tier |
| `google` | (auto) | Fallback via Gemini |

### Web Search Provider

```json
{
  "tools": {
    "web": {
      "search": {
        "enabled": true,
        "provider": "perplexity"
      }
    }
  }
}
```

| Provider | Requires | Notes |
|----------|----------|-------|
| `brave` | `BRAVE_API_KEY` | Default. Keys expire — check regularly |
| `perplexity` | `PERPLEXITY_API_KEY` | More reliable, AI-enhanced results |
| `grok` | `XAI_API_KEY` | X/Twitter integration |

If Brave key expires (422 `SUBSCRIPTION_TOKEN_INVALID`), switch to `perplexity` as drop-in replacement.

---

## Common Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| Bot starts but doesn't respond | Model string instead of object | Use `{"primary": "...", "fallbacks": [...]}` |
| 401 on model calls | Missing/wrong API key | Check env var name matches provider |
| Config not loading | Wrong path or permissions | Must be `/home/node/.openclaw/openclaw.json`, owned by UID 1000 |
| Gateway token mismatch | Env var != config token | `OPENCLAW_GATEWAY_TOKEN` must equal `gateway.auth.token` |
| Zombie processes | Missing `--init` flag | Always use `docker run --init` |
| DNS resolution fails | Docker default DNS | Add `--dns 8.8.8.8 --dns 1.1.1.1` |
| Skills not found | Wrong directory | Place in `/home/node/.openclaw/skills/<name>/SKILL.md` |
| `baseUrl` in auth | Invalid field in v2026.2.18 | Remove `baseUrl`, use AI Gateway network instead |
