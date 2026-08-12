---
name: cards-creator
description: Создание визуальных карточек-каруселей для Telegram-канала — editorial стиль. HTML+CSS шаблон → Playwright render → PNG-серия 1080×1350. Библиотека шаблонов лежит в templates/ (read-only образцы); новая серия создаётся в рабочей директории (CWD). Вызывается сам или из tg-post. Триггеры — «карточки для канала», «карусель в канал», «сделай series», «нарисуй cover», «slides для поста».
---

# Cards Creator — карточки-карусели для Telegram-канала

> Skill для editorial-style carousel-карточек. Production-tested editorial-magazine формат. Библиотека готовых шаблонов лежит в `templates/` как **образцы**. Новые серии создаются в **рабочей директории** на основе этих образцов.

## Когда использовать

- «сделай карточки для поста про X»
- «карусель в канал на тему Y»
- «нарисуй N cards в editorial-стиле»
- «cover + screens + stats серия»
- Из `tg-post` skill — автоматически если контент имеет list / before-after / 3+ цифры / режим long-roundup-announce

## Workflow — KEY PRINCIPLE

```
templates/            ← ОБРАЗЦЫ (read-only, источник истины)
└── cards/
    ├── palette.html    ← готовые шаблоны карточек
    ├── *.css           ← CSS-tokens + class-types
    └── theme-icons.svg ← Sprite

→ Читаем шаблоны → делаем по аналогии → пишем в **CWD** (working dir)

/tmp/my-series/      ← НОВАЯ СЕРИЯ (output, обычная рабочая папка)
├── series.html      ← собственный HTML с правильным контентом
├── styles.css       ← скопированный из templates
├── icons.svg        ← скопированный
└── png/
    ├── 01.png
    ├── 02.png
    └── ...
```

**НИКОГДА не модифицируем `templates/`** — это образцы. Каждая новая серия делается копией нужных файлов в CWD (или `/tmp/cards-<topic>/`).

## Структура библиотеки шаблонов

```
~/.claude/skills/cards-creator/templates/
├── cards/                      ← основная палитра
│   ├── palette.html            ← готовые карточки (grid)
│   ├── palette-tokens.css      ← tokens + базовые классы
│   ├── palette-cards.css       ← per-card overrides
│   ├── palette-fixes.css       ← фиксы overflow и т.д.
│   ├── styles.css              ← оригинальный базовый набор
│   ├── theme-icons.svg         ← sprite глифов
│   ├── preview-grid.html       ← thumbnails для общего обзора
│   ├── samples.html            ← full-size sample карточки
│   └── handoff/                ← self-contained handoff bundle
│       ├── handoff.html        ← все карточки в одном файле + inline CSS
│       ├── render.py           ← Playwright PNG export script
│       ├── README.md           ← документация bundle
│       └── photos/             ← placeholder-фото для карточек
│
├── uploads/                    ← оригинальные референсы + доп. фото
│   └── photos/                 ← photo-pool
│
└── examples/                   ← legacy production-tested серии (старые workflow)
    ├── example-cards.html      ← пример серии (cover + inner + closer)
    ├── template.html           ← legacy базовый template
    └── icons.svg               ← legacy sprite
```

> Плейсхолдер-фото и логотип — замени на свои брендовые ассеты перед первым использованием.

## Параметры

| Параметр | Значение |
|---|---|
| Размер | **1080×1350px** (4:5 portrait, Telegram-friendly) |
| Формат | PNG, 2× DPI (device_scale_factor=2) |
| Серия | 5-9 карточек (sweet spot 7) |
| Файлы | `series-NN.png` (01, 02, 03...) |
| Posting | `sendMediaGroup` (album) с caption на первой |

## Палитра (пример токенов — замени на свой бренд)

```css
/* Brand colors — токены проекта, подставь свои */
--primary: #3B5BDB;   /* Primary accent */
--deep: #0B1021;      /* Deep navy */
--cyan: #4DABF7;      /* Highlight cyan */
--cyan-soft: #B5E1FF;
--cream: #F1F3F5;     /* Base — большинство карточек */
--cream-warm: #EFE6D6;
--cream-deep: #E8DDC6;
--ink: #18181B;
--terra: #CC7357;     /* Accent — warm orange */
--yellow: #FFD447;    /* Highlight */
--text: #111111;
--text-muted: #4A4A55;
--border: #D9D2C4;
```

