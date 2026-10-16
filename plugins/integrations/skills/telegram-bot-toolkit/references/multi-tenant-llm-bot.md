# Публичный LLM-бот: код паттернов

Читать, когда бот **публичный** (один токен — много юзеров) и **управляется LLM**
(агент с tool-calling, а не статичный wizard). Короткие формулировки самих ловушек
есть в теле навыка; здесь — реализация.

## 1. Изоляция данных по юзеру

Один корень `data/` с подпапкой на каждый `tg_user_id`. Никаких глобальных таблиц
с колонкой user_id как ключом — юзер живёт в своей директории и удаляется одной
`rm -rf`, без выборочных DELETE по десятку таблиц.

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

Хелперы `paths.user_dir(uid)` и `paths.topic_dir(uid, slug)` создают директорию
on-demand. Атомарных миграций при росте схемы не нужно: каждый юзер мигрирует
отдельно при следующем обращении.

## 2. BYOK sidechannel — секрет мимо LLM

Токен или ключ, который даёт юзер, **никогда не должен попасть в контекст LLM**:
оттуда он уедет в `history.jsonl` и далее во все последующие промпты.

FSM-флаг в `profile.json` перехватывает следующее сообщение **до** агента:

```python
def dispatch(message):
    text = message["text"].strip()
    profile = state.load_profile(user_id)

    # Sidechannel FSM имеет приоритет НАД LLM-агентом
    dlg = profile.get("dialog")
    if dlg and dlg.get("flow", "").startswith("byok_") and not text.startswith("/cancel"):
        handle_byok_input(text, dlg)      # пишет в Fernet blob, отвечает "✅ сохранено"
        return

    # Команды-инициаторы тоже не идут в LLM — только заводят dialog flag
    if text.startswith("/byok"):
        start_byok_wizard(parts[1:])      # profile["dialog"] = {"flow": "byok_bot"}
        return

    reply = agent.respond(user_id, chat_id, text)
    api.send_message(chat_id, reply)
```

Секрет валидируется (для tg-токена — `getMe` probe) и шифруется:

```python
import base64, hashlib, json, os
from cryptography.fernet import Fernet

def _fernet():
    pw = os.environ["SECRET_KEY"]        # random 48-char string per deploy
    key = base64.urlsafe_b64encode(hashlib.sha256(pw.encode()).digest())
    return Fernet(key)

def secret_put(uid: str, key: str, value: str):
    p = paths.user_dir(uid) / "secrets.enc"
    data = json.loads(_fernet().decrypt(p.read_bytes())) if p.exists() else {}
    data[key] = value
    p.write_bytes(_fernet().encrypt(json.dumps(data).encode()))
    p.chmod(0o600)
```

Ответ юзеру — `✅ сохранён`, **без эха значения**. Никогда `f"saved: {value}"`.

## 3. Reply keyboard как NL-shortcuts

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

`reply_markup=persistent_menu()` передавать **в каждом ответе агента** — иначе
клавиатура пропадает. Тык по `📋 Темы` приходит обычным текстом `"📋 Темы"`, и
system prompt агента знает, что это shortcut на tool `list_topics`.

Inline-кнопки — **только** на preview-сообщениях с действиями (✅ Опубликовать /
✏️ Edit / 🔄 Regen / ❌ Reject), где `callback_data` привязывает кнопку к
конкретному `draft_ts`.

## 4. Markdown → HTML

```python
import html
import re

def md_to_html(text: str) -> str:
    text = html.escape(text, quote=False)   # &, <, > — иначе Bot API 400 «can't parse entities»
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__",     r"<i>\1</i>", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]+)`",   r"<code>\1</code>", text)
    text = re.sub(r"~~(.+?)~~",     r"<s>\1</s>", text, flags=re.DOTALL)
    return text
```

Экранирование идёт **первым**: сырые `<` и `&` из ответа LLM ломают разбор сущностей, а
теги, которые добавляют замены ниже, экранировать уже нельзя.

Прогонять **только** при `parse_mode=HTML` — иначе двойная конверсия.

## 5. Conversation memory с tool_calls

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

Писать все четыре вида записей:

- `{"role": "user", "content": text}`
- `{"role": "assistant", "content": "", "tool_calls": [...]}`
- `{"role": "tool", "tool_call_id": "...", "name": "...", "content": json_string}`
- финальный assistant reply

Без `tool_calls` следующий ход агента не помнит `draft_ts` / `job_id`, который
вернул предыдущий tool. При кросс-провайдерном fallback смотри orphan-tool-message
filter в `multi-model-gateway`.

## 6. Whitelist на бете

```python
def is_whitelisted(uid: int) -> bool:
    if os.environ.get("WHITELIST_ON") != "1":
        return True
    wl = paths.whitelist_path()
    if not wl.exists():
        return False
    return str(uid) in {line.strip() for line in wl.read_text().splitlines()}
```

Добавление админом без передеплоя:

```bash
docker exec mybot bash -c "echo 12345 >> /data/whitelist.txt"
```

В отказе давать контакт: `🚫 Доступ ограничен. Напиши @admin — добавлю.`

## 7. Telethon: поиск реальных каналов (`SearchRequest`)

Tool `discover_channels` для агента. Каналы и группы по ключевому слову ищутся через
MTProto — это реальные сущности, а не выдумка LLM.

```python
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel

async def discover_channels(query: str, limit: int = 15) -> list[dict]:
    # client — уже авторизованный TelegramClient
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

Фильтр `chat.broadcast or chat.megagroup` ловит и каналы, и супергруппы; различать их
потом по полю `type`.

## 8. FloodWait: ретрай с ожиданием

`SearchRequest` и `iter_messages` под нагрузкой дают `FloodWaitError(seconds=N)`: до
20 секунд — подождать и повторить, дольше — упасть с человекочитаемой ошибкой.

```python
import asyncio
import logging
from telethon.errors import FloodWaitError

log = logging.getLogger(__name__)

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

Отдельно в system prompt агента: «Call discover_channels AT MOST 2 times per user
message» — без этого LLM делает по 6 запросов за ход, и flood-wait копится.
