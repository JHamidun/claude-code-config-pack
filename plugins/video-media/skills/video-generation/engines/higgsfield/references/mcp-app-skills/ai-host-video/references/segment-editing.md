# Editing an existing episode locally

For an edit to a previously delivered episode, restore its confirmed editable
checkpoint into a new run directory. Read the current script, original media,
measurements, motion source and native project before changing it. Preserve the
original archive; never overwrite someone else's connected or user-edited project.

Resolve the affected block/phrase and requested change. Preserve every untouched
block, accepted host reference, spoken wording and editable layer. A rendered MP4
alone does not preserve text nodes, source trims or layered graphics. If the edit
requires those and only an MP4 is available, ask for the editable archive instead
of claiming to have reconstructed the source.

Use the installed `$video-editing` skill from the OpenAI catalog for native
inspection and bounded changes.
Avoid a whole-script rebuild over human timeline edits. Measure the changed source
and timeline ranges; do not reuse planned timecodes as actual segment boundaries.
Review only the changed ranges plus their seams unless the change is episode-wide.

Reserve output/checkpoint uploads, render the revised MP4 and PUT it in the same
sandbox work unit. Return confirmed revised MP4 and editable ZIP URLs with a concise
change description. No internal block report, platform editing manifest, or hosted
editor callback is available in the OpenAI profile.
