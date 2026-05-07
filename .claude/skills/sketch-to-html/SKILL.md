---
name: sketch-to-html
description: Грубый рукотворный скетч / whiteboard photo → HTML каркас. Идентифицирует layout regions, превращает в HTML divs/sections с placeholder-контентом для дальнейшей детализации в interactive-prototype или slides.
when_to_use: Юзер прислал фото маркерной доски / whiteboard / paper sketch / Excalidraw screenshot и хочет «превратить это в HTML каркас». Не для финального дизайна — только начальный wireframe-каркас.
---

# Sketch → HTML

Скетч — это структурный сигнал, не визуальный. Цель: понять иерархию и блоки, не воспроизвести каракули.

## Workflow

```
1. Load image (photo / screenshot / Excalidraw)
2. Identify regions (header / hero / 3 columns / footer)
3. Generate HTML с подписанными блоками
4. → wireframe / interactive-prototype для следующего шага
```

## Identification (визуально)

Claude Code умеет читать изображения через `Read` tool. Для скетча — описание, не парсинг:

```
[Юзер скидывает фото]
```

В response Claude:
1. Описывает что видит: «Hero сверху на 60% ширины, справа карточка с 3 пунктами, ниже — 3 равные секции по 33%, footer с лого»
2. Спрашивает уточнения если нужно: «У тебя в верхнем правом углу что-то закрашено — это иконка или CTA?»
3. Генерирует HTML

## Output: wireframe-style HTML

```html
<!-- Re-creating user's sketch as structured HTML -->
<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Sketch interpretation</title>
<style>
  body { font-family: system-ui; padding: 24px; max-width: 1200px; margin: auto; }
  .block { background: #fff; border: 1px dashed #999; border-radius: 4px;
           padding: 16px; margin-bottom: 12px; }
  .block-label { color: #666; font-size: 11px; text-transform: uppercase;
                 letter-spacing: 0.05em; margin-bottom: 6px; }
  .row { display: grid; gap: 12px; }
  .row.cols-2 { grid-template-columns: 2fr 1fr; }
  .row.cols-3 { grid-template-columns: repeat(3, 1fr); }
</style></head>
<body>

<div class="block">
  <div class="block-label">Hero (top, ширина ~60%)</div>
  <h1>[Заголовок 2-3 строки — что юзер написал в скетче]</h1>
  <p>[Подзаголовок если был]</p>
</div>

<div class="row cols-2">
  <div class="block">
    <div class="block-label">Main content (left)</div>
    [Содержимое центрального блока — описать что было в скетче]
  </div>
  <div class="block">
    <div class="block-label">Sidebar card (right, ~30%)</div>
    <p>[3 пункта/опции из скетча]</p>
  </div>
</div>

<div class="row cols-3">
  <div class="block">
    <div class="block-label">Feature 1</div>
    [Что юзер написал в первом блоке]
  </div>
  <div class="block">
    <div class="block-label">Feature 2</div>
    [Второй блок]
  </div>
  <div class="block">
    <div class="block-label">Feature 3</div>
    [Третий блок]
  </div>
</div>

<div class="block">
  <div class="block-label">Footer</div>
  [Что было внизу скетча]
</div>

</body></html>
```

## Excalidraw / draw.io / Whimsical

Если скетч из этих tools — есть structured export:

### Excalidraw
- Save → `.excalidraw` (JSON)
- В JSON: elements with positions, text, types
- Можно парсить и mapping coords → HTML grid

```js
const sketch = JSON.parse(fs.readFileSync('mockup.excalidraw'));
const elements = sketch.elements;
// elements[i] = { type, x, y, width, height, text, ... }
// Группируешь по visual proximity → rows / columns
```

### draw.io
- Save → `.drawio` (XML)
- Mapping shapes → semantic blocks

## Photo recognition (whiteboard)

Это harder — нужно vision. Через Claude Code:
- `Read` tool принимает image
- Ты описываешь что видишь
- Спрашиваешь у юзера про неоднозначности

Если фото плохого качества — попроси юзера переснять или добавить подписи к блокам.

## Что НЕ переносить

- ❌ Точные пропорции рисованных коробок (палец дрожал)
- ❌ Цвета маркера (юзер использовал то что было)
- ❌ Стрелки между блоками — если важно, exposed как «sequence A → B»
- ❌ Художественные элементы (улыбки, человечки) — не нужны в каркасе

## Что переносить

- ✅ Структура (1, 2, 3 колонки)
- ✅ Иерархия (что больше = более важное)
- ✅ Текст-надписи (содержательные подписи)
- ✅ Sequence / порядок (если whiteboard это flow)
- ✅ Группировку (что рядом = одна секция)

## Уточняющие вопросы

После interpretation спрашивай:
```
«Я вижу 4 блока:
  1. Hero сверху во всю ширину
  2. Левая колонка с тремя bullet'ами
  3. Правая колонка с большой иконкой
  4. Footer с тремя кнопками

Угадал? Или что-то не так понял?»
```

## Stack

- `wireframe` — следующий шаг (детализировать структуру)
- `interactive-prototype` — далее (добавить интерактив)
- `placeholders` — для блоков-заглушек

## Антипаттерны

- Воспроизводить скетч буквально (с дрожащими линиями) → дешёвый «hand-drawn» эффект
- Игнорировать подписи юзера и придумывать свой контент
- Делать финальный hi-fi сразу из скетча → теряешь шаг wireframe
- Пытаться парсить фото алгоритмически без vision модели → 99% случаев garbage
- Не задавать уточняющих вопросов → строишь не то что юзер имел в виду
- Передавать sketch напрямую в slides без структурирования → теряется смысл
