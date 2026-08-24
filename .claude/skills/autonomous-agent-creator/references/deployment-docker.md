# Docker Deployment Patterns

> Standard deployment patterns for Hermes and OpenClaw agents on the VPS.
> All examples assume Ubuntu 22.04, Docker with Compose v2.

---

## Hermes Agent -- Standard Pattern

### docker-compose.yml

```yaml
services:
  hermes-BOTNAME:
    image: hermes-agent:local
    container_name: hermes-BOTNAME
    restart: unless-stopped
    network_mode: host
    environment:
      HERMES_HOME: /opt/data
      HERMES_UID: "1000"
      HERMES_GID: "1000"
      HERMES_INFERENCE_PROVIDER: "gemini"      # optional: force provider
      TELEGRAM_BOT_TOKEN: "${TELEGRAM_BOT_TOKEN}"
      TELEGRAM_ALLOWED_USERS: "${TELEGRAM_ALLOWED_USERS}"
      TELEGRAM_HOME_CHANNEL: "${TELEGRAM_HOME_CHANNEL}"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY}"
      GOOGLE_API_KEY: "${GOOGLE_API_KEY}"
      GEMINI_API_KEY: "${GOOGLE_API_KEY}"
      DEEPGRAM_API_KEY: "${DEEPGRAM_API_KEY}"
      PERPLEXITY_API_KEY: "${PERPLEXITY_API_KEY}"
      FAL_KEY: "${FAL_KEY}"
    volumes:
      - hermes-BOTNAME-data:/opt/data
    command: ["gateway", "run"]

volumes:
  hermes-BOTNAME-data:
    external: true
```

### Pre-start Checklist

```bash
# 1. Create external volume (survives docker compose down)
docker volume create hermes-BOTNAME-data

# 2. Create .env file with credentials
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ALLOWED_USERS=12345678,87654321
TELEGRAM_HOME_CHANNEL=-100123456789
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
DEEPGRAM_API_KEY=...
PERPLEXITY_API_KEY=pplx-...
FAL_KEY=...
EOF

# 3. Seed config.yaml into volume
docker run --rm -v hermes-BOTNAME-data:/opt/data alpine sh -c "
  mkdir -p /opt/data && chown -R 10000:10000 /opt/data
"
# Copy config.yaml
docker run --rm \
  -v hermes-BOTNAME-data:/opt/data \
  -v $(pwd)/config.yaml:/src/config.yaml:ro \
  alpine cp /src/config.yaml /opt/data/config.yaml

# 4. Optionally seed SOUL.md
docker run --rm \
  -v hermes-BOTNAME-data:/opt/data \
  -v $(pwd)/SOUL.md:/src/SOUL.md:ro \
  alpine cp /src/SOUL.md /opt/data/SOUL.md

# 5. Start
docker compose up -d
```

### With Custom Plugins and Skills

```yaml
    volumes:
      - hermes-BOTNAME-data:/opt/data
      - ./plugins/my-plugin:/opt/data/plugins/my-plugin:ro
      - ./skills/my-skill:/opt/data/skills/my-skill:ro
      - ./SOUL.md:/opt/data/SOUL.md:ro
      - ./config.yaml:/opt/data/config.yaml:ro
```

### Key Points

- `network_mode: host` -- simplest networking, no port mapping needed
- External volume -- data survives `docker compose down` and `up`
- `HERMES_UID=1000` -- matches host user for bind mounts (s6-overlay remaps)
- s6-overlay handles PID1, UID remap, config seeding automatically
- `config.yaml` is re-read on every incoming message (no restart for config changes)
- `SOUL.md` is loaded at conversation start (restart needed for changes to apply to active sessions)

---

## OpenClaw Agent -- Standard Pattern

### Step-by-step Deployment

