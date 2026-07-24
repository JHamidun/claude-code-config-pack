#!/usr/bin/env python3
"""Objective music-vs-voice balance check — measures the music bed level in a
speech-free gap against a speech region, so you don't guess "is music too loud".

Why: client said "музыка громче меня" twice; eyeballing gain numbers wasn't enough.
This prints both levels so you can confirm music sits clearly UNDER the voice.

GOTCHA: ffmpeg `volumedetect` returns nothing on very short clips and is flaky with
`-ss` BEFORE `-i` — always seek AFTER input and use windows >= ~1s.

Usage:
  python audio_balance_check.py FINAL.mp4 --gap 51.0 [--gaplen 0.3] [--speech 5]
  (--gap = a music-only moment, e.g. the breath gap before the CTA ending)
"""
import argparse
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows cp1251 guard
except Exception:
    pass


def measure(video, ss, dur):
    # -ss AFTER -i (reliable), window >= 1s where possible
    # NB: volumedetect prints its summary at INFO level — do NOT use `-v error` (hides it).
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-ss", f"{ss}", "-t", f"{dur}",
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stderr
    mean = re.search(r"mean_volume:\s*(-?[\d.]+)", out)
    mx = re.search(r"max_volume:\s*(-?[\d.]+)", out)
    return (float(mean.group(1)) if mean else None, float(mx.group(1)) if mx else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--gap", type=float, required=True, help="music-only timestamp (sec)")
    ap.add_argument("--gaplen", type=float, default=1.0)
    ap.add_argument("--speech", type=float, default=5.0, help="speech region start (sec)")
    ap.add_argument("--speechlen", type=float, default=6.0)
    a = ap.parse_args()
    gm, gx = measure(a.video, a.gap, a.gaplen)
    sm, sx = measure(a.video, a.speech, a.speechlen)
    print(f"music-only gap  @{a.gap:>6.1f}s: mean={gm} dB  max={gx} dB")
    print(f"speech region   @{a.speech:>6.1f}s: mean={sm} dB  max={sx} dB")
    if gm is not None and sm is not None:
        # gap = music alone; speech = voice+ducked music. If music-in-gap is NEAR/above the
        # speech mix, the bed competes (too hot). Caveat: short gaps get LIFTED by the final
        # loudnorm pass (see note below) — judge by ear too, and prefer a longer music-only window.
        if gm >= sm - 2:
            print(f"music-only ({gm:.1f}) ~ speech mix ({sm:.1f}) -> bed likely TOO HOT; lower music_gain "
                  f"OR loudnorm the VOICE bus before mixing music (loudnorm after-mix lifts gaps)")
        else:
            print(f"music-only ({gm:.1f}) sits {sm - gm:.1f} dB under speech mix ({sm:.1f}) -> bed under voice, OK")
    else:
        print("(пусто — окно слишком короткое/тихое: --gaplen/--speechlen >= 1s; проверь что --gap реально music-only)")


if __name__ == "__main__":
    main()
