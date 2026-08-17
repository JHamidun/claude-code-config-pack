#!/usr/bin/env python3
"""Google Docs: прочитать документ, найти документ, дописать текст.

Раньше этот код жил в теле команды `/gdocs` — то есть нигде не запускался и ничем
не проверялся. Тела команд не покрыты линтером связности, поэтому протухание в них
незаметно: агент читает инструкцию, упирается в неё и считает, что доступа нет.

Права берутся из `~/.claude/google_oauth_token.json`. У этого токена единственный
скоуп — `drive`, и его ДОСТАТОЧНО: Docs API проверен на живом документе. Для Gmail
того же токена не хватает (там нужны токены из `~/.claude/.gmail-tokens/`).

    python gdocs_client.py read <id_или_ссылка>
    python gdocs_client.py read <id> --json
    python gdocs_client.py search "резюме встреч"
    python gdocs_client.py append <id> --text "строка" [--yes]

Принимает и ссылку целиком, и голый идентификатор.
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
SCOPES = ["https://www.googleapis.com/auth/drive"]
DOC_MIME = "application/vnd.google-apps.document"


def creds():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN.exists():
        raise SystemExit(f"нет токена: {TOKEN}")
    c = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    # Токен доступа живёт час. Без обновления отказ выглядит как «нет прав».
    if not c.valid and c.refresh_token:
        c.refresh(Request())
        TOKEN.write_text(c.to_json(), encoding="utf-8")
    return c


def services():
    from googleapiclient.discovery import build

    c = creds()
    return (build("docs", "v1", credentials=c, cache_discovery=False),
            build("drive", "v3", credentials=c, cache_discovery=False))


def as_id(s: str) -> str:
    """Достать идентификатор из ссылки любого вида."""
    m = re.search(r"/document/d/([\w-]{10,})", s) or re.search(r"[?&]id=([\w-]{10,})", s)
    return m.group(1) if m else s.strip()


def run_text(elements) -> str:
    return "".join(e.get("textRun", {}).get("content", "") for e in elements)


def walk(content) -> list[str]:
    """Текст документа. Таблицы обходим отдельно — иначе их содержимое теряется."""
    out = []
    for el in content:
        if "paragraph" in el:
            style = el["paragraph"].get("paragraphStyle", {}).get("namedStyleType", "")
            line = run_text(el["paragraph"].get("elements", []))
            if style.startswith("HEADING") and line.strip():
                lvl = style.replace("HEADING_", "")
                out.append("\n" + "#" * (int(lvl) if lvl.isdigit() else 2) + " " + line.strip())
            else:
                out.append(line)
        elif "table" in el:
            for row in el["table"].get("tableRows", []):
                cells = []
                for cell in row.get("tableCells", []):
                    cells.append(" ".join(walk(cell.get("content", []))).strip())
                out.append(" | ".join(cells))
        elif "tableOfContents" in el:
            out += walk(el["tableOfContents"].get("content", []))
    return out


def cmd_read(a) -> int:
    docs, _ = services()
    doc = docs.documents().get(documentId=as_id(a.doc)).execute()
    text = "".join(walk(doc.get("body", {}).get("content", [])))
    if a.json:
        print(json.dumps({"title": doc.get("title"), "id": doc.get("documentId"),
                          "text": text}, ensure_ascii=False, indent=1))
        return 0
    print(f"  {doc.get('title', 'без названия')}   [{doc.get('documentId')}]")
    print(f"  символов: {len(text)}\n")
    print(text[:a.limit] if a.limit else text)
    if a.limit and len(text) > a.limit:
        print(f"\n  … обрезано, всего {len(text)} символов (сними --limit)")
    return 0


def cmd_search(a) -> int:
    _, drive = services()
    q = a.query.replace("'", "\\'")
    r = drive.files().list(
        q=f"mimeType='{DOC_MIME}' and name contains '{q}' and trashed=false",
        fields="files(id,name,modifiedTime,owners(emailAddress))",
        pageSize=a.limit, orderBy="modifiedTime desc",
        # Без этих флагов документы на общих дисках не видны — папка «пустая».
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = r.get("files", [])
    for f in files:
        print(f"  {f['name'][:64]:<66} {f.get('modifiedTime', '')[:10]}  {f['id']}")
    print(f"\n  найдено: {len(files)}")
    return 0


def cmd_append(a) -> int:
    if not a.yes:
        print("  это запись в документ. Повтори с --yes, если так и задумано.")
        return 1
    docs, _ = services()
    doc_id = as_id(a.doc)
    doc = docs.documents().get(documentId=doc_id).execute()
    # Конец тела: индекс последнего элемента минус перевод строки, который Docs
    # держит служебным. Вставка в endIndex целиком отвергается API.
    end = doc["body"]["content"][-1]["endIndex"] - 1
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": [
        {"insertText": {"location": {"index": end}, "text": a.text}}]}).execute()
    print(f"  дописано {len(a.text)} символов в «{doc.get('title')}»")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("read", help="текст документа")
    p.add_argument("doc")
    p.add_argument("--limit", type=int, default=0, help="сколько символов показать")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_read)

    p = sub.add_parser("search", help="найти документы по названию")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("append", help="дописать текст в конец документа")
    p.add_argument("doc")
    p.add_argument("--text", required=True)
    p.add_argument("--yes", action="store_true", help="подтвердить запись")
    p.set_defaults(fn=cmd_append)

    a = ap.parse_args()
    try:
        return a.fn(a)
    except Exception as e:
        # Отказ API читаемой строкой, а не стеком на двадцать строк: 404 почти
        # всегда значит «взят не тот идентификатор», 403 — «нет доступа к файлу».
        from googleapiclient.errors import HttpError
        if isinstance(e, HttpError):
            raise SystemExit(f"  отказ Docs/Drive: HTTP {e.status_code} — "
                             f"{e.reason}. Проверь идентификатор и доступ.")
        raise


if __name__ == "__main__":
    sys.exit(main())
