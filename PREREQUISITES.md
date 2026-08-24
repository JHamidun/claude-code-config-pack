# Что должно быть на машине

Список собран разбором самого пака: импорты вытащены из синтаксического дерева
299 Python-файлов, npm-зависимости — из четырёх `package.json`, внешние программы —
поиском вызовов по скиллам. Это не «на всякий случай», а то, что действительно
кто-то вызывает.

Большую часть доводит `python3 ~/.claude/scripts/setup_runtime.py` — он ставит
браузер Playwright, регистрирует маркетплейсы плагинов и подтягивает лёгкие
node-зависимости. Установщик запускает его сам; `--check` показывает, чего не хватает,
ничего не устанавливая.

Он же проверяет внешние программы из таблицы ниже — таблица собрана из его собственного
списка (`EXTERNAL_TOOLS` в `.claude/scripts/setup_runtime.py`), и расходится с ним ровно
в одной последней строке, о чём там же и сказано. По каждой отсутствующей он печатает,
какие скиллы отвалятся и команду установки под твою ОС. Ставить их за тебя он не берётся.
Отсутствие программы «по потребности» не меняет код возврата, но в отчёте она есть
всегда — в том числе когда всё остальное готово.

---

## Обязательное

Без этого не работает заметная часть пака.

| Что | Зачем | Проверка |
|-----|-------|----------|
| **Python 3.10+** | 46 скиллов и все общие CLI в `~/.claude/tools/` | `python --version` **или** `python3 --version` — см. врезку ниже |
| **Node.js 18+** (с `npm`, `npx`) | 68 мест: браузерная автоматизация, сборка, экспорт | `node --version` |
| **git** | 53 места: плагины, маркетплейсы, рабочие процессы | `git --version` |
| **Git Bash** (только Windows) | ~1000 строк в навыках написаны на POSIX-синтаксисе (`2>/dev/null`, `$(…)`, `/tmp/…`, фоновый `&`). В `cmd.exe` и PowerShell они не работают | ставится вместе с Git for Windows: `winget install Git.Git` |
| **Chromium через Playwright** | скриншоты, PDF/PNG-экспорт, парсинг, проверки вёрстки | ставится `setup_runtime.py` |

> **`python` или `python3` — на разных ОС по-разному, и это не мелочь.**
> Установщик python.org и `winget` на Windows кладут только `python.exe`; имя
> `python3` там ведёт в заглушку Microsoft Store, которая **открывает магазин вместо
> запуска**. macOS 12.3+ не несёт `python` вовсе, Ubuntu 22.04+ — без пакета
> `python-is-python3`. В теле навыков 642 команды записаны как `python <скрипт>`,
> в документации пака — `python3`. Работать будет то имя, которое есть у тебя;
> `setup_runtime.py --check` первой же строкой печатает, какое именно, и что делать
> со вторым.

```bash
pip install --user -r requirements.txt   # см. врезку про PEP 668 ниже
npx playwright install chromium          # или просто setup_runtime.py
```

> **Если `pip install --user` отказал с `externally-managed-environment`** — это PEP 668,
> штатное поведение macOS с Homebrew, Debian 12+, Ubuntu 23.04+, Fedora 38+ и Arch.
> Не «мелкая неполадка»: без этих пакетов падает каждый второй скилл с
> `ModuleNotFoundError`. Два рабочих пути:
> `pip install --user --break-system-packages -r requirements.txt` (быстро) или
> отдельное окружение: `python3 -m venv ~/.claude-venv && ~/.claude-venv/bin/pip install -r requirements.txt`
> — тогда зови скрипты через `~/.claude-venv/bin/python`.

## Python-пакеты

`requirements.txt` — рабочий минимум, ставится целиком за пару минут.
Самые востребованные: `requests` (13 скиллов), `pillow` (10), `playwright` (7),
`numpy` (6), `python-dotenv` (5), `google-genai` и `telethon` (по 4).

`requirements-optional.txt` — тяжёлое и нишевое: `torch`, `opencv-python`,
`openai-whisper`, `whisperx`, `ultralytics`, `rembg`, `qdrant-client`, `chromadb`.
Ставить целиком не нужно — только строку под тот скилл, который понадобился.

Пять зависимостей не ставятся из PyPI вообще, и это отмечено в самом файле:
`madmom`, `sam2`, `captacity` (сборка из исходников или git), `liteparse`
(поставляется вендором), `opf` (локальная модель на устройстве). Скиллы, которые их
используют, описывают установку у себя.

## Node

Четыре проекта со своими зависимостями. `setup_runtime.py` ставит первые два,
остальные — по требованию, они тянут React и рендер-тулчейн на сотни мегабайт:

| Проект | Ставится сразу | Зачем |
|--------|----------------|-------|
| `skills/dev-browser` | да | браузер с сохранением сессии |
| `skills/gstack` | да (нужен **Bun**: точка входа компилируется `bun build --compile`, npm её собрать не может) | быстрый headless-обход страниц |
| `skills/video-shotcraft/template` | нет | Remotion: промо-ролики |
| `skills/video-generation/remotion-overlays` | нет | Remotion: оверлеи |

Пятый `package.json` лежит в самом `~/.claude` — это локальные копии MCP-серверов
(`npm install --prefix ~/.claude`). Ставить не обязательно: без них серверы работают
через `npx`, просто каждый разворачивается в 5 процессов ОС вместо 2. Ещё два
`package.json` принадлежат отдельным навыкам (`book-post/scripts`, пример скелета в
`autonomous-agent-creator`) и ставятся этими навыками.

## Внешние программы

