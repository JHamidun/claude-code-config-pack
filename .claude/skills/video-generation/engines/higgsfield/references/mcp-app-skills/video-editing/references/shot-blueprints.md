# Shot construction primitives

These are capability mappings, not required scene templates.

| Need                               | Native primitives                                                                  |
| ---------------------------------- | ---------------------------------------------------------------------------------- |
| Sequential phrases or states       | `sequence`, child `at`/`duration`, text keyframes                                  |
| Cards, lists, or logo walls        | persistent `frame` with column, row, or equal-column grid layout                   |
| Input-to-result demonstration      | frames for UI regions, cursor paths, explicit state clips                          |
| Control and target moving together | shared keyframe data applied to separate nodes or frame motion targets             |
| Footage beside graphics            | row/column frame with a centered `media` slot and text/card frames                 |
| Talking head with overlays         | spine cut for audio/picture plus composed frames for titles and cards              |
| Metrics and charts                 | text, rect, path, `effectParam`, width/height, color, and draw-progress tracks     |
| Hub-and-spoke diagram              | path connectors, icon/media nodes, groups, and 2D transforms                       |
| Before/after comparison            | row or grid frames with synchronized node tracks                                   |
| Zoom or parallax                   | top-level `z` values plus `compose(..., { camera })`, or group/frame 2D transforms |
| Logo or title build                | path, shaped-text draw progress, masks, reveal, token motion, and keyframes        |
| Abstract field                     | deterministic path/rect states, gradients, effects, and explicit tracks            |

Persistent frames retain editable layout. `layout="grid"` supports an integer `columns` count with equal columns; spans and `minmax` are unsupported. `layout="none"` enables deliberate positioning.

Frame child clocks are parent-local. Keyframes are node-local. A child with explicit timing must fit the parent's half-open lifetime. There are no per-frame callbacks; represent state with keyframes, sequence children, text motion, frame choreography, or explicit clips.

Use `contain` or `cover` media in a frame with resolvable dimensions. Animate frame width/height when layout should reflow; use `reveal` when layout should remain fixed.
