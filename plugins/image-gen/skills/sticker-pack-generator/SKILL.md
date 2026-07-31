---
name: sticker-pack-generator
description: 'End-to-end Telegram sticker pack pipeline — static WEBP, animated VP9-alpha video, custom emoji packs. PNG-секвенции или AI-кадры, маски SAM2+rembg, VP9 alpha_encoder, Telethon upload через @Stickers, MessageEntityCustomEmoji, реакции канала; TGS Lottie в 64KB не влезает — только WebM. Triggers: «стикерпак», «видео-эмодзи», «кастом эмодзи», "sticker pack", "custom emoji", "VP9 alpha".'
---

# Sticker Pack Generator

End-to-end pipeline for Telegram sticker assets — covers all three pack types, both for hand-drawn PNG sequences from an artist and for AI-generated frames. Battle-tested on `<your_pack_short_name>`-style static, animated, and custom emoji packs for `<YOUR_CHANNEL>`.

## When to use

- "Make me a sticker pack from this MP4 / PNG sequence"
- "Make a custom emoji pack for my channel reactions"
- "I have 75 PNG frames from an artist, turn them into an animated WebM pack"
- "Why does my hand-authored Lottie not fit 64KB"
- "VP9 with alpha — ffmpeg silently strips the alpha"
- "Set up the channel `/setreactions` with my custom emojis mixed with standard ones"

## Three Telegram sticker formats (unified spec)

| Property         | Static WEBP                | Animated WebM (video sticker)             | Custom Emoji WebM                        |
|------------------|----------------------------|-------------------------------------------|------------------------------------------|
| Codec / container| WEBP (still)               | VP9 + alpha via BlockAdditional, WebM     | VP9 + alpha via BlockAdditional, WebM    |
| Size             | 512×512                    | exactly 512×512                           | exactly 100×100                          |
| Filesize cap     | ≤512 KB                    | ≤256 KB                                   | ≤256 KB                                  |
| FPS / duration   | n/a                        | ≤30 fps, ≤3 sec                           | ≤30 fps, ≤3 sec                          |
| Audio            | n/a                        | none                                      | none                                     |
| Render UX        | renders 1:1 at native size | renders 1:1 in chat                       | renders ~32×32 inline; outline ≥3px or details vanish |
| Solo "jumbo" size| no                         | no                                        | NO — only standard Unicode emoji go jumbo solo |
| Pack short_name  | `<name>_by_<bot>`          | `<name>_by_<bot>`                         | must end in `_by_<bot>`; convention `<name>_emoji_by_<bot>` |
| Pack cap         | up to 120                  | up to 120                                 | up to 200                                |
| Bot              | `@Stickers` `/newpack`     | `@Stickers` `/newvideopack`               | `@Stickers` `/newemojipack`              |

## Source material: PNG sequence from artist

Default expected input: a numbered PNG sequence on disk.

```
<HOME>/sticker-pack/<character>/png_seq/0001.png
<HOME>/sticker-pack/<character>/png_seq/0002.png
...
<HOME>/sticker-pack/<character>/png_seq/NNNN.png
```

The sequence can come from any of these:
- An illustrator handing over baked frames (preferred — alpha is usually clean already).
- An MP4 from After Effects / Procreate Dreams — extract with ffmpeg:
  ```
  ffmpeg -i input.mp4 -vf "fps=30,crop=ih:ih,scale=512:512" "<HOME>/sticker-pack/<character>/png_seq/%04d.png"
  ```
- A gpt-image-2 generation (`gpt-image-2-2026-04-21`, `/v1/images/generations`). Note: `background:"transparent"` returns **HTTP 400** — generate on cream/white, mask later.

## Pipeline overview

