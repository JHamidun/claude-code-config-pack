---
name: webinar-to-pdf
description: "HTML-презентации, документы и транскрипты → PDF через Playwright. Триггеры: «оформи в PDF», «оформи транскрипт», «создай материалы вебинара»."
version: 0.1.0
type: actionable
---

# Webinar-to-PDF Pipeline

Convert webinar materials (HTML slide presentations, summaries, instructions, transcripts)
into professional PDF documents using Playwright.

## When to Use

- Converting interactive HTML slide presentations to PDF (1 slide = 1 page)
- Generating styled PDF documents (summaries, instructions, guides)
- Formatting raw transcripts into readable, sectioned PDFs
- Full webinar materials pipeline: audio -> transcript -> 4 PDFs -> Диск
- **Пакет по спикерам**: запись мастермайнда/конференции → отдельные видео+транскрипт+саммари на каждый доклад → Яндекс.Диск

## Пайплайн: запись встречи → пакет по докладчикам → Я.Диск

Когда из ОДНОЙ записи (мастермайнд, конференция) нужно сделать **отдельные дельиверблы по каждому докладу** (видео + PDF-транскрипт + PDF-саммари) и выложить публичными ссылками:

1. **Скачать запись.** Zoom share-ссылка + passcode → skill `zoom` → «Download a SHARE recording» (Playwright sniff, yt-dlp не умеет). Своя запись → Zoom API recordings.
2. **Полный транскрипт + диаризация.** `ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 -b:a 64k a.mp3` → Deepgram **REST** `diarize=true&utterances=true` (skill `deepgram`, модель `nova-3`, НЕ старый `PrerecordedOptions`).
3. **Границы докладов.** По `utterances` найти, где модератор передаёт слово (смена доминирующего спикера на длинном отрезке) → таймкоды start/end каждого доклада (`segments.json`).
4. **Нарезать видео.** На каждый доклад `ffmpeg -ss START -to END -i full.mp4 -c copy talk_N.mp4` (copy = без перекодирования, быстро).
5. **PDF транскрипт + саммари** на каждый доклад — этим скиллом (`build_transcript_html.py` → `generate_document_pdf.py`); саммари пишет Claude по транскрипту доклада.
6. **Залить на Я.Диск** папками `NN_Тема_Спикер/` (video.mp4 + transcript.pdf + summary.pdf), собрать публичные ссылки (`_file_urls.json`).

**Разовые скрипты пайплайна держи рядом с материалами, а не внутри навыка** — они
привязаны к конкретной записи (таймкоды, имена докладов) и в переиспользование не идут.
Рабочая раскладка папки встречи: `_download.py`, `_transcribe.py`, `_slice_videos.py`,
`_build_all_pdfs.py`, `_upload.py`, `_file_urls.json` + сам материал. Навык даёт шаги и
генераторы PDF; склейка под конкретную запись — одноразовая.

Если контент идёт ещё и в свой канал — посты и карточки см. `tg-post` + `cards-creator`.
**Для чужих встреч свой канал не упоминать вовсе**: пакет отдаётся заказчику, и реклама
в нём выглядит как злоупотребление доступом к записи.

## Architecture

Source materials (audio, HTML presentation) -> transcription (Deepgram or another ASR)
-> HTML documents (presentation, summary, instructions, transcript) -> Playwright
(headless Chromium, `file://` or a local `127.0.0.1` server) -> PDF files -> Диск.

## Что тебе понадобится

| Что | Зачем | Платно? |
|---|---|---|
| Playwright + Chromium | вся генерация PDF | нет |
| `Pillow`, `img2pdf`, `PyMuPDF` | слайды → JPEG → PDF, проверка результата без poppler | нет |
| **ffmpeg** | извлечь звук из записи и нарезать видео по докладам | нет, ставится отдельно от pip |
| **Deepgram API key** (`DEEPGRAM_API_KEY`) | транскрипт с диаризацией; ~$0.0043/мин, час записи ≈ $0.26 | **да**, но есть стартовый грант |
| `YANDEX_OAUTH_TOKEN` **или** Google OAuth | выложить пакет и получить публичные ссылки | нет |

