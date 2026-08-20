---
name: heygen
description: "HeyGen API v3: AI-аватар видео, digital-twin, lip-sync перевод, Voice Clone. Триггеры: «аватар видео», «видео со своим аватаром», «говорящая голова»."
---

# HeyGen API Skill

## Overview

HeyGen = AI avatar video platform. **v3 is the primary API** (`developers.heygen.com`, `api.heygen.com`). v1/v2 endpoints (`docs.heygen.com`) stay operational **until October 31, 2026** but get no new features. Studio API + Template API remain v1/v2-only (no v3 equivalent yet).

**Rendering engines:**
- **Avatar V** — cross-reference-driven animation, most natural motion + lip-sync. v3 only, opt-in `engine: {"type":"avatar_v"}`. **Same price as Avatar IV since 2026-05-12.**
- **Avatar IV** (default on v3) — natural motion, `motion_prompt` + `expressiveness` (photo avatars only).
- **Avatar III** — legacy v1/v2 only, no new integrations.

**Two prompt-driven video products (new, 2026):**
- **Cinematic Avatar** (`type:"cinematic_avatar"` on `POST /v3/videos`) — Seedance pipeline, prompt + 1–3 avatar looks + reference assets, no script/voice. Flat $7/video, 4–15 s.
- **HyperFrames** (`POST /v3/hyperframes/renders`) — render an HTML composition (.zip project, Remotion-style) into video with data variables.

**Base URL:** `https://api.heygen.com` (no version suffix; paths carry `/v3`, `/v2`, `/v1`)
**Server (OpenAPI):** `https://api.heygen.com` (Production)

**Docs:**
- v3 (current): https://developers.heygen.com — локальная копия документации `${HOME}/_heygen_v3_docs.md`
- **OpenAPI spec (authoritative): `${HOME}/_heygen_openapi.json`** (54 paths, 145 schemas, 3.1.0) ← основной источник для этого навыка
- llms.txt: https://developers.heygen.com/llms.txt
- Changelog: https://developers.heygen.com/changelog
- v1/v2 legacy: локальная копия `${HOME}/_heygen_docs.md`

## Auth

```
Header: x-api-key: <your-key>          # apiKey auth (case-insensitive header name)
   OR   Authorization: Bearer <token>  # OAuth2 bearer
```

API key → billed against **API wallet**. OAuth bearer → billed against **web plan**. Same key works v1/v2/v3. Get a key at https://app.heygen.com/settings (API tab).

Test:
```bash
curl -s "https://api.heygen.com/v3/users/me" -H "x-api-key: $HEYGEN_API_KEY"
# {"data":{"billing_type":"wallet","email":"...","wallet":{"currency":"usd","remaining_balance":0.0,...}}}
```

### Ключи

В `.credentials.master.env`:
- `HEYGEN_API_KEY` — алиас DEV-ключа
- `HEYGEN_API_KEY_DEV` = `sk_V2_...` — ключ для разработки (полный API, прямое создание видео)
- `HEYGEN_API_KEY_AGENT` = `sk_V2_...` — ключ для агентных сценариев (Video Agent)

Оба ключа дают одинаковый ответ на `/v3/users/me` и `/v3/avatars`: одна учётная запись, общий кошелёк, разницы в правах нет. Разделение смысловое — DEV для прямого создания, AGENT для Video Agent.

> ⚠️ Кошелёк API бывает пустым. Платные задачи через публичный API идут только при положительном балансе — проверяй перед генерацией: `GET /v3/users/me` → `wallet.remaining_balance`.

## Два пути обращения к сервису

| Путь | Base | Auth | Учёт расхода | Когда |
|---|---|---|---|---|
| **Публичный API** (этот документ) | `api.heygen.com` | `x-api-key` | кошелёк API | документированный v3; нужен положительный баланс кошелька |
| **Сессия своей учётной записи** | `api2.heygen.com` | `x-guest-session-token` (cookie) | тариф учётной записи | работа в рамках уже подключённого плана |

Что доступно сейчас, видно из `GET /v3/users/me` (баланс кошелька API) и команды `quota` веб-клиента (тариф и лимиты учётной записи).

→ **Работа через сессию учётной записи и клиент без браузера: `references/web-session.md`** + `scripts/heygen_web_client.py`.
Креды в `.credentials.master.env`: `HEYGEN_WEB_TOKEN` / `HEYGEN_WEB_RAW_TOKEN` / `HEYGEN_WEB_SPACE_ID` (берутся из своей сессии).

```bash
cd ~/.claude/skills/heygen/scripts
python heygen_web_client.py whoami        # проверка сессии: email заполнен, а не гостевой вход
python heygen_web_client.py quota         # тариф, доступные функции, расход
python heygen_web_client.py avatars       # свои группы аватаров
# Генерация:
python heygen_web_client.py agent "Сделай 15-сек видео-интро про YourProduct"     # Video Agent
python heygen_web_client.py translate "https://my.mp4" "Russian (Russia),Spanish (Spain)" --precision
python heygen_web_client.py seedance "Man in neon city talks to camera" <look_id> --res 1080p --dur 10  # Cinematic
python heygen_web_client.py avatar-iv ./photo.jpg "Привет!" <voice_id>          # Photo-to-Video (Avatar IV)
python heygen_web_client.py image "product ad scene" --refs s3://...            # image / product placement
python heygen_web_client.py seedance-list   # poll your jobs; or: status <item_id>
python heygen_web_client.py call /v1/payment/subscription   # произвольный вызов
```

**Что проверено на практике:** авторизация, все чтения и основные сценарии генерации — запрос проходит, задача создаётся, готовый mp4 скачивается.

