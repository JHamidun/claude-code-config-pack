# DELIVERABLE 1 — SKILL_DRAFT

```markdown
---
name: higgsfield
description: >
  Generate images and videos via Higgsfield AI CLI. Covers all models (Seedance,
  Veo, Kling, Nano Banana, GPT Image 2, Soul, Marketing Studio, Virality
  Predictor). Routes to correct model from brief, assembles CLI flags, executes
  with --wait, returns media URL.
triggers:
  - "higgsfield"
  - "seedance"
  - "nano banana"
  - "soul character"
  - "virality predictor"
  - "marketing studio video"
  - "ugc ad"
  - "generate cinematic"
  - "сделай видео higgsfield"
  - "сгенерируй через higgsfield"
---

# Higgsfield Skill

## Bootstrap / Auth

```bash
# Install (once per machine)
curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh

# Auth (once; persists to ~/.config/higgsfield/credentials.json)
higgsfield auth login

# Verify
higgsfield account status
# Expects: "<email> — <plan> plan, <N> credits"

# Live model catalog (always check before using unfamiliar jst)
higgsfield model list --json
# Full schema for one model:
higgsfield model get <job_set_type> --json | jq '{aspect_ratios,durations,parameters,medias}'
```

## Core Pattern

```bash
higgsfield generate create <job_set_type> --prompt "..." [media flags] [param flags] --wait
# Returns: result URL on stdout
# Machine output: add --json
# Slow models: --wait-timeout 30m --wait-interval 5s
```

---

## Model Decision Tree

### IMAGE — pick by use case

| Brief | job_set_type | Key flags |
|-------|-------------|-----------|
| Default high-fi, text/UI/packaging | `gpt_image_2` | `--aspect_ratio --resolution 2k` |
| Character/cartoon/animated | `nano_banana_2` | `--image ./ref.png` (repeatable, up to 8) |
| Same + harder brief | `nano_banana_pro` | same |
| Aesthetic UGC/fashion/lifestyle + face | `text2image_soul_v2` | `--soul-id <ref_id> --quality 2k` |
| Cinematic still + face | `soul_cinematic` | `--soul-id <ref_id> --quality 2k` |
| Character persona, no photo needed | `soul_cast` | prompt only — NO media flags |
| Environment/location, no people | `soul_location` | prompt only — NO quality selector |
| Vector illust / face-anchored scene edit | `seedream_v4_5` | `--image ./face.png` |
| Same, faster | `seedream_v5_lite` | `--image ./face.png` |
| Fast draft / LoRA stylization | `z_image` | prompt only — NO media flags |
| Style transfer / anime / typography | `flux_kontext_max` | `--image ./ref.png` |
| Precise prompt adherence alt | `flux_2` | `--image` optional |
| Branded image ad + avatar + product | `marketing_studio_image` | `--aspect_ratio --resolution 2k` |
| Open brief, let Higgsfield pick | `auto` | prompt only |

### VIDEO — pick by use case

| Brief | job_set_type | Key flags |
|-------|-------------|-----------|
| Default all-purpose, cinematic, multi-shot | `seedance_2_0` | `--start-image --duration 4-15 --aspect_ratio` |
| Seedance 2.0 + lipsync audio | `seedance_2_0` | `--start-image --audio ./voice.mp3 --duration 8` |
| Budget, single-plane, cheaper | `kling3_0` | `--start-image --end-image --duration 3-15 --sound on\|off` |
| Budget explicit (user asked) | `seedance_1_5_pro` | `--start-image --duration` |
| All ad/commercial/branded video | `marketing_studio_video` | see Marketing Studio section |
| Highest cinema fidelity | `cinema_studio_video_3_0` | `--prompt --aspect_ratio --duration` |
| Ultra-realistic, constrained | `veo3_1` | `--start-image --aspect_ratio 16:9\|9:16 --duration 4\|6\|8 --quality` |
| Veo batch/volume | `veo3_1_lite` | same constraints as veo3_1 |
| Physics-strong, budget | `minimax_hailuo` | `--prompt --aspect_ratio --duration` |
| Audio-sync stylized | `wan2_7` | `--prompt --image --duration` |
| Experimental artistic | `wan2_6` | prompt only in many configs |
| Video analysis / hook scoring | `brain_activity` | `--video ./ad.mp4` — NO prompt |

---

## Media Flags Quick Reference

```
--image          role: image          (path or UUID; repeatable for multi-ref)
--start-image    role: start_image    (first frame anchor)
--end-image      role: end_image      (last frame anchor)
--video          role: video          (video reference or brain_activity input)
--audio          role: audio          (Seedance 2.0 lipsync — NOT --generate-audio)
```

Prompt-only models (NO media flags): `z_image`, `soul_cast`, `soul_location`, some `wan2_6` configs.

UUID sources: `higgsfield upload create <file>` returns upload UUID. Previous job IDs also accepted.

---

## Examples

```bash
# Image — default
higgsfield generate create gpt_image_2 \
  --prompt "product label on matte black bottle, studio light" \
  --aspect_ratio 1:1 --resolution 2k --wait