```bash
# 1. Create volumes
docker volume create openclaw-BOTNAME-config
docker volume create openclaw-BOTNAME-workspace

# 2. Set ownership (node user = UID 1000)
docker run --rm -v openclaw-BOTNAME-config:/data alpine chown -R 1000:1000 /data
docker run --rm -v openclaw-BOTNAME-workspace:/data alpine chown -R 1000:1000 /data

# 3. Copy openclaw.json config
docker run --rm \
  -v openclaw-BOTNAME-config:/config \
  -v $(pwd)/openclaw.json:/src/openclaw.json:ro \
  alpine cp /src/openclaw.json /config/openclaw.json

# 4. Copy skills (optional)
docker run --rm \
  -v openclaw-BOTNAME-config:/config \
  -v $(pwd)/skills:/src:ro \
  alpine sh -c "mkdir -p /config/skills && cp -r /src/* /config/skills/ && chown -R 1000:1000 /config/skills"

# 5. Copy SOUL.md (optional)
docker run --rm \
  -v openclaw-BOTNAME-config:/config \
  -v $(pwd)/SOUL.md:/src/SOUL.md:ro \
  alpine cp /src/SOUL.md /config/SOUL.md

# 6. Start container
docker run -d \
  --name openclaw-BOTNAME \
  --init \
  --restart unless-stopped \
  --dns 8.8.8.8 --dns 1.1.1.1 \
  -e HOME=/home/node \
  -e NODE_ENV=production \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e OPENCLAW_GATEWAY_TOKEN="$GATEWAY_TOKEN" \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -v openclaw-BOTNAME-config:/home/node/.openclaw \
  -v openclaw-BOTNAME-workspace:/home/node/.openclaw/workspace \
  -p 127.0.0.1:PORT:18789 \
  -p 127.0.0.1:PORT+1:18790 \
  openclaw:local

# 7. Connect to AI Gateway network (if using gateway)
docker network connect ai-gateway-network openclaw-BOTNAME
```

### Key Points

- `--init` -- **CRITICAL**: prevents zombie processes (Node.js does not reap children by default)
- `chown 1000:1000` -- node user inside container
- Ports bound to `127.0.0.1` -- not exposed to internet
- AI Gateway network -- for centralized model routing through shared gateway
- `--dns 8.8.8.8 --dns 1.1.1.1` -- Docker internal DNS can be unreliable
- Config changes require container restart (unlike Hermes which hot-reloads)

---

## Port Allocation (заведи свою таблицу)

Порты раздаются один раз и записываются — иначе третий бот молча встанет на порт второго
и «перестанет отвечать» без единой ошибки в логах.

| Range | Assignment | Notes |
|-------|-----------|-------|
| 18789-18790 | Internal (container default) | Never exposed externally |
| 18791 | `openclaw-<bot1>` gateway | заполни своим |
| 18792 | `openclaw-<bot1>` control | control UI |
| 18793-18800 | Reserved for openclaw bots | 4 slots |
| 18801-18810 | New deployments | 5 slots |

**Rule:** Always bind to `127.0.0.1:PORT`, never `0.0.0.0:PORT`. Docker bypasses UFW when binding to all interfaces.

---

## AI Gateway Network

All agent containers connect to the shared `ai-gateway-network` Docker network for model routing:

```bash
# Create network (once)
docker network create ai-gateway-network

# Connect container
docker network connect ai-gateway-network openclaw-BOTNAME
docker network connect ai-gateway-network hermes-BOTNAME
```

Internal URL from containers: `http://ai-gateway:8080`

Supported providers via gateway: OpenAI, Anthropic, Gemini, Bedrock, Perplexity.

---

## Health Checks

### Hermes

```bash
# Check logs
docker logs hermes-BOTNAME --tail 20

# Check if running
docker ps --filter name=hermes-BOTNAME --format "{{.Status}}"

# Check memory usage
docker stats hermes-BOTNAME --no-stream

# Verify Telegram connection (look for "listening" in logs)
docker logs hermes-BOTNAME 2>&1 | grep -i "telegram\|listen\|connected"
```

### OpenClaw

```bash
# Check logs
docker logs openclaw-BOTNAME --tail 20 2>&1

# Look for startup success
docker logs openclaw-BOTNAME 2>&1 | grep -E "model|telegram|listen|error|ready"

# Health endpoint
curl -sf http://127.0.0.1:PORT/healthz && echo OK || echo FAIL

# Control UI (if enabled)
curl -sf http://127.0.0.1:PORT+1/ && echo "Control UI OK"
```

