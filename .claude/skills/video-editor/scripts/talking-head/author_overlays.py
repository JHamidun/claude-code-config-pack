#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Author overlay config: creator face at each take start, AI b-roll over the rest.

Explicit take->clips map keeps b-roll meaning aligned to what he says.
Targets ~16-18 overlays. SFX whoosh at each overlay entry.

Usage: python author_overlays.py r1
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
FACE_INTRO = 2.2     # seconds of creator's face at each take start before b-roll
FACE_TAIL = 0.5      # seconds of creator's face at each take end (back to him)
MIN_OV = 1.4         # min overlay length
ENDING = "broll/ending.mp4"

# take index -> ordered list of clip ids to overlay across that take's window
MAP_R1 = {
    0: ["r1_s01", "r1_s02"],
    1: ["r1_s03"],
    2: ["r1_s04", "r1_s05a", "r1_s05b", "r1_s05c"],
    3: ["r1_s06"],
    4: ["r1_s07"],
    5: ["r1_s08", "r1_s09"],
    6: ["r1_s10"],
    7: ["r1_s11", "r1_s12", "r1_s13"],
    8: ["r1_s14"],
    9: ["r1_s15"],
    10: ["r1_s16"],
}
MAP_R2 = {
    0: ["r2_s01"],
    1: ["r2_s03", "r2_s04"],
    2: ["r2_s05b"],
    3: ["r2_s06"],
    4: ["r2_s07"],
    5: ["r2_s08"],
    6: ["r2_s09", "r2_s10"],
    7: ["r2_s11"],
    8: ["r2_s13"],
    9: [],                # плюшка/лид-магнит — keep creator on screen
    10: ["r2_s15"],
    11: ["r2_s16"],
    12: ["r2_s17"],
    13: ["r2_s18"],
}
FX_CYCLE = ["in", "out", "left", "in", "right", "out"]
SFX = "audio/sfx_whoosh.mp3"
SFX2 = "audio/sfx_whoosh2.mp3"


def main():
    reel = sys.argv[1]
    segv = json.loads((BASE / f"segmap_v_{reel}.json").read_text(encoding="utf-8"))
    cmap = MAP_R1 if reel == "r1" else MAP_R2
    bdur = segv[-1]["t1"]

    overlays = []
    sfx = []
    fxi = 0
    for seg in segv:
        i = seg["i"]
        clips = cmap.get(i, [])
        clips = [c for c in clips if (BASE / "broll" / f"{c}.mp4").exists()]
        if not clips:
            continue
        win0 = seg["t0"] + FACE_INTRO
        win1 = seg["t1"] - FACE_TAIL
        if win1 - win0 < MIN_OV:
            win0 = seg["t0"] + min(0.8, (seg["t1"] - seg["t0"]) * 0.3)  # short take: less face
            win1 = seg["t1"] - 0.1
        if win1 - win0 < 0.8:
            continue
        n = len(clips)
        seglen = (win1 - win0) / n
        for k, c in enumerate(clips):
            t0 = win0 + k * seglen
            t1 = win0 + (k + 1) * seglen
            fx = FX_CYCLE[fxi % len(FX_CYCLE)]
            fxi += 1
            overlays.append({"clip": f"broll/{c}.mp4", "t0": round(t0, 3), "t1": round(t1, 3),
                             "fx": fx, "trans": "cut"})
            sfx.append({"file": SFX if k == 0 else SFX2, "at": round(max(0, t0 - 0.08), 3), "gain": 0.7})

    cfg = {
        "base": f"build/base_{reel}.mp4",
        "ending": ENDING,
        "gap": 0.45,
        "music": "audio/suno_f3955f4e.mp3",
        "music_gain": 0.12,
        "overlays": overlays,
        "sfx": sfx,
    }
    out = BASE / f"cfg_{reel}.json"
    out.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    cov = sum(o["t1"] - o["t0"] for o in overlays)
    print(f"{reel}: {len(overlays)} overlays, {cov:.0f}s b-roll over {bdur:.0f}s base "
          f"({100*cov/bdur:.0f}% covered), creator visible {bdur-cov:.0f}s -> {out.name}")


if __name__ == "__main__":
    main()
