#!/usr/bin/env python3
"""Доводка рантайма после установки пака.

Скопировать файлы мало: часть скиллов работает только когда на машине есть браузер
Playwright, зарегистрированы маркетплейсы плагинов и установлены зависимости
dev-browser. Раньше это доделывали руками, теряя те самые полчаса после установки.

Запускается установщиком; можно и вручную:
    python3 ~/.claude/scripts/setup_runtime.py            # доделать
    python3 ~/.claude/scripts/setup_runtime.py --check    # только показать, чего нет

Что проверяется: имена интерпретатора (`python` / `python3` — навыки зовут оба),
внешние программы (git, node/npm, ffmpeg, curl, jq, uv, pnpm, unzip, bun, gh, docker,
yt-dlp, LibreOffice, poppler, whisper, tesseract, ImageMagick, bd, codegraph,
lsof), браузер Playwright, маркетплейсы плагинов, готовность node-проектов и
интерпретатор для MCP-серверов на Python.

Список внешних программ здесь — ЕДИНСТВЕННЫЙ источник для таблицы в PREREQUISITES.md.
Добавляешь строку сюда — добавь и туда, иначе документ снова начнёт обещать проверку,
которой нет (ровно этим он врал до августа 2026).

Идемпотентно: повторный прогон занимает секунды и ничего не ломает.
Код возврата 0 = обязательное на месте; 1 = что-то из обязательного не доехало
(установку это не отменяет). Программы «по потребности» код возврата не меняют, но
всегда печатаются отдельным списком — вместе с тем, что без них отвалится.
Внешние программы скрипт НЕ ставит: называет отсутствующее и команду установки под
твою ОС.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Вывод — только UTF-8, и это не косметика. Скрипт печатает значки ✔ ✓ ✗ …, а на
# русской Windows кодировка вывода по умолчанию cp1251, где таких символов нет.
# Пока вывод идёт в консоль, Python пишет в неё через широкие символы и всё цело; но
# установщик ЗАПУСКАЕТ этот скрипт с перенаправленным выводом — и там кодировка уже
# локальная. Первый же значок валит процесс с UnicodeEncodeError, доводка рантайма
# обрывается на первом шаге, а снаружи это выглядит как «плагины сами не поставились».
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — на экзотическом стриме просто оставляем как есть
        pass

CLAUDE = Path(os.environ.get("CLAUDE_HOME") or (Path.home() / ".claude"))
SETTINGS = CLAUDE / "settings.json"

IS_WINDOWS = os.name == "nt"
CHECK_ONLY = "--check" in sys.argv


# Список конкретных поломок: что именно не поедет и что с этим делать. Печатается
# в конце. Без него итог «часть шагов не прошла» ничего не сообщает: человек видел
# несколько строк с ✗ минуту назад и уже не помнит, каких именно скиллов они касались.
PROBLEMS: list[str] = []


def say(mark: str, text: str) -> None:
    print(f"  {mark} {text}")


def fail(text: str, consequence: str, remedy: str) -> bool:
    """Громкий отказ: строка на месте + запись в итоговый список с последствием и лечением."""
    say("✗", text)
    PROBLEMS.append(f"{text}\n      что не будет работать: {consequence}\n      как починить: {remedy}")
    return False


def run(cmd: list[str], timeout: int = 900, cwd: Path | None = None) -> tuple[bool, str]:
    """Запустить команду, вернуть (успех, короткий вывод). Никогда не бросает."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace",
                           cwd=str(cwd) if cwd else None,
                           shell=IS_WINDOWS)  # на Windows npx/npm — это .cmd
        out = ((p.stdout or "") + (p.stderr or "")).strip()
        return p.returncode == 0, out[-400:]
    except FileNotFoundError:
        return False, "команда не найдена"
    except subprocess.TimeoutExpired:
        return False, f"превышено время ожидания ({timeout} с)"
    except Exception as e:  # noqa: BLE001 — доводка рантайма не должна ронять установку
        return False, str(e)[:200]


def have(binary: str) -> bool:
    return shutil.which(binary) is not None


