# User-supplied inputs

Read this in Phase 0 whenever the user supplies media that is not the host source, and
reuse those findings during host and editorial planning.

The host-source routes (image keyframe, video avatar, photograph bootstrap) are owned by
[keyframe-prep.md](keyframe-prep.md) and [ai-avatar-creating.md](ai-avatar-creating.md)
and are out of scope here. This file owns everything else the user hands over: a product
the episode is about, a prop, reference photos of a place or document, b-roll, a logo,
an authored intro or outro, a sting, a music track.

## Inspect non-host video inputs

Every video file or public video link routed here as a motion/style reference, subject
media/b-roll, or a finished timeline segment must be inspected with the runtime video-inspection sequence
before it informs the script, motion direction, generation plan, or edit plan:

- pass a supported public video URL directly as `video_source`;
- pass an attached/local video through the owning route's normal ingest and
  compatibility requirements, then analyze the resulting video source;
- focus the prompt on its classified role. For a motion/style reference, extract
  timestamped evidence about composition, typography, palette/material treatment,
  transitions, movement, pacing, and the reusable visual grammar rather than copying
  the video's subject matter;
- record the source URL/path and the role-specific findings in the owning run artifact:
  `brief.json.motion_style` for art direction, or the supplied row and edit plan for
  subject media and timeline segments.

Derived text, metadata, preview images, or information about the hosting page may
supplement the result but never replace analysis of the video's audiovisual content.
If the runtime video-inspection sequence cannot read the source after its normal retry, state the failure and
ask for another supported link or an uploaded video; do not infer the video's content
from indirect evidence.

## Two rules

- **In-frame rule.** A physical object the episode is about belongs in the host's hands
  and on the host's body, carried by the host generations themselves. A supplied product
  composited over a finished master while the host never touches it does not satisfy a
  review or demo brief. A graphic treatment of that product is additive and allowed on
  top of real handling; it is not a substitute for it.
- **No silent drop.** Every supplied file is classified, routed, and named in the requested
  plan review with the place it lands — or the user is told in one sentence why it cannot be
  used (wrong kind, unusable quality, contradicts the approved script). Leaving a
  supplied file unmentioned is a stop condition, not a simplification.

## Intake classification

Classify each supplied file once, before the plan is authored. The kind of information
the file carries decides the route, never its container: a supplied `.mp4` of a product
rotating is subject media, a supplied `.png` end-card is frame furniture.

| Supplied                                                                                                             | Route                | Lands in                                                       |
| -------------------------------------------------------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------- |
| The product/prop the episode is about, handled or worn on camera                                                     | **in-scene object**  | object reference → extra `image` on host jobs       |
| A concrete subject to be inspected but not handled (a place, a document, a screenshot, a chart, third-party footage) | **subject media**    | `visual-plan.json.supplied` + a beat in `edit-plan.md`         |
| Logo, watermark, lower third, end card, subscribe animation, brand font                                              | **frame furniture**  | `edit-plan.md` + `edit.jsx` graphics                           |
| Finished intro, outro, bumper, transition, teaser                                                                    | **timeline segment** | `spine-layout.json` slot + `edit-plan.md`                      |
| Music track, sound logo, jingle                                                                                      | **audio**            | `visual-plan.json.supplied` (`music-bed` for a bed)            |
| Style/brand references ("make it look like this")                                                                    | **art direction**    | `brief.json.motion_style` `custom` route, per SKILL.md Phase 0 |

Ask only when a file is genuinely ambiguous between two routes — a branded mug that
could be the subject or a prop, a looping logo that could be furniture or a segment.
Fold that into the one grouped episode question; never open a separate turn per file, and
never ask whether a supplied asset should be used at all.

Upload every in-scene or subject file once with the runtime upload sequence, keep the exact
response, and copy the local file inside the run directory before approval. Web-origin
media still requires the recorded consent from `generation.md` § _Web-sourced media_.

