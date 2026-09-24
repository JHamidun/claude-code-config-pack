# AI avatar creating

Produce the canonical host reference when no ready image keyframe or video avatar was
supplied. Enter from Phase 0 intake or from the unusable-image branch in
[keyframe-prep.md](keyframe-prep.md). Cast-from-nothing returns an image keyframe.
Create-from-photograph returns the accepted first hook clip as a video avatar and as
the already completed first host job. A user-supplied video avatar bypasses this
reference entirely and goes straight to [keyframe-prep.md](keyframe-prep.md).

Prompt examples below are authoring templates. Resolve every angle-bracket placeholder
into the selected host, room and media values. The submitted prompt contains only
concrete image/video directions; omit authoring notes, field names and references to
unseen brief files. Follow the parent episode's language and creative choices.

## Locked contract

- Output is either one 16:9 image keyframe selected from a four-candidate casting batch
  or one accepted 16:9 Seedance hook clip created from a real photograph.
- In the casting path, the still strongly influences later performance. Previous
  attempts with an open mouth produced exaggerated expressions, and hands lying flat
  on the surface produced static delivery. Keep selecting natural, usable keyframes,
  but do not treat their pose or gesture amplitude as a required limit. The image
  establishes identity and location; the clip prompt authors changing posture and
  gestures through [generation.md](generation.md).
- With a photograph, no image model is used. The photograph conditions the first real
  hook job in Seedance. The accepted complete clip—not a frame extracted from it—is
  the `video` input for every subsequent host job.
- When a photograph of a real person is the source, the hook prompt carries no
  description of that person. See "Never describe a face you already have".
- **The surface in front of the host is clear.** Nothing is placed on it and nothing
  sits in the foreground unless the user names it.
- **Casting prompts write nothing about the pose** — no hands, arms, shoulders,
  posture, or legs. Every written hand placement failed in its own direction
  (steepled, splayed, arms run out along the desk edge), while deleting the pose
  sentence entirely gave four natural seated poses out of four. Hands are policed at
  acceptance instead: resting no wider than the shoulders, elbows in, wrists loose,
  neither steepled nor fingertip-to-fingertip. Which gesture happens on which word
  belongs to the clip prompt, where it is tied to verbatim phrases.
- Cast from nothing means a batch of four, varied. Casting variance in the image models
  is larger than anything the prompt controls.
- Ask about a real voice recording only when a real photograph is used. Attach a
  supplied recording to the hook as `audio`, then let the accepted hook
  carry that voice into later jobs as part of `@Video 1`. Without a recording, the
  hook's generated voice becomes canonical in the same way.

## Intake

Resolve the source type before the grouped card. A supplied video avatar bypasses this
skill without another question.

Ask only the unresolved items together in concise normal chat. If the host exposes
a callable question UI, use its actual schema; do not invent a question tool or
assume Higgs-Pi card fields exist. Preserve the choices and checkpoints below;
plain-chat presentation does not authorize skipping the user's actual selection.

With a supplied photograph, read it with host image inspection first, then ask one grouped
card containing only two questions:

> A. Location
> On the photograph — <what the analysis found>. `keep it` / `build one` →
> `filled room — shelving, posters, objects` / `lounge` /
> `studio or editing room — professionally lit` /
> `lit studio — pale sweep or coloured pool on dark` / `bare painted wall` /
> `other — describe`
>
> B. Is there a recording of this person's voice?
> `yes — attach it` / `no`

Never offer `keep it` blind: a selfie may contain no usable room. Put `build one`
first, give one sentence of reason, and retain `keep it anyway` when the background
fills less than a third of the frame, the crop is chest-up or tighter, the picture is
an arm's-length selfie, or the frame is vertical. The model otherwise finishes a room
from scraps and alternate cameras have nothing dependable to show.

When the hands are raised into the face or the shoulder line, name it inside the same
`<what the analysis found>` sentence: the gesture in a photograph tends to arrive in
the take, and alternate angles inherit it. It changes no option on the card, and the
card still carries exactly the two questions above.

