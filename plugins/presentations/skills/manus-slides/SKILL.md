---
name: manus-slides
description: "Full-pipeline slide presentation creator. 25 AI styles (Gemini image generation) + HTML templates. Export to PPTX/PDF/HTML. Replicas of all 26 Manus 1.6 slide themes — use for slides 'в стиле Manus' or theme names Sketch, Whiteboard, Etching, Editorial, Pixel, Vellum, Dossier, Glamour, Cobalt, Onyx, Neon ('сделай слайды как Manus', 'тема Manus')."
type: actionable
---

# Manus Slides

Full-pipeline presentation tool: topic -> outline -> slides -> export (PPTX/PDF/HTML).

Three modes:

1. **Whiteboard** (recommended) — 24 AI styles via Gemini (`gemini-3.1-flash-image-preview` / Nano Banana 2) → PPTX
2. **HTML** — 13 styled templates via `slide_templates.py`, editable, Playwright screenshots → PPTX/PDF
3. **Image** — Gemini generates custom images per slide → PPTX

## Quick Start — Whiteboard Mode

```bash
# Recommend styles for a task
python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py recommend "investor pitch deck for AI startup"

# Create config JSON with slide prompts
cat > slides.json << 'EOF'
{
  "title": "My Presentation",
  "style": "whiteboard",
  "slides": [
    {"id": "slide_01", "prompt": "TITLE in bold: \"My Topic\"\nSUBTITLE: \"Key subtitle\"\nDraw a relevant illustration below."},
    {"id": "slide_02", "prompt": "TITLE: \"Problem Statement\"\nDraw diagram showing the problem with icons and arrows."}
  ]
}
EOF

# Generate all slides
python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py generate slides.json ./output

# Output: ./output/slide_01.png, slide_02.png + presentation.pptx + preview.html
```

## Quick Start — HTML Mode

```bash
echo '[{"title":"Title","summary":"Welcome","slide_template_key":"cerulean"}]' > outline.json
python ~/.claude/skills/manus-slides/scripts/slide_manager.py init "Title" outline.json ./project
python ~/.claude/skills/manus-slides/scripts/slide_export.py html ./project ./presentation.html
```

## AI Styles (24 total via whiteboard_generator.py)

### Manus Originals (7) — Best visual quality

| Style | Description | Best For |
| ----- | ----------- | -------- |
| `vinyl` | Retro poster, vintage 1930s-50s, bold geometric, warm tones | Pitch decks, music, creative |
| `whiteboard` (default) | Marker board in office, conference room | Business, education, internal |
| `grove` | Enchanted fairy forest, pastel watercolor, cute animals | Children, storytelling, wellness |
| `fresco` | Warm urban illustrations, flat design city scenes | Travel, culture, community |
| `easel` | Artist studio, canvas and paints, warm browns | Art, creative, portfolio |
| `diorama` | Pop-up book, 3D paper craft, bright colors | Startup, innovation, fun |
| `chromatic` | Colorful tech explainer, floating 3D objects, rainbow | Tech explainer, education, startup |

### Manus Hybrid (7) — AI-replicated via Gemini

| Style | Description | Best For |
| ----- | ----------- | -------- |
| `sketch` | Chalk/charcoal on dark paper, stick figures, hand-drawn | Science, education, creative |
| `glamour` | Luxury fashion editorial, dark cinematic, golden silk | Fashion, luxury, premium |
| `amber` | Soft organic abstract shapes, muted pastels, calm | Wellness, mindfulness, NGO |
| `arctic` | Cool corporate tech, silver-gray, blurred tech photo | Tech corporate, B2B, SaaS |
| `neon` | Synthwave/80s, dark purple bg, glowing neon elements | Gaming, nightlife, events |
| `patina` | Cave painting/ancient art, ochre stone texture | History, anthropology, heritage |
| `onyx` | Brutalist black, massive white typography, minimal | Philosophy, statement, art |

### Bonus Styles (10)