# Image — multi-ref character
higgsfield generate create nano_banana_2 \
  --prompt "anime hero in cyberpunk city" \
  --image ./style_ref.png --image ./character.png --wait

# Video — image-to-video default
higgsfield generate create seedance_2_0 \
  --prompt "camera slowly dollies in, shallow depth of field" \
  --start-image ./hero.png --duration 8 --aspect_ratio 16:9 --wait

# Video — lipsync
higgsfield generate create seedance_2_0 \
  --prompt "presenter speaking to camera, professional studio" \
  --start-image ./headshot.png --audio ./voiceover.mp3 --duration 10 --wait

# Analysis — Virality Predictor
higgsfield generate create brain_activity --video ./creative.mp4 --wait
# Output: score 0-100, peak hook second, sustain %, region breakdown,
#         Open report URL: https://<app>/apps/virality-predictor?resultJobId=<id>
```

---

## Soul ID (Face Training)

Requires: Basic+ paid plan. Training time: 15-45 min. Photos: 5-20 (8-12 optimal).
Photo requirements: single person, clear eyes, no sunglasses, varied angles/lighting/expressions.

```bash
# Train for image generation
higgsfield soul-id create --name "founder" --soul-2 \
  --image photo1.jpg --image photo2.jpg --image photo3.jpg ...

# Train for cinematic/video
higgsfield soul-id create --name "founder" --soul-cinematic \
  --image photo1.jpg ...

# Poll training (default 30m timeout)
higgsfield soul-id wait <id>

# List trained souls
higgsfield soul-id list

# Use in generation
higgsfield generate create text2image_soul_v2 \
  --prompt "fashion editorial, golden hour rooftop" \
  --soul-id <reference_id> --quality 2k --aspect_ratio 9:16 --wait