Wardrobe is not a card question. Announce: `I am keeping the clothing from the
photograph because it holds the likeness best; say if you want it changed.` If the
user volunteers a different wardrobe, follow it after explaining once that changing
the shoulder and neck silhouette can reduce likeness.

When there is no photograph, ask this three-question casting card:

Skip the relevant card when the parent workflow records explicit autonomous
delegation. For casting, infer one coherent brief from the episode language and
concept. For a supplied photograph, preserve its location and wardrobe and treat voice
as absent unless a recording was already supplied. These are run-local choices, not
permanent user preferences.

> 1. Host
>    `woman` / `man` / `I will describe them`
> 2. Age
>    `young 20s` / `mid 20s` / `late 20s` / `other — describe`
> 3. Location
>    `filled room — shelving, posters, objects` / `lounge` /
>    `studio or editing room — professionally lit` /
>    `lit studio — pale sweep or coloured pool on dark` /
>    `bare painted wall` / `other — describe`

Every preset list is an offer, and the free-text option is always live: a user who
describes their own room, look, or light in their own words is answered with that, not
steered back to a preset. The ethnicity is selected by the varied batch rather than
asked: the first four candidates are Latin American, Black, Asian, and white European;
`show me more` uses the second set defined below.

Host and age, and the ethnicity selected for each batch slot, are casting parameters.
They decide who is created and do not compete with a reference because that branch has
none. **Never ask or write them when a photograph exists** — there they become
appearance description and redraw the face.

The location fixes the lighting; never ask a separate lighting question. An ordinary
filled room, lounge, and bare painted wall use window illumination from off frame. A
studio or editing room and a lit backdrop studio use professional studio illumination.
Do not ask a casting user about wardrobe, language, accent, lens, aspect ratio, brand
marks, or gesture density. For a real photograph, voice remains the only additional
card question.

## Filled, lit studio, empty, or lounge

The location selects one of four setting geometries and changes the setting and
surface paragraphs completely. An ordinary filled room and a studio or editing room
share the filled geometry; only their props and illumination differ.

**Filled.** The wall runs the full width of the frame and is busy all the way across,
straight through the space behind the head: a dense grid of framed art prints and
posters, shelving, objects. Three object scales, all present — large (a shelving bay,
a pin board, a big plant), medium (boxes, binders, jars, a clock), small (pinned
cards, small frames, objects along a shelf edge). A wall carrying one scale reads as
repeating texture, not as a room. Objects hang on named furniture on a named side of
the frame; grouping props by size instead of by place gives the model a category with
nowhere to put it.

An ordinary room uses the neutral off-frame window sentence. A studio or editing room
uses the same filled-room density but swaps in editing desks, acoustic treatment,
monitors with smooth unmarked screens, and professional studio illumination.

**Lit studio.** Not a room and not a flat colour: a backdrop with nothing on it, shaped
entirely by light. This is the look of a product-review or unboxing channel and a
common professional host set. Describe the light, never an object. Use the exact
sub-mode the user selected:

- **Pale sweep.** A large seamless paper sweep filling the frame, written as a colour
  rather than a quantity of light: soft dove grey, deepening into slate toward the
  upper corners and far edges so the backdrop is shaped rather than flat. The sweep
  curves down into the tabletop so background and table read as one continuous studio.
  Never ask for a white sweep or describe it as bright; both produce a blown-out frame.
- **Coloured pool on dark.** A large dark background, near black at the edges and
  corners, with one broad soft pool of a single colour blooming directly behind the
  head and shoulders and falling away smoothly into darkness toward the frame edges.

For either sub-mode, the provider-facing backdrop sentence is: “The backdrop is
seamless and textureless, with no horizon line, objects or furniture.” The tabletop
is described separately below.

The tabletop gets its own paragraph and is described as a plane, not an edge: a broad
tabletop running across the bottom third of the frame, wide and completely empty, its
surface sharp and clean with nothing standing on it. For a pale sweep make it warm mid
grey and matte, a full stop darker than the face, so the lower third retains a tone.
For a coloured pool it may be white, charcoal, or pale wood and picks up the selected
colour. This differs from the room modes, where the surface is only a soft near edge;
the lit-studio set collapses without the broad lower-third plane.

