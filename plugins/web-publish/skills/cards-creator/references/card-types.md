# Каталог типов карточек

Читать, когда набираешь структуру серии и нужен выбор шире, чем «обложка + список + CTA».
Разметку каждого типа пишешь сам поверх скелета из SKILL.md — здесь только каталог,
что вообще стоит собирать.

## Cover / Hero
- **cover-hero** — большой headline + автор + eyebrow выпуска
- **cover-photo** — cover с фото автора
- **pattern (magazine)** — обложка глянцевого журнала с photo + pattern
- **ASCII-cover** — гигантская ASCII-art на navy CRT

## Stat / Data
- **stat-hero** — одна гигантская цифра + объяснение
- **stat-grid 2×2** — 4 метрики + sparklines
- **stat-grid 3×2** — 6 метрик
- **dashboard.live** — фейковый data-дашборд с metrics + chart

## List / Structure
- **checklist** — 5-7 пунктов с галочками
- **numbered-list** — file-card стиль
- **anti-tip** — список ошибок «так НЕ делай»
- **glossary** — cheat-sheet терминов

## Quote / Voice
- **quote** — большая цитата + post-it стикер
- **hot-take** — manifesto на terra-bg
- **quote-tweet** — фейковая цитата чужого поста
- **diary-note** — handwritten заметка Caveat
- **quote-bomb** — одна фраза на всю карточку
- **napkin-sketch** — full Caveat handwritten

## Compare / Decision
- **vs-split** — раньше vs сейчас
- **mini-case** — case study before/after
- **comparison-matrix** — feature grid
- **myth-buster** — МИФ vs РЕАЛЬНОСТЬ
- **before/after photo** — 2 photos split

## Process / Chart
- **steps** — numbered process
- **timeline** — события по датам
- **chart-line** — линейный график (navy)
- **chart-bar** — bar chart
- **process-flow** — pipeline с stages + arrows + dotted-arc

## UI Mocks (visual hooks)
- **chat-quote** — имитация Telegram-сообщения
- **macOS Terminal** — mac-dots + shell prompt
- **VS Code** — line-numbers + filename tab
- **Notion-page mockup** — sidebar + content blocks

## Special / Format-driven
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

## Распределение фонов по колоде

70% cream / 15% navy / 10% terra solid / 5% gradient/special. Однотонная колода
читается как шаблон; варьируй фон, иначе премиум-эффекта не будет.

## Своя библиотека образцов

Когда серий станет несколько, заведи собственную папку-палитру вне скилла
(например `~/cards-lib/`): `palette.html` со всеми типами в одном файле, разбитый CSS
(`tokens.css` — переменные бренда, `cards.css` — классы под типы, `fixes.css` — overflow-фиксы),
`icons.svg`-спрайт, пул фото и логотип. Дальше новая серия — это `cp` из палитры, а не
сборка с нуля. Палитру **не редактируй под конкретную серию**: она источник истины,
правки идут в копии.