```

Soul quality: `--quality 1.5k` = 720p, `--quality 2k` = 1080p.
`soul_location` has no quality selector — dimensions fixed by aspect ratio.

---

## Marketing Studio

### Product import

```bash
# URL import (auto-polls ~90s)
PRODUCT_ID=$(higgsfield marketing-studio products fetch \
  --url https://shop.example.com/sneakers --wait --json | jq -r .id)

# Manual
higgsfield marketing-studio products create \
  --title "AeroRun Pro" --description "..." --image <upload_id>
```

### Avatar selection

```bash
higgsfield marketing-studio avatars list --json | jq '.[] | {id, name, gender}'

# Custom avatar (BOTH --image AND --image-url required)
UPLOAD=$(higgsfield upload create founder.png --json)
UPLOAD_ID=$(echo $UPLOAD | jq -r .id)
UPLOAD_URL=$(echo $UPLOAD | jq -r .url)
higgsfield marketing-studio avatars create \
  --name "Founder" --image $UPLOAD_ID --image-url $UPLOAD_URL
```

### Generate ad video

```bash
# Write JSON array files (mandatory format)
printf '[{"id":"<avatar_id>","type":"preset"}]' > /tmp/avatars.json
printf '["<product_id>"]' > /tmp/products.json

higgsfield generate create marketing_studio_video \
  --prompt "unboxing reveal, warm home setting" \
  --avatars @/tmp/avatars.json \
  --product_ids @/tmp/products.json \
  --mode ugc_unboxing \
  --hook_id <hook_id> \        # UGC modes only
  --setting_id <setting_id> \  # UGC modes only
  --duration 15 --resolution 720p --aspect_ratio 9:16 \
  --generate-audio true --wait

# Click-to-Ad shortcut (URL-driven)
higgsfield generate create marketing_studio_video \
  --url https://shop.example.com/sneakers \
  --mode ugc --duration 15 --aspect_ratio 9:16 --wait
```

Mode → hook/setting allowed: `ugc`, `ugc_how_to`, `ugc_unboxing`, `product_review`, `ugc_virtual_try_on`.
Mode → hook/setting FORBIDDEN: `product_showcase`, `tv_spot`, `wild_card`, `virtual_try_on`.
Ad reference (inspiration video) and hook/setting are MUTUALLY EXCLUSIVE — never pass both.

### Hooks / Settings discovery

```bash
higgsfield marketing-studio hooks list --search "sale" --json
higgsfield marketing-studio settings list --search "office" --json
```

---

## Errors and Gotchas

| Error | Cause | Fix |
|-------|-------|-----|
| `unknown model "..."` | Wrong jst string | Run `higgsfield model list` |
| `Session expired` / `Not authenticated` | Stale creds | `higgsfield auth login` |
| `Unknown params: hook_id` | hook_id on non-UGC mode | Drop hook_id/setting_id |
| `Model does not accept media inputs` | Media flag on prompt-only model | Remove all --image/--video flags |
| `Minimum Basic plan required` | Soul training on free tier | Upgrade plan |
| `nsfw` / `ip_detected` terminal status | Safety block | Rephrase, avoid real faces/trademarks |
| CloudFlare captcha HTML in response | Anti-bot triggered | Wait 30s, retry |
| HTTP 429 | Rate limit | Back off before retry |
| `Note: adjustments applied` | AR/duration clamped | Non-fatal; check returned value |

Cost estimate without submitting: `higgsfield generate cost <jst> [same flags]`
```

---

# DELIVERABLE 2 — RAW_API_AND_REPLICATION

## (a) Direct API Access — What We Know

### Base URL

`https://api.higgsfield.ai` — documented in CLI source/CLAUDE.md. The CLAUDE.md forbids direct curl explicitly: "Do not call api.higgsfield.ai directly with curl. The CLI handles auth, retries, polling, schema validation, and auto-uploads."

### Auth Token Location

`~/.config/higgsfield/credentials.json` — device-flow OAuth result. Token format: **unknown** (not documented in reverse-engineered files). Likely a Bearer JWT injected as `Authorization: Bearer <token>`. Must be inferred by inspecting the file after `higgsfield auth login`.

### Inferred Endpoint Mapping

Mark: (D) = directly documented, (I) = inferred from CLI noun/verb pattern.

| CLI command | Inferred endpoint | Method | Notes |
|-------------|------------------|--------|-------|
| `model list` | `GET /v1/models` or `/v1/jobs/types` | GET | (I) returns jst catalog |
| `model get <jst>` | `GET /v1/models/<jst>` | GET | (I) schema: params, medias, aspect_ratios |
| `generate create <jst>` | `POST /v1/generations` | POST | (I) body: {job_set_type, prompt, parameters, medias} |
| `generate get <id>` | `GET /v1/generations/<id>` | GET | (I) |
| `generate list` | `GET /v1/generations` | GET | (I) |
| `generate wait <id>` | poll `GET /v1/generations/<id>` | GET | (I) CLI polls on status field |
| `upload create` | `POST /v1/uploads` (multipart) | POST | (I) returns {id, url} where url=CloudFront |
| `soul-id create` | `POST /v1/souls` or `/v1/trainings` | POST | (I) async job, poll until completed |
| `soul-id list/get` | `GET /v1/souls` / `GET /v1/souls/<id>` | GET | (I) |
| `marketing-studio products fetch` | `POST /v1/marketing/products/fetch` | POST | (I) async, polls ~90s |
| `marketing-studio products create` | `POST /v1/marketing/products` | POST | (I) sync |
| `marketing-studio products list` | `GET /v1/marketing/products` | GET | (I) |
| `marketing-studio avatars list` | `GET /v1/marketing/avatars` | GET | (I) |
| `marketing-studio avatars create` | `POST /v1/marketing/avatars` | POST | (I) body: {name, image_id, image_url} |
| `marketing-studio hooks list` | `GET /v1/marketing/hooks` | GET | (I) cursor-paginated |
| `marketing-studio settings list` | `GET /v1/marketing/settings` | GET | (I) |
| `marketing-studio ad-references create` | `POST /v1/marketing/ad-references` | POST | (I) no built-in wait |
| `marketing-studio ad-references get <id>` | `GET /v1/marketing/ad-references/<id>` | GET | (I) poll for status:completed |
| `marketing-studio brand-kits fetch` | `POST /v1/marketing/brand-kits/fetch` | POST | (I) async, polls |
| `marketing-studio brand-kits list/get` | `GET /v1/marketing/brand-kits[/<id>]` | GET | (I) cursor: created_at unix ts |
| `marketing-studio ad-formats list` | `GET /v1/marketing/ad-formats` | GET | (I) |
| `marketing-studio dtc-ads generate` | `POST /v1/marketing/dtc-ads` | POST | (I) |
| `marketing-studio webproducts fetch` | `POST /v1/marketing/webproducts/fetch` | POST | (I) App Store URLs route here |

### Known Request/Response Shape (from reverse-engineering)

**Generation create body (inferred):**
```json
{
  "job_set_type": "seedance_2_0",
  "prompt": "...",
  "parameters": {
    "aspect_ratio": "16:9",
    "duration": 8
  },
  "medias": [
    {"role": "start_image", "value": "<upload_uuid>"},
    {"role": "audio", "value": "<upload_uuid>"}
  ]
}
```

**Job terminal statuses (documented):** `completed`, `failed`, `nsfw`, `ip_detected`

**Generation response includes `adjustments` field** for non-fatal coercions (e.g. aspect_ratio clamped).

**Virality Predictor job params field** contains: `brain_example_url`, `your-serverMapBinaryUrl`, `your-serverMapUrl` (implementation detail, not for normal output), plus Open report URL.

**Product fetch response:** `{id, status, fail_reason}` — dedupes by URL, reuses existing non-failed entity.

**Ad references:** `{id, status, source_platform, video_input_id, job_id, video_s3_url, video_thumbnail_url, avatar_id, product_id}` — no built-in wait, manual poll.

**Brand kits:** `{id, status (queued|in_progress|completed|failed|canceled), data: {brand_name, logo, tagline, business_overview, industry}}` — paginated with cursor (null when done).

**Marketing Studio avatars create** requires both `image` (upload_id) AND `image_url` (CloudFront URL from upload response) — API-level requirement, not just CLI convention.

**product_ids and avatars in generation:** JSON arrays, not scalar. Avatar shape: `{"id": "<id>", "type": "preset"|"custom"}`. Soul Character as custom avatar: `{"id": "<reference_id>", "type": "custom"}`.

---

## (b) Capability Mapping: Higgsfield → Our Stack

### What Higgsfield "AI Employees" / Supercomputer Offers vs Our Stack

| Higgsfield Capability | What It Does | Our Stack Equivalent | Gap / Missing |
|----------------------|--------------|---------------------|---------------|
| **Model routing (Auto jst)** | Server-side picks best image model from prompt | `orchestrator` agent + model-catalog decision tree in SKILL.md | We must implement routing client-side; no server-side Auto for video |
| **Soul Character training** | Fine-tunes face identity from 5-20 photos → reference_id | Nothing direct. Nearest: `heygen` (HeyGen avatar creation) or `did` (D-ID) | No LoRA/IP-Adapter training pipeline in our stack. Gap: face-consistent generation across models |
| **Product Photoshoot (prompt enhancer)** | mode-specific photography vocabulary injected before gpt_image_2 | `nano-banana-pro` skill + custom Claude prompt-enhancement layer per mode | We lack the 10-mode template library. Build: system prompt templates per mode (product_shot, lifestyle_scene, etc.) + call OpenAI gpt-image-2 or Gemini |
| **Marketplace Cards (A+ modules)** | Asset-type templates + nano_banana_2 jobs orchestrated in parallel | No direct equivalent. Could orchestrate via `orchestrator` agent dispatching parallel `image-generation` subagents per asset type | Gap: we lack the 13 asset-type compliance templates (main_image specs differ from aplus_hero_banner) |
| **Marketing Studio Video (UGC ads)** | Avatar + product + hook/setting + Seedance → branded ad video | `heygen` skill (avatar video) + `video-generation` skill (Seedance via Runway) + `tg-post`/`crosspost` for distribution | Gap: no hook/setting library, no product RAG layer, no avatar+product composition in one call |
| **Marketing Studio Image** | Branded static ad with avatar+product, RAG | `image-generation` skill + manual reference injection | Gap: no avatar/product registry with RAG retrieval |
| **Brand Kit from URL** | Scrapes website → brand identity object (colors, fonts, logo, tone) | `firecrawl:firecrawl-scrape` + Claude Vision for color/font extraction + save to memory | Feasible now. Missing: structured brand kit storage + auto-injection into generation prompts |
| **Ad References (inspiration video)** | Upload reference video → bind to avatar+product → use in generation | `video-editor` skill (frame extraction) + Claude Vision for style description + inject into prompt | Gap: no video-style reference binding pipeline; must build as a skill |
| **DTC Ads Engine** | format_id template + brand kit + media → structured ad image | `image-generation` skill + format template library + brand kit context injection | Gap: we have no ad format template library. Build as a JSON/Jinja2 template store |
| **Virality Predictor** | Proprietary neuroscience attention model → hook score + brain region breakdown | No equivalent. Nearest: Claude Vision frame-by-frame analysis with scoring prompt | Gap: no attention heatmap model. Approximation: Claude Vision on keyframes (every 2s) + scoring rubric prompt → 0-100 output. Loses region-level accuracy |
| **Hooks library** | Curated opening-angle text templates, tagged by category | None. Build: CSV/JSON of 50+ hook templates tagged by intent | Gap: easily built, not yet built |
| **Settings library** | Curated scene/environment context blocks | None. Build same way as hooks | Same |
| **Job polling / --wait** | CLI blocks and prints URL on terminal status | `condition-based-waiting` skill + Bash poll loop in any skill | Covered — we already have polling patterns |
| **Async product import (URL fetch)** | Background scrape+import, dedupes by URL | `firecrawl:firecrawl-scrape` + `pgvector-rag` or memory for dedup | Covered with existing tools. Need to wire together |
| **Upload pre-flight (auto-upload)** | CLI auto-uploads local paths before job submission | Manual: `higgsfield upload create <file>` or direct to our own CDN/S3 | For our own stack without Higgsfield: upload to your-server/Cloudflare R2 |
| **Soul → Marketing Studio custom avatar** | Soul reference_id used as custom avatar type in ad generation | `heygen` skill (HeyGen custom avatar) | Gap: no face-consistent custom avatar that plugs into our own video pipeline |
| **Click-to-Ad (URL → ad video in 2 cmds)** | products fetch --url + generate create --url → full ad | `firecrawl:firecrawl-scrape` + `video-generation` + `heygen` orchestrated | Feasible via `orchestrator` agent. Not yet wired |
| **Webproduct (App Store import)** | Separate endpoint for App Store / web page products | iTunes API scrape (public) or Firecrawl on App Store page | Feasible. Route by URL pattern (apps.apple.com → iTunes lookup API) |
| **Scheduled ad generation** | Not directly offered; Higgsfield is per-call | `/schedule` skill + CronCreate for recurring ad generation | We have this already |
| **Multi-agent orchestration** | Not offered; Higgsfield is model-level, not agent-level | Our `orchestrator` agent + `dispatching-parallel-agents` superpowers skill | We exceed Higgsfield here |
| **Memory / context across sessions** | Not offered | `graph-memory` MCP + `memory/` files + `pgvector-rag` | We exceed Higgsfield here |
| **Skill/command system** | Not offered | Our 172 skills + 111 commands | We exceed Higgsfield here |
| **MCP connectors** | Not offered | 19 local + 10 cloud MCP servers | We exceed Higgsfield here |

### What Is Missing to Build Full Higgsfield Capability Without Their API

| Gap | Effort | How to Fill |
|-----|--------|------------|
| Face-consistent generation (Soul substitute) | High | InstantID or IP-Adapter FaceID on HuggingFace Spaces / fal.ai; or HeyGen custom avatar API; or Replicate Flux LoRA fine-tune |
| Product photoshoot prompt enhancer (10 modes) | Low | Build `higgsfield-product-photoshoot` skill: 10 system prompt templates per mode + call gpt-image-2 via OpenAI API directly |
| Marketplace card asset templates (13 types) | Medium | Build compliance-aware system prompts per asset type + orchestrate parallel `image-generation` subagents |
| Hook/Setting library | Low | CSV/JSON of 50+ hook opening texts + 20+ setting descriptions; inject as prompt prefix |
| Brand kit storage + injection | Low | Store as JSON in `memory/` or `pgvector-rag`; inject into generation system prompt |
| Virality Predictor substitute | Medium | Claude Vision on video keyframes (ffmpeg extract every 2s → base64 → Vision API) + structured scoring rubric prompt returning 0-100 + hook/sustain assessment |
| Ad reference style binding | Medium | Extract keyframes via `video-editor` → Claude Vision description → store as style context → inject into generation prompt |
| Product registry with RAG | Medium | `pgvector-rag` or Pinecone skill; embed product images+descriptions; retrieve at generation time |
| DTC ad format templates | Low | JSON/Handlebars templates per format type (headline, bullet-points, us-vs-them); inject layout instructions into image generation prompt |
| Seedance 2.0 direct access | None needed | Already covered: `video-generation` skill routes to Seedance 2.0 via Runway Unlimited |
| Veo 3.1 direct access | None needed | Already covered: `video-generation` skill covers Veo via `veo-direct` reference |
| Nano Banana / gpt_image_2 direct | None needed | `nano-banana-pro` skill = Nano Banana; `image-generation` for gpt_image_2 via local gateway |

### Priority Build Order (highest ROI first)

1. **Install Higgsfield CLI** and integrate as a skill (SKILL_DRAFT above) — gives full access to all 30+ models immediately via one binary
2. **Product photoshoot prompt enhancer** — 10 templates, low effort, high output quality improvement
3. **Hook/Setting library** — JSON file, 2 hours work, unlocks full Marketing Studio UGC workflow
4. **Brand kit builder** — wire Firecrawl scrape + Claude Vision + memory storage
5. **Virality Predictor substitute** — Claude Vision frame analysis; good enough for 80% of use cases
6. **Soul substitute via fal.ai/Replicate** — only needed if Higgsfield account plan cost is prohibitive or face training is needed offline