Guard against three tested failures: the pale sweep blowing out until the host's
shoulder disappears, the crop creeping tighter than waist-up, and a wide-neck garment
slipping off one shoulder. Require visible shoulder separation and select a crew-neck
garment rather than an unspecified wide-neck knit.

**Lounge.** A lounge is a lounge, not a living room, and the difference is furniture.
It does not inherit the full-width desk geometry used by the other room modes.

- Put the host in one freestanding armchair with visible arms, with the room visible
  past it on both sides. Use timber, cane, or upholstered arms.
- Put one small round or square table in front, low and no wider than the chair. It
  crosses the bottom of the frame as a piece of furniture, not as a desk edge running
  the full width.
- Use no sofa, especially no sofa behind the shoulders. A sofa backrest and cushions
  cut across the head, while a separately written desk floats over the seat.
- Compose farther back than the desk modes so the armchair, its arms, and the room
  around it remain legible while the host stays waist-up. Let fireplace detail, alcove
  shelving, wall sconces, or a side table carry the frame rather than a wall directly
  behind the head.

Keep the small table completely clear. The neutral off-frame window sentence remains
the lighting instruction; lamps and sconces may be visible as room furniture, but do
not describe them as bright or as the exposure source. Write nothing about the host's
pose.

**Empty.** A plain painted wall in a real room. Write it as a wall, not as a backdrop:
name the colour, give it fine plaster or paint texture that catches the light, let the
light fall off gently toward one side and the upper corners, and include **one
architectural tell** — a skirting board low in the frame, or the soft vertical of a
corner well off to one side. Nothing hangs on it and nothing stands against it.

The architectural tell is the whole trick. Without it the model builds a studio
cyclorama: one flat unbroken colour with no texture, no edge and no room behind it.
With it, the same prompt produces a wall. Asking for a seamless backdrop asks for the
cyclorama by name; if that is what the user wants they will say so.

Say this once when empty is chosen, then honour it without further argument: alternate
camera angles have nothing to show but the host, because they are prompt-described
shots with no reference image of their own and can only show what this frame implies.
That is the trade, and it is a legitimate look.

## Exposure is fixed by deletion

Do not repair blown highlights by adding exposure qualifications. Every brightness
word votes for a brighter image and survives its qualifier. In testing, adding
`the face the brightest tone in the frame` and `every bright area keeps detail and
gradation` made an already overexposed room worse; deleting the brightness vocabulary
produced the clean frame.

In every casting prompt, omit `bright`, `brightly`, `brightest`, `daylight`, `sunlit`,
`flooding`, and any window visible in frame. A written window becomes a clipped source
and takes the nearby wall with it. Use materials to make a room read light — chalk
plaster, birch, oatmeal linen, oyster, terracotta, walnut — and keep one dark anchor in
frame, such as a black chair, dark clock, walnut skirting, or dark picture frames.

Lighting is one neutral sentence derived from location:

- ordinary filled room, lounge, or bare wall:
  `Window illumination from the left, indoors.`
- studio or editing room, or lit backdrop studio:
  `Even studio illumination from the front left.`

Then state only what remains visible:
`Skin, plaster, wood and cotton all render as mid tones with visible texture and
gradation.` Do not compare the face to the wall in stops and do not call either one the
brightest part of the frame.

## Making the host attractive

This section applies only to Path B casting. Never transfer its anatomy, grooming, age,
ethnicity, or styling prose into a real-photograph request.

Impressive, camera-ready people come from **named grooming and styling**, never from
the word "beautiful" and never from asking for flaws. Asking for imperfections
produces plain, forgettable faces; asking for specific styling produces someone worth
looking at.

Write, in the subject paragraph:

- **Structure.** Even, well-defined cheekbones, a clean jawline, balanced features,
  clear healthy skin.
