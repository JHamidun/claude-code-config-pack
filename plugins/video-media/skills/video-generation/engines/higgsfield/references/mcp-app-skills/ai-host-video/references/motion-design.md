# LLM-authored motion direction

Design one motion language for this episode after the spoken script is approved and
the host reference has been analyzed. `visual-plan.json.coverage` selects the picture
medium for every host job. Accepted generation requests remain immutable: motion
adapts to their camera sequence without silently sending another billed request.
Follow the style route
recorded in `brief.json.motion_style`: automatic, a user-selected built-in, or custom.
Derive the direction from that route, the script, planned media, visual references,
and camera-map constraints. Actual footage geometry is resolved during assembly.

Write the result to `motion-direction.md`. This document is creative intent for
`edit-plan.md` and `edit.jsx`, not a component schema. The stable camera map already
exists in `reference/manifest.json` before this document is authored. Use that map to
define episode-wide placement policy, but leave each treatment's active camera,
composition, and relative screen placement to `edit-plan.md`.

## Style route

Read [motion-styles.md](motion-styles.md) before writing the direction. In preset mode,
load the selected local style reference as described there; preserve its composition and
motion character in the episode's direction. User direction and the selected style
govern craft choices; generic craft defaults fill gaps, while engine capabilities
bound the feasible implementation.

- **`auto`** applies when the user picked Auto in intake or delegated the choice.
  Diagnose the episode and invent the strongest coherent
  direction. It may use one built-in as an influence, blend compatible principles, or
  use none of them. Never turn topic classification into a preset lookup.
- **`preset`** requires an explicit user selection. Keep that preset's compositional
  logic, element family, and motion character recognizable, but adapt palette,
  typography, copy, density, assets, and treatment geometry to the episode. The
  preset is not an event catalog or fixed component kit.
- **`custom`** preserves the user's art direction, brand system, and supplied visual
  references. Do not relabel it as a built-in merely because some traits overlap.
  Adapt only where readability, source truth, platform safety, or host visibility
  requires it.

When a custom visual reference is a video or video URL, use the recorded
the runtime video-inspection sequence findings required by [user-inputs.md](user-inputs.md). Derive the
direction from timestamped evidence in its audiovisual content; indirect
representations may supplement but never replace that evidence.

Do not silently change routes. A user may switch routes before plan approval; update
`brief.json`, re-author `motion-direction.md`, and show the changed plan again.

## Evidence hierarchy

Use these sources in order:

1. **Explicit user references and brand rules.** Preserve supplied colors, typography,
   logos, and visual references unless they make the video unreadable.
2. **Explicitly selected built-in.** In `preset` mode, preserve its defining visual
   grammar while adapting it to the user's brand and content. This source is absent in
   `auto` and `custom`.
3. **Script type and dramatic movement.** Identify what the script is doing, how its
   energy changes, and which ideas need orientation, compression, contrast, proof, or
   payoff.
4. **Audience and platform expectations.** Keep the result readable at YouTube viewing
   distance without defaulting to generic creator graphics.
5. **Host footage compatibility.** Use the reference to find safe placement and enough
   contrast, not as an automatic palette, typography, or material source.

When sources conflict, explicit user references control identity and the script
controls meaning and rhythm. An explicit preset choice controls the starting visual
grammar but does not override brand requirements, factual clarity, or safe placement.
In automatic mode, choose the art direction independently. Sample or echo the host
frame only when that choice strengthens the visual thesis.

## Read the script before styling

Name the dominant narrative form and any secondary mode:

- story, confession, or commentary;
- argument, analysis, finance, or investigation;
- tutorial, process, build, or transformation;
- review, ranking, or comparison;
- news, update, or high-tempo briefing;
- reflective, personal, or emotionally restrained piece;
- another form justified by the actual script.

This classification is reasoning evidence, not a preset lookup. Two analytical scripts
may need different styles when one is urgent and adversarial while the other is calm
and educational. Even when a preset is selected, use the diagnosis to decide which of
its principles belong in each beat and which passages should remain quiet.

Map the script's emotional and informational arc:

- opening promise or tension;
- chapter turns;
- claims that need evidence;
- numbers, comparisons, or enumerations that benefit from visual compression;
- moments that should stay visually quiet;
- reveal, verdict, payoff, and CTA.

Use this map to understand the decisions already recorded in
`visual-plan.json.coverage`; do not replace a selected still or video with a motion
graphic while styling the episode. More host energy does not
automatically mean more graphics or b-roll.

## Editorial judgment

