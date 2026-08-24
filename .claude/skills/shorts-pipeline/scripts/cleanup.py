"""Чистка shorts на СВОЁМ YouTube-канале (канал определяется токеном, mine=True).

Two modes:
  1. --action plan       — show what would be deleted (no API calls)
  2. --action delete     — actually delete using fresh inventory candidates
  3. --action delete-old — delete using legacy cleanup logic (empty/zero/duplicates)
  4. --action hashtags   — add hashtags to remaining shorts descriptions

Замер на живом канале:
  - 44 shorts удалено за один прогон (0 просмотров >7д + <100 просмотров >14д)
  - осталось 401, медиана выросла с 707 до 732 просмотров
  - YT quota: videos.delete = 50/call, videos.update = 50/call
  - Daily budget ~10K quota = 200 deletes OR 200 updates

Usage:
    python cleanup.py --action plan
    python cleanup.py --action delete --yes --limit 50
    python cleanup.py --action hashtags --limit 200

Удаление необратимо, поэтому delete/delete-old требуют --yes и свежего снимка
(inventory.py не старше 24 ч): критерий «0 просмотров >7 дней» верен только на момент
снимка, а за сутки ролик может залететь. Протухший снимок — либо обновить, либо
--allow-stale осознанно. --limit ограничивает и удаление, и хэштеги.
"""
import json, sys, time, argparse
from pathlib import Path
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

# Кандидаты считаются по просмотрам на момент inventory.py. Ролик из «0 просмотров >7 дней»
# за сутки может залететь — удаление с YouTube необратимо, восстановить нечем.
CANDS_MAX_AGE_H = 24

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).parent))
import config

TOKEN = config.YT_TOKEN
SHORTS_FILE = config.CHANNEL_SNAPSHOT
CANDS = config.CLEANUP_CANDIDATES
PROG = config.CLEANUP_PROGRESS

# Свои хэштеги задаются переменной SHORTS_HASHTAGS. Пусто — режим hashtags
# ничего не дописывает и честно об этом говорит, вместо чужого набора тегов.
HASHTAGS = ('\n\n' + config.HASHTAGS) if config.HASHTAGS else ''


def get_yt():
    cd = json.load(open(TOKEN))
    creds = Credentials(token=cd['token'], refresh_token=cd['refresh_token'],
                       token_uri=cd['token_uri'], client_id=cd['client_id'],
                       client_secret=cd['client_secret'], scopes=cd['scopes'])
    creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds, cache_discovery=False)


def load_progress() -> dict:
    if PROG.exists() and PROG.stat().st_size > 0:
        try:
            return json.loads(PROG.read_text(encoding='utf-8'))
        except Exception as e:
            # Раньше битый файл молча превращался в пустой прогресс: список уже удалённых
            # и уже обновлённых терялся, и следующий прогон жёг квоту заново (50 ед. за
            # videos.update). Отказываемся, а не «начинаем с чистого листа» втихую.
            raise SystemExit(f'ОТКАЗ: {PROG} не читается как JSON ({e}). Это журнал уже '
                             f'удалённого и обновлённого — почини или отложи файл в сторону '
                             f'осознанно, начинать с нуля молча нельзя.')
    return {'deleted': [], 'updated': []}


def load_candidates(max_age_h=CANDS_MAX_AGE_H, allow_stale=False):
    """Кандидаты на удаление + отказ, если снимок протух.

    Возраст важен по-настоящему: критерий «0 просмотров старше 7 дней» верен только на
    момент inventory.py, а videos.delete необратим — по вчерашнему списку можно снести
    ролик, который сегодня уже набрал просмотры.
    """
    if not CANDS.exists():
        raise SystemExit(f'ОТКАЗ: нет файла кандидатов {CANDS}. Сначала: python inventory.py')
    age_h = (time.time() - CANDS.stat().st_mtime) / 3600
    print(f'Кандидаты: {CANDS} (снимку {age_h:.1f} ч)')
    if age_h > max_age_h and not allow_stale:
        raise SystemExit(f'ОТКАЗ: снимку {age_h:.1f} ч > {max_age_h} ч. Просмотры с тех пор '
                         f'выросли, а удаление необратимо. Обнови: python inventory.py '
                         f'(или --allow-stale, если точно знаешь что делаешь).')
    return json.load(open(CANDS, encoding='utf-8'))


def save_progress(p: dict):
    PROG.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding='utf-8')


