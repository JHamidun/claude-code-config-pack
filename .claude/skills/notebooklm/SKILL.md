---
name: notebooklm
description: "Google NotebookLM через библиотеку notebooklm-py: подкасты (2 ведущих), deep research с цитатами, квизы, флешкарты, mind maps из PDF/URL/YouTube. Триггеры: «создай подкаст», «quiz из документов», «mind map из темы», «загрузи в NotebookLM»."
allowed-tools: Bash, Read, Write, WebSearch
---

# NotebookLM — Document Intelligence & Podcast Generator

Обёртка над Python-библиотекой `notebooklm-py`.

## Что понадобится

| Нужно | Платно? | Где взять |
|---|---|---|
| Google-аккаунт | **нет** | NotebookLM бесплатен для личного использования |
| `pip install "notebooklm-py[browser]"` | нет | PyPI; `[browser]` тянет Playwright + ~170 МБ Chromium при первом `login` |
| Один интерактивный вход | нет | `notebooklm login` — открывает браузер, ты логинишься руками |

Ключей API нет и не бывает: библиотека работает через **недокументированные внутренние
эндпоинты Google** и живую сессию браузера. Отсюда два следствия, с которыми придётся жить:
эндпоинты меняются без предупреждения (ниже — таблица переименований команд, которые уже
случились), а сессия протухает посреди долгой генерации.

Сессия лежит в `~/.notebooklm/` и в git не попадает — но при шаринге конфига проверь,
что этой папки нет в архиве: там живые cookie твоего Google-аккаунта.

## When to Use

- "сделай подкаст из [документов]" — audio overview generation
- "deep research из [URL/PDF]" — grounded answers with citations
- "quiz/flashcards из [материала]" — learning materials
- "mind map из [темы]" — visual knowledge graphs
- "загрузи в NotebookLM" — add sources to notebook
- "что говорится в документе о [тема]" — Q&A over documents

## Prerequisites

```bash
pip install "notebooklm-py[browser]"

# First-time auth (one-time, interactive in real terminal):
notebooklm login
# Opens Chromium → user logs into Google → press ENTER → saves to ~/.notebooklm/storage_state.json
```

### CRITICAL: stdin is required for interactive login

The CLI uses `input("Press ENTER")` which **fails in piped/background bash sessions** with
`RuntimeError: lost sys.stdin`. Workarounds:

1. **Real terminal (TTY)** — PowerShell, Terminal.app, любой интерактивный shell — preferred
2. **Headed Playwright auto-detect** (no TTY needed) — see "Headed Login" below

### Auth file structure

- `~/.notebooklm/browser_profile/` — Chromium persistent profile (long-lived Google session, weeks)
- `~/.notebooklm/storage_state.json` — short-lived cookie snapshot used by CLI (~1h TTL)

The CLI reads `storage_state.json` for every command. When it expires, you get:

```
Error: Authentication expired or invalid. Redirected to: https://accounts.google.com/...
```

**Long-running operations** (`artifact wait` for 10+ min, multilang loops) **WILL** hit this.
Solution: refresh tokens between calls — или обновиться до 0.7.x, где есть self-healing
master-token (см. `references/upgrade-v0.7-capabilities.md`).

### Headless refresh (no TTY required)

Если сессия в `browser_profile` ещё жива, обновить `storage_state.json` программно:

```python
# refresh-nb-auth.py
import sys, asyncio
from pathlib import Path
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from playwright.sync_api import sync_playwright

HOME = Path.home() / ".notebooklm"
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(HOME / "browser_profile"),
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--password-store=basic"],
        ignore_default_args=["--enable-automation"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://notebooklm.google.com/", wait_until="load", timeout=30000)
    ctx.storage_state(path=str(HOME / "storage_state.json"))
    ctx.close()
```

Запускать перед каждой командой CLI в длинном цикле. Если и профиль протух, скрипт вернёт
URL вида `accounts.google.com/signin/...` и сохранит неполный state — тогда нужен реальный
логин (следующий раздел).

