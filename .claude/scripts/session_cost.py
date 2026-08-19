#!/usr/bin/env python3
"""Сколько стоит одна сессия Claude Code: процессы, память, кто именно.

Мерка одна и та же до и после правок — иначе сравнение ничего не значит.
Считать надо вместе с `conhost`: он рождается на каждый `cmd`, и без него
цифра занижается почти вдвое (было 19,6 вместо 28,2).

    python session_cost.py            # замер сейчас
    python session_cost.py --save     # запомнить как точку отсчёта
    python session_cost.py --compare  # сравнить с точкой отсчёта
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

BASE = pathlib.Path.home() / ".claude" / "cache" / "session-cost-baseline.json"

# Как опознать сервер по командной строке. Порядок важен: playwright-live должен
# проверяться раньше playwright, иначе всё сольётся в одну кучу.
MARKS = [
    ("playwright-live", "playwright-live"),
    ("chrome-devtools", "chrome-devtools"),
    ("playwright", "playwright"),
    ("pdf", "pdf-viewer"),
    ("context7", "context7"),
    ("telegram", "telegram"),
    ("codex", "codex"),
    ("filesystem", "filesystem"),
    ("graph|memory", "graph-memory"),
    ("npx|npm-cli", "обёртка npx"),
]


def measure() -> dict:
    try:
        import psutil
    except ImportError:
        raise SystemExit("нужен psutil: pip install psutil")

    import re
    sessions, procs = [], []
    for p in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
        try:
            n = (p.info["name"] or "").lower()
            if n.startswith("claude"):
                sessions.append(p)
            elif n in ("node.exe", "bun.exe", "cmd.exe", "conhost.exe", "node", "bun"):
                procs.append(p)
        except Exception:
            pass

    def rss(p):
        try:
            return p.info["memory_info"].rss if p.info["memory_info"] else 0
        except Exception:
            return 0

    kinds, kmem = collections.Counter(), collections.Counter()
    for p in procs:
        try:
            cl = " ".join(p.info["cmdline"] or [])
        except Exception:
            cl = ""
        tag = "прочее"
        for pat, name in MARKS:
            if re.search(pat, cl, re.I):
                tag = name
                break
        kinds[tag] += 1
        kmem[tag] += rss(p)

    ns = len(sessions) or 1
    return {
        "sessions": len(sessions),
        "procs": len(procs),
        "procs_per_session": round(len(procs) / ns, 1),
        "mem_gb": round((sum(rss(p) for p in procs) + sum(rss(p) for p in sessions)) / 1024**3, 2),
        "mem_per_session_gb": round(
            (sum(rss(p) for p in procs) + sum(rss(p) for p in sessions)) / 1024**3 / ns, 2),
        "by_kind": {k: [kinds[k], round(kmem[k] / 1024**2)] for k in kinds},
    }


def show(d: dict, title: str) -> None:
    print(f"  {title}")
    print(f"    сессий:              {d['sessions']}")
    print(f"    процессов всего:     {d['procs']}   на сессию: {d['procs_per_session']}")
    print(f"    памяти:              {d['mem_gb']} ГБ   на сессию: {d['mem_per_session_gb']} ГБ")
    print("    по серверам (шт / МБ):")
    for k, (c, m) in sorted(d["by_kind"].items(), key=lambda x: -x[1][1])[:10]:
        print(f"      {k:20} {c:4} {m:7}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--save", action="store_true", help="запомнить как точку отсчёта")
    ap.add_argument("--compare", action="store_true", help="сравнить с точкой отсчёта")
    a = ap.parse_args()

    now = measure()

    if a.save:
        BASE.parent.mkdir(parents=True, exist_ok=True)
        BASE.write_text(json.dumps(now, ensure_ascii=False, indent=1), encoding="utf-8")
        show(now, "запомнено как точка отсчёта:")
        return 0

    if a.compare:
        if not BASE.exists():
            raise SystemExit("точки отсчёта нет — сначала --save")
        was = json.loads(BASE.read_text(encoding="utf-8"))
        show(was, "БЫЛО:")
        print()
        show(now, "СТАЛО:")
        dp = now["procs_per_session"] - was["procs_per_session"]
        dm = now["mem_per_session_gb"] - was["mem_per_session_gb"]
        print(f"\n    разница на сессию: процессов {dp:+.1f}, памяти {dm:+.2f} ГБ")
        return 0

    show(now, "сейчас:")
    return 0


if __name__ == "__main__":
    sys.exit(main())
