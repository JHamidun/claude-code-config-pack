---
name: thumbnail-generation
description: >
  Create or revise finished YouTube/Instagram thumbnails and video cover
  images. Require a request to make or change the image; critique, readability
  analysis, title ideas and channel planning alone stay text. Named Higgsfield
  presets are resolved by higgsfield first: do not load this workflow merely
  because a slash token names a cover. For presets, load it only when the
  resolved instructions request it. Exclude generic images, complete videos,
  video edits and title cards within footage.
---

# Thumbnail Generation

The full production pipeline for cinematic top-tier YouTube/Instagram
thumbnails: **concept framework → casting → scene → 4K render → surgical tweaks → text**.
Distilled from the Thumbnail Maker app build and live user feedback.

## When to Use

Use for a requested finished thumbnail/cover image or a revision to that image.
Reviewing readability, comparing concepts or writing titles without requesting
an image stays an ordinary analysis/text task. Reference analysis below supports
an already requested production task; it does not independently activate it.

A named Higgsfield preset must be resolved through `higgsfield` first. Load this
workflow for that preset only if the returned instructions call for it; a cover
word in the command does not imply this production pipeline.

For a qualifying image-production task, use this skill before `generate_image`.
Reference analysis (when the user attaches an example image) is done with YOUR OWN
vision — look at the reference and extract the structured fields in the
"Reference analysis contract" below. The reference itself is NEVER sent to the
generation model and never enters `medias` — it only shapes the prompt through
those extracted fields.

## OpenAI runtime contract

- Use only tools exposed by the current OpenAI host and Higgsfield connector.
- Use `ask_user_input` when that exact callable is exposed, `ask_user_input_v3` only
  when that exact variant is exposed, otherwise ask one concise normal-chat question.
  Never invent a legacy question tool.
- For a ChatGPT attachment that must enter generation, call
  `media_upload_and_confirm` once with the supplied file object and reuse its returned
  `media_id`. A style-only reference thumbnail stays in the host's visual context and
  is never uploaded or passed to generation.
- Authorized HTTPS image URLs may be passed directly in `medias[].value`; the OpenAI
  generation route imports and confirms them. Never invent a separate import tool.
- One user-facing variant uses `generate_image`. Two or more distinct prompts use
  `generate_image_batch` in groups of at most six, each item shaped
  `{index,params:{...,count:1}}`. Wait with `jobs_wait` in groups of at most eight,
  freeze completed indices, and display the final exact ledger once with
  `show_generation_by_ids`.
- Use `jobs_wait` for submitted batch jobs and use `models_get` or `models_search`
  only when a locked model fails or its live contract must be checked. Do not reach for
  tools outside the current OpenAI profile.
- Run downloads and text baking only in `sandbox_exec`. For a sandbox-created PNG,
  call `media_upload` before the producing command, PUT the file in that same command,
  then call `media_confirm` only after HTTP 200. Never pass a sandbox path to
  `media_upload_and_confirm`.
- If a generation returns `unlim_choice`, no job was submitted. Ask its message and
  resubmit unchanged with the user's selected `use_unlim` value; never choose for them.

## EXECUTE — literal pipeline (follow IN ORDER; a step with IF fires only when its IF holds)

Prompt language: assemble every generation prompt in ENGLISH (translate the user's scene
description); baked TEXT strings stay verbatim in the user's language. Templates: copy library
sentences exactly and fill every `<placeholder>` — a `<...>` slot never ships unfilled.
Precedence everywhere: explicit user ask > reference-extracted field > per-field default.
Every `generate_image` call takes ONE `params` object — `model`, `prompt`, `aspect_ratio`,
`medias` AND model-specific settings (`resolution`, `quality`, …) are all keys of that same
`params` object, never separate top-level fields.

