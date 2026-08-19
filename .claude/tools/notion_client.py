#!/usr/bin/env python3
"""Notion через официальный API: поиск, чтение страницы, база данных, создание задачи.

Замена MCP-плагину Notion. Плагин поднимает отдельный процесс в каждой сессии и
требует авторизации через сторонний коннектор; скрипту хватает ключа
`NOTION_API_KEY` в файле кредов, а официальный API покрывает то же самое.

    python notion_client.py search "название"
    python notion_client.py page <id>              # прочитать страницу целиком
    python notion_client.py db <id>                # строки базы данных
    python notion_client.py create "Заголовок" --parent <id> [--text "тело"]

Идентификатор берётся из ссылки: в адресе страницы это последние 32 знака.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"          # версия API прибита: Notion ломает совместимость молча


def key() -> str:
    env = pathlib.Path.home() / ".claude" / ".credentials.master.env"
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("NOTION_API_KEY="):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v:
                return v
    raise SystemExit("нет NOTION_API_KEY в файле кредов")


def call(path: str, method: str = "GET", body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{API}/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {key()}",
                 "Notion-Version": VERSION,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        # Самая частая причина отказа — страница не расшарена интеграции.
        hint = ("\n  подсказка: страницу надо открыть интеграции — в Notion «…» → "
                "Connections → выбрать интеграцию") if e.code in (403, 404) else ""
        raise SystemExit(f"Notion ответил {e.code}: {detail}{hint}")


def plain(rich: list) -> str:
    return "".join(x.get("plain_text", "") for x in rich or [])


def title_of(obj: dict) -> str:
    props = obj.get("properties") or {}
    for v in props.values():
        if v.get("type") == "title":
            return plain(v.get("title"))
    return plain((obj.get("title") or []))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["search", "page", "db", "create"])
    ap.add_argument("arg", nargs="?", default="")
    ap.add_argument("--parent", help="id родительской страницы для create")
    ap.add_argument("--text", default="", help="тело для create")
    ap.add_argument("--limit", type=int, default=20)
    a = ap.parse_args()

    if a.cmd == "search":
        d = call("search", "POST", {"query": a.arg, "page_size": a.limit})
        res = d.get("results", [])
        print(f"  найдено: {len(res)}")
        for x in res:
            kind = x.get("object", "?")
            print(f"    [{kind:8}] {title_of(x)[:56]:58} {x.get('id')}")
        return 0

    if a.cmd == "page":
        meta = call(f"pages/{a.arg}")
        print(f"  страница: {title_of(meta)}")
        blocks = call(f"blocks/{a.arg}/children?page_size=100")
        for b in blocks.get("results", []):
            t = b.get("type", "")
            content = b.get(t) or {}
            text = plain(content.get("rich_text"))
            if text:
                mark = {"heading_1": "# ", "heading_2": "## ", "heading_3": "### ",
                        "bulleted_list_item": "  • ", "numbered_list_item": "  – ",
                        "to_do": "  [ ] "}.get(t, "")
                print(f"{mark}{text}")
        return 0

    if a.cmd == "db":
        d = call(f"databases/{a.arg}/query", "POST", {"page_size": a.limit})
        rows = d.get("results", [])
        print(f"  строк: {len(rows)}")
        for r in rows:
            print(f"    {title_of(r)[:60]:62} {r.get('id')}")
        return 0

    if a.cmd == "create":
        if not a.parent:
            raise SystemExit("нужен --parent: id страницы, внутри которой создать")
        body = {"parent": {"page_id": a.parent},
                "properties": {"title": {"title": [{"text": {"content": a.arg}}]}}}
        if a.text:
            body["children"] = [{"object": "block", "type": "paragraph",
                                 "paragraph": {"rich_text": [
                                     {"type": "text", "text": {"content": a.text}}]}}]
        d = call("pages", "POST", body)
        print(f"  создано: {a.arg}")
        print(f"  {d.get('url')}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
