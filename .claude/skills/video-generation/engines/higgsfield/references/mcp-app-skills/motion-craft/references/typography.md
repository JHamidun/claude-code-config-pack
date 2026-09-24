# Token text motion

`text.motion` animates tokens inside one native text clip.

```jsx
<text
  motion={{
    by: "character",
    from: { opacity: 0, x: 12, y: 20, scale: 0.9 },
    at: 0,
    duration: 0.4,
    overlap: 0.5,
    easing: "house",
  }}
>
  Native text
</text>
```

`by` is required and accepts `"character"`, `"word"`, or `"line"`. `from` may contain `opacity`, `x`, `y`, and `scale`. `at`, `duration`, and `overlap` are optional numbers. Easing accepts only `"linear"`, `"ease-out"`, or `"house"`. The public contract does not specify defaults for these optional fields.

Text motion emits a `textProgress` track. It is distinct from frame choreography and numeric counters. It does not accept spring, overshoot, or steps objects. To choreograph a text block as one object, wrap it in a frame and animate that frame.