- **Age.** Reinforce it rather than stating it once. "early twenties" on its own comes
  back as thirty-plus often enough to matter; write `clearly in her early twenties
with a youthful face`.
- **Grooming.** Groomed brows, glowing natural makeup for a woman or clean grooming
  for a man, hair styled with one visible choice — a claw clip holding one side back, a
  half-up tie, a low tuck, a fresh fade, a deep side part.
- **Three to five pieces of jewellery or accessory**, each named — enough that the
  person reads as dressed rather than issued a uniform, and few enough that no single
  one is lost: hoop earrings, a layered chain, a fine ring, a signet, a watch on a
  leather strap, clear-framed glasses, a thin cuff, a hair claw in a stated colour, a
  scarf knotted at the throat, a crossbody strap across one shoulder.
- **Skin.** Real photographic texture rather than a plastic retouch. Do not go further
  and ask for redness, blemishes or visible pores — that is where plainness comes from.

**The expression is one light closed-lipped smile and nothing else.** Do not catch
them mid-sentence and do not write a moving face into the still: mid-word, an open
mouth, a blink or a purse all render as a caught, gurning frame, and the locked
contract makes that frame the ceiling of every take built on it. Easy, warm, settled,
lips together, eyes on the lens.

## The batch of four is varied, not repeated

Do not submit one prompt four times. Hold the spec and the contract fixed and vary the
styling across the four, so the user chooses between four different people rather than
four attempts at one.

**Fixed in all four:** gender, age band, location and its implied lighting, framing,
the clear surface, the closed-lipped smile, and the no-pose rule. Those are the user's
answers and the contract; changing them makes the choice meaningless.

**Varied across the four:** ethnicity and styling turn together, so each slot is a
different person rather than one person in four outfits.

- **Ethnicity.** The first batch is fixed and predictable: Latin American, Black,
  Asian, white European. `Show me more` creates a second four-person batch: South
  Asian, Middle Eastern, Southeast Asian, mixed. Across the two batches the user sees
  eight ethnicities without being asked to choose a label.
- the hair choice — a claw clip, a low tuck, loose and half-down, a fresh fade, a side
  part
- the accessory set, selected from the age-band shelf below
- the garment — a different item from that same shelf each time, not the same shape in
  four colours, each still clearing the seat first and the wall second

Four rolls of an identical prompt sample the same distribution four times. Four
deliberate variants sample four places in it, and the batch stops being a lottery.

After the user chooses a person, offer a styling pass: `I will make four more of this
same person with different styling.` The casting batch chooses the face; this optional
second level chooses wardrobe and accessories without spending the ethnicity batch on
outfit variants.

## The wardrobe bank is split by age band and gender

The age answer chooses a shelf and the host answer chooses a column. Never ask a
separate wardrobe question and never write `Gen Z` or `millennial` into the prompt;
those labels produce costumes. Name the visible garment and accessories instead.
Vary the item, not merely its colour.

### Young 20s

Use youthful, casual pieces with visible layering, relaxed volume, and chunkier
accessories.

| woman                                | man                                   |
| ------------------------------------ | ------------------------------------- |
| a tee under an open overshirt        | an open camp-collar shirt over a tank |
| an open hoodie over a tank           | an open varsity bomber over a tank    |
| a slip top over a t-shirt            | an open hoodie over a t-shirt         |
| a mesh long-sleeve over a tank       | an open denim jacket over a t-shirt   |
| a sweatshirt over a long-sleeve      | a sweatshirt over a long-sleeve       |
| an open denim jacket over a crop top | a knitted vest over a long-sleeve     |
| a knitted vest over a long-sleeve    | an open flannel shirt over a tee      |
| an open checked shirt over a tee     | a sports jersey over a long-sleeve    |
| an open bomber over a tank           | an open chore jacket over a t-shirt   |
| an open cardigan over a crop top     | an open leather bomber over a tank    |

Accessories: chunky hoops, layered chains of different weights, a claw clip for a
woman or a single stud for a man, stacked beaded bracelets, a wide ring, sunglasses
pushed into the hair.

