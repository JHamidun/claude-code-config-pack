#!/usr/bin/env python3
"""Motion-graphics overlays for shortform — pure ffmpeg (+PIL for Cyrillic text).

Adds animated UI elements ONTO an existing video. No heavy deps (PIL only, already present).
For richer keyframed motion graphics (React) see references/remotion-overlays.md and
references/motion-graphics.md (movis).

Usage:
  python motion_graphics.py like-counter in.mp4 out.mp4 --to 15000 --start 1 --end 5
  python motion_graphics.py progress in.mp4 out.mp4 --start 2 --end 8 --color FF4444
  python motion_graphics.py countdown in.mp4 out.mp4 --from 3 --at 0
  python motion_graphics.py lower-third in.mp4 out.mp4 --name "Your Name" --sub "CPO YourProduct" --in 1 --out 6
  python motion_graphics.py pop in.mp4 out.mp4 --text "СКИДКА 50%" --at 3 --x 0.5 --y 0.4

Cyrillic-safe: lower-third & pop render text via PIL PNG (ffmpeg drawtext breaks on
Windows+Cyrillic). Numeric counters use drawtext (ASCII digits, safe).
"""
import argparse
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Шрифт. Жёсткий "C:/Windows/Fonts/arialbd.ttf" был путём машины автора: на macOS и
# Linux его нет. Ломалось по двум линиям сразу — PIL в _text_png (→ lower_third, pop)
# кидал `OSError: cannot open resource`, а ffmpeg drawtext в like_counter/countdown
# падал через subprocess(check=True). Из шести режимов уцелевал один (progress).
# Порядок: переменная окружения → системные шрифты трёх ОС → шрифт из самого пака
# (skills/canvas-design/canvas-fonts, OFL, кириллица есть). Ничего нет — громкий отказ.
# Ищем ЛЕНИВО, в момент отрисовки: иначе `--help` умирал бы вместе с поиском шрифта.
# ---------------------------------------------------------------------------
_SYS_FONTS_BOLD = (
    "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
)
_SYS_FONTS_REG = (
    "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
)


def font_path(bold=True):
    env = os.environ.get("VIDEO_FONT_BOLD" if bold else "VIDEO_FONT_REGULAR")
    bundled = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "canvas-design", "canvas-fonts",
        "Montserrat-Bold.ttf" if bold else "Montserrat-Regular.ttf")
    tried = []
    for cand in ([env] if env else []) + list(_SYS_FONTS_BOLD if bold else _SYS_FONTS_REG) + [bundled]:
        tried.append(cand)
        if cand and os.path.exists(cand):
            return cand
    sys.exit(
        "Шрифт не найден — рисовать оверлей нечем.\n"
        "  Искал: " + "\n         ".join(tried) + "\n"
        "  Почини одним из двух:\n"
        "    1) укажи свой TTF:  VIDEO_FONT_%s=/путь/к/шрифту.ttf\n"
        "    2) поставь системные шрифты: Linux — fonts-dejavu-core или fonts-liberation.\n"
        "  Запасной шрифт пака должен лежать здесь: %s" % ("BOLD" if bold else "REGULAR", bundled)
    )


def _font_ff(bold=True):
    """Тот же путь, но с экранированным двоеточием — этого требует ffmpeg drawtext."""
    return font_path(bold).replace(":", "\\:")


