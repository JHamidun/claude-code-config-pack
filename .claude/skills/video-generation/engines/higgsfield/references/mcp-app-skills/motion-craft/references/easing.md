# Easing and sampled curves

Frame choreography accepts raw easing names, four-number bezier arrays, and sampled curve objects.

```js
const curves = [
  "house",
  [0.16, 1, 0.3, 1],
  { kind: "steps", count: 4 },
  { kind: "overshoot", amount: 1.70158 },
  { kind: "spring", stiffness: 170, damping: 26, mass: 1 },
];
```

Raw names are `house`, `ease-out`, `ease-in`, `ease-in-out`, `smooth`, `linear`, `hold`, and `bounce`. Choreography defaults to `ease-out`. Overshoot `amount` defaults to `1.70158`. Spring defaults are stiffness `170`, damping `26`, mass `1`; all spring parameters must be positive.

Springs are sampled at least 120 times/second and 16 times/natural cycle. Overshoot is sampled at 120 times/second. Compiled tracks use linear interpolation; no runtime solver runs. Endpoints are exact. Springs fail when endpoint position error exceeds `0.02` or normalized endpoint speed exceeds `0.1`.

Opacity must stay within `0..1`; scales cannot become negative.
