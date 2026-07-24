---
name: i18n-stress-test
version: 1.0.0
description: Подставляет в макет немецкий, арабский (RTL), японский и emoji-переполнение. Подсвечивает места поломки.
when_to_use: Перед сдачей продуктового макета, который пойдёт в локализацию.
---

# i18n stress test

90% макетов сделаны под английский. Локализаторы потом плачут. Этот скилл — превентивная проверка.

## Стресс-наборы

### DE (длинные слова)
- «Кнопка» → `Bestätigungseinstellungen`
- «Настройки» → `Anwendungseinstellungen`
- «Загрузить» → `Herunterladen`

### AR (RTL + другая ширина)
- `إعدادات الإشعارات`
- Тестирует: направление текста, иконки рядом с текстом, выравнивание чисел.

### JA (плотный текст без пробелов)
- `通知設定をカスタマイズする方法`
- Тестирует: word-break, длина строк.

### ZH (вертикальная плотность)
- `通知设置自定义方法`

### Emoji-переполнение
- `🌟⭐✨💫🌠☄️🌌🌃🌁🌉🌆🏙️`

## Скрипт

`templates/i18n-stress.mjs`:

```js
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const file = process.argv[2];
if (!file) { console.error('Usage: node i18n-stress.mjs <file>'); process.exit(1); }

const samples = {
  de: ['Anwendungseinstellungen', 'Benachrichtigungseinstellungen', 'Bestätigungs-E-Mail'],
  ar: ['إعدادات الإشعارات', 'احفظ التغييرات', 'تسجيل الدخول'],
  ja: ['通知設定をカスタマイズ', '保存', 'サインイン'],
  emoji: ['🌟⭐✨💫🌠☄️', '🎉🎊🥳', '👨👩👧👦'],
};

const browser = await chromium.launch();
for (const [lang, words] of Object.entries(samples)) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(pathToFileURL(path.resolve(file)).href);

  // RTL для арабского
  if (lang === 'ar') await page.evaluate(() => document.documentElement.setAttribute('dir', 'rtl'));

  // Заменим текстовые узлы
  await page.evaluate((words) => {
    function walk(node) {
      if (node.nodeType === 3 && node.textContent.trim().length > 3) {
        node.textContent = words[Math.floor(Math.random() * words.length)];
      }
      for (const c of node.childNodes) walk(c);
    }
    walk(document.body);
  }, words);

  // Найдём переполнения
  const overflows = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('*').forEach(el => {
      if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
        out.push({ tag: el.tagName, text: el.textContent.slice(0, 40), w: el.scrollWidth, cw: el.clientWidth });
      }
    });
    return out.slice(0, 20);
  });

  await page.screenshot({ path: `i18n-${lang}.png` });
  await page.close();

  console.log(`\n[${lang.toUpperCase()}] screenshot → i18n-${lang}.png`);
  if (overflows.length) {
    console.log('  Переполнения:');
    for (const o of overflows) console.log(`    ${o.tag} (${o.cw}px < ${o.w}px): "${o.text}"`);
  } else {
    console.log('  ✓ нет переполнений');
  }
}
await browser.close();
```

## Использование

```bash
node i18n-stress.mjs index.html
# → i18n-de.png, i18n-ar.png, i18n-ja.png, i18n-emoji.png
# + список элементов, у которых текст не помещается
```

## Что нужно сделать в макете заранее

1. **Не используй `width: <px>` для контейнеров с текстом.** Используй `min-width` + `max-width`.
2. **Иконка рядом с текстом** — через flex с gap, не через абсолют.
3. **Числа в сложных форматах** — через `Intl.NumberFormat`, не вручную.
4. **Дата** — `Intl.DateTimeFormat`.
5. **Множественные формы** — через `Intl.PluralRules`, не «1 файл / 2 файлов».
6. **Поддержка RTL** — `margin-inline-start` вместо `margin-left`, `inset-inline-end` вместо `right`. CSS logical properties.
7. **Шрифт с поддержкой нужных алфавитов** — `font-family: Inter, "Noto Sans Arabic", "Noto Sans JP", sans-serif`.

## Что точно сломается

- Кнопки фиксированной ширины.
- Tabs с фиксированными % ширины.
- Сетки `grid-template-columns: 1fr 200px` где справа — текст.
- Иконки с `position: absolute; right: 16px` — в RTL должны быть слева.
- Хедеры с лого, навом и кнопкой в одну строку — на DE сжимается.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-i18n-stress-test.md`. Секции там: 4 категории риска, Test fixtures, Stress-test mode, Чек-лист, Решения проблем, Антипаттерны.