**Распределение фонов**: 70% cream / 15% navy / 10% terra solid / 5% gradient/special.

## Типография

```css
--ft-head: "Inter Tight", system-ui;     /* Headlines 800-900wt, 96-140px */
--ft-body: "Manrope", sans-serif;        /* Body 400-500-700wt, 24-28px */
--ft-mono: "JetBrains Mono", monospace;  /* Eyebrows, badges, code */
--ft-script: "Caveat", cursive;          /* Handwritten — post-it, annotation */
--ft-serif: Georgia, serif;              /* Italic footer-quotes */
```

## Типы карточек (палитра)

Открой `templates/cards/palette.html` чтобы увидеть все. Основные семейства:

### Cover / Hero
- **cover-hero** — большой headline + автор + eyebrow выпуска
- **cover-photo** — cover с фото автора
- **pattern (magazine)** — обложка глянцевого журнала с photo + pattern
- **ASCII-cover** — гигантская ASCII-art на navy CRT

### Stat / Data
- **stat-hero** — одна гигантская цифра + объяснение
- **stat-grid 2×2** — 4 метрики + sparklines
- **stat-grid 3×2** — 6 метрик
- **dashboard.live** — фейковый data-дашборд с metrics + chart

### List / Structure
- **checklist** — 5-7 пунктов с галочками
- **numbered-list** — file-card стиль
- **anti-tip** — список ошибок «так НЕ делай»
- **glossary** — cheat-sheet терминов

### Quote / Voice
- **quote** — большая цитата + post-it стикер
- **hot-take** — manifesto на terra-bg
- **quote-tweet** — фейковая цитата чужого поста
- **diary-note** — handwritten заметка Caveat
- **quote-bomb** — одна фраза на всю карточку
- **napkin-sketch** — full Caveat handwritten

### Compare / Decision
- **vs-split** — раньше vs сейчас
- **mini-case** — case study before/after
- **comparison-matrix** — feature grid
- **myth-buster** — МИФ vs РЕАЛЬНОСТЬ
- **before/after photo** — 2 photos split

### Process / Chart
- **steps** — numbered process
- **timeline** — события по датам
- **chart-line** — линейный график (navy)
- **chart-bar** — bar chart
- **process-flow** — pipeline с stages + arrows + dotted-arc

### UI Mocks (visual hooks)
- **chat-quote** — имитация Telegram-сообщения
- **macOS Terminal** — mac-dots + shell prompt
- **VS Code** — line-numbers + filename tab
- **Notion-page mockup** — sidebar + content blocks

### Special / Format-driven
- **table** — таблица
- **meme** — фото + caption
- **tool-roundup** — workspace photo + features list
- **highlight** — strike-through на navy с фото-фон
- **event** — purple gradient анонс
- **question** — вопрос аудитории + emoji-options
- **closer** — subscribe CTA с portrait coin-stamp
- **resource-pack** — file-list + download CTA
- **Q&A pair** — Q+A serif
- **anatomy-diagram** — central object с callout labels
- **week-overview** — 7-day grid с эмодзи
- **ticket-event** — perforated edges + barcode

## Workflow создания серии

### Шаг 1 — Определи структуру серии

На основе контента поста:
- Количество карточек (5-9, sweet spot 7)
- Какие типы (cover-hero + 4-5 inner/list/stat + closer)

### Шаг 2 — Создай рабочую папку В CWD

```bash
# Создай папку для новой серии в рабочей директории
mkdir -p ./cards-my-series/png
cd ./cards-my-series
```

**ВАЖНО**: НЕ создавай в `~/.claude/skills/cards-creator/`. Всегда — в текущей рабочей директории (CWD) или `/tmp/`.

### Шаг 3 — Скопируй нужные файлы из templates/ как стартеры

