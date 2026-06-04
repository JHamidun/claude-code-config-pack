#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic Telethon CLI-хелпер для Telegram-коннектора (обезличенный).

Авторизация по вашим собственным ключам из .env:
  TELEGRAM_API_ID      — получить на https://my.telegram.org → API development tools
  TELEGRAM_API_HASH    — там же
  TELEGRAM_PHONE       — ваш номер (+1234567890), для первого входа
Сессия сохраняется в ./tg_session.session (НЕ коммитить в git — в .gitignore).

Команды (формат вывода совместим с коннектором telegram.py):
  search-global "<query>" --limit N   — глобальный поиск по доступным чатам
  search "<query>" --limit N          — поиск по личным диалогам
  msg-views <channel> <id1,id2,...>   — просмотры/репосты сообщений канала

ВНИМАНИЕ: используйте только свой аккаунт и соблюдайте ToS Telegram.
"""
import sys
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load_env():
    env = dict(os.environ)
    f = ROOT / ".env"
    if f.exists():
        for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def main():
    try:
        from telethon.sync import TelegramClient
        from telethon import functions
    except ImportError:
        sys.stderr.write("Нужен Telethon: pip install telethon\n")
        return

    env = _load_env()
    api_id = env.get("TELEGRAM_API_ID")
    api_hash = env.get("TELEGRAM_API_HASH")
    phone = env.get("TELEGRAM_PHONE")
    if not (api_id and api_hash):
        sys.stderr.write("Нет TELEGRAM_API_ID / TELEGRAM_API_HASH в .env\n")
        return

    args = sys.argv[1:]
    if not args:
        return
    cmd = args[0]
    session = str(ROOT / "tg_session")

    with TelegramClient(session, int(api_id), api_hash) as client:
        if phone and not client.is_user_authorized():
            client.start(phone=phone)

        def _limit():
            return int(args[args.index("--limit") + 1]) if "--limit" in args else 30

        if cmd in ("search", "search-global"):
            q = args[1] if len(args) > 1 else ""
            n = _limit()
            count = 0
            for msg in client.iter_messages(None if cmd == "search-global" else None, search=q, limit=n):
                if not getattr(msg, "message", None):
                    continue
                try:
                    chat = msg.chat.title if msg.chat and hasattr(msg.chat, "title") else (
                        msg.chat.username if msg.chat else "chat")
                except Exception:
                    chat = "chat"
                sender = ""
                d = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else ""
                text = (msg.message or "").replace("\n", " ")
                print(f"[{d}] [{chat}] {sender}: {text[:800]}")
                count += 1
                if count >= n:
                    break

        elif cmd == "msg-views":
            channel = args[1]
            ids = [int(x) for x in args[2].split(",")] if len(args) > 2 else []
            for mid in ids:
                try:
                    m = client.get_messages(channel, ids=mid)
                    print(f"id {mid} Views: {getattr(m, 'views', 0) or 0} Forwards: {getattr(m, 'forwards', 0) or 0} Replies: 0")
                except Exception:
                    print(f"id {mid} Views: 0 Forwards: 0 Replies: 0")


if __name__ == "__main__":
    main()