## Analyze the object before planning it

An in-scene object is analyzed before its plate is generated and before the episode plan
is authored. Guessing how a thing is held, opened, and operated is what produces a host
who waves a product vaguely instead of using it.

Route through the existing `product-data-extraction` skill and load only the reference
that matches the input:

```
Inspect the supplied product image with host vision; retain only observed details.
Read the authorized product page with available host research or sandbox tools; retain attributable product facts.
```

- **Photo mode** returns the product category, its **usage mechanic**, its **opening
  mechanic**, and the key visual details to preserve. Its mechanic list is written around
  cosmetics; for anything outside it — a wearable, a device, a tool, a case — name the
  mechanic in the same concrete form (`worn over both ears`, `clipped on`, `unfolded`,
  `switched on with the side button`, `slid out of its case`) rather than falling back to
  "holds the product".
- **URL mode** returns structured product data plus curated product images. Use those
  images as plate input when they are cleaner than what the user attached, and use the
  factual claims — materials, construction, named features — as script substance. Do not
  read price, SKU, or marketing superlatives into the spoken script unless the user asked
  for them.

Record the result in `product/manifest.json` alongside the plates:

```json
{
  "category": "over-ear headphones",
  "usage_mechanic": "lifted onto the head, cups over both ears, headband across the top",
  "opening_mechanic": null,
  "key_details": [
    "knit mesh canopy headband",
    "anodised aluminium cups",
    "crown control on the right cup"
  ]
}
```

The analysis is load-bearing in three places: `key_details` are what a repair-plate prompt
preserves, `usage_mechanic` is what the `in_use` state actually shows and what the shot
label describes, and `opening_mechanic` — when the object has one — adds an `opened`
state that must be on screen **before** any contents leave the container.

### Research the product before writing about it

Photo analysis gives shape and mechanic; it cannot give what the thing actually is. A
review that only describes what is visible reads as a stranger holding a box. Once the
object is identified — brand and model read off the object, named by the user, or taken
from a supplied URL — research it with available host web search and available host source reading under the sourcing
rules already in [script.md](script.md): prefer the manufacturer's own pages and other
authoritative sources, and inspect them rather than trusting a search snippet.

Record what you found next to the analysis, with the source per claim:

```json
{
  "identified_as": "Apple AirPods Max (USB-C, 2024)",
  "researched_facts": [
    {
      "claim": "USB-C replaces Lightning",
      "source": "https://www.apple.com/…"
    },
    {
      "claim": "wired lossless audio over USB-C",
      "source": "https://support.apple.com/…"
    }
  ],
  "unverified": ["battery life figures vary by review"]
}
```

Rules:

- **Every spoken factual claim traces to the user's own script or to a recorded fact.**
  Nothing enters the script because it sounds plausible for the category — no invented
  specifications, benchmark numbers, release dates, or comparisons.
- Skip research when the user supplied review copy that already carries the claims: their
  wording is approved speech and is not rewritten. Research then serves only visual
  accuracy — the object's real details and mechanic.
- Disputed or review-dependent numbers go in `unverified` and stay out of the host's mouth,
  or are spoken as the range they are.
- No price, SKU, or marketing superlative unless the user asked for it.
- Research informs the script and a repair plate, never the object's appearance in a
  prompt: the reference stays the appearance.
- If the object cannot be identified with confidence, say so and write from what is visible
  rather than guessing a brand.

## Run artifacts

```text
inputs/manifest.json          # one row per supplied file: path, kind, route, upload id
inputs/upload-receipts.json   # exact confirmed upload responses for supplied media
inputs/source/                # untouched copies of what the user supplied
product/manifest.json         # in-scene objects: plate id, wearability, arc by host job
product/plate-plan.json       # the exact plate request, when a plate is generated
```

`inputs/manifest.json` rows:

