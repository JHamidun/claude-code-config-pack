# Steps and counters

Use native step easing for held pose changes:

```js
const stepped = {
  from: { x: 0 },
  to: { x: 120 },
  duration: 1,
  easing: { kind: "steps", count: 4 },
};
```

`count` must be a positive safe integer.

A counter is available only inside a shared `targets` leaf:

```js
const shared = {
  duration: 0.8,
  targets: [
    { target: "Bar", from: { scaleX: 0 }, to: { scaleX: 1 } },
    {
      target: "Value",
      counter: { from: 0, to: 100, decimals: 0, suffix: "%" },
    },
  ],
};
```

A counter-bearing leaf samples the shared schedule at scene fps and holds those samples for every binding. Maximum: 256 samples including endpoints. Pose-only leaves remain continuous.

`decimals` defaults to `0` and must be an integer `0..6`. `prefix` and `suffix` are single-line strings up to 64 characters. The target must be a fixed-size immediate child frame with `layout="none"` and exactly one full-lifetime, single-line static text child.
