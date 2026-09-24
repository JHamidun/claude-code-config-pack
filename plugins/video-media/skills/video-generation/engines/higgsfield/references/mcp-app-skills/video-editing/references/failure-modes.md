# Limits and diagnostics

| Symptom / refusal                 | Contract                                                                                       |
| --------------------------------- | ---------------------------------------------------------------------------------------------- |
| Frame or motion field unknown     | Installed CLI/types determine support; source changes do not update an installed bundle        |
| Fill under hug / unresolved slot  | Fill needs a resolvable parent axis; absolute frames need dimensions                           |
| Child or keys exceed lifetime     | Local spans must fit the owner; frames exclude their exact endpoint                            |
| `animate` object rejected         | `animate` is an array; frame `motion` is an object                                             |
| Duplicate property tracks         | Replacement channels have one owner; raw offsets add and uniform scales multiply               |
| Incorrect shader animation target | `effectIndex` selects a declared effect; `effectParam` is its existing numeric key             |
| Missing shader / texture / GL     | Rendering fails; texture binding uses imported `handle.id`, not URL or handle object           |
| Shader raster overflow            | Raster bounds exclude overflowing child/stroke/ink; clip or inset the content                  |
| LUT / shader adjustment / HTML    | Unsupported by the native CLI                                                                  |
| Text `fill` / rect stroke object  | Text uses `color`; rect uses flat `strokeColor`/`strokeWidth`; path has `stroke` object        |
| Missing glyphs                    | Font registration does not establish glyph coverage; Lucide paths have no font dependency      |
| Stretched footage                 | `fill` stretches; frame-slot `contain`/`cover` preserve aspect                                 |
| Unexpected source moment          | `from`/`trimStart` are source time, not placement time                                         |
| Lost human edits                  | Whole-script build replaces timeline; fresh `inspect` + bounded `do`/`ops` preserve other work |

## Evidence provided by each command

- `doctor`: installed native dependencies and render smoke.
- `compose` with `dryRun: true`: validation and compiled layout, without mutation.
- `inspect --at`: evaluated parameters and lifetimes, not shader execution/world geometry.
- `frame` / `render`: actual pixels and runtime diagnostics. `sheet` samples frames.
- `probe` / ffprobe: actual media streams; extensions do not establish codecs/depth.

Ten-bit encoding does not guarantee ten-bit processing. Render `fallbacks` report
windows that used the eight-bit compositor; GLSL itself is RGBA8. Shader GL selection
is independent of video encoder `accel`. Native and browser shader support differ.

Main10 sources decode directly through ffmpeg without a compatibility transcode.
Frame equality requires matching assets/fonts/runtime. MP4 metadata and encoders
can change container hashes. An interrupted render or a successful script with no
render call is not a completed movie.

[API](compose.md) · [Inspection](editor-measured.md)
