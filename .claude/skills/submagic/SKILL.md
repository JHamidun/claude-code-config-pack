---
name: submagic
description: "Submagic API: ИИ-субтитры, Magic Brolls/Zooms, Magic Clips (YouTube в нарезку). Триггеры: «субтитры», «нарежь на клипы»."
---

# your subtitle API Skill

## Overview

SubtitleService is an AI video platform for short-form content. The REST API (`https://api.submagic.co/v1`) covers caption generation, automatic B-roll insertion, magic zooms, hook titles, silence removal, audio cleanup, Magic Clips (auto-cut from YouTube), social publishing (YouTube/TikTok/Instagram), and user media library.

**Docs:** https://docs.submagic.co — full source at `${HOME}/_submagic_docs.md` (5750 lines, openapi at /api-reference/openapi.json).

## Auth

```
Header: x-api-key: sk-...
```

NOT `Authorization: Bearer`. Key starts with `sk-`, lives in `~/.claude/.credentials.master.env` as `SUBMAGIC_API_KEY`.

Quick test:
```bash
curl -H "x-api-key: sk-..." https://api.submagic.co/v1/templates
```

## Endpoints reference

| Method | Path | Rate | What it does |
|---|---|---|---|
| POST | `/v1/projects` | 30/h | Create project from **public videoUrl** |
| POST | `/v1/projects/upload` | 30/h | Create project from **multipart file** (≤2GB, ≤2h) |
| GET | `/v1/projects/{id}` | 100/h | Poll status + download URLs |
| PATCH | `/v1/projects/{id}` | 100/h | Update settings (re-export needed after) |
| POST | `/v1/projects/{id}/export` | n/a | Trigger rendering (custom fps/width/height) |
| POST | `/v1/projects/{id}/publish` | n/a | Publish to YT/TikTok/Instagram |
| POST | `/v1/projects/magic-clips` | 500/h | YouTube URL → auto-cut multi-clip project |
| POST | `/v1/projects/magic-clips/upload` | 500/h | Upload file → auto multi-clip |
| GET | `/v1/projects/published` | n/a | List your published posts (cursor pagination) |
| GET | `/v1/user-media` | n/a | List your media library |
| POST | `/v1/user-media` | n/a | Add media from URL |
| POST | `/v1/user-media/upload` | n/a | Upload media file |
| GET | `/v1/templates` | 1000/h | List caption templates (44 styles) |
| GET | `/v1/languages` | 1000/h | List supported languages (50+) |
| GET | `/v1/hook-title-templates` | n/a | List hook-title styles |
| GET | `/health` | n/a | Health probe (no auth) |

## Create Project — full parameter reference

