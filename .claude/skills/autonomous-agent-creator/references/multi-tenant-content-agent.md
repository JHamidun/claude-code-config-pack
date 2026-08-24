# Multi-tenant content agent patterns

Архитектурные паттерны для **публичных** Telegram-агентов (один токен — много юзеров) которые **управляются LLM** (не статичный wizard), мониторят источники, генерят контент. Извлечено из реального деплоя мультиарендного контент-агента на VPS.

Этот reference не дублирует `hermes-plugin-howto` или `openclaw-extension-howto` — те покрывают одиночные агенты. Здесь — **multi-tenant специфика**: per-user data isolation, BYOK, сид-каналы, content-pipeline staging.

## 1. Per-user data isolation

Никакой глобальной таблицы с `user_id` колонкой. Каждый юзер живёт в **своей директории** — отдельная файловая система целиком per tenant:

```text
data/
  users/<tg_user_id>/
    profile.json          # язык UI, режим доставки, current_topic
    secrets.enc           # Fernet-encrypted BYOK creds (см. §3)
    history.jsonl         # conversation memory (rolling 30 turns)
    topics/<slug>/        # темы юзера (он может иметь N параллельно)
      config.json         # описание, источники, расписание
      candidates.db       # SQLite — найденные кандидаты для постов
      published.db        # SQLite — опубликованные посты + метрики
      media_plan.json     # слоты на горизонт
      drafts/<ts>.md      # черновики
      drafts/<ts>-stages/ # этапы pipeline (см. §5)
```

Удалить юзера — одной `shutil.rmtree(paths.user_dir(uid))`. Никаких миграций колонок. Никаких ANALYZE на growing-таблицах.

Хелперы:

```python
DATA_ROOT = Path(os.environ.get("DATA_DIR") or "/data")

def user_dir(uid):
    p = DATA_ROOT / "users" / str(uid)
    p.mkdir(parents=True, exist_ok=True)
    return p

def topic_dir(uid, slug):
    p = user_dir(uid) / "topics" / slug
    p.mkdir(parents=True, exist_ok=True)
    return p
```

## 2. Whitelist для бета-периода

Публичный бот = жертва спама на старте. До того как продукт прошёл бету:

```text
data/whitelist.txt
─────────────────
272540053
1005315440
...
```

```python
def is_whitelisted(uid):
    if os.environ.get("WHITELIST_ON") != "1":
        return True
    wl = DATA_ROOT / "whitelist.txt"
    if not wl.exists():
        return False
    return str(uid) in {line.strip() for line in wl.read_text().splitlines()}

def dispatch(msg):
    uid = msg["from"]["id"]
    if not is_whitelisted(uid):
        api.send_message(msg["chat"]["id"],
            "🚫 Доступ ограничен. Напиши {ADMIN_HANDLE} — добавлю.")
        return
    # ...
```

В прод после беты — `WHITELIST_ON=0`, файл не удалять (хорошая ground truth списка ранних юзеров).

## 3. Fernet BYOK — секреты в обход LLM context

Юзер даёт свои ключи (Bot API токен своего канала, свой ScrapeCreators key, etc.). **Никогда** не должен попасть в history.jsonl → LLM context → следующие prompt'ы.

### Шифрование

```python
import base64, hashlib, json
from pathlib import Path
from cryptography.fernet import Fernet

def _fernet():
    pw = os.environ["AGENT_SECRET"]   # random 48+ char string per deploy
    key = base64.urlsafe_b64encode(hashlib.sha256(pw.encode()).digest())
    return Fernet(key)

def _blob_path(uid): return user_dir(uid) / "secrets.enc"

def _load(uid):
    p = _blob_path(uid)
    if not p.exists():
        return {}
    return json.loads(_fernet().decrypt(p.read_bytes()).decode())

def _save(uid, data):
    blob = _fernet().encrypt(json.dumps(data).encode())
    p = _blob_path(uid)
    p.write_bytes(blob)
    try: p.chmod(0o600)
    except OSError: pass

def secret_put(uid, key, value): d = _load(uid); d[key] = value; _save(uid, d)
def secret_get(uid, key):        return _load(uid).get(key)
def secret_has(uid, key):        return key in _load(uid)
```

