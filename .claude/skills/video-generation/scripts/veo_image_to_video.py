"""Veo 3.1 Fast — batch image-to-video with safety-softener retry.

For each keyframe + motion prompt, calls google-genai generate_videos with the
keyframe as first frame. Wraps every call in a soften-and-retry loop because the
Veo safety filter trips on innocuous words ("awkward silence", "tension", "lonely")
and returns `generated_videos=None` instead of an exception.

Concurrency capped at 3 — Veo 3.1 Fast empirical ceiling. Above that, expect
RESOURCE_EXHAUSTED or silent empty returns. See references/veo-direct.md.

CLI:
    python veo_image_to_video.py clips.json --keyframes keyframes/ --out clips/

clips.json schema:
    [
      {"slug": "01_night_coder", "prompt": "Slow push-in. Subject inhales. Camera holds."},
      ...
    ]
The keyframe file expected at <keyframes>/<slug>.png.
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

from google import genai
from google.genai import types

DEFAULT_MODEL = "veo-3.1-fast-generate-preview"  # проверено ListModels 2026-08-17
# Ранее здесь стояли veo-3.0-*-001: на текущем ключе их БОЛЬШЕ НЕТ — API отвечает
# 404 "not found for API version v1beta, or is not supported for predictLongRunning".
# Живых video-моделей ровно три, все preview: veo-3.1-{generate,fast-generate,lite-generate}-preview.
FULL_MODEL = "veo-3.1-generate-preview"        # Full (медленнее и дороже Fast)
# Veo 3.1 exists ONLY as preview ids on this key: veo-3.1-fast-generate-preview /
# veo-3.1-generate-preview / veo-3.1-lite-generate-preview (NOT "-001"). Swap if you want 3.1.
PARALLEL_CAP = 3                              # empirical reliable ceiling
DEFAULT_NEGATIVE = "subtitles, captions, watermarks, on-screen text, happy stock photo"

# Soften terms that trip Veo safety filter. Symptom: response.generated_videos == None.
SOFT_REPLACEMENTS = {
    "awkward silence": "quiet pause",
    "uncomfortable": "muted",
    "tension": "stillness",
    "lonely": "solitary",
    "empty room": "minimal interior",
    "shadow figure": "silhouette",
    "dark": "dim",
}

# Клиент — лениво, при первом обращении. На верхнем уровне модуля ничего не делаем:
# импорт не должен ни читать .credentials.master.env, ни менять окружение процесса,
# ни строить SDK-клиент с чужим ключом.
_client = None


def get_client():
    """genai-клиент по требованию. Нет ключа — громкий отказ, а не пустой результат."""
    global _client
    if _client is None:
        load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))
        os.environ.pop("GEMINI_API_KEY", None)  # конфликт SDK: нужен GOOGLE_API_KEY
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise SystemExit(
                "ОТКАЗ: не задан GOOGLE_API_KEY.\n"
                "  Где взять: aistudio.google.com/apikey\n"
                "  Как задать: export GOOGLE_API_KEY=... (или строка GOOGLE_API_KEY=... "
                "в ~/.claude/.credentials.master.env)"
            )
        _client = genai.Client(api_key=api_key)
    return _client


def soften(prompt: str) -> str:
    out = prompt
    for k, v in SOFT_REPLACEMENTS.items():
        out = out.replace(k, v)
    return out


def generate_one(slug: str, prompt: str, keyframe_path: Path, out_dir: Path,
                 *, model: str, aspect_ratio: str, duration: int,
                 max_retries: int) -> tuple[str, Path | None]:
    out_path = out_dir / f"{slug}.mp4"
    if out_path.exists() and out_path.stat().st_size > 100_000:
        print(f"[skip] {slug}")
        return slug, out_path

    image = types.Image(
        image_bytes=keyframe_path.read_bytes(),
        mime_type="image/png",
    )

    current = prompt
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            op = get_client().models.generate_videos(
                model=model,
                prompt=current,
                image=image,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    duration_seconds=duration,
                    number_of_videos=1,
                    negative_prompt=DEFAULT_NEGATIVE,
                ),
            )
        except Exception as e:
            last_error = f"submit attempt {attempt}: {e}"
            break

        t0 = time.time()
        print(f"[..]  {slug} attempt {attempt}: generating...")
        while not op.done:
            time.sleep(10)
            try:
                op = get_client().operations.get(op)
            except Exception as e:
                print(f"[WARN] {slug} poll: {e}")
                time.sleep(5)

        if op.error:
            last_error = f"attempt {attempt}: op.error={op.error}"
            current = soften(current)
            continue

        try:
            videos = op.response.generated_videos  # type: ignore[union-attr]
        except AttributeError:
            videos = None

        if not videos:
            # Safety filter — soften and retry
            last_error = f"attempt {attempt}: empty result (likely safety filter)"
            current = soften(current)
            continue

        try:
            vid = videos[0]
            get_client().files.download(file=vid.video)
            vid.video.save(str(out_path))
            dt = time.time() - t0
            size_mb = out_path.stat().st_size / 1_048_576
            print(f"[OK]  {slug} -> {out_path.name} ({size_mb:.1f} MB, {dt:.0f}s)")
            return slug, out_path
        except Exception as e:
            last_error = f"attempt {attempt} download: {e}"
            break

    print(f"[FAIL] {slug}: {last_error}")
    return slug, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("clips_json", help="JSON list of {slug, prompt}")
    ap.add_argument("--keyframes", required=True, help="Directory with <slug>.png")
    ap.add_argument("--out", required=True, help="Output directory for .mp4")
    ap.add_argument("--aspect", default="9:16", choices=["9:16", "16:9", "1:1", "21:9"])
    ap.add_argument("--duration", type=int, default=8, choices=[4, 6, 8])
    ap.add_argument("--full", action="store_true", help="Use Veo 3.1 Full instead of Fast")
    ap.add_argument("--model", help="Явный id модели; перебивает --full. Список: client.models.list()")
    ap.add_argument("--workers", type=int, default=PARALLEL_CAP,
                    help=f"Parallelism (default={PARALLEL_CAP}, empirical Veo ceiling)")
    ap.add_argument("--max-retries", type=int, default=2,
                    help="Soften-and-retry attempts on safety filter (default=2)")
    args = ap.parse_args()

    model = args.model or (FULL_MODEL if args.full else DEFAULT_MODEL)
    clips = json.loads(Path(args.clips_json).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    keyframes_dir = Path(args.keyframes)

    t0 = time.time()
    results: dict[str, Path | None] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(
                generate_one,
                c["slug"], c["prompt"], keyframes_dir / f"{c['slug']}.png", out_dir,
                model=model, aspect_ratio=args.aspect, duration=args.duration,
                max_retries=args.max_retries,
            ): c["slug"]
            for c in clips
        }
        for fut in as_completed(futs):
            slug, path = fut.result()
            results[slug] = path

    ok = sum(1 for v in results.values() if v)
    print(f"\nDone: {ok}/{len(clips)} in {time.time()-t0:.0f}s")
    return 0 if ok == len(clips) else 1


if __name__ == "__main__":
    sys.exit(main())
