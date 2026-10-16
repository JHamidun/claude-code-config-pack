# -*- coding: utf-8 -*-
"""Локальная расшифровка записей — faster-whisper на видеокарте, без платных ключей.

    python transcribe_local.py <видео|аудио> [ещё...] --out ./transcripts
        [--model large-v3] [--device cuda]

Для каждого файла кладёт рядом:
  <имя>.txt   — реплики с таймкодами, по ним ищут места для нарезки;
  <имя>.json  — сегменты со словами и таймингами (для точной резки по паузам).
Уже готовые файлы пропускает, так что прогон возобновляемый.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")


def hhmmss(sec):
    sec = int(sec)
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def audio_of(path, tmp):
    wav = os.path.join(tmp, re.sub(r"[^\w.-]+", "_", os.path.basename(path))[:80] + ".wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", wav],
                       check=True)
    return wav


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--lang", default="ru")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "_audio")
    os.makedirs(tmp, exist_ok=True)

    from faster_whisper import WhisperModel
    print(f"модель {a.model} на {a.device}…", flush=True)
    model = WhisperModel(a.model, device=a.device, compute_type="float16" if a.device == "cuda" else "int8")

    for f in a.files:
        base = re.sub(r"[^\w.-]+", "_", os.path.splitext(os.path.basename(f))[0])[:80]
        txt_p = os.path.join(a.out, base + ".txt")
        json_p = os.path.join(a.out, base + ".json")
        if os.path.exists(txt_p) and os.path.exists(json_p):
            print(f"уже расшифрован: {base}", flush=True)
            continue
        t0 = time.time()
        wav = audio_of(f, tmp)
        segments, info = model.transcribe(wav, language=a.lang, word_timestamps=True,
                                          vad_filter=True, beam_size=5)
        print(f"{base}: длительность {hhmmss(info.duration)}, пошла расшифровка", flush=True)
        segs, lines, last = [], [], 0
        for s in segments:
            segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                         "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)}
                                   for w in (s.words or [])]})
            lines.append(f"[{hhmmss(s.start)}] {s.text.strip()}")
            if s.start - last > 300:
                last = s.start
                print(f"  …{hhmmss(s.start)} из {hhmmss(info.duration)}", flush=True)
        io.open(txt_p, "w", encoding="utf-8").write("\n".join(lines))
        json.dump({"file": f, "duration": info.duration, "segments": segs},
                  io.open(json_p, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"готово: {txt_p} ({len(lines)} реплик, {int(time.time() - t0)} с)", flush=True)


if __name__ == "__main__":
    main()
