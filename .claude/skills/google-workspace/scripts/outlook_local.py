#!/usr/bin/env python3
"""Рабочая почта через УСТАНОВЛЕННЫЙ на машине Outlook (COM), а не по сети.

Сетевой путь через `exchangelib` к корпоративному Exchange пробовать не стоит: он падает
`RecursionError` в urllib3 ещё до авторизации, воспроизводится стабильно, пароль тут ни
при чём. Полтора года инструкция вела именно туда — и всё это время не работала.

Работает обращение к локальному Outlook: приложение стоит на машине, рабочая учётная
запись в нём уже настроена, пароль скрипту не требуется — он берёт ту же сессию, что и
окно Outlook. Работает с учёткой, назначенной в Outlook по умолчанию. Если Outlook
закрыт, COM запустит его сам.

    python outlook_local.py inbox --limit 10
    python outlook_local.py unread
    python outlook_local.py search "счёт" [--field subject|body|from] [--days 30]
    python outlook_local.py read <номер_из_выдачи | EntryID> [--full]
    python outlook_local.py folders
    python outlook_local.py send --to кому@x.ru --subject "Тема" --body "Текст" \\
        [--attach файл.pdf] [--yes]

Требуется Windows, десктопный Outlook и `pip install pywin32`.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Служебные номера папок Outlook (OlDefaultFolders)
FOLDERS = {"inbox": 6, "sent": 5, "outbox": 4, "drafts": 16, "deleted": 3, "junk": 23}


def outlook():
    try:
        import win32com.client as win32
    except ImportError:
        raise SystemExit("нет pywin32: pip install pywin32")
    return win32.Dispatch("Outlook.Application")


def folder(app, name: str):
    ns = app.GetNamespace("MAPI")
    if name.lower() in FOLDERS:
        return ns.GetDefaultFolder(FOLDERS[name.lower()])
    # Папка по названию — ищем среди подпапок входящих и корня учётной записи.
    inbox = ns.GetDefaultFolder(6)
    for src in (inbox.Folders, inbox.Parent.Folders):
        for f in src:
            if f.Name.lower() == name.lower():
                return f
    raise SystemExit(f"нет такой папки: {name}")


def sender_of(m) -> str:
    """Адрес отправителя. У писем внутри Exchange его нет в SenderEmailAddress —
    там лежит LDAP-путь, поэтому падаем обратно на отображаемое имя."""
    try:
        addr = m.SenderEmailAddress or ""
    except Exception:
        addr = ""
    if addr.startswith("/") or not addr:
        try:
            return m.SenderName or "?"
        except Exception:
            return "?"
    return addr


def show(items, limit: int, full: bool = False) -> int:
    n = 0
    for m in items:
        n += 1
        if n > limit:
            break
        try:
            print(f"  [{n}] {m.ReceivedTime:%Y-%m-%d %H:%M}  {sender_of(m)[:34]:<36} "
                  f"{'•' if m.UnRead else ' '} {str(m.Subject)[:56]}")
            if full:
                print(f"      EntryID: {m.EntryID}")
                print("      " + str(m.Body)[:600].replace("\n", "\n      "))
                print()
        except Exception as e:
            print(f"  [{n}] пропущено ({type(e).__name__})")
    return n - 1 if n > limit else n


def sorted_items(f):
    items = f.Items
    items.Sort("[ReceivedTime]", True)  # свежие сверху
    return items


def cmd_inbox(a) -> int:
    f = folder(outlook(), a.folder)
    print(f"  {f.Name}: всего {f.Items.Count}, непрочитанных {f.UnReadItemCount}\n")
    show(sorted_items(f), a.limit)
    return 0


def cmd_unread(a) -> int:
    f = folder(outlook(), a.folder)
    items = sorted_items(f).Restrict("[UnRead] = True")
    print(f"  {f.Name}: непрочитанных {f.UnReadItemCount}\n")
    show(items, a.limit)
    return 0


# Поиск по подстроке идёт ТОЛЬКО через DASL (@SQL со схемными именами полей).
# Простой синтаксис «[Subject] like '%…%'», который был записан в теле команды
# /outlook, Outlook отвергает: «Условие неверно». Проверено — не тратить попытки.
DASL = {"subject": "urn:schemas:httpmail:subject",
        "body": "urn:schemas:httpmail:textdescription",
        "from": "urn:schemas:httpmail:fromname"}


def cmd_search(a) -> int:
    f = folder(outlook(), a.folder)
    # Кавычки в запросе ломают фильтр — вырезаем заранее.
    q = a.query.replace("'", "").replace('"', "")
    flt = f"@SQL=(\"{DASL[a.field]}\" like '%{q}%')"
    if a.days:
        import datetime as dt
        since = (dt.datetime.now() - dt.timedelta(days=a.days)).strftime("%m/%d/%Y")
        flt += f" AND (\"urn:schemas:httpmail:datereceived\" >= '{since}')"
    items = sorted_items(f).Restrict(flt)
    print(f"  поиск {a.field} ~ «{a.query}» в {f.Name}\n")
    found = show(items, a.limit, full=a.full)
    print(f"\n  показано: {found}")
    return 0


def cmd_read(a) -> int:
    app = outlook()
    if len(a.item) > 40:  # EntryID
        m = app.GetNamespace("MAPI").GetItemFromID(a.item)
    else:
        items = sorted_items(folder(app, a.folder))
        m = items.Item(int(a.item))
    print(f"  от:   {sender_of(m)}")
    print(f"  кому: {m.To}")
    print(f"  дата: {m.ReceivedTime:%Y-%m-%d %H:%M}")
    print(f"  тема: {m.Subject}")
    print(f"  id:   {m.EntryID}")
    try:
        att = [a_.FileName for a_ in m.Attachments]
        if att:
            print(f"  вложения: {', '.join(att)}")
    except Exception:
        pass
    print()
    body = str(m.Body)
    print(body if a.full else body[:3000])
    if not a.full and len(body) > 3000:
        print(f"\n  … обрезано, всего {len(body)} символов (добавь --full)")
    return 0


def cmd_folders(a) -> int:
    ns = outlook().GetNamespace("MAPI")
    root = ns.GetDefaultFolder(6).Parent
    print(f"  {root.Name}")
    for f in root.Folders:
        try:
            print(f"    {f.Name[:44]:<46} {f.Items.Count:>6}"
                  f"{'  непроч. ' + str(f.UnReadItemCount) if f.UnReadItemCount else ''}")
            for sub in f.Folders:
                print(f"      └ {sub.Name[:40]:<42} {sub.Items.Count:>6}")
        except Exception:
            continue
    return 0


def cmd_send(a) -> int:
    body = a.body
    if a.body_file:
        body = pathlib.Path(a.body_file).read_text(encoding="utf-8")
    print(f"  кому: {a.to}{'  копия: ' + a.cc if a.cc else ''}")
    print(f"  тема: {a.subject}")
    print(f"  тело: {len(body)} символов"
          f"{', вложений: ' + str(len(a.attach)) if a.attach else ''}")
    if not a.yes:
        print("\n  письмо НЕ отправлено — исходящее действие требует --yes")
        return 1

    app = outlook()
    msg = app.CreateItem(0)
    msg.To = a.to
    if a.cc:
        msg.CC = a.cc
    msg.Subject = a.subject
    if a.html:
        msg.HTMLBody = body
    else:
        msg.Body = body
    for p in a.attach:
        f = pathlib.Path(p).resolve()
        if not f.exists():
            raise SystemExit(f"нет вложения: {f}")
        msg.Attachments.Add(str(f))
    msg.Send()
    print("  отправлено")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default="inbox",
                    help="inbox|sent|drafts|deleted|junk или название папки")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inbox", help="последние письма")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_inbox)

    p = sub.add_parser("unread", help="непрочитанные")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(fn=cmd_unread)

    p = sub.add_parser("search", help="поиск по папке")
    p.add_argument("query")
    p.add_argument("--field", default="subject", choices=["subject", "body", "from"],
                   help="from ищет по ОТОБРАЖАЕМОМУ имени: у писем внутри Exchange "
                        "вместо адреса лежит LDAP-путь, поиск по адресу даёт ноль")
    p.add_argument("--days", type=int, default=0, help="только за последние N дней")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--full", action="store_true", help="показывать начало тела")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("read", help="прочитать письмо целиком")
    p.add_argument("item", help="номер из выдачи или EntryID")
    p.add_argument("--full", action="store_true")
    p.set_defaults(fn=cmd_read)

    p = sub.add_parser("folders", help="дерево папок")
    p.set_defaults(fn=cmd_folders)

    p = sub.add_parser("send", help="отправить письмо")
    p.add_argument("--to", required=True)
    p.add_argument("--cc", default="")
    p.add_argument("--subject", required=True)
    p.add_argument("--body", default="")
    p.add_argument("--body-file")
    p.add_argument("--html", action="store_true", help="тело письма — html")
    p.add_argument("--attach", action="append", default=[])
    p.add_argument("--yes", action="store_true", help="подтвердить отправку")
    p.set_defaults(fn=cmd_send)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
