---
name: gamma
description: "Generate presentations, documents, social posts and webpages with Gamma's Generate API (v1.0). Use when asked to make slides/decks/one-pagers via Gamma, or to export a Gamma to PDF/PPTX/PNG. Triggers: «сделай презентацию в Gamma», «gamma api», «сгенерируй слайды gamma», «экспортируй в pptx через gamma»."
---

# Gamma Generate API

## What this skill really does

Gamma's **Generate API** (v1.0, GA since Nov 2025) creates a Gamma (presentation /
document / social / webpage) from text — a one-line prompt up to ~400k characters of
content — and can export it to PDF, PPTX or PNG. It is a **generation-only** API:
you send input text, poll for completion, and get a shareable `gammaUrl` plus an
optional `exportUrl`.

It is **asynchronous** and one-shot per generation. There is **no** slide-by-slide edit
API, no "outline" endpoint, no templates endpoint. (The previous version of this skill
documented `api.gamma.app/v1/generate`, `/v1/presentations`, `update_slide`,
`list_templates` — none of those exist. They were removed.)

Helper: `scripts/gamma_client.py` (correct endpoints, verified against the live API).

## Status / honesty notes (verified 2026-07-22)

- Base URL, path and header below were probed live and are correct (a bad key returns
  HTTP 401 `Invalid API key`, i.e. the request reaches the real endpoint).
- ⚠️ The `GAMMA_API_KEY` stored in `~/.claude/.credentials.master.env` currently returns
  **401 Invalid API key** — it is expired/revoked or on the wrong plan. `GAMMA_API_KEY_2`
  is a broken placeholder (`os.getenv(...)`), ignore it.
- Before anything works: regenerate a key at **gamma.app → Settings → API keys**
  (needs a paid plan: Pro / Ultra / Teams / Business) and replace `GAMMA_API_KEY`.
- Fields marked "(unverified)" below are from Gamma's docs but were not exercised with a
  live generation here. Treat exact allowed-value lists as best-effort, not gospel.

## API surface

| Property | Value |
|----------|-------|
| Base URL | `https://public-api.gamma.app` |
| Create | `POST /v1.0/generations` |
| Poll | `GET /v1.0/generations/{generationId}` |
| Auth header | `X-API-KEY: sk-gamma-...` (custom header, **not** `Authorization: Bearer`) |
| Plan required | Pro / Ultra / Teams / Business |
| Deprecated | `v0.2` retired 2026-01-16 — use `v1.0` |

### Request body (`POST /v1.0/generations`)

| Field | Type | Values / limit |
|-------|------|----------------|
| `inputText` | string (required) | prompt / outline / full content, ≤ 400,000 chars |
| `format` | enum (required) | `presentation`, `document`, `social`, `webpage` |
| `textMode` | enum | `generate` (expand), `condense`, `preserve` |
| `numCards` | int | 1–75 (plan-dependent) |
| `exportAs` | enum | `pdf`, `pptx`, `png` (png → zip of one PNG per card) |
| `themeId` | string | a theme id (from your workspace) — (unverified) |
| `title` | string | Gamma name, ≤ 500 chars |
| `additionalInstructions` | string | free-text steering — (unverified) |
| `textOptions.tone` | string | e.g. "professional", ≤ 500 chars |
| `textOptions.audience` | string | e.g. "executives", ≤ 500 chars |
| `imageOptions.source` | enum | `aiGenerated`, `webFreeToUseCommercially`, `webFreeToUse`, `noImages`, … |
| `imageOptions.model` | enum | e.g. `dall-e-3`, `flux-1-pro`, `imagen-3-flash` — (unverified list) |
| `folderIds` | array | ≤ 10 folder ids — (unverified) |

Response: `{ "generationId": "..." }`.

### Poll response (`GET /v1.0/generations/{generationId}`)

- `status`: `pending` → `completed` | `failed`
- on `completed`: `gammaUrl`, `gammaId`, `exportUrl` (present only if `exportAs` was set),
  `credits.deducted`, `credits.remaining`
- rate-limit headers: `x-ratelimit-remaining`, `x-ratelimit-remaining-burst`,
  `x-ratelimit-remaining-daily`. Poll every ~5 s.
- export URLs expire in ~1 week and are public-with-link.

## Procedure

1. Ensure a valid `GAMMA_API_KEY` (see status notes). Quick auth check:
   `curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-KEY: $GAMMA_API_KEY" \
   https://public-api.gamma.app/v1.0/generations/x` — expect `404` (key OK) vs `401` (bad key).
2. Build `inputText`. For tighter control, pass a structured outline and use
   `textMode: preserve` or `condense` instead of `generate`.
3. `POST /v1.0/generations`; keep the `generationId`.
4. Poll `GET /v1.0/generations/{generationId}` every ~5 s until `completed`/`failed`.
5. Use `gammaUrl` (view/share) and `exportUrl` (download, if `exportAs` set).

## Output

- `gammaUrl` — editable/shareable Gamma
- `exportUrl` — PDF/PPTX/PNG download (only when `exportAs` requested)
- `gammaId`, credits deducted/remaining

## Usage — helper script

```bash
# generate + wait for completion + export to pptx
python ~/.claude/skills/gamma/scripts/gamma_client.py generate \
  "AI in Healthcare: trends, applications, and outlook" \
  --format presentation --num-cards 10 --export pptx \
  --tone professional --audience "hospital executives" --wait

# poll an existing generation
python ~/.claude/skills/gamma/scripts/gamma_client.py poll <generationId> --wait
```

## Usage — raw curl

```bash
KEY="$GAMMA_API_KEY"
GEN=$(curl -s -X POST https://public-api.gamma.app/v1.0/generations \
  -H "X-API-KEY: $KEY" -H "Content-Type: application/json" \
  -d '{"inputText":"Quarterly sales report Q4: metrics, wins, 2025 outlook",
       "format":"presentation","textMode":"generate","numCards":10,"exportAs":"pptx"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['generationId'])")

# poll
curl -s https://public-api.gamma.app/v1.0/generations/$GEN -H "X-API-KEY: $KEY"
```

## Credits (rough, from docs — unverified against a live run)

- text: ~1–3 credits per card (model-dependent)
- images: ~2–15 (standard) up to 30–125 (ultra) credits each
- example: 10-card deck + 5 images ≈ 20–60 credits

## Checklist before shipping a Gamma job

- [ ] `GAMMA_API_KEY` valid (auth probe returns 404, not 401)
- [ ] `format` is one of presentation/document/social/webpage
- [ ] `inputText` ≤ 400k chars
- [ ] `numCards` within plan limit (1–75)
- [ ] set `exportAs` only if you need a downloadable file
- [ ] poll to `completed` before using `exportUrl` (async!)
- [ ] grab `exportUrl` promptly — it expires in ~1 week

## Not this skill

- Local slide building / templated decks without Gamma → `manus-slides`, `pptx`, `slides`
- KP / Company decks (HTML→PNG→PPTX) → `kp-deck-factory`
- Editing an existing `.pptx` → `pptx`

## References

- Developer docs: <https://developers.gamma.app>
- Endpoint spec: <https://github.com/gamma-app/gamma-docs>