| Style | Description | Best For |
| ----- | ----------- | -------- |
| `chalkboard` | Green blackboard, chalk writing, university | Education, math, science |
| `notebook` | Moleskine on desk, pen writing, sticky notes | Personal, notes, journal |
| `blueprint` | Technical blue bg, white grid, engineering | Engineering, architecture |
| `glassmorphism` | Frosted glass panels, vibrant gradient bg | Modern UI, SaaS, startup |
| `corporate` | Clean white, navy header, professional grid | Corporate, formal |
| `dark-tech` | Black bg, neon green/cyan accents, terminal | Cybersecurity, dev, hacking |
| `dashboard` | Dark navy, card layout, colored charts | Data, KPIs, analytics |
| `infographic` | White bg, flat icons, colorful statistics | Reports, data viz |
| `watercolor` | Soft watercolor washes, calligraphic text | Art, poetry, invitations |
| `minimal-clean` | Pure white, black text only, max whitespace | Luxury, minimalist |

### Manus 1.6 Image Themes (6) — reverse-engineered from Manus's image-mode slide themes (2026-07-02)

Replicas of Manus 1.6's premium image-mode presentation themes, generated on our Gemini. Reference sample slides: `references/manus-theme-samples/<Theme>__<model>/`. **Full 26-theme Manus catalog (modes, models, palettes, HTML-theme mappings): `references/manus-26-themes.md`.**

| Style | Manus model | Description | Best For |
| ----- | ----------- | ----------- | -------- |
| `etching` | gpt-image | Fine pen-and-ink engraving on cream paper, spaced letterpress serif, delicate crosshatch + grey wash, New-Yorker editorial | Literary, essays, refined reports, thought leadership |
| `editorial` | gpt-image | Split layout: moody editorial photo (left) + dark charcoal panel with big Didone serif + copper rule (right), Kinfolk/Monocle | Brand, magazine, premium overview, strategy |
| `pixel` | gpt-image | Retro late-90s Mac OS window (traffic-lights, Bondi-blue pinstripe desktop, bold grotesque, orange underline) | Product design, tech nostalgia, dev/history, playful tech |
| `vellum` | gpt-image | East-Asian sumi-e ink-wash: rice-paper cream, misty ink mountains + pine, ink-green serif, red seal chop | Mindfulness, philosophy, heritage, calm/wellness |
| `dossier` | gpt-image | Vintage archival flat-lay: aged paper pinned to cork/leather + antique objects (bell, stamps, key, wax seal), navy serif | Hospitality, heritage brands, history, storytelling |
| `sketch-notebook` | nano-banana | Manus 1.6 "Sketch": black ink doodles on cream graph-paper — rounded hand-lettering, cute line characters, doodle icons, monochrome | Habits/lifestyle, friendly explainers, education, personal talks |

> ⚠️ Manus's "Sketch" theme = our `sketch-notebook` (light cream ink-doodle). Our legacy `sketch` (white chalk on DARK paper) is a different look — kept for back-compat. Manus's "Whiteboard" = our `whiteboard`.
> ⚠️ `pixel` footer tags and `dossier`/`vellum` decorative stamps are auto-invented by the model if you don't specify them — put real footer/tag text in the slide prompt to avoid gibberish (standard "specify all text" rule).

### Emulating Manus 1.6 themes — honest limitations

- Manus's **server-side prompts were NOT extracted** (nothing in the 34-MB sandbox binary; model choice + prompts live on Manus's servers). Our STYLES prompts are visual reconstructions from previews + 8-slide samples — **style emulation, not a pixel copy**.
- End-to-end Manus generation was observed live only for **Sketch/nano-banana**; other themes are confirmed via the catalog API + samples.
- Manus's 19 **HTML/react themes**: 6 are covered by our AI-image styles (`glamour`, `amber`, `arctic`, `neon`, `patina`, `onyx`), 9 map onto our HTML template categories + palettes (see `references/manus-26-themes.md`), 4 need a new photo-based HTML template (Emerald, Mist, Linen, Mahogany) — no 1:1 path today.
- Exact "as Manus" output is only possible via Manus itself (tool `slides`, export `manus-export-slides manus-slides://<version_id>`).

