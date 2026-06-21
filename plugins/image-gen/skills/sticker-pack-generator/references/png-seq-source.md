# PNG Sequence Source

Canonical input format for the sticker pipeline is a numbered PNG sequence:
`0001.png ... NNNN.png` at 512x512 RGBA.

## Expected Pattern

```
png_seq/
  0001.png
  0002.png
  ...
  0030.png
```

- Resolution: 512x512 (square, hard requirement for sticker output)
- Mode: RGBA (alpha channel present, even if currently opaque)
- Filename: zero-padded 4-digit index, sorted lexicographically
- Frame rate target: 30 fps (matches Telegram WEBM cap)

If the source already has clean transparency, you can skip directly to
the WEBM encoder (see `vp9-alpha-encoder-setup.md`). In practice the source
is almost never clean — see "Pre-mask sanity" below.

## Source A: MP4 -> PNG Sequence

When an artist or generator delivers an MP4:

```bash
ffmpeg -i source.mp4 -vf fps=30 png_seq/%04d.png
```

Notes:
- `fps=30` forces 30 fps regardless of source rate. Drop or duplicate frames
  as needed; sticker playback assumes 30 fps timeline.
- Output is RGB (no alpha) because MP4/H.264 has no alpha channel. You MUST
  run the mask pipeline afterwards (see `sam2-rembg-pipeline.md`).
- If source is 1080p or larger, pre-scale to 512:
  ```bash
  ffmpeg -i source.mp4 -vf "fps=30,scale=512:512:flags=lanczos" png_seq/%04d.png
  ```

If source has letterboxing or off-center subject, crop first:

```bash
# crop 1080x1080 centered from a 1920x1080 source, then scale
ffmpeg -i source.mp4 -vf "crop=1080:1080:420:0,fps=30,scale=512:512:flags=lanczos" png_seq/%04d.png
```

## Source B: gpt-image-2 Frame-by-Frame

Generating frames via `gpt-image-2` (or `gpt-image-2-2026-04-21`) has a
**known caveat**: the documented `background: "transparent"` request
parameter returns HTTP 400 in the current API. You will get an opaque PNG.

```python
# THIS FAILS with 400:
client.images.generate(
    model="gpt-image-2",
    prompt="...",
    size="1024x1024",
    background="transparent",   # <-- 400 Bad Request
)
```

Workflow:
1. Generate frames WITHOUT the `background` parameter (opaque output).
2. Save as `raw_seq/0001.png ... raw_seq/NNNN.png`.
3. Run mask extraction (see `sam2-rembg-pipeline.md`) to produce
   `png_seq/0001.png ... png_seq/NNNN.png` with proper alpha.
4. Resize to 512x512 if generated at 1024:
   ```python
   from PIL import Image
   for f in sorted(Path("png_seq").glob("*.png")):
       Image.open(f).resize((512, 512), Image.LANCZOS).save(f)
   ```

For temporal consistency across frames when using gpt-image-2, pass the
previous frame as `image[]` input with a small variation prompt rather
than re-generating from scratch. Even so, expect 10-20% frame drift —
the mask pipeline must be robust to this.

## Pre-Mask Sanity Probe

Before throwing frames at SAM2/rembg, probe with PIL to catch broken input
early. Cheap checks save hours.

```python
from pathlib import Path
from PIL import Image
from collections import Counter

def probe(seq_dir: Path):
    files = sorted(seq_dir.glob("*.png"))
    if not files:
        raise SystemExit(f"no PNGs in {seq_dir}")

    sizes = Counter()
    modes = Counter()
    alpha_states = Counter()  # "opaque", "binary", "soft", "missing"

    for f in files:
        im = Image.open(f)
        sizes[im.size] += 1
        modes[im.mode] += 1

        if im.mode != "RGBA":
            alpha_states["missing"] += 1
            continue

        alpha = im.split()[-1]
        hist = alpha.histogram()
        nz = sum(hist[1:])     # non-zero alpha pixels
        full = hist[255]       # fully opaque pixels
        partial = nz - full    # semi-transparent pixels

        if nz == 0:
            alpha_states["missing"] += 1
        elif partial == 0:
            alpha_states["binary"] += 1
        elif full == 0:
            alpha_states["soft"] += 1     # no fully-opaque pixel — suspicious
        else:
            alpha_states["soft"] += 1

    print(f"frames     : {len(files)}")
    print(f"sizes      : {dict(sizes)}")
    print(f"modes      : {dict(modes)}")
    print(f"alpha      : {dict(alpha_states)}")
    return sizes, modes, alpha_states
```

What the output tells you:

| Symptom | Diagnosis | Action |
|---------|-----------|--------|
| `modes={'RGB': N}` | Source has no alpha channel | Run mask pipeline |
| `alpha={'missing': N}` | Alpha is all zero (transparent everywhere) | Check mask script — likely save bug |
| `alpha={'binary': N}` | Hard-edge mask, no anti-aliasing | OK for cartoon style, harsh edge on painterly |
| `alpha={'soft': N}` | Anti-aliased edge | Good — what we want |
| `sizes={(512,512): N1, (1024,1024): N2}` | Mixed resolutions | Resize all to 512 first |

## Alpha Histogram Quick Read

For a single frame:

```python
from PIL import Image
im = Image.open("png_seq/0001.png")
if im.mode != "RGBA":
    print(f"NOT RGBA: {im.mode}")
else:
    a = im.split()[-1]
    h = a.histogram()
    print(f"0   (transparent) : {h[0]:>7d}")
    print(f"1-254 (partial)   : {sum(h[1:255]):>7d}")
    print(f"255 (opaque)      : {h[255]:>7d}")
```

Healthy painterly character with proper soft edges:
```
0   (transparent) :  186432
1-254 (partial)   :   12041   <-- this number should be > 0
255 (opaque)      :   63671
```

If `1-254 (partial)` is 0 and the subject is not a hard-edged vector,
the mask was binarized somewhere — re-extract with soft alpha.

## Downstream Steps

1. PNG sequence verified -> alpha extraction (`sam2-rembg-pipeline.md`)
2. Clean RGBA sequence -> WEBM VP9-alpha encode (`vp9-alpha-encoder-setup.md`)
3. WEBM -> upload via Telegram bot (`telegram-bot-flows.md`)
4. Spec/limits per format -> `static-vs-video-vs-emoji-spec.md`
