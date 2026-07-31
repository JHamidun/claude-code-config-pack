#!/usr/bin/env python3
"""Viral karaoke captions (word-by-word highlight) — WhisperX → ASS \\kf → ffmpeg burn.

PRIMARY caption engine (works with moviepy 2.x; captacity does not). Word-level timing
to <100ms, great for Russian. Also accepts pre-known word timings (e.g. from ElevenLabs
TTS-with-timestamps) so you can skip ASR entirely when you authored the script.

Usage:
  python karaoke_captions.py in.mp4 out.mp4 --lang ru                 # transcribe + burn
  python karaoke_captions.py in.mp4 out.mp4 --lang ru --device cuda   # GPU
  python karaoke_captions.py in.mp4 out.mp4 --words-per-line 4 --style hormozi
  python karaoke_captions.py in.mp4 out.mp4 --words-json words.json   # skip ASR (provide timings)
    words.json = [{"word":"привет","start":0.1,"end":0.5}, ...]

Deps: pip install whisperx torch   (first run downloads large-v3 ~3GB; CPU works, GPU faster)
"""
import argparse
import json
import os
import subprocess
import sys

# ASS BGR colors (&HAABBGGRR). Primary = highlight (filled), Secondary = base (unfilled).
STYLES = {
    "hormozi": dict(font="Arial", size=90, primary="&H0000FFFF", secondary="&H00FFFFFF", outline=5, shadow=3),
    "mrbeast": dict(font="Arial", size=100, primary="&H000000FF", secondary="&H0000FFFF", outline=6, shadow=2),
    "minimal": dict(font="Arial", size=80, primary="&H00FFFF00", secondary="&H00FFFFFF", outline=3, shadow=1),
}

# Auto-fit so long RU words/lines never spill off-screen (CRITICAL: a single long word
# like "ПРАВДОПОДОБНОСТИ" at size 90 overflows 1080px). Per-line `\fs` shrinks to the
# safe width; WrapStyle 0 wraps as a last resort. GLYPH ≈ uppercase advance / fontsize.
MARGIN = 70
GLYPH = 0.60


def fit_size(text, base_size, frame_w):
    safe = frame_w - 2 * MARGIN
    n = max(1, len(text))
    return max(48, min(base_size, int(safe / (n * GLYPH))))


def transcribe(video, lang, device):
    import whisperx
    audio = whisperx.load_audio(video)
    compute = "float16" if device == "cuda" else "int8"
    model = whisperx.load_model("large-v3", device, compute_type=compute)
    res = model.transcribe(audio, batch_size=16, language=lang)
    amodel, meta = whisperx.load_align_model(language_code=res["language"], device=device)
    res = whisperx.align(res["segments"], amodel, meta, audio, device)
    return res["segments"]


def ts(t):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return "%d:%02d:%02d.%02d" % (int(h), int(m), int(s), int((s % 1) * 100))


def build_ass(segments, res, wpl, st):
    W, H = res
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, "
            "Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Viral,%s,%d,%s,%s,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,%d,%d,2,%d,%d,260,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            % (W, H, st["font"], st["size"], st["primary"], st["secondary"], st["outline"], st["shadow"],
               MARGIN, MARGIN))
    ev = []
    for seg in segments:
        words = seg.get("words", [])
        for i in range(0, len(words), wpl):
            chunk = words[i:i + wpl]
            if not chunk:
                continue
            t0 = chunk[0].get("start", seg.get("start", 0)) or seg.get("start", 0)
            t1 = chunk[-1].get("end", seg.get("end", t0)) or seg.get("end", t0)
            plain = " ".join(w["word"].strip().upper() for w in chunk)
            fs = fit_size(plain, st["size"], W)   # shrink long lines so they never spill off-screen
            text = " ".join("{\\kf%d}%s" % (max(1, int(((w.get("end", t1) or t1) - (w.get("start", t0) or t0)) * 100)),
                                            w["word"].strip().upper()) for w in chunk)
            ev.append("Dialogue: 0,%s,%s,Viral,,0,0,0,,{\\fs%d}%s" % (ts(t0), ts(t1), fs, text))
    return head + "\n".join(ev)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--lang", default="ru")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--words-per-line", type=int, default=4)
    ap.add_argument("--style", default="hormozi", choices=list(STYLES))
    ap.add_argument("--words-json", default=None, help="provide word timings, skip ASR")
    ap.add_argument("--res", default="1080x1920")
    a = ap.parse_args()
    W, H = (int(x) for x in a.res.split("x"))
    if a.words_json:
        words = json.load(open(a.words_json, encoding="utf-8"))
        segments = [{"start": words[0]["start"], "end": words[-1]["end"], "words": words}]
    else:
        print("transcribing (%s, %s)..." % (a.lang, a.device))
        segments = transcribe(a.input, a.lang, a.device)
    ass = a.input.rsplit(".", 1)[0] + "_caps.ass"
    open(ass, "w", encoding="utf-8").write(build_ass(segments, (W, H), a.words_per_line, STYLES[a.style]))
    print("ASS:", ass)
    # Windows ffmpeg `ass` filter chokes on the drive colon in the path (two-level escaping
    # is unreliable across shells). Bulletproof: run ffmpeg from the .ass dir and reference
    # it by BASENAME (no colon in the filter arg); input/output stay absolute (those are -i/out args).
    ass_dir = os.path.dirname(os.path.abspath(ass)) or "."
    ass_base = os.path.basename(ass)
    subprocess.run(["ffmpeg", "-y", "-i", os.path.abspath(a.input), "-vf", "ass=%s" % ass_base,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy",
                    os.path.abspath(a.output)], check=True, cwd=ass_dir)
    print("captioned:", a.output)


if __name__ == "__main__":
    main()