Ветка «у меня уже есть текст транскрипта» бесплатна целиком: Deepgram нужен только чтобы
получить текст из аудио.

```bash
pip install playwright Pillow img2pdf PyMuPDF requests
playwright install chromium
# ffmpeg: winget install Gyan.FFmpeg | brew install ffmpeg | apt install ffmpeg
```

## Two PDF Generation Methods

Base headless-Chromium mechanics — launching, `page.pdf()`, per-slide screenshots, font
waits, "PDF came out blank" — live in `export-pdf` / `export-png` and are not repeated
here. Below is only what webinar materials add on top.

### Method 1: Screenshot Approach (slide presentations)

`export-png` drives `<deck-stage>` + `goToSlide(i)`; webinar decks use a different
contract (`.slide.active` toggling), which plain `page.pdf()` cannot separate — hence
a local script: screenshot each slide -> JPEG (quality=90) -> `img2pdf`.

```bash
python scripts/generate_presentation_pdf.py --url http://127.0.0.1:8889/presentation.html --output presentation.pdf
```

- Viewport 1920x1080; each slide MUST fit — on overflow reduce font sizes/paddings
- PNG -> JPEG drops ~40MB to ~7MB for 55 slides; `img2pdf.get_fixed_dpi_layout_fun((96, 96))` fixes page size
- **CRITICAL: kill CSS animations before screenshots.** `animation: slideIn` or `opacity: 0` + `transition` render as empty/transparent slides — inject CSS that disables animations and forces opacity (pattern in the script; symptom row in `references/gotchas.md`)

### Method 2: page.pdf() (text documents)

Summaries, instructions, transcripts — normal flow layout, mechanics per `export-pdf`.
Wrapper: `python scripts/generate_document_pdf.py --url http://127.0.0.1:8889/document.html --output document.pdf`
— A4, margins 10mm, `print_background=True`, `@media print` for page breaks.

## Local files: `file://` works — the server is for fetch/modules only

Playwright does **not** block `file://`: both neighbour skills open local HTML exactly
that way (`pathToFileURL(path.resolve(file)).href`). What breaks under `file://` is the
browser's CORS policy on resources the page fetches itself — `fetch`/XHR to local JSON
and `<script type="module">`. Plain markup, inline CSS and `<img>` load fine. So serve
over HTTP only when the page pulls its own data: `python scripts/start_server.py --dir . --port 8889`.

**Critical:** `127.0.0.1`, NOT `localhost` — Playwright sometimes fails to resolve `localhost`.

## HTML contracts

**Slides** (what `generate_presentation_pdf.py` drives): `.slide` absolutely positioned
and `display:none`, the visible one marked `.slide.active`, `body` pinned to 1920x1080,
`overflow:hidden` everywhere. Navigation: ArrowRight/Space = next, ArrowLeft = prev.
Готовый CSS — `references/styling-guide.md` (Slide Layout + Viewport Constraints).

**Documents** (summaries, instructions) — общая библиотека компонентов: `.header` `.step`
`.prompt-box` `.tip-box` `.warning-box` `.webinar-quote` `.table` `.grid-2`+`.card`,
плюс TOC, timestamp-badge и stats-bar для транскриптов; HTML/CSS каждого —
`references/html-components.md`. Не пересобирать по описанию: классы завязаны на
print-CSS оттуда же, свой вариант ломает разрывы страниц.

## Transcript Formatting

To format a raw transcript (format: `[MM:SS] Speaker N: text`) into styled HTML:

1. Parse entries with regex: `\[(\d+:\d+)\]\s*Speaker\s*\d+:\s*(.*)`
2. Group consecutive entries into paragraphs (gap < 25s AND total < 600 chars)
3. Define topic sections manually by timestamp boundaries
4. Generate HTML with TOC, section headers, timestamped paragraphs

Run `scripts/build_transcript_html.py` — edit the `sections` list for topic boundaries.

## Reference-style package (gradient cover + методичка) ⭐

Эталонный стиль пакета материалов вебинара. Спецификация ниже самодостаточна:
генератор `_build_package.py` пишется по ней под свой бренд за один заход и живёт
рядом с материалами встречи, а не внутри навыка.

**Обложка (`cover()`):** полностраничная градиентная секция в цвете бренда
`height:262mm; margin:-18mm`, eyebrow «ЗАКАЗЧИК × ИМЯ СПИКЕРА» (крупный letter-spacing),
огромный заголовок `ТРАНСКРИПТ` / `САММАРИ` (Manrope 900, 74pt), белая черта,
название вебинара, дата. Рендер — HTML + Playwright `page.pdf()` A4,
`print_background=True`, margins 0.

**Транскрипт:** cover → meta-strip → **Содержание** (TOC: раздел + таймкод справа) → **разделы по таймкодам** (h2 с левой синей чертой; границы задаются вручную списком `(start_sec, title)`) → блоки `[таймкод] **Спикер.** текст` (таймкод слева жирным синим, группировка ~90с / смена спикера).

**Саммари = ОБРАЗОВАТЕЛЬНАЯ МЕТОДИЧКА, а не пересказ «о чём говорили».** Обязательные блоки: metabox «О вебинаре», формула промпта (`.formula`), таблица инструментов с колонкой **«доступен ли из твоей страны»** (для аудитории под региональными ограничениями это первый вопрос к любому инструменту), по каждой задаче — тёмный **промпт-бокс** (`.prompt`) для копирования, чек-лист «с чего начать» (`.chk` с ☐), глоссарий, контакты. CSS-компоненты: `.prompt .formula .callout .hl .chk .gloss .metabox`.

**Склейка 2+ записей (два файла с диктофона) в один документ:** части идут по порядку;
таймкоды второй части **смещаются на длительность первой** (`OFFSET = part1_end + ~60с`)
→ сквозное время. Спикеров нормализовать: диаризация регулярно дробит ОДНОГО человека
на `Speaker 1` и `Speaker 3` — сверить по содержанию реплик и слить руками
(`Speaker 1 + Speaker 3 → «Имя спикера»`, остальные → «Слушатель»). Автоматике тут верить
нельзя: через паузу между файлами сшивка по голосу не работает.

**НЕ сваливать сырой markdown из диктофонных сервисов** в саммари: в нём остаются
плейсхолдеры вида `[Insert Question]`, служебные блоки «Задания» / «План действий» с
чекбоксами, картинки-водяные знаки сервиса и **систематические опечатки в названиях
продуктов** — ASR слышит бренд неправильно и пишет уверенно (`Loveable` вместо `Lovable`).
Всё чистить и переписывать редакторски. Названия инструментов проверять отдельным
проходом: в методичке неверное название означает, что читатель просто не найдёт продукт.

**Голос для устных материалов** (спикерноутсы, скрипт): `~/.claude/voice-sample.md`
(шаблон — `~/.claude/templates/voice-sample.md`).

## Color Scheme by Topic

Пример раскладки «тема → цвет»: назначь свои темы, палитра переносимая.

| Topic | Border color | Step circle class |
|-------|-------------|-------------------|
| AI-инструмент №1 | `#8b5cf6` | `.purple` |
| AI-инструмент №2 | `#10b981` | `.green` |
| Gemini | `#4285F4` | `.blue` |
| Telegram | `#0088cc` | `.tg` |
| Agents | `#f97316` | `.orange` |
| n8n | `#ea4c89` | `.pink` |
| Prompts | `#2D2FE8` | `.navy` |
| Tips | `#14b8a6` | `.teal` |

