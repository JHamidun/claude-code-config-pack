<!-- LEGACY: полное тело скилла 'export-png' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: export-png
description: HTML → PNG (один или серия). Для socialmedia (Twitter/Instagram/LinkedIn cover), pre-views в Figma / Notion, отдельных слайдов как картинки.
when_to_use: Юзер просит «сохрани как картинку», «PNG для Twitter», «обложку», «превью каждого слайда отдельно». Через Playwright headless.
---

# Export PNG

Один кадр или серия. Размер указывается явно (1200×675, 1080×1080, etc).

## Базовый каркас

`scripts/export-png.js`:
```js
const { chromium } = require('playwright');
const path = require('path');

async function exportPng(htmlPath, opts = {}) {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: opts.width || 1200, height: opts.height || 675 },
    deviceScaleFactor: opts.scale || 2,   // retina, 2x = 2400x1350 actual
  });

  await page.goto(`file://${path.resolve(htmlPath)}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(opts.wait || 1000);

  const out = opts.out || htmlPath.replace(/\.html$/, '.png');
  await page.screenshot({
    path: out,
    omitBackground: opts.transparent || false,
    fullPage: opts.fullPage || false,
    clip: opts.clip,  // { x, y, width, height } для частичного export
  });

  await browser.close();
  return out;
}

if (require.main === module) {
  const [html, w, h] = process.argv.slice(2);
  exportPng(html, { width: +w || 1200, height: +h || 675 })
    .then(out => console.log(`✓ ${out}`));
}

module.exports = { exportPng };
```

```bash
node scripts/export-png.js cover.html 1200 675
node scripts/export-png.js cover.html 1080 1080  # square для Instagram
```

## Стандартные размеры social

| Платформа | Размер | Aspect |
|---|---|---|
| Twitter/X cover (post) | 1200×675 | 16:9 |
| Twitter/X profile | 400×400 | 1:1 |
| Twitter/X header | 1500×500 | 3:1 |
| LinkedIn post | 1200×627 | 1.91:1 |
| LinkedIn header | 1584×396 | 4:1 |
| Instagram square | 1080×1080 | 1:1 |
| Instagram portrait | 1080×1350 | 4:5 |
| Instagram story / Reels | 1080×1920 | 9:16 |
| TikTok | 1080×1920 | 9:16 |
| YouTube cover | 1280×720 | 16:9 |
| YouTube thumbnail | 1280×720 | 16:9 |
| Facebook post | 1200×630 | 1.91:1 |
| Telegram channel post | 1280×720 | 16:9 |
| Email header | 600×200 | 3:1 |
| Open Graph (og:image) | 1200×630 | 1.91:1 |

## Серия из шаблона

Если есть один HTML-template и нужно сделать N вариантов с разными данными:

```js
const items = [
  { title: 'AI Agents', date: '(see git history)', cover: 'cover-1.png' },
  { title: 'RAG Architecture', date: '2026-05-06', cover: 'cover-2.png' },
  { title: 'Prompt Engineering', date: '2026-05-13', cover: 'cover-3.png' },
];

for (const item of items) {
  const url = `file://template.html?title=${encodeURIComponent(item.title)}&date=${item.date}`;
  await page.goto(url);
  await page.screenshot({ path: item.cover });
}
```

В template.html — JS читает URL params и вписывает в `<h1>`, `<time>`, etc:
```js
const params = new URL(location).searchParams;
document.querySelector('h1').textContent = params.get('title');
document.querySelector('time').textContent = params.get('date');
```

## Серия слайдов как PNG

Из артефакта `slides`:
```js
const total = await page.locator('.slide').count();
for (let i = 1; i <= total; i++) {
  await page.goto(`${url}?slide=${i}&print=1`);
  await page.waitForTimeout(300);
  await page.screenshot({
    path: `slides/slide-${String(i).padStart(2, '0')}.png`,
    clip: { x: 0, y: 0, width: 1920, height: 1080 },
  });
}
```

Получаешь `slide-01.png … slide-12.png` — для PPTX (см. `export-pptx`) или для отдельной публикации.

## Качество vs размер файла

| Параметр | Качество | Размер |
|---|---|---|
| `deviceScaleFactor: 1` | стандарт | минимум |
| `deviceScaleFactor: 2` | retina | 4× |
| `deviceScaleFactor: 3` | mobile retina | 9× |
| `omitBackground: true` | прозрачный PNG | + |
| `type: 'jpeg', quality: 80` | JPEG instead | -50% |

Для retina на social — `scale: 2` хороший компромисс. >2 редко нужно.

## Прозрачный PNG

```js
await page.screenshot({
  path: 'logo.png',
  omitBackground: true,
});
```

В HTML body не должно быть `background-color`. CSS:
```css
body { background: transparent; }
```

## После export — оптимизация

```bash
# Уменьшить размер без потери качества
npx sharp -i source.png -o source.png  # перезаписать с дефолтной optimization
# или
npx imagemin source.png --plugin=pngquant > source-min.png
```

Типичная экономия: 40-70% размера без видимой потери.

## Антипаттерны

- Размер из головы (1080×800) → не подходит ни одной платформе → переэкспортировать
- `fullPage: true` на canvas-design (длинная страница) → 5000px высоты, 30MB
- Не дождаться шрифтов → fallback в PNG
- Включить scrollbars в скриншот → грязная картинка
- Использовать JPEG для UI с текстом → артефакты компрессии вокруг букв
- Не вычистить anti-aliasing на ровных линиях → blurry edges
- 4× scale на Twitter cover → файл 8MB, Twitter режет качество всё равно
