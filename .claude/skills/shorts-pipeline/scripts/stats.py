"""Статистика shorts своего канала (канал берётся из токена, mine=True).

Ничего не делает при импорте: вся работа — в main(), под `if __name__ == "__main__"`.
Иначе `python -c "import stats"`, линтер с исполнением или автодополнение в редакторе
сходили бы в живой YouTube API под твоим токеном и писали файлы.
"""
import sys, json, re, statistics
from pathlib import Path
from datetime import datetime, timezone, timedelta

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

USAGE = 'python stats.py   # аргументов нет: статистика shorts канала'


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

    TOKEN_FILE = config.require_yt_token()
    config.ensure_home()

    creds_data = json.loads(Path(TOKEN_FILE).read_text(encoding='utf-8'))
    creds = Credentials(
        token=creds_data['token'], refresh_token=creds_data['refresh_token'],
        token_uri=creds_data['token_uri'], client_id=creds_data['client_id'],
        client_secret=creds_data['client_secret'], scopes=creds_data['scopes'],
    )
    creds.refresh(Request())
    yt = build('youtube', 'v3', credentials=creds, cache_discovery=False)

    # Get uploads playlist
    ch = yt.channels().list(part='contentDetails,statistics', mine=True).execute()
    if not ch.get('items'):
        print('EMPTY: channels.list(mine=True) вернул ответ без items — канал не виден токену '
              '(флаки YouTube API или токен чужого аккаунта). Повтори позже; если стабильно — '
              f'переавторизуй {TOKEN_FILE}.')
        return 2
    uploads_pid = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    ch_stats = ch['items'][0]['statistics']
    print(f'Channel total: {ch_stats["videoCount"]} videos, {ch_stats["subscriberCount"]} subs, {ch_stats["viewCount"]} total views')

    # Iterate
    all_vids = []
    token = None
    while True:
        resp = yt.playlistItems().list(part='snippet', playlistId=uploads_pid, maxResults=50, pageToken=token).execute()
        for it in resp.get('items', []):
            all_vids.append(it['snippet']['resourceId']['videoId'])
        token = resp.get('nextPageToken')
        if not token: break

    # Pull video stats with duration
    vids_data = []
    for i in range(0, len(all_vids), 50):
        chunk = all_vids[i:i+50]
        resp = yt.videos().list(part='snippet,contentDetails,statistics', id=','.join(chunk)).execute()
        for v in resp.get('items', []):
            cd = v.get('contentDetails', {})
            sn = v.get('snippet', {})
            st = v.get('statistics', {})
            # Parse ISO 8601 PT#M#S → seconds
            dur = cd.get('duration', 'PT0S')
            m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dur)
            if m:
                h, mi, s = m.groups()
                secs = int(h or 0)*3600 + int(mi or 0)*60 + int(s or 0)
            else:
                secs = 0
            vids_data.append({
                'vid': v['id'],
                'title': sn['title'],
                'published': sn['publishedAt'],
                'dur_s': secs,
                'views': int(st.get('viewCount', 0)),
                'likes': int(st.get('likeCount', 0)),
                'comments': int(st.get('commentCount', 0)),
            })

    shorts = [v for v in vids_data if 0 < v['dur_s'] <= 60]
    longs = [v for v in vids_data if v['dur_s'] > 60]

    print(f'\n=== Shorts (≤60s): {len(shorts)} | Long videos (>60s): {len(longs)} ===')

    # Sort shorts by views
    shorts.sort(key=lambda v: v['views'], reverse=True)
    print(f'\n=== TOP-15 shorts by views ===')
    for v in shorts[:15]:
        pub = v['published'][:10]
        print(f'  {v["views"]:>7,}  ❤{v["likes"]:>4}  💬{v["comments"]:>3}  [{pub}]  {v["title"][:65]}')

    # Stats summary
    if shorts:
        views = [v['views'] for v in shorts]
        print(f'\n=== Shorts stats summary ===')
        print(f'  Total views: {sum(views):,}')
        print(f'  Median views: {statistics.median(views):,.0f}')
        print(f'  Mean views: {statistics.mean(views):,.0f}')
        print(f'  Max views: {max(views):,}')
        print(f'  Min views: {min(views):,}')
        print(f'  Total likes: {sum(v["likes"] for v in shorts):,}')

    # Recent shorts (last 14 days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    recent_shorts = [v for v in shorts if datetime.fromisoformat(v['published'].replace('Z','+00:00')) >= cutoff]
    print(f'\n=== Recent shorts (last 14 days): {len(recent_shorts)} ===')
    recent_shorts.sort(key=lambda v: v['published'], reverse=True)
    for v in recent_shorts[:20]:
        pub = v['published'][:16].replace('T',' ')
        print(f'  [{pub}]  👁{v["views"]:>6,}  ❤{v["likes"]:>3}  {v["title"][:60]}')

    config.STATS_OUT.write_text(
        json.dumps({'shorts_count': len(shorts), 'longs_count': len(longs),
                    'recent_shorts': len(recent_shorts), 'top15': shorts[:15]},
                   ensure_ascii=False, indent=2),
        encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
