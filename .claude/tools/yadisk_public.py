#!/usr/bin/env python3
"""Публичные папки Яндекс.Диска: посмотреть и скачать.

Готовый клиент к Диску работает только со своим хранилищем — по чужой публичной
ссылке он не ходит. А материалы курсов и вебинаров раздают именно так: одна ссылка
на папку, внутри вложенные папки с записями. Авторизация для этого не нужна вовсе,
публичный ресурс отдаётся по одному запросу.

    python yadisk_public.py ls https://yadi.sk/d/XXXX
    python yadisk_public.py ls https://yadi.sk/d/XXXX --recursive
    python yadisk_public.py pull https://yadi.sk/d/XXXX -o ./куда/ --ext mp4,m4a
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
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

API = "https://cloud-api.yandex.net/v1/disk/public/resources"
UA = {"User-Agent": "Mozilla/5.0"}


def api(public_key: str, path: str | None = None, limit: int = 500,
        offset: int = 0) -> dict:
    q = {"public_key": public_key, "limit": limit, "offset": offset}
    if path:
        q["path"] = path
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(q)}", headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def items(public_key: str, path: str | None = None) -> list[dict]:
    """Все элементы папки. Список отдаётся страницами — без обхода видно только первые."""
    out, offset = [], 0
    while True:
        d = api(public_key, path, offset=offset)
        emb = d.get("_embedded") or {}
        chunk = emb.get("items", [])
        out += chunk
        offset += len(chunk)
        if not chunk or offset >= emb.get("total", 0):
            break
    return out


def walk(public_key: str, path: str | None = None, prefix: str = "", depth: int = 0):
    for it in items(public_key, path):
        yield prefix, it
        if it.get("type") == "dir" and depth < 4:
            yield from walk(public_key, it["path"], prefix + it["name"] + "/", depth + 1)


def human(n) -> str:
    try:
        size = float(n or 0)
    except (TypeError, ValueError):
        return "—"
    for u in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024:
            return f"{size:.0f} {u}"
        size /= 1024
    return f"{size:.1f} ТБ"


def fetch(public_key: str, path: str, dest: pathlib.Path, name: str) -> None:
    """Скачать файл. Ссылка на скачивание выдаётся отдельным запросом и живёт недолго."""
    q = urllib.parse.urlencode({"public_key": public_key, "path": path})
    req = urllib.request.Request(f"{API}/download?{q}", headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        href = json.loads(r.read())["href"]

    dest.mkdir(parents=True, exist_ok=True)
    out = dest / re.sub(r'[<>:"/\\|?*]', "_", name)
    req = urllib.request.Request(href, headers=UA)
    with urllib.request.urlopen(req, timeout=1800) as r:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        with open(out, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total:
                    print(f"    {name[:40]}: {got * 100 // total}%", end="\r")
    print(f"    скачан: {out.name} ({human(out.stat().st_size)})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ls", help="что внутри публичной папки")
    p.add_argument("url")
    p.add_argument("--recursive", action="store_true")

    p = sub.add_parser("pull", help="скачать файлы из публичной папки")
    p.add_argument("url")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--ext", help="только такие расширения, через запятую")
    p.add_argument("--min-mb", type=float, default=0)
    p.add_argument("--recursive", action="store_true", default=True)

    a = ap.parse_args()
    key = a.url.strip()

    # Ссылка ведёт либо на папку, либо на один файл. У файла нет вложений, и обход
    # папки возвращает пустоту — снаружи это выглядит как «в папке ничего нет».
    head = api(key)
    if head.get("type") == "file":
        got = [("", head)]
    else:
        got = list(walk(key)) if a.recursive else [("", i) for i in items(key)]

    if a.cmd == "ls":
        total = 0
        for prefix, it in got:
            mark = "📁" if it.get("type") == "dir" else "  "
            size = "" if it.get("type") == "dir" else human(it.get("size"))
            total += int(it.get("size") or 0)
            print(f"  {mark} {prefix}{it['name'][:66]:<68} {size:>9}")
        print(f"\n  всего: {len(got)} шт., {human(total)}")
        return 0

    exts = {("." + e.strip().lstrip(".")).lower()
            for e in (a.ext or "").split(",") if e.strip()}
    picked = [(pre, it) for pre, it in got
              if it.get("type") == "file"
              and (not exts or pathlib.Path(it["name"]).suffix.lower() in exts)
              and int(it.get("size") or 0) >= a.min_mb * 1024 * 1024]
    print(f"  подходит: {len(picked)} файлов, "
          f"{human(sum(int(i.get('size') or 0) for _, i in picked))}")
    dest = pathlib.Path(a.out)
    for prefix, it in picked:
        fetch(key, it["path"], dest / prefix if prefix else dest, it["name"])
    print(f"  готово → {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
