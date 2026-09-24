# Generation and delivery

This reference contains the complete Phase 4–8b contract. The caller must resolve
the helper-root variables defined by `faceless-video` before following any
cross-skill path below.

## Contents

- Block video generation and review
- Narration through `narrator`
- Native assembly and QC
- Subtitles through `subtitles`
- Intake-selected cover through `thumbnail-generation`
- Confirmed media delivery

### Hands-off concurrency after SCRIPT LOCK

In explicit auto/headless mode, Phase 4 clips and Phase 5 narration are independent once
the script and assets are locked. Precompute both complete waves, submit the video groups
and the narrator's audio groups before the first `jobs_wait` on either, then poll the two
ledgers independently. Never run two attempts for the same index at once.

This does not apply to interactive runs: VIDEO and AUDIO review questions are spending
gates, so an interactive run completes and approves Phase 4 before submitting Phase 5.

### Phase 4 — Generate blocks (one job per block, submitted in batches)
Before the first block, call `models_get({model_id:"minimax_h3"})`.
Require 10-second generation, `resolution:"2K"`, the chosen 16:9/9:16 ratio,
and image references in the returned schema. Stop on a schema mismatch; never
substitute another model or silently lower resolution. Native audio is required
in the resulting clips. Set `generate_audio:true` only if the live model schema
declares that parameter; otherwise omit the undeclared flag and use H3's native
audio path. Check the returned audio, not the presence of a request flag.
Missing audio, or generated speech/music in a narration block, is a named QC
failure: retry that block once, then stop if it remains unusable. Declared Kids
dialogue and song-mode sound rules remain their respective exceptions.

For each block 1..N, create one request for `generate_video_batch`:
`model:"minimax_h3"`, `duration:10`, `resolution:"2K"`,
`aspect_ratio`: chosen aspect, `medias` = location →
characters → props using the canonical tool role `image`. **HARD LIMIT: at most 7 image
references
per call** — retain this packing even though H3 supports more. Send
ONLY the assets that appear in THIS block; if a block still exceeds 7, trim in reverse
priority (extra props first, then the spare coverage view) — NEVER drop the block's
location or an on-screen character. If the response is a preset recommendation
instead of a job → resubmit the same call with `declined_preset_id` from it (rule 5).
The prompt contains the
FIVE timed hard-cut shots (`SHOT 1 0.0–2.0s … HARD CUT … SHOT 2 2.0–4.0s … HARD CUT
… SHOT 5 8.0–10.0s`; Kids: the 4-cut pattern). Ordinary and
`block_kind:"narration"` prompts add "characters only emote, do NOT talk" plus
diegetic-audio-only. A validated Kids `block_kind:"dialogue"` instead quotes the exact
speaker turns, permits only those named mouths to speak, asks for native dialogue audio,
and forbids narration, music, extra voices, and improvised words. Full template →
`${FACELESS_STYLES_DIR}/references/prompts.md §3`. Follow the main skill's BATCH-WAVE
LAW: submit every ready group of at most six using the block number as `index`, then wait
accepted groups with `jobs_wait`. Apply the RETRY
LADDER on `nsfw`/`failed`, resubmitting only failed block indices.
**A `completed` block is FINAL.** Never pause the run to "re-taste" a finished block:
regenerate ONLY on `failed`/`nsfw` (RETRY LADDER) or on a NAMED gate/QC violation (style
drift vs the assets, static head/tail WARN from the assembler, wrong aspect) — and only
AFTER the whole batch is collected. Do not stop mid-batch to redo a block on preference;
do not resubmit blocks the checklist has no complaint about.
After all N blocks are complete, interactive mode calls
`show_generation_by_ids` with the exact final `{index, job_id}` block ledger
(one call for up to 24 blocks; consecutive groups of at most 24 only when
larger), renders the VIDEO review question, and ends the turn; enter the route's
next stage only after `Continue`. Auto/headless mode proceeds immediately
without the list.
**GATE 4 (completeness):** all N blocks are `completed` and downloaded (`block01..N.mp4`),
one per script block, no gaps. Never proceed with a missing block.

### Phase 5 — Voiceover — INVOKE THE `narrator` SKILL (do not hand-roll TTS)
Voice work is NOT done inline. **Invoke the `narrator` skill** and hand it every ordinary
or `block_kind:"narration"` line:

