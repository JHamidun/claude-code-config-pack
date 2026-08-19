---
name: suno
description: "Генерация музыки в Suno без браузера (suno_client.py): треки, mp3, кредиты. Триггеры: «трек в Suno», «фоновая музыка». НЕ BGM ≤30с → elevenlabs."
---

# Suno — headless internal API

Полноценная работа с Suno **без браузера**: токен минтится из durable `__client` cookie, дальше — generate / list / status / download через `studio-api-prod.suno.com`. Аккаунт **companyaudio (Pro, 2500 кредитов/мес)**.

Аналог `runway_client.py`. Клиент: `scripts/suno_client.py`.

## Когда использовать

- «сделай музыку / трек / саундтрек / инструментал / песню в Suno»
- «фоновая музыка для ролика», «эпик-оркестр», «lo-fi бит»
- «скачай мой трек из suno», «покажи мои треки», «сколько кредитов в suno»

Когда НЕ использовать:
- Быстрый BGM ≤30с без аккаунта → `elevenlabs` (Music) или `local-gateway`
- Коммерчески-чистый score → Lyria 2 (`video-generation/references/audio.md`)
- Озвучка голосом → `elevenlabs`

## Авторизация (Clerk)

Suno использует **Clerk**. Схема:
1. Durable **`__client` cookie** (refresh-токен, `token_type: refresh`, живёт ~1 год) — единственный долгоживущий секрет.
2. Минт короткого **Bearer** (`aud: suno-api`, TTL ~1 час):
   `POST https://auth.suno.com/v1/client/sessions/{SESSION_ID}/tokens?__clerk_api_version=2025-11-10&_clerk_js_version=5.117.0`
   с заголовком `cookie: __client=<...>` → ответ `{"jwt": "<bearer>"}`.
3. Все запросы к API: `Authorization: Bearer <jwt>` + `device-id` + `browser-token`.

Клиент кеширует Bearer и переминчивает за 2 мин до истечения. **Без браузера.**

### Креды (в `~/.claude/.credentials.master.env`)

```
SUNO_CLIENT_COOKIE   # __client (durable refresh JWT, ~1 год). ГЛАВНЫЙ секрет.
SUNO_SESSION_ID      # из .credentials.master.env (SUNO_SESSION_ID)
SUNO_DEVICE_ID       # device-id header (uuid)
SUNO_USER_AGENT      # UA строка
SUNO_BEARER          # (опц.) вставить свежий Bearer для разовой работы без __client (~1ч)
```

Уже сохранены (2026-06-05, аккаунт companyaudio).

### Если `__client` протух (через ~год или при logout) — пере-захват из браузера

Через Playwright MCP (как делалось для perplexity/notebooklm): залогиниться на suno.com, затем
`browser_run_code_unsafe`:
```js
async (page) => {
  const cookies = await page.context().cookies();
  const c = cookies.find(x => x.name === '__client' && x.domain === 'auth.suno.com');
  return JSON.stringify({ client: c.value, sid: (await page.evaluate(()=>window.Clerk.session.id)) });
}
```
Записать `client` → `SUNO_CLIENT_COOKIE`, `sid` → `SUNO_SESSION_ID`. (httpOnly cookie виден только через `context.cookies()`, НЕ через `document.cookie`.)

## API endpoints (база `https://studio-api-prod.suno.com`)

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/api/generate/v2/` | **Генерация (headless, БЕЗ капчи)**. Тело: `{generation_type:"TEXT", mv, prompt:"", gpt_description_prompt, make_instrumental, metadata{create_mode:"simple", lyrics_model:"default"}, title?}` → `{id, clips:[{id,status:"submitted"...}]}` |
| POST | `/api/generate/v2-web/` | Веб-версия — **капча-гейт** (`token_provider:1`, `browser-token`, `/api/c/check`). НЕ для headless. |
| POST | `/api/feed/v3` | Листинг/опрос клипов. Тело: `{cursor, limit, filters:{disliked:"False",trashed:"False",fromStudioProject:{presence:"False"},stem:{presence:"False"},workspace:{presence:"True",workspaceId:"default"}}}` → клипы с `id,status,title,audio_url`. Статусы: `submitted→queued→streaming→complete` (или `error`). |
| GET | `/api/billing/info/` | Кредиты/подписка: `monthly_usage`, `monthly_limit`, `credits` (доп.паки), `renews_on`. |
| GET | `/api/project/me?page=1&...` | Воркспейсы. |
| GET | `/api/video/generate/{clip_id}/status/` | Статус видео-генерации клипа (если делать видео). |
| POST | `auth.suno.com/v1/client/sessions/{sid}/tokens` | Минт Bearer (см. авторизацию). |

**Скачивание mp3:** `https://cdn1.suno.ai/{clip_id}.mp3` (публичный CDN, 200 когда `complete`, 403 пока рендерится). audio_url из feed = тот же CDN.

**Модели (`mv`):** `chirp-fenix` = v5.5 (текущая, по умолчанию). Старые: `chirp-v4`, `chirp-v3-5`.

## CLI

```bash
cd ~/.claude/skills/suno/scripts
python suno_client.py billing                      # кредиты/подписка
python suno_client.py list --limit 10              # мои клипы (id|status|title|url)
python suno_client.py status <clip_id>             # статус видео клипа
python suno_client.py download <clip_id> --out track.mp3
python suno_client.py generate "Epic orchestral, instrumental" --instrumental
python suno_client.py make "Epic orchestral score, instrumental" --instrumental --out-dir .  # generate→poll→download (one-shot)
python suno_client.py token                        # debug: напечатать Bearer
```

## Python