| Feature | Endpoint | CLI |
|---|---|---|
| AI Studio (talking-head, multi-scene) | `text_draft.create`→`text_draft.save`→`text_draft.generate` | `studio "<script>" <avatar_id> <voice_id>` |
| Video Agent (prompt→video) | `POST /v1/video_agent/sessions` + `/v2/video_agent/interactive_chat` | `agent "<prompt>"` |
| Translate | `POST /v3/video_translate.create` | `translate <url> "<lang names>"` |
| Cinematic (Seedance 2) | `POST /v1/seedance2/submit` | `seedance "<prompt>" <look_id>` |
| Photo-to-Video (Avatar IV) | `get_upload_photo_url`→PUT→`POST /v1/avatar/video_generate/submit` | `avatar-iv <photo> "<text>" <voice_id>` |
| Product Placement / Image | `POST /v3/image/generate` | `image "<prompt>"` |
| AI Video Generator / B-Roll (text→video, no avatar) | `POST /v1/file.ai_generate_element` (provider seedance_2) | `ai-video "<prompt>"` |
| Upscale to 4K | `file.upload`→`POST /v1/apps/upscale-video` | `upscale <video>` |
| Face Swap | `POST /v1/face_swap_v2.video.submit` | `face-swap <video_url> <face_url>` |
| Speech Cleanup (filler removal) | `POST /v1/apps/filler-removal/preview/create` | — (`speech_cleanup_preview`) |
| Auto Clips | `instant-highlights` (upload + format/caption) | `apps instant-highlights ...` |
| PPT/PDF → Video | `POST /v1/ent_ppt_pdf_conversion/convert` → AI Studio draft | `ppt <file>` |
| Batch Mode (scripts×avatars) | `POST /v1/avatar/batch_mode/submit` | `batch_mode(...)` method |
| File upload (any) | `file.url` → PUT(SSE) → `file.upload` (3-step) | auto in methods |
| Status / download | `GET /v1/project/items/status` · `/v1/apps/<slug>/{id}/status` · `.check?workflow_id=` | `status <id>` · `download <id> <out> --wait` |

⚠️ **Each app has its OWN API namespace** (frontend slug ≠ API route — Face Swap = `/v1/face_swap_v2.*`, Speech Cleanup = `filler-removal`, B-Roll = `/v1/file.ai_generate_element`, Batch = `/v1/avatar/batch_mode/submit`, PPT = `/v1/ent_ppt_pdf_conversion/convert`). Угадывать путь по названию раздела бесполезно — 404; сверяйся с таблицей выше. Upload is a 3-step `file.url`→PUT(`x-amz-server-side-encryption:AES256`)→`file.upload`, NOT multipart. Full payloads (AI Studio scene graph + every app body) in **`references/web-session.md`**. Only **Lipsync** (use public `/v3/lipsyncs`) and **LiveAvatar** (realtime WS) remain — niche.

## Complete v3 endpoint map (54 paths, OpenAPI-verified)

### Videos
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/videos` | Create video (discriminated union: `avatar`/`image`/`cinematic_avatar`) |
| GET | `/v3/videos` | List (filter `folder_id`, `title` min 1 char) |
| GET | `/v3/videos/{video_id}` | Status + URLs |
| DELETE | `/v3/videos/{video_id}` | Delete |

### Cinematic / HyperFrames (prompt-driven)
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/videos` (`type:"cinematic_avatar"`) | Seedance prompt+refs video |
| POST | `/v3/hyperframes/renders` | Render HTML composition .zip → video |
| GET | `/v3/hyperframes/renders` | List renders |
| GET | `/v3/hyperframes/renders/{render_id}` | Render status |
| DELETE | `/v3/hyperframes/renders/{render_id}` | Delete render |

### Avatars
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/avatars` | Create avatar (`digital_twin`/`photo`/`prompt`) |
| GET | `/v3/avatars` | List groups (characters) |
| GET | `/v3/avatars/{group_id}` | One group |
| DELETE | `/v3/avatars/{group_id}` | Delete group |
| POST | `/v3/avatars/{group_id}/consent` | Consent flow (returns URL → open in browser) |
| GET | `/v3/avatars/looks` | List looks (outfits/styles) |
| GET | `/v3/avatars/looks/{look_id}` | One look (`supported_api_engines`) |
| PATCH | `/v3/avatars/looks/{look_id}` | Rename (photo/digital twin only) |
| DELETE | `/v3/avatars/looks/{look_id}` | Delete look |

### Voices
| Method | Path | Purpose |
|---|---|---|
| GET | `/v3/voices` | List (filter `type`,`engine`,`language`,`gender`) |
| POST | `/v3/voices` | **Design voice** from NL prompt (returns ≤3 matches) |
| GET | `/v3/voices/{voice_id}` | Details + clone status |
| POST | `/v3/voices/clone` | Clone from reference audio |
| POST | `/v3/voices/speech` | TTS (Starfish engine voices only) |

### Lipsync
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/lipsyncs` | Replace audio + re-animate lips |
| GET | `/v3/lipsyncs` | List |
| GET | `/v3/lipsyncs/{lipsync_id}` | Status |
| PATCH | `/v3/lipsyncs/{lipsync_id}` | Rename |
| DELETE | `/v3/lipsyncs/{lipsync_id}` | Delete |

### Video Translation
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/video-translations` | Translate (175+ langs, lip-sync) |
| GET | `/v3/video-translations` | List |
| GET | `/v3/video-translations/{video_translation_id}` | Status |
| PATCH | `/v3/video-translations/{video_translation_id}` | Rename |
| DELETE | `/v3/video-translations/{video_translation_id}` | Delete |
| GET | `/v3/video-translations/languages` | Supported target language names |
| POST | `/v3/video-translations/proofreads` | Start proofread (editable SRT) |
| GET | `/v3/video-translations/proofreads/{proofread_id}` | Proofread status |
| GET/PUT | `/v3/video-translations/proofreads/{proofread_id}/srt` | Download / upload edited SRT |
| POST | `/v3/video-translations/proofreads/{proofread_id}/generate` | Final render w/ approved SRT |

### Video Agent (prompt-to-video)
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/video-agents` | Create session (`generate` one-shot / `chat` multi-turn) |
| GET | `/v3/video-agents` | List sessions |
| GET | `/v3/video-agents/styles` | Curated visual styles |
| GET | `/v3/video-agents/{session_id}` | Session status (incl. `thinking` state) |
| POST | `/v3/video-agents/{session_id}` | Send message (answer question / request edit) |
| POST | `/v3/video-agents/{session_id}/stop` | Halt run, keep partials |
| GET | `/v3/video-agents/{session_id}/videos` | Videos from session |
| GET | `/v3/video-agents/{session_id}/resources/{resource_id}` | One resource |