```json
{
  "version": 1,
  "inputs": [
    {
      "id": "product-headphones",
      "path": "inputs/source/headphones.png",
      "kind": "in_scene_object",
      "origin": "user",
      "media_id": "<upload id>",
      "route": "host_medias",
      "notes": "over-ear headphones, worn on camera"
    }
  ]
}
```

## In-scene objects

### One principle: the reference is something real

Every appearance question about an object is answered by real material first. Synthesis
repairs what real material cannot serve — it never replaces it. Three applications of the
same rule, and nothing below departs from it:

| Question                                                                    | Answered by                            | Synthesis only when                                               |
| --------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------- |
| What does the object look like?                                             | the file the user supplied             | that file cannot serve as a reference — then one **repair plate** |
| How does it sit on the host, worn or in use?                                | the `in_use` job, rendered on camera   | the rendered fit is wrong or drifts — then one **worn plate**     |
| What does an accessory or rival SKU look like that the user did not supply? | an official / press-kit image, sourced | **never** — the claim stays spoken instead                        |

A generated image of a real object is a liability the moment it stops being a faithful
copy: it looks authoritative and can be wrong. So the bar for making one is that the real
material has failed, and the output is a cleanup, never a redesign.

### The object's reference

**Default: the supplied file is the reference.** Upload it, attach it, done — no
generation. It is the most accurate depiction of that exact object that will ever exist in
the run, and in a clean supplied shot a plate buys nothing while risking a subtly altered
object.

**Repair plate — only when the supplied file fails one of these:** it is a collage of
several angles in one frame · it carries a watermark, price badge, or overlaid text · a
hand or model is holding it · the background is busy enough to leak into downstream frames
· it is too small or soft to read the object's markings · several different objects share
the frame.

Then generate one repair plate with `generate_image_batch` (one indexed entry,
`count: 1`). Resolve a reference-capable image model and its supported settings from
the live catalog; request a square plate when supported, attaching the upload with
role `image`. Do not assume a model id, quality enum or resolution from another runtime. The prompt reproduces the object and changes nothing about it: same
shape, proportions, materials, colourway, finish, logo shape and position, same visible
controls and seams, plus every entry in `key_details` from the analysis; isolated on a
plain neutral background, even frontal studio light, natural three-quarter angle, sharp
across the object. Preserve markings already printed on the object; add no captions,
price badges, watermarks or other graphic overlays. Resolve `key_details` into the
actual visible details before submitting; the provider does not read the analysis file.
A plate is a cleanup, never a redesign — do not restyle, recolour, modernise, or invent
a detail the source does not show; if a detail is unreadable in the source, leave it
unstated rather than guessing.

One reference per distinct physical variant that appears on screen. Angle variation inside
the episode is the video model's job, not a second image. Record a repair plate in
`product/plate-plan.json` and `assets.json` with `purpose: "product_reference"` — never in
`visual-plan.json`. A plate is consumed as a generation
reference and is never shown to the viewer: it is exempt from the editorial rule against
unused paid assets, it is reference-only for coverage decisions, and it must not appear in
`edit-plan.md` as a treatment.

Inspect a finished repair plate with host image inspection and compare it against the supplied
file before it is used anywhere: if it altered the object, the supplied file goes back to
being the reference. A wrong colourway caught here costs one image; caught after the host
jobs it costs the episode. When a repair plate is made, its authorized generation and inspection therefore happen before the exact host prompts and their
appended media ids are finalized, and the later grouped requested plan review reports it as
completed reference cost and approves only the remaining host/supporting requests.

### The worn state is established on screen, not pre-generated

For anything worn or carried, the object's look is already locked by its reference. How it
sits on this host does not need a second synthetic image by default: the job that performs
the `in_use` transition puts it on **on camera**, and that rendered result is the truth
every later job continues from.

