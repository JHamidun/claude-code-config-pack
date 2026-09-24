---
name: ugc-review-video
description: >
  Produce a finished brand-authorized UGC-style talking-head video in which one
  consenting adult or generated adult creator demonstrates a product or delivers
  user-supplied copy. Use for explicit UGC, creator-video, TikTok-style product
  showcase, or review-style requests that can be rendered without fabricated
  experience or endorsement; a product is optional, while a missing duration is
  an intake gap. Do not use for testimonials, impersonation, product-only ads
  without an on-camera speaker, off-screen voiceover, unboxing-led videos,
  step-by-step tutorials, try-ons, SaaS or website walkthroughs, generic ads,
  script-only requests, or edits of existing footage.
---

# UGC review video

Produce one hosted 9:16 MP4. Keep one creator identity through every board and
clip. Each board is a 21:9 sheet of eight vertical 9:16 slots; one video clip
turns those slots into eight internal hard cuts.

## Runtime contract

- Use only tools exposed by the current OpenAI host and Higgsfield MCP surface.
- Use `ask_user_input` when the host exposes that exact callable. Use
  `ask_user_input_v3` only when that exact variant is exposed. Otherwise ask one
  concise normal-chat question. Never use a legacy elicitation name or Codex's
  plan-only question mechanism as a ChatGPT substitute.
- For each ChatGPT attachment, call `media_upload_and_confirm` once with the
  supplied file object. Keep its returned `media_id`; do not call
  `media_confirm` afterward.
- Authorized HTTPS image URLs may be passed directly in `medias[].value`; the
  OpenAI generation tools import and confirm them automatically. Reuse the
  exact URL or returned confirmed ID. Do not invent a separate import tool.
- Run ffmpeg, Python, downloads, probes, transcription, assembly, and uploads
  only through `sandbox_exec`, never a client-local shell.
- For a sandbox-created output, call `media_upload` before the producing
  `sandbox_exec`, PUT the file to its `upload_url` in that same sandbox command,
  and call `media_confirm` only after HTTP 200. Never pass a sandbox path to
  `media_upload_and_confirm`.
- Workflow scripts are preinstalled at `$HF_WORKFLOWS/ugc-review-video/scripts/` inside
  the sandbox. Run them from there; do not expect plugin-local scripts.
- Use `generate_image_batch` and `generate_video_batch` for headless workflow
  stages. Each request is `{index, params}`, `params.count` is `1`, and one call
  contains at most six requests. Keep stable indices across retries.
- Wait on returned `{index, job_id}` pairs with `jobs_wait` in groups of at most
  eight and `timeout_seconds:15`. If `all_terminal:false`, wait the returned
  `poll_after_seconds` and poll only active or retryable lookup-failed jobs.
  Freeze completed indices. Never poll jobs through a legacy singleton status
  tool.
- Never pass a batch `submission_failed` entry without a `job_id` to
  `jobs_wait`. Retry only rejected or failed indices, never the whole stage.
- `unlim_choice` means no job was submitted. Ask its message and resubmit the
  unchanged request with the user's `use_unlim` choice; never choose for them.
- Do not substitute a different model when a locked model is unavailable.
  Report the incompatible slug and stop that phase.

## Hard rules

- Use one `character_media_id` for every board and clip. Never regenerate it
  mid-run or replace it with an inline description.
- Generate boards sequentially; generate ready clips through grouped batch
  calls only after every clip prompt is written.
- Never bake text into generation. Burn text only after render and only when
  the user opted in.
- Run the de-slop pass on every board. Never send a raw `gpt_image_2` board to
  video unless both allowed Seedream attempts fail.
- Default to English speech with an American accent unless explicitly changed.
- When a product is present, never greet or reintroduce it after board 1; later
  segments continue mid-thought.
- Hide model names, job IDs, internal phases, and intermediate mechanics from
  the user.

## Safety and truth gate — before intake or generation

If any item below fails, do not generate and do not route around the gate:

- **Creator authorization:** use only a generated adult age 21+ or a consenting
  adult non-public person whose image the user is authorized to use. A supplied
  photo is not permission to impersonate its subject. If third-party consent is
  unclear, ask once; decline public figures, celebrities, minors, and deceptive
  identity use. Never clone or imitate a supplied person's voice.
- **Allowed promotion:** decline political persuasion and promotion of prohibited
  or age-restricted goods or services, including adult sexual content, products,
  or services; gambling; illegal or regulated drugs, drug paraphernalia, and
  prescription medication; tobacco or nicotine; weapons, explosives, or harmful
  materials; counterfeit or illicit goods; extremist goods; deceptive or
  high-risk financial services; malware or spyware; fraud; and covert
  surveillance. A neutral educational mention is not a product promotion and
  belongs outside this workflow.
- **Truthful claims:** `approved_claims` is the complete allowlist of product
  claims supplied by the user. Preserve each allowed claim verbatim; never
  strengthen, combine, infer, or derive another claim. With no allowlist, create
  claim-free copy about visible materials, controls, application, packaging, and
  other directly observable mechanics.
