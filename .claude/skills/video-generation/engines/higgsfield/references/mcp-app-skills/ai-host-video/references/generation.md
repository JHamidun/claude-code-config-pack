# LLM-authored generation contract

The model writes and checks every final generation request itself, in the fixed block
order below. No script writes prompt prose.

## Host jobs

Write `generation-plan.json`. This example shows the image-keyframe data shape;
video-avatar media substitutions are defined below. Values inside angle brackets are
placeholders for this run's authored content or returned media ids. Resolve them before
submission. Submit each inner `request` as MCP `params`, wrapped with a stable batch index per
[operations](operations.md); never send the planning wrapper. The example's two setups and 12 seconds are not defaults: choose cameras
for the beat and calculate duration from its actual spoken words.

```json
{
  "version": 1,
  "camera_mode": "standard",
  "aspect_ratio": "16:9",
  "jobs": [
    {
      "id": "host-001",
      "reference_stage": "primary",
      "dialogue": "<verbatim script segment for this job>",
      "camera_sequence": [
        "CAM_A",
        "CAM_B"
      ],
      "internal_cuts": [
        {
          "after": "<last phrase of SHOT 1>",
          "at": "<first phrase of SHOT 2>",
          "to_camera": "CAM_B"
        }
      ],
      "request": {
        "model": "seedance_2_5",
        "prompt": "<authored provider prompt using the structure below>",
        "duration": 12,
        "aspect_ratio": "16:9",
        "resolution": "1080p",
        "medias": [
          {
            "value": "<keyframe media id>",
            "role": "image"
          }
        ],
        "mode": "omni_reference",
        "generate_audio": true,
        "count": 1
      }
    }
  ]
}
```

## Dialogue timing

Use one internally estimated average speaking pace for the script budget and request
duration. Keep WPM, numeric speech rates and this timing calculation out of the
provider prompt. Count the actual assigned spoken dialogue, once across all shots;
exclude camera labels, speaker labels and production prose. Use the completed text, not the
target word budget. For timing, account for numbers and abbreviations as they will
be spoken while preserving the approved written copy.
For a language without word separators, estimate its spoken duration directly rather
than treating character count or the entire line as a word count.

For an authored request, let `W` be its spoken word count, `N` the chosen average words
per minute, and `P` any deliberate extra silent holds in seconds (normally zero;
ordinary speech rhythm is already included in `N`). Calculate:

```text
speech_seconds = 60 * W / N
duration = max(4, ceil(speech_seconds + P + 0.4))
```

The small 0.4-second allowance covers onset and the closing beat; round up to a whole
second so rounding cannot shorten the estimated speech. If the result exceeds 30,
split at a complete semantic boundary and recalculate each request. Never clamp an
overlong speech estimate to 30 or add time for each camera cut: speech continues
through cuts. Avoid large empty buffers. This is an estimate, not a speech guarantee;
measured transcript times own the finished edit.

For an audio-bearing reference, estimate its natural pace without adding a competing
written voice description. Preserve locked copy. The 4–30-second range above is the
source workflow's planning envelope: fetch the live model schema and use its actual
supported duration range and step. Split at semantic boundaries when the supported
maximum is lower; do not silently clamp speech. Inspect returned adjustments and
reconcile an incompatible duration before continuing with affected work.

## Camera grammar

The selected camera map is stable internal planning metadata for the whole episode:

- `CAM_A` — frontal home anchor, normally a medium shot;
- `CAM_B` — right-cheek or left-cheek three-quarter speaking view with a clearly
  different shot size, normally a medium-close chest-up shot;
- `CAM_C` — near-profile close/accent speaking view, normally head-and-shoulders.