Plan visual pacing in natural language around the episode's information and emotional
arc. Keep the host as the primary picture wherever the performance, framing, or
deliberate stillness best serves the beat. Add graphics or supporting media for a
specific editorial purpose grounded in attention, readability, rhythm, emphasis,
continuity, or understanding.

For a visually quiet structural beat, record the positive performance, framing,
emotion, or attention reason and compare it with the strongest visible treatment.
Judge the complete episode sequence when balancing host-led and visually supported
passages.

Treat selected media as an input and motion as a second decision about how the beat
should be presented and paced. Shape the motion language around the recorded medium
and its role in the episode. Picture ownership is assigned in `edit-plan.md` through
the canonical ON-CAMERA, VISUAL, or PLAYBACK rule.

Reserve major recomposition for content that needs comparison, readable evidence, a
changed attention owner, or a deliberate chapter-level interruption.

## Read the host for compatibility

Inspect:

- available negative space around each camera framing.
- face, hands, captions, and other areas that must remain unobstructed;
- local luminance and color contrast behind possible overlays;
- camera changes that make a placement unsafe.

These observations constrain readability and placement only. They do not prescribe
the palette, fonts, geometry, materials, or animation style.

## Contemporary editorial baseline

Execute the episode's own direction with the visual discipline of current premium
editorial video:

- intentional asymmetry, strong scale contrast, clean negative space, and decisive
  alignment;
- typography composed as image through considered line breaks, tracking, hierarchy,
  and contrast;
- footage and evidence treated as first-class picture material within the edit;
- restrained texture and depth used to unify the episode;
- confident movement followed by calm readable holds.

## Typography as the visual subject

Resolve the episode's type system in the art direction: name the chosen font families
and real weights for display, supporting copy and source/data labels where needed.
Describe their hierarchy, line-break character, alignment and spacing by role. Reuse
supplied brand fonts where suitable; check the actual language, symbols and available
font files before implementation. If a face is unavailable, preserve its role and
character with a verified alternative. Do not default every preset to the same pair.

For a text-led beat, compose the words or numerals themselves through scale, placement,
line breaks and negative space. A short phrase revealing by line, a key word retained
through a change of thought, or a numeral becoming the anchor of a conclusion can be
a complete treatment without a card, pill, border or decorative backing. Add a
container when it clarifies grouping or solves a real contrast problem. Keep display
copy distinct from verbatim captions; do not turn every spoken word into an animation.
Choose these treatments where the script benefits, without a typography quota.

## Editorial motion direction

Write motion character as episode-specific editorial intent. Describe how motion
supports the viewer and how active and visually quiet passages shape the episode.
Every `motion-direction.md` defines:

- **Editorial role** — what motion contributes to attention, readability, rhythm,
  emphasis, continuity, or understanding across this episode.
- **Rhythm and restraint** — where support enters, holds, leaves, or deliberately
  stays absent. Describe pacing relative to the speech and energy arc, not in
  milliseconds.
- **Continuity intent** — which host-job seams and chapter turns cut plainly and which
  carry an editorial handoff, developing object, or base-picture change. Leave the
  concrete transition mechanism to assembly after the footage is visible.
- **Coherence cues** — the visual materials, hierarchy, and motion character that
  make the treatments belong to one episode.
- **Optional signature behavior** — when the script earns a memorable experience,
  name the beat and what should feel different about it. Leave its keyframes to
  implementation.

Exact animation primitives, entrance and exit durations, travel, scale, easing,
stagger, keyframes, component structure, and JSX helpers are implementation choices.
`video-editing` and `motion-craft` choose them in the assembly stage from the approved intent,
measured speech, selected media, and actual generated frames.

Define one coherent visual language for the episode. Choose each treatment from the
script beat, selected media, host performance, composition, and readability. Describe
only the visual behavior needed to deliver its editorial purpose.

## Attention and pacing arc

Map in natural language where the host should remain unobstructed, where visual
support helps, and whether any beat warrants a stronger interruption or change in
attention ownership. Give the hook, chapter turns, and payoff deliberate visual
decisions based on their role in the episode and surrounding pacing.

## Required motion-direction.md

Write one compact global direction, with no per-job inventory:

1. **Visual thesis and art direction** — the episode idea, palette, typography and
   image treatment. Reference the style selection in `brief.json`; describe only its
   adaptation rather than copying intake or script analysis. Include the resolved type
   roles above so assembly can implement the chosen typography rather than guess it.
2. **Motion language and progression** — editorial role, rhythm/restraint, continuity
   intent and coherence cues from the guide above. Record an optional signature only
   when a particular beat earns it. Exact primitives remain implementation choices.
