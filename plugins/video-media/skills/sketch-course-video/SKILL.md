---
name: sketch-course-video
description: "Урок или сторис из записи спикера со скетч-анимацией на Remotion: рисунок проявляется по контурам, маркер, хромакей, субтитры. Триггеры: «видеоурок со скетчами», «скетч-ролик из вебинара». НЕ промо→video-shotcraft; рилс с нуля→video-montage."
metadata:
  version: 1.1.0
  reuses: image-generation, openai-dalle, deepgram, watch-video (all optional)
---

# Sketch Course Video

Turn real recorded lessons into readable, deliberately paced videos. Reuse the approved hand-drawn reveal engine rather than generic template animation. Communicate in the user's language; production code and identifiers in English.

> **Licence.** The pipeline renders with Remotion: free for individuals and companies of up to 3 people; a larger company needs a Remotion Company License (remotion.pro/license). Nothing else is bundled: no fonts, media, logos or `node_modules` — each job supplies its own licensed fonts and footage.
>
> **Where things live.** The skill is read-only at run time: `common.writable()` refuses to write into `~/.claude`, `~/.codex`, `~/.agents` or the skill folder. Every job gets its own directory, passed explicitly on the command line; the documented default is `~/VideoJobs/<YYYY-MM-DD>-<slug>/`. Put jobs on a disk with room: one lesson plus the Remotion runtime is several GB. If the system disk is small, also point `npm_config_cache` and `TEMP`/`TMP` at that disk before `install-runtime` and rendering.
>
> **Long runs.** `raw_edit.py --start` and `pipeline.py --start` can run far longer than a 10-minute tool timeout: start them in the background and check back; cancel with a `STOP` file in the job directory. Write JSON configs with a file-writing tool rather than shell heredocs (Git Bash heredocs eat backslashes). Official Remotion agent skills (create, render, best practices), if installed, help with engine changes.
>
> **Accent of the artwork** is set per source: `"accent": "yellow"` (default, lesson style) or `"coral"` for red/orange accents (e.g. `#E8643C`) — the yellow rule does not draw red/orange at all. Marker and heading underline take `palette.accent` of the scene.
>
> **Vertical 9:16** is supported: `video` 1080×1920, panels of any even geometry, large multi-line left-aligned headings via `titleLayout`, a title-only band over live footage (`arts: []`), `captions.py --width 1080 --height 1920`. Name plates, CTA and logos are PNGs via `branding.logos` with intervals. A sketch sheet may be RGBA (the mask is computed over the theme background).
>
> **Lesson-style captions** — `captions.py --highlight pill`: a marker plate under the first term of a cue; terms with a trailing `*` match word forms (`задач*`).
>
> **One shared Remotion runtime** can serve every job: install it once (e.g. `~/VideoJobs/_runtime`) and set `"paths": {"runtime": "<that path>"}` in each project.json. For recurring series, keep a small per-job generator script (e.g. `build_lesson.py`) that writes project.json from timings — it makes re-cuts reproducible.

## Start here

1. Locate actual source recordings, slide art, transcript/notes and latest approved export. Inspect live files; never assume a previous task completed. Do not select takes by sorted filenames alone.
2. Run `python -B <skill>/scripts/project.py init ~/VideoJobs/<YYYY-MM-DD>-<slug>` (a new empty directory; `<skill>` is where this skill is installed, usually `~/.claude/skills/sketch-course-video`). All state/logs/assets/outputs belong to that project, not the installed skill. Source recordings stay untouched.
3. For raw inputs, read [production.md](references/production.md) and build an explicit edit map. For a visual revision preserve the approved base's repaired audio.
4. Read [animation.md](references/animation.md) before drawing and [design.md](references/design.md) before changing layout. New style: short proof first. Already approved style + request for whole video: complete it without another approval loop.
5. Configure `project.json` per [config.md](references/config.md). Run `scripts/pipeline.py <config>` for a plan, then `--start`. Run `scripts/raw_edit.py <edit.json> --start` first if no approved base exists.
6. Multiple lessons: `scripts/batch.py <batch.json> --start`; see [batch-qa.md](references/batch-qa.md). No unbounded agent/render swarm.
7. Deliver the actual MP4 by absolute path, plus SRT, cover, manifest and QA. Inspect Preview.jpg and contact-sheet frames by opening the images; for a timecoded pass use skill `watch-video` if available. Technical PASS does not prove lip sync, pronunciation or full visual review.

