# TGS / Lottie Dead Ends for Painterly Characters

Verified negative result, 2026-05-30. Documented so we don't re-attempt.

## Goal

Take a painterly raster character (PNG sequence, ~18 frames) and convert
to TGS (Telegram's gzipped Lottie JSON) under the **64 KB hard cap**
while preserving recognizable painterly quality.

## Conclusion (TL;DR)

Painterly raster -> TGS at preserved quality is **not achievable** with
current tooling. Stick to video WebM stickers (see
`vp9-alpha-encoder-setup.md`) which give 256 KB headroom and natively
support raster.

The rest of this file documents what was tried, with numbers, so
future-you doesn't waste a day re-running the same experiments.

## What "TGS" Actually Is

- TGS = gzip-compressed Lottie JSON.
- 64 KB cap = compressed (gzip) size.
- Lottie JSON describes vector shapes with bezier paths + keyframe
  interpolation. Raster pixels do not exist in Lottie — they must be
  vectorized (traced) first.

## Path 1: VTracer Preset Sweep

VTracer (Visioncortex) is the best open-source raster-to-SVG vectorizer.
We ran a preset sweep on a single representative frame from the
sticker pack:

Test directory: `sticker-pack/vector_test/`
Input: 512x512 painterly RGBA character, ~21 KB PNG.

| Preset | color_precision | layer_difference | filter_speckle | Raw SVG size | TGS (gzipped Lottie) |
|--------|-----------------|------------------|----------------|--------------|----------------------|
| `detailed_max` | 8 | 4 | 1 | 7.5 MB | rejected (>>64 KB) |
| `lite_4_24_8` | 4 | 24 | 8 | ~470 KB | 180 KB (still over cap) |
| `lite_3_32_16` | 3 | 32 | 16 | ~58 KB | 1.7 KB (under cap) |

`detailed_max` preserves the painterly look but produces a 7.5 MB SVG —
two orders of magnitude over the cap before even considering animation.

`lite_4_24_8` lands at 180 KB TGS — close but over, and visual quality
is already noticeably degraded (gradients flattened to solid color regions).

`lite_3_32_16` fits in 1.7 KB but the character is unrecognizable —
reduced to ~10 flat color blobs.

There is no preset midpoint that both fits the cap AND preserves the
painterly identity.

## Path 2: Multi-Frame Math

Even ignoring quality:

- 18 frames at 21 KB raw input each = 378 KB raw bitmap budget.
- After raster->SVG trace with quality-preserving settings (~3-7 MB per
  frame), total raw SVG budget = 54-126 MB per animation.
- After conversion to Lottie + gzip (best case ~5-10x compression on
  structured Lottie JSON), final TGS = 5-12 MB.
- That is 80-180x over the 64 KB cap.

You cannot fit 18 frames of painterly raster into 64 KB. The information
density of the source overwhelms what Lottie + gzip can encode.

## Path 3: Hand-Authored SVG

The Lottie path that DOES work is hand-authored vector animation in
After Effects + Bodymovin, or Rive, or directly in Lottiefiles editor.

Cost reference (agencies, 2026):
- Single character TGS animation: $500-2000.
- Multi-emotion pack (10-20 expressions): $5K-20K.
- Even then: aesthetic is geometric / flat / cartoon. **Painterly
  texture cannot be reproduced in vector** without paying the file-size
  cost we already showed is unfit.

So even with budget the deliverable is a different visual style — not a
faithful conversion of the painterly source.

## Path 4: python-lottie + glaxnimate (DLL Tooling)

The python-lottie ecosystem (with glaxnimate's Lottie exporter) is the
typical OSS toolchain for programmatic Lottie generation.

Known compatibility issue:
- glaxnimate ships a native DLL/SO with Python bindings.
- The bindings are pinned to **Python 3.8** ABI.
- No build for Python 3.13 exists, and there is no documented migration
  path from upstream.
- Workaround = run a parallel Python 3.8 environment just for the
  conversion step, then back to 3.13 for everything else.

The cost of maintaining a 3.8 venv (env switching, dependency drift,
build pinning) is higher than the value of the conversion, given that
the output cannot fit the cap anyway. Drop the path.

## Why Video WEBM Wins

| Constraint | TGS Lottie | WEBM VP9-alpha |
|------------|------------|----------------|
| Size cap | 64 KB | 256 KB (4x) |
| Native raster | no (must vectorize) | yes |
| Painterly preserved | impossible at cap | yes, easily |
| Frame count headroom | ~6-8 simple vector frames | 90 frames at 30fps x 3sec |
| Tooling | python-lottie 3.8-only / agency | ffmpeg, mature |

For painterly characters, the 4x size headroom and native raster support
of VP9-alpha WEBM eliminates the entire vectorization problem.

## When TGS Still Makes Sense

Don't read this as "TGS is bad". TGS is the right choice when:
- Source is already vector (Figma export, Adobe Illustrator, SVG).
- Aesthetic is flat / geometric / cartoon (no painterly texture).
- Character is designed Lottie-first (limited shape count, no gradients
  that won't quantize to flat regions).
- You want the smallest possible payload (TGS at 30-50 KB beats WEBM at
  150 KB for low-bandwidth users).

For painterly raster characters specifically, route to WEBM and don't
look back.

## Files Left Behind

In `sticker-pack/vector_test/` (kept for reference):
- `frame.png` — single representative source frame
- `vtracer_detailed_max.svg` — 7.5 MB output
- `vtracer_lite_4_24_8.svg` + `.tgs` — 180 KB
- `vtracer_lite_3_32_16.svg` + `.tgs` — 1.7 KB
- `notes.md` — raw numbers from the sweep

Reproduce a sweep:
```bash
vtracer --input frame.png --output out.svg \
    --color_precision 4 --layer_difference 24 --filter_speckle 8
```
Then count bytes after gzip.

## Cross-References

- Pick format: `static-vs-video-vs-emoji-spec.md`
- Encode WEBM: `vp9-alpha-encoder-setup.md`
- Mask raster source: `sam2-rembg-pipeline.md`
