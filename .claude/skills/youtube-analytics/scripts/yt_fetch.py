#!/usr/bin/env python3
"""Fetch all videos from a YouTube channel via Data API v3. Stdlib only."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import tempfile
from datetime import datetime
from pathlib import Path

# На верхнем уровне модуля — только определения. Раньше здесь читались ключи,
# sys.argv и делался sys.exit(1): импорт файла (линтер, автодополнение) ронял
# чужой процесс, а путь по умолчанию был /tmp — на Windows это C:\tmp.
BASE = "https://www.googleapis.com/youtube/v3"
API_KEY = ""
CHANNEL_ID = ""
UPLOADS_PLAYLIST = ""


def default_out():
    """Файл по умолчанию — во временном каталоге ОС, а не в /tmp."""
    return str(Path(tempfile.gettempdir()) / "yt_videos.json")


def api(endpoint, **params):
    params["key"] = API_KEY
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read().decode())


def iso_to_seconds(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def fetch_all_video_ids():
    ids, page = [], None
    while True:
        kwargs = dict(part="contentDetails", playlistId=UPLOADS_PLAYLIST, maxResults=50)
        if page:
            kwargs["pageToken"] = page
        data = api("playlistItems", **kwargs)
        ids.extend(item["contentDetails"]["videoId"] for item in data.get("items", []))
        page = data.get("nextPageToken")
        if not page:
            break
    return ids


def fetch_video_details(ids):
    out = []
    for i in range(0, len(ids), 50):
        batch = ids[i : i + 50]
        data = api("videos", part="statistics,contentDetails,snippet", id=",".join(batch))
        for v in data.get("items", []):
            stats = v.get("statistics", {})
            snip = v.get("snippet", {})
            dur = iso_to_seconds(v.get("contentDetails", {}).get("duration", "PT0S"))
            out.append({
                "id": v["id"],
                "url": f"https://youtu.be/{v['id']}",
                "shorts_url": f"https://youtube.com/shorts/{v['id']}",
                "title": snip.get("title", ""),
                "published": snip.get("publishedAt", ""),
                "duration_sec": dur,
                "is_short": dur <= 60,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "tags": snip.get("tags", []),
            })
    return out


def main(argv=None):
    global API_KEY, CHANNEL_ID, UPLOADS_PLAYLIST
    argv = sys.argv[1:] if argv is None else argv
    API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
    CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")
    if not API_KEY or not CHANNEL_ID:
        print("ОТКАЗ: не заданы YOUTUBE_API_KEY и/или YOUTUBE_CHANNEL_ID.\n"
              "  Ключ: console.cloud.google.com -> YouTube Data API v3 -> Credentials\n"
              "  ID канала: youtube.com/account_advanced (начинается на UC)", file=sys.stderr)
        return 1
    if not CHANNEL_ID.startswith("UC"):
        # Плейлист загрузок = UU + хвост UC-идентификатора. С чужим форматом id
        # запрос вернёт пустой список, и файл запишется пустым — тихий провал.
        print(f"ОТКАЗ: YOUTUBE_CHANNEL_ID={CHANNEL_ID!r} не похож на id канала (ожидается UC...).",
              file=sys.stderr)
        return 1
    UPLOADS_PLAYLIST = "UU" + CHANNEL_ID[2:]
    out_path = argv[0] if argv else default_out()

    print(f"Channel: {CHANNEL_ID}  Uploads playlist: {UPLOADS_PLAYLIST}", file=sys.stderr)
    ids = fetch_all_video_ids()
    print(f"Found {len(ids)} videos. Fetching details...", file=sys.stderr)
    if not ids:
        print("ОТКАЗ: канал не отдал ни одного видео — проверь YOUTUBE_CHANNEL_ID и квоту ключа. "
              "Пустой файл не пишу.", file=sys.stderr)
        return 2
    videos = fetch_video_details(ids)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "channel_id": CHANNEL_ID,
            "count": len(videos),
            "videos": videos,
        }, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(videos)} videos to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
