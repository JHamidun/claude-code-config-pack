# Migrating OpenClaw → Hermes — Production Playbook

Distilled from 2 real migrations (`openclaw-<bot>` → `hermes-<bot>`). Both were assistant bots with extensive workspace data + session history + cron jobs — the hard case, not the empty one.

## When to migrate

OpenClaw works well as long as:
- One ChatGPT subscription = one bot
- Light tool use (no MCP, no extensive skills)
- AI Gateway is healthy

Migrate to Hermes when:
- You need `gemini-3.5-flash` / `gemini-3-pro` via direct API (Hermes ships `gemini_native_adapter.py` with proper streaming)
- You want Codex Responses API support (Hermes has `codex_responses_adapter.py` with the chatgpt.com endpoint Cloudflare-bypass)
- Self-improving skills (Hermes auto-creates SKILL.md files after complex tasks)
- Multi-platform: TG + Discord + Slack + WhatsApp + Signal + Email + API — Hermes Telegram polling is one of 18+ adapters
- Want FTS5 session search across all past conversations
- Want shared `state.db` (SQLite) for audit trail + cron+messages

## Inventory before starting

```bash
# Existing OpenClaw bot
docker inspect openclaw-<bot> --format='{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'TOKEN|API_KEY'
docker inspect openclaw-<bot> --format='{{range .Mounts}}{{.Source}} → {{.Destination}}{{println}}{{end}}'

# Volume sizes (workspace contains the meaningful data)
du -sh /var/lib/docker/volumes/openclaw-<bot>-*/

# Session history count
ls /var/lib/docker/volumes/openclaw-<bot>-config/_data/agents/main/sessions/*.jsonl | wc -l
```

You should write down:
- TG bot token (will reuse)
- All API keys (will reuse but rotate to fresh)
- Admin TG user IDs (for `TELEGRAM_HOME_CHANNEL` and `TELEGRAM_ALLOWED_USERS`)
- List of cron jobs from `<config>/cron/jobs.json` — will need to recreate

## Step 1: Backup

```bash
ssh "$SERVER" "tar -czf /opt/_archive/openclaw-<bot>-pre-hermes-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C /var/lib/docker/volumes/ \
  openclaw-<bot>-workspace openclaw-<bot>-config openclaw-<bot>-claude"
```

Verify size > 0 and matches the `du -sh` from inventory. Keep these archives until Hermes bot is verified stable for a week.

## Step 2: Build Hermes image (one-time, shared by all bots)

```bash
cd <path/to/workdir>
git clone https://github.com/nousresearch/hermes-agent
cd hermes-agent
tar -czf /tmp/hermes-src.tar.gz --exclude=.git --exclude=node_modules --exclude=__pycache__ .
scp /tmp/hermes-src.tar.gz "$SERVER":/tmp/
ssh "$SERVER" "mkdir -p /opt/hermes-build && tar -xzf /tmp/hermes-src.tar.gz -C /opt/hermes-build"
ssh "$SERVER" "cd /opt/hermes-build && docker build -t hermes-agent:local ."
```

**CRLF gotcha** — if Windows clone, the entrypoint will fail with `exec: not found`. Wrap with this fix layer:

```dockerfile
FROM hermes-agent:local
USER root
RUN find /opt/hermes -name '*.sh' -exec sed -i 's/\r$//' {} \; && \
    find /opt/hermes -name '*.py' -exec sed -i 's/\r$//' {} \; 2>/dev/null || true
```

Then `docker build -t hermes-agent:local -f Dockerfile.fix .`.

## Step 3: Prepare bundle for migration

```bash
ssh "$SERVER" "
mkdir -p /tmp/<bot>-merged/.openclaw
cp -a /var/lib/docker/volumes/openclaw-<bot>-config/_data/. /tmp/<bot>-merged/.openclaw/
rm -rf /tmp/<bot>-merged/.openclaw/workspace
cp -a /var/lib/docker/volumes/openclaw-<bot>-workspace/_data /tmp/<bot>-merged/.openclaw/workspace
"
```

This produces the structure that `hermes claw migrate` expects:

