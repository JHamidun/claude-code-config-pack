# Assembly

`higgsedit` is the native CLI. An edit script is suitable for a new, unshared project; running `higgsedit build edit.jsx` replaces that project's timeline. For linked, human-edited, or canonical projects, read fresh state and use bounded `higgsedit do` or `higgsedit ops` changes instead.

## Picture and audio

`p.cut(handle, { from, dur, at, fit })` places source media on the spine. `from` is source time; `at` is timeline time. Omitted `at` appends cuts in declaration order. Keep `from + dur` within the source duration.

`p.compose(nodes, { at, dur, name, camera })` places native graphics or media overlays. A composed `media` node is picture-only: `muted` and `volume` do not add its source audio. Keep required audio on the spine, extract it separately, or mux/mix after render.

```js
export default async ({ project, text }) => {
  const p = await project({ size: "1080x1920", fps: 30 });
  const source = await p.add("media/source.mp4");
  p.cut(source, { from: 0, dur: 8 });
  p.compose(text("Caption", { fontSize: 64 }), { at: 1, dur: 2 });
  await p.render("renders/final.mp4", { depth: 10, codec: "hevc", bitrate: 8_000_000 });
};
```

An audio clip cannot share a track with visual clips, and `p.cut` exposes no track index. For additional beds, use the `duck` verb where applicable or mix with ffmpeg.

## Native composition

Persistent `<frame>` supports `layout="column"`, `"row"`, `"grid"`, or `"none"`. Grid columns are equal-width; spans and `minmax` are unsupported. Frame children use parent-local `at`/`duration` and must fit the parent's half-open lifetime. Keyframes use node-local time. There are no per-frame callbacks.

Components use `components/*.js` with `meta` and a default `render` export. Component nodes compile at local time zero; only the instance root is placed on the timeline. Components receive node builders, not the live project API, so import assets before placement and pass asset IDs through declared parameters.

Useful commands:

```bash
higgsedit probe media/source.mp4
higgsedit check .
higgsedit build edit.jsx
higgsedit frame . 1.5 --out renders/frame.png
higgsedit render . --out renders/final.mp4
ffprobe -v error -show_entries stream=codec_type renders/final.mp4
```

## Export options

`p.render(out, options)` supports `draft`, `shards`, `concurrency`, `depth: 8|10`,
`codec: hevc|av1`, `bitrate`, `accel: auto|cpu|gpu`, and `lossless`. Default depth 8
encodes H.264; depth 10 selects H.265 (HEVC Main10) or AV1. Lossless AV1 selection
uses FFV1 in MKV/MOV. CLI export also accepts `--range START:END`.
Worker/shard options control parallelism.

`bitrate` is a positive integer in bits/second. CLI `--bitrate 8M`, `--bitrate 8000k`
and `--bitrate 8000000` all target 8 Mbps of video. `higgsedit build edit.jsx
--bitrate 8M` sets a default; an explicit `p.render` bitrate overrides it. Omission
keeps automatic quality settings. The target is not constant bitrate or an exact file size;
audio/container bytes are extra. A bitrate is incompatible with `lossless`.
Older CLIs can silently ignore bitrate; confirm `--bitrate` appears in their help.

Main10 input decodes directly. Render reports include diagnostics and per-window
eight-bit `fallbacks`; output depth alone does not establish retained precision.
Project size/fps are fixed at creation. Cost depends on media, resolution, effects
and concurrency; there is no fixed render-time estimate.
