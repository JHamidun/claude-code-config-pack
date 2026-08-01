"""
Miro CLI for Claude Code — Miro REST API v2 connector.
Boards, items (sticky notes / shapes / text / frames / cards / images / embeds),
connectors, tags, groups, board members, bulk create, board export (Enterprise).

Fallback path for working with Miro boards when the Miro MCP server is unavailable
(MCP requires an Enterprise plan; this REST client works on Free/Starter/Business too,
except for the explicitly Enterprise-only endpoints marked below).

Credentials: ~/.claude/.credentials.master.env
  MIRO_ACCESS_TOKEN   — OAuth access token of your own Miro app
                        (Settings -> Your apps -> Create new app ->
                         "Install app and get OAuth token")
  MIRO_ORG_ID         — optional, only needed for `export` (Enterprise plan)

API: https://api.miro.com  (header: Authorization: Bearer <token>)
Rate limiting is credit based: 100 000 credits/min per user per app.
  Level 1 = 50 credits (2000 req/min)   Level 3 = 500 credits (200 req/min)
  Level 2 = 100 credits (1000 req/min)  Level 4 = 2000 credits (50 req/min)
This client reads X-RateLimit-Remaining and auto-retries 429 with backoff.

Uses `requests` if installed, otherwise falls back to stdlib urllib — no miro SDK needed.

Usage:
  python miro_client.py whoami
  python miro_client.py boards [--query text] [--team ID] [--limit 50]
  python miro_client.py board <board_id>
  python miro_client.py create-board --name "Sprint 42" [--description ...] [--team ID]
  python miro_client.py copy-board <board_id> [--name "Copy"]
  python miro_client.py delete-board <board_id> --confirm
  python miro_client.py items <board_id> [--type sticky_note] [--frame ID] [--all]
  python miro_client.py item <board_id> <item_id>
  python miro_client.py delete-item <board_id> <item_id>
  python miro_client.py sticky <board_id> --text "Idea" --x 0 --y 0 [--color yellow]
  python miro_client.py shape <board_id> --text "Step" --shape round_rectangle --x 0 --y 0
  python miro_client.py text <board_id> --text "Title" --x 0 --y -400 [--font-size 48]
  python miro_client.py frame <board_id> --title "Discovery" --width 1600 --height 900
  python miro_client.py card <board_id> --title "Task" [--description ...] [--due 2026-09-01T10:00:00Z]
  python miro_client.py image <board_id> --url https://... [--title Cover]
  python miro_client.py connect <board_id> --from ID1 --to ID2 [--shape elbowed] [--caption "yes"]
  python miro_client.py connectors <board_id>
  python miro_client.py bulk <board_id> items.json      # up to 20 items, transactional
  python miro_client.py tags <board_id> | create-tag <board_id> --title X | tag-item ... | untag ...
  python miro_client.py groups <board_id>
  python miro_client.py members <board_id> | share <board_id> --emails a@b.c --role editor
  python miro_client.py search "query"                  # boards by name/description
  python miro_client.py export <board_id> [--org ORG_ID] [--format pdf]   # Enterprise only
  python miro_client.py raw GET /v2/boards --query limit=5
"""

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

MIRO_API_BASE = "https://api.miro.com"
CRED_FILE = Path.home() / ".claude" / ".credentials.master.env"
BULK_MAX_ITEMS = 20  # hard API limit for POST /v2/boards/{id}/items/bulk

STICKY_COLORS = [
    "gray", "light_yellow", "yellow", "orange", "light_green", "green",
    "dark_green", "cyan", "light_pink", "pink", "violet", "red",
    "light_blue", "blue", "dark_blue", "black",
]
ITEM_TYPES = [
    "text", "shape", "sticky_note", "image", "document", "card", "app_card",
    "preview", "frame", "embed", "doc_format", "data_table_format",
]

try:
    import requests  # noqa: F401
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False


def load_env():
    """Load ~/.claude/.credentials.master.env without overriding real env vars."""
    if CRED_FILE.exists():
        for line in CRED_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN", "")
ORG_ID = os.getenv("MIRO_ORG_ID", "")


def require_token():
    """Exit with a clear how-to if MIRO_ACCESS_TOKEN is missing."""
    if ACCESS_TOKEN:
        return
    print("MIRO_ACCESS_TOKEN is not configured.")
    print()
    print("How to get one (works on a Free plan, no Enterprise needed):")
    print("  1. Sign in to Miro -> avatar (top right) -> Settings -> 'Your apps' tab.")
    print("     Direct link: https://miro.com/app/settings/user-profile/apps")
    print("  2. Click '+ Create new app'. Give it a name.")
    print("     Miro asks to create a Developer team if you don't have one")
    print("     (https://miro.com/app/dashboard/?createDevTeam=1) — it is free.")
    print("     Leave 'Expire user authorization token' UNCHECKED for a")
    print("     non-expiring token, or check it if you want 60-min tokens + refresh.")
    print("  3. In the app page, 'App Credentials' shows Client ID / Client secret.")
    print("     In 'Permissions' (or the app manifest 'scopes'), enable at least:")
    print("       boards:read   — list boards, read items")
    print("       boards:write  — create/update/delete boards and items")
    print("     (optional: identity:read, team:read, boards:export for Enterprise export)")
    print("  4. Scroll to the bottom -> click 'Install app and get OAuth token'.")
    print("     Pick the team where your boards live -> 'Install & authorize'.")
    print("     Copy the access token shown in the success dialog.")
    print()
    print(f"Then add this line to {CRED_FILE}:")
    print()
    print("  MIRO_ACCESS_TOKEN=<paste_token_here>")
    print()
    print("Docs: https://developers.miro.com/docs/getting-started-with-oauth")
    sys.exit(2)


