---
name: telegram-bot-toolkit
description: Comprehensive toolkit for Telegram bot development, testing, debugging, and deployment. Specializes in python-telegram-bot, Telethon, scene management patterns, middleware configuration, and production deployment strategies.
keywords: telegram, bot, python-telegram-bot, telethon, scenes, middleware, webhooks, deployment, debugging
---

# Telegram Bot Toolkit

## Purpose
Специализированный навык для разработки, отладки и deployment Telegram ботов на Python. Основан на best practices для production-ready ботов.

## Capabilities

### 1. Bot Architecture & Patterns

#### Scene/State Management
**Best practices для scene-based flows:**

```python
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

# Scene states
ONBOARDING, SETTINGS, MAIN_MENU = range(3)

def create_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ONBOARDING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_onboarding)
            ],
            SETTINGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings)
            ],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        # CRITICAL: Per-user conversations
        per_user=True,
        per_chat=True,
        per_message=False
    )
```

**Common scene management issues:**
- ❌ Забытие `per_user=True` → scenes конфликтуют между users
- ❌ Commands handled as text → add specific command handlers BEFORE text handlers
- ❌ No fallback → users get stuck
- ✅ Always provide escape hatch (`/cancel`, `/start`)

#### Middleware Order
**CRITICAL: Правильный порядок middleware:**

```python
from telegram.ext import Application

app = Application.builder().token(BOT_TOKEN).build()

# 1. СНАЧАЛА: Logging middleware (для debugging всего)
app.add_handler(MessageHandler(filters.ALL, log_all_updates), group=-1)

# 2. ЗАТЕМ: Authentication/Authorization
app.add_handler(MessageHandler(filters.ALL, check_auth), group=0)

# 3. ЗАТЕМ: Commands (BEFORE conversation handler)
app.add_handler(CommandHandler('start', start_command), group=1)
app.add_handler(CommandHandler('help', help_command), group=1)
app.add_handler(CommandHandler('settings', settings_command), group=1)

# 4. НАКОНЕЦ: Conversation handler для scenes
app.add_handler(conversation_handler, group=2)

# 5. LAST: Fallback для unknown messages
app.add_handler(MessageHandler(filters.TEXT, unknown_handler), group=999)
```

**Почему это важно:**
- Commands в group=1, conversation в group=2 → commands обрабатываются first
- Logging в group=-1 → видишь все updates
- Fallback в group=999 → catches anything not handled

### 2. Common Bot Patterns

#### Inline Keyboards
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Stats", callback_data='stats'),
            InlineKeyboardButton("⚙️ Settings", callback_data='settings')
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data='help'),
            InlineKeyboardButton("🚪 Exit", callback_data='exit')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # ALWAYS answer callback queries!

    if query.data == 'stats':
        await query.edit_message_text("Stats: ...")
    elif query.data == 'settings':
        await query.edit_message_text("Settings: ...")
```

#### User Context Management
```python
# Store user data in context
context.user_data['step'] = 'onboarding'
context.user_data['settings'] = {}

# Store chat data
context.chat_data['last_command'] = '/start'

# Bot-wide data
context.bot_data['active_users'] = set()
```

#### File Uploads/Downloads
```python
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document

    # Get file
    file = await context.bot.get_file(document.file_id)

    # Download
    file_path = f"downloads/{document.file_name}"
    await file.download_to_drive(file_path)

    # Process...

    # Send back
    await update.message.reply_document(
        document=open(processed_path, 'rb'),
        filename='processed.pdf'
    )
```

### 3. Testing Strategies

#### Unit Tests
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_start_command():
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()

    context = MagicMock()
    context.user_data = {}

    await start(update, context)

    update.message.reply_text.assert_called_once()
    assert context.user_data['step'] == 'onboarding'
```

#### Integration Tests with Mock API
```python
from telegram.ext import ApplicationBuilder
from tests.mock_telegram import MockTelegramAPI

@pytest.fixture
async def app():
    mock_api = MockTelegramAPI()
    app = ApplicationBuilder().token("test-token").build()
    app._bot._http_client = mock_api
    return app

@pytest.mark.asyncio
async def test_full_onboarding_flow(app):
    # Simulate user messages
    await app.process_update(create_message('/start'))
    await app.process_update(create_message('John'))
    await app.process_update(create_message('john@example.com'))

    # Assert final state
    assert user_completed_onboarding(12345)
```

### 4. Deployment Patterns

#### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run bot
CMD ["python", "bot.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - MONGODB_URI=${MONGODB_URI}
      - REDIS_URL=${REDIS_URL}
    restart: unless-stopped
    depends_on:
      - mongodb
      - redis

  mongodb:
    image: mongo:7
    volumes:
      - mongodb_data:/data/db

  redis:
    image: redis:7-alpine

volumes:
  mongodb_data:
```

#### Webhook vs Polling

**Polling (development):**
```python
app.run_polling(allowed_updates=Update.ALL_TYPES)
```

**Webhook (production):**
```python
import uvicorn
from fastapi import FastAPI, Request

fastapi_app = FastAPI()

@fastapi_app.post("/webhook")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), app.bot)
    await app.process_update(update)
    return {"ok": True}