def _run(inp, out, vf):
    subprocess.run(["ffmpeg", "-y", "-i", inp, "-vf", vf,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", out], check=True)


def like_counter(a):
    vf = ("drawtext=fontfile='%s':text='%%{eif\\:min(%d*(t-%g)/%g\\,%d)\\:d}':"
          "x=(w-tw)/2:y=h*0.5:fontsize=110:fontcolor=white:borderw=6:bordercolor=black:"
          "enable='between(t,%g,%g)'" % (_font_ff(True), a.to, a.start, max(0.1, a.end - a.start), a.to, a.start, a.end))
    _run(a.input, a.output, vf)


def progress(a):
    vf = ("drawbox=x=0:y=ih-12:w='if(gt(t,%g),(t-%g)/(%g-%g)*iw,0)':h=12:color=0x%sFF:t=fill:"
          "enable='between(t,%g,%g)'" % (a.start, a.start, a.end, a.start, a.color, a.start, a.end))
    _run(a.input, a.output, vf)


def countdown(a):
    parts = []
    for k in range(a.frm, 0, -1):
        t0 = a.at + (a.frm - k)
        parts.append("drawtext=fontfile='%s':text='%d':x=(w-tw)/2:y=(h-th)/2:fontsize=240:"
                     "fontcolor=white:borderw=8:bordercolor=black:enable='between(t,%g,%g)'"
                     % (_font_ff(True), k, t0, t0 + 1))
    _run(a.input, a.output, ",".join(parts))


def _text_png(text, sub, png, fs=64, sfs=34):
    from PIL import Image, ImageDraw, ImageFont
    f1 = ImageFont.truetype(font_path(True), fs)
    f2 = ImageFont.truetype(font_path(False), sfs)
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    b1 = dummy.textbbox((0, 0), text, font=f1)
    tw = b1[2] - b1[0]
    th = b1[3] - b1[1]
    sh = 0
    if sub:
        b2 = dummy.textbbox((0, 0), sub, font=f2)
        tw = max(tw, b2[2] - b2[0]); sh = (b2[3] - b2[1]) + 14
    pad = 32
    W = tw + pad * 2
    H = th + sh + pad * 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.rounded_rectangle([0, 0, W, H], radius=18, fill=(15, 17, 22, 220))
    dr.rectangle([0, 0, 6, H], fill=(82, 136, 193, 255))
    dr.text((pad - b1[0], pad - b1[1]), text, font=f1, fill=(245, 238, 220, 255))
    if sub:
        dr.text((pad, pad + th + 10), sub, font=f2, fill=(212, 180, 120, 255))
    img.save(png)
    return W, H


def lower_third(a):
    png = a.output + ".lt.png"
    W, H = _text_png(a.name, a.sub, png)
    # slide in from left over 0.4s, hold, slide out
    fc = ("[1:v]format=rgba[lt];[0:v][lt]overlay="
          "x='if(lt(t,%g),-w, if(lt(t,%g+0.4),-w+(t-%g)/0.4*(60+w), 60))':"
          "y=H-h-80:enable='between(t,%g,%g)'" % (a.in_, a.in_, a.in_, a.in_, a.out_))
    subprocess.run(["ffmpeg", "-y", "-i", a.input, "-i", png, "-filter_complex", fc,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", a.output], check=True)
    os.remove(png)


def pop(a):
    png = a.output + ".pop.png"
    W, H = _text_png(a.text, None, png, fs=72)
    # fade-in pop at --at, positioned by normalized x/y, held for --dur (robust, no scale-eval)
    fc = ("[1:v]format=rgba,fade=t=in:st=%g:d=0.25:alpha=1[p];"
          "[0:v][p]overlay=x=(W-w)/2+(%g-0.5)*W:y=(H-h)/2+(%g-0.5)*H:"
          "enable='between(t,%g,%g)'" % (a.at, a.x, a.y, a.at, a.at + a.dur))
    subprocess.run(["ffmpeg", "-y", "-i", a.input, "-i", png, "-filter_complex", fc,
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", a.output], check=True)
    os.remove(png)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lc = sub.add_parser("like-counter"); lc.add_argument("input"); lc.add_argument("output"); lc.add_argument("--to", type=int, default=15000); lc.add_argument("--start", type=float, default=1); lc.add_argument("--end", type=float, default=5); lc.set_defaults(fn=like_counter)
    pr = sub.add_parser("progress"); pr.add_argument("input"); pr.add_argument("output"); pr.add_argument("--start", type=float, default=2); pr.add_argument("--end", type=float, default=8); pr.add_argument("--color", default="FF4444"); pr.set_defaults(fn=progress)
    cd = sub.add_parser("countdown"); cd.add_argument("input"); cd.add_argument("output"); cd.add_argument("--from", dest="frm", type=int, default=3); cd.add_argument("--at", type=float, default=0); cd.set_defaults(fn=countdown)
    lt = sub.add_parser("lower-third"); lt.add_argument("input"); lt.add_argument("output"); lt.add_argument("--name", required=True); lt.add_argument("--sub", default=""); lt.add_argument("--in", dest="in_", type=float, default=1); lt.add_argument("--out", dest="out_", type=float, default=6); lt.set_defaults(fn=lower_third)
    pp = sub.add_parser("pop"); pp.add_argument("input"); pp.add_argument("output"); pp.add_argument("--text", required=True); pp.add_argument("--at", type=float, default=3); pp.add_argument("--dur", type=float, default=2); pp.add_argument("--x", type=float, default=0.5); pp.add_argument("--y", type=float, default=0.4); pp.set_defaults(fn=pop)
    a = ap.parse_args()
    a.fn(a)
    print("saved", a.output)


if __name__ == "__main__":
    main()
