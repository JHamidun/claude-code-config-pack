# Batch and QA

One encoder job at a time; Remotion concurrency 2. Explicit `--start`, otherwise dry plan. Two render attempts maximum, bounded timeouts, below-normal Windows priority. STOP checked between stages and while subprocesses run; terminate owned process tree on cancellation. Do not remove STOP automatically. Resume only with matching inputs/config/engine/output hashes and valid output probe.

Batch `jobs: [{id,config}]`: unique IDs/config/workspace/output. Sequential jobs; stop on first failure by default; explicit `--continue-on-error` if wanted. No scheduled daemon, implicit uploads/publishing or unbounded agents.

Before full render: inspect inputs, sync proof, masks and three animation treatments; validate geometry/clock/protected intervals/fonts; type-check → build → tests. Keep original files immutable.

After render, automated checks: dimensions/FPS/frame count/PTS/duration, full decode, audio hash against approved base, source/output fingerprints, contact sheet of every boundary and scene end, SRT timing/width. Input range/matrix converted explicitly to BT709 limited.

Editorial checks: frame0/ending, drawing progress and final state in all scenes, both sides of each cut, duplicated arrows/caption remnants/frozen flashes/bars/face keying, lip consonants at start/middle/end, listening to repaired syllables and joins. Audio hash alone does not prove sync.

`QA.json` leaves `editorial_review: pending`. Only add a separate reviewed record after actual inspection, tied to final SHA256 and exact scope/timestamps. Do not claim continuous playback from contact sheets or full decoding.

Deliver new MP4 + separate SRT + Preview.jpg + manifest + QA; preserve old versions. If blocked, explain the actual failure rather than presenting a cached draft as new.

## Toolkit regression checks

Run `python -B -m unittest discover -s <skill>/scripts/tests -v` for fast contract checks. To include generated-media FFmpeg tests, set `SKETCH_MEDIA_TESTS=1` first. The latter tests known audio-offset recovery, green keying and BT709/frame-count contracts using disposable synthetic media. No original lesson files are needed by the tests.

After changing the TSX engine, fonts, masks or build flags, additionally render a short disposable three-treatment project and inspect boundary frames. A Python unit pass alone cannot certify a Remotion render. Test resume on a second run and confirm `cached`, not just the presence of an old MP4. Optional local ASR is a separate dependency/model and must be explicitly tested if used.
