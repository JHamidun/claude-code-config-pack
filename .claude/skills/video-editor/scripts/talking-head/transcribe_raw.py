#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Transcribe raw takes with word timestamps for EDL building."""
import json
import os, sys, gc
from pathlib import Path


# Работа — в main(), под `if __name__ == "__main__"`. На верхнем уровне модуля
# только определения: импорт этого файла (линтер с исполнением, автодополнение
# в редакторе, `python -c "import ..."`) не должен ничего запускать и писать.
def main():
    import whisperx

    BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
    FILES = ["raw_5785", "raw_5782", "raw_5784"]

    device = "cpu"
    model = whisperx.load_model("large-v3", device, compute_type="int8", language="ru")

    amodel = None
    meta = None

    for name in FILES:
        wav = BASE / "audio" / f"{name}.wav"
        out = BASE / "transcripts" / f"{name}.json"
        if out.exists():
            print(f"skip {name}", flush=True)
            continue
        print(f"transcribing {name}...", flush=True)
        audio = whisperx.load_audio(str(wav))
        res = model.transcribe(audio, batch_size=8, language="ru")
        if amodel is None:
            amodel, meta = whisperx.load_align_model(language_code="ru", device=device)
        res = whisperx.align(res["segments"], amodel, meta, audio, device)
        segs = []
        for s in res["segments"]:
            segs.append({
                "start": round(s["start"], 3),
                "end": round(s["end"], 3),
                "text": s["text"].strip(),
                "words": [
                    {"w": w.get("word", ""), "s": round(w.get("start", -1), 3), "e": round(w.get("end", -1), 3)}
                    for w in s.get("words", [])
                ],
            })
        out.write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"done {name}: {len(segs)} segments", flush=True)
        del audio, res
        gc.collect()

    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
