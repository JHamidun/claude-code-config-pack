#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Timeline-driven reel assembler: punch-in b-roll + per-cut transitions +
karaoke captions + LUT grade + VO/music/SFX mix + loudnorm.

timeline.json:
{
  "fps": 30,
  "slots": [
    {"clip": "broll/r1_s01.mp4", "dur": 3.4, "fx": "in",  "trans": "hard"},
    {"clip": "broll/r1_s02.mp4", "dur": 3.0, "fx": "out", "trans": "zoom"},
    ...
  ],
  "sfx": [{"file": "audio/sfx_whoosh.mp3", "at": 3.4, "gain": 0.9}, ...],
  "music": "audio/music_bed.mp3",
  "music_gain": 0.18
}

Usage:
  python assemble_reel.py timeline_r1.json audio/vo_r1.wav build/caps_r1.ass final/reel1.mp4 [--lut kodak] [--no-cache]
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
W, H, FPS = 1080, 1920, 30
TMP = BASE / "build" / "slots"   # каталог создаётся в main(), не при импорте

# xfade transition mapping (per-cut "trans" -> xfade type, overlap seconds)
TRANS = {
    "hard": ("fade", 0.06),
    "fade": ("fade", 0.28),
    "flash": ("fadewhite", 0.22),
    "zoom": ("zoomin", 0.32),
    "wipel": ("wipeleft", 0.30),
    "wiper": ("wiperight", 0.30),
    "slidel": ("slideleft", 0.30),
    "slideu": ("slideup", 0.30),
    "smoothl": ("smoothleft", 0.32),
    "circle": ("circleopen", 0.34),
    "dissolve": ("dissolve", 0.30),
}

LUTS = {
    "kodak": Path.home() / ".claude/skills/video-generation/luts/_sanitized_Kodak2383_D55.cube",
}


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        sys.stderr.write(f"\n[FFMPEG ERR] {' '.join(str(c) for c in cmd[:6])}...\n{r.stderr[-1500:]}\n")
        raise SystemExit(1)
    return r


