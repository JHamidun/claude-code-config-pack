---
name: ad-multiplier
description: Create ordered independent edits from one supplied 4-30 second video with Ad Multiplier while preserving motion, timing, audio, and untargeted text. Activate for "ad multiplier", "multiply my video or ad", or several edits of one clip that replace, add, remove, or change people, products, objects, clothing, backgrounds, attributes, or targeted text. Do not use for ordinary generation, Marketing Studio presets, simple edits, out-of-range sources, or Cartesian asset combinations.
---

# Ad Multiplier

Turn one source clip into `N` ordered, independent edited videos. Analyze and
register the source once. One output may contain several simultaneous edits;
`N` always counts final videos, never people, assets, operations, or takes.

## OpenAI runtime contract

- Use only tools exposed by the current OpenAI host and Higgsfield connector.
  Ask one concise normal-chat question when intake is incomplete; never invent a
  question tool.
- For each ChatGPT attachment that must enter generation, call
  `media_upload_and_confirm` once and reuse its confirmed `media_id` and URL.
  This helper has a 100 MiB per-file limit. If the attachment is larger, stop
  before paid work and ask for a compressed 4-30 second MP4, an already-confirmed
  item identifiable through `show_medias`, or an authorized HTTPS download URL.
- For an authorized HTTPS source URL that must become a media id, reserve a
  video slot with `media_upload`, then use one `sandbox_exec` command to download
  the source and PUT it to that exact `upload_url`; call `media_confirm` only
  after HTTP 200. Match the reserved filename extension and content type to the
  actual remote video; if they cannot be established, ask for a recognizable
  direct download instead of inventing them. Authorized HTTPS image references
  may be passed directly in generation `medias[].value`.
- Run downloads, `ffprobe`, `ffmpeg`, remuxing, and QC only through
  `sandbox_exec`, never through a client-local shell. The sandbox is ephemeral:
  any producing call must download inputs, create and verify outputs, and PUT
  them to previously reserved upload slots in the same command.
- Submit independent image or video positions with `generate_image_batch` or
  `generate_video_batch` in stable-index groups of at most six, each request
  shaped `{index,params:{...,count:1}}`. Never fan out singleton tool calls.
- Wait on accepted `{index,job_id}` pairs with `jobs_wait`, at most eight jobs
  per wait and `timeout_seconds:15`, until every position is terminal. Never
  pass a `submission_failed` row without a job id. Retry only the failed index,
  at most once; freeze completed indices.
- Use `show_generation_by_ids` only for generated replacement-person approval.
  Never show raw silent Ad Multiplier edits as final deliverables. Final videos
  are confirmed uploads after audio restoration and QC.
- If a submission returns `unlim_choice`, no job was submitted. Ask its exact
  question and resubmit the unchanged request with the user's `use_unlim`
  choice; never choose for them.

## Non-negotiable output contract

- Accept exactly one measured source video of **4.0-30.0 seconds inclusive**.
  Do not trim, split, loop, freeze, or clamp an out-of-range source.
- Supported operations are replace, add, remove, attribute change, clothing
  change, background/location change, an explicitly requested on-screen-text or
  graphic edit, and user-timed edits. Preserve every caption, subtitle, UI
  element, motion-design graphic, label, branding mark, and other on-screen text
  unless the user explicitly targets it or it is physically attached to a
  replaced target. Never automatically remove, add, or regenerate captions.
- Keep source motion, performance, choreography, camera, cuts, lighting, pacing,
  display aspect ratio, exact final duration, and original default audio.
- A person replacement covers every appearance of that mapped source person,
  including cuts, entrances, exits, occlusions, motion blur, transitions,
  reflections, and shadows. Preserve every unmapped person.
- A mapped person image controls the complete visible look: face, hair, skin
  tone, build, grooming, clothing, footwear, and wearable accessories. Override
  clothing only with a separately mapped garment/full-outfit image or an
  explicit user wardrobe instruction.
- Preserve output order from planning through prompts, generation, QC, and
  delivery. Zip ordered lists. Never create a Cartesian product or a persistent
  variant registry.
- If each of `N` outputs replaces two people and neither has a reference, create
  `2N` distinct adult replacement people and pair two with each output.
- Ad Multiplier renders silently with `mode:"video_edit"` and
  `generate_audio:false`; verified finals receive only the source's default
  audio. A source with no audio produces silent finals.

## Stage 1 — resolve intake once