def delete_fresh(yt, prog, cands, limit):
    """Delete shorts from fresh inventory candidates (не более `limit` за прогон)."""
    todo = [c for c in cands if c['id'] not in prog['deleted']]
    print(f'Total candidates: {len(cands)}, already deleted: {len(prog["deleted"])}, todo: {len(todo)}')
    if len(todo) > limit:
        print(f'  ограничение --limit: за прогон удалим {limit} из {len(todo)}')
        todo = todo[:limit]

    ok, fail = 0, 0
    for c in todo:
        vid = c['id']
        print(f'  DEL {vid}  v={c.get("views",0):>4}  | {c.get("_reason","?"):<18} | {c.get("title","")[:55]}', flush=True)
        try:
            yt.videos().delete(id=vid).execute()
            prog['deleted'].append(vid)
            save_progress(prog)
            ok += 1
            time.sleep(0.8)
        except Exception as e:
            err = str(e)[:200]
            if 'quotaExceeded' in err:
                print(f'  QUOTA EXCEEDED at {ok} — saved + exit'); break
            elif '404' in err:
                prog['deleted'].append(vid); save_progress(prog)
                print(f'    404 (already gone) — marked deleted'); ok += 1
            else:
                print(f'    FAIL: {err[:160]}'); fail += 1

    print(f'\n=== Run done. Deleted {ok}, failed {fail}. Total: {len(prog["deleted"])} ===')


def delete_old_logic(yt, prog, shorts, limit=200):
    """Delete by legacy logic: empty transcript + 0 views + duplicates (не более `limit`)."""
    to_del = []
    for s in shorts:
        t = (s.get('title') or '').strip()
        if t == 'Пустой транскрипт':
            to_del.append((s['id'], 'empty', s))
        elif (s.get('viewCountInt') or s.get('views') or 0) == 0:
            to_del.append((s['id'], '0views', s))

    by_title = {}
    for s in shorts:
        t = (s.get('title') or '').strip()
        if not t or t == 'Пустой транскрипт': continue
        by_title.setdefault(t, []).append(s)
    for t, group in by_title.items():
        if len(group) > 1:
            group.sort(key=lambda x: x.get('viewCountInt') or x.get('views') or 0, reverse=True)
            for dup in group[1:]:
                to_del.append((dup['id'], f'dup→{group[0]["id"]}', dup))

    seen = set(); uniq = []
    for vid, r, s in to_del:
        if vid not in seen: seen.add(vid); uniq.append((vid, r, s))

    print(f'Delete candidates: {len(uniq)} (потолок за прогон: {limit})')
    done = 0
    for vid, reason, s in uniq:
        if vid in prog['deleted']: continue
        if done >= limit:
            print(f'  ограничение --limit: остановились на {done}, остальное — следующим прогоном')
            break
        print(f'  DEL {vid} | {reason} | "{(s.get("title") or "")[:50]}"', flush=True)
        try:
            yt.videos().delete(id=vid).execute()
            prog['deleted'].append(vid); save_progress(prog); done += 1; time.sleep(1)
        except Exception as e:
            err = str(e)[:200]
            if 'quotaExceeded' in err:
                print('QUOTA — exit'); return
            elif '404' in err:
                prog['deleted'].append(vid); save_progress(prog)
            else: print(f'    FAIL: {err[:150]}')


