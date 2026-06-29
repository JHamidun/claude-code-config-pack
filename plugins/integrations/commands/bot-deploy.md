---
description: Deploy Telegram bot to production с Docker и webhook setup
argument-hint: [staging / production]
---

# 🚀 Bot Deploy: $ARGUMENTS

Deploy Telegram bot to **$ARGUMENTS** environment

## Prerequisites Check:

### Required
- [ ] Bot token configured
- [ ] Database ready (MongoDB/PostgreSQL)
- [ ] Docker installed
- [ ] Domain/IP for webhook (production only)
- [ ] SSL certificate (production only)

### Optional
- [ ] Redis для caching
- [ ] Monitoring setup
- [ ] Backup strategy

## Process:

### 1. Environment Selection

**Staging:**
- Use polling mode
- Local database
- Debug logging
- No SSL required

**Production:**
- Use webhook mode
- Production database
- Info logging
- SSL required

### 2. Generate Deployment Files

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run bot
CMD ["python", "bot.py"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram-bot
    restart: unless-stopped

    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ENVIRONMENT=$ARGUMENTS
      - WEBHOOK_URL=${WEBHOOK_URL}  # production only

    ports:
      - "8080:8080"  # webhook endpoint

    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

    depends_on:
      - database
      - redis

    networks:
      - bot-network

  database:
    image: mongo:7  # or postgres:16
    container_name: bot-database
    restart: unless-stopped

    environment:
      MONGO_INITDB_ROOT_USERNAME: ${DB_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${DB_PASSWORD}

    volumes:
      - db_data:/data/db

    networks:
      - bot-network

  redis:
    image: redis:7-alpine
    container_name: bot-redis
    restart: unless-stopped

    command: redis-server --appendonly yes

    volumes:
      - redis_data:/data

    networks:
      - bot-network

  # Nginx reverse proxy (production only)
  nginx:
    image: nginx:alpine
    container_name: bot-nginx
    restart: unless-stopped

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro

    depends_on:
      - bot

    networks:
      - bot-network

    profiles: ["production"]  # only in production

volumes:
  db_data:
  redis_data:

networks:
  bot-network:
    driver: bridge
```

#### .env
```bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ENVIRONMENT=$ARGUMENTS

# Database
DB_USER=bot_user
DB_PASSWORD=secure_password_here
DATABASE_URL=mongodb://bot_user:secure_password_here@database:27017/bot_db

# Redis
REDIS_URL=redis://redis:6379/0

# Webhook (production only)
WEBHOOK_URL=https://yourdomain.com/webhook
WEBHOOK_PORT=8080

# Monitoring
SENTRY_DSN=  # optional
LOG_LEVEL=INFO
```

### 3. Webhook Setup (Production Only)

#### Set Webhook
```python
# In bot.py
import os
from fastapi import FastAPI, Request
from telegram.ext import Application

app_fastapi = FastAPI()
telegram_app = Application.builder().token(os.getenv('BOT_TOKEN')).build()

@app_fastapi.post("/webhook")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

@app_fastapi.get("/health")
async def health():
    return {"status": "ok", "bot": telegram_app.bot.username}

# Set webhook on startup
async def setup_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')
    await telegram_app.bot.set_webhook(
        url=f"{webhook_url}/webhook",
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    import uvicorn
    import asyncio

    asyncio.run(setup_webhook())
    uvicorn.run(app_fastapi, host="YOUR_PUBLIC_IP", port=8080)
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location /webhook {
        proxy_pass http://bot:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://bot:8080;
    }
}
```

### 4. Deploy Commands

#### Staging
```bash
# Build and start
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f bot

# Test bot
curl http://localhost:8080/health
```

#### Production
```bash
# Build
docker-compose --profile production build

# Start services
docker-compose --profile production up -d

# Verify webhook
curl https://yourdomain.com/health

# Monitor logs
docker-compose logs -f bot

# Check Telegram webhook status
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### 5. Health Checks

**Monitoring script:**
```bash
#!/bin/bash

# Check container status
if ! docker ps | grep -q telegram-bot; then
    echo "❌ Bot container not running"
    exit 1
fi

# Check health endpoint
if ! curl -f http://localhost:8080/health; then
    echo "❌ Health check failed"
    exit 1
fi

# Check webhook (production)
if [ "$ENV" = "production" ]; then
    WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
    if echo "$WEBHOOK_INFO" | grep -q '"ok":true'; then
        echo "✅ Webhook configured correctly"
    else
        echo "❌ Webhook issues: $WEBHOOK_INFO"
        exit 1
    fi
fi

echo "✅ All checks passed"
```

### 6. Rollback Strategy

**In case of issues:**
```bash
# 1. Stop new version
docker-compose down

# 2. Restore previous version
git checkout <previous-commit>

# 3. Rebuild and deploy
docker-compose build
docker-compose up -d

# 4. Verify
docker-compose logs -f bot
curl http://localhost:8080/health
```

**Automatic rollback with health check:**
```bash
#!/bin/bash

# Deploy new version
docker-compose up -d --build

# Wait for startup
sleep 10

# Health check
if curl -f http://localhost:8080/health; then
    echo "✅ Deployment successful"
else
    echo "❌ Health check failed, rolling back"
    git checkout HEAD~1
    docker-compose up -d --build
    exit 1
fi
```

### 7. Post-Deploy Verification

**Checklist:**
- [ ] Bot responds to /start
- [ ] Database connection works
- [ ] Logs are being written
- [ ] Health endpoint returns 200
- [ ] Webhook receiving updates (production)
- [ ] Error handling works
- [ ] User data persists
- [ ] Metrics being collected

**Test commands:**
```bash
# 1. Test bot directly
# Send /start to bot in Telegram

# 2. Check logs for errors
docker-compose logs --tail=100 bot | grep ERROR

# 3. Monitor resource usage
docker stats telegram-bot

# 4. Check database
docker exec -it bot-database mongo  # or psql
```

### 8. Monitoring Setup

**Log aggregation:**
```yaml
# Add to docker-compose.yml
  bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Prometheus metrics (optional):**
```python
from prometheus_client import Counter, Histogram, start_http_server

messages_received = Counter('bot_messages_received', 'Messages received')
command_duration = Histogram('bot_command_duration', 'Command execution time')

# In handlers
messages_received.inc()
with command_duration.time():
    await handle_command()

# Start metrics server
start_http_server(9090)
```

### 9. Backup & Restore

**Database backup:**
```bash
# Backup
docker exec bot-database mongodump --out=/backup

# Restore
docker exec bot-database mongorestore /backup
```

**Automated daily backup:**
```bash
#!/bin/bash
# Save as backup.sh, run via cron

DATE=$(date +%Y%m%d)
docker exec bot-database mongodump --out=/backup/dump_$DATE
find /backup -name "dump_*" -mtime +7 -delete  # Keep 7 days
```

## Output:

### Deployment Summary
```
🚀 Deployment to $ARGUMENTS

Status: ✅ Success
Environment: $ARGUMENTS
Webhook: [enabled/disabled]
Database: [type]
Services: [list]

Health Check: ✅ Passing
Logs: [location]
Monitoring: [setup]

Next Steps:
- Test bot functionality
- Monitor logs for errors
- Set up alerts
- Schedule backups
```

## Examples:

```
/bot-deploy staging
```

```
/bot-deploy production
```

---

**Deploying bot! 🚀**