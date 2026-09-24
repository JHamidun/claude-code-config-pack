---
name: ugc-try-on-video
description: >
  Produce a finished UGC try-on video where one consenting adult or generated adult creator wears and poses with a garment,
  footwear item, bag, jewelry piece, or wearable accessory while showing fit
  and texture. Use when try-on, wearing, OOTD, fit-check, or
  video-of-me-wearing intent is explicit. Do not load this skill for a text-only
  script, outline, shot list, or advice, even if it mentions UGC, OOTD, or try-on;
  those requests need writing, not the video-production workflow.
  Missing product, duration, or creator
  input is an intake gap. Do not use for reviews without a try-on, unboxings,
  tutorials, product-only ads, SaaS walkthroughs, generic ads, or footage edits.
---

# UGC try-on video

Produce one hosted 9:16 MP4 with a single locked creator identity and wearable
product. Each board is a 21:9 sheet of eight vertical 9:16 slots; one Seedance
clip turns those slots into eight narrative beats separated by seven hard cuts.

## Runtime contract

- Use only tools exposed by the current OpenAI host and Higgsfield MCP.
- Ask through `ask_user_input` when exposed, `ask_user_input_v3` only when that
  exact variant exists, otherwise one concise chat question. Never use legacy
  elicitation names.
- Import every ChatGPT attachment once through `media_upload_and_confirm` and
  keep its confirmed `media_id`.
- Authorized HTTPS product images may seed image generation directly. Convert
  the chosen product image once into a confirmed Higgsfield UUID before video:
  `media_upload` → download and PUT inside `sandbox_exec` → `media_confirm`.
- Run downloads, ffmpeg, Python, probing, transcription, assembly, and uploads
  only through `sandbox_exec`.
- Reserve sandbox outputs with `media_upload` before producing them, PUT in the
  same command, and call `media_confirm` only after HTTP 200.
- Caption scripts are preinstalled at
  `$HF_WORKFLOWS/ugc-try-on-video/scripts/`.
- Use `generate_image_batch` and `generate_video_batch`, at most six requests
  per call, each `{index, params}` with `params.count:1`. Keep indices stable.
- Wait with `jobs_wait` in groups of at most eight and
  `timeout_seconds:15`. Poll only active or retryable lookup-failed jobs.
- Never send `submission_failed` entries without job IDs to `jobs_wait`. Retry
  only rejected or failed indices.
- If a call returns `unlim_choice`, ask its message and resubmit unchanged with
  the user's `use_unlim` choice.
- Never substitute a locked unavailable model.

## Hard rules

- Use one `character_media_id` for every board and clip.
- Board 1 slot 1 is the muted pre-wear outfit with one plain kraft bag. From
  slot 2 onward, the product is worn and the bag never returns.
- Never depict a costume change, opening the kraft bag, or lifting the product
  from it. The hard cut performs the change.
- Slots 4 and 6 are hand-free garment macros; no hand touches the fabric.
- No mirrors or reflections. Lock hair, face, product silhouette, color, print,
  and design across the video.
- Generate boards sequentially. Write all clip prompts before grouped video
  submission.
- Run the de-slop pass on every board; raw fallback is allowed only after both
  Seedream attempts fail.
- Never bake text into generation. Optional text is post-render only.
- No CTA tail. End naturally on the final spoken beat.
- Default to English with an American accent unless explicitly changed.

## Safety and suitability gate — before intake or generation

If any item below fails, do not generate and do not route around the gate:

- **Creator authorization:** use only a generated adult age 21+ or a consenting
  adult non-public person whose image the user is authorized to use. A supplied
  photo is not permission to impersonate its subject. If third-party consent or
  adult status is unclear, ask once; decline public figures, celebrities,
  minors, non-consenting people, and deceptive identity use. Never silently
  age-transform a request and never clone or imitate a supplied person's voice.
- **General-audience fashion:** this workflow is for ordinary garments,
  footwear, bags, jewelry, and wearable accessories presented as a fit or style
  demonstration. Decline intimate apparel, lingerie, underwear, fetish wear,
  transparent garments, sexualized styling, nudity, or an emphasis on intimate
  anatomy. Do not adapt a disallowed request into a different outfit.
- **Allowed promotion:** decline political persuasion and promotion of
  prohibited or age-restricted goods or services, including adult sexual
  products or services, gambling, illegal or regulated drugs, prescription
  medication, tobacco or nicotine, weapons, counterfeit or illicit goods,
  extremist goods, deceptive or high-risk financial services, malware,
  spyware, fraud, and covert surveillance.
- **Truthful presentation:** preserve only product claims supplied by the user;
  never infer performance, results, purchase, ownership, endorsement, or lived
  experience. A generated creator presents a brand-authorized concept, not an
  organic customer testimonial.

## Duration and board progression

| Total duration | Boards | Clip durations |
| --- | ---: | --- |
| 4–15s | 1 | total duration |
| 16–19s | 2 | balance both to at least 4s |
| 20–30s | 2 | 15, remainder |
| 31–45s | 3 | 15, 15, remainder |
| 46–60s | 4 | 15, 15, 15, remainder |
| >60s | ceil(D/15) | 15 each, final clip at least 4s |

Use these arc roles:

- K=1 `BOARD_1_TRY_ON_CANONICAL`: PRE_WEAR, WEARING, FRONT_POSE,
  TEXTURE_CLOSEUP, TURN, DETAIL, STYLE_POSE, FINAL_LOOK.
- K=2 `BOARD_2_TRY_ON_HOME_TOUR`: continue through other rooms in the same
  home.
- K=3 `BOARD_3_TRY_ON_OUTDOOR`: all outdoor; light rain from slot 2, dry hair,
  wet-detail macros, no reflections.
