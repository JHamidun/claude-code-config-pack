#!/usr/bin/env python3
"""Какую форму принимает рот на каждом кадре речи.

Липсинк по громкости — тупиковый путь: рот открывается одинаково на «м» и на «а»,
челюсть ходит вверх-вниз, и получается щелкунчик. Настоящая артикуляция различает
звуки: на «м» губы сомкнуты, на «о» вытянуты трубочкой, на «и» растянуты, на «ф»
нижняя губа уходит под зубы. Этих различий глаз ждёт даже от рисованного персонажа —
именно они отличают говорящего от картинки с дёргающейся челюстью.

Форм рта нужно немного. В рисованной анимации со времён студии Диснея обходятся
десятком: разные звуки, выглядящие одинаково, рисуют одной формой — например, «п»,
«б» и «м» неразличимы на вид, все три это сомкнутые губы.

Вход — тайминги букв от синтезатора речи (voice_timed.py --align).
Выход — форма рта на каждый кадр видео.

    python visemes.py align.json --fps 30 --duration 20 -o visemes.json
    python visemes.py align.json --fps 30 --duration 20 -o visemes.json --stats
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

# Буква → форма рта. Группировка по тому, как рот ВЫГЛЯДИТ, а не как звук слышится:
# видимых форм меньше, чем звуков, и лишние различия только добавляют дрожание.
VISEME_OF = {}


def _fill(letters: str, viseme: str) -> None:
    for ch in letters:
        VISEME_OF[ch] = viseme


# Губы сомкнуты — единственная форма, где рта не видно вовсе. Её пропуск сразу
# выдаёт подделку: персонаж говорит «мама» с постоянно открытым ртом.
_fill("мбп", "closed")
# Нижняя губа под верхними зубами.
_fill("фв", "teeth")
# Широко открыт.
_fill("ая", "wide")
# Приоткрыт, углы растянуты.
_fill("эе", "mid")
# Узкая растянутая щель, зубы видны.
_fill("иый", "narrow")
# Губы трубочкой, круглое отверстие.
_fill("оё", "round")
# Трубочка уже и меньше.
_fill("ую", "small")
# Язык у зубов, рот приоткрыт.
_fill("лтдн", "tongue")
# Шипящие и свистящие: зубы почти сомкнуты, щель узкая.
_fill("сзшщжцч", "hiss")
# Заднеязычные и «р»: рот приоткрыт средне.
_fill("кгхр", "mid")
# Мягкий и твёрдый знаки формы не имеют — тянут предыдущую.
_fill("ьъ", "")

REST = "rest"     # молчание: рот закрыт, но не сжат


def viseme_for(ch: str) -> str:
    low = ch.lower()
    if low in VISEME_OF:
        return VISEME_OF[low] or ""
    if low.strip() == "" or low in ".,!?…:;—-«»\"'()":
        return REST
    return "mid"      # неизвестный символ: нейтрально приоткрытый рот


def build(align: list[dict], fps: float, duration: float,
          hold: float = 0.045) -> list[str]:
    """Разложить буквы по кадрам.

    Очень короткие звуки (сотые доли секунды) не попадают ни в один кадр и пропадают,
    из-за чего рот проскакивает слог целиком. Поэтому каждая буква удерживается на
    экране не меньше минимального времени — рот успевает принять форму.
    """
    total = int(duration * fps)
    frames = [REST] * total
    for item in align:
        v = viseme_for(item["c"])
        if not v:
            continue
        s, e = item["s"], max(item["e"], item["s"] + hold)
        a, b = int(s * fps), max(int(e * fps), int(s * fps) + 1)
        for i in range(a, min(b, total)):
            if 0 <= i:
                frames[i] = v
    return frames


def smooth(frames: list[str], min_run: int = 2) -> list[str]:
    """Убрать одиночные кадры.

    Форма, продержавшаяся один кадр из тридцати, читается как рябь, а не как звук:
    на экране это тридцатая доля секунды. Такие вспышки заменяются соседней формой.
    """
    out = frames[:]
    i = 0
    while i < len(out):
        j = i
        while j < len(out) and out[j] == out[i]:
            j += 1
        if j - i < min_run and i > 0:
            for k in range(i, j):
                out[k] = out[i - 1]
        i = j
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("align", help="тайминги букв от voice_timed.py --align")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--stats", action="store_true", help="показать разбор по формам")
    a = ap.parse_args()

    align = json.loads(pathlib.Path(a.align).read_text(encoding="utf-8"))
    frames = smooth(build(align, a.fps, a.duration))
    pathlib.Path(a.out).write_text(json.dumps(frames, ensure_ascii=False),
                                   encoding="utf-8")

    speaking = sum(1 for f in frames if f != REST)
    print(f"  букв на входе: {len(align)}, кадров: {len(frames)}, "
          f"с артикуляцией: {speaking} ({speaking * 100 // max(len(frames), 1)}%)")

    if a.stats:
        from collections import Counter
        c = Counter(frames)
        for name, n in c.most_common():
            print(f"    {name:8} {n:4} кадров  {n * 100 // len(frames):2}%")
        # Смыкание губ — самая заметная форма; её отсутствие сразу выдаёт подделку.
        if not c.get("closed"):
            print("    ← ни одного смыкания губ: проверь, дошли ли до разбора буквы м/б/п")
    print(f"  формы рта: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