# --- 0. Внешние программы -----------------------------------------------------------------
# Скрипт обещает «показывает, чего не хватает». Раньше он смотрел четыре вещи из мира
# Node и молчал про ffmpeg, git, LibreOffice, poppler и Bun — а именно они держат
# половину скиллов. Итог «Рантайм готов» человек читал как «можно работать» и упирался
# в отсутствующий ffmpeg посреди рендера, когда связь с установкой уже не видна.
#
# Ставить эти программы за пользователя скрипт не берётся (менеджеры пакетов у всех
# разные, часть требует прав администратора) — но назвать отсутствующее обязан, вместе
# с тем, что именно отвалится, и командой установки под его ОС.
if IS_WINDOWS:
    OS_KEY = "win"
elif sys.platform == "darwin":
    OS_KEY = "mac"
else:
    OS_KEY = "linux"

# Программы, которые на Windows штатно ставятся МИМО PATH: искать только по имени —
# значит ложно объявить их отсутствующими. Значения — шаблоны для glob.
OFF_PATH_HINTS = {
    "soffice": [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ],
    "magick": [
        r"C:\Program Files\ImageMagick*\magick.exe",
    ],
}

# Имена-омонимы: на Windows в system32 лежит СВОЙ `convert.exe` — утилита перевода
# FAT в NTFS, не имеющая к ImageMagick никакого отношения. `shutil.which("convert")`
# находит именно её, и проверка радостно печатала ✓ на машине без ImageMagick —
# ровно тот тихий обман, ради которого этот блок и писался.
IGNORED_ON_WINDOWS = {"convert"}

