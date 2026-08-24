# Быстрые выжимки по движкам

Короткие рабочие куски: создание плагина Hermes и расширения OpenClaw, миграция OpenClaw→Hermes, каскад резолва провайдера, обнаружение моделей Gemini, автотест-петля на Telethon, эксплуатация и диагностика OpenClaw, AI Gateway и детект Anthropic. Читай нужный раздел; полные версии — в отдельных файлах, перечисленных в `SKILL.md`.

## Оглавление

- Hermes Plugin Creation
- OpenClaw Extension Creation
- Migrating OpenClaw → Hermes (Production Playbook)
- When to migrate
- 8-step migration sequence
- Critical things to also do (often missed)
- Cutover sequence
- Rollback
- Hermes Provider Resolution Cascade (5 Layers)
- Gemini Model Discovery (production-safe pattern)
- Telethon Autonomous Testing Loop

---

## Hermes Plugin Creation

See `references/hermes-plugin-howto.md` for step-by-step guide.

Quick structure:
```
plugins/my-plugin/
├── plugin.yaml       # manifest: name, provides_tools, requires_env
├── __init__.py       # registration: TOOL_BINDINGS, ctx.register_tool()
├── schemas.py        # OpenAI function-calling format schemas
├── tools.py          # handlers returning _ok(data) / _err(msg)
└── db.py             # (optional) database connection pool
```

**plugin.yaml example:**
```yaml
name: my-plugin
version: "1.0.0"
description: "Custom plugin for domain logic"
provides_tools:
  - my_tool_name
  - my_other_tool
requires_env:
  - MY_PLUGIN_DB_URL
```

**__init__.py example:**
```python
from .tools import handle_my_tool, handle_my_other_tool
from .schemas import MY_TOOL_SCHEMA, MY_OTHER_TOOL_SCHEMA

TOOL_BINDINGS = {
    "my_tool_name": {
        "schema": MY_TOOL_SCHEMA,
        "handler": handle_my_tool,
    },
    "my_other_tool": {
        "schema": MY_OTHER_TOOL_SCHEMA,
        "handler": handle_my_other_tool,
    },
}
```

**schemas.py example:**
```python
MY_TOOL_SCHEMA = {
    "name": "my_tool_name",
    "description": "Does something useful. Use when user asks for X.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "limit": {"type": "integer", "description": "Max results", "default": 10},
        },
        "required": ["query"],
    },
}
```

**tools.py example:**
```python
from typing import Any

def _ok(data: Any) -> dict:
    return {"status": "ok", "data": data}

def _err(msg: str) -> dict:
    return {"status": "error", "message": msg}

async def handle_my_tool(ctx, params: dict) -> dict:
    query = params.get("query")
    if not query:
        return _err("query is required")
    # ... business logic ...
    return _ok({"results": results})
```

Key gotchas for Hermes plugins:
- Tool description IS the instruction. Agent reads it to decide when to call.
- Return `_ok()` or `_err()` — agent sees raw dict as tool response.
- Use `ctx.db` for shared database pool (if db.py configured).
- Async handlers are preferred (non-blocking).

---

## OpenClaw Extension Creation

See `references/openclaw-extension-howto.md` for step-by-step guide.

Quick structure:
```
extensions/my-extension/
├── package.json      # deps: @sinclair/typebox
├── tsconfig.json
└── src/
    ├── index.ts      # definePluginEntry + registerTool
    └── tools/        # one file per tool
```

**package.json example:**
```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "main": "dist/index.js",
  "scripts": {"build": "tsc"},
  "dependencies": {
    "@sinclair/typebox": "^0.32.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0"
  }
}
```

**src/index.ts example:**
```typescript
import { Type } from "@sinclair/typebox";

export const definePluginEntry = () => ({
  name: "my-extension",
  version: "1.0.0",
  tools: [
    {
      name: "my_tool",
      description: "Does something useful. Call when user needs X.",
      parameters: Type.Object({
        query: Type.String({ description: "Search query" }),
        limit: Type.Optional(Type.Number({ description: "Max results", default: 10 })),
      }),
      handler: async (params: { query: string; limit?: number }) => {
        const { query, limit = 10 } = params;
        // ... business logic ...
        return { status: "ok", results: [] };
      },
    },
  ],
});
```

