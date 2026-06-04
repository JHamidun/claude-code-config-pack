---
name: screenshot-test
description: Pixel-diff между текущим и эталонным скриншотом. Падает, если артефакт визуально сломался.
when_to_use: CI / pre-commit для дизайн-системы, лендинга, ключевых экранов прототипа.
---

# Screenshot test

Регрессионный тест. Эталонный скриншот хранится в репо. Каждый раз перед коммитом / в CI — снимаем новый, сравниваем по пикселям. Если разница > порога — fail.

## Установка

```bash
npm i -D playwright pixelmatch pngjs
npx playwright install chromium
```

## Структура

```
screenshots/
  baseline/
    home-1280.png       ← эталоны, в репо
    home-mobile.png
  current/              ← gitignored
    home-1280.png       ← снятые в этом ране
  diff/                 ← gitignored
    home-1280.png       ← подсвеченные различия (если есть)
test-screenshots.config.json
```

## Конфиг

`test-screenshots.config.json`:
```json
{
  "tests": [
    { "name": "home-1280",   "url": "index.html",          "viewport": [1280, 800] },
    { "name": "home-mobile", "url": "index.html",          "viewport": [390, 844] },
    { "name": "settings",    "url": "index.html#settings", "viewport": [1280, 800] }
  ],
  "threshold": 0.1,
  "maxDiffPixels": 200
}
```

## Скрипт

`templates/test.mjs`:

```js
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import fs from 'node:fs/promises';
import path from 'node:path';

const cfg = JSON.parse(await fs.readFile('test-screenshots.config.json', 'utf8'));
const isUpdate = process.argv.includes('--update');

const baseDir = 'screenshots/baseline';
const curDir  = 'screenshots/current';
const diffDir = 'screenshots/diff';
await fs.mkdir(curDir, { recursive: true });
await fs.mkdir(diffDir, { recursive: true });

const browser = await chromium.launch();
let failures = 0;

for (const t of cfg.tests) {
  const ctx = await browser.newContext({ viewport: { width: t.viewport[0], height: t.viewport[1] } });
  const page = await ctx.newPage();
  await page.goto(`file://${path.resolve(t.url)}`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts && document.fonts.ready);

  const curPath  = path.join(curDir,  t.name + '.png');
  const basePath = path.join(baseDir, t.name + '.png');

  await page.screenshot({ path: curPath, fullPage: true });
  await ctx.close();

  if (isUpdate) {
    await fs.mkdir(baseDir, { recursive: true });
    await fs.copyFile(curPath, basePath);
    console.log(`✓ Updated baseline: ${t.name}`);
    continue;
  }

  let basePNG;
  try { basePNG = PNG.sync.read(await fs.readFile(basePath)); }
  catch { console.error(`✗ ${t.name}: no baseline. Run with --update.`); failures++; continue; }

  const curPNG = PNG.sync.read(await fs.readFile(curPath));
  if (basePNG.width !== curPNG.width || basePNG.height !== curPNG.height) {
    console.error(`✗ ${t.name}: size mismatch ${basePNG.width}x${basePNG.height} vs ${curPNG.width}x${curPNG.height}`);
    failures++;
    continue;
  }

  const { width, height } = basePNG;
  const diffPNG = new PNG({ width, height });
  const px = pixelmatch(basePNG.data, curPNG.data, diffPNG.data, width, height, { threshold: cfg.threshold });

  if (px > cfg.maxDiffPixels) {
    const diffPath = path.join(diffDir, t.name + '.png');
    await fs.writeFile(diffPath, PNG.sync.write(diffPNG));
    console.error(`✗ ${t.name}: ${px} px differ (max ${cfg.maxDiffPixels}). diff → ${diffPath}`);
    failures++;
  } else {
    console.log(`✓ ${t.name}: ${px} px (within ${cfg.maxDiffPixels})`);
  }
}

await browser.close();
process.exit(failures ? 1 : 0);
```

## Использование

```bash
# Первый запуск — создать baseline
node test.mjs --update

# Дальше — проверка
node test.mjs
# ✓ home-1280: 12 px (within 200)
# ✓ home-mobile: 0 px
# ✗ settings: 4521 px differ. diff → screenshots/diff/settings.png

# Когда визуальные изменения **намеренные**:
node test.mjs --update     # обновить baseline
git add screenshots/baseline
git commit -m "Update screenshots: redesigned settings"
```

## .gitignore

```
screenshots/current/
screenshots/diff/
```

`baseline/` — в репо.

## Pre-commit hook

`.husky/pre-commit`:
```bash
#!/bin/sh
node test.mjs || (echo "Screenshot test failed. Review diff/, run --update if intended."; exit 1)
```

## CI (GitHub Actions)

```yaml
- run: npm ci
- run: npx playwright install --with-deps chromium
- run: node test.mjs
- if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: screenshot-diffs
    path: screenshots/diff/
```

## Стабилизация скриншотов

Pixel-diff чувствителен к шуму. Чтобы тесты не флакали:

1. **Отключи анимации** перед скриншотом:
   ```js
   await page.addStyleTag({ content: `*, *::before, *::after { transition: none !important; animation: none !important; }` });
   ```

2. **Подожди шрифты**:
   ```js
   await page.evaluate(() => document.fonts && document.fonts.ready);
   ```

3. **Скрой курсор / каретки**:
   ```js
   await page.addStyleTag({ content: `* { caret-color: transparent !important; }` });
   ```

4. **Фиксированная dpr**: viewport: { ..., deviceScaleFactor: 2 }.

5. **Stub time** для динамических виджетов (часы, "X minutes ago"):
   ```js
   await page.addInitScript(() => Date.now = () => 1700000000000);
   ```

## Антипаттерны

- ❌ Делать порог `maxDiffPixels: 0` — будет флакать на любую антиалиас-разницу.
- ❌ Хранить baseline для viewport >2K — огромные файлы. Достаточно 1280px.
- ❌ Тестировать SPA с anim splash без отключения анимаций — каждый ран новые пиксели.
- ❌ Игнорировать diff/ когда тест зафейлил — всегда проверь визуально, что разница ожидаемая.

## Когда **не** использовать

- Артефакты с реальными данными от API — содержимое меняется.
- Анимированные постеры — снимай конкретный кадр или не тестируй.
- Лёгкие правки (один цвет) — overhead не оправдан.

## Связь со скиллами

- `verifier` запускает раз, screenshot-test — регулярно.
- `comparison-mode` — для ручного diff'а перед обновлением baseline.
- `a11y-audit` — комплементарно: визуал + структура.
