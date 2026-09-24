# Frame layout and transforms

Frame choreography changes pose, not layout geometry.

```jsx
<frame
  x={100}
  y={80}
  width={640}
  height={360}
  origin="center"
  layout="row"
  gap={24}
  motion={{ enter: { from: { x: 40, scale: 0.9 }, duration: 0.5 } }}
/>
```

Pose `x`/`y` compile to additive `offsetX`/`offsetY`; they do not replace frame coordinates. `scale` is uniform and cannot be combined with `scaleX`/`scaleY`. Rotation is in degrees. Neutral values are `x: 0`, `y: 0`, `scale: 1`, axis scales `1`, `opacity: 1`, and `rotation: 0`.

Supported pose fields are limited to `x`, `y`, `scale`, `scaleX`, `scaleY`, `opacity`, and `rotation`. Use raw `animate` tracks for other properties. Use a wrapper frame when two independent transforms must affect the same content.
