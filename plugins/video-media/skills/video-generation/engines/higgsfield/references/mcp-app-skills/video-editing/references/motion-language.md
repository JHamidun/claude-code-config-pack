# Motion feature mappings

These are combinations of native features, not additional preset names.
Exact fields and limits: [composition API](compose.md).

| Result                            | Supported mechanism                                                          |
| --------------------------------- | ---------------------------------------------------------------------------- |
| Entrance / hold / exit            | Frame `motion.enter`, `settle`, end-anchored `exit`                          |
| Pop / overshoot / spring          | Choreography easing objects or explicit raw scale keys                       |
| Staggered cards                   | `motion.timeline.stagger` with `each`; targets are immediate child frames    |
| Word / character / line arrival   | Text `motion.by`; one text clip                                              |
| Wipe / phrase highlight           | Frame `clip` + `reveal`, or animated mask geometry                           |
| Counter and bar                   | One timeline leaf with `targets`: transform bindings plus explicit `counter` |
| Slider / cursor / target coupling | Shared `targets` progress or identical authored key times                    |
| State replacement                 | Timed sibling clips, opacity tracks, or sequence transitions                 |
| Repeated movement                 | Finite closed `animate` chain with `repeat`                                  |
| Connector reveal / morph          | Mask wipe, or matching `d`/`morphTo` with `morphProgress`                    |
| Camera move / parallax            | Parent frame transforms, or compose camera with top-level `z`                |
| Particles / glitch                | Finite generated shapes and deterministic authored keyframe tables           |

A mask wipe is not a path-length-aware stroke draw. Shaped glyph outlines instead
support `textDrawProgress` with font bytes and visible stroke.

Shared counters use held scene-fps samples for all coupled bindings, not a
runtime text callback. Independent animated values are not automatically coupled.
A color tween is a solid-color change; gradient stencils use separate geometry
and mattes. None of these mappings implies cross-scene object identity.
