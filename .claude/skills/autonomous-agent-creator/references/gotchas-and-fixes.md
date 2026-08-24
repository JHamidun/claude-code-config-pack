# Gotchas and Fixes

> 15 real-world problems encountered while deploying Hermes and OpenClaw bots. Each entry has: symptom, root cause, fix, and code snippet where applicable.

---

## 1. Model Version Mismatch

**Symptom:** `400 Bad Request: model not found` or `unknown model` in logs.

**Root cause:** OpenClaw v2026.2.18 model registry only recognizes specific model strings. Arbitrary model names fail silently or with cryptic errors.

**Fix:** Use exact model IDs from the AI Gateway registry. Common mapping:
```
openai/gpt-5.2          # Works
openai/gpt-5-mini       # Works
openai/gpt-5.4          # Works
gpt-5.2                 # FAILS — needs provider prefix
```

For Hermes, the `model.default` field must also be a recognized string.

---

## 2. Token Revocation Detection

**Symptom:** Bot suddenly stops responding. Logs show `401 Unauthorized` from Telegram API.

**Root cause:** BotFather token was revoked (manual /revoke or security event).

**Fix:**
```bash
# Check token validity
curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | jq .ok

# If false: get new token from @BotFather, update config
ssh "$SERVER" 'python3 -c "
import json
path = \"/var/lib/docker/volumes/<bot>-config/_data/openclaw.json\"
c = json.load(open(path))
c[\"channels\"][\"telegram\"][\"botToken\"] = \"NEW_TOKEN_HERE\"
json.dump(c, open(path, \"w\"), indent=2)
print(\"Token updated\")
"'
docker restart <container>
```

---

## 3. Container Restart Policy

**Symptom:** Bot container disappears after server reboot. `docker ps` shows nothing.

**Root cause:** Container created without `--restart` flag.

**Fix:** Always use `--restart unless-stopped`:
```bash
docker run -d --name openclaw-mybot \
  --restart unless-stopped \
  ...
```

For existing containers:
```bash
docker update --restart unless-stopped openclaw-mybot
```

---

## 4. Volume Permission Patterns

**Symptom:** `EACCES: permission denied` when writing config or workspace files inside container.

**Root cause:** OpenClaw runs as UID 1000 (node user). Docker volumes default to root ownership.

**Fix (OpenClaw):**
```bash
docker run --rm -v mybot-config:/data alpine chown -R 1000:1000 /data
docker run --rm -v mybot-workspace:/data alpine chown -R 1000:1000 /data
```

**Fix (Hermes):** Hermes typically runs as root inside container, so no chown needed. But if running as non-root:
```bash
docker run --rm -v hermes-data:/data alpine chown -R 1000:1000 /data
```

---

## 5. bootstrap.sh for Python Dependencies

**Symptom:** Hermes plugin fails with `ModuleNotFoundError: No module named 'psycopg2'`.

**Root cause:** Plugin requires Python packages not in the base image.

**Fix:** Create `bootstrap.sh` in the plugin directory:
```bash
#!/bin/bash
# bootstrap.sh — executed once at container start
pip install --no-cache-dir psycopg2-binary redis requests
```

Or add to Dockerfile:
```dockerfile
RUN pip install --no-cache-dir psycopg2-binary redis
```

For Hermes images that already have pip, the bootstrap approach is simplest during development.

---

## 6. Image Sending via Bot API

**Symptom:** `curl: (26) couldn't open file "photo"` or image sent as document instead of photo.

**Root cause:** Wrong curl syntax. The `photo=@file` format requires NO protocol prefix.

**Fix:**
```bash
# CORRECT
curl -F "chat_id=12345" -F "photo=@/path/to/image.jpg" \
  "https://api.telegram.org/bot<TOKEN>/sendPhoto"

# WRONG — do NOT add file:// prefix
curl -F "photo=file:///path/to/image.jpg" ...   # FAILS

# WRONG — missing @ sign
curl -F "photo=/path/to/image.jpg" ...           # Sends path as string, not file
```