def dur_of(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(r.stdout.strip())


def punch_vf(fx, dur, frames):
    """Scale/crop to WxH then a slow MOVING zoom via zoompan d=1.

    d=1 = one output frame per INPUT frame -> native Veo motion preserved
    (d=N froze the clip into a still). Zoom animates on the global 'on' counter,
    rate normalized so travel completes across the slot regardless of duration.
    """
    base = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
    nfr = max(2, int(round(dur * FPS)))
    Z = 0.14  # total zoom travel
    rate = Z / nfr
    center = f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if fx == "in":
        z = f"min(1.0+{rate:.6f}*on,{1.0+Z:.3f})"
    elif fx == "out":
        z = f"max({1.0+Z:.3f}-{rate:.6f}*on,1.0)"
    elif fx in ("left", "right"):
        sgn = "+" if fx == "right" else "-"
        z = "1.10"
        center = (f"x='iw/2-(iw/zoom/2){sgn}(iw-iw/zoom)*(on/{nfr}-0.5)':"
                  f"y='ih/2-(ih/zoom/2)'")
    else:
        return base  # none — full native motion, no move
    return (f"{base},zoompan=z='{z}':d=1:{center}:s={W}x{H}:fps={FPS}")


def normalize_slot(idx, slot, no_cache):
    out = TMP / f"slot_{idx:02d}.mp4"
    dur = slot["dur"]
    frames = max(2, int(round(dur * FPS)) + 2)
    if out.exists() and not no_cache:
        if abs(dur_of(out) - dur) < 0.15:
            return out
    src = BASE / slot["clip"]
    sdur = dur_of(src)
    vf = punch_vf(slot.get("fx", "in"), dur, frames)
    # loop short source if needed
    inputs = ["-i", str(src)]
    if sdur < dur + 0.05:
        inputs = ["-stream_loop", "2", "-i", str(src)]
    run(["ffmpeg", "-y", "-v", "error", *inputs,
         "-t", f"{dur:.3f}", "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", str(FPS), str(out)])
    return out


def build_visual(slots, norm_paths, out):
    """xfade chain with per-cut transitions. trans on slot[i] = how slot[i] ENTERS (cut from i-1)."""
    n = len(slots)
    if n == 1:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(norm_paths[0]), "-c", "copy", str(out)])
        return
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for p in norm_paths:
        cmd += ["-i", str(p)]
    fc = []
    durs = [dur_of(p) for p in norm_paths]
    prev = "0:v"
    offset = durs[0]
    cum = durs[0]
    for i in range(1, n):
        ttype, ov = TRANS.get(slots[i].get("trans", "hard"), TRANS["hard"])
        ov = min(ov, durs[i] - 0.1, durs[i - 1] - 0.1)
        off = cum - ov
        lbl = f"x{i}"
        fc.append(f"[{prev}][{i}:v]xfade=transition={ttype}:duration={ov:.3f}:offset={off:.3f}[{lbl}]")
        prev = lbl
        cum = off + durs[i]
    fc_str = ";".join(fc)
    cmd += ["-filter_complex", fc_str, "-map", f"[{prev}]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    run(cmd)
    return cum


def burn_caps_grade(visual, caps, out, lut):
    caps_esc = str(caps).replace("\\", "/").replace(":", "\\:")
    vf = f"ass='{caps_esc}'"
    if lut and lut in LUTS and LUTS[lut].exists():
        lp = str(LUTS[lut]).replace("\\", "/").replace(":", "\\:")
        # sanitize LUT_3D_INPUT_RANGE
        raw = LUTS[lut].read_text(errors="ignore")
        if "LUT_3D_INPUT_RANGE" in raw:
            tmp = TMP / "lut_clean.cube"
            tmp.write_text("\n".join(l for l in raw.splitlines() if not l.startswith("LUT_3D_INPUT_RANGE")))
            lp = str(tmp).replace("\\", "/").replace(":", "\\:")
        vf = f"lut3d='{lp}':interp=tetrahedral,eq=saturation=1.06:contrast=1.04,{vf}"
    else:
        vf = f"eq=saturation=1.10:contrast=1.05,vignette=PI/5,{vf}"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(visual), "-vf", vf,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", str(out)])


def build_audio(spec, vo, vdur, out):
    music = spec.get("music")
    mg = spec.get("music_gain", 0.18)
    sfx = spec.get("sfx", [])
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(BASE / vo)]
    idx = 1
    mlabel = None
    if music and (BASE / music).exists():
        cmd += ["-stream_loop", "-1", "-i", str(BASE / music)]
        mlabel = idx
        idx += 1
    sfx_idx = []
    for s in sfx:
        cmd += ["-i", str(BASE / s["file"])]
        sfx_idx.append((idx, s))
        idx += 1
    fc = []
    # VO: pad to video length, slight boost
    fc.append(f"[0:a]aresample=48000,apad,atrim=0:{vdur:.3f},volume=1.25[vo]")
    mix_inputs = ["[vo]"]
    if mlabel is not None:
        fc.append(f"[{mlabel}:a]aresample=48000,atrim=0:{vdur:.3f},volume={mg}[mus]")
        # sidechain duck music under VO
        fc.append("[mus][vo]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300:makeup=1[mduck]")
        mix_inputs.append("[mduck]")
    for i, (ii, s) in enumerate(sfx_idx):
        at = s["at"]
        g = s.get("gain", 0.8)
        fc.append(f"[{ii}:a]aresample=48000,volume={g},adelay={int(at*1000)}|{int(at*1000)}[sfx{i}]")
        mix_inputs.append(f"[sfx{i}]")
    fc.append("".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=first:normalize=0[mx]")
    fc.append("[mx]loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[out]", "-ar", "48000", str(out)]
    run(cmd)


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    tl_path, vo, caps, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    lut = None
    no_cache = "--no-cache" in sys.argv
    if "--lut" in sys.argv:
        lut = sys.argv[sys.argv.index("--lut") + 1]
    spec = json.loads((BASE / tl_path).read_text(encoding="utf-8"))
    slots = spec["slots"]
    Path(BASE / out).parent.mkdir(parents=True, exist_ok=True)

    print(f"normalizing {len(slots)} slots...", flush=True)
    norm = [normalize_slot(i, s, no_cache) for i, s in enumerate(slots)]

    visual = TMP / "_visual.mp4"
    print("building xfade chain...", flush=True)
    vdur = build_visual(slots, norm, visual)
    vdur = dur_of(visual)
    print(f"visual dur = {vdur:.2f}s", flush=True)

    graded = TMP / "_graded.mp4"
    print("captions + grade...", flush=True)
    burn_caps_grade(visual, BASE / caps, graded, lut)

    aud = TMP / "_audio.wav"
    print("audio mix...", flush=True)
    build_audio(spec, vo, vdur, aud)

    print("mux final...", flush=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(graded), "-i", str(aud),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", str(BASE / out)])
    print(f"DONE -> {out} ({dur_of(BASE / out):.2f}s)", flush=True)


if __name__ == "__main__":
    main()