1. **Collect inputs** from the user message: scene text · face or character references (0–3) · reference
   thumbnail (a style EXAMPLE, never a face source) · logo · headline text and whether to bake
   it · ratio · emotions and variant count. Apply per-field defaults (below) to whatever is
   missing. Then **pick the framework(s)** — read `references/thumbnail-frameworks.md`
   from this installed skill: every
   concept must open an information gap; brainstorm ≥5 options across frameworks and carry the
   strongest (possibly a combination) into the prompt blocks.

   **Text-in-generation gate (decide BEFORE generating):** the default is ALWAYS a CLEAN render
   with NO text baked into the image. Bake text INTO the generation ONLY on an EXPLICIT user text
   request — the user gives a headline/string to show, says "add text" / "with a caption", or
   asks for a text-based framework BY NAME. A text-carrying framework (Social UI / News Clip /
   Day badge / map callout) that is merely brainstormed or auto-picked while exploring frameworks
   does NOT authorize baking — render that concept text-free, or ask first. Never infer text
   intent from the topic or from the framework pick; when unsure, default to clean or ask once.

   **EXCEPTION — faceless Phase-8b handoffs:** when the caller supplies the locked style key,
   3–6 word hook title, render medium, `bake during generation:provider-first`, people/identity choice, and
   variant count `one`, treat every supplied value as an answered, locked input. Do not reopen
   match mode, character, text-bake, ratio, medium, or variant-count intake. Render exactly one
   16:9 image with the hook in block 3's exact `TEXT` contract. Validate it character-for-character.
   If provider text fails, render one new clean version of the same concept with the default
   no-text block, then bake the exact hook through the deterministic recovery in step 9.
   For a non-photoreal medium such as paper collage, flat motion graphics, storybook, or cutout:
   - replace block 1's photoreal frame contract with `reproduce the exact medium of the style key`,
     naming the supplied medium, materials, palette, and rendering verbatim and ending `NOT
     photoreal, no real photography`;
   - drop block 10's photographic lighting rig and block 11's glossy photoreal grade while keeping
     the hero subject, safe zone, palette, and punchy feed-size legibility;
   - translate recurring characters into the locked medium while preserving their exact design,
     silhouette, wardrobe, colors, and facial identifiers; do not turn illustrated references into
     photoreal faces.
   A `photoreal` medium keeps the normal house frame, lighting, grade, and identity contracts.

   **Character gate (MANDATORY — run this FIRST, before rendering ANYTHING; the face question is
   first-class):** decide WHO is in frame; never assume, never silently substitute a stranger, and
   NEVER generate a person as a periodic or silent default. **Reference-lock is the DEFAULT: whenever
   a face photo OR a provided character image exists, ALWAYS upload it, attach its confirmed id as an
   image reference (`image 1 = CHARACTER 1`, `image 2 = CHARACTER 2`, ...), and Identity-Lock it
   (block 4). NEVER invent or substitute a new person or character when one was supplied.** If the
   concept(s) will contain a person and NO face photo / character is attached, STOP and ASK ONCE, up
   front: "Do you want yourself (or a specific person) in the thumbnail? Send a face photo and I'll
   lock the identity — or should it be a generated person, or people-free?" In a BATCH (e.g. "go
   through all frameworks / render N"), ask this ONCE before rendering the set whenever ANY chosen
   framework is people-centric — do not proceed until it is answered. Then: a supplied face photo /
   provided character → Identity Lock (block 4, up to 3 references); the user EXPLICITLY asks to
   generate a person → a generated person described in prose (ONLY an explicit choice, NEVER the
   silent default); no people → a subject-only framework (Landscape / Product / Graphical /
   Map-Aerial). Never invent a specific identity and never skip a supplied character.

   **Variant-count gate (decide BEFORE generating):** an exact variant count already supplied by
   the user or calling workflow is an answered field — use it and do not ask again. Otherwise ask
   once whether the user wants a single
   thumbnail or a SET of variants of the same concept — offer ~4 by default (same concept, each
   a different emotion and/or camera take), rendered as distinct requests (never one `count:N`
   call). One thumbnail if they prefer. Variants = emotions × takes, hard cap 16
   (see below).
