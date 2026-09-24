# Production and release gates

## Input contract

Identify the exact current program and template. Extract slide text, notes, imagery, metadata,
logos, fonts and dimensions. Do not infer the syllabus from a visual sample deck. Confirm
which previous conference notes are the tone/reference and which facts belong to this lesson.
Do not fabricate information while transferring a speaker slide.

## Editorial map before image generation

For each stable slide ID specify: title, exact visible text, argument drawn visually, palette,
full spoken paragraphs, stage directions and sources. Generate the illustration only after
the content makes sense. Image prompts are not the source of truth for facts.

The first slide explains what participants will learn. If a speaker slide follows, put the
self-introduction there, not twice. Before a live build, provide the minimum conceptual base:
where the work happens, what the agent receives, what gets created and how to verify it.
An installer may handle setup; that does not remove the need for orientation.

## Notes

Write ready-to-speak paragraphs in the speaker's actual voice, not a slide summary or an essay
to be read at double speed. Match the requested depth and delivery length; avoid imposing a
universal word count. Include concrete examples and transitions. Keep stage directions in a
separate field and out of the teleprompter export. Store paragraphs as array items; do not hard
wrap lines at 60/80/100 columns. A text viewer should wrap to its own window width.

## Proof and batch

Approve a representative light and dark slide first. Use explicit per-slide IDs. Bind actual
art with SHA256 and prompt signature. Never reuse images solely because a filename exists.
Check stale bindings when content, palette or asset reservations change. Keep source images
unchanged; build into a new directory. No automatic regeneration or provider cost in the build.

## Visual inspection checklist (every slide)

- Exact words and numbers; Cyrillic vs Latin lookalikes; no repetitions/truncation.
- One visual argument; arrows and object relationships make sense.
- Readable at playback size; not only at 4K zoom.
- No stretch, missing edge, unintentional strip, duplicated frame or empty logo placeholder.
- Authentic logos/portrait/QR preserved; no personal files behind UI screenshots.
- Full notes matched to the correct ID after reordering.
- Consistent PPTX slide count, dimensions, notes, PDF and image exports.

The bundled export renders its own PNG/PDF from the source layers. It does NOT launch PowerPoint.
When PowerPoint/LibreOffice is available, open/export the PPTX independently and compare it
(on Windows with PowerPoint installed: COM, read-only — snippet in SKILL.md).
Otherwise report that application-level rendering is unverified, not that visual QA is automatic.
Raster text remains raster; separate logo/screenshot objects stay separate picture shapes.
