#!/usr/bin/env python3
"""Звуки интерфейса под события в кадре — синтезом, без библиотеки сэмплов.

Зачем синтез. В роликах, где картинка не режется, а собирается слоями, каждое появление
титра или стикера сопровождается коротким звуком: щелчок, всплытие, мягкий удар. Без
них ролик выглядит немым даже с голосом — глаз видит движение, ухо ничего не получает,
и монтаж читается как слайд-шоу.

Готовые библиотеки требуют лицензии и весят десятки мегабайт ради звуков на сотню
миллисекунд. Эти же звуки описываются формулой: тон с быстрым затуханием, шумовой
щелчок, короткий скользящий свист. Синтез даёт их без файлов и без лицензий.

    python ui_sfx.py pop -o pop.wav
    python ui_sfx.py --list
    python ui_sfx.py track --events 0.0,0.62,1.24 --duration 20 -o sfx.wav
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import math
import pathlib
import struct
import sys
import wave

RATE = 44100


def envelope(n: int, attack: float, decay: float) -> list[float]:
    """Оболочка громкости: резкий подъём, экспоненциальный спад.

    Медленная атака превращает щелчок в шорох — для звука интерфейса подъём должен быть
    почти мгновенным, иначе он не совпадает с событием на экране.
    """
    a = max(int(attack * RATE), 1)
    out = []
    for i in range(n):
        if i < a:
            out.append(i / a)
        else:
            out.append(math.exp(-(i - a) / (decay * RATE)))
    return out


def tone(freq: float, dur: float, *, attack=0.001, decay=0.05,
         glide: float = 1.0, harm: float = 0.0) -> list[float]:
    """Тон с затуханием. glide меняет высоту к концу, harm подмешивает обертон."""
    n = int(dur * RATE)
    env = envelope(n, attack, decay)
    out = []
    phase = 0.0
    for i in range(n):
        f = freq * (1 + (glide - 1) * (i / max(n, 1)))
        phase += 2 * math.pi * f / RATE
        v = math.sin(phase)
        if harm:
            v += harm * math.sin(phase * 2)
        out.append(v * env[i])
    return out


def noise(dur: float, *, attack=0.0005, decay=0.02, seed: int = 1) -> list[float]:
    """Шумовой щелчок. Псевдослучайность детерминированная: звук должен повторяться."""
    n = int(dur * RATE)
    env = envelope(n, attack, decay)
    out, x = [], seed
    for i in range(n):
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        out.append(((x / 0x3FFFFFFF) - 1.0) * env[i])
    return out


def mix(*layers: list[float]) -> list[float]:
    n = max(len(x) for x in layers)
    out = [0.0] * n
    for L in layers:
        for i, v in enumerate(L):
            out[i] += v
    return out


SOUNDS = {
    "pop":    lambda: mix(tone(660, 0.10, decay=0.030, glide=1.9, harm=0.25),
                          noise(0.02, decay=0.008)),
    "click":  lambda: mix(noise(0.03, decay=0.006, seed=7),
                          tone(1800, 0.03, decay=0.010)),
    "whoosh": lambda: tone(240, 0.22, attack=0.05, decay=0.07, glide=3.2),
    "thud":   lambda: mix(tone(90, 0.16, decay=0.055, harm=0.15),
                          noise(0.03, decay=0.012, seed=3)),
    "ding":   lambda: mix(tone(1180, 0.34, decay=0.13, harm=0.4),
                          tone(1770, 0.24, decay=0.09)),
    "swipe":  lambda: tone(520, 0.14, attack=0.02, decay=0.04, glide=0.45),
}


def write_wav(path: pathlib.Path, samples: list[float], peak: float = 0.72) -> None:
    m = max((abs(v) for v in samples), default=1.0) or 1.0
    k = peak / m
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v * k)) * 32767))
                               for v in samples))


def build_track(events: list[float], duration: float, kinds: list[str] | None = None,
                gain: float = 0.5) -> list[float]:
    """Дорожка: звуки расставлены по моментам событий."""
    total = int(duration * RATE)
    track = [0.0] * total
    kinds = kinds or ["pop"] * len(events)
    for i, at in enumerate(events):
        kind = kinds[i % len(kinds)]
        s = SOUNDS.get(kind, SOUNDS["pop"])()
        start = int(at * RATE)
        for j, v in enumerate(s):
            k = start + j
            if 0 <= k < total:
                track[k] += v * gain
    return track


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="какие звуки есть")

    p = sub.add_parser("one", help="один звук в файл")
    p.add_argument("kind", choices=sorted(SOUNDS))
    p.add_argument("-o", "--out", required=True)

    p = sub.add_parser("track", help="дорожка со звуками по моментам")
    p.add_argument("--events", required=True, help="секунды через запятую")
    p.add_argument("--kinds", help="какие звуки, через запятую; по кругу")
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--gain", type=float, default=0.5)
    p.add_argument("-o", "--out", required=True)

    a = ap.parse_args()

    if a.cmd == "list":
        for k in SOUNDS:
            print(f"  {k}")
        print(f"\n  всего: {len(SOUNDS)}; всё считается формулой, файлов не нужно")
        return 0

    if a.cmd == "one":
        write_wav(pathlib.Path(a.out), SOUNDS[a.kind]())
        print(f"  {a.kind} → {a.out}")
        return 0

    events = [float(x) for x in a.events.split(",") if x.strip()]
    kinds = [x.strip() for x in a.kinds.split(",")] if a.kinds else None
    track = build_track(events, a.duration, kinds, a.gain)
    write_wav(pathlib.Path(a.out), track)
    print(f"  событий: {len(events)}, длительность {a.duration:.1f} с → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
