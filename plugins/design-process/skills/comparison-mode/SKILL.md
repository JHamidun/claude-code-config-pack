---
name: comparison-mode
description: "Diff двух HTML-версий: side-by-side, DOM-, pixel- и style-разница. Триггеры: «сравни две версии», «что изменилось в макете»."
---

# Comparison mode

Не текстовый diff (его делает git). А **визуальный** + **семантический**.

## Что показывает

1. **Side-by-side** — два iframe, один над другим / рядом, одинаковый scroll.
2. **DOM diff** — какие узлы добавили/удалили/поменяли.
3. **Pixel diff** — оверлей с подсветкой, что отличается.
4. **Style diff** — изменения в computed styles (color, font-size, padding...).

## Структура

```
comparison/
  index.html          ← главная
  before.html         ← (или any path)
  after.html
  diff-engine.js      ← логика
```

## index.html

```html
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Comparison</title>
  <style>
    body { display: grid; grid-template: auto 1fr / 1fr 1fr; height: 100vh; margin: 0; font: 13px ui-monospace, monospace; gap: 1px; background: #888; }
    h2 { margin: 0; padding: 8px 16px; background: #222; color: #fff; font-size: 12px; font-weight: normal; }
    iframe { width: 100%; height: 100%; border: 0; background: #fff; }
    .toolbar { grid-column: 1 / -1; padding: 8px 16px; background: #fafafa; border-bottom: 1px solid #ddd; display: flex; gap: 16px; align-items: center; }
    .mode { display: flex; gap: 4px; }
    .mode button { padding: 4px 12px; border: 1px solid #ccc; background: #fff; cursor: pointer; }
    .mode button.active { background: #111; color: #fff; }
    .stats { color: #888; }
    .stats b { color: #111; }
  </style>
</head>
<body>
  <div class="toolbar">
    <strong>Comparison</strong>
    <div class="mode" id="mode">
      <button data-mode="side"    class="active">Side by side</button>
      <button data-mode="overlay">Overlay diff</button>
      <button data-mode="dom">DOM tree</button>
    </div>
    <span class="stats" id="stats">Loading…</span>
  </div>
  <h2>Before</h2>
  <h2>After</h2>
  <iframe id="a" src="before.html"></iframe>
  <iframe id="b" src="after.html"></iframe>

  <script src="diff-engine.js" defer></script>
</body>
</html>
```

## diff-engine.js (минимум)

```js
// 1. Sync scroll
function syncScroll() {
  const a = document.getElementById('a').contentWindow;
  const b = document.getElementById('b').contentWindow;
  let last = 0, fromA = false;
  a.addEventListener('scroll', () => {
    if (Date.now() - last < 50 && !fromA) return;
    fromA = true; b.scrollTo(0, a.scrollY); last = Date.now();
    setTimeout(() => fromA = false, 100);
  });
  b.addEventListener('scroll', () => {
    if (Date.now() - last < 50 && fromA) return;
    a.scrollTo(0, b.scrollY); last = Date.now();
  });
}

// 2. DOM diff (rough)
function domDiff() {
  const ad = document.getElementById('a').contentDocument;
  const bd = document.getElementById('b').contentDocument;
  const aSet = new Set([...ad.querySelectorAll('*')].map(el => el.tagName + (el.id ? '#' + el.id : '') + ' ' + el.className));
  const bSet = new Set([...bd.querySelectorAll('*')].map(el => el.tagName + (el.id ? '#' + el.id : '') + ' ' + el.className));
  const removed = [...aSet].filter(x => !bSet.has(x));
  const added   = [...bSet].filter(x => !aSet.has(x));
  return { added, removed };
}

// 3. Stats
window.addEventListener('load', () => {
  document.getElementById('a').addEventListener('load', update);
  document.getElementById('b').addEventListener('load', update);
  syncScroll();
  function update() {
    try {
      const d = domDiff();
      const stats = document.getElementById('stats');
      stats.innerHTML = `<b>+${d.added.length}</b> added · <b>-${d.removed.length}</b> removed`;
    } catch (e) { /* not loaded yet */ }
  }
});
```

## Pixel diff (overlay-режим)

Через Playwright (или html-to-image в браузере):

```js
// templates/pixel-diff.mjs
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import fs from 'node:fs/promises';

const [a, b] = process.argv.slice(2);
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });

async function shoot(file) {
  const page = await ctx.newPage();
  await page.goto(`file://${process.cwd()}/${file}`, { waitUntil: 'networkidle' });
  const buf = await page.screenshot({ fullPage: true });
  await page.close();
  return PNG.sync.read(buf);
}

const imgA = await shoot(a);
const imgB = await shoot(b);
await browser.close();

const { width, height } = imgA;
const diff = new PNG({ width, height });
const pixels = pixelmatch(imgA.data, imgB.data, diff.data, width, height, { threshold: 0.1 });
await fs.writeFile('diff.png', PNG.sync.write(diff));
console.log(`${pixels} pixels differ. → diff.png`);
```

```bash
npm i pixelmatch pngjs playwright
node pixel-diff.mjs before.html after.html
```

## DOM tree mode

Для глубокого diff'а — text-based рекурсивный обход:

```js
function tree(el, depth = 0) {
  let s = '  '.repeat(depth) + el.tagName.toLowerCase();
  if (el.id) s += '#' + el.id;
  if (el.className) s += '.' + [...el.classList].slice(0,2).join('.');
  s += '\n';
  for (const c of el.children) s += tree(c, depth + 1);
  return s;
}

const treeA = tree(ad.body);
const treeB = tree(bd.body);
// → unified diff (через `diff` lib)
```

```bash
npm i diff
```

```js
import { diffLines } from 'diff';
const out = diffLines(treeA, treeB);
out.forEach(p => console.log((p.added ? '+' : p.removed ? '-' : ' ') + p.value.split('\n').join('\n' + (p.added?'+':p.removed?'-':' '))));
```

## Workflow

1. До правок → `cp index.html .compare/before.html`.
2. Делаешь правки.
3. После → `cp index.html .compare/after.html`.
4. Открой `.compare/index.html` в браузере → side-by-side.
5. (опционально) `node pixel-diff.mjs ...` для overlay.

## Ограничения

- Cross-origin: если артефакты загружают разные origin'ы — sync scroll работает, DOM diff может упасть. Локальные файлы через `file://` работают.
- Лучше работает на статичных HTML. Анимированные / интерактивные требуют paused state для diff.

## Антипаттерны

- ❌ Использовать как замену git diff. Текстовый diff информативнее для кода.
- ❌ Пытаться сравнить два production-сайта на разных доменах — упрётся в CORS.
- ❌ Pixel diff на каждый тривиальный изменение шрифта — даёт огромную разницу. Используй с порогом и для крупных правок.