- **No synthetic testimonials:** a generated creator is a host or demonstrator,
  never a real customer. Do not invent purchase, ownership, use, results,
  before/after outcomes, ratings, reviews, social proof, relationships, or lived
  experience. First-person experience is allowed only when a consenting user
  supplies the exact script and confirms it describes their own experience.
- **Transparent framing:** describe product-present output as a brand demo,
  creator concept, or sponsored creative—not an organic customer review. When a
  post package is requested, include an appropriate ad/sponsorship disclosure.

## Duration and arc

| Total duration | Boards | Clip durations |
| --- | ---: | --- |
| 4–15s | 1 | total duration |
| 16–19s | 2 | balance both to at least 4s; e.g. 18 → 14+4 |
| 20–30s | 2 | 15, remainder |
| 31–45s | 3 | 15, 15, remainder |
| 46–60s | 4 | 15, 15, 15, remainder |
| >60s | ceil(D/15) | 15 each, final clip at least 4s |

Assign board roles as follows:

- N=1: `FULL_ARC` (HOOK → MAIN → CLOSER).
- N=2: `HOOK+SETUP`, then `APPLY+CLOSER`.
- N=3: `HOOK`, `MAIN`, `CLOSER`.
- N=4: `HOOK`, `REVEAL`, `APPLY`, `CLOSER`.
- N>4: `HOOK` first, `CLOSER` last, `REVEAL`/`APPLY` between.

## Phase 0 — Intake

After the safety and truth gate passes, parse an optional product photo or URL,
duration, creator photo or requested gender, and
explicit overrides for location, hair, ethnicity, outfit register, mood, props,
language, accent, music, `approved_claims`, and on-video text.

Classify specificity:

- `auto`: 1–5 words with no scenario; choose the complete treatment.
- `guided`: 1–3 sentences of tone or rough flow; preserve that direction.
- `director`: 4+ sentences, scenario, shot list, or location sequence; map the
  supplied beats one-to-one to slots.

Ask only for real gaps, bundled into one question: duration (offer 10s, 15s,
30s, 45s) and creator photo/gender when absent. Never ask for a product merely
because none was supplied; lock `product_reference:null` and
`product_description:null` and continue with creator-led, scenario-driven UGC. Include
an accent or physical quirk option only when the brief already signals origin or
deliberately unusual character energy. Never ask about locked models, aspect
ratios, boards, resolution, audio, batching, or identity training.

Do not start paid generation until the required creator input and duration are
resolved. The later text/post-package choice is the only sanctioned second ask.

## Phase 1 — Normalize the optional product

If a product photo or URL was supplied, read `references/product-intake.md` and
follow it exactly. Resolve once:

- `product_reference`: confirmed attachment `media_id` or authorized HTTPS hero
  image URL;
- canonical `product_description`;
- `tier`: `luxury`, `premium`, or `drugstore` from visual packaging cues only;
- `category` and exact usage/opening mechanic.
- `approved_claims`: exact user-supplied strings, or an empty list.

Reuse those values verbatim downstream. Never infer price, invent claims or
creator experience, or
replace a blocked/thin product page with a stock or generated product. If no
product was supplied, skip the reference, keep both product fields null, and
use the no-product branches in `ugc-board.md`, `ugc-clip.md`, and monologue craft.

## Phase 2 — Lock the creator

If the safety gate established that the user is authorized to use an attached
creator photo, call `media_upload_and_confirm` with `type:"image"`, save its
`media_id` as `character_media_id`, and do not ask for confirmation again.

Otherwise read `references/ugc-character.md`, resolve the required variety rolls
and creator prompt, then submit one headless image request:

```json
{"requests":[{"index":0,"params":{"model":"soul_2","prompt":"<creator prompt>","count":1,"aspect_ratio":"3:4","quality":"2k"}}]}
```

Wait with `jobs_wait` until terminal. On success save the returned `job_id` and
`result_url` as `character_media_id` and `character_url`. This identity is a
mandatory board input. Keep wardrobe fixed unless the story explicitly changes
context.

## Phase 3 — Write the monologue

Read `references/monologue-craft.md`. Preserve only allowlisted user-supplied
claims and the requested tone; never invent the creator's history or experience.
apply its density, hook, persona, story-shape, accent, and anti-slop rules. Split
the final monologue into N board segments. Save the exact full text to
`output/script.txt` in the later sandbox assembly command; if a hook plate may be
burned, also save its headline to `output/hook.txt`.

## Phase 4 — Generate boards sequentially

Read `references/ugc-board.md`. For K=1..N, build the complete board prompt and
submit exactly one `generate_image_batch` request with stable index K:

```json
{"requests":[{"index":1,"params":{"model":"gpt_image_2","prompt":"<board prompt>","count":1,"aspect_ratio":"21:9","resolution":"2k","quality":"high","medias":[{"value":"<product_reference>","role":"image"},{"value":"<character_media_id>","role":"image"}]}}]}
```

