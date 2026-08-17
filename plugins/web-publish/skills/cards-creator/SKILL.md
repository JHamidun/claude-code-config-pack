---
name: cards-creator
description: Создание визуальных карточек-каруселей для Telegram-канала — editorial стиль. HTML+CSS → Playwright render → PNG-серия 1080×1350. Готовой библиотеки образцов в паке нет: серия собирается с нуля в рабочей директории по стартовому скелету и каталогу типов карточек из этого файла. Триггеры — «карточки для канала», «карусель в канал», «сделай series», «нарисуй cover», «slides для поста».
---

# Cards Creator — карточки-карусели для Telegram-канала

> Skill для editorial-style carousel-карточек. Production-tested editorial-magazine формат.
> **Библиотека готовых образцов в пак не входит** — это реальные карточки авторского канала, они не публикуются. Всё, что нужно для сборки серии, лежит в этом файле: стартовый скелет (HTML + CSS-токены), каталог типов карточек, правила плотности и рендер-скрипт `scripts/render_cards.py`. Серия собирается **с нуля в рабочей директории** — первая занимает лишний час, дальше копируешь свою предыдущую.

## Когда использовать

- «сделай карточки для поста про X»
- «карусель в канал на тему Y»
- «нарисуй N cards в editorial-стиле»
- «cover + screens + stats серия»
- Из своего навыка-копирайтера постов — если контент имеет list / before-after / 3+ цифры / формат «обзор-подборка-анонс» (см. «Когда пост просит карточки»)

## Workflow — KEY PRINCIPLE

Одна серия = одна отдельная папка. Скилл ничего в себя не пишет — только отдаёт скелет и скрипты.

```
~/.claude/skills/cards-creator/     ← read-only: скрипты + этот файл
├── scripts/render_cards.py         ← HTML → png/series-NN.png
├── scripts/card_image_generator.py ← иллюстрации в едином стиле
└── references/visual-playbook.md   ← тип инфы → визуальный приём

./cards-my-series/                  ← НОВАЯ СЕРИЯ (CWD или /tmp/cards-<topic>/)
├── series.html                     ← карточки: по одному <section class="card"> на штуку
├── styles.css                      ← токены + базовые классы (скелет ниже)
├── img/                            ← иллюстрации/фото/вырезки
├── logo.png, avatar.jpg            ← своя айдентика (опционально)
└── png/                            ← вывод render_cards.py
    ├── series-01.png
    └── ...
```

**Своя библиотека образцов.** Когда серий станет несколько, заведи собственную папку-палитру
(вне скилла, например `~/cards-lib/`) и держи там: `palette.html` со всеми типами карточек в одном
файле, разбитый CSS (`tokens.css` — переменные бренда, `cards.css` — классы под типы,
`fixes.css` — overflow-фиксы), `icons.svg`-спрайт, пул фото и логотип. Дальше новая серия — это
`cp` из своей палитры, а не сборка с нуля. Палитру **не редактируй под конкретную серию** — она
источник истины, правки идут в копии.

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

Разметку каждого типа пишешь сам поверх скелета (см. «Шаг 3»); ниже — каталог, что вообще стоит собирать. Основные семейства:

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

### Шаг 3 — Положи стартовый скелет (или копию своей прошлой серии)

Если серия не первая — просто скопируй `styles.css` предыдущей и правь. Первый раз пиши эти два
файла руками. Скелет минимальный, но рабочий: `render_cards.py` снимает ровно элементы `.card`,
поэтому размер и `overflow` на `.card` — обязательны.

`styles.css`:

```css
/* ---- токены бренда: подставь свои цвета/шрифты ---- */
:root{
  --primary:#3B5BDB; --deep:#0B1021; --cyan:#4DABF7; --cyan-soft:#B5E1FF;
  --cream:#F1F3F5; --cream-warm:#EFE6D6; --ink:#18181B; --terra:#CC7357;
  --yellow:#FFD447; --text:#111; --text-muted:#4A4A55; --border:#D9D2C4;
  --ft-head:"Inter Tight",system-ui;  --ft-body:"Manrope",sans-serif;
  --ft-mono:"JetBrains Mono",monospace; --ft-script:"Caveat",cursive;
}
*{box-sizing:border-box;margin:0}
body{background:#888;display:flex;flex-direction:column;align-items:center;gap:40px;padding:40px}

/* ---- карточка: ровно 1080×1350, её и снимает render_cards.py ---- */
.card{width:1080px;height:1350px;position:relative;overflow:hidden;
  display:flex;flex-direction:column;gap:26px;padding:64px 72px 56px;
  background:var(--cream);color:var(--text);
  font-family:var(--ft-body);font-size:26px;line-height:1.35}
.card.dark{background:var(--deep);color:#fff}

.eyebrow{font-family:var(--ft-mono);font-size:22px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--text-muted)}
h1{font-family:var(--ft-head);font-weight:900;font-size:112px;line-height:.92;
  letter-spacing:-.02em;text-wrap:balance}
.hl{background:linear-gradient(transparent 62%, var(--yellow) 62%)}
.big{font-family:var(--ft-head);font-weight:900;font-size:280px;line-height:.85;
  color:var(--primary);white-space:nowrap}
.lead{font-size:30px;color:var(--text-muted);max-width:34ch}
/* .grow — блок, который съедает свободную высоту. Ровно один на карточку:
   без него всё липнет к верху, а низ карточки читается как дыра (см. ANTI-AIR) */
.grow{flex:1}
.hero{display:flex;flex-direction:column;justify-content:center;gap:18px}
.teaser{list-style:none;padding:0;display:flex;flex-direction:column;font-size:28px}
.teaser li{flex:1;display:flex;align-items:center;border-top:1px solid var(--border)}
/* массивная полоса-вывод вплотную к футеру, а не тонкая строка */
.takeaway{background:var(--deep);color:#fff;border-radius:18px;
  padding:28px 32px;font-size:28px;line-height:1.3}
.foot{font-family:var(--ft-mono);font-size:20px;color:var(--text-muted);
  border-top:1px solid var(--border);padding-top:18px}
```

