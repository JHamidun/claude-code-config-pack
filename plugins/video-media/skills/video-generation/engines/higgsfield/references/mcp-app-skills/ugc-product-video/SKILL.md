---
name: ugc-product-video
description: >
  Produce a finished product-only UGC video with off-screen voiceover; a person
  may appear only as auxiliary hands, cropped body, or POV. Require UGC or casual
  creator-style intent together with product-only, no creator on camera,
  no talking head, or product-as-hero framing. Product-only or faceless framing
  alone does not qualify a generic commercial. Exclude silent or no-narration
  requests even when labeled UGC; use ordinary video generation instead. Its
  off-screen voice is native Seedance audio: do not
  activate narrator or call separate audio-generation tools. Missing product or
  duration is an intake gap. Do not
  use for creator-led reviews, unboxings, tutorials, try-ons, SaaS or website
  walkthroughs, generic ads, scripts, or footage edits.
---

# UGC product video

Produce one hosted 9:16 MP4. The product is the hero; any visible person stays
auxiliary and silent. Each board is a 21:9 sheet of four vertical 9:16 slots;
one Seedance clip turns those slots into four internal hard cuts.

## Runtime contract

- Use only tools exposed by the current OpenAI host and Higgsfield MCP.
- Use `ask_user_input` when exposed, `ask_user_input_v3` only when that exact
  variant is exposed, otherwise one concise normal-chat question. Never use
  legacy elicitation names.
- Import each ChatGPT attachment once with `media_upload_and_confirm` and keep
  the returned `media_id`; do not call `media_confirm` afterward.
- Authorized HTTPS images may seed image generation directly. Before video
  generation, convert an HTTPS product image once into a confirmed Higgsfield
  image UUID: reserve with `media_upload`, download and PUT it inside
  `sandbox_exec`, then call `media_confirm`.
- Run downloads, ffmpeg, Python, probing, transcription, assembly, and uploads
  only through `sandbox_exec`, never through a client-local shell.
- For a sandbox-created output, reserve its upload with `media_upload` before
  the producing command, PUT it in that same command, and call `media_confirm`
  only after HTTP 200. Never give a sandbox path to
  `media_upload_and_confirm`.
- Workflow scripts are preinstalled at
  `$HF_WORKFLOWS/ugc-product-video/scripts/` inside the sandbox.
- Use `generate_image_batch` and `generate_video_batch`. Each request is
  `{index, params}`, `params.count` is `1`, and each call contains at most six
  requests. Keep indices stable across retries.
- Wait with `jobs_wait` in groups of at most eight and
  `timeout_seconds:15`. Poll only active or retryable lookup-failed jobs; never
  use a legacy singleton status tool.
- Never pass `submission_failed` entries without job IDs to `jobs_wait`.
  Retry only rejected or failed indices.
- An `unlim_choice` result submitted nothing. Ask its message and resubmit the
  unchanged request with the user's `use_unlim` choice.
- Never replace a locked model because it is unavailable. Report the
  incompatible slug and stop that phase.

## Hard rules

- Off-screen speech is part of this workflow's scope. For a silent/no-narration
  ad, route to ordinary video generation rather than adapting this workflow.
- A real product reference is required. Never invent or substitute one.
- Product is the hero in every slot. A person may be absent, hands-only,
  cropped, or POV, but never identity-locked or the focal subject.
- Voiceover only: no on-camera dialogue, lip-sync, greeting, or speaking mouth.
- Native Seedance speech only. Do not load or activate `narrator`; never call
  `generate_audio` or `generate_audio_batch`, and never assemble a separate TTS
  track over these clips.
- Generate boards sequentially; submit ready clips in grouped batch calls only
  after every clip prompt is written.
- Run the de-slop pass on every board. Never send a raw board to video unless
  both permitted Seedream attempts fail.
- Never bake text into generation. Add optional hook/subtitles only after the
  final video exists.
- Default to English voiceover with an American accent unless explicitly
  changed.
- Hide models, job IDs, internal phases, and intermediate mechanics.

## Duration and arc

| Total duration | Boards | Clip durations |
| --- | ---: | --- |
| 4–15s | 1 | total duration |
| 16–19s | 2 | balance both to at least 4s; e.g. 18 → 14+4 |
| 20–30s | 2 | 15, remainder |
| 31–45s | 3 | 15, 15, remainder |
| 46–60s | 4 | 15, 15, 15, remainder |
| >60s | ceil(D/15) | 15 each, final clip at least 4s |

Board 1 always uses `PRODUCT-INTRO → PRODUCT-DEMO-A → PRODUCT-DEMO-B →
PRODUCT-RESULT`. Later boards continue with materially different product-demo
angles, conditioned on the cleaned previous board.

## Phase 0 — Intake

Parse the product photo or product-page URL, duration, requested language and
accent, approved claims, music request, and explicit setting or demo overrides.
Ask only for missing product and duration, bundled once. Offer 10s, 15s, 30s,
and 45s for duration. Never ask about models, aspect ratios, resolution, boards,
audio, batching, identity, or transitions.

