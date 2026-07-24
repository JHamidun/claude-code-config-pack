#!/usr/bin/env python3
"""
gen_text_overlay.py — Generate styled text overlay PNG for vertical reels (1080x1920)

Features:
- Multiple font presets (Impact, Helvetica, Arial Black, etc.)
- Auto font-size reduction when text is too tall
- Sentence-aware word wrap
- Text outline + shadow for readability on any background
- Three position presets: center, lower_third, upper_third

Usage:
    python3 gen_text_overlay.py --text "Your quote here" --output overlay.png
    python3 gen_text_overlay.py --text "Long text" --output overlay.png --font Helvetica --font-size 50
    python3 gen_text_overlay.py --text "Bottom text" --output overlay.png --position lower_third

Requirements:
    pip install Pillow
"""

import argparse
import os
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

CANVAS_W = 1080
CANVAS_H = 1920

# Font presets — macOS paths. Adjust for your OS if needed.
FONTS = {
    "Impact": ("/System/Library/Fonts/Supplemental/Impact.ttf", 0),
    "ArialBlack": ("/System/Library/Fonts/Supplemental/Arial Black.ttf", 0),
    "ArialBold": ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
    "DIN": ("/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf", 0),
    "Trebuchet": ("/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf", 0),
    "Verdana": ("/System/Library/Fonts/Supplemental/Verdana Bold.ttf", 0),
    "Helvetica": ("/System/Library/Fonts/HelveticaNeue.ttc", 1),        # Bold
    "HelveticaBlack": ("/System/Library/Fonts/HelveticaNeue.ttc", 9),    # Condensed Black
    "SFPro": ("/System/Library/Fonts/SFNS.ttf", 0),
    "Typewriter": ("/System/Library/Fonts/Supplemental/AmericanTypewriter.ttc", 0),
    "CourierBold": ("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 0),
}

POSITIONS = {
    "center": lambda block_h: (CANVAS_H - block_h) // 2,
    "lower_third": lambda block_h: 1280,
    "upper_third": lambda block_h: 480,
}

DEFAULT_STYLE = {
    "font": "Helvetica",
    "font_size": 50,
    "color": (255, 255, 255),
    "outline_color": (0, 0, 0),
    "outline_width": 3,
    "shadow": True,
    "shadow_offset": (3, 3),
    "shadow_color": (0, 0, 0, 100),
    "position": "center",
    "max_chars_per_line": 30,
    "line_spacing": 14,
}


def draw_text_with_outline(draw, pos, text, font, fill, outline, outline_width):
    """Draw text with pixel-based outline for readability on any background."""
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def render_text_overlay(text, output_path, style=None):
    """Render styled text onto a 1080x1920 transparent PNG."""
    s = {**DEFAULT_STYLE, **(style or {})}

    for key in ("color", "outline_color", "shadow_color", "shadow_offset"):
        if isinstance(s[key], list):
            s[key] = tuple(s[key])

    font_entry = FONTS.get(s["font"], s["font"])
    if isinstance(font_entry, tuple):
        font_path, font_index = font_entry
    else:
        font_path, font_index = font_entry, 0
    font_size = s["font_size"]

    # Sentence-aware word wrap
    sentences = re.split(r'(?<=[.!?])\s+', text)
    lines = []
    for sent in sentences:
        wrapped = textwrap.wrap(sent, width=s["max_chars_per_line"])
        lines.extend(wrapped)

    # Auto-reduce font size if text block exceeds 70% of canvas height
    max_block_h = int(CANVAS_H * 0.70)
    while font_size > 36:
        font = ImageFont.truetype(font_path, font_size, index=font_index)
        block_h = _measure_block_height(font, lines, s["line_spacing"])
        if block_h <= max_block_h:
            break
        font_size -= 4
    else:
        font = ImageFont.truetype(font_path, font_size, index=font_index)

    if font_size != s["font_size"]:
        print(f"  Auto-reduced font: {s['font_size']}pt -> {font_size}pt")

    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    block_h = _measure_block_height(font, lines, s["line_spacing"])
    pos_fn = POSITIONS.get(s["position"], POSITIONS["center"])
    y = pos_fn(block_h)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = (CANVAS_W - line_w) // 2

        if s["shadow"]:
            sx, sy = s["shadow_offset"]
            draw.text((x + sx, y + sy), line, font=font, fill=s["shadow_color"])

        draw_text_with_outline(
            draw, (x, y), line, font,
            fill=s["color"],
            outline=s["outline_color"],
            outline_width=s["outline_width"],
        )

        y += line_h + s["line_spacing"]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    print(f"  Overlay: {output_path} ({CANVAS_W}x{CANVAS_H}, {len(lines)} lines, {font_size}pt)")
    return output_path


def _measure_block_height(font, lines, line_spacing):
    """Measure total pixel height of text block."""
    if not lines:
        return 0
    tmp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(tmp)
    total = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        total += bbox[3] - bbox[1]
        if i < len(lines) - 1:
            total += line_spacing
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate text overlay PNG for vertical reels")
    parser.add_argument("--text", required=True, help="Text to render")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--font", default="Helvetica", choices=list(FONTS.keys()),
                        help="Font preset (default: Helvetica)")
    parser.add_argument("--font-size", type=int, default=50,
                        help="Font size in pt (default: 50, auto-reduces if too tall)")
    parser.add_argument("--position", default="center", choices=list(POSITIONS.keys()),
                        help="Text position: center, lower_third, upper_third")
    parser.add_argument("--max-chars", type=int, default=30,
                        help="Max characters per line for word wrap (default: 30)")
    parser.add_argument("--outline-width", type=int, default=3,
                        help="Outline thickness in px (default: 3)")
    args = parser.parse_args()

    render_text_overlay(
        args.text,
        os.path.expanduser(args.output),
        style={
            "font": args.font,
            "font_size": args.font_size,
            "position": args.position,
            "max_chars_per_line": args.max_chars,
            "outline_width": args.outline_width,
        },
    )
