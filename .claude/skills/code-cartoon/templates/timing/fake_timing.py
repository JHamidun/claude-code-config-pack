"""DRAFT timing without a voice, so scenes can be built and previewed before the owner approves the text
(and before any voice credits are spent).

    python timing/fake_timing.py [--rate 2.6]

Words come from voice/script.txt (pairs {показ|произношение} -> the shown part), at ~`draft_rate` words per second
(longer words get longer slots), pauses at sentence ends (. ! ? … 0.45 s; , ; : — 0.18 s) plus the `pauses` from
timing/timing_config.json, `lead` before and `tail` after; the mouth envelope is synthetic (opens per syllable).
Writes timing/timing.json and timing/timing.js with "draft": true — the same shape build_timing.py writes, with the same
scene names, so scenes keep working when the real voice arrives (run timing/build_timing.py then; times will move,
which is why scenes take every time from W('слово') and K.scene(), never from hard-coded seconds).
"""
import re
import sys

import numpy as np

from timing_common import ROOT, build_scenes, find_word, load_config, report, turn_info, write_outputs

cfg = load_config()
FPS, LEAD, TAIL = cfg['fps'], cfg['lead'], cfg['tail']
RATE = float(sys.argv[sys.argv.index('--rate') + 1]) if '--rate' in sys.argv else float(cfg['draft_rate'])
script = ROOT / 'voice' / 'script.txt'
if not script.exists():
    raise SystemExit(f'no {script}: write the voice-over text there first')

text = re.sub(r'\{([^{}|]*)\|([^{}]*)\}', lambda m: m.group(1), script.read_text(encoding='utf-8'))
raw = text.split()
tokens = []
for tok in raw:
    if not re.search(r'\w', tok):                 # a lone dash / quote: glued to the previous word ('линия —'), dropped if first
        if tokens:
            tokens[-1] += ' ' + tok
        continue
    tokens.append(tok)
if not tokens:
    raise SystemExit('voice/script.txt is empty')

VOW = set('аеёиоуыэюяАЕЁИОУЫЭЮЯaeiouyAEIOUY')


def syllables(w):
    core = w.split(' ')[0]
    return max(1, sum(ch in VOW for ch in core) + 2 * sum(ch.isdigit() for ch in core))


def punct_pause(w):
    tail = w.rstrip('»"\')]')
    if tail.endswith(('.', '!', '?', '…')):
        return 0.45
    if tail.endswith((',', ';', ':', '—', '–')):
        return 0.18
    return 0.0


syl = [syllables(w) for w in tokens]
weight = np.array([0.12 + 0.1 * s for s in syl])
k = (len(tokens) / RATE) / weight.sum()          # speech time without punctuation pauses = words / rate
slots = weight * k

extra = [0.0] * len(tokens)
for wtext, n, sec in cfg['pauses']:
    i = find_word([{'w': w} for w in tokens], wtext, n)
    extra[i] += sec

words, t = [], LEAD
for i, w in enumerate(tokens):
    d = slots[i] * 0.86
    words.append({'w': w, 's': round(t, 3), 'e': round(t + d, 3)})
    t += slots[i]
    if i + 1 < len(tokens):
        t += punct_pause(w) + extra[i]
total = round(words[-1]['e'] + TAIL, 3)

# synthetic mouth: opens once per syllable inside a word, closed between words, same smoothing as the real envelope
nfr = int(np.ceil(total * FPS))
env = np.zeros(nfr)
for w, s in zip(words, syl):
    a, b = int(np.ceil(w['s'] * FPS)), int(np.floor(w['e'] * FPS))
    for f in range(a, min(nfr, b + 1)):
        u = (f / FPS - w['s']) / max(1e-6, w['e'] - w['s'])
        env[f] = 0.35 + 0.65 * abs(np.sin(np.pi * s * min(1.0, max(0.0, u))))
env = np.clip(np.convolve(env, [0.25, 0.5, 0.25], mode='same'), 0, 1)

data = {'fps': FPS, 'duration': total, 'lead': LEAD, 'tail': TAIL, 'draft': True, 'words': words,
        'scenes': build_scenes(words, cfg, total), 'turn': turn_info(words, cfg, total),
        'mouth': [round(float(v), 3) for v in env]}
write_outputs(data)
report(data)
print(f'draft rate {RATE} words/s; record the voice and run timing/build_timing.py to replace this draft')
