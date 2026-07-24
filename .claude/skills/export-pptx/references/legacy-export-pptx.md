<!-- LEGACY: полное тело скилла 'export-pptx' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: export-pptx
description: HTML слайды → PPTX где каждый слайд — картинка-скриншот. Простой путь, никакой текстовой редактируемости. Если нужны редактируемые текст-боксы — используй pptx-editable-extractor.
when_to_use: Юзер просит «сохрани в PowerPoint», «pptx», «отправь в Keynote». Когда финальные слайды и редактировать в PPT не нужно (только показать).
---

# Export PPTX (screenshots)

Каждый слайд → PNG → вставлен в PPTX слайд. Простой, надёжный, не редактируемый по тексту.

## Зависимости

```bash
pip install python-pptx pillow
# Для экспорта PNG из HTML — playwright (см. export-png)
```

## Каркас

```python
# scripts/export_pptx.py
from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from PIL import Image
import os, sys

def export_pptx(slides_dir, out_pptx, width_in=13.333, height_in=7.5):
    """
    slides_dir/  должна содержать slide-01.png, slide-02.png, ...
    PPTX-стандарт 16:9 = 13.333" × 7.5"
    """
    prs = Presentation()
    prs.slide_width  = Inches(width_in)
    prs.slide_height = Inches(height_in)

    blank = prs.slide_layouts[6]  # blank layout

    for img_name in sorted(os.listdir(slides_dir)):
        if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(
            os.path.join(slides_dir, img_name),
            left=0, top=0,
            width=prs.slide_width,
            height=prs.slide_height,
        )

    prs.save(out_pptx)
    print(f"✓ {out_pptx} ({len(prs.slides)} slides)")

if __name__ == '__main__':
    slides_dir = sys.argv[1]      # ./slides/
    out = sys.argv[2] if len(sys.argv) > 2 else 'output.pptx'
    export_pptx(slides_dir, out)
```

```bash
# Сначала экспортить все слайды как PNG (см. export-png)
node scripts/export-png.js slides.html  # или skill 'export-png'
# Получит slides/slide-01.png ... slide-12.png

# Потом упаковать в PPTX
python3 scripts/export_pptx.py ./slides/ output.pptx
```

## Workflow целиком

```
1. slides skill → slides.html (1920×1080 канва)
2. export-png skill → slides/slide-01.png ... slide-NN.png (по одной странице)
3. export-pptx skill → output.pptx (картинки)
4. Открыть в PowerPoint / Keynote / Google Slides
```

## PPTX размеры

| Тип | Inches | Pixels @ 96 dpi |
|---|---|---|
| 16:9 standard (default) | 13.333 × 7.5 | 1280 × 720 |
| 16:9 widescreen HD | 13.333 × 7.5 | 1280 × 720 (тот же aspect) |
| 4:3 | 10 × 7.5 | 960 × 720 |
| 1:1 (Instagram) | 7.5 × 7.5 | 720 × 720 |
| Custom A4 portrait | 8.27 × 11.69 | 794 × 1122 |

Для презентаций — 16:9 always. Для печати handout — 4:3.

## Альтернативный путь: LibreOffice

Если установлен LibreOffice — конвертит HTML напрямую в PPTX:

```bash
soffice --headless --convert-to pptx slides.html
```

⚠ Качество хуже чем через screenshots — LibreOffice ре-рендерит HTML по-своему. Используй только если screenshots-путь не работает.

## Когда нужен **редактируемый** PPTX

Если после export юзер хочет менять текст/стили — `export-pptx` (этот скилл) НЕ подходит, картинки не редактируются. Иди в `pptx-editable-extractor` — он выкачивает текст и расположение из HTML и собирает нативные text boxes.

## Скрытые слайды

```python
slide = prs.slides.add_slide(blank)
slide.shapes.add_picture(...)
slide.element.set('show', '0')  # скрыть в режиме показа
```

Полезно для вспомогательных слайдов (notes, draft).

## Speaker notes

```python
notes_slide = slide.notes_slide
notes_text_frame = notes_slide.notes_text_frame
notes_text_frame.text = "Тут заметки для докладчика — не покажутся аудитории."
```

Если в `slides` HTML есть `<aside data-notes>...</aside>` — extract их и кладём в notes:

```python
# В каждый slide-NN.png парсим заметки из соответствующего HTML
# и вставляем в notes
```

## Метаданные

```python
prs.core_properties.title = "ExampleProduct — Pitch Deck"
prs.core_properties.author = "Your Name"
prs.core_properties.subject = "Edtech про AI"
prs.core_properties.created = datetime.utcnow()
```

Это видно в file properties и в email-attachments превью.

## Антипаттерны

- Ожидать что текст в PPTX будет редактируемый → screenshots не редактируются. Для этого `pptx-editable-extractor`
- Использовать LibreOffice convert на сложном HTML (с React/Babel) → mess
- 1920×1080 PNG в 4:3 PPTX → растянутые слайды
- Низкое разрешение PNG (1200×675) на 16:9 PPTX → блёрит на full-screen
- Не вписать metadata → файл «без названия»
- Не speaker-notes → потерял весь скрипт презентации
- Огромные images (>2MB каждый) × 30 слайдов → PPTX 60MB, не отправишь
