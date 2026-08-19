#!/usr/bin/env python3
"""Linear через официальный GraphQL API: задачи, поиск, создание, смена статуса.

Замена MCP-плагину Linear. Плагин поднимает отдельный процесс в каждой сессии и
требует авторизации через сторонний коннектор; скрипту хватает ключа
`LINEAR_API_KEY` в файле кредов — у Linear один эндпоинт GraphQL на всё.

    python linear_client.py teams                  # команды и их префиксы
    python linear_client.py issues [--team ENG] [--state "In Progress"]
    python linear_client.py search "текст"
    python linear_client.py issue ENG-123          # одна задача целиком
    python linear_client.py create "Заголовок" --team ENG [--desc "описание"]
    python linear_client.py states --team ENG      # какие статусы бывают
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://api.linear.app/graphql"


def key() -> str:
    env = pathlib.Path.home() / ".claude" / ".credentials.master.env"
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("LINEAR_API_KEY="):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v:
                return v
    raise SystemExit("нет LINEAR_API_KEY в файле кредов")


def gql(query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        method="POST",
        # Ключ Linear идёт БЕЗ приставки Bearer — с ней сервер отвечает отказом.
        headers={"Authorization": key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Linear ответил {e.code}: {e.read().decode('utf-8','replace')[:220]}")
    if d.get("errors"):
        raise SystemExit("Linear: " + "; ".join(x.get("message", "") for x in d["errors"])[:220])
    return d.get("data") or {}


Q_ISSUES = """
query($first:Int!, $filter:IssueFilter) {
  issues(first:$first, filter:$filter, orderBy:updatedAt) {
    nodes { identifier title state{name} assignee{name} priority updatedAt url }
  }
}"""


def show(nodes: list) -> None:
    if not nodes:
        print("  пусто")
        return
    for n in nodes:
        who = (n.get("assignee") or {}).get("name") or "—"
        st = (n.get("state") or {}).get("name") or "?"
        print(f"  {n['identifier']:10} {st:14} {who[:16]:18} {n['title'][:52]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["teams", "issues", "search", "issue", "create", "states"])
    ap.add_argument("arg", nargs="?", default="")
    ap.add_argument("--team", help="префикс команды, например ENG")
    ap.add_argument("--state", help="фильтр по статусу")
    ap.add_argument("--desc", default="", help="описание для create")
    ap.add_argument("--limit", type=int, default=25)
    a = ap.parse_args()

    if a.cmd == "teams":
        d = gql("{ teams(first:50){ nodes{ key name id } } }")
        for t in d["teams"]["nodes"]:
            print(f"  {t['key']:8} {t['name'][:44]:46} {t['id']}")
        return 0

    if a.cmd == "states":
        d = gql("""query($k:String){ workflowStates(first:50,
                 filter:{team:{key:{eq:$k}}}){ nodes{ name type } } }""", {"k": a.team})
        for s in d["workflowStates"]["nodes"]:
            print(f"  {s['name']:22} {s['type']}")
        return 0

    if a.cmd == "issues":
        f = {}
        if a.team:
            f["team"] = {"key": {"eq": a.team}}
        if a.state:
            f["state"] = {"name": {"eq": a.state}}
        d = gql(Q_ISSUES, {"first": a.limit, "filter": f or None})
        show(d["issues"]["nodes"])
        return 0

    if a.cmd == "search":
        d = gql(Q_ISSUES, {"first": a.limit,
                           "filter": {"title": {"containsIgnoreCase": a.arg}}})
        show(d["issues"]["nodes"])
        return 0

    if a.cmd == "issue":
        d = gql("""query($id:String!){ issue(id:$id){ identifier title description
                 state{name} assignee{name} url
                 comments(first:20){ nodes{ body user{name} } } } }""", {"id": a.arg})
        i = d.get("issue")
        if not i:
            raise SystemExit(f"задача {a.arg} не найдена")
        print(f"  {i['identifier']}  {i['title']}")
        print(f"  статус: {(i.get('state') or {}).get('name')}   "
              f"исполнитель: {(i.get('assignee') or {}).get('name') or '—'}")
        if i.get("description"):
            print(f"\n{i['description'][:1500]}")
        for c in (i.get("comments") or {}).get("nodes", []):
            print(f"\n  — {(c.get('user') or {}).get('name','?')}: {c['body'][:220]}")
        print(f"\n  {i.get('url')}")
        return 0

    if a.cmd == "create":
        if not a.team:
            raise SystemExit("нужен --team: префикс команды, смотри `teams`")
        t = gql("query($k:String){ teams(first:1, filter:{key:{eq:$k}}){ nodes{ id } } }",
                {"k": a.team})["teams"]["nodes"]
        if not t:
            raise SystemExit(f"команда {a.team} не найдена")
        d = gql("""mutation($t:String!,$ti:String!,$d:String){
                 issueCreate(input:{teamId:$t,title:$ti,description:$d}){
                   success issue{ identifier url } } }""",
                {"t": t[0]["id"], "ti": a.arg, "d": a.desc})
        i = d["issueCreate"]["issue"]
        print(f"  создана {i['identifier']}: {a.arg}")
        print(f"  {i['url']}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