For sending from URL:
```bash
curl -F "chat_id=12345" -F "photo=https://example.com/image.jpg" \
  "https://api.telegram.org/bot<TOKEN>/sendPhoto"
```

---

## 7. Model Config Must Be Object, Not String

**Symptom:** Hermes crashes with `TypeError: Cannot read properties of string` on startup.

**Root cause:** Config has `"model": "openai/gpt-5.2"` instead of the required object format.

**Fix:**
```yaml
# WRONG
model: "openai/gpt-5.2"

# CORRECT
model:
  default: "openai/gpt-5.2"
  provider: "openai"
```

For OpenClaw:
```json
// WRONG
"model": "openai/gpt-5.2"

// CORRECT
"model": { "primary": "openai/gpt-5.2", "fallbacks": ["openai/gpt-5-mini"] }
```

---

## 8. Telegram Offset Reset on Restart

**Symptom:** Bot processes old messages (sometimes thousands) after restart.

**Root cause:** Telegram getUpdates offset not persisted. On restart, bot fetches all pending updates.

**Fix (OpenClaw):** Handled automatically via workspace volume — offset is persisted in `/home/node/.openclaw/state/`.

**Fix (Hermes):** Ensure the state directory is on a persistent volume:
```yaml
volumes:
  - hermes-data:/app/data   # Includes offset persistence
```

If stuck with a message flood, manually skip:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getUpdates?offset=-1"
```

---

## 9. Cron Timezone Issues

**Symptom:** Cron job fires at wrong time. "0 9 * * *" fires at noon instead of 9 AM.

**Root cause:** Container timezone is UTC. Cron expressions are evaluated in container time.

**Fix:** Specify timezone explicitly in cron config.

OpenClaw:
```json
"schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Europe/Moscow" }
```

Hermes (cronjob tool):
```json
{ "schedule": "0 9 * * *", "timezone": "Europe/Moscow" }
```

Or set container timezone:
```bash
docker run -e TZ=Europe/Moscow ...
```

---

## 10. baseUrl Not Supported in Auth Profiles

**Symptom:** OpenClaw ignores custom API base URL. Requests go to official OpenAI endpoint instead of AI Gateway.

**Root cause:** Auth profile `baseUrl` field is NOT supported in OpenClaw v2026.2.18. The gateway URL is configured separately.

**Fix:** Use the `gateway` section in openclaw.json, or connect to the `ai-gateway-network` Docker network:
```json
{
  "auth": {
    "profiles": {
      "openai-api": {
        "provider": "openai",
        "mode": "api_key"
      }
    }
  }
}
```
Then set `OPENAI_BASE_URL=http://ai-gateway:8080/openai/v1` as an environment variable, or use Docker networking.

---

## 11. Docker Tag Lost After Prune

**Symptom:** After `docker image prune` or `docker system prune`, the OpenClaw image tag disappears. `docker images` shows `<none>`.

**Root cause:** Prune removes dangling images. If the tag was reassigned, the old image becomes dangling.

**Fix:** Always tag the rollback image explicitly:
```bash
docker tag d8ddc0536d9b openclaw:rollback-2026-04-21
```

Before pruning, verify your critical images are tagged:
```bash
docker images | grep openclaw
```

---

## 12. Context Compression Anti-Thrashing

**Symptom:** Bot responses become slow and repetitive. Memory usage climbs. Agent seems confused.

**Root cause:** Context window fills up, triggers compression, which loses important context, which triggers re-fetching, which fills context again. Loop.

**Fix:** Set appropriate context limits and compression thresholds:
```yaml
# Hermes
context:
  max_tokens: 128000
  compression_threshold: 0.7    # Compress at 70% full
  keep_system_prompt: true       # Never compress system prompt
  keep_recent_turns: 5           # Always keep last 5 turns
```

For OpenClaw, use `sessionTarget: "isolated"` for cron jobs to avoid polluting the main context.

---

## 13. Plugin Tools Not Appearing

**Symptom:** Plugin loads without errors, but tools don't show up in the agent's tool list.