Do not start paid generation until product and duration are resolved. The later
text/post-package choice is the only sanctioned second ask.

## Phase 1 — Normalize the product

Read `references/product-intake.md` and follow it exactly. Resolve once:

- `product_reference`: confirmed attachment ID or authorized HTTPS hero image
  for image stages;
- `product_video_reference`: confirmed Higgsfield image UUID for Seedance;
- canonical `product_description`, including mechanics, hand-relative scale,
  visible side, absent features, label treatment, and one imperfection;
- `tier`, `category`, and `voice_gender`.

Reuse these values verbatim. Never infer price, invent claims, or replace a
blocked product page with stock or generated imagery.

## Phase 2 — Write the voiceover

Write off-screen voiceover only. Use roughly 12–20 words for ≤10s, 20–28 for
11–12s, and 28–35 for 13–15s. Split the total into one segment per board and
four beat-sized phrases per segment. Use sensory or mechanical specifics, not
generic praise. Remove greetings, repeated ideas, AI-tell phrases, and
unsupported claims. When an approved-claims list exists, preserve only exact
allowlisted strings.

Save the exact script as `output/script.txt` in the later assembly command.

## Phase 3 — Generate boards sequentially

Read `references/ugc-product-boards.md`. For K=1..N, write the complete prompt
and submit one stable-index request:

```json
{"requests":[{"index":1,"params":{"model":"gpt_image_2","prompt":"<board prompt>","count":1,"aspect_ratio":"21:9","resolution":"2k","quality":"high","medias":[{"value":"<product_reference>","role":"image"}]}}]}
```

For K>1 append the cleaned previous-board job ID as the final `image` media and
match every `@ImageN` declaration to media order. Wait until terminal before
continuing.

### Mandatory de-slop pass

For every raw board, take the completed `result_url` returned by `jobs_wait` and
submit one `generate_image_batch` request using `seedream_v5_pro`, that HTTPS
result URL with canonical role `image`, `aspect_ratio:"21:9"`, `resolution:"2k"`,
and this exact prompt:

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

Replace the board pair with the cleaned job ID and URL. On moderation failure,
retry once with `seedream_v5_lite`; then retain the raw board rather than stall.

## Phase 4 — Write and submit clips

Read `references/ugc-product-clip-prompt.md`. Write every clip prompt before
submitting video. Carry K, N, duration, arc role, voiceover segment,
`voice_gender`, product description, board reference, and approved claims.

Require `product_video_reference` to be a confirmed UUID. Submit clips with
`generate_video_batch`, stable K indices, at most six per call:

Before the first submission, assert all three native-audio locks together:
`model:"seedance_2_5"`, `mode:"omni_reference"`, and
`generate_audio:true`. If any is absent, fix the video request; do not route to
`narrator` or compensate with a separate audio call.

```json
{"requests":[{"index":1,"params":{"model":"seedance_2_5","prompt":"<clip prompt>","count":1,"aspect_ratio":"9:16","resolution":"1080p","duration":15,"mode":"omni_reference","generate_audio":true,"medias":[{"value":"<clean_board_job_id>","role":"image"},{"value":"<product_video_reference>","role":"image"}]}}]}
```

Seedance 2.5 renders native voiceover with `mode:"omni_reference"` and
`generate_audio:true`; never call `generate_audio`. Wait for all
clips. Retry only failed indices and replace their prior job IDs.

## Phase 5 — Frozen-frame QA

Before assembly, inspect evenly spaced frames and every product close-up.
Require exactly one hero product; at most two hands per person; consistent
mechanism, scale, cap/button/prop state, and absent features; no gibberish,
mirrored, or unrelated branding; no baked text. Fix and rerun only the failed
clip.

## Phase 6 — Assemble and export

For N=1, the accepted clip URL is final. For N≥2, reserve `final.mp4`, then use
one `sandbox_exec` command to download clips in stable K order, create an
explicit concat manifest, concatenate with hard cuts and stream copy, verify
with `ffprobe`, and PUT to the reserved upload URL:

```bash
ffmpeg -f concat -safe 0 -i clips.txt -c copy output/final.mp4
```

After HTTP 200, call `media_confirm` with `type:"video"`. For a detached-command
deadline, use bounded foreground calls that each finish within the current
limit; never use `nohup`.

## Phase 7 — Optional text and delivery

If unanswered, ask once for `Subtitles`, `Hook`, `Both`, or `No text` (default),
plus whether a post package is wanted. Read `references/subtitles.md` for text.
Use word-level timing from final audio, never planned beats.

Return exactly one confirmed hosted video URL and total duration. If requested,
add a chat-only post package: caption, 3–5 hashtags, pinned first comment, and
loop note. Never burn the post package into video.

## References

- `references/product-intake.md`: product normalization
- `references/ugc-product-boards.md`: four-slot 21:9 board prompt
- `references/ugc-product-clip-prompt.md`: four-cut Seedance prompt
- `references/subtitles.md`: optional transcript-timed text burn

Never load sibling UGC references; their creator, unboxing, tutorial, try-on,
and website contracts conflict with this product-only skill.
