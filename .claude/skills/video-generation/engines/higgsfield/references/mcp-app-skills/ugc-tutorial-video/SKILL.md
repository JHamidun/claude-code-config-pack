---
name: ugc-tutorial-video
description: >
  Produce a UGC tutorial where one visible creator demonstrates realistic
  step-by-step use of a specific product and every step has a baked
  "Step N — Heading" label. Use when tutorial, how-to, or step-by-step intent
  and creator/UGC framing are explicit. Missing product or duration is an intake
  gap. Do not use for ordinary reviews, unboxings, try-ons, product-only ads,
  SaaS walkthroughs, generic ads, scripts, or footage edits.
---

# UGC tutorial video

Produce one hosted 9:16 MP4 with one locked creator identity. Each board is a
21:9 sheet of four vertical 9:16 slots; every slot depicts one physical product
step and displays exactly one `Step N — Heading` caption. One Seedance clip
turns a board into four internal hard cuts.

## Runtime contract

- Use only tools exposed by the current OpenAI host and Higgsfield MCP.
- Ask with `ask_user_input` when exposed, `ask_user_input_v3` only when that
  exact variant exists, otherwise one concise normal-chat question. Never use
  legacy elicitation names.
- Import ChatGPT attachments once with `media_upload_and_confirm` and keep each
  confirmed `media_id`.
- Authorized HTTPS product images may seed image generation directly. Before
  video generation convert the chosen product URL once into a confirmed image
  UUID using `media_upload`, sandbox download+PUT, then `media_confirm`.
- Run ffmpeg, Python, downloads, probes, transcription, assembly, and uploads
  only through `sandbox_exec`.
- Reserve sandbox outputs before producing them; PUT in that same command and
  confirm only after HTTP 200.
- Caption scripts are preinstalled at
  `$HF_WORKFLOWS/ugc-tutorial-video/scripts/`.
- Use `generate_image_batch` and `generate_video_batch`, at most six requests
  per call, stable `{index, params}` entries, and `params.count:1`.
- Wait through `jobs_wait` in groups of at most eight with
  `timeout_seconds:15`. Poll only active or retryable lookup-failed jobs.
- Never pass a batch entry without a job ID to `jobs_wait`; retry only rejected
  or failed indices.
- For `unlim_choice`, ask its message and resubmit unchanged with the user's
  `use_unlim` choice.
- Never substitute a different model for a locked unavailable model.

## Hard rules

- Product usage analysis is mandatory. Never invent a capability or impossible
  action.
- Use one `character_media_id` for every board and clip.
- Step numbering is global: board J contains steps `4*(J-1)+1` through `4*J`.
- Each slot displays exactly one English Title Case caption in the form
  `Step N — Heading`; no other generated text is allowed.
- The last ~0.5–1s of the final cut of the final board contains a brief
  talking-head CTA. It is not a fifth step and never a board caption.
- Generate boards sequentially; submit video only after all prompts are ready.
- De-slop every board while preserving existing step captions. Raw fallback is
  allowed only after both Seedream attempts fail.
- English is the default for step labels, dialogue, CTA, and prompt content.
- Optional extra hook/subtitles are post-render only.

## Duration and step count

| Total duration | Boards | Clip durations | Total steps |
| --- | ---: | --- | ---: |
| 4–15s | 1 | total duration | 4 |
| 16–19s | 2 | balance both to at least 4s | 8 |
| 20–30s | 2 | 15, remainder | 8 |
| 31–45s | 3 | 15, 15, remainder | 12 |
| 46–60s | 4 | 15, 15, 15, remainder | 16 |
| >60s | ceil(D/15) | 15 each, final clip at least 4s | 4N |

## Phase 0 — Intake

Parse product photo or URL, duration, user instructions/manual/usage notes,
attached creator photo or desired gender, approved claims, language, accent,
and explicit setting or appearance overrides. Ask once for missing product,
duration (offer 10s/15s/30s/45s), and creator photo/gender. Offer accent/quirk
only if the brief already signals it. Never ask about models, boards, aspect
ratios, resolution, audio, split, transitions, or identity training.

## Phase 1 — Normalize the product and steps

Read `references/product-intake.md`. Resolve `product_reference`, confirmed
`product_video_reference`, canonical product description, tier, category,
mechanics, visible side, and absent features.

Build `total_steps = 4*N` chronological, physically realistic usage steps. If
the natural sequence is shorter, add real preparation and finishing steps; if
longer, merge adjacent micro-actions. Preserve a user-supplied director step
list one-to-one. Produce `step_captions[]`, each exactly
`Step N — 1–4 Word Heading`, and split into groups of four.

## Phase 2 — Lock the creator

If a creator photo is attached, import it once and use it unchanged.

Otherwise read `references/soul-v2-ugc-character.md`, write one clean creator
prompt with no product, and submit:

```json
{"requests":[{"index":0,"params":{"model":"soul_2","prompt":"<creator prompt>","count":1,"aspect_ratio":"3:4","quality":"2k"}}]}
```

Wait until terminal and lock the returned job ID and URL as the character. Do
not regenerate mid-run.

## Phase 3 — Write the monologue