### Assets
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/assets` | Multipart upload (image/video/audio/PDF, ≤32 MB) → `asset_id` |
| POST | `/v3/assets/direct-uploads` | Init presigned S3 upload (big files) |
| POST | `/v3/assets/{asset_id}/complete` | Finalize direct upload |
| GET | `/v3/assets/{asset_id}` | Asset metadata + public URL |
| DELETE | `/v3/assets/{asset_id}` | Delete |

### Audio / Brand
| Method | Path | Purpose |
|---|---|---|
| GET | `/v3/audio/sounds?query=...` | **Search background music** (`query` REQUIRED) |
| GET | `/v3/brand-kits` | List Brand Kits (`brand_kit_id` → Video Agent) |
| GET | `/v3/brand-glossaries` | List Brand Glossaries (`brand_glossary_id` → translation custom terms) |

### Webhooks
| Method | Path | Purpose |
|---|---|---|
| POST | `/v3/webhooks/endpoints` | Create (returns `signing_secret` ONCE) |
| GET | `/v3/webhooks/endpoints` | List |
| PATCH | `/v3/webhooks/endpoints/{endpoint_id}` | Update URL / events |
| DELETE | `/v3/webhooks/endpoints/{endpoint_id}` | Delete |
| POST | `/v3/webhooks/endpoints/{endpoint_id}/rotate-secret` | New signing secret |
| GET | `/v3/webhooks/event-types` | Available event types |
| GET | `/v3/webhooks/events` | Delivery history (filter type/entity) |

### Account
| Method | Path | Purpose |
|---|---|---|
| GET | `/v3/users/me` | Profile + `wallet`/`subscription` + `billing_type` |

### Legacy (v1/v2 — sunset 2026-10-31)
| Method | Path | Notes |
|---|---|---|
| POST | `/v1/audio/text_to_speech` | Legacy TTS (Starfish) |
| GET | `/v1/audio/voices` | Legacy voice list |
| GET | `/v1/user/me` | Legacy account |
| POST | `/v1/video_agent/generate` | Legacy Video Agent |
| GET | `/v1/workflows` | **Workflow API** list |
| POST | `/v1/workflows/executions` | Run a workflow |
| GET | `/v1/workflows/executions/{execution_id}` | Execution status |
| POST | `/v1/workflows/graph-executions` | Run graph workflow |
| POST | `/v2/video_translate` | Legacy translate (`brand_glossary_id`, `stock_voice_config`) |
| GET | `/v2/video_translate/caption` | Legacy caption |
| GET | `/v2/video_translate/target_languages` | Legacy lang list |
| POST/GET | `/v2/videos` | Legacy create/list (Studio API multi-scene lives here) |
| GET/DELETE | `/v2/videos/{video_id}` | Legacy status/delete |

## POST /v3/videos — three variants (discriminator `type`)

### Variant A — `avatar` (registered look)

```jsonc
{
  "type": "avatar",                          // REQUIRED discriminator
  "avatar_id": "<look_id>",                  // REQUIRED. video avatar or photo-avatar look ID
  "script": "...",                           // OR audio_url OR audio_asset_id (mutually exclusive)
  "voice_id": "<voice_id>",                  // required with script, UNLESS avatar has default voice
  "audio_url": "https://...",                // public audio to lip-sync
  "audio_asset_id": "...",                   // uploaded audio asset
  "voice_settings": {                        // optional voice tuning
    "speed": 1.0,                            // 0.5–1.5
    "pitch": 0,                              // -50..+50 semitones
    "volume": 1.0,                           // 0.0 silent .. 1.0 full
    "locale": "en-US",
    "engine_settings": { /* engine_type-discriminated */ }
  },
  "title": "Dashboard label",
  "resolution": "4k | 1080p | 720p",
  "aspect_ratio": "16:9 | 9:16 | 4:5 | 5:4 | 1:1 | auto",   // default 16:9
  "fit": "cover | contain",                  // how subject fits canvas
  "background": { "type": "color|image", "value": "#FFFFFF", "url": "...", "asset_id": "..." },
  "remove_background": false,                 // requires matting-trained video avatar
  "output_format": "mp4 | webm",             // webm = alpha/transparent BG
  "caption": { "style": "..." },             // burned-in caption; sidecar SRT always returned via subtitle_url
  "watermark": {                             // premium/Enterprise (WatermarkInput)
    "url": "https://...", "asset_id": "...",
    "scale": 1.0,                            // 0–2
    "opacity": 1.0,                          // 0–1
    "placement": "top_left|top_right|bottom_left|bottom_right",
    "offset_x": 0.0, "offset_y": 0.0
  },
  "motion_prompt": "...",                     // Avatar IV + photo avatars only
  "expressiveness": "high|medium|low",        // Avatar IV + photo avatars only (default low)
  "engine": { "type": "avatar_v" },           // opt-in Avatar V (object, NOT string). Default = IV
  "callback_url": "https://...",
  "callback_id": "echoed-back-in-webhook"
}
```

### Variant B — `image` (arbitrary image, no registered avatar)

```jsonc
{
  "type": "image",
  "image": { "type": "url", "url": "https://..." },     // OR {type:"asset_id",asset_id} OR {type:"base64",base64}
  "script": "...", "voice_id": "...",
  "motion_prompt": "...", "expressiveness": "high",     // supported here
  // engine.type=avatar_v NOT supported for image
}
```

### Variant C — `cinematic_avatar` (Seedance, prompt + references) — NEW 2026-06

No script/voice — motion + speech driven entirely by prompt + reference content.

```jsonc
{
  "type": "cinematic_avatar",                 // REQUIRED discriminator
  "prompt": "A founder in a sunlit studio...",// REQUIRED, 1–10000 chars
  "avatar_id": ["<look_id1>", "<look_id2>"],  // REQUIRED, ARRAY of 1–3 look IDs (visual refs)
  "references": [                             // optional asset refs (images/videos/audio)
    { "type": "url", "url": "https://..." },
    { "type": "asset_id", "asset_id": "..." },
    { "type": "base64", "base64": "..." }
  ],                                          // combined limit: ≤3 videos + ≤9 images across avatars+refs
  "aspect_ratio": "16:9 | 9:16 | 1:1",        // default 16:9 (cinematic supports only these 3)
  "resolution": "720p | 1080p",               // default 720p
  "auto_duration": false,                     // true → model picks length, omit duration
  "duration": 10,                             // 4–15 s, default 10
  "enhance_prompt": false,                    // server-side prompt enhancement
  "title": "..."
}
```
**Pricing:** flat **$7.00 per video** (4–15 s). Backed by Seedance.

**Response (all variants):** `{"data": {"video_id": "...", "status": "waiting", "output_format": "mp4"}}`

**Status:** `waiting → pending → processing → completed | failed`. Completed → `video_url`, `thumbnail_url`, `duration`, `subtitle_url`. **URLs expire — download or re-poll.**

## POST /v3/hyperframes/renders — HTML composition → video (NEW)

Renders a programmatic HTML/CSS/JS composition (Remotion-style) into video.

```jsonc
{
  "project": { "type": "url|asset_id|base64", "url": "https://.../composition.zip" }, // REQUIRED .zip
  "composition": "compositions/intro.html",   // entry HTML relative to project root (default index.html)
  "variables": { "title": "Hello", "color": "#0af" }, // overrides data-composition-variables
  "fps": 30,                                   // default 30
  "quality": "<preset>",                       // higher = slower
  "format": "<container/codec>",
  "resolution": "1080p | 4k",                  // default 1080p; 4k billed 1.5x
  "aspect_ratio": "16:9 | 9:16 | 1:1",         // default 16:9
  "title": "...",
  "callback_id": "...", "callback_url": "https://..."
}
```
Poll `GET /v3/hyperframes/renders/{render_id}`.

## Avatar types & Avatar V eligibility

| Type | Description | Avatar V eligible |
|---|---|---|
| `studio_avatar` | HeyGen public library | ✓ if look's `supported_api_engines` has `avatar_v` |
| `digital_twin` | Trained from real video footage | ✓ if eligible |
| `photo_avatar` | From a single photo | ✓ if eligible |
| `image` | Arbitrary image (no registered avatar) | ✗ requires a registered look |
| `prompt` | AI-generated from text | ✓ if eligible |

Check: `GET /v3/avatars/looks/{look_id}` → `data.supported_api_engines` (array). Avatar V eligibility is per **look**, not per group. `motion_prompt` + `expressiveness` are **rejected** when `engine.type=avatar_v`.

## POST /v3/avatars — create avatar (discriminator `type`)

```jsonc
// digital_twin (from video footage)
{ "type": "digital_twin", "name": "YourFirstName", "file": {"type":"url","url":"https://...mp4"}, "avatar_group_id": "<optional>" }
// photo (from a photo)
{ "type": "photo", "name": "...", "file": {"type":"url","url":"https://...jpg"}, "avatar_group_id": "<optional>" }
// prompt (AI-generated)
{ "type": "prompt", "name": "...", "prompt": "a 30yo founder, navy blazer", "reference_images": [{"type":"url","url":"..."}], "avatar_group_id": "<optional>" }
```
Custom avatars require consent: `POST /v3/avatars/{group_id}/consent` (optional `consent_text` for audit) → returned URL must be opened in a browser by the person. Training is async → `instant_avatar.*` / `photo_avatar_train.*` webhooks.

## Voices

```bash
GET  /v3/voices?engine=starfish&language=en&type=clone&gender=female&limit=20
GET  /v3/voices/{voice_id}                 # details + clone workflow status
POST /v3/voices                            # DESIGN voice (NL prompt → ≤3 matches)
POST /v3/voices/clone                      # clone from audio
POST /v3/voices/speech                     # TTS (Starfish voices only)
```
**Engines:** `starfish` (HeyGen native, only one that supports TTS), `elevenlabs`, `fish`.

### Design voice — `POST /v3/voices`
```jsonc
{ "prompt": "warm, confident female narrator, slight British accent",   // REQUIRED
  "gender": "female", "locale": "en-US", "seed": 0 }   // seed=0 = top matches; bump for new batch
