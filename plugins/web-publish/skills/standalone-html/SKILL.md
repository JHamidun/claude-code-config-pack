---
name: standalone-html
description: "Свернуть HTML со всеми ассетами в один офлайн-файл (inline base64). Триггеры: «один файл html», «self-contained», «чтобы можно было отправить»."
---

# Standalone HTML

Inline-вшивает в один HTML все локальные ресурсы: CSS, JS, изображения, шрифты.

## Скрипт

Готового файла в навыке НЕТ (каталога `templates/` тоже) — код ниже сохрани сам
рядом с обрабатываемым HTML как `inline.mjs`, оттуда и запускай.

```js
import fs from 'node:fs/promises';
import path from 'node:path';

const [, , input, output] = process.argv;
if (!input) { console.error('Usage: node inline.mjs <input.html> [output.html]'); process.exit(1); }

const out = output || input.replace(/\.html?$/, '.standalone.html');
const dir = path.dirname(input);
let html = await fs.readFile(input, 'utf8');

// <link rel="stylesheet" href="..."> → <style>
html = await replaceAsync(html, /<link\s+[^>]*rel=["']stylesheet["'][^>]*>/gi, async (tag) => {
  const m = tag.match(/href=["']([^"']+)["']/);
  if (!m || /^https?:|\/\//.test(m[1])) return tag;
  // url(...) внутри CSS отсчитывается от САМОГО CSS, а не от HTML — базу берём по файлу стиля
  const cssPath = path.join(dir, m[1]);
  const css = await inlineUrls(await fs.readFile(cssPath, 'utf8'), path.dirname(cssPath), false);
  return `<style>\n${css}\n</style>`;
});

// <script src="..."> → <script>...</script>
html = await replaceAsync(html, /<script\s+[^>]*src=["']([^"']+)["'][^>]*>\s*<\/script>/gi, async (tag, src) => {
  if (/^https?:|\/\//.test(src)) return tag;
  const code = await fs.readFile(path.join(dir, src), 'utf8');
  const typeMatch = tag.match(/type=["']([^"']+)["']/);
  const type = typeMatch ? ` type="${typeMatch[1]}"` : '';
  return `<script${type}>\n${code}\n</script>`;
});

// <img src="..."> → data URL
html = await replaceAsync(html, /<img\s+[^>]*src=["']([^"']+)["'][^>]*>/gi, async (tag, src) => {
  if (/^https?:|\/\/|data:/.test(src)) return tag;
  try {
    const buf = await fs.readFile(path.join(dir, src));
    const ext = path.extname(src).slice(1).toLowerCase() || 'png';
    const mime = { svg: 'svg+xml', jpg: 'jpeg', jpeg: 'jpeg', png: 'png', webp: 'webp', gif: 'gif' }[ext] || 'octet-stream';
    const data = `data:image/${mime};base64,${buf.toString('base64')}`;
    return tag.replace(src, data);
  } catch { return tag; }
});

// url(...), написанные прямо в <style> самого HTML — база тут и правда каталог HTML
html = await inlineUrls(html, dir);

await fs.writeFile(out, html);
console.log('✓', out);

// warn=false на первом (CSS-относительном) проходе: непойманное добьёт финальный проход от HTML
async function inlineUrls(css, baseDir, warn = true) {
  return replaceAsync(css, /url\(["']?([^"')]+)["']?\)/g, async (m, src) => {
    if (/^https?:|\/\/|data:|^#/.test(src)) return m;
    try {
      const buf = await fs.readFile(path.resolve(baseDir, src));
      const ext = path.extname(src).slice(1).toLowerCase();
      const mime = ({ woff2: 'font/woff2', woff: 'font/woff', ttf: 'font/ttf',
        svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg' })[ext] || 'application/octet-stream';
      return `url("data:${mime};base64,${buf.toString('base64')}")`;
    } catch {
      // молча оставлять ссылку нельзя: файл уедет получателю без фона/шрифта
      if (warn) console.warn('! не вшит ассет:', src, '(искал от', baseDir + ')');
      return m;
    }
  });
}

async function replaceAsync(str, re, fn) {
  const promises = [];
  str.replace(re, (...args) => { promises.push(fn(...args)); return ''; });
  const results = await Promise.all(promises);
  let i = 0;
  return str.replace(re, () => results[i++]);
}
```

## Запуск

```bash
node inline.mjs deck.html
# → deck.standalone.html
```

## Ограничения

- Внешние URL (`https://...`) скрипт не трогает — они останутся ссылками. Если нужен полный офлайн — заранее скачай шрифты и CDN-скрипты в проект.
- `<iframe src="...">` не разворачивается. iframe-вариантные канвасы (см. `design-canvas`) теряют содержимое — для них либо инлайнь HTML внутрь, либо отдай ZIP.
- Размер: один HTML с шрифтами и картинками легко вырастает до 5–10 MB. Для отправки по почте оставь ассеты во внешних папках или сожми изображения.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-standalone-html.md`. Секции там: Какие inline'ятся, Каркас inliner script, CDN scripts — оставлять или embedd'ить?, Размеры — что разумно, Verifier для standalone, Когда НЕ делать standalone, Stacking, Антипаттерны.