## Google Drive Upload

Готовым клиентом `python ~/.claude/tools/gdrive_client.py` (`/gdrive`, хаб —
`google-workspace`): папки, публичный доступ и токен там уже обработаны. Своего кода на
`googleapiclient` не писать — дубль расходится с клиентом при первой смене скоупов.

## Yandex Disk Upload ⭐

Русскоязычной аудитории пакет удобнее отдавать на **Яндекс.Диск**, а не на Google Drive:
у части зрителей Drive не открывается без VPN, и половина ссылок «не работает» ещё до
того, как человек дошёл до материала.

**REST-рецепт (mkdir → upload сырым телом → publish → public_url → удаление навсегда)
вынесен в `references/yandex-disk-rest.md`** — он нужен не только вебинарам; доступы и
полная таблица эндпоинтов живут в скилле `yandex`. Здесь — только политика пакета:

- **На Диске — ТОЛЬКО PDF для пользователей.** Редактируемые исходники (docx/xlsx/pptx) НЕ заливать — держать локально. Если по ошибке залил папку `Исходники_*` — удалить `permanently=true`.
- Структура пакета: `Презентация/`, `Транскрипт_и_саммари/`, `Гайд_инструменты/`.
- В пакет добавляй **гайд-таблицу инструментов** (что делает / цена / доступен ли из твоей страны / сайт) отдельным landscape-PDF. Это самый частый вопрос после вебинара — без таблицы он приходит в личку по одному.

## Verify PDFs without poppler/LibreOffice

`pdftoppm` часто отсутствует на Windows. Рендер страниц через **PyMuPDF**: `fitz.open(p)[i].get_pixmap(dpi=80).tobytes('png')` → собрать в сетку PIL и `Read`. Презентацию из картинок-слайдов в PDF собирать через PIL `append_images` (без LibreOffice).

## Pre-Flight Checklist

- [ ] Every slide fits within 1920x1080 (no overflow)
- [ ] Promo codes and contacts are correct across ALL HTML files
- [ ] If the page fetches its own data — server is up on 127.0.0.1 (otherwise `file://` is fine)
- [ ] PDF page count matches slide count (for presentations)
- [ ] `@media print` CSS rules prevent broken page breaks (for documents)
- [ ] Uploaded folder is published (Я.Диск `public_url` / Drive "anyone can view")

## Additional Resources

### Reference Files

- **`references/html-components.md`** — Full HTML/CSS code for all document components (header, steps, prompt-box, tip-box, tables, cards, footer)
- **`references/gotchas.md`** — Common problems and solutions (file locking, encoding, parallel Playwright, emoji rendering)
- **`references/styling-guide.md`** — Dark theme CSS for presentations, light theme CSS for documents, print CSS
- **`references/yandex-disk-rest.md`** — Я.Диск REST: mkdir / upload сырым телом / publish / public_url / удаление навсегда

### Neighbour skills (не дублировать здесь)

`export-pdf` — печать HTML в PDF headless-Chromium · `export-png` — скриншоты слайдов ·
`yandex` — доступы и полная таблица эндпоинтов Диска · `google-workspace` — Drive-клиент.

### Scripts

- **`scripts/generate_presentation_pdf.py`** — Screenshot approach: slides -> JPEG -> PDF
- **`scripts/generate_document_pdf.py`** — page.pdf() approach for text documents
- **`scripts/build_transcript_html.py`** — Parse and format transcript into styled HTML
- **`scripts/start_server.py`** — HTTP server for pages that fetch their own local data

### Reference Implementation

Готового демо-пакета в навыке нет намеренно: он весит десятки мегабайт и устаревает
вместе с контентом. Первый свой пакет собирается по шагам выше; контракты HTML
(`.slide.active`, компоненты документов) и готовый CSS лежат в `references/` —
их достаточно, чтобы получить рабочий PDF с первого прогона.