**Root cause:** Name mismatch between `provides_tools` in plugin.yaml and actual tool names in schemas/bindings.

**Fix checklist:**
1. `plugin.yaml` `provides_tools` list matches keys in `TOOL_BINDINGS`
2. Schema `"name"` field matches the binding key
3. `register()` function is called (check for import errors in logs)
4. For OpenClaw extensions: `names` array in `registerTool()` matches the tool factory's `name` field

```bash
# Debug: check what tools are registered
ssh "$SERVER" 'docker logs <container> 2>&1 | grep -i "register\|tool"'
```

---

## 14. Rate Limiting for Browser Automation

**Symptom:** LinkedIn/social media account gets restricted or banned after automated actions.

**Root cause:** Too many actions too fast. No rate limiting between browser operations.

**Fix:** Implement dual-window rate limiting (see openclaw-extension-howto.md):
- Hourly limit: 15-20 actions
- Daily limit: 50-100 actions
- Random delays between actions: 3-8 seconds minimum
- Human-like patterns: vary timing, don't batch all at once

```typescript
// Between each browser action
await new Promise(r => setTimeout(r, 3000 + Math.random() * 5000));
```

---

## 15. Hermes Host Networking vs OpenClaw Port Mapping

**Symptom:** Hermes bot can't reach AI Gateway. Or OpenClaw ports conflict with other services.

**Root cause:** Different networking models.

**Hermes** typically uses `--network host` or joins specific Docker networks:
```bash
docker run --network ai-gateway-network ...
# AI Gateway accessible at http://ai-gateway:8080
```

**OpenClaw** uses port mapping:
```bash
docker run -p 18797:18789 -p 18798:18790 ...
# Gateway: 18797 on host -> 18789 inside
# Control: 18798 on host -> 18790 inside
```

When both need AI Gateway access, join the same Docker network:
```bash
docker network connect ai-gateway-network openclaw-mybot
docker network connect ai-gateway-network hermes-mybot
```

Never expose gateway/control ports to the internet. Use `127.0.0.1:PORT:PORT` binding:
```bash
docker run -p 127.0.0.1:18797:18789 ...
```

---

## 16. Proactive Notification Spam (user_id vs entity.id)

**Symptom:** Admin receives the same "Hot lead!" alert every hour for the same user.

**Root cause:** Code passed `lead.id` (leads table PK) instead of `lead.user_id` (FK to users table) to `wasProactiveSentToday()` and `logProactive()`. Since `proactive_log.user_id` references `users.id`, the insert either silently stored the wrong user_id or failed, and the dedup lookup never found existing records.

**Fix:** Always use the entity's `user_id` field (the FK to users), not its own `id` (PK):
```typescript
// WRONG — lead.id is the leads table PK, NOT the user reference
await logProactive(lead.id, "hot_alert");
await wasProactiveSentToday(lead.id, "hot_alert");

// CORRECT — lead.user_id is the FK to users.id
await logProactive(lead.user_id, "hot_alert");
await wasProactiveSentToday(lead.user_id, "hot_alert");
```

**Prevention:** Name your FK columns explicitly (e.g., `user_id`) and never pass a row's `.id` to a function expecting a different table's reference. Code review should flag any `logProactive(entity.id, ...)` as suspicious.

---

## 17. SQL Injection via Dynamic Column Names

**Symptom:** No visible error, but malicious input in column-name positions could execute arbitrary SQL.

**Root cause:** Parameterized queries (`$1`, `$2`) protect VALUES but NOT identifiers (column/table names). String interpolation of user-influenced data into column positions is exploitable:
```typescript
// VULNERABLE — reminderField could be "id; DROP TABLE meetings; --"
const query = `UPDATE meetings SET ${reminderField} = true WHERE id = $1`;
```

**Fix:** Allowlist pattern:
```typescript
const ALLOWED_FIELDS = new Set(["reminder_24h_sent", "reminder_1h_sent"]);
if (!ALLOWED_FIELDS.has(reminderField)) {
  throw new Error(`Invalid field: ${reminderField}`);
}
// Now safe to interpolate
```