class MiroError(Exception):
    pass


def api_request(method, path, params=None, body=None, retries=3, verbose=False):
    """Call the Miro REST API. Returns parsed JSON (or {} for 204).

    method: GET / POST / PATCH / PUT / DELETE
    path:   absolute API path, e.g. "/v2/boards"
    params: dict -> query string
    body:   dict -> JSON body
    Retries on HTTP 429 (rate limit) and 5xx with exponential backoff.
    """
    url = MIRO_API_BASE + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
    }
    payload = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    delay = 2.0
    last_err = None
    for attempt in range(retries + 1):
        status, text, resp_headers = _do_request(method, url, headers, payload)

        if verbose:
            rem = resp_headers.get("X-RateLimit-Remaining")
            lim = resp_headers.get("X-RateLimit-Limit")
            if rem is not None:
                print(f"[rate-limit] {rem}/{lim} credits left", file=sys.stderr)

        if status == 429 or 500 <= status < 600:
            last_err = (status, text)
            if attempt < retries:
                wait = delay * (2 ** attempt)
                label = "rate limited" if status == 429 else f"server error {status}"
                print(f"Miro {label}, retrying in {wait:.0f}s...", file=sys.stderr)
                time.sleep(wait)
                continue

        if status == 401:
            raise MiroError(
                "401 Unauthorized — the token is invalid or expired.\n"
                "If your app was created with 'Expire user authorization token' checked, "
                "access tokens live only 60 minutes; re-install the app "
                "('Install app and get OAuth token') or refresh via "
                "POST https://api.miro.com/v1/oauth/token (grant_type=refresh_token)."
            )
        if status == 403:
            raise MiroError(
                f"403 Forbidden — the token lacks the required scope, or this endpoint "
                f"needs an Enterprise plan.\nAPI said: {text[:500]}"
            )
        if status == 404:
            raise MiroError(f"404 Not Found — wrong board/item ID, or no access.\n{text[:500]}")
        if status >= 400:
            raise MiroError(f"HTTP {status} from Miro:\n{text[:1500]}")

        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except ValueError:
            return {"raw": text}

    status, text = last_err
    raise MiroError(f"Miro kept returning HTTP {status} after {retries} retries:\n{text[:800]}")