@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}

# Set webhook
await app.bot.set_webhook(
    url=f"https://your-domain.com/webhook",
    allowed_updates=Update.ALL_TYPES
)

# Run FastAPI
uvicorn.run(fastapi_app, host="YOUR_PUBLIC_IP", port=8080)
```

#### Environment Configuration
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    mongodb_uri: str
    redis_url: str | None = None
    webhook_url: str | None = None
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
```

### 5. Common Bugs & Fixes

#### Bug 1: Bot застревает в onboarding
**Причина:** Commands обрабатываются как text в conversation handler

**Fix:**
```python
# WRONG:
states={
    ONBOARDING: [
        MessageHandler(filters.TEXT, handle_onboarding)  # catches /start too!
    ]
}

# CORRECT:
states={
    ONBOARDING: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_onboarding)
    ]
}
# OR add commands to fallbacks:
fallbacks=[
    CommandHandler('start', start),
    CommandHandler('cancel', cancel)
]
```

#### Bug 2: Race conditions в async handlers
**Причина:** Multiple handlers accessing same data

**Fix:**
```python
import asyncio

# Use locks for critical sections
user_locks = {}

async def handle_payment(update, context):
    user_id = update.effective_user.id

    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()

    async with user_locks[user_id]:
        # Critical section - process payment
        balance = get_balance(user_id)
        if balance >= amount:
            deduct_balance(user_id, amount)
            process_purchase()
```

#### Bug 3: Memory leak в long-polling
**Причина:** Not cleaning up user_data

**Fix:**
```python
# Clean up после завершения conversation
async def end_conversation(update, context):
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

# Periodic cleanup
async def cleanup_inactive_users(context):
    for user_id in list(context.application.user_data.keys()):
        last_seen = context.application.user_data[user_id].get('last_seen')
        if last_seen and (datetime.now() - last_seen > timedelta(hours=24)):
            del context.application.user_data[user_id]
```

#### Bug 4: Callback queries не отвечают
**Причина:** Забыли вызвать `query.answer()`

**Fix:**
```python
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()  # ALWAYS call this first!

    # Then process
    await query.edit_message_text(f"You clicked: {query.data}")
```

### 6. Monitoring & Logging

```python
import logging
import structlog

# Structured logging
logger = structlog.get_logger()

async def log_middleware(update, context):
    logger.info(
        "update_received",
        user_id=update.effective_user.id if update.effective_user else None,
        chat_id=update.effective_chat.id if update.effective_chat else None,
        update_type=update.to_dict().get('type'),
        message_text=update.message.text if update.message else None
    )

# Error handling
async def error_handler(update, context):
    logger.error(
        "bot_error",
        error=str(context.error),
        update=update.to_dict() if update else None,
        exc_info=True
    )

    # Notify user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Попробуйте позже или /start для начала."
        )

app.add_error_handler(error_handler)
```

### 7. Database Integration

**MongoDB с motor (async):**
```python
from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    def __init__(self, uri: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client.bot_database

    async def get_user(self, user_id: int):
        return await self.db.users.find_one({"user_id": user_id})

    async def upsert_user(self, user_id: int, data: dict):
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )
```

## Usage Examples

**Debug застревание бота:**
```
"Используй telegram-bot-toolkit: бот застревает в onboarding scene после /start.
Файл: backend/bot/src/handlers/onboarding.py"
```

**Создать нового бота:**
```
"Используй telegram-bot-toolkit: создай бота с scenes:
1. Registration (имя, email)
2. Settings (notifications on/off)
3. Main menu (stats, help, logout)"
```

**Deploy бота в production:**
```
"Используй telegram-bot-toolkit: настрой production deployment:
- Docker с webhook
- MongoDB для state
- Redis для caching
- Health checks
- Monitoring"
```

**Исправить bug:**
```
"Используй telegram-bot-toolkit: команды /help и /settings не работают в conversation handler"
```

## Best Practices

1. **Always use `~filters.COMMAND`** в conversation handlers
2. **Middleware order matters:** logging → auth → commands → conversations → fallback
3. **Always answer callback queries:** `await query.answer()`
4. **Use webhooks в production** (not polling)
5. **Clean up user_data** периодически
6. **Structured logging** для debugging
7. **Locks для critical sections** (payments, balance updates)
8. **Health checks** для мониторинга
9. **Environment-based config** (не hardcode tokens)
10. **Test scene transitions** тщательно

## Resources

- [python-telegram-bot docs](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Best practices guide](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets)
