"""HeyGen Avatar V generator для ТВОЕГО digital twin — 3 режима.

Avatar: $HEYGEN_AVATAR_ID  (твой digital twin; аватар должен быть Avatar V eligible)
Voice:  $HEYGEN_VOICE_ID  (твой основной голос; запасной — аргументом --voice-id)
Voice:  $HEYGEN_VOICE_ID  (кабинет HeyGen → Voices → Copy ID)

Pricing: $0.0667/sec talking head  →  $2.00 per 30-sec short  →  $162 for 81 shorts
Wallet check: GET /v1/user/remaining_quota  (returns USD cents)

Three modes:
  1. tts           — HeyGen Russian TTS. Fast, cheap, but reads "pivot" → "пиво".
  2. tts-clean     — Run trigger_word_check.py --fix BEFORE sending to HeyGen TTS.
                     Removes "pivot"/"roadmap"/etc — safest TTS mode.
  3. real-audio    — Upload pre-recorded audio via /v3/assets, then lipsync via avatar.
                     Твой настоящий голос, идеальное произношение, но SubMagic всё равно
                     transcribes the audio and may caption "pivot" → "пиво". Use clean
                     script + matching audio recording for best results.

Usage:
    python heygen_avatar_v.py --mode tts        --text "..." --out raw.mp4
    python heygen_avatar_v.py --mode tts-clean  --text-file script.txt --out raw.mp4
    python heygen_avatar_v.py --mode real-audio --audio voice.mp3 --out raw.mp4
    python heygen_avatar_v.py --video-id <id> --out raw.mp4   # забрать УЖЕ оплаченное видео
    python heygen_avatar_v.py --check-wallet

Stdout-контракт для вызывающих скриптов (full_pipeline.py):
    VIDEO_ID=<id>       печатается сразу после создания — это чек об оплате
    SIGNED_URL=<url>    печатается после готовности
Парсить надо метки, а не «последнюю строку»: при --out после URL идут ещё строки
про скачивание.
"""
import sys, os, time, json, argparse, subprocess
from pathlib import Path
import urllib.request, urllib.error
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

sys.path.insert(0, str(Path(__file__).parent))
import config

# --- Creds и идентификаторы ---
# Ленивое чтение, а не константы на импорте: иначе `--help` и `--check-wallet`
# падали бы у того, кто ещё не завёл аватар.
# Аватар и голос — ТВОИ, из кабинета HeyGen (Avatars / Voices → Copy ID).
# Дефолта здесь нет и быть не может: чужой avatar_id либо не пройдёт авторизацию,
# либо (хуже) отрисует чужое лицо за твои деньги.
def heygen_key():    return config.key('HEYGEN_API_KEY')
def avatar_id():     return config.key('HEYGEN_AVATAR_ID')
def default_voice(): return config.key('HEYGEN_VOICE_ID')

BASE = 'https://api.heygen.com'

THIS = Path(__file__).parent
TRIGGER_CHECK = THIS / 'trigger_word_check.py'


def http(method, url, headers=None, data=None, timeout=120):
    """Simple HTTP. Returns (status, body_text)."""
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


def check_wallet():
    """GET /v1/user/remaining_quota — returns wallet info."""
    st, body = http('GET', f'{BASE}/v1/user/remaining_quota',
                    headers={'X-Api-Key': heygen_key()})
    if st != 200:
        print(f'wallet check {st}: {body[:300]}'); return None
    j = json.loads(body)
    print(f'HeyGen wallet: {json.dumps(j.get("data", j), ensure_ascii=False, indent=2)}')
    return j


def clean_text(text):
    """Pipe text through trigger_word_check.py --fix."""
    if not TRIGGER_CHECK.exists():
        print(f'WARN: {TRIGGER_CHECK} missing — skipping clean')
        return text
    r = subprocess.run([sys.executable, str(TRIGGER_CHECK), '-', '--fix'],
                       input=text, capture_output=True, text=True, encoding='utf-8')
    # stderr has warnings about replacements
    if r.stderr.strip():
        sys.stderr.write(r.stderr)
    return r.stdout


def heygen_create_tts(script_text, voice_id=None):
    voice_id = voice_id or default_voice()
    """Mode 1/2: HeyGen TTS Avatar V. Returns video_id."""
    body = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id(),
                "avatar_style": "normal",
            },
            "voice": {
                "type": "text",
                "input_text": script_text,
                "voice_id": voice_id,
                "speed": 1.0,
            },
        }],
        "dimension": {"width": 1080, "height": 1920},  # 9:16, 1080p
        "aspect_ratio": "9:16",
        "engine": {"type": "avatar_v"},
        "test": False,
    }
    st, body_text = http('POST', f'{BASE}/v2/video/generate',
                         headers={'X-Api-Key': heygen_key(), 'Content-Type': 'application/json'},
                         data=body)
    if st != 200:
        raise RuntimeError(f'HeyGen create {st}: {body_text[:500]}')
    return json.loads(body_text)['data']['video_id']