```bash
POST /v1/projects
Body (application/json):
{
  "title": "1-100 chars",                    # REQUIRED
  "language": "en",                          # REQUIRED. Codes from /v1/languages, or "auto"
  "videoUrl": "https://...",                 # REQUIRED. Public direct URL. NO social media URLs.
  "templateName": "Hormozi 2",               # OPTIONAL. From /v1/templates. Default "Sara".
  "userThemeId": "uuid",                     # OPTIONAL. Your custom theme (mutually excl. with templateName)
  "presetId": "uuid",                        # OPTIONAL. Saved preset. Cannot combine with templateName/userThemeId/hookTitle/music/items/magicZooms/magicBrolls/magicBrollsPercentage/removeSilencePace/removeBadTakes
  "aiEditTemplate": "kelly|karl|ella",       # OPTIONAL. Full AI edit. Mutually excl. with everything except title/language/videoUrl/webhookUrl/dictionary
  "magicZooms": true,                        # Default false. Auto zoom-in on emphasis
  "magicBrolls": true,                       # Default false. Auto B-roll insertion
  "magicBrollsPercentage": 75,               # 0-100. Default 50. Only if magicBrolls=true
  "removeSilencePace": "natural|fast|extra-fast",  # OPTIONAL
                                             #   extra-fast: 0.1-0.2s silence removed
                                             #   fast: 0.2-0.6s
                                             #   natural: 0.6+s
  "removeBadTakes": true,                    # Default false. AI removes bad takes/silence
  "cleanAudio": true,                        # Default false. Background noise cleanup
  "hideCaptions": false,                     # Default false. Hide captions from export
  "hookTitle": true,                         # OR object:
                                             #   { "text":"1-100 chars",
                                             #     "template":"tiktok" (from /v1/hook-title-templates),
                                             #     "top": 0-80 (default 50),
                                             #     "size": 0-80 (default 30) }
  "music": {                                 # Background music (full project duration)
    "userMediaId": "uuid",                   # Must be AUDIO type from /v1/user-media
    "volume": 1-100,
    "startFromTime": 0,
    "fade": true
  },
  "dictionary": ["term1", "term2"],          # Up to 100 terms, 50 chars each. Improves transcription
  "items": [                                 # Custom B-roll insertions (no time overlap!)
    {
      "type": "user-media",                  # From your library
      "startTime": 5, "endTime": 10,
      "userMediaId": "uuid",
      "layout": "cover|contain|rounded|square|split-50-50|split-35-65|split-50-50-bordered|split-35-65-bordered|pip-top-right|pip-bottom-right"  # Image: cover/contain/rounded/square only
    },
    {
      "type": "ai-broll",                    # AI-generated cutaway
      "startTime": 15, "endTime": 21,        # endTime - startTime ≤ 12 sec
      "prompt": "1-2500 chars description",
      "layout": "..."                        # same set as user-media video
    }
  ],
  "webhookUrl": "https://..."                # OPTIONAL HTTPS for completion notification
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "status": "processing|transcribing|exporting|completed|failed",
  "title": "...",
  "language": "...",
  "templateName": "...",
  "magicZooms": true, "magicBrolls": true, "magicBrollsPercentage": 75,
  "removeSilencePace": "...", "removeBadTakes": ..., "cleanAudio": ...,
  "createdAt": "ISO 8601",
  "updatedAt": "ISO 8601"
}
```

## Status polling — GET /v1/projects/{id}

Response when `status: completed`:
```json
{
  "id": "uuid", "title": "...", "language": "...",
  "status": "completed",
  "downloadUrl": "https://app.submagic.co/api/file/download?path=...",
  "directUrl": "https://...cloudfront.net/api/.../video.mp4",
  "previewUrl": "https://app.submagic.co/view/{projectId}",
  "transcriptionStatus": "COMPLETED",
  "magicZooms": true, ...
}
```

Statuses:
- `processing` — download/setup phase
- `transcribing` — STT in progress
- `exporting` — rendering
- `completed` — `downloadUrl` available
- `failed` — see `failureReason`

## Webhook payload

```json
{
  "projectId": "uuid",
  "status": "completed",
  "downloadUrl": "https://app.submagic.co/api/file/download?...",
  "directUrl": "https://...cloudfront.net/...",
  "timestamp": "2024-01-15T10:45:00.000Z"
}
```

Magic Clips webhook has extra `clips: [{ clipId, downloadUrl, ... }]`.

## Caption templates (44 как на 2026-05-16)

`Matt, Jess, Jack, Nick, Laura, Kelly 2, Claire, Michael, Caleb, Kendrick, Lewis, Doug, Carlos, Luke, Leila, Mark, Sara (default), Daniel, Dan 2, Hormozi 4, Dan, Devin, Tayo, Ella, Tracy, Hormozi 1, Hormozi 2, Hormozi 3, Hormozi 5, Jason, William, Leon, Ali, Beast, Bob, Maya, Karl, Iman, Umi, David, Noah, Gstaad, Malta, Nema, seth`

Pull fresh list: `GET /v1/templates` → `{"templates":[...]}`

For YourName AI educational/business shorts: **Hormozi 2** (default), **Beast** (for entertainment), **Sara** (clean).

## AI Edit Templates

Pass `aiEditTemplate: "kelly|karl|ella"` for full hands-off AI edit (auto scene splits + B-roll + music + styling). Mutually exclusive with everything except title/language/videoUrl/webhookUrl/dictionary.

- `kelly` — minimal, design
- `karl` — effective, modern
- `ella` — dynamic, bold

## Magic Clips — YouTube auto-cut

```bash
POST /v1/projects/magic-clips
{
  "title": "...",
  "language": "en",
  "youtubeUrl": "https://www.youtube.com/watch?v=...",
  "templateName": "Hormozi 2",                # optional
  "minClipLength": 15, "maxClipLength": 60,   # 15-300 sec range
  "faceTracking": true,                       # default true
  "webhookUrl": "https://..."
}
```

