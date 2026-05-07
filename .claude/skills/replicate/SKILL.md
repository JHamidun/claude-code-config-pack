---
name: replicate
description: "Replicate - run 1000+ AI models (FLUX, Stable Diffusion, Whisper, LLaMA, etc.) via API. Use when user needs a specific AI model not available natively."
---

# Replicate API Skill

## Overview

Run 1000+ open-source AI models via API. Image generation (FLUX, SDXL), video, audio, text, and more.

## API Key

```python
import os
REPLICATE_API_KEY = os.getenv('REPLICATE_API_KEY')
# Key from ~/.claude/.credentials.master.env
```

## MCP Server

Already configured in `~/.claude/mcp.json` as `replicate`. Can use MCP tools directly.

## Dependencies

```bash
pip install replicate
```

## Basic Usage

```python
import replicate

# Image generation with FLUX
output = replicate.run(
    "black-forest-labs/flux-1.1-pro",
    input={
        "prompt": "a beautiful sunset over mountains, photorealistic",
        "aspect_ratio": "16:9",
        "output_format": "png"
    }
)

# Stable Diffusion XL
output = replicate.run(
    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    input={
        "prompt": "an astronaut riding a horse on mars",
        "negative_prompt": "blurry, low quality",
        "width": 1024,
        "height": 1024
    }
)
```

## Popular Models

| Category | Model | ID |
|----------|-------|----|
| **Image** | FLUX 1.1 Pro | `black-forest-labs/flux-1.1-pro` |
| **Image** | SDXL | `stability-ai/sdxl` |
| **Image** | Ideogram v2 | `ideogram-ai/ideogram-v2` |
| **Video** | Minimax Video | `minimax/video-01` |
| **Audio** | Whisper | `openai/whisper` |
| **Text** | LLaMA 3.1 | `meta/meta-llama-3.1-405b` |
| **Upscale** | Real-ESRGAN | `nightmareai/real-esrgan` |
| **Remove BG** | RemBG | `cjwbw/rembg` |

## Async Predictions

```python
prediction = replicate.predictions.create(
    model="black-forest-labs/flux-1.1-pro",
    input={"prompt": "..."}
)
prediction = replicate.predictions.get(prediction.id)
print(prediction.status)  # "starting", "processing", "succeeded", "failed"
print(prediction.output)  # URL when done
```

## Tips

1. Check model page on replicate.com for input parameters
2. Use `replicate.models.search("keyword")` to find models
3. Output is usually a URL - download with requests
4. Billing is per-second of GPU time
