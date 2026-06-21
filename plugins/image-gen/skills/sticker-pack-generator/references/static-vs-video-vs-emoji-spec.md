# Static vs Animated vs Custom Emoji — Telegram Sticker Spec

Three formats, three sets of constraints, three different UX patterns.
Pick before encoding — different formats need different pipelines.

## Spec Matrix

| Property | Static WEBP | Animated WEBM (VP9-alpha) | Custom Emoji WEBM |
|----------|-------------|---------------------------|-------------------|
| Container | WEBP | WEBM | WEBM |
| Codec | VP8 image / lossless WEBP | VP9 (alpha via yuva420p) | VP9 (alpha via yuva420p) |
| Pixel format | RGBA | yuva420p | yuva420p |
| Dimensions | 512x512 (one side exactly 512) | 512x512 (one side exactly 512) | 100x100 |
| File size cap | 512 KB | 256 KB | 64 KB |
| FPS cap | n/a (static) | 30 fps | 30 fps |
| Duration cap | n/a | 3.0 sec | 3.0 sec |
| Alpha support | yes (RGBA) | yes (yuva420p) | yes (yuva420p) |
| Stickers per pack | 120 | 50 | n/a (different unit) |
| Emoji per set | n/a | n/a | 200 per custom emoji set |
| Pack type | regular `/newpack` | video `/newvideopack` | emoji `/newemojipack` |
| Premium required (sender) | no | no | yes (to USE custom emoji) |
| Premium required (viewer) | no | no | no (sees emoji rendered) |

Notes:
- "One side exactly 512" means either width or height must be 512 and the
  other side must be <= 512. For sticker packs we always go 512x512.
- Custom emoji inline render at ~18-22px (text-line size) but become JUMBO
  (~64-100px) when used as a channel reaction or in chats with only emoji.
- The 64 KB cap on Custom Emoji is the hardest constraint in the system.
  This is why painterly raster characters cannot become custom emoji at
  meaningful quality — see `tgs-lottie-deadends.md`.

## Static WEBP

Use when:
- One frame says it all.
- You want maximum reuse (every Telegram client renders WEBP cleanly).
- You want emoji-style coverage (120 slots is enough for a full emotion set).

Encoding:
```bash
# from a single PNG
ffmpeg -i frame.png -vcodec libwebp -lossless 1 -compression_level 6 \
    -q:v 80 -loop 0 -preset picture -an -vsync 0 sticker.webp
```

Verify:
- `identify sticker.webp` (ImageMagick) shows 512x512.
- Filesize <= 512 KB.

Pack creation flow (BotFather):
1. `/newpack` -> name + title
2. Upload each WEBP as document + emoji alt
3. `/publish` -> short_name

## Animated WEBM (VP9-alpha)

Use when:
- You have a loop or short character animation.
- Static would lose the personality (subtle blink, breathing, gesture).
- You can fit under 256 KB at 512x512 30fps 3sec — practical only for
  short loops or simple motion.

Encoding (canonical command, see `vp9-alpha-encoder-setup.md` for details):
```bash
ffmpeg -framerate 30 -i png_seq/%04d.png \
    -c:v libvpx-vp9 -pix_fmt yuva420p \
    -b:v 200k -minrate 100k -maxrate 256k \
    -lag-in-frames 25 -auto-alt-ref 0 \
    -t 3 -an sticker.webm
```

Render UX: inline message renders at standard sticker size (256x256 logical
or larger on tablets/desktop). Reuse via sticker picker is identical to
static stickers — just animated.

Pack type: video stickers — `/newvideopack`. Mixed packs (static + animated)
are NOT supported — separate packs.

## Custom Emoji WEBM

Use when:
- Reaction packs (channel + chat reactions).
- Inline emoji in chat text — the WEBM renders inline at ~22px where a
  regular emoji would render.
- Premium subscribers want a recognizable inline brand mark.

Encoding (extra strict):
```bash
ffmpeg -framerate 30 -i png_seq/%04d.png \
    -vf "scale=100:100:flags=lanczos" \
    -c:v libvpx-vp9 -pix_fmt yuva420p \
    -b:v 32k -minrate 16k -maxrate 64k \
    -lag-in-frames 25 -auto-alt-ref 0 \
    -t 3 -an emoji.webm
```

Hard constraints (any miss = rejection):
- 100x100 dimensions (NOT 512x512).
- <= 64 KB filesize.
- 30 fps, <= 3 sec, yuva420p, libvpx-vp9.

Render UX:
- **Inline in chat**: ~22x22 px (line-height of regular text).
- **As channel reaction**: ~64x64 px on mobile.
- **In emoji-only message**: JUMBO ~100x100 px.
- The 100x100 source is correct — Telegram does NOT upscale beyond it
  for jumbo.

Set type: custom emoji — `/newemojipack`. 200 emoji per set.

See `custom-emoji-posting.md` for the Telethon flow to actually USE
custom emoji inline in messages, and `channel-reactions-setup.md` for
the reaction setup.

## Triggers — Which Format

| Need | Format |
|------|--------|
| "I have one PNG of a face" | Static WEBP |
| "Artist delivered a 3-sec loop, 512x512" | Animated WEBM |
| "I want a branded fire/sparkle for reactions on my channel" | Custom Emoji WEBM |
| "I want both — pack for chats AND emoji set for reactions" | Two outputs: WEBM 512 for pack, WEBM 100 for emoji set |
| "Painterly character, multi-frame, must look high quality" | Animated WEBM (NOT TGS — see `tgs-lottie-deadends.md`) |
| "Vector character, geometric, simple shapes" | TGS Lottie (smaller, cleaner) — when applicable |

## Common Mistakes

- Encoding animated stickers at 60 fps. Telegram caps at 30 — extra frames
  are silently dropped during upload, wasting your bitrate budget.
- Forgetting `yuva420p` on VP9. `yuv420p` = no alpha = silent black bg.
- Using 512x512 for Custom Emoji — file size cannot fit in 64 KB at that
  resolution for any non-trivial content.
- Mixing static + animated in one pack — BotFather rejects.
- Trying to put custom emoji into a sticker pack flow (`/newvideopack`)
  instead of an emoji set flow (`/newemojipack`).