Key gotchas for OpenClaw extensions:
- Use TypeBox for parameter schemas (not Zod — OpenClaw parses TypeBox internally).
- Handler receives validated params object directly.
- Return plain object — serialized to JSON for agent.
- Extension must be compiled (`tsc`) before mounting into container.
- Mount compiled `dist/` into `/home/node/.openclaw/extensions/my-extension/`.

---

## Migrating OpenClaw → Hermes (Production Playbook)

This is the canonical migration playbook, distilled from 2 live migrations of assistant bots. See `references/hermes-migration-from-openclaw.md` for full step-by-step with commands.

### When to migrate
- OpenClaw bot zacycling on 429 / rate-limit errors from AI Gateway
- Want Codex subscription endpoint properly handled (Hermes has `codex_responses_adapter.py`)
- Need self-improving skills (Hermes auto-creates them after complex tasks)
- Need multi-channel (TG + Discord + Slack + WhatsApp from one process)
- Want session FTS5 search across all past conversations

### 8-step migration sequence

1. **Backup volumes** — `tar -czf openclaw-<bot>-backup.tar.gz -C /var/lib/docker/volumes/ openclaw-<bot>-workspace openclaw-<bot>-config openclaw-<bot>-claude`
2. **Merge bundle** — combine `<bot>-config/_data` + `<bot>-workspace/_data` into a single `.openclaw/` tree (config root + `workspace/` subdir)
3. **Build Hermes image** — `docker build -t hermes-agent:local` from clone of `nousresearch/hermes-agent`. **CRITICAL CRLF gotcha**: if cloned on Windows, rebuild with `find /opt/hermes -name '*.sh' -exec sed -i 's/\r$//' {} \;` step or `entrypoint.sh` fails with "exec: not found"
4. **Bootstrap volume** — `docker run -d --name hermes-<bot>-bootstrap --rm -v hermes-<bot>-data:/opt/data --entrypoint /bin/sleep hermes-agent:local infinity`, then `docker cp` bundle into `/opt/data/.openclaw/`
5. **Run claw migrate** — `hermes claw migrate --yes --preset full --overwrite --migrate-secrets` (inside container). Imports: SOUL.md, USER.md (→ memories/), config.yaml, .env secrets, gateway-token. Does **NOT** import: workspace files, cron jobs, conversation history
6. **Manual workspace copy** — `cp -r /var/lib/docker/volumes/openclaw-<bot>-workspace/_data/* /opt/data/workspace/` (Hermes claw migrate **misses** non-MD files: budget CSVs, Python scripts, images, video, audio recordings)
7. **Session history migration** — run the migration script (no file in the skill — source inline in `references/hermes-migration-from-openclaw.md`) to import all `<config>/agents/main/sessions/*.jsonl` files into Hermes `state.db` (SQLite + FTS5). Schema: `sessions(id, source, user_id, model, started_at, ended_at, message_count, title)` + `messages(session_id, role, content, tool_name, tool_call_id, timestamp)`. **UNIQUE constraint on title** — make titles unique by appending session_id prefix
8. **Cron jobs migration** — recreate manually via `hermes cron create` CLI (OpenClaw and Hermes cron formats are NOT compatible). Convert local timezone offsets to UTC since `hermes cron parse_schedule` does NOT accept tz suffix

### Critical things to also do (often missed)

- **Codex auth.json transform** — if migrating Codex subscription, run a transform script (not shipped in the skill — write it) to convert `~/.codex/auth.json` → Hermes provider-state format (`auth.json` → `{providers: {openai-codex: {tokens: {...}, auth_mode: "chatgpt"}}}`)
- **TELEGRAM_HOME_CHANNEL** — set to admin user ID to suppress Hermes onboarding `/sethome` prompt on every first-time user message. Without this, every fresh chat gets a 184-char "📬 No home channel is set" notice before any agent reply
- **Restore Python dependencies in container** — `uv pip install --python /opt/hermes/.venv pandas openpyxl pillow google-genai beautifulsoup4 fpdf2 pypdf pdfplumber pytesseract yt-dlp reportlab` for typical workspace scripts. Plus `apt install tesseract-ocr-rus poppler-utils imagemagick`
- **Fix hardcoded paths in workspace scripts** — `sed -i 's|/home/node/.openclaw/workspace|/opt/data/workspace|g' /opt/data/workspace/*.py` (OpenClaw used `/home/node/.openclaw/workspace`, Hermes uses `/opt/data/workspace`)
- **Restore OAuth credentials** — `credentials/google-oauth-*.json` etc. live in workspace volume; manually copy to `/opt/data/workspace/credentials/` (claw migrate intentionally skips secret files for security, but production scripts need them)