So the default is: no worn plate. The transition job attaches the object's reference and
describes the fit from `usage_mechanic`; every later job with that host keeps that
reference attached and restates the worn condition in the `performance` of every shot that
shows the host.
A synthetic plate of the host wearing the object risks a fit that contradicts what the
video actually produced, and it is a paid generation the happy path does not need.

**Fallback — generate a worn plate only when the run needs it:** the transition job comes
back with the object worn wrongly, or the fit drifts between later jobs. Then generate one
plate with **`nano_banana_pro`**, `aspect_ratio` `3:4`, `resolution` `2k`, attaching the
host reference first and the object's reference second, both with role `image`:
the same host, identity unchanged, wearing or holding the object with the concrete
observed fit or grip from `usage_mechanic`. Spell out that physical action in the prompt;
the field name and analysis document stay outside it. Use a plain backdrop so nothing
of its background can leak into a rendered shot. `nano_banana_pro` takes `resolution`
(`1k` / `2k` / `4k`) and has no `quality` parameter — do not copy the `gpt_image_2`
parameter pair onto it. If that plate keeps the host but alters the object, re-run that one
plate on `gpt_image_2` before touching anything else in the chain.

Do not try to carry the transition job's own frame forward instead: an extracted frame is
forbidden as provider input ([keyframe-prep.md](keyframe-prep.md),
[ai-avatar-creating.md](ai-avatar-creating.md)), and every primary job keeps the canonical
manifest reference id.

### Attaching to host jobs

The canonical host reference keeps its position and role; supplied object media is
**appended** to `request.medias`:

```json
{
"medias": [
  { "value": "<keyframe or avatar media id>", "role": "image" },
  { "value": "<object reference: supplied media id, or repair plate job id>", "role": "image" },
  { "value": "<worn plate job id, only when the fallback was needed>", "role": "image" }
]
}
```

- The canonical reference stays first with its recorded id and role; append additional
  object references after it.
- The mandatory opening declaration is unchanged — the prompt still starts with the exact
  `@Image 1` or `@Video 1` sentence required by the recorded reference mode. Never
  rewrite that sentence to mention the product.
- Reference tokens are numbered inside their own media kind. In `image_keyframe` mode the
  keyframe is `@Image 1`, the object's reference `@Image 2`, and a fallback worn plate —
  when one exists — `@Image 3`. In
  `video_avatar` mode the avatar is `@Video 1` and the object's reference is `@Image 1`.
  Confirm the resolved numbering on the first completed job before submitting the rest of
  the wave; a mismatch shows up as the object replacing the host or vice versa.
- Attach the object's reference to every job where the object is on screen, and a fallback worn plate
  from the job that first puts it on onward. A job where the object is genuinely absent
  drops those entries.

### Writing the object into a host prompt

The plate carries the appearance. Name the object with a minimal noun plus its token and
let the reference do the rest.

- Write `the headphones @Image 2`, `holds the headphones @Image 2 up toward the camera`,
  `wearing the headphones as in @Image 3`.
- Do not describe its looks in prose — a written inventory of colour, material, and logo
  competes with the reference and is the fastest route to a mutated object.
- Do not write `match @Image 2 exactly` or describe the reference's background; reference framing
  never appears in the rendered shot, exactly as with the host reference.
- Do not put the brand wordmark, a price, a spec line, or any on-screen text in the
  prompt. Text belongs to `edit.jsx`; a video model renders it as broken glyphs.
- Every shot that shows the object says where it is and what is being done with it, in
  that shot's `performance`; a handling beat that must land on specific words goes in
  `actions` as `{ "on": "<verbatim phrase>", "do": "<behavior>" }`. A job that
  attaches the reference but never mentions the object drops it out of frame.
- Handling stays inside the mapped setup's framing. A product lifted into a
  head-and-shoulders accent setup leaves frame; plan handling on the setups whose crop
  contains the hands.

### Object state across the episode

An object that only sits in the set is invisible. Plan its state alongside the camera map
and record it in `product/manifest.json`, keyed by host job id:

