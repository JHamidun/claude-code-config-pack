# Timing and phases

`enter`, `settle`, and `exit` require a positive `duration` plus `from` or `to`.

```js
const motion = {
  enter: { from: { y: 40, opacity: 0 }, duration: 0.55 },
  settle: { to: { y: 0 }, duration: 0.2 },
  exit: { to: { y: -16, opacity: 0 }, duration: 0.25, anchor: "end" },
};
```

Defaults:

- `enter`: starts at local zero, anchored to start.
- `settle`: starts after `enter`, or at zero without it; anchored to start.
- `exit`: ends at the frame end; anchored to end.
- choreography easing: `"ease-out"`.

For start anchors, numeric `at` delays the default start. For end anchors, numeric `at` is lead time before the frame end. End-anchored phases cannot use cues. Motion spans cannot exceed the target frame lifetime.

Missing `from` continues the previous settled value or neutral pose. Missing `to` returns to neutral. Values hold before, between, and after phases. Frame lifetimes are half-open.