Webhook returns `clips: [...]` array with each clip's downloadUrl. **1 Magic Clips credit per project**, not API credit.

## Publish to social — POST /v1/projects/{id}/publish

Requires `downloadUrl` (project exported) + connected accounts in https://app.submagic.co/publishing.

```json
{
  "scheduledAt": "ISO 8601",                 # omit for immediate
  "platforms": {
    "youtube": { "title": "≤100ch", "description": "...", "tags": ["..."], "firstComment": "..." },
    "tiktok": { "caption": "..." },
    "instagram": { "format": "reel|story", "caption": "...", "firstComment": "..." }
  }
}
```

## Custom export — POST /v1/projects/{id}/export

After PATCH update, re-trigger export:
```json
{
  "fps": 30,                                  # 1-60. Default from source.
  "width": 1080, "height": 1920,              # 100-4000. Default from source.
  "webhookUrl": "https://..."
}
```

## User Media library

Upload reusable assets (logos, music, signature B-roll):
- `POST /v1/user-media` (URL) or `/v1/user-media/upload` (file)
- `GET /v1/user-media` to list with UUIDs
- Use UUIDs in `items.userMediaId` or `music.userMediaId`

Media types: `VIDEO`, `IMAGE`, `AUDIO`.

## Rate limits

| Tier | Limit | Endpoints |
|---|---|---|
| Lightweight | 1000/h | `/templates`, `/languages` |
| GET | 100/h | `/projects/{id}` |
| POST (heavy) | 30/h | `/projects`, `/projects/upload`, Magic Clips |

Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

429 response:
```json
{ "error": "RATE_LIMIT_EXCEEDED", "message": "...", "retryAfter": 30 }
```

Also sent as `Retry-After:` header. Use exponential backoff.

## Error codes

- `VALIDATION_ERROR` (400) — body details in `details` array
- `UNAUTHORIZED` (401) — bad key
- `NOT_FOUND` (404) — wrong UUID or wrong endpoint
- `RATE_LIMIT_EXCEEDED` (429) — `retryAfter`
- `INTERNAL_SERVER_ERROR` (500)

Common 400s:
- Preset combined with `templateName`/`magicZooms`/etc → conflict
- `aiEditTemplate` combined with anything beyond whitelist
- `videoUrl` from social media (use direct CDN)
- Invalid `hookTitle.template` name

## Idiomatic Python client

```python
import os, time, requests
from pathlib import Path

KEY = os.environ['SUBMAGIC_API_KEY']
BASE = 'https://api.submagic.co/v1'
H = {'x-api-key': KEY, 'Content-Type': 'application/json'}


def create_from_url(video_url: str, title: str, **opts) -> dict:
    """Create project. Returns {id, status, ...}."""
    body = {
        'title': title,
        'language': opts.pop('language', 'auto'),
        'videoUrl': video_url,
        'templateName': opts.pop('templateName', 'Hormozi 2'),
        'magicZooms': opts.pop('magicZooms', True),
        'magicBrolls': opts.pop('magicBrolls', True),
        'magicBrollsPercentage': opts.pop('magicBrollsPercentage', 50),
        **opts,
    }
    r = requests.post(f'{BASE}/projects', headers=H, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def get_project(pid: str) -> dict:
    r = requests.get(f'{BASE}/projects/{pid}', headers={'x-api-key': KEY}, timeout=30)
    r.raise_for_status()
    return r.json()


def wait_for_completion(pid: str, max_min: int = 15, poll_s: int = 20) -> dict:
    """Poll until completed or failed. Returns final project dict."""
    deadline = time.time() + max_min * 60
    while time.time() < deadline:
        p = get_project(pid)
        st = p.get('status')
        if st == 'completed':
            return p
        if st == 'failed':
            raise RuntimeError(f'Project {pid} failed: {p.get("failureReason")}')
        time.sleep(poll_s)
    raise TimeoutError(f'Project {pid} not done in {max_min} min')


def download(url: str, dest: Path) -> Path:
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(64 * 1024):
            f.write(chunk)
    return dest


# Magic Clips
def youtube_to_clips(yt_url: str, title: str, **opts) -> dict:
    body = {
        'title': title,
        'language': opts.pop('language', 'auto'),
        'youtubeUrl': yt_url,
        'templateName': opts.pop('templateName', 'Hormozi 2'),
        'minClipLength': opts.pop('minClipLength', 15),
        'maxClipLength': opts.pop('maxClipLength', 60),
        'faceTracking': opts.pop('faceTracking', True),
        **opts,
    }
    r = requests.post(f'{BASE}/projects/magic-clips', headers=H, json=body, timeout=30)
    r.raise_for_status()
    return r.json()
```