def heygen_upload_asset(audio_path):
    """Mode 3: POST /v3/assets — upload audio file. Returns asset_id."""
    audio = Path(audio_path).read_bytes()
    ext = Path(audio_path).suffix.lower().lstrip('.')
    ctype = {'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'm4a': 'audio/mp4', 'aac': 'audio/aac'}.get(ext, 'audio/mpeg')
    st, body = http('POST', f'{BASE}/v3/assets',
                    headers={'X-Api-Key': heygen_key(), 'Content-Type': ctype},
                    data=audio, timeout=300)
    if st not in (200, 201):
        raise RuntimeError(f'HeyGen asset upload {st}: {body[:500]}')
    j = json.loads(body)
    # Response shape: {"data": {"id": "...", "url": "..."}} or flat
    aid = (j.get('data') or {}).get('id') or j.get('id') or j.get('asset_id')
    if not aid:
        raise RuntimeError(f'No asset_id in: {body[:300]}')
    return aid


def heygen_create_audio_lipsync(audio_asset_id):
    """Mode 3: Avatar V + uploaded audio (lipsync to real recording). Returns video_id."""
    body = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id(),
                "avatar_style": "normal",
            },
            "voice": {
                "type": "audio",
                "audio_asset_id": audio_asset_id,
            },
        }],
        "dimension": {"width": 1080, "height": 1920},
        "aspect_ratio": "9:16",
        "engine": {"type": "avatar_v"},
        "test": False,
    }
    st, body_text = http('POST', f'{BASE}/v2/video/generate',
                         headers={'X-Api-Key': heygen_key(), 'Content-Type': 'application/json'},
                         data=body)
    if st != 200:
        raise RuntimeError(f'HeyGen audio-lipsync create {st}: {body_text[:500]}')
    return json.loads(body_text)['data']['video_id']


def heygen_wait(video_id, max_wait_min=15, poll_every=15):
    """Poll until ready. Returns signed download URL."""
    deadline = time.time() + max_wait_min * 60
    while time.time() < deadline:
        st, body = http('GET', f'{BASE}/v1/video_status.get?video_id={video_id}',
                        headers={'X-Api-Key': heygen_key()})
        if st != 200:
            print(f'  poll {st}'); time.sleep(poll_every); continue
        j = json.loads(body)
        d = j.get('data', {})
        status = d.get('status')
        if status == 'completed':
            return d['video_url']
        if status == 'failed':
            raise RuntimeError(f'HeyGen failed: {d.get("error", "unknown")}')
        print(f'    heygen: {status}...', flush=True)
        time.sleep(poll_every)
    raise TimeoutError(f'HeyGen timeout {max_wait_min}min')


def download(url, out_path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=300) as r, open(out_path, 'wb') as f:
        while True:
            chunk = r.read(64 * 1024)
            if not chunk: break
            f.write(chunk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['tts', 'tts-clean', 'real-audio'], default='tts-clean')
    ap.add_argument('--text', help='Inline script text (tts/tts-clean)')
    ap.add_argument('--text-file', help='Script file path (tts/tts-clean)')
    ap.add_argument('--audio', help='Pre-recorded audio path (real-audio mode)')
    ap.add_argument('--voice-id', default=None,
                    help='HeyGen voice_id; по умолчанию $HEYGEN_VOICE_ID. '
                         'Второй голос удобно держать в окружении и передавать явно, '
                         'если основной звучит «роботом»')
    ap.add_argument('--out', required=False, help='Output mp4 path (omit to print URL only)')
    ap.add_argument('--check-wallet', action='store_true')
    ap.add_argument('--print-url', action='store_true', help='Print signed URL even if --out given')
    ap.add_argument('--video-id', help='Подхватить УЖЕ созданное (и уже оплаченное) видео '
                                       'вместо генерации нового — если прошлый запуск упал на '
                                       'поллинге или скачивании. Без него это вторая оплата.')
    args = ap.parse_args()

    if args.check_wallet:
        check_wallet(); return

    if args.video_id:
        # Ролик уже отрисован и списан с кошелька: заново создавать его — платить дважды.
        print(f'  → HeyGen resume существующего video_id (без новой оплаты)')
        vid = args.video_id
    elif args.mode in ('tts', 'tts-clean'):
        if args.text:
            text = args.text
        elif args.text_file:
            text = Path(args.text_file).read_text(encoding='utf-8')
        else:
            ap.error('--text or --text-file required for TTS modes')
        if args.mode == 'tts-clean':
            print('  Running trigger-word check + clean...')
            text = clean_text(text)
            print(f'  Cleaned script: "{text[:160]}..."')
        print('  → HeyGen create (TTS Avatar V)')
        vid = heygen_create_tts(text, args.voice_id)
    elif args.mode == 'real-audio':
        if not args.audio:
            ap.error('--audio required for real-audio mode')
        print(f'  → HeyGen upload asset: {args.audio}')
        aid = heygen_upload_asset(args.audio)
        print(f'    asset_id = {aid}')
        print('  → HeyGen create (audio lipsync Avatar V)')
        vid = heygen_create_audio_lipsync(aid)
    else:
        raise SystemExit(f'unknown mode {args.mode}')

    print(f'    video_id = {vid}')
    # Машиночитаемая метка. С этого момента ролик ОПЛАЧЕН, даже если дальше упадёт
    # поллинг или скачивание: id — единственный способ забрать его без второй оплаты
    # (`--video-id`). Раньше id жил только в человекочитаемой строке выше и терялся.
    print(f'VIDEO_ID={vid}', flush=True)
    print('  → HeyGen wait (poll)')
    url = heygen_wait(vid)
    print(f'    ready: {url[:80]}...')
    # Метка для вызывающего: раньше full_pipeline угадывал URL как «последнюю строку
    # stdout» и при --out забирал строку `saved: ...mp4` вместо ссылки.
    print(f'SIGNED_URL={url}', flush=True)

    if args.print_url or not args.out:
        print(url)
    if args.out:
        print(f'  → download to {args.out}')
        download(url, args.out)
        print(f'    saved: {args.out} ({Path(args.out).stat().st_size/1024:.0f}KB)')


if __name__ == '__main__':
    main()
