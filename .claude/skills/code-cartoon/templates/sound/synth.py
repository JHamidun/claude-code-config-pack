"""Sound for the cartoon, written as code (methodology: «звук — тоже текст»): every effect is synthesised and placed at the
time the picture uses (the cue sheet window.CUES that render.py dumps), the music is a plucked-synth score whose bar line
falls on the anchor event (the turn), ducked under the voice; then loudness -15 LUFS, true peak -1.5 dBTP (ffmpeg loudnorm,
2 passes), and the written file is measured again (the printed result is a measurement, not the target).

    python sound/synth.py <cues.json> <timing.json> <voice_final.wav | none> <out_mix.wav> [--music-only out_music.wav] [--no-music]

Cue sheet without a full render (CUES are filled in SETUP, so a 2-frame render dumps all of them):
    python render/render.py pencil/index.html out/cues.mp4 --to 0.1 --workers 1        -> out/cues.cues.json
`none` instead of the voice = music + effects only (works on a draft timing from timing/fake_timing.py).
After a change of length or timing, rebuild the cue sheet and the mix — otherwise the sound drifts off the picture.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

# ============================== configuration ==============================
SR = 48000
ANCHOR_CUE = 'click'           # cue kind whose time gets a bar line (the turn); fallback: timing.json "turn", then 40 % of length
LOUDNESS_I, TRUE_PEAK, LRA = -15.0, -1.5, 11      # methodology: -16..-14 LUFS, peak <= -1 dB (target -1.5: loudnorm overshoots ~0.05 dB)
UNKNOWN_KIND = 'warn'          # cue kind without a recipe in sfx_for(): 'warn' = skip it and say so, 'error' = stop
BPM = 100
# music form: None = automatic from the scenes — A intro, B build-up (from the scene start nearest to half-way to the
# anchor), C after the anchor, D from the second-to-last scene, E (outro) from the last scene; empty sections are skipped.
# Or a list [(start, section)], start = seconds | scene name | '@anchor', sections 'A'..'E'.
MUSIC_FORM = None
PROGRESSIONS = {'A': ['Am', 'F', 'C', 'G'], 'B': ['Am', 'F', 'C', 'G'], 'C': ['C', 'G', 'Am', 'F'], 'D': ['F', 'G', 'Em', 'Am'], 'E': ['C', 'F', 'G', 'C']}
FINAL_CHORD_LEAD = 1.0         # the final chord rings from the first bar line >= (end - tail - this), under the poster
MIX = {'voice': 1.0, 'sfx': 0.9, 'music': 0.62}
DUCK_DEPTH = 0.55              # music dips under the voice by up to this share
# per-kind gain; the recipes are in sfx_for(). Kinds in BOOST_EXEMPT play as is, the rest get x1.8 (reference balance).
SFX_GAIN = {'pencil_long': 0.22, 'cross': 0.35, 'scribble': 0.35, 'chalk': 0.28, 'color_fill': 0.3, 'type_run': 0.28, 'tick': 0.35,
            'pop': 0.35, 'clank': 0.3, 'paper': 0.35, 'whir': 0.3, 'lever': 0.4, 'whoosh': 0.32, 'unroll': 0.35, 'hop': 0.3,
            'land': 0.45, 'shutter': 0.35, 'ding': 0.32, 'zoom': 0.3, 'zoom_out': 0.28, 'click': 0.75, 'shine': 0.4, 'scan': 0.35,
            'chop': 0.45, 'slide': 0.3, 'snap': 0.35, 'chime': 0.4, 'sparkle': 0.35}
BOOST_EXEMPT = {'click', 'chop'}
# ===========================================================================

rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def lp(x, hi):
    return bp(x, 0, hi)


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def mix_at(buf, x, t, g):
    i = int(round(t * SR))
    if i >= len(buf) or i + len(x) <= 0:
        return
    j = min(len(buf), i + len(x))
    buf[max(0, i):j] += g * x[max(0, -i):j - i]


def add(*xs):
    """Sum signals of different lengths (zero-padded): a plain + fails with a broadcast error."""
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[:len(x)] += x
    return out


# ---------- effects ----------
def pencil(d, rate=9.0, bright=1.0):
    n = noise(d); x = bp(n, 1800, 7000 * bright)
    t = t_(d)[:len(x)]
    strokes = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t + np.sin(2 * np.pi * 1.3 * t) * 2)
    grain = (rng.random(len(x)) < 0.25) * 0.6 + 0.4
    e = np.minimum(1, t / 0.04) * np.minimum(1, (d - t) / 0.08)
    return norm(x * strokes ** 2 * grain * e, 0.5)


def click(f=2400, d=0.035, body=0.0):
    t = t_(d); x = np.sin(2 * np.pi * f * t) * np.exp(-t * 160) + 0.5 * bp(noise(d), 2000, 9000) * np.exp(-t * 300)
    if body:
        x += body * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 60)
    return norm(x, 0.9)


def pop(f0=320, f1=1000, d=0.09):
    t = t_(d); f = f0 + (f1 - f0) * (t / d) ** 0.6
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * np.minimum(1, t / 0.004), 0.8)


def whoosh(d=0.45, f0=400, f1=3000, up=True):
    x = noise(d); out = np.zeros_like(x); seg = 1024
    for i in range(0, len(x), seg):
        k = i / len(x); fc = f0 + (f1 - f0) * (k if up else 1 - k)
        out[i:i + seg] = bp(x[i:i + seg], fc * 0.6, fc * 1.6)
    t = t_(d)[:len(out)]
    return norm(out * np.sin(np.pi * t / d) ** 2, 0.6)


def bell(f=1320, d=1.0, partials=((1, 1), (2.01, 0.5), (3.02, 0.25), (4.1, 0.12))):
    t = t_(d)
    return norm(sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * (3 + 2 * m)) for m, a in partials) * np.minimum(1, t / 0.003), 0.7)


def thud(f=90, d=0.18):
    t = t_(d)
    return norm(np.sin(2 * np.pi * f * t * (1 - 0.3 * t / d)) * np.exp(-t * 22) + 0.3 * lp(noise(d), 400) * np.exp(-t * 40), 0.9)


def metal(d=0.5):
    t = t_(d); fs = [520, 1310, 1870, 2450, 3330]
    return norm(sum(np.sin(2 * np.pi * f * t + i) * np.exp(-t * (6 + i)) for i, f in enumerate(fs)) + 0.4 * bp(noise(d), 2000, 6000) * np.exp(-t * 30), 0.6)


def sfx_for(kind):
    """Recipe per cue kind; None = no recipe (see UNKNOWN_KIND)."""
    if kind == 'pencil_long': return pencil(1.3)
    if kind == 'cross': return pencil(0.28, rate=4, bright=1.2)
    if kind == 'scribble': return pencil(0.45, rate=16, bright=1.1)
    if kind == 'chalk': return pencil(1.0, rate=7, bright=0.7) * 0.9
    if kind == 'color_fill': return pencil(0.55, rate=14, bright=0.8) * 0.8
    if kind == 'type_run':
        out = np.zeros(int(1.6 * SR))
        for k in range(18):
            mix_at(out, click(f=1700 + 500 * rng.random(), d=0.03), k * 0.085 + 0.02 * rng.random(), 0.5 + 0.4 * rng.random())
        return out
    if kind == 'tick': return click(2600, 0.03)
    if kind == 'pop': return pop()
    if kind == 'clank': return metal(0.5)
    if kind == 'paper': return norm(lp(noise(0.12), 5000) * np.exp(-t_(0.12) * 25), 0.4)
    if kind == 'whir':
        t = t_(0.5); saw = 2 * ((t * 110) % 1) - 1
        return norm((0.4 * saw + 0.6 * bp(noise(0.5), 300, 1500)) * np.sin(np.pi * t / 0.5), 0.45)
    if kind == 'lever':
        out = np.zeros(int(0.45 * SR))
        for k in range(5): mix_at(out, click(1200, 0.025), k * 0.05, 0.6)
        mix_at(out, thud(140, 0.15), 0.27, 0.8); return out
    if kind == 'whoosh': return whoosh(0.45)
    if kind == 'unroll': return add(whoosh(0.6, 200, 1500) * 0.8, pencil(0.6, rate=20) * 0.3)
    if kind == 'hop':
        t = t_(0.28); f = 220 + 480 * (t / 0.28) + 25 * np.sin(2 * np.pi * 18 * t)
        return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.28), 0.5)
    if kind == 'land': return thud(100, 0.15)
    if kind == 'shutter':
        out = np.zeros(int(0.1 * SR)); mix_at(out, click(3000, 0.02), 0, 0.8); mix_at(out, click(2200, 0.03), 0.045, 0.6); return out
    if kind == 'ding': return bell(1568, 0.9)
    if kind == 'zoom': return whoosh(0.55, 300, 4000)
    if kind == 'zoom_out': return whoosh(0.7, 4000, 300, up=True)
    if kind == 'click':                                   # the turn: a crisp key press + low body
        out = np.zeros(int(0.3 * SR)); mix_at(out, click(2000, 0.04, body=0.8), 0, 1.0); mix_at(out, click(3200, 0.02), 0.012, 0.5); return out
    if kind == 'shine':
        out = np.zeros(int(1.2 * SR))
        for k, f in enumerate([1047, 1319, 1568, 2093, 2637]): mix_at(out, bell(f, 0.9), k * 0.06, 0.45)
        return out
    if kind == 'scan':
        t = t_(1.7)
        return norm(np.sin(2 * np.pi * (300 + 200 * t / 1.7) * t) * 0.3 * np.sin(np.pi * t / 1.7) + 0.15 * bp(noise(1.7), 3000, 6000) * np.sin(np.pi * t / 1.7), 0.25)
    if kind == 'chop':
        out = np.zeros(int(0.25 * SR)); mix_at(out, thud(160, 0.12), 0, 0.9); mix_at(out, click(3500, 0.02), 0.005, 0.6); return out
    if kind == 'slide': return whoosh(0.3, 800, 2500) * 0.6
    if kind == 'snap':
        out = np.zeros(int(0.4 * SR)); mix_at(out, click(2800, 0.025), 0, 0.8); mix_at(out, bell(2093, 0.35), 0.01, 0.4); return out
    if kind == 'chime':
        out = np.zeros(int(1.6 * SR)); mix_at(out, bell(1047, 1.4), 0, 0.6); mix_at(out, bell(1568, 1.2), 0.14, 0.5); return out
    if kind == 'sparkle':
        out = np.zeros(int(1.0 * SR))
        for k in range(7): mix_at(out, bell(2000 + 900 * rng.random(), 0.4), k * 0.07, 0.3)
        return out
    return None


# ---------- music: plucked-synth score, bar line on the anchor ----------
NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}
CH = {'Am': [('A', 3), ('C', 4), ('E', 4)], 'F': [('F', 3), ('A', 3), ('C', 4)], 'C': [('C', 4), ('E', 4), ('G', 4)],
      'G': [('G', 3), ('B', 3), ('D', 4)], 'Em': [('E', 3), ('G', 3), ('B', 3)], 'Dm': [('D', 3), ('F', 3), ('A', 3)]}


def hz(name, octv):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octv + 1) - 69) / 12)


def pluck(f, d, bright=0.6):
    t = t_(d)
    x = sum((bright ** (k - 1)) / k * np.sin(2 * np.pi * f * k * t + k) * np.exp(-t * (2.5 + 1.8 * k)) for k in range(1, 7))
    return x * np.minimum(1, t / 0.004)


def pad(freqs, d):
    t = t_(d); x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    return x * np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.5) / len(freqs)


def music_form(timing, anchor_t):
    """[(start_seconds, section)] sorted, non-decreasing."""
    sc = timing['scenes']
    if MUSIC_FORM:
        def at(v):
            if v == '@anchor':
                return anchor_t
            if isinstance(v, str):
                return next(s['start'] for s in sc if s['name'] == v)
            return float(v)
        return sorted((at(v), s) for v, s in MUSIC_FORM)
    inner = [s['start'] for s in sc if 0 < s['start'] < anchor_t]
    b = min(inner, key=lambda x: abs(x - anchor_t / 2)) if inner else anchor_t / 2
    d = max(anchor_t, sc[-2]['start']) if len(sc) >= 3 else anchor_t
    e = max(d, sc[-1]['start']) if len(sc) >= 2 else d
    return [(0.0, 'A'), (b, 'B'), (anchor_t, 'C'), (d, 'D'), (e, 'E')]


def music(timing, anchor_t):
    total, tail = timing['duration'], timing.get('tail', 3.0)
    form = music_form(timing, anchor_t)
    section = lambda t: [s for st, s in form if t >= st - 0.01][-1]
    beat = 60 / BPM; bar = 4 * beat
    start = anchor_t - round(anchor_t / bar) * bar
    while start < 0:
        start += bar
    final_t = total - tail - FINAL_CHORD_LEAD
    buf = np.zeros(int((total + 5) * SR))
    t, b = start, 0
    while t < total - 0.2:
        sec = section(t)
        ch = PROGRESSIONS[sec][b % len(PROGRESSIONS[sec])]
        notes = [hz(n, o) for n, o in CH[ch]]
        if t >= final_t:                                         # final chord rings out under the poster
            for f in notes + [notes[0] * 2]: mix_at(buf, pluck(f, 4.0, 0.5), t, 0.16)
            mix_at(buf, pad(notes, min(4.5, total - t + 1)), t, 0.10)
            mix_at(buf, bell(notes[0] * 4, 2.5), t, 0.06)
            break
        pattern = [0, 1, 2, 1] if sec in 'AB' else [0, 2, 1, 2, 0, 2, 1, 2]    # pizzicato, denser after the turn
        step = bar / len(pattern)
        for k, idx in enumerate(pattern):
            g = 0.10 if sec == 'A' else 0.12 if sec == 'B' else 0.13
            mix_at(buf, pluck(notes[idx] * (2 if sec in 'CDE' and k % 4 == 3 else 1), 0.9), t + k * step, g)
        mix_at(buf, pluck(notes[0] / 2, 1.8, 0.4), t, 0.16 if sec != 'A' else 0.1)          # bass
        if sec in 'CDE':
            mix_at(buf, pad(notes, bar), t, 0.05)
            melody = [notes[2] * 2, notes[1] * 2, notes[0] * 2, notes[1] * 2]
            for k in range(2): mix_at(buf, bell(melody[(b + k) % 4], 0.8), t + k * 2 * beat + beat, 0.035)
        if sec in 'BCD':                                            # soft brush shaker on 8ths
            for k in range(8):
                sh = bp(noise(0.05), 5000, 11000) * np.exp(-t_(0.05) * 70)
                mix_at(buf, sh, t + k * beat / 2, 0.025 if k % 2 else 0.04)
        t += bar; b += 1
    return buf[:int(total * SR)], form, start


def loudnorm_stats(path, af='loudnorm=print_format=json'):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', af, '-f', 'null', '-'], capture_output=True, text=True)
    return json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])


def main():
    args = [a for a in sys.argv[1:]]
    pos = []
    while args:
        a = args.pop(0)
        if a == '--music-only':
            args.pop(0)
        elif not a.startswith('--'):
            pos.append(a)
    if len(pos) < 4:
        raise SystemExit(__doc__)
    cues = json.load(open(pos[0], encoding='utf-8'))
    timing = json.load(open(pos[1], encoding='utf-8'))
    out = Path(pos[3])
    out.parent.mkdir(parents=True, exist_ok=True)
    total = timing['duration']
    n = int(total * SR)
    v = np.zeros(n)
    if pos[2].lower() != 'none':
        voice, vsr = sf.read(pos[2])
        voice = voice.mean(1) if voice.ndim > 1 else voice
        if vsr != SR:
            from scipy.signal import resample_poly
            voice = resample_poly(voice, SR, vsr)
        v[:min(n, len(voice))] = voice[:n]
    fx = np.zeros(n)
    skipped = {}
    for c in cues:
        x = sfx_for(c['k'])
        if x is None:
            if UNKNOWN_KIND == 'error':
                raise SystemExit(f"cue kind {c['k']!r} has no recipe in sfx_for() (t = {c['t']})")
            skipped[c['k']] = skipped.get(c['k'], 0) + 1
            continue
        if c['k'] == 'snap' and c.get('p'):                         # a pitched snap: + a pluck at c.p Hz
            x = add(x, 0.9 * norm(pluck(c['p'], 0.5, 0.7), 0.9))
        boost = 1.0 if c['k'] in BOOST_EXEMPT else 1.8
        mix_at(fx, x, c['t'], SFX_GAIN.get(c['k'], 0.3) * c.get('g', 1) * boost)
    for k, cnt in skipped.items():
        print(f'WARNING: {cnt} cue(s) of kind {k!r} skipped: no recipe in sfx_for()')
    anchor = next((c['t'] for c in cues if c['k'] == ANCHOR_CUE), None)
    src = f'cue {ANCHOR_CUE!r}'
    if anchor is None and timing.get('turn'):
        anchor, src = timing['turn']['t'], 'timing.json turn'
    if anchor is None:
        anchor, src = total * 0.4, '40 % of the length'
    mu = np.zeros(n)
    if '--no-music' not in sys.argv:
        mu, form, mstart = music(timing, anchor)
        mu = np.pad(mu, (0, max(0, n - len(mu))))[:n]
        print(f'music: {BPM} bpm, bar line on {anchor:.2f} s ({src}), starts {mstart:.2f} s; form ' + ', '.join(f'{s}@{t:.2f}' for t, s in form))
        if v.any():                                                 # duck the music under the voice (smoothed envelope)
            ve = np.abs(v); win = int(0.12 * SR)
            ve = np.convolve(ve, np.ones(win) / win, mode='same')
            duck = 1 - DUCK_DEPTH * np.clip(ve / (np.percentile(ve, 90) + 1e-9), 0, 1)
            mu *= np.convolve(duck, np.ones(win) / win, mode='same')
        if '--music-only' in sys.argv:
            sf.write(sys.argv[sys.argv.index('--music-only') + 1], mu, SR)
    mix = v * MIX['voice'] + fx * MIX['sfx'] + mu * MIX['music']
    fade = min(n, int(0.6 * SR))
    mix[n - fade:] *= np.linspace(1, 0, fade)                        # soft end
    raw = out.with_suffix('.raw.wav')
    sf.write(raw, np.stack([mix, mix], 1) * 0.5, SR)
    target = f'loudnorm=I={LOUDNESS_I}:TP={TRUE_PEAK}:LRA={LRA}'
    js = loudnorm_stats(raw, target + ':print_format=json')
    af = (f"{target}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
          f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-af', af, '-ar', str(SR), str(out)], check=True)
    raw.unlink()
    res = loudnorm_stats(out)                                         # measure what was written, do not trust the target
    print(f"{out.name}: {total:.2f} s, {len(cues)} cues, voice: {'yes' if v.any() else 'none'}; "
          f"result {res['input_i']} LUFS, true peak {res['input_tp']} dBTP (target {LOUDNESS_I} / {TRUE_PEAK})")


if __name__ == '__main__':
    main()
