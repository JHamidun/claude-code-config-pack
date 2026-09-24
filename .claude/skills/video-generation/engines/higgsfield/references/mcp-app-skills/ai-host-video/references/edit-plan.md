# LLM-authored edit plan

`edit-plan.md` is the treatment plan. Write it while hosts generate, or before
generation only when the user requests full-plan review.
The model writes it directly; it is not generated from a restricted event catalog.
Use the episode's `motion-direction.md` as the global visual source of truth.
`edit-plan.md` owns each treatment's semantic intent, information states, ownership,
and relative placement. It does not own higgsedit implementation mechanics.

Before writing the sections, read the completed
`visual-plan.json.coverage` rows from the asset-opportunity pass required by
[supporting-media.md](supporting-media.md). The picture medium is already decided: each host job
names the strongest specific still/video candidate and either selects asset ids or
rejects that candidate for host or motion-graphic coverage. Do not reopen or reverse
those choices merely because a motion treatment is easier to author. A card, badge,
diagram, icon field, or typography composition built in higgsedit remains
`motion-graphic`; labels such as content-backed or non-typographic do not turn it into
a supporting asset.

Do not repeat global art direction, provider prompts or complete asset records here.

## Treatment identity

Give every planned graphic or composed visual one stable line:

```text
Treatment ID: host-003-one-few-many
```

The id starts with the owning host job id and a descriptive lowercase slug. It binds
the freeform creative plan to the prepared component, built project, proof sheets, and
final review without constraining the treatment's design. Keep the same id when
geometry or animation mechanics change during calibration or repair. If the complete
episode intentionally contains no treatments, record exactly `Treatment IDs: none`.
Do not use that declaration to bypass the motion-opportunity or creative-review passes.

Now run the motion-opportunity pass on top of the chosen picture plan. For the hook,
chapter turns, enumerations, comparisons, and payoff, record the strongest visual
treatment and its editorial reason. Base the decision on the selected picture, host
performance, framing, attention, readability, rhythm, continuity, and the surrounding
episode. For a visually quiet treatment, name the positive performance, framing,
emotion, or attention reason and compare it with the strongest visible treatment.

For every section record only its editorial decisions:

- **Inputs:** host job id and, on direct runs, coverage row and selected asset ids.
  Reference approved dialogue, camera sequence and media records instead of copying them.
- **Purpose and ownership:** the treatment's information or emotional purpose,
  ON-CAMERA / VISUAL / PLAYBACK mode, and why this composition serves the selected
  picture better than the alternatives. Reuse the coverage rationale rather than
  writing another asset justification.
- **States and lifetime:** what visibly changes between required states, the exact
  phrase or word admitting each speech-dependent action, completed-state hold, and
  exit condition. “Subtract” means objects leave; “compare” means the difference is
  visible. Their labels alone do not implement the action.
- **Placement and continuity:** active camera at entrance and exit, relative screen
  region, host/face/hand exclusions, the outgoing and incoming picture at each handoff,
  behavior across camera changes, and the smallest fallback preserving the meaning.
  Follow Treatment placement below.
- **Audio and open decisions:** music exceptions to the standard ducked bed, PLAYBACK
  mute policy, and unresolved assets or choices. Omit repeated defaults.

Do not prescribe reveal primitives, keyframes, exact entrance or exit durations,
travel, scale, easing, stagger, component trees, helper names, or pixel geometry.
Those choices are made in `edit.jsx` through `video-editing` and `motion-craft` after
the generated footage and measured timing exist. A user-selected style or reference
may require a recognizable motion character, but the plan records the intended
experience rather than compiling it into animation instructions.

Use three picture/audio meanings consistently:

- **ON-CAMERA** — the host's commentary, expression, or performance is the primary
  thing to watch. Supporting material may annotate or share the composition without
  displacing that role.
- **VISUAL** — the selected object, action, place, evidence, or other content is itself
  the subject currently being explained. It may share the frame with the host or own
  the picture while host narration continues.
- **PLAYBACK** — the audience watches or hears inserted content on its own, without
  host commentary. It owns picture and audio in an approved structural slot.

Full-screen composition belongs to VISUAL or PLAYBACK ownership. Under host narration,
compose selected images and videos with the host meaningfully present by default.
Give support the complete frame when required detail needs the available scale,
continuous action needs uninterrupted viewing, explicit user direction calls for it,
or the host's absence creates the stronger editorial result. Record the composition
rationale.

