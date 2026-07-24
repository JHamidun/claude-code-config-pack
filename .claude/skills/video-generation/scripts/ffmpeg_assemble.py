"""ffmpeg assembly — concat clips + safe audio mix + PIL brand-card.

Fixes three silent-data-loss bugs documented in references/assembly.md:
- amix duration=longest actually truncates to SHORTEST → apad on shorter input + -t
- concat-demuxer drops audio entirely if ANY clip lacks audio stream → anullsrc pre-pad
- Windows subprocess(text=True) crashes on cp1251 ffmpeg stderr → bytes + decode

Brand-card with cyrillic is rendered via PIL (ffmpeg drawtext + cyrillic fails on
Windows due to font-cache encoding mismatch).

CLI:
    python ffmpeg_assemble.py manifest.json --out final.mp4

manifest.json schema:
    {
      "clips": [{"path": "clips/01.mp4"}, {"path": "clips/02.mp4"}, ...],
      "voiceover": "audio/voice.mp3",
      "music": "audio/music.m4a",
      "music_volume": 0.30,
      "duration": 72,
      "aspect": "9:16",
      "brand_card": {
          "enabled": true,
          "duration": 5,
          "lines": [
              {"text": "ТехПред",         "size": 120, "color": "white",   "y_offset": -220},
              {"text": "[университет] × Сколково", "size": 60,  "color": "white",   "y_offset": -30},
              {"text": "Поступление 2026", "size": 40, "color": "#BBBBBB", "y_offset": 90}
          ]
      }
    }
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], label: str) -> None:
    print(f"[..] {label}")
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        stderr = (r.stderr or b"").decode("utf-8", errors="replace")
        print(stderr[-1800:])
        sys.exit(1)


def has_audio(path: Path) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return "audio" in (r.stdout or "")


def ensure_audio(clip: Path, out: Path) -> Path:
    """Add silent 48 kHz stereo AAC if the clip has no audio stream."""
    if has_audio(clip):
        return clip
    run([
        "ffmpeg", "-y", "-i", str(clip),
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(out),
    ], f"add silent audio -> {out.name}")
    return out


def concat_video_only(clip_paths: list[Path], aspect: str, fps: int, out: Path) -> Path:
    """Re-encode concat with normalized 1080×1920 (or 1920×1080) + 30 fps."""
    if aspect == "9:16":
        scale = "scale=1080:1920:force_original_aspect_ratio=decrease," \
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    elif aspect == "16:9":
        scale = "scale=1920:1080:force_original_aspect_ratio=decrease," \
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    elif aspect == "1:1":
        scale = "scale=1080:1080:force_original_aspect_ratio=decrease," \
                "pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    else:
        scale = "setsar=1"

    list_path = out.parent / "_concat.txt"
    list_path.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in clip_paths),
        encoding="utf-8",
    )
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-vf", scale, "-r", str(fps), "-an",
        str(out),
    ], f"concat {len(clip_paths)} clips -> {out.name}")
    return out


def mix_voice_music(voice: Path, music: Path, duration: int,
                    music_volume: float, out: Path) -> Path:
    """apad on voice (in case shorter), sidechain-duck music, hard -t to enforce length."""
    fade_start = max(duration - 4, 0)
    fc = (
        f"[0:a]apad=whole_dur={duration},volume=1.0,asplit=2[voice][sc];"
        f"[1:a]volume={music_volume}[musicraw];"
        f"[musicraw][sc]sidechaincompress=threshold=0.04:ratio=8:"
        f"attack=15:release=350[musicduck];"
        f"[voice][musicduck]amix=inputs=2:duration=longest:dropout_transition=0,"
        f"atrim=end={duration},asetpts=PTS-STARTPTS,alimiter=limit=0.97,"
        f"afade=t=out:st={fade_start}:d=4[a]"
    )
    run([
        "ffmpeg", "-y", "-i", str(voice), "-i", str(music),
        "-filter_complex", fc, "-map", "[a]",
        "-c:a", "aac", "-b:a", "192k", "-t", str(duration),
        str(out),
    ], f"mix voice+music -> {out.name}")
    return out


def mux(silent_video: Path, mix_audio: Path, out: Path) -> Path:
    run([
        "ffmpeg", "-y", "-i", str(silent_video), "-i", str(mix_audio),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
        "-shortest", "-movflags", "+faststart",
        str(out),
    ], f"mux video+audio -> {out.name}")
    return out


def make_brand_card(spec: dict, aspect: str, out_dir: Path) -> Path:
    """Render text PNG via PIL, encode to mp4 with silent AAC track."""
    from PIL import Image, ImageDraw, ImageFont

    if aspect == "9:16":
        W, H = 1080, 1920
    elif aspect == "16:9":
        W, H = 1920, 1080
    else:
        W, H = 1080, 1080

    img = Image.new("RGB", (W, H), "black")
    draw = ImageDraw.Draw(img)
    font_bold = "C:/Windows/Fonts/arialbd.ttf"
    font_reg = "C:/Windows/Fonts/arial.ttf"

    for ln in spec.get("lines", []):
        text = ln["text"]
        size = ln.get("size", 60)
        color = ln.get("color", "white")
        y_off = ln.get("y_offset", 0)
        font_path = font_bold if size >= 90 else font_reg
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (W - w) // 2 - bbox[0]
        y = (H - h) // 2 + y_off - bbox[1]
        draw.text((x, y), text, font=font, fill=color)

    png = out_dir / "_brand_card.png"
    img.save(png)

    out = out_dir / "_brand_card.mp4"
    run([
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(spec.get("duration", 5)), "-i", str(png),
        "-f", "lavfi", "-t", str(spec.get("duration", 5)),
        "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-vf", "fade=t=in:st=0:d=0.5,fade=t=out:st=4:d=1",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(out),
    ], "brand card render")
    return out


def append_brand(main: Path, brand: Path, out: Path) -> Path:
    list_path = out.parent / "_final_concat.txt"
    list_path.write_text(
        f"file '{main.as_posix()}'\nfile '{brand.as_posix()}'\n",
        encoding="utf-8",
    )
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(out),
    ], "append brand card")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", help="JSON manifest (see docstring for schema)")
    ap.add_argument("--out", default="final.mp4")
    args = ap.parse_args()

    m = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    out_dir = Path(args.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    work = out_dir / "_work"
    work.mkdir(exist_ok=True)

    # 1. Ensure every clip has audio (concat demuxer kills audio if any clip lacks it)
    safe_clips: list[Path] = []
    for i, c in enumerate(m["clips"]):
        src = Path(c["path"])
        fixed = work / f"with_audio_{i:02d}.mp4"
        safe_clips.append(ensure_audio(src, fixed))

    # 2. Concat clips into silent normalized video
    silent = concat_video_only(safe_clips, m.get("aspect", "9:16"),
                               m.get("fps", 30), work / "silent.mp4")

    # 3. Mix voice + music with apad/duration guard + sidechain ducking
    mix = mix_voice_music(
        Path(m["voiceover"]), Path(m["music"]),
        duration=m["duration"],
        music_volume=m.get("music_volume", 0.30),
        out=work / "mix.m4a",
    )

    # 4. Mux silent video + mix audio
    main_video = mux(silent, mix, work / "main.mp4")

    # 5. Optional brand card + final concat
    if m.get("brand_card", {}).get("enabled"):
        brand = make_brand_card(m["brand_card"], m.get("aspect", "9:16"), work)
        final = append_brand(main_video, brand, Path(args.out))
    else:
        final = Path(args.out)
        subprocess.run(["ffmpeg", "-y", "-i", str(main_video),
                        "-c", "copy", str(final)], check=True, capture_output=True)

    size_mb = final.stat().st_size / 1_048_576
    print(f"\n=== FINAL: {final} ({size_mb:.1f} MB) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
