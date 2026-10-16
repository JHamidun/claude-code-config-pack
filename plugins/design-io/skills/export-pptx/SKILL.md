---
name: export-pptx
description: "HTML-дек в PPTX: режим картинок (надёжный) или редактируемый (нативный текст, pptxgenjs). Триггеры: «html в pptx», «выгрузи в PowerPoint»."
---

# Export PPTX

Два режима, оба живут здесь. Раньше `editable` был описан тут, а его код лежал в
соседнем скилле `pptx-editable-extractor` — на запрос «HTML в PPTX» выпадала
лотерея из двух навыков, каждый из которых неполон без другого. Теперь и описание,
и скрипты в одном месте; `pptx-editable-extractor` слит сюда.

## Что выбирать когда

| Ситуация | Режим |
|---|---|
| Дек уйдёт в PowerPoint, его будут править | editable (с компромиссами по визуалу) |
| Просто переслать как PPTX, без правок | screenshots |
| В деке много кастомных эффектов / SVG / градиентов | screenshots, иначе сломается |
| Текст должен искаться / переводиться в PowerPoint | editable |
| Нужно и то, и другое | оба, два разных файла |

## Режим 1: screenshots (надёжно, не редактируется)

Каждый слайд → PNG → фон слайда PPTX. Pixel-perfect, но текст внутри картинки.

```bash
npm i -D playwright pptxgenjs
npx playwright install chromium

node templates/pptx-screenshots.mjs deck.html deck.pptx
```

Скрипт гоняет дек тем же путём, что `export-png`: снимает `deck-stage` кадр за
кадром и собирает через **pptxgenjs**, `LAYOUT_WIDE` (13.33×7.5 in ≈ 1920×1080).

Ожидает разметку скилла `slides` — кастомный элемент `<deck-stage>` со свойством
`.total` и методом `.go(i)`. Если его нет, скрипт скажет об этом прямо и выйдет с
кодом 2; без такой проверки падало невнятное «Cannot read properties of null».

## Режим 2: editable (текст и фигуры — нативные)

Два шага: Node обходит DOM и пишет JSON, Python собирает из JSON настоящий PPTX,
где каждая «коробка» — TextBox, Picture или прямоугольник.

```bash
npm i -D playwright
npx playwright install chromium
pip install python-pptx pillow

node templates/extract.mjs deck.html --slide-selector "deck-stage > section"
python templates/build_pptx.py deck.json deck.pptx
```

Что собирает экстрактор с каждого слайда:

```js
{ kind: 'text',  x, y, w, h, text, fontFamily, fontSize, fontWeight, italic, color, align }
{ kind: 'image', x, y, w, h, src }
{ kind: 'rect',  x, y, w, h, fill, radius, z: -1 }
```

Координаты — в пикселях относительно слайда; `build_pptx.py` переводит их в EMU
(1 px @96dpi = 9525 EMU), кегль — в пункты (px × 0.75).

Две неочевидные вещи в алгоритме, которые легко сломать при правке:

- **Берутся только текстовые листья.** У элемента-обёртки `textContent` тот же,
  что у детей, и без фильтра `isTextLeaf` один заголовок уехал бы в PPTX
  несколько раз, слоями друг на друге.
- **Порядок = z-index.** PPTX рисует фигуры в порядке добавления, другого способа
  задать слои нет. Поэтому фоновым плашкам ставится `z: -1` и список сортируется:
  иначе карточка закрасит собственный текст.

`--slide-selector` обязателен, если разметка не `deck-stage > section`. Селектор,
не нашедший ни одного слайда, — это ошибка (exit 2), а не пустой JSON: молчаливый
пустой результат раньше выглядел как «сработало».

## Ограничения editable

- **Шрифты.** PowerPoint считает метрики по-своему, идентичной вёрстки не будет.
  Соглашайся на ~95%.
- **CSS-эффекты** — тени, фильтры, градиенты — не переносятся. Нужна
  пиксель-точность → режим screenshots.
- **Инлайн-SVG** не переносится. Замени на PNG заранее.
- **Overlap слоёв** может лечь неидеально: см. про порядок выше.
- Хорошо работает для макетов «заголовок + текст + 1–2 фигуры», плохо — для
  художественных слайдов.
- Экстрактор — **черновик**: для сложных макетов потребуется ручная подкрутка
  (скрипты лежат рядом, в `templates/`).

## Замечания по обоим режимам

- Шрифты берутся с машины получателя. Helvetica Neue в HTML + Windows у клиента =
  подмена. Google Fonts PPT не подтянет вообще — предупреди заранее и закладывай
  это в выбор шрифтов ещё на этапе вёрстки.
- 16:9 — `LAYOUT_WIDE` (13.33×7.5 in). 4:3 — `LAYOUT_STANDARD` (10×7.5 in).
- Пропавшую картинку `build_pptx.py` печатает в stderr и продолжает. Смотри лог:
  иначе дек уедет заказчику с дырой и никто не узнает почему.

## Файлы

- `templates/pptx-screenshots.mjs` — режим screenshots целиком.
- `templates/extract.mjs` — режим editable, шаг 1 (HTML → JSON).
- `templates/build_pptx.py` — режим editable, шаг 2 (JSON → PPTX).

## Legacy reference

- `references/legacy-export-pptx.md` — прежняя расширенная версия (дерево
  @2026-04-30): Зависимости, Каркас, Workflow целиком, PPTX размеры, путь через
  LibreOffice, скрытые слайды, speaker notes, метаданные, антипаттерны.
- `references/legacy-pptx-editable-extractor.md` — то же для editable-половины:
  Принцип, Extraction script, Сборка PPTX, End-to-end, что **не** перенесётся,
  решения для шрифтов, антипаттерны.