## Image Model Selection (env `MANUS_SLIDES_MODEL`)

`whiteboard_generator.py` defaults to **`gemini-3.1-flash-image-preview`** (Nano Banana 2 — fast, cheap, excellent Cyrillic). Override per run for premium decks:

| `MANUS_SLIDES_MODEL=` | Marketing name | When |
| --- | --- | --- |
| *(unset — default)* | Nano Banana 2 | Default; fast, great text, cheapest |
| `nano-banana-pro-preview` | Nano Banana Pro | Premium: richest detail, best incidental/small text (this is what Manus uses) |
| `gemini-3-pro-image` | Nano Banana Pro | Same tier; even localizes decorative text to Cyrillic |
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | Cheapest, quick drafts |

```bash
# premium deck with Nano Banana Pro:
MANUS_SLIDES_MODEL=nano-banana-pro-preview python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py generate slides.json ./output editorial
```
> ⚠️ `gemini-3.5-flash` is **text-only** (no image output) — do NOT set it here. It's the newest flash but generates text, not slide images. (Verified via API 2026-07-02.)

### Production notes for the 5 Manus themes (validated on multi-slide decks, 2026-07-02)

The refined prompts are hardened against the #1 failure mode: **the model invents gibberish in any element the style declares mandatory but the slide content leaves empty** (subtitle, footer tags, "Est." line). Subtitle / footer / accent lines are now CONDITIONAL — omitted (not invented) when you don't supply them. Still, for full control, **specify every piece of on-slide text** in the prompt.

- **`editorial`** — auto-switches layout: title/section slides → dark photo-split; content slides (lists/diagrams) → light cream "paper" layout (matches Manus). Hint it by starting a slide prompt with `TITLE SLIDE.` or `CONTENT SLIDE.`.
- **`pixel`** — give footer tags explicitly (`Footer tags: "Агенты · Автономность · 2026"`) and a window label; if omitted they're dropped cleanly (no more garbled bar). Great for product-design / tech-nostalgia decks.
- **`vellum`** — do NOT wrap terms in quotes in the prompt (the model renders the quote marks literally on the slide). Seal chop is auto-anchored under the title / bottom-right.
- **`dossier`** — the red `Est. YYYY` line is an opt-in signature: add `RED ITALIC ACCENT LINE: "Est. 2026"` on the title slide; omit on content slides. Don't quote list lead-ins. Lists ≤5 items and 2×3 comparisons hold best; props auto-arrange around the edges.
- **`etching`** — production-ready as-is; footer running caption + roman numeral render cleanly only when you specify them.
- Reference look for all 7 Manus image themes (incl. `whiteboard`/`sketch`): `references/manus-theme-samples/<Theme>__<model>/`.

## HTML-Only Styles (13 via slide_templates.py)

`cerulean`, `cobalt`, `emerald`, `basalt`, `mist`, `sand`, `linen`, `alabaster`, `quartz`, `mahogany`, `ginkgo`, `sunset`, `lavender`

## Scripts

All in `~/.claude/skills/manus-slides/scripts/`:

### whiteboard_generator.py (AI Mode)

Generates slides using Gemini Image (`gemini-3.1-flash-image-preview` / Nano Banana 2) in any of 24 AI styles.

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `generate` | `generate <config.json> <output_dir> [style]` | Generate all slides from config |
| `test` | `test "<prompt>" <output_dir>` | Generate single test slide |
| `pptx` | `pptx <image_dir> <output.pptx>` | Package images into PPTX |
| `html` | `html <image_dir> <output.html>` | Create navigable HTML preview |
| `styles` | `styles` | List all 24 AI styles |
| `recommend` | `recommend "<task description>"` | Suggest best styles for a task |

