#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-mcp-links.py — проверить, что объявленные MCP-серверы реально запускаемы.

ЗАЧЕМ. На чистой машине ученика конфиг «успешно установился», но MCP-серверов не было
ни одного. Часть записей ссылалась на файлы, которых в паке нет и быть не может:
личная база ~/.brain, устаревший FalkorDB-сервер, каталоги ~/.claude/mcps/... с чужими
виртуальными окружениями. Такие записи не ломают установку — они просто молчат, и
человек видит «MCP просто нет», не понимая почему.

Здесь каждая запись проверяется по факту: раскрываем ${HOME}/.claude в каталог пака и
смотрим, существует ли файл. Пути, которые программа создаёт сама (профиль браузера,
каталог вывода), не проверяются — их и не должно быть до первого запуска.

Запуск:  python tools/check-mcp-links.py [--json]
"""
from __future__ import annotations

import json
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE = os.path.join(ROOT, ".claude")
SETTINGS = os.path.join(CLAUDE, "settings.json")

# Аргумент после такого флага — это то, что создаётся при запуске, а не то, что должно
# лежать в паке.
CREATED_BY_FLAG = re.compile(r"^--(user-data-dir|output|out|profile|storage|cache|data-dir)$", re.I)
HOME_CLAUDE = re.compile(r"^\$\{HOME\}[\\/]\.claude[\\/]", re.I)
HOME_OTHER = re.compile(r"^\$\{HOME\}[\\/](?!\.claude)", re.I)
# Абсолютный путь к каталогу КОНКРЕТНОЙ машины: у другого человека такой записи нет.
# Проверяем по форме пути, а не по чьему-то имени и не по списку известных каталогов, —
# иначе проверка работала бы только у одного автора и молчала бы у всех остальных.
# Любая буква диска в начале и любой /Users//home/ — это машина, а не пак.
HARDCODED = re.compile(r"^[A-Za-z]:[\\/]|^/(Users|home)/", re.I)


def check() -> list:
    data = json.load(io.open(SETTINGS, encoding="utf-8"))
    out = []
    for name, cfg in (data.get("mcpServers") or {}).items():
        if not isinstance(cfg, dict):
            continue
        raw = [cfg.get("command", "")] + [a for a in (cfg.get("args") or []) if isinstance(a, str)]
        args = [a for i, a in enumerate(raw)
                if not (i > 0 and CREATED_BY_FLAG.match(raw[i - 1] or ""))]
        blob = json.dumps(cfg, ensure_ascii=False)

        problem = None
        if HARDCODED.search(blob):
            problem = "жёстко прописан путь машины автора"
        else:
            for a in args:
                if HOME_CLAUDE.match(a):
                    rel = HOME_CLAUDE.sub("", a).replace("/", os.sep).replace("\\", os.sep)
                    if not os.path.exists(os.path.join(CLAUDE, rel)):
                        problem = f"нет файла в паке: {rel}"
                        break
                elif HOME_OTHER.match(a):
                    problem = f"ведёт вне пака: {a}"
                    break
        out.append({
            "name": name,
            "disabled": bool(cfg.get("disabled")),
            "problem": problem,
        })
    return out


def main() -> int:
    rows = check()
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    bad = [r for r in rows if r["problem"]]
    good = [r for r in rows if not r["problem"]]
    print(f"  MCP объявлено: {len(rows)}, запускаемых: {len(good)}, с битой ссылкой: {len(bad)}")
    for r in bad:
        mark = "отключён" if r["disabled"] else "ВКЛЮЧЁН"
        print(f"    ✗ {r['name']:<16} [{mark}] {r['problem']}")
    for r in good:
        if not r["disabled"]:
            print(f"    ✓ {r['name']:<16} [активен]")
    return 1 if any(r["problem"] and not r["disabled"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
