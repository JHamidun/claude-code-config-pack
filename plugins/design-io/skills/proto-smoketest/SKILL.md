---
name: proto-smoketest
description: "Smoke-тесты прототипа: 5-10 критичных путей не отвалились, не unit. Триггеры: «playwright smoke», «happy path тест». НЕ разовая проверка файла→verifier."
---

# Proto smoketest

Не пытайся писать unit-тесты для прототипа — это не production. Зато 5 e2e-проверок «не сломалось ли главное» окупаются с первой регрессии.

## Место в предсдаточном прогоне

Этот скилл — одна строка из общего набора проверок; какие ещё звать под твой тип
артефакта и **в каком порядке** — матрица в `verifier` («Матрица: тип артефакта →
набор проверок»). Заходи туда первым, иначе получится 5-8 угаданных вызовов подряд.

Отличие от соседей по набору — во входе, а не в инструменте (Playwright у всех):
`verifier` открывает **один готовый файл** и смотрит, сыплет ли он ошибками;
`webapp-testing` работает с **поднятым dev-сервером**; `screenshot-test` сверяет
снимок с **эталоном**. Здесь на входе — **список сценариев**, и отвечает он на
единственный вопрос «путь до цели проходится?». Практическое следствие: пока
прототип открывается со сломанной консолью, smoke-тесты писать рано — сперва
режим 1 `verifier`, он дешевле и падает раньше.

## Стек

Playwright Test — самый простой запуск.

```bash
npm i -D @playwright/test
npx playwright install chromium
```

## smoketest.spec.js

Готового файла в навыке нет — сохрани код ниже как `smoketest.spec.js` рядом с прототипом:

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

## Снимки UI — не здесь

Визуальная регрессия (снять скриншот, сравнить с эталоном, упасть при разнице) живёт
в скилле `screenshot-test` — там же стабилизация снимков: отключение анимаций, ожидание
шрифтов, скрытие каретки, stub времени. Без них pixel-diff флакает на пустом месте.

Держать вторую реализацию того же здесь незачем: два набора эталонов расходятся,
и падение читается как «сломался тест», а не «сломался UI». Smoke-тест отвечает на вопрос
«путь работает?», screenshot-test — «картинка не поехала?».

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