### Mid 20s

Use one relaxed visible garment and accessories between chunky and fine.

| woman                   | man                       |
| ----------------------- | ------------------------- |
| an oversized t-shirt    | an oversized t-shirt      |
| a knit polo             | a knit polo               |
| an oversized sweatshirt | an oversized sweatshirt   |
| a knitted jumper        | a knitted jumper          |
| an oversized shirt      | an oversized shirt        |
| a boat-neck knit top    | a henley                  |
| a striped long-sleeve   | a striped long-sleeve     |
| a crew-neck tee         | a waffle-knit long-sleeve |

Accessories: one chain of middling weight, a ring, and a watch.

### Late 20s

Use a more restrained, tidy register with fine hardware. A structural layer such as a
blazer, waistcoat, or buttoned cardigan is allowed; do not use an open streetwear
layer over another garment.

| woman                           | man                              |
| ------------------------------- | -------------------------------- |
| a satin blouse                  | a blazer over a white tee        |
| a blazer over a tee             | a linen shirt, sleeves pushed up |
| a striped shirt, sleeves rolled | a merino crew-neck               |
| a turtleneck                    | a half-zip sweatshirt            |
| a buttoned cardigan             | an oxford shirt                  |
| a silk shirt                    | a turtleneck                     |
| a fine-knit crew-neck           | a cardigan over a tee            |
| a waistcoat over a shirt        | a chambray shirt                 |
| a blouse tied at the throat     | a knit polo                      |

Accessories: one fine chain, small studs or hoops, a watch on a leather strap, a thin
band ring, and clear-framed glasses.

Only visible waist-up signals matter: neckline and layering, shoulder/sleeve volume,
and accessory register. Pick the shortest garment phrase that identifies the item;
do not over-specify cut, weight, or seam placement.

## Path B casting models

Discover the preferred Soul Cinema image model through `models_search` or
`models_list`, then call `models_get` with its returned id. Catalog aliases are not
stable. Use only quality/resolution/options supported by that live schema. A higher
pixel count alone does not prove better downstream identity.

If that model is unavailable or incompatible, resolve another reference-capable image
model through the live catalog (the OpenAI default is `nano_banana_pro`). Preserve the
visual brief and use its supported options; do not guess a Soul alias or send
`quality`, `resolution` or `enhance_prompt` when unsupported. A weak candidate is a
creative result, not a capability failure that automatically licenses a model switch.
The four-paragraph prompt below is this workflow's casting direction, not a guarantee
of how every model interprets prose.

## Path A — photograph supplied

Read it with host image inspection to confirm that the face carries enough identity detail:
the eyes, nose, and mouth are readable. Prefer a waist-up source over a tight portrait,
but accept a sharper close photograph when it is the user's best identity source. When
one of those features is hidden, blurred, or too small to resolve, ask for a better
photograph or offer casting; do not spend a hook generation trying to recover absent
detail. Everything else the analysis notices—a hand raised to the cheek, a laptop, the
lighting—belongs in the intake card as a stated reason and leaves the run moving.

At Phase 0, copy the photograph into `identity/` and upload it once. Save the exact
response as `identity/upload-receipt.json` and write `identity/manifest.json` with its
path, media id, location choice, wardrobe choice, optional voice path/media id, and
status `"awaiting_script"`. Generate nothing yet. Return control to the parent for
episode intake and script drafting; wait for approval only if requested.

After `script.md` is locked (and approved if requested), re-enter this path. Select the first complete semantic
job from the approved opening; its exact dialogue becomes `host-001` and never appears
again in later jobs. Write the exact request to `bootstrap-plan.json` before the paid
action. The bootstrap is one real frontal `CAM_A` hook shot with no generated-internal
cut, not a disposable identity test. Use `seedance_2_5`, `16:9`, `1080p`,
`omni_reference`, generated audio, and the photograph as `image`.

This wrapper illustrates the data shape. Fill the opening dialogue and complete
provider prompt from this run, and calculate its duration from that dialogue; eight
seconds is an example, not a bootstrap default. Reuse the completed row unchanged:

