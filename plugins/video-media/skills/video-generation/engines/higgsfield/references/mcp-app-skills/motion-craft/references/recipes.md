# Raw animation forms

Use `animate` arrays for native properties not covered by frame poses.

```js
const animate = [
  {
    property: "blur",
    from: 12,
    to: 0,
    at: 0.1,
    duration: 0.4,
    easing: "ease-out",
  },
  {
    property: "opacity",
    keyframes: [
      { at: 0, value: 0, easing: "linear" },
      { at: 0.2, value: 1 },
      { at: 1.8, value: 1, easing: "linear" },
      { at: 2, value: 0 },
    ],
  },
];
```

Track times are seconds from the node's start. `at` defaults to `0`. A keyframe's `easing` controls the segment leaving that keyframe; otherwise the animation easing applies. Values may be numbers or CSS colours.

A chain may set `repeat`; each cycle shifts by the chain span and the chain must end where it starts. For `property: "effectParam"`, provide `effectIndex` and `effectParam`.

Raw tracks and choreography may coexist only when they own unrelated properties.
