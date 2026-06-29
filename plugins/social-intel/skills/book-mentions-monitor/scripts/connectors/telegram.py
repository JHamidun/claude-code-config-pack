# -*- coding: utf-8 -*-
"""Telegram-коннектор (Telethon).
Поиск упоминаний книги в Telegram через CLI-клиент:
  - если в .env задан TG_CLIENT_PATH — используется ваш собственный Telethon-CLI
    (ожидаются команды: `search-global "<q>" --limit N` и `search "<q>" --limit N`,
     формат вывода: [YYYY-MM-DD HH:MM] [Канал] отправитель: текст);
  - иначе используется встроенный generic-хелпер lib/tg_telethon.py
    (логин по TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_PHONE из .env).
Если ни то ни другое не настроено — коннектор тихо возвращает [].
"""
import sys
import os
import re
import subprocess
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s+\[([^\]]+)\]\s+(.*?)\s*:\s*(.*)$")


def _tg_command(creds):
    """Возвращает (argv_prefix, kind) для запуска поиска или (None, None)."""
    ext = creds.get("TG_CLIENT_PATH") or os.environ.get("TG_CLIENT_PATH")
    if ext and pathlib.Path(ext).exists():
        return [sys.executable, ext], "external"
    helper = pathlib.Path(__file__).resolve().parents[1] / "lib" / "tg_telethon.py"
    if helper.exists() and (creds.get("TELEGRAM_API_ID") and creds.get("TELEGRAM_API_HASH")):
        return [sys.executable, str(helper)], "helper"
    return None, None


def _run(prefix, args, timeout=90):
    try:
        p = subprocess.run(prefix + args, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.stdout or ""
    except Exception:
        return ""


def _parse(output):
    recs, cur = [], None
    for ln in output.splitlines():
        m = LINE_RE.match(ln)
        if m:
            if cur:
                recs.append(cur)
            d, chat, sender, text = m.groups()
            cur = {"date": d, "chat": chat.strip(), "sender": sender.strip(), "text": text.strip()}
        elif cur is not None and ln.strip():
            cur["text"] += " " + ln.strip()
    if cur:
        recs.append(cur)
    return recs


def _relevant(text, book):
    t = (text or "").lower()
    if any(e.lower() in t for e in book.get("exclude", [])):
        return False
    pos = book.get("anchors", []) + book.get("authors", []) + [book.get("title", ""), book.get("publisher", "")]
    return any(p and len(p) >= 4 and p.lower() in t for p in pos)


def collect(book, creds, limit=50):
    prefix, _ = _tg_command(creds)
    if not prefix:
        return []
    queries = list(book.get("queries", []))
    for a in book.get("authors", []):
        ln = a.split()[0]
        if len(ln) >= 4:
            queries.append(ln)
    # уникализируем
    seen_q, uniq = set(), []
    for q in queries:
        if q.lower() not in seen_q:
            seen_q.add(q.lower()); uniq.append(q)

    mentions, seen = [], set()
    for q in uniq:
        if len(mentions) >= limit:
            break
        out = _run(prefix, ["search-global", q, "--limit", "30"]) + "\n" + _run(prefix, ["search", q, "--limit", "30"])
        for rec in _parse(out):
            if len(mentions) >= limit:
                break
            text = rec.get("text", "")
            if not text or not _relevant(text, book):
                continue
            chat = rec.get("chat", "")
            key = (chat.lower()[:40], text[:60].lower())
            if key in seen:
                continue
            seen.add(key)
            slug = chat.strip("@")
            url = f"https://t.me/{slug}" if re.match(r"^[A-Za-z0-9_]{3,}$", slug) else ""
            mentions.append(make_mention(channel="telegram", type="Соцсеть", source=chat, url=url,
                                         title=f"Упоминание в {chat}", snippet=text[:500],
                                         date=rec.get("date", ""), author=rec.get("sender", ""), raw=rec))
    return mentions


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
