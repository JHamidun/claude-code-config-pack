# Measured native assembly

Author `edit.jsx` from the actual source media and measured speech. Load the separate
`video-editing` skill for the installed Higgsedit API and `motion-craft` for motion
mechanics. Load only the selected local motion-style profile. Prepare parameterized
motion during generation; bind it to real timing and geometry after collection.

## Sources of truth

Use the selected provider job receipts, original media, actual word timestamps,
source trims and measured master positions. The brief, coverage, motion direction
and edit plan own editorial intent. Suggested records such as `clip-bounds.json`,
`spine-map.json` and `anchors.json` are written by the agent following
[anchor preparation](anchor-prep.md); no helper creates or validates them.
Keep one authoritative measured table and read it from the authoring script rather
than copying seconds into multiple tables. Save the built `project.json` with all
imported assets in one project directory. A Treatment ID connects the plan to its
named composition; it is not evidence that the intended behavior rendered.

## Picture fidelity

Treat `visual-plan.json.coverage` as the picture contract and
`assets.json` as its result ledger. Before authoring treatments, account for every
`use_asset` id: it must be downloaded, imported from its recorded preview/master
source, and used at the matching edit-plan section. Do not replace a selected still
or video with a card, diagram, icon field, generated-looking interface, or typography
because motion is easier to implement; all of those remain `motion-graphic`.

Likewise, do not add a rejected candidate late merely because it finished or looks
attractive. Changing `use_asset`/`reject_asset`, ownership mode, or the selected
asset ids changes the approved plan and requires an updated `visual-plan.json`,
`edit-plan.md`. Repair a failed selected asset, or choose and record a suitable
fallback before assembly. Ask only if this changes a user constraint or needs their
decision; do not silently replace the subject footage with decorative graphics.
Product-reference plates explicitly marked as not shown are exempt from timeline use.

That includes the editorial motion direction and attention arc: every treatment
preserves its approved purpose and intended relationship to the host. Use the plan's
declared fallback when the footage cannot support the planned treatment.

## Implementation ownership

The approved plan is a contract for meaning, not a compiled animation program.
Preserve its ownership mode, selected media, base-picture relationship, semantic
before/after states, state order, phrase anchors, and intended viewer experience.
`video-editing` and `motion-craft` own the concrete `edit.jsx` implementation:
component structure, layout details, reveal primitives, keyframes, entrance and exit
durations, travel, scale, easing, stagger, and helper functions.

Implement every approved state in order when the plan requires staged development.
Choose and refine the animation between those states after inspecting the footage and
proof renders. For a plan with one completed state, choose the reveal that best serves
the treatment.

Local implementation changes stay in the assembly stage and do not invalidate approval when they
preserve the approved intent above. Revise the editorial plan only when changing treatment
meaning, ownership mode, selected media, required semantic states or their order,
speech anchors, or the declared fallback.

Build motion around the approved editorial purpose, episode pacing, and measured
semantic anchors. Use the loaded `video-editing` and `motion-craft` skills as the
implementation authority for components, timing, easing, and animation mechanics.
Keep the complete edit within one coherent craft language.

## Host spine and first delivery

Place selected original host sources in script order using measured `source_from`
and retained duration. `p.cut(handle, {from, dur, at, fit})` uses source `from` and
master `at`, both in seconds. Preserve every spoken word and internal pause. Include
real PLAYBACK and supplied structural segments in their measured slots, with their
own audio. Do not invent holds or stretch speech to reach a planning estimate.

