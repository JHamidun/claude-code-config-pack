#!/usr/bin/env python3
"""
ACE-Step 1.5 CLI wrapper for Claude Code.
Generates music via the running Gradio UI API at localhost:7860.

Usage:
    python generate.py "epic orchestral battle theme" --duration 120
    python generate.py "chill lofi hip-hop" --duration 60 --instrumental
    python generate.py "pop song about summer" --lyrics "..." --duration 180
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

def _client(url):
    """gradio_client по требованию.

    Раньше `import gradio_client` стоял на верхнем уровне модуля, а в except —
    `pip install` подпроцессом: простой импорт этого файла (линтер, автодополнение)
    молча ставил пакет в чужой Python. Теперь установка происходит только при
    реальном запуске, вслух, и её провал — понятный отказ, а не CalledProcessError.
    """
    try:
        from gradio_client import Client
    except ImportError:
        print("gradio_client не установлен, ставлю: pip install gradio_client", flush=True)
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio_client"])
        except subprocess.CalledProcessError as e:
            raise SystemExit(
                f"ОТКАЗ: не удалось поставить gradio_client (pip вернул {e.returncode}).\n"
                f"  Поставь вручную: {sys.executable} -m pip install gradio_client\n"
                "  На системах с PEP 668 (Homebrew, Debian 12+, Ubuntu 23.04+) — в venv\n"
                "  или добавь --break-system-packages."
            )
        from gradio_client import Client
    return Client(url)

def user_media_dir(xdg_name: str, english_name: str) -> tuple[Path, str]:
    """Настоящий пользовательский каталог («Музыка», «Видео»…), а не его английское имя.

    На локализованном Linux `~/Music` не существует: каталог называется «Музыка» или
    «Музика». `mkdir -p ~/Music` ошибки не даст — он молча создаст ВТОРОЙ каталог рядом,
    и файлы окажутся не там, где человек их ищет. Порядок разрешения:
    переменная окружения → `xdg-user-dir` → существующий английский каталог → домашний.
    Возвращает (каталог, как он был выбран) — второе печатается, чтобы путь не был тайной.
    """
    override = os.getenv("ACE_STEP_OUTPUT_DIR")
    if override:
        return Path(os.path.expanduser(override)), "переменная ACE_STEP_OUTPUT_DIR"

    if sys.platform.startswith("linux") and shutil.which("xdg-user-dir"):
        import subprocess
        try:
            out = subprocess.run(["xdg-user-dir", xdg_name], capture_output=True,
                                 text=True, timeout=10).stdout.strip()
            if out and Path(out).is_dir() and Path(out) != Path.home():
                return Path(out), f"xdg-user-dir {xdg_name}"
        except Exception:  # noqa: BLE001 — отсутствие xdg не повод падать
            pass

    english = Path.home() / english_name
    if english.is_dir():
        return english, f"~/{english_name}"

    return Path.home(), (
        f"домашний каталог: ~/{english_name} не существует, а localized-имя "
        f"определить нечем (поставь xdg-user-dirs или задай ACE_STEP_OUTPUT_DIR)"
    )


_MUSIC_DIR, _MUSIC_DIR_SOURCE = user_media_dir("MUSIC", "Music")
OUTPUT_DIR = _MUSIC_DIR / "ace-step"
GRADIO_URL = "http://127.0.0.1:7860/"


def generate(
    caption: str,
    lyrics: str = "",
    duration: int = 120,
    instrumental: bool = False,
    bpm: int = 0,
    keyscale: str = "",
    language: str = "en",
    seed: int = -1,
    steps: int = 15,
    thinking: bool = True,
    batch_size: int = 1,
) -> dict:
    """Generate music via Gradio API."""

    client = _client(GRADIO_URL)

    start = time.time()

    # Call /generation_wrapper with the essential params
    # Params order matches the endpoint definition
    result = client.predict(
        caption,                    # Music Caption
        lyrics if lyrics else "",   # Lyrics
        bpm if bpm > 0 else 0,     # BPM
        keyscale if keyscale else "",  # Key
        "4",                        # Time Signature
        language,                   # Vocal Language
        steps,                      # DiT Inference Steps
        1.0,                        # DiT Guidance Scale
        seed < 0,                   # Random Seed (bool)
        str(seed) if seed >= 0 else "0",  # Seed value (string!)
        None,                       # Reference Audio
        duration,                   # Audio Duration
        batch_size,                 # Batch Size
        None,                       # Source Audio
        "",                         # LM Codes Hints
        0,                          # Repainting Start
        -1,                         # Repainting End
        "",                         # Instruction
        0.5,                        # LM Codes Strength
        0.5,                        # Cover Strength
        "text2music",               # task_type
        True,                       # Use ADG
        0.0,                        # CFG Interval Start
        1.0,                        # CFG Interval End
        3.0,                        # Shift
        "ode",                      # Inference Method
        "euler",                    # Sampler Mode
        1.0,                        # Velocity Norm Threshold
        0.0,                        # Velocity EMA Factor
        "",                         # Custom Timesteps
        "wav",                      # Audio Format
        "320k",                     # MP3 Bitrate
        44100,                      # MP3 Sample Rate
        0.9,                        # LM Temperature
        thinking,                   # Think
        3.0,                        # LM CFG Scale
        50,                         # LM Top-K (max 100)
        0.95,                       # LM Top-P
        "",                         # LM Negative Prompt
        True,                       # CoT Metas
        True,                       # CaptionRewrite
        True,                       # CoT Language Detection
        False,                      # Constrained Decoding Debug
        False,                      # ParallelThinking
        False,                      # Auto Score
        False,                      # Auto LRC
        0.5,                        # Quality Score Sensitivity
        4,                          # LM Batch Chunk Size
        "vocals",                   # Track Name (required dropdown)
        [],                         # Track Names (empty array)
        True,                       # Enable Normalization
        -1.0,                       # Target Peak dB
        0.0,                        # Fade In
        0.0,                        # Fade Out
        0.0,                        # Latent Shift
        1.0,                        # Latent Rescale
        "balanced",                  # Repaint Mode (conservative/balanced/aggressive)
        0.5,                        # Repaint Strength
        False,                      # AutoGen
        api_name="/generation_wrapper"
    )

    elapsed = time.time() - start

    # Result is a tuple of outputs — find audio files
    audio_files = []
    if isinstance(result, (list, tuple)):
        for item in result:
            if isinstance(item, str) and item.endswith((".wav", ".mp3", ".flac")):
                audio_files.append(item)
            elif isinstance(item, dict) and "path" in item:
                audio_files.append(item["path"])
            elif isinstance(item, (list, tuple)):
                for sub in item:
                    if isinstance(sub, str) and sub.endswith((".wav", ".mp3", ".flac")):
                        audio_files.append(sub)
                    elif isinstance(sub, dict) and "path" in sub:
                        audio_files.append(sub["path"])

    # Copy to output dir. Путь печатается всегда: «файлы сохранены» без указания куда —
    # ровно тот случай, когда человек ищет их в «Музыке», а лежат они в ~/Music.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Каталог вывода: {OUTPUT_DIR}  (выбран: {_MUSIC_DIR_SOURCE})", flush=True)
    saved_files = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, f in enumerate(audio_files):
        if os.path.exists(f):
            ext = Path(f).suffix
            safe_caption = "".join(c if c.isalnum() or c in " -_" else "" for c in caption)[:50].strip()
            dest = OUTPUT_DIR / f"{ts}_{safe_caption}_{i+1}{ext}"
            shutil.copy2(f, dest)
            saved_files.append(str(dest))

    return {
        "success": len(saved_files) > 0,
        "elapsed_seconds": round(elapsed, 1),
        "audio_files": saved_files,
        "raw_files": audio_files,
    }


def main():
    parser = argparse.ArgumentParser(description="ACE-Step music generation (via Gradio API)")
    parser.add_argument("caption", nargs="?", default="", help="Music description / style prompt")
    parser.add_argument("--lyrics", type=str, default="", help="Song lyrics")
    parser.add_argument("--duration", type=int, default=120, help="Duration in seconds (10-600)")
    parser.add_argument("--instrumental", action="store_true", help="Instrumental only")
    parser.add_argument("--bpm", type=int, default=0, help="BPM (0 = auto)")
    parser.add_argument("--key", type=str, default="", help="Key/scale (e.g. 'C major')")
    parser.add_argument("--language", type=str, default="en", help="Vocal language")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed (-1 = random)")
    parser.add_argument("--steps", type=int, default=15, help="Inference steps (max 20 on 16GB)")
    parser.add_argument("--no-thinking", action="store_true", help="Disable LM thinking")
    parser.add_argument("--batch", type=int, default=1, help="Batch size (1-8)")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if not args.caption:
        parser.error("Caption is required")

    lyrics = args.lyrics
    if args.instrumental and not lyrics:
        lyrics = "[Instrumental]"

    print(f"Generating {args.duration}s track...")
    print(f"Style: {args.caption}")
    if args.instrumental:
        print("Mode: Instrumental")
    print()

    result = generate(
        caption=args.caption,
        lyrics=lyrics,
        duration=args.duration,
        instrumental=args.instrumental,
        bpm=args.bpm,
        keyscale=args.key,
        language=args.language,
        seed=args.seed,
        steps=args.steps,
        thinking=not args.no_thinking,
        batch_size=args.batch,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"\nDone in {result['elapsed_seconds']}s")
            for f in result["audio_files"]:
                print(f"  {f}")
        else:
            print(f"\nGeneration completed in {result['elapsed_seconds']}s but no audio files found")
            print(f"Raw result: {result['raw_files']}")

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
