---
name: ugc-unboxing-video
description: >
  Produce a creator-led UGC unboxing video: a visible creator opens a
  package and reacts to its reveal. Require both the creator-led format and
  an unboxing, haul or PR-drop arc. Opening a package, showing its contents or
  focusing on packaging alone does not request a creator performance; use
  ordinary video generation for a product-only reveal. Exclude scripts,
  still images, footage edits and other UGC formats. Named preset commands
  such as /unboxing use the Higgsfield preset resolver. Missing assets after
  a valid format match are intake gaps.
---

# UGC unboxing video

## Format gate

The brief must request a creator-led reveal, not simply a product coming out of
its packaging. Do not introduce a visible creator or reaction arc to make a
product-only video fit this workflow. Once the format matches, collect the
creator identity, product and duration normally.

Produce one hosted 9:16 MP4 with one creator identity. Each board is a 21:9
sheet of four vertical 9:16 slots; one Seedance clip turns the board into four
internal hard cuts: PACKED → REVEAL → PRODUCT-FOCUS → SATISFACTION.

## Runtime contract

- Use only current OpenAI-host and Higgsfield MCP tools.
- Ask through `ask_user_input` when exposed, `ask_user_input_v3` only when that
  exact variant exists, otherwise one concise chat question. Never use legacy
  elicitation names.
- Import ChatGPT attachments once with `media_upload_and_confirm`; keep their
  confirmed IDs.
- Authorized HTTPS images may seed image generation directly. Convert the
  selected product image into a confirmed Higgsfield image UUID before video:
  `media_upload` → sandbox download+PUT → `media_confirm`.
- Run downloads, ffmpeg, Python, probes, transcription, assembly, and uploads
  only through `sandbox_exec`.
- Reserve sandbox outputs before producing them, PUT within the same command,
  and confirm only after HTTP 200.
- Caption scripts are preinstalled at
  `$HF_WORKFLOWS/ugc-unboxing-video/scripts/`.
- Use `generate_image_batch` and `generate_video_batch`, stable
  `{index, params}` entries, `params.count:1`, and at most six requests per call.
- Wait through `jobs_wait` in groups of at most eight with
  `timeout_seconds:15`. Poll only active or retryable lookup-failed jobs.
- Never pass an entry without `job_id` to `jobs_wait`; retry only rejected or
  failed indices.
- For `unlim_choice`, ask its message and resubmit unchanged with the user's
  `use_unlim` choice.
- Do not substitute a locked unavailable model.

## Hard rules

- Use one `character_media_id` throughout.
- Board 1 slot 1 always shows a sealed, taped box and no product. The reveal is
  slot 2. The box is at the edge or gone in slot 2 and absent forever in slots
  3–4 and later boards.
- A real package photo is optional. Without one use one generic plain brown
  delivery box; never invent branding.
- Product analysis happens once and is reused verbatim.
- Generate boards sequentially; write all clip prompts before grouped video
  submission.
- De-slop every board. Use a raw board only after both allowed Seedream attempts
  fail.
- Never bake text into generation. Optional text is post-render.
- No greeting or reintroduction after board 1.
- Default to English speech with an American accent unless explicitly changed.

## Duration and arc

| Total duration | Boards | Clip durations |
| --- | ---: | --- |
| 4–15s | 1 | total duration |
| 16–19s | 2 | balance both to at least 4s |
| 20–30s | 2 | 15, remainder |
| 31–45s | 3 | 15, 15, remainder |
| 46–60s | 4 | 15, 15, 15, remainder |
| >60s | ceil(D/15) | 15 each, final clip at least 4s |

Use `BOARD_1_CANONICAL_UNBOXING` for K=1 and `BOARD_K_POST_REVEAL` for
K>1. Later boards continue exploring, using, or demonstrating the product.

## Phase 0 — Intake

Parse product photo or URL, duration, attached creator photo or desired gender,
optional real-package photos, approved claims, language/accent, and explicit
look or location overrides. Classify specificity as `auto`, `guided`, or
`director`.

Ask once for missing duration (offer 10s/15s/30s/45s), product, creator
photo/gender, and whether a real package photo is available. If the user chooses
to attach a package but has not attached it, ask once for the actual image and
wait. A bare “yes” is not package media. Never ask about models, board count,
aspect ratios, resolution, audio, transitions, or identity training.

## Phase 1 — Normalize product and package

Read `references/product-intake.md`. Resolve `product_reference`, confirmed
`product_video_reference`, canonical product description, tier, category,
mechanics, hand-relative scale, visible side, and absent features.

Import real package photos once and keep their confirmed IDs. Otherwise set the
package reference to null and use the generic-box contract.

## Phase 2 — Lock the creator

If a creator photo is attached, import it once and use it unchanged.

Otherwise read `references/ugc-character.md`, settle fresh variety rolls, write
one clean creator prompt, and submit:

```json
{"requests":[{"index":0,"params":{"model":"soul_2","prompt":"<creator prompt>","count":1,"aspect_ratio":"3:4","quality":"2k"}}]}
```

Wait until terminal and lock the returned job ID and result URL.

