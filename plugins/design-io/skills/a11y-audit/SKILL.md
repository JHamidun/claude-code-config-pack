---
name: a11y-audit
version: 1.0.0
description: "Прогон axe-core в headless: отчёт по WCAG-нарушениям готовой страницы. Триггеры: «проверь accessibility», «WCAG», «контраст AA». НЕ как размечать форму→forms-a11y."
---

# A11y audit

`axe-core` — индустриальный стандарт. Запускается в headless-Chrome через Playwright.

## Граница с `forms-a11y`: измеритель против рецепта

Оба скилла про accessibility, и по слову «доступность» подходят одинаково — поэтому их
путают. Различает их не тема, а **на что ты смотришь в момент вызова**: на готовую
страницу («проверь, что получилось») — сюда; на пустой редактор («как правильно
разметить это поле») — в `forms-a11y`. Здесь нечего писать, там нечего запускать.

Важнее другое: **зелёный axe не означает, что форма доступна.** Секция «Что axe не
ловит» ниже — это ровно та зона, за которую отвечает `forms-a11y`: смысловое
соответствие label полю, перевод фокуса после сабмита, конкретность текста ошибки,
проход с клавиатуры. axe видит наличие атрибута, а не то, верен ли он. Поэтому на
форме порядок такой: сперва разметить по `forms-a11y`, потом прогнать axe отсюда, и
после зелёного прогона всё равно пройти ручной чек-лист из конца этого файла.

## Установка

```bash
npm i -D playwright @axe-core/playwright
npx playwright install chromium
```

## Скрипт

`templates/a11y.mjs`:

```js
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const file = process.argv[2];
if (!file) { console.error('Usage: node a11y.mjs <file>'); process.exit(1); }

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });

const results = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
  .analyze();

await browser.close();

await fs.writeFile('a11y-report.json', JSON.stringify(results, null, 2));

const v = results.violations;
if (!v.length) {
  console.log('✓ Нет нарушений WCAG AA');
  process.exit(0);
}

console.error(`\n✗ ${v.length} категорий нарушений:\n`);
for (const violation of v) {
  console.error(`  [${violation.impact}] ${violation.id} — ${violation.help}`);
  console.error(`    ${violation.helpUrl}`);
  for (const node of violation.nodes.slice(0, 3)) {
    console.error(`    → ${node.target.join(' ')}`);
    console.error(`      ${node.failureSummary.split('\n')[0]}`);
  }
  if (violation.nodes.length > 3) console.error(`    ...и ещё ${violation.nodes.length - 3}`);
  console.error('');
}
process.exit(1);
```

## Использование

```bash
node a11y.mjs index.html
```

Exit code 1 при наличии violations — встраивай в CI / pre-commit.

## Категории нарушений (по impact)

- **critical** — экран нечитаем для скрин-ридера. Чинить сразу.
- **serious** — недоступен для подмножества пользователей.
- **moderate** — деградация опыта.
- **minor** — best practice.

При сдаче — 0 critical и 0 serious. Moderate допустимо обсуждать.

## Что axe **не** ловит

- Логические ошибки (label не соответствует полю смыслом).
- Visual contrast динамических элементов (hover, focus).
- Доступность кастомных ARIA-паттернов (только проверка наличия атрибутов).
- Реальное взаимодействие с клавиатуры.

Если непройденное — форма, чинится это не здесь: разметка label/`aria-describedby`/
`fieldset`, конкретный текст ошибки и перевод фокуса после сабмита — в `forms-a11y`.

Для последнего — отдельный manual-чек:
1. Tab через всё. Видно ли, где фокус?
2. Можно ли активировать каждый элемент с клавиатуры?
3. Закрывается ли модалка по Escape?
4. Tab в модалке закольцован (focus trap)?

## Интеграция с verifier

В `verifier/templates/verify.mjs` добавь флаг `--a11y`:
```js
if (args.a11y) {
  const a11y = await new AxeBuilder({ page }).analyze();
  if (a11y.violations.length) problems.push(...);
}
```