- the N block lines, numbered, in order (you wrote them in Phase 3);
- the LOCKED voice pair from `voice.lock` (written at GATE 0) — `voice_id` +
  `voice_type`, the same pair for the whole video;
- the timing target: **7.8–9.5s of measured speech for every full 10s block**;
- the delivery direction: ONE `{DELIVERY}` phrase for the whole video (channel +
  topic — see `${FACELESS_FLOW_DIR}/references/vo_and_captions.md`), plus optional per-block mood;
- the density target: **20–23 words** per full-block line; Kids use **17–21**
  with an EXCITED delivery cue and carefully bounded performed brackets;
- for a SHORT final block (non-multiple-of-10 duration): that block's own window.

The narrator skill owns the mechanics and guarantees: `text2speech_v2` with
`variant:"elevenlabs"`, one voice everywhere, MP3 tail-click removal before WAV
measurement, speech-length and `rate=ok` gates, rewriting a line denser/shorter when
it misses (NEVER `atempo`, never `speech_rate`), no internal pause ≥0.8s, RETRY SET
LAW, and a per-line attempt budget. The timecode bracket carries delivery direction
but does not pace ElevenLabs; word count is the length control.

It returns completed audio job IDs plus result URLs, measured speech length when
available, and final wording. Keep final wording synchronized with the current
validated `script_manifest.json`.

After every narration wave, materialize and measure all final takes in **one self-contained sandbox call**. The measurement helper needs ffmpeg, not Whisper;
run it even on the declared missing-Whisper route.
Replace the base64 placeholder with the compact current
manifest encoded as base64, list every final completed result URL in numeric block order,
and replace the language placeholder with the run's locked `NARRATION_LANGUAGE`. The
command writes the manifest, downloads and converts every final result into deterministic
`voice01.wav … voiceNN.wav` slots, then immediately verifies them before the ephemeral
sandbox can recycle:

```
sandbox_exec({
  command:"set -e; mkdir -p work/voices; " +
          "printf '%s' '<script-manifest-base64>' | base64 -d > script_manifest.json; " +
          "printf '%s\\n' '<voice01-result-url>' '<voice02-result-url>' > voice_urls.txt; " +
          "i=0; while IFS= read -r url; do i=$((i+1)); idx=$(printf '%02d' \"$i\"); " +
          "curl -fL --retry 3 --retry-all-errors \"$url\" -o \"work/voices/take$idx.mp3\"; " +
          "ffmpeg -hide_banner -loglevel error -i \"work/voices/take$idx.mp3\" -ac 1 -ar 24000 " +
          "-af 'areverse,atrim=start=0.030,asetpts=N/SR/TB,afade=t=in:st=0:d=0.060,areverse' " +
          "-y \"work/voices/voice$idx.wav\"; done < voice_urls.txt; " +
          "python3 ${HF_WORKFLOWS}/faceless-video/scripts/measure_narration_takes.py " +
          "--script script_manifest.json --voice-dir work/voices --duration-seconds {requested_seconds} && " +
          "python3 ${HF_WORKFLOWS}/faceless-video/scripts/verify_takes.py " +
          "--script script_manifest.json --voice-dir work/voices --language '<narration-language-code>'"
})
```

If Phase 0 selected the missing-Whisper degraded route, do not run this intermediate
`verify_takes.py` command and do not claim that the audio-content gate passed. Still
run `measure_narration_takes.py` in the materialization call: missing Whisper never
waives duration/rate checks. Keep the ordered completed URLs and current manifest for
the final self-contained finisher with `--allow-unverified-audio` and its degraded receipt.

The helper maps each exact `vo_line` to `voiceNN.wav`, skips declared Kids dialogue
and scales the speech window for a short final block. Read its JSON `retry_blocks`,
`overlong_blocks` and `recommended_words`; never hand-build a `speech_metrics.sh --text`
loop. A measured overlong block may use the 17-word retry floor: rewrite that line,
then rerun `validate_motion_script.py --script script_manifest.json --duration-seconds {requested_seconds}`
with `--duration-retry-blocks N,...`. Retain the union of measured overlong block
numbers across retries; all other blocks keep their initial word floor.
Pass `--accept-soft-blocks N,...` to measurement only for 7.2–7.8s takes already
retried once. Re-measure every wave, regenerate only the returned retry indices,
and never change successful takes.