# required=True → без этого пак не работает как целое, влияет на код возврата.
# required=False → отваливаются конкретные скиллы; печатаем отдельным блоком.
EXTERNAL_TOOLS = [
    {"names": ["git"], "required": True,
     "breaks": "плагины, маркетплейсы, git-скиллы (53 места)",
     "install": {"win": "winget install Git.Git",
                 "mac": "brew install git",
                 "linux": "sudo apt install git"}},
    {"names": ["node"], "required": True,
     "breaks": "браузерная автоматизация, сборки, экспорт (68 мест)",
     "install": {"win": "winget install OpenJS.NodeJS.LTS",
                 "mac": "brew install node",
                 "linux": "sudo apt install nodejs npm"}},
    {"names": ["npm"], "required": True,
     "breaks": "установка node-зависимостей скиллов",
     "install": {"win": "winget install OpenJS.NodeJS.LTS",
                 "mac": "brew install node",
                 "linux": "sudo apt install nodejs npm"}},
    {"names": ["ffmpeg"], "required": False,
     "breaks": "видео и аудио целиком: video-editor, video-montage, deepgram, ace-step, "
               "склейка потоков в yt-dlp (20 навыков)",
     "install": {"win": "winget install Gyan.FFmpeg",
                 "mac": "brew install ffmpeg",
                 "linux": "sudo apt install ffmpeg"}},
    {"names": ["curl"], "required": False,
     "breaks": "примеры обращений к API (43 навыка)",
     "install": {"win": "уже есть в Windows 10+ (проверь PATH)",
                 "mac": "brew install curl",
                 "linux": "sudo apt install curl"}},
    {"names": ["jq"], "required": False,
     "breaks": "github-import (обход дерева репозитория), brand-extractor, notebooklm, "
               "last30days, примеры higgsfield в video-generation",
     "install": {"win": "winget install jqlang.jq",
                 "mac": "brew install jq",
                 "linux": "sudo apt install jq"}},
    {"names": ["uv"], "required": False,
     "breaks": "ace-step, edit-banana, python-fullstack-dev, video-shotcraft; "
               "last30days им же подбирает Python 3.12 (5 навыков)",
     "install": {"win": "winget install astral-sh.uv",
                 "mac": "brew install uv",
                 "linux": "curl -LsSf https://astral.sh/uv/install.sh | sh"}},
    {"names": ["pnpm"], "required": False,
     "breaks": "quality-gates (`pnpm type-check && pnpm build`), health-inline, "
               "run-quality-gate, rollback-changes, web-artifacts-builder (9 единиц)",
     "install": {"win": "npm install -g pnpm",
                 "mac": "npm install -g pnpm",
                 "linux": "npm install -g pnpm"}},
    {"names": ["unzip"], "required": False,
     "breaks": "last30days/build-skill.sh; в document-import уже есть запасной путь через "
               "python-zipfile, там отсутствие unzip не смертельно",
     # На Windows пакета unzip нет ни в системе, ни в Git Bash — зато с Windows 10
     # штатно едет bsdtar, который zip распаковывает.
     "install": {"win": "нет в Windows; тот же результат: tar -xf file.docx -C out",
                 "mac": "уже есть в macOS",
                 "linux": "sudo apt install unzip"}},
    {"names": ["whisper"], "required": False,
     "breaks": "video-montage: субтитры и word-timestamps (CLI, не Python-пакет)",
     "install": {"win": "pip install -U openai-whisper  (нужен ещё ffmpeg)",
                 "mac": "pip install -U openai-whisper  (нужен ещё ffmpeg)",
                 "linux": "pip install -U openai-whisper  (нужен ещё ffmpeg)"}},
    # ImageMagick: 27 «упоминаний» из прежней таблицы были посчитаны словом — в них
    # попал английский глагол convert. Реальных мест ровно два, и они зовут РАЗНЫЕ
    # имена: pwa-shell — `magick` (IM7), web-assets-generator — `convert` (IM6).
    {"names": ["magick", "convert"], "required": False,
     "breaks": "pwa-shell (иконки PWA) и web-assets-generator (фавиконы) — 2 навыка",
     "install": {"win": "winget install ImageMagick.ImageMagick",
                 "mac": "brew install imagemagick",
                 "linux": "sudo apt install imagemagick"}},
    {"names": ["tesseract"], "required": False,
     "breaks": "edit-banana с `ocr.engine: tesseract` (по умолчанию там другой движок)",
     "install": {"win": "winget install UB-Mannheim.TesseractOCR",
                 "mac": "brew install tesseract",
                 "linux": "sudo apt install tesseract-ocr"}},
    {"names": ["bd"], "required": False,
     "breaks": "навык beads (трекер задач для агентов) и команда /beads-init",
     "install": {"win": "npm install -g @beads/bd",
                 "mac": "brew install steveyegge/tap/beads",
                 "linux": "go install github.com/steveyegge/beads/cmd/bd@latest"}},
    {"names": ["codegraph"], "required": False,
     "breaks": "codegraph: граф вызовов, callers/callees/impact",
     "install": {"win": "npm i -g @colbymchenry/codegraph",
                 "mac": "npm i -g @colbymchenry/codegraph",
                 "linux": "npm i -g @colbymchenry/codegraph"}},
    {"names": ["lsof"], "required": False,
     "breaks": "webapp-testing и dev-browser: чистка чужого процесса на занятом порту "
               "(без него порт просто останется занятым, без объяснения)",
     "install": {"win": "в Windows нет; тот же ответ даёт: netstat -ano | findstr :ПОРТ",
                 "mac": "уже есть в macOS",
                 "linux": "sudo apt install lsof"}},
    {"names": ["gh"], "required": False,
     "breaks": "работа с GitHub из скиллов (16 мест)",
     "install": {"win": "winget install GitHub.cli",
                 "mac": "brew install gh",
                 "linux": "https://cli.github.com"}},
    {"names": ["docker"], "required": False,
     "breaks": "локальные сервисы, n8n, сборки (18 мест)",
     "install": {"win": "winget install Docker.DockerDesktop",
                 "mac": "brew install --cask docker",
                 "linux": "https://docs.docker.com/engine/install/"}},
    {"names": ["yt-dlp"], "required": False,
     "breaks": "video-downloader и всё, что качает ролики",
     "install": {"win": "winget install yt-dlp.yt-dlp",
                 "mac": "brew install yt-dlp",
                 "linux": "pipx install yt-dlp"}},
    {"names": ["soffice", "libreoffice"], "required": False,
     "breaks": "конвертация офисных форматов: docx, pptx, export-pptx, video-generation "
               "(`soffice --headless --convert-to pdf`)",
     "install": {"win": "winget install TheDocumentFoundation.LibreOffice",
                 "mac": "brew install --cask libreoffice",
                 "linux": "sudo apt install libreoffice-calc"}},
    {"names": ["pdftotext", "pdftoppm"], "required": False,
     "breaks": "разбор PDF и превью страниц: pdf, document-import, last30days; в "
               "webinar-to-pdf есть запасной путь через PyMuPDF (пакет poppler)",
     "install": {"win": "https://github.com/oschwartz10612/poppler-windows/releases",
                 "mac": "brew install poppler",
                 "linux": "sudo apt install poppler-utils"}},
    {"names": ["bun"], "required": False,
     "breaks": "сборка бинаря gstack (`bun build --compile`, npm этого не умеет)",
     "install": {"win": "powershell -c \"irm bun.sh/install.ps1 | iex\"",
                 "mac": "brew install oven-sh/bun/bun",
                 "linux": "curl -fsSL https://bun.sh/install | bash"}},
    # Здесь НЕТ sqlite3 и pandoc, и это не пропуск. Обход всех файлов пака: бинарь
    # sqlite3 не зовёт ни один скрипт — он встречается только в денилистах хука
    # (пак его блокирует, а не вызывает), а питону нужен stdlib-модуль, идущий с
    # интерпретатором. pandoc не упомянут вообще ни разу. Прежняя таблица требовала
    # ставить обе программы — это чистый расход времени человека на пустом месте.
]

