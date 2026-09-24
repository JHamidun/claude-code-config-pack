# Slides → drawn animation

The optional `sketch-course-video` skill ships in the same pack
(`~/.claude/skills/sketch-course-video`; jobs in `~/VideoJobs/<YYYY-MM-DD>-<slug>/`, one shared
Remotion runtime such as `~/VideoJobs/_runtime`). It supports `sources.accent: coral` for a
red/orange accent, RGBA sheets, a `titleLayout` for 9:16 stories, pill captions, soft panel shadows.

Its approach: classify ink/accent from reviewed artwork → skeletonize ink → reveal the original
pixels along SVG strokes → add selective hatching and a moving marker at the stroke tip.
This preserves the slide's illustration style rather than replacing it with generic icons.

1. Start with approved slides and actual spoken recording/transcript. `motion-handoff.json`
   exports IDs/palette/art paths/notes/draw_order but invents NO timestamps.
2. Select clean object crops in original pixel coordinates; exclude captions/logo fragments.
   Keep main type as separate crisp labels. Do not reveal a giant slide rectangle as one wipe.
3. Map drawings to actual speech beats. Every stage, especially the last one, must finish
   before the cut. Allow a completed hold. Do not highlight step2 while the speaker explains3.
4. Alternate paper, dark and occasional marker based on content. Avoid constant camera motion.
5. A scene with several placements shares one clock: changing shot size must not restart art.
   Check both sides of each cut to avoid one-frame slide flashes or duplicate entrances.
6. Keep presenter attached to the bottom of a softly rounded frame; use a lighter gentle
   gradient behind dark clothing. Do not float a cropped torso in empty space. Avoid double
   borders, giant repeated headers and dense chrome. Preserve hair/mask edges, no fake relighting.
7. Reserve a subtitle band below the presenter/information, not over slide text. Short phrases,
   stable lines, restrained accent-word color; no perpetual rainbow karaoke or bouncing letters.
8. Audio and video must share the edit map. Diagnose sync across beginning/middle/end; do not
   guess one global offset. Remove stumbles only with frame/sample-aware cuts and check joins.
9. The first frame is a designed readable cover, not half an entrance animation or an empty panel.
10. Inspect 0/25/50/75/100% of every drawn scene plus all cuts, subtitles, ending and lip-sync.

Read the sibling's `SKILL.md`, then `references/config.md` and `references/animation.md` for
executable schemas. This handoff file is editorial metadata, not itself a video project config.
Marker animation is deterministic/stylized, not a photoreal human hand. Source ink colors are
preserved; generate genuine light/dark source art instead of hoping palette parameters recolor it.
