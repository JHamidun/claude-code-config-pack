# Text and caption capabilities

Text is an editable native clip, not DOM content. Timed captions are text/frame
clips placed from supplied cue or word timestamps; the CLI has no speech
transcription or transcript-search API. Transcript strings are display data.

## Text fields

- Box: `x`, `y`, `width`, `height`; wrapping, explicit newlines, `align`.
- Font: `fontFamily`, `fontSize`, `fontWeight`, `italic`, `letterSpacing`;
  `lineHeight` is a multiplier, default 1.2.
- Appearance: `color`, flat `strokeColor`/`strokeWidth`, `shadow`, effects and masks.
  Text does not accept `fill` or a `stroke` object.
- Token entrance: `motion: {by: "character"|"word"|"line", from?, at?, duration?,
overlap?, easing?}`. Pose: opacity/x/y/scale; easing: linear/ease-out/house.
- Whole-block motion: raw `animate` or surrounding frame choreography/reveal.

## Font bytes and shaping

```bash
higgsedit fonts list
higgsedit fonts add PROJECT "Inter:700"
```

`await p.add("Face.ttf")` returns a font handle. `typography: {fontAssetId: face.id}`
opts into native shaping; registered legacy text uses `fontFamily`.

Typography options include variable `axes`, OpenType `features`, `script`,
`language`, `direction: ltr|rtl`, `bend: {amplitude, wavelength, phase, stretch}`
(phase in radians), and `drawProgress`. Axes require supporting font bytes.
`textDrawProgress` animates shaped glyph contours; visible stroke is required for
an outline draw. Shaping is single-font/single-script with limited fallback.

## Caption layers

Static phrases, per-word color/opacity, outline states, plate backgrounds,
karaoke and moving highlights are combinations of nodes and tracks, not named
caption presets. Composed media is picture-only; required source audio belongs
on the cut/audio spine or a separate mix.

[Caption systems](caption-systems.md) · [Title mechanisms](title-animation.md)