The model authors each framing in `reference/manifest.json` from the supplied studio
and topic. `standard` keeps restrained conventional setups locked off. `creative`
permits any story-motivated framing and camera movement appropriate to the episode and
hosted YouTube storytelling. `CAM_A` remains a usable frontal direct-address anchor,
and speaking shots keep lip-sync readable. Record a standard `shot_size` (`wide`,
`medium-wide`, `medium`, `medium-close`, or `close`) for every setup. Mapped setups
must not share the same shot size. Every framing definition must state:

- one concrete physical viewpoint such as `frontal single`,
  `right-cheek three-quarter single`, `left-cheek three-quarter single`, or
  `near-profile single`; for oblique views, specify the host's anatomical side and
  which cheek and shoulder are nearer the lens. An approximate camera offset from
  the attached reference viewpoint may clarify this geometry; a bare angle without
  a reference viewpoint and anatomical side is insufficient;
- vertical angle as `eye-level`, `high-angle`, or `low-angle`;
- one standard shot size and an observable body crop such as waist-up, chest-up, or
  head-and-shoulders;
- subject placement and negative-space direction;
- locked-off or an explicit motivated camera move.

Do not use “alternate angle”, “side angle”, “closer”, “wider”, “dynamic”, or lens
language alone as a framing definition. They do not tell the provider which view and
scale must visibly change.

For a seated presenter, keep the lap, knees, and lower legs outside every speaking
setup. Do not choose `wide`, `medium-wide`, or any below-waist crop merely to create a
size change. Prefer the default progression of medium waist-up, medium-close chest-up,
and close head-and-shoulders.

Each job declares `camera_sequence`; every adjacent entry differs. Declare one
`internal_cuts` row per camera change, using verbatim semantic phrases. At **every
adjacent host-job boundary**, the outgoing camera of the previous job and the incoming
camera of the next job must differ. Compare the last and first `camera_sequence`
entries, not just the jobs' opening shots: `A→B | B→A` repeats `B` at the seam.
Update the actual physical SHOT descriptions along with the metadata; a dissolve or
covering image does not repair the camera plan. Check for repeated seams while authoring, before submission. Existing frozen/submitted requests retain their
resume/retry contract. A one-shot identity bootstrap stays one shot; open the following
authored job on another camera. Respect an explicit user request for a single camera.

Internal ids remain planning metadata. In `request.prompt`, map used setups in sequence
directly to numbered `SHOT 1`, `SHOT 2`, and optional `SHOT 3` blocks. Do not define
or use request-local labels such as `CAMERA A`, `CAMERA B`, or `CAMERA C`. Every
`SHOT N` label must begin with its complete physical viewpoint phrase and vertical
angle, then state shot size, body crop, composition, movement, and performance. Use
provider-facing phrases such as `RIGHT-CHEEK THREE-QUARTER SINGLE, eye-level` or
`NEAR-PROFILE SINGLE, eye-level`; never expose an internal underscore id such as
`CAM_A`.

Every host request is stateless apart from its supplied image or video media. Reuse the same physical
framing language when a setup recurs, but do not imply that a label or an earlier
request gives the provider cross-job camera memory. With one accepted reference,
alternate views are continuity targets inferred from the visible studio, not
reference-proven views. Do not invent distinctive objects or geometry outside the
accepted image.

## Cut rhythm

When multiple cameras are available, plan expressive coverage. Read each multi-sentence
block for its distinct story beats before choosing the shot count. When the dialogue
changes from setup to consequence, claim to proof, or explanation to payoff, author an
internal camera change at the strongest
transitions: claim to example, question to answer, contrast, the next countdown item,
or payoff. Choose a new angle to make that development clear or give the next key
phrase more emphasis.
Introduce the new framing as that phrase begins, using the preceding verbatim phrase
as the hard-cut anchor. Keep related sentences together while they develop the same
beat; not every sentence needs a cut. Keep every word in order; do not rewrite
dialogue to manufacture cuts. Apply this within the available camera map.

