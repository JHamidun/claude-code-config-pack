#!/usr/bin/env python3
"""Подготовить записи к клонированию голоса.

Модель копирует всё, что слышит. Если в исходнике паузы ожидания, скачки громкости,
чужая реплика или шум — клон впитает и это: будет тянуть паузы, менять громкость,
подхрипывать. Поэтому материал не «скармливают как есть», а готовят.

Что делает скрипт:

    вырезает тишину   паузы длиннее порога сжимаются, ожидание не попадает в датасет
    выравнивает       громкость приводится к диапазону, который ждёт сервис клонирования
    режет на куски    длинные записи бьются на файлы удобного размера
    считает           сколько чистой речи получилось на выходе

Чего он НЕ делает: не давит шум и не правит эквалайзер. Шумодав меняет тембр, и клон
выучит звучание обработки вместо голоса — лучше взять запись почище, чем чистить эту.

    python voice_dataset.py webinar.mp4 -o dataset/
    python voice_dataset.py rec1.mp4 rec2.m4a -o dataset/ --target-lufs -20 --chunk 600
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

# Сервис ждёт материал в этом коридоре громкости: тише — клон звучит вяло, громче —
# в обучение попадают перегрузы.
TARGET_LUFS = -20.0
TRUE_PEAK = -3.0


def duration(path: pathlib.Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def measure(path: pathlib.Path) -> dict:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af",
                        f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    s, e = r.rfind("{"), r.rfind("}")
    return json.loads(r[s:e + 1]) if s >= 0 and e > s else {}


def speech_share(path: pathlib.Path, floor: str = "-38dB") -> float:
    """Какая доля записи — собственно речь, а не паузы.

    Полезно до обработки: запись с 40% тишины даст вдвое меньше материала, чем кажется
    по её длине, и это надо знать заранее, а не после часа обработки.
    """
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af",
                        f"silencedetect=noise={floor}:d=0.5", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    quiet = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", r))
    total = duration(path)
    return max(0.0, (total - quiet) / total) if total else 0.0


def clean(src: pathlib.Path, dst: pathlib.Path, target: float, keep_pause: float,
          floor: str) -> None:
    """Вырезать паузы и выровнять громкость за один проход.

    Нормализация двухпроходная: одиночный проход не знает исходных уровней и либо
    недотягивает, либо загоняет пики в перегруз. Замер делается по уже подрезанному
    материалу — иначе тишина занижает измеренную громкость.
    """
    tmp = dst.with_suffix(".trim.wav")
    # stop_periods=-1 — обрабатывать все паузы, а не только первую.
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "44100",
         "-af", (f"silenceremove=stop_periods=-1:stop_duration={keep_pause}:"
                 f"stop_threshold={floor}:detection=rms"),
         str(tmp)], check=True)

    m = measure(tmp)
    if m.get("input_i"):
        norm = (f"loudnorm=I={target}:TP={TRUE_PEAK}:LRA=9:"
                f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                f"offset={m['target_offset']}")
    else:
        norm = f"loudnorm=I={target}:TP={TRUE_PEAK}:LRA=9"

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", norm,
                    "-b:a", "192k", str(dst)], check=True)
    tmp.unlink(missing_ok=True)


def split(src: pathlib.Path, out_dir: pathlib.Path, chunk: float, stem: str) -> list:
    """Разрезать на куски. Общий метраж важнее числа файлов, но грузить удобнее частями."""
    pattern = str(out_dir / f"{stem}_%03d.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                    "-f", "segment", "-segment_time", str(chunk),
                    "-c:a", "libmp3lame", "-b:a", "192k", pattern], check=True)
    return sorted(out_dir.glob(f"{stem}_*.mp3"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", help="записи: видео или аудио")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--target-lufs", type=float, default=TARGET_LUFS)
    ap.add_argument("--keep-pause", type=float, default=0.45,
                    help="какой длины паузу оставлять, с")
    ap.add_argument("--floor", default="-38dB", help="ниже этого уровня считается паузой")
    ap.add_argument("--chunk", type=float, default=600,
                    help="длина куска на выходе, с; 0 — не резать")
    a = ap.parse_args()

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    total_in = total_out = 0.0
    files = []
    for s in a.sources:
        src = pathlib.Path(s)
        if not src.exists():
            print(f"  нет файла: {src}")
            continue
        d_in = duration(src)
        share = speech_share(src, a.floor)
        print(f"  {src.name}: {d_in / 60:.1f} мин, речи примерно {share * 100:.0f}%")

        stem = re.sub(r"[^\w-]+", "_", src.stem)[:40]
        clean_path = out / f"{stem}_clean.mp3"
        clean(src, clean_path, a.target_lufs, a.keep_pause, a.floor)
        d_out = duration(clean_path)

        if a.chunk:
            parts = split(clean_path, out, a.chunk, stem)
            clean_path.unlink(missing_ok=True)
            files += parts
            print(f"    → {len(parts)} кусков, {d_out / 60:.1f} мин чистой речи")
        else:
            files.append(clean_path)
            print(f"    → {clean_path.name}, {d_out / 60:.1f} мин чистой речи")

        total_in += d_in
        total_out += d_out

    print(f"\n  на входе {total_in / 60:.0f} мин → на выходе {total_out / 60:.0f} мин "
          f"чистой речи в {len(files)} файлах")
    print(f"  папка: {out}")

    # Порог не выдуман: сервис требует получаса минимум и заметно лучше работает от двух.
    m = total_out / 60
    if m < 30:
        print(f"  ← для профессионального клона нужно от 30 мин, не хватает {30 - m:.0f}")
        print("    на мгновенный клон хватит: ему нужно 1–2 минуты")
    elif m < 120:
        print("  ← на профессиональный клон хватает; от двух часов результат заметно ровнее")
    else:
        print("  ← метража достаточно для лучшего качества")
    print("  проверь на слух хотя бы один кусок перед загрузкой: замеры не слышат "
          "чужую реплику и призвуки")
    return 0


if __name__ == "__main__":
    sys.exit(main())
