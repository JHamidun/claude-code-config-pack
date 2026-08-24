"""Full pipeline orchestrator: SRT analysis → trigger check → HeyGen Avatar V → SubMagic → cover.

Idempotent via state.json — each stage records its output and skips on re-run.

Stages per short:
  1. Read analysis (hook_3s + gist + loop_close) from $SHORTS_HOME/analysis.json
  2. Build script (hook → gist → loop_close)
  3. trigger_word_check.py --fix  (replace "pivot" → "разворот концепции" etc.)
  4. HeyGen Avatar V (3 modes selectable via --mode)
       tts          → fast TTS, risky (pivot bug)
       tts-clean    → trigger-check + TTS (default, recommended)
       real-audio   → upload pre-recorded mp3 + lipsync (свой живой голос)
  5. SubMagic (Hormozi 2, magicBrolls=FALSE, magicZooms=true, cleanAudio=true, language=ru)
  6. PIL cover via templates/cover_navy.py
  7. (Optional) YouTube upload — left to user / separate script

Cost per 30-sec short (tts modes): $0.0667 * 30 = $2.00 HeyGen + SubMagic plan
                                  пакет из 81 ролика ≈ $162 — держи на кошельке запас
                                  (баланс: heygen_avatar_v.py --check-wallet)
Cost real-audio: same HeyGen pricing — Avatar V billed per second regardless of voice type.

State file: <out-dir>/state.json
  state[key] = {
      "script": "...",        # cleaned script
      "heygen_video_id": "...",
      "heygen_url": "...",    # signed
      "raw_path": "...",
      "submagic_id": "...",
      "submagic_url": "...",
      "final_path": "...",
      "cover_path": "...",
  }

Usage:
    python full_pipeline.py <key>                              # one short
    python full_pipeline.py --batch 5 --mode tts-clean --yes   # first 5 viable
    python full_pipeline.py --all --mode real-audio --audio-dir voices/ --yes
    python full_pipeline.py <key> --resume                     # continue interrupted

Пакет (--batch/--all) требует --yes: перед стартом печатается оценка в долларах и
проверяются ключи, потому что отменить уже отрисованные ролики нельзя. Три провала
подряд рвут цикл (--max-fails) — иначе одна системная поломка оплачивается 81 раз.
"""
import sys, os, json, time, argparse, subprocess
from pathlib import Path
import urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

sys.path.insert(0, str(Path(__file__).parent))
import config

# --- Creds ---
# Ленивое чтение: `--help` и разбор аргументов должны работать без ключей.
def submagic_key(): return config.key('SUBMAGIC_API_KEY')
SUBMAGIC_BASE = 'https://api.submagic.co/v1'

THIS = Path(__file__).parent
TRIGGER_CHECK = THIS / 'trigger_word_check.py'
HEYGEN_RUNNER = THIS / 'heygen_avatar_v.py'
COVER_GEN = THIS / 'cover_gen.py'

# Default analysis + outputs (пути настраиваются через config.py / SHORTS_HOME)
DEFAULT_ANALYSIS = config.ANALYSIS
DEFAULT_OUT = config.OUT_DIR


def http(method, url, headers=None, data=None, timeout=120):
    if data is not None and not isinstance(data, (bytes, str)):
        data = json.dumps(data).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')


def build_script(v):
    """Combine hook_3s + gist + loop_close into a ≤30s spoken script."""
    hook = (v.get('hook_3s') or '').strip()
    gist = (v.get('gist') or '').strip()
    loop = (v.get('loop_close') or '').strip()
    return f'{hook} {gist} {loop}'.strip()


def clean_script(text):
    """Pipe through trigger_word_check.py --fix."""
    r = subprocess.run([sys.executable, str(TRIGGER_CHECK), '-', '--fix'],
                       input=text, capture_output=True, text=True, encoding='utf-8')
    if r.stderr.strip(): sys.stderr.write(r.stderr)
    return r.stdout


class HeyGenRunError(RuntimeError):
    """Падение раннера с уже созданным (= уже оплаченным) video_id, если он успел появиться."""
    def __init__(self, msg, video_id=''):
        super().__init__(msg)
        self.video_id = video_id


