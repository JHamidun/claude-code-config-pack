---
description: "Презентация из темы через Manus Slides: 24 AI-стиля, экспорт PPTX/PDF/HTML. Триггеры: «сделай слайды», «в стиле Manus». НЕ skill slides (ручные HTML-деки)."
argument-hint: <topic or "edit project_dir">
---

Create a professional slide presentation using the Manus Slides pipeline.

## Instructions

Read the skill `~/.claude/skills/manus-slides/SKILL.md` for full reference.

### Mode Detection

- If $ARGUMENTS contains "html" or "editable" → **HTML Mode**
- If $ARGUMENTS starts with "edit" → **Edit Mode**
- Default → **AI Mode** (best visual quality, 24 styles)

### AI Mode (Default, Recommended)

1. **Analyze the topic** — Determine audience, goal, key messages
2. **Recommend style** — Run:
   ```bash
   python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py recommend "$ARGUMENTS"
   ```
   Present top 3-5 styles to the user. Let them choose or accept default.
3. **Research** — If user provides docs/files, read them first
4. **Generate outline** — Plan 8-12 slides with titles and content summaries
5. **Write prompts** — For each slide, create a content prompt adapted to chosen style:
   ```text
   TITLE in large bold text: "Заголовок"
   SUBTITLE: "Подзаголовок"
   [Layout: diagrams, icons, lists, charts]
   At the bottom: "Ключевой вывод"
   ```
6. **Create config** — Write `slides.json`:
   ```json
   {
     "title": "Title",
     "style": "whiteboard",
     "slides": [
       {"id": "slide_01", "prompt": "TITLE: ..."},
       {"id": "slide_02", "prompt": "TITLE: ..."}
     ]
   }
   ```
7. **Generate** — Run:
   ```bash
   python ~/.claude/skills/manus-slides/scripts/whiteboard_generator.py generate slides.json ./generated
   ```
8. **Review** — Check each generated image, note any that need fixes
9. **Deliver** — PPTX and HTML preview are auto-created alongside the images

### HTML Mode (If Requested)

1. **Analyze** → 2. **Outline as JSON** → 3. **Confirm with user**
4. **Init project:**
   ```bash
   python ~/.claude/skills/manus-slides/scripts/slide_manager.py init "<title>" outline.json ./<project-dir>
   ```
5. **For each slide** — Generate HTML using templates:
   ```bash
   python ~/.claude/skills/manus-slides/scripts/slide_templates.py get <template_key> '<data_json>'
   ```
6. **Export:**
   ```bash
   python ~/.claude/skills/manus-slides/scripts/slide_export.py html ./<project-dir> ./presentation.html
   ```

### Edit Mode

If $ARGUMENTS starts with "edit", extract the project directory and modify existing slides.

### AI Styles (24 available)

**Manus Originals:** vinyl, whiteboard, grove, fresco, easel, diorama, chromatic
**Manus Hybrid:** sketch, glamour, amber, arctic, neon, patina, onyx
**Bonus:** chalkboard, notebook, blueprint, glassmorphism, corporate, dark-tech, dashboard, infographic, watercolor, minimal-clean

| Task | Recommended Styles |
|:--|:--|
| Pitch deck, investors | vinyl, chromatic, onyx |
| Business, strategy | whiteboard, corporate, dashboard |
| Education, training | chalkboard, sketch, whiteboard |
| Tech, engineering | blueprint, dark-tech, chromatic |
| Creative, design | easel, watercolor, glassmorphism |
| Data, analytics | dashboard, infographic, arctic |
| Luxury, premium | glamour, onyx, fresco |

Default style: `whiteboard`

### HTML-Only Styles (13)

If user asks for: cerulean, cobalt, emerald, basalt, mist, sand, linen, alabaster, quartz, mahogany, ginkgo, sunset, lavender — switch to HTML Mode automatically.

Topic: $ARGUMENTS