```bash
# Скопируй CSS (выбери нужную версию)
cp ~/.claude/skills/cards-creator/templates/cards/palette-tokens.css ./styles-tokens.css
cp ~/.claude/skills/cards-creator/templates/cards/palette-cards.css ./styles-cards.css
cp ~/.claude/skills/cards-creator/templates/cards/palette-fixes.css ./styles-fixes.css

# Скопируй SVG sprite
cp ~/.claude/skills/cards-creator/templates/cards/theme-icons.svg ./

# Скопируй render.py + photos (если нужно)
cp ~/.claude/skills/cards-creator/templates/cards/handoff/render.py ./
cp -r ~/.claude/skills/cards-creator/templates/cards/handoff/photos ./
```

### Шаг 4 — Создай series.html

Возьми за основу нужный шаблон из `palette.html` (например `cover-hero` + 5× `inner` + `closer`). Найди разметку каждой карточки в `palette.html` и скопируй в новый `series.html`. Замени контент.

Альтернатива — использовать самодостаточный handoff:
```bash
cp ~/.claude/skills/cards-creator/templates/cards/handoff/handoff.html ./template-full.html
# Открой template-full.html в редакторе, оставь нужные .card блоки, переписав контент
```

### Шаг 5 — Render через Playwright

```bash
python render.py series.html
# → ./png/series-01.png, series-02.png, ...
```

### Шаг 6 — Verify

Открой `./png/series-01.png` в Preview — проверь:
- Headline не обрезан
- Photos загрузились (relative paths корректны)
- Footer-italic читается

### Шаг 7 — Отправь / запланируй в Telegram

⚠️ `tg_client.py` НЕ имеет `send-album`. Альбомы + богатую подпись (спойлер,
раскрывающиеся цитаты, ссылки, фото+видео в одной группе, отложка) шлёт модуль
**`~/.claude/skills/tg-post/scripts/tg_rich_post.py (скилл `tg-post` в пак не входит — он завязан на личный канал автора; публикацию делай своим ботом через `~/.claude/tools/tg_bot.py`)`** — см. секцию «ПЛАНИРОВАНИЕ И ПУБЛИКАЦИЯ»
в `tg-post/SKILL.md`. Коротко:

```python
import sys; sys.path.insert(0, os.path.expanduser('~/.claude/skills/tg-post/scripts'))
from tg_rich_post import client, schedule_album, UTC
# schedule_album(c, 'YOUR_CHANNEL', files=[...png], html=CAPTION_HTML, when=datetime(...,tzinfo=UTC))
```

## render.py (Playwright скрипт)

`templates/cards/handoff/render.py` уже готов. Использование:

```bash
# Установка зависимостей (один раз)
pip install playwright
playwright install chromium

# Render одной серии
python render.py path/to/series.html
# → выходные PNG в ./png/
```

## Связь с `tg-post`

Skill `tg-post` автоматически предлагает запустить cards-creator если контент поста:

1. **list ≥ 4 пунктов** в посте
2. **before/after** упоминание
3. **3+ конкретных цифр** в тексте
4. Режим `long` / `review` / `roundup` / `announce`
5. Тематика «инструмент / стек / сетап»

При ≥ 2 признаках — `tg-post` спросит юзера и передаст структуру в `cards-creator`.

См. секцию «Связь с cards-creator» в `~/.claude/skills/tg-post/SKILL.md` для деталей.

## ПЛОТНЫЕ КАРТОЧКИ + КАРТИНКИ (gpt-image-2)

> Бриф требует «не бойся насыщать» — пустота на карточках читается как «кастрированно».
> Готовый плотный пример-шаблон со ВСЕМИ приёмами: **`templates/examples/dense-cards.html`**
> (9 карточек: cover-stats, таблица-сравнение, bar-chart, split с картинкой, терминал-мок,
> effort-таблица, stat-strip, CTA).

### Скрипты скилла (`scripts/`)

| Скрипт | Что делает |
|--------|-----------|
| `scripts/render_cards.py` | HTML-дек → `./png/series-NN.png` (1080×1350 @2x). `python render_cards.py series.html` |
| `scripts/gen_card_images.py` | Редакторские иллюстрации через **gpt-image-2** (`gpt-image-2-2026-04-21`), брендовая палитра в `STYLE`. Альтернатива 0-токенов — local-gateway `/studio/image` (Gemini) |