```

### Clone voice — `POST /v3/voices/clone`
```jsonc
{ "audio": {"type":"url","url":"https://...mp3"},   // REQUIRED (url|asset_id|base64)
  "voice_name": "YourFirstName RU",                          // REQUIRED (NOT "name")
  "language": "ru",                                  // optional hint, auto-detected
  "remove_background_noise": true }
```
Returns a poll-able clone job; clone `voice_id` usable anywhere. Quota exceeded → `resource_limit_reached` (400).

### TTS — `POST /v3/voices/speech` (Starfish only)
```jsonc
{ "text": "...",                  // REQUIRED 1–5000 chars (field is "text", NOT "input")
  "voice_id": "<starfish voice>", // REQUIRED, must support starfish engine
  "input_type": "text | ssml",    // default text
  "speed": 1.0,                   // 0.5–2.0
  "language": "ru", "locale": "ru-RU" }  // optional; locale infers language
```
Returns audio URL + duration. **$0.000667/sec** — самый дешёвый вызов в API, удобен для коротких хуков и интро.

## Lipsync — `POST /v3/lipsyncs` (dub existing video)

```jsonc
{ "video": {"type":"url","url":"https://...mp4"},     // REQUIRED (url|asset_id)
  "audio": {"type":"url","url":"https://...mp3"},     // REQUIRED (url|asset_id)
  "mode": "speed | precision",                         // speed=fast; precision=avatar inference (better)
  "title": "...",
  "enable_caption": true,
  "keep_the_same_format": true,                        // preserve source resolution/bitrate
  "enable_dynamic_duration": false,
  "disable_music_track": false,
  "enable_speech_enhancement": false,
  "enable_watermark": false,
  "start_time": 0, "end_time": 30,                     // partial lipsync (sec)
  "fps_mode": "vfr | cfr | passthrough",
  "folder_id": "...",
  "callback_url": "...", "callback_id": "..." }
```
Poll `GET /v3/lipsyncs/{id}` → `status`, `video_url`, `caption_url`, `failure_reason`.

## Video Translation — `POST /v3/video-translations` ⚠️ schema corrected

```jsonc
{ "video": {"type":"url","url":"https://...mp4"},     // REQUIRED (url|asset_id) — NOT "video_url"
  "output_languages": ["Spanish (Spain)", "German", "Portuguese (Brazil)"],  // REQUIRED — language NAMES, not codes!
  "title": "...",
  "mode": "speed | precision",                         // precision uses avatar inference (better lip-sync)
  "audio": {"type":"url","url":"..."},                 // custom dubbing audio
  "input_language": "en",                              // source (auto-detected if omitted)
  "translate_audio_only": false,                       // keep original video, swap audio
  "speaker_num": 2,                                    // improves speaker separation
  "enable_caption": true,
  "keep_the_same_format": false,
  "enable_dynamic_duration": false,
  "disable_music_track": false,
  "enable_speech_enhancement": false,
  "enable_watermark": false,
  "start_time": 0, "end_time": 60,                     // partial translation (sec)
  "brand_glossary_id": "...",                          // custom term translations (brand_voice_id = legacy alias)
  "stock_voice_config": { "use_stock_voice": true, "engine": "starfish", "voice_id": "..." },  // Stock TTS instead of voice clone
  "srt": {"type":"url","url":"..."}, "srt_role": "input | output",  // custom subtitle file
  "fps_mode": "vfr | cfr | passthrough",
  "folder_id": "...",
  "callback_url": "...", "callback_id": "..." }
