# HeyGen WEB-session internal API (api2.heygen.com)

> Reverse-engineered 2026-06-05 via Playwright. Account `your-heygen-account@example.com`,
> **plan = Team Unlimited** (`tier:team`, `is_trial:false`). Use this to bill the
> **web subscription** instead of the empty **$0 public-API wallet**.
> Public API (`api.heygen.com` v1/v2/v3) is documented in `../SKILL.md`; it bills the
> API wallet and the web session token is NOT accepted there as Bearer (401).

## Why this exists

`GET api.heygen.com/v3/users/me` → `wallet.remaining_balance = 0.0`. But the account
has an active paid **Team Unlimited** subscription used via the web app. The web app
talks to a **separate internal API** at `api2.heygen.com` that bills the subscription
(paid videos created this cycle). This skill drives that internal API headlessly.

## Auth (cracked)

- The web app sends header **`x-guest-session-token`** = the value of the
  **`heygen_token` cookie** (domain `.heygen.com`, NOT httpOnly → readable).
- That value is `base64(JSON)`: `{"token":"<32-hex>","token_type":"regular","created_at":<ts>}`.
- A second cookie `heygen_session` (httpOnly, on `api2.heygen.com`) wraps the SAME inner
  token under `{"session_token": "<same base64>"}` — one secret, two carriers.
- Also send **`x-space-id`** = the account/space id (`<HEYGEN_SPACE_ID>`).
- **Guest vs regular:** before OAuth completes, the token resolves to a throwaway guest
  (email null, `video_duration_limit:60`). After Google login it binds to the real
  account (email set, limit 1800s, `tier:team`). Always verify via `whoami`.

Headers that work headless (verified):
```
x-guest-session-token: <heygen_token base64>
x-space-id: <HEYGEN_SPACE_ID>
x-ver: 4.1.0
accept: application/json, text/plain, */*
origin: https://app.heygen.com
```

### Credentials (in ~/.claude/.credentials.master.env)
```
HEYGEN_WEB_TOKEN      # heygen_token base64 value → x-guest-session-token. MAIN secret.
HEYGEN_WEB_RAW_TOKEN  # inner 32-hex token (informational)
HEYGEN_WEB_SPACE_ID   # <HEYGEN_SPACE_ID>
HEYGEN_WEB_API_BASE   # https://api2.heygen.com
```

### Re-capture when expired (token rotates on logout / after weeks)
Via Playwright MCP on a logged-in `app.heygen.com`:
```js
async (page) => {
  const c = (await page.context().cookies()).find(x => x.name === 'heygen_token');
  const sp = (await page.context().cookies()).find(x => x.name === 'heygen_space' || x.name==='shared-u');
  return JSON.stringify({ HEYGEN_WEB_TOKEN: c && c.value, HEYGEN_WEB_SPACE_ID: sp && sp.value });
}
```
`heygen_token` is NOT httpOnly → also readable via `document.cookie`. If the app shows a
guest token, complete the Google login first (account `your-heygen-account@example.com`).

## Feature taxonomy (from /v1/project/items item_types)

The Team plan exposes every HeyGen feature. Internal item/project types:
`heygen_video` (AI Studio avatar video), `heygen_video_draft`, `video_translate`,
`video_translate_proofread`, `video_agent`, `video_agent_edit`, `interactive_video`
(streaming avatar), `video_repurpose`, `heygen_podcast`, **`seedance_2`** (Cinematic
Avatar), `upscale_video`, `filler_removal`, and `batch_*` variants. Product Placement
lives under **Apps**.

## CONFIRMED read endpoints (base api2.heygen.com, all GET unless noted)

### Account / billing
| Endpoint | Returns |
|---|---|
| `/v1/pacific/account.get?include_ff=true` | user, limits, feature flags |
| `/v1/user.get` | user profile |
| `/v1/payment/subscription` | tier, entitlements[], addons[] |
| `/v1/account/usage` | paid_videos_created_*, renewal date |
| `/v1/space.list`, `/v1/space.get?space_id=` | spaces |
| `/v1/space/user.list[?include_superadmins=true]` | members |
| `/v1/payment/product` | plans catalog |
| `/v1/video_history/monthly_priority_video_count` | fast-render usage |
| POST `/v1/appsync/token` | realtime token |

