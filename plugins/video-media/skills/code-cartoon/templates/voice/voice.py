"""Voice the cartoon script with an ElevenLabs voice on Eleven v4 and keep word timings for timing/build_timing.py.

    python voice/voice.py voice --dry-run          # print what will be spoken (brands respelled, pairs applied), no API call
    python voice/voice.py voice --takes 3          # reads voice/script.txt, writes voice.mp3, voice.wav, alignment.json, words.json
    python voice/voice.py voice --force            # regenerate even if voice.mp3 exists (costs credits)

The voice: --voice-id, else the environment variable ELEVENLABS_VOICE_ID, else the key named by --voice-key (default
ELEVENLABS_VOICE_ID) in ~/.claude/.credentials.master.env. The API key: ELEVENLABS_API_KEY from the environment or that file.
script.txt is the DISPLAY text (what the captions show). What the voice must say differently is written as {display|spoken}:
  «за {11,4 млн|одиннадцать и четыре десятых миллиона} аккаунтов». Brand names are respelled automatically (BRANDS).
  Digits outside a pair are refused: v4 reads numbers well, but the case endings must be decided by a human.
Eleven v4 (eleven_v4) takes a professional (PVC) voice without fine-tuning and returns character timings via
/with-timestamps (checked 01.10.2026); settings: stability 0.5, language_code ru, mp3 44.1 kHz 192 kbps.
--takes N > 1 keeps the take with the fewest stress problems (stress_audit.py: RUAccent + a phoneme recognizer; needs
pip install ruaccent transformers torch librosa huggingface_hub — without them every take scores 0 and take 0 is kept).
"""
import base64
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

CRED = Path.home() / '.claude/.credentials.master.env'
VOICE = None                            # resolved in main(): --voice-id / ELEVENLABS_VOICE_ID / --voice-key in CRED
MODEL = 'eleven_v4'
SETTINGS = {'stability': 0.5}
LANG = 'ru'
FMT = 'mp3_44100_192'
PUNCT_ONLY = re.compile(r'^[—–\-.,!?:;…«»"„“”()]+$')

# display token -> spoken form, longest first (word-bounded, case-sensitive)
BRANDS = [
    ('Claude Code', 'Клод Код'), ('Claude Sonnet', 'Клод Сонет'), ('Claude Opus', 'Клод Опус'),
    ('claude.ai', 'клод точка эй-ай'), ('Claude.ai', 'Клод точка эй-ай'), ('Claude', 'Клод'), ('ChatGPT', 'ЧатДжипити'),
    ('Codex', 'Кодекс'), ('Anthropic', 'Антропик'), ('VS Code', 'Ви-Эс Код'), ('Visual Studio Code', 'Вижуал Студио Код'),
    ('Remote Control', 'Ремоут Контрол'), ('Switch account', 'Свитч аккаунт'), ('Transparency Hub', 'Транспаренси Хаб'),
    ('OpenCode', 'ОупенКод'), ('OpenClaw', 'ОупенКлоу'), ('GitHub', 'ГитХаб'), ('Google', 'Гугл'), ('Gmail', 'Джимейл'),
    ('Telegram', 'Телеграм'), ('Habr', 'Хабр'), ('API', 'эй-пи-ай'), ('VPN', 'ВПН'), ('Max', 'Макс'), ('Pro', 'Про'),
    ('PDF', 'ПДФ'), ('Word', 'Ворд'), ('Excel', 'Эксель'), ('Perplexity', 'Перплексити'), ('Gemini', 'Джемини'),
]
BRAND_RE = re.compile('|'.join(r'(?<![\w.])' + re.escape(a) + r'(?![\w])' for a, _ in sorted(BRANDS, key=lambda p: -len(p[0]))))
BRAND_MAP = dict(BRANDS)
PAIR_RE = re.compile(r'\{([^{}|]+)\|([^{}]+)\}')


def cred(name):
    """A value from the environment, else from ~/.claude/.credentials.master.env; None when absent."""
    if os.environ.get(name):
        return os.environ[name].strip()
    if CRED.exists():
        for line in CRED.read_text(encoding='utf-8').splitlines():
            if line.startswith(name + '='):
                return line.split('=', 1)[1].strip().strip('"').strip("'") or None
    return None