```
Get supported names: `GET /v3/video-translations/languages`. Poll `GET /v3/video-translations/{id}` → `status`, `caption_url`, `video_url`.

### Proofread workflow (edit SRT before final render)
1. `POST /v3/video-translations/proofreads` → `proofread_id`
2. Poll `GET /v3/video-translations/proofreads/{id}`
3. `GET /v3/video-translations/proofreads/{id}/srt` → download editable SRT (presigned)
4. Edit locally → `PUT /v3/video-translations/proofreads/{id}/srt` (upload edited)
5. `POST /v3/video-translations/proofreads/{id}/generate` → final render
   (`brand_glossary_id` accepted here too)

## Video Agent — `POST /v3/video-agents` (prompt-to-video)

```jsonc
{ "prompt": "Make a 30s ad for our product launch...",  // REQUIRED 1–10000 chars
  "mode": "generate | chat",                             // generate = one-shot; chat = multi-turn
  "avatar_id": "<optional>", "voice_id": "<optional>",
  "style_id": "<from GET /v3/video-agents/styles>",
  "brand_kit_id": "<from GET /v3/brand-kits>",
  "orientation": "landscape | portrait",                 // auto-detected if omitted
  "files": [ /* ≤20 attachments: image/video/audio/PDF */ ],
  "incognito_mode": false,                               // disable memory injection/extraction
  "callback_url": "...", "callback_id": "..." }
```
Returns `session_id`. Poll `GET /v3/video-agents/{session_id}` (status incl. `thinking`). Iterate: `POST /v3/video-agents/{session_id}` (answer questions / request edits). Stop: `POST /v3/video-agents/{session_id}/stop`. Outputs: `GET /v3/video-agents/{session_id}/videos`.

## Assets

**Small (≤32 MB) — direct multipart:**
```bash
POST /v3/assets   # multipart/form-data, file=<binary> → {data:{asset_id}}
```

**Large — presigned direct upload (3 steps):**
```jsonc
// 1. init
POST /v3/assets/direct-uploads
{ "filename": "clip.mp4", "content_type": "video/mp4", "size_bytes": 73400320, "checksum_sha256": "<hex optional>" }
// → returns asset_id + presigned upload URL
// 2. PUT bytes to the presigned URL
// 3. finalize
POST /v3/assets/{asset_id}/complete
```
`GET /v3/assets/{asset_id}` → metadata + public URL. `DELETE /v3/assets/{asset_id}`.

Unified asset reference union (every v3 endpoint accepting media):
```jsonc
{"type":"url","url":"https://..."} | {"type":"asset_id","asset_id":"..."} | {"type":"base64","base64":"..."}
```

## Webhooks — managed CRUD + signing

```bash
POST   /v3/webhooks/endpoints                       # create → signing_secret ONCE
GET    /v3/webhooks/endpoints
PATCH  /v3/webhooks/endpoints/{id}                  # change url/events
DELETE /v3/webhooks/endpoints/{id}
POST   /v3/webhooks/endpoints/{id}/rotate-secret
GET    /v3/webhooks/event-types
GET    /v3/webhooks/events                          # delivery history
```
```jsonc
POST /v3/webhooks/endpoints
{ "url": "https://yoursite.com/heygen-webhook",
  "events": ["avatar_video.success","avatar_video.fail","video_translate.success"] }
// → {"data":{"endpoint_id":"we_...","signing_secret":"whsec_..."}}  // STORE secret now (shown once)
```
Verify payloads via HMAC-SHA256 of raw body using `signing_secret`.

**`avatar_video.success` payload:**
```jsonc
{ "event_type":"avatar_video.success",
  "event_data":{ "video_id":"...","url":"<video_url>","gif_download_url":"...",
    "video_page_url":"...","video_share_page_url":"...","folder_id":"...","callback_id":"..." } }