```
PNG seq (alpha or RGB)
       │
       ├─► (if no alpha) SAM2 + rembg UNION mask  ──┐
       │                                            ▼
       │                                   per-frame chromakey
       │                                            ▼
       │                                   morph close + re-threshold
       │                                            ▼
       │                                   RGBA PNG frames
       │
       ▼
ffmpeg yuva420p raw stream  →  Google `alpha_encoder` (VP9 + BlockAdditional)
       │
       ▼
512×512 .webm  ──►  Telethon /newvideopack | /addsticker | /replacesticker
                                │
                                ▼
                  100×100 .webm  ──►  /newemojipack    (Custom Emoji)
                                │
                                ▼
                   document_id  ──►  MessageEntityCustomEmoji
                                          (UTF-16 offsets in caption)
                                │
                                ▼
                          /setreactions in channel admin
```

## Step 1 — Mask extraction (SAM2 + rembg UNION + chromakey)

White-on-white characters break both rembg and SAM2 individually.
- **rembg per-frame**: flickers and drills holes through motion-blur frames.
- **SAM2 single-click on a white body**: only grabs the colored details, drops the body.

**Solution = UNION of three sources:**

```python
# pseudo-code, full impl in scripts/process_png_seq.py
seed_mask = rembg(frame_0) | chromakey(frame_0, white_threshold=215)
masks = SAM2.add_new_mask(seed_mask).propagate_in_video(frames)
for i, frame in enumerate(frames):
    alpha = masks[i] | chromakey(frame, white_threshold=215)
    alpha = morph_close(alpha, kernel=5)
    alpha = rethreshold(alpha, lo=60, hi=180)   # kills trailing halo
    save_rgba(frame, alpha, f"rgba/{i:04}.png")
```

Notes:
- Chromakey threshold 235 leaves white halo; **use 215**.
- Morph close + re-threshold (under 60 → 0, over 180 → 255) cleans the SAM2 fuzzy edge.
- Flying props (mic, spatula) get lost by SAM2 — the per-frame chromakey UNION recovers them.

## Step 2 — Frame-level alpha encoding (libvpx `alpha_encoder`, custom build)

`ffmpeg -c:v libvpx-vp9 -pix_fmt yuva420p` silently strips alpha when muxing to WebM. Every libvpx build through ffmpeg does this. The ONLY working path is Google's `webm-tools/alpha_encoder` which muxes alpha through Matroska BlockAdditional.

- It is **Linux-only** — run through WSL.
- The upstream `master` branch breaks at low CBR (50 kbps); the well-known patch to `alpha_encoder.cc` restores CBR + `--target-bitrate=50`.
- Battle-tested config: `--end-usage=cbr --target-bitrate=50 --fps=30/1 --width=512 --height=512`.
- Output: ~70–90 KB for a 3-sec sticker.

Build path (one-time):
```
git clone <webm-tools-fork-with-patch> ~/webm-tools
cd ~/webm-tools/alpha_encoder && make
# binary: ~/webm-tools/alpha_encoder/alpha_encoder
```

## Step 3 — Compose into WebM (ffmpeg yuva420p stream → alpha_encoder)

```
ffmpeg -y -framerate 30 -i rgba/%04d.png \
  -pix_fmt yuva420p -f rawvideo - \
  | wsl ~/webm-tools/alpha_encoder/alpha_encoder \
       --width=512 --height=512 --fps=30/1 \
       --end-usage=cbr --target-bitrate=50 \
       -o out.webm
```

Verify in ffprobe: stream `pix_fmt=yuva420p` AND a sibling `BlockAdditional` track.

## Step 4 — Custom emoji crop (100×100)

Telegram renders custom emoji **inline at ~32×32**. Source 512×512 → naive `scale=100:100` makes characters unreadable. Two tradeoffs:

1. **Tight bbox crop** — find non-transparent bbox per frame, crop to it, then resize to 100×100. Maximises character visibility, but if motion is wide, you get bouncy framing.
2. **Slight margin (10–15%)** — crop bbox + margin from the union of bboxes across the entire clip. Stable framing, slightly smaller character.

Empirical: option 2 (union bbox + margin) wins for full-body characters; option 1 wins for head-only emojis.

Outline of ≥3px on key features (eyes, mouth, glasses) is mandatory or they disappear at 32×32.