### Cutover sequence

```bash
docker stop openclaw-<bot>             # frees TG bot token
docker stop hermes-<bot>-bootstrap     # volume persists
cd /opt/hermes-<bot> && docker compose up -d   # gateway run mode
# Wait for: "✓ telegram connected" and "Gateway running with 1 platform(s)"
# Smoke test via Telethon (no scripts/telethon-smoke-test.sh in the skill — write it ad hoc)
```

### Rollback

OpenClaw container is stopped but volumes preserved. To rollback: `docker start openclaw-<bot>` + `docker stop hermes-<bot>` → reverts to OpenClaw, no data loss. Hermes-<bot>-data volume kept for forensics.

See `references/hermes-migration-from-openclaw.md` for full commands, gotcha database, and rollback recipes.

---

## Hermes Provider Resolution Cascade (5 Layers)

**THE single biggest source of "I changed config but bot still uses old provider" frustrations.** See `references/hermes-provider-resolution-cascade.md` for exhaustive resolver source-code analysis.

Hermes resolves the primary model+provider at agent-loop turn-start by reading from FIVE independent state locations. Any one of them can override the others. If you change config but bot still uses old provider, you missed one of these:

1. **`config.yaml` `model:` block** — first thing Hermes reads. Persistent.
2. **`HERMES_INFERENCE_PROVIDER` env var** — read from `/opt/data/.env` AND from container env. **Container env does NOT override `.env` file** (counterintuitive!). If `.env` has old value, you must `sed -i` the file.
3. **`auth.json` `active_provider` key** — runtime cache, set by `hermes model` interactive selector
4. **`state.db sessions.billing_provider`** — per-session pinning. When user writes, Hermes finds their existing DM session and reads `billing_provider` from there, **OVERRIDING config.yaml**. To unstick: `UPDATE sessions SET billing_provider=NULL, model=NULL, billing_base_url=NULL`
5. **`/opt/data/sessions/*.jsonl` session_meta** — first JSON line of each session file has `{model: "X", platform: "Y"}`. Replay sometimes reads from here. To unstick: `sed -i 's/openai-codex/gemini/g; s/gpt-5.4/gemini-3.5-flash/g' /opt/data/sessions/*.jsonl`

**Fix order when switching provider on an existing bot:**

```bash
docker exec -u 0 <bot> sed -i 's/openai-codex/gemini/g' /opt/data/.env /opt/data/config.yaml
docker exec -u 0 <bot> sed -i 's/gpt-5.4/gemini-3.5-flash/g; s/chatgpt.com\/backend-api\/codex/generativelanguage.googleapis.com\/v1beta\/openai/g' /opt/data/config.yaml
docker exec -u 1000 <bot> /opt/hermes/.venv/bin/hermes config set HERMES_INFERENCE_PROVIDER gemini
docker exec -u 1000 <bot> /opt/hermes/.venv/bin/hermes config set HERMES_DEFAULT_MODEL gemini-3.5-flash
docker exec -u 1000 <bot> python3 -c "
import sqlite3
c = sqlite3.connect('/opt/data/state.db')
c.execute('UPDATE sessions SET billing_provider=NULL, model=NULL, billing_base_url=NULL')
c.commit()
"
docker exec -u 0 <bot> sed -i 's/openai-codex/gemini/g; s/gpt-5\.4/gemini-3.5-flash/g; s|chatgpt.com/backend-api/codex|generativelanguage.googleapis.com/v1beta/openai|g' /opt/data/sessions/*.jsonl
docker exec <bot> rm -f /opt/data/sessions/sessions.json   # cache
docker exec -u 0 <bot> python3 -c "
import json
fp='/opt/data/auth.json'
d=json.load(open(fp))
d.get('providers',{}).pop('openai-codex',None)
d['active_provider']='gemini'
json.dump(d, open(fp,'w'), indent=2)
"
docker compose up -d --force-recreate
```

After this, primary cleanly resolves to new provider. Verify in `/opt/data/logs/agent.log` with:
`grep "provider=" agent.log | tail -1`

---

## Gemini Model Discovery (production-safe pattern)

