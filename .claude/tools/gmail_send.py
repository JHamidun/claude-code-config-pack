#!/usr/bin/env python3
"""Отправка писем через Gmail — то, чего в конфиге не было.

Читать почту умели два инструмента, отправлять — ни один. Команда `/gmail` описывала
отправку, но обращалась к токену `google_oauth_token.json`, у которого есть только
право на Диск: попытка неизбежно заканчивалась ошибкой прав, а выглядело это как
зависание и списывалось на сеть.

Рабочие права лежат рядом: у аккаунтов в `~/.claude/.gmail-tokens/` есть `gmail.modify`,
и он включает отправку. Этот скрипт берёт их.

    python gmail_send.py --to кому@example.com --subject "Тема" --body "Текст"
    python gmail_send.py --to a@b.ru,c@d.ru --subject "Тема" --body-file письмо.txt
    python gmail_send.py --to кому@example.com --subject "Тема" --body "…" \\
        --attach отчёт.pdf --from you@example.com
    python gmail_send.py --list-accounts
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

TOKENS = pathlib.Path.home() / ".claude" / ".gmail-tokens"
API = "https://gmail.googleapis.com/gmail/v1/users/me"


def accounts() -> list[pathlib.Path]:
    return sorted(TOKENS.glob("*.json")) if TOKENS.exists() else []


def can_send(data: dict) -> bool:
    """Право на отправку: modify или полный доступ. readonly не подойдёт."""
    sc = data.get("scopes") or []
    if isinstance(sc, str):
        sc = sc.split()
    return any(s.endswith(("gmail.modify", "gmail.send", "mail.google.com/"))
               or s.endswith("mail.google.com") for s in sc)


def access_token(data: dict) -> str:
    """Свежий токен доступа. Живёт час, поэтому обновляется перед каждой отправкой."""
    body = urllib.parse.urlencode({
        "client_id": data["client_id"],
        "client_secret": data["client_secret"],
        "refresh_token": data["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())["access_token"]


def build(sender: str, to: list[str], subject: str, body: str,
          html: str | None, attach: list[str], cc: list[str],
          reply_to: str | None) -> str:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    for path in attach:
        p = pathlib.Path(path)
        if not p.exists():
            raise SystemExit(f"нет вложения: {p}")
        mime, _ = mimetypes.guess_type(p.name)
        main, sub = (mime or "application/octet-stream").split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=main, subtype=sub, filename=p.name)

    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def send(raw: str, token: str, thread_id: str | None = None) -> dict:
    payload: dict = {"raw": raw}
    if thread_id:
        payload["threadId"] = thread_id
    req = urllib.request.Request(
        f"{API}/messages/send", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list-accounts", action="store_true",
                    help="какие ящики доступны и у каких есть право отправки")
    ap.add_argument("--from", dest="sender", help="с какого ящика слать")
    ap.add_argument("--to", help="получатели через запятую")
    ap.add_argument("--cc", default="")
    ap.add_argument("--subject", default="")
    ap.add_argument("--body", default="")
    ap.add_argument("--body-file", help="взять текст письма из файла")
    ap.add_argument("--html-file", help="html-версия письма из файла")
    ap.add_argument("--attach", action="append", default=[], help="файл вложения")
    ap.add_argument("--reply-to")
    ap.add_argument("--thread", help="идентификатор переписки — ответить в неё")
    ap.add_argument("--dry-run", action="store_true",
                    help="собрать письмо и показать, но не отправлять")
    a = ap.parse_args()

    files = accounts()
    if not files:
        raise SystemExit(f"нет токенов в {TOKENS}")

    if a.list_accounts:
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            print(f"  {f.stem:36} {'отправка есть' if can_send(d) else 'только чтение'}")
        print(f"\n  всего ящиков: {len(files)}")
        return 0

    if not a.to or not a.subject:
        raise SystemExit("нужны --to и --subject (или --list-accounts)")

    # Ящик отправителя: явно заданный либо первый, у которого есть право отправки.
    chosen = None
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        if a.sender and f.stem != a.sender:
            continue
        if can_send(d):
            chosen = (f.stem, d)
            break
    if not chosen:
        raise SystemExit("ни у одного ящика нет права отправки "
                         "(нужен gmail.modify или gmail.send)"
                         if not a.sender else
                         f"у ящика {a.sender} нет права отправки")

    sender, data = chosen
    body = a.body
    if a.body_file:
        body = pathlib.Path(a.body_file).read_text(encoding="utf-8")
    html = pathlib.Path(a.html_file).read_text(encoding="utf-8") if a.html_file else None
    to = [x.strip() for x in a.to.split(",") if x.strip()]
    cc = [x.strip() for x in a.cc.split(",") if x.strip()]

    raw = build(sender, to, a.subject, body, html, a.attach, cc, a.reply_to)
    size_kb = len(raw) * 3 // 4 // 1024
    print(f"  от кого: {sender}")
    print(f"  кому: {', '.join(to)}{'  копия: ' + ', '.join(cc) if cc else ''}")
    print(f"  тема: {a.subject}")
    print(f"  размер: {size_kb} КБ{', вложений: ' + str(len(a.attach)) if a.attach else ''}")

    if a.dry_run:
        print("  проверочный прогон — письмо НЕ отправлено")
        return 0

    try:
        r = send(raw, access_token(data), a.thread)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"  отказ: HTTP {e.code} — "
                         f"{e.read().decode('utf-8', 'replace')[:300]}")
    print(f"  отправлено: id={r.get('id')}, переписка={r.get('threadId')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