# Отсутствующее «по потребности» — печатается отдельным блоком, код возврата не трогает.
OPTIONAL_MISSING: list[str] = []


def locate_tool(tool: dict) -> str | None:
    """Путь к программе: сперва PATH, затем известные места мимо PATH."""
    import glob

    names = [n for n in tool["names"]
             if not (IS_WINDOWS and n in IGNORED_ON_WINDOWS)]
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for name in names:
        for pattern in OFF_PATH_HINTS.get(name, []):
            for candidate in sorted(glob.glob(pattern), reverse=True):
                if Path(candidate).exists():
                    return candidate
    return None


def ensure_external_tools() -> bool:
    ok_all = True
    for tool in EXTERNAL_TOOLS:
        shown = " / ".join(tool["names"])
        found = locate_tool(tool)
        if found:
            on_path = any(shutil.which(n) == found for n in tool["names"])
            say("✓", f"{shown}" if on_path else f"{shown} (мимо PATH: {found})")
            continue
        fix = tool["install"].get(OS_KEY, "см. PREREQUISITES.md")
        if tool["required"]:
            ok_all = fail(f"нет {shown}", tool["breaks"], fix) and ok_all
        else:
            # Строкой в общем списке — только имя: подробности (что отвалится и как
            # поставить) печатаются отдельным блоком в конце. Иначе полтора десятка
            # трёхстрочных абзацев прокручивают экран, и человек не видит итога.
            say("~", f"нет {shown}")
            OPTIONAL_MISSING.append(f"{shown}\n      что не будет работать: {tool['breaks']}"
                                    f"\n      как поставить: {fix}")
    return ok_all


# --- 0b. Имена интерпретатора -------------------------------------------------------------
# В теле навыков 642 команды вида `python <скрипт>` в 138 файлах, а документация пака
# говорит `python3 …`. Ни одна из двух записей не работает везде:
#   • macOS 12.3+ бинарника `python` не несёт вовсе, Ubuntu 22.04+ — без пакета
#     python-is-python3;
#   • установщик python.org и winget на Windows кладут только `python.exe`; имя
#     `python3` там ведёт в заглушку Microsoft Store, которая открывает магазин
#     вместо запуска.
# Отказ выглядит по-разному («command not found», «Python was not found», открывшийся
# магазин), и ни одна формулировка не подсказывает, что делать. Поэтому проверяем оба
# имени и говорим прямо. Код возврата не трогаем: интерпретатор, которым запущен этот
# скрипт, очевидно работает — вопрос только в том, каким именем его звать.
def ensure_interpreter_names() -> bool:
    names = {n: shutil.which(n) for n in ("python", "python3")}
    missing = [n for n, p in names.items() if not p]
    if not missing:
        say("✓", "python и python3 оба на PATH")
        return True
    have_name = next(n for n, p in names.items() if p)
    if IS_WINDOWS:
        fix = ("это норма для Windows: команды из навыков запускай как "
               f"`{have_name} …`; заглушку Microsoft Store можно убрать в "
               "«Параметры → Приложения → Псевдонимы выполнения приложения»")
    else:
        fix = ('добавь короткое имя: `alias python=python3` в ~/.zshrc или ~/.bashrc; '
               'системно — `sudo apt install python-is-python3` (Debian/Ubuntu) либо '
               '`brew install python` (macOS, положит python3 и python в один префикс)')
    say("~", f"на PATH есть {have_name}, но нет {', '.join(missing)}")
    OPTIONAL_MISSING.append(
        f"имя `{missing[0]}` не найдено (есть `{have_name}`)"
        f"\n      что не будет работать: команды из навыков, записанные этим именем — "
        f"а их в паке 642 в 138 файлах"
        f"\n      как починить: {fix}")
    return True