`AGENT_SECRET` генерится один раз при deploy и кладётся в docker-compose env (либо в `secrets:` mount). Потерял — все юзерские BYOK creds потеряны.

### Sidechannel FSM (перехват ввода до LLM)

```python
def dispatch(msg):
    text = msg["text"].strip()
    profile = state.load_profile(uid)

    # Sidechannel приоритет — следующее сообщение НЕ идёт в LLM
    dlg = profile.get("dialog")
    if dlg and dlg["flow"].startswith("byok_") and not text.startswith("/cancel"):
        handle_byok_input(uid, text, dlg)  # сохраняет в Fernet, отвечает «✅»
        return

    # Команды-инициаторы тоже sidechannel
    if text.startswith("/byok"):
        parts = text.split()
        start_byok_wizard(uid, parts[1:])  # ставит profile["dialog"] = {"flow": "byok_bot"}
        return
    if text.startswith("/byok_status"):
        show_byok_status(uid)
        return

    # Всё остальное — в LLM-агент
    reply = agent.respond(uid, chat_id, text)
    api.send_message(chat_id, reply)
```

Wizard:

```python
def start_byok_wizard(uid, args):
    sub = args[0] if args else None
    if sub == "bot":
        dialog.start(uid, "byok_bot")
        api.send_message(chat_id,
            "Пришли Bot API токен одной строкой (NNNN:Axxx...).")
    elif sub == "target":
        dialog.start(uid, "byok_target")
        api.send_message(chat_id, "Пришли @username канала или -100... id.")
    elif sub == "sc":
        dialog.start(uid, "byok_sc")
        api.send_message(chat_id, "Пришли ScrapeCreators API key.")
    elif sub and sub.startswith("llm"):
        provider = args[1] if len(args) > 1 else None
        dialog.start(uid, "byok_llm", ctx={"provider": provider})
        api.send_message(chat_id, f"Пришли API key для {provider}.")
    else:
        show_byok_menu()

def handle_byok_input(uid, text, dlg):
    flow = dlg["flow"]
    if flow == "byok_bot":
        # Валидация через getMe пробу
        try:
            r = telegram_get_me(text)
            if not r["ok"]: raise RuntimeError(r["description"])
        except Exception as e:
            api.send_message(chat_id, f"❌ токен невалиден: {e}")
            dialog.clear(uid)
            return
        secret_put(uid, "user_bot_token", text)
        dialog.clear(uid)
        api.send_message(chat_id, f"✅ сохранено. Твой бот: @{r['result']['username']}")
    elif flow == "byok_sc":
        if len(text) < 10:
            api.send_message(chat_id, "❌ выглядит слишком коротко")
            return
        secret_put(uid, "sc_api_key", text)
        dialog.clear(uid)
        api.send_message(chat_id, "✅ ScrapeCreators key сохранён")
    # ... etc
```

Ответ юзеру — `✅ сохранён` **без эха значения**. Никогда `f"saved: {value}"`.

## 4. LLM agent loop (multi-provider)

См. `multi-model-gateway` skill, разделы 1–6. Ключевое для multi-tenant:

- Provider routing by model name prefix
- GPT-5.x `max_completion_tokens` (не `max_tokens`)
- Fallback chain с last_error reporting
- **Orphan-tool-message filter** перед каждым LLM-вызовом (критично)
- Tool-call trace persistence в history.jsonl

Без orphan-filter'а при кросс-провайдерном fallback все провайдеры отдают HTTP 400 на одну и ту же испорченную историю.

## 5. Staged content pipeline pattern

Когда генерация дорогая (Veo credits, ElevenLabs minutes) или результат критичен (cinematic trailer), pipeline разбивается на этапы с **per-stage approval**.

См. `agent-tool-design` skill §11.3–11.5. Применять для:

- **Видео-генерация**: voiceover script → storyboard → reference images → final render
- **Длинные посты**: structure outline → section drafts → review → final assembly
- **Email-кампании**: brief → subject lines → body draft → CTA → send