### Headed Login with auto-detect (no manual ENTER)

Когда `browser_profile` протух и нужен новый вход, а терминал не интерактивный.
Скрипт открывает окно, ждёт, пока человек прокликает логин Google, и сам ловит момент.

```python
# login-nb.py
import sys, time, asyncio
from pathlib import Path
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from playwright.sync_api import sync_playwright

HOME = Path.home() / ".notebooklm"
HOME.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(HOME / "browser_profile"),
        headless=False,                      # окно нужно человеку
        args=["--disable-blink-features=AutomationControlled", "--password-store=basic"],
        ignore_default_args=["--enable-automation"],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://notebooklm.google.com/", wait_until="load", timeout=60000)

    deadline = time.monotonic() + 240        # 4-минутное окно на вход
    ok = False
    while time.monotonic() < deadline:
        url = page.url
        if "notebooklm.google.com" in url and "signin" not in url:
            if "SID" in [c["name"] for c in ctx.cookies()]:
                time.sleep(3)                # дать досесться ленивым XHR
                ctx.storage_state(path=str(HOME / "storage_state.json"))
                ok = True
                break
        time.sleep(2)
    ctx.close()

sys.exit(0 if ok else 1)
```

Человек просто проходит логин в открывшемся окне — взаимодействия с терминалом не требуется.
Проверка cookie `SID` обязательна: страница успевает отрисоваться раньше, чем сессия
становится валидной, и без неё сохранится пустой state.

### Windows-specific: Unicode + path issues

```bash
# Always set this for any notebooklm CLI call
export PYTHONIOENCODING=utf-8

# Without it: 'charmap' codec can't encode '✓' / 'Русский' → Unicode crash on Windows console
```

```bash
# Node.js on Windows can't open POSIX paths like /tmp/...
# Use TMPDIR or convert with cygpath -m before passing to node:
TMPDIR_WIN="${TMPDIR:-${TEMP:-$HOME/AppData/Local/Temp}}"
SRC_PATH_NODE=$(cygpath -m "$SRC_PATH" 2>/dev/null || echo "$SRC_PATH")
node -e "fs.readFileSync('$SRC_PATH_NODE')"
```

## Input Validation (MANDATORY)

Before passing ANY user input to NotebookLM, validate:

```python
import re

def validate_input(text: str) -> str:
    """Sanitize input before sending to NotebookLM API."""
    # Block prompt injection patterns
    INJECTION_PATTERNS = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'disregard\s+(all\s+)?previous',
        r'override\s+(system|previous)',
        r'you\s+are\s+now\s+',
        r'pretend\s+(?:you|to\s+be)',
        r'</?(?:system|assistant|human)>',
        r'\[SYSTEM\]',
        r'\[INST\]',
    ]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Blocked: potential injection pattern detected")

    # Limit length (NotebookLM has own limits, but defense-in-depth)
    if len(text) > 10000:
        text = text[:10000]

    return text.strip()

def validate_url(url: str) -> str:
    """Validate URL before adding as source."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
    # Block local/private URLs
    if parsed.hostname in ('localhost', '127.0.0.1', '0.0.0.0'):
        raise ValueError("Local URLs not allowed")
    if parsed.hostname and parsed.hostname.startswith('192.168.'):
        raise ValueError("Private network URLs not allowed")
    return url
```

## CLI Operations

### Create notebook and add sources

```bash
# Create a new notebook
notebooklm create "Research: AI Agents 2026"

# Add sources — сигнатура `source add [OPTIONS] CONTENT`, тип определяется сам
notebooklm source add "https://example.com/article" -n NOTEBOOK_ID
notebooklm source add "/path/to/document.pdf" -n NOTEBOOK_ID --type file
notebooklm source add "https://youtube.com/watch?v=VIDEO_ID" -n NOTEBOOK_ID --type youtube
```