Same applies to `make_interval()`:
```sql
-- VULNERABLE: make_interval(hours => ${hoursAhead})
-- SAFE: make_interval(hours => $1)
```

---

## 18. Typing Indicator Leak in Grammy

**Symptom:** Bot keeps showing "typing..." forever after an error, consuming Telegram API quota.

**Root cause:** `setInterval(() => ctx.replyWithChatAction("typing"), 4000)` without cleanup in error path.

**Fix:** Always use `try/finally`:
```typescript
const typingInterval = setInterval(() => {
  ctx.replyWithChatAction("typing").catch(() => {});
}, 4000);

try {
  await processWithClaude(messageText);
} finally {
  clearInterval(typingInterval);
}
```

---

## 19. SCP Missed Files on Deploy

**Symptom:** Docker build succeeds but new feature doesn't work. Logs show old behavior.

**Root cause:** `scp -r src/` copied most files but missed a newly created file (often in a subdirectory like `scheduler/`). The old file was still in the Docker build context from a previous copy.

**Fix:** After SCP, always verify the critical file exists on the server:
```bash
ssh "$SERVER" "ls -la /opt/mybot/src/scheduler/index.ts && head -5 /opt/mybot/src/scheduler/index.ts"
```

Or use a checksumming approach:
```bash
# Local
find src -name "*.ts" -exec md5sum {} \; | sort > /tmp/local.md5
# Remote
ssh "$SERVER" "cd /opt/mybot && find src -name '*.ts' -exec md5sum {} \;" | sort > /tmp/remote.md5
diff /tmp/local.md5 /tmp/remote.md5
```

---

## 20. Zod Validation Catches Missing Env Vars Too Late

**Symptom:** Bot starts fine but crashes when a specific feature is triggered (e.g., "schedule a zoom" fails because `ZOOM_CLIENT_SECRET` is not set).

**Root cause:** Env vars were read via raw `process.env.VAR_NAME` at call time, not at startup. Missing vars only surface when the code path is hit.

**Fix:** Centralize ALL env vars through a Zod schema at the top of `config.ts`. Mark required vars as `z.string().min(1)` and optional vars as `z.string().optional()`. Call `envSchema.safeParse(process.env)` at import time — container won't start if any required var is missing.

See `references/custom-sales-bot-patterns.md` for full example.

---

## 21. Voice Messages Not Transcribed (Audio Provider Auto-Detection)

**Symptom:** Bot receives voice messages but doesn't transcribe them, or transcription is inconsistent. Bot may say "ломается локальный скрипт транскрибации".

**Root cause:** OpenClaw auto-detects audio provider by checking API keys in order: `openai → groq → deepgram → google`. If `OPENAI_API_KEY` is set, OpenAI Whisper is picked even when Deepgram would be more reliable (especially for Russian). OpenAI via AI Gateway can be unstable (timeouts, failover issues).

**Fix:** Explicitly set Deepgram Nova-3 as the audio provider in openclaw.json:
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

**Verification:** Send a voice message to the bot. If using a custom `transcribe_audio.py` script, also update its model from `nova-2` to `nova-3`.

**Source code path:** Auto-detection logic is in `/app/src/media-understanding/runner.ts` → `resolveAutoEntries()` → `resolveKeyEntry()` which iterates `AUTO_AUDIO_KEY_PROVIDERS = ["openai", "groq", "deepgram", "google"]`.

---

## 22. Web Search Provider Expired (Brave → Perplexity)

**Symptom:** Every web_search call fails with `422: SUBSCRIPTION_TOKEN_INVALID`. Cron jobs that depend on web search also fail.

**Root cause:** Brave Search API key expired. Brave keys have limited validity and require manual renewal at brave.com/search/api.

**Fix:** Switch to Perplexity as web search provider in openclaw.json:
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
Requires `PERPLEXITY_API_KEY` in container env vars.