```
**Event types (20+):** `avatar_video.success/fail`, `avatar_video_gif.success/fail`, `video_agent.success/fail`, `video_translate.success/fail`, `personalized_video`, `instant_avatar.success/fail`, `photo_avatar_generation.success/fail`, `photo_avatar_train.success/fail`, `photo_avatar_add_motion.success/fail`, `proofread_creation.success/fail`, `live_avatar.success/fail`. (Authoritative list via `GET /v3/webhooks/event-types`.)

## Pricing (USD per second, 2026 self-serve)

### Avatar IV & V (same rates since 2026-05-12)
| Avatar Type | 720p/1080p | 4K |
|---|---|---|
| Photo Avatar | $0.05/s | $0.0667/s |
| **Digital Twin** | **$0.0667/s** | $0.0833/s |
| Studio Avatar | $0.0667/s | $0.0833/s |

**YourFirstName = digital_twin → $2.00 per 30-s short (1080p), $200 per 100 shorts.** Avatar V no longer costs more than IV.

### Other
| Feature | Rate |
|---|---|
| Video Agent (prompt-to-video) | $0.0333/s (~half of Digital Twin direct) |
| **Cinematic Avatar** | **$7.00 flat per video** (4–15 s) |
| HyperFrames 4K | resolution 4k billed **1.5×** vs 1080p |
| Lipsync — speed / precision | $0.0333 / $0.0667 per s |
| Translation — audio-only / lipsync speed / precision | $0.0167 / $0.0333 / $0.0667 per s |
| TTS Starfish | $0.000667/s |
| Avatar creation (digital twin / photo) | $1.00 per call |
| Avatar III legacy (existing v1/v2 only) | $0.0167/s (720p/1080p), $0.02/s (4K) |

## Usage limits
| Resource | Limit |
|---|---|
| Concurrent video jobs | 10 (Pay-As-You-Go) → 429 + `Retry-After` |
| Script text | 5000 chars |
| Cinematic prompt / Video Agent prompt | 10,000 chars |
| Cinematic refs | ≤3 videos + ≤9 images (avatars+refs combined); 1–3 avatar looks |
| Cinematic duration | 4–15 s |
| Audio input | 600 s (10 min) |
| Multipart asset upload | 32 MB (use direct-uploads for larger) |
| Video input (lipsync/translate) | 100 MB, <2K, MP4/WebM |
| Image input | 50 MB, <2K, JPG/PNG |
| Audio input file | 50 MB, WAV/MP3 |
| Video Agent attachments | ≤20 (image/video/audio/PDF) |
| Output (avatar videos) | 25 fps, 128–4096 px/axis, ≤50 scenes, ≤30 min |
| Aspect ratio (avatar/image) | 16:9, 9:16, 4:5, 5:4, 1:1, auto (default 16:9) |
| Aspect ratio (cinematic/hyperframes) | 16:9, 9:16, 1:1 |
| TTS | 1–5000 chars, speed 0.5–2.0× |

## Idempotency-Key (all POST mutations)
Header `Idempotency-Key: <1–255 chars [A-Za-z0-9_:.-]>` (UUID = safe default).
- Same key within 24h → replays original response.
- Same key while original in flight → 409 `request_in_progress`.
- Scope: per-endpoint + per-resource.

## Error codes (v3 standard format)
```jsonc
{ "error": { "code": "...", "message": "...", "param": "field", "doc_url": "https://developers.heygen.com/docs/error-codes#..." } }
```
Codes: `invalid_parameter`, `authentication_failed`, `unauthorized`, `rate_limit_exceeded`, `resource_limit_reached`, `request_in_progress`, `not_found`, `internal_error`, `download_failed` (URL fetch failed), `gateway_timeout` (external fetch timed out), `ai_vendor_access_restricted` (workspace AI policy), `unlimited_mode_disabled`, `voice_unavailable` (clone failed/expired), `ephemeral_upload_disabled`, `avatar_group_not_found`, `webhook_not_found`.

| HTTP | Meaning |
|---|---|
| 200 | OK |
| 400 | invalid_parameter / validation / download_failed |
| 401 | unauthorized |
| 404 | not_found / avatar_group_not_found / webhook_not_found |
| 409 | request_in_progress (idempotency in flight) / webhook registration conflict |
| 429 | rate_limit_exceeded (+ Retry-After) |
| 500 | internal_error |

Pagination: cursor-based (`has_more`, `next_token`/`next_cursor`) → `?cursor=...&limit=20`.

## Idiomatic Python client (v3)

```python
import os, time, requests
from pathlib import Path

KEY = os.environ['HEYGEN_API_KEY']
BASE = 'https://api.heygen.com'
H = {'x-api-key': KEY, 'Content-Type': 'application/json'}
ASSET = lambda url=None, asset_id=None: ({'type':'url','url':url} if url else {'type':'asset_id','asset_id':asset_id})


def wallet_balance() -> float:
    r = requests.get(f'{BASE}/v3/users/me', headers={'x-api-key': KEY}, timeout=30); r.raise_for_status()
    return r.json()['data'].get('wallet', {}).get('remaining_balance', 0.0)


def create_video_avatar(*, avatar_id, script=None, audio_asset_id=None, voice_id=None,
                        aspect_ratio='9:16', resolution='1080p', use_avatar_v=False,
                        motion_prompt=None, expressiveness=None,
                        callback_id=None, callback_url=None, idempotency_key=None) -> str:
    body = {'type': 'avatar', 'avatar_id': avatar_id,
            'aspect_ratio': aspect_ratio, 'resolution': resolution}
    if script: body['script'] = script
    if audio_asset_id: body['audio_asset_id'] = audio_asset_id
    if voice_id: body['voice_id'] = voice_id
    if use_avatar_v: body['engine'] = {'type': 'avatar_v'}
    if motion_prompt: body['motion_prompt'] = motion_prompt
    if expressiveness: body['expressiveness'] = expressiveness
    if callback_id: body['callback_id'] = callback_id
    if callback_url: body['callback_url'] = callback_url
    headers = dict(H)
    if idempotency_key: headers['Idempotency-Key'] = idempotency_key
    r = requests.post(f'{BASE}/v3/videos', headers=headers, json=body, timeout=30)
    r.raise_for_status(); return r.json()['data']['video_id']


def create_video_cinematic(*, prompt, avatar_ids, references=None, aspect_ratio='9:16',
                           resolution='1080p', duration=10, auto_duration=False,
                           enhance_prompt=False, title=None) -> str:
    """Seedance prompt+refs. avatar_ids = list of 1–3 look IDs. Flat $7/video."""
    body = {'type': 'cinematic_avatar', 'prompt': prompt, 'avatar_id': avatar_ids,
            'aspect_ratio': aspect_ratio, 'resolution': resolution, 'enhance_prompt': enhance_prompt}
    if references: body['references'] = references          # [{'type':'url','url':...}, ...]
    if auto_duration: body['auto_duration'] = True
    else: body['duration'] = duration
    if title: body['title'] = title
    r = requests.post(f'{BASE}/v3/videos', headers=H, json=body, timeout=30)
    r.raise_for_status(); return r.json()['data']['video_id']


def get_video(video_id: str) -> dict:
    r = requests.get(f'{BASE}/v3/videos/{video_id}', headers={'x-api-key': KEY}, timeout=30)
    r.raise_for_status(); return r.json()['data']


def wait_for_video(video_id: str, max_min=15, poll_s=15) -> dict:
    deadline = time.time() + max_min * 60
    while time.time() < deadline:
        d = get_video(video_id); st = d.get('status')
        if st == 'completed': return d
        if st == 'failed': raise RuntimeError(f'{video_id} failed: {d.get("failure_reason")}')
        time.sleep(poll_s)
    raise TimeoutError(f'{video_id} not done in {max_min} min')


def avatar_v_eligible(look_id: str) -> bool:
    r = requests.get(f'{BASE}/v3/avatars/looks/{look_id}', headers={'x-api-key': KEY}, timeout=30)
    r.raise_for_status()
    return 'avatar_v' in r.json()['data'].get('supported_api_engines', [])


