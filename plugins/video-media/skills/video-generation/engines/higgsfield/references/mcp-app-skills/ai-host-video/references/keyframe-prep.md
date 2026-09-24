# Host reference contract

The canonical provider reference is either an image keyframe or a video avatar:

- `image_keyframe` — the existing path. One accepted image carries identity and
  location into every host generation as `image`.
- `video_avatar` — an accepted host clip carries identity, location, performance, and
  its voice when audio is present into subsequent host generations as
  `video`.

When the user already supplied a video avatar, select `video_avatar` immediately. Do
not ask whether they have an image or offer casting. A video avatar created from a real
photograph by [ai-avatar-creating.md](ai-avatar-creating.md) enters through the same
mode after its bootstrap hook is accepted.

## Image keyframe

Use one accepted image that clearly shows the intended host in the intended studio. It
may be user-supplied or returned by
[ai-avatar-creating.md](ai-avatar-creating.md) after the user selects it. For a
user-supplied image, check that the eyes, nose, and mouth are readable and that
wardrobe, lighting, and set are useful identity context. A generated avatar selected
by the user is accepted as-is; do not run host image inspection or reject their choice.

If a supplied image is unusable as a keyframe but its eyes, nose, and mouth are still
readable, offer creating a video avatar from that photograph as well as attaching a
better keyframe or explicitly casting a host. Wait for the user's choice unless the
parent workflow records continuous autonomous mode. If any of those identity features
is hidden, blurred, or too small to resolve, ask for a better photograph or offer
casting; video bootstrapping cannot recover missing identity detail. Never substitute
an unrelated photo or an unchecked generated host.

Copy the accepted source into `reference/` without creative alteration. For a generated
source, download its completed URL into `reference/` while preserving the original
bytes and image format; do not regenerate or transcode it. Write
`reference/manifest.json` with `"reference_mode": "image_keyframe"`, that exact
run-local path, and the shared camera map. Reuse a compatible existing upload/job id;
only upload the exact file if one is needed. Save the actual receipt and selected id.

## Video avatar

Use the complete accepted clip as the canonical provider reference. Do not extract one
frame and substitute it as `image`; a still from the clip is inspection
material only.

For a user-supplied video, confirm that it is playable and that representative
full-resolution frames show one stable intended host with a sharp, unobstructed face.
Inspect whether its location, wardrobe, lighting, and motion are suitable continuity
sources. Do not reject a usable video because one frame has an open mouth, a gesture,
or a hand position that would fail the image-keyframe rules; the clip carries a range
of performance rather than one frozen ceiling. Record whether its audio contains a
usable host voice.

Copy or download the exact accepted video to `reference/avatar.mp4` without creative
alteration. Reuse the supplied media id when the attachment already has one. Otherwise
upload the exact clip once with the runtime upload sequence and save the response as
`reference/video-upload-receipt.json`. Never upload it again on resume.

Extract one sharp, representative full-resolution frame to
`reference/inspection-frame.png` for visual analysis and camera-map authorship. Prefer
a moment with the face toward camera and no motion blur. Publish this frame if host inspection needs a confirmed URL, but never attach its
inspection upload id to a host generation or treat it as the canonical reference.

For a direct user-supplied video, write:

```json
{
  "reference_mode": "video_avatar",
  "video_avatar": {
    "path": "reference/avatar.mp4",
    "media_id": "<video media id>",
    "origin": "user",
    "has_audio": true,
    "inspection_frame": "reference/inspection-frame.png"
  },
  "creative_notes": "Identity, wardrobe, set, lighting, motion, and useful framing observations",
  "cameras": {}
}
```

For a photograph-created avatar, set `"origin": "photo_bootstrap"` and also record
`"bootstrap_source_media_id"` and `"bootstrap_plan_job_id": "host-001"`. The accepted
hook at `reference/avatar.mp4` is the same completed `host-001` source file, not a
second encode or generation.

Every later request attaches `video_avatar.media_id` with role `video`.
When `has_audio` is true, the video also owns voice identity; do not add a competing
physical voice description. The provider prompt uses the exact matching `@Video 1`
declaration from [generation.md](generation.md).

## Author the camera map

The reference is identity and location context, not a start-frame lock. Author one
stable three-camera map from the visible image or accepted video plus its inspection
frame, and preserve it across all jobs:

- `CAM_A` — frontal single, normally eye-level medium with an explicit waist-up crop,
  for direct address, hook, verdict, and CTA;
- `CAM_B` — right-cheek or left-cheek three-quarter single, with an explicit vertical
  angle, normally medium-close with a chest-up crop, for sustained explanation;
- `CAM_C` — near-profile close/accent single, with an explicit vertical angle and
  head-and-shoulders crop for reveals and emotional emphasis.

Record `shot_size` for each camera using only `wide`, `medium-wide`, `medium`,
`medium-close`, or `close`. Selected cameras must use distinct sizes so every
generated-internal cut changes both composition and scale; an angle-only
medium-to-medium cut is not sufficient. In each `framing`, record a concrete physical
viewpoint (`frontal single`, side-specific `right-cheek` or `left-cheek three-quarter
single`, or `near-profile single`), vertical angle, standard size, observable body
crop, subject placement, negative-space direction, and movement. For an oblique
setup, name the host's anatomical side and the nearer cheek and shoulder; an
approximate camera offset from the reference viewpoint can reinforce that view.
Define camera positions around the host while preserving the host's place and
general facing direction in the set, with the chair fixed when present. These spatial
anchors allow natural leaning, weight shifts, slight turns and changing hand positions
during speech; the reference pose does not constrain performance. Follow the camera and
shot-entry rules in [generation.md](generation.md). Reject vague definitions such
as “alternate”, “closer”, “wider”, or “dynamic”.

A framing travels into the provider's `SHOT N` label, so it describes only what the
camera records and follows the graphic-layer rule of
[generation.md](generation.md). The subject placement and negative-space direction are
planning expectations, not measured safe zones. They let `motion-direction.md` define
global camera-aware placement policy and let `edit-plan.md` assign each treatment to a relative region.
Generated footage may deviate from the reference composition, so exact geometry is
chosen only in `edit.jsx` after inspecting the actual host frames.

For a seated presenter, keep the lap, knees, and lower legs outside every speaking
setup. Do not choose `wide`, `medium-wide`, or any below-waist crop merely to satisfy
the distinct-size rule; the default three-camera progression is medium waist-up,
medium-close chest-up, and close head-and-shoulders.

For `standard`, keep all setups restrained, conventional, and locked off. For
`creative`, author any story-motivated framing and camera movement appropriate to the
episode and premium hosted YouTube storytelling. Keep `CAM_A` available as a frontal
anchor and every speaking angle readable for lip-sync. Prompt-level camera directions
preserve the named camera roles while adapting their behavior to the job.

Do not:

- generate a replacement host without the user's explicit casting choice or recorded
  autonomous delegation;
- treat missing information alone as autonomous consent;
- create alternate reference images merely to force camera angles;
- replace an accepted video avatar with its extracted inspection frame in provider
  requests;
- change one camera's visual meaning between jobs;
- put remote URLs or paths outside the run directory into the manifest;
- copy a media id by hand from an unrelated run.
