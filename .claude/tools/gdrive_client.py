#!/usr/bin/env python3
"""Google Диск: посмотреть папку и забрать из неё файлы.

Доступ к Диску в этой системе был всегда — живой OAuth-токен с полными правами и
несколько скриптов под разовые задачи. Но общего инструмента не было, в карте
маршрутизации Диск не значился, и поиск по названиям файлов его не находил. Этот
файл закрывает дыру: одна точка входа вместо десятка одноразовых скриптов.

    python gdrive_client.py ls <id_или_ссылка>
    python gdrive_client.py ls <id> --recursive
    python gdrive_client.py get <id_файла> -o ./куда/
    python gdrive_client.py pull <id_папки> -o ./куда/ --ext mp4,m4a,mp3
    python gdrive_client.py find "вебинар"

Принимает и ссылку целиком, и голый идентификатор — из ссылки он вынимается сам.
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import io
import pathlib
import re
import sys

TOKEN = pathlib.Path.home() / ".claude" / "google_oauth_token.json"
FOLDER_MIME = "application/vnd.google-apps.folder"


def service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if not TOKEN.exists():
        raise SystemExit(f"нет токена: {TOKEN}")
    creds = Credentials.from_authorized_user_file(
        str(TOKEN), ["https://www.googleapis.com/auth/drive"])
    # Токен живёт час; обновление молчаливое, и его отсутствие выглядит как «нет доступа».
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def as_id(s: str) -> str:
    """Достать идентификатор из ссылки любого вида."""
    for pat in (r"/folders/([\w-]{10,})", r"/file/d/([\w-]{10,})", r"[?&]id=([\w-]{10,})"):
        m = re.search(pat, s)
        if m:
            return m.group(1)
    return s.strip()


def human(raw: int | str | None) -> str:
    try:
        size = float(raw or 0)
    except (TypeError, ValueError):
        return "—"
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} ТБ"


def listing(svc, folder: str) -> list[dict]:
    out, token = [], None
    while True:
        r = svc.files().list(
            q=f"'{folder}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType,size,modifiedTime,videoMediaMetadata)",
            pageSize=1000, pageToken=token,
            # Без этих двух флагов не видно ничего, что лежит на общих дисках, —
            # и папка выглядит пустой, хотя в ней есть файлы.
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        out += r.get("files", [])
        token = r.get("nextPageToken")
        if not token:
            break
    return sorted(out, key=lambda f: (f["mimeType"] != FOLDER_MIME, f["name"].lower()))


def walk(svc, folder: str, prefix: str = "", depth: int = 0, max_depth: int = 4):
    for f in listing(svc, folder):
        yield prefix, f
        if f["mimeType"] == FOLDER_MIME and depth < max_depth:
            yield from walk(svc, f["id"], prefix + f["name"] + "/", depth + 1, max_depth)


def download(svc, file_id: str, dest: pathlib.Path, name: str | None = None) -> pathlib.Path:
    from googleapiclient.http import MediaIoBaseDownload

    meta = svc.files().get(fileId=file_id, fields="name,size,mimeType",
                           supportsAllDrives=True).execute()
    name = name or meta["name"]
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / re.sub(r'[<>:"/\\|?*]', "_", name)
    if out.exists() and out.stat().st_size == int(meta.get("size") or 0):
        print(f"    уже скачан: {out.name}")
        return out

    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.FileIO(str(out), "wb")
    dl = MediaIoBaseDownload(buf, req, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        status, done = dl.next_chunk()
        if status:
            print(f"    {name[:44]}: {int(status.progress() * 100)}%", end="\r")
    buf.close()
    print(f"    скачан: {out.name} ({human(out.stat().st_size)})")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ls", help="что лежит в папке")
    p.add_argument("folder")
    p.add_argument("--recursive", action="store_true")

    p = sub.add_parser("get", help="скачать один файл")
    p.add_argument("file")
    p.add_argument("-o", "--out", default=".")

    p = sub.add_parser("pull", help="скачать содержимое папки")
    p.add_argument("folder")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--ext", help="только такие расширения, через запятую")
    p.add_argument("--min-mb", type=float, default=0, help="пропускать файлы мельче")
    p.add_argument("--recursive", action="store_true")

    p = sub.add_parser("find", help="поиск по имени по всему диску")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=40)

    a = ap.parse_args()
    svc = service()

    if a.cmd == "ls":
        fid = as_id(a.folder)
        items = list(walk(svc, fid)) if a.recursive else [("", f) for f in listing(svc, fid)]
        total = 0
        for prefix, f in items:
            is_dir = f["mimeType"] == FOLDER_MIME
            mark = "📁" if is_dir else "  "
            size = "" if is_dir else human(f.get("size"))
            dur = ""
            vm = f.get("videoMediaMetadata") or {}
            if vm.get("durationMillis"):
                dur = f"  {int(vm['durationMillis']) / 60000:.0f} мин"
            total += int(f.get("size") or 0)
            print(f"  {mark} {prefix}{f['name'][:64]:<66} {size:>9}{dur}   {f['id']}")
        print(f"\n  всего: {len(items)} шт., {human(total)}")
        return 0

    if a.cmd == "get":
        download(svc, as_id(a.file), pathlib.Path(a.out))
        return 0

    if a.cmd == "pull":
        fid = as_id(a.folder)
        dest = pathlib.Path(a.out)
        exts = {("." + e.strip().lstrip(".")).lower() for e in (a.ext or "").split(",") if e.strip()}
        items = list(walk(svc, fid)) if a.recursive else [("", f) for f in listing(svc, fid)]
        picked = []
        for prefix, f in items:
            if f["mimeType"] == FOLDER_MIME:
                continue
            if exts and pathlib.Path(f["name"]).suffix.lower() not in exts:
                continue
            if int(f.get("size") or 0) < a.min_mb * 1024 * 1024:
                continue
            picked.append((prefix, f))
        print(f"  под условия подходит: {len(picked)} файлов, "
              f"{human(sum(int(f.get('size') or 0) for _, f in picked))}")
        for prefix, f in picked:
            download(svc, f["id"], dest / prefix if prefix else dest, f["name"])
        print(f"  готово → {dest}")
        return 0

    r = svc.files().list(
        q=f"name contains '{a.query}' and trashed=false",
        fields="files(id,name,mimeType,size,modifiedTime)",
        pageSize=a.limit, supportsAllDrives=True,
        includeItemsFromAllDrives=True).execute()
    for f in r.get("files", []):
        kind = "📁" if f["mimeType"] == FOLDER_MIME else "  "
        print(f"  {kind} {f['name'][:70]:<72} {human(f.get('size')):>9}  {f['id']}")
    print(f"\n  найдено: {len(r.get('files', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
