# Gemini Models Catalog (via Public AI Studio API key)

As of June 2026. Verified via live API discovery — DO NOT trust announcements or docs, model availability drifts.

## How to discover what's actually on YOUR key

```bash
GEMINI_KEY=AIzaSy...
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_KEY}" \
  | python -c "
import json, sys
d = json.load(sys.stdin)
for m in sorted(d['models'], key=lambda x: x['name']):
    name = m['name'].replace('models/', '')
    methods = ','.join(m.get('supportedGenerationMethods', [])[:2])
    in_tok = m.get('inputTokenLimit', 0)
    out_tok = m.get('outputTokenLimit', 0)
    print(f'{name:50} in:{in_tok:>10}  out:{out_tok:>10}  [{methods}]')
"
```

Run this BEFORE hardcoding a model name in any config. Model lists vary between keys (some keys have preview access, others don't).

## Current catalog (June 2026, public API key)

### Text generation (use as `model:` default)

| Name | Best for | Latency | In | Out | Notes |
|---|---|---|---|---|---|
| `gemini-3.5-flash` | **Recommended primary** for bots | 1-3s | ~1M | 64K | Stable, fast, cheap |
| `gemini-3.1-pro-preview` | Higher-quality answers when latency OK | 5-15s | ~2M | 64K | Best reasoning |
| `gemini-3.1-flash-lite` | Cheapest, simple Q&A | <1s | ~1M | 8K | Light tasks |
| `gemini-3-flash-preview` | Beta — limited features | 2-4s | ~1M | 64K | Still beta in some regions |
| `gemini-flash-latest` | Always-on alias to newest stable Flash | 1-3s | varies | varies | Use carefully — may change behavior |
| `gemini-pro-latest` | Always-on alias to newest stable Pro | 5-15s | varies | varies | Use carefully |
| `gemini-2.5-flash` | Stable fallback | 1-3s | 1M | 64K | Known good |
| `gemini-2.5-pro` | Stable fallback for hard reasoning | 5-15s | 1M | 64K | Known good |
| `gemini-2.0-flash` | Older stable | 1-3s | 1M | 8K | Smaller output |
| `gemini-2.0-flash-lite` | Cheapest 2.0 | <1s | 1M | 8K | OK for routing/classification |

### Image generation (use in `generate_image.py` style scripts, NOT primary model)

| Name | Notes |
|---|---|
| `gemini-3.1-flash-image-preview` | **Nano Banana 2 (NB2, канон-дефолт)** — recommended for kid bots and quick illustrations |
| `gemini-3.1-flash-image` | Stable Nano Banana |
| `gemini-3-pro-image-preview` | High-quality, slow |
| `gemini-2.5-flash-image` | NB1 — устарела, канон `rules/dont-do.md` ЗАПРЕЩАЕТ; fallback = `gemini-3.1-flash-image` |

### Specialty

| Name | Use case |
|---|---|
| `gemini-3.1-flash-tts-preview` | Text-to-speech |
| `gemini-3.1-pro-preview-customtools` | Custom tool calling experiments |
| `gemini-2.5-computer-use-preview-10-2025` | Browser/UI automation |
| `gemini-embedding-001`, `gemini-embedding-2` | Embeddings for RAG |
| `gemini-robotics-er-1.5-preview` | Robotics planning |

## How Hermes addresses the model

In `config.yaml`:
```yaml
model:
  default: gemini-3.5-flash               # bare model name, NOT prefixed with "models/"
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta/openai
```

**CRITICAL**: `base_url` MUST be `/v1beta/openai` shim, not bare `/v1beta`. Hermes uses `chat_completions` api_mode → it expects OpenAI-style `/chat/completions` path. The `/v1beta/openai` shim exposes Gemini under OpenAI Chat Completions surface.

If you hit `HTTP 404: Gemini returned HTTP 404` — base_url is wrong.

If you hit `HTTP 404: models/X is not found for API version v1beta` — model name doesn't exist on this key. Run discovery curl above.

## Pricing as of June 2026 (USD per 1M tokens)

| Model | Input | Output |
|---|---|---|
| gemini-3.5-flash | ~$0.10 | ~$0.40 |
| gemini-3.1-flash-lite | ~$0.04 | ~$0.20 |
| gemini-3.1-pro-preview | ~$1.25 | ~$10 |
| gemini-2.5-flash | ~$0.075 | ~$0.30 |
| gemini-2.5-pro | ~$1.25 | ~$10 |
| gemini-2.0-flash | ~$0.05 | ~$0.20 |

For comparison:
- Claude Sonnet 4.5: $3 / $15
- GPT-5.4: $2.50 / $10 (subscription via Codex backend = free but rotation hell)

Gemini Flash ~30x cheaper than Sonnet for typical bot workloads.

## Rate limits as of June 2026

Public AI Studio key (free tier):
- 1500 requests / day across all models
- 15 RPM gemini-3.5-flash
- 60 RPM gemini-2.5-flash (legacy higher quota)

For a 3-bot fleet with 100 conversations/day each = 300 inbound msgs/day, well under the 1500 limit. Safe.

If you need more — Vertex AI billing-account key has 100k+ RPD. Different infrastructure though, doesn't work with raw API key (needs service account).

## Quick OpenAI-compat smoke test

```bash
GEMINI_KEY=AIzaSy...
MODEL=gemini-3.5-flash

curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
  -H "authorization: Bearer ${GEMINI_KEY}" \
  -H 'content-type: application/json' \
  -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"reply with 1 word\"}],\"max_tokens\":50}"
```

Expected: `{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"Hi"}}],...}`.

If `choices[0].message` is empty `{}` but status 200 — model spent all max_tokens on hidden reasoning. Bump `max_tokens` or set `reasoning_effort: low` in Hermes config.

## Native Gemini endpoint (not for Hermes — for reference only)

If you have custom code outside Hermes, native Gemini endpoint format:

```bash
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_KEY}" \
  -H 'content-type: application/json' \
  -d '{"contents":[{"parts":[{"text":"reply with 1 word"}]}]}'
```

Returns Gemini-native response shape. Hermes does NOT use this endpoint — it uses the `/v1beta/openai/chat/completions` shim because runtime is hard-wired to chat_completions api_mode.

## What's NOT on the public API key

These exist but require Vertex AI (service account, GCP project):
- `gemini-3.5-pro` (full pro, separate from -preview)
- `gemini-3-pro` (full release)
- `claude-sonnet-4-6` via Vertex
- `claude-opus-4-6` via Vertex
- Anthropic models via Vertex

If user asks for "Gemini 3.5 Pro" — clarify that public key only has `gemini-3.5-flash` and `gemini-3.1-pro-preview`. Pro full release is Vertex-only.

## When Google deprecates a model

Run the discovery curl regularly. If a model you depend on disappears from the list, Hermes will start returning HTTP 404. Migration path:
1. Check announcements at https://ai.google.dev/gemini-api/docs/models
2. Switch to closest available model in same family
3. Update `default: ...` in config.yaml of all bots
4. Force-recreate containers

We've already lost `gemini-3-flash` (without -preview) once — it existed briefly then 404'd silently.