def _marker(stdout, name):
    """Достать значение метки `NAME=...` из stdout раннера ('' если метки нет)."""
    for l in (stdout or '').splitlines():
        l = l.strip()
        if l.startswith(name + '='):
            return l.split('=', 1)[1]
    return ''


def heygen_run(mode, script_text=None, audio_path=None, out_mp4=None, video_id=None):
    """Invoke heygen_avatar_v.py. Returns (video_id, signed URL); saves mp4 to out_mp4 if given.

    URL берётся из метки SIGNED_URL=, а НЕ из последней строки stdout: при --out раннер
    после ссылки печатает ещё «→ download to …» и «saved: …mp4 (NNNKB)», и старый парсер
    отдавал в SubMagic строку `saved: …` — HeyGen при этом уже был оплачен.
    """
    cmd = [sys.executable, str(HEYGEN_RUNNER), '--mode', mode]
    if video_id:
        cmd += ['--video-id', video_id]
    elif mode in ('tts', 'tts-clean'):
        if not script_text: raise ValueError(f'script_text required for {mode}')
        cmd += ['--text', script_text]
    elif mode == 'real-audio':
        if not audio_path: raise ValueError('audio_path required for real-audio')
        cmd += ['--audio', str(audio_path)]
    if out_mp4:
        cmd += ['--out', str(out_mp4), '--print-url']
    else:
        cmd += ['--print-url']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    sys.stdout.write(r.stdout or '')
    vid = _marker(r.stdout, 'VIDEO_ID') or (video_id or '')
    if r.returncode != 0:
        raise HeyGenRunError(f'HeyGen runner failed: {r.stderr[:500]}', vid)
    url = _marker(r.stdout, 'SIGNED_URL')
    if not url:
        # Раннер без меток (старая версия/подмена) — падаем громко, а не шлём мусор
        # в SubMagic: ролик уже оплачен, и молчаливая подстановка теряет эти деньги.
        raise HeyGenRunError(
            f'В stdout раннера нет метки SIGNED_URL= — не подставляю случайную строку как URL. '
            f'stderr={r.stderr[:300]}', vid)
    return vid, url


def submagic_create(video_url, title, language='ru'):
    """Hormozi 2 + magicBrolls=FALSE (KEY anti-emoji setting).

    dictionary helps recognize NEW words but does NOT fix mistranscribed common terms.
    For "pivot"→"пиво" bug — use clean script via trigger_word_check, not dictionary.
    """
    body = {
        "title": title[:100],
        "language": language,
        "videoUrl": video_url,
        "templateName": "Hormozi 2",
        "magicZooms": True,
        "magicBrolls": False,   # KEY — no emoji b-rolls (prevents 🍺 on "пиво")
        "cleanAudio": True,
        # "dictionary": ["<новый термин>"],  # только для НОВЫХ терминов; уже
        # mistranscribed слово словарь не чинит — чистим скрипт ДО TTS (gotchas §1)
    }
    st, body_text = http('POST', f'{SUBMAGIC_BASE}/projects',
                         headers={'x-api-key': submagic_key(), 'Content-Type': 'application/json'},
                         data=body)
    if st not in (200, 201):
        raise RuntimeError(f'SubMagic create {st}: {body_text[:500]}')
    j = json.loads(body_text)
    return j.get('id') or j.get('projectId') or j.get('project_id')


def submagic_wait(project_id, max_wait_min=20):
    deadline = time.time() + max_wait_min * 60
    while time.time() < deadline:
        st, body = http('GET', f'{SUBMAGIC_BASE}/projects/{project_id}',
                        headers={'x-api-key': submagic_key()})
        if st != 200:
            print(f'  poll {st}'); time.sleep(20); continue
        j = json.loads(body)
        s = j.get('status')
        if s == 'completed':
            return j.get('downloadUrl') or j.get('download_url') or j.get('outputUrl') or j.get('directUrl')
        if s == 'failed':
            raise RuntimeError(f'SubMagic failed: {j.get("error") or j.get("failureReason")}')
        print(f'    submagic: {s}...', flush=True)
        time.sleep(20)
    raise TimeoutError(f'SubMagic timeout {max_wait_min}min')


