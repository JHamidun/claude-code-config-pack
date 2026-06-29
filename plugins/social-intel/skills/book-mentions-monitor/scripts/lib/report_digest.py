# -*- coding: utf-8 -*-
"""Markdown-дайджест + опциональная отправка в Telegram + алерт на негатив.

Отправка работает, если в .env задан способ доступа к Telegram:
  TG_CLIENT_PATH  — путь к вашему Telethon-CLI с командой `send <chat> "<text>"`
                    (и опц. `send-file <chat> <path>`),
  либо TELEGRAM_API_ID/HASH/PHONE — используется встроенный lib/tg_telethon.py.
Если ничего не настроено — дайджест только пишется в файл, отправка пропускается."""
import os
import sys
import subprocess
import pathlib
from collections import Counter


def _tg_prefix(creds):
    creds = creds or {}
    ext = creds.get("TG_CLIENT_PATH") or os.environ.get("TG_CLIENT_PATH")
    if ext and pathlib.Path(ext).exists():
        return [sys.executable, ext]
    helper = pathlib.Path(__file__).resolve().parent / "tg_telethon.py"
    if helper.exists() and (creds.get("TELEGRAM_API_ID") and creds.get("TELEGRAM_API_HASH")):
        return [sys.executable, str(helper)]
    return None


def make_digest(mentions, book, stats):
    rel = [m for m in mentions if m.get("_is_target")]
    tone = Counter(m.get("_tone", "Нейтрал") for m in rel)
    top = sorted(rel, key=lambda x: x.get("_mi", 0), reverse=True)[:5]
    neg = [m for m in rel if m.get("_tone") == "Негатив"]
    L = [f"📚 *Мониторинг: {book.get('title','')}*",
         f"Всего упоминаний: *{len(rel)}* (ориг {stats.get('orig','?')}/переп {len(rel)-stats.get('orig',0)})",
         f"СМИ {stats.get('smi',0)} · Соцсети {stats.get('soc',0)} · Видео {stats.get('vid',0)} · Читательское {stats.get('rdr',0)}",
         f"Тональность: 👍 {tone.get('Позитив',0)} · ⚪ {tone.get('Нейтрал',0)} · 👎 {tone.get('Негатив',0)}",
         f"Суммарный охват: ~{sum(m.get('_reach',0) for m in rel):,}".replace(",", " ")]
    if neg:
        L.append(f"\n⚠️ *Негатив ({len(neg)}):*")
        for m in neg[:3]:
            L.append(f"• {m.get('title','')[:80]} — {m.get('source','')} {m.get('url','')}")
    L.append("\n*Топ по МедиаИндексу:*")
    for m in top:
        L.append(f"• [{m.get('_mi','')}] {m.get('title','')[:70]} — {m.get('source','')}")
    return "\n".join(L)


def send_telegram(text, chat, creds=None, files=None):
    prefix = _tg_prefix(creds)
    if not (prefix and chat):
        return False
    try:
        subprocess.run(prefix + ["send", str(chat), text], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
        for f in (files or []):
            subprocess.run(prefix + ["send-file", str(chat), str(f)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        return True
    except Exception:
        return False


def alert_negative(mentions, book, chat, creds=None):
    if not (_tg_prefix(creds) and chat):
        return 0
    neg = [m for m in mentions if m.get("_is_target") and m.get("_tone") == "Негатив"]
    for m in neg:
        send_telegram(f"🚨 *Негатив о книге «{book.get('title','')}»*\n{m.get('title','')}\n{m.get('source','')} · {m.get('url','')}", chat, creds)
    return len(neg)
