---
name: heygen
description: "HeyGen API v3: AI-аватар видео, digital-twin, lip-sync перевод, Voice Clone. Триггеры: «аватар видео», «видео со своим аватаром», «говорящая голова»."
---

# HeyGen API Skill

## Overview

HeyGen = AI avatar video platform. **v3 — основной API** (`developers.heygen.com`,
`api.heygen.com`). v1/v2 (`docs.heygen.com`) живут **до 31 октября 2026**, новых
фич не получают. Studio API + Template API остались только на v1/v2.

**Движки рендера:**
- **Avatar V** — самое естественное движение и lip-sync. Только v3, включается явно: `engine: {"type":"avatar_v"}`. **С 2026-05-12 стоит столько же, сколько IV.**
- **Avatar IV** (дефолт v3) — `motion_prompt` + `expressiveness` (только photo-аватары).
- **Avatar III** — legacy v1/v2, для новых интеграций не брать.

**Два prompt-продукта (2026):**
- **Cinematic Avatar** (`type:"cinematic_avatar"` на `POST /v3/videos`) — Seedance: промпт + 1–3 look'а + референсы, без скрипта и голоса. $7 за ролик, 4–15 с.
- **HyperFrames** (`POST /v3/hyperframes/renders`) — рендер HTML-композиции (.zip, Remotion-style) в видео с подстановкой переменных.

**Base URL:** `https://api.heygen.com` (без суффикса версии; версия в пути)

## Auth

```
Header: x-api-key: <your-key>          # apiKey auth (имя заголовка регистронезависимо)
   OR   Authorization: Bearer <token>  # OAuth2 bearer
```

API-ключ списывает с **кошелька API**. OAuth bearer — с тарифа веб-плана. Один и
тот же ключ работает на v1/v2/v3. Выпуск: https://app.heygen.com/settings (вкладка API).

```bash
curl -s "https://api.heygen.com/v3/users/me" -H "x-api-key: $HEYGEN_API_KEY"
# {"data":{"billing_type":"wallet","email":"...","wallet":{"currency":"usd","remaining_balance":0.0,...}}}
```

### Ключи

В `.credentials.master.env`:
- `HEYGEN_API_KEY` — алиас DEV-ключа
- `HEYGEN_API_KEY_DEV` = `sk_V2_...` — разработка (полный API, прямое создание видео)
- `HEYGEN_API_KEY_AGENT` = `sk_V2_...` — агентные сценарии (Video Agent)

Оба ключа дают одинаковый ответ на `/v3/users/me` и `/v3/avatars`: одна учётная
запись, общий кошелёк, разницы в правах нет. Разделение смысловое.

> ⚠️ Кошелёк API бывает пустым. Платные задачи через публичный API идут только при
> положительном балансе — проверяй ПЕРЕД генерацией: `GET /v3/users/me` →
> `wallet.remaining_balance`. Иначе получишь отказ уже после сборки сценария.

## Единственный поддерживаемый путь — публичный API

| Путь | Base | Auth | Учёт расхода |
|---|---|---|---|
| **Публичный API v3** (этот документ) | `api.heygen.com` | `x-api-key` | кошелёк API |

Что доступно прямо сейчас, видно из `GET /v3/users/me`: `wallet.remaining_balance`.

> **Чего в паке нет и почему.** У веб-приложения HeyGen есть второй, недокументированный
> контур (`api2.heygen.com`, авторизация по кукам браузерной сессии). Через него доступны
> функции, которых нет в публичном v3 — AI Studio с multi-scene, Face Swap, PPT→Video,
> Batch Mode. Описание этого контура и клиент к нему **намеренно не входят в пак**:
> обращение к внутреннему API скриптом — за пределами условий использования HeyGen,
> и риск блокировки аккаунта несёт тот, кто это запускает, а не тот, кто раздал конфиг.
> Нужны эти функции — делай их руками в интерфейсе <https://app.heygen.com> либо пиши
> в поддержку про доступ к соответствующему плану.
>
> На перечень v3 это не влияет: рендер аватара, cinematic, оживление картинки,
> HyperFrames, lip-sync, перевод, клон голоса и вебхуки — всё ниже и всё документировано.

## Минимальный вызов v3

```jsonc
POST /v3/videos
{ "type": "avatar",              // дискриминатор: avatar | image | cinematic_avatar
  "avatar_id": "<look_id>",      // look_id, НЕ group_id
  "script": "...",               // ИЛИ audio_url ИЛИ audio_asset_id (взаимоисключающие)
  "voice_id": "<voice_id>",      // обязателен со script, если у аватара нет голоса по умолчанию
  "aspect_ratio": "9:16",        // дефолт 16:9 — для шортсов задавать явно
  "resolution": "1080p",
  "engine": {"type": "avatar_v"} // опционально; объект, не строка
}
// → {"data":{"video_id":"...","status":"waiting"}}
```

