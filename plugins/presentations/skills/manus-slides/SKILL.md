---
name: manus-slides
description: "Слайды: 32 AI-стиля, HTML-шаблоны, темы Manus, рисованный exec-sketch (светлый/тёмный, ноутсы по ID). Триггеры: «презентация», «слайды», «скетчевая преза». НЕ deck-stage→slides"
type: actionable
metadata:
  version: 2.0.0
  updated: 2026-09-23
  reuses: image-generation, openai-dalle, sketch-course-video
---

# Manus Slides

Full-pipeline presentation tool: topic -> outline -> slides -> export (PPTX/PDF/HTML).

Four routes, equal — pick by the Mode Selection Guide below:

1. **Whiteboard** (default for «сделай презентацию по теме») — 32 AI styles via Gemini (`gemini-3.1-flash-image-preview` / Nano Banana 2) → PPTX
2. **Exec-sketch** — `exec_sketch.py`: whole-slide hand-drawn visual argument, light/dark/classic palettes, full speaker notes bound by slide ID, strict PPTX/PDF/offline HTML/TXT export + QA, motion handoff for video
3. **HTML** — 32 templates in 8 categories via `slide_templates.py`, editable, Playwright screenshots → PPTX/PDF
4. **Image** — Gemini generates custom images per slide → PPTX

## Где живут джобы и что нужно для запуска

- Навык только читается. `exec_sketch.py` сам отказывается писать в `~/.claude`, `~/.codex`,
  `~/.agents` и в папку навыка — джоба живёт в своей папке, например
  `~/presentations/<ГГГГ-ММ-ДД>-<slug>/` (на диске, где есть место). Шаблон и примеры сначала
  копировать туда.
- Зависимости: `pip install -r <skill>/scripts/requirements.txt` (движок: python-pptx, Pillow,
  PyMuPDF, pytest), `requirements-generate.txt` (мост `exec_generate.py`: openai, google-genai,
  python-dotenv), `requirements-legacy.txt` (старые скрипты + Playwright). `<skill>` — папка, куда
  установлен навык, обычно `~/.claude/skills/manus-slides`.
- Ключи — из окружения или из `~/.claude/.credentials.master.env`: `OPENAI_API_KEY` для
  `gpt-image-*`, `GOOGLE_API_KEY` для `gemini-*`. Движок `exec_sketch.py` ключей не касается,
  платные вызовы живут только в `exec_generate.py` и `whiteboard_generator.py`. В интерактивной
  сессии генерировать по лестнице моделей; в автономных прогонах (крон, боты, рой агентов) тратить
  платный ключ — только с явного разрешения.
- Тесты (41, без сети и платных вызовов — провайдер подменяется):
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest <skill>/tests -q -p no:cacheprovider`.
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD` отгораживает прогон от глобально установленных плагинов pytest
  (например, плагин hydra со старым antlr падает с «ATN version 3») — это среда, не навык.
