# Карта эндпоинтов v3 (54 пути, сверено с OpenAPI)

Полный список путей API с методами и назначением. Читай, когда ищешь нужный эндпоинт или проверяешь, существует ли он в v3. Авторитетный источник — `${HOME}/_heygen_openapi.json`.

## Оглавление

- Complete v3 endpoint map (54 paths, OpenAPI-verified)
- Videos
- Cinematic / HyperFrames (prompt-driven)
- Avatars
- Voices
- Lipsync
- Video Translation
- Video Agent (prompt-to-video)
- Assets
- Audio / Brand
- Webhooks
- Account
- Legacy (v1/v2 — sunset 2026-10-31)

---

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