### Приёмы плотности (editorial-magazine, проверено)

- **cover-stats**: на обложке под lead — ряд из 3 мини-плашек (цифра + подпись) поверх затемнённого фото. Сразу превью контента.
- **split text+image**: `grid 1.18fr 0.82fr` — слева big-number/буллеты/цитата, справа `col-img` с иллюстрацией во всю высоту. Убивает пустоту на «одна-цифра» карточках.
- **bar-chart (A vs B)**: горизонтальные пары баров (baseline `#BCAE8E` / актуал `#3B5BDB`), ширина = `val/max*100%`, цифра в конце бара, дельта-чип справа (`+8.5` зелёным).
- **таблица-сравнение**: колонка «своей» опции подсвечена `cyan-soft`, лучший в строке — класс `best` с `✦`. ЧЕСТНО помечай и чужие победы (где конкурент впереди).
- **terminal-mock**: `#0B1020` окно с mac-точками + mono `<pre>` с подсветкой (`pr/cmd/ok/cm`). Сильный визуал для «как включить / команды».
- **effort/мини-таблица**: ряд карточек-плашек, дефолтная подсвечена + badge «по умолчанию».
- **stat-strip**: 3-4 белые плашки `st__num` (Inter Tight 800, акцент на единице `.accentnum`).
- **imgband**: слим-полоса 200px с иллюстрацией-фоном как разделитель в карточке.

### ⛔ ANTI-AIR — воздух на карточках (повторяющийся косяк, читать обязательно)

> Размытое «fill height» НЕ работает — нужны конкретные рычаги + независимый аудит. **Fail-условие: любая пустая полоса (cream или navy) > ~8% высоты карточки (≈108px на 1350).**

**Корневые причины (ищи именно их в series.html):**
- `flex:1 1 auto; justify-content:center` на главном блоке → контент висит в центре, пусто сверху И снизу.
- колонки (`triplet`/`strip`/`cmp2`) с `flex:1`, а число/контент прижаты к низу/верху колонки → пустая треть.
- `.note-flow { margin-top:auto }` → тонкая строка улетает в самый низ, над ней дыра.
- `.formula`/панель с `flex:1 + justify-content:center` → текст в верхней трети, низ панели пустой (на тёмном фоне = «дыра»).
- cover: контент прижат к низу, сверху пустой навигейт.

**Рычаги (применять точечно):**
1. Колонки: группа `flex:1`, КАЖДАЯ колонка `display:flex;flex-direction:column;justify-content:center` → число центрируется по высоте колонки.
2. Тонкую `.note-flow` → заменить на массивную тёмную `.takeaway`-полосу (2-3 строки, padding 26-30px), которая ДОХОДИТ до футера. Никогда не оставляй зазор между последним блоком и футером.
3. `flex:1`-панель/формула: либо `justify-content:flex-start` + контент сверху, либо `flex:0 0 auto` (хагает контент) и распределить карту через `justify-content:space-between` — но только когда у блоков есть масса.
4. Две неравные колонки: обе `flex:1`, в короткой `justify-content:space-between` (буллеты растягиваются на всю высоту) или добавить 1 правдивый пункт.
5. Урезать межблочные отступы до 22-28px, отвоёванное место отдать главному блоку (крупнее шрифт/боксы).
6. Дыру на cover закрыть **cutout-картинкой** (см. ниже) или тизер-списком «▸ В РАЗБОРЕ» (реальный контент).

**Обязательный процесс:** генерящий агент СИСТЕМАТИЧЕСКИ недооценивает свой воздух (говорит «8%», аудит видит 14%). Поэтому всегда после рендера — **НЕЗАВИСИМЫЙ visual-аудит** (отдельный агент читает PNG, меряет пустые полосы в %, заворачивает >8-10%). Без этого гейта не публиковать.

### 🖼 КАРТИНКИ НА КАРТАХ (не отгружай typography-only колоду)

Ждём премиум-уровень: **на каждой обложке — сильный 3D-cutout или фото** + **минимум 1 inner-карта с cutout** на серию (телефон/роботы/щит/staircase по теме). Карты-«число-герой» (гигантская цифра 300px+) считаются за графику и cutout не требуют. Генерь через `scripts/card_image_generator.py` (см. ниже), режь фон, ставь без рамки. Воздух на cover закрывается этой же картинкой.