---

## Restart and Update Patterns

### Config Change (Hermes)

```bash
# config.yaml changes -- NO restart needed (hot-reload per message)
# Just edit the file in the volume:
docker run --rm \
  -v hermes-BOTNAME-data:/opt/data \
  -v $(pwd)/config.yaml:/src/config.yaml:ro \
  alpine cp /src/config.yaml /opt/data/config.yaml
# Next incoming message will use new config
```

### Config Change (OpenClaw)

```bash
# Config changes require restart:
docker run --rm \
  -v openclaw-BOTNAME-config:/config \
  -v $(pwd)/openclaw.json:/src/openclaw.json:ro \
  alpine cp /src/openclaw.json /config/openclaw.json

docker restart openclaw-BOTNAME
```

### Image Update (Both Engines)

```bash
# Hermes (via compose)
docker compose pull && docker compose up -d

# OpenClaw (manual)
docker stop openclaw-BOTNAME
docker rm openclaw-BOTNAME
# Re-run the docker run command with same volumes (data persists)
```

### SOUL.md Update

```bash
# Both engines: copy new SOUL.md
docker run --rm \
  -v VOLUME_NAME:/data \
  -v $(pwd)/SOUL.md:/src/SOUL.md:ro \
  alpine cp /src/SOUL.md /data/SOUL.md

# Hermes: takes effect on next session reset
# OpenClaw: restart container
docker restart openclaw-BOTNAME
```

---

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| Bot doesn't respond | `docker logs CONTAINER --tail 50` | Check bot token, allowed users |
| "Model not found" | Logs for model string | Verify model format `provider/model` |
| Container restarts in loop | `docker logs CONTAINER` | Usually missing env var or bad config |
| High memory usage | `docker stats CONTAINER` | Check for memory leaks, restart |
| Telegram webhook conflict | Another bot instance running | Stop duplicate container |
| Permission denied on volume | Volume ownership | `chown -R UID:GID` inside volume |
| DNS resolution fails | `docker exec CONTAINER nslookup google.com` | Add `--dns 8.8.8.8` |
| Gateway token mismatch | Compare env var vs config | Must be identical strings |
| Zombie processes | `docker top CONTAINER` | Add `--init` flag |

---

## Docker Compose Template (Multi-Bot)

```yaml
# docker-compose.yml for multiple Hermes bots sharing .env
services:
  hermes-bot1:
    image: hermes-agent:local
    container_name: hermes-bot1
    restart: unless-stopped
    network_mode: host
    env_file: .env.bot1
    environment:
      HERMES_HOME: /opt/data
    volumes:
      - hermes-bot1-data:/opt/data
    command: ["gateway", "run"]

  hermes-bot2:
    image: hermes-agent:local
    container_name: hermes-bot2
    restart: unless-stopped
    network_mode: host
    env_file: .env.bot2
    environment:
      HERMES_HOME: /opt/data
    volumes:
      - hermes-bot2-data:/opt/data
    command: ["gateway", "run"]

volumes:
  hermes-bot1-data:
    external: true
  hermes-bot2-data:
    external: true
```

---

## Backup and Recovery

```bash
# Backup volume data
docker run --rm \
  -v hermes-BOTNAME-data:/data:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/hermes-BOTNAME-$(date +%Y%m%d).tar.gz -C /data .

# Restore volume data
docker run --rm \
  -v hermes-BOTNAME-data:/data \
  -v $(pwd)/backups:/backup:ro \
  alpine sh -c "cd /data && tar xzf /backup/hermes-BOTNAME-20260601.tar.gz"
```

Key files in volume to back up:
- `config.yaml` -- agent configuration
- `SOUL.md` -- persistent knowledge
- `MEMORY.md` -- agent memory
- `USER.md` -- user profile data
- `skills/` -- custom skills
- `plugins/` -- custom plugins