```
/tmp/<bot>-merged/.openclaw/
├── openclaw.json            # config
├── agents/main/sessions/    # 234 conversation jsonl files
├── cron/jobs.json
├── memory/main.sqlite       # rag chunk database
├── telegram/                # offsets
├── identity/
└── workspace/               # all working files (CSVs, scripts, images)
    ├── SOUL.md
    ├── AGENTS.md
    ├── USER.md
    ├── budget_*.csv, *.xlsx
    └── generate_image.py, etc.
```

## Step 4: Bootstrap Hermes volume

```bash
ssh "$SERVER" "
docker volume create hermes-<bot>-data
docker run -d --name hermes-<bot>-bootstrap --rm \
  -v hermes-<bot>-data:/opt/data \
  -e HERMES_HOME=/opt/data \
  --entrypoint /bin/sleep hermes-agent:local infinity

docker cp /tmp/<bot>-merged/.openclaw hermes-<bot>-bootstrap:/opt/data/.openclaw
docker exec hermes-<bot>-bootstrap chown -R hermes:hermes /opt/data
"
```

## Step 5: Codex auth (if migrating Codex subscription)

```bash
# On Windows, your local ~/.codex/auth.json is the source of truth
scp ~/.codex/auth.json "$SERVER":/tmp/codex-auth.json

# Convert OpenAI format → Hermes provider-state format
ssh "$SERVER" "docker cp /tmp/codex-auth.json hermes-<bot>-bootstrap:/tmp/"
ssh "$SERVER" "docker exec hermes-<bot>-bootstrap python3 -c '
import json
src = json.load(open(\"/tmp/codex-auth.json\"))
hermes = {
  \"providers\": {
    \"openai-codex\": {
      \"auth_mode\": \"chatgpt\",
      \"tokens\": {
        \"id_token\":      src[\"tokens\"][\"id_token\"],
        \"access_token\":  src[\"tokens\"][\"access_token\"],
        \"refresh_token\": src[\"tokens\"][\"refresh_token\"],
        \"account_id\":    src[\"tokens\"][\"account_id\"],
      },
      \"last_refresh\": src.get(\"last_refresh\"),
    }
  },
  \"active_provider\": \"openai-codex\",
}
json.dump(hermes, open(\"/opt/data/auth.json\", \"w\"), indent=2)
print(\"Hermes auth.json written\")
'"
```

Verify: `docker exec hermes-<bot>-bootstrap /opt/hermes/.venv/bin/hermes auth status openai-codex` → should say `logged in`.

**WARNING: Codex refresh tokens rotate on use.** If you have other clients (codex CLI, VS Code extension, another Hermes bot) sharing the same ChatGPT subscription — they will collide constantly. Strongly recommend Gemini direct API for multi-bot deployments. See `hermes-provider-resolution-cascade.md`.

## Step 6: Run `claw migrate`

```bash
ssh "$SERVER" "docker exec -u hermes hermes-<bot>-bootstrap bash -c '
  cd /opt/data && /opt/hermes/.venv/bin/hermes claw migrate --yes --preset full --overwrite --migrate-secrets
'"
```

Expected output:

```
✓ Pre-migration backup: /opt/data/backups/pre-migration-...zip
✓ Migrated:
    soul                   → ~/SOUL.md
    user-profile           → ~/memories/USER.md
    secret-settings        → ~/.env
    model-config           → ~/config.yaml
    env-var                → .env HERMES_GATEWAY_TOKEN
─ Skipped:
    workspace-agents       No workspace target provided
    cron-jobs              No cron configuration found
    ...
```

**What was actually migrated:** SOUL.md, USER.md → memories/, model-config → config.yaml stub, secrets → .env, gateway token.

**What was NOT migrated (you must do this manually):**
- Workspace files (CSVs, XLSX, images, video, audio, Python scripts)
- Cron jobs (format incompatible)
- Conversation history (need custom script)
- OAuth credentials JSONs (security-skipped on purpose)

## Step 7: Manual workspace copy

```bash
ssh "$SERVER" "docker cp /var/lib/docker/volumes/openclaw-<bot>-workspace/_data/. hermes-<bot>-bootstrap:/opt/data/workspace/
docker exec hermes-<bot>-bootstrap chown -R hermes:hermes /opt/data/workspace
"
```

Then fix path hardcodes in workspace Python scripts:

```bash
ssh "$SERVER" "docker exec -u 0 hermes-<bot>-bootstrap bash -c '
  grep -lE \"/home/node/.openclaw/workspace\" /opt/data/workspace/*.py 2>/dev/null \
    | xargs -I {} sed -i \"s|/home/node/.openclaw/workspace|/opt/data/workspace|g\" {}
'"
```

## Step 8: Restore OAuth credentials (Google, Microsoft, etc.)

```bash
# IF workspace had credentials/ directory
ssh "$SERVER" "docker exec -u 0 hermes-<bot>-bootstrap mkdir -p /opt/data/workspace/credentials
docker cp /var/lib/docker/volumes/openclaw-<bot>-workspace/_data/credentials/. hermes-<bot>-bootstrap:/opt/data/workspace/credentials/
docker exec hermes-<bot>-bootstrap chmod -R 600 /opt/data/workspace/credentials/*.json
docker exec hermes-<bot>-bootstrap chown -R hermes:hermes /opt/data/workspace/credentials
"
```

**Do NOT** copy plaintext password files (`google_creds.txt` with email+password). OAuth refresh tokens are enough — they self-rotate, and not leaking the password is good security.

## Step 9: Install missing Python deps in container

Most OpenClaw bots used `python3` scripts in workspace. Install their deps in Hermes venv:

```bash
ssh "$SERVER" "docker exec -u 0 hermes-<bot>-bootstrap bash -c '
  cd /opt/hermes && uv pip install --python /opt/hermes/.venv \
    pandas openpyxl pillow google-genai \
    beautifulsoup4 fpdf2 pypdf pdfplumber pytesseract \
    yt-dlp reportlab google-api-python-client google-auth-httplib2 google-auth-oauthlib
'"
```

System tools (one-time):

```bash
ssh "$SERVER" "docker exec -u 0 hermes-<bot>-bootstrap bash -c '
  apt-get update -qq && \
  apt-get install -y -q \
    tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng \
    poppler-utils imagemagick ffmpeg
'"
```

## Step 10: Conversation history migration

OpenClaw stores conversations in `<config>/agents/main/sessions/*.jsonl`. Hermes uses `state.db` SQLite with FTS5. Need a custom transformer:

```python
# scripts/migrate-openclaw-sessions-to-hermes.py
import json, sqlite3, sys
from pathlib import Path
from datetime import datetime

OPENCLAW_DIR = Path("/opt/data/.openclaw/agents/main/sessions")
HERMES_DB = Path("/opt/data/state.db")
USER_ID = "<your admin TG id>"   # for sessions.user_id

def iso_to_ts(s):
    if not s: return None
    if isinstance(s, (int, float)): return float(s)
    try: return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except: return None

def extract_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        out = []
        for b in content:
            if not isinstance(b, dict): continue
            t = b.get("type")
            if t == "text": out.append(b.get("text",""))
            elif t == "toolCall": out.append(f"[tool:{b.get('name','?')}]")
            elif t == "image": out.append("[image]")
        return "\n".join(out).strip()
    return ""

c = sqlite3.connect(HERMES_DB)
cur = c.cursor()
ms = mm = 0

for fp in sorted(OPENCLAW_DIR.glob("*.jsonl")):
    events = []
    for line in open(fp):
        try: events.append(json.loads(line))
        except: continue
    sess_event = next((e for e in events if e.get("type") == "session"), None)
    if not sess_event: continue
    sess_id = sess_event["id"]
    cur.execute("SELECT id FROM sessions WHERE id=?", (sess_id,))
    if cur.fetchone(): continue
    started_at = iso_to_ts(sess_event.get("timestamp")) or 0
    model_event = next((e for e in events if e.get("type") == "model_change"), None)
    model = (model_event or {}).get("modelId", "unknown")
    msg_events = [e for e in events if e.get("type") == "message"]
    if not msg_events: continue
    last_ts = iso_to_ts(msg_events[-1].get("timestamp")) or started_at
    first_user = next((e for e in msg_events if e.get("message",{}).get("role") == "user"), None)
    base = "openclaw-imported"
    if first_user:
        t = extract_text(first_user["message"].get("content"))
        if t.strip(): base = t[:60].replace("\n"," ").strip()
    title = f"{base} #{sess_id[:8]}"   # UNIQUE INDEX requires this prefix
    cur.execute("""
      INSERT INTO sessions (id, source, user_id, model, started_at, ended_at, message_count, title)
      VALUES (?,?,?,?,?,?,?,?)
    """, (sess_id, "telegram-imported", USER_ID, model, started_at, last_ts, len(msg_events), title))
    ms += 1
    for ev in msg_events:
        m = ev.get("message", {})
        role = "tool" if m.get("role") == "toolResult" else m.get("role", "user")
        content = extract_text(m.get("content"))
        if not content and role != "tool": continue
        ts = iso_to_ts(ev.get("timestamp")) or started_at
        cur.execute("""
          INSERT INTO messages (session_id, role, content, tool_name, tool_call_id, timestamp)
          VALUES (?,?,?,?,?,?)
        """, (sess_id, role, content, m.get("toolName"), m.get("toolCallId"), ts))
        mm += 1

c.commit()
print(f"Sessions: {ms}, Messages: {mm}, FTS5 entries: {cur.execute('SELECT count(*) FROM messages_fts').fetchone()[0]}")
c.close()
```

