#!/usr/bin/env python3
"""
gen_subs.py — Convert SRT to ASS subtitles for vertical reels (1080x1920)

Splits text into 3-word chunks for TikTok-style pacing.
Two font presets: Impact (bold meme style) and Helvetica (clean talking-head style).

Usage:
    python3 gen_subs.py input.srt output.ass
    python3 gen_subs.py input.srt output.ass --font helvetica
    python3 gen_subs.py input.srt output.ass --offset 5.0
    python3 gen_subs.py input.srt output.ass --max-words 2
"""

import argparse
import re
import os


ASS_HEADER_TEMPLATE = """[Script Info]
Title: Reel Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

STYLES = {
    # Impact: 90pt, 8px outline — bold TikTok/meme style
    "impact": "Style: Default,Impact,90,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,2,60,60,480,1",
    # Helvetica Neue: 80pt, 3px outline — clean talking-head style
    "helvetica": "Style: Default,Helvetica Neue,80,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,3,0,2,60,60,480,1",
}


def parse_srt_time(s):
    """Parse SRT timestamp '00:00:01,234' to float seconds."""
    s = s.strip().replace(',', '.')
    h, m, rest = s.split(':')
    sec, ms = rest.split('.')
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def fmt_ass_time(t):
    """Format float seconds to ASS timestamp '0:00:01.23'."""
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    cs = round((s - int(s)) * 100)
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def chunk_words(text, max_words=3):
    """Split text into chunks of max N words for subtitle pacing."""
    words = text.split()
    return [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def srt_to_ass(srt_path, ass_path, offset=0.0, max_words=3, font="impact"):
    """Convert SRT file to ASS with word chunking and style selection."""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'\n\n+', content.strip())
    entries = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        m = re.match(r'(\S+)\s+-->\s+(\S+)', lines[1])
        if not m:
            continue
        t_start = parse_srt_time(m.group(1)) + offset
        t_end = parse_srt_time(m.group(2)) + offset
        text = ' '.join(lines[2:]).strip()

        chunks = chunk_words(text, max_words)
        if not chunks:
            continue
        duration = t_end - t_start
        chunk_dur = duration / len(chunks)
        for i, chunk in enumerate(chunks):
            cs = t_start + i * chunk_dur
            ce = cs + chunk_dur
            entries.append((fmt_ass_time(cs), fmt_ass_time(ce), chunk))

    style_line = STYLES.get(font, STYLES["impact"])
    header = ASS_HEADER_TEMPLATE.format(style_line=style_line)

    os.makedirs(os.path.dirname(ass_path) if os.path.dirname(ass_path) else '.', exist_ok=True)
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for s, e, t in entries:
            f.write(f"Dialogue: 0,{s},{e},Default,,0,0,0,,{t}\n")

    print(f"Done: {len(entries)} subtitle chunks (offset={offset:.2f}s, font={font}) -> {ass_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert SRT to ASS subtitles for vertical reels")
    parser.add_argument("srt", help="Input SRT file")
    parser.add_argument("ass", help="Output ASS file")
    parser.add_argument("--offset", type=float, default=0.0,
                        help="Time offset in seconds (e.g. for intro duration)")
    parser.add_argument("--max-words", type=int, default=3,
                        help="Max words per subtitle chunk (default: 3)")
    parser.add_argument("--font", choices=list(STYLES.keys()), default="impact",
                        help="Font style: impact (default) or helvetica")
    args = parser.parse_args()
    srt_to_ass(args.srt, args.ass, offset=args.offset, max_words=args.max_words, font=args.font)
