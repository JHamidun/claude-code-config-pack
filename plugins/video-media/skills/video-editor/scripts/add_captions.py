#!/usr/bin/env python3
"""Animated word-highlight captions (CapCut/Hormozi style) — fast path via captacity.

Usage:
  python add_captions.py in.mp4 out.mp4 --style hormozi
  python add_captions.py in.mp4 out.mp4 --style mrbeast|minimal --font /path/to/Bold.ttf

Шрифт без --font подбирается сам: системный жирный (Windows/macOS/Linux), иначе тот,
что едет в паке (skills/canvas-design/canvas-fonts/Montserrat-Bold.ttf, OFL, кириллица
есть). Не нашлось ничего — скрипт скажет об этом словами, а не `cannot open resource`.

Deps: pip install captacity  (downloads a Whisper model on first run; or pass --openai-key
to transcribe via API). For Russian word-level precision prefer karaoke_captions.py (WhisperX).
"""
import argparse
import os
import sys

# Жёсткий "C:/Windows/Fonts/arialbd.ttf" в default аргумента был путём машины автора:
# на macOS и Linux его нет, и captacity падал с `OSError: cannot open resource` уже
# после того, как скачал модель Whisper и прогнал транскрипцию.
_SYS_FONTS_BOLD = (
    "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
)


def resolve_font(explicit=None):
    """Путь к жирному TTF, который существует на ЭТОЙ машине.

    Порядок: --font → VIDEO_FONT_BOLD → системные шрифты трёх ОС → шрифт из пака.
    Явно указанный несуществующий путь — отдельная ошибка: молча подменять его
    другим шрифтом нельзя, человек просил конкретный.
    """
    if explicit:
        if not os.path.exists(explicit):
            sys.exit("Шрифт не найден по указанному --font: %s" % explicit)
        return explicit
    bundled = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "canvas-design", "canvas-fonts", "Montserrat-Bold.ttf")
    env = os.environ.get("VIDEO_FONT_BOLD")
    tried = []
    for cand in ([env] if env else []) + list(_SYS_FONTS_BOLD) + [bundled]:
        tried.append(cand)
        if cand and os.path.exists(cand):
            return cand
    sys.exit(
        "Жирный шрифт не найден — субтитры рисовать нечем.\n"
        "  Искал: " + "\n         ".join(tried) + "\n"
        "  Почини: передай --font /путь/к/Bold.ttf, задай VIDEO_FONT_BOLD\n"
        "  или поставь системные шрифты (Linux: fonts-dejavu-core / fonts-liberation).\n"
        "  Запасной шрифт пака должен лежать здесь: %s" % bundled
    )


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
    ap.add_argument("--font", default=None, help="TTF; по умолчанию подбирается сам (см. resolve_font)")
    ap.add_argument("--openai-key", default=None)
    a = ap.parse_args()
    font = resolve_font(a.font)   # до import captacity: отказ должен прийти ДО скачивания модели
    import captacity
    cfg = STYLES[a.style]
    kw = dict(video_file=a.input, output_file=a.output, font=font,
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