# --- 1. Браузер Playwright ---------------------------------------------------------------
def playwright_installed() -> bool:
    """Ищем распакованный Chromium в кэше Playwright."""
    if IS_WINDOWS:
        cache = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ms-playwright"
    elif sys.platform == "darwin":
        cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    else:
        cache = Path.home() / ".cache" / "ms-playwright"
    if not cache.is_dir():
        return False
    return any(d.name.startswith("chromium") for d in cache.iterdir() if d.is_dir())


def ensure_playwright() -> bool:
    if playwright_installed():
        say("✓", "браузер Playwright уже на месте")
        return True
    browser_breaks = ("скриншоты, export-png/pdf/pptx, verifier, webapp-testing, "
                      "playwright-automation, brand-extractor")
    if CHECK_ONLY:
        return fail("браузера Playwright нет", browser_breaks,
                    "npx playwright install chromium")
    if not have("npx"):
        return fail("нет npx", browser_breaks,
                    "поставь Node.js (https://nodejs.org), затем: npx playwright install chromium")
    say("…", "ставлю Chromium для Playwright (это самая долгая часть)")
    ok, out = run(["npx", "--yes", "playwright", "install", "chromium"])
    if ok:
        say("✓", "Chromium установлен")
        return True
    return fail(f"Chromium не поставился: {out.splitlines()[-1] if out else 'без вывода'}",
                browser_breaks, "npx playwright install chromium")


# --- 2. Маркетплейсы плагинов ------------------------------------------------------------
def declared_marketplaces() -> dict:
    """Маркетплейсы, на которые ссылается settings.json пака."""
    try:
        s = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for key in ("extraKnownMarketplaces", "marketplaces"):
        block = s.get(key)
        if isinstance(block, dict):
            for name, body in block.items():
                src = (body or {}).get("source") or {}
                url = src.get("url") or src.get("repo") or ""
                if url:
                    out[name] = url
    return out


def ensure_marketplaces() -> bool:
    want = declared_marketplaces()
    if not want:
        say("✓", "маркетплейсы не объявлены — добавлять нечего")
        return True
    if not have("claude"):
        return fail("CLI claude не найден — маркетплейсы не добавлены",
                    "плагины пака (" + ", ".join(want) + ")",
                    "запусти Claude Code хотя бы раз, затем повтори этот скрипт")
    ok_all = True
    listed_ok, listed = run(["claude", "plugin", "marketplace", "list"], timeout=90)
    known = listed if listed_ok else ""
    for name, url in want.items():
        if name in known:
            say("✓", f"маркетплейс {name} уже добавлен")
            continue
        if CHECK_ONLY:
            ok_all = fail(f"маркетплейс {name} не добавлен", f"плагины из {name}",
                          f"claude plugin marketplace add {url}") and ok_all
            continue
        added, out = run(["claude", "plugin", "marketplace", "add", url], timeout=180)
        if added or "already" in out.lower():
            say("✓", f"маркетплейс {name} добавлен")
        else:
            ok_all = fail(f"{name}: {out.splitlines()[-1] if out else 'не добавился'}",
                          f"плагины из {name}",
                          f"claude plugin marketplace add {url}") and ok_all
    return ok_all