**Config format:**
```json
{
  "title": "Presentation Title",
  "style": "whiteboard",
  "slides": [
    {
      "id": "slide_01",
      "prompt": "Content description — what to draw/write"
    }
  ]
}
```

**Dependencies:** `pip install google-genai python-dotenv Pillow python-pptx`

## Post-processing exec-sketch decks — production gotchas (learned in prod)

A logo is composited AFTER generation (the prompt no longer reserves an empty corner — see the white-box fix below). Hard-won lessons when assembling/maintaining real decks:

- **Logo is a separate composite, not part of the prompt.** Keep a logo PNG with alpha (e.g. an "H" mark) and `img.alpha_composite()` it post-gen. Position is a design choice — be consistent across the WHOLE deck. Standard for YourFirstName's ClientCorpN decks = **top-RIGHT**: right edge ≈ `0.976*W`, top `0.038*H`, height `0.072*H` → `x = W - lw - int(W*0.024); y = int(H*0.038)`. (Top-left works too but clips left-aligned titles — see below.)
- **Keep the pre-logo RAW PNGs** (`exec_slides_raw/`, no logo). To move the logo to the other side / resize / rebrand, re-run the composite on raws — never try to "erase" a baked-in logo.
- **⭐ WHITE-BOX ROOT CAUSE = the prompt itself.** The old `exec-sketch` prompt said *"Leave the very top-left corner clean and empty (… a logo is composited there later)"* — telling Gemini to "leave a corner empty" makes it literally draw an **empty white box/container** there. FIXED at the prompt level (2026-06-14): the style string now says the cream bg *"COMPLETELY covers all four corners — NO white rectangles, NO empty blocks, NO containers, NO reserved boxes in any corner"* and no longer reserves a logo corner. New decks won't have the box. The logo is composited on top of the cream afterwards regardless.
  - **For decks generated with the OLD prompt** (box already baked in): fix ONLY a real box, never a title. Sample slide bg (median of edge points away from corners) and fill the corner with it **only if**: `white_px > 1500 AND dark_px < 300` inside `[0,0, 0.14W, 0.15H]` (`>244` all-channels = white; `<120` all-channels = dark text). A *left-aligned title* gives ~200-400 "white" px (antialiasing) + lots of dark px — DO NOT fill, or you erase the first word ("2012:" → cut).
  - Also keep using the anti-box wording in any **custom `EXEC_PREFIX`** you copy into a deck's `_common.py` (the reference decks already do).
- **Build a deck from full-bleed PNGs + ported notes (no LibreOffice):** `slide.shapes.add_picture(png,0,0,width=SW,height=SH)` on blank 13.333×7.5" layout; port notes by position from a source pptx (`deepcopy` the BODY notes placeholder if target has none); export to PDF via **PIL** `imgs[0].save(out,save_all=True,append_images=imgs[1:],resolution=150)`.
- **Verify without poppler/LibreOffice:** render PDF pages with **PyMuPDF** (`fitz.open(p)[i].get_pixmap(dpi=80)`); detect logo side via indigo-mask `(b>110)&(b-r>40)&(b-g>30)&(r<140)` count in top-left vs top-right band.
- **Cyrillic:** `markitdown` shows mojibake in the terminal (cp1251 console) — the file is fine UTF-8. Verify slide text **visually** (text is baked into images), not by terminal dump.

## Modular production pattern for big decks (build.py + notes.py + assemble.py) ⭐

For real multi-slide decks (30–64 slides) WITH speaker notes, the maintainable scaffold is the **modular deck pattern**, not one giant config JSON. Reference decks: `presentations/<your-conference-deck>/`, `presentations/clientcorp-webinar2-practice/`.

```
deck/
├── _common.py        # shared EXEC_PREFIX + make_client() + gen_slide() + run_generation()
├── assemble.py       # pptx from exec_raw/*.png + notes.py; supports --swap-speaker
└── slides/
    ├── build.py      # SLIDES = {n: '''english layout + "русский текст в кавычках"'''}
    ├── notes.py      # NOTES  = {n: '''разговорный спикерноут'''}
    └── exec_raw/      # slide_NN.png 1280×720 (gemini-3-pro-image-preview / nano-banana-pro)
```

