# OpenClaw Operations & Monitoring

> Practical ops knowledge from running a fleet of ~6 OpenClaw bots on one or two VPS.

---

## Inventory Commands

```bash
# List all openclaw containers
docker ps --format '{{.Names}}\t{{.Status}}' | grep openclaw

# Get bot username from token
TOKEN=$(sudo cat /var/lib/docker/volumes/${CONTAINER}-config/_data/openclaw.json | \
  python3 -c 'import json,sys; print(json.load(sys.stdin)["channels"]["telegram"]["botToken"])')
curl -s "https://api.telegram.org/bot$TOKEN/getMe" | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["username"])'

# List all openclaw volumes
docker volume ls | grep openclaw

# Read openclaw.json without entering container
sudo cat /var/lib/docker/volumes/${CONTAINER}-config/_data/openclaw.json | python3 -m json.tool
```

---

## Health Check Patterns

### Quick health (all bots):
```bash
for c in $(docker ps --format '{{.Names}}' | grep openclaw); do
  echo "=== $c ==="
  docker logs --tail 5 $c 2>&1 | grep -iE 'error|rate limit|failover|listening'
done
```

### Identify issues:
```bash
# Rate limit errors
docker logs $CONTAINER 2>&1 | grep -c "rate limit"

# Model config warnings
docker logs $CONTAINER 2>&1 | grep "specified without provider" | head -3

# Cron job failures
docker logs $CONTAINER 2>&1 | grep "lane task error.*cron" | tail -5

# Last successful interaction
docker logs $CONTAINER 2>&1 | grep "⇄ res ✓" | tail -1
```

### AI Gateway health:
```bash
# Current failover state
docker logs <your-gateway> --since 10m 2>&1 | grep -E 'FAILOVER|EXHAUSTED|CB|circuit'

# Circuit breaker status
docker logs <your-gateway> 2>&1 | grep -E 'OPEN|CLOSED|HALF_OPEN' | tail -10

# Which providers are working
docker logs <your-gateway> --since 5m 2>&1 | grep "FAILOVER OK"
```

---

## Common Failure Patterns

> These are **illustrations of a class of problem**, not a log of what happened on any
> particular host. Container names, paths and quota numbers are stand-ins: `<your-gateway>`
> is whatever your multi-provider gateway container is called, and `/opt/<your-gateway>/`
> is wherever you mounted its config. What transfers is the shape — the order in which
> providers fall over, and which signal tells you which link in the chain broke.

### 1. "FailoverError: API rate limit reached"

**Symptom:** Bot sends `⚠️ Agent failed before reply: API rate limit reached. Please try again later.`

**Root cause chain:**
1. Gemini skipped (tool_results in request → unified.py:176 filters gemini_native)
2. OpenAI circuit breaker CLOSED (key expired / billing / 429)
3. Vertex AI quota exceeded (per-minute input tokens)
4. All providers exhausted → 503 → error shown to user

**Fix:**
- Emergency: `docker restart <your-gateway>` (resets circuit breaker)
- Proper: fix credentials in `/opt/<your-gateway>/config.yaml`, increase Vertex quota

### 2. "Model specified without provider"

**Symptom:** Log spam: `Model "claude-haiku-4-5-20251001" specified without provider. Falling back to "anthropic/claude-haiku-4-5-20251001"`

**Root cause:** openclaw.json uses model ID without prefix.

**Fix:** In `agents.defaults.model`:
```json
"primary": "anthropic/claude-haiku-4-5-20251001"  // NOT "claude-haiku-4-5-20251001"
```

### 3. ENOENT on MEMORY.md

**Symptom:** `read failed: ENOENT: no such file or directory, access '/home/node/.openclaw/workspace/MEMORY.md'`

**Root cause:** Agent tries to read memory file that was never created.

**Fix:**
```bash
docker exec $CONTAINER sh -c 'echo "# Memory\n" > /home/node/.openclaw/workspace/MEMORY.md'
```

### 4. Cron job lastStatus=error

**Symptom:** Cron fires but payload fails.

**Diagnosis:**
```bash
# Read cron config
sudo cat /var/lib/docker/volumes/${CONTAINER}-config/_data/cron/jobs.json | \
  python3 -c 'import json,sys; [print(j["id"],"|",j["state"].get("lastStatus","?")) for j in json.load(sys.stdin)["jobs"]]'
```

**Fix:** Usually the AI Gateway rate limit issue. Fix gateway first, then either:
- Wait for next scheduled run
- Trigger manually: send the cron payload message to the bot

### 5. Gateway name conflict (bonjour)

**Symptom:** `gateway name conflict resolved; newName="...OpenClaw (4)"` in logs.

**Root cause:** Multiple OpenClaw containers on same Docker network advertising via mDNS.

**Impact:** Cosmetic. No functional issue. Each bot gets a unique suffix.

### 6. Embedded agent failed before reply

**Symptom:** User sees error message in Telegram chat.

**Root cause:** The AI model provider returned error before generating any tokens.

**Common causes:**
- 429 from all providers (rate limit cascade)
- 401 from anthropic (key expired)
- 500 from provider (transient)
- Timeout (>120s, gateway gives up)

