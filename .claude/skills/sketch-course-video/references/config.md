# Executable project contract

Use Python 3.11+ and Node 22+, `ffmpeg`/`ffprobe` on PATH. FFmpeg must include libx264 and libass; NVENC is optional. Install Python requirements into an explicit virtual environment, not a canonical source directory. Run scripts with `python -B` to avoid state in the installed skill. Optional: `fontTools` (more exact pill placement in `captions.py`), `faster-whisper` (local `transcribe.py`).

The job directory is always an explicit argument; the documented default location is `~/VideoJobs/<YYYY-MM-DD>-<slug>`.

```powershell
$skill = Join-Path $HOME '.claude/skills/sketch-course-video'
$job = Join-Path $HOME 'VideoJobs/2026-01-15-lesson-01'
python -B "$skill/scripts/project.py" init $job
python -m venv "$job/.venv"
& "$job/.venv/Scripts/python.exe" -m pip install --no-cache-dir -r "$skill/scripts/requirements.txt"
# $env:npm_config_cache = 'E:/npm-cache'   # only if the system disk is short of space; same for TEMP/TMP
python -B "$skill/scripts/project.py" install-runtime "$job/runtime" --start
```

```bash
skill=~/.claude/skills/sketch-course-video
job=~/VideoJobs/2026-01-15-lesson-01
python -B "$skill/scripts/project.py" init "$job"
python -m venv "$job/.venv" && "$job/.venv/bin/python" -m pip install --no-cache-dir -r "$skill/scripts/requirements.txt"
python -B "$skill/scripts/project.py" install-runtime "$job/runtime" --start
```

`pipeline.py` runs the unit tests through `sys.executable`: start it with the Python that has the requirements.

One runtime can serve every job: install it once (e.g. `~/VideoJobs/_runtime`) and set `"paths": {"runtime": "<absolute path to it>"}` in each project.json — saves ~250 MB of node_modules and the Chrome download per job. Each config adds its own `public/sketch-<hash>/`; prune old ones if bundles grow.

`init` writes `project.json`, `edit-example.json`, `scene-example.json`. They are templates, not finished lesson data. Supply actual media and licensed fonts. The runtime installer downloads pinned npm dependencies. **The first render downloads Chrome Headless Shell (~113 MB, storage.googleapis.com) into `runtime/node_modules/.remotion` without a separate prompt** — `--start` covers it. No uploads. Remotion is free for individuals and companies of up to 3 people; a larger company needs a Remotion Company License (remotion.pro/license) — the user decides.

## Two-stage workflow

1. `raw_edit.py edit.json --start` creates a new base from a reviewed take/cut map. Skip this if revising an already approved base with fixed speech.
2. Make reviewed captions using `captions.py`; if burning, use a **different** master filename. Set this as `base_video`.
3. `pipeline.py project.json` validates and prints the plan; `--proof --start` exports proof stills. `--only SceneId --start` renders selected clips but does not claim a complete export. `--start` builds the complete film.

All paths in JSON are relative to its own directory unless absolute. No dependence on this conversation's folders. Do not edit private source recordings in place.

## project.json

