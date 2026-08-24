#!/usr/bin/env python3
"""Reusable cover generator for habr-post pipeline via Gemini 3.1 Flash Image.

Generates a 1408x768 native cover plus 1200x675 web crop.

Usage:
    python gen_cover.py --workdir ./article-myslug \\
        --theme "personal AI workspace" \\
        --visual-core "laptop with knowledge graph; lavalier mic on desk; hand-drawn diagram in notebook" \\
        --negative-extra ""

Notes:
- Needs GOOGLE_API_KEY (paid, https://ai.google.dev). Read from the environment first,
  then from ~/.claude/.credentials.master.env if you keep one (template:
  ~/.claude/templates/.credentials.master.env.example)
- Pops GEMINI_API_KEY (SDK conflict)
- Model: gemini-3.1-flash-image-preview (mandatory for editorial covers)
"""
import argparse
import io
import os
import sys
from pathlib import Path

try:
    from dotenv import dotenv_values
except ImportError:  # python-dotenv is optional: env var alone is enough
    dotenv_values = None

DEFAULT_NEGATIVE = (
    "Strictly NO: glowing AI brain, neon HUD, robot hands, holograms, "
    "code on screens that's actually readable, floating UI elements, "
    "generic stock-photo handshakes, faces, sci-fi visual clichés, "
    "generative-art swooshes."
)


def make_prompt(theme: str, visual_core: str, negative_extra: str = "") -> str:
    negative = DEFAULT_NEGATIVE
    if negative_extra:
        negative += " " + negative_extra
    return f"""Editorial photograph, 16:9 aspect, 1408x768.

Theme: {theme}.

Scene: {visual_core}

Soft personal atmosphere — workspace lighting, late afternoon or golden hour
(warm window light from one side). Wooden surfaces preferred over plastic.
A small hand-written touch (paper notebook, sketch, ceramic mug) keeps
the frame human.

Color grade: Kodak Portra 400 — warm tones, soft contrast, gentle film grain.
Camera: Sony A7R IV with Sigma 35mm f/1.4, shallow depth of field, focus on
the foreground objects.

Mood: contemplative engineering, careful craftsmanship, personal project.
{negative}
"""


def generate(workdir: Path, theme: str, visual_core: str, negative_extra: str = "") -> Path:
    # Environment wins; the dotenv file is a convenience, not a requirement.
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        env_file = Path.home() / ".claude" / ".credentials.master.env"
        if env_file.exists() and dotenv_values is not None:
            google_api_key = dotenv_values(env_file).get("GOOGLE_API_KEY")
    if not google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY not set. Get one at https://ai.google.dev (image generation "
            "is billed), then: export GOOGLE_API_KEY=... , or put it in "
            "~/.claude/.credentials.master.env")
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ.pop("GEMINI_API_KEY", None)

    from google import genai
    from google.genai import types
    from PIL import Image

    workdir = workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    prompt = make_prompt(theme, visual_core, negative_extra)

    client = genai.Client()
    print("Generating with gemini-3.1-flash-image-preview...")
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    saved = None
    for cand in (response.candidates or []):
        content = cand.content
        if not content or not content.parts:
            continue
        for part in content.parts:
            inline = getattr(part, "inline_data", None)
            if not inline or not inline.data:
                continue
            blob = inline.data
            img = Image.open(io.BytesIO(blob))
            ext = (img.format or "PNG").lower()
            if ext == "jpeg":
                ext = "jpg"
            cover_path = workdir / f"cover.{ext}"
            cover_path.write_bytes(blob)
            print(f"Saved: {cover_path} ({len(blob)} bytes, "
                  f"{img.size[0]}x{img.size[1]} {img.format})")
            saved = cover_path
            break
        if saved:
            break

    if not saved:
        raise RuntimeError("No image returned by Gemini")

    png_path = workdir / "cover.png"
    img = Image.open(saved)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(png_path, "PNG")
    print(f"PNG re-export: {png_path} ({png_path.stat().st_size} bytes)")

    web_path = workdir / "cover-1200.jpg"
    target_w, target_h = 1200, 675
    src_w, src_h = img.size
    src_aspect = src_w / src_h
    tgt_aspect = target_w / target_h
    if src_aspect > tgt_aspect:
        new_w = int(src_h * tgt_aspect)
        x = (src_w - new_w) // 2
        crop = img.crop((x, 0, x + new_w, src_h))
    else:
        new_h = int(src_w / tgt_aspect)
        y = (src_h - new_h) // 2
        crop = img.crop((0, y, src_w, y + new_h))
    crop = crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
    crop.save(web_path, "JPEG", quality=88)
    print(f"Web 1200x675: {web_path} ({web_path.stat().st_size} bytes)")

    meta = workdir / "ILLUSTRATION.md"
    meta.write_text(
        f"# Cover image — {theme}\n\n"
        f"**Model:** gemini-3.1-flash-image-preview\n"
        f"**Native size:** {img.size[0]}x{img.size[1]}\n"
        f"**Web crop:** 1200x675\n\n"
        f"## Theme\n\n{theme}\n\n"
        f"## Visual core\n\n{visual_core}\n\n"
        f"## Full prompt\n\n```\n{prompt}\n```\n",
        encoding="utf-8",
    )
    print(f"Metadata: {meta}")
    return saved


def main():
    parser = argparse.ArgumentParser(description="Generate cover via Gemini 3.1 Flash Image")
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--theme", required=True,
                        help="One-line theme, e.g. 'personal AI workspace'")
    parser.add_argument("--visual-core", required=True,
                        help="What's in the frame (concrete objects)")
    parser.add_argument("--negative-extra", default="",
                        help="Extra negative-prompt items beyond defaults")
    args = parser.parse_args()

    try:
        generate(args.workdir, args.theme, args.visual_core, args.negative_extra)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
