#!/usr/bin/env python3
"""Context7 docs without the MCP server.

Replaces the @upstash/context7-mcp stdio server (4-5 OS processes via npx)
with a plain HTTP call. Endpoints and parameters were taken from the cached
package source: dist/lib/api.js of @upstash/context7-mcp@1.0.29.

  search:  GET https://context7.com/api/v1/search?query=<q>
  docs:    GET https://context7.com/api/v2/docs/code/<org>/<project>[/<version>]
                 ?topic=<t>&page=<n>&limit=<n>&type=txt
           header: X-Context7-Source: mcp-server

Auth is optional. Anonymous quota is ~200 requests per window
(Ratelimit-Limit header, Context7-Quota-Tier: anonymous). A key from
CONTEXT7_API_KEY (format ctx7sk...) raises the limit; it is sent as
Authorization: Bearer <key>.

Examples:
  context7_docs.py search fastapi
  context7_docs.py search react -n 5 --json
  context7_docs.py docs /microsoft/playwright --topic locators
  context7_docs.py docs /vercel/next.js --topic routing --max-chars 8000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://context7.com/api"
USER_AGENT = "context7_docs.py (urllib)"
TIMEOUT = 30
MAX_REDIRECTS = 5


class Context7Error(Exception):
    """Any failure worth showing to the user as a single clear line."""


def _headers(extra: dict | None = None) -> dict:
    h = {"User-Agent": USER_AGENT}
    if extra:
        h.update(extra)
    key = os.getenv("CONTEXT7_API_KEY")
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def _explain(code: int, body: str) -> str:
    has_key = bool(os.getenv("CONTEXT7_API_KEY"))
    if code == 429:
        if has_key:
            return "429: rate limit exceeded even with CONTEXT7_API_KEY. Try later."
        return (
            "429: anonymous rate limit exceeded (~200 requests per window). "
            "Wait, or set CONTEXT7_API_KEY (free key at https://context7.com/dashboard)."
        )
    if code == 401:
        return "401: CONTEXT7_API_KEY rejected. Keys start with 'ctx7sk'."
    if code == 404:
        return "404: no such library id. Run `search` first and copy the exact id."
    return f"HTTP {code}: {body[:300]}"


def _get(url: str, extra_headers: dict | None = None) -> tuple[int, bytes, dict]:
    """GET without following redirects (Context7 signals renames with 301 + JSON)."""

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_a, **_kw):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers=_headers(extra_headers))
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read()
        if e.code in (301, 302, 307, 308):
            return e.code, body, dict(e.headers)
        raise Context7Error(_explain(e.code, body.decode("utf-8", "replace"))) from None
    except urllib.error.URLError as e:
        raise Context7Error(f"network error: {e.reason}") from None
    except TimeoutError:
        raise Context7Error(f"timeout after {TIMEOUT}s: {url}") from None


def search(query: str) -> list[dict]:
    url = f"{API_BASE}/v1/search?" + urllib.parse.urlencode({"query": query})
    status, body, _ = _get(url)
    if status != 200:
        raise Context7Error(_explain(status, body.decode("utf-8", "replace")))
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise Context7Error("search returned non-JSON body") from None
    if data.get("error"):
        raise Context7Error(str(data["error"]))
    return data.get("results") or []


def _unmangle(library_id: str) -> str:
    """Undo MSYS/Git-Bash path translation of ids that start with '/'.

    In Git Bash `/microsoft/playwright` arrives as
    `C:/Program Files/Git/microsoft/playwright`.
    """
    s = library_id.replace("\\", "/")
    marker = "/Git/"
    if ":" in s[:3] and marker in s:
        s = s.split(marker, 1)[1]
    return s


def fetch_docs(library_id: str, topic: str | None, page: int, snippets: int) -> str:
    lib = _unmangle(library_id).strip().lstrip("/")
    if not lib:
        raise Context7Error("empty library id")
    seen = []
    for _ in range(MAX_REDIRECTS):
        params = {"type": "txt", "page": str(page), "limit": str(snippets)}
        if topic:
            params["topic"] = topic
        url = f"{API_BASE}/v2/docs/code/{lib}?" + urllib.parse.urlencode(params)
        status, body, _ = _get(url, {"X-Context7-Source": "mcp-server"})
        text = body.decode("utf-8", "replace")
        if status in (301, 302, 307, 308):
            # Context7 renames libraries and answers with a JSON redirect body.
            try:
                target = json.loads(text).get("redirectUrl")
            except json.JSONDecodeError:
                target = None
            if not target:
                raise Context7Error(f"redirect without redirectUrl for /{lib}")
            seen.append(lib)
            lib = target.lstrip("/")
            continue
        if status != 200:
            raise Context7Error(_explain(status, text))
        if not text.strip() or text in ("No content available", "No context data available"):
            raise Context7Error(
                f"/{lib}: no documentation for this id"
                + (f" with topic '{topic}'" if topic else "")
            )
        if seen:
            print(f"# redirected: /{' -> /'.join(seen)} -> /{lib}", file=sys.stderr)
        return text
    raise Context7Error(f"too many redirects (>{MAX_REDIRECTS}) starting at /{library_id}")


def format_results(results: list[dict]) -> str:
    def reputation(score) -> str:
        if score is None or score < 0:
            return "Unknown"
        if score >= 7:
            return "High"
        if score >= 4:
            return "Medium"
        return "Low"

    out = []
    for r in results:
        lines = [
            f"- Title: {r.get('title')}",
            f"- Context7-compatible library ID: {r.get('id')}",
            f"- Description: {r.get('description')}",
        ]
        if r.get("totalSnippets", -1) not in (-1, None):
            lines.append(f"- Code Snippets: {r['totalSnippets']}")
        lines.append(f"- Source Reputation: {reputation(r.get('trustScore'))}")
        if r.get("benchmarkScore"):
            lines.append(f"- Benchmark Score: {r['benchmarkScore']}")
        if r.get("versions"):
            lines.append(f"- Versions: {', '.join(r['versions'])}")
        out.append("\n".join(lines))
    return "\n----------\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="context7_docs.py",
        description="Context7 library search and docs over plain HTTP (no MCP server).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  context7_docs.py search fastapi\n"
            "  context7_docs.py search react -n 5 --json\n"
            "  context7_docs.py docs /microsoft/playwright --topic locators\n"
            "  context7_docs.py docs /vercel/next.js --topic routing --max-chars 8000\n"
            "\nCONTEXT7_API_KEY is optional; without it the anonymous quota applies.\n"
        ),
    )
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("search", help="find a library id by name")
    s.add_argument("query", nargs="+", help="library name, e.g. fastapi")
    s.add_argument("-n", "--num", type=int, default=10, help="how many results to show (default 10)")
    s.add_argument("--json", action="store_true", help="raw JSON instead of formatted text")

    d = sub.add_parser("docs", help="fetch documentation for a library id")
    d.add_argument("library_id", help="id from search, e.g. /microsoft/playwright")
    d.add_argument("-t", "--topic", help="narrow docs to a topic, e.g. routing")
    d.add_argument("-p", "--page", type=int, default=1, help="page 1..10 (default 1)")
    d.add_argument("-s", "--snippets", type=int, default=10, help="snippets per page (default 10)")
    d.add_argument("-m", "--max-chars", type=int, default=0, help="truncate output to N chars (0 = no limit)")
    d.add_argument("-o", "--out", help="write to file instead of stdout")

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return 2

    try:
        if args.cmd == "search":
            results = search(" ".join(args.query))
            if not results:
                print("nothing found; try a different name", file=sys.stderr)
                return 1
            results = results[: max(1, args.num)]
            print(json.dumps(results, ensure_ascii=False, indent=2) if args.json
                  else format_results(results))
            return 0

        if not 1 <= args.page <= 10:
            raise Context7Error("--page must be between 1 and 10")
        text = fetch_docs(args.library_id, args.topic, args.page, args.snippets)
        if args.max_chars and len(text) > args.max_chars:
            text = text[: args.max_chars] + f"\n\n[truncated at {args.max_chars} chars]"
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{len(text)} chars -> {args.out}")
        else:
            print(text)
        return 0
    except Context7Error as e:
        print(f"context7: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
