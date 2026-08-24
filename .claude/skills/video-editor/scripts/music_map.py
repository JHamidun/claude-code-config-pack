#!/usr/bin/env python3
"""Карта музыкального трека: темп, такты, секции, дропы — монтажная сетка из аудио.

Зачем отдельно от beat_sync_edit. Тот режет по битам равномерно, и получается ровный
метроном: на вступлении столько же склеек, сколько на кульминации. Живой монтаж
устроен иначе — плотность склеек следует за энергией трека: длинные планы на вступлении,
частые на подъёме, удар на дропе, выдох на спаде.

Здесь трек разбирается на:
    темп и сетку тактов   — куда вообще можно ставить склейку
    секции                — где музыка меняет характер (по автоподобию)
    энергию по тактам     — насколько громко и плотно в каждом такте
    события               — дроп (скачок энергии) и брейк (провал)

На выходе JSON с готовым планом: для каждой секции сказано, какой длины держать план
и какой класс перехода уместен. Дальше это скармливается монтажу.

    python music_map.py track.mp3                      # карта в консоль
    python music_map.py track.mp3 -o map.json          # + файл
    python music_map.py track.mp3 --plot map.png       # картинка энергии с разметкой
    python music_map.py track.mp3 --cuts               # только моменты склеек, по строке

Опирается на librosa. Референсный трек и трек для монтажа разбираются одинаково —
поэтому чужую структуру можно снять и приложить к своему материалу.
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
import json
import pathlib
import sys

import numpy as np


# Как ведёт себя монтаж в секции такого характера. Числа — доли такта на один план:
# 4.0 = один план на 4 такта (долгий), 0.5 = две склейки за такт (частит).
SECTION_STYLE = {
    "intro":    {"bars_per_shot": 4.0, "transition": "мягкий",  "note": "вступление: держать план, дать зрителю осмотреться"},
    "build":    {"bars_per_shot": 2.0, "transition": "ритм",    "note": "нарастание: сокращать планы к концу секции"},
    "peak":     {"bars_per_shot": 1.0, "transition": "удар",    "note": "пик: склейка в такт, короткие акценты"},
    "drop":     {"bars_per_shot": 0.5, "transition": "удар",    "note": "дроп: самый плотный монтаж, эффект на самой доле"},
    "break":    {"bars_per_shot": 4.0, "transition": "роспуск", "note": "брейк: выдох, длинный план, без резких склеек"},
    "outro":    {"bars_per_shot": 4.0, "transition": "мягкий",  "note": "финал: замедлять, уводить в затемнение"},
}


def load(path: str, sr: int = 22050):
    import librosa
    y, sr = librosa.load(path, sr=sr, mono=True)
    return y, sr


def grid(y, sr):
    """Темп и сетка долей. Первую долю такта берём по силе, а не по счёту.

    madmom (единственная библиотека, честно ищущая сильную долю) под свежий Python не
    ставится, поэтому такт восстанавливаем сами: из четырёх кандидатов фазы выбираем
    ту, у которой суммарная сила онсетов на сильных долях максимальна. На музыке с
    выраженной бочкой это попадает практически всегда.
    """
    import librosa
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    tempo = float(np.atleast_1d(tempo)[0])
    times = librosa.frames_to_time(beats, sr=sr)
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    strength = onset[np.clip(beats, 0, len(onset) - 1)]

    best_phase, best_score = 0, -1.0
    for phase in range(4):
        score = float(strength[phase::4].sum())
        if score > best_score:
            best_phase, best_score = phase, score
    downbeats = times[best_phase::4]
    return tempo, times, downbeats


def sections(y, sr, n: int = 8):
    """Границы секций по автоподобию: где музыка перестаёт быть похожей на себя."""
    import librosa
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    bounds = librosa.segment.agglomerative(chroma, n)
    return librosa.frames_to_time(bounds, sr=sr)


def energy_curve(y, sr, at_times):
    """Громкость в окрестности каждой опорной точки, нормированная в 0..1."""
    import librosa
    rms = librosa.feature.rms(y=y)[0]
    t = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    vals = np.interp(at_times, t, rms)
    lo, hi = float(vals.min()), float(vals.max())
    return (vals - lo) / (hi - lo) if hi > lo else np.zeros_like(vals)


def classify(seg_start, seg_end, dbeats, energy_at_db, total) -> str:
    """Назвать секцию по её энергии и положению в треке.

    Пороги подобраны так, чтобы не назвать пиком всё подряд: «пик» — это верхняя
    четверть трека по громкости, а не просто «громче среднего». Дроп отличается от
    пика не уровнем, а СКАЧКОМ относительно предыдущей секции.
    """
    idx = np.where((dbeats >= seg_start) & (dbeats < seg_end))[0]
    if len(idx) == 0:
        return "break"
    e = float(energy_at_db[idx].mean())
    pos = seg_start / total if total else 0.0

    if pos < 0.10 and e < 0.55:
        return "intro"
    if pos > 0.85 and e < 0.65:
        return "outro"
    if e < 0.30:
        return "break"
    if e > 0.75:
        return "peak"
    if len(idx) >= 3 and energy_at_db[idx[-1]] > energy_at_db[idx[0]] + 0.15:
        return "build"
    return "peak" if e > 0.55 else "break"


def find_drops(dbeats, energy_at_db, jump: float = 0.28) -> list[float]:
    """Дроп — такт, где энергия скакнула вверх сильнее порога и осталась высокой."""
    out = []
    for i in range(2, len(energy_at_db)):
        prev = float(energy_at_db[i - 2:i].mean())
        if energy_at_db[i] - prev >= jump and energy_at_db[i] > 0.6:
            out.append(float(dbeats[i]))
    # Схлопываем соседние срабатывания: дроп — событие, а не серия
    merged = []
    for t in out:
        if not merged or t - merged[-1] > 4.0:
            merged.append(t)
    return merged


def build_map(path: str) -> dict:
    y, sr = load(path)
    total = float(len(y) / sr)
    tempo, beats, dbeats = grid(y, sr)
    e_db = energy_curve(y, sr, dbeats)
    bounds = sections(y, sr)
    drops = find_drops(dbeats, e_db)

    bar_s = 60.0 / tempo * 4 if tempo else 2.0
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        kind = classify(a, b, dbeats, e_db, total)
        style = SECTION_STYLE[kind]
        idx = np.where((dbeats >= a) & (dbeats < b))[0]
        segs.append({
            "start": round(float(a), 3),
            "end": round(float(b), 3),
            "kind": kind,
            "energy": round(float(e_db[idx].mean()) if len(idx) else 0.0, 3),
            "shot_len_s": round(style["bars_per_shot"] * bar_s, 2),
            "transition": style["transition"],
            "note": style["note"],
        })

    # Моменты склеек: внутри каждой секции шагаем её собственным шагом, а не общим.
    cuts = []
    for s in segs:
        t, step = s["start"], max(s["shot_len_s"], 0.35)
        while t < s["end"]:
            near = dbeats[np.argmin(np.abs(dbeats - t))] if len(dbeats) else t
            cuts.append(round(float(near), 3))
            t += step
    for d in drops:                       # на дропе склейка обязана быть точно в долю
        cuts.append(round(d, 3))
    cuts = sorted(set(cuts))

    return {
        "file": str(pathlib.Path(path).resolve()),
        "duration_s": round(total, 2),
        "tempo_bpm": round(tempo, 1),
        "bar_s": round(bar_s, 3),
        "beats": [round(float(t), 3) for t in beats],
        "downbeats": [round(float(t), 3) for t in dbeats],
        "drops": [round(d, 2) for d in drops],
        "sections": segs,
        "cuts": cuts,
    }


def plot(m: dict, out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 3.2))
    colors = {"intro": "#9ecae1", "build": "#fdd0a2", "peak": "#fc9272",
              "drop": "#de2d26", "break": "#c7c7c7", "outro": "#bcbddc"}
    for s in m["sections"]:
        ax.axvspan(s["start"], s["end"], color=colors.get(s["kind"], "#eee"), alpha=.75)
        ax.text((s["start"] + s["end"]) / 2, .92, s["kind"], ha="center", fontsize=8)
    for d in m["drops"]:
        ax.axvline(d, color="k", lw=1.6)
    for c in m["cuts"]:
        ax.axvline(c, color="w", lw=.5, alpha=.8)
    ax.set_xlim(0, m["duration_s"]); ax.set_ylim(0, 1); ax.set_yticks([])
    ax.set_xlabel(f"секунды   ·   {m['tempo_bpm']} BPM   ·   склеек: {len(m['cuts'])}")
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("-o", "--out", help="куда положить JSON")
    ap.add_argument("--plot", help="картинка с разметкой энергии")
    ap.add_argument("--cuts", action="store_true", help="печатать только моменты склеек")
    a = ap.parse_args()

    m = build_map(a.track)

    if a.cuts:
        print("\n".join(str(c) for c in m["cuts"]))
        return 0

    print(f"  {pathlib.Path(a.track).name}")
    print(f"  {m['duration_s']:.0f} с · {m['tempo_bpm']} BPM · такт {m['bar_s']:.2f} с "
          f"· долей {len(m['beats'])} · тактов {len(m['downbeats'])}")
    print(f"  дропы: {', '.join(f'{d:.1f}с' for d in m['drops']) or 'не найдены'}")
    print(f"  склеек по плану: {len(m['cuts'])}\n")
    for s in m["sections"]:
        print(f"   {s['start']:7.1f}–{s['end']:6.1f}  {s['kind']:6s} "
              f"энергия {s['energy']:.2f}  план {s['shot_len_s']:5.2f}с  {s['transition']:8s} {s['note']}")

    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  карта: {a.out}")
    if a.plot:
        plot(m, a.plot)
        print(f"  картинка: {a.plot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
