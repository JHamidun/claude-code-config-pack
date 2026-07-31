---
name: export-pdf
description: Печать HTML-макета или дека в PDF через headless Chrome (Playwright). Одна страница = один слайд.
when_to_use: Пользователь просит сохранить дизайн/презентацию в PDF.
---

# Export PDF

Headless Chromium через Playwright. Без него не работает — поставь:

```bash
npm i -D playwright
npx playwright install chromium
```

## Скрипт

`templates/print-pdf.mjs`:

```js
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const [, , file, outArg] = process.argv;
if (!file) { console.error('Usage: node print-pdf.mjs <html> [out.pdf]'); process.exit(1); }

const out = outArg || file.replace(/\.html?$/, '.pdf');
const url = pathToFileURL(path.resolve(file)).href;

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(url, { waitUntil: 'networkidle' });

// Размер страницы PDF берём из <deck-stage width height>, если он есть
const dims = await page.evaluate(() => {
  const ds = document.querySelector('deck-stage');
  return ds ? { w: +ds.getAttribute('width') || 1920, h: +ds.getAttribute('height') || 1080 } : null;
});

if (dims) {
  // Перед печатью включим режим "noscale", чтоб <deck-stage> отдал слайды для @page
  await page.evaluate(() => document.querySelector('deck-stage').setAttribute('noscale', ''));
  await page.pdf({
    path: out,
    width:  dims.w + 'px',
    height: dims.h + 'px',
    printBackground: true,
    pageRanges: '',
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
    preferCSSPageSize: true,
  });
} else {
  // Обычный документ — A4
  await page.pdf({ path: out, format: 'A4', printBackground: true });
}

await browser.close();
console.log('✓', out);
```

## Запуск

```bash
node print-pdf.mjs deck.html
# → deck.pdf
```

## Почему так, а не window.print()

`window.print()` требует пользовательского клика и не даёт контроля над размером страницы. Playwright делает то же самое, но программно и предсказуемо.

## Подсказки

- Если PDF выходит пустой — скорее всего дек не успел отрисоваться. Увеличь `waitUntil` до `'load'` и добавь `await page.waitForTimeout(500)`.
- Если шрифты с CDN не подгружаются — добавь `await page.waitForLoadState('networkidle')` ИЛИ `document.fonts.ready` через evaluate.
- Картинки с `lazy` — пролистай страницу до конца перед печатью или поменяй на `eager`.
- Для деков обязательно `<deck-stage>` должен иметь корректные `width`/`height`. Скрипт читает их и задаёт размер @page.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-export-pdf.md`. Секции там: Каркас, Для slides — особенности, Для лендингов, Custom CSS @page, Шрифты в PDF, Размер файла, Multi-section PDF, Stacking со связанными скиллами, Антипаттерны.