All N files are mandatory even when local measurement was unavailable during
generation. On the normal route, after any line is regenerated, replace only that
index's URL and rerun this whole materialize-and-verify command; never run
`verify_takes.py` in a later call that assumes the downloaded files survived.

The command uses tiny local transcription to catch a provider returning another job's
audio or a take that predates a line rewrite. On non-zero exit, regenerate only the
named mismatching narration indices from the current manifest with the locked voice
pair, then rerun the verifier. A passing take stays immutable. A content mismatch is
never accepted as the "closest" take and never reaches assembly; stop after the bounded
per-line attempt budget instead of shipping the wrong words.

For a validated Kids Talking Characters run, do not send dialogue blocks to `narrator`.
Download each completed dialogue clip and extract its full audio as that block's numbered
voice file, normalized to −16 LUFS without changing timing. Keep the same `voiceNN.wav`
slot sequence as the clips, so the assembler receives exactly N clip/voice pairs. Dialogue
audio is already lip-synced and must never be centered, time-stretched, or passed through
`voice_change`.

The narrator MUST use `generate_audio_batch` + `jobs_wait` per its own contract
and must not render progress widgets. If this run requires a music bed, generate
it now through the same headless audio batch contract (before review), not during
assembly. After every take and due bed passes its bounded checks, interactive
mode calls `show_generation_by_ids` with the exact final audio ledger (give a
due bed its own unique stage index), renders the AUDIO review question, and ends
the turn; enter assembly only after `Continue`.
Auto/headless mode proceeds immediately without the list.

**GATE 5:** exactly N numbered voice files, `measure_narration_takes.py` exits zero,
and, whenever `faster_whisper` is
available, `verify_takes.py` exits clean. Every narration block uses the one locked
voice and passes the 7.8–9.5s target (soft 7.2–7.8s only after one retry; hard reject
outside 7.2–9.5s, scaled for a short final block), `rate=ok`, and no
internal pause ≥0.8s. Every dialogue block uses the corresponding clip's full-length
native audio. The only degraded exception is the Phase-0 missing-Whisper route: the
single finisher call must include `--allow-unverified-audio`, its
`AUDIO_CONTENT_UNVERIFIED=faster_whisper` receipt is mandatory, and delivery must state
that take content could not be transcribed for verification.
After at most three attempts per line (changed text before a third attempt), stop
with the exact failing slot and metrics if the hard window or delivery gate still
fails. Never ship the closest failed take.

**Picture Story voice = ONE continuous narration, then Whisper (NOT per-beat takes).**
Invoke `narrator` in its CONTINUOUS mode (it handles the 2048-char chunking and the
lossless join) to get one `narration.wav`, then the frame timeline comes from Whisper
word timestamps per `${FACELESS_MODES_DIR}/references/picture-flow.md` Phase 5 / 5b: segments every
~0.7–1.2s, and at each framing change; no frame
segment >1.5s). Those Whisper timings set every frame's duration in Phase 6.
NOTE (feedback to backend): `validate_picture_story_audio.py` is the OLD per-beat audio
gate (rejects takes >3.0s, expects one take per beat) — it does NOT apply to a single
continuous narration and is NOT run in this model. It needs a rewrite to validate the
frame timeline (sum of frame durations ≈ narration length, max-hold ≤1.5s) — the
assembler's `--audio` mode already asserts exactly that, so the check is covered until
the validator is updated.

### Phase 6 — Assemble in the Higgsfield sandbox → ONE final video

**Canonical ordinary ChatGPT motion-video route:**

1. Keep every completed video and audio job's result URL in block order.
2. Before starting the sandbox assembly, call:
   ```
   media_upload({filename:"final_clean.mp4", content_type:"video/mp4"})
   ```
   Keep the returned `uploads[0].upload_url` and `uploads[0].media_id`. This is
   the sandbox-output route. Never pass `work/output/final.mp4` to
   `media_upload_and_confirm`; that tool accepts only ChatGPT attachments.
   When subtitles are enabled, also reserve
   `media_upload({filename:"final.mp4",content_type:"video/mp4"})` **before this same
   assembly call** and keep its second upload URL/media id. Phase 6 and delegated
   Phase 7 will share one sandbox command.