- **`run_generation(SLIDES, RAW)` skips PNGs already >100 KB → idempotent.** Regenerate one slide: `python slides/build.py --only=5,12`. Edit a slide's text in `build.py`, delete its PNG, re-run `--only=N`.
- **EXEC_PREFIX lives once in `_common.py`** (cream `#F1F3F5`, marker icons indigo `#3B5BDB` / copper `#C77B30`; anti-corner-box, anti-Latin-lookalike Cyrillic «render И/С/Н as Cyrillic, NOT I/C/H», NO duplicates, render each element exactly once). Per-slide prompt holds ONLY content.
- **`python assemble.py slides [--swap-speaker]`** lays each `slide_NN.png` full-bleed on a blank 16:9 pptx and ports `NOTES[n]` into the notes slide (clone BODY notes placeholder via `deepcopy` when target has none). `--swap-speaker` overlays a ready speaker card onto `slide_02`.
- **Insert / reorder slides WITHOUT regenerating everything (remap):** keep the old build as `build_v1.py`; new `build.py` does `from build_v1 import SLIDES as OLD`, maps old→new index (e.g. shift keys `≥11` by `+1`) and adds `NEW = {...}`. Then shift PNGs to match — **descending** `mv slide_30→31 … slide_11→12` — delete only changed numbers, and `--only=` the new/changed slides. Same trick for `notes.py` (programmatic remap script). Adds a mid-deck slide in ~30 s of gen instead of 11 min.
- **PowerPoint lock:** if the target .pptx is open, `assemble` raises `PermissionError`. Fall back to a new name (`import assemble; assemble.OUT_NAMES['slides']='..._обновлено.pptx'; assemble.main('slides')`) and tell the user to close the original.
- **QA before delivery:** montage `exec_raw/*.png` into 2–3 contact sheets (PIL, 4×4) and eyeball the whole deck.

### Slide text + speaker notes: NO infobiz, human language ⭐ (YourFirstName's hard rule)
On-slide text AND speaker notes must read like a human, not an info-business coach. Strip on every pass:
- Empty value-less framing: «Инструмент мощный, но толк только если правильно», «честная рамка, чтобы не разочароваться».
- Hype adjectives: «прям клад», «огонь», «золото», «кайф», vague «в десять раз».
- Clichés: «лучшее время начать было…», «дисциплина быстрых циклов / Shipped > Perfect», «золотое правило».
- Garbled idioms: «не молотком по гвоздику» → plain («простую — лёгкой моделью, сложную — мощной»).
Replace each with a concrete, useful statement or cut it. Bottom-marker lines should teach or instruct, not motivate.

### Speaker-notes voice for YourFirstName's decks
Write `notes.py` in the speaker's real spoken voice — keep a voice-profile file (e.g. `~/.claude/skills/tg-post/references/user-spoken-voice.md`) with concrete markers: metronome/filler openers for transitions, favourite connectives, peer-address forms, homely analogies, self-irony on glitches. Reference notes: `presentations/clientcorp-webinar2-practice/slides/notes.py`.

### slide_manager.py (HTML Mode Core)

State machine for HTML-based projects. Manages `slide_state.json`.

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `init` | `init <title> <outline.json> <output_dir>` | Create project |
| `modify` | `modify <project_dir> <operation> <data_json>` | Add/delete/edit/split/reorder |
| `present` | `present <project_dir>` | List active slides |
| `notes` | `notes <project_dir> <slide_id> <text>` | Update speaker notes |

### slide_templates.py (HTML Templates)

13 named styles generating self-contained 1280x720 HTML slides.