def _do_request(method, url, headers, payload):
    """Single HTTP call. Returns (status, body_text, headers_dict)."""
    if HAVE_REQUESTS:
        import requests
        try:
            resp = requests.request(method, url, headers=headers, data=payload, timeout=60)
        except requests.RequestException as e:
            print(f"Network error talking to Miro: {e}", file=sys.stderr)
            sys.exit(1)
        return resp.status_code, resp.text, dict(resp.headers)

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers or {})
    except urllib.error.URLError as e:
        print(f"Network error talking to Miro: {e.reason}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------- helpers

def out(args, data, lines=None):
    """Print JSON when --json, otherwise the human-readable lines."""
    if getattr(args, "json", False) or lines is None:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for line in lines:
            print(line)


def position(args):
    return {"x": float(args.x), "y": float(args.y)}


def geometry(width=None, height=None):
    g = {}
    if width is not None:
        g["width"] = float(width)
    if height is not None:
        g["height"] = float(height)
    return g or None


def parent(args):
    pid = getattr(args, "parent", None)
    return {"id": pid} if pid else None


def compact(d):
    """Drop None values from a dict (one level)."""
    return {k: v for k, v in d.items() if v is not None}


def item_line(it):
    data = it.get("data") or {}
    label = (
        data.get("content")
        or data.get("title")
        or data.get("url")
        or ""
    )
    label = " ".join(str(label).split())[:70]
    pos = it.get("position") or {}
    xy = f"({pos.get('x', '?')},{pos.get('y', '?')})"
    return f"{it.get('id'):<22} {it.get('type', '?'):<14} {xy:<18} {label}"


def board_url(b):
    return (b.get("viewLink") or "").strip()


# ---------------------------------------------------------------- commands

def cmd_whoami(args):
    """GET /v1/oauth-token — token info: scopes, user, team, type."""
    data = api_request("GET", "/v1/oauth-token", verbose=args.verbose)
    lines = [
        f"token type : {data.get('type')}",
        f"scopes     : {', '.join(data.get('scopes') or [])}",
        f"user       : {(data.get('user') or {}).get('name')} ({(data.get('user') or {}).get('id')})",
        f"team       : {(data.get('team') or {}).get('name')} ({(data.get('team') or {}).get('id')})",
        f"org        : {(data.get('organization') or {}).get('name') or '(none — non-Enterprise plan)'}",
        f"created by : {(data.get('createdBy') or {}).get('name')}",
    ]
    out(args, data, lines)


def cmd_boards(args):
    """GET /v2/boards — list boards (Level 1)."""
    params = {
        "query": args.query,
        "team_id": args.team,
        "project_id": args.project,
        "owner": args.owner,
        "limit": args.limit,
        "offset": args.offset,
        "sort": args.sort,
    }
    data = api_request("GET", "/v2/boards", params=params, verbose=args.verbose)
    boards = data.get("data") or []
    lines = [f"{len(boards)} board(s), total {data.get('total', '?')}"]
    for b in boards:
        lines.append(f"{b.get('id'):<28} {(b.get('name') or '')[:45]:<47} {board_url(b)}")
    out(args, data, lines)


def cmd_search(args):
    """Alias for `boards --query` (Miro v2 has no global item search)."""
    args.query = args.text
    args.team = args.project = args.owner = None
    args.offset = None
    args.sort = "last_created"
    cmd_boards(args)


def cmd_board(args):
    """GET /v2/boards/{board_id} (Level 1)."""
    data = api_request("GET", f"/v2/boards/{args.board_id}", verbose=args.verbose)
    lines = [
        f"id          : {data.get('id')}",
        f"name        : {data.get('name')}",
        f"description : {data.get('description')}",
        f"link        : {board_url(data)}",
        f"team        : {(data.get('team') or {}).get('name')}",
        f"owner       : {(data.get('owner') or {}).get('name')}",
        f"created     : {data.get('createdAt')}   modified: {data.get('modifiedAt')}",
    ]
    out(args, data, lines)


def cmd_create_board(args):
    """POST /v2/boards (Level 3). Free plan: max 3 team boards."""
    body = compact({
        "name": args.name,
        "description": args.description,
        "teamId": args.team,
    })
    if args.sharing or args.access:
        body["policy"] = {"sharingPolicy": compact({
            "access": args.sharing,
            "teamAccess": args.access,
        })}
    data = api_request("POST", "/v2/boards", body=body, verbose=args.verbose)
    out(args, data, [f"created board {data.get('id')}", board_url(data)])


def cmd_copy_board(args):
    """PUT /v2/boards?copy_from=... (Level 4 — heaviest call, 2000 credits)."""
    body = compact({"name": args.name, "description": args.description, "teamId": args.team})
    data = api_request("PUT", "/v2/boards", params={"copy_from": args.board_id},
                       body=body or None, verbose=args.verbose)
    out(args, data, [f"copied to board {data.get('id')}", board_url(data)])


def cmd_delete_board(args):
    """DELETE /v2/boards/{board_id} (Level 3)."""
    if not args.confirm:
        print("Refusing to delete a board without --confirm.")
        sys.exit(2)
    api_request("DELETE", f"/v2/boards/{args.board_id}", verbose=args.verbose)
    out(args, {"deleted": args.board_id}, [f"deleted board {args.board_id}"])


def cmd_items(args):
    """GET /v2/boards/{id}/items, or items inside a frame when --frame is given."""
    params = {"limit": args.limit, "type": args.type}
    path = f"/v2/boards/{args.board_id}/items"
    if args.frame:
        params["parent_item_id"] = args.frame

    collected, cursor, pages = [], None, 0
    while True:
        if cursor:
            params["cursor"] = cursor
        data = api_request("GET", path, params=params, verbose=args.verbose)
        chunk = data.get("data") or []
        collected.extend(chunk)
        cursor = data.get("cursor")
        pages += 1
        if not (args.all and cursor) or pages > 100:
            break

    result = {"total": len(collected), "data": collected, "cursor": cursor}
    lines = [f"{len(collected)} item(s)" + (" (more pages available, use --all)" if cursor and not args.all else "")]
    lines += [item_line(i) for i in collected]
    out(args, result, lines)


def cmd_item(args):
    """GET /v2/boards/{id}/items/{item_id} (Level 1)."""
    data = api_request("GET", f"/v2/boards/{args.board_id}/items/{args.item_id}",
                       verbose=args.verbose)
    out(args, data)


def cmd_delete_item(args):
    """DELETE /v2/boards/{id}/items/{item_id} (Level 3)."""
    api_request("DELETE", f"/v2/boards/{args.board_id}/items/{args.item_id}",
                verbose=args.verbose)
    out(args, {"deleted": args.item_id}, [f"deleted item {args.item_id}"])


def _create_item(args, endpoint, body, label):
    data = api_request("POST", f"/v2/boards/{args.board_id}/{endpoint}",
                       body=body, verbose=args.verbose)
    out(args, data, [f"created {label} {data.get('id')}"])


def cmd_sticky(args):
    """POST /v2/boards/{id}/sticky_notes (Level 2)."""
    body = compact({
        "data": compact({"content": args.text, "shape": args.shape}),
        "style": compact({
            "fillColor": args.color,
            "textAlign": args.align,
        }) or None,
        "position": position(args),
        "geometry": geometry(args.width),
        "parent": parent(args),
    })
    _create_item(args, "sticky_notes", body, "sticky note")


def cmd_shape(args):
    """POST /v2/boards/{id}/shapes (Level 2)."""
    body = compact({
        "data": compact({"content": args.text, "shape": args.shape}),
        "style": compact({
            "fillColor": args.fill,
            "borderColor": args.border,
            "color": args.text_color,
            "fontSize": str(args.font_size) if args.font_size else None,
        }) or None,
        "position": position(args),
        "geometry": geometry(args.width, args.height),
        "parent": parent(args),
    })
    _create_item(args, "shapes", body, "shape")


def cmd_text(args):
    """POST /v2/boards/{id}/texts (Level 2)."""
    body = compact({
        "data": {"content": args.text},
        "style": compact({
            "color": args.color,
            "fontSize": str(args.font_size) if args.font_size else None,
            "fontFamily": args.font,
            "textAlign": args.align,
        }) or None,
        "position": position(args),
        "geometry": geometry(args.width),   # texts accept width only
        "parent": parent(args),
    })
    _create_item(args, "texts", body, "text")


def cmd_frame(args):
    """POST /v2/boards/{id}/frames (Level 2)."""
    body = compact({
        "data": compact({"title": args.title, "format": "custom", "type": "freeform"}),
        "style": compact({"fillColor": args.fill}) or None,
        "position": position(args),
        "geometry": geometry(args.width, args.height),
    })
    _create_item(args, "frames", body, "frame")


def cmd_card(args):
    """POST /v2/boards/{id}/cards (Level 2)."""
    body = compact({
        "data": compact({
            "title": args.title,
            "description": args.description,
            "dueDate": args.due,
            "assigneeId": args.assignee,
        }),
        "style": compact({"cardTheme": args.theme}) or None,
        "position": position(args),
        "geometry": geometry(args.width, args.height),
        "parent": parent(args),
    })
    _create_item(args, "cards", body, "card")


def cmd_image(args):
    """POST /v2/boards/{id}/images — image from URL (Level 2)."""
    body = compact({
        "data": compact({"url": args.url, "title": args.title}),
        "position": position(args),
        "geometry": geometry(args.width),
        "parent": parent(args),
    })
    _create_item(args, "images", body, "image")


def cmd_embed(args):
    """POST /v2/boards/{id}/embeds — embed an external URL (Level 2)."""
    body = compact({
        "data": compact({"url": args.url, "mode": args.mode}),
        "position": position(args),
        "geometry": geometry(args.width),
    })
    _create_item(args, "embeds", body, "embed")


def cmd_document(args):
    """POST /v2/boards/{id}/documents — document from URL (Level 2)."""
    body = compact({
        "data": compact({"url": args.url, "title": args.title}),
        "position": position(args),
        "geometry": geometry(args.width),
        "parent": parent(args),
    })
    _create_item(args, "documents", body, "document")


def cmd_connect(args):
    """POST /v2/boards/{id}/connectors (Level 2). Frames cannot be connected."""
    if args.start == args.end:
        print("startItem.id must be different from endItem.id")
        sys.exit(2)
    start = {"id": args.start}
    end = {"id": args.end}
    if args.snap_start:
        start["snapTo"] = args.snap_start
    if args.snap_end:
        end["snapTo"] = args.snap_end

    body = compact({
        "startItem": start,
        "endItem": end,
        "shape": args.shape,
        "captions": [{"content": args.caption}] if args.caption else None,
        "style": compact({
            "strokeColor": args.color,
            "strokeStyle": args.stroke,
            "startStrokeCap": args.start_cap,
            "endStrokeCap": args.end_cap,
        }) or None,
    })
    data = api_request("POST", f"/v2/boards/{args.board_id}/connectors",
                       body=body, verbose=args.verbose)
    out(args, data, [f"created connector {data.get('id')}: {args.start} -> {args.end}"])


def cmd_connectors(args):
    """GET /v2/boards/{id}/connectors (Level 2)."""
    data = api_request("GET", f"/v2/boards/{args.board_id}/connectors",
                       params={"limit": args.limit}, verbose=args.verbose)
    conns = data.get("data") or []
    lines = [f"{len(conns)} connector(s)"]
    for c in conns:
        s = (c.get("startItem") or {}).get("id")
        e = (c.get("endItem") or {}).get("id")
        caps = "; ".join(x.get("content", "") for x in (c.get("captions") or []))
        lines.append(f"{c.get('id'):<22} {s} -> {e}  {c.get('shape', '')} {caps}")
    out(args, data, lines)


def cmd_bulk(args):
    """POST /v2/boards/{id}/items/bulk — up to 20 items, transactional (Level 2 per item).

    JSON file must be a list of item objects, each with "type" plus the usual
    data/style/position/geometry keys, e.g.:
      [{"type":"sticky_note","data":{"content":"A"},"position":{"x":0,"y":0}},
       {"type":"shape","data":{"content":"B","shape":"circle"},"position":{"x":300,"y":0}}]
    """
    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(2)
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"{path} is not valid JSON: {e}")
        sys.exit(2)
    if not isinstance(items, list):
        print(f"{path} must contain a JSON array of item objects.")
        sys.exit(2)
    if not items:
        print(f"{path} contains an empty array — nothing to create.")
        sys.exit(2)

    created, failed = [], []
    chunks = [items[i:i + BULK_MAX_ITEMS] for i in range(0, len(items), BULK_MAX_ITEMS)]
    for n, chunk in enumerate(chunks, 1):
        if len(chunks) > 1 and not args.json:
            print(f"chunk {n}/{len(chunks)} ({len(chunk)} items)...", file=sys.stderr)
        try:
            data = api_request("POST", f"/v2/boards/{args.board_id}/items/bulk",
                               body=chunk, verbose=args.verbose)
        except MiroError as e:
            failed.append({"chunk": n, "error": str(e)})
            print(f"chunk {n} failed (bulk is transactional — none of its items were "
                  f"created):\n{e}", file=sys.stderr)
            continue
        created.extend(data.get("data") or [])
        if n < len(chunks):
            time.sleep(0.3)

    result = {"created": len(created), "data": created, "failed": failed}
    lines = [f"created {len(created)} item(s) in {len(chunks)} chunk(s)"]
    lines += [item_line(i) for i in created]
    if failed:
        lines.append(f"{len(failed)} chunk(s) failed — see --json for details")
    out(args, result, lines)


