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
