#!/usr/bin/env python3
"""Beat-synced montage: cut clips to music beats + xfade chain + loudnorm.

Detects beats with librosa, trims clips to beat intervals, chains them with a short
xfade, lays the music on top, normalizes to -14 LUFS. The backbone of music-driven
shortform montage.

Usage:
  python beat_sync_edit.py music.mp3 clip1.mp4 clip2.mp4 ... -o out.mp4
    --beats-per-cut 2     # 1=every beat (fast), 2=every other, 4=every bar
    --transition fade     # any ffmpeg xfade name (fade/wipeleft/pixelize/zoomin...)
    --xfade-dur 0.08      # transition length (shortform: 0.06-0.20)
    --downbeats           # cut on bar starts only (needs madmom; falls back to beats)

Deps: pip install librosa   (madmom optional for --downbeats)
"""
import argparse
import os
import subprocess
import sys
import tempfile


def get_beat_times(audio_path, beats_per_cut=2, downbeats=False):
    import librosa
    import numpy as np
    if downbeats:
        try:
            from madmom.features.downbeats import RNNDownBeatProcessor, DBNDownBeatTrackingProcessor
            raw = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)(
                RNNDownBeatProcessor()(audio_path))
            cut = raw[raw[:, 1] == 1, 0].tolist()
            if cut:
                return cut, 0.0
        except Exception as e:
            print("madmom downbeats unavailable (%s) -> librosa beats" % type(e).__name__)
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr)
    times = librosa.frames_to_time(frames, sr=sr)
    return times[::beats_per_cut].tolist(), float(np.atleast_1d(tempo)[0])  # librosa may return ndarray


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def trim(clip, length, i, tmp):
    out = os.path.join(tmp, "seg_%04d.mp4" % i)
    subprocess.run(["ffmpeg", "-y", "-i", clip, "-ss", "0", "-t", "%.3f" % length,
                    "-c:v", "libx264", "-crf", "20", "-an", out],
                   check=True, capture_output=True)
    return out, length


def build(trimmed, output, transition, xfade, music):
    n = len(trimmed)
    inputs = []
    for p, _ in trimmed:
        inputs += ["-i", p]
    inputs += ["-i", music]                      # music = input index n (ALL inputs before -map)
    norm = "".join("[%d:v]settb=AVTB,setsar=1,fps=30[%dv];" % (i, i) for i in range(n))
    fg, cum, last = [], 0.0, "0v"
    for i in range(1, n):
        cum += trimmed[i - 1][1] - xfade
        out_v = "xv%d" % i if i < n - 1 else "outv"
        fg.append("[%s][%dv]xfade=transition=%s:duration=%.3f:offset=%.4f[%s]"
                  % (last, i, transition, xfade, cum, out_v))
        last = out_v
    fc = norm + ";".join(fg)
    cmd = (["ffmpeg", "-y"] + inputs +
           ["-filter_complex", fc, "-map", "[outv]", "-map", "%d:a" % n, "-shortest",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", output])
    subprocess.run(cmd, check=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("music")
    ap.add_argument("clips", nargs="+")
    ap.add_argument("-o", "--output", default="beat_sync.mp4")
    ap.add_argument("--beats-per-cut", type=int, default=2)
    ap.add_argument("--transition", default="fade")
    ap.add_argument("--xfade-dur", type=float, default=0.08)
    ap.add_argument("--downbeats", action="store_true")
    a = ap.parse_args()
    cuts, bpm = get_beat_times(a.music, a.beats_per_cut, a.downbeats)
    print("BPM %.1f | %d cut points" % (bpm, len(cuts)))
    with tempfile.TemporaryDirectory() as tmp:
        trimmed = [trim(a.clips[i % len(a.clips)], e - s, i, tmp)
                   for i, (s, e) in enumerate(zip(cuts, cuts[1:]))]
        build(trimmed, a.output, a.transition, a.xfade_dur, a.music)
    print("saved", a.output)


if __name__ == "__main__":
    main()