Let the story determine shot count and hold length, with no target interval, maximum
shot length or cut quota. A long continuous shot is appropriate when it sustains
clarity, tension, intimacy, a demonstration or a performance. Retain a multi-beat block
as one shot only when a specific direction in the brief or a concrete performance
reason calls for uninterrupted coverage; make that reason clear in the shot's existing
performance direction. Request duration does not determine shot count. Retain the
view while continuity serves the moment; change it when a new view
adds meaning. Do not
treat a generation request as one unbroken shot merely because its dialogue arrives
as one block, or insert a token cut simply to label it multi-shot. Do not cycle through
A/B/C mechanically. Apply this approach to both standard and creative camera modes.

Internal shot rhythm remains an authoring decision, not a cut quota or a new review step.
Plan internal cuts within the existing request rather than adding billed jobs just
for more camera changes. Preserve the one-shot identity bootstrap and any explicitly
supplied single-camera restriction. Platform blocks retain their supplied words, duration and
one-generation boundary; multi-camera blocks use this rhythm within that block.

## Supplied object media on a host request

When the user supplied an object the episode handles on camera, the object's reference —
the supplied file itself, or a repair plate when that file could not serve, per
[user-inputs.md](user-inputs.md) — is
**appended** to `request.medias` after the canonical host reference, which keeps its
position and role. The mandatory first sentence never changes — it still declares only
`@Image 1` or `@Video 1` per the recorded reference mode.

```json
{
"medias": [
  { "value": "<keyframe or avatar media id>", "role": "image" },
  { "value": "<object reference: supplied media id, or repair plate job id>", "role": "image" }
]
}
```

Reference tokens are numbered inside their own media kind: in `image_keyframe` mode the
keyframe is `@Image 1` and the object's reference is `@Image 2`; in `video_avatar` mode the
avatar is `@Video 1` and the object's reference is `@Image 1`. Confirm the resolved numbering on the first
completed job of a wave before submitting the rest.

Name the object with a minimal noun plus its token — `the headphones @Image 2`,
`wearing the headphones as in @Image 3` — inside the shot labels that show it, and state
what is being done with it there. The plate carries the appearance: do not describe the
object's colour, material, or markings in prose, do not write `match @Image N exactly` or
describe the plate's background, and never put a brand wordmark, price, spec line, or any
on-screen copy in a provider prompt. Plan handling on setups whose crop contains the
hands; an object lifted into a head-and-shoulders accent setup leaves frame.

Full intake, plate preparation, object state across jobs, and the routes for supplied
segments, brand assets, subject media, and audio live in
[user-inputs.md](user-inputs.md).

## Prompt authoring structure

Every host prompt uses the following block order. The order is stable so the request is
easy to inspect, but the prose inside each block is authored for the actual host,
studio, script beat, and selected camera style. Do not collapse this foundation into a
short generic paragraph.

This section instructs the prompt author. `request.prompt` contains the finished
scene, camera, performance and speech directions addressed directly to the video
model. Turn authoring guidance into that final wording before packaging the request;
keep instructions about writing or explaining a prompt outside the provider payload.
Quoted sentences and `text` blocks are provider-facing examples. Expand brace, angle
and bracket placeholders into concrete wording; omit optional example content that
does not apply. No unresolved placeholder, authoring note, file name or planning-field
name belongs in the final prompt. Each request is self-contained: the provider sees
its prompt and attached media, not the brief, edit plan or previous requests.

1. **Reference declaration and character lock.** The prompt's first sentence must
   exactly match its recorded reference mode:
   - primary `image_keyframe`: “@Image 1 is the reference for the character and the
     location.”
   - photograph `identity_bootstrap`: “@Image 1 is the reference for the character
     only.”
   - `video_avatar` with usable audio: “@Video 1 is the reference for the character,
     location, performance, and voice.”
   - silent `video_avatar`: “@Video 1 is the reference for the character, location, and
     performance.”

   For an image keyframe, describe only the visible host traits and wardrobe needed for
   continuity. Preserve the same supplied location and lighting, but do not inventory
   the location in detail. For a video avatar, the complete clip is the source of truth
   and the extracted inspection frame is never attached. For an identity bootstrap,
   never describe the real person's appearance; the photograph alone owns identity,
   while the approved location choice determines whether the photographed setting is
   kept or replaced.

   For either image reference mode, add: “The image establishes appearance, not a
   held pose. During speech the host changes hand positions, naturally shifts posture,
   and uses expressive gestures that follow the meaning and rhythm of the words.”