# --- 3. Зависимости Node ------------------------------------------------------------------
# Ставим лёгкие и часто нужные. Remotion-проекты (video-shotcraft, remotion-overlays)
# тянут React и рендер-тулчейн на сотни мегабайт — их ставит сам скилл, когда до них
# дойдёт дело, иначе первая установка растянется на десятки минут ради того, чем
# большинство не пользуется.
#
# ВАЖНО про признак готовности. Раньше здесь стояло «есть каталог node_modules → ✓».
# Это неправда для обоих ставящихся проектов, и неправда молча:
#   • dev-browser запускается через `npx tsx scripts/start-server.ts`, а tsx объявлен
#     в devDependencies — при `--omit=dev` его в node_modules нет. Каталог есть,
#     галочка зелёная, а при первом запуске npx лезет за tsx в реестр и спрашивает
#     «Ok to proceed? (y)» в подпроцессе, где отвечать некому;
#   • gstack — не node-проект: его точка входа `browse/dist/browse` компилируется
#     Bun-ом (`bun build --compile`), npm её не собирает и собрать не может. В паке
#     бинаря нет. npm install кладёт node_modules, печаталось «зависимости
#     установлены», а `/gstack browse` упирался в отсутствующий бинарь.
# Поэтому у каждого проекта теперь есть entry — файл, по которому видно, что проект
# реально готов, и говорить ✓ раньше его появления нельзя.
NODE_PROJECTS = [
    {
        "path": CLAUDE / "skills" / "dev-browser",
        "label": "dev-browser",
        "install": True,
        "omit_dev": False,  # tsx — точка входа, а лежит в devDependencies
        "entry": ["node_modules/tsx/package.json"],
        "entry_what": "tsx (им запускается scripts/start-server.ts)",
        "entry_fix": 'npm install --prefix "{path}"   (именно без --omit=dev)',
        "breaks": "dev-browser: браузер с сохранёнными логинами, режим расширения",
    },
    {
        "path": CLAUDE / "skills" / "gstack",
        "label": "gstack",
        "install": True,
        "omit_dev": True,
        "entry": ["browse/dist/browse", "browse/dist/browse.exe"],
        "entry_what": "бинарь browse (собирается Bun-ом, npm его не делает)",
        "entry_fix": 'поставь Bun (https://bun.sh), затем: cd "{path}" && bun install && bun run build',
        "builder": "bun",
        "breaks": "gstack: быстрый headless-браузер и скиллы qa / review / ship / plan-*",
    },
    {
        "path": CLAUDE / "skills" / "video-shotcraft" / "template",
        "label": "video-shotcraft",
        "install": False,
        "omit_dev": True,
        "entry": ["node_modules"],
        "entry_what": "зависимости Remotion",
        "entry_fix": 'npm install --prefix "{path}"',
        "breaks": "video-shotcraft: рендер промо-роликов",
    },
    {
        "path": CLAUDE / "skills" / "video-generation" / "remotion-overlays",
        "label": "remotion-overlays",
        "install": False,
        "omit_dev": True,
        "entry": ["node_modules"],
        "entry_what": "зависимости Remotion",
        "entry_fix": 'npm install --prefix "{path}"',
        "breaks": "remotion-overlays: наложение соц-UI на видео",
    },
]


def entry_present(proj: dict) -> bool:
    """Готов ли проект по-настоящему: существует ли его точка входа."""
    return any((proj["path"] / rel).exists() for rel in proj["entry"])


def build_gstack(path: Path) -> bool:
    """Собрать бинарь browse. Только Bun: `bun build --compile` не имеет замены в npm."""
    if not have("bun"):
        return False
    say("…", "собираю бинарь gstack через Bun (npm этого не умеет)")
    ok, out = run(["bun", "install"], timeout=600, cwd=path)
    if ok:
        ok, out = run(["bun", "run", "build"], timeout=900, cwd=path)
    if not ok:
        say("~", f"bun: {out.splitlines()[-1] if out else 'без вывода'}")
    return ok


def ensure_node_project(proj: dict) -> bool:
    path, label = proj["path"], proj["label"]
    if not (path / "package.json").is_file():
        say("·", f"{label}: не установлен — пропускаю")
        return True

    if entry_present(proj):
        say("✓", f"{label}: готов")
        return True

    fix = proj["entry_fix"].format(path=path)

    if not proj["install"]:
        say("·", f"{label}: не ставлю сейчас (тяжёлый рендер-стек) — "
                 f"поставит сам скилл при первом обращении, либо вручную: {fix}")
        return True

    if CHECK_ONLY:
        return fail(f"{label}: нет — {proj['entry_what']}", proj["breaks"], fix)

    # 1. Зависимости npm (для gstack это ещё не готовность, но playwright оттуда нужен).
    if (path / "node_modules").is_dir():
        say("·", f"{label}: node_modules на месте")
    elif not have("npm"):
        return fail(f"{label}: нет npm", proj["breaks"],
                    f"поставь Node.js (https://nodejs.org), затем: {fix}")
    else:
        say("…", f"ставлю зависимости {label}")
        cmd = ["npm", "install", "--no-audit", "--no-fund", "--prefix", str(path)]
        if proj["omit_dev"]:
            cmd.insert(2, "--omit=dev")
        ok, out = run(cmd, timeout=600)
        if not ok:
            return fail(f"{label}: npm install не прошёл — "
                        f"{out.splitlines()[-1] if out else 'без вывода'}",
                        proj["breaks"], fix)

    # 2. Сборка, если проект компилируемый.
    if proj.get("builder") == "bun":
        build_gstack(path)

    # 3. Проверяем ровно то, ради чего всё затевалось.
    if entry_present(proj):
        say("✓", f"{label}: готов")
        return True
    return fail(f"{label}: зависимости стоят, но {proj['entry_what']} так и не появился",
                proj["breaks"], fix)


