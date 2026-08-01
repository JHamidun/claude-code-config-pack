<!-- LEGACY: полное тело скилла 'moodboard' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: moodboard
description: HTML-мудборд с автоизвлечённой палитрой. Юзер скидывает 4-12 референсных картинок, скилл собирает их в HTML-сетку и извлекает доминирующие цвета в палитру для следующего шага (design-system-create).
when_to_use: Юзер собирает визуал для нового проекта, есть файлы-референсы, нужно зафиксировать направление до старта системы.
---

# Moodboard

Один HTML, в котором лежат 6-12 референсных изображений + извлечённая палитра + 2-3 текстовых ключа стиля.

## Каркас

```html
<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Moodboard — <Project></title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.5 -apple-system, system-ui, sans-serif;
         background: #f5f5f5; color: #111; padding: 32px; }
  .mb-head { display: flex; justify-content: space-between; align-items: end; margin-bottom: 32px; }
  .mb-head h1 { font: 700 32px/1.1 "Inter Tight", sans-serif; margin: 0; }
  .mb-tags { display: flex; gap: 8px; }
  .mb-tag { padding: 6px 14px; border: 1px solid #111; border-radius: 999px; font-size: 12px; }
  .mb-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .mb-grid img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 8px;
                 box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .mb-grid img.tall { aspect-ratio: 3/4; grid-row: span 2; }
  .mb-grid img.wide { aspect-ratio: 16/9; grid-column: span 2; }
  .mb-palette { margin-top: 32px; padding: 24px; background: #fff; border-radius: 12px; }
  .mb-swatches { display: grid; grid-template-columns: repeat(8, 1fr); gap: 8px; margin-top: 12px; }
  .mb-swatch { aspect-ratio: 1; border-radius: 6px; display: flex; align-items: end;
               padding: 8px; font: 600 11px/1 "JetBrains Mono", monospace; color: #fff;
               text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
</style></head>
<body>
  <header class="mb-head">
    <h1>Moodboard · <Project></h1>
    <div class="mb-tags">
      <span class="mb-tag">editorial</span>
      <span class="mb-tag">warm cream</span>
      <span class="mb-tag">slow rhythm</span>
    </div>
  </header>

  <div class="mb-grid">
    <img src="refs/01.jpg" class="tall" alt="Linear billing">
    <img src="refs/02.jpg" alt="Stripe pricing">
    <!-- … 6-12 ref images … -->
  </div>

  <div class="mb-palette">
    <h2 style="margin:0;font-size:18px">Извлечённая палитра</h2>
    <div class="mb-swatches">
      <div class="mb-swatch" style="background:#0A0E27">#0A0E27</div>
      <div class="mb-swatch" style="background:#3B5BDB">#3B5BDB</div>
      <div class="mb-swatch" style="background:#4DABF7">#4DABF7</div>
      <div class="mb-swatch" style="background:#F1F3F5;color:#111;text-shadow:none">#F1F3F5</div>
      <div class="mb-swatch" style="background:#FFFFFF;color:#111;text-shadow:none;border:1px solid #ddd">#FFFFFF</div>
      <!-- … 8 swatches … -->
    </div>
  </div>
</body></html>
```

## Извлечение палитры из изображений

Если установлен `npm i canvas` — используй `node-canvas` чтобы вытащить доминирующие цвета:

```js
const { createCanvas, loadImage } = require('canvas');
async function extractPalette(imgPath, k = 6) {
  const img = await loadImage(imgPath);
  const c = createCanvas(50, 50); const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0, 50, 50);
  const px = ctx.getImageData(0, 0, 50, 50).data;
  // ...k-means на pixel-array, возвращает k hex-цветов
}
```

Если canvas нет — попроси юзера вытащить палитру вручную через CSS-color picker и просто впиши hex'ы в `mb-swatches`.

## Tags — что это

3-5 коротких слов про **vibe**, не про категорию:
- ✅ «editorial», «warm cream», «slow rhythm», «monochrome», «dense», «soft brutalism»
- ❌ «landing», «website», «design» (слишком общие)

## Использование с design-system-create

Moodboard → читаешь палитру и tags → `design-system-create` принимает их как input для построения tokens.

```
«Используй палитру из moodboard.html и vibe-tags
[editorial, warm cream, slow rhythm]. Сделай design tokens
с этой палитрой как primary, и type scale соответствующий
spacious/slow ритму.»
```

## Антипаттерны

- 30+ референсов → не moodboard, а scrollable mess
- Изображения разного качества/масштаба без обработки → визуальный шум
- Палитра > 8 цветов → не палитра, а хроматическая помойка
- Tags слишком общие («modern», «clean», «professional») → не помогают
- Сделать moodboard и потом про него забыть → впустую