> Группы `notebook` в CLI 0.3.4 НЕТ (`create` — команда верхнего уровня), а у `source add`
> нет ни `--notebook-id`, ни `--url`/`--file`: только `-n/--notebook`, `--type [url|text|file|youtube]`,
> `--title`, `--mime-type`. Заглавный токен `URL`/`PDF`/`YOUTUBE` уйдёт в CONTENT и создаст
> текстовый источник со словом «URL» внутри.

### Query notebook (grounded answers)

```bash
# Группы `chat` в CLI нет — `ask` это команда верхнего уровня
notebooklm ask "What are the key findings about AI agents?" -n NOTEBOOK_ID
```

### Generate studio artifacts

Структура CLI менялась; ниже — команды, проверенные на 0.3.4:

```bash
# Audio podcast — preferred for content discussion
notebooklm generate audio --json -n NB_ID --format deep-dive --length long "Description guides hosts"

# Format options:
#   deep-dive  — TWO conversational hosts (recommended for podcasts)
#   brief      — single-host short summary (1-3 min)
#   critique   — analytical breakdown
#   debate     — opposing viewpoints

# Length options:
#   short    — ~1-3 min (truncates aggressively)
#   default  — ~3-7 min
#   long     — ~10-25 min (use for substantial content)

# Returns task_id in JSON. Use --json to parse.

# Other artifact types
notebooklm generate report -n NB_ID
notebooklm generate slide-deck -n NB_ID
notebooklm generate mind-map -n NB_ID
notebooklm generate quiz -n NB_ID
notebooklm generate flashcards -n NB_ID
notebooklm generate infographic -n NB_ID
notebooklm generate data-table -n NB_ID
notebooklm generate cinematic-video -n NB_ID
notebooklm generate video -n NB_ID
```

### Wait for completion + download

```bash
# Block until ready (CRITICAL for scripts — generation takes 5-25 min)
notebooklm artifact wait TASK_ID -n NB_ID --timeout 900 --interval 15 --json

# Status check (no wait, returns current state)
notebooklm artifact poll TASK_ID -n NB_ID

# Download — uses notebook context, picks latest of given type
notebooklm download audio /path/to/output.mp3 -n NB_ID
notebooklm download mind-map /path/to/output.png -n NB_ID

# IMPORTANT: --output is positional in new CLI. Pass full path as ARG, not flag.
```

### CLI command renames (old docs → current)

Эти переименования — прямое следствие того, что API недокументированный. Если команда из
чужой инструкции не находится, сверься с таблицей и с `notebooklm <group> --help`.

| Old | New |
|-----|-----|
| `notebooklm notebook create "T"` | `notebooklm create "T"` |
| `notebooklm studio generate ID audio_overview` | `notebooklm generate audio -n ID` |
| `notebooklm studio download ID audio_overview --output P` | `notebooklm download audio P -n ID` |
| `notebooklm studio status ID audio_overview` | `notebooklm artifact poll TASK_ID -n ID` |
| `notebooklm source add ID --file P --type text` | `notebooklm source add P -n ID --type text --title T` |

## Python API (for advanced workflows)

```python
import asyncio
from notebooklm import NotebookLMClient

async def research_and_podcast(topic, urls):
    async with await NotebookLMClient.from_storage() as client:
        # Create notebook
        nb = await client.notebooks.create(f"Research: {topic}")

        # Add sources
        for url in urls:
            validated_url = validate_url(url)  # ALWAYS validate
            await client.sources.add_url(nb.id, validated_url)

        # Ask questions
        question = validate_input(f"Summarize key insights about {topic}")
        answer = await client.chat.ask(nb.id, question)
        print(answer.text)

        # Generate podcast — атрибута `client.studio` НЕТ; артефакты живут в client.artifacts,
        # и обобщённых generate/download там тоже нет, только по типам
        status = await client.artifacts.generate_audio(nb.id, audio_format="deep-dive",
                                                       audio_length="long")
        await client.artifacts.wait_for_completion(nb.id, status.task_id, timeout=1800)

        # Download — output_path позиционный, каталога не хватит, нужен полный путь к файлу
        await client.artifacts.download_audio(nb.id, "~/Documents/NotebookLM/podcast.mp3")

asyncio.run(research_and_podcast("AI Agents", [
    "https://arxiv.org/abs/2405.12345",
    "https://example.com/agent-patterns"
]))
```