def upload_asset(path: Path) -> str:
    with open(path, 'rb') as f:
        r = requests.post(f'{BASE}/v3/assets', headers={'x-api-key': KEY}, files={'file': f}, timeout=120)
    r.raise_for_status(); return r.json()['data']['asset_id']


def lipsync(*, video_url, audio_url, mode='precision') -> str:
    r = requests.post(f'{BASE}/v3/lipsyncs', headers=H, json={
        'video': ASSET(url=video_url), 'audio': ASSET(url=audio_url), 'mode': mode}, timeout=30)
    r.raise_for_status(); return r.json()['data']['lipsync_id']


def translate(*, video_url, output_languages, mode='precision', title='Translation') -> list:
    """output_languages = language NAMES (e.g. ['Spanish (Spain)','German'])."""
    r = requests.post(f'{BASE}/v3/video-translations', headers=H, json={
        'video': ASSET(url=video_url), 'output_languages': output_languages,
        'mode': mode, 'title': title, 'fps_mode': 'passthrough'}, timeout=30)
    r.raise_for_status(); return r.json()['data']


def tts_starfish(*, voice_id, text, speed=1.0, input_type='text') -> dict:
    r = requests.post(f'{BASE}/v3/voices/speech', headers=H, json={
        'voice_id': voice_id, 'text': text, 'input_type': input_type, 'speed': speed}, timeout=60)
    r.raise_for_status(); return r.json()['data']


def clone_voice(*, audio_url, voice_name, language=None) -> dict:
    body = {'audio': ASSET(url=audio_url), 'voice_name': voice_name}
    if language: body['language'] = language
    r = requests.post(f'{BASE}/v3/voices/clone', headers=H, json=body, timeout=60)
    r.raise_for_status(); return r.json()['data']


def video_agent(*, prompt, mode='generate', style_id=None, brand_kit_id=None, callback_url=None) -> str:
    body = {'prompt': prompt, 'mode': mode}
    if style_id: body['style_id'] = style_id
    if brand_kit_id: body['brand_kit_id'] = brand_kit_id
    if callback_url: body['callback_url'] = callback_url
    r = requests.post(f'{BASE}/v3/video-agents', headers=H, json=body, timeout=30)
    r.raise_for_status(); return r.json()['data']['session_id']


def register_webhook(url: str, events: list) -> dict:
    r = requests.post(f'{BASE}/v3/webhooks/endpoints', headers=H, json={'url': url, 'events': events}, timeout=30)
    r.raise_for_status(); return r.json()['data']   # {endpoint_id, signing_secret} — store secret now
```

## Recipes

### YourFirstName short — highest quality (Avatar V if eligible)
```python
look_id = '<yourfirstname look_id>'   # verify it's a v3 look via GET /v3/avatars/looks
vid = create_video_avatar(avatar_id=look_id, script='Hook... reveal... loop close.',
    voice_id = 'YOUR_HEYGEN_VOICE_ID', aspect_ratio='9:16', resolution='1080p',
    use_avatar_v=avatar_v_eligible(look_id), callback_id='shorts-user-001')
d = wait_for_video(vid)   # d['video_url'] → SubMagic
```

### Cinematic Avatar — prompt + YourFirstName reference (Seedance)
```python
vid = create_video_cinematic(
    prompt='YourFirstName in a sunlit studio, warm cinematic grade, slow push-in, talking to camera about AI.',
    avatar_ids=['<yourfirstname look_id>'], references=[{'type':'url','url':'https://.../user-ref.jpg'}],
    aspect_ratio='9:16', resolution='1080p', duration=12)
d = wait_for_video(vid)
```

### ElevenLabs clone → HeyGen lip-sync
```python
# Option A: pre-recorded audio into /v3/videos
asset_id = upload_asset(elevenlabs_tts(text='...', voice_id=os.environ['ELEVENLABS_VOICE_ID_YOURNAME']))
create_video_avatar(avatar_id = 'YOUR_HEYGEN_AVATAR_ID', audio_asset_id=asset_id, aspect_ratio='9:16')
# Option B: dub an existing video
lipsync(video_url='https://...user.mp4', audio_url='https://...eleven.mp3', mode='precision')
```

### Translate webinar to 5 languages
```python
ids = translate(video_url='https://...webinar.mp4',
    output_languages=['English','Spanish (Spain)','French','German','Portuguese (Brazil)'],
    mode='precision', title='YourFirstName webinar')
# poll GET /v3/video-translations/{id} per returned translation
```

### HyperFrames — branded intro from HTML
```python
import requests
r = requests.post(f'{BASE}/v3/hyperframes/renders', headers=H, json={
    'project': {'type':'url','url':'https://.../intro-comp.zip'},
    'composition': 'compositions/intro.html',
    'variables': {'title': 'Your Channel Name', 'accent': '#ff6a00'},
    'resolution': '1080p', 'aspect_ratio': '9:16', 'fps': 30}, timeout=30)