### Avatars / voices
| Endpoint | Returns |
|---|---|
| `/v2/avatar_group.private.list?limit=&page=` | your avatar groups |
| `/v2/avatar_group?id=<group_id>` | one group |
| `/v2/avatar_group/look.list?group_id=&type=all&page=&limit=` | looks (outfits) |
| `/v2/avatar.get?look_id=` | look details |
| `/v1/avatar_group/voices.get?avatar_group_id=&is_public=false` | voices for avatar |
| `/v1/avatar_group/recently_used.list` | recent avatars |
| `/v1/avatar_group/slot_info.get` | digital-twin slot usage |
| POST `/v3/avatars` | create avatar (digital_twin/photo/prompt) |

### Projects / videos (output listing + status)
| Endpoint | Returns |
|---|---|
| `/v1/projects?project_types=...&is_trash=false[&traverse_deep=true&limit=999]` | projects |
| `/v1/project/items?limit=&item_types=...&sort_key=created_ts&sort_order=desc` | all items (videos, translations, agent runs) w/ status + URLs |
| `/v1/video_agent/sessions?page_size=&sort_by=last_activity_ts` | agent sessions |

Note: each `project/items` row carries the item status and output `video_url` once ready —
this is the **polling + download** surface (no separate status endpoint needed for most).

## WRITE / generate endpoints — CAPTURED (verified live 2026-06-05)

All paths POST to api2. **Internal create paths are NON-obvious** (mix of `.create`
dot-style and `/submit` slash-style) — captured from live submits, not guessable.
Generic status poll for ALL of them: `GET /v1/project/items/status?item_ids=<id>`
(or feature-specific list endpoints). The client wraps each below.

### Video Translation — `POST /v3/video_translate.create`
```jsonc
{ "name": "title",
  "google_url": "https://public-video.mp4",   // OR "input_video_id": "<existing id>"
  "output_languages": ["Russian (Russia)"],    // language NAMES (GET /v2/video_translate/support_languages)
  "instruction": "", "vocabulary": [], "enable_video_stretching": true,
  "source_type": "video_translate", "translate_audio_only": false, "captions": false,
  "keep_the_same_format": false, "enable_speech_enhancement": false, "disable_music_track": false,
  "recaptcha_token": "", "create_collection": true, "is_quality_mode": false }  // is_quality_mode=true → precision
```
Preflight (optional): `POST /v1/video_translate.preflight` {input_type:"url"|"file", duration, translate_audio_only}.
List: `GET /v2/video_translate/list?limit=20`. Status: `GET /v1/project/items/status?item_ids=<base>-<lang>` (e.g. `...-jv_jv-ID`).

### Video Agent (prompt-to-video) — `POST /v1/video_agent/sessions`
```jsonc
{ "prompt": "Make a 15s avatar intro about YourProduct",
  "config": {"orientation":"auto","use_video_agent_v2a":true,"chat_mode":"auto","agent_mode":"super_agent"},
  "chat_configuration": {"duration":"auto","orientation":"auto"},
  "video_source_type":"video_agent","subtype":"interactive_chat" }
// → { session_id, chat_id, ... }
```
Drive the session: `POST /v2/video_agent/interactive_chat`
```jsonc
{ "session_id":"...","chat_id":"...","user_input":"...",
  "asset_references":[{"asset_type":"avatar","asset_id":"<look>","display_name":"Ryan","tag_id":"{{@avatar:<look>}}"},
                      {"asset_type":"voice","asset_id":"<voice>","display_name":"Juno","tag_id":"{{@voice:<voice>}}"}],
  "auto_proceed":false,"debug_mode":false,"engine_tier":"default","chat_mode":"auto",
  "chat_configuration":{},"edit_plan":[] }
```
Read: `GET /v1/video_agent/sessions?page_size=&sort_by=last_activity_ts` · `/sessions/{id}` · `/sessions/{id}/chat` · `/v1/video_agent/{id}/artifacts` · `/v2/video_agent/{id}/board?filters=...`.

