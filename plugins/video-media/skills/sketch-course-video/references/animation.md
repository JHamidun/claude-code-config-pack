# Original-art sketch animation

## Reusable art direction

The reference style uses black/white/yellow source sketches, not a physical whiteboard. Raster colors cannot be changed by merely changing the stage palette. Prefer approved originals. For new illustrations use skill `image-generation` (model ladder in `~/.claude/config/models.md`: NB2 Flash → NB Pro → `gpt-image-2.5-sunburst`) and retain the exact prompt, model id and hash. Gemini SDK gotcha: when both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set, the SDK prefers one of them — unset the key you do not mean (e.g. `os.environ.pop('GEMINI_API_KEY', None)` when you use `GOOGLE_API_KEY`).

Prompt core (replace palette/content):

> One coherent [16:9 | 9:16] instructional exec-sketch visualization. Confident slightly imperfect ink contours, purposeful hand hatching, expressive connecting arrows, selective accent-marker fills. Every drawing explains the supplied idea. Large crisp typeset heading; short exact [language] labels, precise spelling (for Russian: precise Cyrillic). No invented facts, generic decorative people, physical room/whiteboard, chalk texture or 3D. No logos, portrait, QR or reserved logo boxes. Continuous background; content safely inside margins. Separate objects enough to animate but keep connectors coherent. Palette: [paper/ink/accent]. Exact content and reading order: [brief].

Authentic screenshots/logos/portrait/QR remain separate assets. Schematics must be identified as such.

## Three treatments

1. Paper: warm off-white, dark contours then accent hatching.
2. Dark: original black art with white ink/yellow connectors within the lighter shared stage.
3. Selective marker: same reveal plus a small physical marker following the actual stroke endpoint. Use for one or two semantic accents, not constantly. No bouncing decorative hand.

Choose by meaning/contrast, not random equal alternation.

## Engine

- Original image bytes unchanged. OpenCV/numpy detect ink/accent; skimage skeletonizes ink into centerline paths. This is mask generation, not redrawing the source image.
- Long contours establish objects, nearby details follow. Accent fill uses diagonal hatch strokes; roughly 74% ink, 24% accent, small gap.
- SVG `strokeDashoffset` reveals original raster pixels. Final diluted silhouette covers missed flecks, not a rectangular crop (which would show paper patches/neighbor captions).
- Marker follows active path arc length with stable grip angle, tip on stroke, tiny shadow, accent band while coloring.
- Frame-driven only: `useCurrentFrame()` / `useVideoConfig().fps`. No CSS animations, wall time, unseeded random or playback timers.
- Object start/duration are scene-local seconds. Global cuts are integer frames. Draw to semantic speech beats, not equal spacing. Finish the third step before leaving the scene; allow a short completed hold.

## Crops and continuous scenes

Inspect crops for partial old captions, adjacent arrowheads and logos. `exclude` rectangles remove such fragments only from the mask. Connected overlapping crops must share one source→destination transform or be split without overlaps; moving them independently creates duplicated arrows.

Use multiple `placements` for a continuous scene changing size. Keep one `scene.start` so drawing does not restart. Placements must preserve aspect ratio and not overlap in time. Check 0/25/50/75/100% progress and both sides of cuts.
