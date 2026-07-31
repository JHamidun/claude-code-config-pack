#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Generate BGM (ElevenLabs Music, 30s segments) + SFX pack for montage."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
from elevenlabs.client import ElevenLabs  # noqa: E402

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd()) / "audio"
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

MUSIC = [
    ("music_01", "Energetic modern promo underscore, punchy minimal tech beat, tight drums, "
                 "sub-bass pulse, percussive groove, confident forward drive, no melody clutter"),
    ("music_02", "Continues the energetic minimal tech promo beat, same tempo and key, "
                 "adds subtle rising tension layer, punchy drums, sub-bass pulse"),
    ("music_03", "Continues the energetic minimal tech promo beat, same tempo and key, "
                 "final section with extra percussion energy and confident resolve"),
]

SFX = [
    ("sfx_whoosh", "fast cinematic whoosh transition, short, punchy", 1.0),
    ("sfx_whoosh2", "quick air swish whip pan transition sound", 0.8),
    ("sfx_pop", "soft UI pop bubble notification sound, single short pop", 0.5),
    ("sfx_click", "crisp camera shutter click", 0.5),
    ("sfx_riser", "short cinematic riser build-up swell, one second", 1.5),
    ("sfx_impact", "deep punchy bass impact hit, short boom", 1.0),
    ("sfx_ding", "bright success notification ding, single chime", 0.8),
]

for name, prompt in MUSIC:
    out = BASE / f"{name}.mp3"
    if out.exists():
        print(f"skip {name}")
        continue
    print(f"music {name}...", flush=True)
    audio = client.music.compose(prompt=prompt, music_length_ms=30000, force_instrumental=True, model_id="music_v1")
    with open(out, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"  -> {out.stat().st_size // 1024}KB", flush=True)

for name, prompt, dur in SFX:
    out = BASE / f"{name}.mp3"
    if out.exists():
        print(f"skip {name}")
        continue
    print(f"sfx {name}...", flush=True)
    audio = client.text_to_sound_effects.convert(text=prompt, duration_seconds=dur)
    with open(out, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"  -> {out.stat().st_size // 1024}KB", flush=True)

print("AUDIO ASSETS DONE", flush=True)
