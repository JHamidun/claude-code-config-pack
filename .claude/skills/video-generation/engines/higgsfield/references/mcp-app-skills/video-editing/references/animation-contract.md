# Time and animation semantics

| Clock                                   | Meaning                                             |
| --------------------------------------- | --------------------------------------------------- |
| `p.cut(..., {from})`, media `trimStart` | Source seconds                                      |
| `p.cut` / `p.compose` `at`              | Whole-project timeline seconds                      |
| Frame child `at`                        | Seconds after parent starts                         |
| Animation/keyframe `at`                 | Seconds after target starts                         |
| `inspect --at`                          | Whole-project timeline seconds; scenes concatenated |

A composition at 10s containing a frame child at 1s places that child at 11s.
If the parent lasts 4s and child duration is omitted, the child inherits 3s.
Frame lifetimes are half-open `[start,end)`; ancestors gate descendants.
Explicit child and animation spans must fit their owner.

## Compiled motion

Frame `motion` emits property tracks. End-anchored exits resolve against the
frame's lifetime during compilation. Script rebuilds recompute them; visual-editor
track edits do not rerun the script. Whole-script builds replace the timeline;
shared documents retain their current state through bounded `do`/`ops` edits.

Raw `animate` is an array. A keyframe's easing controls its outgoing segment.
Equal values at consecutive keys hold a state; `hold` retains the previous value
until the next key. Finite `repeat` requires a closed chain and unrolls it.

Offsets add and uniform scales multiply across raw tracks. Other duplicate
channels are refused. Frame choreography cannot also own a raw channel.
Text `motion.by` animates tokens inside a clip and is a separate API.

## Evaluation

Tracks evaluate from absolute requested time, including reverse/out-of-order seeks.
Procedural authored data can use fixed seeds; wall clocks and per-frame mutable
callbacks are not animation inputs.

Pose-only tracks interpolate continuously. A shared leaf containing a counter
uses one scene-fps held schedule for every binding, capped at 256 samples.
Stepping a single track does not quantize other tracks, footage or shader `u_time`.

`inspect --at` returns center-time evaluated effects, not proof of effect execution
or all motion-blur samples. Pixel comparisons require matching assets, fonts and
runtime; matching MP4 hashes are not required.

[API](compose.md) · [Motion mappings](motion-language.md)
