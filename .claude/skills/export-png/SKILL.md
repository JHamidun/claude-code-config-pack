---
name: export-png
description: "PNG-скриншоты слайдов/экранов через Playwright: кадр на слайд или по селектору. Триггеры: «html в png», «выгрузи слайды картинками», «социалки cover». НЕ тест UI→webapp-testing."
---

# Export PNG

Playwright headless. Установка та же, что для `export-pdf`:

```bash
npm i -D playwright && npx playwright install chromium
```

## Скрипт

`templates/render-png.mjs` — умеет:

- Если на странице есть `<deck-stage>` — переключает слайды через `goToSlide(i)` и снимает кадр на каждый.
- Иначе — снимает либо весь viewport, либо элементы по селектору (`--selector ".artboard"`).

```bash
# Все слайды дека
node render-png.mjs deck.html out/

# Все артборды по селектору
node render-png.mjs canvas.html out/ --selector dc-artboard --width 1200 --height 800

# Один скрин страницы
node render-png.mjs prototype.html out/screen.png
```

## Размеры

По умолчанию viewport 1920×1080, scale 2 (retina). Меняется флагами `--width`, `--height`, `--scale`.

## Подсказки

- Для деков скрипт ждёт 600ms между слайдами — этого хватает для transition. Если у тебя длиннее — `--delay 1200`.
- Для прозрачных картинок добавь `--omit-background` (установит body background в transparent перед снимком).
- Шрифты — `await document.fonts.ready` уже стоит. Если используешь Google Fonts с `display: swap`, добавь `--font-wait 1000`.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-export-png.md`. Секции там: Базовый каркас, Стандартные размеры social, Серия из шаблона, Серия слайдов как PNG, Качество vs размер файла, Прозрачный PNG, После export — оптимизация, Антипаттерны.