### Photo-to-Video / Avatar IV — `POST /v1/avatar/video_generate/submit`
3 steps: (1) `GET /v1/avatar/video_generate/get_upload_photo_url` → `{upload_url, s3_key, s3_url}`
(2) `PUT` image bytes to `upload_url` (headers: content-type, `x-amz-server-side-encryption: AES256`)
(3) submit:
```jsonc
{ "photo_s3_key": "<s3_key>", "title": "Avatar IV video",
  "text_voice_setting": {"input_text":"Привет!","voice_id":"<voice_id>"} }   // XOR "audio_voice_setting":{"audio_url":...}
```
Setup reads: `/v1/avatar/video_generate/limits`, `/preset_photo_and_voice_list?mode=normal`, `/preset_scripts_and_audios`.

### Cinematic Avatar (Seedance 2) — `POST /v1/seedance2/submit`
```jsonc
{ "prompt": "Man walks through neon night city, talks to camera",
  "avatar_look_ids": ["<look_id>"],          // 1–3 avatar looks as references
  "ratio": "16:9",                            // 16:9 | 9:16 | 1:1
  "resolution": "720p",                       // 720p | 1080p
  "duration": 10,                             // 4–15 s
  "enhance_prompt": true }
// → { video_id, status:"processing", ... }   ~4 credits/sec
```
List/status: `GET /v1/seedance2.list?offset=0&limit=10` (→ generations[] with video_id+status).

### Image generation / Product Placement — `POST /v3/image/generate`
```jsonc
{ "prompts": ["Realistic photo of influencer holding the product ..."],
  "reference_images": ["s3://heygen-product/avatar_v4_user_photar/<key>/image.jpg", ...],  // from get_upload_photo_url s3_url
  "num_generations": 1 }
```
Product Placement = upload product photo + avatar photo (get_upload_photo_url → PUT) → image_generate to
compose → then Avatar IV submit with the composed image. Standalone AI image gen uses image_generate without refs.

### AI Studio — multi-scene avatar video (`heygen_video`, canonical talking-head)
3 calls: `POST /v1/text_draft.create` → `{video_id}`; `POST /v1/text_draft.save` (scene graph);
`POST /v1/text_draft.generate` (render). video_id = draft id. Also `/v1/draft/heartbeat` (keepalive).
The scene graph (`text_draft`):
```jsonc
{ "video_id":"<draft id>",
  "script": {"elements":{"<tts_id>":{"type":"tts","attributes":{"voice_id":"<v>","voice_settings":{"speed":1,"pitch":0,"volume":1,"voice_engine_settings":{"engine_type":"auto"}}},"text":"<script>"}},"timeline":["<tts_id>"],"brand_kit_id":"<opt>"},
  "captions":{"elements":{},"remove_punctuation":false}, "background_audio":{"elements":{}},
  "visual": {"elements":{
      "<scene_id>":{"type":"scene","content":{"elements":["<av_id>"],"background_color":"#FFFFFF"}},
      "<av_id>":{"type":"avatar","attributes":{"position":{"type":"center"},"size":{"fit":"contain","scale":{"x":1,"y":1}}},
        "content":{"avatar_id":"<look>","avatar_type":"photo_avatar","avatar_group_id":"<grp>","use_avatar_iv_model":true,
                   "engine":"avatar_iv","engine_settings":{"engine_type":"avatar_iv_turbo","model":"4.3_turbo_edge","resolution":"1080p","alpha":0}}}},
    "layout":["<scene_id>"]},
  "alignments": {"<scene_id>":{"alignment_info":{"start":{"script_id":"<tts_id>","word_index":0},"end":{"script_id":"<tts_id>","word_index":-1}}}, "<av_id>":{...same...}},
  "video_output": {"resolution":{"width":1920,"height":1080},"fps":25,"caption":false} }
```
`generate` body = `{video_id, enable_watermark:false, generate_type:"normal", draft_details:{title, text_draft_with_metadata:{text_draft:<draft>, video_output:{...}}}, complete_tts_in_backend:true}`.
Client wraps this as `studio_video(script=, avatar_id=, voice_id=, avatar_group_id=, resolution=)` (single-scene builder).