- Windows + установленный PowerPoint (+ `pywin32`) — открыть PPTX и выгрузить слайды настоящим
  приложением (только чтение):

  ```python
  import win32com.client, pythoncom; pythoncom.CoInitialize()
  app = win32com.client.DispatchEx('PowerPoint.Application')
  pres = app.Presentations.Open(r'<job>/export/presentation.pptx', True, False, False)  # ReadOnly, no window
  for i in range(1, pres.Slides.Count + 1):
      pres.Slides(i).Export(rf'<job>/ppt-render/{i:02d}.png', 'PNG', 1920, 1080)
  pres.Close(); app.Quit()
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
| Course / webinar deck, hand-drawn light+dark, full notes, maybe video later | **Exec-sketch** (`exec-sketch-light-calm` / `-dark-calm`) | One drawn argument per slide, notes bound by ID, strict QA, motion handoff |
| Business deck in the classic exec style (clean type + hand-drawn marker icons) | **Exec-sketch** `exec-sketch-classic`, or the modular pattern for an existing deck | Same look as the `exec-sketch` AI style |
| Fully editable charts or dense legal/number tables | **HTML** or native pptx tooling | Exec-sketch text is raster |

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

## Quick Start — Exec-sketch Mode

```bash
S=~/.claude/skills/manus-slides; J=~/presentations/2026-09-23-my-deck      # <YYYY-MM-DD>-<slug>
mkdir -p $J && cp $S/templates/deck.json $J/          # fill ids, titles, text, visual, notes (references/manifest.md)
python -B $S/scripts/exec_sketch.py plan $J/deck.json --out $J/prompts
# proof first: ONE light + ONE dark slide, look at them, only then the batch
python -B $S/scripts/exec_generate.py $J/deck.json --prompts $J/prompts --ids intro,loop      # paid; binds each image
python -B $S/scripts/exec_generate.py $J/deck.json --prompts $J/prompts                      # the rest (unbound)
python -B $S/scripts/exec_sketch.py build $J/deck.json --out $J/export-v1                    # NEW empty dir
python -B $S/scripts/exec_sketch.py qa $J/deck.json --out $J/export-v1
```

Then read EVERY slide at full size (Cyrillic, one argument, arrows, margins), all notes, and the
PPTX in PowerPoint (snippet above) when available. Offline demo without any API: copy `examples/`
(or `examples/improved/`) into a job and `build` it — both are already bound to the original
generated slides (`improved/` = the same two slides after the 23.09.2026 proof, gpt-image-2.5-sunburst).

## Quick Start — HTML Mode

```bash
echo '[{"title":"Title","summary":"Welcome","slide_template_key":"professional-title"}]' > outline.json   # keys: slide_templates.py list
python ~/.claude/skills/manus-slides/scripts/slide_manager.py init "Title" outline.json ./project
python ~/.claude/skills/manus-slides/scripts/slide_export.py html ./project ./presentation.html
```

## AI Styles (32 total via whiteboard_generator.py)

> `len(STYLES) == 32`, `styles` prints all 32 in five groups (the last one — Production:
> `exec-sketch`, `clean-marker`). HTML templates are separate: 32 in `slide_templates.py`.

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

### Manus Hybrid (7) — стили по мотивам Manus, рендер на Gemini

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

### Manus 1.6 Image Themes (6) — стили по мотивам image-режима Manus (2026-07-02)

Наши промпт-стили, повторяющие внешний вид image-тем Manus 1.6; рендер идёт на Gemini. Образцы слайдов для сверки: `references/manus-theme-samples/<Theme>__<model>/`. **Карта 26 тем (режимы, модели, палитры, соответствие HTML-темам): `references/manus-26-themes.md`.**

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

### Production styles (2)

| Style | Description | Best For |
| ----- | ----------- | -------- |
| `exec-sketch` | Деловой слайд на светлом фоне `#F1F3F5` во весь кадр (углы залиты — никаких белых прямоугольников), Manrope/Inter, тёмный индиго `#0B1021` в заголовках, маркерные иконки индиго `#3B5BDB` и медь `#C77B30`. Алиасы: `exec`, `business-sketch` | Деловые деки и корпоративные вебинары — см. «Post-processing exec-sketch decks» ниже. Тот же префикс лежит в `references/prompts/classic-prefix.txt` и = палитра `exec-sketch-classic` движка `exec_sketch.py` |
| `clean-marker` | Чистый белый холст без комнаты и рамки доски, контент нарисован толстым маркером: чёрный в заголовках, синий в подзаголовках, цветные акценты | Когда нужен маркерный look без интерьера `whiteboard` |

### Что даёт эмуляция тем Manus 1.6 и где её предел

- Наши STYLES-промпты собраны по внешнему виду: превью тем плюс 8-слайдовые образцы. Это **эмуляция стиля, а не точная копия** — совпадения слайд-в-слайд не будет.
- Живьём генерация в Manus прогонялась только для **Sketch/nano-banana**; остальные темы сверялись по образцам слайдов.
- Из 19 **HTML/react-тем** Manus: 6 закрываются нашими AI-image стилями (`glamour`, `amber`, `arctic`, `neon`, `patina`, `onyx`), 9 ложатся на наши HTML-шаблоны и палитры (см. `references/manus-26-themes.md`), под 4 (Emerald, Mist, Linen, Mahogany) нужен новый photo-based HTML-шаблон — готового соответствия нет.
- Результат «ровно как в Manus» получается только в самом Manus.

