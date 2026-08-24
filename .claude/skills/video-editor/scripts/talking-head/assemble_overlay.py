#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Talking-head reel: creator base (video+his synced audio) + AI b-roll OVERLAYS on top.

creator is the base; b-roll clips play fullscreen over chosen windows (hiding jump
cuts, illustrating speech) while HIS audio continues underneath. Then ending
(real CTA footage) is appended. Music bed ducked under voice + SFX + captions + LUT.

config json:
{
  "base": "build/base_r1.mp4",
  "ending": "broll/ending.mp4",
  "gap": 0.45,
  "music": "audio/suno_f3955f4e.mp3", "music_gain": 0.13,
  "overlays": [{"clip":"broll/r1_s03.mp4","t0":8.0,"t1":12.5,"fx":"in","trans":"flash"}],
  "sfx": [{"file":"audio/sfx_whoosh.mp3","at":8.0,"gain":0.8}]
}

Usage: python assemble_overlay.py cfg_r1.json words_base_r1_full.json final/reel1.mp4 --lut kodak
"""
import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
W, H, FPS = 1080, 1920, 30
TMP = BASE / "build" / "ov"   # каталог создаётся в main(), не при импорте
LUT = Path.home() / ".claude/skills/video-generation/luts/_sanitized_Kodak2383_D55.cube"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write("\n[ERR] " + " ".join(str(c) for c in cmd[:5]) + "\n" + r.stderr[-1800:] + "\n")
        raise SystemExit(1)
    return r


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)


def punch(fx, d):
    nfr = max(2, int(round(d * FPS)))
    Z = 0.14
    rate = Z / nfr
    c = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if fx == "in":
        z = f"min(1.0+{rate:.6f}*on,{1.0+Z:.3f})"
    elif fx == "out":
        z = f"max({1.0+Z:.3f}-{rate:.6f}*on,1.0)"
    elif fx in ("left", "right"):
        sgn = "+" if fx == "right" else "-"
        z = "1.10"
        c = f"x='iw/2-(iw/zoom/2){sgn}(iw-iw/zoom)*(on/{nfr}-0.5)':y='ih/2-(ih/zoom/2)'"
    else:
        return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
    return (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
            f"zoompan=z='{z}':d=1:{c}:s={W}x{H}:fps={FPS}")


def norm_overlay(idx, ov):
    """Normalize a b-roll clip to its window length with punch; silent."""
    out = TMP / f"ov_{idx:02d}.mp4"
    d = ov["t1"] - ov["t0"]
    src = BASE / ov["clip"]
    sdur = dur(src)
    inp = ["-stream_loop", "2", "-i", str(src)] if sdur < d + 0.05 else ["-i", str(src)]
    run(["ffmpeg", "-y", "-v", "error", *inp, "-t", f"{d:.3f}", "-vf", punch(ov.get("fx", "in"), d), "-an",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((BASE / sys.argv[1]).read_text(encoding="utf-8"))
    words = sys.argv[2]
    out = BASE / sys.argv[3]
    lut = "--lut" in sys.argv
    out.parent.mkdir(parents=True, exist_ok=True)

    base = BASE / cfg["base"]
    ending = BASE / cfg["ending"]
    gap = cfg.get("gap", 0.45)
    bdur = dur(base)
    edur = dur(ending)

    # 1) Concatenate base + gap(freeze last base frame) + ending -> full video+audio (creator's voice)
    #    Build via: base.mp4, gap silence with last frame held, ending.mp4
    full = TMP / "_full_base.mp4"
    # gap: hold last frame of base (extract still -> loop) + silent audio
    lastpng = TMP / "_last.png"
    run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.1", "-i", str(base), "-update", "1",
         "-vf", f"scale={W}:{H},setsar=1", "-frames:v", "1", str(lastpng)])
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{gap}", "-i", str(lastpng),
         "-f", "lavfi", "-t", f"{gap}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
         "-vf", f"fps={FPS},setsar=1", "-c:v", "libx264", "-preset", "fast", "-crf", "19",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(TMP / "_gap.mp4")])
    lst = TMP / "full_concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in [base, TMP / "_gap.mp4", ending]), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(full)])
    fdur = dur(full)
    print(f"full base (creator+ending): {fdur:.2f}s", flush=True)

    # 2) Normalize overlays + composite over full base video
    overlays = cfg.get("overlays", [])
    norm = [(norm_overlay(i, ov), ov) for i, ov in enumerate(overlays)]
    print(f"compositing {len(norm)} overlays...", flush=True)

    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(full)]
    for p, _ in norm:
        cmd += ["-i", str(p)]
    fc = []
    prev = "0:v"
    for i, (p, ov) in enumerate(norm):
        t0, t1 = ov["t0"], ov["t1"]
        inp = i + 1
        # shift overlay so its start aligns to t0; enable only within window
        fc.append(f"[{inp}:v]setpts=PTS-STARTPTS+{t0}/TB[s{i}]")
        nxt = f"o{i}"
        trans = ov.get("trans", "cut")
        if trans == "flash":
            # quick white flash at the cut via overlay of a white-ish boost is complex;
            # approximate with a short fade-in of the overlay opacity
            fc.append(f"[{prev}][s{i}]overlay=enable='between(t,{t0},{t1})':eof_action=pass[{nxt}]")
        else:
            fc.append(f"[{prev}][s{i}]overlay=enable='between(t,{t0},{t1})':eof_action=pass[{nxt}]")
        prev = nxt
    comp = TMP / "_comp.mp4"
    if norm:
        cmd += ["-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "0:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                "-c:a", "copy", str(comp)]
        run(cmd)
    else:
        comp = full

    # 3) Captions + grade
    graded = TMP / "_graded.mp4"
    caps_esc = str(BASE / words).replace("\\", "/")  # words is json -> need ass; build ass first
    # build ASS from words via make_captions
    ass = TMP / "_caps.ass"
    run([sys.executable, str(BASE / "make_captions.py"), str(BASE / words), str(ass)])
    ass_esc = str(ass).replace("\\", "/").replace(":", "\\:")
    vf = f"ass='{ass_esc}'"
    if lut and LUT.exists():
        lp = str(LUT).replace("\\", "/").replace(":", "\\:")
        # tame exposure BEFORE LUT: pull highlights down (no more blown white shirt/skin),
        # slightly lower mids; then LUT at reduced contrast so nothing clips.
        grade = (f"curves=all='0/0 0.5/0.45 1/0.86',eq=brightness=-0.04,"
                 f"lut3d='{lp}':interp=tetrahedral,eq=saturation=1.02")
        vf = f"{grade},{vf}"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(comp), "-vf", vf,
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "copy", str(graded)])

    # 4) Audio: his voice (from base) + PRESENT music (gentle duck) + tasteful SFX
    music = cfg.get("music")
    mg = cfg.get("music_gain", 0.38)        # louder bed by default
    sfx_gain_mul = cfg.get("sfx_gain", 0.35)  # SFX much quieter
    sfx = cfg.get("sfx", [])
    acmd = ["ffmpeg", "-y", "-v", "error", "-i", str(graded)]
    idx = 1
    fc = ["[0:a]aresample=48000,volume=1.22[vo]"]
    mix = ["[vo]"]
    if music and (BASE / music).exists():
        acmd += ["-stream_loop", "-1", "-i", str(BASE / music)]
        # music clearly UNDER voice: lower bed + deeper duck while he speaks
        fc.append(f"[{idx}:a]aresample=48000,atrim=0:{fdur:.3f},volume={mg}[mus]")
        fc.append("[mus][vo]sidechaincompress=threshold=0.06:ratio=5:attack=30:release=350:makeup=1[md]")
        mix.append("[md]")
        idx += 1
    for s in sfx:
        acmd += ["-i", str(BASE / s["file"])]
        at = s["at"]
        g = s.get("gain", 0.8) * sfx_gain_mul
        fc.append(f"[{idx}:a]aresample=48000,volume={g:.3f},adelay={int(at*1000)}|{int(at*1000)}[x{idx}]")
        mix.append(f"[x{idx}]")
        idx += 1
    fc.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0[mx]")
    fc.append("[mx]loudnorm=I=-14:TP=-1.5:LRA=11[oa]")
    acmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[oa]",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out)]
    run(acmd)
    print(f"DONE -> {sys.argv[3]} ({dur(out):.2f}s)", flush=True)


if __name__ == "__main__":
    main()
