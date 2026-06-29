---
name: manus-slides
description: "Full-pipeline slide presentation creator. 24 AI styles (Gemini image generation) + 13 HTML-only styles. Export to PPTX/PDF/HTML."
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