## Language management

Output language is a **GLOBAL account-level setting**, NOT per-notebook:

```bash
notebooklm language list      # show all 30+ supported codes
notebooklm language get       # current default
notebooklm language set ru    # set default

# Codes that need region suffix:
#   pt_BR — Portuguese Brazilian
#   pt_PT — Portuguese Portugal
#   ar_001 — Modern Standard Arabic
#   ar_eg — Egyptian Arabic
#   es_419 — Latin American Spanish
#   fr_CA — Canadian French
#   zh_Hans — Simplified Chinese
#   zh_Hant — Traditional Chinese
```

**For multilang generation**: switch language → generate → wait → download → switch next.
Generations themselves take 5-25 min, language switch is instant.

```bash
# Multilang loop pattern
for lang_full in ru en es pt_BR fr ar_001; do
    notebooklm language set "$lang_full"
    notebooklm generate audio --json -n "$NB_ID" --format deep-dive --length long "Cover all sources" \
        | jq -r '.task_id' > /tmp/last_task.txt
    notebooklm artifact wait "$(cat /tmp/last_task.txt)" -n "$NB_ID" --timeout 1800 --interval 20 --json
    notebooklm download audio "/tmp/podcast-$lang_full.mp3" -n "$NB_ID"
done
```

Такой цикл — самый частый способ упереться в истечение сессии: шесть языков по 10-25 минут
это два-три часа. Ставь `refresh-nb-auth.py` перед каждой итерацией или обновись до 0.7.x.

## Content quality matters: titles ≠ podcast material

**Проверено на практике:** ведущие обсуждают только то, что ЕСТЬ в источнике. Дашь им
заголовки и превью по 150 символов — они двенадцать минут будут рассуждать вокруг названия
темы без единой конкретики. На слух это ровно тот случай, когда сразу понятно, что говорит
машина, и слушать нечего.

**Плохо** (ведущим не за что зацепиться):

```markdown
## OpenAI Codex
_Source: TechCrunch_
OpenAI released a new Codex guide.
```

**Хорошо** (у ведущих есть материал):

```markdown
## Новость 1: OpenAI выпустила руководство по Codex
_Источник: TechCrunch_

**Краткая суть:** OpenAI опубликовала практический гид по настройке workspace, проектов и потоков задач для разработчиков.

[FULL 500-800 word article body with names, numbers, quotes, product details]
```

Всегда клади в источник полный текст, а не только заголовки и метаданные. Для содержательного
обсуждения на 10-15 минут ноутбуку нужно **30-100 КБ реального контента**.

## Format & length to runtime mapping (empirical)

| Format | Length | Hosts | Typical runtime | Use case |
|--------|--------|-------|-----------------|----------|
| `brief` | `short` | 1 | 1-3 min | Quick TLDR |
| `brief` | `default` | 1 | 3-5 min | Single article scan |
| `deep-dive` | `default` | 2 | 5-10 min | Single article discussion |
| `deep-dive` | `long` | 2 | 10-25 min | Daily digest, multi-source |
| `debate` | any | 2 | varies | Pros/cons takes |
| `critique` | any | 1 | varies | Analytical breakdown |

**Note**: NotebookLM игнорирует подсказку длины, если контента мало. Замеры: источник на
591 слово с `--length long` дал ~22 минуты (ведущие растягивали), источник на 44 КБ с теми же
флагами — 14 минут (плотнее, меньше воды).

## Workflow: Document → Podcast Pipeline