def cmd_tags(args):
    """GET /v2/boards/{id}/tags (Level 1)."""
    data = api_request("GET", f"/v2/boards/{args.board_id}/tags",
                       params={"limit": args.limit}, verbose=args.verbose)
    tags = data.get("data") or []
    lines = [f"{len(tags)} tag(s)"]
    lines += [f"{t.get('id'):<22} {t.get('fillColor', ''):<12} {t.get('title')}" for t in tags]
    out(args, data, lines)


def cmd_create_tag(args):
    """POST /v2/boards/{id}/tags (Level 1)."""
    body = compact({"title": args.title, "fillColor": args.color})
    data = api_request("POST", f"/v2/boards/{args.board_id}/tags",
                       body=body, verbose=args.verbose)
    out(args, data, [f"created tag {data.get('id')} '{data.get('title')}'"])


def cmd_tag_item(args):
    """POST /v2/boards/{id}/items/{item_id}?tag_id=... (Level 1)."""
    api_request("POST", f"/v2/boards/{args.board_id}/items/{args.item_id}",
                params={"tag_id": args.tag_id}, verbose=args.verbose)
    out(args, {"item": args.item_id, "tag": args.tag_id},
        [f"attached tag {args.tag_id} to item {args.item_id}"])


def cmd_untag(args):
    """DELETE /v2/boards/{id}/items/{item_id}?tag_id=... (Level 1)."""
    api_request("DELETE", f"/v2/boards/{args.board_id}/items/{args.item_id}",
                params={"tag_id": args.tag_id}, verbose=args.verbose)
    out(args, {"item": args.item_id, "tag": args.tag_id},
        [f"removed tag {args.tag_id} from item {args.item_id}"])


