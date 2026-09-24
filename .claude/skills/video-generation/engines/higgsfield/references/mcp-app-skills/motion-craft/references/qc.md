# Validation and limits

Choreography rejects unknown fields, nulls, nonfinite values, malformed or ambiguous targets, missing poses/cues, invisible spans, and spans outside frame lifetimes.

Ownership rules:

- Motion and raw tracks cannot own the same property.
- Position/offset aliases conflict.
- Uniform and axis-scale aliases conflict.
- Overlapping choreography segments on one channel fail, including overlaps inside `parallel`.
- Non-overlapping segments on one channel compile into one chain.

Limits per frame motion:

- combinator nesting: 8 levels;
- plans/bindings: 256;
- compiled keys: 500 per property track;
- counter-bearing shared leaf: 256 scene-fps samples, including endpoints.

Opacity outside `0..1` and negative scale are errors. Limits fail rather than truncate.

Choreography is frame-only and recompiles when its authored script rebuilds. Editing compiled tracks on the human timeline does not rerun choreography. Persisted output contains native groups, property tracks, and bounded text states; it introduces no runtime callbacks or new wire format.
