---
name: cards-creator
description: "Карточки-карусели для Telegram-канала: HTML+CSS → Playwright → PNG 1080×1350. Триггеры: «карточки для канала», «карусель в канал»."
---

# Cards Creator — карточки-карусели для Telegram-канала

Editorial-style карусели: HTML+CSS → Playwright → PNG → альбом в канал.

**Готовых образцов в паке нет** — это реальные карточки авторского канала, они не публикуются.
Всё для сборки серии здесь: скелет (HTML + CSS-токены), рендер-скрипт, правила плотности.
Серия собирается **с нуля в рабочей директории**; первая занимает лишний час, дальше копируешь
свою предыдущую.

## Раскладка файлов

Одна серия = одна отдельная папка. Скилл ничего в себя не пишет — только отдаёт скрипты и скелет.

```
~/.claude/skills/cards-creator/     ← read-only
├── scripts/render_cards.py         ← HTML → png/series-NN.png
├── scripts/card_image_generator.py ← иллюстрации в едином стиле
├── scripts/cut_bg.py               ← rembg-вырезка фона
├── scripts/build_story_frames.py   ← 4:5 → 9:16
├── scripts/post_stories.py         ← сторис (Telethon)
└── references/                     ← каталог типов, плотность, сторис, visual-playbook

./cards-my-series/                  ← НОВАЯ СЕРИЯ (CWD или /tmp/cards-<topic>/)
├── series.html                     ← по одному <section class="card"> на карточку
├── styles.css                      ← токены + базовые классы (скелет ниже)
├── img/                            ← иллюстрации/фото/вырезки
├── logo.png, avatar.jpg            ← своя айдентика (опционально)
└── png/series-01.png, ...          ← вывод render_cards.py
```

**НЕ создавай серию внутри `~/.claude/skills/cards-creator/`** — скилл общий и read-only,
рабочие файлы серии там ломают его при следующем обновлении пака.

## Параметры

| Параметр | Значение |
|---|---|
| Размер | **1080×1350px** (4:5 portrait, Telegram-friendly) |
| Формат | PNG, 2× DPI (device_scale_factor=2) |
| Серия | 5-9 карточек (sweet spot 7) |
| Файлы | `series-NN.png` (01, 02, 03...) |
| Posting | `sendMediaGroup` (album), caption на первой, **максимум 10 файлов** |

## Workflow

### Шаг 1 — структура серии

Количество карточек (5-9) и типы под контент: cover-hero + 4-5 inner (list/stat/compare) + closer.
Каталог из ~40 типов по семействам (Cover, Stat, List, Quote, Compare, Process, UI-mock, Special)
→ `references/card-types.md` — открывай, когда нужен выбор шире очевидного набора.

### Шаг 2 — папка в CWD

```bash
mkdir -p ./cards-my-series/png && cd ./cards-my-series
```

### Шаг 3 — стартовый скелет

Не первая серия — копируй `styles.css` предыдущей и правь. Первый раз пиши руками.
`render_cards.py` снимает ровно элементы `.card`, поэтому **фиксированный размер и `overflow:hidden`
на `.card` обязательны** — без них кадр «поедет» и PNG выйдет не 1080×1350.

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

Скелет проверен: рендерится как есть и даёт 2160×2700 (1080×1350 @2×). Обложку тизер-индекс
держит по высоте, а вот `.hero` с `justify-content:center` на второй карточке оставляет по ~15%
воздуха сверху и снизу — это ровно случай из ANTI-AIR ниже, оставлен намеренно, чтобы было
видно, с чем борешься. В боевой колоде место закрывают вырезкой-объектом или крупнее кеглем.

Дальше наращиваешь классы под нужные типы (`.cmp` таблица, `.bars` график, `.term` терминал-мок,
`.col-img` split с картинкой) — приёмы плотности в `references/editorial-density.md`.

### Шаг 4 — контент

Каждой карточке — один смысловой блок. Больше 10 карточек не собирай: `sendMediaGroup` берёт максимум 10.

### Шаг 5 — рендер

```bash
pip install playwright && playwright install chromium     # один раз
python ~/.claude/skills/cards-creator/scripts/render_cards.py series.html
# → ./png/series-01.png, series-02.png, ...
```

### Шаг 6 — verify

Открой `./png/series-01.png` глазами: headline не обрезан, фото загрузились (relative paths),
футер читается. Плюс обязательный аудит воздуха — см. ANTI-AIR.

### Шаг 7 — публикация

Альбом шлёт бот, `~/.claude/tools/tg_bot.py album` (навык `tg-bot-publish`). Бот должен быть
**админом канала** с правом Post Messages. Подпись (HTML: `<b>`, `<tg-spoiler>`,
`<blockquote expandable>`, ссылки) идёт на первую картинку:

```bash
python ~/.claude/tools/tg_bot.py --token MYBOT --dry-run album --to @yourchannel \
  png/series-01.png png/series-02.png png/series-03.png \
  --text "<b>Заголовок</b>\n\nПодпись поста"   # убери --dry-run когда payload устроит
```

`--token` принимает и сам токен, и имя переменной из `~/.claude/.credentials.master.env`.
НЕ `tg_client.py send-album` — такой подкоманды нет.