2. **IF a reference thumbnail is supplied:** before analysis, ask exactly once whether to
   **Match this reference** (default: closely preserve its style, composition and subject)
   or make a **Unique take** (use it only as loose inspiration). Use the runtime question
   contract above and stop until answered. A previously stated "match" / "inspired by" intent is
   already the answer and must not be re-asked. On Match, drive the prompt hard from the
   reference; if it contains a real person, still require that person's supplied face photo
   rather than generating a stranger. On Unique, carry only loose visual inspiration and
   author a fresh subject/composition.

   Then analyze the reference with your own vision to fill the "Reference analysis
   contract" (below) — extract exactly those fields as STRICT JSON, then use them to
   drive the prompt according to the settled match mode. Field→block mapping: brief→block 2 · subject→block 4 · elements→block 5 ·
   location→block 7 · composition→block 8 · background→block 9 · split→step 5 split branch ·
   emotion + emotion_detail→the Expression slot. The reference's `subject` prose attaches to
   the photo characters positionally as their pose/action — it never ADDS a person; a
   `person_count` above the number of attached photos becomes text-described extras ONLY if the
   user asked for them. The reference is analyzed by eye ONLY — it NEVER enters any `medias`
   and is NEVER sent to the generation model.
3. **IF any face/character references or a 2D logo were supplied as ChatGPT attachments and do
   not already have confirmed `media_id` values:** call `media_upload_and_confirm` once per
   generation input. Preserve character ids in CHARACTER numbering order and record the logo
   separately. Do not upload a style-only reference thumbnail and do not call `media_confirm`
   after the combined helper. Otherwise skip this step.
4. **IF a logo was uploaded AND the user wants it 3D:** submit the "3D logo prompt" (below) NOW
   as one headless `generate_image_batch` item — `model:"gpt_image_2"`, `resolution:"4k"`,
   `aspect_ratio:"1:1"`, `quality:"high"`, `count:1`, medias = the uploaded 2D logo id. Wait
   on the returned indexed job with `jobs_wait`; the MAIN render on the 3D path uses its
   completed job id as the logo media entry.
5. **Assemble ONE prompt per variant** from "House prompt structure" blocks 1–11 in order.
   - Include/omit rules: blocks 1 and 11 — always, except the non-photoreal faceless handoff drops
     block 11 and substitutes its medium-locked block 1. 2 — if scene text or reference `brief`
     exists. 3 — always the default no-text line; the TEXT / BAKED UI variant fires ONLY on an
     EXPLICIT user text request, NEVER merely because a text-carrying framework was picked. 4 — if ANY person or creature is in frame:
     photo-referenced people get an Identity Lock each; text-described people/creatures are
     described here in prose (never in block 5) and their prose ALSO ends with
     `Expression: <emotion phrase>` — the Expression slot exists per subject regardless of photo
     reference. 5 — if signature props exist or the KEY-ELEMENTS default fires. 6 — if logo. 7 —
     if a location is known. 8 and 9 — always (use the per-field default line when nothing is
     known). 10 — if any person is in frame, except the non-photoreal faceless handoff drops it;
     plain rig by default, the colored-rim variant ONLY when the USER names a rim color.
   - `<ratio note>` = "`<ratio>` aspect ratio". For 9:16 append the tall-canvas clause; with no
     people in frame say `the hero subject in the upper two-thirds` instead of `faces`.
   - Expression slot = the PARENTHETICAL descriptor of the chosen emotion preset (shock →
     `mouth open gasp, wide eyes`), or the user's custom phrase verbatim. Append the
     reference's `emotion_detail` sentence ONLY on the variant(s) using the reference's own
     emotion — user-overridden emotions use the preset parenthetical alone.
   - **Split branch:** fires per the Trigger rule in "Split frames" (below) — layout asks only;
     `X vs Y` as a SCENE stays one unified frame. When it fires, the split contract
     replaces block 1 and counts as it.
   - Variants = emotions × takes, hard cap 16; no person in frame → the Expression axis is
     empty and variants = takes. Variants differ ONLY by the Expression phrase and/or one
     ALTERNATE TAKE line.
6. **Submit:** every variant gets its own distinct prompt and exactly one job. For one variant,
   call `generate_image` so the result widget renders immediately. For two or more, call
   `generate_image_batch` in groups of at most six with stable indices, then use `jobs_wait` and
   one final `show_generation_by_ids`. NEVER use `count` to multiply a variant. `medias` lists one
   entry per asset (characters first, then the logo) and is omitted when empty:

```
generate_image({ params: {
  model: "nano_banana_pro", prompt: "<variant prompt>", aspect_ratio: "<ratio>",
  resolution: "4k", medias: [ {value: "<character-id-1>", role: "image"},
                              {value: "<logo-id-or-3d-job-id>", role: "image"} ] } })

generate_image_batch({ requests: [
  {index: 0, params: {model: "nano_banana_pro", prompt: "<variant 0>",
   aspect_ratio: "<ratio>", resolution: "4k", count: 1, medias: [...]}}
] })
```

   With 2+ medias the FIRST prompt line is the manifest:
   `IMAGE REFERENCES: image 1 = CHARACTER 1 face reference; image 2 = brand logo.`
7. **POST-RENDER CHECK on every image:** (a) IF face or character references exist — identity and
   character design visibly match them; (b) baking NOT ordered → no stray text/watermark anywhere; (b2) baking ordered →
   the rendered text matches the ordered string character-for-character; (c) the Expression
   (when a subject has one) and the hero element still read at ~120px wide. For faceless
   `provider-first`, a text mismatch does not enter the generic same-prompt retry loop: generate
   one clean no-text recovery render of the same concept and continue to deterministic overlay in
   step 9. Any other failure → re-render the SAME prompt (max 2 retries per variant); still failing
   → report it honestly, never ship silently.
8. **IF the user asks for tweaks:** use the "Surgical tweaks" prompts verbatim in a new
   `generate_image` call on `seedream_v5_pro`, `resolution:"2k"`, i2i
   `medias:[{value:"<picked job_id>", role:"image"}]`.
   Submit error OR model absent from the catalog → retry ONCE on `seedream_v4_5` with
   `quality:"high"`, same prompt. Each accepted output's job id feeds the next tweak.