Required:
- `schema_version: 1`; `id`: letter then letters/digits/hyphens.
- `video: {width,height,fps,frames}`: positive integers, even dimensions, constant FPS. Intervals everywhere are half-open integer frames `[start,end)`. Seconds only for art/labels **relative to scene start** and raw source `in` values.
- `base_video`: MP4, one approved master audio track, exact output dimensions/FPS/frame count; BT709 limited. Do not merely retag unknown color data.
- `fonts: {heading,hand}`: supplied licensed font files. Both must support the language. No fonts are bundled.
- `sources`: map of source IDs to `{path,theme,accent?}`. IDs use letters/digits/underscore/hyphen. Actual PNG bytes, theme `paper` or `dark`. `accent`: `yellow` (default, lesson thresholds) or `coral` (red/orange accent such as #E8643C — the yellow rule never draws it). Source art colors are preserved, not recolored by palette settings.
- `scenes`: list below. Empty is allowed for a technical pass without drawings.

Optional:
- `paths: {work:'work',output:'output',runtime:'runtime'}`: separate job-owned directories. Never put source media inside output.
- `encoder`: `libx264` default; `h264_nvenc` only after actual hardware smoke test.
- `timeout_seconds`: per scene, default 1800; two attempts maximum.
- `protected_intervals`: cover, live UI or shots that must not be overlaid.
- `caption_band: [x,y,width,height]`: no sketch placement may cross it. This is a declared safe area, not OCR detection.
- `subtitle_file`: reviewed SRT copied beside the final export. The pipeline does not burn it implicitly.
- `branding: {logos: []}`: no logos by default. Each optional item: `{path,rect:[x,y,w,h],intervals:[[start,end],...]}`. Rect is a contain-fit box, original proportions preserved. No fixed brand, initials or name.

Scene example (one continuous drawing, two shot sizes):

```json
{
  "id": "Concept01", "start": 30, "end": 330,
  "width": 1280, "height": 720, "theme": "paper",
  "title": "Заголовок сцены", "subtitle": "Шаг 1 → шаг 2 → шаг 3",
  "palette": {"background":"#F8F3EC","ink":"#171713","muted":"#69675F","accent":"#DAA400"},
  "arts": [{"name":"folder","source":"paper","crop":[100,200,400,300],
    "dest":[200,230,400,300],"start":0.2,"duration":3.0,"pen":true,"exclude":[]}],
  "labels": [{"value":"Подпись","x":400,"y":610,"start":3.5,"size":32,"accent":false}],
  "placements": [
    {"start":30,"end":180,"rect":[32,80,1280,720],"radius":22},
    {"start":180,"end":330,"rect":[160,0,1600,900],"radius":22}
  ]
}
```

Art crop `[x,y,w,h]` uses **original PNG pixels**, destination uses panel pixels. Preserve crop aspect ratio. `start`/`duration` must finish inside the scene. Allow a hold after completion (the silhouette settles over another 8% of draw duration). `until` optional seconds controls exit. `exclude` optional source-pixel rectangles removes existing text/branding from the reveal mask without altering the source image. Inspect proof for mask halos and clipping.

`pen:true` draws a moving marker at the active stroke tip; false draws without a visible tool. This is a deterministic stylized marker, not photoreal human hand synthesis. Palette changes panel/text/underline only; the raster remains authentic. Dark artwork must be generated for a dark panel, paper artwork for a light panel.

Optional `titleLayout` (vertical stories, big headlines): `{"size":100,"y":330,"align":"left","x":84,"lineGap?":…,"subtitleSize?":…,"underline?":true}`; `\n` in `title`/`subtitle` makes lines. Without it the lesson header (centred, 43–48 px, y 88) renders exactly as before. A scene may have `"arts": []` — a title-only band over live footage.

Sources may be RGBA: the mask is computed on the image composited over the theme colour (paper #F8F3EC / dark #000), the PNG itself ships untouched. Declare one sheet twice (`theme: paper` and `theme: dark`) when it mixes light and dark quadrants.

Labels have value/x/y/start and optional size/accent/heading/until/align (`center` default, `left`: x is the left edge). Anchors are centered. Long text must be shortened or manually wrapped into separate labels, not shrunk until unreadable. Temporal and geometric validation does not replace visual font QA.

Placements within one scene share its clock; they **do not restart** drawing at shot changes. Placements must not overlap in time, change aspect ratio or cover protected footage/caption band. Enlarge slide/panel within those constraints; speaker-close and live UI are built in the base edit map.

## Raw edit schema

`edit-example.json` illustrates the full structure. Set:
- `video` and segment frame counts with exact sum; `output` new MP4; `work` explicit state directory.
- Each segment: safe unique `id`, positive `frames`, `background` CSS hex or `{center,edge}` radial gradient.
- `audio: {path,in,track:0}` uses source seconds and selected audio track. Must cover segment duration; no guessed padding for missing speech.
- `layers`: back to front, each `{path,kind:'video'|'image',in,rect,fit,radius}`. `in` only for video. `fit` contain/cover; cover anchors at bottom unless `anchor:'center'`.
- Optional `crop:[x,y,w,h]` before fit; `panel:{center,edge}` behind foreground; `key:{color:'0x00ff00',similarity:0.3,blend:0.12}` for green replacement. Tune on hair/clothing, do not assume defaults fit every camera.

For a jump cut, split the segment and advance every source by the matching media offset. For a new shot without an audio cut, continue audio/camera source time. No automatic filler-word removal, no lip-sync prediction. `raw_edit.py` produces a source-to-final `edit-map.json`.

## Captions, notes, inventory and synchronization

```powershell
python -B "$skill/scripts/media_tools.py" inventory "$job/input/camera.mp4" "$job/input/screen.mp4" --output "$job/inventory.json"
python -B "$skill/scripts/media_tools.py" sync-candidate "$job/input/mic.wav" "$job/input/camera.mp4" --reference-start 0 --target-start 2 --search-seconds 20 --sample-seconds 5 --output "$job/sync.json"
python -B "$skill/scripts/media_tools.py" unwrap-notes "$job/notes-source.txt" "$job/notes-readable.txt"
python -B "$skill/scripts/captions.py" "$job/input/reviewed.srt" --font "$job/fonts/hand.ttf" --output "$job/captions.ass" --size 38 --safe-width 1400 --x 960 --y 930 --terms "термин" "задач*"
```

`sync-candidate` returns where a target audio sample matches the reference. It cannot measure video latency. Verify mouth consonants at start/middle/end and apply any measured video offset in raw source `in` values.

`--highlight pill` reproduces the lesson style: a rounded marker plate (`--pill-color`, default #FFD43B) under the FIRST term of each cue, text stays ink-coloured, one event per row (libass width via fontTools, so the plate sits under the word). Terms are literal; a trailing `*` matches word forms (`задач*` → задача, задачей).

Caption burn: add `--video <uncaptioned.mp4> --render <captioned.mp4> --start`. Color highlights of supplied terms are visual accents, **not** claimed word-level synchronization. To animate word-by-word, supply reviewed word timings from a transcript/alignment tool; never divide cue duration evenly and pretend it is speech alignment. Keep complete SRT separately even when burning.

`--regions regions.json` changes caption placement for live UI or alternate shots without shifting speech. Example array: `[{"start":40,"end":62,"x":960,"y":140,"size":36,"safe_width":1200,"ink":"#FFFFFF","accent":"#FFD014"}]`. Intervals are seconds, must not overlap. A cue crossing a region boundary is split in place. Confirm the new region is truly empty; this is not automatic collision detection.

Optional local transcription adapter: `transcribe.py --help`. It requires `faster-whisper` and an existing local model directory, is not part of the mandatory runtime and never silently downloads a model. Without these, use a cloud ASR (e.g. skill `deepgram`) as a draft and save reviewed SRT/word timestamps into the project.

## Batch

```json
{"jobs":[{"id":"Lesson01","config":"lesson-01/project.json"},{"id":"Lesson02","config":"lesson-02/project.json"}]}
```

`batch.py batch.json --start` executes sequentially with independent output/work directories. Default stops on failure; `--continue-on-error` explicitly permits remaining jobs. Touch `STOP` beside the batch manifest or individual project to cancel its owned process tree and preserve checkpoints. Remove STOP yourself after deciding to resume, then run the same command. Cache reuse checks both input and rendered output hashes; changed art/font/timing/code invalidates the clip.

## Deliverables and limits

Output: `<id>.mp4`, first-frame `Preview.jpg`, `manifest.json`, `QA.json`, contact-sheet frames, optional SRT. `technical_pass` checks container/frame clock/color/full decode/audio identity, **not** final editorial approval. Watch the actual MP4 with sound; mark editorial QA only after that. No broken placeholders, fabricated logs or successful-status claims based on a launched subprocess.