3. In one `sandbox_exec` background command, write ordered `clips.txt` and
   `voices.txt` URL lists plus `script_manifest.json`, run the preinstalled
   wrapper exactly once, verify the MP4, and PUT it before the ephemeral command
   exits:
   ```
   sandbox_exec({
     background:true,
     command:"set -e; printf '%s\\n' '<clip01 url>' '<clip02 url>' > clips.txt; " +
             "printf '%s\\n' '<voice01 url>' '<voice02 url>' > voices.txt; " +
             "printf '%s' '<script-manifest-base64>' | base64 -d > script_manifest.json; " +
             "python3 ${HF_WORKFLOWS}/faceless-video/scripts/validate_motion_script.py " +
             "--script script_manifest.json --duration-seconds <requested-seconds>; " +
             "bash ${HF_WORKFLOWS}/faceless-video/scripts/finish_video.sh " +
             "--blocks N --clips-file clips.txt --voices-file voices.txt " +
             "<optional --allow-unverified-audio> --script script_manifest.json " +
             "--language '<narration-language-code>' --out work/output/final_clean.mp4; " +
             "test -s work/output/final_clean.mp4; " +
             "code=$(curl -sS -o /dev/null -w '%{http_code}' -X PUT " +
             "--upload-file work/output/final_clean.mp4 '<upload_url>'); " +
             "echo \"PUT -> $code\"; [ \"$code\" = \"200\" ]"
   })
   ```
   `<script-manifest-base64>` is the compact current validated manifest encoded as
   base64; never reference a manifest from an earlier sandbox call. When subtitles
   are enabled, do not let this command exit after the clean PUT: append the delegated
   subtitles skill's font fetch → transcription from the local takes/sidecar → transcript
   gate → burn → mechanical checks → PUT to the already-reserved `final.mp4` URL.
   Require both PUTs to return HTTP 200 in this one command.
   Add `--music URL|FILE` and `--stepped 12` only when applicable. This call always
   creates the clean Phase-6 master; subtitles are a separate Phase-7 operation.
   `--allow-unverified-audio` is allowed only after the Phase-0 import retry failed;
   require the matching `AUDIO_CONTENT_UNVERIFIED=faster_whisper` receipt and disclose
   the degraded verification state with the clean deliverable. When the import succeeds,
   omit the flag and keep take verification fatal.
   Poll its returned `log_path` immediately through `sandbox_exec`. Do not stop
   until the process is terminal and the log contains `PUT -> 200`.
4. The wrapper downloads `block01.mp4 … blockNN.mp4` and
   `voice01.wav … voiceNN.wav`, writes `pairs.txt` in strict numeric order, runs
   the canonical assembler, verifies every output, and the
   same command uploads the final MP4.
5. Only after the clean `PUT -> 200`, call:
   ```
   media_confirm({type:"video", media_id:"<media_id>"})
   ```
   Preserve its confirmed hosted URL. When captions are off, this is the final
   deliverable. When captions are on, also require the captioned PUT's HTTP 200 and
   confirm the already-reserved `final.mp4` media id once; that second confirmed URL is
   the user-facing result. Preserve the generated
   `final_clean_poster.jpg` and `final_clean.mp4.assembly.json` as assembly receipts. If the
   PUT fails, do not confirm: create a fresh upload slot and rerun the same
   idempotent finish-and-PUT command.

Do not call `explainer_video` for ordinary stitching, even when it appears in a tool
registry: sandbox FFmpeg assembly is self-contained and does not need a remote
generation record. Do not call `job_display` for a sandbox file or uploaded-media id.
The confirmed hosted MP4 is the deliverable.