Inspect both sides of job seams and generated internal camera changes. A detector
can suggest a boundary but cannot identify a camera. Repair a demonstrated missing
change through the [completed-source replacement path](generation.md#replace-a-completed-source-with-a-missed-camera-change).
A crop, black pulse or covering graphic does not repair a missing generation change.

Resolve imported media relative to the project directory (or use an absolute local
source path); after import, retain project-local assets in the archive.

Build the measured host spine first, render a host-cut preview with the existing CLI,
probe it and upload it in that same producing sandbox command. Reserve the output
and checkpoint before that command as described in [the runtime](../SKILL.md#openai-runtime-contract).
Present it as the montage without motion, then continue immediately unless the user
requested that checkpoint. Add motion to the same original-source edit; never import
the preview MP4 as the final project's base clip.

VISUAL changes the picture while host narration continues. PLAYBACK occupies real
master time and owns audio. Do not reconstruct generated internal cuts in the editor.
At every picture handoff use one shared frame boundary. A nearby phrase anchor and
source cut are different measurements: do not create a gap or an accidental double
cut between them. Retain a live host window across supporting-picture changes when
the plan requires it, without restarting its entrance animation.

## Placement from actual footage

The camera map and approved edit plan describe intended composition; the downloaded
host frames are the authority for exact geometry. This inspection is owed only by
treatments that share the picture with the host. Before implementing a windowed,
lower-third, or annotating treatment, inspect representative full-resolution frames
for every camera span it overlaps, including both sides of a generated-internal
camera change rather than assuming the mapped negative-space direction survived
generation. A treatment that owns the whole picture has no host geometry to protect;
one representative frame confirming each handoff point is enough for
host-collision safety. A simpler geometry proof does not lower the creative bar:
verify any picture-owning treatment's crop, purpose, presentation, duration, and
handoff with the same care as an integrated composition.

Translate the plan's relative placement into exact `edit.jsx` coordinates, scale,
crop, layout, masks, washes, animation mechanics, and feathering only after that
inspection. Keep the host's face, hands, captions, and active gesture path clear. A
treatment that crosses a camera change must preserve its approved camera-change
behavior. If the intended region is unusable, apply the plan's declared fallback; do
not silently invent a new treatment or ownership mode. Dropping a planned host window
or changing ON-CAMERA, VISUAL, or PLAYBACK is an ownership change, not an
implementation adjustment.

Implement a planned host window as live original footage, above the supporting
picture in the layer order, with a crop that preserves the host's aspect ratio and
gesture. A static host frame is not a window. At master time `t` within one host span,
its source time is `source_from + (t - timeline_start)` from the measured bounds and
spine. For `trimStart`, `t` is the actual media node's master start, including every
ancestor and child `at`; using only its outer treatment start desynchronizes a delayed
window. Keep the window's geometry and motion continuous when a background changes.
Split or rebind it at a host-job boundary to follow the next original source, preserving
the visible state. Keep the original host audio exactly once; composed media is muted
by default.

Transition a screen-owning visual over host footage with a clean cut or an
intentionally designed handoff. Reserve opacity blending for treatments that
explicitly use it: blend the outgoing and incoming pictures over a shared overlap,
without accidentally revealing a third layer of host beneath them. A cut starts fully
opaque; do not add a default parent fade, edge dip or one-frame opacity ramp.

Geometry, component structure, and animation mechanics may change from the planning
expectation without invalidating approval when the editorial intent, required
semantic states, picture/audio ownership, selected media, anchors, and declared
fallback remain intact. Changes to those approved decisions require an updated
`edit-plan.md`.

## Background music

Use an authorized supplied instrumental bed when available; this OpenAI surface has
no music-generation tool. If none exists, continue with clear voice and disclose the
omission. Never substitute speech generation or put music into host prompts.

Prepare the supplied bed with installed FFmpeg at the measured final duration. Join
short repeated regions with `acrossfade`, accounting for overlap duration; three seconds
is a starting crossfade shortened for tiny sources and checked by listening. Preserve
intentional internal pauses. Trim the assembled bed to master length, apply the chosen
gain once (`volume=-24dB` by default) and 0.05–0.15-second outer `afade` ramps. Record
the original, exact preparation command, resulting file and gain in the run.

### Native editable music lane

Use the documented `place` operation after building the picture edit. Check
`higgsedit do PROJECT place --help`. Import the prepared WAV once with `p.add` in
`edit.jsx`, but do not `p.cut` it onto the visual spine. Read the built document:
select the imported audio asset's actual id and the active scene, then append one
new audio lane with `trackIndex` equal to that scene's current track count. Do not
invent ids or hardcode a lane number from another project.

For each measured host-audio span, call native `place` with that same asset id/lane,
`--at` equal to the span's master start, `--duration` equal to its duration, and
`--trimStart` equal to that master start in the full-length prepared bed. For example,
substituting actual ids, lane and measured seconds:

```bash
higgsedit do project place --assetId AUDIO_ASSET_ID --trackIndex NEXT_LANE --at START --duration LENGTH --trimStart START
```

This lets music continue at the correct source time across omitted PLAYBACK slots.
The default bed is absent under PLAYBACK that owns its own audio. Respect explicit
planned music under playback or other intentional omissions. Check every span fits
the prepared source and master. Keep the new audio lane and its cuts at unity gain,
with host voice unchanged. Do not attenuate again through ducking or a post-render mix.

Before placing anything, inspect existing cuts of that prepared asset. Preserve an
already authored bed and its intentional omissions instead of stacking another lane.
A fresh whole-script build replaces the timeline, so repeat this documented placement
step only after a rebuild that removed those cuts. Save the placement recipe, measured
spans, original bed, prepared derivative, authoring source and final built project in
the archive. Render only after placement and read back the actual music cuts.

If native `place` is unavailable, a disclosed fallback is to render voice/picture and
mix the same prepared bed once with FFmpeg `amix` (`normalize=0`, `duration=first`),
copying the video stream. Inspect available audio streams before constructing the
filter. The fallback's bed is reproducible from its archived command/assets but is
not an editable music lane inside the native project; explain that difference.

Listen at the opening, dense speech, repeated joins, PLAYBACK boundaries and ending.
A crossfade does not prove a musically seamless join; adjust audible restarts or dips.
Reduce the single bed gain if it masks consonants. A valid probe does not establish
balance, intelligibility or absence of clipping. Include the final mixed master in
[delivery review](delivery.md), regardless of the chosen route.

## Phrase timing

Use `anchors.json.timeline_phrase_ranges[event_id]` for in-job starts and ends. A
phrase range locates the idea; it does not make phrase start, picture change and word
impact the same event. Use the exact spoken word or item anchor for a timed emphasis,
then work backward for preparation/entrance and forward for the readable hold.
Item reveals use their own measured anchors from `anchor-plan.json`; a percentage of
the scene duration or a fixed delay is not a substitute, including inside helpers.
If any anchor is unresolved, first re-anchor it from the actual transcript as
described in [anchor-prep.md](anchor-prep.md); omit the dependent graphic or visual
treatment only when no usable transcript phrase exists at that beat. Never eyeball a
replacement time and never regenerate an otherwise completed host clip because ASR
wording differs from the approved dialogue.

The anchor end is the final supported spoken idea, not an automatic exit frame. Build
the visible span around the actual composition. Give the entrance time to settle,
hold the completed state long enough to understand, and leave a short readability
tail after the final anchored word. Progressive builds keep earlier items visible
while later items reveal.

Longer copy requires longer holds. Estimate at no faster than three short display words
per second after the composition is fully revealed. Never let entrance and exit overlap
or make a multi-item card appear and disappear inside one fast phrase. If the available
clip range is too short, simplify copy, begin on an earlier valid phrase, continue over
the next compatible camera shot, or redesign the treatment.

Holds have a ceiling as well as a floor. Once the completed state has held its
readable span and the speech has moved past the anchored idea, the treatment exits or
advances — normally within a second or two after the end anchor's tail, not at the
next seam or camera change. Match a longer treatment's visual behavior to inspection,
calm emphasis, or the host's performance, and advance or exit when its value is
exhausted. If the copy cannot be read inside a reasonable span, shorten the copy or
split the treatment instead of extending a static hold.

Set a still's duration from the time the viewer needs to inspect it. Use internal
movement, reframing, or annotation when it improves the approved viewing experience.

## Higgsedit time coordinates

The outer `p.compose(node, { at, dur })` uses master-timeline placement. A child's
`at` is local to its immediate parent, and its `duration` is a span length, not an end
timestamp. Animation keyframe times are local to the animated node itself. For a
measured master anchor `a` and a node starting at master time `s`, its keyframe time
is `a - s`; sum ancestor starts when deriving `s`. A nested frame adds another local
clock. Derive these values from shared measurements once and keep every child and
animation inside its node and ancestor lifetimes. For a delayed animation, its end
is `at + duration`, not just `duration`. Preserve the intended endpoint and elapsed
motion when resolving keyframes; never discard the final key or move its value to
the next frame to make a chain valid. A cut needs no opacity animation. Inspect the
built keyframe times when a span is shortened or keyframes coincide.

A stepped value — a counter, a list of years, a rank that advances — is **one node per
value**, never one node holding a keyframe per value. A node with no explicit lifetime
shows its first keyframe's value from the start of the treatment, so a single node prints
every step at once. Hand over between neighbours flush: end each value at the exact end of its
step and start the next on the step boundary. A visibility window comfortably shorter
than the step leaves frames carrying no value at all, which reads as a dropout and costs
another repair round. Land the number and whatever bar, ring or dial it drives on the same
beat, from the same progress.

## Visual implementation loop

Establish the actual states and layout in code, inspect the built result before
reusing a component, then judge the whole edit from the final render. Prepare
components while hosts generate; the host cut does not require this work to finish
first. Reuse mechanics without replacing individual states with a generic image/fade loop.

- Use persistent `<frame>` trees (`layout` of `column`, `row`, or `grid`) for
  content-flow cards so measured text, padding, gaps, and decoration participate in
  one resolved layout that survives into the published editor. JSX `<row>`/`<column>`
  are baked-layout compatibility nodes, not the default. Frame `layout="none"` with
  explicit local coordinates remains allowed for deliberate overlap and other
  composition-specific designs.
- Give each image or live host a sized native media slot, with a media child using
  `fit` and no duplicate absolute fit geometry. Choose `contain` for the whole object
  or inspect the intended `cover` crop. Allocate the actual free picture area after
  text and host regions; a later opaque column must not cover part of that allocation.
- A layout frame does not require a visible card. For standalone typography, keep
  backgrounds, borders and shadows absent unless the direction calls for them. Use
  the font families and real weights from `motion-direction.md`, verify the rendered
  glyphs in the episode's language, and preserve its intended line breaks and hierarchy.
- Verify text after font resolution and wrapping: all lines, padding and decoration
  must fit the settled box, including later states. Check the final screen position
  after animation, not only authored coordinates. Use `offsetX`/`offsetY` for travel
  relative to a placed node; `positionX`/`positionY` replace that position.
- Build once and inspect `p.read()` / `higgsedit read PROJECT` for timeline and
  resolved layout, then render representative frames. Readback describes the document;
  only pixels show actual glyphs, collision and clipping. There is no compose dry-run API.
- In this same readback, compare each treatment with `edit-plan.md`: the correct live
  host/source is present, the layer order leaves the planned host window visible,
  each required state has an active lifetime, sequential items use their own anchors,
  and the exit restores the intended picture. Reusing a Treatment ID or importing the
  correct asset does not establish that these behaviors were implemented.
- Implement the planned action: subtraction removes the competing objects, a comparison
  exposes the difference, and pointers locate their subjects. Adding labels that name
  those actions is not equivalent. Preserve a shared object when the plan transforms it
  in place. A quiet single-state hold is valid; a decorative zoom does not replace a
  missing state. Use the declared fallback explicitly if the intended action is infeasible.
- Decoration associated with text must follow the resolved layout or be verified
  against it. It must not cross readable text in any animated state. Put a native
  `reveal` on a frame; animate a line rect with `scaleX` or reveal its frame. Do not
  assume a frame-only prop animates a bare rect; confirm the built track exists.
- Moving elements may use any direction, easing, transform, mask, or reveal. Constrain
  or clip them only when their travel would unintentionally leave their intended
  visual region or collide with the host or other readable content. Intentional
  edge-to-edge travel remains allowed when required by the approved motion direction.
- Name every `p.compose` treatment with its exact approved Treatment ID
  (`{ name: "host-003-one-few-many" }`). The agent uses those names to select review ranges; names alone do not prove coverage.

## Washes, scrims, and masks

Never place a semi-transparent rectangular scrim whose visible edge crosses the
footage. That creates a horizontal or vertical exposure boundary through the host.

- An edge-to-edge wash extends to all four scene edges.
- A local readability wash fades to true zero alpha before its boundary; the zero-alpha
  stop must be comfortably outside the text area.
- A lower-third support is either a clearly designed panel or a feathered local mask,
  never an accidental full-width dark band.
- Gradient endpoints must meet a frame edge or have zero alpha. Increase feather width
  on bright, high-contrast footage until no boundary is visible.
- A wash never raises opacity over the host's face or head. Meeting the edge rule does
  not license covering the subject: a gradient authored on the wrong axis can satisfy
  every endpoint rule while its opaque end lands on the face. If text needs a wash
  where the host is, move the text; do not wash the host.
- Keep one opacity treatment per hierarchy level; do not stack parent and child scrims
  into a muddy rectangle.

Verify washes on full-resolution frames from the encoded master: the settled and
seam-side frames of a treatment that carries a wash show which direction each gradient
actually runs and what it covers at full opacity over the real footage. If the viewer
can identify where a wash begins or ends, or any wash overlaps the host's face,
redesign it and inspect the changed output.

If source media, transcripts, bounds, spine, or anchors change, re-read the changed
measurements and update `edit.jsx` before rendering.

## Rendering

Use the installed native CLI and actual help/types as described in
[renderer compatibility](renderer-compatibility.md). In `edit.jsx`, record the edit
with `p.cut` and `p.compose`; omit `p.render()` when rendering separately through the
CLI. A build should not also encode a duplicate full master. For example, with
`project({dir: "project", size: "1920x1080", fps: 24})`:

```bash
higgsedit build edit.jsx
higgsedit read project
higgsedit render project --quality draft --out renders/proof.mp4
higgsedit render project --quality final --depth 10 --workers 3 --out renders/final-pending.mp4
```

Each command is part of an output-producing sandbox unit with downloads/restoration,
probe and PUT, not a promise that the next sandbox sees these paths. The two render
lines illustrate different stages: use draft only when useful for iteration, and
render final once the edit is coherent. Include depth/worker flags only when supported
as described in renderer compatibility. See [delivery](delivery.md) for actual review.
Do not repeat an unchanged render just to pass another phase.

Set 24 fps explicitly. Keep timing in seconds and preserve source speed even when its
frame rate differs. Outer compose placement uses `at` and `dur`; children use local
`at` and `duration`. Child lifetimes and ancestor offsets must preserve the measured
master anchors. Consecutive stepped states use contiguous half-open spans; shortening
each state's lifetime to a percentage would create unwanted blank gaps.

Native 0.14 supports custom GLSL through its documented API when native dependencies
work. Check the specific effect and render a small sample rather than importing an
old blanket ban or assuming browser parity. There is no native LUT support. Use local
font assets and inspect glyphs in the episode's language; repair a failed font in the
same project. Keep authored components, originals and fonts in the final archive.

If a source or measured timing changes, update all dependent nodes and review ranges
before rendering. For a render-only freeze, compare the short encoded range with its
original source. Distinguish static artwork, a frozen source, a frozen video layer and
a frozen whole composition. Retain the command log and failing range; a correct
project preview or valid probe does not prove the encoded failure fixed.

## Full master review and repair verification

Follow [delivery](delivery.md) to extract actual encoded-master frames and short
excerpts around treatment changes, internal cuts and job seams. The agent derives
these ranges from the plan and built timeline; no proof helper or automatic coverage
report is present. Include opening, settled, changed and ending states, with the
concurrent live host and supporting media visible. Inspect full-size pixels and
normal-speed playback when available. Do not infer motion quality from a contact
sheet or a scene summary alone.

Use [creative review](creative-review.md) against the script, direction, state order,
anchors, coverage and intended attention ownership. Gather concrete defects, repair
them together in the owning plan or edit, and inspect changed ranges and neighboring
seams. Broaden review when sources, shared components or master timing changed.
Old samples do not clear a new render. Disclose any review capability that was
unavailable; never invent a successful inspection, metric, receipt or hosted editor.