```json
{
  "version": 1,
  "job": {
    "id": "host-001",
    "reference_stage": "identity_bootstrap",
    "dialogue": "<verbatim opening script segment>",
    "camera_sequence": [
      "CAM_A"
    ],
    "internal_cuts": [],
    "request": {
      "model": "seedance_2_5",
      "prompt": "<authored single-shot bootstrap prompt>",
      "duration": 8,
      "aspect_ratio": "16:9",
      "resolution": "1080p",
      "medias": [
        {
          "value": "<source photograph media id>",
          "role": "image"
        }
      ],
      "mode": "omni_reference",
      "generate_audio": true,
      "count": 1
    }
  }
}
```

When a voice sample exists, add it to the same `medias` array with role
`audio`.

The hook prompt follows the image-reference prompt contract in
[generation.md](generation.md), including the `VOICE & MANNER`, unchanged
`REALISM LAYER`, exact `DIALOG`, pacing note, and technical exclusions. It also obeys
these photograph rules:

- write no age, ethnicity, build, facial structure, hair, grooming, nationality, or
  appearance description; the photograph alone owns identity;
- when location is kept, write no room replacement at all;
- when location is rebuilt, do not write the room into the hook prompt and hope —
  attach an empty room plate as a second reference (see below);
- keep the photographed wardrobe by default; when the user chose another garment,
  describe one layer and acknowledge the likeness trade-off before generation;
- set low, loose, asymmetrical hands and a clear surface as observable performance,
  without prescribing finger or palm shape;
- never write `the desk in front of him is clear and empty with nothing standing on
it` into the hook prompt — that line, not the plate, is what blows the empty desk
  up to a third of the frame.

**Location rebuilt — generate the room as an empty plate and attach it.** Generate the
selected room on its own with the Path B casting image model, **with nobody in it**,
within existing task authorization and any actual connector approval, and pass it to Seedance as a second reference:
the photograph stays `@Image 1`, the plate is `@Image 2`, and the hook prompt says
**"@Image 2 is the room"** in those words after the identity declaration. Record the
plate path and media id in `identity/manifest.json` and add it to the same `medias`
array with role `image`.

Measured by ArcFace cosine against the source photograph (same person calibrates at
+0.76…+0.82): an empty plate named as the room holds +0.81…+0.91; a plate with a
stand-in person in it hands the take that person's face and body (−0.05); a plate
attached but never named in the prompt is a coin flip between the two. There is no
controllable middle, so the plate is always empty and always named.

An empty studio plate returns the face slightly more exactly (0.895–0.911) than a
room plate (0.806–0.850); the room buys its frame and its furniture for about
0.05–0.09 of likeness. Inside the rooms, how much stuff is in them predicts nothing —
choose the fill for the look, not for likeness.

The plate hands over exactly what is drawn on it, defects included: a wrong camera
height, a bloated tabletop and a messy wall all transfer one for one. Polish the
plate; keep the hook prompt fixed. Building a plate with nobody in it has two traps,
both from the missing person:

- **The camera sinks to tabletop height**, because the person was the framing anchor.
  Stating a height in centimetres does not fix it — that failed four rolls running.
  Fix non-lounge modes with geometry instead: a desk across the full width filling
  the bottom quarter, and a chair behind it with a stated back height. For a lounge,
  use the freestanding armchair as the scale anchor, keep the room visible on both
  sides, and put only the low small table no wider than the chair in front. Never add
  a full-width desk or a sofa to make a lounge plate easier to frame.
- **A studio backdrop has no scale anchor at all** — sweeps and colour fills bloat the
  tabletop and shrink the chair. A real room carries its own scale in the furniture.

When a real voice recording was supplied, attach it as `audio` and use the
reference-led voice form from [generation.md](generation.md). Do not describe pitch,
accent, timbre, resonance, age, or vocal anatomy beside the audio reference. Ensure the
selected voice sample is shorter than the requested hook duration. Without a voice
recording, author the normal physical voice block; the generated hook audio becomes
the canonical voice.