def download(url, out_path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as r, open(out_path, 'wb') as f:
        while True:
            chunk = r.read(64 * 1024)
            if not chunk: break
            f.write(chunk)


def load_state(state_file):
    if state_file.exists():
        return json.loads(state_file.read_text(encoding='utf-8'))
    return {}


def save_state(state_file, state):
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


# HeyGen Avatar V биллит $0.0667/сек; целевая длина ролика ~30 сек → ~$2.00 за штуку.
COST_PER_SHORT_USD = 2.00


def preflight(n_shorts, args):
    """Отказ ДО первого платного вызова + печать оценки стоимости пакета.

    SUBMAGIC_API_KEY проверяется здесь, а не на 3-м шаге: к тому моменту HeyGen уже
    оплачен, и пустой ключ означал бы ~$2 за ролик в мусор — по разу на каждый ролик пакета.
    """
    # config.key() сам печатает, где взять каждый ключ, и падает с понятным текстом.
    for name in ('HEYGEN_API_KEY', 'HEYGEN_AVATAR_ID', 'HEYGEN_VOICE_ID', 'SUBMAGIC_API_KEY'):
        config.key(name)
    est = n_shorts * COST_PER_SHORT_USD
    print(f'ОЦЕНКА: {n_shorts} шортсов x ~${COST_PER_SHORT_USD:.2f} = ~${est:.2f} HeyGen '
          f'(Avatar V, ~30 сек/ролик). Баланс: heygen_avatar_v.py --check-wallet')
    if est > args.max_cost:
        raise SystemExit(f'ОТКАЗ: ~${est:.2f} превышает потолок --max-cost ${args.max_cost:.2f}. '
                         f'Уменьши --batch или подними потолок осознанно.')
    if not args.yes:
        raise SystemExit('ОТКАЗ: пакетный прогон платный и необратимый. Сверь оценку выше '
                         'с балансом и повтори с --yes.')


def process_one(key, analysis, args):
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / 'heygen_raw'; raw_dir.mkdir(exist_ok=True)
    final_dir = out_dir / 'submagic_final'; final_dir.mkdir(exist_ok=True)
    covers_dir = out_dir / 'covers'; covers_dir.mkdir(exist_ok=True)
    state_file = out_dir / 'state.json'

    state = load_state(state_file)
    rec = state.setdefault(key, {})

    v = analysis.get(key) or analysis.get(key.replace('__', '/'))
    if not v:
        print(f'  SKIP {key}: not in analysis'); return None
    if not v.get('keep'):
        print(f'  SKIP {key}: keep=false ({v.get("skip_reason","?")})'); return None

    # 1. Script
    if not rec.get('script'):
        script = build_script(v)
        if args.mode == 'tts-clean':
            script = clean_script(script)
        rec['script'] = script
        save_state(state_file, state)
    print(f'  Script: "{rec["script"][:140]}..."')

    safe = key.replace('/', '__')

    # 2. HeyGen
    raw_mp4 = raw_dir / f'{safe}.mp4'
    if not rec.get('heygen_url'):
        # Уже оплаченный ролик прошлого запуска (упал поллинг/скачивание) — забираем его,
        # а не заказываем новый: HeyGen списывает за генерацию, не за скачивание.
        paid_vid = rec.get('heygen_video_id') or None
        if paid_vid:
            print(f'  → HeyGen resume оплаченного video_id={paid_vid}')
        try:
            if paid_vid:
                vid, url = heygen_run(args.mode, out_mp4=raw_mp4, video_id=paid_vid)
            elif args.mode == 'real-audio':
                audio = Path(args.audio_dir) / f'{safe}.mp3' if args.audio_dir else None
                if not audio or not audio.exists():
                    print(f'  SKIP {key}: real-audio mode needs {audio}'); return None
                print(f'  → HeyGen real-audio: {audio.name}')
                vid, url = heygen_run('real-audio', audio_path=audio, out_mp4=raw_mp4)
            else:
                print(f'  → HeyGen {args.mode}')
                vid, url = heygen_run(args.mode, script_text=rec['script'], out_mp4=raw_mp4)
        except HeyGenRunError as e:
            if e.video_id:
                # Ролик отрисован и списан, но забрать не вышло. Без записи id повторный
                # запуск закажет новый и заплатит второй раз — пишем в state и кричим.
                rec['heygen_video_id'] = e.video_id
                save_state(state_file, state)
                print(f'  !! ОПЛАЧЕНО, НО НЕ ЗАБРАНО: video_id={e.video_id} сохранён в '
                      f'{state_file}. Следующий запуск подхватит его без второй оплаты.')
            raise
        rec['heygen_video_id'] = vid
        rec['heygen_url'] = url
        rec['raw_path'] = str(raw_mp4)
        save_state(state_file, state)
    else:
        print(f'  ✓ HeyGen cached: {rec["heygen_url"][:60]}...')

    # 3. SubMagic
    if not rec.get('submagic_id'):
        print(f'  → SubMagic create (Hormozi 2, magicBrolls=False)')
        rec['submagic_id'] = submagic_create(rec['heygen_url'], v.get('title', key))
        save_state(state_file, state)
    if not rec.get('submagic_url'):
        print(f'  → SubMagic wait')
        rec['submagic_url'] = submagic_wait(rec['submagic_id'])
        save_state(state_file, state)

    final_mp4 = final_dir / f'{safe}.mp4'
    if not final_mp4.exists():
        print(f'  → download final to {final_mp4}')
        download(rec['submagic_url'], final_mp4)
    rec['final_path'] = str(final_mp4)
    save_state(state_file, state)

    # 4. Cover
    cover_png = covers_dir / f'{safe}.png'
    if not cover_png.exists():
        print(f'  → cover')
        subprocess.run([sys.executable, str(COVER_GEN),
                        '--title', v.get('title') or v.get('on_screen_text') or 'AI NEWS',
                        '--out', str(cover_png)], check=False)
    rec['cover_path'] = str(cover_png)
    save_state(state_file, state)

    print(f'  ✓ {key} done')
    print(f'      final: {final_mp4}')
    print(f'      cover: {cover_png}')
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('key', nargs='?', default=None, help='Short key (e.g. 0HCAhzgS27Y/short_01)')
    ap.add_argument('--batch', type=int, help='First N viable shorts')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--mode', choices=['tts', 'tts-clean', 'real-audio'], default='tts-clean')
    ap.add_argument('--audio-dir', help='Dir of pre-recorded mp3s (real-audio mode). File <safe_key>.mp3')
    ap.add_argument('--analysis', default=str(DEFAULT_ANALYSIS), help='Analysis JSON from analyze_srt.py')
    ap.add_argument('--out-dir', default=str(DEFAULT_OUT))
    ap.add_argument('--yes', action='store_true',
                    help='Подтвердить платный пакетный прогон (обязателен для --batch/--all)')
    ap.add_argument('--max-cost', type=float, default=200.0,
                    help='Потолок оценки HeyGen в USD на пакет (по умолчанию 200 — чуть выше '
                         'полного прогона 81x$2=$162; ловит разросшийся analysis.json)')
    ap.add_argument('--max-fails', type=int, default=3,
                    help='Стоп после N провалов подряд (по умолчанию 3): системная поломка '
                         'не лечится следующим роликом, а каждый ролик стоит денег')
    args = ap.parse_args()

    if not Path(args.analysis).exists():
        print(f'No analysis at {args.analysis}. Run: python analyze_srt.py'); sys.exit(2)
    analysis = json.load(open(args.analysis, encoding='utf-8'))

    if args.all or args.batch:
        viable = sorted([k for k, v in analysis.items() if v.get('keep')])
        todo = viable if args.all else viable[:args.batch]
        preflight(len(todo), args)
        print(f'Processing {len(todo)} shorts in mode={args.mode}')
        ok = fail = streak = 0
        for k in todo:
            try:
                process_one(k, analysis, args)
                ok += 1
                streak = 0
            except Exception as e:
                print(f'  FAIL {k}: {e}')
                fail += 1
                streak += 1
                # Протухший ключ, отвалившийся SubMagic, сменившийся контракт раннера —
                # всё это повторится и на следующем ролике, но HeyGen за каждый уже спишет.
                if streak >= args.max_fails:
                    print(f'\nСТОП: {streak} провала подряд, дальше каждый ролик — это ещё '
                          f'~${COST_PER_SHORT_USD:.2f} HeyGen впустую. Разбери причину: {e}')
                    break
        print(f'\n=== Done. OK={ok} FAIL={fail} ===')
    elif args.key:
        process_one(args.key, analysis, args)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