```json
{
  "version": 1,
  "objects": [
    {
      "id": "product-headphones",
      "plate_job_id": "<plate job id>",
      "object_reference": "<supplied media id, or repair plate job id>",
      "repair_plate_job_id": null,
      "worn_plate_job_id": null,
      "wearable": true,
      "states": {
        "host-001": "present",
        "host-002": "handled",
        "host-003": "examined",
        "host-004": "in_use",
        "host-005": "in_use"
      }
    }
  ]
}
```

- `present` — in the set, untouched. `handled` — lifted and turned while speaking.
  `examined` — held toward the camera with one concrete feature indicated. `opened` —
  only for an object with an `opening_mechanic`, and it comes before `in_use`, on screen,
  before anything leaves the container. `in_use` — the analysed `usage_mechanic` actually
  performed: worn over both ears, pump pressed, cap off and product applied, switched on.
  After `in_use` the state does not go back.
- A demo or review episode reaches at least `examined`. An object that never leaves the
  table for a whole episode is a planning failure, not a style.
- `in_use` is written as the analysed mechanic, never as generic contact. "Puts them on,
  cups settling over both ears" is a state; "interacts with the product" is not.
- At most one state change per host job, and the line that carries it refers to what the
  host is doing with the object, so speech and picture agree. A silent pickup under
  unrelated dialogue reads as a glitch.
- Once `in_use`, every later job with that host keeps the object's reference attached and restates the
  worn condition in the `performance` of every shot that shows the host. Close/accent setups are where a
  worn object disappears first. Never write that the host adjusts or removes it unless
  the approved script does.
- A state change is a story beat: if it coincides with a generated-internal cut, that cut
  still owes a clear shot-size step, exactly as every other cut in the episode.
- Two objects never reach `examined` in the same job. Stagger them.

### Accessories and other SKUs the script names but the user did not supply

A review talks about more than the box it was handed: a case, a charger, a cable, a rival
model, another colourway. The moment the script makes a claim about how one of those
**actually looks** — it protects almost nothing, it is bulkier than the old one, the port
sits here — that object is a real named product and its appearance is evidence, not
decoration. `generation.md` § _Web-sourced media_ governs it: source an official or
press-kit image, download it into `inputs/source/`, upload it, and give it a reference like
any other in-scene object. Recorded web consent applies.

**Never invent such an object from prose.** A text-only generation of a real accessory
produces a plausible-looking fake — wrong shape, wrong material, wrong coverage — shown to
the viewer as what the product is. That is fabricated proof, the same failure as describing
the supplied object's appearance in words instead of attaching its reference.

If no official image can be sourced, the claim stays in the host's mouth over the supplied
object or the host alone. A spoken "the case barely covers the cups" needs no picture; a
picture of a case nobody verified is worse than none.

Two rules that follow, and that a text-only accessory prompt always breaks:

- **Any frame containing the supplied object attaches its reference.** A generation that
  shows the product with nothing attached will drift its colourway and finish — this is how
  a Starlight object comes back silver.
- **One subject per generation.** "Shown alone on a neutral surface" and "shown next to the
  headphones" in the same prompt are two different frames; the model obeys one and the
  request is wasted. Decide which frame the beat needs and ask for that one.

### Product detail and macro shots

Hands-and-object macros, port close-ups, texture detail, and the object in another
setting are **supporting media**, not host jobs. Plan them in `visual-plan.json` as
generated images or video that attach the object's reference, so the object
is the same object, and give each one its beat and use in `edit-plan.md`. This keeps the
host jobs to mapped speaking setups while the detail the script promises is still shown.

## Subject media

