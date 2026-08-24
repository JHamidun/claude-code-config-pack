"""Fresh shorts inventory + cleanup candidates by latest views.

Ничего не делает при импорте: вся работа — в main(), под `if __name__ == "__main__"`.
Иначе `python -c "import inventory"`, линтер с исполнением или автодополнение
в редакторе сходили бы в живой YouTube API под твоим токеном и писали файлы.
"""
import sys, json, re
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

USAGE = 'python inventory.py   # аргументов нет: инвентаризация shorts + кандидаты на чистку'


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    # --help должен работать без ключей и без сети — поэтому до любых тяжёлых импортов
    if '-h' in argv or '--help' in argv:
        print(__doc__ or '')
        print('Usage:')
        print(USAGE)
        return 0

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    sys.path.insert(0, str(Path(__file__).parent))
    import config

    TOKEN = config.require_yt_token()
    config.ensure_home()
    cd = json.loads(Path(TOKEN).read_text(encoding='utf-8'))
    creds = Credentials(token=cd['token'], refresh_token=cd['refresh_token'],
                       token_uri=cd['token_uri'], client_id=cd['client_id'],
                       client_secret=cd['client_secret'], scopes=cd['scopes'])
    creds.refresh(Request())
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)

    ch = yt.channels().list(part='contentDetails', mine=True).execute()
    if not ch.get('items'):
        print('EMPTY: channels.list(mine=True) вернул ответ без items — канал не виден токену '
              '(флаки YouTube API или токен чужого аккаунта). Повтори позже; если стабильно — '
              f'переавторизуй {TOKEN}.')
        return 2
    uploads = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    all_ids = []
    tok = None
    while True:
        r = yt.playlistItems().list(part='snippet', playlistId=uploads, maxResults=50, pageToken=tok).execute()
        for it in r.get('items', []):
            all_ids.append(it['snippet']['resourceId']['videoId'])
        tok = r.get('nextPageToken')
        if not tok: break

    print(f'Total channel videos: {len(all_ids)}')

    vids = []
    for i in range(0, len(all_ids), 50):
        chunk = all_ids[i:i+50]
        r = yt.videos().list(part='snippet,contentDetails,statistics,status', id=','.join(chunk)).execute()
        for v in r.get('items', []):
            dur = v.get('contentDetails', {}).get('duration', 'PT0S')
            m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dur)
            h, mi, s = (m.groups() if m else (0,0,0))
            secs = int(h or 0)*3600 + int(mi or 0)*60 + int(s or 0)
            vids.append({
                'id': v['id'],
                'title': v['snippet']['title'],
                'published': v['snippet']['publishedAt'],
                'dur_s': secs,
                'views': int(v.get('statistics', {}).get('viewCount', 0)),
                'likes': int(v.get('statistics', {}).get('likeCount', 0)),
                'comments': int(v.get('statistics', {}).get('commentCount', 0)),
                'privacy': v.get('status', {}).get('privacyStatus'),
            })

    shorts = [v for v in vids if 0 < v['dur_s'] <= 60]
    print(f'Shorts (≤60s): {len(shorts)}')

    now = datetime.now(timezone.utc)

    # Categorize
    trash = []          # 'Пустой транскрипт', нулевые названия
    zero_views = []     # 0 views and >7 days old (had chance)
    very_low = []       # <50 views and >14 days old
    duplicates = []     # same title

    # Trash titles
    TRASH_PATTERNS = ['Пустой транскрипт', 'untitled', 'пустой', 'draft', 'черновик']

    for s in shorts:
        t = (s['title'] or '').strip()
        if not t or any(p.lower() in t.lower() for p in TRASH_PATTERNS):
            trash.append(s)
            continue
        pub = datetime.fromisoformat(s['published'].replace('Z','+00:00'))
        age_days = (now - pub).days
        if s['views'] == 0 and age_days > 7:
            zero_views.append(s)
        elif s['views'] < 100 and age_days > 14:
            very_low.append(s)

    # Dupes by title
    by_title = {}
    for s in shorts:
        t = (s['title'] or '').strip()
        if not t: continue
        by_title.setdefault(t, []).append(s)
    for t, group in by_title.items():
        if len(group) > 1:
            group.sort(key=lambda x: x['views'], reverse=True)
            for d in group[1:]:
                duplicates.append({**d, 'dup_kept': group[0]['id'], 'dup_kept_views': group[0]['views']})

    # Unique candidate set
    seen = set()
    candidates = []
    for label, lst in [('trash', trash), ('zero_views_7d+', zero_views), ('low_views<100_14d+', very_low), ('duplicate', duplicates)]:
        for s in lst:
            if s['id'] in seen: continue
            seen.add(s['id'])
            candidates.append({**s, '_reason': label})

    print(f'\n=== Cleanup candidates: {len(candidates)} ===')
    print(f'  trash titles:      {len(trash)}')
    print(f'  zero views 7d+:    {len(zero_views)}')
    print(f'  <50 views 14d+:    {len(very_low)}')
    print(f'  duplicate titles:  {len(duplicates)}')

    # Save
    config.CHANNEL_SNAPSHOT.write_text(
        json.dumps(shorts, ensure_ascii=False, indent=2), encoding='utf-8')
    config.CLEANUP_CANDIDATES.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'\n=== First 30 candidates ===')
    for c in candidates[:30]:
        pub = c['published'][:10]
        print(f'  [{c["_reason"][:18]:<18}] {c["id"]}  v={c["views"]:>5}  [{pub}]  {c["title"][:55]}')

    # Stats summary for remaining shorts
    remaining = [s for s in shorts if s['id'] not in seen]
    print(f'\n=== After cleanup: {len(remaining)} shorts would remain ===')
    if remaining:
        import statistics
        views = [s['views'] for s in remaining]
        print(f'  Median views: {statistics.median(views):,.0f}')
        print(f'  Mean views: {statistics.mean(views):,.0f}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