---

## Cron Job Management

### List all jobs:
```bash
sudo cat /var/lib/docker/volumes/${CONTAINER}-config/_data/cron/jobs.json | \
  python3 -c '
import json,sys
d=json.load(sys.stdin)
for j in d["jobs"]:
  sched = j["schedule"]["expr"] if j["schedule"]["kind"]=="cron" else j["schedule"]["kind"]
  print(f"{j[\"id\"]:30} | {sched:15} | enabled={j[\"enabled\"]} | last={j[\"state\"].get(\"lastStatus\",\"?\")}")
'
```

### Disable a broken cron:
```bash
# Edit jobs.json directly
sudo python3 -c '
import json
path="/var/lib/docker/volumes/CONTAINER-config/_data/cron/jobs.json"
d=json.load(open(path))
for j in d["jobs"]:
    if j["id"] == "JOB_ID":
        j["enabled"] = False
json.dump(d, open(path, "w"), indent=2)
'
docker restart $CONTAINER
```

### Trigger cron manually:
Send the exact cron payload message to the bot via Telegram. The agent will process it as a user message and execute the same logic.

---

## Volume Structure

```
/var/lib/docker/volumes/openclaw-{name}-config/_data/
├── openclaw.json          # Main config (model, channels, auth)
├── agents/main/           # Agent state (sessions, auth)
├── cron/jobs.json         # Cron configuration
├── telegram/              # Telegram provider state
├── memory/                # Built-in memory storage
├── canvas/                # Web canvas UI
└── update-check.json      # Version check state

/var/lib/docker/volumes/openclaw-{name}-workspace/_data/
├── SOUL.md               # Agent personality
├── IDENTITY.md           # Agent identity metadata
├── AGENTS.md             # Session behavior config
├── TOOLS.md              # Available tools documentation
├── USER.md               # User profile
├── HEARTBEAT.md          # Periodic tasks
├── BOOTSTRAP.md          # First-run behavior
├── MEMORY.md             # Agent long-term memory
├── stars.json            # Gamification state (tutor bot)
├── alerts.log            # Safety alerts (tutor bot)
├── users/                # Per-user data (multi-tenant bot)
├── leaderboard.json      # Global leaderboard (multi-tenant bot)
└── *.py                  # Custom tool scripts
```

---

## Testing Bots via Telethon

```bash
# Send message
python ~/.claude/tools/tg_client.py send @BotUsername "test message"

# Read last N messages
python ~/.claude/tools/tg_client.py read-chat @BotUsername --limit 5

# IMPORTANT: On Windows Git Bash, /start gets mangled to C:/Program Files/Git/start
# Fix: MSYS_NO_PATHCONV=1 python ... send @Bot "/start"
```

### Pre-demo warmup:
```bash
for bot in $BOTS; do   # BOTS="@bot1 @bot2 …" — свои из fleet inventory
  MSYS_NO_PATHCONV=1 python ~/.claude/tools/tg_client.py send $bot "тест"
done
sleep 30
for bot in $BOTS; do   # BOTS="@bot1 @bot2 …" — свои из fleet inventory
  python ~/.claude/tools/tg_client.py read-chat $bot --limit 1
done
```

---

## Emergency Procedures

### All bots down (AI Gateway failure):
```bash
docker restart <your-gateway>
# Wait 10s for gateway to warm up
docker logs <your-gateway> --since 10s 2>&1 | grep "listening\|OPEN"
```

### Single bot unresponsive:
```bash
docker restart openclaw-$NAME
docker logs openclaw-$NAME --tail 10 2>&1 | grep -E "error|listen"
```

### Gateway providers all exhausted:
```bash
# Check which provider is actually available RIGHT NOW
curl -s -H "Authorization: Bearer sk-ant-..." https://api.anthropic.com/v1/messages \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}' | head -1

# Check OpenAI
curl -s -H "Authorization: Bearer sk-proj-..." https://api.openai.com/v1/models | python3 -c 'import json,sys; d=json.load(sys.stdin); print("OK" if "data" in d else d.get("error",{}).get("message","FAIL"))'
```

---

## Fleet inventory — заведи свою

Список контейнеров и портов пишется один раз и обновляется при каждом новом боте. Без него
через полгода никто не помнит, какой контейнер кому отвечает, и «перезапусти бота Х»
превращается в поиск по `docker ps`.

| Container | Server | Bot | Purpose | Model |
|-----------|--------|-----|---------|-------|
| `openclaw-<name>` | `<host>` | `@<bot>` | что делает | `<provider>/<model>` |

Заполнять из живой системы, а не по памяти:

```bash
docker ps --format '{{.Names}}	{{.Status}}	{{.Ports}}' | grep -E 'openclaw|hermes'
```

Что обязательно в таблице, кроме имени: **кому бот отвечает** (личный / клиентский /
демо) и **какая модель**. Первое определяет, можно ли его молча перезапускать в рабочее
время; второе — куда смотреть, когда «все боты легли» окажется исчерпанной квотой одного
провайдера.