`series.html` — по одному `<section class="card">` на карточку, в порядке публикации:

```html
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@700;800;900&family=Manrope:wght@400;500;700&family=JetBrains+Mono:wght@500;700&family=Caveat:wght@600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css"></head><body>

<section class="card">                        <!-- 01 · cover-hero -->
  <div class="eyebrow">выпуск 01</div>
  <h1>Заголовок обложки<br><span class="hl">во всю ширину</span></h1>
  <p class="lead">Один абзац лида — о чём серия.</p>
  <ul class="teaser grow">                    <!-- тизер закрывает низ реальным контентом -->
    <li>▸ что разбираем первым</li>
    <li>▸ вторая тема</li>
    <li>▸ третья тема</li>
  </ul>
  <footer class="foot">@yourchannel</footer>
</section>

<section class="card">                        <!-- 02 · stat-hero -->
  <div class="eyebrow">01 / факт</div>
  <div class="hero grow">
    <div class="big">×4</div>
    <p class="lead">Что означает эта цифра.</p>
  </div>
  <div class="takeaway">Вывод карточки — массивная полоса, а не тонкая строка.</div>
  <footer class="foot">@yourchannel</footer>
</section>

</body></html>
```

Проверено: этот скелет рендерится `render_cards.py` как есть и даёт 2160×2700 (1080×1350 @2×).
Обложка высоту держит — тизер-индекс разбивает низ на равные строки. А вот на второй карточке
`.hero` с `justify-content:center` оставляет по ~15% воздуха сверху и снизу от цифры: это ровно
тот случай, который разбирает ANTI-AIR ниже. В боевой колоде это место закрывают вырезкой-объектом
по теме или увеличивают кегль — скелет намеренно оставлен «как получается по умолчанию», чтобы
было видно, с чем борешься.

Дальше наращиваешь классы под нужные типы из каталога выше (`.cmp` таблица, `.bars` график,
`.term` терминал-мок, `.col-img` split с картинкой) — правила плотности и анти-воздух ниже.

### Шаг 4 — Наполни контентом

Каждой карточке — один смысловой блок. Больше 10 карточек не собирай: `sendMediaGroup` берёт максимум 10.

### Шаг 5 — Render через Playwright

```bash
python ~/.claude/skills/cards-creator/scripts/render_cards.py series.html
# → ./png/series-01.png, series-02.png, ...
```

### Шаг 6 — Verify

Открой `./png/series-01.png` в Preview — проверь:
- Headline не обрезан
- Photos загрузились (relative paths корректны)
- Footer-italic читается

### Шаг 7 — Отправь в Telegram

Альбом шлёт бот — `~/.claude/tools/tg_bot.py album` (навык `tg-bot-publish`). Бот должен быть
**админом канала** с правом Post Messages; подпись HTML идёт на первую картинку, лимит альбома — 10 файлов:

```bash
python ~/.claude/tools/tg_bot.py --token MYBOT --dry-run album --to @yourchannel \
  png/series-01.png png/series-02.png png/series-03.png \
  --text "<b>Заголовок</b>\n\nПодпись поста"   # убери --dry-run когда payload устроит
```

`--token` принимает и сам токен, и имя переменной из `~/.claude/.credentials.master.env`.

**Отложка.** В Bot API отложенных постов нет — бот шлёт только «сейчас». Варианты: cron/планировщик
на этой же команде, либо user-аккаунт через Telethon (`send_file(..., schedule=dt)`); у `tg_client.py`
подкоманды `send-album` нет, отложенный альбом — это несколько строк своего кода на Telethon.

## render_cards.py (Playwright скрипт)

`scripts/render_cards.py` уже готов — снимает каждый `.card` в документном порядке. Использование:

```bash
# Установка зависимостей (один раз)
pip install playwright
playwright install chromium

# Render одной серии
python ~/.claude/skills/cards-creator/scripts/render_cards.py path/to/series.html
# → выходные PNG в <папке серии>/png/
```

## Когда пост просит карточки