**Canonical motion / Picture Story scripts under the wrapper:** run
`bash ${HF_WORKFLOWS}/faceless-video/scripts/assemble_final.sh` once
for motion blocks or
`bash ${HF_WORKFLOWS}/faceless-video/scripts/assemble_slides.sh` once
for Picture Story. Every motion run
writes a MANIFEST first (one
`blockNN.mp4 voiceNN.wav` pair per line, in order) and passes the expected block
count — `--blocks N` is REQUIRED (the script refuses to start without it) and a
missing, extra, or number-mismatched pair is a hard fail:
```
sandbox_exec({
  background:true,
  command:"bash ${HF_WORKFLOWS}/faceless-video/scripts/assemble_final.sh --out work/output/final_clean.mp4 --blocks N --manifest pairs.txt --script script_manifest.json"
})
```
Add `--music bed.mp3` and `--stepped 12` only when applicable.
(**pass `--stepped 12` for Fairy Tale & Myth / any Cinematic Storybook run — the
on-twos cadence**; positional pairs remain for ad-hoc debugging only. Subtitles are
NOT part of assembly any more — Phase 7 invokes the `subtitles` skill on the
assembled file.)
**NO chunked assembly** — never split a long run into "chunks of 10" with your own
ffmpeg, never build the audio track separately, never re-mux by hand: one script call
does all N blocks, however many there are. **NO invented progress reports:** the only
legitimate assembly status is the script's own stderr (per-block lines + asserts) —
paste it; fabricating "chunk 6 assembling, ~7 minutes remaining" tables while nothing
runs is lying to the user and grounds for a failed run.
Run the assembler with `background:true`, then poll its returned log immediately
with the next `sandbox_exec` call. If it is demonstrably alive, keep polling that
process; never launch a duplicate assembly.
The script does everything and guarantees the hard parts: fixed **N×10s** length, each
voice CENTERED in its 10s block, NO atempo, NO leading freeze, ONE output file, + optional
low music bed and `loudnorm -16 LUFS`. Diegetic SFX already live in the clips. Music bed
when the user supplied a file or explicitly asked — PLUS any KIDS-LOOK run (the Kids
channel, or ANY channel in a Kids-catalog style) AND every FAIRY TALE & MYTH /
Cinematic Storybook run, where a wordless bed is ON BY DEFAULT. No file needed: a due
bed was GENERATED before the AUDIO review with `sonilo_music` at the VIDEO's exact
duration (one request covers
up to 600s — verified; longer runs join ≤600s parts into one file — mechanism in
`${FACELESS_STYLES_DIR}/references/kids-styles.md §Kids music bed`). **Mood by channel: Kids = playful/bouncy;
Fairy Tale & Myth = MYSTERIOUS-CALM dark-enchanted ambient** (never bouncy —
`${FACELESS_STYLES_DIR}/references/style-cinematic-storybook.md §Music`). user file → generated bed →
generation failed = ship without + say so in one line. The generic audio router accepts
`sonilo_music` even though its default description focuses on speech; never substitute
`seed_audio` for music. **Default-bed level: `--music-vol
0.05` for Kids, `0.09` for Fairy Tale & Myth** (the narration must never fight the bed)
— and the assembler additionally DUCKS the bed under speech (sidechain keyed by the voice). Never block delivery on a bed, never
synthesize music with the speech model. Do NOT split into parts, do NOT re-encode by
hand, do NOT trim to the audio.
Besides the MP4 the script writes two platform artifacts next to it — keep both:
`final_clean_poster.jpg` (the result thumbnail) and `final_clean.mp4.assembly.json` (the machine-
readable ASSEMBLY SIDECAR: block count, per-block speech metrics, gates passed — the
proof the final went through the script; `assemble_slides.sh` writes the same pair).
**GATE 6:** exactly ONE `final_clean.mp4`, duration = N×10s (±1s, the script asserts this),
narration present in EVERY window (the script asserts this too — a "silent second half"
cannot pass), plays from frame 1 (no static head), one voice, SFX under the voice (music
only if provided), poster + assembly sidecar present next to the MP4.

**Picture Story assembly command** (frame-by-frame `--audio` mode; `--blocks` = the
FRAME count, not the billing count):
```
bash ${HF_WORKFLOWS}/faceless-video/scripts/assemble_slides.sh \
  --out work/output/final_clean.mp4 --audio work/voices/narration.wav \
  --blocks {FRAME_COUNT} --timeline scene_manifest.bound.json --frames-dir work/frames \
  --requested-seconds {REQUESTED_SECONDS}
```
This is a fragment inside the same self-contained Phase-6/7 command, not a separate
`sandbox_exec`. Before it, materialize the current base64-encoded script manifest and
rerun `validate_picture_story.py`, write the unbound `scene_manifest.json`, bind the
completed indexed results to `scene_manifest.bound.json`, materialize every frame from
that bound manifest's durable result URLs, and download the final continuous narration
URL. When subtitles are enabled, append the delegated subtitle pipeline immediately
after `assemble_slides.sh` succeeds, transcribing `work/voices/narration.wav`; then PUT
both the clean and captioned MP4s to the slots reserved before this command exits.
Add `--music bed.mp3` only when applicable.
`scene_manifest.json` is the unbound manifest v2 produced from Whisper words by
`build_scene_timeline.py`. `scene_manifest.bound.json` is the only assembly input: it is
bound to actual OpenAI indexed job results by `bind_scene_frame_results.py` and atomically
restored into `work/frames` by `materialize_scene_frames.py`. Never invent durations or
rename by completion order.
The one continuous narration is laid over the whole cut. The script asserts the
per-frame durations sum to the narration length (±1.5s), **frame numbers strictly
ascending with no gaps (a jumble hard-fails — the "assembled out of order" bug)**,
max-hold ≤1.5s/frame, **a DENSITY FLOOR
of `ceil(narration_sec/1.5)` frames (≈40 for a minute — a slideshow like 15 frames/min
hard-fails; generate the dense set in Phase 4, do not pad holds)**, aspect, 1080p cap,
narration present, full decode. Block accounting stays `ceil(requested_seconds/10)`
(NOT the frame count) — the sidecar records both `frames` and the billing blocks.
NOTE (feedback to backend): the old `--target-duration` per-beat total-duration gate is
replaced by the `--audio` sum-of-durations assert.