def key():
    k = cred('ELEVENLABS_API_KEY')
    if not k:
        raise SystemExit(f'ELEVENLABS_API_KEY missing (environment or {CRED})')
    return k


def pieces(script):
    """[(display, spoken, same?)] covering the whole script in order."""
    out = []

    def plain(seg):
        pos = 0
        for m in BRAND_RE.finditer(seg):
            if m.start() > pos:
                out.append((seg[pos:m.start()], seg[pos:m.start()], True))
            out.append((m.group(0), BRAND_MAP[m.group(0)], False))
            pos = m.end()
        if pos < len(seg):
            out.append((seg[pos:], seg[pos:], True))

    pos = 0
    for m in PAIR_RE.finditer(script):
        plain(script[pos:m.start()])
        out.append((m.group(1), m.group(2), False))
        pos = m.end()
    plain(script[pos:])
    bad = [p[0] for p in out if p[2] and re.search(r'\d', p[0])]
    if bad:
        raise SystemExit('digits outside {display|spoken} pairs — decide how they are read: ' + ' | '.join(b.strip()[:60] for b in bad))
    return out


def char_times(spoken, al):
    """Start/end time for every character of `spoken`, matching ElevenLabs' alignment characters (normally identical)."""
    chars = ''.join(al['characters'])
    st, en = al['character_start_times_seconds'], al['character_end_times_seconds']
    if chars == spoken:
        return st, en
    sm = difflib.SequenceMatcher(a=spoken, b=chars, autojunk=False)
    s2, e2 = [-1.0] * len(spoken), [-1.0] * len(spoken)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            s2[a + k], e2[a + k] = st[b + k], en[b + k]
    last = 0.0
    for i in range(len(spoken)):                  # fill gaps with the previous known time
        if s2[i] < 0:
            s2[i], e2[i] = last, last
        last = e2[i]
    return s2, e2


def words_from(parts, spoken, al):
    st, en = char_times(spoken, al)
    out, off = [], 0
    for disp, said, same in parts:
        if same:
            for m in re.finditer(r'\S+', disp):
                a, b = off + m.start(), off + m.end() - 1
                out.append({'w': m.group(0), 's': st[a], 'e': en[b]})
        else:
            idx = [off + m.start() for m in re.finditer(r'\S', said)]
            if idx:
                t0, t1 = st[idx[0]], en[idx[-1]]
                toks = disp.split()
                total = sum(len(t) for t in toks) or 1
                t = t0
                for tok in toks:
                    dt = (t1 - t0) * len(tok) / total
                    out.append({'w': tok, 's': t, 'e': t + dt})
                    t += dt
        off += len(said)
    merged = []
    for w in out:                                 # a lone dash or quote is not a word to highlight: glue it to the previous one
        if merged and PUNCT_ONLY.match(w['w']):
            merged[-1]['w'] += (' ' + w['w']) if w['w'] in '—–' else w['w']
            merged[-1]['e'] = max(merged[-1]['e'], w['e'])
        else:
            merged.append(w)
    for w in merged:
        w['s'], w['e'] = round(w['s'], 3), round(w['e'], 3)
    return merged


def tts(spoken, seed):
    r = requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format={FMT}',
                      headers={'xi-api-key': key()}, timeout=300,
                      json={'text': spoken, 'model_id': MODEL, 'voice_settings': SETTINGS, 'language_code': LANG, 'seed': seed})
    if not r.ok:
        raise SystemExit(f'ElevenLabs {r.status_code}: {r.text[:400]}')
    return r.json()


def stress_score(take, alignment):
    """(score, flags) from stress_audit.py, or (0, []) with a note when its heavy dependencies are not installed."""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from stress_audit import audit_take
    except ImportError as e:
        print(f'  stress audit skipped ({e}); pip install ruaccent transformers torch librosa huggingface_hub')
        return 0.0, []
    return audit_take(take, alignment)