Supplied stills or footage of a place, document, screenshot, or third-party clip enter
`visual-plan.json.supplied` with their run-local path and `origin`. Each selected file
earns a beat in `edit-plan.md` naming the editorial purpose, the active setup,
placement relative to the host, and the base-picture relationship. Per `generation.md`
§ _Supporting media_, selection does not grant frame ownership. Assign ON-CAMERA,
VISUAL, or PLAYBACK through the canonical rule in `edit-plan.md`, then design the
composition for that role. When a claim needs authentic proof, supplied media is
preferred over a generated substitute.

If inspection rejects a supplied still or clip, keep its row and add a non-empty
`set_aside_reason` instead of selecting it in coverage. A selected row omits that
field. This records the user's input without pretending an unusable or contradictory
file belongs in the edit.

### Inspect before planning

Plan from what is actually in the file, never from its filename or the user's one-line
description. Read stills with host image inspection; read footage with the runtime video-inspection sequence — what
it shows, which moments are usable, whether it carries usable audio — and take its real
duration, resolution, and frame rate from `ffprobe`. Record the finding next to the row
in `visual-plan.json` so the beat that uses it can be justified. A clip nobody looked at
is a clip that lands on the wrong beat.

### Choose the window, don't use the whole file

A supplied clip is almost never used end to end. Record the chosen in/out per use so
measurement and `edit.jsx` read the same numbers, and let the `edit-plan.md` beat say why
that window:

```json
{
  "id": "broll-workshop",
  "kind": "supplied",
  "media_type": "video",
  "path": "inputs/source/workshop.mov",
  "origin": "user",
  "uses": [
    {
      "beat": "the assembly line claim",
      "source_from": 12.4,
      "source_to": 15.1
    }
  ]
}
```

One file may serve several beats with different windows; each use is its own entry.

### Original media

Import the untouched supplied video directly; higgsedit owns media compatibility for
build, render, and editor sync. For stills, check the pixel size against the intended
crop — a small image is composed at its real size or dropped, never upscaled to fill
the frame.

### Audio ownership

B-roll under host speech is muted by default. Keep its natural sound only where the
approved beat says so, and state there how the music bed behaves. Host speech is never in
competition with b-roll audio, and a supplied clip never silently takes over the master's
sound.

### Everything supplied goes into work

A file the user handed over is material they expect to see used. The default is that
**every supplied still and clip gets at least one beat**, not that the strongest few are
picked and the rest quietly disappear. Finding a place for a file is the job; discarding
it is an exception that has to be named.

Setting one aside means keeping its row and filling `set_aside_reason` rather than
selecting it in coverage, as the intake rules above require. That reason must be one of
these, and only after inspection:

- **technically unusable** — corrupt, unreadably low resolution for any crop, a duration
  too short to hold a cut, audio-only where picture was expected;
- **contradicts the approved script** — it shows something the episode explicitly says is
  not the case, or a different product or place than the one under discussion;
- **duplicate** — two takes of the same action where one is clearly better; the weaker one
  is the redundant take, and this is the only reason a _usable_ file may be set aside.

The requested plan review reports the pass file by file: which are in and on which beats, which
carry a `set_aside_reason` and what it says. A set-aside file is a decision the user sees
and can overturn, never a silent omission.

**When the user explicitly says to use all of their footage**, that is a commitment, not a
preference. Every supplied file gets a beat, and if some genuinely cannot, they are named
before approval with the reason so the user decides. Do not answer an explicit "use all of
them" by shortlisting.

### Fitting more footage than the episode carries

Master duration is host speech plus approved structural slots, and stretching it silently
invalidates the music bed's generated length — so "use everything" is delivered through
composition first, extension second:

1. **Share beats.** One beat can carry several files — a sequence of short windows, a
   split composition, a stack that reveals in order, a screenshot beside the photo of the
   same thing. The beat states their order and how they share the frame. This is where
   most of a large set lands.
2. **Shorten windows.** Ten clips at one second each read as a montage; ten clips at four
   seconds each do not fit. Tighten the in/out windows rather than dropping files.
