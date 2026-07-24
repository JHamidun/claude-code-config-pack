#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
captions_ass.py — auto karaoke captions for shorts.

Calls ElevenLabs text-to-speech WITH character timestamps (no Whisper pass needed),
converts char alignment -> word timings -> a word-pop ASS subtitle file. RU/cyrillic safe.
Pairs with engines/higgsfield/scripts/assemble.py burn_ass.

Pipeline: text -> (vo.mp3 + captions.ass) -> burn onto video.

USAGE
  python captions_ass.py "текст..." --out-audio vo.mp3 --out-ass captions.ass [--voice-id ID] [--chunk 2] [--style hormozi]
  python captions_ass.py script.txt --out-audio vo.mp3 --out-ass cap.ass        # .txt input
Then:
  python ../engines/higgsfield/scripts/assemble.py burn_ass video.mp4 captions.ass out.mp4

(Ref: references/audio.md §6 TTS-with-timestamps -> ASS karaoke.)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

YOURNAME_VOICE = "YOUR_ELEVENLABS_VOICE_ID"
DEFAULT_MODEL = "eleven_multilingual_v2"
CRED = Path(os.path.expanduser("~/.claude/.credentials.master.env"))

STYLES = {  # PlayRes 1080x1920; word-pop bottom-center
    "hormozi": dict(font="Arial", size=96, primary="&H00FFFFFF", outline="&H00101010",
                    border=7, shadow=3, marginv=300, accent="&H0000E5FF"),
    "clean": dict(font="Arial", size=78, primary="&H00FFFFFF", outline="&H00202020",
                  border=5, shadow=2, marginv=240, accent="&H0000E5FF"),
}


def _api_key() -> str:
    k = os.getenv("ELEVENLABS_API_KEY")
    if not k and CRED.exists():
        for line in CRED.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("ELEVENLABS_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not k:
        sys.exit("ELEVENLABS_API_KEY not found (env or ~/.claude/.credentials.master.env)")
    return k


def tts_with_timestamps(text: str, voice_id: str, model: str) -> dict:
    """POST /v1/text-to-speech/{id}/with-timestamps -> {audio_base64, alignment{characters,*_times_seconds}}."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    body = json.dumps({
        "text": text, "model_id": model,
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.80, "style": 0.15, "use_speaker_boost": True},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "xi-api-key": _api_key(), "Content-Type": "application/json", "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def chars_to_words(alignment: dict) -> list[dict]:
    chars = alignment["characters"]
    st = alignment.get("character_start_times_seconds") or alignment.get("characterStartTimesSeconds")
    et = alignment.get("character_end_times_seconds") or alignment.get("characterEndTimesSeconds")
    words, cur, ws, prev_e = [], "", None, 0.0
    for c, s, e in zip(chars, st, et):
        if c.strip() == "":
            if cur:
                words.append({"w": cur, "s": ws, "e": prev_e})
                cur, ws = "", None
            continue
        if ws is None:
            ws = s
        cur += c
        prev_e = e
    if cur:
        words.append({"w": cur, "s": ws, "e": prev_e})
    return words


def _t(sec: float) -> str:
    cs = int(round(sec * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def build_ass(words: list[dict], style: str, chunk: int) -> str:
    st = STYLES.get(style, STYLES["hormozi"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop, {st['font']}, {st['size']}, {st['primary']}, {st['outline']}, &H00000000, 1, 1, {st['border']}, {st['shadow']}, 2, 50, 50, {st['marginv']}, 1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for i in range(0, len(words), max(1, chunk)):
        grp = words[i:i + max(1, chunk)]
        s, e = grp[0]["s"], grp[-1]["e"]
        txt = " ".join(g["w"] for g in grp).upper()
        # accent every other chunk for rhythm
        col = st["accent"] if (i // max(1, chunk)) % 2 == 1 else st["primary"]
        lines.append(f"Dialogue: 0,{_t(s)},{_t(e)},Pop,,0,0,0,,{{\\c{col}\\fad(60,60)}}{txt}")
    return head + "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Auto karaoke captions (ElevenLabs timestamps -> ASS)")
    ap.add_argument("text", help="caption text OR path to .txt")
    ap.add_argument("--voice-id", default=YOURNAME_VOICE)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--out-audio", default="vo.mp3")
    ap.add_argument("--out-ass", default="captions.ass")
    ap.add_argument("--chunk", type=int, default=2, help="words per caption pop (1-3)")
    ap.add_argument("--style", default="hormozi", choices=list(STYLES))
    a = ap.parse_args(argv)

    text = Path(a.text).read_text(encoding="utf-8").strip() if (len(a.text) < 260 and Path(a.text).exists()) else a.text
    print(f"[..] TTS+timestamps ({len(text)} chars) voice={a.voice_id}")
    res = tts_with_timestamps(text, a.voice_id, a.model)
    Path(a.out_audio).write_bytes(base64.b64decode(res["audio_base64"]))
    words = chars_to_words(res["alignment"])
    Path(a.out_ass).write_text(build_ass(words, a.style, a.chunk), encoding="utf-8")
    dur = words[-1]["e"] if words else 0
    print(f"[OK] {a.out_audio} + {a.out_ass}  ({len(words)} words, {dur:.1f}s, style={a.style}, chunk={a.chunk})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
