# Native composition API

`p.compose(nodes, {at, dur, name?, camera?})` accepts JSX or supplied builders.
`dur` is required. Coordinates are pixels; times are seconds. Authoring fields
come from the installed `types/fable.d.ts`.

## Nodes

| Node            | Fields and behavior                                                                                                                                                   |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `frame`         | Persistent layout, sizing, background, clipping, reveal, choreography                                                                                                 |
| `text`          | Text/children; `width`, `height`, `fontFamily`, `fontSize`, `fontWeight`, `italic`, `letterSpacing`, `lineHeight`, `align`, `color`; flat `strokeColor`/`strokeWidth` |
| `rect`          | `width`, `height`, optional `x/y`, `fill`, `radius`, flat `strokeColor`/`strokeWidth`                                                                                 |
| `path`          | `d`, `width`, `height`, optional `fill`, `stroke: {color, width, cap}`, top-level `dash`                                                                              |
| `media`         | `file={handle}`, `trimStart`, `fit`, sizing, radius; picture-only composition                                                                                         |
| `group`         | Shared transforms/timing; positioned groups need nonzero geometry                                                                                                     |
| `row`, `column` | Compatibility layout baked into coordinates, not persistent Auto Layout                                                                                               |
| `sequence`      | Children follow previous ends plus `gap`; every child needs `duration`                                                                                                |
| `adjustment`    | `effects` on content below; optional `x/y/width/height` region; no pixel shaders                                                                                      |

`icon(name, {size, color, strokeWidth, ...})` returns a Lucide path; names come from
`higgsedit icons QUERY`. Paths support `M/L/H/V/C/Q/Z`, not arcs or `S`.
`morphTo` requires the same command skeleton as `d`; animate `morphProgress` from 0 to 1.

Rect/path fills accept a color or `{kind: "linear"|"radial", angle?,
stops: [{offset, color, opacity?}]}`. At least two stops; offsets are 0–1.
Text uses `color`, not `fill`. Font assets use `typography: {fontAssetId: face.id}`;
registered families use `fontFamily`. See [text features](caption-titling.md).

## Frames

- `layout`: `column` (default), `row`, `grid` with integer `columns`, or `none`.
  Grid has equal columns, no spans. Layout mode does not animate.
- `width/height`: positive pixels, `fill`, or `hug`. Roots default to scene size;
  laid-out child frames default to fill width/hug height. Fill needs a non-hug
  parent axis. Nested absolute frames need explicit dimensions.
- `gap`, `rowGap`, `padding` (number or sides), `wrap`, `align: start|center|end`,
  `justify: start|center|end|space-between`; `origin: top-left|center`.
- `background`, `radius`, `clip`; `reveal: {from, at?, duration?, easing?}` with
  `from: left|right|top|bottom|center`. Reveal clips without reflow; animated
  `width/height/gap` reflow children.
- Children use local coordinates/time. Omitted duration fills the remaining
  parent lifetime; explicit `at + duration` must fit. Lifetimes are `[start,end)`.

Automatic media slots center `contain`/`cover` and preserve aspect; `fill` stretches.
Slots need a resolvable height. Standalone media needs explicit geometry and has
no automatic centering guarantee. In row/column/grid slots, effectParam tracks stay on the media;
transform/opacity tracks stay on the slot. Effects also traverse motion-blur samples.

## Visual options

| Option           | Contract                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `at`, `duration` | Parent-local lifetime                                                                               |
| `animate`        | An array of animation specs                                                                         |
| `effects`        | Ordered `[{kind, params?}]`                                                                         |
| `shadow`         | `{x?, y?, blur?, color?}`                                                                           |
| `mask`           | Non-frame nodes: `{shape: rectangle                                                                 | ellipse | path, x?, y?, width?, height?, radius?, feather?, invert?, d?}`; path uses `d`; frames use `clip`/`reveal` |
| `matte`          | Sibling name or `{source, invert?}`; sibling alpha becomes stencil and stops painting independently |
| `motionBlur`     | `true` or `{samples: 2..16, shutter: 0..1}`                                                         |
| `blendMode`      | Normal plus standard multiply/screen/overlay, contrast and HSL modes                                |
| `z`              | Top-level depth for the compose camera                                                              |