Статусы: `waiting → pending → processing → completed | failed`. У `completed`
появляются `video_url`, `thumbnail_url`, `duration`, `subtitle_url`. **Ссылки
протухают — скачивай сразу или опрашивай заново.**

Полные тела всех эндпоинтов (три варианта `/v3/videos`, hyperframes, avatars,
voices, lipsync, translation+proofread, video-agents, assets, webhooks, коды
ошибок, Idempotency-Key, MCP, CLI) → **`references/v3-api.md`**. Открывай, когда
собираешь запрос сложнее минимального или ищешь путь, которого нет в таблице «Use
cases» ниже.

Цены и лимиты (сколько стоит партия шортсов, потолки длины скрипта, размера
файла, числа параллельных задач) → **`references/pricing-limits.md`**.

Готовый Python-клиент к публичному API + рецепты (short, cinematic, ElevenLabs →
lip-sync, вебинар на 5 языков, HyperFrames) → **`references/python-client.md`**.

## Gotchas (проверено 2026-06-05)

- **Заголовок `x-api-key`** (регистр не важен). НЕ Bearer, если это не OAuth.
- **Баланс кошелька API** — платные задачи идут только при положительном балансе; проверка `GET /v3/users/me`.
- **`POST /v3/videos` — union из трёх вариантов** по полю `type`: `avatar` / `image` / `cinematic_avatar`.
- **У cinematic `avatar_id` — МАССИВ** из 1–3 look ID; скрипта и голоса нет; фикс $7.
- **Перевод: `output_languages` — НАЗВАНИЯ языков, не коды** (`'Spanish (Spain)'`), и поле называется `video`, а не `video_url`. Список названий: `GET /v3/video-translations/languages`.
- **Lipsync принимает `video`+`audio` как asset-union**, а не `video_url`/`audio_url` верхним уровнем.
- **TTS-поле — `text`** (не `input`). **Клон голоса — `audio`+`voice_name`** (не `audio_url`+`name`). **Дизайн голоса — `POST /v3/voices`** с `prompt`.
- **Avatar V включается объектом** `engine: {"type":"avatar_v"}`. Вместе с ним `motion_prompt`/`expressiveness` отклоняются. Право на Avatar V — у **look'а**, не у группы: `GET /v3/avatars/looks/{look_id}` → `supported_api_engines`. Тип `image` с Avatar V не работает.
- **Avatar V = цена Avatar IV** (с 2026-05-12).
- **`aspect_ratio` по умолчанию 16:9** — для шортсов всегда передавай `"9:16"`. Cinematic/HyperFrames поддерживают только 16:9/9:16/1:1.
- **`voice_settings.speed` — 0.5–1.5**, а у TTS-эндпоинта speed 0.5–2.0. Разные диапазоны у одноимённого поля.
- **`signing_secret` вебхука показывают один раз**; менять url/события — `PATCH`, новый секрет — `rotate-secret`.
- **`fps_mode` — строгий enum:** `vfr|cfr|passthrough`.
- **Большие файлы — через `direct-uploads`** (init → PUT → complete), а не 32-МБ multipart.
- **Сообщение Video Agent'у шлётся на `POST /v3/video-agents/{session_id}`** (в саму сессию), не на `/messages`.
- **Ссылки на результат протухают** — скачивай или опрашивай заново.
- **Studio API (multi-scene) и Template API остались на v2.**
- **`callback_id`** возвращается дословно в вебхуке — `event_data.callback_id`.

## Свой аватар и свой голос — откуда берутся id

**Пак не поставляется ни с каким аватаром и ни с каким голосом.** Аватар — это
биометрия конкретного человека: чужой id в чужом аккаунте не отработает, а в своём
сделает ролик с чужим лицом. Оба идентификатора держатся в окружении.

```bash
# ~/.claude/.credentials.master.env
HEYGEN_AVATAR_ID=<YOUR_AVATAR_ID>        # горизонтальный (16:9) look_id
HEYGEN_AVATAR_ID_9X16=<YOUR_AVATAR_ID>   # вертикальный (9:16), если аватар снят отдельно
HEYGEN_VOICE_ID=<YOUR_VOICE_ID>
```

| Что | Кабинет | API |
|---|---|---|
| аватар (look_id) | https://app.heygen.com/avatars → аватар → ID | `GET /v3/avatars` → группы; `GET /v3/avatars/looks?group_id=<group>` → look'и |
| голос | https://app.heygen.com/voices | `GET /v3/voices` |

Своего аватара ещё нет — заводится там же (Instant Avatar по видео 2 мин, либо
photo-аватар по одному фото); голос — Voice Clone в том же кабинете или готовый из
библиотеки. Свой аватар требует **согласия человека в кадре**:
`POST /v3/avatars/{group_id}/consent` возвращает ссылку, которую этот человек
открывает сам в браузере — обойти нельзя и не нужно. Проверь на выбранном
**look'е** (не на группе) поле `supported_api_engines`: `avatar_v` есть не у всех.

