---
name: motion-craft
description: >
  Design concrete motion tracks for native Higgsedit compositions:
  frame choreography, timed text entrances, shared timelines and counters.
  Use for authoring how a native composition animates. General animation
  ideas, UI advice and CSS or JavaScript snippets do not activate this skill.
  Use video-editing for project assembly, footage edits and rendering.
metadata:
  source_revision: "5073f3a09d3f6b0469db9ff7e8a9df0d339f743a"
---

# Motion Craft

## Scope

The deliverable is a motion specification for a native composition. General
suggestions about animation or interface behavior remain an ordinary text/code
request; do not choose Higgsedit for the user merely because motion is mentioned.

Use native composition motion only. There is no HTML animation, CSS, expression evaluator, runtime callback, or playback physics clock.

## Runtime and loading

Use the installed `$video-editing` skill for project creation, sandbox execution,
media transfer and rendering. Inspect the installed CLI help and `types/fable.d.ts`
before selecting APIs: a newer skill does not update the hosted renderer. Use only
supported native motion; frame choreography and shared timelines below require a
matching CLI. On older versions, use supported raw tracks for equivalent behavior
or explain the specific missing capability. Do not upgrade the shared runtime.

Read only the references needed for the selected motion technique. Start with the
relevant timing or layout contract; do not load all eight references by default.

## Motion APIs

- Frame choreography: set `motion` on `frame(...)` or `<frame motion={...}>`. It supports named `poses`, local `cues`, `enter`, `settle`, `exit`, and literal `motion.timeline` data. Pose fields are `x`, `y`, `scale`, `scaleX`, `scaleY`, `opacity`, and `rotation`.
- Raw tracks: set `animate: [{ property, from, to, at, duration, easing }]` or use `keyframes: [{ at, value, easing? }]`. Use raw tracks for properties outside the frame-pose set.
- Token text motion: `<text motion={{ by: "word", from: { opacity: 0, y: 20 }, at: 0, duration: 0.4, overlap: 0.5, easing: "house" }}>Text</text>`. `by` is `"character" | "word" | "line"`; accepted easing is `"linear" | "ease-out" | "house"`.
- Shared choreography: one timeline leaf can bind the same progress to multiple immediate child frames through `targets`. A pose-only leaf remains continuously interpolated. If any binding is a `counter`, the whole leaf uses held samples at scene fps, including pose bindings, with at most 256 samples.

Choreography compiles into editable native property tracks and bounded text states when the script builds. Rebuilding the script recompiles it; human timeline edits do not rerun choreography.

## References

- [Timing and phases](references/timing.md)
- [Easing and sampled curves](references/easing.md)
- [Token text motion](references/typography.md)
- [Frame layout and transforms](references/composition.md)
- [Timelines, targets, and cues](references/causality.md)
- [Steps and counters](references/stepped.md)
- [Raw animation forms](references/recipes.md)
- [Validation and limits](references/qc.md)
