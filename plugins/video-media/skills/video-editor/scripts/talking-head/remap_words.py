#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Remap raw-take word timestamps to the assembled VO timeline.

Reads edl_rX.json (rendered by cut_audio with --gap) + raw transcript JSONs.
Produces words_rX.json: [{"w","s","e"}] on final timeline, plus seg_map_rX.json:
EDL segments with their final-timeline offsets (for visual sync).
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
GAP = 0.15


def main():
    edl_path, words_out, segmap_out = sys.argv[1], sys.argv[2], sys.argv[3]
    edl = json.loads((BASE / edl_path).read_text(encoding="utf-8"))

    tr_cache = {}

    def words_for(file):
        if file not in tr_cache:
            name = Path(file).stem  # raw_5785
            segs = json.loads((BASE / "transcripts" / f"{name}.json").read_text(encoding="utf-8"))
            ws = []
            for s in segs:
                for w in s["words"]:
                    if w["s"] >= 0:
                        ws.append(w)
            tr_cache[file] = ws
        return tr_cache[file]

    out_words = []
    seg_map = []
    t = 0.0
    for i, seg in enumerate(edl):
        dur = seg["end"] - seg["start"]
        seg_map.append({**seg, "t0": round(t, 3), "t1": round(t + dur, 3)})
        for w in words_for(seg["file"]):
            ws, we = w["s"], w["e"]
            mid = (ws + we) / 2
            if seg["start"] - 0.02 <= mid <= seg["end"] + 0.02:
                ns = max(0.0, ws - seg["start"]) + t
                ne = min(dur, we - seg["start"]) + t
                if ne - ns > 0.03:
                    out_words.append({"w": w["w"], "s": round(ns, 3), "e": round(ne, 3)})
        t += dur
        if i < len(edl) - 1:
            t += GAP

    (BASE / words_out).write_text(json.dumps(out_words, ensure_ascii=False, indent=0), encoding="utf-8")
    (BASE / segmap_out).write_text(json.dumps(seg_map, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out_words)} words, {len(seg_map)} segments, total {t:.2f}s")


if __name__ == "__main__":
    main()
