"""ElevenLabs Music — fallback when Lyria 2 doesn't fit (vocals, named genres).

GOTCHA: Music API rejects any prompt that names a real artist or copyrighted track
("in the style of Daft Punk", "Beyoncé-style vocal", "Hans Zimmer cinematic").
Returns 400 content_policy_violation. Use descriptive substitutes instead:
genre + era + instrumentation + BPM + mood + vocal description.

See references/audio.md for the full descriptor-substitution table.

CLI:
    python elevenlabs_music.py "Upbeat house anthem, female vocal hook, 124 BPM, \\
        warm analog synths, sidechained bass, four-on-the-floor kick, mood: triumphant" \\
        --duration-ms 45000 --out track.mp3
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))

from elevenlabs import ElevenLabs

# Loose guard against the most common policy-violation pattern.
# Not exhaustive — ElevenLabs has more triggers. See references/audio.md.
NAMED_ARTIST_RE = re.compile(
    r"\b(in the style of|sounds like|reminiscent of|à la|inspired by)\s+[A-Z]",
    re.I,
)


def prompt_guard(prompt: str) -> None:
    if NAMED_ARTIST_RE.search(prompt):
        print("[WARN] prompt contains a named-artist reference pattern.")
        print("       ElevenLabs Music will likely reject with content_policy_violation.")
        print("       See references/audio.md for substitution table.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", help="Music prompt — descriptor-only, no named artists")
    ap.add_argument("--duration-ms", type=int, default=30000,
                    help="≤30_000 (30s hard cap per generation); >30s → 2×30s segments, see references/audio.md")
    ap.add_argument("--model", default="music_v1")
    ap.add_argument("--out", default="track.mp3")
    args = ap.parse_args()

    prompt_guard(args.prompt)

    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    t0 = time.time()
    try:
        audio = client.music.compose(
            prompt=args.prompt,
            music_length_ms=args.duration_ms,
            model_id=args.model,
        )
    except AttributeError:
        # Older SDK exposed it as music.generate
        audio = client.music.generate(  # type: ignore[attr-defined]
            prompt=args.prompt,
            music_length_ms=args.duration_ms,
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        if isinstance(audio, (bytes, bytearray)):
            f.write(audio)
        else:
            for chunk in audio:
                f.write(chunk)

    print(f"[OK] {out_path} ({out_path.stat().st_size//1024} KB, {time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
