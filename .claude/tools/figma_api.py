#!/usr/bin/env python3
"""Figma API helper for Claude Code.

Usage:
    python figma_api.py me                          # Current user info
    python figma_api.py projects                    # List team projects
    python figma_api.py files <project_id>          # List files in project
    python figma_api.py pages <file_key>            # List pages in file
    python figma_api.py tree <file_key> <node_id>   # Print node tree with text
    python figma_api.py text <file_key> <node_id>   # Extract all text from node
    python figma_api.py export <file_key> <node_id> [scale] [format]  # Export as image
    python figma_api.py parse-url <figma_url>       # Parse Figma URL
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

TOKEN = None  # resolved lazily in main() — never at import time


def load_token():
    token = os.getenv("FIGMA_ACCESS_TOKEN")
    if not token:
        env_path = os.path.expanduser("~/.claude/.credentials.master.env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("FIGMA_ACCESS_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return token


TEAM_ID = os.getenv("FIGMA_TEAM_ID", "")  # your Figma team id (from team URL)


def figma_get(path):
    """GET request to Figma API."""
    req = urllib.request.Request(f"https://api.figma.com/v1/{path}")
    req.add_header("X-Figma-Token", TOKEN)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        print(f"Error {e.code}: {e.reason}", file=sys.stderr)
        if body:
            print(body[:500], file=sys.stderr)
        sys.exit(1)


def cmd_me():
    """Show current user info."""
    data = figma_get("me")
    print(f"Handle: {data.get('handle')}")
    print(f"Email:  {data.get('email')}")
    print(f"ID:     {data.get('id')}")


def cmd_projects():
    """List team projects."""
    if not TEAM_ID:
        print("Error: FIGMA_TEAM_ID not set (take it from your Figma team URL).", file=sys.stderr)
        sys.exit(1)
    data = figma_get(f"teams/{TEAM_ID}/projects")
    for p in data.get("projects", []):
        print(f"  {p['name']:40s} id: {p['id']}")


def cmd_files(project_id):
    """List files in a project."""
    data = figma_get(f"projects/{project_id}/files")
    for f in data.get("files", []):
        mod = f.get("last_modified", "")[:10]
        print(f"  {f['name']:40s} key: {f['key']}  modified: {mod}")


def cmd_pages(file_key):
    """List pages in a file."""
    data = figma_get(f"files/{file_key}?depth=1")
    print(f"File: {data.get('name')}")
    print(f"Modified: {data.get('lastModified', '')}")
    print()
    for i, page in enumerate(data.get("document", {}).get("children", []), 1):
        n_children = len(page.get("children", []))
        print(f"  {i}. {page['name']:30s} id: {page['id']}  ({n_children} top-level elements)")


def print_tree(node, indent=0):
    """Recursively print node tree."""
    t = node.get("type", "")
    name = node.get("name", "")
    chars = node.get("characters", "")
    prefix = "  " * indent
    if chars:
        display = chars[:120].replace("\n", " | ")
        print(f'{prefix}{t}: "{name}" => "{display}"')
    else:
        print(f'{prefix}{t}: "{name}"')
    for c in node.get("children", []):
        print_tree(c, indent + 1)


def cmd_tree(file_key, node_id):
    """Print full node tree."""
    api_id = node_id.replace("-", ":")
    data = figma_get(f"files/{file_key}/nodes?ids={node_id}&depth=10")
    node = data["nodes"][api_id]["document"]
    print(f"Node: {node.get('name')} (type: {node.get('type')})")
    print()
    print_tree(node)


def extract_text(node, results=None):
    """Extract all text nodes recursively."""
    if results is None:
        results = []
    if node.get("characters"):
        results.append({
            "id": node.get("id"),
            "name": node.get("name"),
            "text": node.get("characters"),
        })
    for c in node.get("children", []):
        extract_text(c, results)
    return results


def cmd_text(file_key, node_id):
    """Extract all text from a node."""
    api_id = node_id.replace("-", ":")
    data = figma_get(f"files/{file_key}/nodes?ids={node_id}&depth=10")
    node = data["nodes"][api_id]["document"]
    texts = extract_text(node)
    for t in texts:
        print(f"[{t['id']}] {t['name']}: {t['text'][:200]}")
        print()


def cmd_export(file_key, node_id, scale="2", fmt="png"):
    """Export node as image."""
    data = figma_get(f"images/{file_key}?ids={node_id}&format={fmt}&scale={scale}")
    api_id = node_id.replace("-", ":")
    url = data.get("images", {}).get(api_id)
    if url:
        print(f"Image URL: {url}")
        # Download
        out_file = f"figma_export_{node_id.replace(':', '-')}.{fmt}"
        urllib.request.urlretrieve(url, out_file)
        print(f"Saved: {out_file}")
    else:
        print("No image returned", file=sys.stderr)


def cmd_parse_url(url):
    """Parse Figma URL into components."""
    file_match = re.search(r"figma\.com/(?:design|file)/([a-zA-Z0-9]+)", url)
    node_match = re.search(r"node-id=([0-9]+-[0-9]+)", url)
    team_match = re.search(r"team/([0-9]+)", url)
    project_match = re.search(r"project/([0-9]+)", url)

    result = {
        "file_key": file_match.group(1) if file_match else None,
        "node_id": node_match.group(1) if node_match else None,
        "team_id": team_match.group(1) if team_match else None,
        "project_id": project_match.group(1) if project_match else None,
    }
    for k, v in result.items():
        if v:
            print(f"  {k}: {v}")


def main():
    global TOKEN

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd != "parse-url":  # parse-url is offline, no token needed
        TOKEN = load_token()
        if not TOKEN:
            print("Error: FIGMA_ACCESS_TOKEN not found", file=sys.stderr)
            print("Set it in ~/.claude/.credentials.master.env", file=sys.stderr)
            sys.exit(1)

    def arg(i, name):
        if len(sys.argv) <= i:
            print(f"Error: {cmd} requires <{name}>", file=sys.stderr)
            print(__doc__)
            sys.exit(2)
        return sys.argv[i]

    if cmd == "me":
        cmd_me()
    elif cmd == "projects":
        cmd_projects()
    elif cmd == "files":
        cmd_files(arg(2, "project_id"))
    elif cmd == "pages":
        cmd_pages(arg(2, "file_key"))
    elif cmd == "tree":
        cmd_tree(arg(2, "file_key"), arg(3, "node_id"))
    elif cmd == "text":
        cmd_text(arg(2, "file_key"), arg(3, "node_id"))
    elif cmd == "export":
        scale = sys.argv[4] if len(sys.argv) > 4 else "2"
        fmt = sys.argv[5] if len(sys.argv) > 5 else "png"
        cmd_export(arg(2, "file_key"), arg(3, "node_id"), scale, fmt)
    elif cmd == "parse-url":
        cmd_parse_url(arg(2, "figma_url"))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
