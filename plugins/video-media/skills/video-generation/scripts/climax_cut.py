#!/usr/bin/env python3
"""Climax-aware trim — вырезать N-секундное окно из длинного трека так,
чтобы энергетический пик (кульминация) лёг на заданный offset в куске.

Зачем: Suno/Lyria часто выдают 2-4 мин трек, а ролику нужно ~60с. Обрезать
с начала — потерять кульминацию. Этот скрипт находит пик RMS и режет окно так,
чтобы пик встал под «вершину» нарратива (за ~10-15с до конца ролика).

Из проекта «Хроники Восхождения» (поздравление [Client]), generalized.

CLI:
    python climax_cut.py IN.mp3 OUT.mp3 [--win 62] [--climax-at 47]
        --win        длина итогового куска, сек (default 62)
        --climax-at  куда поставить пик внутри куска, сек от начала (default 47)

Требует ffmpeg/ffprobe в PATH и numpy.
"""
import argparse
import io
import subprocess
import sys
import wave

import numpy as np

SR = 16000


def decode(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "wav", "-"],
        capture_output=True).stdout
    w = wave.open(io.BytesIO(raw), "rb")
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return a


def best_window(path, win, climax_at):
    a = decode(path)
    dur = len(a) / SR
    step = 0.5
    hop = int(step * SR)
    rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2) + 1e-9) for i in range(0, len(a) - hop, hop)])
    sm = np.convolve(rms, np.ones(5) / 5, mode="same")          # smooth k=5
    climax_t = float(np.argmax(sm) * step)
    start = max(0.0, climax_t - climax_at)
    if start + win > dur:
        start = max(0.0, dur - win)
    return start, min(win, dur - start), dur, climax_t


def cut(path, out, win, climax_at):
    start, length, dur, climax = best_window(path, win, climax_at)
    print("%s: dur=%.1fs climax@%.1fs -> cut [%.1f..%.1f]" % (path, dur, climax, start, start + length))
    subprocess.run([
        "ffmpeg", "-y", "-ss", "%.2f" % start, "-t", "%.2f" % length, "-i", path,
        "-af", "afade=t=in:st=0:d=1.5,afade=t=out:st=%.2f:d=3" % (length - 3),
        "-c:a", "libmp3lame", "-b:a", "192k", out,
    ], capture_output=True)
    print("saved", out)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("outfile")
    ap.add_argument("--win", type=float, default=62.0)
    ap.add_argument("--climax-at", type=float, default=47.0)
    a = ap.parse_args()
    cut(a.infile, a.outfile, a.win, a.climax_at)


if __name__ == "__main__":
    main()