Run before first gateway start (state.db is created on first gateway boot, so do a `docker compose up -d` once to create empty state.db, then stop, run script, then start again):

```bash
ssh "$SERVER" "docker cp scripts/migrate-openclaw-sessions-to-hermes.py hermes-<bot>:/tmp/migrate.py
docker exec -u 1000 hermes-<bot> python3 /tmp/migrate.py"
```

## Step 11: Cron jobs migration

OpenClaw stores cron in `<config>/cron/jobs.json` with fields `agentId, sessionKey, schedule, payload, delivery, state`.

Hermes uses `hermes cron create` CLI with positional args. Format incompatible. Manually convert each job:

```bash
# Each OpenClaw job has:
#   schedule.expr = "30 10 * * *"     # cron
#   schedule.tz   = "Europe/Berlin"     # tz suffix
#   payload.message = "..."           # prompt
#   delivery.to = "telegram:12345"    # target chat
#
# Hermes parse_schedule does NOT accept tz suffix in expr.
# Convert the tz-suffix local time to UTC yourself: e.g. Berlin (UTC+1) 10:30 = UTC 09:30.

ssh "$SERVER" "docker exec -u 1000 -w /opt/data hermes-<bot> /opt/hermes/.venv/bin/hermes cron create \
  --name 'Morning Quest' \
  --deliver 'telegram:12345' \
  '30 9 * * *' \
  'Send the morning quest message: ...'"
```

Verify with: `docker exec -u 1000 -w /opt/data hermes-<bot> /opt/hermes/.venv/bin/hermes cron list`

## Step 12: Custom config.yaml (recommended)

```yaml
# /opt/data/config.yaml — overwrite the claw-migrated stub

model:
  default: gemini-3.5-flash
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta/openai

reasoning_effort: medium

personality:
  default: <bot-name>
  personalities:
    <bot-name>: |
      <full persona — copy from workspace/SOUL.md if exists>

platform_toolsets:
  telegram: [web, vision, image_gen, tts, file, skills, todo, cronjob, memory, session_search]

platforms:
  telegram:
    reply_to_mode: "first"

skills:
  nudge_after_complex_tasks: true
  nudge_every_n_iterations: 12

verbose: false
```

## Step 13: .env file (overwrite migrated stub)

```bash
docker exec -u hermes hermes-<bot> bash -c "cat > /opt/data/.env <<EOF
HERMES_INFERENCE_PROVIDER=gemini
TELEGRAM_BOT_TOKEN=<from openclaw>
TELEGRAM_ALLOWED_USERS=<admin_id>,<user_id>
TELEGRAM_HOME_CHANNEL=<admin_id>
OPENAI_API_KEY=<fresh>
ANTHROPIC_API_KEY=<fresh>
GOOGLE_API_KEY=<fresh>
GEMINI_API_KEY=<fresh>
DEEPGRAM_API_KEY=<fresh>
PERPLEXITY_API_KEY=<fresh>
EOF
chmod 640 /opt/data/.env
"
```

## Step 14: docker-compose.yml

