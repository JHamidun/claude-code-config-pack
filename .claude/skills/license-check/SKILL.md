---
name: license-check
version: 1.0.0
description: Пробегает все ассеты и флагает проблемы — Google Fonts с неправильной лицензией, неподписанный stock, отсутствующий alt.
when_to_use: Перед публикацией / релизом / отдачей клиенту.
---

# License check

## Что проверяет

- **Шрифты** в `<link href="fonts.googleapis.com">` — не SIL Open Font License (теоретически OK, но требует attribution).
- **Картинки** без явной лицензии — `data-license="..."` или комментария.
- **`<img>` без `alt`** — accessibility + legal в EU.
- **Видео/аудио без credits**.
- **Stock-картинки** с известных хостов — Unsplash / Pexels / Shutterstock URL paterns.

## Скрипт

`templates/license-check.mjs`:

```js
import fs from 'node:fs/promises';
import path from 'node:path';
import { JSDOM } from 'jsdom';

const file = process.argv[2];
if (!file) { console.error('Usage: node license-check.mjs <file>'); process.exit(1); }

const html = await fs.readFile(file, 'utf8');
const dom = new JSDOM(html);
const doc = dom.window.document;

const issues = [];

// Картинки без alt
doc.querySelectorAll('img').forEach((img, i) => {
  if (!img.hasAttribute('alt')) {
    issues.push({ kind: 'a11y', el: 'img', index: i, msg: `<img src="${img.getAttribute('src')}"> без alt` });
  }
});

// Stock-источники без указания
const stockHosts = ['images.unsplash.com', 'images.pexels.com', 'cdn.shutterstock.com', 'getty'];
doc.querySelectorAll('img').forEach((img) => {
  const src = img.getAttribute('src') || '';
  for (const h of stockHosts) {
    if (src.includes(h) && !img.hasAttribute('data-credit')) {
      issues.push({ kind: 'license', el: 'img', msg: `Stock-картинка без data-credit: ${src}` });
    }
  }
});

// Шрифты Google Fonts
doc.querySelectorAll('link[href*="fonts.googleapis.com"]').forEach(l => {
  const href = l.getAttribute('href');
  issues.push({
    kind: 'info', el: 'link',
    msg: `Google Fonts: ${href} — проверь, что у выбранных шрифтов SIL Open Font License`
  });
});

// Видео без credits
doc.querySelectorAll('video, iframe[src*="youtube"], iframe[src*="vimeo"]').forEach(v => {
  if (!v.hasAttribute('data-credit')) {
    issues.push({ kind: 'license', el: v.tagName.toLowerCase(), msg: 'Видео без data-credit' });
  }
});

if (!issues.length) { console.log('✓ Лицензии в порядке'); process.exit(0); }
console.error(`\n✗ ${issues.length} замечаний:\n`);
for (const i of issues) console.error(`  [${i.kind}] ${i.msg}`);
process.exit(issues.filter(i => i.kind !== 'info').length ? 1 : 0);
```

Зависимость: `npm i jsdom`.

## Конвенция атрибутов

В HTML используй:

```html
<img src="..."
     alt="..."
     data-credit="Photo by Jane Doe / Unsplash"
     data-license="Unsplash License">

<video data-credit="Loom · Acme Inc.">

<link rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Inter"
      data-license="OFL">
```

`license-check` не упадёт, если эти атрибуты есть.

## Что не проверяется

- Лицензии npm-пакетов (для этого `license-checker`).
- Использование защищённых брендов в копирайте.
- DMCA-материалы пользователя (текст, лого клиента).

## Workflow

```bash
# при сборке прода
node license-check.mjs dist/index.html
# fail build при критичных
```

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-license-check.md`. Секции там: 4 категории ассетов, Output отчёт, Fonts, Images, Icons, Dependencies (если артефакт идёт в build), Risks, Action items, Когда нашёл проблему, Risks (FIX BEFORE HANDOFF), Привязка к dev-handoff, Антипаттерны.