Background music is a bed beneath these ownership modes, never the primary audio. Keep
it ducked under ON-CAMERA and VISUAL speech. Mute it under PLAYBACK unless the plan
explicitly establishes that the inserted media has no conflicting music or ambience.

The plan may invent any coherent editorial motion direction. `auto` and `custom` are
not constrained to the built-in library. In `preset` mode, the selected built-in
constrains the episode-wide visual character but does not impose fixed layouts,
treatment types, components, or animation parameters. No fixed motion recipe, placement
enum, or template catalog is imposed. Camera coverage is the exception: use the stable
camera map from `reference/manifest.json`.

Density is a production budget, not a template. `brief.json.graphics_density` sets how
many treatments the episode pays for: `light` about one per 20 seconds of speech,
`standard` about one per 14, `rich` about one per 10. `standard` is the default when the
user has not asked for more or less ornament. The band bounds the count and nothing
else — which treatments exist, what they do, and how they look stay authored per
episode. Spend the budget where the script earns it instead of spreading it evenly, and
say plainly when a brief needs more treatments than its band allows rather than silently
exceeding it: authoring is the largest single cost in the run, so an unbounded count is
an unbounded schedule.

`CAM_A` remains the frontal direct-address anchor; `CAM_B` is the alternate speaking
angle; `CAM_C` is the close/accent setup. The model decides which mapped setups each
job needs, but does not redefine a camera between jobs. With multiple cameras,
adjacent host jobs must change camera at the seam: the outgoing last shot and incoming
first shot cannot use the same setup. A graphic handoff does not replace this camera
change. Honor an explicit user request for a single camera.

## Treatment placement

For each graphic or composed visual, name the camera active at entrance and exit,
which side or region of the frame it occupies relative to the host, the host/face/hand
area it must avoid, and whether it overlays, recomposes, or replaces the base picture.
Use spatial intent such as `frame-left negative space`, `edge-to-edge background`, or
`host windowed on frame-right`; do not invent pixel coordinates before the generated
footage exists.

When a treatment spans a generated-internal camera change, state whether it
repositions for the destination camera, deliberately holds in a camera-safe region,
splits into two treatment spans, exits before the cut, or moves to another intentional
base picture. Never assume one overlay position is safe across cameras.

A fallback is the smallest change that preserves the treatment's information:
reposition to another safe region, simplify or shorten the copy, split across shots,
move to a neighboring beat, or omit. It must preserve the approved ownership mode;
missing negative space does not promote supporting material from ON-CAMERA to VISUAL
or PLAYBACK. Prefer omission over an unplanned ownership change.

Recomposing the host picture is content-driven treatment vocabulary: a beat may
window or scale the host while host audio continues under VISUAL ownership when the
surrounding frame carries real content — b-roll, evidence, a sourced still, a data
graphic — and the viewer should keep seeing the host react to it. Name that content
in the treatment. Absent explicit user direction, typography-only windowing is either
a brief chapter or hook gesture inside the transition grammar, or a sustained
identity moment with a named editorial purpose at a beat with nothing
showable. When the beat has showable content, the content wins the surrounding frame;
recurring sustained typography-only recompositions fail the anti-template checks. A
user style or reference that specifically calls for that grammar overrides this. A
host-job seam or chapter turn may use a graphic handoff or match-on-motion instead of
a bare camera change when the direction's continuity intent calls for it; assembly
chooses the concrete transition mechanism and those seam handoffs remain chapter
devices.

The camera map describes intended composition, not measured output. The final
`edit.jsx` must inspect the actual generated frames and may refine coordinates, scale,
crop, layout, animation mechanics, and feathering without changing the approved
information intent, ownership mode, selected media, required semantic states, or
speech anchors. If the real footage invalidates the planned composition, use the
approved fallback; do not silently invent a different treatment.

## Timing intent

Before generation, express in-job timing with verbatim phrases, never estimated
seconds. Separate the phrase admitting a composition from the word on which its
emphasis lands; put each needed selector in `anchor-plan.json`, including item reveals.
If a boundary must be frame-exact, make it a host-job seam or a
PLAYBACK structural boundary instead of promising an exact generated-internal cut; a
treatment that must meet a generated cut takes its frame from the measured `cuts.json`
after generation. Resolve adjacent picture spans together during assembly; their
shared handoff need not coincide with an internal label's speech cue.

