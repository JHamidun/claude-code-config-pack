#!/usr/bin/env python3
"""Доводка рантайма после установки пака.

Скопировать файлы мало: часть скиллов работает только когда на машине есть браузер
Playwright, зарегистрированы маркетплейсы плагинов и установлены зависимости
dev-browser. Раньше это доделывали руками, теряя те самые полчаса после установки.

Запускается установщиком; можно и вручную:
    python3 ~/.claude/scripts/setup_runtime.py            # доделать
    python3 ~/.claude/scripts/setup_runtime.py --check    # только показать, чего нет

Идемпотентно: повторный прогон занимает секунды и ничего не ломает.
Код возврата 0 = всё на месте; 1 = что-то не доехало (установку это не отменяет).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CLAUDE = Path(os.environ.get("CLAUDE_HOME") or (Path.home() / ".claude"))
SETTINGS = CLAUDE / "settings.json"
DEV_BROWSER = CLAUDE / "skills" / "dev-browser"

IS_WINDOWS = os.name == "nt"
CHECK_ONLY = "--check" in sys.argv


def say(mark: str, text: str) -> None:
    print(f"  {mark} {text}")


def run(cmd: list[str], timeout: int = 900) -> tuple[bool, str]:
    """Запустить команду, вернуть (успех, короткий вывод). Никогда не бросает."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace",
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
    if CHECK_ONLY:
        say("✗", "браузера Playwright нет (от него зависят скриншоты, экспорт и деки)")
        return False
    if not have("npx"):
        say("✗", "нет npx — поставь Node.js, затем: npx playwright install chromium")
        return False
    say("…", "ставлю Chromium для Playwright (это самая долгая часть)")
    ok, out = run(["npx", "--yes", "playwright", "install", "chromium"])
    if ok:
        say("✓", "Chromium установлен")
    else:
        say("✗", f"не поставился: {out.splitlines()[-1] if out else 'без вывода'}")
    return ok


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
        say("✗", "CLI claude не найден — плагины подтянутся при первом запуске Claude Code")
        return False
    ok_all = True
    listed_ok, listed = run(["claude", "plugin", "marketplace", "list"], timeout=90)
    known = listed if listed_ok else ""
    for name, url in want.items():
        if name in known:
            say("✓", f"маркетплейс {name} уже добавлен")
            continue
        if CHECK_ONLY:
            say("✗", f"маркетплейс {name} не добавлен")
            ok_all = False
            continue
        added, out = run(["claude", "plugin", "marketplace", "add", url], timeout=180)
        if added or "already" in out.lower():
            say("✓", f"маркетплейс {name} добавлен")
        else:
            say("✗", f"{name}: {out.splitlines()[-1] if out else 'не добавился'}")
            ok_all = False
    return ok_all


# --- 3. Зависимости dev-browser ----------------------------------------------------------
def ensure_dev_browser() -> bool:
    pkg = DEV_BROWSER / "package.json"
    if not pkg.is_file():
        say("·", "скилл dev-browser не установлен — пропускаю")
        return True
    if (DEV_BROWSER / "node_modules").is_dir():
        say("✓", "зависимости dev-browser на месте")
        return True
    if CHECK_ONLY:
        say("✗", "нет node_modules у dev-browser (иначе он ставит их прямо во время работы)")
        return False
    if not have("npm"):
        say("✗", "нет npm — поставь Node.js, затем npm install в skills/dev-browser")
        return False
    say("…", "ставлю зависимости dev-browser")
    ok, out = run(["npm", "install", "--omit=dev", "--no-audit", "--no-fund",
                   "--prefix", str(DEV_BROWSER)], timeout=600)
    if ok:
        say("✓", "зависимости dev-browser установлены")
    else:
        say("✗", f"не установились: {out.splitlines()[-1] if out else 'без вывода'}")
    return ok


def main() -> int:
    if not CLAUDE.is_dir():
        print(f"Каталога {CLAUDE} нет — пак не установлен.")
        return 1
    print("Проверяю рантайм:" if CHECK_ONLY else "Довожу рантайм:")
    results = [ensure_playwright(), ensure_marketplaces(), ensure_dev_browser()]
    print()
    if all(results):
        print("Рантайм готов.")
        return 0
    if CHECK_ONLY:
        print("Чего-то не хватает. Доделать: python3 ~/.claude/scripts/setup_runtime.py")
    else:
        print("Часть шагов не прошла — на работу пака это не влияет, "
              "затронуты только соответствующие скиллы.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
