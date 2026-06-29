---
name: void-video
description: "Netflix VOID — remove objects from video with physics-aware interaction handling. Uses HuggingFace Spaces API (free). Triggers: 'удали объект из видео', 'remove object from video', 'VOID', 'video inpainting', 'убери из видео'."
---

# VOID — Video Object & Interaction Deletion

Netflix's AI model that removes objects from video while realistically simulating physical interactions. If you remove a domino, the falling chain stops. If you remove a person holding a guitar, the guitar falls.

## How It Works

- Model: CogVideoX-based, fine-tuned by Netflix Research
- Resolution: 384x672, up to 197 frames, 12 FPS
- Requires: input video + quadmask video + text prompt
- Free tier via HuggingFace Spaces (GPU Zero)

## API Access

```python
import os
HF_TOKEN = os.getenv('HUGGINGFACE_API_KEY')
```

## Dependencies

```bash
pip install gradio_client
```

## Usage via Gradio Client

```python
from gradio_client import Client

client = Client("<author>/VOID", hf_token=HF_TOKEN)

result = client.predict(
    input_video="path/to/input.mp4",       # Input video file
    mask_video="path/to/quadmask.mp4",     # Quadmask video (see format below)
    prompt="A table with objects on it",    # Describe scene AFTER removal
    num_steps=30,                           # 10-50, default 30
    guidance_scale=1.0,                     # 1.0-10.0, default 1.0
    seed=42,                                # Reproducibility seed
    api_name="/run_inpaint"
)
# result = path to output video file
```

## Quadmask Format

The mask video must encode 4 semantic levels as grayscale pixel values:

| Pixel Value | Meaning |
|-------------|---------|
| 0 (black) | Object to remove |
| 63 (dark gray) | Overlap/interaction zone |
| 127 (mid gray) | Affected region (shadows, reflections) |
| 255 (white) | Background (keep as-is) |

### Creating a Simple Binary Mask (FFmpeg)

For basic removal (object only, no interaction zones):

```bash
# From a mask image sequence (black = remove, white = keep):
ffmpeg -framerate 12 -i masks/frame_%04d.png -c:v libx264 -pix_fmt yuv420p quadmask.mp4

# From a single static mask applied to all frames:
ffmpeg -i input.mp4 -i mask.png -filter_complex "[1:v]scale=iw:ih[mask];[mask]loop=loop=-1:size=1:start=0[mloop];[0:v][mloop]overlay=shortest=1" -pix_fmt gray quadmask.mp4
```

### Auto Mask Generation (requires SAM2 + Gemini)

The full VOID repo includes VLM-MASK-REASONER for automatic mask generation:
1. Point selector GUI to mark objects
2. SAM2 segmentation
3. Gemini VLM for interaction reasoning
4. Automatic quadmask generation

GitHub: https://github.com/Netflix/void-model

## Quick Script

```python
#!/usr/bin/env python3
"""VOID - Remove objects from video via HuggingFace Spaces API."""

import os
import sys
from gradio_client import Client

def remove_object(input_video: str, mask_video: str, prompt: str,
                  steps: int = 30, guidance: float = 1.0, seed: int = 42,
                  output_path: str = None) -> str:
    """Remove object from video using VOID model.
    
    Args:
        input_video: Path to input video
        mask_video: Path to quadmask video (grayscale: 0=remove, 255=keep)
        prompt: Description of scene AFTER object removal
        steps: Inference steps (10-50, higher=better quality, slower)
        guidance: Guidance scale (1.0 recommended)
        seed: Random seed
        output_path: Where to save result (optional)
    
    Returns:
        Path to output video
    """
    token = os.getenv('HUGGINGFACE_API_KEY')
    client = Client("<author>/VOID", hf_token=token)
    
    result = client.predict(
        input_video=input_video,
        mask_video=mask_video,
        prompt=prompt,
        num_steps=steps,
        guidance_scale=guidance,
        seed=seed,
        api_name="/run_inpaint"
    )
    
    if output_path:
        import shutil
        shutil.copy2(result, output_path)
        return output_path
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python void_remove.py <input.mp4> <mask.mp4> <prompt> [--steps N] [--output path]")
        print()
        print("Example:")
        print('  python void_remove.py video.mp4 mask.mp4 "A table with cups" --output result.mp4')
        sys.exit(1)
    
    import argparse
    parser = argparse.ArgumentParser(description="VOID - Video Object Removal")
    parser.add_argument("input_video", help="Input video path")
    parser.add_argument("mask_video", help="Quadmask video path")
    parser.add_argument("prompt", help="Scene description after removal")
    parser.add_argument("--steps", type=int, default=30, help="Inference steps (10-50)")
    parser.add_argument("--guidance", type=float, default=1.0, help="Guidance scale")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", "-o", help="Output video path")
    args = parser.parse_args()
    
    print(f"Processing {args.input_video}...")
    print(f"Mask: {args.mask_video}")
    print(f"Prompt: {args.prompt}")
    print(f"Steps: {args.steps}, Guidance: {args.guidance}, Seed: {args.seed}")
    
    result = remove_object(
        args.input_video, args.mask_video, args.prompt,
        steps=args.steps, guidance=args.guidance, seed=args.seed,
        output_path=args.output
    )
    print(f"Output saved to: {result}")
```

## CLI Usage

```bash
# Basic usage
python ~/.claude/skills/void-video/void_remove.py input.mp4 mask.mp4 "Empty road" -o result.mp4

# High quality (slower)
python ~/.claude/skills/void-video/void_remove.py input.mp4 mask.mp4 "Empty room" --steps 50 -o result.mp4
```

## Limitations

- Max resolution: 384x672 (model resizes internally)
- Max length: ~16 seconds at 12 FPS (197 frames)
- Free HF Spaces tier: queue wait times, 5 min GPU timeout
- Mask must be precise — poor masks = artifacts
- No real-time processing (inference takes 2-5 min per clip)

## When to Use

- Remove unwanted objects/people from video clips
- Clean up video backgrounds
- Creative editing (remove elements to change narrative)
- Research and experimentation with video inpainting

## Links

- Demo: https://huggingface.co/spaces/<author>/VOID
- GitHub: https://github.com/Netflix/void-model
- Model weights: https://huggingface.co/netflix/void-model
- Paper: VOID (Netflix Research, 2025)