### slide_export.py (HTML Export)

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `html` | `html <project_dir> [output.html]` | Combine into navigable HTML |
| `pdf` | `pdf <project_dir> [output.pdf]` | Screenshots → PDF |
| `pptx` | `pptx <project_dir> [output.pptx]` | Screenshots → PPTX |

## Style Recommendation Guide

| Task Type | Recommended Styles |
| --------- | ------------------ |
| Investor pitch deck | `vinyl`, `diorama`, `chromatic` |
| Corporate / B2B | `whiteboard`, `arctic`, `corporate` |
| Education / lectures | `chalkboard`, `sketch`, `whiteboard` |
| Tech / engineering | `blueprint`, `dark-tech`, `arctic` |
| Creative / art | `easel`, `watercolor`, `onyx` |
| Startup / product | `glassmorphism`, `chromatic`, `diorama` |
| Data / analytics | `dashboard`, `infographic`, `corporate` |
| Luxury / fashion | `glamour`, `minimal-clean`, `onyx` |
| Children / wellness | `grove`, `amber`, `watercolor` |
| History / culture | `patina`, `fresco`, `easel` |
| Gaming / events | `neon`, `dark-tech`, `glassmorphism` |

## Prompt Engineering

Quality depends entirely on prompt quality. Key rules:

### Structure
```
TITLE in large bold marker: "Заголовок слайда"
SUBTITLE: "Подзаголовок"

[Layout description with specific content]

At the bottom: "Key takeaway or footer text"
```

### Content Elements

- **Lists**: "Numbered list: 1. First item 2. Second item"
- **Diagrams**: "Draw a flowchart: Box A → Box B → Box C"
- **Charts**: "Draw a bar chart: Year 1: 20M, Year 2: 100M"
- **Tables**: "Draw a table: Feature | Status | Priority"
- **Icons**: "Draw a shield icon", "a brain icon", "a clock icon"
- **Highlights**: "In a green box:", "In a red circle:", "Underlined in blue:"
- **Comparisons**: "LEFT side: ... RIGHT side: ..."
- **Colors**: black (headers), blue (subtitles), green (positive), red (critical), purple (accents)

### Example Prompt

```
TITLE in large bold black marker: "8-слойная архитектура"
SUBTITLE in blue marker: "Снизу вверх — от души до интерфейса"

Draw a vertical stack of 8 colored horizontal layers:
Layer 8 (gray): "ADMIN PANEL — Control UI"
Layer 7 (cyan): "CHANNELS — Telegram, Slack"
Layer 6 (orange): "PROACTIVITY — Heartbeat, Cron"
Layer 5 (green): "TOOLS — Calendar, Email, Search"
Layer 4 (blue): "BRAIN — LLM Router"
Layer 3 (purple): "MEMORY — Qdrant, Hybrid Search"
Layer 2 (teal): "DATA — PostgreSQL, APIs"
Layer 1 (red): "SOUL — Constitution, Values"

Draw small icons next to each layer.
On the right: vertical arrow labeled "Уровень абстракции"
```

## Mode Selection Guide

| Need | Mode | Why |
| ---- | ---- | --- |
| Pitch deck, investor presentation | **Whiteboard** (`vinyl`, `diorama`) | Visually impressive, unique |
| Internal docs, editable deck | **HTML** | Easy to modify, no API calls |
| Marketing, creative deck | **Whiteboard** (`glamour`, `chromatic`) | Custom AI visuals per slide |
| Quick prototype | **HTML** | Fastest, no API calls needed |
| Conference talk | **Whiteboard** (`whiteboard`, `sketch`) | Memorable visual style |
| Data presentation | **Whiteboard** (`dashboard`, `infographic`) | Clear data visualization |

## Unified Pipeline (Whiteboard Mode) — FOLLOW THIS

When user asks to create a presentation ("сгенерь презу", "create slides", "make a deck"), follow these steps:

### Step 1: UNDERSTAND
Clarify topic, audience, goal, language. If user gave a clear topic — proceed without asking.

### Step 2: STYLE
Run `python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py recommend "<topic>"` to get top style suggestions. Pick the best one or let user choose. Default: `whiteboard`.