3. **Integration and compatibility** — how selected media and host footage share the
   visual language, camera-wide placement/fallback principles and quality priorities.
   Individual assets, treatments, anchors and required states belong in their own plans.

`motion-direction.md` governs what motion communicates and how it shapes the episode;
`video-editing` governs the higgsedit implementation.

## Responsibility boundary

Keep `motion-direction.md` global. It defines the visual thesis, art direction, motion
character, hierarchy, and camera-aware placement policy shared by the episode. It does
not choose the treatment for an individual phrase, assign that treatment to a camera,
or prescribe exact coordinates.

Put those beat-level decisions in `edit-plan.md`: treatment form, active mapped
camera, relative placement around the host, ownership mode, behavior across any
generated-internal camera change, and a fallback when the planned safe region is not
available. Exact pixel geometry belongs only in `edit.jsx` after the generated footage
has been inspected.

## Design rules

- Use motion to support attention, readability, rhythm, emphasis, continuity,
  understanding, or another episode-specific viewing need.
- Write designed display copy with exact transcript phrases reserved for semantic
  timing anchors.
- Give text on busy footage readable support through an edge-safe wash, quiet panel,
  controlled crop, or another treatment consistent with the material language.
- Extend a wash to every scene edge or feather it to true zero alpha, keeping exposure
  continuous across the host and set.
- Place graphics in real negative space. If a camera places the host on frame right,
  prefer frame left; reverse this when the host is on frame left. If there is no useful
  negative space, reposition, simplify, split, move, or omit the overlay without
  changing its ownership mode. Treat the camera map as a planning constraint, not
  proof that generated footage preserved the expected empty area.
- Author movement specifically for the composition and editorial purpose.
- Choose each composition from the script beat, selected media, host performance,
  available space, and readability while maintaining the episode's visual language.
- Treat host-job seams and chapter turns as design surfaces. The continuity intent
  decides which boundaries receive an editorial handoff or base-picture change and
  which cut plainly; assembly chooses the transition mechanism.
- Windowing or scaling the host while host audio continues follows real hosted-YouTube
  grammar: the recomposition exists to give the frame to content. Window the host when
  the surrounding picture carries information — b-roll, evidence, a sourced still, a
  data graphic — and the viewer should keep seeing the host react to it.
  Typography-only windowing serves a brief chapter or hook gesture inside the
  direction's continuity intent, or a sustained identity moment with a named
  editorial purpose.
- A treatment is a bounded event: entrance, readable hold, exit, each tied to the idea
  it supports. When the speech moves to the next idea, the treatment leaves or
  advances; it does not persist until the next seam by default.
- Match each hold to the time needed for readability, inspection, calm emphasis, or
  host performance. Add internal development when it improves the beat.
- Let a picture-owning still remain available for useful inspection. Add crop, focus,
  annotation, or other motion when it improves the content's presentation.
- Treat recurring subjects according to the role of each appearance and the episode's
  established visual language.
- Base in-job timing on measured phrase anchors after transcription.
- Graphics may cover or recompose host picture while host audio continues. Only an
  approved PLAYBACK slot may interrupt host speech and own audio.

## Self-check

Before plan approval, confirm:

- the visual thesis follows the script, the recorded `brief.json.motion_style` route,
  and explicit user references; the route is stated accurately and honoured (automatic
  derives from the episode, preset adapts the selected style, custom preserves the
  user's own direction);
- the palette and materials maintain readable contrast, and every wash reaches the
  frame edge or fades completely to zero alpha without a visible exposure seam;
- the editorial motion direction states editorial role, rhythm and restraint,
  continuity intent, and coherence cues; rhythm follows the script's information and
  emotional arc, and any signature behavior follows a specific episode beat;
- the attention and pacing arc records deliberate hook, chapter-turn, and payoff
  decisions in relation to the complete episode;
- every treatment belongs to the episode's visual language, has a stated editorial
  purpose, and fits its content, readability, placement, and ownership; the direction
  feels authored for this episode rather than assembled from a house template;
- selected assets remain first-class picture material with beat-appropriate ownership,
  recurring assets are reviewed together for coherent use, major recompositions follow
  content and ownership, and the host remains the visual center of the episode;
- every sustained host-windowing passage carries real content in the surrounding frame
  or serves a typography-only identity moment with a named editorial purpose;
- every treatment has a planned exit tied to its idea, and every long stable span
  remains readable and useful for its full duration;
- global placement policy accounts for every selected camera without duplicating
  treatment-level placement from `edit-plan.md`, and `edit-plan.md` implements the
  direction as an episode-specific plan.