> Вертикальный и горизонтальный ролики нередко снимаются **разными** аватарами — не
> одним и тем же id с другим `aspect_ratio`. Отсюда две переменные, а не одна.

### Мигрируешь конфиг с v2

```yaml
# config/settings.yaml
avatar_id: ${HEYGEN_AVATAR_ID}      # должен резолвиться в v3 look_id
voice_id: ${HEYGEN_VOICE_ID}
dimension: {width: 720, height: 1280}          # → aspect_ratio "9:16" в v3
```
**Что сделать:** убедиться, что `avatar_id` резолвится в v3 `look_id` через
`GET /v3/avatars/looks?group_id=<group>`, и проверить `supported_api_engines` на `avatar_v`.

## LiveAvatar — Realtime Video Avatar (отдельный сервис)

**Полный справочник: `references/liveavatar.md`** (исходники SDK, OpenAPI,
протокол WebSocket, архитектура интеграции с Telegram). Открывай, когда делаешь
realtime-разговор с аватаром, а не рендер ролика.

**Base URL:** `https://api.liveavatar.com` (НЕ `api.heygen.com`)
**Auth:** заголовок `X-API-KEY`, ключ в `.credentials.master.env` → `HEYGEN_LIVE_AVATAR_API_KEY`
**SDK:** `@heygen/liveavatar-web-sdk` (npm), поверх **LiveKit** (WebRTC-комнаты)
**OpenAPI:** `https://docs.liveavatar.com/openapi.json` (24 эндпоинта)

| Mode | Cost | HeyGen делает | Ты даёшь |
|------|------|---------------|----------|
| **FULL** | 2 credits/min | STT + LLM + TTS + аватар | настройку через API |
| **LITE** | 1 credit/min | только рендер аватара | свой STT + LLM + TTS |

**LITE — ключевой режим для своих интеграций** (звонки в Telegram, свой
голосовой агент): получаешь LiveKit-комнату с video+audio дорожками аватара и
WebSocket, куда шлёшь PCM 24 кГц → аватар синхронизирует губы. Команды:
`agent.speak` (base64 PCM чанками), `agent.interrupt`, `agent.start/stop_listening`.

```python
import os, requests
r = requests.get('https://api.liveavatar.com/v1/users/credits',
                 headers={'X-API-KEY': os.environ['HEYGEN_LIVE_AVATAR_API_KEY']})
print(r.json())
```

## References

- **OpenAPI (источник истины):** https://developers.heygen.com/openapi/external-api.json
  (54 paths, 145 schemas). Схемы меняются — сверяйся с сетевой версией, а не с памятью.
- Changelog: https://developers.heygen.com/changelog · llms.txt: https://developers.heygen.com/llms.txt
- Креды: `~/.claude/.credentials.master.env` → `HEYGEN_API_KEY` (плюс `_DEV` / `_AGENT`,
  если держишь отдельные ключи под разные окружения)

Локальный кэш спеки (удобно, когда гоняешь много вызовов подряд, — но не обязателен):

```bash
mkdir -p ./work/heygen
curl -sL https://developers.heygen.com/openapi/external-api.json -o ./work/heygen/openapi.json
```

## Use cases → endpoints

| Goal | Endpoint(s) |
|---|---|
| Максимальное качество говорящей головы | проверить eligibility look'а → `POST /v3/videos` + `engine:{"type":"avatar_v"}` |
| Обычное видео с аватаром | `POST /v3/videos` type=avatar (без `engine`) |
| Cinematic по промпту (Seedance) | `POST /v3/videos` type=cinematic_avatar |
| Оживить произвольную картинку | `POST /v3/videos` type=image |
| Моушн-графика из HTML | `POST /v3/hyperframes/renders` |
| Подложить аудио ElevenLabs | upload asset → `POST /v3/videos` с `audio_asset_id` |
| Переозвучить готовое видео | `POST /v3/lipsyncs` (precision) |
| Вебинар на нескольких языках | `POST /v3/video-translations` (названия языков) |
| Поправить субтитры до рендера | proofreads → PUT srt → generate |
| Видео по промпту целиком | `POST /v3/video-agents` (+ `brand_kit_id` для бренда) |
| Голос по описанию / клон / TTS | `POST /v3/voices` · `/v3/voices/clone` · `/v3/voices/speech` |
| Фоновая музыка | `GET /v3/audio/sounds?query=...` (`query` обязателен) |
| Свой перевод терминов | `brand_glossary_id` (`GET /v3/brand-glossaries`) |
| Большой файл | `/v3/assets/direct-uploads` → complete |
| Прозрачный фон | `output_format=webm` + `remove_background=true` |
| Безопасный повтор POST | заголовок `Idempotency-Key` |
| Отслеживание асинхронно | `callback_url` + `callback_id` ИЛИ управляемый вебхук |
| Multi-scene / шаблоны | только v2 Studio API / Template API |