Use roughly 12–20 words for ≤10s, 20–28 for 11–12s, and 28–35 for 13–15s.
Split into N board segments and four step beats per segment. Explain what the
creator is physically doing in concise conversational English. Tutorial steps,
not a generic story arc, are the spine. Remove AI-tell phrases, repetition, and
unsupported claims.

Reserve ~0.5–1s at the end for `Link in bio.`, `Follow me.`, or `Subscribe!`.
If timing is tight, shorten the instructional line rather than dropping a step.
Save the exact monologue to `output/script.txt` during assembly.

## Phase 4 — Generate boards sequentially

Read `references/ugc-tutorial-boards.md`. For K=1..N submit one stable-index
`generate_image_batch` request using `gpt_image_2`, 21:9, 2k, high quality,
and media order product, character, then cleaned previous board for K>1. Match
every `@ImageN` declaration and pass this board's four captions.

Wait until terminal before K+1. Keep the returned job ID and result URL.

### Mandatory de-slop pass

For each raw board, take the completed `result_url` returned by `jobs_wait` and
call `generate_image_batch` once with `seedream_v5_pro`, that HTTPS result URL
with canonical role `image`, 21:9, 2k, and this exact prompt:

> KEEP EXACTLY the framing, composition, slot layout, camera distances, poses,
> subjects, product AND any on-frame step captions of this horizontal storyboard
> sheet and every one of its side-by-side vertical slots — no reframe, no zoom,
> no crop, no re-layout, no change to the scene, to any person's face / hair /
> body, to the product design, or to existing on-frame text. CHANGE ONLY
> micro-realism, applied identically in every slot: true-to-life pore-level skin
> with natural texture and fine vellus hair, real material detail, even natural
> daytime light with gentle highlight roll-off and faint true sensor noise, a
> flat authentic iPhone photo, deep focus. PRESERVE each face's exact shape /
> width / proportions 1:1 — do NOT squeeze / narrow / slim / stretch any face.
> AVOID AI-slop: waxy plastic skin, airbrushed poreless skin, beauty-filter
> smoothing, over-saturation, HDR glow / bloom / halos, oversharpening,
> teal-orange grade, shallow depth of field, bokeh, cinematic / DSLR look. Keep
> the product blank / unbranded, no NEW added text, no watermark.

The OpenAI generation route imports that URL as a concrete `media_input` and
normalizes the generic image role to Seedream's `image_references` wire field.
Never pass the raw board job ID to this i2i call.

Replace raw board refs with the cleaned output. Moderation failure: retry once
with `seedream_v5_lite`, then retain raw rather than stall. Use cleaned K-1 as
the previous board for K.

## Phase 5 — Write and submit clips

Read `references/ugc-tutorial-clip-prompt.md`. Write every prompt before video
submission. Carry K, N, duration, `BOARD_TUTORIAL_STEPS`, four step captions,
monologue segment verbatim, `is_last_board`, creator/product continuity, and
approved claims.

Require confirmed `product_video_reference`. Submit stable K requests through
`generate_video_batch`, at most six per call:

```json
{"requests":[{"index":1,"params":{"model":"seedance_2_5","prompt":"<clip prompt>","count":1,"aspect_ratio":"9:16","resolution":"1080p","duration":15,"mode":"omni_reference","generate_audio":true,"medias":[{"value":"<clean_board_job_id>","role":"image"},{"value":"<character_media_id>","role":"image"},{"value":"<product_video_reference>","role":"image"}]}}]}
```

Seedance 2.5 supplies native speech with `mode:"omni_reference"` and
`generate_audio:true`. Never call `generate_audio`. Wait for every
job and retry only failed indices.

## Phase 6 — Frozen-frame QA

Inspect evenly spaced frames, product close-ups, and 2–3 mid-word frames.
Require correct product mechanics, one product, at most two hands, consistent
state and scale, clean face/lips, readable unchanged step captions, and no new
text. Fix and rerun only the failed clip.

## Phase 7 — Assemble and export

For N=1, use the accepted clip URL. For N≥2, reserve `final.mp4` and run one
self-contained sandbox command that downloads clips in K order, writes the
concat manifest, stream-copies hard cuts, verifies with `ffprobe`, and PUTs the
result. Confirm only after HTTP 200. On detached-command deadline, use bounded
foreground calls; never use `nohup`.

## Phase 8 — Optional extra text and delivery

If unanswered, ask once for extra `Subtitles`, `Hook`, `Both`, or `No text`
(default), plus a post-package choice. Read `references/subtitles.md`. Preserve
the top step labels; subtitles stay in the bottom safe zone. Add a top hook only
when it visibly clears the step text.

Return one confirmed hosted video URL and duration. A requested post package is
chat-only: caption, 3–5 hashtags, pinned comment, and loop note.

## References

- `references/product-intake.md`: product normalization
- `references/soul-v2-ugc-character.md`: creator prompt
- `references/ugc-tutorial-boards.md`: four-slot 21:9 labeled board
- `references/ugc-tutorial-clip-prompt.md`: four-cut tutorial prompt and CTA
- `references/subtitles.md`: optional extra post-render text

Never load sibling UGC references.