def main():
    import argparse
    import shutil
    global VOICE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dir')
    ap.add_argument('--force', action='store_true', help='re-voice even if voice.mp3 exists (costs credits)')
    ap.add_argument('--takes', type=int, default=1, help='voice up to N takes, keep the one with the fewest stress problems')
    ap.add_argument('--tempo', type=float, default=None, help='speed-up by time-stretch (v4 has no speed setting), e.g. 1.06')
    ap.add_argument('--voice-id', default=None, help='ElevenLabs voice id (overrides the environment and the credentials file)')
    ap.add_argument('--voice-key', default='ELEVENLABS_VOICE_ID', help='name of the variable that holds the voice id')
    ap.add_argument('--dry-run', action='store_true', help='write spoken.txt and print it; no API call')
    a = ap.parse_args()
    d = Path(a.dir)
    script = re.sub(r'[ 	]+', ' ', (d / 'script.txt').read_text(encoding='utf-8').strip())
    parts = pieces(script)
    spoken = ''.join(p[1] for p in parts)
    (d / 'spoken.txt').write_text(spoken, encoding='utf-8')
    if a.dry_run:
        print(spoken)
        print(f'-- {len(spoken)} characters to voice; respelled/paired: ' + ', '.join(f'{p[0]}→{p[1]}' for p in parts if not p[2]))
        return
    mp3 = d / 'voice.mp3'
    if a.force or not mp3.exists():
        VOICE = a.voice_id or cred(a.voice_key)
        if not VOICE:
            raise SystemExit(f'no voice id: pass --voice-id or set {a.voice_key} (environment or {CRED})')
        best = None
        for k in range(a.takes):
            seed = 1000 + k * 7919
            data = tts(spoken, seed)
            take = d / f'voice_take{k}.mp3'
            take.write_bytes(base64.b64decode(data['audio_base64']))
            score, flags = 0.0, []
            if a.takes > 1:
                score, flags = stress_score(take, data['alignment'])
                print(f'  дубль {k}: баллы {score} ' + '; '.join(f"{f['word']} ({f['why']}: {f['heard']})" for f in flags))
            if best is None or score < best[0]:
                best = (score, k, data, flags, seed)
            if score == 0:
                break
        score, k, data, flags, seed = best
        shutil.copy(d / f'voice_take{k}.mp3', mp3)
        old = json.loads((d / 'alignment.json').read_text(encoding='utf-8')) if (d / 'alignment.json').exists() else {}
        (d / 'alignment.json').write_text(json.dumps({'alignment': data['alignment'], 'model': MODEL, 'voice': VOICE, 'settings': SETTINGS,
                                                      'language_code': LANG, 'seed': seed, 'take': k, 'stress_score': score,
                                                      'stress_flags': flags, 'tempo': a.tempo or old.get('tempo', 1.0),
                                                      'spoken': spoken, 'display': script}, ensure_ascii=False), encoding='utf-8')
    meta = json.loads((d / 'alignment.json').read_text(encoding='utf-8'))
    if meta.get('spoken') and meta['spoken'] != spoken:
        raise SystemExit('script.txt changed since voice.mp3 was made — run with --force to re-voice')
    tempo = a.tempo or meta.get('tempo', 1.0)
    if a.tempo and meta.get('tempo') != a.tempo:
        meta['tempo'] = a.tempo
        (d / 'alignment.json').write_text(json.dumps(meta, ensure_ascii=False), encoding='utf-8')
    words = words_from(parts, spoken, meta['alignment'])
    if tempo != 1.0:                             # the voice is time-stretched below, so every word moves with it
        for w in words:
            w['s'], w['e'] = round(w['s'] / tempo, 3), round(w['e'] / tempo, 3)
    (d / 'words.json').write_text(json.dumps(words, ensure_ascii=False, indent=0), encoding='utf-8')
    af = ['-filter:a', f'atempo={tempo}'] if tempo != 1.0 else []
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp3), *af, '-ar', '48000', '-ac', '2', str(d / 'voice.wav')], check=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(d / 'voice.wav')],
                               capture_output=True, text=True).stdout)
    print(f'{d.name}: {len(words)} слов, голос {dur:.1f} с (темп ×{tempo}), дубль {meta.get("take", 0)}, '
          f'проблем ударения {meta.get("stress_score", "—")}, последнее слово кончается на {words[-1]["e"]:.2f} с')


if __name__ == '__main__':
    main()
