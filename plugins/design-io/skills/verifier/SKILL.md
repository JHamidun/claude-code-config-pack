---
name: verifier
description: Headless-проверка HTML артефакта — открыть в Chromium, прочитать console (errors / warnings), сделать скриншот для review, проверить network errors. Финальный gate перед handoff.
when_to_use: После каждого крупного изменения в HTML/JSX, перед export, перед демонстрацией юзеру. Должен запускаться автоматически design-orchestrator после finalize.
---

# Verifier

Открывает артефакт в headless Chromium, проверяет ничего ли не сломалось, делает референсный скриншот.

## Зависимости

```bash
npm i -D playwright
npx playwright install chromium
```

Или через cli:
```bash
npm exec --package=playwright -- playwright install chromium
```

## Базовый verifier

`scripts/verify.js`:

```js
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function verify(htmlPath, opts = {}) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const errors = [];
  const warnings = [];
  const networkErrors = [];

  page.on('pageerror', (e) => errors.push({ msg: e.message, stack: e.stack }));
  page.on('console', (msg) => {
    const t = msg.type();
    if (t === 'error') errors.push({ msg: msg.text() });
    else if (t === 'warning') warnings.push({ msg: msg.text() });
  });
  page.on('requestfailed', (req) => {
    networkErrors.push({ url: req.url(), failure: req.failure()?.errorText });
  });

  const url = `file://${path.resolve(htmlPath)}`;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(opts.wait || 1000);

  // Скриншот для review
  const out = opts.screenshot || htmlPath.replace(/\.html$/, '.verify.png');
  await page.screenshot({ path: out, fullPage: true });

  // Меряем размер DOM (если очень большой — проблема)
  const domSize = await page.evaluate(() => document.querySelectorAll('*').length);

  await browser.close();

  return {
    file: htmlPath,
    screenshot: out,
    errors, warnings, networkErrors,
    domSize,
    passed: errors.length === 0 && networkErrors.length === 0,
  };
}

if (require.main === module) {
  verify(process.argv[2]).then((r) => {
    console.log(JSON.stringify(r, null, 2));
    process.exit(r.passed ? 0 : 1);
  });
}

module.exports = { verify };
```

```bash
node scripts/verify.js path/to/artifact.html
```

## Что проверяет

| Чек | Хорошо | Плохо |
|---|---|---|
| Console errors | 0 | >0 → fix |
| Console warnings | 0-2 | >5 → review (часто React StrictMode noise) |
| Network errors | 0 | >0 → ассет не загрузился |
| Page errors (uncaught) | 0 | >0 → JS sintax broke |
| DOM size | <2000 nodes | >5000 → производительность падает |
| Screenshot | визуально корректный | пустой / overflow / layout broken |

## Скриншот для review

`<artifact>.verify.png` — приложи к ответу юзеру:
> «Готово. Скриншот ниже. 0 errors, 1 warning (React 18 deprecation, безопасно).»

Юзер видит результат сразу, не открывая файл.

## Multi-viewport проверка

```js
const viewports = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet',  width: 768,  height: 1024 },
  { name: 'mobile',  width: 375,  height: 812 },
];

for (const vp of viewports) {
  await page.setViewportSize({ width: vp.width, height: vp.height });
  await page.screenshot({ path: `${out}.${vp.name}.png`, fullPage: true });
}
```

## Custom assertions

Можно расширить под конкретный артефакт:

```js
// Проверить что hero имеет нужный текст
const heroText = await page.locator('.hero h1').textContent();
if (!heroText.includes('ExampleProduct')) throw new Error('Hero text missing');

// Проверить что есть нужное число секций
const sections = await page.locator('section').count();
if (sections < 8) throw new Error(`Expected 8+ sections, got ${sections}`);

// Проверить что тёмная тема активна (если применимо)
const bg = await page.locator('body').evaluate(el => getComputedStyle(el).background);
if (!bg.includes('rgb(1, 3, 52)')) throw new Error('Dark theme not applied');
```

## Когда запускать

| Триггер | Что проверяем |
|---|---|
| После генерации каждого артефакта | базовый verifier (errors+screenshot) |
| Перед export-pdf / export-pptx | full verifier + multi-viewport |
| Перед dev-handoff | + a11y-audit + perf-audit |
| Перед демонстрацией юзеру | + custom assertions |

## Не путать с

- `a11y-audit` — accessibility-специфичный, использует axe-core
- `perf-audit` — Lighthouse метрики
- `proto-smoketest` — E2E кликабельный тест (не просто открыл и посмотрел)

## Антипаттерны

- Не запускать verifier и сдавать → проблемы вылезают у юзера на показе
- Игнорировать console.warning'и → когда станут errors не заметишь
- Проверять только desktop → mobile сломается у юзера
- Делать скриншот не fullpage → пропустишь нижние секции
- Запускать verifier на `localhost:3000` без проверки что сервер up → false positives
- Не возвращать exit 1 при failures → CI пропускает сломанные артефакты
