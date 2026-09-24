# Script contract

Write for one visible host with a clear promise, progression, and payoff. Choose the
narrative form that fits the topic: story, argument, review, experiment, build,
commentary, or another coherent form. Do not force a house outline.

## Preserve authorship

- A user-supplied script is locked unless the user explicitly permits rewriting.
- A generated script remains editable until approval.
- `script.md` is the approved spoken source. Production headings and bracketed mode
  markers may organize it, but every spoken word must appear once and in order across
  `generation-plan.json.jobs[].dialogue`.
- Never hide a rewrite inside job splitting, prompt polishing, or assembly.

## Route brief-based writing

For a brief, first load the installed `$youtube-script` SKILL.md and apply its canonical
narrative-engine router without reproducing or simplifying its genre table here.
Diagnose the subject, viewer promise, narrative engine, evidence spine, and host
stance. Topic nouns such as company, AI, economics, work, productivity, or money are
not decisive. Select a guide only when its affirmative entry gate is satisfied; no
guide, especially business/finance, is a fallback.

Record `script_source: "brief_generated"` and the chosen genre briefly in `brief.json`,
then load `references/<genre>.md` from that installed skill directory.
No routing receipt or rejected-alternative report is needed.

If two affirmative entry gates remain genuinely satisfied and the run is
interactive, ask one concrete outcome question before drafting. Under explicit
autonomous delegation, choose from the requested outcome, title promise, available
evidence, and intended payoff; never default an ambiguous brief to business/finance.
Do not blend full guides.

Load the matching `references/<genre>-patterns.md` from the installed `youtube-script` only
for a long or structurally complex episode, or when the concise guide does not resolve
a craft decision. These paths are relative to the installed `youtube-script`
directory, not to `ai-host-video`.

The genre guide supplies writing craft, not a second workflow. This skill still owns
the accepted host, approved spoken source, generation plan, and edit.

## Adapt the guide to an AI host

- For user-supplied copy, record `"script_source": "user_supplied"` in `brief.json`
  and omit `script_route`; preserve the supplied script rather than retroactively
  classifying or reshaping it.
- Keep one visible host as the episode's presenter. Do not choose a faceless,
  parallel-activity, footage-only, or multi-host lane unless the user supplied the
  required material and explicitly wants that presentation.
- Never invent first-person experience, tests, purchases, spending, revenue,
  failures, confessions, credentials, audience history, or access. If a genre expects
  personal receipts, use user-supplied receipts or switch to named sourced evidence
  and an honest analyst/explainer register.
- For factual claims that need verification, use available host web search to discover sources and
  available host source reading to inspect them before drafting. Prefer primary or authoritative
  sources. Keep unresolved claims out of the spoken script; report them separately
  rather than turning them into host certainty.
- Do not invent sponsors, affiliate pitches, courses, merchandise, or product plugs.
  Include a monetization beat only when the user explicitly requested it, and preserve
  their supplied claims and disclosure requirements.

## Draft from a brief

1. Follow the selected guide to create three genuinely different hook candidates.
2. Select the strongest candidate by specificity, available proof, fit to the title
   promise, and fit to the one-host presentation.
3. Write the complete spoken script around that selected hook. Use the guide's beat
   proportions and retention devices, with the delivery pace and word budget below
   for runtime planning.
4. Write only the selected complete spoken draft to `script-draft.md`. Do not put
   alternate hooks, timestamps, a retention map, source notes, or internal labels in
   that file.
5. Review the selected draft yourself and continue. Only at an explicitly requested
   script checkpoint, present it with the other hook options as described below.

Genre timestamps are planning estimates derived from target duration, words per
minute, and beat percentages. They do not control assembly and must not enter
`script.md`. Target duration is approximate: write toward it, then report an honest
runtime estimate. After generation, measured transcript word times own edit timing,
and the master is allowed to land short or long of the brief. Do not later add
speech-free holds or cut speech to hit the planned number.

## Write for generation

Choose the average delivery pace before budgeting a new script. Honor an explicit
pace or an available speaking reference; otherwise start at 150 words per minute.
A deliberately brisk countdown can use 160–170 and a calm explainer 140–150. These
numbers are internal estimates for word budgeting and request duration only.

Budget spoken words as target speaking minutes times that pace. Deduct any known
speech-free structural inserts and deliberate silent holds from the episode target;
visuals over continuing narration do not reduce its word budget. Count the completed
spoken text, excluding headings and notes; do not report the budget as the actual
word count. Record the request in `brief.target_duration_minutes` and compare a new
draft with the budget before splitting. Report the runtime estimate
honestly. If a later host reference reveals a different natural pace, preserve locked
copy and update the estimate. There is no script-length gate; do not pad, retime,
truncate speech or rewrite user-supplied copy merely to hit a number.

Prefer natural sentence-safe job boundaries. Calculate each request's duration using
the shared [dialogue timing](generation.md#dialogue-timing) rule, including the same
pace and a small allowance for onset and the closing beat. Read the line aloud mentally
and split it when natural delivery would exceed the model's limit. Avoid large silence
buffers that invite stretched delivery.

Vary sentence shape, intensity, gesture, and camera behavior according to meaning.
Avoid prompt-like prose, fake quotations, generic creator filler, repeated hooks, and
stage directions inside spoken dialogue.

## Canonicalization

Only for an explicitly requested script checkpoint, show the complete spoken script
in chat with word count and an honest runtime estimate. Ask in normal chat whether
to continue, select an alternate hook, or edit. Checkpoint first and wait for the
actual answer. Re-present the complete revised text if wording changes.

After approval, copy the exact draft to `script.md`. In autonomous mode select the
strongest hook, review it yourself, save `script-draft.md` and `script.md`, and
continue without inventing a review gate. Billing follows the OpenAI runtime.