Признаки, что текстовый пост стоит усилить каруселью:

1. **list ≥ 4 пунктов** в посте
2. **before/after** упоминание
3. **3+ конкретных цифр** в тексте
4. Формат «лонгрид / обзор / подборка / анонс»
5. Тематика «инструмент / стек / сетап»

При ≥ 2 признаках — спроси автора и собирай серию: структура карточек берётся прямо из структуры
поста (пункты списка → `numbered-list`/`checklist`, цифры → `stat-hero`/`stat-grid`, before/after →
`vs-split`). Если пишешь посты отдельным своим навыком-копирайтером, вызов cards-creator удобно
повесить туда же — этот шаг конвейера отдаёт готовый `png/series-NN.png` и подпись.

## ПЛОТНЫЕ КАРТОЧКИ + КАРТИНКИ (gpt-image-2)

> Бриф требует «не бойся насыщать» — пустота на карточках читается как «кастрированно».
> Плотная колода — это 9 карточек примерно такого набора: cover-stats, таблица-сравнение,
> bar-chart, split с картинкой, терминал-мок, effort-таблица, stat-strip, CTA. Приёмы каждого
> расписаны ниже — собери такую колоду один раз и держи её у себя как эталон под копирование.

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

Положи логотип своего проекта рядом с `series.html` как `logo.png` и встраивай **маленьким (~52px) в верхний-правый угол** каждой карточки — не отвлекает, держит айдентику. Один CSS-приём на всю колоду:

```css
.card.inner .ast.tr { display: none; }                 /* логотип занимает место правого астериска */
.card.inner::after { content:""; position:absolute; top:44px; right:52px; width:52px; height:52px;
  background:url('logo.png') center/contain no-repeat; border-radius:12px; z-index:6;
  filter: drop-shadow(0 4px 10px rgba(1,3,52,0.22)); }
```
Для cover-карточки (там свой `::before`/`::after` под фото-фон) — ставь логотип `<img>`-элементом: `.brandlogo-cover { position:absolute; top:46px; right:52px; width:56px; z-index:5; }`.

### Аватарка канала

Аватарку канала зашей в обложку (`.cover-author .ava { background-image:url('avatar.jpg') }`) — файл кладётся рядом с `series.html`. Генерация новых концептов из фото:

```bash
python ~/.claude/skills/cards-creator/scripts/gen_avatar.py <фото.jpg> [concepts|all] [out_dir]
# concepts: brand (PIL-композит, max likeness) | rim (контурное свечение)
#           | circle (светящийся диск) | symbols (парящие code-символы > [] {} <>) | char3d | tech
# gpt-image-2 /edits сохраняет лицо по рефу.
```

### Публикация

Альбом + подпись (HTML: `<b>`, `<tg-spoiler>`, `<blockquote expandable>`, ссылки) — ботом:
`python ~/.claude/tools/tg_bot.py --token MYBOT --dry-run album --to @yourchannel png/series-*.png --text "…"`,
навык `tg-bot-publish`. НЕ `tg_client.py send-album` — такой подкоманды нет.

---

## Common gotchas

1. **Overflow на длинных русских заголовках** → `text-wrap: balance` + line-height: 0.92, размер 96-140px
2. **Шрифты не успевают загрузиться в Playwright** → пауза после networkidle (в `render_cards.py` уже стоит 900 мс)
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
| **`tg-bot-publish`** | Отправка альбома в канал ботом (`tools/tg_bot.py album`) |
| **`image-generation`** (gemini-3.1-flash-image / gpt-image-2) | Генерация иллюстраций и placeholder-фото для карточек |
| **`brand-extractor`** | Вытащить палитру и шрифты чужого бренда → свои токены в `styles.css` |
| свой навык-копирайтер постов | Пишет текст поста → отдаёт сюда структуру серии (в паке такого навыка нет, он у каждого свой под свой канал) |

## Quick reference

**Что даёт скилл (read-only):**
```
~/.claude/skills/cards-creator/scripts/render_cards.py         # HTML → PNG
~/.claude/skills/cards-creator/scripts/card_image_generator.py # иллюстрации в одном стиле
~/.claude/skills/cards-creator/scripts/cut_bg.py               # rembg-вырезка фона
~/.claude/skills/cards-creator/scripts/build_story_frames.py   # 4:5 → 9:16
~/.claude/skills/cards-creator/scripts/post_stories.py         # сторис (Telethon)
~/.claude/skills/cards-creator/references/visual-playbook.md   # тип инфы → приём
```
Готовых HTML/CSS-образцов в паке нет — скелет в «Шаг 3», типы карточек в каталоге выше.

**Output новых серий (CWD или /tmp):**
```
./cards-my-series/
├── series.html
├── styles.css   (скелет из «Шаг 3» или копия прошлой серии)
├── img/         (иллюстрации, вырезки, фото)
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

**post (альбом ботом, до 10 файлов):**
```bash
python ~/.claude/tools/tg_bot.py --token MYBOT --dry-run album --to @yourchannel \
  png/series-01.png png/series-02.png --text "<b>Заголовок</b>"
```