def cmd_groups(args):
    """GET /v2/boards/{id}/groups (Level 2)."""
    data = api_request("GET", f"/v2/boards/{args.board_id}/groups",
                       params={"limit": args.limit}, verbose=args.verbose)
    groups = data.get("data") or []
    lines = [f"{len(groups)} group(s)"]
    lines += [f"{g.get('id'):<22} {len(g.get('data', {}).get('items', []))} item(s)" for g in groups]
    out(args, data, lines)


def cmd_group(args):
    """POST /v2/boards/{id}/groups (Level 2) — group existing items."""
    ids = [i.strip() for i in args.items.split(",") if i.strip()]
    if len(ids) < 2:
        print("Need at least 2 item IDs to form a group (comma separated).")
        sys.exit(2)
    data = api_request("POST", f"/v2/boards/{args.board_id}/groups",
                       body={"data": {"items": ids}}, verbose=args.verbose)
    out(args, data, [f"created group {data.get('id')} of {len(ids)} items"])


def cmd_members(args):
    """GET /v2/boards/{id}/members (Level 1)."""
    data = api_request("GET", f"/v2/boards/{args.board_id}/members",
                       params={"limit": args.limit}, verbose=args.verbose)
    members = data.get("data") or []
    lines = [f"{len(members)} member(s)"]
    lines += [f"{m.get('id'):<22} {m.get('role', ''):<10} {m.get('name')}" for m in members]
    out(args, data, lines)


def cmd_share(args):
    """POST /v2/boards/{id}/members (Level 3) — invite by email."""
    emails = [e.strip() for e in args.emails.split(",") if e.strip()]
    if not emails:
        print("Provide at least one email via --emails a@b.c,c@d.e")
        sys.exit(2)
    body = compact({"emails": emails, "role": args.role, "message": args.message})
    data = api_request("POST", f"/v2/boards/{args.board_id}/members",
                       body=body, verbose=args.verbose)
    out(args, data, [f"invited {len(emails)} user(s) as {args.role}"])


