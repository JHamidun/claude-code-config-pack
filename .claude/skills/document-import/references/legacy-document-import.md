<!-- LEGACY: полное тело скилла 'document-import' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: document-import
description: PDF / DOCX / PPTX / sketch.app → структурированный контент для слайдов или лендинга. Извлекает заголовки, текст, цитаты, изображения. Используется для pitch-deck из PRD, лендинга из brief, slides из manifesto.
when_to_use: Юзер прислал документ как источник контента. Перед slides если контент лежит в Word/PDF. Перед content-engine если нужно вытащить ключевые сообщения.
---

# Document import

Источник: PDF / DOCX / PPTX / RTF / Markdown. Цель: вытащить контент в структурированном виде — иерархия (h1/h2/h3) + текст + изображения + cite.

## PDF

### Через pdf-parse (Node)
```bash
npm i pdf-parse
```
```js
const pdf = require('pdf-parse');
const fs = require('fs');
const data = await pdf(fs.readFileSync('source.pdf'));
console.log(data.text);   // весь текст
console.log(data.numpages);
console.log(data.info);   // metadata
```

### Через poppler (CLI)
```bash
brew install poppler  # mac
sudo apt-get install poppler-utils  # linux
choco install poppler  # windows (или: scoop install poppler)

pdftotext -layout source.pdf source.txt
pdfimages -all source.pdf images/img    # извлекает картинки
pdfinfo source.pdf                       # metadata
```

### Через Read tool
Claude Code умеет читать PDF напрямую через `Read` (если PDF до 10 страниц, или `pages: "1-5"` для длинных).

## DOCX

```bash
pip install python-docx
```
```python
from docx import Document
doc = Document('source.docx')
for p in doc.paragraphs:
    style = p.style.name  # "Heading 1", "Heading 2", "Normal"
    print(f"[{style}] {p.text}")
for table in doc.tables:
    for row in table.rows:
        print([cell.text for cell in row.cells])
```

Достоинство python-docx: знает styles (h1/h2/h3) которые юзер реально выставил, не парсит «больший шрифт = заголовок».

## PPTX

```bash
pip install python-pptx
```
```python
from pptx import Presentation
prs = Presentation('source.pptx')
for i, slide in enumerate(prs.slides, 1):
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                print(f"slide {i}: {para.text}")
        elif shape.shape_type == 13:  # Picture
            print(f"slide {i}: image, {shape.image.size}")
```

## Sketch (legacy)

`.sketch` — это zip с JSON внутри:
```bash
unzip source.sketch -d sketch-extracted/
ls sketch-extracted/pages/    # JSON каждой страницы
ls sketch-extracted/images/   # PNG ассеты
```

JSON структура complex — лучше поискать `sketchtool` (Sketch CLI, **macOS-only** — ставится вместе с Sketch.app):
```bash
sketchtool list pages source.sketch    # список страниц
sketchtool export artboards source.sketch --output=exports/   # все артборды как PNG
```

На Windows/Linux sketchtool недоступен — fallback: `.sketch` это zip, распаковать и забрать превью:
```bash
unzip -qo source.sketch -d sketch-extracted/
ls sketch-extracted/previews/ sketch-extracted/images/   # preview.png + PNG-ассеты
```

## Структурирование вывода

После парсинга → выдаёшь юзеру **content-tree**:

```yaml
title: "AI in Banking — Trends 2026"
sections:
  - h1: "Executive Summary"
    text: "Three trends will reshape banking..."
    citations: ["McKinsey 2026", "Gartner Q1"]
  - h1: "Trend 1: Agentic AI"
    h2: "What it is"
    text: "..."
    images:
      - path: "images/img-001.png"
        caption: "AI agent architecture"
    h2: "Why now"
    text: "..."
```

Дальше — этот content-tree feed'ишь в `slides` или `interactive-prototype` как рабочий контент.

## Извлечение по типам

### Pitch deck из PRD (Word/PDF)
- h1 → новый слайд
- bullet lists → bullets на слайде
- tables → table-slide или chart placeholder
- images → как есть на слайды

### Landing из brief
- Executive summary → hero text
- «Why» секция → problem-solution
- «Who» → target audience block
- Numbers → metrics row
- Quote → testimonial

### Slides из manifesto
- Цитаты → отдельные slide-cards
- Manifesto text → split на 5-7 слайдов с одной мыслью каждая
- «Не делать X» → антипаттерн-секция

## Качество текста

Если PDF — скан (изображения), `pdftotext` вернёт мусор. Признаки:
- Текст с randomized символами
- 30%+ слов невалидные
- Много пробелов / переносов

В этом случае → OCR (см. отдельный скилл `ocr-restore` если есть, или внешний tesseract).

## Изображения из документов

- Вытащил → положи в `uploads/source-<doc-name>/img-NNN.png`
- В content-tree укажи путь
- На слайдах используй с подписью
- Не используй автоматически low-res scan'ы — они выглядят плохо. Лучше плейсхолдер с описанием.

## Антипаттерны

- Импортить весь документ как «один длинный текст» → теряется структура
- Парсить PDF где текст — это картинки → получаешь шум
- Использовать regex для headers вместо styles → ловишь bold-paragraph как h1
- Игнорировать таблицы → теряешь часто самый ценный контент
- Не сохранять source-документ в `uploads/originals/` → теряется provenance
- Делать lossy преобразование (PDF → текст → slides) на больших docs → лучше через структурированный middle (content-tree YAML/JSON)