render_id = r.json()['data']['render_id']
```

## Gotchas (verified 2026-06-05)

- **Auth header `x-api-key`** (case-insensitive). NOT Bearer (unless OAuth). NOT `X-Api-Key` required-case.
- **Баланс кошелька API** — платные задачи идут только при положительном балансе; проверка `GET /v3/users/me`.
- **`POST /v3/videos` is a 3-way union** on `type`: `avatar` / `image` / `cinematic_avatar`.
- **Cinematic `avatar_id` is an ARRAY** of 1–3 look IDs; no script/voice; flat $7.
- **Translation: `output_languages` = language NAMES not codes** (`'Spanish (Spain)'`), field is `video` not `video_url`. Get names from `GET /v3/video-translations/languages`.
- **Lipsync uses `video`+`audio` asset unions**, not `video_url`/`audio_url` top-level.
- **TTS field is `text`** (not `input`). **Voice clone fields are `audio`+`voice_name`** (not `audio_url`+`name`). **Voice design is `POST /v3/voices`** with `prompt`.
- **Avatar V opt-in:** `engine: {"type":"avatar_v"}` (object). `motion_prompt`/`expressiveness` rejected with it. Eligibility per **look**. `image` type can't use Avatar V.
- **Avatar V = same price as IV** (since 2026-05-12).
- **aspect_ratio default 16:9** — for Shorts always pass `"9:16"`. Cinematic/HyperFrames support only 16:9/9:16/1:1.
- **`voice_settings.speed` is 0.5–1.5** (TTS endpoint speed is 0.5–2.0).
- **Webhook `signing_secret` shown once**; `PATCH` to change url/events, `rotate-secret` for new secret.
- **`fps_mode` strict enum:** `vfr|cfr|passthrough`.
- **Large assets:** use `direct-uploads` (init → PUT → complete), not 32 MB multipart.
- **Send Video Agent message = `POST /v3/video-agents/{session_id}`** (the session itself), not `/messages`.
- **Output URLs expire** — download or re-poll.
- **Studio API (multi-scene) + Template API** remain v2-only.
- **`callback_id`** echoed verbatim in webhook `event_data.callback_id`.

## YourFirstName setup reference
your-server `/root/video-production/config/settings.yaml` (legacy v2):
```yaml
avatar_id: YOUR_HEYGEN_AVATAR_ID    # verify this is a valid v3 look_id
voice_id: YOUR_HEYGEN_VOICE_ID_1
dimension: {width: 720, height: 1280}          # → aspect_ratio "9:16" in v3
```
**Action item:** confirm `avatar_id` resolves to a v3 `look_id` via `GET /v3/avatars/looks?group_id=<group>`; check `supported_api_engines` for `avatar_v`.

## MCP server (no API key)
HeyGen Remote MCP — Claude Web/Code, Cursor, Gemini CLI, OpenAI, Manus, Superhuman. OAuth, no local server. https://developers.heygen.com/mcp/overview. Tools: `create_video_from_avatar`, `create_video_from_image`, `list_videos`, `get_video`, `delete_video`, `create_digital_twin`, `create_photo_avatar`, `create_prompt_avatar`, `create_avatar_consent`, `list_avatar_looks`, `get_avatar_look`, `update_avatar_look`, `create_lipsync`, `create_video_translation`, `design_voice`.

## CLI (heygen v0.0.4)
```bash
heygen video create --avatar-id <id> --script "..." --voice-id <id> --wait --timeout 600
heygen video translate --video-url <url> --target-languages "Spanish (Spain),German" --mode precision --wait
heygen lipsync create --video-url <url> --audio-url <url> --mode precision --wait
heygen voice design "warm confident narrator"
heygen voice clone --audio-url <url> --name "My Voice"
heygen webhook create --url <url> --events avatar_video.success,avatar_video.fail
heygen avatar looks --avatar-type digital_twin
heygen --request-schema POST /v3/videos        # inspect schema w/o API key
```

## LiveAvatar — Realtime Video Avatar (separate service)

**Full reference: `references/liveavatar.md`** (SDK source, OpenAPI spec, WebSocket protocol, Telegram integration architecture).

**Base URL:** `https://api.liveavatar.com` (NOT `api.heygen.com`)
**Auth:** `X-API-KEY` header, key in `.credentials.master.env` → `HEYGEN_LIVE_AVATAR_API_KEY`
**SDK:** `@heygen/liveavatar-web-sdk` (npm), built on **LiveKit** (WebRTC rooms)
**OpenAPI:** `https://docs.liveavatar.com/openapi.json` (24 endpoints)
**SDK source:** `github.com/heygen-com/liveavatar-web-sdk` → `packages/js-sdk/src/`

| Mode | Cost | HeyGen does | You provide |
|------|------|-------------|-------------|
| **FULL** | 2 credits/min | STT + LLM + TTS + avatar | Configure via API |
| **LITE** | 1 credit/min | Avatar render only | STT + LLM + TTS pipeline |

**LITE mode** is key for custom integrations (Telegram calls, custom voice agents):
- You get a LiveKit room with avatar video+audio tracks
- You get a WebSocket for sending PCM 24kHz audio → avatar lip-syncs
- Commands: `agent.speak` (chunked base64 PCM), `agent.interrupt`, `agent.start/stop_listening`

**Quick check credits:**
```python
import os, requests
r = requests.get('https://api.liveavatar.com/v1/users/credits',
                 headers={'X-API-KEY': os.environ['HEYGEN_LIVE_AVATAR_API_KEY']})
print(r.json())
```

## Local references
- **OpenAPI spec (authoritative): `${HOME}/_heygen_openapi.json`** (54 paths, 145 schemas)
- v3 docs (локальная копия): `${HOME}/_heygen_v3_docs.md`
- v1/v2 legacy (локальная копия): `${HOME}/_heygen_docs.md`
- Skill backups: `SKILL.md.bak.v3-pre-20260605` (this update), `SKILL.md.bak.v2`
- Creds: `~/.claude/.credentials.master.env` → `HEYGEN_API_KEY` / `_DEV` / `_AGENT`
- your-server pipeline (legacy v2): `ssh your-server` → `/root/video-production/services/heygen.py`
- Changelog: https://developers.heygen.com/changelog · OpenAPI online: https://developers.heygen.com/openapi/external-api.json

## Use cases → endpoints
| Goal | Endpoint(s) |
|---|---|
| Highest-quality talking head | check look eligibility → `POST /v3/videos` + `engine:{"type":"avatar_v"}` |
| Default avatar video | `POST /v3/videos` type=avatar (omit engine) |
| Cinematic prompt video (Seedance) | `POST /v3/videos` type=cinematic_avatar |
| Animate arbitrary image | `POST /v3/videos` type=image |
| Render HTML motion graphics | `POST /v3/hyperframes/renders` |
| Lip-sync ElevenLabs audio | upload asset → `POST /v3/videos` audio_asset_id |
| Dub existing video | `POST /v3/lipsyncs` (precision) |
| Multilingual webinar | `POST /v3/video-translations` (output_languages names) |
| Edit subtitles before render | proofreads → srt PUT → generate |
| Prompt-to-video AI | `POST /v3/video-agents` |
| Voice from description | `POST /v3/voices` (design) |
| Clone a voice | `POST /v3/voices/clone` |
| TTS only | `POST /v3/voices/speech` (Starfish) |
| Background music | `GET /v3/audio/sounds` |
| Brand-consistent video | `POST /v3/video-agents` + brand_kit_id |
| Custom term translation | brand_glossary_id (`GET /v3/brand-glossaries`) |
| Large file upload | `/v3/assets/direct-uploads` → complete |
| Transparent BG video | output_format=webm + remove_background=true |
| Safe POST retries | Idempotency-Key header |
| Async tracking | callback_url + callback_id OR managed webhook |
| Multi-scene / templates | v2 Studio API / Template API only |
