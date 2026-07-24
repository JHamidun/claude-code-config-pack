#!/usr/bin/env python3
"""
assemble.py — self-contained ffmpeg-assembly module porting Higgsfield's sandbox
media pipeline. Each function shells out to ffmpeg with the EXACT command from the
Higgsfield sandbox references (sandbox-media-scripts.md,
sandbox-camera-audio-transcribe.md, sandbox-titles-assembly-platform.md,
sandbox-creative-effects.md).

No third-party deps — only ffmpeg/ffprobe on PATH (+ whisper for SRT step, noted).

CLI:
    python assemble.py <command> [args...]
    python assemble.py --help
"""

import argparse
import glob
import os
import subprocess
import sys
import tempfile

# Cross-platform bold font (Windows / Linux / macOS); falls back to a bare name on PATH.
FONT = next((p for p in (
    r"C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
) if os.path.exists(p)), "DejaVuSans-Bold.ttf")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _run(cmd):
    """Run an ffmpeg command (list of args) and return the exit code."""
    print("+ " + " ".join(str(c) for c in cmd), file=sys.stderr)
    return subprocess.run(cmd, check=True)


def _ffprobe_duration(path):
    """Return float duration (seconds) of a media file via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


# ---------------------------------------------------------------------------
# 1. Poster / thumbnail grid  (sandbox-media-scripts.md §1,2)
# ---------------------------------------------------------------------------
def poster(inp, out):
    """Poster frame at 1s (anti-black-frame), 1280x720 letterboxed, q:v 2."""
    return _run([
        "ffmpeg", "-y", "-i", inp,
        "-ss", "00:00:01", "-vframes", "1", "-q:v", "2",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
        out,
    ])


def thumb_grid(inp, out, cols=3, rows=3):
    """Contact sheet cols x rows. For 15s/9 frames step=1.5s -> fps=1/1.5."""
    cols = int(cols)
    rows = int(rows)
    n = cols * rows
    # step so that n tiles span the clip; mirrors §2 (3x3 -> 1.5s, 4x3 -> 1.2s)
    try:
        dur = _ffprobe_duration(inp)
        step = max(dur / n, 0.1)
    except Exception:
        step = 1.5
    return _run([
        "ffmpeg", "-y", "-i", inp,
        "-vf", f"fps=1/{step:g},scale=320:180,tile={cols}x{rows}",
        "-vframes", "1", out,
    ])


# ---------------------------------------------------------------------------
# 3. Concat / web mp4  (sandbox-media-scripts.md §3)
# ---------------------------------------------------------------------------
def concat(clips, out):
    """Stream-copy concat (same codec/res). clips = list of paths."""
    tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                      encoding="utf-8")
    try:
        for c in clips:
            tmp.write(f"file '{os.path.abspath(c)}'\n")
        tmp.close()
        return _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", tmp.name,
            "-c", "copy", out,
        ])
    finally:
        os.unlink(tmp.name)


def to_web_mp4(inp, out):
    """MOV/WebM -> web MP4 (H.264 slow crf22 / AAC 128k / yuv420p for iOS)."""
    return _run([
        "ffmpeg", "-y", "-i", inp,
        "-c:v", "libx264", "-preset", "slow", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", out,
    ])


# ---------------------------------------------------------------------------
# Aspect / blurred-bg reframe  (sandbox-titles-assembly-platform.md §5)
# ---------------------------------------------------------------------------
def reframe_blurred_bg(inp, out, target="9:16"):
    """Blurred-bg fill to 9:16 (default): boxblur 40 background + centred fg."""
    dims = {"9:16": (1080, 1920), "16:9": (1920, 1080),
            "1:1": (1080, 1080), "4:5": (1080, 1350)}
    w, h = dims.get(target, (1080, 1920))
    fc = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},boxblur=luma_radius=40:luma_power=3[bg];"
        f"[0:v]scale={w}:-1[fg];"
        f"[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2:format=rgb[outv]"
    )
    return _run([
        "ffmpeg", "-y", "-i", inp,
        "-filter_complex", fc,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out,
    ])


# ---------------------------------------------------------------------------
# xfade chain  (sandbox-titles-assembly-platform.md §2 — cumulative offsets)
# ---------------------------------------------------------------------------
def xfade_chain(clips, out, transition="dissolve", dur=1.0):
    """
    Chain xfade across N clips. Cumulative offset formula (from ref):
        offset_i = (prev_offset + prev_clip_dur) - dur
    For 3x5s clips, dur=1 -> offsets 4, 8.
    """
    dur = float(dur)
    clips = list(clips)
    if len(clips) < 2:
        raise ValueError("xfade_chain needs >= 2 clips")

    durations = [_ffprobe_duration(c) for c in clips]

    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", c]

    parts = []
    # first pair
    offset = durations[0] - dur
    label = "[v01]"
    parts.append(
        f"[0:v][1:v]xfade=transition={transition}:duration={dur:g}:"
        f"offset={offset:g}{label}"
    )
    cum = offset  # running offset of last applied xfade
    prev = label
    for i in range(2, len(clips)):
        # cumulative: new offset = prev_offset + (prev_clip_dur) - dur
        offset = cum + durations[i - 1] - dur
        out_label = f"[v0{i}]" if i < len(clips) - 1 else "[vout]"
        parts.append(
            f"{prev}[{i}:v]xfade=transition={transition}:duration={dur:g}:"
            f"offset={offset:g}{out_label}"
        )
        cum = offset
        prev = out_label
    if len(clips) == 2:
        prev = "[vout]"
        parts[-1] = parts[-1].replace("[v01]", "[vout]")

    fc = ";".join(parts)
    cmd += ["-filter_complex", fc, "-map", prev,
            "-c:v", "libx264", "-crf", "18", out]
    return _run(cmd)


# ---------------------------------------------------------------------------
# Color / LUT  (sandbox-media-scripts.md §9)
# ---------------------------------------------------------------------------
def color_lut(inp, out, cube):
    """Apply a .cube 3D LUT (film look / teal-orange). Use the LUT_3D_INPUT_RANGE-sanitized .cube.
    Windows fix: ffmpeg's filter parser splits on ':' so a drive path 'C:/...' inside lut3d= breaks
    (and Git Bash further mangles escaped 'C\\:/'). We sidestep both by running ffmpeg FROM the LUT's
    directory with a bare filename — input/output keep their absolute (colon-ok) paths."""
    cube_dir, cube_name = os.path.split(os.path.abspath(cube))
    inp_abs, out_abs = os.path.abspath(inp), os.path.abspath(out)
    print(f"[..] color_lut {cube_name}")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", inp_abs, "-vf", f"lut3d={cube_name}", "-c:a", "copy", out_abs],
        cwd=cube_dir, capture_output=True,
    )
    if r.returncode != 0:
        print((r.stderr or b"").decode("utf-8", errors="replace")[-1500:])
        raise SystemExit(f"color_lut failed (rc={r.returncode})")


# ---------------------------------------------------------------------------
# Audio  (sandbox-media-scripts.md §7)
# ---------------------------------------------------------------------------
def audio_duck(video, music, out):
    """VO + BGM auto-ducking via sidechaincompress (thr 0.15 ratio 4)."""
    fc = (
        "[0:a]volume=1.0[voice];"
        "[1:a]volume=0.2[bgm_quiet];"
        "[bgm_quiet][voice]sidechaincompress=threshold=0.15:ratio=4:"
        "release=500:attack=15[mixed_audio]"
    )
    return _run([
        "ffmpeg", "-y", "-i", video, "-i", music,
        "-filter_complex", fc,
        "-map", "0:v", "-map", "[mixed_audio]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out,
    ])


def loudnorm(inp, out, I=-14):
    """
    EBU R128 loudnorm. Ref §7 uses I=-16 for broadcast; default I=-14 here
    (social / platform target). TP=-1.5 LRA=11 per ref.
    """
    return _run([
        "ffmpeg", "-y", "-i", inp,
        "-af", f"loudnorm=I={I}:TP=-1.5:LRA=11:print_format=summary", out,
    ])


# ---------------------------------------------------------------------------
# Subtitles  (sandbox-media-scripts.md §8)
# ---------------------------------------------------------------------------
def burn_ass(video, ass, out):
    """Burn an ASS karaoke (word-highlight {\\k}) subtitle file into video."""
    return _run([
        "ffmpeg", "-y", "-i", video,
        "-vf", f"ass={ass}", "-c:a", "copy", out,
    ])


# ---------------------------------------------------------------------------
# Transparent outputs  (palettegen/paletteuse + alpha)
# ---------------------------------------------------------------------------
def transparent_webm(frames_glob, out):
    """PNG frame sequence (alpha) -> VP9 WebM with alpha (yuva420p)."""
    return _run([
        "ffmpeg", "-y", "-framerate", "30", "-pattern_type", "glob",
        "-i", frames_glob,
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0", "-b:v", "0", "-crf", "20", out,
    ])


def apng(frames_glob, out):
    """PNG frame sequence -> animated PNG (APNG) preserving alpha."""
    return _run([
        "ffmpeg", "-y", "-framerate", "30", "-pattern_type", "glob",
        "-i", frames_glob,
        "-f", "apng", "-plays", "0", out,
    ])


# ---------------------------------------------------------------------------
# Ken Burns  (sandbox-camera-audio-transcribe.md §1)
# ---------------------------------------------------------------------------
def ken_burns(img, out, dur=5, size="1920x1080"):
    """
    Ken Burns / push-in (zoompan), ASPECT-AWARE. size='WxH' (e.g. '1080x1920' for 9:16,
    '1920x1080' for 16:9). Covers+crops the source to target aspect so portrait stills
    yield portrait clips. d computed from dur (5s @ 25fps -> 125 frames).
    """
    dur = float(dur)
    d = int(round(dur * 25))
    w, h = (int(v) for v in size.lower().split("x"))
    vf = (
        f"scale={w * 4}:{h * 4}:force_original_aspect_ratio=increase,crop={w * 4}:{h * 4},"
        f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d={d}:s={w}x{h}:fps=25"
    )
    return _run([
        "ffmpeg", "-y", "-loop", "1", "-i", img,
        "-vf", vf, "-t", f"{dur:g}",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out,
    ])


# ---------------------------------------------------------------------------
# Beat-sync cut  (sandbox-titles-assembly-platform.md §2 — Python port)
# ---------------------------------------------------------------------------
def beat_sync_cut(clips, audio, beats_ms, out):
    """
    Cut clips at beat timecodes (ms) -> concat + overlay audio.
    beats_ms = [1200, 2400, 3600, ...]. Mirrors the ref beat_sync() exactly.
    """
    clips = list(clips)
    beats = [float(b) for b in beats_ms]
    segs = []
    prev = 0.0
    tmpdir = tempfile.mkdtemp(prefix="beatsync_")
    try:
        for i, b in enumerate(beats):
            cur = b / 1000.0
            seg = os.path.join(tmpdir, f"seg_{i}.mp4")
            _run([
                "ffmpeg", "-y", "-ss", str(prev), "-to", str(cur),
                "-i", clips[i % len(clips)],
                "-c:v", "libx264", "-crf", "18", "-r", "30",
                "-pix_fmt", "yuv420p", "-an", seg,
            ])
            segs.append(seg)
            prev = cur
        cl = os.path.join(tmpdir, "cl.txt")
        with open(cl, "w", encoding="utf-8") as f:
            f.write("".join(f"file '{s}'\n" for s in segs))
        return _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", cl,
            "-i", audio, "-c:v", "copy", "-c:a", "aac", "-shortest", out,
        ])
    finally:
        for s in segs:
            try:
                os.unlink(s)
            except OSError:
                pass
        try:
            os.unlink(cl)
        except OSError:
            pass
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Platform export  (sandbox-titles-assembly-platform.md §4 — TikTok/Reels) ⭐
# ---------------------------------------------------------------------------
def platform_export(inp, out):
    """
    TikTok/Reels/Shorts preset: H.264 High@4.2, yuv420p, GOP=2s (g=60),
    audio -14 LUFS (loudnorm I=-14:LRA=11:TP=-1.5). EXACT flags from ref §4.
    """
    return _run([
        "ffmpeg", "-y", "-i", inp,
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.2",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", "-bf", "2",
        "-b:v", "6M", "-maxrate", "10M", "-bufsize", "12M",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-af", "loudnorm=I=-14:LRA=11:TP=-1.5",
        out,
    ])


# ---------------------------------------------------------------------------
# Audio visualizer  (sandbox-camera-audio-transcribe.md §6)
# ---------------------------------------------------------------------------
def showwaves(audio, out):
    """Waveform visualizer (mirrored lines, log-scale) -> mp4."""
    fc = (
        "[0:a]showwaves=s=1920x1080:mode=line:"
        "colors=0x00ffff|0x008b8b:scale=log[v]"
    )
    return _run([
        "ffmpeg", "-y", "-i", audio,
        "-filter_complex", fc,
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "20", "-c:a", "copy", out,
    ])


# ---------------------------------------------------------------------------
# Whisper SRT  (sandbox-camera-audio-transcribe.md §7)
# ---------------------------------------------------------------------------
def whisper_srt(audio, out):
    """
    Extract mono 16k WAV for ASR (exact ffmpeg from ref §7), then transcribe
    with whisper large-v3, word_timestamps + highlight_words -> SRT.

    The ffmpeg extraction always runs. The whisper step runs only if the
    `whisper` package is importable; otherwise it prints the equivalent recipe.
    """
    wav = os.path.splitext(out)[0] + "_mono16k.wav"
    _run([
        "ffmpeg", "-y", "-i", audio,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav,
    ])
    try:
        import whisper
        from whisper.utils import get_writer
    except ImportError:
        print(
            "NOTE: whisper not installed. Extracted 16k mono WAV at:\n"
            f"  {wav}\n"
            "Run transcription with whisper large-v3:\n"
            "  import whisper; from whisper.utils import get_writer\n"
            "  model = whisper.load_model('large-v3')\n"
            f"  result = model.transcribe('{wav}', temperature=0.0,\n"
            "      word_timestamps=True, beam_size=5)\n"
            f"  get_writer('srt', '{os.path.dirname(out) or '.'}')(result,\n"
            f"      '{wav}', {{'max_line_width':42,'max_line_count':2,\n"
            "      'highlight_words':True}})",
            file=sys.stderr,
        )
        return None
    model = whisper.load_model("large-v3")
    result = model.transcribe(wav, temperature=0.0,
                              word_timestamps=True, beam_size=5)
    out_dir = os.path.dirname(os.path.abspath(out)) or "."
    get_writer("srt", out_dir)(
        result, wav,
        {"max_line_width": 42, "max_line_count": 2, "highlight_words": True},
    )
    return None


# ---------------------------------------------------------------------------
# argparse __main__ dispatch
# ---------------------------------------------------------------------------
def _build_parser():
    p = argparse.ArgumentParser(
        description="Higgsfield sandbox ffmpeg-assembly pipeline (local port)."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("poster"); s.add_argument("inp"); s.add_argument("out")

    s = sub.add_parser("thumb_grid")
    s.add_argument("inp"); s.add_argument("out")
    s.add_argument("--cols", type=int, default=3)
    s.add_argument("--rows", type=int, default=3)

    s = sub.add_parser("concat")
    s.add_argument("clips", nargs="+"); s.add_argument("--out", required=True)

    s = sub.add_parser("to_web_mp4"); s.add_argument("inp"); s.add_argument("out")

    s = sub.add_parser("reframe_blurred_bg")
    s.add_argument("inp"); s.add_argument("out")
    s.add_argument("--target", default="9:16")

    s = sub.add_parser("xfade_chain")
    s.add_argument("clips", nargs="+"); s.add_argument("--out", required=True)
    s.add_argument("--transition", default="dissolve")
    s.add_argument("--dur", type=float, default=1.0)

    s = sub.add_parser("color_lut")
    s.add_argument("inp"); s.add_argument("out"); s.add_argument("cube")

    s = sub.add_parser("audio_duck")
    s.add_argument("video"); s.add_argument("music"); s.add_argument("out")

    s = sub.add_parser("loudnorm")
    s.add_argument("inp"); s.add_argument("out")
    s.add_argument("--I", type=float, default=-14)

    s = sub.add_parser("burn_ass")
    s.add_argument("video"); s.add_argument("ass"); s.add_argument("out")

    s = sub.add_parser("transparent_webm")
    s.add_argument("frames_glob"); s.add_argument("out")

    s = sub.add_parser("apng")
    s.add_argument("frames_glob"); s.add_argument("out")

    s = sub.add_parser("ken_burns")
    s.add_argument("img"); s.add_argument("out")
    s.add_argument("--dur", type=float, default=5)

    s = sub.add_parser("beat_sync_cut")
    s.add_argument("clips", nargs="+")
    s.add_argument("--audio", required=True)
    s.add_argument("--beats_ms", required=True,
                   help="comma-separated beat timecodes in ms")
    s.add_argument("--out", required=True)

    s = sub.add_parser("platform_export")
    s.add_argument("inp"); s.add_argument("out")

    s = sub.add_parser("showwaves")
    s.add_argument("audio"); s.add_argument("out")

    s = sub.add_parser("whisper_srt")
    s.add_argument("audio"); s.add_argument("out")

    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    c = args.cmd
    if c == "poster":
        poster(args.inp, args.out)
    elif c == "thumb_grid":
        thumb_grid(args.inp, args.out, args.cols, args.rows)
    elif c == "concat":
        concat(args.clips, args.out)
    elif c == "to_web_mp4":
        to_web_mp4(args.inp, args.out)
    elif c == "reframe_blurred_bg":
        reframe_blurred_bg(args.inp, args.out, args.target)
    elif c == "xfade_chain":
        xfade_chain(args.clips, args.out, args.transition, args.dur)
    elif c == "color_lut":
        color_lut(args.inp, args.out, args.cube)
    elif c == "audio_duck":
        audio_duck(args.video, args.music, args.out)
    elif c == "loudnorm":
        loudnorm(args.inp, args.out, args.I)
    elif c == "burn_ass":
        burn_ass(args.video, args.ass, args.out)
    elif c == "transparent_webm":
        transparent_webm(args.frames_glob, args.out)
    elif c == "apng":
        apng(args.frames_glob, args.out)
    elif c == "ken_burns":
        ken_burns(args.img, args.out, args.dur)
    elif c == "beat_sync_cut":
        beats = [int(x) for x in args.beats_ms.split(",") if x.strip()]
        beat_sync_cut(args.clips, args.audio, beats, args.out)
    elif c == "platform_export":
        platform_export(args.inp, args.out)
    elif c == "showwaves":
        showwaves(args.audio, args.out)
    elif c == "whisper_srt":
        whisper_srt(args.audio, args.out)


if __name__ == "__main__":
    main()