## Step 5 — Upload to Telegram (Telethon: NewStickerPack / AddSticker)

All upload scripts use Telethon, share `scripts/_telethon_base.py`, and key off `~/.claude/.credentials.master.env` (`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`). Session file: `~/.claude/telegram_session`.

Pack short_name convention: `<base>_by_<your_bot>`. For emoji packs: `<base>_emoji_by_<your_bot>`.

| Action                              | Bot command                                     | Script                          |
|-------------------------------------|-------------------------------------------------|---------------------------------|
| New static pack                     | `/newpack`                                      | `scripts/upload_static_pack.py` |
| New animated WebM pack              | `/newvideopack`                                 | `scripts/create_pack.py`        |
| New custom emoji pack               | `/newemojipack`                                 | `scripts/create_emoji_pack.py`  |
| Add stickers to existing pack       | `/addsticker`                                   | `scripts/add_to_pack.py`        |
| Replace by emoji (preserves slot)   | `/replacesticker` (or `/replaceemoji`)          | `scripts/replace_in_pack.py`    |
| Delete stickers                     | `/delsticker`                                   | `scripts/clean_pack.py`         |
| Read current pack state             | (no bot — telethon GetStickerSet)               | `scripts/check_pack.py`         |

All upload scripts map stickers **by emoji**, not by position — Telegram resorts video packs by upload date. Emojis must be VS16-normalised before comparing:

```python
norm = lambda e: e.replace('️', '')
```

## Step 6 — Custom emoji posting via MessageEntityCustomEmoji (UTF-16 offsets)