Standard effect IDs: `layer-blur`, `blur`, `brightness`, `contrast`, `grayscale`,
`hue-rotate`, `invert`, `saturate`, `sepia`, `drop-shadow`. Native pixel effects:
`shader`, `film-grain`, `threshold-key`.

## Raw animation

`animate` is always an array of animation specs, including one animation:

```js
const animate = [
  {
    property: "offsetX",
    from: 0,
    to: 80,
    at: 0,
    duration: 0.5,
    easing: "house",
  },
  {
    property: "opacity",
    keyframes: [
      { at: 0, value: 0 },
      { at: 0.3, value: 1 },
      { at: 1.7, value: 1 },
      { at: 2, value: 0 },
    ],
  },
];
```

Keyframe easing controls the outgoing segment. Curves: `ease-out` (default),
`house`, `ease-in`, `ease-in-out`, `smooth`, `linear`, `hold`, `bounce`, or
`[x1,y1,x2,y2]`. Raw tracks do not accept easing objects.

Channels include transforms, opacity, color, blur, volume, masks, path morph,
text progress, frame dimensions, and `effectParam`; the installed animate verb
schema lists supported fields. Times must fit the node. Finite `repeat` unrolls
closed chains, capped at 500 keys. Raw offsets add and uniform scales multiply;
other duplicate property tracks are refused. Distinct effect/parameter targets
can coexist. Choreography cannot also own an existing raw channel.

## Frame choreography

`motion` supports `poses`, local `cues`, `enter`, `settle`, `exit`, and `timeline`.
Phases require positive `duration` and a `from` or `to` pose (or named pose).

```js
const motion = {
  enter: { from: { y: 24, scale: 0.94, opacity: 0 }, duration: 0.4 },
  exit: { to: { opacity: 0 }, duration: 0.2, anchor: "end" },
};
```

Pose channels: `x/y` offsets, `scale` or `scaleX/scaleY`, opacity, rotation.
Neutral offsets/rotation are 0; scale/opacity are 1. Uniform and axis scale cannot
share a target. Enter starts at 0; settle follows enter; exit ends at the frame end.
End-anchored numeric `at` is a lead before the end, not a start time.

`motion.timeline` forms:

| Form                                            | Timing                                  |
| ----------------------------------------------- | --------------------------------------- |
| `{from?, to?, duration, easing?, at?, target?}` | Self or one named immediate child frame |
| `{sequence: [...], gap?, at?}`                  | Consecutive children                    |
| `{parallel: [...], at?}`                        | Same start                              |
| `{stagger: [...], each, at?}`                   | Start offset by index × each            |
| `{duration, easing?, at?, targets: [...]}`      | Shared progress; no per-binding timing  |

`at` is relative to the enclosing cursor/start, or `{cue: "name", offset?}` for an
absolute frame-local cue. Cues cannot precede a sequence cursor. Names are unique;
each tween must fit its target lifetime. Compilation resolves end anchors;
rebuilding retimes them, editing the compiled document does not rerun choreography.

Extra choreography curves: `{kind: "steps", count}`, `{kind: "overshoot", amount?}`
(default 1.70158), `{kind: "spring", stiffness?, damping?, mass?}` (170/26/1).
Springs/overshoot compile to bounded sampled tracks, not live simulations.
Springs reject endpoint position error >0.02 or normalized endpoint speed >0.1.
Opacity outside 0–1 and negative scale are refused. Text `motion.by` is separate.

### Shared counters

```jsx
<frame
  width={320}
  height={160}
  gap={12}
  padding={16}
  motion={{
    timeline: {
      duration: 0.8,
      easing: "linear",
      targets: [
        { target: "Bar", from: { scaleX: 0 }, to: { scaleX: 1 } },
        {
          target: "Value",
          counter: { from: 0, to: 100, decimals: 0, suffix: "%" },
        },
      ],
    },
  }}
>
  <frame name="Bar" width={280} height={12} background="#32acff" />
  <frame name="Value" width={280} height={40} layout="none">
    <text width={280} height={40} fontSize={28} color="#ffffff">
      0%
    </text>
  </frame>
</frame>
```