### gpt-image-2 рецепт (картинки на карточки)

- Модель `gpt-image-2-2026-04-21`, endpoint `/v1/images/generations` (или `/edits` с рефом), ключ `OPENAI_API_KEY` из creds.
- `size='1024x1536'` (вертикаль под split/band), `quality='high'`, ответ `b64_json`.
- Когезия серии = общий `STYLE`-суффикс с **точными hex палитры** (cream/navy/blue/cyan/terra) + «flat editorial vector, NO text/logos». gpt-image-2 держит стиль между картинками.
- Генерь пачкой в фоне (`run_in_background`) — 30-60с на картинку.

### Overflow-фиксы (когда заголовок/число съедает карточку)

- Длинная двусоставная цифра («11 дней») → `white-space:nowrap` + unit меньшим кеглем, big ~210-240px (не 360).
- Плотные карточки → `h1.tiny` (72px) вместо 100-108px, чтобы влез контент ниже.
- `footnote` позиционируется `absolute` снизу — не считай его в потоке, оставляй ему место.

### Интегрированные вырезки — НЕ «картинка в коробке»

Editorial-референс НЕ ставит картинки в скруглённый бокс — объекты **вырезаны (прозрачный фон)** и
интегрированы: лежат на cream/navy, выходят за край, перекрывают текст.

- **gpt-image-2 НЕ поддерживает `background:transparent`** (400). Поэтому: генерируем картинку обычно
  (`gen_card_images.py`) → режем фон **rembg** (`scripts/cut_bg.py`, модель `isnet-general-use` + alpha matting +
  tight-crop по alpha-bbox). На вектор-арте edges чистые.
- Размещение: `col-img/imgband { background:transparent; border:none; box-shadow:none }` + `img{object-fit:contain}`,
  можно `transform:scale(1.08)` чтобы слегка выйти за край (`.card` имеет `overflow:hidden` → бликует к краю).
- Широкий объект (последовательность) → отдельной `.cutband` (полоса flex:1) на всю ширину, не в узкой колонке.

### Что приближает к премиум-референсу

1. **Вырезки без боксов** (rembg) — объекты лежат на фоне, не в рамке.
2. **Варьируй фон** — не все cream: navy-радиалка, светлая графика контрастно поверх.
3. **Рукописные аннотации** (Caveat, terra, `transform:rotate(-7deg)`) — `.scribble` «рекорд!» у дельты графика.
4. **Стикер-коллаж** — `.sticker` (жёлтая плашка + Caveat-подпись, повёрнут) поверх картинки.
5. **Тёплая палитра** — terra/yellow, не только cyan.
6. **Глубина** — мягкие тени на белых карточках/плашках (`box-shadow: 0 8px 24px rgba(1,3,52,0.07)`).
7. **Заполняй высоту** — hero-блок `flex:1`, текст-колонка `justify-content:space-between`, нижняя плашка-итог.

### Обогнать референс

- **Реалистичные изображения вместо flat-вектора** — gpt-image-2 «Photorealistic 3D render … PLAIN seamless background for cutout» → rembg → вставка без бокса. Реал-объекты (робот, спидометр, 3D-стрелка) выглядят дороже иллюстраций.
- **Если метафора нечитаема — бери реальное фото, а не иллюстрацию.** Фото-полоса (cover, без обрезки) читается мгновенно.
- **Речевое облако** `.speech` (белое, обводка navy, хвостик-ромб, лёгкий наклон) — реплика от персонажа. Чистая коллаж-DNA.
- **3D-объект в «воздух»** — не растягивай пустые блоки; верни им высоту по тексту, а свободное место займи вырезанным 3D-объектом по теме (стрелка вверх для «прогресс», спидометр для «скорость»).
- НЕ ставить «рекорд!» там, где конкурент впереди по абсолюту — помечай дельту честно.

### Фабрика картинок в едином стиле — `scripts/card_image_generator.py`

