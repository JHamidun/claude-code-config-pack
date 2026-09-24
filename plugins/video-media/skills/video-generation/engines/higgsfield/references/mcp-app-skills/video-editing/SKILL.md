---
name: video-editing
description: |
  Edit footage and motion graphics with Higgsedit.
  Activate only for a requested edit or graphics deliverable:
  cuts, soundtrack changes, overlays and animated title cards.
  Do not activate when the user only asks to analyze, summarize, describe,
  critique or review a video, including scene-by-scene breakdowns.
  Timeline inspection is supporting work for a requested edit, not a standalone
  activation trigger. Exclude standalone still cards, image-to-video photo
  animation without native composition, generative restyling,
  transcription and subtitle text work. For speech-caption burning, use subtitles.
  Object replacements or targeted clip variants use ad-multiplier.
---

# Video editing

Higgsedit runs natively in Node. A project contains `project.json`, imported
`media/`, and `renders/`. The installed `higgsedit --help` and `types/fable.d.ts`
define available commands and authoring fields.

## OpenAI runtime

`sandbox_exec` reuses a per-user sandbox within its limited lifetime. Keep inputs
recoverable and export results before expiry; use `background:true` and poll its
returned status for long renders. A local path is not a durable deliverable. `media_upload` reserves
an output; `media_confirm` confirms it after a successful PUT. ChatGPT attachment
ingress uses `media_upload_and_confirm`, not a sandbox-local path.

These APIs require the matching native CLI; older sandbox builds may lack them.
A local development installation does not update the hosted sandbox. Bitrate needs
`--bitrate` in the installed CLI help; older builds can silently ignore it.

## Capabilities

| Area     | Features                                                                                 |
| -------- | ---------------------------------------------------------------------------------------- |
| Media    | Import images/video/audio; source trims, cuts, fitting and audio mixing                  |
| Layout   | Persistent frames: column, row, equal-column grid, absolute; fill/hug sizing             |
| Graphics | Text, shaped fonts, rectangles, gradients, paths, Lucide icons, masks and mattes         |
| Motion   | Raw keyframes, frame choreography, shared counters, token text, transitions, 2.5D camera |
| Effects  | Standard filters, shadows, motion blur, custom GLSL, image textures, animated uniforms   |
| Output   | Native PNGs, contact sheets, MP4/MOV/MKV, H.264, H.265/HEVC Main10, AV1, target bitrate, editable projects     |

## Script API

Scripts accept JSX/TSX or supplied node builders; no React or DOM runtime.

| Call                                                                     | Result                      |
| ------------------------------------------------------------------------ | --------------------------- |
| `await project({dir, size, fps, background})`                            | Create/open project         |
| `await p.add(file)`                                                      | Import asset; return handle |
| `p.cut(handle, {from, dur, at, fit})`                                    | Place footage/audio         |
| `p.compose(nodes, {at, dur, name, camera})`                              | Place native graphics/media |
| `p.duration()` / `await p.read()`                                        | Timeline length / document  |
| `await p.frame(time, out)`                                               | PNG                         |
| `await p.render(out, {draft, depth, codec, bitrate, accel, shards, concurrency})` | Encoded movie               |

`from` is source seconds; composition `at` is timeline seconds. Frame children
and animations use local seconds. `cut` and `compose` record work synchronously.

See the [complete example](references/compose.md#complete-example).

## Commands

```bash
higgsedit build edit.jsx
higgsedit inspect PROJECT --id CLIP_ID --at 1.2
higgsedit frame PROJECT 1.2 --out renders/frame.png
higgsedit sheet PROJECT --times 0.1,1,1.8
higgsedit render PROJECT --depth 10 --codec hevc --bitrate 8M --out renders/master.mp4
higgsedit do PROJECT VERB --help
```

`inspect --at` requires an ID or unambiguous name. It reports evaluated parameters,
not execution proof. `doctor` checks native dependencies; `check` validates supported
inputs. `fonts list`, `fonts add` and `icons QUERY` expose asset catalogs.

## Boundaries

- Whole-script builds replace the timeline. Existing human/shared edits use fresh
  inspection and bounded `do`/`ops`; canonical connections require host credentials.
- Native HEVC Main10 import needs no compatibility transcode. Ten-bit output may
  contain reported eight-bit compositor fallbacks; GLSL pixels are RGBA8.
- No HTML capture, runtime animation callbacks, native LUT, or shader adjustments.
  Browser shader previews are not universally equivalent to native output.
- The OpenAI tool surface supplies no editable-project publishing service.
  An editable local project is not a hosted editor URL.

## References

- API: [composition](references/compose.md), [geometry](references/clip-geometry.md),
  [timing](references/animation-contract.md), [motion](references/motion-language.md).
- Text: [captions](references/caption-titling.md), [caption layers](references/caption-systems.md),
  [titles](references/title-animation.md).
- Projects: [assembly](references/assembly.md), [patch/sync](references/workflows.md),
  [inspection](references/editor-measured.md), [asset identity](references/provenance.md).
- Reference: [composition patterns](references/shot-blueprints.md), [limits](references/failure-modes.md).