## Recipe: HeyGen avatar → SubMagic → final

```python
# 1. Generate HeyGen video (returns temporary signed URL)
heygen_url = heygen_generate(script_text, avatar_id, voice_id)  # mp4

# 2. Pass that URL directly to SubMagic (no re-upload needed)
proj = create_from_url(
    video_url=heygen_url,
    title='Pivot в бизнес-модели',
    language='ru',
    templateName='Hormozi 2',
    magicZooms=True,
    magicBrolls=True,
    magicBrollsPercentage=50,           # user wants 50%
    removeSilencePace='natural',
    cleanAudio=True,
    hookTitle={'text': 'Как спасти бизнес от краха?', 'template': 'tiktok'},
    dictionary=['YourFirstName', 'pivot', 'Custdev', 'Agile', 'Scrum'],
)

# 3. Wait + download
final = wait_for_completion(proj['id'])
download(final['downloadUrl'], Path(f'{proj["id"]}.mp4'))
```

## Recipe: full webinar → Magic Clips → multi-Shorts

```python
result = youtube_to_clips(
    yt_url='https://www.youtube.com/watch?v=...',  # YourFirstName full webinar
    title='Webinar Magic Clips',
    language='ru',
    templateName='Hormozi 2',
    minClipLength=20, maxClipLength=45,
)
# Wait webhook or poll. clips[] returned via webhookUrl.
```

## Gotchas

- **`Authorization: Bearer` → 404/UNAUTHORIZED.** Must be `x-api-key:`.
- **`videoUrl` cannot be social media URL** (YouTube/TikTok/Instagram) — use direct CDN/Drive direct link. For YouTube use Magic Clips endpoint instead.
- **`presetId` cannot combine** with templateName/magicZooms/magicBrolls/etc.
- **`aiEditTemplate`** restricts you to title/language/videoUrl/webhookUrl/dictionary — everything else ignored.
- **Items cannot overlap** in time. AI-broll item endTime - startTime ≤ 12 sec.
- **Magic Clips uses Magic Clips credits**, not API credits (1 credit/project).
- **Webhook is HTTPS only** + must respond 2xx within ~10s.
- **Status flow:** `processing → transcribing → exporting → completed`. `transcriptionStatus` independent: `PROCESSING/COMPLETED/FAILED`.
- After PATCH (UpdateProject) — call `POST /export` again to render new version.

## MCP server option

SubtitleService provides an MCP server: https://docs.submagic.co/mcp-server.md — Claude Code/Desktop/Cursor compatible. Not configured in `~/.claude/mcp.json` by default; can add for natural-language flows.

## Local references

- Full docs dump: `${HOME}/_submagic_docs.md` (5750 lines)
- OpenAPI spec: https://docs.submagic.co/api-reference/openapi.json
- Pipeline script: `${HOME}/_factory_87_v4_pipeline.py`
- Memory: `~/.claude/projects/C--Users-youruser/memory/feedback_tg_channel.md` for related context

## Use cases mapped

| Goal | API |
|---|---|
| AI captions on existing mp4 | POST /v1/projects/upload + templateName |
| HeyGen avatar → captioned + B-roll | POST /v1/projects with HeyGen URL + magicZooms/magicBrolls |
| YouTube webinar → 5-10 viral shorts | POST /v1/projects/magic-clips |
| Custom B-roll cutaways | POST /v1/projects with `items: [{type:"ai-broll", prompt:..}]` |
| Add hook title overlay | `hookTitle: {text, template, top, size}` |
| Replace music | PATCH /v1/projects/{id} + `music.userMediaId` → POST /export |
| Multi-platform publish | POST /v1/projects/{id}/publish |
