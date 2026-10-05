"""Sound measurements for code-cartoon QA (works on .wav and on the audio track of .mp4).

    python qa_audio.py win <media> <t0> <t1>           sample peak and RMS (dBFS) in a window
    python qa_audio.py hit <media> <t> [--w 0.08]      does an effect at t stand out: RMS [t, t+w] vs [t-0.1, t-0.02]
    python qa_audio.py onset <media> <t> [--s 0.12]    where the loudest sample near t is: offset in ms from t (sync check)
    python qa_audio.py loud <media>                    integrated loudness (LUFS) and true peak (dBTP), ffmpeg ebur128
    python qa_audio.py vm <voice.wav> <music.wav> [--g 0.62]   voice over music while the voice speaks, dB (music x mix gain)
"""
import re
import subprocess
import sys

import numpy as np

SR = 48000


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def decode(path):
    # native channel count, no '-ac': ffmpeg's rematrix uses 0.707 both ways (stereo->mono +3 dB on identical L/R,
    # mono->stereo -3 dB), which fakes peaks and ratios
    ch = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels',
                             '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')[0] or 1)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, stdin=subprocess.DEVNULL, check=True).stdout
    return np.abs(np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, ch)).max(1)   # per-sample max over channels


def db(v):
    return 20 * np.log10(v + 1e-9)


def seg(y, a, b):
    return y[max(0, int(a * SR)):max(0, int(b * SR))]


def rms(s):
    return db(np.sqrt(np.mean(s ** 2)))


if len(sys.argv) < 3:
    raise SystemExit(__doc__)
cmd, path = sys.argv[1], sys.argv[2]
if cmd == 'loud':
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    tail = r[r.rfind('Summary:'):]
    li, tp = re.search(r'I:\s+(-?[\d.]+) LUFS', tail), re.search(r'Peak:\s+(-?[\d.]+) dBFS', tail)
    print(f'I {li.group(1) if li else "?"} LUFS, true peak {tp.group(1) if tp else "?"} dBTP')
    sys.exit(0)
if cmd == 'vm':
    v, m = decode(path), decode(sys.argv[3]) * arg('--g', 0.62)
    n, hop = min(len(v), len(m)), SR // 10
    rv = np.array([np.sqrt(np.mean(v[i:i + hop] ** 2)) for i in range(0, n - hop, hop)])
    rm = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) for i in range(0, n - hop, hop)])
    act = rv > np.percentile(rv, 60)                          # 100 ms windows where the voice is loud
    print(f'voice over music while speaking: {db(np.mean(rv[act])) - db(np.mean(rm[act])):.1f} dB')
    sys.exit(0)
y = decode(path)
t = float(sys.argv[3])
if cmd == 'win':
    s = seg(y, t, float(sys.argv[4]))
    print(f'peak {db(s.max()):.1f} dBFS, rms {rms(s):.1f} dBFS')
elif cmd == 'hit':
    w = arg('--w', 0.08)
    ra, rb = rms(seg(y, t, t + w)), rms(seg(y, t - 0.1, t - 0.02))
    print(f'rms at hit {ra:.1f} dB vs before {rb:.1f} dB -> {ra - rb:+.1f} dB')
elif cmd == 'onset':
    s = arg('--s', 0.12)
    a = max(0.0, t - s)
    w = seg(y, a, t + s)
    print(f'loudest sample at {(a + np.argmax(w) / SR - t) * 1000:+.0f} ms from {t:.3f} s')
else:
    raise SystemExit(__doc__)