Stage artefacts в `<task>/<ts>-stages/{stage}.json`. Final stage **проверяет наличие всех артефактов** до запуска расхода API.

## 6. Cred lazy loader

Единая точка чтения секретов **deployment-level** (не юзерских BYOK — для них Fernet, см. §3). Из env → master creds file → docker secrets:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def _file_creds():
    out = {}
    home = Path.home() / ".claude" / "credentials.env"   # свой env-файл
    if home.exists():
        for line in home.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def cred_get(name, default=None):
    if name in os.environ and os.environ[name]:
        return os.environ[name]
    fc = _file_creds()
    if name in fc and fc[name]:
        return fc[name]
    ds = Path(f"/run/secrets/{name}")
    if ds.exists():
        return ds.read_text(encoding="utf-8").strip()
    return default
```

## 7. Per-user rate limiting на shared API quota

ScrapeCreators / OpenAI / Veo — общий ключ на всех юзеров. Защита от того что один юзер сожжёт квоту:

```python
def check_rate_limit(uid, action, budget_per_day=200):
    today = date.today().isoformat()
    counter_path = user_dir(uid) / f"limits-{today}.json"
    counters = json.loads(counter_path.read_text()) if counter_path.exists() else {}
    counters[action] = counters.get(action, 0) + 1
    counter_path.write_text(json.dumps(counters))
    if counters[action] > budget_per_day:
        raise RuntimeError(
            f"daily limit hit ({action}: {counters[action]}/{budget_per_day}). "
            f"Reset at midnight UTC or use /byok to bring your own key."
        )
```

Юзер с `/byok sc` — лимит снимается (использует свой ключ).

## 8. Cron / scheduler container — отдельно от bot

Bot — long-poll, scheduler — cron-like:

```yaml
# docker-compose.yml
services:
  bot:
    image: myagent:latest
    command: ["python", "/app/bot.py"]
    volumes:
      - data:/data

  scheduler:
    image: myagent:latest      # same image, different command
    command: ["python", "/app/scheduler.py"]
    volumes:
      - data:/data
```

`scheduler.py` тикает каждые N минут:

```python
def run():
    while True:
        for uid in list_active_users():
            for slug in list_active_topics(uid):
                if due_for_monitoring(uid, slug):
                    run_monitor(uid, slug)
                for slot in due_slots(uid, slug):
                    process_slot(uid, slug, slot)   # generate + publish
        time.sleep(TICK_SEC)
```

State (last-run timestamp, slot statuses) — в тех же per-user JSON файлах. Никакого Redis / Celery.

## 9. Whitelist админских команд

Часть команд только для админа (импорт юзеров, force-monitor всех, dump статистики). Discriminator:

```python
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x}

def dispatch(msg):
    uid = msg["from"]["id"]
    text = msg["text"]
    if text.startswith("/admin_") and uid not in ADMIN_IDS:
        return  # silent ignore, не выдавать что команда существует
    # ...
```

## 10. Gotchas из реального deploy'a

| Trap | Симптом | Fix |
|------|---------|-----|
| `docker compose restart` не перечитывает `env_file` | Bot держит старый TG token после ротации | `docker compose up -d --force-recreate <svc>` |
| Один service builds image, others share by `image:` | Перебилд `service-2` через compose ничего не делает | Build только через тот service у которого есть `build:` блок |
| `MSYS_NO_PATHCONV` на Git Bash Windows | `/start` → `C:/Program Files/Git/start` | `MSYS_NO_PATHCONV=1 python tg_client.py send "/start"` |
| Stage artefacts persist между runs | Юзер просит «новый драфт», получает старый | Reset через `rm -rf <ts>-stages/` или sentinel param на регенерацию |
| Telegram Bot API token в `cat config.json` | Token светится в логах и оперативной видимости | Маскировать `sed -E 's/("?(?:apiKey|botToken|token)"?\s*:?\s*"?)[^"\s]+/\1***/g'` |
| Fernet `AGENT_SECRET` потерян | Все юзерские BYOK creds потеряны | Хранить в password manager + docker secrets. Резервная копия отдельно |
