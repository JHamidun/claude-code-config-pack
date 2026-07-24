#!/usr/bin/env python3
"""Animated word-highlight captions (CapCut/Hormozi style) — fast path via captacity.

Usage:
  python add_captions.py in.mp4 out.mp4 --style hormozi
  python add_captions.py in.mp4 out.mp4 --style mrbeast|minimal --font "C:/Windows/Fonts/arialbd.ttf"

Deps: pip install captacity  (downloads a Whisper model on first run; or pass --openai-key
to transcribe via API). For Russian word-level precision prefer karaoke_captions.py (WhisperX).
"""
import argparse
import sys

STYLES = {
    "hormozi": dict(font_color="white", word_highlight_color="#FF6B35", font_size=130, line_count=1),
    "mrbeast": dict(font_color="yellow", word_highlight_color="red", font_size=140, line_count=1),
    "minimal": dict(font_color="white", word_highlight_color="#00FFFF", font_size=100, line_count=2),
}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--style", default="hormozi", choices=list(STYLES))
    ap.add_argument("--font", default="C:/Windows/Fonts/arialbd.ttf")
    ap.add_argument("--openai-key", default=None)
    a = ap.parse_args()
    import captacity
    cfg = STYLES[a.style]
    kw = dict(video_file=a.input, output_file=a.output, font=a.font,
              font_size=cfg["font_size"], font_color=cfg["font_color"],
              stroke_width=4, stroke_color="black", shadow_strength=1.0, shadow_blur=0.1,
              highlight_current_word=True, word_highlight_color=cfg["word_highlight_color"],
              line_count=cfg["line_count"], padding=50)
    if a.openai_key:
        kw["openai_api_key"] = a.openai_key
    captacity.add_captions(**kw)
    print("captioned:", a.output)


if __name__ == "__main__":
    main()