As soon as a source is supplied, collect all still-missing fields in one turn:

1. the requested edit and ordered output list or explicit `N`;
2. whether replacement reference images exist: all, some, or none;
3. final resolution: `720p` (recommended/faster) or `1080p`.

Do not ask again for explicit information. If references are promised, wait for
them before paid generation. If target identity, time range, reference mapping,
or list-to-output assignment is ambiguous, ask one bundled mapping question.

## Stage 2 — register, probe, and analyze once

1. Resolve one confirmed source `media_id` plus its hosted HTTPS URL. Reuse an
   existing confirmed upload from `show_medias({type:"video"})` when the user
   identifies it.
2. Read [media-pipeline.md](references/media-pipeline.md). In one
   `sandbox_exec`, download the trusted hosted URL and run its source probe.
   Retain only the returned measurements; sandbox files are not durable.
3. Reject the source before generation unless its measured duration is within
   4.0-30.0 seconds inclusive.
4. Call `video_analysis_create` exactly once with
   `video_input_id:<source media_id>`, then poll that id with
   `video_analysis_status` every 30-60 seconds until `completed` or `failed`.
   Use completed scenes as the timed source caption. Do not start a second
   analysis while one is pending.
5. Retry analysis once only if it fails, has no usable scenes/timing, omits a
   requested target, or lacks observable evidence for either required
   casting-presentation or hairstyle axis. Stop before generation if the retry
   remains unusable.

For every source person that will be replaced without a user reference, derive
a fictional `source_visual_casting_profile` from observable evidence only:
apparent racial/ethnic casting presentation plus hairstyle length, texture, and
shape. These are visual casting descriptors, not claims about identity.
Stature/build is optional and non-gating. If either required axis remains
unclear after the one retry, ask for a clearer source or both the visible source
trait and desired replacement trait; never guess.

## Stage 3 — plan ordered outputs

- Preserve explicit `N`; otherwise infer it from the ordered output list, or use
  one for a single edit request.
- Map edits on existing content to analysis target descriptions, a unique
  plain-language anchor, and natural visible ranges. An `add` uses
  caption-grounded placement and timing.
- A person identity replacement is global. If the user asks for a partial
  identity replacement, ask them to choose full identity replacement or a
  non-identity attribute edit.
- Resolve each person reference's appearance authority before prompt writing.
  Default to `complete_look`; record a clothing override only for a separately
  mapped garment/full-outfit reference or explicit wardrobe instruction.
- `remove` needs no asset and describes the revealed background. `add` states
  placement, scale, motion, and interaction. Attribute edits change only the
  named property. A targeted text edit preserves source typography, placement,
  animation, and timing unless the user explicitly changes them.
- Resolve every user-dependent choice during planning. A final prompt contains
  no branches, alternatives, placeholders, or meta-conditions.

## Stage 4 — acquire replacement references

### User-supplied images

Keep each attachment's confirmed media id and hosted URL in one fixed order.
An authorized HTTPS image reference may remain an HTTPS value. The value is the
downstream media input; visual inspection must never change its position.

### Missing adult human references — Soul 2.0

Use `soul_2` only for a requested human replacement lacking a user image. It is
not a fallback for animals, products, objects, backgrounds, removals, attributes,
text edits, children, or teens.

1. Load the live contract once with `models_get({model_id:"soul_2"})`.
2. Make one distinct stable-index request per missing adult with
   `generate_image_batch`; use no medias or `soul_id`, `count:1`,
   `aspect_ratio:"3:4"`, and `quality:"2k"`.
3. Before submission, build a positive two-axis contrast plan. The replacement
   must have a clearly different apparent racial/ethnic casting presentation
   and a different hairstyle length, texture, and shape. Generated people in
   the same request must also remain visibly distinct. For a source under 20,
   require a user reference or explicit consent to recast the role as an adult.
4. Write one cohesive 140-190 word English paragraph per person. It must specify
   a straight-on, eye-level, full-body portrait of exactly one adult 20+; concrete
   positive casting and hairstyle traits; direct gaze; attractive, natural,
   photogenic features; complete opaque stylish wardrobe and footwear; a
   seamless matte-white studio; soft high-key lighting; professional deep-focus
   capture; realistic anatomy, hands, limbs, and skin; no props, text, logos,
   clutter, plastic retouching, or exaggerated traits. Include or closely
   paraphrase `high model facial features`, `symmetrical features`,
   `well-proportioned figure`, and `natural skin texture`. Never describe only
   "different" or mention source traits in the Soul prompt.
