"""Nano Banana Pro — batch keyframe generation with optional reference chaining.

Generates a sequence of cinematic keyframes from a JSON shot list. Two modes:
- independent: each shot generated separately (fastest, lowest identity consistency)
- chained:     pass previous output as reference image (forward chain + re-anchor every Nth)

Identity consistency rules — see references/runway-seedance.md and the nano-banana-pro
skill's "Multi-Image Consistency via Reference Chaining" section.

CLI:
    python nano_banana_keyframes.py shots.json --out keyframes/ --mode chained --reanchor 3

shots.json schema:
    [
      {"slug": "01_night_coder", "prompt": "...", "anchor": false},
      {"slug": "02_polite_silence", "prompt": "...", "anchor": false},
      ...
    ]
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

# Default model — see rules/dont-do.md: only gemini-3-pro-image-preview or
# gemini-3.1-flash-image-preview are allowed
DEFAULT_MODEL = "gemini-3-pro-image-preview"
DEFAULT_STYLE = (
    "Cinematic 9:16 portrait, muted editorial palette, soft volumetric haze, "
    "shallow depth of field, 35mm film grain, documentary photographic style, "
    "no text overlays, realistic photography, no illustration, no CGI."
)
PARALLEL_CAP = 4  # Nano Banana Pro empirical ceiling — see chat session 2026-04-20

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


def _extract_image(resp) -> bytes | None:
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return part.inline_data.data
    return None


def generate_one(slug: str, prompt: str, style: str, out_dir: Path,
                 reference: bytes | None = None) -> tuple[str, bytes | None]:
    """Single keyframe generation. Returns (slug, image_bytes or None)."""
    out_path = out_dir / f"{slug}.png"
    if out_path.exists() and out_path.stat().st_size > 1024:
        print(f"[skip] {slug}")
        return slug, out_path.read_bytes()

    parts: list = []
    if reference is not None:
        parts.append(types.Part.from_bytes(data=reference, mime_type="image/png"))
        parts.append(
            "Use the attached image as the exact identity and style reference. "
            "Keep face, hair, clothing, lighting, and color palette consistent."
        )
    parts.append(f"{style}\n\nSCENE: {prompt}")

    try:
        resp = get_client().models.generate_content(
            model=DEFAULT_MODEL,
            contents=parts,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
    except Exception as e:
        print(f"[ERR] {slug}: {e}")
        return slug, None

    data = _extract_image(resp)
    if data is None:
        print(f"[WARN] {slug}: no image in response")
        return slug, None

    out_path.write_bytes(data)
    print(f"[OK]  {slug} -> {out_path.name} ({len(data)//1024} KB)")
    return slug, data


def run_independent(shots: list[dict], style: str, out_dir: Path) -> dict[str, bytes | None]:
    """All shots in parallel (cap PARALLEL_CAP). No identity sharing."""
    results: dict[str, bytes | None] = {}
    with ThreadPoolExecutor(max_workers=PARALLEL_CAP) as pool:
        futs = {pool.submit(generate_one, s["slug"], s["prompt"], style, out_dir): s["slug"]
                for s in shots}
        for fut in as_completed(futs):
            slug, data = fut.result()
            results[slug] = data
    return results


def run_chained(shots: list[dict], style: str, out_dir: Path, reanchor_every: int = 3) -> dict[str, bytes | None]:
    """Sequential chain. Every Nth re-anchors to the first 'anchor: true' shot."""
    results: dict[str, bytes | None] = {}
    anchor: bytes | None = None
    last: bytes | None = None
    for i, s in enumerate(shots):
        use_anchor = (i > 0 and i % reanchor_every == 0 and anchor is not None)
        reference = anchor if use_anchor else last
        slug, data = generate_one(s["slug"], s["prompt"], style, out_dir, reference)
        results[slug] = data
        if data is not None:
            last = data
            if s.get("anchor") or anchor is None:
                anchor = data
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shots_json", help="Path to JSON shot list")
    ap.add_argument("--out", default="keyframes", help="Output directory")
    ap.add_argument("--mode", choices=["independent", "chained"], default="independent")
    ap.add_argument("--reanchor", type=int, default=3,
                    help="Re-anchor every Nth shot (chained mode only)")
    ap.add_argument("--style", default=DEFAULT_STYLE, help="Style header injected into every prompt")
    args = ap.parse_args()

    shots = json.loads(Path(args.shots_json).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    if args.mode == "chained":
        results = run_chained(shots, args.style, out_dir, args.reanchor)
    else:
        results = run_independent(shots, args.style, out_dir)

    ok = sum(1 for v in results.values() if v)
    print(f"\nDone: {ok}/{len(shots)} in {time.time()-t0:.1f}s")
    return 0 if ok == len(shots) else 1


if __name__ == "__main__":
    sys.exit(main())