def ensure_node() -> bool:
    return all([ensure_node_project(p) for p in NODE_PROJECTS])


# --- 4. Интерпретатор для MCP-серверов на Python ------------------------------------------
# MCP-сервер объявлен как command: "python" — короткое имя, которого в PATH может не быть
# вовсе. На Windows хуже: там это имя штатно ведёт в заглушку Microsoft Store, которая
# вместо запуска открывает магазин и не возвращает управление (пак обходит её отдельно
# в установщике Python — грабли известные). В обоих случаях снаружи это выглядит как
# «MCP просто нет»: запись в настройках есть, инструментов ноль.
#
# Рабочий интерпретатор мы уже держим в руках — тот, которым запущен этот скрипт.
# Прописываем его абсолютным путём. Идемпотентно: если путь уже проставлен, файл не
# трогаем вовсе (лишняя перезапись настроек пользователя — тоже вред).
BARE_PYTHON = {"python", "python3", "python.exe", "python3.exe", "py", "py.exe"}


def ensure_python_mcp() -> bool:
    if not SETTINGS.is_file():
        say("~", "settings.json не найден — нечего настраивать")
        return True
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return fail(f"settings.json не читается ({e})",
                    "MCP-серверы на Python (запись в настройках есть, инструментов ноль)",
                    f"почини JSON в {SETTINGS} и повтори этот скрипт")

    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return True

    targets = [name for name, cfg in servers.items()
               if isinstance(cfg, dict) and str(cfg.get("command", "")).lower() in BARE_PYTHON]
    if not targets:
        return True

    if CHECK_ONLY:
        return fail("MCP на Python объявлены коротким именем: " + ", ".join(targets),
                    "эти MCP-серверы не поднимутся (на Windows короткое `python` ведёт "
                    "в заглушку Microsoft Store)",
                    "python3 ~/.claude/scripts/setup_runtime.py — проставит абсолютный путь")

    for name in targets:
        servers[name]["command"] = sys.executable
    try:
        SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return fail(f"не смог записать settings.json ({e})",
                    "MCP-серверы на Python",
                    f'пропиши вручную в {SETTINGS}: "command": "{sys.executable}"')
    say("✔", f"интерпретатор для MCP ({', '.join(targets)}): {sys.executable}")
    return True


def main() -> int:
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print((__doc__ or "").strip())
        return 0
    if not CLAUDE.is_dir():
        print(f"Каталога {CLAUDE} нет — пак не установлен.")
        return 1
    print("Проверяю рантайм:" if CHECK_ONLY else "Довожу рантайм:")
    results = [ensure_interpreter_names(), ensure_external_tools(), ensure_playwright(),
               ensure_marketplaces(), ensure_node(), ensure_python_mcp()]
    print()

    # Блок «по потребности» печатается ВСЕГДА, в том числе при успехе: иначе
    # «Рантайм готов» читается как «всё есть», и отсутствующий ffmpeg всплывает
    # посреди рендера, когда связь с установкой уже не видна.
    if OPTIONAL_MISSING:
        print("Не найдено — отвалятся отдельные скиллы (ставить по потребности):")
        for i, p in enumerate(OPTIONAL_MISSING, 1):
            print(f"  {i}) {p}")
        print()

    if all(results):
        print("Обязательное на месте."
              + (" Список выше — то, чего не хватает отдельным скиллам."
                 if OPTIONAL_MISSING else " Рантайм готов."))
        return 0

    # Итог называет ровно то, что не поедет, и что с этим сделать. Общая фраза вроде
    # «часть шагов не прошла» приравнивает отсутствующий бинарь к мелочи: человек
    # закрывает окно и упирается в отказ через неделю, уже не связывая его с установкой.
    if PROBLEMS:
        print("НЕ ГОТОВО — по пунктам:")
        for i, p in enumerate(PROBLEMS, 1):
            print(f"  {i}) {p}")
        print()
    print("Остальной пак работает; перечисленные скиллы — нет, пока не починишь.")
    if CHECK_ONLY:
        print("Доделать: python3 ~/.claude/scripts/setup_runtime.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
