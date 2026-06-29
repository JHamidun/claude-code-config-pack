---
name: proto-smoketest
description: E2E кликабельный smoke-test через Playwright. Проходит критичные user-paths в interactive-prototype, проверяет что переходы работают, формы сабмитятся, navigation не сломан. Не unit-test — happy-path смоук.
when_to_use: После interactive-prototype с >3 экранами, перед dev-handoff. Лучше verifier когда нужно проверить что юзер реально может пройти flow, а не только что страница открывается.
---

# Proto smoke test

Прогоняет 1-3 happy paths через прототип. Цель — поймать сломанные переходы, не покрыть 100%.

## Инсталляция

```bash
npm i -D @playwright/test
npx playwright install chromium
```

## Структура

`tests/smoke.spec.js`:
```js
const { test, expect } = require('@playwright/test');
const path = require('path');

const ARTIFACT = `file://${path.resolve(__dirname, '../artifact.html')}`;

test.beforeEach(async ({ page }) => {
  await page.goto(ARTIFACT);
});

test('Welcome → Main flow', async ({ page }) => {
  await expect(page.locator('h1')).toContainText('Welcome');
  await page.click('button:has-text("Начать")');
  await expect(page.locator('.main')).toBeVisible();
  await expect(page).toHaveURL(/main/);  // если используется ?screen=main
});

test('Form: fill and submit', async ({ page }) => {
  await page.click('text=Начать');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=name]', 'YourFirstName');
  await page.click('button:has-text("Отправить")');
  await expect(page.locator('text=Готово')).toBeVisible();
});

test('Navigation: cycle through screens', async ({ page }) => {
  const screens = ['welcome', 'features', 'pricing', 'final'];
  for (const s of screens) {
    await page.click(`[data-nav="${s}"]`);
    await expect(page.locator(`[data-screen="${s}"]`)).toBeVisible();
  }
});
```

```bash
npx playwright test tests/smoke.spec.js
```

## Какие сценарии писать

| Тип прототипа | Smoke paths |
|---|---|
| Onboarding | welcome → setup → permissions → done (1 path) |
| E-commerce | catalog → product → cart → checkout (1 path) |
| Dashboard | login → main → widget-detail → back (1 path) |
| Form-flow | step 1 → 2 → 3 → review → submit (1 path) |
| Multi-screen | full nav cycle (1 path) |

3 теста max на прототип. Это smoke, не coverage.

## Что НЕ тестировать

- ❌ Каждый button hover (бессмысленно)
- ❌ CSS layout (это для visual regression)
- ❌ A11y (это `a11y-audit`)
- ❌ Performance (это `perf-audit`)
- ❌ Сложные edge cases (это для unit/E2E реального продукта)

Smoke = 3 теста по 5 секунд каждый.

## Selectors — best practices

Используй data-attrs специально для тестов:
```jsx
<button data-testid="start-btn">Начать</button>
```

```js
await page.click('[data-testid=start-btn]');
```

Альтернативы в порядке предпочтения:
1. `data-testid` (best — стабильно)
2. `role` + accessible name (`button[name="Начать"]`)
3. `text=` (хрупко при i18n)
4. CSS selectors (`.btn-primary`) — хрупко при рефакторинге
5. XPath (последнее средство)

## Multi-viewport

```js
test.describe.parallel('responsive', () => {
  for (const vp of [{w:1440,h:900,name:'desktop'}, {w:375,h:812,name:'mobile'}]) {
    test(`flow on ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.w, height: vp.h });
      await page.goto(ARTIFACT);
      // ... тест
    });
  }
});
```

## Скриншот failures

```js
test.use({
  screenshot: 'only-on-failure',  // авто-скриншот при failure
  trace: 'retain-on-failure',     // полная trace для debug
});
```

При failure — у тебя есть `test-results/<name>/test-failed-1.png` для визуального ревью.

## CI integration

```yaml
# .github/workflows/smoke.yml
- run: npx playwright install chromium
- run: npx playwright test tests/smoke.spec.js --reporter=html
- uses: actions/upload-artifact@v3
  if: always()
  with:
    name: playwright-report
    path: playwright-report/
```

## Output: PASS / FAIL

```
Running 3 tests using 1 worker

  ✓ Welcome → Main flow (2.3s)
  ✓ Form: fill and submit (3.1s)
  ✓ Navigation: cycle through screens (1.8s)

  3 passed (7.2s)
```

При failure:
```
  ✘ Form: fill and submit (4.2s)
    Error: Timeout 30000ms exceeded.
    waiting for locator('text=Готово')

  See trace: test-results/form-flow-trace.zip
```

Юзеру: «Smoke ОК, 3/3 пройдены» или «Сломан flow X — экран Y не появляется после клика на Z. Скриншот в `test-results/`.»

## Когда НЕ запускать

- Прототип статичный (slides, лендинг без forms) → verifier достаточно
- Один экран без переходов → нет flow для тестирования
- На early итерации → структура ещё меняется, тесты постоянно ломаются

## Антипаттерны

- 30+ smoke tests → не smoke, а E2E suite
- Тестировать UI specifics (bg color = X) → это хрупко, для visual regression
- Не использовать data-testid → тест ломается при любом рефакторе текста
- Игнорировать timeouts → тесты flaky, все теряют доверие
- Запускать smoke на staging без отдельного artifact → совмещение concerns
- Не сохранять report на CI → не понятно что упало
