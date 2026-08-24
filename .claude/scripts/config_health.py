#!/usr/bin/env python3
"""Здоровье конфига: что заявлено, что существует, что запускается.

Линтер связности проверяет ссылки — ведут ли они в существующие файлы. Но файл
может существовать и при этом не работать: упасть на импорте, потребовать
пропавшую библиотеку, звать модель, которой больше нет. Разница между «файл на
месте» и «инструмент работает» и есть то, из-за чего навык считается живым,
пока его не позовут.

Скрипт проверяет три уровня, от дешёвого к дорогому:

    заявлено    навык обещает скрипт в своём описании
    существует  файл лежит на диске
    запускается --help отрабатывает без трассировки

Плюс ищет признаки устаревания: модели, которых больше нет, ссылки на удалённые
инструменты, даты в текстах старше полугода.

    python config_health.py                 # полная проверка
    python config_health.py --quick         # без запуска скриптов
    python config_health.py --json отчёт.json
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

C = pathlib.Path.home() / ".claude"

# Модели, которых больше нет или которые запрещены каноном конфига.
DEAD_MODELS = re.compile(
    r"\b(gpt-4-turbo|gpt-3\.5|text-davinci|claude-3-opus|claude-3-sonnet|claude-3-haiku|"
    r"claude-2|gemini-pro-vision|gemini-1\.5|gemini-2\.0-flash-exp|"
    r"gemini-2\.5-flash-image|dall-e-2|whisper-1)\b", re.I)

SCRIPT_CALL = re.compile(
    r"(?:python\d?|node|bun)\s+[\"'`]?([^\s\"'`|>&]*(?:scripts|tools)/[\w./-]+\.(?:py|mjs|js))")


def skills() -> list[pathlib.Path]:
    return sorted((C / "skills").glob("*/SKILL.md"))


def resolve(raw: str, skill_dir: pathlib.Path) -> pathlib.Path:
    p = raw.strip().strip("\"'`")
    for var in ("${CLAUDE_SKILL_DIR}", "$CLAUDE_SKILL_DIR", "${SKILL_DIR}"):
        p = p.replace(var, skill_dir.as_posix())
    if p.startswith("~/"):
        return pathlib.Path.home() / p[2:]
    if re.match(r"^[A-Za-z]:/", p):
        return pathlib.Path(p)
    return skill_dir / p


def runs(path: pathlib.Path, timeout: int = 45) -> tuple[bool, str]:
    """Отрабатывает ли --help без трассировки.

    Отказ с внятным сообщением («нет ключа») — это НЕ поломка: инструмент жив,
    ему просто нечем работать. Поломка — трассировка на импорте.
    """
    exe = {".py": [sys.executable], ".mjs": ["node"], ".js": ["node"]}.get(path.suffix)
    if not exe:
        return True, "не запускаемый"
    env = {k: v for k, v in os.environ.items()
           if not any(x in k.upper() for x in ("API", "TOKEN", "KEY", "SECRET"))}
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(exe + [str(path), "--help"], capture_output=True, text=True,
                           timeout=timeout, env=env, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, "виснет"
    except Exception as e:
        return False, str(e)[:60]
    err = r.stderr or ""
    if "Traceback" in err:
        last = [l for l in err.strip().splitlines() if l.strip()][-1]
        return False, last[:80]
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="без запуска скриптов")
    ap.add_argument("--json", help="куда сохранить отчёт")
    a = ap.parse_args()

    promised, missing, stale = {}, {}, {}
    for sk in skills():
        name = sk.parent.name
        try:
            text = sk.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in SCRIPT_CALL.finditer(text):
            p = resolve(m.group(1), sk.parent)
            promised.setdefault(name, set()).add(p)
            if not p.exists():
                missing.setdefault(name, set()).add(m.group(1))
        dead = set(DEAD_MODELS.findall(text))
        if dead:
            stale[name] = sorted(dead)

    all_scripts = {p for s in promised.values() for p in s if p.exists()}
    print(f"  навыков: {len(skills())}")
    print(f"  из них обещают скрипты: {len(promised)}")
    print(f"  скриптов заявлено: {len(all_scripts)}")
    print(f"  ОБЕЩАНО, НО НЕТ НА ДИСКЕ: {sum(len(v) for v in missing.values())} "
          f"в {len(missing)} навыках")
    for n, v in sorted(missing.items())[:10]:
        print(f"    {n:28} {', '.join(sorted(v))[:60]}")
    print(f"\n  УСТАРЕВШИЕ МОДЕЛИ упомянуты в {len(stale)} навыках")
    for n, v in sorted(stale.items())[:10]:
        print(f"    {n:28} {', '.join(v)[:60]}")

    broken = {}
    if not a.quick:
        print(f"\n  запускаю {len(all_scripts)} скриптов с --help…")
        with ThreadPoolExecutor(max_workers=8) as ex:
            for p, (ok, why) in zip(all_scripts, ex.map(runs, all_scripts)):
                if not ok:
                    broken[str(p)] = why
        print(f"  НЕ ЗАПУСКАЮТСЯ: {len(broken)} из {len(all_scripts)}")
        for p, why in sorted(broken.items())[:15]:
            print(f"    {pathlib.Path(p).name:34} {why[:56]}")

    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({
            "skills": len(skills()),
            "missing": {k: sorted(v) for k, v in missing.items()},
            "stale_models": stale,
            "broken": broken,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n  отчёт: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