```python
import sys; sys.path.insert(0, os.path.expanduser("~/.claude/skills/suno/scripts"))
from suno_client import SunoClient
c = SunoClient()
c.billing()                                  # dict
batch = c.generate("Lo-fi hip-hop, rainy night", instrumental=True)  # -> {id, clips:[{id,...}]}
ids = [x["id"] for x in batch["clips"]]
done = c.wait_clips(ids, timeout=300)         # poll feed until complete
for cid in ids: c.download(cid, f"{cid}.mp3")
# one-shot:
paths = c.make_track("Cinematic trailer, instrumental", instrumental=True, out_dir="out", timeout=300)
```

## Промпт-инжиниринг (Simple mode)

`gpt_description_prompt` = одно описание (стиль + настроение + структура). Suno сам решает аранжировку.
- Инструментал: `make_instrumental=True` (никакого вокала).
- Хороший эпик-промпт: указывай дугу («intimate cello → storm with war drums → triumphant brass + choir → tender resolution»), BPM, инструменты, референс-жанр (БЕЗ имён артистов — Suno фильтрует меньше, но лучше дескрипторы).
- Полноценная песня со СВОИМИ словами (custom mode): тело `/api/generate/v2/` = `{generation_type:"TEXT", mv, prompt:<LYRICS с тегами [Verse]/[Chorus]>, tags:<STYLE>, title, make_instrumental:false, metadata:{create_mode:"custom", lyrics_model:"default"}}`. **Реверс подтверждён (2026-06-08), но headless этот payload тоже ловит `422 token_validation_failed`** (капча) — поэтому custom-песни делаем через Playwright UI, см. gotcha #3 (Custom-recipe).
- Suno выдаёт **2 дубля** на запрос, каждый ~2-4 мин. Под короткий ролик — нарезать нужный 60с фрагмент (ставить кульминацию по макс-RMS, см. `_client_birthday/scripts/analyze_cut.py`).

## Gotchas

1. **Bearer TTL ~1 час** — клиент переминчивает сам из `__client`. Не кешировать Bearer надолго вручную.
2. **`__client` httpOnly** — достаётся только через `context.cookies()` (Playwright `browser_run_code_unsafe`), НЕ через `document.cookie`.
3. **Генерация теперь КАПЧА-ГЕЙТ даже на `/api/generate/v2/`** (2026-06-07: `422 token_validation_failed` / "We couldn't verify your request"). Headless generate БОЛЬШЕ НЕ РАБОТАЕТ. Чтения (billing/list/feed) и **скачивание `cdn1.suno.ai/{id}.mp3` работают headless**. Для генерации — **Playwright-браузер** (логин companyaudio через Clerk-сессию персистит): `browser_navigate suno.com/create` → ввести Song Description → toggle Instrumental → Create → дождаться `streaming→complete` через headless `list_clips` → скачать по cdn. Рецепт проверен (трек «Signal at Dawn», проект `_viral_ai`).

   **Custom-mode (свои слова) через Playwright — точные селекторы (проверено 2026-06-08, проект `_client2_birthday`):**
   1. `browser_navigate https://suno.com/create` (по умолчанию режим Simple).
   2. Клик `button "Add your own lyrics"` → форма переключается в custom (radio "Lyrics mode" = **Write**).
   3. Заполнить 3 поля (`browser_fill_form`):
      - **Lyrics** — `textarea[data-testid="lyrics-textarea"]` (макс 5000; вписать текст с тегами `[Verse]/[Chorus]/[Outro]`).
      - **Styles** — textbox с плейсхолдером-рекомендациями стилей (макс 1000; жанр/вокал/BPM, БЕЗ имён артистов).
      - **Title** — `textbox "Song Title (Optional)"`.
   4. Клик `button[aria-label="Create song"]` (становится `enabled` после заполнения).
   5. 2 дубля появляются в воркспейсе (`streaming`); дальше **headless**: `list_clips` → ждать `complete` → `download` по `cdn1.suno.ai/{id}.mp3`.
   Капчу решает сам браузер (invisible) — тосты/ошибок нет, генерация просто стартует.
4. **CDN 403 пока рендерится** — качать после `status==complete` (poll `feed/v3`).
5. **Windows stdout cp1251** ломает кириллицу в print → клиент делает `sys.stdout.reconfigure(utf-8)`; в Bash ставь `PYTHONIOENCODING=utf-8`.
6. **Кредиты:** Pro = 2500/мес (≈500 песен, 5 кредитов/песня = 2 дубля). `billing` показывает `monthly_usage/monthly_limit`. Доп.паки (`credits`) отдельно.
7. **device-id / browser-token** требуются как заголовки (browser-token = `{"token": base64({"timestamp": ms})}` — генерится клиентом).
8. **suno.com vs suno.ai** — API на `studio-api-prod.suno.com`; CDN на `cdn1.suno.ai`; auth на `auth.suno.com`.
9. **Playwright «Browser is already in use»** (профиль `ms-playwright/mcp-chrome-*` залочен зависшим инстансом) → перед стартом убить процессы: PowerShell `Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | ? {$_.CommandLine -match 'mcp-chrome'} | % {Stop-Process -Id $_.ProcessId -Force}`, затем `browser_navigate` заново.
10. **Custom-mode payload (для будущего fix headless):** `metadata.create_mode:"custom"` + `prompt`=lyrics + `tags`=style (НЕ `gpt_description_prompt`). Сейчас 422 (капча), но это верная схема — если появится способ отдавать валидный `browser-token`/captcha-solve, headless custom заработает этим телом.

## Файлы

- `scripts/suno_client.py` — клиент (token mint, billing, list, status, download, generate, wait_clips, make_track) + CLI.

Реверс-инжиниринг проведён 2026-06-05 (сессия видео-поздравления [Client]). Проверено headless: token/billing/list/download/generate/make — всё работает без браузера.