Before hardcoding a Gemini model name in config, **always verify it exists on the public API key**. Model names drift fast (`gemini-3-flash` worked then 404'd; `gemini-3.5-flash` shipped silently).

```bash
GEMINI_KEY=AIzaSy...
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_KEY}" \
  | python -c "
import json, sys
d=json.load(sys.stdin)
for m in sorted([m['name'] for m in d['models'] if 'gemini' in m['name']]):
    print(m)
"
```

If the model you want is not in this list — it's not available on your key, regardless of what announcements say. Vertex AI has different list (requires service account, not API key).

---

## Telethon Autonomous Testing Loop

When fixing a frozen bot, do **not** ask the user to "send test, what did you get?". Drive Telegram yourself via `tg_client.py` (Telethon as user account) until the bot responds correctly.

Pattern:

```bash
python ~/.claude/tools/tg_client.py send <BotName>_bot "тест N"
until python ~/.claude/tools/tg_client.py read-chat <BotName>_bot --limit 1 \
        | grep -E '<BotName>.*\] ' \
        | grep -vE 'тест N|API call failed|⏳|⚠|Gateway'; do
  sleep 5
done
python ~/.claude/tools/tg_client.py read-chat <BotName>_bot --limit 4
```

The `grep -vE` filters out error/retry sentinel messages — only succeeds when a **real** agent reply lands. Use incrementing test numbers ("тест 4", "тест 5"...) so you can correlate replies to specific sends across restarts.

See `references/telethon-smoke-test-loop.md` for full multi-bot fleet test patterns.

---

## OpenClaw Operations & Diagnostics

See `references/openclaw-ops-monitoring.md` for full ops runbook.

### Quick Health Check (all bots at once):
```bash
for c in $(docker ps --format '{{.Names}}' | grep openclaw); do
  echo "=== $c ==="
  docker logs --tail 5 $c 2>&1 | grep -iE 'error|rate limit|failover|listening'
done
```

### Key Log Patterns:
| Pattern | Meaning | Action |
|---------|---------|--------|
| `⇄ res ✓` | Successful response sent | OK |
| `FailoverError: API rate limit` | All AI providers exhausted | Fix AI Gateway |
| `Model "X" specified without provider` | Config needs `anthropic/` prefix | Edit openclaw.json |
| `ENOENT: MEMORY.md` | Memory file not created yet | `echo "# Memory" > MEMORY.md` |
| `lane task error: lane=cron` | Cron job failed | Check AI Gateway first |
| `gateway name conflict resolved` | Multiple bots on same network | Cosmetic, ignore |

### Emergency: All Bots Down
```bash
docker restart ai-gateway   # resets circuit breaker
# Wait 10s, then verify:
docker logs ai-gateway --since 10s 2>&1 | grep "listening"
```

### Testing via Telethon:
```bash
# Send: MSYS_NO_PATHCONV=1 to prevent /start mangling on Windows Git Bash
MSYS_NO_PATHCONV=1 python ~/.claude/tools/tg_client.py send @BotName "/start"
# Read:
python ~/.claude/tools/tg_client.py read-chat @BotName --limit 3
```

---

## AI Gateway failover

### AI Gateway Failover Chain

For Claude models (Sonnet-4.5 = "heavy" tier):
```
1. gemini_native/gemini-3.1-pro-high  ← SKIPPED if request has tool_results
2. gemini_native/gemini-3.1-pro-low   ← SKIPPED if request has tool_results
3. openai/gpt-5.4                      ← may hit circuit breaker
4. vertex_ai/claude-sonnet-4-6         ← may hit quota (429)
```

**Critical gap:** OpenClaw agents always have `tool_results` → Gemini always skipped → only 2 providers remain. If both fail → `ALL MODELS EXHAUSTED`.

### Tool-name rewriting (provider compatibility only)

Some providers reject or mangle specific tool names (Bedrock has its own naming rules).
A thin proxy that renames tools in both directions — request in, response out — solves that
in ~130 lines of Node.

Where it does **not** belong: rewriting tool names to hide which client you are, so the
provider bills you as a different product. That's a terms-of-service problem, not an
engineering one, and it ends with the account banned — including the subscription you use
for everything else. Pay for the tier you actually use.

### Diagnostic Layer for Gateway

Add to `unified.py` before dispatch to log detectable tool names:
```python
OPENCLAW_MARKERS = {"subagents", "session_status"}
tool_names = {t.get("name") for t in parsed.get("tools", [])}
detected = OPENCLAW_MARKERS & tool_names
if detected:
    logger.warning(f"[detection] OpenClaw markers found: {detected}")
```

---