**Alternative:** If no API key is available, the bot can use a workspace Python script with DuckDuckGo (no API key needed):
```python
# web_search.py in workspace — DuckDuckGo HTML scraping fallback
import requests
from bs4 import BeautifulSoup
r = requests.get("https://html.duckduckgo.com/html/", params={"q": query})
```

---

## 23. Cron Can't Find Private Telegram Channel

**Symptom:** Cron job for channel digest fails. Bot logs: "Could not get entity" or "username not found". The cron prompt references `@toporlive` but the real channel has no public username.

**Root cause:** Private Telegram channels (or channels that changed username) can't be resolved by `@username`. Need numeric channel ID.

**Fix:** Find the channel ID via Telethon:
```python
async for d in client.iter_dialogs(limit=500):
    if "search_term" in d.name.lower():
        print(f"{d.name} | id={d.id}")
```

Then use the numeric ID in your fetch script:
```python
CHANNEL_ID = -1001754252633  # Private channel, no username
channel = await client.get_entity(CHANNEL_ID)
```

**Important:** Private channel links use `https://t.me/c/CHANNEL_ID/MSG_ID` format (without the `-100` prefix for the link).

---

## 24. SQLite "Readonly Database" for Telethon Session

**Symptom:** Telethon crashes with `sqlite3.OperationalError: attempt to write a readonly database` when opening session file.

**Root cause:** SQLite needs write access to the **directory** (not just the file) to create WAL/journal files. If the workspace directory is owned by root, the node user (UID 1000) can't create these temp files.

**Fix:** Fix both file AND directory ownership:
```bash
# Fix directory (this is what people miss)
chown 1000:1000 /var/lib/docker/volumes/openclaw-friend-workspace/_data

# Fix session file
chown 1000:1000 /var/lib/docker/volumes/openclaw-friend-workspace/_data/natalya_session.session
```

---

## 25. Pip Packages Lost After Container Recreate

**Symptom:** After `docker rm + docker run` (not just `docker restart`), all pip packages are gone. Bot tools fail with `ModuleNotFoundError`.

**Root cause:** `docker restart` preserves the container filesystem layer. `docker rm + run` creates a fresh container from the base image — only volume-mounted data survives.

**Fix:** Create a `setup_deps.sh` script in the workspace volume (which survives recreates), plus a host-level auto-runner:

```bash
# setup_deps.sh — in workspace volume
#!/bin/bash
echo "[setup_deps] Installing dependencies..."
apt-get update -qq && apt-get install -y -qq ffmpeg chromium xvfb 2>&1 | tail -3
pip3 install --break-system-packages --quiet telethon python-dotenv yt-dlp pydub playwright httpx
playwright install chromium 2>&1 | tail -2
playwright install-deps chromium 2>&1 | tail -2
echo "[setup_deps] Done"
```

```bash
# Host-level post-start script
cat > /usr/local/bin/openclaw-bot-post-start.sh << 'EOF'
#!/bin/bash
sleep 10
docker exec -u root $1 bash /home/node/.openclaw/workspace/setup_deps.sh
docker network connect ai-gateway-network $1 2>/dev/null || true
EOF
chmod +x /usr/local/bin/openclaw-bot-post-start.sh

# Add to crontab for auto-run on reboot
(crontab -l; echo "@reboot /usr/local/bin/openclaw-bot-post-start.sh openclaw-friend >> /var/log/openclaw-setup.log 2>&1") | crontab -
```

---

## 26. Telethon Env Var Name Mismatch

**Symptom:** Telethon script fails with `ValueError: Your API ID or Hash cannot be empty or None`.

**Root cause:** The `.credentials/telethon.env` file uses `TELEGRAM_API_ID` but the Python script reads `os.getenv("API_ID")`.

**Fix:** Always check what the .env file actually defines:
```bash
cat .credentials/telethon.env
# TELEGRAM_API_ID=37845924   ← actual key name
# TELEGRAM_API_HASH=2b7b...
```

Then match in Python:
```python
from dotenv import load_dotenv
load_dotenv("/path/.credentials/telethon.env")
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))  # Match the actual env key
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
```