### Phase 7 — Subtitles — verify the `subtitles` result (only if subtitles = yes)
Captions are never hand-timed. After native Phase-6 assembly, invoke `subtitles` with:

- the assembled video (the Phase-6 `final_clean.mp4`);
- `script_manifest.json` (or the line list) as the AUTHORED WORDING — Whisper is the
  word clock, the words come from the script, so names/numbers are spelled right;
- the LOOK: `clean` (default — slim white CAPS, tiny, bottom ~12%, no plate),
  `paper` (torn cream label, handwritten — fits fairytale/storybook looks) or
  `bold` (UGC ALL-CAPS with safe zones). Channel default: Fairy Tale & Myth →
  `paper`, everything else → `clean`, unless the user asked otherwise.

The skill owns: backend/Whisper word timestamps, the ≤5 words / ≤32 chars caption sizing,
authored-wording substitution, the three burners, per-language font coverage (it
auto-swaps a font that has no glyphs for the script instead of shipping blank
labels), the dependency install, and the "unavailable Whisper → deliver unsubbed and
say so" fallback. In this delegated route the faceless parent remains the sole
delivery owner: the skill writes `work/output/final.mp4` plus the verification sidecar
`work/output/final.srt` into the parent's producing sandbox command and does not
allocate or confirm another upload slot. The current backend does not host `.srt`
files, so only the captioned MP4 becomes a confirmed deliverable.

The faceless parent reserved the `final.mp4` upload slot immediately before the shared
Phase-6/7 `sandbox_exec`. Pass that `upload_url` + `media_id` to the delegated subtitle
fragment. In the same command that still owns `final_clean.mp4`, its sidecar, the voice
takes (or continuous `narration.wav`) and `script_manifest.json`, transcribe, gate, burn, verify, and PUT
`work/output/final.mp4`; require HTTP 200 before exit. Only then does the faceless parent
call `media_confirm` once for that media id. Only this confirmed captioned URL is
delivered. Never start Phase 7 in a later sandbox call, allocate a second caption slot,
or overwrite/re-burn the Phase-6 clean upload.

If Whisper remains unavailable after the one allowed preflight retry, mark captions
unavailable before generation and treat subtitles as off: reserve and confirm only the
clean output. If the delegated caption pipeline fails inside an already-started shared
Phase-6/7 command specifically because Whisper is unavailable, copy
`work/output/final_clean.mp4` to `work/output/final.mp4`, probe it, PUT that copy to the
already-reserved final slot, confirm it, and state that captions were unavailable. Never
leave the reserved final slot empty or claim that the clean copy contains captions.
Implement this as an explicit shell branch inside the shared command:

```
if python3 -c 'import faster_whisper' >/dev/null 2>&1; then
  # delegated transcript gate, burner and final MP4 PUT; any failure remains fatal
  : <caption-fragment-and-final-put>
else
  rm -f work/output/final.srt work/output/final.mp4
  cp work/output/final_clean.mp4 work/output/final.mp4
  ffprobe -v error work/output/final.mp4 >/dev/null
  curl -f -X PUT --upload-file work/output/final.mp4 '<reserved-final-upload-url>'
  echo 'CAPTIONS_UNAVAILABLE=faster_whisper'
fi
```

Do not put an unguarded caption command after `set -e`: only the failed import selects
the clean-copy branch; transcript, alignment, burn, probe, or PUT errors still stop.