For K>1 append the cleaned previous board job ID as the final `image` media. If
there is no product reference, remove it and renumber every `@ImageN` declaration
to match the remaining media order. Wait until terminal before continuing.

### Mandatory de-slop pass

For each completed raw board, take the completed `result_url` returned by
`jobs_wait` and submit one `generate_image_batch` request using model
`seedream_v5_pro`, that HTTPS result URL as canonical role `image`,
`aspect_ratio:"21:9"`, `resolution:"2k"`, and this prompt:

When the run is productless, replace every product-preservation clause in the prompt
with `do not introduce any product, package, brand, or sales prop`.

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
Never pass the raw board job ID to this i2i call. Wait until terminal and replace
the board pair with the cleaned job ID and URL.
On moderation failure retry once with `seedream_v5_lite`; if that also fails,
retain the raw board and report the degraded fallback internally.

## Phase 5 — Write and submit clips

Read `references/ugc-clip.md`. Write every clip prompt before submitting any
video. Carry K, N, duration, board role, monologue segment verbatim, specificity,
persona, and board/character/product references.

Submit clips with `generate_video_batch`, stable index K, and groups of at most
six. For N>6, finish one group before submitting the next because the current
OpenAI surface cannot accept a larger batch. Each request uses:

```json
{"index":1,"params":{"model":"seedance_2_5","prompt":"<clip prompt>","count":1,"aspect_ratio":"9:16","resolution":"1080p","duration":15,"mode":"omni_reference","generate_audio":true,"medias":[{"value":"<clean_board_job_id>","role":"image"},{"value":"<character_media_id>","role":"image"},{"value":"<product_reference>","role":"image"}]}}
```

Drop the product media when absent. Seedance 2.5 produces native speech with
`mode:"omni_reference"` and `generate_audio:true`; never call
`generate_audio`. Wait for all clips to become terminal. Retry only failed
indices with the corrected prompt; a successful retry replaces the old job ID at
that index.

## Phase 6 — Frozen-frame QA

Before stitching or displaying clips, inspect evenly spaced frames, every
product close-up when a product is present, and 2–3 mid-word frames. Require:

- when a product is present, exactly one hero product and no clones;
- at most two hands per person, including mirrors and frame edges;
- absent features remain absent; cap/button/prop state stays consistent;
- labels are not gibberish, mirrored, or a different real brand;
- when a product is present, its scale matches the holding hand;
- no doubled lip edges, face drift, baked text, or subtitles.

For a staging failure, correct and rerun only that clip. For lip artifacts, cut
spoken words first. For baked text, rerun once, then remove it in post. Freeze
every accepted index.

## Phase 7 — Assemble and export

For N=1, the accepted clip URL is the final video URL; do not run a sandbox.

For N>=2, call `media_upload` first for `final.mp4`. Then run one
`sandbox_exec` command that downloads accepted clips in stable board order,
writes an explicit concat manifest, concatenates with stream copy and hard cuts
only, verifies the output with `ffprobe`, and PUTs it to the reserved upload URL:

```bash
ffmpeg -f concat -safe 0 -i clips.txt -c copy output/final.mp4
```

Use `background:true` for long assembly and poll its `log_path` at least every
60 seconds without starting a duplicate process. After HTTP 200 call
`media_confirm` with `type:"video"`. If detached execution returns
`deadline_exceeded`, use bounded foreground calls that each finish within the
current 120-second maximum; never use `nohup` as a fallback.

## Phase 8 — Optional text and post package

If the brief did not answer it, ask one bundled delivery question: `Subtitles`,
`Hook`, `Both`, or `No text` (default), plus whether a post package is wanted.

For text, read `references/subtitles.md`. Timings must come from a word-level
transcript of the final audio, never planned beats. Run the preinstalled scripts
from `$HF_WORKFLOWS/ugc-review-video/scripts/` inside `sandbox_exec`; reserve and upload
`final_captioned.mp4` through the sandbox-output flow. If no speech is detected,
burn nothing and keep `final.mp4`.

If requested, return a chat-only post package: one comment-bait caption with an
unanswered open loop, 3–5 hashtags, one pinned comment that answers or adds
observable detail, an appropriate ad/sponsorship disclosure for product-present
marketing, and a one-line loop note. Never burn it into the video.

## Delivery

Return exactly one confirmed hosted video URL and total duration. When captions
were requested, return `final_captioned.mp4` and retain `final.mp4` as the clean
master. Do not expose job IDs or intermediate assets.

## References

- `references/product-intake.md`: product normalization and staging contract
- `references/ugc-character.md`: Soul creator prompt and continuity rules
- `references/monologue-craft.md`: speech density, voice, hooks, and story shapes
- `references/ugc-board.md`: eight-slot GPT Image board prompt
- `references/ugc-clip.md`: eight-cut Seedance prompt
- `references/subtitles.md`: optional transcript-timed text burn

Do not load sibling UGC workflow references; their product-only, unboxing,
tutorial, try-on, and SaaS contracts conflict with this skill.