A counter requires a fixed-size `layout="none"` frame with one static, single-line,
full-lifetime text template, without token motion, animation or matte.
`decimals`: 0–6; prefix/suffix: single-line, ≤64 characters; scaled values must be
safe integers. Counter-bearing leaves quantize **all** bindings to scene-fps held
samples, at most 256 including endpoints. Labels hold before/after the tween.
Pose-only leaves remain continuous. This is compiled text states, not a live text channel.

## GLSL and textures

```jsx
export default async ({ project }) => {
  const p = await project({ size: "320x180", fps: 24 });
  const texture = await p.add("texture.png");
  p.compose(
    <rect
      width={320}
      height={180}
      fill="#dec8a2"
      effects={[
        {
          kind: "shader",
          params: {
            glsl: `vec4 pixel(vec2 uv) {
          vec4 src = texture(u_src, uv);
          vec3 paper = texture(u_paper, uv * 3.0).rgb;
          return vec4(mix(src.rgb, src.rgb * paper, u_amount) * src.a, src.a);
        }`,
            textures: {
              paper: { assetId: texture.id, wrap: "repeat", filter: "linear" },
            },
            amount: 0,
          },
        },
      ]}
      animate={[
        {
          property: "effectParam",
          effectIndex: 0,
          effectParam: "amount",
          from: 0,
          to: 0.7,
          duration: 1,
          easing: "linear",
        },
      ]}
    />,
    { dur: 2 }
  );
  await p.frame(1, "renders/texture.png");
  await p.render("renders/texture.mp4");
};
```

- Define `vec4 pixel(vec2 uv)` only; the wrapper owns GLSL version, precision,
  uniforms and `main`. UV origin is top-left. `u_src` is straight RGBA;
  `u_resolution` is pixel size; `u_time` is supplied timeline seconds.
- Finite numeric parameters become `u_<key>` floats. `effectIndex` selects the
  zero-based declared effect; `effectParam` is its exact existing numeric key,
  not the generated uniform name. Authored `u_amount` therefore maps to `u_u_amount`.
- Up to eight static image textures: imported `assetId`, `wrap: clamp|repeat|mirror`
  (default clamp), `filter: linear|nearest` (default linear). Names must be legal,
  distinct identifiers, without built-in/float collisions. No URLs/video textures.
- Return premultiplied RGBA. Native GL needs EGL/ANGLE; driver failures, invalid
  shaders and missing textures fail rendering. GL selection is separate from video `accel`.
- Shader processing is RGBA8. Direct footage shaders can force an eight-bit fallback;
  separate graphic overlays may retain the high-depth video path. No native LUT or
  shader adjustment nodes. Graphic raster overflow is refused. Browser graphics/group
  shader previews do not share the native rasterization path.

## Transitions and camera

A sequence's outgoing child accepts `transition: {preset, duration}`: fade, blur,
grow, shrink, directional slide, spin, twist. The out/in pair is centered on the cut.

Compose `camera: {focal?, keyframes: [{at, x?, y?, dolly?, easing?}]}` needs at least
two keyframes in absolute timeline seconds and top-level nodes with `z`. Depth
scales motion by `focal/(focal+z)`; dolly changes perspective. This is 2.5D, not mesh 3D.

`compose` with `dryRun: true` validates/compiles without mutation.
`inspect --id CLIP_ID --at SECONDS` reports center-time evaluated parameters, not
shader execution or evaluated world geometry. See [inspection](editor-measured.md).

## Complete example

```jsx
export default async ({ project }) => {
  const p = await project({ size: "640x360", fps: 24 });
  p.compose(
    <frame
      width={640}
      height={360}
      padding={40}
      motion={{
        enter: { from: { y: 24, opacity: 0 }, duration: 0.4 },
        exit: { to: { opacity: 0 }, duration: 0.2, anchor: "end" },
      }}
    >
      <rect
        width={400}
        height={80}
        fill="#32acff"
        animate={[{ property: "scaleX", from: 0, to: 1, duration: 0.6 }]}
      />
    </frame>,
    { dur: 2 }
  );
  await p.frame(1, "renders/frame.png");
  await p.render("renders/video.mp4");
};
```
