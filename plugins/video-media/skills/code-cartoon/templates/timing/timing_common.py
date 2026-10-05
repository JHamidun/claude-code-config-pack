"""Shared by build_timing.py (real voice) and fake_timing.py (draft): config, word lookup, scenes, output files.

The word rule is the same as K.word() in engine/core.js: a timing word keeps its punctuation ('кодом:', 'линия —').
A bare query ('тоже') matches the exact token or the token's first space-separated part without leading quotes/brackets
and trailing punctuation ('тоже', 'тоже.'); a query with punctuation ('тоже.') matches only that exact token.
Occurrence n counts only matching words (W('кодом', 2) in JS == ('кодом', 2) here).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CONFIG = HERE / 'timing_config.json'
LEAD_P = '«"\'([„“'
TRAIL_P = '.,:;!?…»"\')]—–-'


def load_config():
    if not CONFIG.exists():
        raise SystemExit(f'no config: {CONFIG}')
    cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    cfg.setdefault('fps', 24)
    cfg.setdefault('lead', 0.7)
    cfg.setdefault('tail', 3.6)
    cfg.setdefault('scenes', [])
    cfg.setdefault('pauses', [])
    cfg.setdefault('draft_rate', 2.6)
    if not cfg['scenes']:
        raise SystemExit('timing_config.json: "scenes" is empty — list [scene_name, first_word, occurrence] for every scene')
    return cfg


def norm_word(s):
    return str(s).split(' ')[0].lstrip(LEAD_P).rstrip(TRAIL_P)


def find_word(words, text, n=1):
    """Index of the n-th word matching text (see module doc)."""
    k = 0
    for i, w in enumerate(words):
        if w['w'] == text or norm_word(w['w']) == text:
            k += 1
            if k == n:
                return i
    near = ', '.join(w['w'] for w in words[:40])
    raise SystemExit(f'word not found: {text!r} #{n} (found {k}). Words start with: {near} ...')


def build_scenes(words, cfg, total):
    scenes = []
    for k, (name, text, n) in enumerate(cfg['scenes']):
        i = find_word(words, text, n)
        start = 0.0 if k == 0 else round((words[i - 1]['e'] + words[i]['s']) / 2, 3) if i > 0 else round(words[i]['s'], 3)
        scenes.append({'name': name, 'start': start, 'firstWord': i})
    for k in range(1, len(scenes)):
        if scenes[k]['start'] <= scenes[k - 1]['start']:
            raise SystemExit(f"scene {scenes[k]['name']} starts before {scenes[k - 1]['name']}: check the first words in timing_config.json")
    for k in range(len(scenes)):
        scenes[k]['end'] = scenes[k + 1]['start'] if k + 1 < len(scenes) else round(total, 3)
    return scenes


def turn_info(words, cfg, total):
    if not cfg.get('turn'):
        return None
    text, n = cfg['turn'][0], cfg['turn'][1] if len(cfg['turn']) > 1 else 1
    i = find_word(words, text, n)
    t = words[i]['e']
    return {'word': words[i]['w'], 'index': i, 't': round(t, 3), 'pct': round(t / total * 100, 1)}


def write_outputs(data):
    """timing/timing.json (Python side: synth, critic) + timing/timing.js (pages load ../timing/timing.js)."""
    js = json.dumps(data, ensure_ascii=False)
    (HERE / 'timing.json').write_text(js, encoding='utf-8')
    (HERE / 'timing.js').write_text('window.TIMING = ' + js + ';\n', encoding='utf-8')


def report(data):
    words, total = data['words'], data['duration']
    tag = 'DRAFT (no voice) ' if data.get('draft') else ''
    print(f"{tag}total {total:.2f} s, {len(words)} words, {len(data['mouth'])} mouth frames; scenes:")
    for s in data['scenes']:
        print(f"  {s['name']:14} {s['start']:6.2f} - {s['end']:6.2f}  ({s['end'] - s['start']:5.2f} s)  «{words[s['firstWord']]['w']}»")
    tr = data.get('turn')
    lo, hi = total * 0.35, total * 0.45
    if tr:
        flag = 'ok' if lo <= tr['t'] <= hi else 'OUTSIDE 35-45 %: move the turn or rebalance the text'
        print(f"turn «{tr['word']}» ends at {tr['t']:.2f} s = {tr['pct']:.0f} % of length ({flag}; target {lo:.1f}-{hi:.1f} s)")
    else:
        print(f'turn: not configured; methodology target 35-45 % = {lo:.1f}-{hi:.1f} s')
    last = words[-1]['e'] if words else 0
    if total - last < 3.0:
        print(f'WARNING: only {total - last:.2f} s after the last word — the poster needs >= 3 s (raise "tail")')
    print('-> timing/timing.json, timing/timing.js (pages load ../timing/timing.js)')
