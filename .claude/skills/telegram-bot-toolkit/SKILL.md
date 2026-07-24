---
name: telegram-bot-toolkit
description: Comprehensive toolkit for Telegram bot development, testing, debugging, and deployment. Specializes in python-telegram-bot, Telethon, scene management patterns, middleware configuration, and production deployment strategies. Also covers when NOT to use a bot as a TG Ads funnel — triggers «бот как коллектор базы», «антипаттерн бот-воронки», «бот из TG Ads», «воронка через бот».
keywords: telegram, bot, python-telegram-bot, telethon, scenes, middleware, webhooks, deployment, debugging, бот как коллектор, антипаттерн бот-воронки, бот из TG Ads, воронка через бот
---

# Telegram Bot Toolkit

## Purpose
Специализированный навык для разработки, отладки и deployment Telegram ботов на Python. Основан на best practices для production-ready ботов.

> **Бот как воронка из TG Ads?** Сначала прочитай `references/tg-ads-bot-funnel.md` —
> предупреждение эксперта (методология: 80% бот-воронок из TG Ads убыточны,
> бот лучше как коллектор базы, а не первичная конверсия. Паттерн: TG Ads → лендинг
> с регистрацией → бот для прогрева (бот вторичен). Cross-link: `telegram-ads-pro-ru`,
> `manychat-funnel-ru`.

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

## Multi-tenant LLM-driven bot patterns

Когда бот **публичный** (один токен — много юзеров) и **управляется LLM** (агент с tool-calling, не статичный wizard), нужны паттерны которые не покрывает стандартный python-telegram-bot wiki.

### 1. Per-user data isolation

Структура файловой системы — один корневой `data/` с подпапкой на каждого tg_user_id. Никаких глобальных таблиц с user_id-колонкой как ключом — каждый юзер живёт в своей изолированной директории, его можно полностью удалить одной `rm -rf`.

```text
data/
  users/<tg_user_id>/
    profile.json         # язык UI, режим, current_topic
    secrets.enc          # Fernet-encrypted BYOK creds
    history.jsonl        # conversation memory (rolling window)
    topics/<slug>/       # темы/проекты юзера
      config.json
      candidates.db      # SQLite
      drafts/<ts>.md
```

Хелперы `paths.user_dir(uid)`, `paths.topic_dir(uid, slug)` создают директорию on-demand. Никаких атомарных миграций при росте — каждый юзер мигрирует отдельно при следующем обращении.

### 2. BYOK sidechannel — секреты в обход LLM

Если юзер должен дать токен/ключ (свой Bot API token для auto-publish, свой ScraperVendor key, etc.), это **никогда не должно попасть в context LLM**. Иначе токен утечёт в history.jsonl и далее во все последующие prompt'ы.

Паттерн — FSM-флаг в profile.json, который **перехватывает следующее сообщение до LLM**:

```python
def dispatch(message):
    text = message["text"].strip()
    profile = state.load_profile(user_id)

    # Sidechannel FSM имеет приоритет НАД LLM-агентом
    dlg = profile.get("dialog")
    if dlg and dlg.get("flow", "").startswith("byok_") and not text.startswith("/cancel"):
        handle_byok_input(text, dlg)  # пишет в Fernet blob, отвечает "✅ сохранено"
        return

    # Команды-инициаторы тоже не идут в LLM — они только заводят dialog flag
    if text.startswith("/byok"):
        start_byok_wizard(parts[1:])  # → ставит profile["dialog"] = {"flow": "byok_bot"}
        return

    # Всё остальное — нормально в агент
    reply = agent.respond(user_id, chat_id, text)
    api.send_message(chat_id, reply)
```

Секрет валидируется (для tg-токена — `getMe` probe) и шифруется (Fernet, ключ из env `SECRET_KEY`):

```python
import base64, hashlib, json
from cryptography.fernet import Fernet

def _fernet():
    pw = os.environ["SECRET_KEY"]  # random 48-char string per deploy
    key = base64.urlsafe_b64encode(hashlib.sha256(pw.encode()).digest())
    return Fernet(key)

def secret_put(uid: str, key: str, value: str):
    p = paths.user_dir(uid) / "secrets.enc"
    data = json.loads(_fernet().decrypt(p.read_bytes())) if p.exists() else {}
    data[key] = value
    p.write_bytes(_fernet().encrypt(json.dumps(data).encode()))
    p.chmod(0o600)
```

Ответ юзеру — `✅ сохранён` **без эха** значения. Никогда не `f"saved: {value}"`.

### 3. Reply keyboard как NL-shortcuts (не callbacks)

Reply keyboard внизу под input — кнопки с эмодзи-лейблами **отправляют свой текст как обычное сообщение**. Это означает: один и тот же tool-routing цикл обрабатывает и тыкание кнопки, и свободный ввод.

```python
def persistent_menu() -> dict:
    return {
        "keyboard": [
            [{"text": "📋 Темы"}, {"text": "➕ Новая тема"}],
            [{"text": "🔎 Мониторить"}, {"text": "✍️ Черновик"}],
            [{"text": "🗓 План недели"}, {"text": "📊 Статистика"}],
            [{"text": "🔐 BYOK"}, {"text": "⚙️ Настройки"}, {"text": "❓ Помощь"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }
```

При `sendMessage` передавать `reply_markup=persistent_menu()` **в каждом ответе агента** — клавиатура держится снизу. Юзер тыкает `📋 Темы` → бот получает буквальный текст `"📋 Темы"` → агент через свой system prompt знает что это shortcut на `list_topics` tool.

**Не использовать `InlineKeyboardMarkup` для shortcuts** — callback_query поток отдельный, у него нет text content, нужно отдельное парсинг и роутинг. Reply keyboard переиспользует существующий text pipeline.

Inline кнопки **только** на preview-сообщениях с действиями (✅ Опубликовать / ✏️ Edit / 🔄 Regen / ❌ Reject) — там callback_data нужен для привязки к конкретному draft_ts.

### 4. Markdown → HTML для LLM-replies

LLM нативно генерит markdown (`**bold**`, `__italic__`, `` `code` ``). Telegram `parse_mode=Markdown` устарел; `MarkdownV2` требует escape всех `_*[]()~>#+-=|{}.!`. `HTML` — единственный реально удобный режим, но LLM в HTML не пишет.

Конвертер перед отправкой:

```python
import re

def md_to_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"<i>\1</i>", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text, flags=re.DOTALL)
    return text
```

Без этого юзер видит `**Темы**` буквальными звёздочками. Регулярки прогонять **только** если `parse_mode=HTML` — иначе двойная конверсия.

### 5. Windows Git bash `MSYS_NO_PATHCONV` trap

При тестировании slash-commands через `tg_client.py send @bot "/start"` из Git bash на Windows MSYS конвертирует `/start` → `C:/Program Files/Git/start` ДО запуска python. Бот получает мусор.

```bash
# WRONG (Git bash on Windows)
python tg_client.py send @bot "/start"
# Bot receives: "C:/Program Files/Git/start"

# RIGHT
MSYS_NO_PATHCONV=1 python tg_client.py send @bot "/start"
# Bot receives: "/start"
```

Альтернатива — вызывать Telethon напрямую из Python без bash прослойки. Документировать оба способа в README.

### 6. Telethon channel discovery (`SearchRequest`)

Для нахождения **реальных** существующих каналов/групп по ключевому слову (не LLM-галлюцинации) — `SearchRequest` MTProto:

```python
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel

async def discover_channels(query: str, limit: int = 15) -> list[dict]:
    result = await client(SearchRequest(q=query, limit=limit))
    out = []
    for chat in result.chats:
        if not isinstance(chat, Channel):
            continue
        if chat.broadcast or chat.megagroup:
            out.append({
                "ref": f"@{chat.username}" if chat.username else str(chat.id),
                "title": chat.title,
                "participants": getattr(chat, "participants_count", None),
                "verified": bool(getattr(chat, "verified", False)),
                "type": "channel" if chat.broadcast else "group",
            })
    out.sort(key=lambda x: x.get("participants") or 0, reverse=True)
    return out[:limit]
```

Фильтр `chat.broadcast or chat.megagroup` ловит и **каналы**, и **супергруппы**. Дискриминация — поле `type`.

### 7. FloodWait retry с backoff

`SearchRequest` и `iter_messages` на нагрузке дают `FloodWaitError(seconds=N)`. Короткие waits — retry, длинные — bail с человекочитаемой ошибкой:

```python
from telethon.errors import FloodWaitError

async def with_flood_retry(coro_factory, max_attempts=2):
    for attempt in range(max_attempts):
        try:
            return await coro_factory()
        except FloodWaitError as e:
            if e.seconds <= 20 and attempt < max_attempts - 1:
                log.info("flood wait %ss, retrying", e.seconds)
                await asyncio.sleep(e.seconds + 1)
                continue
            raise RuntimeError(f"Telegram flood-wait: {e.seconds}s — retry later")
```

В агенте — добавить в system prompt: `"Call discover_channels AT MOST 2 times per user message"`. Иначе LLM спамит 6 разных query за одно сообщение → flood-wait накапливается.

### 8. `iter_messages` универсален для channel и megagroup

Нет отдельных веток для broadcast и megagroup — `client.iter_messages(entity)` работает одинаково. `entity` через `get_entity(@username)` resolve'ит и каналы, и группы. Разница только в семантике views/reactions:

- Broadcast (`@durov`): `msg.views` отражает охват
- Megagroup (`@python_ru`): `msg.views = 0`, но `msg.reactions` есть

При scoring виральности — учитывать оба:

```python
def virality(msg) -> float:
    views = float(msg.views or 0)
    reactions = sum(r.count for r in (msg.reactions.results or []))
    forwards = float(msg.forwards or 0)
    return views + 3 * reactions + 5 * forwards
```

### 9. Conversation memory persistence (LLM agent)

LLM-driven bot ≠ scripted FSM bot. Сообщения юзера + ответы агента + **tool_calls трейс** должны жить в файле:

```python
def history_load(uid, limit=20):
    p = paths.user_dir(uid) / "history.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines[-limit:] if l.strip()]

def history_append(uid, message):
    p = paths.user_dir(uid) / "history.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")
```

Что писать в memory:

- user message (`{"role": "user", "content": text}`)
- assistant с tool_calls (`{"role": "assistant", "content": "", "tool_calls": [...]}`)
- tool результаты (`{"role": "tool", "tool_call_id": "...", "name": "...", "content": json_string}`)
- финальный assistant reply

**Без сохранения tool_calls** следующий ход агента не помнит draft_ts/job_id который вернул предыдущий tool. См. `multi-model-gateway` про orphan-tool-message filter — критично при кросс-провайдерном fallback.

### 10. Whitelist в data/ + admin overrides

Для публичного бота на бете — `data/whitelist.txt` с одним tg_user_id на строку, проверка перед dispatch:

```python
def is_whitelisted(uid: int) -> bool:
    if os.environ.get("WHITELIST_ON") != "1":
        return True
    wl = paths.whitelist_path()
    if not wl.exists():
        return False
    return str(uid) in {line.strip() for line in wl.read_text().splitlines()}
```

Админ shell:

```bash
docker exec mybot bash -c "echo 12345 >> /data/whitelist.txt"
```

В отказе — ссылка на админа: `🚫 Доступ ограничен. Напиши @admin — добавлю.`

## Resources

- [python-telegram-bot docs](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telethon docs](https://docs.telethon.dev/)
- [Best practices guide](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets)
