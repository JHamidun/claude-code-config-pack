# Clip geometry and raw document edits

Persistent native `<frame>` owns layout. Raw clip fields are accessible through bounded `higgsedit ops` edits.

## Clip fields

A clip has `transform`, intrinsic `size`, `opacity`, `blendMode`, `effects`, `timeRange`, animations, presets, mask, and visibility/locking fields. Media clips also have `assetId`, `trim`, `volume`, `muted`, `speed`, `preservePitch`, and `cornerRadius`.

`timeRange: { start, duration }` uses seconds: top-level starts are scene-local, nested starts are parent-local. `trim: { start, end }` uses source seconds.

`transform.x/y` place the anchor in scene pixels. `scaleX/scaleY` multiply intrinsic size; rotation and skew are degrees. `anchorX/anchorY` are normalized within the clip box.

`cornerRadius` and raw clip-mask dimensions are clip-local, pre-transform pixels. Convert an intended screen value by dividing by scale. `cornerRadius` is an object:

```json
{ "mixed": false, "uniform": 64, "tl": 0, "tr": 0, "br": 0, "bl": 0 }
```

Raw box masks use center-based clip-local `x/y`, width, height, rotation, radius, feather, and invert. Compose node masks use a separate top-left schema, including path masks.

## Placement and ops

`place` accepts asset, timeline, trim, track, and fit inputs; use raw `set` ops for unsupported clip fields. `fit` is `cover`, `contain`, or `fill`. Cover crops overflow; contain letterboxes; fill stretches.

```json
[
  {
    "op": "set",
    "path": ["scenes", 0, "tracks", 1, "clips", 0, "transform", "x"],
    "value": 960
  }
]
```

Raw op discriminants are `set`, `insert`, `remove`, and `move`. Paths use array positions, so read fresh state before deriving them. Preserve unrelated fields.

Animated clip properties use supported property names such as `positionX`, `offsetX`, `scale`, `opacity`, `volume`, or `effectParam`; dotted paths such as `transform.x` are not animation properties.
