"""ElevenLabs voiceover — TTS with cloned-voice presets.

The voice is YOURS: this pack ships with no voice id. Put your own into
`ELEVENLABS_VOICE_ID_RU` in ~/.claude/.credentials.master.env, or pass --voice-id.
Where to get it: https://elevenlabs.io/app/voice-lab → your voice → ID
(or `GET https://api.elevenlabs.io/v1/voices`, cloned voices have category="cloned").

Voice settings below are tuned for Russian narration from a cloned voice —
see references/audio.md §3 for the reasoning.

CLI:
    # One-shot: file in, mp3 out
    python elevenlabs_voiceover.py script.txt --out voice.mp3

    # Per-clip mode: directory of .txt → directory of .mp3
    python elevenlabs_voiceover.py clips_dir/ --out audio/ --per-clip
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))

from elevenlabs import ElevenLabs, VoiceSettings

# Tuned for believable Russian narration from a cloned voice
CLONE_SETTINGS = VoiceSettings(
    stability=0.55,         # 0.50-0.60 = expressive but not chaotic
    similarity_boost=0.80,  # high = stays close to cloned timbre
    style=0.15,             # low = neutral delivery, no over-acting
    use_speaker_boost=True,
)
DEFAULT_MODEL = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_192"


def default_voice_id():
    """Your own voice id from the environment. Never hardcoded: a literal
    placeholder here would silently reach the API and fail with an opaque 404."""
    return os.getenv("ELEVENLABS_VOICE_ID_RU") or os.getenv("ELEVENLABS_VOICE_ID")


def synthesize(client: ElevenLabs, text: str, voice_id: str,
               settings: VoiceSettings, model: str, fmt: str) -> bytes:
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model,
        output_format=fmt,
        voice_settings=settings,
    )
    return b"".join(audio)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Text file OR directory of .txt files")
    ap.add_argument("--out", required=True, help="Output mp3 path or directory")
    ap.add_argument("--per-clip", action="store_true",
                    help="Treat input as a directory; produce one mp3 per .txt")
    ap.add_argument("--voice-id", default=default_voice_id(),
                    help="ElevenLabs voice id; defaults to $ELEVENLABS_VOICE_ID_RU")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--format", default=DEFAULT_OUTPUT_FORMAT)
    ap.add_argument("--stability", type=float, default=0.55)
    ap.add_argument("--similarity-boost", type=float, default=0.80)
    ap.add_argument("--style", type=float, default=0.15)
    args = ap.parse_args()

    if not args.voice_id:
        print("No voice id. Set ELEVENLABS_VOICE_ID_RU in "
              "~/.claude/.credentials.master.env, or pass --voice-id <id>.\n"
              "Get yours: https://elevenlabs.io/app/voice-lab -> your voice -> ID "
              "(or GET https://api.elevenlabs.io/v1/voices).", file=sys.stderr)
        return 2
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("ELEVENLABS_API_KEY not set (env or ~/.claude/.credentials.master.env). "
              "Get one: https://elevenlabs.io/app/settings/api-keys", file=sys.stderr)
        return 2

    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    settings = VoiceSettings(
        stability=args.stability,
        similarity_boost=args.similarity_boost,
        style=args.style,
        use_speaker_boost=True,
    )

    inp = Path(args.input)
    if args.per_clip:
        if not inp.is_dir():
            print(f"--per-clip requires directory; got {inp}")
            return 1
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        txts = sorted(inp.glob("*.txt"))
        for txt in txts:
            text = txt.read_text(encoding="utf-8").strip()
            if not text:
                continue
            audio = synthesize(client, text, args.voice_id, settings, args.model, args.format)
            mp3 = out_dir / f"{txt.stem}.mp3"
            mp3.write_bytes(audio)
            print(f"[OK] {mp3.name} ({len(audio)//1024} KB)")
        return 0

    # Single file mode
    text = inp.read_text(encoding="utf-8").strip()
    audio = synthesize(client, text, args.voice_id, settings, args.model, args.format)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio)
    print(f"[OK] {out_path} ({len(audio)//1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