Отдельный скрипт скилла (зависит только от requests + PIL + rembg, ничего внешнего).
Чтобы все иллюстрации колоды были в ОДНОМ стиле/палитре/типаже (а не дрейфили от ad-hoc промптов),
картинка проходит через **шаблон-обёртку** прямо в этом скрипте до модели:
`TEMPLATES[style] (frozen prefix: палитра+рендер+«plain bg for cutout») + subject → gpt-image-2`.

- **9 шаблонов**:
  - cutout (объект на plain bg → rembg): `photoreal-3d` (дефолт, премиум), `flat-editorial`, `isometric`, `marker` (рукописная маркер-диаграмма — для «нарисуй концепт схемой»), `chromatic` (играющий 3D-объект), `paper-craft`.
  - full-bg (фон карточки, без обрезки): `glamour` (люкс-навигейт), `sketch` (мел на доске), `real-photo` (реальное фото, когда метафора не читается вектором).
- Консистентность держится фиксированным префиксом (один стиль → один префикс), не сидом.
- **recommend-движок**: `python scripts/card_image_generator.py recommend "тема"` → подсказывает стили (релиз→photoreal-3d/chromatic, концепт→marker, личное→sketch/real-photo).
- CLI: `templates` (список) · `test "<subject>" <style> --cut --size 1536x1024` (одна) · `generate cards.json ./img` (вся колода одним стилем). `--cut`/`"cut":true` → rembg-вырезка `_t.png`.
- Конфиг: `{"template":"photoreal-3d","cards":[{"id":"item","subject":"…","size":"1536x1024","cut":true}, …]}`.
- Правило единства: генери ВСЕ иллюстрации одной колоды одним `template` (не мешай flat + 3d).
- **«Рисовалка» (главное!):** ПЕРЕД генерацией выбери визуальный ПРИЁМ под тип инфы карточки — см. **`references/visual-playbook.md`** (тип инфы → приём → метафора-объект). Картинка должна *кодировать идею* (×4→лупа+баг, прогресс→стрелка, скорость→спидометр), а не быть «просто иллюстрацией». Неочевидно в вектор-арте → реальное фото + подпись.

### Бренд-логотип в углу (айдентика)

Положи логотип своего проекта в `templates/cards/logo.png` и встраивай **маленьким (~52px) в верхний-правый угол** каждой карточки — не отвлекает, держит айдентику. Один CSS-приём на всю колоду (копируй `logo.png` рядом с series.html):

```css
.card.inner .ast.tr { display: none; }                 /* логотип занимает место правого астериска */
.card.inner::after { content:""; position:absolute; top:44px; right:52px; width:52px; height:52px;
  background:url('logo.png') center/contain no-repeat; border-radius:12px; z-index:6;
  filter: drop-shadow(0 4px 10px rgba(1,3,52,0.22)); }
```
Для cover-карточки (там свой `::before`/`::after` под фото-фон) — ставь логотип `<img>`-элементом: `.brandlogo-cover { position:absolute; top:46px; right:52px; width:56px; z-index:5; }`.

### Аватарка канала

Аватарку канала зашей в обложку (`.cover-author .ava { background-image:url('avatar.jpg') }`). Положи свою в `templates/examples/avatar.jpg`. Генерация новых концептов из фото:

```bash
python ~/.claude/skills/cards-creator/scripts/gen_avatar.py <фото.jpg> [concepts|all] [out_dir]
# concepts: brand (PIL-композит, max likeness) | rim (контурное свечение)
#           | circle (светящийся диск) | symbols (парящие code-символы > [] {} <>) | char3d | tech
# gpt-image-2 /edits сохраняет лицо по рефу.
```

### Публикация

Альбом + богатая подпись (спойлер / раскрывающиеся цитаты / фото+видео / отложка) — модуль
**`~/.claude/skills/tg-post/scripts/tg_rich_post.py`** (см. tg-post/SKILL.md). НЕ `tg_client.py send-album` (такой команды нет).

---

## Common gotchas