### Apps / enhancement tools — ⚠️ EACH HAS ITS OWN API NAMESPACE (frontend slug ≠ API route)
Confirmed: `POST /v1/apps/upscale-video {}` → 400 (exists), but `POST /v1/apps/faceswap {}` → 404
(face swap's real route is `/v1/face_swap_v2.*`). So you MUST capture each app's real endpoint from a
live submit — guessing fails. **Universal source upload — 3 steps (NOT multipart, file.upload is JSON):**
1. `POST /v1/file.url` `{file_type:"video"|"image"|"audio"|"document", filename, md5, properties:{width,height,duration}}`
   → `{id, key, url(presigned S3 PUT, or **null** if md5 dedup), upload_part_urls(multipart), download_url}`.
2. If `url` not null: **`PUT` bytes to it with header `x-amz-server-side-encryption: AES256`** (it's in the signed
   headers — omitting → 403). If `url` null, content already exists (md5 dedup) — skip.
3. `POST /v1/file.upload` `{name, id, file_type, md5, pipeline:"asset", upload_knowledge:false}` (register).
Result file lives at `download_url` = `https://resource2.heygen.ai/video/<id>/original.mp4`. Client `file_upload(path)` does all 3 (ffprobe for dims).

Captured real endpoints (verified live 2026-06-05):
| App (UI name → frontend slug) | API endpoint(s) | body |
|---|---|---|
| **Upscale Video** (`upscale-video`) | `POST /v1/apps/upscale-video` (+ `/estimate`) ; status `/v1/apps/upscale-video/{id}/status` ; output `/v1/apps/output/{id}` | `{video_url, model:"slp-2.5"(Starlight Precise), output_width:3840, output_height:2160, video_width, video_height, duration, file_size}` (4K=3840×2160 / HD=1920×1080) |
| **Face Swap** (`faceswap`) | `POST /v1/face_swap_v2.video.submit` ; status `POST /v1/face_swap_v2.video.status` ; credits `GET /v1/face_swap_v2.free_credits` | `{source_video_url, target_face_url(png), duration}` (also `.image.submit` for image targets) |
| **Speech Cleanup** (`speech-cleanup` → app `filler-removal`) | `POST /v1/apps/filler-removal/preview/create` → preview ; `GET /v1/apps/filler-removal/preview/{id}/status` ; render `POST /v1/apps/filler-removal` | `{video_url, duration, source_filename}` |
| **AI Video Generator / B-Roll** (`generate-b-roll`) | `POST /v1/file.ai_generate_element` ; status `GET /v1/file.ai_generate_element.check?workflow_id=` ; history `.history?type=video` | `{element:{type:"video"|"image", id, provider:"seedance_2", aspect_ratio, prompt, config:{duration,resolution}}, stats_trace_id:"video-generator", source:"VideoGenerator_redesign"}` (text→video, no avatar) |
| **Auto Clips** (`instant-highlights`) | upload → `POST /v1/apps/instant-highlights*` (long video) | params: clip_duration(auto), output_format(9:16/16:9/1:1), caption_style, additional_instructions |
| Apps generic | `GET /v1/apps/recents` ; `GET /v1/apps/<slug>/history` | — |

Client: `file_upload(path)`, `upscale(path_or_url, to_4k=)`, `face_swap(source_video_url, target_face_url, duration)`,
`speech_cleanup_preview(video_url, duration)`, `ai_generate(prompt, type=, aspect_ratio=, duration=, resolution=)` + `ai_generate_status`,
generic `apps_run(slug, **params)` / `apps_status` / `apps_output` / `apps_recents`.

### Status / download (generic)
- `GET /v1/project/items/status?item_ids=<id>[&item_ids=<id2>]` — status for avatar/translate/agent/seedance items.
- `GET /v1/project/items?item_types=...&limit=` — list; completed rows carry `video_url` + `video_download_url` (presigned).
- App jobs: `GET /v1/apps/<slug>/{id}/status` + `GET /v1/apps/output/{id}`.
- Client `wait_item(id)` polls to completion; `download(url, out)` / CLI `download <item_id> <out> --wait`. **Verified: full generate→poll→download produces a valid mp4.**

### PPT / PDF → Video (captured 2026-06-06)
Upload deck (`file_upload(path)` with file_type=document) → convert → opens an AI Studio draft → render via `studio_generate`.
- `POST /v1/ent_ppt_pdf_conversion/convert` `{ppt_uuid, conversion_type:"image_background", extract_notes:false, generate_script:true, ppt_conversion_version:"v2", template_name}` → `{workflow_id}`
- `GET /v1/ent_ppt_pdf_conversion/status.get?workflow_id=` ; `GET /v1/pacific/ppt/workflow/{wf}/unsupported_fonts` ; per-slide `POST /v1/pacific/artifacts/ppt_rendered_scene`.
- Client `ppt_to_video(path)` + `ppt_conversion_status(wf)`. NOTE: the deck must be registered through the **PPT pipeline**, not `pipeline:"asset"` — an asset-pipeline `ppt_uuid` → convert returns `400569 Not found`. Re-capture the browser's exact PDF register call (pipeline value) to finish local-deck upload; or upload the deck via the PPT page once.

### Batch Mode (captured 2026-06-06) — scripts × avatars matrix
- `POST /v1/avatar/batch_mode/submit` `{video_output:{resolution:{width,height},fps,caption}, source_type:"avatar_video_batch_mode", project_name, batches:[{batch_name, batch_script, avatar_batch_videos:[{title, text_draft_with_metadata:{text_draft:<AI-Studio scene graph>, video_output}}]}]}`.
- Each `avatar_batch_videos[]` carries the SAME text_draft scene graph as AI Studio (one per avatar). Client `batch_mode(project_name, scripts=[...], avatars=[{avatar_id,voice_id,avatar_group_id,avatar_type,name}])`.

### Still TODO (niche)
- **Lipsync** — no standalone web app in the grid; use the public `/v3/lipsyncs` (SKILL.md, bills API wallet) or the AI Studio editor's per-scene audio. Web `/v1/apps/lip-sync` not present.
- **Interactive / LiveAvatar** (streaming) — separate realtime API (`/v1/appsync/token` + streaming session over WebSocket), not REST; not captured.

Capture recipe (for any remaining flow): open in logged-in browser → Submit →
`browser_network_requests {filter:"api2\\.heygen\\.com", static:false}` → find the `[POST]` →
`browser_network_request {index:N, part:"request-body"}` → call via `client.call(path,"POST",json_body=...)` or `apps_run(slug, **params)`.

## Client

`../scripts/heygen_web_client.py` — auth from env, all read endpoints, quota, generic
`call(path, method, params, json_body)`. CLI: `whoami quota account subscription usage
avatars looks <gid> avatar <lid> voices <gid> projects items agent-sessions call <path>`.

```bash
cd ~/.claude/skills/heygen/scripts
python heygen_web_client.py whoami
python heygen_web_client.py quota
python heygen_web_client.py avatars
python heygen_web_client.py call /v1/payment/subscription
```

## Gotchas
- Internal API wraps responses in `{code:100, data:..., msg}` — client unwraps `data`.
- `api2.heygen.com` does NOT host `/v3/users/me` etc (404) — different surface than public API.
- Web token rejected as Bearer on public `api.heygen.com` (401) — surfaces are separate.
- Guest-token trap: always `whoami` to confirm `email` is set (not a guest session).
- Windows stdout cp1251 → client does `sys.stdout.reconfigure(utf-8)`.
