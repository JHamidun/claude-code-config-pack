#!/usr/bin/env python3
"""
Video Editor CLI — local FFmpeg-based video editing.
No server required. Just FFmpeg installed locally.

Usage: python video_editor.py <command> [args]
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
MUSIC_DIR = SCRIPT_DIR / "music"

# Track recently used to avoid repeats
_recent_file = SCRIPT_DIR / ".recent_tracks"

EFFECTS_CYCLE = ["zoom_in", "pan_right", "zoom_out"]


def _check_ffmpeg():
    """Ensure ffmpeg is available."""
    if not shutil.which("ffmpeg"):
        print("Error: ffmpeg not found. Install it first:")
        print("  Windows: winget install ffmpeg  OR  choco install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   apt install ffmpeg")
        sys.exit(1)


def _run_ffmpeg(cmd, label="ffmpeg"):
    """Run an ffmpeg command, print stderr on failure."""
    print(f"  [{label}] {' '.join(str(c) for c in cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr[-500:]}" if result.stderr else f"  Error: exit code {result.returncode}")
        return False
    return True


def _get_random_music(custom_music=None):
    """Pick a random music file, avoiding recent repeats."""
    if custom_music:
        p = Path(custom_music)
        if p.exists():
            return p
        print(f"Warning: custom music not found: {custom_music}")
        return None

    music_files = sorted([
        f for f in MUSIC_DIR.iterdir()
        if f.suffix.lower() in ('.mp3', '.wav', '.ogg', '.m4a')
    ]) if MUSIC_DIR.exists() else []

    if not music_files:
        print("  No music files found in music/ directory")
        return None

    # Anti-repeat
    recent = []
    if _recent_file.exists():
        recent = _recent_file.read_text().strip().split("\n")[-5:]

    available = [f for f in music_files if f.name not in recent]
    if not available:
        available = music_files

    chosen = random.choice(available)

    # Save recent
    recent.append(chosen.name)
    _recent_file.write_text("\n".join(recent[-5:]))

    print(f"  Music: {chosen.name} (pool: {len(music_files)} tracks)")
    return chosen


def _add_music_to_video(video_path, output_path, music_path, volume=0.3):
    """Mix background music into video."""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path), "-i", str(music_path),
        "-filter_complex",
        f"[0:a]volume=1.0[a0];[1:a]volume={volume},aloop=loop=-1:size=2e+09[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(output_path)
    ]
    return _run_ffmpeg(cmd, "add music")


def _probe_image_size(image_path):
    """Return (width, height) of an image using ffprobe."""
    if not shutil.which("ffprobe"):
        return None, None
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", str(image_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None, None
    try:
        info = json.loads(result.stdout)
        for s in info.get("streams", []):
            if s.get("codec_type") == "video":
                return int(s["width"]), int(s["height"])
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    return None, None


def concat(args):
    """Concatenate video files with optional music and transitions."""
    _check_ffmpeg()

    for path in args.videos:
        if not os.path.exists(path):
            print(f"Error: file not found: {path}")
            sys.exit(1)

    if len(args.videos) < 2:
        print("Error: at least 2 video files required")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    output = args.output or f"concat_{job_id}.mp4"
    tmp_concat = f".tmp_concat_{job_id}.mp4"
    tmp_list = f".tmp_list_{job_id}.txt"

    try:
        print(f"Concatenating {len(args.videos)} videos...")

        if args.transition == "none":
            # Fast concat without re-encoding
            with open(tmp_list, "w") as f:
                for v in args.videos:
                    f.write(f"file '{os.path.abspath(v)}'\n")

            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", tmp_list, "-c", "copy", tmp_concat]
            if not _run_ffmpeg(cmd, "concat"):
                sys.exit(1)
        else:
            # Fade transition with xfade
            n = len(args.videos)
            inputs = []
            for v in args.videos:
                inputs.extend(["-i", os.path.abspath(v)])

            filter_parts = []
            prev_v, prev_a = "0:v", "0:a"
            dur = args.transition_duration

            for i in range(1, n):
                out_v = f"v{i}" if i < n - 1 else "outv"
                out_a = f"a{i}" if i < n - 1 else "outa"
                filter_parts.append(f"[{prev_v}][{i}:v]xfade=transition=fade:duration={dur}:offset=auto[{out_v}]")
                filter_parts.append(f"[{prev_a}][{i}:a]acrossfade=d={dur}[{out_a}]")
                prev_v, prev_a = out_v, out_a

            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", ";".join(filter_parts),
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "fast", "-c:a", "aac",
                tmp_concat
            ]
            if not _run_ffmpeg(cmd, "concat+fade"):
                # Fallback to simple concat
                print("  Fade failed, falling back to simple concat...")
                with open(tmp_list, "w") as f:
                    for v in args.videos:
                        f.write(f"file '{os.path.abspath(v)}'\n")
                cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", tmp_list, "-c", "copy", tmp_concat]
                if not _run_ffmpeg(cmd, "concat fallback"):
                    sys.exit(1)

        # Add music if requested
        if args.music:
            music = _get_random_music(args.custom_music)
            if music:
                if _add_music_to_video(tmp_concat, output, music, args.music_volume):
                    os.remove(tmp_concat)
                else:
                    os.rename(tmp_concat, output)
            else:
                os.rename(tmp_concat, output)
        else:
            os.rename(tmp_concat, output)

        size_mb = os.path.getsize(output) / 1024 / 1024
        print(f"Done: {output} ({size_mb:.1f} MB)")

    finally:
        for f in [tmp_list, tmp_concat]:
            if os.path.exists(f):
                os.remove(f)


def process(args):
    """Process a single video with optional music."""
    _check_ffmpeg()

    if not os.path.exists(args.video):
        print(f"Error: file not found: {args.video}")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    output = args.output or f"processed_{job_id}.mp4"

    print(f"Processing {args.video}...")

    if args.music:
        music = _get_random_music(args.custom_music)
        if music:
            if not _add_music_to_video(args.video, output, music, args.music_volume):
                shutil.copy(args.video, output)
        else:
            shutil.copy(args.video, output)
    else:
        # Apply video filters if any non-default values
        has_filters = (args.brightness != 1.0 or args.contrast != 1.0 or args.saturation != 1.0)
        if has_filters:
            vf = f"eq=brightness={args.brightness - 1.0}:contrast={args.contrast}:saturation={args.saturation}"
            cmd = [
                "ffmpeg", "-y", "-i", os.path.abspath(args.video),
                "-vf", vf, "-c:a", "copy",
                output
            ]
            if not _run_ffmpeg(cmd, "filters"):
                sys.exit(1)
        else:
            shutil.copy(args.video, output)

    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"Done: {output} ({size_mb:.1f} MB)")


def trim(args):
    """Trim video to start-end range."""
    _check_ffmpeg()

    if not os.path.exists(args.video):
        print(f"Error: file not found: {args.video}")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    output = args.output or f"trimmed_{job_id}.mp4"

    cmd = ["ffmpeg", "-y", "-i", os.path.abspath(args.video)]
    if args.start:
        cmd.extend(["-ss", args.start])
    if args.end:
        cmd.extend(["-to", args.end])
    cmd.extend(["-c", "copy", output])

    print(f"Trimming {args.video} [{args.start or '0'} → {args.end or 'end'}]...")
    if not _run_ffmpeg(cmd, "trim"):
        sys.exit(1)

    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"Done: {output} ({size_mb:.1f} MB)")


def probe(args):
    """Show video file info (duration, resolution, codecs)."""
    _check_ffmpeg()

    if not shutil.which("ffprobe"):
        print("Error: ffprobe not found")
        sys.exit(1)

    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", os.path.abspath(args.video)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    info = json.loads(result.stdout)
    fmt = info.get("format", {})
    duration = float(fmt.get("duration", 0))
    size_mb = int(fmt.get("size", 0)) / 1024 / 1024

    print(f"File: {args.video}")
    print(f"Duration: {int(duration // 60)}:{int(duration % 60):02d} ({duration:.1f}s)")
    print(f"Size: {size_mb:.1f} MB")

    for s in info.get("streams", []):
        if s["codec_type"] == "video":
            print(f"Video: {s.get('width')}x{s.get('height')}, {s.get('codec_name')}, {s.get('r_frame_rate')} fps")
        elif s["codec_type"] == "audio":
            print(f"Audio: {s.get('codec_name')}, {s.get('sample_rate')} Hz, {s.get('channels')} ch")


def music_pool(_args):
    """Show available music tracks."""
    if not MUSIC_DIR.exists():
        print(f"No music directory at {MUSIC_DIR}")
        print(f"Create it and add .mp3/.wav/.ogg/.m4a files")
        return

    tracks = sorted([
        f.name for f in MUSIC_DIR.iterdir()
        if f.suffix.lower() in ('.mp3', '.wav', '.ogg', '.m4a')
    ])

    print(f"Music dir: {MUSIC_DIR}")
    print(f"Pool: {len(tracks)} tracks")
    for t in tracks:
        print(f"  - {t}")

    if _recent_file.exists():
        recent = _recent_file.read_text().strip().split("\n")
        print(f"Recently played: {', '.join(recent)}")


# ---------------------------------------------------------------------------
# NEW: ken-burns
# ---------------------------------------------------------------------------

def _build_ken_burns_vf(effect, w, h, frames):
    """Return the zoompan vf string for the given effect."""
    if effect == "zoom_in":
        return (
            f"scale={int(w * 1.12)}:{int(h * 1.12)},"
            f"zoompan=z='1.12-0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps=30"
        )
    elif effect == "pan_right":
        return (
            f"scale={int(w * 1.15)}:{int(h * 1.15)},"
            f"zoompan=z=1.15:x='0.15*iw*on/{frames}':y='ih*0.075'"
            f":d={frames}:s={w}x{h}:fps=30"
        )
    else:  # zoom_out
        return (
            f"scale={int(w * 1.12)}:{int(h * 1.12)},"
            f"zoompan=z='1.0+0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps=30"
        )


def ken_burns(args):
    """Animate a static image with Ken Burns camera motion effect."""
    _check_ffmpeg()

    img_path = os.path.abspath(args.image)
    if not os.path.exists(img_path):
        print(f"Error: image not found: {img_path}")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    output = args.output or f"ken_burns_{job_id}.mp4"

    # Determine effect — cycle if not specified
    effect = args.effect
    if not effect:
        # Cycle deterministically based on image name hash
        idx = hash(Path(img_path).stem) % len(EFFECTS_CYCLE)
        effect = EFFECTS_CYCLE[idx]

    print(f"Ken Burns: {Path(img_path).name} → effect={effect}, duration={args.duration}s")

    # Auto-detect resolution from image
    w, h = _probe_image_size(img_path)
    if w is None or h is None:
        # Default: portrait for social, landscape otherwise
        w, h = 1080, 1920
        print(f"  Could not detect image size, defaulting to {w}x{h}")
    else:
        print(f"  Detected image size: {w}x{h}")

    fps = 30
    frames = int(args.duration * fps)
    vf = _build_ken_burns_vf(effect, w, h, frames)

    cmd = [
        "ffmpeg", "-loop", "1", "-i", img_path,
        "-vf", vf,
        "-t", str(args.duration),
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "fast",
        output, "-y"
    ]

    if not _run_ffmpeg(cmd, "ken-burns"):
        sys.exit(1)

    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"Done: {output} ({size_mb:.1f} MB, effect={effect})")


# ---------------------------------------------------------------------------
# NEW: ducking
# ---------------------------------------------------------------------------

def _build_duck_filter(regions, speech_vol=0.12, gap_vol=0.25, buffer=0.3):
    """Build FFmpeg volume filter expression for ducking during speech regions.

    Args:
        regions: list of {"start": float, "end": float} dicts or (start, end) tuples
        speech_vol: volume multiplier during speech (default 0.12)
        gap_vol: volume multiplier outside speech (default 0.25)
        buffer: extra seconds to extend each speech region on both sides

    Returns:
        FFmpeg audio filter string ready to pass to -af
    """
    if not regions:
        return f"volume={gap_vol}"

    conditions = []
    for r in regions:
        if isinstance(r, dict):
            start, end = float(r["start"]), float(r["end"])
        else:
            start, end = float(r[0]), float(r[1])
        s = max(0.0, start - buffer)
        e = end + buffer
        conditions.append(f"between(t,{s:.2f},{e:.2f})")

    expr = "+".join(conditions)
    return f"volume='if({expr},{speech_vol},{gap_vol})':eval=frame"


def _extract_speech_regions_whisper(video_path):
    """Try to extract speech regions using openai-whisper."""
    try:
        import whisper  # type: ignore
    except ImportError:
        print("Error: --whisper flag requires 'openai-whisper' package.")
        print("  Install: pip install openai-whisper")
        sys.exit(1)

    print("  Extracting speech regions with Whisper (this may take a moment)...")
    model = whisper.load_model("base")
    result = model.transcribe(str(video_path), word_timestamps=True)

    regions = []
    for segment in result.get("segments", []):
        regions.append({"start": segment["start"], "end": segment["end"]})

    # Merge regions with gap < 0.5s
    if not regions:
        return regions
    merged = [regions[0].copy()]
    for r in regions[1:]:
        if r["start"] - merged[-1]["end"] < 0.5:
            merged[-1]["end"] = r["end"]
        else:
            merged.append(r.copy())
    print(f"  Detected {len(merged)} speech regions")
    return merged


def ducking(args):
    """Auto-duck music volume during speech regions in a video."""
    _check_ffmpeg()

    video_path = os.path.abspath(args.video)
    if not os.path.exists(video_path):
        print(f"Error: video not found: {video_path}")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    output = args.output or f"ducked_{job_id}.mp4"

    # Get speech regions
    if args.whisper:
        regions = _extract_speech_regions_whisper(video_path)
    elif args.timestamps:
        ts_path = os.path.abspath(args.timestamps)
        if not os.path.exists(ts_path):
            print(f"Error: timestamps file not found: {ts_path}")
            sys.exit(1)
        with open(ts_path, "r", encoding="utf-8") as f:
            regions = json.load(f)
        print(f"  Loaded {len(regions)} speech regions from {ts_path}")
    else:
        print("Error: provide --timestamps TIMESTAMPS_JSON or --whisper")
        sys.exit(1)

    if not regions:
        print("Warning: no speech regions found, applying flat gap volume")

    duck_filter = _build_duck_filter(
        regions,
        speech_vol=args.speech_vol,
        gap_vol=args.gap_vol,
        buffer=args.buffer,
    )
    print(f"  Duck filter: {duck_filter[:80]}{'...' if len(duck_filter) > 80 else ''}")

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-af", duck_filter,
        "-c:v", "copy",
        output
    ]

    if not _run_ffmpeg(cmd, "ducking"):
        sys.exit(1)

    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"Done: {output} ({size_mb:.1f} MB, {len(regions)} speech regions)")


# ---------------------------------------------------------------------------
# NEW: thumbnail
# ---------------------------------------------------------------------------

def _find_font():
    """Try to find a usable font path for PIL ImageFont."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        # macOS
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def thumbnail(args):
    """Generate a YouTube thumbnail from an image and text overlay."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except ImportError:
        print("Error: 'Pillow' package is required for thumbnail generation.")
        print("  Install: pip install Pillow")
        sys.exit(1)

    img_path = os.path.abspath(args.image)
    if not os.path.exists(img_path):
        print(f"Error: image not found: {img_path}")
        sys.exit(1)

    job_id = str(uuid.uuid4())[:8]
    output = args.output or f"thumbnail_{job_id}.png"

    print(f"Thumbnail: {Path(img_path).name} → \"{args.text}\"")

    # Open and resize to 1280x720
    img = Image.open(img_path).convert("RGB")
    target_w, target_h = 1280, 720
    orig_w, orig_h = img.size

    # Cover-crop: scale so image fills 1280x720 without whitespace
    scale = max(target_w / orig_w, target_h / orig_h)
    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS  # type: ignore[attr-defined]
    img = img.resize((new_w, new_h), resample)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    draw = ImageDraw.Draw(img)

    # Semi-transparent black bar at bottom 25%
    bar_h = int(target_h * 0.25)
    bar_top = target_h - bar_h
    overlay = Image.new("RGBA", (target_w, bar_h), (0, 0, 0, 160))
    img_rgba = img.convert("RGBA")
    img_rgba.paste(overlay, (0, bar_top), overlay)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Load font
    font_path = _find_font()
    font_size = args.font_size
    font = None
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
            print(f"  Font: {Path(font_path).name} @ {font_size}px")
        except (IOError, OSError) as e:
            print(f"  Warning: could not load font {font_path}: {e}")
    if font is None:
        font = ImageFont.load_default()
        print("  Font: PIL default (install a TTF font for better results)")

    # Measure text and center it in the bar
    text = args.text
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        # Older PIL fallback
        text_w, text_h = draw.textsize(text, font=font)  # type: ignore[attr-defined]

    text_x = (target_w - text_w) // 2
    text_y = bar_top + (bar_h - text_h) // 2

    # Drop shadow (3px offset, black)
    draw.text((text_x + 3, text_y + 3), text, font=font, fill=(0, 0, 0))
    # Main text (white)
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))

    img.save(output, "PNG")
    size_kb = os.path.getsize(output) / 1024
    print(f"Done: {output} ({size_kb:.0f} KB, 1280x720)")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Video Editor CLI (local FFmpeg)")
    sub = parser.add_subparsers(dest="command", required=True)

    # concat
    p = sub.add_parser("concat", help="Concatenate video files")
    p.add_argument("videos", nargs="+", help="Video files (min 2)")
    p.add_argument("--music", action="store_true", help="Add background music")
    p.add_argument("--custom-music", help="Custom music file path")
    p.add_argument("--music-volume", type=float, default=0.3)
    p.add_argument("--transition", choices=["none", "fade", "dissolve"], default="none")
    p.add_argument("--transition-duration", type=float, default=0.5)
    p.add_argument("--output", "-o", help="Output file path")
    p.set_defaults(func=concat)

    # process
    p = sub.add_parser("process", help="Process single video")
    p.add_argument("video", help="Video file")
    p.add_argument("--music", action="store_true")
    p.add_argument("--custom-music", help="Custom music file")
    p.add_argument("--music-volume", type=float, default=0.3)
    p.add_argument("--brightness", type=float, default=1.0, help="0.0-2.0")
    p.add_argument("--contrast", type=float, default=1.0, help="0.0-2.0")
    p.add_argument("--saturation", type=float, default=1.0, help="0.0-3.0")
    p.add_argument("--output", "-o")
    p.set_defaults(func=process)

    # trim
    p = sub.add_parser("trim", help="Trim video")
    p.add_argument("video", help="Video file")
    p.add_argument("--start", "-ss", help="Start time (HH:MM:SS or seconds)")
    p.add_argument("--end", "-to", help="End time (HH:MM:SS or seconds)")
    p.add_argument("--output", "-o")
    p.set_defaults(func=trim)

    # probe
    p = sub.add_parser("probe", help="Show video info")
    p.add_argument("video", help="Video file")
    p.set_defaults(func=probe)

    # music-pool
    p = sub.add_parser("music-pool", help="Show music pool")
    p.set_defaults(func=music_pool)

    # ken-burns
    p = sub.add_parser("ken-burns", help="Animate static image with Ken Burns camera motion")
    p.add_argument("image", help="Input image file (JPG, PNG, etc.)")
    p.add_argument("--duration", type=float, default=5.0, help="Output duration in seconds (default: 5)")
    p.add_argument(
        "--effect",
        choices=["zoom_in", "pan_right", "zoom_out"],
        default=None,
        help="Camera effect (default: auto-cycle based on filename)",
    )
    p.add_argument("--output", "-o", help="Output video file path")
    p.set_defaults(func=ken_burns)

    # ducking
    p = sub.add_parser("ducking", help="Auto-duck music volume during speech regions")
    p.add_argument("video", help="Input video file with mixed audio")
    p.add_argument(
        "--timestamps",
        help="Path to JSON file with speech regions: [{\"start\": 1.2, \"end\": 3.5}, ...]",
    )
    p.add_argument(
        "--whisper",
        action="store_true",
        help="Auto-detect speech regions using Whisper (requires openai-whisper)",
    )
    p.add_argument("--speech-vol", type=float, default=0.12, help="Music volume during speech (default: 0.12)")
    p.add_argument("--gap-vol", type=float, default=0.25, help="Music volume in gaps (default: 0.25)")
    p.add_argument("--buffer", type=float, default=0.3, help="Seconds to pad each speech region (default: 0.3)")
    p.add_argument("--output", "-o", help="Output file path")
    p.set_defaults(func=ducking)

    # thumbnail
    p = sub.add_parser("thumbnail", help="Generate YouTube thumbnail from image + text")
    p.add_argument("image", help="Input image file")
    p.add_argument("--text", required=True, help="Text to overlay on the thumbnail")
    p.add_argument("--font-size", type=int, default=60, help="Font size in pixels (default: 60)")
    p.add_argument("--output", "-o", help="Output PNG file path")
    p.set_defaults(func=thumbnail)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
