# Direct MCP operations

## Build the actual request

Keep stable nonnegative numeric indices for generated host and supporting assets.
Track each index's plan id and exact submitted params. A plan record may include
`id`, `dialogue`, cameras and an inner `request`; send only that inner request as
MCP `params`, without the planning wrapper. All model options are already flat.

For multiple independent requests, call the matching batch tool with 1–6 entries:

```json
{
  "requests": [
    {
      "index": 0,
      "params": {
        "model": "seedance_2_5",
        "prompt": "<complete authored prompt with the exact spoken words>",
        "count": 1,
        "duration": 8,
        "aspect_ratio": "16:9",
        "resolution": "1080p",
        "mode": "omni_reference",
        "generate_audio": true,
        "medias": [{"value": "<confirmed host media UUID>", "role": "image"}]
      }
    }
  ]
}
```

Resolve placeholders and verify model-specific options before submitting. Eight
seconds is an example. Image-keyframe uses `image`; a video avatar uses `video`.
Supported canonical roles are image, video, audio, start_image, end_image and
ref_element, limited further by the model. Never send backend role aliases, an
extra nested params object, or plan-only ids/fields. One standalone user-facing
request can use `generate_image` / `generate_video` with `{params: request}`;
those tools also require the outer `params` wrapper.

Record payloads before submission. Reading a plan is not submission; there is no
prepare tool/token, conversion helper or backend reading a local JSON path.
Keep prompts unchanged when transferring a written payload into a tool call.

## Record actual outcomes

Batch results contain `jobs`, `submitted_count` and `failed_count`. Match every
returned index to the submitted set. Persist real job_id, status, error, warning
and adjustments; accepted siblings remain accepted even when another entry fails.
Unknown, duplicate or missing indices require reconciliation before another call.
Never manufacture a job id, completed URL or successful status from a planned row.

Store accepted ids in conversation immediately, then in the next checkpoint.
A lost response is ambiguous submission, not a failed generation. If a returned
id exists, use it. If no id can be recovered through available job tools, explain
the ambiguity before proposing a new paid request; do not silently duplicate it.

## Continuous dispatch

Send the ready hook shots as the first wave; finish authoring the remaining requests
while they run. Keep at most six entries per submission, not one tool call per shot.
Record the first wave before sending the next. Completed hosts can be downloaded,
transcribed and inspected while other jobs remain pending. Author supporting media
and reusable motion during those waits.

Poll `jobs_wait` with `jobs:[{index,job_id}]`, at most eight, timeout_seconds 0 for
a snapshot or up to 15 for a wait. Preserve results across wait groups. Respect
poll_after_seconds. Use each completed entry's result_url to retrieve its media.
Transient lookup errors can be polled later; permanent lookup failures stop polling
that id and need reconciliation. Neither means the provider generation failed.
`all_terminal` can include permanently unresolvable ids; it does not mean all succeeded.

After every group in the user's generation set is terminal, collect the indexed
set and show it once using `show_generation_by_ids`, at most 24 ids per display.
Casting and the independent thumbnail are separate generation sets; finished host/support sets do not replace the
final MP4. Do not use history browsing or one widget per batch id.

## One retry policy

- Pending/accepted/completed jobs are never resubmitted as retries.
- For an explicit submission failure with no job, resolve the returned cause and
  retry only that entry; for a confirmed provider failure, one corrected replacement
  may be attempted within the authorized task. Further attempts need user direction.
- A completed clip with an actual identity, speech or camera defect is a creative
  replacement, not provider failure. Explain the defect and proposed replacement
  before spending unless the user already delegated such corrections. Preserve the
  original, give the replacement a new index and record which source was selected.
- A transcript spelling/anchor mismatch alone is not a generation defect. Inspect
  the actual audio and correct its timing mapping. A URL-less completed result
  needs retrieval/reconciliation, not regeneration.
- Billing-choice entries are unsubmitted: keep their params, obtain the actual choice,
  and retry only those entries. This does not authorize replaying accepted siblings.

## File work and continuation

Use the [runtime checkpoint protocol](../SKILL.md#persist-state-across-calls)
for downloads, measured transcripts, plans and authoring files. Operations are
explicit calls to available tools/CLI; no command automatically creates ledgers,
anchors, renders, proof sheets or review verdicts. Derive measurements as described
in [anchor preparation](anchor-prep.md), assemble with [assembly](assembly.md), and
inspect/export through [delivery](delivery.md).

On resume, inspect the saved receipts and existing process status before another
operation. Start each render/transcription once, retain its actual handle/log and
confirm it ended before retrying a timeout. Do not run concurrent writers against the
same project or transcript outputs. Reuse transcripts when only anchor wording changes.
Keep the cover receipt outside required asset/build inputs; a status-only change or
cover completion never invalidates a finished master or triggers another render.