def cmd_export(args):
    """POST /v2/orgs/{org_id}/boards/export/jobs — ENTERPRISE ONLY.

    Requires: Enterprise plan, Company Admin role, eDiscovery enabled,
    and the boards:export scope. There is no board-export endpoint on
    Free/Starter/Business plans.
    """
    org = args.org or ORG_ID
    if not org:
        print("Board export needs an organization ID (Enterprise plan only).")
        print("Pass --org <ORG_ID> or set MIRO_ORG_ID in")
        print(f"  {CRED_FILE}")
        print()
        print("Note: POST /v2/orgs/{org_id}/boards/export/jobs is documented as")
        print("'Enterprise only ... you must be a Company Admin and have eDiscovery")
        print("enabled'. On Free/Starter/Business there is no REST board export —")
        print("use the Miro UI (Export board as PDF/image) or the Web SDK instead.")
        sys.exit(2)

    body = {
        "boardIds": [b.strip() for b in args.board_id.split(",") if b.strip()],
        "boardFormat": args.format,
        "boardIdsWithFormat": None,
        "requestId": args.request_id,
    }
    body = compact(body)
    data = api_request("POST", f"/v2/orgs/{org}/boards/export/jobs",
                       params={"request_id": args.request_id}, body=body,
                       verbose=args.verbose)
    job_id = data.get("jobId") or data.get("id")
    lines = [
        f"export job: {job_id}",
        f"poll:   python miro_client.py raw GET /v2/orgs/{org}/boards/export/jobs/{job_id}",
        f"result: python miro_client.py raw GET /v2/orgs/{org}/boards/export/jobs/{job_id}/results",
    ]
    out(args, data, lines)


def cmd_raw(args):
    """Escape hatch: call any endpoint directly."""
    params = {}
    for q in args.query or []:
        k, _, v = q.partition("=")
        params[k] = v
    body = None
    if args.data:
        src = Path(args.data)
        text = src.read_text(encoding="utf-8") if src.exists() else args.data
        try:
            body = json.loads(text)
        except ValueError as e:
            print(f"--data is not valid JSON (and not a path to a JSON file): {e}")
            sys.exit(2)
    data = api_request(args.method.upper(), args.path, params=params or None,
                       body=body, verbose=args.verbose)
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- CLI

