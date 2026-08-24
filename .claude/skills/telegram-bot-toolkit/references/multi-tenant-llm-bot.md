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
import re

def md_to_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__",     r"<i>\1</i>", text, flags=re.DOTALL)
    text = re.sub(r"`([^`\n]+)`",   r"<code>\1</code>", text)
    text = re.sub(r"~~(.+?)~~",     r"<s>\1</s>", text, flags=re.DOTALL)
    return text
```

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
