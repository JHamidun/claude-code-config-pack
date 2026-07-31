#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Build overlay cfg from a Gemini montage plan (plan_rX.json).

Each 'broll' segment -> a clip (explicit plan-order list, matched to topics),
varied fx + transitions; 'face' segments -> creator shows (no overlay).
SFX only on a few major b-roll entries, quiet. Music present.

Usage: python author_from_plan.py r1
"""
import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())

# clip assigned to each b-roll segment, in PLAN ORDER (matched to Gemini topics)
BROLL_R1 = ["r1_s03", "r1_s07", "r1_s05a", "r1_s06", "r1_s05c", "r1_s02", "r1_s09", "r1_s08",
            "r1_s10", "r1_s11", "r1_s12", "r1_s13", "r1_s14", "r1_s15", "r1_s04", "r1_s16"]
BROLL_R2 = ["r2_s03", "r2_s04", "r2_s05b", "r2_s05a", "r2_s05b", "r2_s07", "r2_s06",
            "r2_s10", "r2_s09", "r2_s13", "r2_s13", "r2_s04", "r2_s01", "r2_s15",
            "r2_s15", "r2_s16", "r2_s11", "r2_s17", "r2_s10", "r2_s17", "r2_s18"]

FX = ["in", "left", "out", "right", "in", "out"]
SFX_FILE = "audio/sfx_whoosh.mp3"
SFX_FILE2 = "audio/sfx_whoosh2.mp3"


def main():
    reel = sys.argv[1]
    plan = json.loads((BASE / f"plan_{reel}.json").read_text(encoding="utf-8"))
    clips = BROLL_R1 if reel == "r1" else BROLL_R2
    base_clean = "build/base_r1_final2.mp4" if reel == "r1" else "build/base_r2_final2.mp4"

    segs = plan["segments"]
    overlays = []
    sfx = []
    bi = 0
    fxi = 0
    for k, s in enumerate(segs):
        if s["mode"] != "broll":
            continue
        if bi >= len(clips):
            clip = clips[-1]
        else:
            clip = clips[bi]
        bi += 1
        if not (BASE / "broll" / f"{clip}.mp4").exists():
            continue
        t0 = round(s["start"], 3)
        t1 = round(s["end"], 3)
        if t1 - t0 < 0.6:
            continue
        fx = FX[fxi % len(FX)]
        fxi += 1
        # transition: alternate cut / flash / zoom for variety; flash on high energy
        energy = s.get("energy", "")
        prev_face = (k > 0 and segs[k - 1]["mode"] == "face")
        trans = "flash" if (prev_face or energy == "high") and (bi % 3 == 0) else "cut"
        overlays.append({"clip": f"broll/{clip}.mp4", "t0": t0, "t1": t1, "fx": fx, "trans": trans})

    # SFX only on entries that follow a FACE segment (the punchy re-entries), quiet
    for k, s in enumerate(segs):
        if s["mode"] == "broll" and k > 0 and segs[k - 1]["mode"] == "face":
            sfx.append({"file": SFX_FILE, "at": round(max(0, s["start"] - 0.06), 3), "gain": 0.8})

    cfg = {
        "base": base_clean,
        "ending": "broll/ending_av.mp4",
        "gap": 0.4,
        "music": "audio/suno_f3955f4e.mp3",
        "music_gain": 0.42,
        "sfx_gain": 0.3,
        "overlays": overlays,
        "sfx": sfx,
    }
    out = BASE / f"cfg_{reel}.json"
    out.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    cov = sum(o["t1"] - o["t0"] for o in overlays)
    print(f"{reel}: {len(overlays)} overlays, {len(sfx)} sfx, {cov:.0f}s b-roll -> {out.name}")


if __name__ == "__main__":
    main()
