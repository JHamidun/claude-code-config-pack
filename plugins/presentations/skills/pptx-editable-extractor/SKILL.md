---
name: pptx-editable-extractor
description: HTML → редактируемый PPTX. Каждый текст-узел становится нативным TextBox с координатами, шрифтом, цветом. Пользователь редактирует в PowerPoint.
when_to_use: Нужен PPTX, который можно править. Не путать с export-pptx (screenshots).
---

# PPTX editable extractor

Алгоритм: открыть HTML в headless, обойти DOM, для каждого видимого текстового / графического узла собрать `{x, y, w, h, text, fontFamily, fontSize, fontWeight, color, bgColor, image?}`. Сериализовать в JSON. Затем Python через `python-pptx` собрать PPTX, где каждая «коробка» — настоящий TextBox или Picture.

## Зависимости

```bash
npm i -D playwright
npx playwright install chromium
pip install python-pptx pillow
```

## Скрипт-экстрактор

`templates/extract.mjs`:

```js
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const args = parse(process.argv.slice(2));
const file = args._[0];
if (!file) { console.error('Usage: node extract.mjs <html> [--slide-selector "deck-stage > section"] [--width 1920] [--height 1080] [--out slides.json]'); process.exit(1); }

const sel = args['slide-selector'] || 'deck-stage > section';
const width  = +(args.width  || 1920);
const height = +(args.height || 1080);
const out = args.out || file.replace(/\.html?$/, '.json');

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width, height } });
const page = await ctx.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

const slides = await page.$$eval(sel, (nodes, args) => {
  function rgbToHex(rgb) {
    const m = rgb.match(/\d+/g);
    if (!m) return null;
    return '#' + m.slice(0,3).map(n => (+n).toString(16).padStart(2,'0')).join('');
  }
  function visible(el) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }
  function isTextLeaf(el) {
    if (!el.childNodes.length) return false;
    return [...el.childNodes].every(n =>
      n.nodeType === Node.TEXT_NODE ||
      (n.nodeType === Node.ELEMENT_NODE && ['B','I','EM','STRONG','SPAN','BR','A'].includes(n.tagName))
    );
  }

  return nodes.map(slide => {
    const sr = slide.getBoundingClientRect();
    const items = [];

    // Тексты
    slide.querySelectorAll('*').forEach(el => {
      if (!visible(el)) return;
      if (!el.textContent || !el.textContent.trim()) return;
      if (!isTextLeaf(el)) return;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      items.push({
        kind: 'text',
        x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
        text: el.innerText,
        fontFamily: cs.fontFamily.split(',')[0].replace(/"/g,'').trim(),
        fontSize: parseFloat(cs.fontSize),
        fontWeight: cs.fontWeight,
        italic: cs.fontStyle === 'italic',
        color: rgbToHex(cs.color),
        align: cs.textAlign,
        lineHeight: cs.lineHeight,
        letterSpacing: cs.letterSpacing,
      });
    });

    // Картинки
    slide.querySelectorAll('img').forEach(el => {
      if (!visible(el)) return;
      const r = el.getBoundingClientRect();
      items.push({
        kind: 'image',
        x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
        src: el.currentSrc || el.src,
      });
    });

    // Прямоугольники с фоном (карточки, плашки)
    slide.querySelectorAll('div, section, article, header, footer').forEach(el => {
      if (!visible(el)) return;
      const cs = getComputedStyle(el);
      const bg = cs.backgroundColor;
      if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') return;
      const r = el.getBoundingClientRect();
      items.push({
        kind: 'rect',
        x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
        fill: rgbToHex(bg),
        radius: parseFloat(cs.borderRadius),
        z: -1,
      });
    });

    // Фон слайда
    const sCs = getComputedStyle(slide);
    return {
      width: sr.width, height: sr.height,
      bg: rgbToHex(sCs.backgroundColor),
      items: items.sort((a,b) => (a.z||0) - (b.z||0)),
    };
  });
}, { width, height });

await browser.close();
await fs.writeFile(out, JSON.stringify({ width, height, slides }, null, 2));
console.log('✓', out, '—', slides.length, 'слайдов');

function parse(argv) {
  const a = { _: [] };
  for (let i=0; i<argv.length; i++) {
    const v = argv[i];
    if (v.startsWith('--')) { const k = v.slice(2), n = argv[i+1]; if (!n||n.startsWith('--')) a[k]=true; else { a[k]=n; i++; } }
    else a._.push(v);
  }
  return a;
}
```