## Visual contract

- Alternate light paper and dark panels by meaning, not a timer. A visible marker is selective, not attached to every stroke.
- Reveal the approved illustration along its contours, then hatching and accent fills. Do not replace detailed sketches with generic boxes or a fade-in.
- Tie beats to spoken words. The final step must finish before the cut. A layout change must not restart a continuous drawing.
- Crisp typeset headings; selective handwritten short labels; readable captions in a dedicated band, not over slides or face.
- Anchor the speaker at a softly rounded panel's bottom. Light/moderate gradient behind dark clothes. No floating torso, doubled borders or stretched face.
- Logos are **optional and brand-agnostic**: `branding.logos: []` by default. Any authentic supplied assets, one or many. No built-in logo, name, portrait, course identity or statistics.
- Use purposeful split/large-slide/speaker-close/concept/real-UI shots. A schematic must not be passed off as an actual interface.

## Reliability invariants

- One integer `[start,end)` frame clock. Normalize source PTS/FPS. No copying old lesson timestamps into a new lesson.
- Speech cuts change camera, illustrations and caption timing together through the edit map. Never time-stretch speech to fit animation.
- For visual revisions copy the approved audio bitstream and verify its hash. Audio identity preserves existing sync; it does not establish that sync was correct.
- Preserve source PNG bytes and hashes. Compute reveal masks/paths locally. For new illustrations or image edits use skill `image-generation` and the model ladder in `~/.claude/config/models.md` (default `gemini-3.1-flash-image-preview`; dense Cyrillic or small text → `gemini-3-pro-image-preview`; one identity across a series or multi-reference → `gpt-image-2.5-sunburst` via skill `openai-dalle`) unless the user specifies another provider. Save prompt, model id and SHA256 beside the PNG; check the real format with PIL before naming it .png.
- Check input color range/matrix and convert explicitly to BT709 limited. Never apply range conversion twice.
- Missing inputs and failed tests stop the run. Bound retries/timeouts; resume only verified caches; honor STOP. No silent fallback to an old export.
- No raw recordings, private documents, secrets, proprietary fonts or dependency trees bundled inside the skill. No automatic uploads/publishing/provider installation.

## Read only the active-stage reference

- [production.md](references/production.md): ingest, sync, edit map, raw assembly, keying, audio/captions.
- [animation.md](references/animation.md): prompts, three treatments, original-art tracing, marker and connected arrows.
- [design.md](references/design.md): layout, palette, optional branding, shot grammar.
- [config.md](references/config.md): requirements, commands and executable manifest contract.
- [recording-notes.md](references/recording-notes.md): OBS and full spoken notes without hard wraps.
- [batch-qa.md](references/batch-qa.md): batching, proof/full-render checks and delivery gate.
- [provenance.md](references/provenance.md): scripts and automation boundaries.

## Bundled executable toolkit

`project.py` creates an isolated project; `media_tools.py` inventories, estimates audio offsets and unwraps notes; `raw_edit.py` assembles explicit A/V cuts and layers; `prepare.py` extracts stroke masks; `pipeline.py` type-checks/builds/tests/renders/composites/verifies; `captions.py` formats SRT into measured two-line ASS with optional time-specific positions; `batch.py` runs bounded sequential jobs. `transcribe.py` optionally uses an existing local faster-whisper model (extra dependency, no automatic download), or use skill `deepgram` for a draft. `assets/remotion/SketchPanel.tsx` and `scripts/trace.py` contain the actual drawing engine. Tests ship with the scripts: `python -B -m unittest discover -s <skill>/scripts/tests -v`.

Every script prints a plan and does nothing heavy without `--start`.

Automation removes repetitive rendering work. Editorial cut selection, transcript correction, semantic timing and perceptual A/V review remain explicit work, not invented one-click decisions.