After a custom emoji is in a pack, every emoji becomes a `document_id` you can substitute for the literal Unicode emoji in any message **you send via your user account** (or any premium account; standard accounts only see them in channels where they're set as reactions).

```python
from telethon.tl.types import MessageEntityCustomEmoji

text = "🔥 fire takes 🤝 hands"
# offsets are UTF-16 code units, not bytes, not chars
def utf16_len(s): return len(s.encode('utf-16-le')) // 2

entities = []
cursor = 0
for ch, doc_id in replacements:   # [(emoji_unicode, document_id), ...]
    idx = text.find(ch, cursor)
    off = utf16_len(text[:idx])
    length = utf16_len(ch)
    entities.append(MessageEntityCustomEmoji(off, length, document_id=doc_id))
    cursor = idx + len(ch)

await client.send_message(target, text, formatting_entities=entities)
```

`formatting_entities=` and `parse_mode=` are mutually exclusive — pick one. For mixed (HTML + custom emoji) build the entities list manually from `client.parse_mode.parse(...)` and append `MessageEntityCustomEmoji` entries.

## Step 7 — Channel reactions setup (`/setreactions` admin panel)

A channel can have a mix of **standard** emoji reactions and **custom** ones. Both groups count toward Telegram's per-channel reaction cap.

Reference setup that works well on a tech channel:
- 73 standard emoji + 8 custom from the channel's own emoji pack.
- Custom picks pulled from the pack (`🔥 ❤️ 🤔 🤯 🎉 🤝 🤩 🤣` — overwrite with your own).
- Daily story limit is gated by channel **boost level** (level N → ~N stories/day; level 8 → 8). Hitting the cap returns `RPCError 400: BOOSTS_REQUIRED` from `SendStory`. Deleting a sent story does NOT refund the daily slot.

Reactions are configured **once via the @BotFather-less admin UI** (channel → Edit → Reactions → All / Some). Scripted helpers live in `scripts/set_channel_reactions.py` (uses `EditChannelReactionsRequest`).

## TGS Lottie dead ends — DO NOT RETRY

This is the most expensive lesson in this skill. The painterly maximalist illustration style does NOT survive vectorisation under the 64KB TGS cap.

1. **VTracer (Rust raster→SVG) — all 3 presets fail.** `default`, `binarized`, `cartoon`, `polygon` — every output is "unwatchable" (user verdict). Cancelled.
2. **Hand-authored SVG ($500–2000 studio quote).** Doesn't capture painterly stylistic depth either — gradients-rich illustrations with 14 layered groups need too many vertices.
3. **Per-frame animation as Lottie.** 18 frames × ~21 KB per SVG path-set = ~382 KB raw, vs. **64 KB TGS hard cap**. No amount of gzip closes that gap.
4. **`python-lottie` raster→TGS toolchain.** Depends on `glaxnimate.dll` — Windows build is **Python 3.8 only**. No path on Python 3.13.

**Final negative finding:** painterly raster character cannot fit the Telegram TGS hard cap. Stick to **video WebM** for emoji and stickers. The "TGS Lottie renders jumbo at large size like basketball 🏀" trick does not apply to character-based emoji at all.

Keep the bookkeeping packs (`<name>_vector_test`, `<name>_static_test`) around as evidence so you don't re-run this in three months.

## Gotchas (9 items)

1. **TGS 64KB cap** — painterly = no go. Use video WebM (see dead-ends section).
2. **SAM2 loses edges + rembg drifts on shadows** → always UNION mask, morph close + re-threshold; threshold 235 leaves halo, use 215.
3. **`gpt-image-2 background:"transparent"`** → HTTP 400. Generate on cream/white, mask afterwards via SAM2+rembg UNION.
4. **libvpx `master` breaks CBR 50kbps** when building `alpha_encoder` — apply the well-known patch to `alpha_encoder.cc`.
5. **Telethon 1.39 entity parsing**: `<spoiler>`, `<tg-spoiler>`, `||x||`, expandable blockquote are **NOT parsed** by `html_parse`. Build them manually: `MessageEntitySpoiler(offset, length)` and `MessageEntityBlockquote(offset, length, collapsed=True)` with **UTF-16** offsets.
6. **Custom emoji renders 32×32 inline** in chat. Outline ≥3px on key features (eyes, mouth, glasses, badge), or they vanish.
7. **Channel boost level caps daily story limit** (lvl 8 → 8/day). 9th story returns `RPCError 400: BOOSTS_REQUIRED`. Deleting a story in the same day does NOT refund the slot. To fix bad stories without spending quota, use `EditStoryRequest` to swap media.
8. **Workflow strict `schema`** parameter crashes `StructuredOutput` parsers across all subagents — rerun without `schema=` and parse plain text.
9. **Progress files `*_done.txt`** block retries — `rm -f` before any rerun, or the script silently skips work.

Bonus:
- **No parallel Telethon processes on the same `.session`** — SQLite lock; copy the session file (`shutil.copy`) and override `SESSION=` env var for each worker.
- **`tg_client.py` has NO `send-album`** — older docs sometimes claim it does.
- **`@Stickers` FloodWaitError** after ~37 fast replaces; catch and `await asyncio.sleep(fw.seconds + 5)`.
- **Mapping by position** is wrong — Telegram resorts video packs by upload date. Always key off emoji (VS16-normalised).
- **`pipe | tail`** on a long-running encode can SIGPIPE-kill the producer when the tail buffer fills. Pipe to a file instead.

## Scripts catalogue

```
scripts/
├── _config.py                  — loads creds from ~/.claude/.credentials.master.env
├── _telethon_base.py           — shared Telethon client init
├── cuda_init.py                — CUDA DLL bootstrap (must import BEFORE sam2/rembg/torch)
│
├── process_png_seq.py          — PNG seq → SAM2+rembg UNION → yuva420p → alpha_encoder
├── batch_process.py            — batch wrapper around process_png_seq for a dir of seqs
├── make_emoji_variant.py       — 512px webm → 100×100 ≤256KB (union bbox + margin)
│
├── gen_mascot_reference.py     — gpt-image-2 master frame
├── gen_emotion.py              — single emotion via images/edits
├── batch_gen_emotions.py       — batch generate 75 emotion frames
├── tight_crop_alpha.py         — rembg cut + tight crop to 512 webp (for static pack)
│
├── upload_static_pack.py       — /newpack flow
├── create_pack.py              — /newvideopack flow
├── create_emoji_pack.py        — /newemojipack flow
├── add_to_pack.py              — /addsticker, skips already-present emojis
├── replace_in_pack.py          — /replacesticker, preserves slot, keyed by emoji
├── replace_all_custom_emojis.py — bulk text replace via MessageEntityCustomEmoji
├── clean_pack.py               — /delsticker (extras / duplicates)
├── check_pack.py               — GetStickerSet, dump current state
└── set_channel_reactions.py    — EditChannelReactionsRequest (mix standard + custom)
```

## References

- `references/png-seq-source.md` — expected PNG-seq layout + how to extract from MP4 / gpt-image-2.
- `references/static-vs-video-vs-emoji-spec.md` — three formats unified spec (sizes, caps, render UX).
- `references/sam2-rembg-pipeline.md` — UNION mask details, threshold tuning, chromakey for flying props.
- `references/vp9-alpha-encoder-setup.md` — building `alpha_encoder`, the libvpx patch, CBR config.
- `references/tgs-lottie-deadends.md` — why painterly doesn't vectorise; the 64KB math; VTracer presets verdict.
- `references/channel-reactions-setup.md` — `/setreactions` workflow, boost-level story caps.
- `references/custom-emoji-posting.md` — `MessageEntityCustomEmoji` flow + UTF-16 offset helper.
- `references/telegram-bot-flows.md` — every `@Stickers` command flow as a state diagram.
- `references/troubleshooting.md` — failure-mode → diagnosis → fix.
- `references/static-character-design.md` — consistency strategy for 75 emotions on one mascot.
- `references/sample-mascot-prompt.txt` — reusable mascot prompt template.
- `references/sample-emotions.json` — 75-emotion list with constraint blocks.
- `references/sample-mapping.json` — sticker→emoji mapping example.

## Triggers

- **ru**: "стикерпак", "видео-эмодзи", "альбом для канала", "кастом эмодзи", "VP9 alpha", "SAM2 mask", "пак для @-канала", "залей в Telegram", "transparent webm", "пак из mp4", "PNG-секвенция от художника", "TGS не лезет в 64KB"
- **en**: "sticker pack", "custom emoji", "vp9 alpha encoder", "telegram pack pipeline", "alpha_encoder cbr", "BlockAdditional alpha", "sam2 union mask", "rembg+sam2", "tgs lottie 64kb fail"

## GitHub depersonalization checklist (when packaging for public)

When publishing this skill or its scripts as a standalone repo:

**SCRUB:**
- All `@`-handles → replace with `<your_pack_short_name>`, `<your_channel>`, `<your_bot>`.
- Real names of channels, packs, persons, products.
- Absolute paths containing user names: `C:/Users/<user>/...` → `<HOME>/...`.
- API keys, tokens, channel IDs, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`.
- Session files (`*.session`, `*.session-journal`).
- Sample `.env` only as `.env.example` with placeholder values.
- Channel and pack screenshots — blur any identifying handles before checking in.

**KEEP (this is the gold for other users):**
- The technique: SAM2+rembg UNION, chromakey threshold 215, morph close + re-threshold.
- The libvpx `alpha_encoder` patch + CBR config.
- The TGS Lottie dead-end writeup — so nobody else wastes a week on it.
- UTF-16 offset helper for `MessageEntityCustomEmoji`.
- Boost-level story cap notes.
- All 9 gotchas as a top-of-README "DO NOT REDO" block.

**PLACEHOLDERS to use consistently:**
- `<your_pack_short_name>` — e.g. `mymascot_by_examplebot`
- `<YOUR_CHANNEL>` — e.g. `@example_channel`
- `<HOME>` — user home directory
- `<TELEGRAM_API_ID>`, `<TELEGRAM_API_HASH>` — credential placeholders
- `<your_bot>` — the bot suffix all packs must end with
- `<character>` — sticker-pack subject name
