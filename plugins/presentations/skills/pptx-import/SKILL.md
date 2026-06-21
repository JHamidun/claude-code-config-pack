---
name: pptx-import
description: Распаковать PPTX как zip, прочитать XML слайдов, извлечь текст/картинки/координаты. Чтобы редактировать чужой дек как HTML.
when_to_use: Юзер прислал .pptx, нужно либо посмотреть содержимое, либо переверстать в HTML.
---

# PPTX import

PPTX — обычный zip с XML внутри. Структура:

```
deck.pptx (zip)
├── ppt/
│   ├── slides/
│   │   ├── slide1.xml
│   │   ├── slide2.xml
│   ├── media/
│   │   ├── image1.png
│   ├── theme/theme1.xml
│   └── presentation.xml
└── [Content_Types].xml
```

## Подход

Можно через `python-pptx` (надёжнее) или собственный парсер на Node.

### Python-вариант (рекомендую)

```bash
pip install python-pptx
```

`templates/import.py`:

```python
#!/usr/bin/env python3
import sys, json, os, base64
from pptx import Presentation
from pptx.util import Emu

EMU_PER_PX = 9525

def emu_px(emu): return int(round(emu / EMU_PER_PX))

def shape_to_dict(shape):
    out = {
        'kind': str(shape.shape_type).split('.')[-1] if shape.shape_type else 'unknown',
        'x': emu_px(shape.left or 0),
        'y': emu_px(shape.top or 0),
        'w': emu_px(shape.width or 0),
        'h': emu_px(shape.height or 0),
    }
    if shape.has_text_frame:
        out['kind'] = 'text'
        out['paragraphs'] = []
        for p in shape.text_frame.paragraphs:
            runs = []
            for r in p.runs:
                runs.append({
                    'text': r.text,
                    'bold': r.font.bold,
                    'italic': r.font.italic,
                    'size': r.font.size.pt if r.font.size else None,
                    'name': r.font.name,
                    'color': str(r.font.color.rgb) if r.font.color and r.font.color.type else None,
                })
            out['paragraphs'].append({ 'runs': runs, 'align': str(p.alignment) if p.alignment else None })
    elif shape.shape_type == 13:  # PICTURE
        out['kind'] = 'image'
        try:
            img = shape.image
            out['ext'] = img.ext
            out['data_b64'] = base64.b64encode(img.blob).decode()
        except Exception: pass
    return out

def main():
    if len(sys.argv) < 2:
        print("Usage: python import.py <file.pptx> [out.json]"); sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src.replace('.pptx', '.json')

    prs = Presentation(src)
    W, H = emu_px(prs.slide_width), emu_px(prs.slide_height)

    slides = []
    for i, sl in enumerate(prs.slides):
        items = [shape_to_dict(sh) for sh in sl.shapes]
        slides.append({ 'index': i, 'items': items })

    with open(out, 'w') as f:
        json.dump({ 'width': W, 'height': H, 'slides': slides }, f, indent=2, default=str)
    print(f"✓ {out} — {len(slides)} slides, {W}×{H}")

if __name__ == "__main__":
    main()
```

```bash
python import.py deck.pptx
# → deck.json
```

### Конвертер JSON → HTML

`templates/json-to-html.mjs`:

```js
import fs from 'node:fs/promises';
const file = process.argv[2];
const data = JSON.parse(await fs.readFile(file, 'utf8'));

let html = `<!doctype html><html><head><meta charset="utf-8"><title>Imported</title>
<script src="deck-stage.js"></script>
<style>
  body { margin: 0; }
  .slide-content { position: absolute; }
</style></head><body><deck-stage>`;

for (const sl of data.slides) {
  html += `\n<section data-screen-label="${String(sl.index+1).padStart(2,'0')}">`;
  for (const it of sl.items) {
    const style = `left:${it.x}px;top:${it.y}px;width:${it.w}px;height:${it.h}px;`;
    if (it.kind === 'text') {
      const txt = (it.paragraphs || []).map(p =>
        p.runs.map(r => {
          let t = `<span`;
          if (r.size) t += ` style="font-size:${r.size}px;`;
          if (r.bold) t += `font-weight:bold;`;
          if (r.color) t += `color:#${r.color};`;
          t += `"`;
          return t + `>${r.text}</span>`;
        }).join('')
      ).join('<br>');
      html += `\n<div class="slide-content" style="${style}">${txt}</div>`;
    } else if (it.kind === 'image' && it.data_b64) {
      html += `\n<img class="slide-content" src="data:image/${it.ext};base64,${it.data_b64}" style="${style}">`;
    } else {
      html += `\n<div class="slide-content" style="${style};outline:1px dashed #aaa;"></div>`;
    }
  }
  html += `\n</section>`;
}
html += `\n</deck-stage></body></html>`;

await fs.writeFile(file.replace('.json', '.html'), html);
console.log('✓', file.replace('.json', '.html'));
```

## Round-trip workflow

1. `python import.py original.pptx` → `original.json`
2. `node json-to-html.mjs original.json` → `original.html`
3. Правишь в HTML.
4. `pptx-editable-extractor` → новый PPTX.

## Ограничения

- **Layouts и masters**: импорт берёт shapes явно на слайде, не туннелирует master-уровень. Логотипы и фон с master'а потеряются — добавляй вручную.
- **Анимации, переходы, видео** — не переносятся в HTML.
- **Smart Art / диаграммы** — приходят как группы shapes, выглядят коряво. Лучше переделать заново.
- **Скрытые слайды** — не фильтруются, попадают в JSON.

## Что делать с невнятным импортом

Если PPTX сделан в дизайнерском стиле (выровнено по сетке, аккуратные шрифты) — round-trip даёт 80% результат, доделать вручную ~20%.

Если PPTX-каша (Word-style, всё в textbox'ах с разными шрифтами) — лучше **переписать с нуля** в HTML, импорт даёт текст и картинки, остальное — заново.

## Связь с другими скиллами

- `pptx-editable-extractor` — обратная задача (HTML → PPTX).
- `slides` — каркас для нового HTML, куда переносить контент.
- `document-import` — общий импорт docx/pdf/pptx.
