# HeyGen v3 — полная карта эндпоинтов и тел запросов

Источник истины: `${HOME}/_heygen_openapi.json` (54 paths, 145 schemas, OpenAPI 3.1.0).
Читай этот файл, когда собираешь тело запроса или ищешь путь, которого нет в
таблице «Use cases» в SKILL.md.

**Base URL:** `https://api.heygen.com` (без суффикса версии; версия в пути — `/v3`, `/v2`, `/v1`)

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

### Variant C — `cinematic_avatar` (Seedance, prompt + references) — 2026-06

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

**Response (all variants):** `{"data": {"video_id": "...", "status": "waiting", "output_format": "mp4"}}`

**Status:** `waiting → pending → processing → completed | failed`. Completed → `video_url`, `thumbnail_url`, `duration`, `subtitle_url`. **URLs expire — download or re-poll.**

## POST /v3/hyperframes/renders — HTML composition → video

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
{ "type": "digital_twin", "name": "<имя своего аватара>", "file": {"type":"url","url":"https://...mp4"}, "avatar_group_id": "<optional>" }
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
  "voice_name": "<имя своего голоса>",                 // REQUIRED (NOT "name")
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
Returns audio URL + duration.

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

## Video Translation — `POST /v3/video-translations`

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

## MCP server (no API key)

HeyGen Remote MCP — Claude Web/Code, Cursor, Gemini CLI, OpenAI, Manus, Superhuman. OAuth, no local server. https://developers.heygen.com/mcp/overview
Tools: `create_video_from_avatar`, `create_video_from_image`, `list_videos`, `get_video`, `delete_video`, `create_digital_twin`, `create_photo_avatar`, `create_prompt_avatar`, `create_avatar_consent`, `list_avatar_looks`, `get_avatar_look`, `update_avatar_look`, `create_lipsync`, `create_video_translation`, `design_voice`.

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