### Step 3: OUTLINE
Generate a JSON config with detailed visual prompts. Write it to a temp file:
```json
{
  "title": "Presentation Title",
  "style": "whiteboard",
  "slides": [
    {"id": "slide_01", "prompt": "TITLE in large bold marker: \"Title\"\nSUBTITLE: \"Subtitle\"\nDraw relevant illustration below."},
    {"id": "slide_02", "prompt": "TITLE: \"Problem\"\nDraw diagram showing..."}
  ]
}
```
**Rules for prompts:**
- Each prompt must be 3-5 sentences minimum with SPECIFIC visual details
- Use Prompt Engineering section below for structure (TITLE, SUBTITLE, layout, colors)
- First slide = title, last slide = summary/CTA
- Include real data, numbers, examples where relevant
- 8-12 slides is optimal (no fewer than 6, no more than 15)

### Step 4: REVIEW
Show the outline to user as a formatted list:
```
1. Title Slide — "Presentation Title"
2. Problem — diagram showing market gap
3. Solution — architecture overview
...
```
Wait for OK or edits. If user says "OK" / "давай" / "go" — proceed. If edits requested — update config and re-show.

### Step 5: GENERATE
```bash
python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py generate <config.json> <output_dir> [style]
```
This auto-creates `presentation.pptx` + `preview.html`.

### Step 6: CHECK
After generation, review results. If any slides failed or look bad (user reports), proceed to Step 7.

### Step 7: REGENERATE (if needed)
```bash
python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py regenerate <config.json> <output_dir> <slide_id> [style]
```
This deletes the old image, regenerates, and rebuilds PPTX + HTML.

### Step 8: SPEAKER NOTES (optional)
If user wants speaker notes ("добавь заметки докладчика", "add speaker notes"):
1. Generate notes as JSON: `[{"index": 0, "notes": "Welcome everyone..."}, ...]`
2. Save to `notes.json`
3. Run: `python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py notes-pptx <image_dir> <output.pptx> <notes.json>`

### Step 9: DELIVER
Inform user:
- PPTX: `<output_dir>/../presentation.pptx`
- HTML preview: `<output_dir>/../preview.html`
- Individual slides: `<output_dir>/slide_01.png`, `slide_02.png`, ...

## Research Mode

When the topic needs real data ("с актуальными данными", statistics-heavy topic, market analysis):

1. Use **WebSearch** to find current facts, statistics, trends
2. Collect key numbers and sources
3. Incorporate real data into slide prompts at Step 3 (OUTLINE)
4. Example: instead of "Draw a bar chart showing growth" → "Draw a bar chart: 2023: $150B, 2024: $185B, 2025: $220B (source: Gartner)"

## URL Source Mode

When user provides a URL ("сделай презу по этой статье"):

1. Use **WebFetch** to read the URL content
2. Extract key points, data, structure
3. Use this content to generate the outline at Step 3
4. Reference source in the title slide

## Change Style Flow

When user says "поменяй стиль на X" / "change style to X":

1. Update the `"style"` field in config.json
2. Delete all existing slide images in output_dir
3. Re-run `generate` with new style
4. All 24 AI styles are available (see AI Styles section below)

## Legacy Pipeline (HTML Mode)

### HTML Pipeline
1. **Understand** → 2. **Outline** → 3. **Confirm**
4. **Init** — `slide_manager.py init`
5. **Generate** — Write HTML per slide using templates
6. **Export** — `slide_export.py html/pdf/pptx`

## Project Structure

### Whiteboard Mode
```
my-presentation/
├── slides.json           # Config with prompts + style
├── generated/
│   ├── slide_01.png
│   ├── slide_02.png
│   └── ...
├── presentation.pptx
└── preview.html
```

### HTML Mode
```
my-presentation/
├── slide_state.json
├── slides/
│   ├── slide_001.html
│   └── ...
├── presentation.html
└── presentation.pptx
```
