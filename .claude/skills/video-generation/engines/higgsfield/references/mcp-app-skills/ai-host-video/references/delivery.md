# Render, inspect and deliver

## Host cut and final render

Build the measured original-source host spine and produce a playable host-cut preview
using [assembly](assembly.md). Reserve outputs first, then restore/download, build,
render, probe and PUT within one sandbox command. Confirm uploads and continue with
motion in the same authoring project. The preview is not a source asset and its
handoff is not a new approval gate.

Use a draft render only when it helps iteration; draft pixels cannot settle final
compression, thin text or banding. Render the coherent final edit at full quality to
a pending filename. Preserve the previous master until the new file passes checks.
If music is mixed with FFmpeg, the mixed file is the pending final master.

Probe the actual file using installed `ffprobe`:

```bash
ffprobe -v error -show_entries format=duration:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,duration -of json renders/final-pending.mp4
```

Check nonempty decodable video, expected dimensions/aspect ratio, required audio,
actual pixel format/bit depth (add `pix_fmt,bits_per_raw_sample` to stream entries),
nominal 24 fps and measured master duration. Allow normal container rounding rather
than retiming speech for a tiny discrepancy. Investigate a meaningful duration or
frame-count mismatch. A probe is a technical check, not a creative or speech review.
After successful production and PUT, confirm the exact current master and retain its
URL with the source/edit revision. Rendering a different file invalidates that link
as evidence for the new version.

## Inspect the actual encoded master

Derive review timestamps from measured anchors, compose lifetimes, internal cuts and
job seams. Extract opening, settled, changed and ending states for every treatment,
plus frames immediately around picture boundaries. For example, substituting a
measured timestamp and using distinct filenames:

```bash
ffmpeg -v error -i renders/final-pending.mp4 -ss 1.25 -frames:v 1 review/state.png
ffmpeg -v error -ss 1 -i renders/final-pending.mp4 -t 2 -c:v libx264 -c:a aac review/boundary.mp4
```

Use the actual frame grid around the event and clamp ranges to the master. Publish
needed frames/excerpts and checkpoint in the producing command so the host can
inspect them after sandbox expiry. A project `frame` or `sheet` preview helps layout
but is not evidence of encoded-master continuity. No automatic proof sheets, blank
scan, static scan, cache or review receipts are supplied by this skill.

Inspect full-resolution frames for glyphs, wrapping, crop, host collisions, scrims and
layer order. Use normal-speed audiovisual playback when the host exposes it for:

- complete speech in order, stable identity and actual camera changes;
- required information states, readable holds and word-aligned emphasis;
- a continuously moving host where expected, including live windows and exits;
- no unintended flashes, gaps, frozen layers or broken transitions;
- intelligible voice at the hook, dense speech, PLAYBACK boundaries and ending;
- music joins without clicks, masking, recurring silence or distracting restarts.

Apply [creative review](creative-review.md) yourself against the episode artifacts.
The existing asynchronous video-analysis tools can provide a scene summary using
only their documented input id/URL. They do not accept a creative prompt or script
and do not guarantee frame-level timing, lip-sync, freezes or audio-mix review.
If direct playback or another inspection modality is unavailable, state what was
actually checked and what remains unverified. Do not equate no returned findings
with a clean master, or claim an independent full-length review happened.

Repair concrete findings together and inspect the changed output and neighboring
seams. Use a full review for global impact; do not repeatedly review unaffected
ranges. Preserve originals and use [operations](operations.md#one-retry-policy) for
any generation replacement. A user may accept the exact current master with a
clearly disclosed limitation; no waiver form or prescribed review file is required.

## Handoff

Reuse the thumbnail job started during generation. Take one `jobs_wait` snapshot
with `timeout_seconds: 0`; if completed, inspect identity, exact headline and small-size
readability per `thumbnail-generation` before including it. Show its separate completed
generation set once as required by the tool protocol. Do not wait for a pending cover,
resubmit it, block delivery on a retry or promise an unscheduled automatic follow-up.
Disclose a pending, failed or rejected cover and retain the id for a requested later
check. If an older run has no job, submit one with resolved inputs without delaying
the video handoff. A declined thumbnail requires no work.

Deliver the actual confirmed master URL. Package originals, fonts, authoring source,
built project, selected receipts and measurements using the standard ZIP/checkpoint
procedure in [OpenAI runtime](../SKILL.md#openai-runtime-contract). Include the music source and exact
mix recipe when the final bed was mixed outside the native timeline. Confirm that ZIP
and describe it as an editable project archive. No hosted editor publishing service
exists in this profile. Report a missing cover/archive or unverified review scope
plainly alongside the delivered result.
