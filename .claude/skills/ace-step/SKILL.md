---
name: ace-step
description: "AI-музыка локально на your GPU (ACE-Step 1.5): инструменталы, песни, лирика; CLI scripts/generate.py. Триггеры: «напиши песню», jingle, soundtrack. НЕ Suno→suno."
---

# ACE-Step: AI Music Generation

Generate music tracks locally using ACE-Step 1.5. Runs on local your GPU.

## When to use

Trigger on: "сгенерируй музыку", "сделай трек", "music generation", "ace-step", "напиши песню", "сгенерируй аудио", "background music", "soundtrack", "jingle"

## Quick start

```bash
# Simple instrumental
cd ~/your-ace-step && uv run python ~/.claude/skills/ace-step/scripts/generate.py "epic cinematic orchestral" --instrumental --duration 60

# Song with auto-generated lyrics
cd ~/your-ace-step && uv run python ~/.claude/skills/ace-step/scripts/generate.py "upbeat pop song about coding" --generate-lyrics --duration 120

# Song with custom lyrics
cd ~/your-ace-step && uv run python ~/.claude/skills/ace-step/scripts/generate.py "indie folk acoustic" --lyrics "[Verse 1]\nWalking down the road..." --duration 90

# Use XL model for better quality (slower, uses CPU offload)
cd ~/your-ace-step && uv run python ~/.claude/skills/ace-step/scripts/generate.py "jazz piano trio" --model acestep-v15-xl-turbo --instrumental --duration 60

# Fast draft with no LM thinking
cd ~/your-ace-step && uv run python ~/.claude/skills/ace-step/scripts/generate.py "techno beat" --no-thinking --instrumental --duration 30
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `caption` | required | Music style/description prompt |
| `--lyrics` | "" | Song lyrics (with [Verse], [Chorus] tags) |
| `--duration` | 120 | Length in seconds (10-600) |
| `--instrumental` | false | No vocals |
| `--bpm` | auto | Beats per minute |
| `--key` | auto | Key/scale (e.g. "C major", "A minor") |
| `--language` | en | Vocal language: en, zh, ja, ko, ru, etc |
| `--model` | auto | DiT model (acestep-v15-turbo, acestep-v15-sft, acestep-v15-xl-turbo, acestep-v15-xl-sft) |
| `--seed` | -1 | Random seed for reproducibility |
| `--steps` | auto | Inference steps (more = better quality) |
| `--no-thinking` | false | Skip LM (faster but lower quality) |
| `--generate-lyrics` | false | Auto-generate lyrics from caption |
| `--config` | "" | Use existing TOML config file |
| `--json` | false | Output as JSON (for programmatic use) |

## Models available

| Model | Quality | Speed (16GB) | When to use |
|-------|---------|-------------|-------------|
| **acestep-v15-turbo** | Good | ~5-10s | Quick drafts, iteration |
| **acestep-v15-sft** | Better | ~10-20s | Default, balanced |
| **acestep-v15-xl-turbo** | Great | ~20-40s | Final renders (CPU offload) |
| **acestep-v15-xl-sft** | Best | ~30-60s | Production quality (CPU offload) |

## Output

- Files saved to `~/Music/ace-step/`
- Format: WAV (lossless)
- First run downloads model weights (~15-25 GB total from HuggingFace)

## Lyrics format

```
[Verse 1]
First verse lyrics here
Second line of verse

[Chorus]
Chorus lyrics here

[Verse 2]
Second verse

[Bridge]
Bridge section

[Outro]
Final words
```

## Caption prompt tips

Be specific about:
- **Genre**: "melodic death metal", "lo-fi hip hop", "orchestral film score"
- **Instruments**: "acoustic guitar, soft piano, ambient synths"
- **Mood**: "melancholic, introspective, building to triumphant"
- **Vocals**: "powerful female soprano", "raspy male baritone", "whispered"
- **Tempo**: "slow ballad", "high-energy 140 BPM"
- **Reference**: "in the style of Hans Zimmer film scores"

## Gradio UI (alternative)

```bash
cd ~/your-ace-step && uv run acestep
# Opens http://127.0.0.1:7860
```

## REST API (alternative)

```bash
cd ~/your-ace-step && uv run acestep-api
# REST API on http://127.0.0.1:8001
```

## Architecture

- **Location**: `~/your-ace-step/`
- **Runtime**: Python 3.12 via uv (isolated venv)
- **GPU**: your GPU, CPU offload (configure as needed) for XL models
- **Tier**: tier6a (16-20GB config)
- **LM models**: 0.6B, 1.7B (for lyrics gen and thinking)