The semantic end anchor marks the final idea a treatment supports; it is not a command
to disappear on that word. Plan a readable completed-state hold and tail using
[assembly.md](assembly.md). If the host job cannot fit the treatment comfortably,
move, simplify, or omit it rather than accepting a flash.

After transcription and measurement, `clip-bounds.json`, `spine-map.json`, and
`anchors.json` replace semantic intent with measured coordinates. `edit.jsx` must use
those measurements.

## Structural spine

Normally host jobs are contiguous in `jobs.json` order. When media intentionally adds
time, write `spine-layout.json`:

```json
{
  "items": [
    { "kind": "host", "plan_job_id": "host-001" },
    { "kind": "slot", "id": "product-demo", "duration": 5.0 },
    { "kind": "host", "plan_job_id": "host-002" }
  ]
}
```

Every host job must appear exactly once and in order. Slots require unique ids and
positive durations. The edit plan explains what each slot shows and who owns audio.
A slot exists only when media intentionally adds time — PLAYBACK, a supplied intro,
outro, bumper, or similar. Never invent a speech-free hold or empty slot to pad
toward a target duration.

## Approval self-check

- Every speech-dependent treatment has one top-level `anchor-plan.json` label, every
  sequential build carries its own item anchors, and the plan contains no invented
  timecodes.
- The hook, every chapter turn, every enumeration or comparison, and the payoff each
  received a motion-opportunity decision after picture selection: motion over the
  chosen medium, a designed structural event, or a recorded reason to stay quiet. No
  treatment exists to satisfy a count, fill a quiet passage, or pad the master.
- Every treatment follows `motion-direction.md` (visual language, attention/pacing
  arc, continuity intent at seams and chapter turns) and names what it contributes to
  the viewing experience plus the visual behavior that delivers it; concrete animation
  mechanics live only in `edit.jsx`.
- Every treatment names its active mapped camera, relative screen placement, host
  avoidance region, base-picture relationship, camera-change behavior, and a fallback
  that never changes its ownership mode (reposition, simplify, split, move, or omit).
- Every treatment has enough planned room for entrance, fully readable hold, exit, and
  post-anchor tail, and none persists to the next seam without a stated reason.
- Every beat has one intentional base picture and the correct ON-CAMERA, VISUAL, or
  PLAYBACK role under the canonical rule: VISUAL does not interrupt host speech,
  PLAYBACK does; selection, convenience, or missing host-safe space never chose or
  upgraded ownership; every screen-owning image or video under narration records why a
  host-present composition would be weaker; large recompositions appear only when the
  content needs them; the host remains the primary picture across the episode.
- Every sustained host-windowing treatment names the real content owning the
  surrounding frame, or is a typography-only identity moment with a named editorial
  purpose at a beat with nothing showable, and no such recomposition recurs as a
  template device.
- Edge-to-edge and local washes cannot create visible opacity boundaries across
  footage; containers and components serve the episode's language, hierarchy, and
  readability.
- Every approved spoken word appears once and in order; every generation job has one
  exact final request; camera sequences and internal cuts agree with
  `generation-plan.json`; job order and structural slots are unambiguous.
- On normal routes, every generation job has exactly one coverage row with a specific
  strongest still/video candidate, a verbatim anchor, and a use/reject decision
  reflected here; a rejected candidate is the strongest plausible picture, not generic
  filler; `zero_asset_review` challenges the strongest rejected row when nothing is
  selected; chapters about concrete subjects are not left typography-only without
  comparing the chosen treatment against that candidate.
- Every generated or web-sourced image or video is tied to a verbatim script beat, has
  a distinct editorial purpose, and appears in the planned edit; web-sourced items
  carry recorded consent, a source URL, and a run-local file; the medium follows the
  information (video for visible action or change, a still for inspection, authentic
  media only where authenticity is the information); supporting media and graphics do
  not duplicate the same information without a stated reason.
- On normal routes unless the user opted out, `visual-plan.json` contains exactly one
  generated or supplied instrumental music bed kept below the voice, and every required
  asset is named there; without a supplied bed, record that music is omitted.
- Creative choices are specific to this episode: a selected built-in stays recognizable
  through principles and element vocabulary, never through copied layouts or a mandatory
  treatment sequence, and automatic and custom routes are not pulled toward a house
  style.