def hashtags_phase(yt, prog, shorts, limit=200):
    """Add hashtags to remaining shorts descriptions."""
    deleted = set(prog['deleted'])
    # Пустой набор тегов означал бы «дописать в описание ничего» — но с расходом квоты
    # на videos.update по каждому ролику. Отказываем сразу и говорим, где задать.
    if not HASHTAGS.strip():
        raise SystemExit('ОТКАЗ: не задан SHORTS_HASHTAGS — дописывать в описания нечего.\n'
                         '  export SHORTS_HASHTAGS="#тег1 #тег2 #тег3"')

    todo = [s for s in shorts
            if s['id'] not in deleted
            and s['id'] not in prog['updated']
            and (s.get('title') or '').strip() not in ('Пустой транскрипт',)]
    print(f'Hashtags todo: {len(todo)}, limit: {limit}')

    cnt = 0
    for s in todo:
        if cnt >= limit: break
        vid = s['id']
        old_desc = s.get('description') or ''
        if HASHTAGS.strip() in old_desc:
            prog['updated'].append(vid); continue
        new_desc = (old_desc.rstrip() + HASHTAGS)[:5000]
        try:
            cur = yt.videos().list(part='snippet', id=vid).execute()
            if not cur['items']:
                prog['updated'].append(vid); continue
            snip = cur['items'][0]['snippet']
            snip['description'] = new_desc
            yt.videos().update(part='snippet', body={'id': vid, 'snippet': snip}).execute()
            prog['updated'].append(vid); cnt += 1
            if cnt % 10 == 0: save_progress(prog); print(f'  {cnt}/{limit}...', flush=True)
            time.sleep(0.5)
        except Exception as e:
            err = str(e)[:200]
            if 'quotaExceeded' in err:
                print(f'QUOTA at {cnt}'); save_progress(prog); return
            elif '404' in err: prog['updated'].append(vid)
            else: print(f'  FAIL {vid}: {err[:120]}')
    save_progress(prog)
    print(f'  Updated {cnt} this run')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--action', choices=['plan', 'delete', 'delete-old', 'hashtags'], default='plan')
    ap.add_argument('--limit', type=int, default=200,
                    help='Потолок операций за прогон (delete + hashtags). YT-квота: 50 ед. за операцию')
    ap.add_argument('--threshold', type=int, default=100, help='View threshold for low-views (info only — uses inventory candidates)')
    ap.add_argument('--yes', action='store_true',
                    help='Подтвердить УДАЛЕНИЕ роликов (обязателен для delete/delete-old). '
                         'Удаление с YouTube необратимо')
    ap.add_argument('--allow-stale', action='store_true',
                    help=f'Разрешить работу по снимку кандидатов старше {CANDS_MAX_AGE_H} ч')
    args = ap.parse_args()

    prog = load_progress()

    if args.action == 'plan':
        if CANDS.exists():
            cands = json.load(open(CANDS, encoding='utf-8'))
            todo = [c for c in cands if c['id'] not in prog['deleted']]
            print(f'PLAN (fresh candidates):')
            print(f'  candidates total: {len(cands)}')
            print(f'  already deleted: {len(prog["deleted"])}')
            print(f'  todo: {len(todo)}')
            for c in todo[:30]:
                print(f'    {c["id"]} v={c.get("views",0):>4} | {c.get("_reason","?"):<18} | {c.get("title","")[:55]}')
        else:
            print('No candidates file. Run: python inventory.py')
        return

    # Гейт для необратимого: сколько именно роликов уйдёт и с чьего ведома.
    # Раньше `--action delete` начинал сносить сразу, без подтверждения и без потолка.
    if args.action in ('delete', 'delete-old'):
        if args.action == 'delete':
            cands = load_candidates(allow_stale=args.allow_stale)
            n = len([c for c in cands if c['id'] not in prog['deleted']])
        else:
            if not SHORTS_FILE.exists():
                raise SystemExit(f'ОТКАЗ: нет {SHORTS_FILE}. Сначала: python inventory.py')
            age_h = (time.time() - SHORTS_FILE.stat().st_mtime) / 3600
            print(f'Снимок канала: {SHORTS_FILE} ({age_h:.1f} ч)')
            if age_h > CANDS_MAX_AGE_H and not args.allow_stale:
                raise SystemExit(f'ОТКАЗ: снимку {age_h:.1f} ч > {CANDS_MAX_AGE_H} ч, а удаление '
                                 f'необратимо. Обнови: python inventory.py (или --allow-stale).')
            shorts = json.loads(SHORTS_FILE.read_text(encoding='utf-8'))
            n = None
        if n is not None:
            print(f'К УДАЛЕНИЮ: {min(n, args.limit)} роликов (всего в очереди {n}, '
                  f'потолок --limit {args.limit}). Восстановить их с YouTube нельзя.')
        if not args.yes:
            raise SystemExit('ОТКАЗ: удаление необратимо. Сверь список '
                             '(`--action plan`) и повтори с --yes.')

    yt = get_yt()

    if args.action == 'delete':
        delete_fresh(yt, prog, cands, args.limit)
    elif args.action == 'delete-old':
        delete_old_logic(yt, prog, shorts, args.limit)
    elif args.action == 'hashtags':
        if not SHORTS_FILE.exists():
            print('Run inventory.py first'); return
        shorts = json.loads(SHORTS_FILE.read_text(encoding='utf-8'))
        hashtags_phase(yt, prog, shorts, args.limit)


if __name__ == '__main__':
    main()
