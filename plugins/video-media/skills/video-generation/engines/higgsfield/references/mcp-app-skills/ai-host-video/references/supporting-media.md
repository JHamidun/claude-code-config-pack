# Supporting media

Write `visual-plan.json` for picture coverage plus generated or supplied supporting
media. Record coverage even when there are no selected image/video assets or music.
Write it after the initial host wave, without waiting for all host completions or the
backlog. Supporting work may add independent requests but never change or resubmit
an accepted host request.

Run an explicit asset-opportunity pass over every chapter and major beat in the
approved script before settling on uninterrupted host or typography-only motion. A
candidate still or video is valuable when it contributes inspectable appearance,
spatial context, visible action or change, story-specific atmosphere, or other
non-verbal information that the host and abstract graphics cannot communicate as
directly. If a candidate has that distinct value and a concrete use in the planned
composition, include it; do not reject it merely because the host could technically
carry the dialogue or because generation adds work.

This pass precedes motion design: every host job records the strongest specific
still/video candidate and either selects it or explains why the host or a motion
graphic communicates that job better. Dialogue about concrete subjects — a product,
a place, a process, an event, evidence, a comparison — normally earns real picture
support in this format. Absent explicit user direction toward a typography-led style,
an episode with real chapters whose only visual variety is typography motion is a
planning failure of the same rank as a templated plan: motion graphics are one medium
in the mix, not the default answer to every visual beat.

Select the medium by the information it contributes, not from a desire to fill the
timeline:

- use a still image when a concrete subject, place, document, result, or visual
  reference benefits from inspection;
- use generated video when action, transformation, sequence, or atmosphere carries
  information that a still cannot;
- use authentic sourced media — user-supplied first, then web-sourced — only when
  authenticity itself is the information: archival or historical material, a current
  or news event, a real named product, person, place, interface, or document, or
  factual proof that a generated look-alike would misrepresent. Illustrative,
  atmospheric, and conceptual beats stay generated;
- use motion graphics when designed graphic support best serves the beat's editorial
  purpose and viewing experience;
- keep the host on screen when another visual would only restate the words.

Cards, badges, diagrams, icons, generated-looking interfaces, and typography built
inside higgsedit are all `motion-graphic` picture support. Calling them
content-backed, illustrative, or non-typographic does not make them a still/video
asset and does not discharge the candidate review below.

Before motion design, create each selected image/video row as a request brief with a
stable id, kind, editorial purpose, verbatim dialogue anchor, model, aspect ratio, and
any duration that affects cost. Leave final prompt prose absent until
`motion-direction.md` and `edit-plan.md` define the episode art direction, picture
ownership, composition, and intended use. The edit plan references the stable asset id,
so prompt finalization does not reopen medium selection.

After the edit plan is complete, write each final image/video prompt for the specific
informative content and composition needed at that beat rather than generic mood
footage. Express the chosen subject, framing, visual style or sound directly: the
provider does not see `motion-direction.md`, the script or the editorial purpose field.
Keep phrases about matching the episode, following the plan or writing a prompt out
of the submitted text; replace them with the actual visual or musical choices.
Do not generate unused alternatives, low-specificity stock-like filler,
fabricated evidence, or a literal illustration of every sentence. When a factual claim
requires authentic proof, use supplied or properly sourced media rather than a generated
substitute. Do not express the same idea simultaneously as b-roll and motion graphics
unless the combination adds distinct information. Follow the episode art direction in
`motion-direction.md` without copying the host frame's palette by default. This is a
positive editorial bias, not an asset quota.

### Coverage decisions

Write one `coverage` row per `generation-plan.json` host job, in the same order. Each
row records the strongest concrete still/video candidate before motion design can
replace the question with a graphic:

- `host_job_id` — one exact generation job id;
- `strongest_candidate.kind` — `generated-image`, `generated-video`, `supplied`, or
  `web`;
- `strongest_candidate.concept` — the specific visible content, not a generic medium
  such as “stock b-roll”;
- `strongest_candidate.information_gain` — one of `appearance`, `action`,
  `spatial-context`, `process`, `atmosphere`, or `evidence`;
- `strongest_candidate.dialogue_anchor` — a verbatim phrase from that job's dialogue;
- `decision.outcome` — `use_asset` or `reject_asset`;
- `decision.reason` — why the selected picture communicates the beat better;
- for `use_asset`, non-empty `decision.asset_ids` naming rows from `requests` or
  `supplied`;
- for `reject_asset`, `decision.fallback_picture` set to `host` or
  `motion-graphic`.

The strongest candidate is adversarial: test the best specific still/video that could
be made for the beat, not a deliberately weak laptop, money, office, or generic stock
alternative. One coverage row may select multiple asset ids, but every selected id
must have a real use in `edit-plan.md`. At least one selected id must match the
strongest candidate's kind. Every selected generated image/video request must anchor
inside that coverage row's host-job dialogue; supplemental assets may use different
anchors from the same job.

