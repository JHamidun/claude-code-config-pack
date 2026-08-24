"""Bulk upload shorts thumbnails to YouTube. Costs 50 quota per upload.

Daily limit: ~200 thumbnail uploads (10K quota / 50 = 200) before quota exhausted.
But quota also shared with webinars — usually only 100-150 thumbs/day.

Usage:
    python _yt_shorts_thumb_upload.py [limit]   # default 100
    python _yt_shorts_thumb_upload.py 50        # safer
"""
import json, sys, os, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
import config

PROGRESS = str(config.THUMBS_DONE)
COVERS_DIR = str(config.COVERS_DIR)
TOKEN_PATH = Path.home() / '.claude' / '.youtube-oauth-token.json'


def get_creds():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f: f.write(creds.to_json())
    return build('youtube', 'v3', credentials=creds)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    yt = get_creds()

    # Done shorts
    done = set()
    if os.path.exists(PROGRESS):
        with open(PROGRESS, encoding='utf-8') as f: done = set(json.load(f))

    # All shorts with covers ready
    cover_ids = set()
    for f in os.listdir(COVERS_DIR):
        if f.endswith('.png'):
            cover_ids.add(f[:-4])

    pending = sorted(cover_ids - done)
    print(f'Pending: {len(pending)}, will upload up to {limit}')

    from googleapiclient.http import MediaFileUpload

    uploaded = 0
    quota_hit = False
    for vid in pending:
        if uploaded >= limit: break
        cover = os.path.join(COVERS_DIR, f'{vid}.png')
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(cover, mimetype='image/png')).execute()
            done.add(vid)
            uploaded += 1
            if uploaded % 10 == 0:
                print(f'  {uploaded}/{limit} done...', flush=True)
        except Exception as e:
            err = str(e)[:200]
            if 'quotaExceeded' in err:
                print(f'QUOTA EXCEEDED at {uploaded} — saving progress + exiting')
                quota_hit = True
                break
            elif '404' in err or 'video' in err.lower():
                # video doesn't exist anymore
                done.add(vid)  # mark to skip next time
                print(f'  SKIP {vid}: video not found')
            else:
                print(f'  FAIL {vid}: {err[:120]}')

    with open(PROGRESS, 'w', encoding='utf-8') as f:
        json.dump(sorted(done), f, indent=2)

    print(f'\n=== Run done. Uploaded {uploaded}, total done: {len(done)} ===')
    if quota_hit:
        sys.exit(2)


if __name__ == '__main__':
    main()