9. **Export and present every variant that passed step 7**; "picked" = the user's choice
   (user doesn't choose → deliver all). No text supplied → deliver the clean renders as-is.
   Headline text supplied and text was NOT explicitly baked into generation, or faceless
   `provider-first` entered exact-text recovery → bake the
   deterministic overlay into a flat PNG; a browser-only preview is not a deliverable:
   - inspect the picked render and choose `top`, `bottom`, `left`, `right`, or `center` so the
     headline occupies a free quarter and never covers the face;
   - choose one Text policy style (`beast` default, `fire`, `neon-lime`, `clean-glass`, or
     `marker`), and keep the headline to 2–6 words;
   - call `media_upload({filename:"thumbnail.png",content_type:"image/png"})` BEFORE the
     producing sandbox call;
   - this reserve is stateful and single-use: record the first successful `media_id` and
     `upload_url`, then reuse that exact pair. For one picked variant call `media_upload`
     exactly once and `media_confirm` exactly once. Never reserve again to rename the file,
     never request a second slot after a successful reserve, and never repeat a successful
     confirmation;
   - in ONE `sandbox_exec`, download the picked render and run the bundled native-resolution
     canvas recipe, then verify and upload the result:
     ```bash
     set -e
     curl -fL --retry 3 '<picked_result_url>' -o work/thumbnail_clean.png
     printf '%s' '<headline_base64>' | base64 -d > work/headline.txt
     TEXT_CASE=upper # use preserve only for faceless provider-first exact-text recovery
     node "$HF_WORKFLOWS/thumbnail-generation/scripts/bake_text_overlay.mjs" \
       --image work/thumbnail_clean.png --text-file work/headline.txt --style beast \
       --position bottom --case "$TEXT_CASE" --out work/thumbnail.png
     [ -s work/thumbnail.png ]
     code=$(curl -sS -o /dev/null -w '%{http_code}' -X PUT \
       --upload-file work/thumbnail.png '<upload_url>')
     [ "$code" = "200" ]
     ```
     Encode the exact headline as UTF-8 base64 before constructing the command; never interpolate
     user text into shell syntax. The base64 placeholder contains only shell-safe characters.
     Ordinary overlays keep the source recipe's `upper` default. Set `TEXT_CASE=preserve` only for
     faceless provider-first recovery so the promised hook remains character-for-character exact.
     Only after HTTP 200 call `media_confirm({type:"image",media_id:"<media_id>"})` once, and
     deliver its confirmed hosted URL. Repeat the reserve → bake/PUT → confirm sequence per picked
     variant, never within the same variant.

### PRE-SUBMIT CHECKLIST (verify before every generate call; any NO → fix the prompt first)

- [ ] Right model for the call: main render `nano_banana_pro` + `resolution:"4k"` · tweak →
      seedream per step 8 · 3D logo → `gpt_image_2` per step 4
- [ ] Block 1 (or its Split / non-photoreal faceless substitution) is the FIRST prompt block;
      GRADE is the LAST when block 11 applies, while a non-photoreal faceless handoff omits it
- [ ] Person in frame → LIGHTING rig present (the selected plain/colored variant, verbatim) +
      an Identity Lock per face photo, except a non-photoreal faceless handoff uses its supplied
      medium and character-design lock with no photographic lighting block
- [ ] Reference thumbnail NOT in `medias`
- [ ] Each ordinary call or batch request renders exactly ONE variant; batch `count` is `1`
- [ ] Baking not ordered → the prompt contains `No text, no readable UI labels, no watermark.`

### Per-field defaults (apply to ANY field both the user and the reference left empty)

- ratio `16:9` · takes 1 · emotion `shock` when a person is in frame; no person → the Expression
  axis is empty and variants = takes
- BACKGROUND: `bold, vivid saturated color-field gradient with punchy high-contrast tones matching the subject's palette, soft
  vignette, edge falloff`
- COMPOSITION: `the subject rendered LARGE and dominant — chest-up / medium-close, filling ~40–60% of the frame, pushed to the foreground on a power third, camera at eye level, strong separation from the background so the subject pops, shallow depth with a foreground accent element`
- KEY ELEMENTS: the most concrete depictable noun of the user's topic (your judgment),
  oversized, flying toward camera — omit when it would duplicate the SUBJECT
- LOCATION: omit the block

## Thumbnail frameworks (the concept layer — pick BEFORE assembling the prompt)

The "what to depict" layer lives in a reference: the 16 engaging thumbnail frameworks, the
information-gap principle, combining, and the truthfulness law. Load it on demand and pick the
framework(s) in EXECUTE step 1:

`references/thumbnail-frameworks.md` in this installed skill

Most frameworks map straight onto the house-structure blocks below; the ones needing readable
in-image text use the BAKED UI clause in the Text contract (block 3).

## Model routing

| Task | Model | Settings |
|---|---|---|
| Main thumbnail render | `nano_banana_pro` (Nano Banana Pro — Google's ultimate-quality tier; NOT `nano_banana_2`, which is the faster "Flash"/base tier) | `resolution: '4k'`, ALWAYS 4K (the model default is 1k — pass `4k` explicitly); batch via separate prompts, not `count` |
| 3D logo from a flat 2D logo | `gpt_image_2` | `quality: 'high'`, `resolution: '4k'`, `aspect_ratio: '1:1'` |
| Surgical edits on a finished render (emotion/background/colors) | `seedream_v5_pro` (top Seedream tier; **paid plans BASIC+ only**) | `resolution: '2k'`; i2i chained off the finished render; on a free plan or a catalog miss fall back to `seedream_v4_5` (`quality: 'high'` ≈ v5 2k) |

**Unlim clash — 4K is normally not covered by an unlimited grant.** Pass `use_unlim:true`
only when the user explicitly asks. If the request returns `unlim_choice` or a typed uncovered
configuration, ask whether to use the covered resolution or keep 4K on credits, then resubmit the
unchanged creative request with that answer. Never silently downgrade and never silently charge.

**Aspect ratios (always 4K):** 16:9 (YouTube), 4:3, 9:16 (Shorts 3072×5504), 4:5 (Instagram 3712×4608 — native on Nano Banana only; Seedream has NO 4:5, downgrade tweaks to 3:4 and disclose). Multi-reference submits: up to 14 images; prepend an "IMAGE REFERENCES:" manifest to the prompt numbering each image and its role.

## House prompt structure (assemble in THIS order)

1. **Frame contract** — `Bold, punchy YouTube-thumbnail composite — poster-grade, photoreal and high-impact, NOT a muted cinematic movie still, <ratio note>, single unified frame — no split-screen, no diagonal divide, everything blends smoothly and organically across the same continuous shot.` For 9:16 add `subject framing adapted to the tall canvas, faces in the upper two-thirds`. Framework 8 "Graphical Representation" replaces this with a clean diagram/graphic brief and drops the photoreal + lighting-rig blocks. A non-photoreal faceless Phase-8b handoff makes the same replacement using its supplied render medium and also drops the glossy grade.
2. **Scene brief** (if the user described exact content): `SCENE BRIEF (must be depicted exactly): <text>.`
3. **Text contract** — default: `No text, no readable UI labels, no watermark.` Only when baked text is explicitly wanted: `TEXT: bold thumbnail headline text baked into the image, reading exactly "<TEXT>" — massive, ultra-legible sans-serif with a clean outline/glow treatment, placed where it never covers the subject's face. No other text, no watermark.` When the user EXPLICITLY asked for a text-based framework that carries an in-image UI element (Social UI, News Clip, Day badge, Map/Aerial callout — see the frameworks reference), add instead: `BAKED UI: a <generic chat bubble / DM row / star-review card / breaking-news lower-third / DAY N badge / map callout label> reading exactly "<short text>", clean generic platform styling — NO real brand name, app name or network logo. Keep the text short and truthful to the video.` A text-carrying framework that was only auto-picked (not explicitly requested) renders text-free instead. This is the ONLY sanctioned readable text besides the headline; every other prop stays text-free and wordmark-free.
4. **SUBJECT(s)** — see Identity Lock below. Up to 3 characters; photo characters map positionally onto attached face references. **Render the subject LARGE and dominant — the clear hero, filling roughly 40–60% of the frame, chest-up or medium-close, pushed to the foreground and cleanly separated from the background; NEVER a small subject stuck in the lower third, never a distant video-frame look.** End with `All faces crisply sharp as the anchors of the shot.`
5. **KEY ELEMENTS** — signature props/effects that make it pop.
6. **LOGO** (if any) — 2D: `the attached logo placed into the composition EXACTLY as provided — keep its shapes, colors and proportions untouched, clean 2D placement at a strong focal position, subtle drop shadow for separation, never covering the subject's face.` 3D: `the attached 3D logo render integrated into the scene as a physical volumetric object — glossy dimensional material, catching the scene's key light and rim light, casting a soft contact shadow, composited at a strong focal position without covering the subject's face.`
7. **LOCATION** — place, time of day, weather, atmosphere.
8. **COMPOSITION** — subject LARGE and foreground-dominant (fills ~40–60% of the frame, chest-up / medium-close) on a power third, strong subject-vs-background separation so the subject pops off the background; scale hierarchy, camera angle, depth layering.
9. **BACKGROUND TREATMENT (blended, not divided)** — bold saturated color field, vivid punchy gradients, strong color contrast, texture, blur, edge falloff.
10. **LIGHTING (the YouTube rig — mandatory on people)** — `signature YouTube thumbnail lighting rig on the subject — a strong KEY LIGHT sculpting the face with crisp highlights and controlled falloff, a soft dreamy DREAM LIGHT fill lifting the shadows with a subtle cinematic glow, and a defined BACK LIGHT + HAIR LIGHT tracing a clean bright rim along the hair, shoulders and silhouette, separating the subject sharply from the background.` Colored rim variant: replace last clause with `a defined <color> BACK LIGHT + HAIR LIGHT tracing a vivid colored rim ... with a subtle matching glow.` Rim palette: Ice Blue `#4DA6FF` "electric ice-blue", Neon Magenta `#FF3DBE` "hot neon magenta", Toxic Lime `#C8FF2E` "toxic neon lime", Amber Gold `#FFB63D` "warm amber-gold", Pure White. Key/fill NEVER change color — only back+hair.
11. **GRADE** — `vivid high-impact color grade, punchy high contrast, bright clean exposure, rich saturated colors that pop off the screen, deep blacks and bright highlights, crisp and glossy, poster-punchy, cohesive as one image. <ratio>.` Dial back to a restrained / soft / low-contrast grade ONLY on an explicit calm / premium / muted / aesthetic request.

## Identity Lock (anti face-drift — REQUIRED per photo-referenced person)

Soft phrasing ("keep face and identity exact") is NOT enough — models drift. Per character with a face photo emit:

> CHARACTER N: the person from attached face reference #K — IDENTITY LOCK: reproduce this exact person with a photographic identity match — same bone structure, eye shape, nose, lips, jawline, skin tone, hairline and hair texture as the reference photo. Do NOT beautify, do NOT average with other faces, do NOT restyle the face; it must be recognizably the same person at a glance. Expression: `<emotion phrase>`.

Drift still happens occasionally (stochastic) — the recovery is re-render.

## Emotion casting (11 presets)

**shock** (mouth open gasp, wide eyes), **hype** (ecstatic grin, blazing eyes), **fear** (terrified stare, frozen breath), **confusion** (one brow raised, puzzled), **determination** (locked jaw, laser focus), **smug** (knowing smirk), **charisma** (calm magnetic gaze, relaxed brows, faintest composed half-smile — charismatic leading-man poise, confident but never aggressive; the calm positive option — "determination" alone reads too harsh), **disgust** (recoiling grimace), **awe** (jaw dropped, glittering wonder), **rage** (bared teeth fury), **laugh** (head back).

The emotion phrase used in Expression slots = the preset's PARENTHETICAL descriptor. A custom user phrase replaces the preset phrase verbatim (`Expression: <custom>`). When the user gives an emotion COUNT without naming them, take the first N of this ladder: shock → hype → rage → awe → laugh → fear → smug → charisma → confusion → determination → disgust. When offering emotion choices interactively, always include an Other/custom option.

## Takes per emotion (camera variations)

Take 1 = designed framing (no modifier). Takes 2–4 append one line each:

- `ALTERNATE TAKE: reframe as a low-angle hero shot — camera below eye level looking up, the subject towering with extra dominance, background perspective stretching upward, same scene and lighting.`
- `ALTERNATE TAKE: extreme close-up punch-in — the face and expression dominate more than half the frame, background compressed into soft bokeh context, same scene and lighting.`
- `ALTERNATE TAKE: wider dynamic shot with a subtle dutch tilt — more of the environment visible, subject anchored off-center on a power third, stronger motion energy sweeping the frame, same scene and lighting.`

Total variants = emotions × takes (hard cap 16). Each variant = its own ordinary call or indexed
batch request with a distinct prompt (never one `count:N` submit).

## Split frames

Trigger (EXECUTE step 5): fires ONLY when the user asks for a split/panel LAYOUT — "split",
"before/after", "versus screen", "side by side" — or the reference analysis
returned `split=true`. `X vs Y` as a SCENE means one unified frame with both subjects — NO
split. N = the number of contenders/states/facets named (before/after and versus default to 2);
N=2 → `halves`, N≥3 → `vertical panels`. The split contract REPLACES block 1 (the substitution
counts as block 1) and carries `<ratio note>` and the 9:16 tall-canvas clause exactly as
block 1 would.

Replace block 1 with: `SPLIT-FRAME thumbnail, <ratio note>: the frame divided into N
<halves|vertical panels> by clean bold seams, each panel its own complete mini-scene, unified
premium grade across all panels.` — then append exactly ONE mode sentence:

- **plain**: `Each panel shows one facet of the story: <panel 1: desc; panel 2: desc; ...>.`
- **before/after**: `LEFT panel: the BEFORE state — <desc>. RIGHT panel: the AFTER state —
  <desc>. Maximum visual contrast between the two states of the same transformation.`
- **versus**: `Each panel presents one contender lit and framed like a fighter poster:
  <panel 1: contender A desc; panel 2: contender B desc>. Equal visual weight, confrontation
  energy across the seam.`
- **custom**: `<the user's panel-by-panel description>.`

ALWAYS append: `No labels, no captions, no words, no numbers on or between the panels — the
comparison reads purely visually. All panels graded as one premium image.`

## Text policy

Default: NO text in the image — deliver the clean render; headline text belongs in a crisp typographic overlay layered on top (zero generation credits, always legible). Bake text into the generation ONLY when the user explicitly asks (then use the TEXT block from the house structure) — generative type is the fallback, not the default. The one workflow exception is a faceless Phase-8b `provider-first` handoff: use its locked exact `TEXT` contract in the first provider render, validate the rendered characters, and use the clean-render deterministic-overlay recovery above only when that text mismatches. When the user EXPLICITLY asks for a text-based framework (Social UI / News Clip / Day badge / map callout), that in-image text uses the BAKED UI clause (block 3) — short, truthful, brand-generic. Never bake it just because such a framework was auto-picked while exploring.

5 proven overlay styles (art direction for whatever surface renders the text): **Beast** (Anton white + heavy black stroke + drop shadow), **Fire** (yellow→orange→red gradient + dark stroke + warm glow), **Neon Lime** (`#D4FF3F` + lime glow), **Clean Glass** (Inter 800 on frosted blur pill), **Marker** (black Anton on lime line-boxes).

The full HTML/CSS + canvas-bake recipe for these 5 styles — exact stroke/shadow/gradient values,
the critical `paint-order: stroke fill`, font-load-before-draw, and 4K export — lives in
`references/text-overlay-bake.md` in this installed skill. The executable implementation is
preinstalled at `$HF_WORKFLOWS/thumbnail-generation/scripts/bake_text_overlay.mjs`; use it for
the default post-generation overlay. Baking text INTO generation remains the explicit-ask
fallback except for the locked faceless Phase-8b provider-first path.

## Surgical tweaks on a finished render (Seedream i2i)

Feed the FINISHED render back as the i2i input (pass the completed job's id as `value` in `medias`). Every tweak prompt must state everything else stays pixel-faithful.

- **Emotion swap:** `Change ONLY the person's facial expression ... to: <phrase>. Keep identity, face structure, hair, pose, body, clothing, logo, background, lighting and composition EXACTLY unchanged, pixel-faithful — pure expression swap. Keep the YouTube thumbnail lighting rig intact.`
- **Background swap:** `Replace ONLY the background with: <desc>. Keep subject, face, identity, pose, clothing, logo and all foreground elements EXACTLY unchanged. Rebuild the lighting wrap around the subject so the new background's light direction, color and rim light read naturally — keep the YouTube rig.`
- **Background recolor:** `Shift ONLY the background color palette to dominant <color> tones. Keep the background's structure, content and depth exactly — only recolor. Rebuild the subtle ambient color wrap on the subject's edges but keep key light and fill on the face unchanged.`
- **Rim light recolor:** `Change ONLY the back light / hair light (rim light) color on the subject to <phrase> — the bright edge tracing hair, shoulders, silhouette. Do NOT change key light or fill; do NOT change background, pose, identity, clothing, logo, composition.`

Tweaks chain — each output becomes the new picked source.

## 3D logo prompt (GPT Image 2)

> Transform the attached 2D logo into a premium 3D logo render: extrude the exact logo shapes into glossy dimensional volumes, keep every letterform, proportion and brand color EXACT, high-end CGI product-render finish with soft studio reflections, subtle bevels, crisp edges, floating on a clean dark neutral studio background with a soft contact shadow. Centered, generous margins, no extra text, no watermark.

Run it in the background, don't block the flow; the final render waits for it.

## Reference analysis contract (vision → scene)

Extraction is done with YOUR OWN vision — look at the attached reference thumbnail and produce
STRICT JSON with exactly these keys and nothing else:

```
brief (one dense sentence on the concept), subject (pose/action generically, NEVER a specific
identity), elements, location, composition, background, split (boolean), split_count,
person_count (0-3), emotion (one of the 11 presets or 'other'), emotion_detail (one vivid
sentence covering eyes, brows, mouth, head angle)
```

The reference drives energy/composition/style — it is NEVER sent to the generation model itself and never enters `medias`; fill any scene field the user left empty with derive-from-reference instructions ("mirror the reference's framing logic...").

## Pitfalls

- 4:5 exists only on Nano Banana; NO Seedream tier has 4:5 (v5_pro: 1:1, 4:3, 16:9, 3:2, 3:4, 9:16, 2:3; some model tables also list 21:9 — verify via `models_get` when it matters; the load-bearing fact is: NO Seedream tier has 4:5) — tweaks on a 4:5 render go to 3:4 (disclose the downgrade).
- `seedream_v5_pro` is gated to paid plans (BASIC+) and has already been pulled from the catalog once (2026-07) — if the submit errors or the model is absent, fall back to `seedream_v4_5` (quality 'high' ≈ v5 2k) instead of retrying.
- Faces drift even with the Identity Lock (stochastic) — inspect every render against the face reference before showing it; the fix is a re-render, not an apology.
- One submit per variant: batching via `count` breaks per-variant prompts (emotions/takes each need their own prompt).
- Final readability test: a thumbnail competes at ~120px wide in a sidebar — the emotion and the hero element must still read at that size; if they don't, the composition (not the resolution) is wrong.