Within the existing authorization, submit only `bootstrap-plan.json.job.request`
inside `generate_video({params: request})`, or one indexed batch entry per [operations](operations.md). Record the returned id immediately in `jobs.json`, download the completion
once to `media/orig/host-001.mp4`, and preserve it unchanged. Inspect the complete
video and representative full-resolution frames against the source photograph. Check
hair volume and texture, face weight and asymmetry, head-to-neck proportions, stable
wardrobe, location, and absence of text or production equipment. Hair is the most
reliable tell — it is the first thing tidied when the model is synthesising toward a
description instead of copying the reference. Judge identity from full frames, not
only a contact sheet.

For a demonstrated identity defect, follow [the single retry policy](operations.md#one-retry-policy):
a completed result requires a distinct creative replacement, with its original retained.
Clarify appearance or wardrobe instructions only where they caused the defect. An ASR
mismatch or an absent result URL is not authorization to regenerate an accepted job.

The accepted `media/orig/host-001.mp4` is both the first final host source and the
canonical avatar reference. Copy or hard-link the exact bytes to
`reference/avatar.mp4`, upload that clip once when a reusable media id is required,
and save the response as `reference/video-upload-receipt.json`. Do not generate a
still keyframe and do not use an extracted frame as provider input. Continue through
[keyframe-prep.md](keyframe-prep.md) in `video_avatar` mode; it may extract an
inspection frame only for QC and camera-map authorship.

## Path B — cast from nothing

Generate four varied candidates in one `generate_image_batch` call using four indexed `{index, params}` entries:
four independent request objects with one complete prompt per variation. Set `count: 1` in every entry; the four prompts deliberately differ.

After the call returns the four job ids, return control to the parent immediately.
The parent starts episode intake and script drafting while these existing jobs run;
avatar polling must not block writing. Keep polling the same ids in combined sweeps
whenever control returns. Script readiness and avatar selection are independent:
either may finish first. Only an explicitly requested script review requires a reply. Image-keyframe preparation may start as soon as the avatar is
selected, but plan authoring waits for both the complete reference and approved script.

In every interaction mode, show all four completed candidates together as soon as they
are ready and let the user pick one or ask for the second ethnicity batch. Ask one host-selection question through the available conversation interface. Keep it as a durable human gate: wait
indefinitely for an explicit choice, never self-select after silence or timeout, and
never treat continuous autonomous delivery as delegated avatar selection. Handle failed entries through [operations](operations.md#one-retry-policy).
Reconcile an accepted job with no URL by status lookup; never resubmit it as a retry.

Four paragraphs, no headings, roughly 2600-2900 characters, with the **setting
paragraph second**, and longest whenever the room is filled. On an empty wall there is
less to say and the paragraph is naturally short. A lit studio uses a concise backdrop
description plus the required broad-tabletop paragraph; keep the paragraph positions,
not their lengths. A long block-labelled prompt is read as a list of framing
constraints and the setting falls out of it entirely.

```text
Ultra-realistic editorial lifestyle photograph in a horizontal 16:9 composition. <AGE WITH
REINFORCEMENT, ETHNICITY, GENDER> sits behind <SURFACE> in <LOCATION>, still and
settled, with a light easy closed-lipped smile and eyes on the lens. <HAIR WITH ONE
VISIBLE STYLING CHOICE>, groomed brows, <THREE TO FIVE NAMED ACCESSORIES>, <MAKEUP OR
GROOMING>. Even well-defined cheekbones, a clean jawline, balanced features and clear
healthy skin with real photographic texture rather than a plastic retouch. Wearing
<GARMENT FROM THE AGE-BAND SHELF>, the colour standing clear of <SEAT>. Eye-level
angle at the height of their own eyes, camera square on to the back wall, centred in
the frame, framed from the waist up.

<FILLED, LIT-STUDIO, EMPTY, OR LOUNGE SETTING PARAGRAPH>.

<SURFACE PARAGRAPH FOR THE SELECTED SETTING MODE>.

<NEUTRAL LIGHTING SENTENCE DERIVED FROM LOCATION>. A soft rim along the
shoulder and jaw separates them from the wall behind. Skin, plaster, wood and cotton
all render as mid tones with visible texture and gradation. No cameras, tripods, light
stands or softboxes in the picture, and every screen, spine, lid and printed surface
is smooth and unmarked. Shot on a full-frame camera, 35mm lens, f/4, eye-level angle,
subject tack-sharp, professional color grade, high dynamic range, editorial campaign
quality. No text, no watermark.
```

Filling the remaining choices:

- **Surface paragraph follows the setting mode.** For filled and empty room modes:
  “The surface in front of them is clear and empty, its near edge crossing the bottom
  of the frame softly out of focus, with nothing standing on it.” For either lit-studio
  mode, use the broad, sharp, empty tabletop plane across the lower third defined
  above; do not describe it as a soft near edge. For a lounge, use one low small table,
  round or square and no wider than the armchair, crossing the bottom of the frame as
  furniture with its surface completely clear; never turn it into a full-width desk.
- **Name a garment from the correct age-and-gender shelf, not a default.** Left to
  itself the model returns a plain t-shirt or crew-neck sweater every time, and a
  batch of four comes back monotone. Pick a different shelf item for every candidate,
  then a colour that clears the seat and wall. Do not collapse the expanded shelves
  back into one generic bank.
- **Garment colour is checked against the seat first and the wall second.** On a medium
  shot the chair is the surface that surrounds the torso, so a pale sweater on a cream
  chair blends even against a perfect wall.
- **35-40mm at f/4.** The background softens but stays legible. 50mm at f/2.8 turns a
  filled room into a wash and gains nothing on an empty one.
- Never write a clean patch of wall behind the head in a filled room. Separation comes
  from depth, luminance and rim light.
- Never write a softening or emptying instruction in a filled room: "open floor visible
  behind the chair" and "the wall falls out of focus" both produce a bare set by
  accident, which is a different thing from choosing one.
- **Write nothing about the pose** — no hands, arms, shoulders, posture, or legs.
  Every attempt to place the hands failed in a different
  direction: raised clear of the surface steepled in four renders out of five;
  "forearms along the front edge" ran the arms out sideways and rendered the subject
  spread-eagled across the whole frame; "angled forward" splayed two in four. Deleting
  the pose sentence entirely gave four natural seated poses out of four on the first
  submission. The model's default sit is better than any sit you can specify, so
  specify nothing and spend the words on the person and the room.
- Never write a moving face. Mid-word, a blink, a purse, parted lips or "about to
  speak" all land as a caught frame, and the locked contract makes that frame the
  ceiling of every take built on it. One light closed-lipped smile, held.

## Never describe a face you already have

With a photograph attached, every sentence about age, build, ethnicity, accent as a
proxy for either, or facial structure competes with the reference, and the model
redraws the face toward the words. Observed directly: identical prompts with and
without those lines produced a tidied, younger, flatter face in the first case and a
faithful one in the second.

Delete them all. Keep wardrobe, keep the room, keep what the person does. A
closed-lipped smile is behaviour and stays; a description of cheekbones is anatomy and
goes.

## Return

For casting, there may be one interim return immediately after submission: hand the
four existing job ids back to the parent as pending work so episode intake and script
writing can proceed. This is not an accepted reference and does not unlock Phase 2.

For casting, hand back the user-selected image keyframe and resume
[keyframe-prep.md](keyframe-prep.md) in `image_keyframe` mode.

For a real photograph, hand back the accepted `reference/avatar.mp4`, its reusable
video media id, whether it has usable audio, the exact completed `host-001` request and
result, and one representative inspection frame. Resume
[keyframe-prep.md](keyframe-prep.md) in `video_avatar` mode. The parent copies the
bootstrap request byte-for-byte into the first row of the complete
`generation-plan.json` and initializes that `jobs.json` row as completed; no later
stage regenerates or repeats its dialogue.
