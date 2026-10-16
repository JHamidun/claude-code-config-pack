#!/usr/bin/env python3
"""Прочитать сессию Claude Code в ПРАВИЛЬНОМ хронологическом порядке.

Зачем. Записи в .jsonl штампуются в момент начала события, а пишутся по его
завершении. Сообщение, отправленное в середине хода, получает запись мгновенно,
поэтому уже начатый блок ассистента ложится ПОСЛЕ него со штампом более ранним.
Замер на 25 транскриптах: 99 738 обратных скачков времени из 839 644 записей;
у сводок Stop-хука — 87,6 %, у переключений модели — 96,7 %.

Для чтения глазами это косметика. Опасно другое: после автосжатия транскрипт
читаю я сам, чтобы восстановить контекст, — и порядок строк может подсунуть
раннюю реплику как позднюю.

Использование:
    transcript_read.py <сессия|путь>              последние 40 сообщений
    transcript_read.py <сессия> --all             целиком
    transcript_read.py <сессия> --grep "текст"    только совпадения с контекстом
    transcript_read.py <сессия> --raw-order       как в файле, чтобы увидеть сдвиг
    transcript_read.py --list                     какие сессии есть
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
# Служебное: не несёт содержимого разговора, только шумит при чтении.
NOISE = {
    "queue-operation", "file-history-snapshot", "file-history-delta",
    "last-prompt", "ai-title", "atis-latch", "permission-mode",
    "isolation-latch", "worktree-state", "attribution-snapshot",
}


def find_session(token: str) -> Path:
    p = Path(token)
    if p.is_file():
        return p
    hits = sorted(PROJECTS.rglob(f"{token}*.jsonl"))
    if not hits:
        sys.exit(f"сессия не найдена: {token}")
    if len(hits) > 1:
        print(f"[неоднозначно, беру первую из {len(hits)}]", file=sys.stderr)
    return hits[0]


def load(path: Path) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        r["_line"] = i
        rows.append(r)
    return rows


def kind(r: dict) -> str:
    t = r.get("type", "?")
    return f"{t}/{r['subtype']}" if r.get("subtype") else t


def body(r: dict) -> str:
    m = r.get("message") or {}
    c = m.get("content")
    if isinstance(c, str):
        return c
    if not isinstance(c, list):
        att = r.get("attachment") or {}
        if not isinstance(att, dict):
            return ""
        # Напоминание об остатке токенов — служебный шум, не содержимое.
        if att.get("type") == "total_tokens_reminder":
            return ""
        return att.get("text", "")
    out = []
    for b in c:
        k = b.get("type")
        if k == "text":
            out.append(b.get("text", ""))
        elif k == "thinking":
            out.append("〔размышление〕")
        elif k == "tool_use":
            out.append(f"〔вызов {b.get('name')}〕")
        elif k == "tool_result":
            out.append("〔результат инструмента〕")
    return "\n".join(x for x in out if x)


def is_tool_result(r: dict) -> bool:
    """Результат инструмента приходит в сообщении с ролью user — но это не
    владелец. Подписывать его «ВЛАДЕЛЕЦ» значит врать при чтении."""
    c = (r.get("message") or {}).get("content")
    return (isinstance(c, list) and bool(c)
            and all(b.get("type") == "tool_result" for b in c))


def stamp(r: dict) -> str:
    return r.get("timestamp") or ""


def render(rows: list[dict], width: int, show_noise: bool) -> None:
    for r in rows:
        k = kind(r)
        if not show_noise and k in NOISE:
            continue
        text = body(r).strip()
        if not text:
            continue
        ts = stamp(r)
        when = ts[11:19] if len(ts) > 19 else "--:--:--"
        role = (r.get("message") or {}).get("role") or k
        head = {"user": "ВЛАДЕЛЕЦ", "assistant": "КЛОД"}.get(role, k.upper())
        if role == "user" and is_tool_result(r):
            head = "инструмент"
        moved = "  ⟲сдвиг" if r.get("_moved") else ""
        print(f"\n── {when}  {head}{moved}  ── стр. {r['_line']}")
        for line in text.splitlines():
            while len(line) > width:
                cut = line.rfind(" ", 0, width)
                cut = cut if cut > 40 else width
                print("   " + line[:cut])
                line = line[cut:].lstrip()
            print("   " + line)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?", help="id сессии, префикс или путь к .jsonl")
    ap.add_argument("--all", action="store_true", help="целиком, а не последние 40")
    ap.add_argument("--tail", type=int, default=40, help="сколько последних сообщений")
    ap.add_argument("--grep", help="только сообщения с этой подстрокой")
    ap.add_argument("--raw-order", action="store_true",
                    help="порядок как в файле — чтобы УВИДЕТЬ сдвиг, а не убрать его")
    ap.add_argument("--noise", action="store_true", help="показать и служебные записи")
    ap.add_argument("--width", type=int, default=100)
    ap.add_argument("--list", action="store_true", help="список сессий")
    a = ap.parse_args()

    if a.list:
        files = sorted(PROJECTS.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        print(f"сессий: {len(files)}\n")
        for p in files[:30]:
            mt = datetime.fromtimestamp(p.stat().st_mtime).strftime("%m-%d %H:%M")
            print(f"  {mt}  {p.stat().st_size/1024/1024:>7.1f} МБ  {p.stem}")
        return

    if not a.session:
        ap.error("нужен id сессии (или --list)")

    path = find_session(a.session)
    rows = load(path)

    # Замер сдвига ДО сортировки — чтобы было что сообщить.
    moved = 0
    prev = ""
    for r in rows:
        ts = stamp(r)
        if ts and prev and ts < prev:
            r["_moved"] = True
            moved += 1
        if ts:
            prev = ts

    print(f"# {path.name}")
    print(f"# записей: {len(rows)}   не по времени: {moved} "
          f"({moved/max(len(rows),1)*100:.1f} %)")
    print(f"# порядок: {'КАК В ФАЙЛЕ' if a.raw_order else 'по времени (исправленный)'}")

    if not a.raw_order:
        # Стабильная сортировка: при равных штампах сохраняется порядок файла.
        rows.sort(key=lambda r: (stamp(r) or "", r["_line"]))

    if a.grep:
        needle = a.grep.lower()
        rows = [r for r in rows if needle in body(r).lower()]
        print(f"# совпадений с «{a.grep}»: {len(rows)}")
    elif not a.all:
        keep = [r for r in rows if body(r).strip() and kind(r) not in NOISE]
        rows = keep[-a.tail:]

    render(rows, a.width, a.noise)


if __name__ == "__main__":
    main()
