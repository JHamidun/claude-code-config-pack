---
name: export-pdf
description: HTML → PDF через Playwright Chromium. Для слайдов и лендингов которые нужно отправить как один файл. Сохраняет векторный текст (можно копировать), reasonable file size, корректные cuts по слайдам.
when_to_use: Юзер просит «сделай PDF», «отправлю в Telegram», «один файл для презентации». После slides или standalone-html.
---

# Export PDF

Playwright headless Chromium → векторный PDF. Текст копируется, размер ~200KB-2MB.

## Каркас

`scripts/export-pdf.js`:
```js
const { chromium } = require('playwright');
const path = require('path');

async function exportPdf(htmlPath, opts = {}) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(`file://${path.resolve(htmlPath)}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(opts.wait || 1000);

  const out = opts.out || htmlPath.replace(/\.html$/, '.pdf');
  await page.pdf({
    path: out,
    format: opts.format || 'A4',
    landscape: opts.landscape ?? false,
    printBackground: true,
    margin: opts.margin || { top: '0', right: '0', bottom: '0', left: '0' },
    preferCSSPageSize: true,
    scale: opts.scale || 1,
  });

  await browser.close();
  return out;
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const html = args[0];
  const isSlides = args.includes('--slides');
  exportPdf(html, isSlides ? { format: { width: '1920px', height: '1080px' }, landscape: true } : {})
    .then(out => console.log(`✓ ${out}`));
}

module.exports = { exportPdf };
```

```bash
node scripts/export-pdf.js artifact.html
node scripts/export-pdf.js deck.html --slides
```

## Для slides — особенности

Если артефакт — `slides`:
1. Размер страницы = размер слайда (1920×1080)
2. Один слайд = одна страница в PDF
3. Каждый слайд должен иметь `page-break-after: always` в CSS

```css
.slide {
  width: 1920px;
  height: 1080px;
  page-break-after: always;
  break-after: always;        /* modern */
  break-inside: avoid;
}

@media print {
  body { background: #fff; }
  .deck { display: block !important; }
  .slide {
    position: static;
    opacity: 1 !important;
    transform: none !important;
    pointer-events: auto;
  }
}
```

В JS (`slides` каркас) для PDF-режима:
```js
// Активировать все слайды для PDF
if (new URL(location).searchParams.get('print') === '1') {
  document.querySelectorAll('.slide').forEach(s => s.classList.add('active'));
}
```

И передавать `?print=1` в URL при экспорте.

## Для лендингов

Континуальный документ — без `page-break`. Просто весь HTML на A4 portrait.

```js
await page.pdf({
  path: 'landing.pdf',
  format: 'A4',
  printBackground: true,
  margin: { top: '20mm', bottom: '20mm', left: '15mm', right: '15mm' },
});
```

## Custom CSS @page

В HTML:
```css
@page {
  size: 1920px 1080px;
  margin: 0;
}
@page :first {
  margin-top: 0;
}
```

И `preferCSSPageSize: true` в Playwright options.

## Шрифты в PDF

Web fonts через CDN иногда не embed'ятся. Решение:

```js
await page.evaluateHandle('document.fonts.ready');   // ждать загрузки
await page.waitForTimeout(500);                      // запас
```

Или **self-host шрифты** в `fonts/` — гарантированный embed.

## Размер файла

Что увеличивает:
- Большие изображения внутри HTML (sharp resize до экспорта)
- PNG вместо JPEG/WebP
- Embedded fonts (4 weights × 200KB = 800KB только на шрифт)
- backdrop-filter (Chromium растрирует blur)

Что уменьшает:
- WebP / optimized JPEG
- Subset шрифтов (только нужные glyphs)
- `printBackground: false` (но теряешь градиенты)
- `scale: 0.8` (но теряешь чёткость)

## Multi-section PDF

Если артефакт = N экранов, и хочешь разные ориентации:

```js
const { PDFDocument } = require('pdf-lib');

const slides = await exportPdf('slides.html', { landscape: true });
const docs   = await exportPdf('docs.html');

const merged = await PDFDocument.create();
for (const file of [slides, docs]) {
  const src = await PDFDocument.load(fs.readFileSync(file));
  const pages = await merged.copyPages(src, src.getPageIndices());
  pages.forEach(p => merged.addPage(p));
}
fs.writeFileSync('combined.pdf', await merged.save());
```

## Stacking со связанными скиллами

- `print-styles` — добавляет `@media print` стили для красивой печати
- `pptx-editable-extractor` — альтернатива если нужен PPTX, не PDF
- `verifier` — проверяй артефакт перед export
- `slides` / `standalone-html` — обычно exportим эти

## Антипаттерны

- Не ждать `document.fonts.ready` → fallback-шрифт в PDF
- `printBackground: false` на artistic дизайне → потеря всех градиентов и фонов
- Полагаться на CDN шрифт → иногда не успевает загрузиться, fallback embed'ится
- Margin 20mm на slides → текст обрезан справа/слева
- Gigantic PDF (>50MB) → не отправишь по Telegram → оптимизировать images заранее
- Не проверять PDF перед отправкой юзеру → можно отправить сломанный
- `page.pdf()` без `waitUntil: 'networkidle'` → asset'ы не догружены
