---
name: proto-smoketest
description: Минимальные e2e-тесты для прототипа — критичные пути не отвалились. Не unit-тесты, а защита от регрессий.
when_to_use: Прототип большой, итераций много, и хочется быстро ловить когда сломалось.
---

# Proto smoketest

Не пытайся писать unit-тесты для прототипа — это не production. Зато 5 e2e-проверок «не сломалось ли главное» окупаются с первой регрессии.

## Стек

Playwright Test — самый простой запуск.

```bash
npm i -D @playwright/test
npx playwright install chromium
```

## smoketest.spec.js

`templates/smoketest.spec.js`:

```js
import { test, expect } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const FILE = pathToFileURL(path.resolve('proto.html')).href;

test('страница загружается без console error', async ({ page }) => {
  const errors = [];
  page.on('console', m => m.type() === 'error' && errors.push(m.text()));
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(FILE);
  await page.waitForLoadState('networkidle');
  expect(errors, errors.join('\n')).toEqual([]);
});

test('главный CTA ведёт на следующий экран', async ({ page }) => {
  await page.goto(FILE);
  await page.click('text=Начать');
  await expect(page.locator('h1')).toContainText('Шаг 1');
});

test('форма входа принимает email и password', async ({ page }) => {
  await page.goto(FILE);
  await page.click('text=Войти');
  await page.fill('input[type=email]', 'test@test.ru');
  await page.fill('input[type=password]', 'password123');
  await page.click('button[type=submit]');
  await expect(page).toHaveURL(/dashboard/);
});

test('навигация по табам работает', async ({ page }) => {
  await page.goto(FILE + '#dashboard');
  for (const tab of ['Главная', 'Лента', 'Профиль']) {
    await page.click(`role=tab[name=${tab}]`);
    await expect(page.locator(`[role=tabpanel][aria-label=${tab}]`)).toBeVisible();
  }
});

test('тёмная тема переключается', async ({ page }) => {
  await page.goto(FILE);
  await page.click('#theme-toggle');
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  expect(bg).toMatch(/rgb\(\s*(\d+)/);
  // Просто проверяем, что фон стал тёмным:
  const [r,g,b] = bg.match(/\d+/g).map(Number);
  expect(r + g + b).toBeLessThan(150);
});
```

```bash
npx playwright test smoketest.spec.js
```

## Что покрывать

5–10 ключевых сценариев. **Не** покрывай каждый клик.

Хорошие кандидаты:
- ✅ Прототип вообще открывается без ошибок.
- ✅ Главный путь от первого экрана до целевого.
- ✅ Самые ломкие переходы (после большого UI-рефакторинга).
- ✅ Форма с валидацией.
- ✅ Тёмная/светлая тема.

Плохие:
- ❌ Каждый текст в каждом блоке (это уже unit-тест).
- ❌ Анимации (хрупко, ломается на каждом изменении CSS).
- ❌ Точные пиксельные значения (нет смысла).

## Снимки UI

Опционально — снимки экранов для визуальной регрессии:

```js
test('скриншот главной страницы', async ({ page }) => {
  await page.goto(FILE);
  await expect(page).toHaveScreenshot('home.png', { maxDiffPixels: 100 });
});
```

При первом запуске Playwright создаст baseline. При следующих — сравнит. Чувствительность настраивается через `maxDiffPixels` / `threshold`.

## Когда запускать

- Перед сдачей пользователю — обязательно.
- После каждого крупного рефакторинга.
- В CI, если репо приватный (для прототипа CI обычно избыточен).

## Когда НЕ нужно

- Прототип на 1 день.
- Один экран без интерактива.
- Дек слайдов.
- Анимация-видео.

## Поддержка

Тесты — тоже код. Если не обновляешь их вместе с прототипом, они становятся ложными срабатываниями. Лучше **меньше** актуальных, чем больше устаревших.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-proto-smoketest.md`. Секции там: Инсталляция, Структура, Какие сценарии писать, Что НЕ тестировать, Selectors — best practices, Multi-viewport, Скриншот failures, CI integration, Output: PASS / FAIL, Когда НЕ запускать, Антипаттерны.