- K=4 `BOARD_4_TRY_ON_HOME_REFLECT`: settled indoor reflection.
- K≥5 `BOARD_K_TRY_ON_LOOP`: alternate established and new compatible places.

## Phase 0 — Intake

After the safety and suitability gate passes, parse product photo or URL,
duration, attached authorized adult creator photo or desired generated-adult
gender, plus explicit location, appearance, mood, language, accent, claims, and
text choices. Classify the brief as `auto`, `guided`, or `director`.

Ask once for real gaps: product, duration (offer 10s/15s/30s/45s), and creator
photo or gender. Offer accent/quirk only when the brief already signals origin
or unusual creator energy. Never ask about models, boards, aspect ratios,
resolution, audio, transitions, or identity training.

## Phase 1 — Normalize the product

Read `references/product-intake.md`. Resolve and reuse verbatim:
`product_reference`, confirmed `product_video_reference`, canonical wearable
description, tier, category, materials, drape, absent features, and visible
side. Never infer price, claims, or an unseen side.

## Phase 2 — Lock the creator

If an authorized adult creator photo is attached and the gate has established
consent, import it with `media_upload_and_confirm` and use that confirmed ID
without re-asking or editing the photo.

Otherwise read `references/ugc-character.md`, settle fresh variety rolls and
write one creator prompt. Submit:

```json
{"requests":[{"index":0,"params":{"model":"soul_2","prompt":"<creator prompt>","count":1,"aspect_ratio":"3:4","quality":"2k"}}]}
```

Wait with `jobs_wait`, then lock `(character_media_id, character_url)` to the
returned job ID and result URL. Never replace the identity mid-run except under
the bounded character re-roll below.

## Phase 3 — Write the monologue

Use roughly 12–20 words for ≤10s, 20–28 for 11–12s, and 28–35 for 13–15s.
Split into one segment per board; the clip reference distributes it across the
eight beats. Board 1 is a personal-want mini-story. Later boards continue
mid-thought. Remove AI-tell openers, generic praise, repeats, unsupported
claims, and any CTA. The first word of each segment must be hook content, not a
recording warm-up.

Save the exact full monologue to `output/script.txt` during assembly.

## Phase 4 — Generate boards sequentially

Read `references/ugc-try-board.md`. For each K submit one stable-index
`generate_image_batch` request using `gpt_image_2`, `aspect_ratio:"21:9"`,
`resolution:"2k"`, `quality:"high"`, and media in this order: product,
character, then cleaned previous board when K>1. Match `@ImageN` declarations
to that order.

Wait until terminal before creating K+1. Keep the returned board job ID and
result URL.

### Mandatory de-slop pass

For every board, take the completed `result_url` returned by `jobs_wait` and run
one `generate_image_batch` request with `seedream_v5_pro`, that HTTPS result URL
with canonical role `image`, 21:9, 2k, and this exact prompt:

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
with `seedream_v5_lite`, then retain raw rather than stall. Feed the cleaned K-1
to board K.

## Phase 5 — Write and submit clips

Read `references/ugc-try-clip.md`. Write every clip prompt before submission.
Carry K, N, duration, arc role, monologue segment verbatim, specificity,
persona, garment contract, and references. Enforce the six lip-sync beats and
two silent macro voiceover beats described in the reference.

Require a confirmed `product_video_reference`. Submit stable K requests through
`generate_video_batch`, at most six per call:

```json
{"requests":[{"index":1,"params":{"model":"seedance_2_5","prompt":"<clip prompt>","count":1,"aspect_ratio":"9:16","resolution":"1080p","duration":15,"mode":"omni_reference","generate_audio":true,"medias":[{"value":"<clean_board_job_id>","role":"image"},{"value":"<character_media_id>","role":"image"},{"value":"<product_video_reference>","role":"image"}]}}]}
```

Seedance 2.5 renders native speech with `mode:"omni_reference"` and
`generate_audio:true`; never call `generate_audio`. Wait for all jobs
and retry only failed indices.

## Phase 6 — Frozen-frame QA

Inspect evenly spaced frames, garment close-ups, and 2–3 mid-word frames.
Require garment consistency, hand-free macros, bag only in board 1 slot 1, no
mirrors/reflections, at most two hands, stable hair and face, clean lips, and no
baked text. Correct and rerun only the failed clip.

## Phase 7 — Assemble and export

For N=1, use the accepted clip URL. For N≥2, reserve `final.mp4`, then run one
self-contained `sandbox_exec` that downloads clips in K order, writes an
explicit concat manifest, stream-copies hard cuts, probes the output, and PUTs
it to the reserved URL. Confirm only after HTTP 200. Never use `nohup` after a
detached-command deadline; split into bounded foreground calls instead.

## Phase 8 — Optional text and delivery

If unanswered, ask once for `Subtitles`, `Hook`, `Both`, or `No text` (default),
plus whether a post package is wanted. Read `references/subtitles.md`; timing
must come from the final audio's word-level transcript.

Return one confirmed hosted video URL and duration. A requested post package is
chat-only: caption, 3–5 hashtags, pinned comment, and loop note.

## Character re-roll

If the same board or Seedance call fails twice consecutively in a way consistent
with character moderation, rerun the original character request with a new
seed, discard dependent boards, and resume from board generation. Cap at two
character re-rolls. Never continue with missing media.

## References

- `references/product-intake.md`: wearable normalization
- `references/ugc-character.md`: creator prompt
- `references/ugc-try-board.md`: eight-slot 21:9 try-on board
- `references/ugc-try-clip.md`: eight-beat Seedance prompt
- `references/subtitles.md`: optional post-render text

Never load sibling UGC references.
