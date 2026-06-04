# Static character design — keep 75 emotions visually consistent

## Problem

OpenAI's `gpt-image-2` / `gpt-image-1` generate beautiful one-offs, but if you ask
for 75 emotions of "the same character", each one drifts:

- Eyes shift size/position
- Outfit details vanish or change colour
- Companion / props disappear or transform
- Style oscillates between flat / 3D / chibi
- Anatomy errors (extra arms, mirrored hands, missing fingers)

For a sticker pack you need them to look like the SAME character in 75 poses,
not 75 lookalikes.

## Solution: master reference + edits API + invariant constraints block

1. **Generate ONE master reference** in a neutral pose, with EVERY visible detail
   nailed (palette, accessories, companion, base, props). This is the source of truth.
   Use `images/generations` endpoint, 1024×1024, high quality. See
   `sample-mascot-prompt.txt` for the template that worked for the egg mascot.

2. **For each of the 75 emotions**, call `images/edits` endpoint passing the
   master reference as `image[]`. Prompt structure:

   ```
   Variation of the SAME character shown in reference.
   Keep design and accessories IDENTICAL.
   Change only the emotion/pose as below.

   CHANGE FOR THIS EMOTION: <variable, 1-3 sentences>

   ABSOLUTE CONSTRAINTS — preserve from reference:
   <invariant block, ~10 bullets>
   ```

3. **Invariant CONSTRAINTS block** lists every must-preserve detail. For the egg
   mascot example:

   - Same character: anthropomorphic sunny-side-up fried egg
   - Same outfit: white Greek toga with golden trim and blue logo badge on chest
   - Same accessories: round black nerd glasses, white AirPods, gold laurel wreath
   - Same companion: tiny baby fried-egg with two yolks and own wreath
   - Same base: black cast-iron frying pan with brown wooden handle
   - Same props: parchment scroll in left hand, kitchen spatula in right
   - Same style: editorial illustration, painterly, warm palette
   - Plain white background, square 1:1

   Don't reuse this list — write yours for your character.

## What still goes wrong + fixes

| Problem | Fix |
|---------|-----|
| Third arm appears for "hands up" emotions | Add `EXACTLY 2 arms, no third hand near face` to constraints |
| Companion changes (becomes chicken, fluffball) | Repeat companion details verbatim in constraints |
| Base disappears for "jumping" emotions | Explicit `Base must stay: <base description>` in change prompt |
| Eyes drift size between sticker 12 and 47 | First fix: regenerate. Persistent: tighter "pupils PERFECTLY CENTERED, same focus" |
| Specific prop unclear (mug vs cup) | Be ultra-specific in description, e.g. mate → "calabash gourd + bombilla straw" not "mug" |

## Cost & timing

For 75 emotions at high quality on `gpt-image-2`:
- ~$0.15-0.40 per image
- ~30-60s per image
- Batch of 75: ~50 min + manual review of ~20 you'll want to regen

Cheaper alternative: `gpt-image-1` is ~3× cheaper and still good for consistent
characters via edits API. Quality drop is visible but acceptable for stickers.

## Telegram static sticker requirements (post-gen)

- Max side: 512 px (rectangular OK — e.g. 512×460)
- Format: WebP (preferred) or PNG
- Max file size: 512KB per sticker
- Transparent background (rembg + tight crop — see `tight_crop_alpha.py`)

`gpt-image-2` outputs come on white background with padding. Use `tight_crop_alpha.py`:
rembg cuts the background → `Image.getbbox()` crops to actual content → resize so
longest side = 512.

## Naming convention

Use `NN-slug.png` (e.g. `01-fire.png`, `02-love.png`) to match a `mapping.json`:

```json
[
  {"name": "01-fire", "emoji": "🔥", "change": "Mascot is fired up..."},
  ...
]
```

This makes `upload_static_pack.py` and `replace_in_pack.py` work seamlessly via
emoji-based mapping (not index — pack docs may be reordered by Telegram).

## Personal touches matter

Generic "coffee in hand" is forgettable. Specific "mate in calabash gourd with
bombilla straw" makes the character yours. Pick 5-10 spots in your 75 to insert
personal/cultural details — they're what people remember.