3. **Add a structural slot** — a montage or gallery slot in `spine-layout.json` with its
   own approved duration, which extends the master _explicitly_ and therefore recomputes
   the music-bed length before generation. Such a slot exists to carry real supplied
   footage; it is never an empty graphic hold invented to reach a round runtime, which
   § _Timeline segments_ forbids outright.
4. **Only if the set still does not fit**, put the choice to the user before approving the affected plan: a longer
   script, a longer montage slot, or a named shortlist they approve. Present the arithmetic
   — files, needed seconds, available seconds — not a verdict.

A montage that exists only to consume files is still bad editing: give the sequence a
purpose the script earns, and never pad it with holds to reach a duration. But "there was
nowhere to put it" is not a reason to drop a file without telling the user.

## Frame furniture

A logo, watermark, lower third, or end card is built in `edit.jsx` as a graphic over the
master, with its placement, timing, and host-avoidance region approved in `edit-plan.md`.
Supplied brand assets are used as-is; do not regenerate or redraw them. A supplied brand
font is proved like any other text-bearing treatment, through the layout-safety states in
[assembly.md](assembly.md) § _Visual implementation loop_. None of this ever enters a provider prompt.

## Timeline segments

A finished intro, outro, bumper, or transition adds master duration, so it is a
structural slot, not a host job. Empty graphic holds invented to hit a round target
duration are not timeline segments; do not create them. Write it into `spine-layout.json` as a uniquely named
slot of its measured duration, in play order around the host items, and describe its
picture and audio ownership in `edit-plan.md`:

```json
{
  "items": [
    { "kind": "slot", "id": "intro-supplied", "duration": 6.0 },
    { "kind": "host", "plan_job_id": "host-001" },
    { "kind": "host", "plan_job_id": "host-002" },
    { "kind": "slot", "id": "outro-supplied", "duration": 8.0 }
  ]
}
```

- Probe the real duration with `ffprobe` and use the measured value; never the user's
  estimate.
- Import the untouched supplied clip directly.
- A supplied clip owns its own audio. Mute the music bed under it unless the approved
  edit keeps it, and never place a segment inside a host clip: host speech stays
  continuous.
