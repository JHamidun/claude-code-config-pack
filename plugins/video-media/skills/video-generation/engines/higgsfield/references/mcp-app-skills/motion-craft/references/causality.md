# Timelines, targets, and cues

`motion.timeline` supports leaves and nested `sequence`, `parallel`, and `stagger` combinators.

```js
const motion = {
  cues: { result: 0.6 },
  timeline: {
    sequence: [
      { target: "Title", from: { y: 24 }, duration: 0.4 },
      {
        parallel: [
          { target: "Bar", from: { scaleX: 0 }, duration: 0.3 },
          { target: "Value", from: { opacity: 0 }, duration: 0.2 },
        ],
      },
    ],
    gap: 0.1,
  },
};
```

`sequence` inserts `gap` between children; default gap is `0`. `parallel` lasts to the latest end. `stagger` requires `each` and offsets item `i` by `i * each`. Numeric `at` delays assigned start. `{ cue: "result", offset: 0.1 }` uses the owning frame's local cue.

Omit `target` to animate the owner. A target must uniquely name an immediate child frame. Cues and poses are not inherited.