## Phase 3 — Write the monologue

Use roughly 12–20 words for ≤10s, 20–28 for 11–12s, and 28–35 for 13–15s.
Split into one segment per board. Board 1 uses a caved-in confession or other
specific reveal-compatible hook, a body-event reaction at the reveal, one turn,
and a natural resolution. Later boards continue mid-thought.

Remove AI-tell warm-ups, generic praise, repetition, and unsupported claims.
The literal first word of every segment must be hook content. Save the exact
full monologue to `output/script.txt` during assembly.

## Phase 4 — Generate boards sequentially

Read `references/ugc-unboxing-board.md`. For each K submit one stable-index
`generate_image_batch` request using `gpt_image_2`, 21:9, 2k, high quality,
and media order product, character, optional real package, then cleaned previous
board for K>1. Drop absent media and renumber `@ImageN` declarations.

Wait until terminal before K+1. Keep each board job ID and result URL.

### Mandatory de-slop pass

For every raw board, take the completed `result_url` returned by `jobs_wait` and
call `generate_image_batch` with `seedream_v5_pro`, that HTTPS result URL with
canonical role `image`, 21:9, 2k, and this exact prompt:

> KEEP EXACTLY the framing, composition, slot layout, camera distances, poses,
> subjects and product of this horizontal storyboard sheet and every one of its
> side-by-side vertical slots — no reframe, no zoom, no crop, no re-layout, no
> change to the scene, to any person's face / hair / body, or to the product
> design. CHANGE ONLY micro-realism, applied identically in every slot:
> true-to-life pore-level skin with natural texture and fine vellus hair, real
> material detail, even natural daytime light with gentle highlight roll-off and
> faint true sensor noise, a flat authentic iPhone photo, deep focus. PRESERVE
> each face's exact shape / width / proportions 1:1 — do NOT squeeze / narrow /
> slim / stretch any face. AVOID AI-slop: waxy plastic skin, airbrushed poreless
> skin, beauty-filter smoothing, over-saturation, HDR glow / bloom / halos,
> oversharpening, teal-orange grade, shallow depth of field, bokeh, cinematic /
> DSLR look. Keep the product blank / unbranded, no added text, no watermark, no
> baked slot labels.

The OpenAI generation route imports that URL as a concrete `media_input` and
normalizes the generic image role to Seedream's `image_references` wire field.
Never pass the raw board job ID to this i2i call.

Replace raw board refs with the cleaned result. Moderation failure: retry once
with `seedream_v5_lite`, then keep raw rather than stall. Feed cleaned K-1 into
board K.

## Phase 5 — Write and submit clips

Read `references/ugc-unboxing-clip.md`. Write all prompts before submission.
Carry K, N, duration, arc role, monologue segment verbatim, specificity,
character/product/package continuity, and approved claims.

Require confirmed `product_video_reference`. Submit stable K requests through
`generate_video_batch`, at most six per call:

```json
{"requests":[{"index":1,"params":{"model":"seedance_2_5","prompt":"<clip prompt>","count":1,"aspect_ratio":"9:16","resolution":"1080p","duration":15,"mode":"omni_reference","generate_audio":true,"medias":[{"value":"<clean_board_job_id>","role":"image"},{"value":"<character_media_id>","role":"image"},{"value":"<product_video_reference>","role":"image"}]}}]}
```

Seedance 2.5 supplies native speech with `mode:"omni_reference"` and
`generate_audio:true`. Never call `generate_audio`. Wait for all jobs
and retry only failed indices.

## Phase 6 — Frozen-frame QA

Inspect evenly spaced frames, every product close-up, and 2–3 mid-word frames.
Require one product, at most two hands, correct box disappearance, consistent
mechanics/scale/state, no gibberish or competing brand, stable face, clean lips,
and no baked text. Correct and rerun only the failed clip.

## Phase 7 — Assemble and export

For N=1, use the accepted clip URL. For N≥2, reserve `final.mp4` and run one
self-contained sandbox command that downloads clips in K order, writes an
explicit concat manifest, stream-copies hard cuts, verifies with `ffprobe`, and
PUTs the result. Confirm only after HTTP 200. On detached-command deadline, use
bounded foreground calls; never use `nohup`.

## Phase 8 — Optional text and delivery

If unanswered, ask once for `Subtitles`, `Hook`, `Both`, or `No text` (default),
plus a post-package choice. Read `references/subtitles.md`; use word-level
timing from final audio.

Return one confirmed hosted video URL and duration. A requested post package is
chat-only: caption, 3–5 hashtags, pinned comment, and loop note.

## Character re-roll

If the same board or video call fails twice consecutively in a way consistent
with creator moderation, rerun the original creator request with a new seed,
discard dependent boards, and resume at board generation. Cap at two re-rolls.
Never submit video with missing media.

## References

- `references/product-intake.md`: product normalization
- `references/ugc-character.md`: creator prompt
- `references/ugc-unboxing-board.md`: four-slot 21:9 board and box rules
- `references/ugc-unboxing-clip.md`: four-cut Seedance prompt
- `references/subtitles.md`: optional post-render text

Never load sibling UGC references.