If no supporting picture asset benefits the episode, explain the choice briefly in
working notes. No separate zero-asset review is needed. Viewers of a factual countdown
need to inspect its subjects; rank cards alone do not satisfy that purpose.

These choices describe what source material to create or source, not how much screen
it owns. Selection never grants picture ownership. The edit plan makes that later
decision through the canonical ON-CAMERA / VISUAL / PLAYBACK rule in `edit-plan.md`.
Several related assets should form one developing visual argument — rank, chronology,
comparison, evidence, or state — instead of restarting an independent reveal for each
item. These are editorial decisions, not numerical caps.

### Web-sourced media

This route puts web-sourced material on screen; it is separate from the
fact-verification research in [script.md](script.md), which uses the same tools to
check claims before drafting, needs no consent, and never places media in the video.

Web sourcing is a narrow evidence route, not a general b-roll supply. It applies only
where authenticity itself is what the beat communicates: archival and historical
material, current or news events, a real named subject whose actual appearance the
script discusses, or proof behind a factual claim. Generated media remains the default
for everything illustrative, atmospheric, or conceptual, and a typical episode without
such beats has zero web-sourced items. Do not add a web item merely because consent
was recorded or because the tool is available.

When such a beat exists and the user supplied nothing for it, source the material with
available host web search and available host source reading: official press or product images, publicly published
screenshots, event photos, charts, or documents. Prefer official and press-kit
sources for brands and products. Present a page or interface as a screenshot
treatment so it reads as evidence, never as the episode's own footage, and keep the
source identifiable when the beat makes a factual claim.

Web sourcing requires recorded consent in `brief.json.web_media_consent`. The user
asking for internet materials, supplying links, or explicitly delegating creative
choices grants it; otherwise, when the topic has archival, current-event, or
real-subject beats that generated media would misrepresent, include one consent entry
in the grouped episode intake. Consent permits the route; it does not create a quota
or make web sourcing the preferred medium. Never web-source without that consent; use
a generated composition clearly presented as an illustration instead.

Record each selected item in `visual-plan.json.supplied` with `"origin": "web"`, the
exact `source_url`, and a one-line provenance note. Download the file into
`inputs/source/` before approval and import web-sourced video from that original file.
Every web-sourced item gets the same beat, editorial purpose, and composition decision
as any other supporting asset.

A user-supplied picture belongs in `coverage` when selected. When inspection shows
that it should not appear, preserve the supplied row for auditability and add a
non-empty `set_aside_reason`; do not create a fake coverage use. A selected supplied
row must omit `set_aside_reason`. Generated requests are paid plan decisions and may
not be left orphaned. Audio is supplied on this OpenAI surface; music, sound logos and jingles remain
supplied rows whose placement is described in the edit plan.

Product and worn plates are not supporting-media rows. Their exact requests live in
`product/plate-plan.json`, their results live in `assets.json` with
`purpose: "product_reference"`, and host requests consume their inspected media ids.
Do not duplicate a product-reference request inside `visual-plan.json`.

This is a structural example of an illustrative asset, not fabricated evidence.
Resolve placeholders and replace example concepts, anchors, musical choices and
durations with the current episode's values before submission.

```json
{
  "version": 1,
  "coverage": [
    {
      "host_job_id": "host-001",
      "strongest_candidate": {
        "kind": "generated-image",
        "concept": "Illustration of three stages of a general process",
        "information_gain": "process",
        "dialogue_anchor": "the process has three stages"
      },
      "decision": {
        "outcome": "use_asset",
        "asset_ids": [
          "asset-process"
        ],
        "reason": "The viewer needs to see how the stages connect"
      }
    }
  ],
  "requests": [
    {
      "id": "asset-process",
      "kind": "generated-image",
      "purpose": "Illustrate the relationship between the three stages",
      "dialogue_anchor": "the process has three stages",
      "request": {
        "model": "<chosen model>",
        "prompt": "<concrete subject, composition and visual style>",
        "aspect_ratio": "16:9",
        "count": 1
      }
    }
  ],
  "supplied": [
    {
      "id": "asset-unused-document",
      "kind": "supplied",
      "path": "inputs/source/document.png",
      "origin": "user",
      "set_aside_reason": "Inspection showed an obsolete revision that contradicts the approved script"
    }
  ]
}
```

### Music bed

This OpenAI surface cannot synthesize music/SFX. Do not add a generated-audio
request or use speech generation as a substitute. Reuse an authorized supplied
instrumental track, registered as `music-bed` in `assets.json` per
[OpenAI runtime](../SKILL.md#music-editor-and-platform-limitations).
Without a supplied track, disclose the limitation and set background_music false;
if music is explicitly required, resolve that asset before paid generation.

For supplied music preserve the upstream arrangement intent: unobtrusive steady
energy, no vocals or speech, no busy leads masking the host. Follow
[assembly](assembly.md#background-music) to extend and mix it with installed FFmpeg
at the measured duration, applying attenuation once. Never pad picture to a track.