- Account for real segment slots in music planning. If they extend the master, update
  the supplied bed's crossfaded arrangement and measured length as described in
  [assembly](assembly.md#background-music). This surface does not generate music.
- A supplied transition placed between host jobs breaks the continuity the episode spine
  builds. Use one only where the user asked, and prefer chapter boundaries.

## Audio

Register a supplied music track through a `supplied` row
with `"id": "music-bed"` and `"media_type": "audio"`, and keeps the approved mix contract
(host speech at `1.0`, one `-24 dB` track attenuation). A supplied sting or sound logo
belongs to the segment it was made for, not sprinkled between host jobs.

## Review and approval

The requested plan review names every supplied file and where it lands: which host jobs carry
the object and from which job it is worn, which beats use supplied subject media, which
graphics are built from supplied brand assets, which slots hold supplied segments, and
the music source. List any repair-plate jobs as completed approved reference cost with
their purpose, so a plate is never mistaken for an unused timeline asset.

Before approval, confirm directly:

- every row in `inputs/manifest.json` has a route, and every routed file exists inside the
  run directory;
- apply the in-scene-object checks below only when `inputs/manifest.json` contains an
  `in_scene_object`; ordinary runs have no product checklist;
- each in-scene object has been analysed through `product-data-extraction`, with
  `category`, `usage_mechanic`, `opening_mechanic`, and `key_details` recorded in
  `product/manifest.json`;
- each in-scene object has a settled reference — the supplied file by default, or a repair
  plate that was inspected against it and did not alter the object; a worn plate exists
  only where the rendered fit failed, and then it was generated with `nano_banana_pro`;
- the `in_use` shots carry the recorded `usage_mechanic` in `performance` / `actions`, and an object with an
  `opening_mechanic` has an `opened` state before it;
- an identified object carries its researched facts with a source per claim, and every
  spoken factual claim traces to the user's script or to one of those facts;
- no generation invents the appearance of a real named product the user did not supply:
  accessories and rival SKUs whose look the script claims are sourced per
  `generation.md` § _Web-sourced media_, or the claim stays spoken;
- every request that shows a supplied object attaches its reference, and each request asks
  for one frame rather than two contradictory ones;
- host requests carry the canonical reference first and the object media appended, with
  the declaration sentence unchanged and the token numbering stated per mode;
- `product/manifest.json` covers every host job, reaches at least `examined`, never
  regresses, and changes state at most once per job;
- no provider prompt describes the object's appearance, no prompt contains
  `match @Image N exactly`, and no prompt contains brand text, price, or any on-screen
  copy;
- every supplied segment has a `spine-layout.json` slot with a probed duration;
- every supplied still and clip has been inspected (host image inspection / the runtime video-inspection sequence)
  with its finding recorded and a recorded in/out window per use;
- every beat using supplied footage states its audio ownership;
- every supplied still and clip is either placed on at least one beat or listed as set
  aside with a stated reason — technically unusable, contradicting the script, or a
  redundant duplicate — and that list goes into the requested plan review; an explicit "use all
  of them" leaves nothing set aside without the user's decision;
- the master is extended only through an approved structural slot, with the music-bed
  duration recomputed — never silently to fit more footage;
- the music bed still covers the master after slots were added.

## Failure modes

- **Object only in post.** Host never touches the product; the supplied image floats over
  the master. Cause: the file was classified as frame furniture instead of an in-scene
  object. Fix: plate it, append it to the host medias, plan the state arc, drop the
  overlay.
- **Object mutates between jobs.** Colour, proportion, or markings shift, or a second
  copy appears. Cause: prose description competing with the reference, or the reference attached
  to some jobs only. Fix: one plate, attached everywhere the object shows, appearance
  described nowhere.
- **An invented accessory shown as the real thing.** A case, charger, or rival model
  generated from prose comes back the wrong shape and material while the script claims it
  is what the product ships with. Cause: a real named product treated as illustrative
  filler instead of evidence. Fix: source an official image, or keep the claim spoken.
- **The supplied object drifts in a generated still.** Colourway or finish changes — a
  Starlight object returns silver. Cause: the generation attached no reference and described
  the object in prose. Fix: attach the reference, cut the appearance prose, one frame per
  request.
- **Worn object disappears.** Cause: worn plate not carried past the transition job, or
  the worn condition stated once for the job instead of in every shot's `performance`.
- **Object never leaves the table.** Cause: no state arc. Fix: place `examined` on the
  job carrying the strongest claim.
- **Host handles the object wrongly.** Sprays a tube, applies a capsule, holds headphones
  like a cup, uses a product before opening it. Cause: the arc was written from the
  object's looks instead of its analysed mechanic. Fix: run `product-data-extraction`
  first and write `in_use` from `usage_mechanic`, with `opened` before it where an
  opening mechanic exists.
- **Supplied intro has the wrong timeline length.** Cause: its duration was guessed
  instead of probed.
- **A supplied file quietly never appears.** The user asks where their footage went. Cause:
  no route owned it at intake, or it was judged weaker than the rest and dropped without a
  stated reason. Fix: classify every file at intake, then give it a beat or a
  `set_aside_reason` the requested plan review names; capacity problems go to the user as a
  choice, not a verdict.
- **A clip used end to end as one undifferentiated treatment.** Cause: no window
  selection. Fix: choose in/out ranges per beat and preserve the approved ownership
  mode.
- **The master silently grew to fit the footage.** Cause: extension without an approved
  structural slot, which leaves the music bed short. Fix: share beats and tighten windows
  first; extend only through an approved slot with the bed recomputed.
- **B-roll audio fights the host.** Cause: natural sound kept by default instead of muted
  per beat.