5. Wait through `jobs_wait`. Inspect completed results against their contrast
   plans and quality gate. Retry only a failed-quality index once.
6. Show all passing candidates in exact stable order with
   `show_generation_by_ids` (split only above 24) and ask for approval. Continue
   only after approval. Keep each approved `(job_id,result_url)`; use the job id
   directly as the later Ad Multiplier image input without re-uploading it.

## Stage 5 — write and validate one prompt per output

Read [prompt-writer.md](references/prompt-writer.md) once and apply it directly.
Build one in-memory asset manifest per output:

1. user references first as `@Image1..@ImageK`, matching exact downstream order;
2. approved generated-person references afterward, beginning at
   `@Image(K+1)`, with job ids in the matching later image positions.

Do not write manifests or prompts to disk. Preserve each finished prompt
byte-for-byte after validation:

- non-empty and at most 3900 characters;
- every required image tag occurs and no undeclared tag, transport id, or URL
  survives;
- every requested operation is covered;
- the exact unconditional source-text preservation block from the reference
  occurs exactly once;
- every person replacement transfers the approved complete look and explicitly
  excludes the original person everywhere;
- no unresolved condition or placeholder remains.

Rewrite one invalid prompt once against the same plan, then fail only that
output before generation.

## Stage 6 — submit silent ordered edits

Load the live contract once with `models_get({model_id:"ad_multiplier"})`. For
each output, send the source video first, followed by image inputs in the exact
manifest order:

```json
{"requests":[{"index":0,"params":{"model":"ad_multiplier","prompt":"<validated prompt verbatim>","count":1,"duration":8,"duration_policy":"strict","aspect_ratio":"auto","resolution":"720p","mode":"video_edit","generate_audio":false,"medias":[{"value":"<source media id>","role":"video"},{"value":"<@Image1 media id, job id, or authorized HTTPS URL>","role":"image"}]}}]}
```

Use `ceil(SOURCE_DURATION)`, not the illustrative duration. Use the chosen
resolution. Split ordered requests into `generate_video_batch` groups of at most
six, retain every accepted job id under its stable output index, and wait each
group with `jobs_wait`. Retry only a rejected or terminal-failed index once with
the same approved identity, prompt, and scope. Never retry a pending index.

Do not call `show_generation_by_ids`, `job_display`, or history tools for these
raw edits. Keep each completed trusted HTTPS `result_url` only for Stage 7. If
some outputs remain pending, report them and never duplicate their jobs.

## Stage 7 — restore audio, verify, upload, and deliver

Never deliver raw silent result URLs. Process at most four completed outputs per
sandbox call:

1. Read [media-pipeline.md](references/media-pipeline.md).
2. Reserve one final MP4 slot per output with `media_upload` before the sandbox
   call.
3. In one self-contained `sandbox_exec`, download the immutable source and raw
   results, extract the source's default audio once, trim/remux every result,
   run all duration/aspect/resolution/audio gates, and PUT each passing final to
   its own exact reserved `upload_url`.
4. Call `media_confirm` only for outputs whose PUT returned HTTP 200.

Deliver only confirmed final upload URLs in original order, labeled `Output 1`,
`Output 2`, and so on. State `completed/total`, concise failed and pending
counts, selected resolution, measured source duration, and whether source audio
was restored or the source was silent. Never expose raw edit URLs, generated
person references, prompts, manifests, local paths, or job/media ids as
deliverables.

## Failure boundaries

| Failure | Required response |
| --- | --- |
| Source outside 4-30s | Stop; report measured duration and accepted range |
| Attachment exceeds 100 MiB | Stop; request compression, confirmed media, or authorized HTTPS URL |
| Source upload/probe fails | Retry once when safe; otherwise stop before spend |
| Analysis invalid twice | Stop before generation |
| Ambiguous mapping | Ask one bundled mapping question |
| Generated-person position fails twice | Fail each dependent whole output or stop |
| User rejects generated people | Regenerate named people or stop |
| Prompt validation fails twice | Fail only that output before generation |
| Ad Multiplier position fails | Retry only that position once |
| Source is silent | Produce a silent verified final |
| Audible source extraction fails | Do not deliver a silent substitute |
| Download/remux/QC/upload fails | Isolate that output; keep verified successes |
| Some outputs remain pending | Report pending; never duplicate them |
