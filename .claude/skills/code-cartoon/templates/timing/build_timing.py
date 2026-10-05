"""Final voice track with scene pauses + TIMING (words, scenes, turn, mouth envelope), shared by picture and sound.

    python timing/build_timing.py      (no arguments; edit timing/timing_config.json first)

Reads voice/words.json + voice/voice.wav (made by voice/voice.py, see the elevenlabs skill), inserts
`lead` silence before the voice, extra silence after the `pauses` words (in the quietest 20 ms of the gap) and `tail`
silence for the poster, remaps word times, splits scenes at the midpoint before each scene's first word.
Writes timing/voice_final.wav (same sample rate as voice.wav), timing/timing.json, timing/timing.js.
The pages load ../timing/timing.js directly — nothing to copy.
"""
import json

import numpy as np
import soundfile as sf

from timing_common import ROOT, HERE, build_scenes, find_word, load_config, report, turn_info, write_outputs

cfg = load_config()
FPS, LEAD, TAIL = cfg['fps'], cfg['lead'], cfg['tail']
VOICE = ROOT / 'voice'
if not (VOICE / 'words.json').exists() or not (VOICE / 'voice.wav').exists():
    raise SystemExit('no voice/words.json + voice/voice.wav yet: record the voice first, or use timing/fake_timing.py for a draft')

words = json.loads((VOICE / 'words.json').read_text(encoding='utf-8'))
y, sr = sf.read(VOICE / 'voice.wav')
if y.ndim == 1:
    y = y[:, None]
mono = y.mean(1)

cuts = []  # (sample position in the source, extra seconds)
for text, n, extra in cfg['pauses']:
    i = find_word(words, text, n)
    if i + 1 >= len(words):
        print(f'pause after the last word {text!r} ignored: raise "tail" instead')
        continue
    a, b = words[i]['e'], words[i + 1]['s']
    sa = int(a * sr)
    sb = max(sa + 1, int(b * sr))
    win = int(0.02 * sr)
    best, pos = 1e18, (sa + sb) // 2
    for p in range(sa, sb, max(1, win // 2)):          # quietest 20 ms inside the gap
        e = float(np.mean(mono[p:p + win] ** 2)) if p + win <= len(mono) else 1e18
        if e < best:
            best, pos = e, p
    cuts.append((pos, extra))
cuts.sort()

out, prev, shift_at = [np.zeros((int(LEAD * sr), y.shape[1]))], 0, []
for pos, extra in cuts:
    out.append(y[prev:pos])
    out.append(np.zeros((int(extra * sr), y.shape[1])))
    shift_at.append((pos / sr, extra))
    prev = pos
out.append(y[prev:])
out.append(np.zeros((int(TAIL * sr), y.shape[1])))
final = np.concatenate(out)
sf.write(HERE / 'voice_final.wav', final, sr)
total = len(final) / sr


def remap(t):
    s = LEAD
    for p, extra in shift_at:
        if t >= p:
            s += extra
    return t + s


fw = [{'w': w['w'], 's': round(remap(w['s']), 3), 'e': round(remap(w['e']), 3)} for w in words]
scenes = build_scenes(fw, cfg, total)

# mouth envelope at FPS: RMS of the final voice, smoothed, 0..1
fm = final.mean(1)
hop = sr // FPS
n = int(np.ceil(len(fm) / hop))
rms = np.array([np.sqrt(np.mean(fm[k * hop:(k + 1) * hop] ** 2)) if k * hop < len(fm) else 0 for k in range(n)])
db = 20 * np.log10(rms + 1e-6)
env = np.clip((db + 46) / 26, 0, 1)
env = np.convolve(env, [0.25, 0.5, 0.25], mode='same')
data = {'fps': FPS, 'duration': round(total, 3), 'lead': LEAD, 'tail': TAIL, 'draft': False, 'words': fw, 'scenes': scenes,
        'turn': turn_info(fw, cfg, total), 'mouth': [round(float(v), 3) for v in env]}
write_outputs(data)
report(data)
print(f'-> timing/voice_final.wav ({sr} Hz, {final.shape[1]} ch)')
