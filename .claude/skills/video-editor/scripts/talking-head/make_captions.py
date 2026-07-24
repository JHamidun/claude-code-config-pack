#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Viral word-pop karaoke captions (CapCut/Hormozi style) from remapped words.

One Dialogue per word-state: whole line visible, active word highlighted +
line pop-in on first word. Uppercase, Segoe UI Black, thick outline.

Usage: python make_captions.py words_r1.json build/caps_r1.ass [--y 1290]
"""
import json
import re
import sys
from pathlib import Path

W, H = 1080, 1920
FONT = "Segoe UI Black"
SIZE = 84            # base size; auto-shrinks per line to fit safe width
MIN_SIZE = 52
MARGIN = 70         # L/R safe margin
SAFE_W = W - 2 * MARGIN          # 940px usable
GLYPH = 0.60        # avg uppercase glyph advance as fraction of fontsize (Segoe UI Black)
ACTIVE = 1.06       # active-word scale (was 1.08 — narrower to avoid edge spill)
MAX_WORDS = 3
GAP_BREAK = 0.75   # new line if pause between words exceeds this


def fit_size(text):
    """Largest font size (<=SIZE) whose rendered width fits SAFE_W (accounting for
    the active word being ACTIVE× wider). Falls back to MIN_SIZE; libass WrapStyle
    will wrap if even MIN_SIZE overflows."""
    n = max(1, len(text))
    eff = n + 1.0  # +1 for the enlarged active word
    size = int(SAFE_W / (eff * GLYPH))
    return max(MIN_SIZE, min(SIZE, size))

WHITE = r"\c&HFFFFFF&"
YELLOW = r"\c&H00D4FF&"   # active word
GREEN = r"\c&H7EE050&"
RED = r"\c&H4040FF&"

EMPH = {
    "забирайте": RED, "бесплатную": GREEN, "бесплатная": GREEN, "плюшку": GREEN,
    "лид-магнит": GREEN, "оффер": GREEN, "клиентов": YELLOW, "доверие": GREEN,
    "завирусится": RED, "офигеть": RED, "30-минутную": GREEN,
}


def clean(w):
    return w.strip()


def lines_from_words(words):
    lines = []
    cur = []
    for w in words:
        if cur:
            prev = cur[-1]
            brk = (w["s"] - prev["e"] > GAP_BREAK) or len(cur) >= MAX_WORDS \
                  or re.search(r"[.!?…]$", prev["w"]) or (re.search(r",$", prev["w"]) and len(cur) >= 2)
            if brk:
                lines.append(cur)
                cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def fmt_t(t):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(w):
    return w.replace("{", "").replace("}", "").upper()


def main():
    words_path, out_path = sys.argv[1], sys.argv[2]
    y = 1290
    if "--y" in sys.argv:
        y = int(sys.argv[sys.argv.index("--y") + 1])
    words = json.loads(Path(words_path).read_text(encoding="utf-8"))

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},{SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,{MARGIN},{MARGIN},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    act = int(ACTIVE * 100)
    ev = []
    for line in lines_from_words(words):
        line_end = line[-1]["e"] + 0.12
        plain = " ".join(esc(clean(w["w"])) for w in line)
        fs = fit_size(plain)            # per-line size that fits the safe width
        for i, w in enumerate(line):
            ws = w["s"]
            we = line[i + 1]["s"] if i + 1 < len(line) else line_end
            if we <= ws:
                we = ws + 0.05
            parts = []
            for j, w2 in enumerate(line):
                token = esc(clean(w2["w"]))
                if j == i:
                    color = EMPH.get(clean(w2["w"]).lower().strip(".,!?…"), YELLOW)
                    parts.append(r"{%s\fscx%d\fscy%d}%s{\fscx100\fscy100%s}" % (color, act, act, token, WHITE))
                else:
                    parts.append(token)
            text = " ".join(parts)
            pop = (r"{\an5\pos(540,%d)\fs%d\fscx90\fscy90\t(0,70,\fscx100\fscy100)}" % (y, fs)) if i == 0 \
                else (r"{\an5\pos(540,%d)\fs%d}" % (y, fs))
            ev.append(f"Dialogue: 0,{fmt_t(ws)},{fmt_t(we)},Cap,,0,0,0,,{pop}{text}")

    Path(out_path).write_text(header + "\n".join(ev) + "\n", encoding="utf-8")
    print(f"{out_path}: {len(ev)} events")


if __name__ == "__main__":
    main()