For this workflow the subtitle skill runs only through `sandbox_exec`, using
`${HF_WORKFLOWS}/subtitles/scripts/`. It reads the immutable
Phase-6 clean video and writes a distinct captioned deliverable in Phase 7. Never pass
`--subs` to either assembler and never use a previously captioned video as burn input.

**Non-negotiables that stay TRUE regardless of who asks:** timings come from
Whisper ONLY — even if the user says "time them from the script" (rule 8); captions
stay small and out of the way (rule 20); styling asks map to the skill's flags, and
anything that breaks readability is declined in one line.

Keep `final_clean_poster.jpg` extracted from the CLEAN video (Phase 6 does this before
captions) — a result card must never show a random subtitle fragment.

**GATE 7:** one `final.mp4` with backend/Whisper-timed captions from the `subtitles`
skill, or an explicit note that captions were unavailable.

> **Whisper normally serves both narrated-motion take verification (Gate 5) and
> subtitles (Phase 7).** A/V sync is by construction (one centered narration line per
> block — Phase 5/6). If Whisper remains unavailable after the one retry, the explicit
> `--allow-unverified-audio` route may deliver the clean cut without captions, but it must
> report and disclose that take content was not transcribed. Never ship guessed caption
> timings or claim the content gate passed.

### Phase 8 — Native resolution, no automatic upscale

Deliver the native 2K motion cut. Do not run or offer a 1080p downscale. This OpenAI
profile has no `upscale_video` tool, so do not invent an upscale call; a requested
4K upscale requires a separately available, authorized capability. Picture Story
keeps its existing 1080p-class output and never calls H3.

### Phase 8b — Generate the thumbnail only when the cover answer was yes

Run only when the locked intake answer is `thumbnail: yes`. Hands-off runs resolve an
unanswered thumbnail round to the documented `yes` default. A request for exactly one MP4
or one finished video constrains the video-file count only; it is not a thumbnail decline.
Only an explicit “no thumbnail” / “no cover” locks `thumbnail: no`. The cover is an
additional still-image deliverable; failure never blocks or delays the validated video.

Invoke the installed `thumbnail-generation` skill with a complete locked handoff assembled
only from this run:

- **Reference image:** the Phase-1 style key and explicit `Match this reference` intent. It is
  analyzed for style and does not enter thumbnail generation `medias`.
- **Hook title:** for a pasted script, use the exact title locked at intake. For idea and
  research paths, derive one exact 3–6 word promise in the video's language and channel
  register from the current script manifest. Request `bake during generation:provider-first`.
- **Scene:** one sentence carrying the episode hook and topic, not the full script.
- **Identity:** up to three recurring character images from the current asset roster. If there
  are none, lock a people-free concept. Never invent a photoreal person.
- **Aspect:** `16:9` even when the video is vertical.
- **Medium:** the exact locked illustrated medium, materials, and palette from this run.
- **Variant count:** one. Do not reopen match mode, character choice, text mode, or count.

The first provider render must contain the exact hook. Validate it character-for-character.
On a mismatch, the thumbnail skill creates one clean no-text recovery render and uses its
preinstalled deterministic canvas overlay. Accept only a provider-baked hosted image that
passes the exact-text gate or a confirmed overlay PNG. Retry the handoff once when a required
field was omitted or stale.

If thumbnail generation still fails, create a durable clean-poster fallback from this run's
confirmed clean-video URL: reserve `fallback-thumbnail.jpg` with `media_upload`, then in one
`sandbox_exec` download the clean MP4, extract a frame near one second with ffmpeg, verify the
JPEG, and PUT it to the reserved upload URL. Call `media_confirm({type:"image",media_id})`
only after HTTP 200. Record `thumbnail_source:"generated"` or
`thumbnail_source:"poster_frame"`, plus `thumbnail_render:"provider_baked"` or
`"deterministic_overlay"` when generated, and the confirmed `thumbnail_url`.

**GATE 8b:** when the locked cover answer was yes, one confirmed cover URL exists and every value came
from this run's script manifest, style key, and asset roster rather than memory of another run.

The plugin's terminal actions are the final video `media_confirm` from Phase 6 or 7 and, when
selected, the Phase-8b confirmed cover. Deliver the hosted video and selected thumbnail URL together.
It has no platform reporting callback and must never invent one. Keep the script, asset,
assembly, subtitle, and thumbnail receipts in the sandbox for the rest of the session; they are
diagnostic evidence, not an additional delivery API.