1. **Overflow на длинных русских заголовках** → `text-wrap: balance` + line-height: 0.92, размер 96-140px
2. **Шрифты не успевают загрузиться в Playwright** → wait 800ms после networkidle в render.py
3. **SVG sprite IDs дублируются** при merge нескольких серий — используй уникальные prefix
4. **PNG export size** — каждое <2MB (Telegram сжимает большие)
5. **Album max 10 photos в `sendMediaGroup`** — если серия больше — split
6. **device_scale_factor=2** = retina @ 2x DPI = crisp на retina-экранах
7. **Photos в карточках** — используй `object-fit: cover` + `object-position: center 38%` (фокус на лице если portrait)
8. **Relative paths в html** — после копирования файлов в рабочую папку убедись что `<img src="photos/xxx.jpg">` корректен относительно `series.html`

## Сторис канала (9:16) — адаптация карточек

Карточки 1080×1350 (4:5). Сторис Telegram — 1080×1920 (9:16). **Если запостить 4:5 как сторис, Telegram зумит по высоте и РЕЖЕТ бока** (заголовок «DYNAMIC» → «NAMIC»). Под сторис карточки нужно вписать в кадр 9:16.

```bash
# 1) собрать 9:16-кадры: png/series-*.png -> story_png/story-*.png
python ~/.claude/skills/cards-creator/scripts/build_story_frames.py
#   карточка центрируется; верх/низ — бесшовные полосы из растянутого+размытого края карточки,
#   пустые полосы попадают под оверлеи Telegram (шапка/ответ), контент не перекрыт
# 2) лимит/уровень/живые сторис
python ~/.claude/skills/cards-creator/scripts/post_stories.py list YOUR_CHANNEL
# 3) запостить новые сторис
python ~/.claude/skills/cards-creator/scripts/post_stories.py post YOUR_CHANNEL
# 4) ИСПРАВИТЬ уже висящие кривые (подмена медиа, НЕ тратит квоту):
python ~/.claude/skills/cards-creator/scripts/post_stories.py edit YOUR_CHANNEL 3,4,5,6,7,8,9,10
```

**Грабли:**
- **Дневной лимит сторис = boost level канала.** Например level 8 → ~8 сторис/сутки. 9-я падает `RPCError 400: BOOSTS_REQUIRED` (и `CanSendStory` тоже). Лимит на *отправленные*, удаление слот в тот же день НЕ возвращает → планируй число карточек под boost level.
- **Чинить живые сторис без расхода квоты — только `EditStoryRequest`** (подмена медиа на месте).
- `EditStory` требует caption и entities **оба заданы или оба None**; чтобы сохранить подпись — передавай **только media**.
- `period=86400`, `privacy_rules=[InputPrivacyValueAllowAll()]`; .session лочится sqlite → работать с копией файла.

## Параллельные скиллы

| Скилл | Связь |
|---|---|
| **`tg-post`** | Пишет текст поста → передаёт структуру cards-creator |
| **`crosspost`** | Адаптирует пост под платформы — карточки переиспользуются для LinkedIn |
| **`image-generation`** (gemini-3.1-flash-image / gpt-image-2) | Генерация placeholder-фото для карточек |
| **`brand-extractor`** | Расширение skill на другие проекты |

## Quick reference

**Источник палитры (read-only):**
```
~/.claude/skills/cards-creator/templates/cards/palette.html
~/.claude/skills/cards-creator/templates/cards/palette-*.css
~/.claude/skills/cards-creator/templates/cards/theme-icons.svg
~/.claude/skills/cards-creator/templates/cards/handoff/photos/
```

**Output новых серий (CWD или /tmp):**
```
./cards-my-series/
├── series.html
├── styles.css (копия palette-*.css)
├── icons.svg (копия theme-icons.svg)
├── photos/  (копия templates/cards/handoff/photos/)
└── png/
```

**render command:**
```
python ~/.claude/skills/cards-creator/scripts/render_cards.py series.html  # → ./png/series-NN.png
```

**image gen (gpt-image-2):**
```
# отредактируй IMAGES в скрипте, затем:
python ~/.claude/skills/cards-creator/scripts/gen_card_images.py ./   # → ./<name>.png
```

**post / schedule (Telethon, не tg_client):**
```python
# ~/.claude/skills/tg-post/scripts/tg_rich_post.py
schedule_album(c, 'YOUR_CHANNEL', files=[...png], html=CAPTION_HTML, when=datetime(...,tzinfo=UTC), spoilers=[...])
```
