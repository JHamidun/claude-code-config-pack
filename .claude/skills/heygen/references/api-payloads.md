# Тела запросов: видео, аватары, голоса, липсинк, перевод, ассеты, вебхуки

Схемы и примеры payload по каждому семейству вызовов: три варианта `POST /v3/videos`, HyperFrames, создание аватаров, голоса и клонирование, липсинк, перевод с исправленной схемой, Video Agent, ассеты, CRUD вебхуков и подпись. Читай перед тем, как формировать запрос.

## Оглавление

- POST /v3/videos — three variants (discriminator `type`)
- Variant A — `avatar` (registered look)
- Variant B — `image` (arbitrary image, no registered avatar)
- Variant C — `cinematic_avatar` (Seedance, prompt + references) — NEW 2026-06
- POST /v3/hyperframes/renders — HTML composition → video (NEW)
- Avatar types & Avatar V eligibility
- POST /v3/avatars — create avatar (discriminator `type`)
- Voices
- Design voice — `POST /v3/voices`
- Clone voice — `POST /v3/voices/clone`
- TTS — `POST /v3/voices/speech` (Starfish only)
- Lipsync — `POST /v3/lipsyncs` (dub existing video)
- Video Translation — `POST /v3/video-translations` ⚠️ schema corrected
- Proofread workflow (edit SRT before final render)
- Video Agent — `POST /v3/video-agents` (prompt-to-video)
- Assets
- Webhooks — managed CRUD + signing

---

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
Returns audio URL + duration. **$0.000667/sec** — effectively free for hooks/intros.

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

