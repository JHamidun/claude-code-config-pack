#!/usr/bin/env python3
"""Sound design — fetch SFX from Freesound + place on timeline + sidechain ducking.

Uses the Freesound REST API directly (no SDK dep). Get a free token:
https://freesound.org/apiv2/apply  → put FREESOUND_API_KEY in ~/.claude/.credentials.master.env

Usage:
  python sfx.py search whoosh --max 5                     # list + download top SFX
  python sfx.py place in.mp4 out.mp4 --sfx whoosh.mp3 --at 4.0   # mix SFX at 4.0s
  python sfx.py duck music.mp3 vo.mp3 ducked.mp3          # sidechain music under VO

CC license note: filter to CC0/CC-BY for commercial; check each file's license.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

API = "https://freesound.org/apiv2"


def _key():
    p = os.path.expanduser("~/.claude/.credentials.master.env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if line.startswith("FREESOUND_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv("FREESOUND_API_KEY", "")


def search(query, max_n, out_dir="sfx"):
    key = _key()
    if not key:
        print("No FREESOUND_API_KEY — get one at https://freesound.org/apiv2/apply"); return
    os.makedirs(out_dir, exist_ok=True)
    q = urllib.parse.urlencode({
        "query": query, "filter": "duration:[0.1 TO 4.0]", "sort": "rating_desc",
        "fields": "id,name,license,previews", "page_size": max_n, "token": key})
    data = json.loads(urllib.request.urlopen("%s/search/text/?%s" % (API, q), timeout=30).read())
    for r in data.get("results", []):
        url = r["previews"]["preview-hq-mp3"]
        out = os.path.join(out_dir, "%s_%d.mp3" % (query, r["id"]))
        req = urllib.request.Request(url + ("?token=" + key if "token" not in url else ""))
        with urllib.request.urlopen(req, timeout=60) as resp, open(out, "wb") as f:
            f.write(resp.read())
        print("%-40s %-12s -> %s" % (r["name"][:40], r["license"].split("/")[-2] if "/" in r["license"] else r["license"], out))


def place(video, out, sfx, at):
    ms = int(at * 1000)
    subprocess.run(["ffmpeg", "-y", "-i", video, "-i", sfx, "-filter_complex",
                    "[1:a]adelay=%d|%d[s];[0:a][s]amix=inputs=2:normalize=0[a]" % (ms, ms),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out], check=True)


def duck(music, vo, out):
    subprocess.run(["ffmpeg", "-y", "-i", music, "-i", vo, "-filter_complex",
                    "[1:a]asplit=2[sc][v];"
                    "[0:a][sc]sidechaincompress=threshold=0.02:ratio=8:attack=50:release=500:makeup=1[d];"
                    "[d][v]amix=inputs=2:normalize=0[a]",
                    "-map", "[a]", "-c:a", "aac", "-b:a", "192k", out], check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--max", type=int, default=5); s.add_argument("--out-dir", default="sfx")
    p = sub.add_parser("place"); p.add_argument("video"); p.add_argument("out"); p.add_argument("--sfx", required=True); p.add_argument("--at", type=float, required=True)
    d = sub.add_parser("duck"); d.add_argument("music"); d.add_argument("vo"); d.add_argument("out")
    a = ap.parse_args()
    if a.cmd == "search":
        search(a.query, a.max, a.out_dir)
    elif a.cmd == "place":
        place(a.video, a.out, a.sfx, a.at); print("saved", a.out)
    elif a.cmd == "duck":
        duck(a.music, a.vo, a.out); print("saved", a.out)


if __name__ == "__main__":
    main()
