<!-- LEGACY: полное тело скилла 'pptx-editable-extractor' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: pptx-editable-extractor
description: HTML слайды → PPTX с НАТИВНЫМИ text-боксами (можно редактировать в PowerPoint). Парсит DOM, извлекает text-узлы с координатами, создаёт корректно-позиционированные shapes. Сложнее чем export-pptx, но даёт настоящий PowerPoint, не картинки.
when_to_use: Юзер просит «pptx с редактируемым текстом», «дай мне финальные слайды что-бы я мог дальше делать в PowerPoint», «не картинки». После slides когда финал нужен в PPTX.
---

# PPTX editable extractor

Парсит HTML слайдов, извлекает каждый text-узел с его computed-координатами, создаёт PPTX с нативными `text_frame`'ами. Картинки и фоны идут отдельно как shapes.

## Зависимости

```bash
pip install python-pptx pillow lxml
npm i -D playwright   # для extraction координат
```

## Принцип

1. Открыть HTML в Playwright headless
2. Для каждого text-узла вытянуть: text, bbox (x/y/width/height), font, size, color, weight
3. Для каждого `<img>` / `background-image` — координаты + asset path
4. Сложить в PPTX через python-pptx с тем же расположением

## Extraction script (Node)

`scripts/extract.js`:
```js
const { chromium } = require('playwright');
const fs = require('fs');

async function extract(htmlPath, outJson) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });

  const slides = await page.$$eval('.slide', (slides) => {
    return slides.map((slide, idx) => {
      const result = { i: idx + 1, texts: [], images: [], shapes: [] };

      // Активировать слайд
      slide.classList.add('active');

      // Текст-узлы
      const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
      let node;
      while (node = walker.nextNode()) {
        const text = node.textContent.trim();
        if (!text) continue;
        const range = document.createRange();
        range.selectNodeContents(node);
        const rect = range.getBoundingClientRect();
        const slideRect = slide.getBoundingClientRect();
        const cs = getComputedStyle(node.parentElement);
        result.texts.push({
          text,
          x: rect.left - slideRect.left,
          y: rect.top - slideRect.top,
          w: rect.width,
          h: rect.height,
          font: cs.fontFamily.split(',')[0].replace(/['"]/g, ''),
          size: parseFloat(cs.fontSize),
          weight: cs.fontWeight,
          color: cs.color,
          align: cs.textAlign,
          lineHeight: cs.lineHeight,
        });
      }

      // Изображения
      slide.querySelectorAll('img').forEach(img => {
        const rect = img.getBoundingClientRect();
        const slideRect = slide.getBoundingClientRect();
        result.images.push({
          src: img.src.replace('file://', ''),
          x: rect.left - slideRect.left,
          y: rect.top - slideRect.top,
          w: rect.width,
          h: rect.height,
        });
      });

      slide.classList.remove('active');
      return result;
    });
  });

  fs.writeFileSync(outJson, JSON.stringify(slides, null, 2));
  await browser.close();
  console.log(`✓ extracted ${slides.length} slides → ${outJson}`);
}

extract(process.argv[2], process.argv[3] || 'slides.json');
```

```bash
node scripts/extract.js /abs/path/slides.html slides.json
```

## Сборка PPTX (Python)

`scripts/build_pptx.py`:
```python
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
import json, sys, re

def px_to_emu(px, slide_w_px=1920, slide_w_in=13.333):
    """Convert pixel coords (1920×1080 canvas) → EMU (PPTX unit)."""
    return Emu(int(px * slide_w_in / slide_w_px * 914400))

def parse_color(s):
    """rgb(255, 0, 0) → RGBColor(0xff, 0x00, 0x00)"""
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', s)
    if m: return RGBColor(int(m[1]), int(m[2]), int(m[3]))
    return RGBColor(0, 0, 0)

def build(slides_data, out):
    prs = Presentation()
    prs.slide_width = Emu(int(13.333 * 914400))
    prs.slide_height = Emu(int(7.5 * 914400))
    blank = prs.slide_layouts[6]

    for s in slides_data:
        slide = prs.slides.add_slide(blank)

        # Изображения сначала (под текстом)
        for img in s['images']:
            slide.shapes.add_picture(
                img['src'],
                left=px_to_emu(img['x']), top=px_to_emu(img['y']),
                width=px_to_emu(img['w']), height=px_to_emu(img['h']),
            )

        # Текст
        for t in s['texts']:
            tb = slide.shapes.add_textbox(
                left=px_to_emu(t['x']), top=px_to_emu(t['y']),
                width=px_to_emu(t['w'] + 20),  # +20px запас на text-flow
                height=px_to_emu(t['h']),
            )
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = t['text']
            run.font.name = t['font']
            run.font.size = Pt(t['size'] * 0.75)  # CSS px → PT
            run.font.bold = int(t['weight']) >= 600
            run.font.color.rgb = parse_color(t['color'])

    prs.save(out)
    print(f"✓ {out} ({len(prs.slides)} slides)")

if __name__ == '__main__':
    data = json.load(open(sys.argv[1]))
    build(data, sys.argv[2] if len(sys.argv) > 2 else 'output.pptx')
```

```bash
python3 scripts/build_pptx.py slides.json output.pptx
```

## End-to-end

```bash
# 1. Generate slides.html через slides skill
# 2. Extract structure
node scripts/extract.js /abs/slides.html slides.json
# 3. Build editable PPTX
python3 scripts/build_pptx.py slides.json output.pptx
# 4. Open в PowerPoint — текст редактируется, картинки на месте
```

## Что **не** перенесётся

- `backdrop-filter: blur(...)` — Chromium растрирует, в PPTX потеряется
- CSS gradients — становятся flat color (PowerPoint поддерживает gradients нативно, но extraction сложен)
- SVG inline — становятся текст или вообще пропадают
- box-shadow — частично (PowerPoint имеет shadows, mapping ручной)
- Анимации / переходы — нет вообще
- Custom fonts — если шрифт не установлен на машине открывающего, fallback

## Решения для шрифтов

**Embed fonts** в PPTX:
```python
# python-pptx не поддерживает font-embedding напрямую,
# нужно через manipulating XML внутри .pptx (zip)
import zipfile
with zipfile.ZipFile(out, 'a') as z:
    z.write('fonts/InterTight-Bold.ttf', 'ppt/fonts/InterTight-Bold.ttf')
# + добавить reference в presentation.xml
```

Или просто **используй системные шрифты в slides.html** (Helvetica / Arial / Times New Roman), которые есть везде.

## Антипаттерны

- Использовать pptx-editable-extractor на сложном HTML с position: absolute everywhere → координаты будут off
- Пропустить шрифт-fallback → у юзера PPTX выглядит криво
- Включать background-color body как «слой» → дублируется на каждый slide
- Не fix'ить overflow text → text frame обрезает на edit'е
- Использовать non-pixel units (em, rem, %) → extraction врут координаты, всё съезжает
- Не testить открыв реальный PPTX в PowerPoint → могут быть rendering quirks
