#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""WhisperX word-level transcription of the cleaned bases -> caption words."""
import json
import os
import sys
from pathlib import Path

import whisperx

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
device = "cpu"
model = whisperx.load_model("large-v3", device, compute_type="int8", language="ru")
amodel, meta = whisperx.load_align_model(language_code="ru", device=device)

for reel in ["r1", "r2"]:
    wav = BASE / "build" / f"base_{reel}_clean.mp4"
    audio = whisperx.load_audio(str(wav))
    res = model.transcribe(audio, batch_size=8, language="ru")
    res = whisperx.align(res["segments"], amodel, meta, audio, device)
    words = []
    for s in res["segments"]:
        for w in s.get("words", []):
            if w.get("start") is not None:
                words.append({"w": w["word"].strip(), "s": round(w["start"], 3), "e": round(w["end"], 3)})
    (BASE / f"words_clean_{reel}.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    print(f"{reel}: {len(words)} words", flush=True)
print("DONE", flush=True)