2. **Sequential self-contained shot plan.** Choose up to the selected number of
   persistent episode setups using the [cut rhythm](#cut-rhythm) above.
   Describe the actual episode format in one short sentence, for example “A hosted
   explainer with natural on-camera speech.” Use the subject's format rather than
   labeling every episode a lifestyle vlog. Put this job's shot and cut counts in the
   following sentence; define physical views only inside the numbered shot labels.
   - One setup: “One continuous shot with no internal cut.”
   - Multiple setups: use exactly `camera_sequence.length - 1` immediate hard cuts
     from each numbered shot to the next. For a two-shot job: “Exactly one immediate
     hard cut from SHOT 1 to SHOT 2.” Adapt the count and shot numbers for this job.
   - When a multi-shot segment does not use the frontal single, place this sentence
     near the shot count: “The frontal single is not used in this segment.”
   - For an image keyframe, use: “@Image 1 fixes the host identity and location. Each
     shot uses the physical camera position and framing specified in its shot label.”
     For a video avatar, use: “@Video 1 fixes the host identity, location and
     performance. Each shot uses the physical camera position and framing specified
     in its shot label.” The reference declaration and voice block retain the mode's
     audio rules. An identity bootstrap keeps only the photograph's identity lock and
     uses the approved studio location.
   - For alternate views of the same host reference, add: “Camera changes preserve
     the host's place in the set and general facing direction. Hands, head, shoulders,
     and torso move naturally during speech; gestures and posture changes continue
     across cuts.” If seated, keep the chair's placement and orientation fixed while
     allowing the host to lean, shift weight, and turn slightly during delivery.
     Establish the new view by placing the camera around the host; a body turn must
     not substitute for a camera change. Keep the
     concrete camera position in its shot label; use the actual attached reference
     as the origin, including when a platform job supplies its own camera reference.
   - For multiple setups, use: “Each cut switches to the physically different camera
     position and shot size defined in the next shot label. The studio perspective
     changes with that view. No digital crop, punch-in or zoom of the previous shot.”
     Keep the concrete side, scale and framing in the matching shot label. Omit this
     cut direction in a single-shot job.
   - Every adjacent shot must change shot size by at least one clear standard step,
     such as medium to medium-close or medium-close to close. Angle change alone is
     insufficient.
     Do not cut medium to medium, even when the viewpoints differ.
   - Every adjacent shot must also change horizontal viewpoint. Specify a concrete
     physical view using `frontal single`, a side-specific `right-cheek` or
     `left-cheek three-quarter single`, or `near-profile single`. “Alternate angle” or
     “three-quarter” without a visible cheek side is insufficient.
   - `standard` keeps every used shot locked off. In `MOVEMENT`, establish SHOT 1 at
     its specified camera position from the first frame; each later shot starts at
     its specified position immediately after the hard cut. No visible repositioning
     or orbit connects these locked-off views. `creative` may author any appropriate
     story-motivated framing and camera movement within premium hosted YouTube grammar;
     describe that move explicitly instead of applying the locked-off wording.
   - Give each cut a specific spoken transition and a purpose in the next beat.
     Choose cuts and continuous holds using the cut-rhythm guidance, according to
     what best supports the story in that moment.
3. **Voice and recording realism.** Immediately before `DIALOG`, write separate
   `VOICE & MANNER:` and `REALISM LAYER.` blocks in that order. The voice belongs to
   the person or canonical media reference; the realism belongs to the recording. Use
   a physical voice description only when no audio-bearing reference is attached. With
   an audio-bearing `@Audio 1` bootstrap source or `@Video 1` avatar, use the
   reference-led form below and write no competing pitch, accent, timbre, resonance,
   age, nationality, dialect, or vocal-anatomy description. Repeat the episode's
   realism block unchanged. Follow the short guide and templates below.
4. **Numbered, self-contained shot dialogue, spoken exactly once.** Under
   `DIALOG (labeled per shot):`, partition the assigned dialogue across one quoted
   speaker line per used setup. Concatenating those lines must reconstruct the exact
   assigned dialogue without loss, repetition, or reordering. Do not include a second
   full-dialogue copy elsewhere in the prompt. Use this exact label order:
   `SHOT`, an unlabeled physical viewpoint phrase with vertical angle, `SIZE`, `CROP`,
   `COMPOSITION`, `MOVEMENT`, `PERFORMANCE`. This example establishes an oblique
   opening shot from a frontal reference; its side and 40-degree offset are
   authored choices, not defaults for every setup:
   `[SHOT 1 | RIGHT-CHEEK THREE-QUARTER SINGLE, eye-level; camera 40 degrees around the host toward the host's anatomical right from the reference viewpoint, aimed at the host; right cheek and right shoulder nearer the lens | SIZE: medium-close | CROP: chest-up | COMPOSITION: host slightly left, natural room to the right | MOVEMENT: locked-off at this position from the first frame | PERFORMANCE: leans forward on "number one", lifting an open hand into the lower frame to mark the point, then eases back as the hand lowers into a relaxed new position]`.
   Keep the complete bracketed label on one physical line, number shots from 1 with no
   gaps, and repeat the complete physical view inside each label.
5. **Performance inside each shot label.** Author natural, evolving delivery inside
   the matching `[SHOT N | ... | PERFORMANCE: ...]` label. Tie concrete gestures,
   posture changes and expressions to short verbatim anchor phrases. Give a gesture
   an onset, emphasis and release into a relaxed position; between accents, let the
   hands reposition, the shoulders settle and the torso shift with speech. Match
   amplitude and frequency to the script's energy and the host's delivery; avoid
   repetitive waving or a gesture on every word. Do not prescribe holding the
   keyframe's hand placement or torso pose, or returning to it after every gesture.
   Keep actions visible within the crop: use hand gestures where hands fit and head,
   expression and shoulder changes in close shots. `MOVEMENT: locked-off` fixes only
   the camera. A deliberate pause can briefly settle the body, then movement resumes
   with speech. Later shots continue the ongoing performance without resetting the
   pose or restarting speech. For example: `PERFORMANCE: leans toward the listener
on "here is why", raises an open hand to emphasize "the difference", then lowers
it while easing back; the shoulders settle briefly during the pause, and a nod
leads into "next"`.
6. **Semantic cut cues.** Describe each generated-internal transition as an immediate
   hard cut from `SHOT N` to `SHOT N+1` after its matching short verbatim phrase. Never
   use an internal underscore camera id or a `CAMERA A`/`B`/`C` label, and never promise
   a frame-exact generated cut.
7. **Shot labels describe what the camera records, never the graphic layer.**
   `COMPOSITION` says where the host sits in the frame and what the visible set does
   behind them; `MOVEMENT` says what the camera does. Physical set elements the camera
   sees belong there. The graphic layer does not: no graphics, captions, subtitles,
   lower thirds, overlays, b-roll, split screens, picture-in-picture, on-screen text,
   and no space “reserved for” any of them, because the video model renders such words
   literally. Overlay planning lives in `edit-plan.md`.
8. **Pacing note, continuity, and technical exclusions.** Immediately after the final
   dialogue line, add the `Pacing note:` from the template below. Then preserve person,
   face, wardrobe, set, lighting, continuous lip-synced speech, and room tone. Put all
   technical exclusions last: prohibit accidental restarts, unplanned text, captions,
   logos, watermarks, extra people, music, sound design, extra angles, zoom substitutes,
   identity changes, and visible production equipment unless the approved plan
   explicitly requires them. Include this exact sentence: “The frame contains only
   the host and the supplied set; no filming or production equipment is visible.”

### Voice & Realism — Short Guide

Describe physical behavior, not impressions. Register, resonance, tempo, pitch
movement, stress, and volume are executable; adjectives such as “warm” or “confident”
are not.

Use the episode language recorded in `brief.json` and spoken in the script. When no
voice-bearing reference exists, author one consistent voice with fluent pronunciation
in that language and clear articulation. Honor an explicitly requested accent; otherwise
use natural pronunciation without assigning an accent from the host's appearance.
When an attached reference contains usable audio, it supplies voice identity. Preserve
that identity while speaking the new script in the requested language.

Choose one dominant per voice: either weight and calm, or brightness and speed. Mixed
signals average into a neutral announcer. Write every line as a statement of fact;
conditional phrasing gets skipped.

Do not ask the user to choose between these internal prompt profiles. Honor explicit
voice or delivery direction; otherwise infer the dominant from the approved script's
host role, pace, and energy while preserving the stable episode voice fingerprint.
Never infer the dominant from appearance.

A register name is not executable and often backfires: `upper` in a timbre field is
read as an instruction to sit high, and `light` competes with weight. Write where the
voice sits as behavior: where it starts a sentence, where it returns, and which word
in the sentence is lowest.

Keep the two blocks separate. The voice belongs to the person or canonical reference,
while the realism belongs to the recording. Only the realism block travels unchanged
between hosts. Within one episode, keep the same voice source stable and repeat the
complete realism block unchanged across every host job.

Dose realism sparingly. A few physical traits read as life; a full catalogue reads as
acting.

When brightness and speed dominate and no audio-bearing reference exists, use this
voice template as one paragraph, replacing every brace:

```text
VOICE & MANNER: one consistent adult {gender} voice, speaking {episode language}
fluently with clear articulation, {physical vocal weight}, {timbre}. Resonance:
{where the sound sits}, close-miked, {distance}. Attitude: {who is addressed and with
what intent}. Pitch contour: {one movement across a sentence}.
{rhythm shape}. Stress: {what is emphasized} while {what is compressed}. Volume:
{range and what the contrast achieves}. {One affirmative guardrail}.
```

When weight and calm dominate and no audio-bearing reference exists, use the
weight-dominant template below instead of the brightness-dominant paragraph. Do not
append it to another physical voice description. Excitement is routed into tempo and
consonant attack so a reveal cannot push the pitch upward.

Never append a second physical voice paragraph.

Weight-dominant template, one paragraph, replacing every brace:

```text
VOICE & MANNER: one consistent adult {gender} voice, speaking {episode language}
fluently with clear articulation, close-miked at
arm's-length distance, one voice from the first word to the last. REGISTER: {he/she}
speaks from the bottom of {his/her} range and keeps returning to it; declarative
sentences end lower than they began, and their final two words form the lowest landing
in the sentence. WEIGHT LEADS: the landings carry the weight and the speed lives inside
the phrase, never at its ends. PROJECTION: the sound travels outward through the lens
to one person sitting a metre away, carried on air pushed from low in the body.
EXCITEMENT ROUTING: rising interest is spent on tempo and on harder consonant attack,
and the more {he/she} leans into a line the more clipped and the lower it finishes.
The middle of each phrase runs fast while the final two or three
words separate and slow. PITCH MOVEMENT: the moves are downward steps — one step down
onto {anchor 1}, one onto {anchor 2}, one onto the last word of the take. STRESS: {what
carries the line} carries the whole line while the connecting words compress to almost
nothing. VOLUME: one word in a sentence steps up and the level returns immediately;
the whole take lives in the middle of its range, the loudest moment only a little above
the quietest and taking its force from clarity rather than size. {landing module}
```

Replace `{landing module}` with exactly one of these endings inside the same paragraph:

- When the assigned dialogue contains a real reveal:
  `THE DROP: {he/she} stops fully before {the reveal phrase}, and the words after that
stop come in lower, slower, quieter and more precise than the words before it. BREATH
& LANDING: one audible intake before {the reveal phrase}; the final word is completed,
falls away in pitch, and the line stops cleanly.`
- Without a reveal:
  `BREATH & LANDING: breaths stay inside natural phrase boundaries; the final word is
completed, falls away in pitch, and the line stops cleanly.`

`{anchor 1}` and `{anchor 2}` are the two words the segment actually turns on.
`{the reveal phrase}` is the short verbatim phrase held behind the pause.

When the bootstrap request carries a real voice sample, replace the physical template
with:

```text
VOICE & MANNER: @Audio 1 is the sole voice identity. Preserve that voice without
written reinterpretation. The host speaks only the new DIALOG below in {episode
language}; the reference recording supplies identity, not words to repeat.
```

When an accepted video avatar has usable audio, use:

```text
VOICE & MANNER: @Video 1 is the sole voice identity. Preserve that voice without
written reinterpretation. The host speaks only the new DIALOG below in {episode
language}; the reference clip supplies identity, not dialogue to repeat.
```

Use this recording template as one paragraph, replacing every brace:

```text
REALISM LAYER. BREATH & BODY: relaxed breathing sits under the voice as a quiet
constant; faint mouth sounds accompany speech; blinking runs off the speech rhythm; a
faint {fabric} rustle and a soft {contact sound} accompany movement; the head settles
a fraction after the last word. NATURAL VARIATION: breaths and emphasis follow the
meaning of each phrase; articulation remains clear and every spoken word is completed.
RECORDING REALITY: quiet room floor noise of {room}, early reflections off the
{nearest hard surface}, close-mic warmth on the low end; no polish, no broadcast sheen,
no artificial perfection.
```

After the shot-labelled dialogue, use:

```text
Pacing note: maintain the specified conversational pace through the complete dialogue.
Finish the final word clearly, then settle naturally for a brief closing beat with
room tone continuing. No prolonged silent hold, slowed delivery or repeated words.
```

The final placement is: reference and continuity → shot structure → `VOICE & MANNER`
→ `REALISM LAYER` → dialogue per shot → `Pacing note` → technical exclusions.

Write each shot's camera geometry, movement and performance directly in provider prose.
Keep internal camera ids in metadata. Do not retype or rewrite prompts after approval.
For example, a dialogue row uses this structure with the exact assigned words:

```text
DIALOG (labeled per shot):
[SHOT 1 | FRONTAL SINGLE, eye-level | SIZE: medium | CROP: waist-up | COMPOSITION: centered | MOVEMENT: locked-off | PERFORMANCE: observable action tied to a phrase]
The host (on-camera, mouth synced to speech): "[exact dialogue segment]"
```

Use the example as an authoring convention. Formatting differences do not require a
rewrite or user checkpoint. Each shot owns one spoken segment; together they preserve
the exact assigned words. The author resolves missing or duplicated speech while
writing. Preparation packages that text and does not parse dialogue headings or judge
its meaning.

For an `identity_bootstrap` request, replace the opening with the exact character-only
`@Image 1` declaration, omit all appearance description, keep or replace the location
according to `identity/manifest.json`, use one frontal shot with no internal cut, and
attach the real photograph as `image`. If a real voice sample is attached,
use the `@Audio 1` voice form above.

For a primary `video_avatar` request, replace the opening with the exact audio-bearing
or silent `@Video 1` declaration and attach the accepted complete avatar clip as
`video`. Never attach its inspection frame. When the clip has usable audio,
use the `@Video 1` voice form above. Its provider-facing sentence already restricts
speech to the new `DIALOG`; keep it once without an extra authoring instruction.

Omit unused shot rows. Identify additional attached object references by their actual
media tokens and describe their use in the matching shot. Post-production overlays
belong in the edit plan.

One request may direct up to three generated speaking setups with motivated internal
cuts. Choose shot count and hold length using the [cut rhythm](#cut-rhythm) above.
Generated internal cuts are creative targets, not frame-exact edit points. Use a new
job when an exact boundary or clean editor-controlled seam is required.

## Resolve the request while authoring

Keep the actual request consistent with the decisions above:

- Use `seedance_2_5`, `mode: "omni_reference"`, generated audio, the selected
  format and the canonical media id with the correct image/video role. Only the
  photograph-bootstrap job uses its source photograph; subsequent avatar jobs use
  the accepted video.
- Choose an integer duration from 4 through 30 seconds using
  [dialogue timing](#dialogue-timing). Split dialogue that cannot fit naturally.
  Check the live duration limits. Never default every job to 30s.
- Preserve the script's words once and in order across jobs and shots. Keep camera
  changes aligned with their semantic cuts and the stable camera map. Use concrete
  physical views, movement and performance in the matching shot labels.
- Keep provider prose self-contained and addressed to the video model. Resolve
  authoring placeholders, repeat the stable voice/reference direction and exclude
  planning ids, graphic-layer instructions and commentary to the requester.

Check this as part of writing each request. Compare dialogue order, adjacent cameras,
media roles and the exact live schema yourself. Record accepted payloads and job ids
unchanged; no preparation tool stamps slots, freezes files or validates prose.

## Editorial work after host submit

Read [supporting-media.md](supporting-media.md) for the asset-opportunity pass,
`visual-plan.json.coverage`, web media and music requests. Load it after initial host
submission, or during the explicitly requested full-plan review. Keep dispatching
ready hosts and supporting assets through the
[continuous dispatch loop](operations.md#continuous-dispatch); a pending generation
does not block unrelated requests.

## Semantic anchors

For graphics or visual changes tied to speech inside a host job, write
`anchor-plan.json` keyed by plan job id. Omit it only when no treatment depends on an
in-job phrase:

```json
{
  "host-001": {
    "proof-card": {
      "start": "the evidence is right here",
      "end": "right here",
      "required": true
    },
    "step-list__item_0": "first, collect the source"
  }
}
```

Anchor phrases quote that job's `dialogue` verbatim. After download, measure them from
the actual word timestamps and map source time to master time as described in
[anchor preparation](anchor-prep.md). The agent writes the resulting measurements.

## Submission and recovery

Use [operations](operations.md) for submission, waiting, gallery and the single retry
policy. Distinguish ASR recognition errors from audible speech defects. A mismatch
in recognized wording does not authorize regenerating a completed host or silently
dropping a treatment. Inspect the actual speech, use measured neighboring words to
resolve the intended phrase, and preserve the clip's interior pauses.

### Replace a completed source with a missed camera change

A demonstrated missing camera change, identity defect or wrong spoken copy may need
a new creative replacement under [the retry policy](operations.md#one-retry-policy).
Explain the defect and proposed additional generation unless that correction is
already delegated. Preserve the completed source, its receipt and exact request.
Submit only the affected replacement with a new unique index; do not replay siblings.
Keep the script and accepted reference while clarifying the failed instruction.

Inspect the new source before selecting it. Retain both originals under distinct
filenames and record which job now supplies the same narrative slot. Preserve the
old selection as provenance. Transcribe and measure the new file afresh, recompute
all affected trims, master positions and anchors, and update the edit. Old transcripts,
source cuts and proof samples do not describe the replacement. Review its changed
ranges and neighboring seams without resubmitting an already accepted request.
