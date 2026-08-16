#!/usr/bin/env python3
"""Насколько громко звучит голос в каждый кадр ролика.

Нужно, чтобы рот персонажа открывался под речь. Настоящая синхронизация по звукам
речи требует распознавания фонем и отдельной модели; для рисованного персонажа в
вертикальном ролике этого не нужно — глаз читает совпадение «громко → рот шире»
и не проверяет, какая именно гласная произнесена. Так делают в рисованной анимации
с тех пор, как её начали синхронизировать со звуком.

Поэтому дорожка разбивается на отрезки по кадру видео, в каждом считается
среднеквадратичная громкость, шкала сжимается — тихие места слышны, но рот на них
почти закрыт, — и результат нормируется в 0…1.

    python voice_envelope.py voice.mp3 --fps 30 --duration 24.4 -o envelope.json
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import struct
import subprocess
import sys
import tempfile
import wave

RATE = 16000   # для огибающей высокая частота не нужна, а разбор ускоряется вчетверо


def decode(src: pathlib.Path, offset: float) -> list[int]:
    """Развернуть любой аудиофайл в отсчёты через ffmpeg."""
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "a.wav"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src),
               "-ac", "1", "-ar", str(RATE), str(tmp)]
        subprocess.run(cmd, check=True, capture_output=True)
        with wave.open(str(tmp), "rb") as w:
            raw = w.readframes(w.getnframes())
    vals = list(struct.unpack(f"<{len(raw) // 2}h", raw))
    # Голос в ролике начинается не с нуля: перед ним стоит задержка, и без неё
    # рот открывался бы раньше, чем звучит речь.
    return [0] * int(offset * RATE) + vals


def envelope(samples: list[int], fps: float, duration: float,
             floor: float = 0.06) -> list[float]:
    """Громкость по кадрам, сжатая по шкале и нормированная в 0…1."""
    total = int(duration * fps)
    step = RATE / fps
    out = []
    for i in range(total):
        a, b = int(i * step), int((i + 1) * step)
        chunk = samples[a:b]
        if not chunk:
            out.append(0.0)
            continue
        rms = math.sqrt(sum(v * v for v in chunk) / len(chunk)) / 32768
        # Корень сжимает разницу между шёпотом и криком: без него рот стоит закрытым
        # почти всю реплику и распахивается только на ударных слогах.
        out.append(math.sqrt(rms))
    peak = max(out) or 1.0
    out = [v / peak for v in out]
    # Ниже порога считаем тишиной — иначе рот подрагивает на шуме дорожки.
    return [0.0 if v < floor else round((v - floor) / (1 - floor), 3) for v in out]


def smooth(vals: list[float], window: int = 3) -> list[float]:
    """Сгладить: рот не может захлопываться и распахиваться каждый кадр."""
    out = []
    for i in range(len(vals)):
        a = max(0, i - window // 2)
        b = min(len(vals), i + window // 2 + 1)
        out.append(round(sum(vals[a:b]) / (b - a), 3))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--offset", type=float, default=0.0,
                    help="на сколько секунд голос сдвинут в ролике")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    src = pathlib.Path(a.audio)
    if not src.exists():
        raise SystemExit(f"нет файла: {src}")

    vals = smooth(envelope(decode(src, a.offset), a.fps, a.duration))
    pathlib.Path(a.out).write_text(json.dumps(vals), encoding="utf-8")

    speaking = sum(1 for v in vals if v > 0.15)
    print(f"  кадров: {len(vals)}, из них с речью: {speaking} "
          f"({speaking * 100 // max(len(vals), 1)}%)")
    print(f"  средняя громкость по речи: "
          f"{sum(v for v in vals if v > 0.15) / max(speaking, 1):.2f}")
    print(f"  огибающая: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
