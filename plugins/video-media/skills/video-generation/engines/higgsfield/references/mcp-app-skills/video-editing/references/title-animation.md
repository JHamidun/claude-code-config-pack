# Title animation primitives

Titles are native node trees. There is no title-animation library or per-frame callback API.

## Primitives

- **Move, scale, rotate, fade:** node `animate` tracks or frame `motion`.
- **Blur and color:** raw `animate` tracks, not frame poses.
- **Token entrance:** `text.motion` by character, word, or line.
- **Wipe:** frame `reveal` or node mask with `maskWidth`/`maskHeight` animation.
- **Outline and draw-on:** text `strokeColor`/`strokeWidth`; shaped text `textDrawProgress`; path `strokeWidth` animation or mask reveals.
- **Reflowing resize:** animate persistent frame `width` or `height`.
- **Fixed-layout transform:** animate a frame or group transform.
- **State sequence:** `sequence` children, explicit child timing, or keyframe chains.
- **2.5D camera:** top-level node `z` plus `compose(..., { camera })`.
- **Effects:** ordered node `effects`; animate numeric parameters with `property: "effectParam"`, `effectIndex`, and `effectParam`.
- **Motion blur:** `motionBlur: true` or `{ samples, shutter }`; effects are evaluated through motion-blur samples.

## Timing contract

Animation times are local to the node. Replacement properties use one track; raw offsets add and uniform scales multiply. Keyframe times must strictly increase and the chain must end within the node lifetime. Frame children use the immediate parent's local clock and must fit its half-open lifetime.

Component node trees compile at local time zero. Place only the component instance root on the timeline; nested nodes retain local timing.

A positioned frame can use `origin="center"` for center-based transforms. Frame `width`/`height` tracks trigger layout; `reveal` does not.

Text uses flat `strokeColor` and `strokeWidth`, not a `stroke` object. `path()` accepts `M/L/H/V/C/Q/Z` commands in its own pixel coordinate system and does not scale path data merely because `width` or `height` changes.

Raw easing accepts named curves or four cubic-bezier handles. Frame choreography also supports steps, overshoot, and bounded spring timing.