1. **Collect sources:** URLs, PDFs, YouTube videos about topic
2. **Validate inputs:** All URLs through `validate_url()`, all text through `validate_input()`
3. **Create notebook:** `notebooklm create "Topic Name"`
4. **Add sources:** `notebooklm source add "<url|path|text>" -n NB_ID` for each source
5. **Generate podcast:** `notebooklm generate audio --json -n NB_ID --format deep-dive --length long`
6. **Download MP3:** `notebooklm artifact wait TASK_ID -n NB_ID --timeout 1800` → `notebooklm download audio /path/out.mp3 -n NB_ID`
7. **Save the summary** рядом с MP3 в свою базу заметок

## Workflow: интеграция со своей базой заметок

Пример на markdown-хранилище (Obsidian, Logseq, просто папка с `.md`). Подставь свой путь.

```bash
NOTES=~/notes            # твоя база заметок

# 1. Создать ноутбук
notebooklm create "From notes: Topic"

# 2. Добавить заметку как текстовый источник (CLI умеет: путь к .md уедет как text)
notebooklm source add "$NOTES/research/topic.md" -n NOTEBOOK_ID --type text --title "Topic"

# 3. Сгенерировать артефакт
notebooklm generate mind-map -n NOTEBOOK_ID

# 4. Забрать результат обратно — путь ПОЗИЦИОННЫЙ и должен быть файлом, не каталогом
notebooklm download mind-map "$NOTES/research/topic-mindmap.png" -n NOTEBOOK_ID
```

## Автоматизация по расписанию

Генерация идёт 5-25 минут и переживает истечение сессии плохо — поэтому в cron/планировщике
всегда ставь обновление токена перед вызовом и `--timeout 1800`, а не короткий.

Гоча Windows Task Scheduler, которая стоит отдельного упоминания: `RepetitionDuration`
обязан быть ограничен. `[TimeSpan]::MaxValue` даёт XML-ошибку `P99999999DT23H59M59S`
и задача не регистрируется. Используй `New-TimeSpan -Days 365`.

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Program Files\Git\bin\bash.exe" `
    -Argument "-c 'export PYTHONIOENCODING=utf-8; bash ~/bin/my-podcast.sh >> /tmp/podcast-cron.log 2>&1'"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Hours 12) `
    -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledTask -TaskName "NotebookLMPodcast" -Action $action -Trigger $trigger
```

## Output Directory

Default: `~/Documents/NotebookLM/`. На Windows CLI переводит POSIX-пути (`/tmp/...`) в
`C:\tmp\` через `cygpath -m` — если ждёшь файл не там, где он появился, дело в этом.

## Credit/Usage Notes

- Google NotebookLM is **free** for personal use — платного ключа нет
- Unofficial API — may break with Google updates
- Rate limits apply (undocumented, typically ~50 requests/hour); multilang-циклы идут близко к границе
- Large documents may take time to process
- Audio podcasts take 5-25 minutes to generate (`--length long` — ближе к верхней границе; ставь `--timeout 1800`, а не короткий)

## Integration Chain

| Next Step | Skill |
|-----------|-------|
| Research trending topics first | `last30days` |
| Transcribe podcast audio | `deepgram` |
| Translate content | `deepl-pro` |
| Create social post from research | `tg-post`, `content-creation` |

## Safety

- All inputs validated through `validate_input()` and `validate_url()` before API calls
- No private/local URLs allowed as sources
- Prompt injection patterns blocked before transmission
- Session credentials stored locally in `~/.notebooklm/` — **не класть в git и не отдавать
  вместе с конфигом**: это живые cookie твоего Google-аккаунта
- Аккаунт используется обычный личный — библиотека не умеет иначе. Если это неприемлемо,
  заведи отдельный Google-аккаунт под NotebookLM

## Дальше

`references/upgrade-v0.7-capabilities.md` — что даёт версия 0.7.x (self-healing master-token
вместо Playwright-костылей + встроенный MCP-сервер) и чек-лист безопасного апгрейда.