Ставить по потребности — без них отваливаются конкретные скиллы, а не пак целиком.
Таблица собрана из списка `EXTERNAL_TOOLS` в `.claude/scripts/setup_runtime.py`:
`--check` проверяет каждую её строку, кроме последней (там сказано, почему).
Счёт — по навыкам, агентам и командам, которые программу действительно **вызывают**,
а не по числу упоминаний слова в текстах: в прежней редакции ImageMagick получил так
27 «единиц» из-за английского глагола *convert*, а `pandoc` и бинарь `sqlite3`
требовались при нуле вызовов.

| Программа | Кто ждёт | Ради чего |
|-----------|----------|-----------|
| `curl` | 43 навыка + 8 агентов + 5 команд | обращения к API из примеров и скриптов |
| `ffmpeg` + `ffprobe` | 20 навыков + 6 агентов video-factory | всё видео и аудио |
| `gh` | 14 навыков + 12 агентов | работа с GitHub из скиллов |
| `docker` | 12 навыков + 3 команды | локальные сервисы, n8n, сборки |
| `pnpm` | 9 навыков + 14 агентов + 6 команд | `pnpm type-check && pnpm build` из `rules/quality-gates.md`, health-inline, run-quality-gate |
| `yt-dlp` | 8 навыков | скачивание видео (**+ ffmpeg**: без него 1080p не склеить, качается 360p/720p и без ошибки) |
| `jq` | github-import, brand-extractor, notebooklm, last30days, примеры higgsfield | разбор JSON в bash-конвейерах |
| `uv` | ace-step, edit-banana, python-fullstack-dev, video-shotcraft, last30days | быстрые venv и подбор Python 3.12 |
| `bun` | gstack (целиком), cards-creator, dev-browser, openwiki | сборка бинарей, быстрый рантайм |
| poppler (`pdftotext`, `pdftoppm`) | pdf, document-import, last30days | разбор PDF и превью страниц (в `webinar-to-pdf` есть запасной путь через PyMuPDF) |
| LibreOffice (`soffice`) | docx, pptx, export-pptx, video-generation | `soffice --headless --convert-to pdf` — конвертация офисных форматов |
| `whisper` (**CLI**, не Python-пакет) | video-montage | субтитры и word-timestamps |
| `unzip` | last30days/build-skill.sh | распаковка zip; в `document-import` уже есть запасной путь через python-`zipfile`, там отсутствие `unzip` не смертельно |
| ImageMagick | pwa-shell (зовёт `magick`, IM7), web-assets-generator (зовёт `convert`, IM6) | иконки PWA и фавиконы |
| `tesseract` | edit-banana с `ocr.engine: tesseract` | OCR (по умолчанию там другой движок) |
| `bd` (beads) | навык `beads`, команда `/beads-init` | трекер задач для агентов |
| `codegraph` | codegraph, openwiki | граф вызовов, callers/callees/impact |
| `lsof` | webapp-testing, dev-browser, skill-creator | освободить занятый порт; на Windows нет — там `netstat -ano` |
| `rsync`, `wget` | по 1–2, всегда с фолбэком | точечно — **единственные две строки таблицы, которых `--check` не проверяет**: у обеих в коде уже есть запасной путь (`install.sh` берёт `hm_copy()` вместо `rsync`), и их отсутствие ничего не ломает |

**ImageMagick зовут двумя разными именами.** IM7 ставит `magick`, IM6 — `convert`.
На Windows `convert.exe` существует всегда, но это системная утилита перевода FAT в
NTFS: команда из навыка ответит `Invalid drive specification.` от чужой программы.
Проверка в `setup_runtime.py` это имя на Windows игнорирует специально.

**Чего в таблице нет и не будет:** `sqlite3` (бинарь не зовёт ни один скрипт — он есть
только в денилистах защитного хука; питону хватает stdlib-модуля) и `pandoc` (не
упомянут в паке ни разу). Прежняя редакция требовала ставить обе программы.

Строки установки — то, что печатает `setup_runtime.py --check` по каждой отсутствующей.
Одним заходом:

```powershell
winget install Git.Git OpenJS.NodeJS.LTS Gyan.FFmpeg GitHub.cli jqlang.jq astral-sh.uv `
              yt-dlp.yt-dlp TheDocumentFoundation.LibreOffice ImageMagick.ImageMagick QPDF.QPDF
npm install -g pnpm
powershell -c "irm bun.sh/install.ps1 | iex"   # Bun
winget install oschwartz10612.Poppler   # poppler; после установки проверь `pdftoppm -v` в НОВОМ терминале
```

```bash
brew install git node ffmpeg gh jq uv pnpm yt-dlp poppler qpdf imagemagick oven-sh/bun/bun
brew install --cask libreoffice
```

```bash
sudo apt install git nodejs npm ffmpeg jq unzip lsof poppler-utils qpdf imagemagick libreoffice-calc
npm install -g pnpm
curl -fsSL https://bun.sh/install | bash
```

## Ключи

Пак спроектирован работать **без единого платного ключа** — это проверяется на каждом
коммите отдельной проверкой, и её не обойти незаметно. Модели ходят через подписку
Claude Code.

Полный список имён переменных — один файл: `.claude/templates/.credentials.master.env.example`
в клоне, после установки он же лежит в `~/.claude/templates/.credentials.master.env.example`.
Там ключи для отдельных скиллов (генерация изображений, озвучка, публикации в соцсети,
внешние API) с пометками «где взять» и «что сломается без неё». Ни один не нужен для
запуска: скилл, которому не хватает ключа, скажет об этом сам и не сломает остальное.

Установщик копирует этот же файл в `~/.claude/.credentials.master.env` — но только если
такого файла ещё нет; существующий не трогает никогда. Раскомментируй в нём те строки,
которые тебе действительно нужны.
