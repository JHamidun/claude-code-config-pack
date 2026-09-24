# On-screen narrator — video + photo in, narrated video out

Use this mode only when the request supplies an existing video and asks to place the
person from a photo on-screen as its narrator. The photo must depict the user or another
consenting non-public person. This is a video workflow: never substitute audio-only Mode
A, a static image overlay, generic dubbing, or a hand-written chroma-key command.

## Locked contract

- Preserve the base video's picture and cover its full duration by default.
- One 10-second generation = one presenter line. Use `ceil(base_duration / 10)` blocks;
  fewer blocks require an explicit test-range request. When the final base window is shorter
  than 10 seconds, generate and revoice the normal 10-second talking clip, then trim that
  talking clip to the measured final-window duration before compositing it.
- Supplied script text is authored text. Split it only at sentence boundaries and keep every
  word in order. Budget roughly 3.1–3.5 words per second: 31–35 words for each full block
  and proportionally fewer for a partial final window. If its length cannot fit that grid,
  report both counts and ask whether the base duration or covered range should change.
- Without supplied text, transcribe the base video in `sandbox_exec` with preinstalled
  `faster_whisper`; use `video_analysis_create` / `video_analysis_status` only when scene
  structure is also needed.
- Lock one `voice_id` + `voice_type` pair for every block. If absent, call `list_voices` as
  the only tool in that turn and resume from its selected pair.
- `voice_change` is mandatory after talking-clip generation: it preserves the clip timing
  while replacing timbre. Never add a lipsync pass.

## Pipeline

1. **Resolve inputs.** For ChatGPT attachments, call `media_upload_and_confirm` once for the
   video and once for the photo. Keep their confirmed media ids and hosted URLs. When the
   request instead supplies a confirmed media UUID without its URL, call `show_medias` once
   for that UUID's declared type and exact-match the returned `items[].id`; use only the
   matching item's URL. Resolve the video and image separately when both URLs are absent.
   If an exact UUID is not in the returned page, ask for that file to be attached again;
   never guess from recency or use another item. Probe the video duration in `sandbox_exec`.
   Survey its audio: a mono mix means original speech and
   music cannot be separated safely, so disclose that the original audio will be dropped.
2. **Make one green-screen identity reference.** Submit one `generate_image_batch` item with
   stable index `0`, model `gpt_image_2`, `aspect_ratio:"9:16"`, `resolution:"1k"`,
   `quality:"medium"`, and the photo media id as role `image`. Wait with `jobs_wait`
   (`timeout_seconds:15`). On two failures or `nsfw`, retry the same prompt and index on
   `nano_banana_pro`.

   Prompt, verbatim except for pronouns:

   ```text
   Edit this photo. Keep the PERSON identical — same face, hairstyle, clothing, skin tone,
   pose and framing, copied faithfully, not beautified and not a lookalike. Change one thing
   only: replace the background with a perfectly uniform flat chroma-key green screen
   (#00B140), evenly lit, no gradient, shadow or vignette, filling everything behind the
   person. No green spill on the person; preserve clean hair edges.
   ```

3. **Generate every talking block.** Submit `generate_video_batch` groups of at most six,
   using the block number as the stable index. Each item uses `gemini_omni`,
   `aspect_ratio:"9:16"`, `duration:10`, `resolution:"720p"`, and the completed green-screen
   image job id as role `image` (the server normalizes it to the backend's
   `image_references`). Wait in groups of at most eight. Preserve completed indices and retry
   only failed ones, at most twice.

   Prompt template:

   ```text
   IDENTITY REFERENCE (appearance only, not a start frame): copy the attached person and
   solid green background faithfully. The first frame already catches them mid-speech, never
   frozen. They look into the front camera and say in <DELIVERY>, in <LANGUAGE>:
   "<BLOCK LINE VERBATIM, 31–35 WORDS FOR A FULL BLOCK>". Say every word exactly once at a
   brisk steady pace, then hold a calm engaged look. For a partial final window, size the line
   to that window even though the provider clip is 10 seconds. Camera locked; small natural head and
   shoulder gestures only. Audio is only the clear voice. Keep the background uniformly vivid
   green. No repeated or improvised words, captions, watermark, camera motion, beautification,
   background change, or frozen opening.
   ```

4. **Revoice every completed clip.** Call `voice_change` once per block with
   `params:{video_id:"<talking-job-id>",voice_id:"<locked-id>",voice_type:"<locked-type>"}`.
   Wait for every returned job through `jobs_wait`; each must remain the block's duration and
   contain audio. Never accept a missing block.
5. **Composite and export in one durable sandbox operation.** Before the producing command,
   reserve `presenter.mp4` with `media_upload` and a PNG contact-sheet slot for visual QC. In
   the same `sandbox_exec` command:
   - download the base-video URL and every final revoiced result URL;
   - cut the base into ordered windows of at most 10 seconds as `blkNN.mp4`; measure the last
     window exactly and, when it is partial, trim both audio and video of `talkNN.mp4` to that
     duration before compositing (do not pad, loop, or leave the generated 10-second tail);
   - run the preinstalled script once per block, never a custom key:
     ```bash
     "$HF_WORKFLOWS/narrator/scripts/presenter_composite.sh" \
       blkNN.mp4 talkNN.mp4 outNN.mp4 --style cutout --pos br
     ```
   - require each `outNN.mp4.qc.json` to contain `result:"PASS"`; concatenate the ordered
   outputs, probe audio/video/duration, require the joined result to match the measured base
   duration within 0.1 seconds, create one representative-frame contact sheet, and PUT
     both artifacts to their reserved upload URLs before the command exits.
   - use `badge` instead of `cutout` when fine hair has a ragged/green edge or a close-up crop
     reads badly. Never tune chroma thresholds by hand.
6. Call `media_confirm` only after both PUTs return HTTP 200. Inspect the confirmed contact
   sheet: the presenter is opaque, fully inside the frame, clean-edged, and never covers the
   important base-video content. A QC failure regenerates/recomposites only the affected block.

## Delivery gate

Deliver only the confirmed hosted MP4. Report the locked voice, block count, covered duration,
presenter position/style, and whether original audio was dropped. When supplied lines were used,
verify every sentence survived in order with nothing invented. Offer burned captions separately;
do not add them silently.