## Image Model Selection (env `MANUS_SLIDES_MODEL`)

`whiteboard_generator.py` defaults to **`gemini-3.1-flash-image-preview`** (Nano Banana 2 — fast, cheap, excellent Cyrillic). Override per run for premium decks:

| `MANUS_SLIDES_MODEL=` | Marketing name | When |
| --- | --- | --- |
| *(unset — default)* | Nano Banana 2 | Default; fast, great text, cheapest |
| `nano-banana-pro-preview` | Nano Banana Pro | Premium: richest detail, best incidental/small text |
| `gemini-3-pro-image-preview` | Nano Banana Pro | Same tier (canonical id in `config/models.md`); even localizes decorative text to Cyrillic |
| `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite | Cheapest, quick drafts |

```bash
# premium deck with Nano Banana Pro:
MANUS_SLIDES_MODEL=nano-banana-pro-preview python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py generate slides.json ./output editorial
```
> ⚠️ `gemini-3.5-flash` is **text-only** (no image output) — do NOT set it here. It's the newest flash but generates text, not slide images. (Verified via API 2026-07-02.)
>
> Top rung of the image ladder (`rules/dont-do.md` #11) is **`gpt-image-2.5-sunburst`** — not via this
> script. For exec-sketch slides it is the default of `exec_generate.py` (cleanest Cyrillic in the
> 23.09.2026 proof, ~$0.04 per 1920×1088 slide). When one character must stay the same across a
> series, use skill `openai-dalle` directly: `input_fidelity` and up to 16 references.
>
> A non-16:9 answer is letterboxed with the image's own edge colour (`ImageOps.pad`), not
> stretched. `styles`/`recommend`/`pptx`/`notes-pptx`/`html` need neither a key nor the Gemini SDK —
> it loads lazily, only for an actual generation.

### Production notes for the 5 Manus themes (validated on multi-slide decks, 2026-07-02)

The refined prompts are hardened against the #1 failure mode: **the model invents gibberish in any element the style declares mandatory but the slide content leaves empty** (subtitle, footer tags, "Est." line). Subtitle / footer / accent lines are now CONDITIONAL — omitted (not invented) when you don't supply them. Still, for full control, **specify every piece of on-slide text** in the prompt.

- **`editorial`** — auto-switches layout: title/section slides → dark photo-split; content slides (lists/diagrams) → light cream "paper" layout (matches Manus). Hint it by starting a slide prompt with `TITLE SLIDE.` or `CONTENT SLIDE.`.
- **`pixel`** — give footer tags explicitly (`Footer tags: "Агенты · Автономность · 2026"`) and a window label; if omitted they're dropped cleanly (no more garbled bar). Great for product-design / tech-nostalgia decks.
- **`vellum`** — do NOT wrap terms in quotes in the prompt (the model renders the quote marks literally on the slide). Seal chop is auto-anchored under the title / bottom-right.
- **`dossier`** — the red `Est. YYYY` line is an opt-in signature: add `RED ITALIC ACCENT LINE: "Est. 2026"` on the title slide; omit on content slides. Don't quote list lead-ins. Lists ≤5 items and 2×3 comparisons hold best; props auto-arrange around the edges.
- **`etching`** — production-ready as-is; footer running caption + roman numeral render cleanly only when you specify them.
- Reference look for all 7 Manus image themes (incl. `whiteboard`/`sketch`): `references/manus-theme-samples/<Theme>__<model>/`.

## HTML Templates (32 via slide_templates.py)

8 categories × 4: `landing-*`, `portfolio-*`, `event-*`, `dashboard-*`, `minimal-*`, `dark-*`,
`professional-*`, `creative-*` — exact keys: `slide_templates.py list`. An unknown
`slide_template_key` silently falls back to `professional-content`.

The 13 Manus HTML theme names (`cerulean`, `cobalt`, `emerald`, `basalt`, `mist`, `sand`, `linen`,
`alabaster`, `quartz`, `mahogany`, `ginkgo`, `sunset`, `lavender`) are NOT template keys: `styles`
lists them for orientation; map each to a category + palette via `references/manus-26-themes.md`.

## Scripts

All in `~/.claude/skills/manus-slides/scripts/`:

### whiteboard_generator.py (AI Mode)

Generates slides using Gemini Image (`gemini-3.1-flash-image-preview` / Nano Banana 2) in any of 32 AI styles (+13 Manus HTML theme names for orientation, see HTML Templates).

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `generate` | `generate <config.json> <output_dir> [style]` | Generate all slides from config |
| `test` | `test "<prompt>" <output_dir>` | Generate single test slide |
| `pptx` | `pptx <image_dir> <output.pptx>` | Package images into PPTX |
| `html` | `html <image_dir> <output.html>` | Create navigable HTML preview |
| `styles` | `styles` | List all 32 AI styles (+ the 13 Manus HTML theme names) |
| `recommend` | `recommend "<task description>"` | Suggest best styles for a task |
| `regenerate` | `regenerate <config.json> <output_dir> <slide_id> [style]` | Перегенерировать ОДИН слайд + пересобрать PPTX/HTML (Step 7); без `[style]` — стиль из config |
| `notes-pptx` | `notes-pptx <image_dir> <output.pptx> <notes.json>` | PPTX со спикер-ноутами (Step 8) |

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

⚠️ Do not feed prompts from `exec_sketch.py plan` into `whiteboard_generator.py test/generate`: it
prepends its own style prefix (double, contradicting instructions — its palette vs the manifest's)
and resizes to 1280×720. Exec-sketch art goes through `exec_generate.py`.

### exec_sketch.py (Exec-sketch engine, offline)

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `plan` | `plan <deck.json> --out <prompts_dir>` | Writes `<id>.txt` prompt per slide + `plan.json`; generates nothing |
| `bind` | `bind <deck.json> --id <id> --image <png> --provider <model>` | Re-encodes to a true PNG (strips EXIF), stores `media/<id>-<sha16>.png`, writes the binding INTO the manifest |
| `build` | `build <deck.json> --out <new_dir>` | PPTX (art + separate logo/QR/photo shapes + full notes), PDF, offline HTML, `slides/*.png`, contact sheet, `speaker-notes.txt`, `teleprompter.txt`, `motion-handoff.json`, `build-manifest.json`, `qa.json` |
| `qa` | `qa <deck.json> [--out <dir>]` | IDs, hashes, stale bindings, notes inside PPTX, layer counts, PDF pages |

Refuses: a non-empty `--out`, writes into `~/.claude`/`~/.codex`/`~/.agents`/the skill, unbound or stale slides.
Details: `references/manifest.md`, `references/production.md`.

### exec_generate.py (plan → model → bind, PAID)

`exec_generate.py <deck.json> [--prompts <dir>] [--ids a,b] [--model gpt-image-2.5-sunburst|gemini-3.1-flash-image-preview] [--art <dir>] [--parallel 4] [--no-bind]`
— the prompt is always the manifest's current one; `--prompts` (plan output) is only cross-checked and
refused when stale. Default selection: every unbound or stale slide. Saves `art/<id>.png` (true PNG;
1920×1088 trimmed to 1080) and `art/<id>.json` (model, prompt sha, image sha, returned size, usage).
Reuses art only when the sidecar matches this prompt and the file is unchanged; art drawn for an older
prompt goes to `art/superseded/` and is redrawn; a file without sidecar is refused (bind it by hand).
All reuse decisions happen before the first paid call. The binding records the model that drew it.
Gemini returns ~1376×768: the engine letterboxes it (warning in `qa`), never stretches. A missing
`OPENAI_API_KEY`/`GOOGLE_API_KEY` is a loud refusal, not an empty result.

### build_visual_prompt.py (cinematic prompt constructor)

Assembles an image prompt in five layers — optics → movement → subject → light → style last.
Flags: `--subject --role --content --fov --size --move --light --dof --color-temp --texture --style
--aspect --still --text --blocking --gaze --facing --first-frame-lock --no-anti-drift --json --lenses`.

```bash
python -B ~/.claude/skills/manus-slides/scripts/build_visual_prompt.py --subject "A folder becoming an application" --still --aspect 16:9
python -B ~/.claude/skills/manus-slides/scripts/build_visual_prompt.py --lenses
```

For photographic/cinematic slide art and covers; the exec-sketch prefix does not need it.

### slide_manager.py (HTML Mode Core)

State machine for HTML-based projects. Manages `slide_state.json`.

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `init` | `init <title> <outline.json> <output_dir> [mode=html]` | Create project |
| `modify` | `modify <project_dir> <operation> <data_json>` | Add/delete/edit/split/reorder |
| `state` | `state <project_dir>` | Print project state |
| `update-states` | `update-states <project_dir> <updates_json>` | Batch status update |
| `present` | `present <project_dir>` | List active slides |
| `notes` | `notes <project_dir> <slide_id> <text>` | Update speaker notes |

### slide_templates.py (HTML Templates)

32 templates in 8 categories generating self-contained 1280x720 HTML slides: `list`, `categories`,
`get <template_key> <data_json>`. Templates pull Tailwind from a CDN and Google Fonts — for
offline/air-gapped delivery use the exec-sketch route.

### slide_export.py (HTML Export)

| Command | Usage | Description |
| ------- | ----- | ----------- |
| `screenshots` | `screenshots <project_dir>` | PNG per slide into `<project_dir>/screenshots/` (Playwright Chromium) |
| `html` | `html <project_dir> [output.html]` | Combine into navigable HTML |
| `pdf` | `pdf <project_dir> [output.pdf]` | Screenshots → PDF |
| `pptx` | `pptx <project_dir> [output.pptx]` | Screenshots → PPTX |

CLI reference for all five legacy scripts: `references/legacy-workflow.md`.

## Post-processing exec-sketch decks — production gotchas (whiteboard_generator / `_common.py`)

A logo is composited AFTER generation (the prompt no longer reserves an empty corner — see the white-box fix below). Hard-won lessons when assembling/maintaining real decks:

- **Logo is a separate composite, not part of the prompt.** Keep a logo PNG with alpha (your brand mark) and `img.alpha_composite()` it post-gen. Position is a design choice — be consistent across the WHOLE deck. A safe default for client decks = **top-RIGHT**: right edge ≈ `0.976*W`, top `0.038*H`, height `0.072*H` → `x = W - lw - int(W*0.024); y = int(H*0.038)`. (Top-left works too but clips left-aligned titles — see below.)
- **Keep the pre-logo RAW PNGs** (`exec_slides_raw/`, no logo). To move the logo to the other side / resize / rebrand, re-run the composite on raws — never try to "erase" a baked-in logo.
- **⭐ WHITE-BOX ROOT CAUSE = the prompt itself.** The old `exec-sketch` prompt said *"Leave the very top-left corner clean and empty (… a logo is composited there later)"* — telling Gemini to "leave a corner empty" makes it literally draw an **empty white box/container** there. FIXED at the prompt level (2026-06-14): the style string now says the cream bg *"COMPLETELY covers all four corners — NO white rectangles, NO empty blocks, NO containers, NO reserved boxes in any corner"* and no longer reserves a logo corner. New decks won't have the box. The logo is composited on top of the cream afterwards regardless.
  - **For decks generated with the OLD prompt** (box already baked in): fix ONLY a real box, never a title. Sample slide bg (median of edge points away from corners) and fill the corner with it **only if**: `white_px > 1500 AND dark_px < 300` inside `[0,0, 0.14W, 0.15H]` (`>244` all-channels = white; `<120` all-channels = dark text). A *left-aligned title* gives ~200-400 "white" px (antialiasing) + lots of dark px — DO NOT fill, or you erase the first word ("2012:" → cut).
  - Also keep using the anti-box wording in any **custom `EXEC_PREFIX`** you copy into a deck's `_common.py`.
- **Build a deck from full-bleed PNGs + ported notes (no LibreOffice):** `slide.shapes.add_picture(png,0,0,width=SW,height=SH)` on blank 13.333×7.5" layout; port notes by position from a source pptx (`deepcopy` the BODY notes placeholder if target has none); export to PDF via **PIL** `imgs[0].save(out,save_all=True,append_images=imgs[1:],resolution=150)`.
- **Verify without poppler/LibreOffice:** render PDF pages with **PyMuPDF** (`fitz.open(p)[i].get_pixmap(dpi=80)`); detect logo side via indigo-mask `(b>110)&(b-r>40)&(b-g>30)&(r<140)` count in top-left vs top-right band.
- **Cyrillic:** `markitdown` shows mojibake in a cp1251 Windows console — the file is fine UTF-8. Verify slide text **visually** (text is baked into images), not by terminal dump.

## Modular production pattern for big decks (build.py + notes.py + assemble.py) ⭐

For EXISTING multi-slide decks (30–64 slides) WITH speaker notes, the maintainable scaffold is the **modular deck pattern**, not one giant config JSON. New decks: prefer the exec-sketch manifest — notes live on the slide object by ID, so reordering can never shift them (the modular pattern maps `NOTES[n]` by number, `notes-pptx` by sorted position). Готовых примеров-деков в паке нет — каркас ниже описывает паттерн целиком.

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

### Slide text + speaker notes: NO infobiz, human language ⭐
Applies to every route, including `notes.spoken[]` of exec-sketch manifests.
On-slide text AND speaker notes must read like a human, not an info-business coach. Strip on every pass:
- Empty value-less framing: «Инструмент мощный, но толк только если правильно», «честная рамка, чтобы не разочароваться».
- Hype adjectives: «прям клад», «огонь», «золото», «кайф», vague «в десять раз».
- Clichés: «лучшее время начать было…», «дисциплина быстрых циклов / Shipped > Perfect», «золотое правило».
- Garbled idioms: «не молотком по гвоздику» → plain («простую — лёгкой моделью, сложную — мощной»).
Replace each with a concrete, useful statement or cut it. Bottom-marker lines should teach or instruct, not motivate.

### Speaker-notes voice
Write `notes.py` / `notes.spoken[]` in the **speaker's real spoken voice**, not in deck-English. The voice sample does not ship with the pack — how a specific person talks is personal data, and someone else's markers in your notes read as a forgery. Take yours from `~/.claude/voice-sample.md` (шаблон — `~/.claude/templates/voice-sample.md`); if the speaker is not you, ask for 2-3 transcripts of their own talks and pull the markers from there: metronome/filler openers for transitions, favourite connectives, forms of address to the room, homely analogies, self-irony on glitches. No sample and no time to get one — write plainly and say so in the handoff, instead of inventing a voice.

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
| Course / webinar, hand-drawn | exec-sketch `exec-sketch-light-calm` + `exec-sketch-dark-calm` |

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

### Semantic sketch (exec-sketch route)

The slide prompt is synthesized: `references/prompts/semantic-prefix.txt` + palette JSON +
EXACT HEADING + EXACT OTHER TEXT + VISUAL ARGUMENT + asset reservations. Write the `visual` field
as the argument ("three steps, the check is the active idea"), not decoration. Composition
patterns and anti-patterns: `references/exec-sketch-design.md`. A slide's `art_prompt` replaces
the whole synthesis — then the palette JSON does NOT reach the model; put colours in its text.

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
- Use the Prompt Engineering section above for structure (TITLE, SUBTITLE, layout, colors)
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

⚠️ `pptx`/`notes-pptx` match images and notes by sorted position. For a deck with full notes that
may be reordered, bind the PNGs into an exec-sketch manifest (`exec_sketch.py bind`) and `build` there.

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
4. All 32 AI styles are available (see AI Styles section above)

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

### Exec-sketch Mode
```
~/presentations/<YYYY-MM-DD>-<slug>/
├── deck.json             # manifest: ids, text, visual, notes, bindings (bind writes here)
├── prompts/              # plan output: <id>.txt + plan.json
├── art/                  # exec_generate: raw art + <id>.json provenance
├── media/                # bound PNGs <id>-<sha16>.png (+ logos/QR/photos you add)
└── export-v1/            # build output (never reused: next build → export-v2)
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

## Exec-sketch engine

| Palette key | Canvas | Ink / accent | Use |
|---|---|---|---|
| `exec-sketch-light-calm` ⭐ | warm paper `#F7F3E8` | warm black `#1A1814` / marigold `#FFC000` | default light for new decks (proof 23.09.2026) |
| `exec-sketch-dark-calm` ⭐ | black `#000000` | warm off-white `#F2EFE6` / `#FFC000` | default dark for new decks |
| `exec-sketch-light` | `#F8F5EC` | `#151515` / `#FFC000` | the bundled `examples/` |
| `exec-sketch-dark` | `#000000` | `#FFFFFF` / `#FFC000` | the bundled `examples/` |
| `exec-sketch-classic` | light `#F1F3F5` | indigo `#0B1021`, `#3B5BDB`, copper `#C77B30` | business decks; = the `exec-sketch` AI style |

Never edit an existing palette key in place: the palette is part of every binding's signature, so
all bound slides of that theme (and the examples/tests) go stale. Add a new key or `deck.themes`.

**Design rules** (proven 23.09.2026 on the same two slides with gpt-image-2.5-sunburst, control
included) live in the semantic prefix: ACCENT BUDGET (accent on one key phrase + one active object,
≤1 burst of rays), TYPE HIERARCHY (heading / half / third + quiet footnote), DRAWING LANGUAGE
(outline-first, identical repeats, no stock pictograms, equal line weights). Margins are NOT
achieved by prompting — the model ignored 6–7 % in every variant; use `art_inset` (0.8–1.0, deck or
slide): the art is scaled around the centre and the margin continues the artwork's own paper, no
seam. Results, metrics and the rejected variant: `references/exec-sketch-design.md` → «Proof 23.09.2026».

- **Logos/QR/photos/real UI** — never drawn by the model: `branding[]` (whole deck) or `overlays[]`
  (slide), `{role, image, sha256, rect:[x,y,w,h] in 0..1}`, each a separate PPTX picture, contain-fit
  and CENTRED in its rect. Preset «logo top-right»: `rect = [0.976 − w, 0.038, w, 0.072]`,
  `w = 0.072 · (logo_w / logo_h) · 1080 / 1920`. `art_inset < 1` cannot be combined with them.
- **Notes** — `notes.spoken[]` paragraphs (no hard wraps), `notes.stage[]`, `sources[]`. PPTX notes and
  `speaker-notes.txt` get all three; `teleprompter.txt` only the spoken part; both TXT are UTF-8 with BOM.
  Editing notes never invalidates art. Fewer than 70 spoken words → warning.
- **Stale = regenerate**: title, text, visual, art_prompt, palette or reservations changed → `qa` fails
  «Stale image»; generate and bind again. Never re-bind the old picture to new content.
- **Video** → skill `sketch-course-video` (same pack; 16:9 and 9:16, coral accent, pill captions) +
  `references/motion-handoff.md`; `build` exports `motion-handoff.json` without timestamps.

## References

| File | Read when |
|---|---|
| `references/exec-sketch-design.md` | designing exec-sketch slides; proof results and what failed |
| `references/manifest.md` | writing `deck.json`: every field, assets, `art_inset`, outputs |
| `references/production.md` | editorial map, notes, proof → batch, per-slide visual checklist |
| `references/motion-handoff.md` | the deck will become a drawn video |
| `references/prompts/` | semantic prefix (exec-sketch route), classic prefix (= `exec-sketch` style), 8 course recipes, verified example prompts |
| `references/legacy-workflow.md` | CLI of the five legacy scripts |
| `references/manus-26-themes.md` + `manus-theme-samples/` | Manus 1.6 theme catalog and reference slides |