**Отложка.** В Bot API отложенных постов нет, бот шлёт только «сейчас». Варианты: cron на этой же
команде, либо user-аккаунт через Telethon (`send_file(..., schedule=dt)`) — это несколько строк
своего кода, готовой подкоманды нет.

## ⛔ ANTI-AIR — воздух на карточках (повторяющийся косяк)

Размытое «fill height» НЕ работает — нужны конкретные рычаги и независимый аудит.
**Fail-условие: любая пустая полоса (cream или navy) > ~8% высоты карточки (≈108px на 1350).**

**Корневые причины — ищи именно их в `series.html`:**
- `flex:1 1 auto; justify-content:center` на главном блоке → контент висит в центре, пусто сверху И снизу.
- колонки (`triplet`/`strip`/`cmp2`) с `flex:1`, а число прижато к низу/верху колонки → пустая треть.
- `.note-flow { margin-top:auto }` → тонкая строка улетает в самый низ, над ней дыра.
- `.formula`/панель с `flex:1 + justify-content:center` → текст в верхней трети, низ панели пустой (на тёмном фоне читается как провал).
- cover: контент прижат к низу, сверху пустой навигейт.

**Рычаги (точечно):**
1. Колонки: группа `flex:1`, КАЖДАЯ колонка `display:flex;flex-direction:column;justify-content:center`.
2. Тонкую `.note-flow` → массивная тёмная `.takeaway`-полоса (2-3 строки, padding 26-30px), доходящая до футера. Зазор между последним блоком и футером не оставляй никогда.
3. `flex:1`-панель: либо `justify-content:flex-start` + контент сверху, либо `flex:0 0 auto` и распределить карточку через `justify-content:space-between` — но только когда у блоков есть масса.
4. Две неравные колонки: обе `flex:1`, в короткой `justify-content:space-between` или добавь 1 правдивый пункт.
5. Межблочные отступы урезать до 22-28px, отвоёванное отдать главному блоку (крупнее шрифт/боксы).
6. Дыру на cover закрыть cutout-картинкой или тизер-списком «▸ В РАЗБОРЕ» (реальный контент).

**Обязательный гейт.** Генерящий агент СИСТЕМАТИЧЕСКИ недооценивает свой воздух: говорит «8%»,
аудит видит 14% — он смотрит на свой замысел, а не на пиксели. Поэтому после рендера всегда
**независимый visual-аудит**: отдельный агент читает PNG, меряет пустые полосы в % и заворачивает
всё, что >8-10%. Без этого гейта не публиковать.

## Overflow-фиксы

- Длинная двусоставная цифра («11 дней») → `white-space:nowrap` + unit меньшим кеглем, `big` ~210-240px (не 360).
- Плотные карточки → `h1.tiny` (72px) вместо 100-108px, чтобы влез контент ниже.
- `footnote` позиционируется `absolute` снизу — не считай его в потоке, оставляй ему место.

## Когда пост просит карточки

Признаки, что текстовый пост стоит усилить каруселью: список ≥4 пунктов · упоминание before/after ·
3+ конкретных цифр · формат «лонгрид/обзор/подборка/анонс» · тематика «инструмент/стек/сетап».

При ≥2 признаках спроси автора и собирай серию: структура карточек берётся прямо из структуры поста
(пункты → `numbered-list`/`checklist`, цифры → `stat-hero`/`stat-grid`, before/after → `vs-split`).

## Common gotchas

1. **Overflow на длинных русских заголовках** → `text-wrap: balance` + `line-height:0.92`, размер 96-140px.
2. **Шрифты не успевают загрузиться в Playwright** → пауза после networkidle (в `render_cards.py` уже стоит 900 мс).
3. **SVG sprite IDs дублируются** при merge нескольких серий — уникальный prefix на серию.
4. **PNG >2MB** — Telegram пережимает крупные файлы, качество падает; держи каждый под 2MB.
5. **Album max 10 photos** в `sendMediaGroup` — серия больше → split на два поста.
6. **device_scale_factor=2** = retina @2x, иначе на телефоне мыло.
7. **Photos в карточках** — `object-fit:cover` + `object-position:center 38%` (фокус на лице у портретов).
8. **Relative paths** — после копирования файлов проверь `<img src="img/xxx.jpg">` относительно `series.html`.

## Справочники

| Файл | Когда читать |
|---|---|
| `references/card-types.md` | подбираешь состав серии, нужен каталог типов шире очевидного |
| `references/editorial-density.md` | колода получилась typography-only или дешевле референса: приёмы плотности, gpt-image-2, вырезки rembg, логотип и аватар |
| `references/visual-playbook.md` | ПЕРЕД генерацией картинок: тип инфы → визуальный приём → метафора-объект |
| `references/stories-9x16.md` | ту же серию нужно выложить сторис (другой кадр + лимит по boost level) |

## Параллельные скиллы

| Скилл | Связь |
|---|---|
| `tg-bot-publish` | отправка альбома в канал ботом (`tools/tg_bot.py album`) |
| `image-generation` | генерация иллюстраций и placeholder-фото |
| `brand-extractor` | вытащить палитру и шрифты чужого бренда → свои токены в `styles.css` |
| свой навык-копирайтер постов | пишет текст поста → отдаёт сюда структуру серии (в паке такого нет, он у каждого свой) |
