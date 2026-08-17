#!/usr/bin/env python3
"""Google Sheets: посмотреть листы, прочитать диапазон, записать, найти таблицу.

Код жил в теле команды `/gsheets` и потому не проверялся ничем. Здесь он собран в
один инструмент и прогнан на живых таблицах.

Два пути доступа, оба рабочие:

    OAuth (по умолчанию)   ~/.claude/google_oauth_token.json — таблицы владельца.
                           Скоуп у токена только `drive`, и его хватает: Sheets API
                           на нём проверен.
    Service account (--sa) ~/.claude/google_service_account.json — таблицы, которые
                           расшарены на служебный ящик
                           your-sa@your-project.iam.gserviceaccount.com.
                           Нужен, когда таблица чужая: OAuth-токен её не видит,
                           пока владелец не дал доступ ЧЕЛОВЕКУ, а не роботу.

    python gsheets_client.py info  <id_или_ссылка>
    python gsheets_client.py read  <id> [--tab Лист1] [--range A1:H50] [--json]
    python gsheets_client.py write <id> --range "Лист1!A1" --values '[["a","b"]]' --yes
    python gsheets_client.py append <id> --tab Лист1 --values '[["a","b"]]' --yes
    python gsheets_client.py search "продажи"
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TOKEN = pathlib.Path.home() / ".claude" / "google_oauth_token.json"
SA = pathlib.Path.home() / ".claude" / "google_service_account.json"
OAUTH_SCOPES = ["https://www.googleapis.com/auth/drive"]
SA_SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
SHEET_MIME = "application/vnd.google-apps.spreadsheet"


def creds(use_sa: bool):
    if use_sa:
        from google.oauth2.service_account import Credentials as SACreds
        if not SA.exists():
            raise SystemExit(f"нет служебного ключа: {SA}")
        return SACreds.from_service_account_file(str(SA), scopes=SA_SCOPES)

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    if not TOKEN.exists():
        raise SystemExit(f"нет токена: {TOKEN}")
    c = Credentials.from_authorized_user_file(str(TOKEN), OAUTH_SCOPES)
    if not c.valid and c.refresh_token:
        c.refresh(Request())
        TOKEN.write_text(c.to_json(), encoding="utf-8")
    return c


def services(use_sa: bool):
    from googleapiclient.discovery import build

    c = creds(use_sa)
    return (build("sheets", "v4", credentials=c, cache_discovery=False),
            build("drive", "v3", credentials=c, cache_discovery=False))


def as_id(s: str) -> str:
    m = re.search(r"/spreadsheets/d/([\w-]{10,})", s)
    return m.group(1) if m else s.strip()


def table(rows: list[list], width: int = 24) -> str:
    if not rows:
        return "  (пусто)"
    cols = max(len(r) for r in rows)
    out = []
    for r in rows:
        cells = [str(r[i]) if i < len(r) else "" for i in range(cols)]
        out.append("  " + " | ".join(c[:width].ljust(min(len(c), width)) for c in cells))
    return "\n".join(out)


def cmd_info(a) -> int:
    sheets, _ = services(a.sa)
    meta = sheets.spreadsheets().get(spreadsheetId=as_id(a.sheet)).execute()
    print(f"  {meta['properties']['title']}")
    for s in meta["sheets"]:
        p = s["properties"]
        g = p.get("gridProperties", {})
        print(f"    {p['title'][:40]:<42} {g.get('rowCount', '?')}×{g.get('columnCount', '?')}")
    print(f"\n  листов: {len(meta['sheets'])}")
    return 0


def cmd_read(a) -> int:
    sheets, _ = services(a.sa)
    sid = as_id(a.sheet)
    rng = a.range
    if a.tab:
        rng = f"'{a.tab}'!{a.range}" if a.range else f"'{a.tab}'"
    elif not rng:
        # Без диапазона Sheets требует явного листа — берём первый.
        meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
        rng = f"'{meta['sheets'][0]['properties']['title']}'"
    r = sheets.spreadsheets().values().get(spreadsheetId=sid, range=rng).execute()
    rows = r.get("values", [])
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    print(f"  {r.get('range')}  строк: {len(rows)}\n")
    print(table(rows[:a.limit] if a.limit else rows))
    if a.limit and len(rows) > a.limit:
        print(f"\n  … показано {a.limit} из {len(rows)} строк")
    return 0


def parse_values(raw: str) -> list[list]:
    v = json.loads(raw)
    if not isinstance(v, list):
        raise SystemExit("--values: нужен JSON-массив строк, например [[\"a\",\"b\"]]")
    return v if v and isinstance(v[0], list) else [v]


def cmd_write(a) -> int:
    if not a.yes:
        print("  это запись в таблицу. Повтори с --yes, если так и задумано.")
        return 1
    sheets, _ = services(a.sa)
    body = {"values": parse_values(a.values)}
    r = sheets.spreadsheets().values().update(
        spreadsheetId=as_id(a.sheet), range=a.range,
        valueInputOption="USER_ENTERED", body=body).execute()
    print(f"  записано: {r.get('updatedCells')} ячеек в {r.get('updatedRange')}")
    return 0


def cmd_append(a) -> int:
    if not a.yes:
        print("  это запись в таблицу. Повтори с --yes, если так и задумано.")
        return 1
    sheets, _ = services(a.sa)
    rng = f"'{a.tab}'" if a.tab else "A1"
    r = sheets.spreadsheets().values().append(
        spreadsheetId=as_id(a.sheet), range=rng,
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body={"values": parse_values(a.values)}).execute()
    up = r.get("updates", {})
    print(f"  добавлено строк: {up.get('updatedRows')} → {up.get('updatedRange')}")
    return 0


def cmd_search(a) -> int:
    _, drive = services(a.sa)
    q = a.query.replace("'", "\\'")
    r = drive.files().list(
        q=f"mimeType='{SHEET_MIME}' and name contains '{q}' and trashed=false",
        fields="files(id,name,modifiedTime)", pageSize=a.limit,
        orderBy="modifiedTime desc",
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = r.get("files", [])
    for f in files:
        print(f"  {f['name'][:64]:<66} {f.get('modifiedTime', '')[:10]}  {f['id']}")
    print(f"\n  найдено: {len(files)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sa", action="store_true",
                    help="через служебный ключ (для расшаренных на робота таблиц)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="какие листы в таблице")
    p.add_argument("sheet")
    p.set_defaults(fn=cmd_info)

    p = sub.add_parser("read", help="прочитать диапазон")
    p.add_argument("sheet")
    p.add_argument("--tab", help="название листа")
    p.add_argument("--range", default="", help="A1:H50")
    p.add_argument("--limit", type=int, default=0, help="сколько строк показать")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_read)

    p = sub.add_parser("write", help="перезаписать диапазон")
    p.add_argument("sheet")
    p.add_argument("--range", required=True, help="'Лист1'!A1")
    p.add_argument("--values", required=True, help='JSON: [["a","b"],["c","d"]]')
    p.add_argument("--yes", action="store_true")
    p.set_defaults(fn=cmd_write)

    p = sub.add_parser("append", help="дописать строки в конец листа")
    p.add_argument("sheet")
    p.add_argument("--tab")
    p.add_argument("--values", required=True, help='JSON: [["a","b"]]')
    p.add_argument("--yes", action="store_true")
    p.set_defaults(fn=cmd_append)

    p = sub.add_parser("search", help="найти таблицы по названию")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_search)

    a = ap.parse_args()
    try:
        return a.fn(a)
    except Exception as e:
        from googleapiclient.errors import HttpError
        if isinstance(e, HttpError):
            hint = ("  Если таблица чужая — попробуй --sa: служебный ключ видит то, "
                    "что расшарено на робота." if e.status_code in (403, 404) else "")
            raise SystemExit(f"  отказ Sheets/Drive: HTTP {e.status_code} — "
                             f"{e.reason}.\n{hint}")
        raise


if __name__ == "__main__":
    sys.exit(main())