```yaml
services:
  hermes-<bot>:
    image: hermes-agent:local
    container_name: hermes-<bot>
    restart: unless-stopped
    network_mode: host
    environment:
      HERMES_HOME: /opt/data
      HERMES_UID: "1000"
      HERMES_GID: "1000"
      HERMES_INFERENCE_PROVIDER: gemini
      TELEGRAM_BOT_TOKEN: "<from openclaw>"
      TELEGRAM_ALLOWED_USERS: "<admin>,<user>"
      TELEGRAM_HOME_CHANNEL: "<admin>"
      OPENAI_API_KEY: "<fresh>"
      ANTHROPIC_API_KEY: "<fresh>"
      GOOGLE_API_KEY: "<fresh>"
      GEMINI_API_KEY: "<fresh>"
      DEEPGRAM_API_KEY: "<fresh>"
      PERPLEXITY_API_KEY: "<fresh>"
    volumes:
      - hermes-<bot>-data:/opt/data
    command: ["gateway", "run"]   # NOT "gateway start" — that's interactive

volumes:
  hermes-<bot>-data:
    external: true
```

## Step 15: Cutover

```bash
# Stop bootstrap (volume persists)
ssh "$SERVER" "docker stop hermes-<bot>-bootstrap"

# Stop old OpenClaw (frees TG bot token)
ssh "$SERVER" "docker stop openclaw-<bot>"

# Launch new Hermes
ssh "$SERVER" "cd /opt/hermes-<bot> && docker compose up -d"

# Wait for gateway running
until ssh "$SERVER" "docker exec hermes-<bot> grep -q 'Gateway running' /opt/data/logs/gateway.log"; do
  sleep 3
done

# Smoke test via Telethon
python ~/.claude/tools/tg_client.py send <BotUsername> "тест 1"
sleep 30
python ~/.claude/tools/tg_client.py read-chat <BotUsername> --limit 4
```

If reply is "Provider authentication failed" or similar, see `hermes-provider-resolution-cascade.md` — almost always one of 5 cascade layers still pointed at old provider.

## Rollback

OpenClaw volumes are untouched. To rollback at any time:

```bash
ssh "$SERVER" "docker stop hermes-<bot>"
ssh "$SERVER" "docker start openclaw-<bot>"
```

Hermes volume kept for forensics. Re-attempt migration after fixing root cause.

## Cleanup (only after 1+ week stable)

```bash
ssh "$SERVER" "docker rm openclaw-<bot>"
ssh "$SERVER" "docker volume rm openclaw-<bot>-workspace openclaw-<bot>-config openclaw-<bot>-claude"
# Backup tar.gz in /opt/_archive/ stays forever — cheap insurance
```

## Common cutover gotchas

- **Bot doesn't respond after start** — first `inbound message` after gateway boot takes 5-10s extra (cold init). Wait, then retry.
- **`/sethome` onboarding nag** — set `TELEGRAM_HOME_CHANNEL` env var. Critical for child bots — don't want a 184-char system notice to confuse a kid.
- **`API call failed after 3 retries: HTTP 404`** — model name wrong. `gemini-3-flash` doesn't exist, use `gemini-3.5-flash`. Or `base_url` missing `/v1beta/openai` shim.
- **First user message AFTER cutover gets stale reply** — pinned session metadata in `state.db sessions` (billing_provider) and `sessions/*.jsonl` (model field). See `hermes-provider-resolution-cascade.md`.
- **OAuth credentials missing** — `claw migrate` excludes them. Manual copy step required.
- **Persona drift** — Hermes loads SOUL.md as system prompt PLUS personality.personalities.<name> from config.yaml. Pick one, don't define persona in both — they will conflict.

## Migration time budget

For a small bot (~10 sessions, ~10MB workspace):
- Build image: ~10 min one-time, 2 min for rebuilds
- Backup: <1 min
- Bundle prep + bootstrap: 2 min
- `claw migrate`: 30 sec
- Workspace copy: <1 min
- Cron migration: 5-15 min (depends on N jobs)
- Session migration script: <1 min
- Custom config + .env: 5 min
- Smoke test + iteration: 15-30 min

Total: ~1 hour per bot once you've done it once.

For a heavy bot (260 sessions, 126MB workspace with budgets, scripts, OAuth):
- Building from scratch first time: 2-3 hours
- Subsequent migrations following this guide: 1-2 hours