def main():
    parser = argparse.ArgumentParser(
        prog="miro_client.py",
        description="Miro REST API v2 CLI. Needs MIRO_ACCESS_TOKEN in "
                    "~/.claude/.credentials.master.env "
                    "(run any command without it to get setup instructions).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Rate limits are credit-based: 100000 credits/min per user per app. "
               "L1=50, L2=100, L3=500, L4=2000 credits per call.",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    parser.add_argument("--verbose", action="store_true",
                        help="print X-RateLimit headers to stderr")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--json", action="store_true", help="machine-readable JSON output")
        p.add_argument("--verbose", action="store_true", help="print rate-limit headers")
        return p

    def xy(p):
        p.add_argument("--x", type=float, default=0, help="x coordinate, board center is 0")
        p.add_argument("--y", type=float, default=0, help="y coordinate, board center is 0")
        return p

    # --- account -----------------------------------------------------
    p = common(sub.add_parser("whoami", help="token info: scopes, user, team (GET /v1/oauth-token)"))
    p.set_defaults(func=cmd_whoami)

    # --- boards ------------------------------------------------------
    p = common(sub.add_parser("boards", help="list boards (GET /v2/boards, L1)"))
    p.add_argument("--query", help="search board name and description")
    p.add_argument("--team", help="filter by team_id")
    p.add_argument("--project", help="filter by project_id (Spaces)")
    p.add_argument("--owner", help="filter by owner id")
    p.add_argument("--limit", type=int, default=50, help="page size, default 50 (max 50)")
    p.add_argument("--offset", type=int, help="pagination offset")
    p.add_argument("--sort", choices=["default", "last_modified", "last_opened",
                                      "last_created", "alphabetically"],
                   help="sort order")
    p.set_defaults(func=cmd_boards)

    p = common(sub.add_parser("search", help="search boards by name/description "
                                             "(alias of boards --query; Miro v2 has no item search)"))
    p.add_argument("text", help="search string")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_search)

    p = common(sub.add_parser("board", help="board info (GET /v2/boards/{id}, L1)"))
    p.add_argument("board_id")
    p.set_defaults(func=cmd_board)

    p = common(sub.add_parser("create-board", help="create a board (POST /v2/boards, L3). "
                                                   "Free plan allows only 3 team boards"))
    p.add_argument("--name", required=True, help="board name, 1-60 chars")
    p.add_argument("--description", help="board description, max 300 chars")
    p.add_argument("--team", help="team_id to place the board in")
    p.add_argument("--sharing", choices=["private", "view", "edit", "comment"],
                   help="sharing policy access level")
    p.add_argument("--access", choices=["private", "view", "edit", "comment"],
                   dest="access", help="team access level")
    p.set_defaults(func=cmd_create_board)

    p = common(sub.add_parser("copy-board", help="copy a board (PUT /v2/boards?copy_from, L4 = 2000 credits)"))
    p.add_argument("board_id", help="source board to copy")
    p.add_argument("--name")
    p.add_argument("--description")
    p.add_argument("--team")
    p.set_defaults(func=cmd_copy_board)

    p = common(sub.add_parser("delete-board", help="delete a board (DELETE /v2/boards/{id}, L3)"))
    p.add_argument("board_id")
    p.add_argument("--confirm", action="store_true", help="required — this is destructive")
    p.set_defaults(func=cmd_delete_board)

    # --- items -------------------------------------------------------
    p = common(sub.add_parser("items", help="list items on a board (GET /v2/boards/{id}/items, L2)"))
    p.add_argument("board_id")
    p.add_argument("--type", choices=ITEM_TYPES, help="filter by item type")
    p.add_argument("--frame", help="list items inside this frame id (parent_item_id)")
    p.add_argument("--limit", type=int, default=50, help="page size, default 50")
    p.add_argument("--all", action="store_true", help="follow cursor and fetch every page")
    p.set_defaults(func=cmd_items)

    p = common(sub.add_parser("item", help="get one item (GET /v2/boards/{id}/items/{item_id}, L1)"))
    p.add_argument("board_id")
    p.add_argument("item_id")
    p.set_defaults(func=cmd_item)

    p = common(sub.add_parser("delete-item", help="delete an item (DELETE, L3)"))
    p.add_argument("board_id")
    p.add_argument("item_id")
    p.set_defaults(func=cmd_delete_item)

    # --- create items ------------------------------------------------
    p = common(xy(sub.add_parser("sticky", help="create a sticky note (POST .../sticky_notes, L2)")))
    p.add_argument("board_id")
    p.add_argument("--text", required=True, help="sticky note content (supports basic HTML)")
    p.add_argument("--color", choices=STICKY_COLORS, help="fill color, default light_yellow")
    p.add_argument("--shape", choices=["square", "rectangle"], help="default square")
    p.add_argument("--align", choices=["left", "center", "right"])
    p.add_argument("--width", type=float, help="width in dp (height is derived)")
    p.add_argument("--parent", help="frame id to place the item into")
    p.set_defaults(func=cmd_sticky)

    p = common(xy(sub.add_parser("shape", help="create a shape (POST .../shapes, L2)")))
    p.add_argument("board_id")
    p.add_argument("--text", help="text inside the shape")
    p.add_argument("--shape", default="rectangle",
                   help="rectangle, round_rectangle, circle, triangle, rhombus, "
                        "star, cloud, flow_chart_decision, ... (default rectangle)")
    p.add_argument("--width", type=float)
    p.add_argument("--height", type=float)
    p.add_argument("--fill", help="fill color, hex like #2d9bf0")
    p.add_argument("--border", help="border color, hex")
    p.add_argument("--text-color", dest="text_color", help="text color, hex")
    p.add_argument("--font-size", dest="font_size", type=int)
    p.add_argument("--parent", help="frame id")
    p.set_defaults(func=cmd_shape)

    p = common(xy(sub.add_parser("text", help="create a text item (POST .../texts, L2)")))
    p.add_argument("board_id")
    p.add_argument("--text", required=True, help="text content (supports basic HTML)")
    p.add_argument("--width", type=float, help="text items accept width only")
    p.add_argument("--font-size", dest="font_size", type=int)
    p.add_argument("--font", help="fontFamily, e.g. arial, roboto, open_sans")
    p.add_argument("--color", help="text color, hex like #1a1a1a")
    p.add_argument("--align", choices=["left", "center", "right"])
    p.add_argument("--parent", help="frame id")
    p.set_defaults(func=cmd_text)

    p = common(xy(sub.add_parser("frame", help="create a frame (POST .../frames, L2)")))
    p.add_argument("board_id")
    p.add_argument("--title", required=True)
    p.add_argument("--width", type=float, default=1600)
    p.add_argument("--height", type=float, default=900)
    p.add_argument("--fill", help="frame background color, hex or #ffffff")
    p.set_defaults(func=cmd_frame)

    p = common(xy(sub.add_parser("card", help="create a card (POST .../cards, L2)")))
    p.add_argument("board_id")
    p.add_argument("--title", required=True)
    p.add_argument("--description")
    p.add_argument("--due", help="ISO 8601 UTC, e.g. 2026-09-01T10:00:00Z")
    p.add_argument("--assignee", help="Miro user id")
    p.add_argument("--theme", help="card theme color, hex")
    p.add_argument("--width", type=float)
    p.add_argument("--height", type=float)
    p.add_argument("--parent", help="frame id")
    p.set_defaults(func=cmd_card)

    p = common(xy(sub.add_parser("image", help="add an image from URL (POST .../images, L2)")))
    p.add_argument("board_id")
    p.add_argument("--url", required=True, help="publicly reachable image URL")
    p.add_argument("--title")
    p.add_argument("--width", type=float)
    p.add_argument("--parent", help="frame id")
    p.set_defaults(func=cmd_image)

    p = common(xy(sub.add_parser("embed", help="embed an external URL (POST .../embeds, L2)")))
    p.add_argument("board_id")
    p.add_argument("--url", required=True, help="URL to embed (YouTube, Figma, ...)")
    p.add_argument("--mode", choices=["inline", "modal"], help="default inline")
    p.add_argument("--width", type=float)
    p.set_defaults(func=cmd_embed)

    p = common(xy(sub.add_parser("document", help="add a document from URL (POST .../documents, L2)")))
    p.add_argument("board_id")
    p.add_argument("--url", required=True, help="publicly reachable document URL (PDF etc.)")
    p.add_argument("--title")
    p.add_argument("--width", type=float)
    p.add_argument("--parent", help="frame id")
    p.set_defaults(func=cmd_document)

    # --- connectors --------------------------------------------------
    p = common(sub.add_parser("connect", help="connect two items (POST .../connectors, L2). "
                                              "Frames cannot be connected"))
    p.add_argument("board_id")
    p.add_argument("--from", dest="start", required=True, help="start item id")
    p.add_argument("--to", dest="end", required=True, help="end item id")
    p.add_argument("--shape", choices=["straight", "elbowed", "curved"], help="default curved")
    p.add_argument("--caption", help="text on the connector, max 200 chars")
    p.add_argument("--color", help="line color, hex like #2d9bf0")
    p.add_argument("--stroke", choices=["normal", "dashed", "dotted"])
    p.add_argument("--start-cap", dest="start_cap",
                   help="none, stealth, arrow, oval, filled_triangle, ... (default none)")
    p.add_argument("--end-cap", dest="end_cap",
                   help="none, stealth, arrow, oval, filled_triangle, ... (default stealth)")
    p.add_argument("--snap-start", dest="snap_start",
                   choices=["auto", "top", "right", "bottom", "left"])
    p.add_argument("--snap-end", dest="snap_end",
                   choices=["auto", "top", "right", "bottom", "left"])
    p.set_defaults(func=cmd_connect)

    p = common(sub.add_parser("connectors", help="list connectors (GET .../connectors, L2)"))
    p.add_argument("board_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_connectors)

    # --- bulk --------------------------------------------------------
    p = common(sub.add_parser("bulk", help="create many items from a JSON file "
                                           "(POST .../items/bulk, max 20 per call, transactional)"))
    p.add_argument("board_id")
    p.add_argument("file", help="path to a JSON array of item objects")
    p.set_defaults(func=cmd_bulk)

    # --- tags --------------------------------------------------------
    p = common(sub.add_parser("tags", help="list board tags (GET .../tags, L1)"))
    p.add_argument("board_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_tags)

    p = common(sub.add_parser("create-tag", help="create a tag (POST .../tags, L1)"))
    p.add_argument("board_id")
    p.add_argument("--title", required=True)
    p.add_argument("--color", help="red, magenta, violet, green, blue, cyan, "
                                   "yellow, gray, black, ...")
    p.set_defaults(func=cmd_create_tag)

    p = common(sub.add_parser("tag-item", help="attach a tag to an item (POST .../items/{id}?tag_id, L1)"))
    p.add_argument("board_id")
    p.add_argument("item_id")
    p.add_argument("tag_id")
    p.set_defaults(func=cmd_tag_item)

    p = common(sub.add_parser("untag", help="detach a tag from an item (DELETE .../items/{id}?tag_id, L1)"))
    p.add_argument("board_id")
    p.add_argument("item_id")
    p.add_argument("tag_id")
    p.set_defaults(func=cmd_untag)

    # --- groups ------------------------------------------------------
    p = common(sub.add_parser("groups", help="list item groups (GET .../groups, L2)"))
    p.add_argument("board_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_groups)

    p = common(sub.add_parser("group", help="group existing items (POST .../groups, L2)"))
    p.add_argument("board_id")
    p.add_argument("--items", required=True, help="comma-separated item ids, at least 2")
    p.set_defaults(func=cmd_group)

    # --- members -----------------------------------------------------
    p = common(sub.add_parser("members", help="list board members (GET .../members, L1)"))
    p.add_argument("board_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_members)

    p = common(sub.add_parser("share", help="invite users to a board (POST .../members, L3)"))
    p.add_argument("board_id")
    p.add_argument("--emails", required=True, help="comma-separated emails")
    p.add_argument("--role", default="commenter",
                   choices=["viewer", "commenter", "editor", "coowner", "owner", "guest"])
    p.add_argument("--message", help="invitation message")
    p.set_defaults(func=cmd_share)

    # --- export (Enterprise) ----------------------------------------
    p = common(sub.add_parser("export", help="ENTERPRISE ONLY: create a board export job "
                                             "(POST /v2/orgs/{org}/boards/export/jobs, L4)"))
    p.add_argument("board_id", help="board id, or several comma-separated")
    p.add_argument("--org", help="organization id (or set MIRO_ORG_ID)")
    p.add_argument("--format", default="pdf", choices=["pdf", "html", "csv"],
                   help="board export format, default pdf")
    p.add_argument("--request-id", dest="request_id", help="idempotency key for the job")
    p.set_defaults(func=cmd_export)

    # --- raw ---------------------------------------------------------
    p = common(sub.add_parser("raw", help="call any endpoint directly"))
    p.add_argument("method", help="GET / POST / PATCH / PUT / DELETE")
    p.add_argument("path", help="e.g. /v2/boards/xxx/items")
    p.add_argument("--query", action="append", help="key=value, repeatable")
    p.add_argument("--data", help="JSON string or path to a .json file")
    p.set_defaults(func=cmd_raw)

    args = parser.parse_args()
    require_token()
    try:
        args.func(args)
    except MiroError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