## Скрипт-сборщик PPTX

`templates/build_pptx.py`:

```python
#!/usr/bin/env python3
import json, sys, os, urllib.request, tempfile
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

EMU_PER_PX = 9525  # PowerPoint

def px(v): return Emu(int(round(v * EMU_PER_PX)))

def hex_to_rgb(s):
    s = s.lstrip('#')
    return RGBColor(int(s[0:2],16), int(s[2:4],16), int(s[4:6],16))

def fetch_image(src, tmp):
    if src.startswith('data:'):
        import base64
        head, b64 = src.split(',', 1)
        ext = 'png' if 'png' in head else 'jpg'
        path = os.path.join(tmp, f"img_{abs(hash(src))}.{ext}")
        with open(path, 'wb') as f: f.write(base64.b64decode(b64))
        return path
    elif src.startswith('http'):
        path = os.path.join(tmp, f"img_{abs(hash(src))}")
        urllib.request.urlretrieve(src, path)
        return path
    elif src.startswith('file://'):
        return src.replace('file://','')
    else:
        return src  # относительный путь

def main():
    if len(sys.argv) < 2:
        print("Usage: build_pptx.py slides.json [out.pptx]"); sys.exit(1)

    data = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace('.json', '.pptx')
    W, H = data['width'], data['height']

    prs = Presentation()
    prs.slide_width  = px(W)
    prs.slide_height = px(H)
    blank = prs.slide_layouts[6]

    tmp = tempfile.mkdtemp()

    for s in data['slides']:
        slide = prs.slides.add_slide(blank)
        # Фон
        if s.get('bg'):
            try:
                slide.background.fill.solid()
                slide.background.fill.fore_color.rgb = hex_to_rgb(s['bg'])
            except Exception: pass

        for item in s['items']:
            x,y,w,h = px(item['x']), px(item['y']), px(item['w']), px(item['h'])

            if item['kind'] == 'rect':
                shp = slide.shapes.add_shape(1, x, y, w, h)  # MSO_SHAPE.RECTANGLE
                shp.fill.solid()
                if item.get('fill'): shp.fill.fore_color.rgb = hex_to_rgb(item['fill'])
                shp.line.fill.background()

            elif item['kind'] == 'text':
                tb = slide.shapes.add_textbox(x, y, w, h)
                tf = tb.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
                p = tf.paragraphs[0]
                p.text = item['text']
                run = p.runs[0]
                run.font.name = item.get('fontFamily') or 'Helvetica'
                run.font.size = Pt(item.get('fontSize', 16) * 0.75)  # px → pt approx
                if item.get('color'): run.font.color.rgb = hex_to_rgb(item['color'])
                fw = str(item.get('fontWeight','400'))
                run.font.bold = fw in ('bold','600','700','800','900')
                run.font.italic = bool(item.get('italic'))
                a = (item.get('align') or 'left')
                p.alignment = {'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT,'justify':PP_ALIGN.JUSTIFY}.get(a, PP_ALIGN.LEFT)

            elif item['kind'] == 'image':
                try:
                    p = fetch_image(item['src'], tmp)
                    slide.shapes.add_picture(p, x, y, w, h)
                except Exception as e:
                    print("img fail:", item['src'], e)

    prs.save(out)
    print("✓", out)

if __name__ == "__main__":
    main()
```

## Использование

```bash
node extract.mjs deck.html --slide-selector "deck-stage > section"
python build_pptx.py deck.json deck.pptx
```

## Ограничения

- **Шрифты.** PowerPoint использует свои метрики; идентичной верстки не будет. Согласись на 95%.
- **CSS-эффекты** (тени, фильтры, gradients) — не переносятся в editable. Для пиксель-точности используй `export-pptx` в screenshot-режиме.
- **Слои с z-index** — алгоритм вытаскивает фоновые прямоугольники, но overlap может быть неидеальным.
- **SVG-инлайн** — не переносится. Замени на PNG-плейсхолдеры.

## Когда использовать что

| Задача | Скилл |
|---|---|
| Презентация будет редактироваться в PowerPoint | `pptx-editable-extractor` |
| Нужна пиксель-идентичность с HTML | `export-pptx` (screenshots) |
| Нужно и то, и другое | оба, два разных файла |

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-pptx-editable-extractor.md`. Секции там: Зависимости, Принцип, Extraction script (Node), Сборка PPTX (Python), End-to-end, Что **не** перенесётся, Решения для шрифтов, Антипаттерны.
