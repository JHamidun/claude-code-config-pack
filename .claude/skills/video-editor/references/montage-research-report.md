# MONTAGE RESEARCH — ANALYTICS REPORT + UPGRADE PLAN

---

## 1. EXECUTIVE SUMMARY

### Where Our Stack Stands vs Pro

**What we have:** AI video generation (Veo/Sora/Seedance), TTS pipeline (ElevenLabs + Suno + Lyria), basic ffmpeg assembly (xfade chain, amix, sidechain ducking, loudnorm, Ken Burns, PIL title cards, ASS karaoke from TTS timestamps, 3-tier compression). Paid captions via SubtitleService. HeyGen avatar + captions.

**What pro editors have that we lack:**

| Gap | Severity | Revenue Impact |
|-----|----------|---------------|
| Beat-synced cuts (music drives edits) | CRITICAL | Virality |
| Animated word-highlight captions (Hormozi/CapCut style) | CRITICAL | Retention +15–25% |
| Silence/jump-cut auto-removal | HIGH | Pacing |
| Auto-reframe 16:9→9:16 | HIGH | Shorts/Reels reach |
| Color grading with LUTs | HIGH | Visual identity |
| Speed ramps (slow-mo→fast) | MEDIUM | Cinematic feel |
| GL/shader transitions | MEDIUM | Polish |
| Social-UI composited overlays (Instagram/Telegram chrome) | MEDIUM | Engagement hooks |
| Motion graphics (kinetic text, data viz) | MEDIUM | Authority |
| Shot boundary detection for b-roll automation | LOW | Efficiency |

### Top 5 Highest-Leverage Upgrades

1. **auto-editor** — one command removes all dead air from raw recordings. Closes silence/jump-cut gap with zero custom code. Biggest quality-per-effort ratio.
2. **WhisperX + ASS \\kf karaoke pipeline** — replace paid SubtitleService with sub-100ms word-level animated captions. Already partially built (TTS-with-timestamps→ASS in stack), just needs WhisperX upgrade + \\kf format.
3. **librosa beat-sync pipeline** — 50 lines of Python, pure Windows/pip. Unlocks music-driven montage automation.
4. **Kodak 2383 LUT + ffmpeg lut3d** — single .cube file download + one ffmpeg flag = Hollywood print-film look on every output.
5. **captacity** — one pip install + one Python call wraps any output with animated word-highlight captions. Zero ASS knowledge needed.

---

## 2. TOOL LANDSCAPE

### 2A. Silence/Jump-Cut Auto-Edit

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **auto-editor** ⭐ PICK | Silence+motion detection, NLE XML export | Unlicense (PD) | 4.4k★, v30.4.0 Jun 2026 | LOW — pip install + CLI | Silence/jump-cut |
| jumpcutter (emkademy) | ffmpeg silencedetect wrapper | MIT | Stable | LOW | Silence/jump-cut |
| ffmpeg silencedetect (raw) | Built-in filter, parse stderr | LGPL | Production | MEDIUM — Python parser | Silence/jump-cut |

**PICK: auto-editor.** Windows binary available at auto-editor.com, also pip installable. Exports Premiere/Resolve/FCP XML for NLE roundtrip.

### 2B. Beat Detection / Beat-Sync Editing

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **librosa** ⭐ PICK | beat_track, onset_detect, BPM | ISC | 7.5k★, production | LOW — pip install | Beat-sync cuts |
| madmom | RNN+DBN, highest accuracy | BSD-3 | Stable, research-grade | MEDIUM — needs VC++ Build Tools | Beat-sync, downbeats |
| BeatNet | CRNN+particle filter, joint beat/downbeat/meter | MIT | 500★, v1.2.0 | MEDIUM | Beat-sync, downbeats |
| aubio | C lib + Python, lightweight, CLI | GPL-3.0 | 3.7k★, stable | LOW — pip install | Beat-sync, onsets |
| emjjkk/beat-detection | librosa → EDL markers for NLE | MIT | Small utility | LOW | EDL marker export |

**PICK: librosa** for primary beat detection (pip, pure Python, Windows). **madmom** as upgrade for complex/non-EDM music.

### 2C. Animated/Viral Captions

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **captacity** ⭐ PICK (fast path) | Whisper + MoviePy word-highlight, one call | MIT | 137★, alpha | VERY LOW — pip install | Animated captions |
| **WhisperX + ASS \\kf** ⭐ PICK (quality path) | Sub-100ms word timestamps + karaoke format | BSD-4 | 22.3k★, production | MEDIUM — CUDA 12.8 + conda | Animated captions |
| pycaps | CSS-driven animated subtitles, Playwright | MIT | 154★, alpha | MEDIUM — pip + playwright install | Animated captions |
| PupCaps | Node.js CSS karaoke overlay | MIT | 54★ | LOW (Node) | Animated captions |
| Remotion @remotion/captions | React word-by-word spring animation | BUSL (free <$1M ARR) | 39k★+ | MEDIUM (Node/React) | Animated captions |

**PICK: captacity** for immediate deployment (one pip install replaces SubtitleService). **WhisperX + ASS \\kf pipeline** for production quality.

### 2D. GL/Shader Transitions

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **ffmpeg xfade** ⭐ PICK | 44 built-in transitions, native ffmpeg | LGPL | Production | VERY LOW | Basic transitions |
| **xfade-easing** ⭐ PICK | 80+ GLSL transitions + CSS easing for xfade | MIT | 114★ | MEDIUM — MSYS2 build or expression mode | GL transitions |
| ffmpeg-concat | Node CLI, 30+ GL transitions via headless GL | MIT | 988★ | LOW (Node) — npm install -g | GL transitions |
| ffmpeg-gl-transition | Native GLSL in ffmpeg (C filter) | MIT | ~1.5k★ | HIGH — compile from source | Full GLSL |
| gl-transitions collection | 60+ GLSL shaders | MIT/mixed | 2.1k★ | Source library | Reference |

**PICK: xfade-easing** for pure ffmpeg path (expression mode, no recompile). **ffmpeg-concat** for Node-available steps.

### 2E. Motion Graphics + Social-UI Overlays

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **Remotion** ⭐ PICK | React→video, social UI chrome, kinetic text | BUSL (free personal) | 49.1k★ | MEDIUM (Node/React) | Social overlays, motion graphics |
| **movis** ⭐ PICK | Python keyframe+easing compositing | MIT | 475★ | LOW — pip install | Motion graphics in Python |
| Motion Canvas | TypeScript vector animation | MIT | 18.6k★ | MEDIUM (Node) | Kinetic typography |
| Revideo | MIT fork of Motion Canvas, renderVideo() API | MIT | 3.8k★ | MEDIUM (Node) | Batch motion graphics |
| FFCreator | Node, ~90 animate.css effects | MIT | 3.2k★ | LOW (Node) | Animated title cards |
| Manim Community | Python math/explanatory animation | MIT | 20k★ | MEDIUM — LaTeX required | Data viz, kinetic titles |

**PICK: Remotion** for Instagram/Telegram chrome overlays and kinetic captions. **movis** for Python-native motion graphics.

### 2F. Auto-Reframe 16:9→9:16

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **Autocrop-vertical** ⭐ PICK | YOLOv8 per-scene + ffmpeg, TRACK/LETTERBOX | Not specified | 277★, v1.4.1 recent | LOW — Python + ffmpeg | Auto-reframe |
| pyautoflip | UNISAL saliency + MediaPipe, pip install | Not specified | 14★, v0.2.0 Mar 2026 | LOW | Saliency-based reframe |
| OpenShorts | Full pipeline incl. reframe + captions (Docker) | MIT | 2.3k★ | HIGH — Docker | End-to-end Shorts |
| AI-Youtube-Shorts-Generator | LLM virality scoring + reframe + captions | MIT | 3.8k★ | MEDIUM | End-to-end Shorts |
| smart-reframe | Audio-reactive speaker tracking | MIT | 0★ published | LOW — pip | Podcast/interview |
| ffmpeg static center crop | One-liner, no tracking | LGPL | Production | VERY LOW | Simple reframe |

**PICK: Autocrop-vertical** for batch unattended processing. **pyautoflip** for saliency-based content (products, nature).

### 2G. Color Grading / LUTs

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **ffmpeg lut3d** ⭐ PICK | Apply .cube LUT files natively | LGPL | Production | VERY LOW | Color grading |
| **ffmpeg haldclut** ⭐ PICK | Apply PNG-based LUT (editable in Photoshop) | LGPL | Production | LOW | Color grading |
| YahiaAngelo/Film-Luts | Free .cube film LUT collection (G'MIC) | Open | 190★ | VERY LOW — download + apply | Film look |
| imnz730/LUTs | Kodak 2383 D55 + camera log LUTs | Open | 134★ | VERY LOW — download + apply | Hollywood look |
| spectral_film_lut | Generate .cube from real film datasheets (GUI) | Open | 67★ | LOW — Python GUI | Custom film emulation |
| ComfyUI-Darkroom | 161 film stocks, exports .cube | Open | 69★ | HIGH — ComfyUI | Custom film emulation |
| scikit-image match_histograms | Color match between shots (Python) | BSD | Production | LOW — pip | Shot color matching |

**PICK: imnz730 Kodak 2383 + ffmpeg lut3d** for immediate Hollywood look. **haldclut workflow** for custom grades.

### 2H. Scene Detection / Shot Boundaries

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **PySceneDetect** ⭐ PICK | Content+adaptive detection, Python API + CLI | BSD-3 | 4.9k★, v0.7 May 2026 | LOW — pip install | Scene segmentation |
| TransNetV2 | Neural shot detection (F1 96.2 on Planet Earth) | MIT | 956★ | MEDIUM — PyTorch | Dissolve/fade detection |

**PICK: PySceneDetect** for primary detection. TransNetV2 as accuracy upgrade for complex transitions.

### 2I. Video Assembly / Pipeline

| Tool | What | License | Maturity | Integration | Gap Closed |
|------|------|---------|----------|-------------|------------|
| **MoviePy v2** ⭐ PICK | Pythonic clip concat, composite, audio mix | MIT | 14.7k★ | LOW — pip | Assembly prototyping |
| VidGear | Multi-gear Python ffmpeg wrapper | Apache-2.0 | 3.7k★ | LOW — pip | Pipeline integration |
| OpenTimelineIO | Parse/write NLE timelines (EDL, OTIO, FCP XML) | Apache-2.0 | 1.9k★ | LOW — pip | NLE roundtrip |

---

## 3. TECHNIQUE LIBRARY

### 3A. Dynamic Cutting

**Silence/Jump-Cut Removal:**
```bash
# auto-editor (recommended — Windows binary available)
pip install auto-editor
auto-editor input.mp4 --margin 0.2sec --edit audio:threshold=4% -o cut.mp4

# Export to DaVinci Resolve XML (non-destructive)
auto-editor input.mp4 --export davinci-resolve -o resolve.xml

# Fast-forward silence instead of cutting (YouTube vlogger style)
auto-editor input.mp4 --when-silent speed:8 -o speed.mp4
```

**Raw ffmpeg silencedetect pipeline:**
```python
import subprocess, re

def detect_silence(input_file, thresh_db=-35, min_duration=0.4):
    cmd = ['ffmpeg', '-hide_banner', '-vn', '-i', input_file,
           '-af', f'silencedetect=n={thresh_db}dB:d={min_duration}',
           '-f', 'null', '-']
    result = subprocess.run(cmd, capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r'silence_start: (\S+)', result.stderr)]
    ends = [float(x) for x in re.findall(r'silence_end: (\S+)', result.stderr)]
    return list(zip(starts, ends))

def silence_to_keep_segments(silences, total_duration, padding=0.1):
    keep, prev = [], 0.0
    for s_start, s_end in silences:
        seg_end = s_start + padding
        if seg_end - prev > 0.1:
            keep.append((max(0, prev - padding), seg_end))
        prev = s_end
    keep.append((prev - padding, total_duration))
    return keep

def build_concat_filter(input_file, output_file, segs):
    n = len(segs)
    fp = []
    for i, (s, e) in enumerate(segs):
        fp.append(f'[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}];')
        fp.append(f'[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}];')
    cv = ''.join(f'[v{i}]' for i in range(n))
    ca = ''.join(f'[a{i}]' for i in range(n))
    fp.append(f'{cv}{ca}concat=n={n}:v=1:a=1[outv][outa]')
    cmd = ['ffmpeg', '-i', input_file, '-filter_complex', '\n'.join(fp),
           '-map', '[outv]', '-map', '[outa]', '-c:v', 'libx264',
           '-preset', 'fast', '-crf', '23', '-c:a', 'aac', output_file]
    subprocess.run(cmd)
```

**Punch-In Cut (Emphasis Zoom):**
```bash
# Create 15% punch-in version
ffmpeg -i input.mp4 -vf "scale=iw*1.15:ih*1.15,crop=iw/1.15:ih/1.15" punched.mp4

# Cut at frame 3.4s between normal and punched
ffmpeg -i normal.mp4 -i punched.mp4 -filter_complex \
  "[0:v]trim=0:3.4,setpts=PTS-STARTPTS[a];[1:v]trim=0:3.6,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[out]" \
  -map "[out]" -c:v libx264 punchcut.mp4
```

### 3B. Beat-Synced Editing

**Core Pipeline (librosa → ffmpeg xfade):**
```python
import librosa
import numpy as np
import subprocess

def get_beat_times(audio_path, beats_per_cut=2):
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    # Every N beats = one cut point
    cut_times = beat_times[::beats_per_cut].tolist()
    return cut_times, float(tempo)

def build_beat_sync_video(music_path, clips, output_path, xfade_dur=0.08):
    """Cut clips to beat timestamps with xfade chain."""
    cut_times, bpm = get_beat_times(music_path, beats_per_cut=2)
    print(f'BPM: {bpm:.1f}, {len(cut_times)} cut points')

    # Trim each clip to its beat interval
    trimmed = []
    for i, (start, end) in enumerate(zip(cut_times, cut_times[1:])):
        dur = end - start
        clip = clips[i % len(clips)]
        out = f'_beat_seg_{i}.mp4'
        subprocess.run(['ffmpeg', '-y', '-i', clip, '-ss', '0', '-t', str(dur),
                        '-c:v', 'libx264', '-an', out], check=True, capture_output=True)
        trimmed.append((out, dur))

    # Build xfade filter chain
    inputs = []
    for path, _ in trimmed:
        inputs += ['-i', path]

    n = len(trimmed)
    fg, offset, last_v = [], 0.0, '[0:v]'
    for i in range(1, n):
        offset += trimmed[i-1][1] - xfade_dur
        new_v = f'[xf{i}]' if i < n - 1 else '[outv]'
        fg.append(f'{last_v}[{i}:v]xfade=transition=fade:'
                  f'duration={xfade_dur}:offset={offset:.4f}{new_v}')
        last_v = f'[xf{i}]'

    cmd = (['ffmpeg', '-y'] + inputs +
           ['-filter_complex', ';'.join(fg),
            '-map', '[outv]',
            '-i', music_path,
            '-map', f'{n}:a',
            '-shortest', '-c:v', 'libx264', '-crf', '18', output_path])
    subprocess.run(cmd, check=True)

# Onset detection (more granular — snare/hi-hat hits)
def get_onset_times(audio_path):
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    return onsets.tolist()
```

**madmom downbeat detection (for scene changes):**
```python
from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor
from madmom.features.downbeats import RNNDownBeatProcessor, DBNDownBeatTrackingProcessor
import numpy as np

# Downbeats = bar starts (beat position 1) — use for major scene changes
rnn = RNNBeatProcessor()
tracker = BeatTrackingProcessor(fps=100)
beats = tracker(rnn('song.wav'))

db_proc = RNNDownBeatProcessor()
db_tracker = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)
db_raw = db_tracker(db_proc('song.wav'))  # Nx2: [timestamp, beat_in_bar]
downbeats = db_raw[db_raw[:, 1] == 1, 0]

print(f'Downbeats (scene changes): {downbeats[:5]}')
print(f'All beats (B-roll cuts): {beats[:10]}')
```

### 3C. Animated / Viral Captions

**Fastest path — captacity (replaces SubtitleService):**
```python
import captacity

captacity.add_captions(
    video_file='input_short.mp4',
    output_file='output_captioned.mp4',
    font='C:/Windows/Fonts/arialbd.ttf',  # or Montserrat ExtraBold
    font_size=130,
    font_color='white',
    stroke_width=4,
    stroke_color='black',
    shadow_strength=1.0,
    shadow_blur=0.1,
    highlight_current_word=True,
    word_highlight_color='yellow',  # Hormozi style
    line_count=1,
    padding=50,
)
```

**Production quality — WhisperX + ASS \\kf karaoke:**
```python
import whisperx
import subprocess

def transcribe_with_word_times(video_path, device='cuda', language='ru'):
    audio = whisperx.load_audio(video_path)
    model = whisperx.load_model('large-v3', device, compute_type='float16')
    result = model.transcribe(audio, batch_size=16, language=language)
    align_model, meta = whisperx.load_align_model(
        language_code=result['language'], device=device)
    result = whisperx.align(result['segments'], align_model, meta, audio, device)
    return result['segments']

def build_ass_karaoke(segments, resolution=(1080, 1920)):
    W, H = resolution
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Viral,Montserrat-ExtraBold,90,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def ts(t):
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        cs = int((s % 1) * 100)
        return f'{int(h)}:{int(m):02d}:{int(s):02d}.{cs:02d}'

    events = []
    for seg in segments:
        words = seg.get('words', [])
        for i in range(0, len(words), 4):  # 4 words per line
            chunk = words[i:i+4]
            if not chunk:
                continue
            t_start = chunk[0].get('start', seg['start'])
            t_end = chunk[-1].get('end', seg['end'])
            text = ' '.join(
                f'{{\\kf{int((w.get("end",t_end) - w.get("start",t_start)) * 100)}}}'
                f'{w["word"].strip().upper()}'
                for w in chunk
            )
            events.append(f'Dialogue: 0,{ts(t_start)},{ts(t_end)},Viral,,0,0,0,,{text}')

    return header + '\n'.join(events)

def burn_captions(input_video, ass_file, output_video):
    subprocess.run([
        'ffmpeg', '-i', input_video,
        '-vf', f'ass={ass_file}',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
        '-c:a', 'copy', output_video, '-y'
    ], check=True)

# Integration with existing ElevenLabs TTS timestamps:
def elevenlabs_alignment_to_words(alignment):
    """Convert ElevenLabs character alignment to word timing."""
    words_timed = []
    current_word, word_start = '', None
    chars = alignment['characters']
    starts = alignment['character_start_times_seconds']
    ends = alignment['character_end_times_seconds']
    for ch, st, en in zip(chars, starts, ends):
        if ch == ' ':
            if current_word:
                words_timed.append({'word': current_word, 'start': word_start, 'end': en})
                current_word, word_start = '', None
        else:
            if not current_word:
                word_start = st
            current_word += ch
    if current_word:
        words_timed.append({'word': current_word, 'start': word_start, 'end': ends[-1]})
    return words_timed
```

**ASS karaoke format reference:**
```
# {\\kf43} = fill-sweep 430ms (centiseconds)
# {\\k43}  = instant color flip 430ms
# PrimaryColour = highlight color (yellow = &H0000FFFF)
# SecondaryColour = base text color (white = &H00FFFFFF)
# Show 4 words per Dialogue line, 50ms gap between chunks
# ffmpeg burn: ffmpeg -i video.mp4 -vf ass=captions.ass -c:v libx264 -crf 18 out.mp4
```

### 3D. Transitions (GL + ffmpeg)

**ffmpeg xfade — all 44 transition names:**
```bash
# FADES: fade, fadeblack, fadewhite, fadegrays
# DISSOLVES: dissolve, distance
# WIPES: wipeleft, wiperight, wipeup, wipedown
# SLIDES: slideleft, slideright, slideup, slidedown
# COVERS: coverleft, coverright, coverup, coverdown
# REVEALS: revealleft, revealright, revealup, revealdown
# SMOOTHS: smoothleft, smoothright, smoothup, smoothdown
# CIRCLES: circleopen, circleclose, circlecrop
# DIAGONALS: diagtl, diagtr, diagbl, diagbr
# HORIZONTAL: hlslice, hrslice, hlwind, hrwind
# VERTICAL: vuslice, vdslice, vuwind, vdwind
# EFFECTS: hblur, radial, pixelize, zoomin
# SQUEEZE: horzopen, horzclose, vertopen, vertclose
# CUSTOM: custom (use expr= parameter)
```

**Python xfade chain builder for N clips:**
```python
import subprocess

def get_duration(filepath):
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
        capture_output=True, text=True)
    return float(r.stdout.strip())

def build_xfade_chain(clips, output, transition='dissolve', xfade_dur=0.25,
                      music_track=None):
    """Build ffmpeg xfade filter chain for N clips."""
    durations = [get_duration(c) for c in clips]
    inputs = []
    for c in clips:
        inputs += ['-i', c]

    n = len(clips)
    # Normalize all clips to same fps/sar
    norm = ''.join(f'[{i}:v]settb=AVTB,setsar=1,fps=30[{i}v];' for i in range(n))
    fg_v, fg_a = [], []
    last_v, last_a = '0v', '0:a'
    cumulative = 0.0

    for i in range(1, n):
        cumulative += durations[i-1] - xfade_dur
        out_v = f'xv{i}' if i < n - 1 else 'outv'
        out_a = f'xa{i}' if i < n - 1 else 'outa'
        fg_v.append(f'[{last_v}][{i}v]xfade=transition={transition}:'
                    f'duration={xfade_dur}:offset={cumulative:.4f}[{out_v}]')
        fg_a.append(f'[{last_a}][{i}:a]acrossfade=d={xfade_dur}[{out_a}]')
        last_v, last_a = out_v, out_a

    fc = norm + ';'.join(fg_v) + ';' + ';'.join(fg_a)
    cmd = (['ffmpeg', '-y'] + inputs +
           ['-filter_complex', fc, '-map', f'[{last_v}]', '-map', f'[{last_a}]'])
    if music_track:
        cmd += ['-i', music_track, '-map', f'{n}:a']
    cmd += ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium', output]
    subprocess.run(cmd, check=True)
```

**GL transitions via ffmpeg-concat (Node, no recompile):**
```python
import subprocess

def gl_concat(clips, output, transition='crosszoom', duration_ms=600):
    """
    Transitions: fade, circleopen, directionalwarp, crosswarp, crosszoom,
    dreamy, squareswire, angular, radial, cube, swap, GridFlip, GlitchDisplace,
    ZoomInCircles, Ripple, directionalwipe
    """
    cmd = (['ffmpeg-concat', '-t', transition, '-d', str(duration_ms),
             '-o', output] + clips)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'ffmpeg-concat failed: {result.stderr}')
    return output

# Install once: npm install -g ffmpeg-concat
```

**Glitch transition:**
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "
  [0]split=3[r0][g0][b0];
  [r0]lutrgb=g=0:b=0[red];
  [g0]lutrgb=r=0:b=0[green];
  [b0]lutrgb=r=0:g=0[blue];
  [red][green]blend=all_mode=addition[rg];
  [rg][blue]blend=all_mode=addition[rgb];
  [rgb][1]xfade=transition=pixelize:duration=0.4:offset=4[out]
" -map [out] glitch_cut.mp4

# Chromatic aberration overlay
ffmpeg -i input.mp4 -vf "rgbashift=rh=-8:gh=8:bv=-4,noise=c0s=30:c0f=t+u" glitch.mp4
```

**Flash/white cut:**
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
  "xfade=transition=fadewhite:duration=0.15:offset=4" flash_cut.mp4
```

**Whip-pan simulation:**
```bash
# Apply increasing horizontal blur to last 0.5s of outgoing clip
ffmpeg -i a.mp4 \
  -vf "vboxblur=luma_radius='if(gte(t,3.5),min((t-3.5)*60,40),0)':luma_power=1" \
  -t 4.0 -y a_blur.mp4
# Then xfade a_blur.mp4 + b.mp4 with wipeleft:duration=0.2
```

### 3E. Motion Graphics + Social-UI Overlays

**Instagram story chrome (Remotion React component):**
```tsx
// InstagramChrome.tsx
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export const InstagramChrome: React.FC<{username: string}> = ({username}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, fps*0.3], [0, 1], {extrapolateRight: 'clamp'});
  const progress = (frame / (fps * 15)) * 100;  // 15s story

  return (
    <AbsoluteFill style={{opacity}}>
      {/* Story progress bar */}
      <div style={{position:'absolute',top:12,left:8,right:8,
                   height:2,background:'rgba(255,255,255,0.4)',borderRadius:2}}>
        <div style={{height:'100%',width:`${progress}%`,
                     background:'white',borderRadius:2}} />
      </div>
      {/* Username header */}
      <div style={{position:'absolute',top:24,left:12,display:'flex',
                   alignItems:'center',gap:8,color:'white',fontWeight:700}}>
        <div style={{width:32,height:32,borderRadius:'50%',
                     border:'2px solid white',background:'#8B5CF6'}} />
        <span style={{fontSize:14}}>{username}</span>
        <span style={{fontSize:12,opacity:0.7}}>2h</span>
      </div>
    </AbsoluteFill>
  );
};
```

```bash
# Render transparent WebM overlay
npx remotion render InstagramChrome overlay.webm \
  --props='{"username":"@yourchannel"}' --transparent

# Composite over b-roll
ffmpeg -i broll.mp4 -i overlay.webm \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto[outv]" \
  -map "[outv]" -map 0:a -c:a copy composite.mp4
```

**Telegram forward badge (pure ffmpeg drawtext):**
```bash
ffmpeg -i broll.mp4 -vf \
  "drawbox=x=20:y=ih-180:w=iw-40:h=140:color=0x212121CC:t=fill,
   drawbox=x=20:y=ih-180:w=iw-40:h=3:color=0x5288C1FF:t=fill,
   drawtext=fontfile='C\\:/Windows/Fonts/segoeui.ttf':
     text='Your Name':x=40:y=ih-160:fontsize=22:fontcolor=0x5288C1FF:
     enable='between(t,1,6)',
   drawtext=fontfile='C\\:/Windows/Fonts/segoeui.ttf':
     text='Смотрите новый выпуск!':x=40:y=ih-128:fontsize=26:fontcolor=white:
     enable='between(t,1,6)',
   drawtext=fontfile='C\\:/Windows/Fonts/segoeui.ttf':
     text='14\\:32':x=iw-80:y=ih-110:fontsize=18:fontcolor=0x888888FF:
     enable='between(t,1,6)'" \
  -c:v libx264 -crf 18 tg_overlay.mp4
```

**Python motion graphics via movis:**
```python
import movis as mv
import numpy as np

# Animated lower-third name card
scene = mv.layer.Composition(size=(1920, 1080), duration=8.0)

# Background bar (slides in from left)
bar = scene.add_layer(mv.layer.Rectangle(size=(600, 80), color='#1a1a1a'))
bar.transform.position.enable_motion().extend(
    times=[0.0, 0.5, 1.0],
    values=[(-600, -80), (0, -80), (0, -80)],  # slide in from left
    easings=['ease_out', 'linear']
)

# Name text
name_text = scene.add_layer(mv.layer.Text('Your Name', font_size=42, color='white'))
name_text.transform.position.set_value((0, -80))
name_text.opacity.enable_motion().extend([0.4, 0.9], [0.0, 1.0])

scene.write_video('lower_third.mp4')
```

**Animated progress/like counter (ffmpeg):**
```bash
# Like counter counting up 0→15000 over t=1..4
ffmpeg -i input.mp4 -vf \
  "drawtext=fontfile='C\\:/Windows/Fonts/arialbd.ttf':
   text='%{eif\\:min(15000*(t-1)/3,15000)\\:d}':
   x=(w-tw)/2:y=h/2:fontsize=72:fontcolor=white:
   enable='between(t,1,5)'" \
  -c:v libx264 -crf 18 counter.mp4

# Animated growing progress bar
ffmpeg -i input.mp4 -vf \
  "drawbox=x=0:y=ih-8:
   w='if(gt(t,2),(t-2)/(8-2)*iw,0)':h=8:
   color=0xFF4444FF:t=fill:enable='between(t,2,8)'" \
  -c:v libx264 -crf 18 progress.mp4
```

**Manim kinetic title card:**
```python
# manim_title.py
from manim import *

class TitleCard(Scene):
    def construct(self):
        title = Text('Результат', font_size=72, color=WHITE)
        subtitle = Text('за 30 дней', font_size=36, color=YELLOW)
        subtitle.next_to(title, DOWN)
        self.play(Write(title), run_time=0.8)
        self.play(FadeIn(subtitle, shift=UP*0.3), run_time=0.5)
        self.wait(2)
        self.play(FadeOut(VGroup(title, subtitle)), run_time=0.4)
```

```bash
# Render transparent background at 1080p
manim -qh --transparent manim_title.py TitleCard -o title.mov

# Composite onto video
ffmpeg -i main.mp4 -i title.mov \
  -filter_complex "[0:v][1:v]overlay=0:0:enable='between(t,0,4)'[out]" \
  -map "[out]" -map 0:a -c:a copy titled.mp4
```

### 3F. Color Grading / LUTs

**Apply .cube LUT (core recipe):**
```bash
# Direct .cube application — Kodak 2383 D55 (Hollywood print film)
ffmpeg -i input.mp4 \
  -vf "lut3d=file='Kodak2383_D55.cube':interp=tetrahedral" \
  -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a copy \
  graded.mp4

# LUT at 70% strength (blend with original)
ffmpeg -i input.mp4 -filter_complex \
  "[0:v]split[a][b];[a]lut3d=file='Kodak2383.cube'[lut];[b][lut]blend=all_expr='A*0.3+B*0.7'" \
  -c:v libx264 -crf 18 -c:a copy graded_partial.mp4

# Full film pipeline (LUT + lifted blacks + vignette + grain)
ffmpeg -i input.mp4 \
  -vf "lut3d=file='Kodak2383.cube':interp=tetrahedral,
       curves=all='0/0.10 0.5/0.52 1/0.97',
       colorbalance=rs=0.05:bs=-0.10:rh=0.08:bh=-0.12,
       vignette=angle=PI/5,
       noise=c0s=20:c0f=t+u" \
  -c:v libx264 -crf 16 -preset slow -tune grain -pix_fmt yuv420p -c:a copy \
  film_look.mp4
```

**Hald CLUT workflow (edit in any photo editor):**
```bash
# Generate identity Hald CLUT + reference frame side-by-side
ffmpeg -f lavfi -i haldclutsrc=8 -i input.mp4 -ss 00:00:04 -frames:v 1 \
  -filter_complex "[1]scale=-1:512[b];[0][b]hstack" hald_edit.png

# Edit hald_edit.png in Lightroom/GIMP/Photoshop
# Save as hald_graded.png, then apply to video:
ffmpeg -i input.mp4 -i hald_graded.png \
  -filter_complex haldclut \
  -pix_fmt yuv420p -c:v libx264 -preset slow -crf 18 -c:a copy \
  graded.mp4
```

**Teal-orange cinematic grade (no LUT file):**
```bash
ffmpeg -i input.mp4 -vf \
  "colorbalance=rs=0.05:gs=-0.05:bs=-0.15:rm=0.03:gm=-0.03:bm=-0.08:rh=0.12:gh=-0.05:bh=-0.18,
   curves=all='0/0 0.25/0.20 0.5/0.50 0.75/0.82 1/1'" \
  -c:v libx264 -crf 18 -c:a copy teal_orange.mp4
```

**Film grain:**
```bash
ffmpeg -i input.mp4 \
  -vf "noise=c0s=25:c0f=t+u" \
  -c:v libx264 -crf 18 -tune grain -c:a copy grainy.mp4
```

**Chromatic aberration (lens fringing):**
```bash
ffmpeg -i input.mp4 -vf "rgbashift=rh=-4:gh=4" \
  -pix_fmt yuv420p -c:v libx264 -crf 18 -c:a copy aberration.mp4
```

**Python color match between shots:**
```python
import cv2
from skimage import exposure

def color_match_frame(source_path, reference_path, output_path):
    ref = cv2.cvtColor(cv2.imread(reference_path), cv2.COLOR_BGR2RGB)
    src = cv2.cvtColor(cv2.imread(source_path), cv2.COLOR_BGR2RGB)
    matched = exposure.match_histograms(src, ref, channel_axis=-1)
    cv2.imwrite(output_path, cv2.cvtColor(matched.astype('uint8'), cv2.COLOR_RGB2BGR))
```

### 3G. Auto-Reframe 16:9→9:16

**Fastest path — static center crop:**
```bash
ffmpeg -i input_16x9.mp4 \
  -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920" \
  -c:v libx264 -crf 18 -c:a copy output_9x16.mp4
```

**Autocrop-vertical (subject-aware, recommended):**
```bash
pip install ultralytics opencv-python scenedetect
git clone https://github.com/kamilstanuch/Autocrop-vertical
cd Autocrop-vertical && pip install -r requirements.txt
python main.py -i landscape.mp4 -o vertical.mp4 --ratio 9:16 --quality balanced
```

**pyautoflip (saliency-based, non-face content):**
```bash
pip install pyautoflip
pyautoflip reframe -i input.mp4 -o output_9x16.mp4 --method saliency --aspect-ratio 9:16
```

**Manual YOLOv8 face-tracked crop:**
```python
from ultralytics import YOLO
import cv2, subprocess, numpy as np

def face_tracked_crop(input_path, output_path, target_ratio=(9, 16)):
    model = YOLO('yolov8n.pt')
    cap = cv2.VideoCapture(input_path)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    crop_w = int(H * target_ratio[0] / target_ratio[1])

    centers = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, classes=[0], verbose=False)
        if results[0].boxes:
            box = results[0].boxes[0].xyxy[0].cpu().numpy()
            cx = int((box[0] + box[2]) / 2)
        else:
            cx = W // 2
        centers.append(cx)
    cap.release()

    # Smooth with rolling mean (30-frame window)
    smoothed = np.convolve(centers, np.ones(30)/30, mode='same')
    smoothed = np.clip(smoothed, crop_w//2, W - crop_w//2).astype(int)

    # Write frame-level crop commands via ffmpeg sendcmd
    with open('crop_cmd.txt', 'w') as f:
        prev_x = -1
        for i, cx in enumerate(smoothed):
            x = cx - crop_w // 2
            if x != prev_x:
                f.write(f'{i/fps:.4f} crop x {x};\n')
                prev_x = x

    subprocess.run([
        'ffmpeg', '-i', input_path,
        '-vf', f'sendcmd=f=crop_cmd.txt,crop={crop_w}:{H}',
        '-c:v', 'libx264', '-crf', '18', '-c:a', 'copy',
        output_path, '-y'
    ], check=True)
```

### 3H. Sound Design

**Sidechain ducking (music under VO/SFX):**
```bash
ffmpeg -i music.mp3 -i voiceover.mp3 -filter_complex "
  [1:a]asplit=2[sc][vo];
  [0:a][sc]sidechaincompress=threshold=0.02:ratio=8:attack=50:release=500:makeup=1[ducked];
  [ducked][vo]amix=inputs=2:normalize=0[outa]
" -map "[outa]" -c:a aac -b:a 192k ducked.mp3
```

**Auto-download SFX from Freesound API:**
```python
import freesound, subprocess, os

def download_sfx_pack(api_key, sfx_types, output_dir='sfx'):
    """Download whoosh, impact, riser SFX by tag."""
    client = freesound.FreesoundClient()
    client.set_token(api_key, 'token')
    os.makedirs(output_dir, exist_ok=True)

    for sfx_type, tag in sfx_types.items():
        results = client.text_search(
            query=sfx_type,
            filter=f'tag:{tag} duration:[0.2 TO 3.0]',
            sort='rating_desc',
            fields='id,name,previews',
            page_size=5
        )
        for snd in results:
            out = os.path.join(output_dir, f'{sfx_type}_{snd.id}.mp3')
            subprocess.run(['curl', '-L', '-o', out,
                           snd.previews.preview_lq_mp3], check=True)

# sfx_types = {'whoosh': 'transition', 'impact': 'hit', 'riser': 'riser'}

def mix_sfx_at_timestamp(video, sfx_file, timestamp_sec, output):
    """Mix SFX onto video at a specific timestamp."""
    delay_ms = int(timestamp_sec * 1000)
    subprocess.run([
        'ffmpeg', '-i', video, '-i', sfx_file,
        '-filter_complex',
        f'[1:a]adelay={delay_ms}|{delay_ms}[sfx];[0:a][sfx]amix=inputs=2:normalize=0[outa]',
        '-map', '0:v', '-map', '[outa]',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output, '-y'
    ], check=True)
```

**Audio spectrum visualization overlay:**
```bash
ffmpeg -i video.mp4 -filter_complex "
  [0:a]showfreqs=s=1080x200:mode=bar:ascale=log:fscale=log:
     colors=0x00FF88,format=yuva420p,
     colorchannelmixer=aa=0.7[viz];
  [0:v][viz]overlay=0:H-200:format=auto[outv]
" -map "[outv]" -map 0:a -c:a copy spectrum_overlay.mp4
```

### 3I. Speed Ramps

**Reusable speed ramp builder:**
```python
def build_speed_ramp(input_file, output_file, ramp_segments):
    """
    ramp_segments: list of (start_sec, end_sec, speed_factor)
    speed_factor: 0.25 = 4x slo-mo, 1.0 = normal, 2.0 = 2x fast
    """
    import subprocess
    fc_v, fc_a = [], []
    concat_v, concat_a = '', ''

    for i, (start, end, speed) in enumerate(ramp_segments):
        pts = 1.0 / speed
        # Audio tempo: chain if outside 0.5-2.0 range
        if 0.5 <= speed <= 2.0:
            atempo = f'atempo={speed:.4f}'
        elif speed > 2.0:
            atempo = f'atempo=2.0,atempo={speed/2:.4f}'
        else:
            atempo = f'atempo=0.5,atempo={speed*2:.4f}'

        fc_v.append(f'[0:v]trim={start}:{end},setpts={pts:.4f}*(PTS-STARTPTS)[v{i}];')
        fc_a.append(f'[0:a]atrim={start}:{end},asetpts=PTS-STARTPTS,{atempo}[a{i}];')
        concat_v += f'[v{i}]'
        concat_a += f'[a{i}]'

    n = len(ramp_segments)
    fc = ''.join(fc_v) + ''.join(fc_a)
    fc += f'{concat_v}{concat_a}concat=n={n}:v=1:a=1[outv][outa]'

    subprocess.run([
        'ffmpeg', '-i', input_file, '-filter_complex', fc,
        '-map', '[outv]', '-map', '[outa]',
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
        '-c:a', 'aac', '-b:a', '192k', output_file, '-y'
    ], check=True)

# Example: 4x slo-mo intro, normal middle, 2x fast outro
# build_speed_ramp('clip.mp4', 'ramped.mp4', [
#   (0, 3, 0.25),   # first 3s at 4x slow
#   (3, 12, 1.0),   # middle normal
#   (12, 18, 2.0),  # last 6s at 2x fast
# ])
```

**True slow-mo via frame interpolation:**
```bash
ffmpeg -i input.mp4 \
  -vf "minterpolate=fps=120:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,setpts=4.0*PTS" \
  -r 30 slowmo_4x.mp4
```

**Motion blur on fast segment:**
```bash
# tmix blends N consecutive frames = motion blur effect
ffmpeg -i fast_segment.mp4 -vf "tmix=frames=8:weights='1 1 1 1 1 1 1 1'" blurred.mp4
```

---

## 4. THE CRAFT — Codifiable Shortform Editing Rules

### Hook Architecture
- **3-second rule:** Complete promise OR pattern interrupt within 3 seconds. Under 12 spoken words.
- **Hook triggers (need 2+ of 4):** curiosity + pattern interrupt + self-relevance + emotion
- **Hook taxonomy:** Unexpected Confession ("I probably shouldn't share this…") / Wrong Method Challenge ("Stop doing X") / Before/After Setup / One-Minute Fix / Curiosity Loop ("Watch what happens when I…") / Stakes Hook ("This cost me $2,300") / Exclusivity ("No one talks about this")
- **Always pair spoken hook with visual interrupt** in the same 3s (bold caption, sudden cut, zoom punch)

### Pacing Rules
- New visual element or cut every **3–6 seconds** — no exceptions for talking heads
- Tension→Release cycle: fast cuts + rising audio → momentary pause + payoff → repeat
- Remove: filler words, pauses >0.3s, repeated explanations, any shot lasting >8s without interrupt
- Target: 70–100% completion rate for Shorts (<30% = pacing failure)

### Cut Mechanics
- **J-Cut:** Next scene audio starts BEFORE visual cut — creates anticipation, prevents swipe-away
- **L-Cut:** Current audio continues UNDER next visual — maintains emotional context
- **Match Cut:** Outgoing frame shape/motion mirrors incoming frame — signals editorial sophistication
- **Punch-In:** 10–15% digital zoom into same shot on hard cut — never more than 20%
- **Jump Cut:** Remove dead air; keep 0.1–0.2s margin around speech to avoid clipped consonants

### Beat-Sync Rules
- At 120 BPM: cuts every 0.5s. At 90 BPM: every 0.67s. Allow ±2 frames tolerance.
- Downbeats (bar start) = scene changes. Regular beats = B-roll cuts. Onsets = SFX placement.
- Hard cuts on downbeats = stability. Hard cuts on upbeats = tension.

### Open Loop Structure
```
[0-3s]   HOOK: state outcome/problem WITHOUT showing it
[4-15s]  VALUE: establish credibility ('I tried X before finding this')
[16-60s] BUILD: step-by-step with mini open loops ('here's where it gets wrong')
[50% mark] RE-ENGAGE: pattern interrupt + re-state promise
[Final 10s] PAYOFF: resolve main loop → immediately plant next-video hook
```

### Visual Design Rules
- Captions font: min 6% of frame height; high-contrast pill background; max 3–5 words visible
- Punch-in max: 20% zoom before pixelation
- Vignette: always subtle (angle=PI/5), never obvious
- Color grade: consistent LUT per series; apply as final filter step
- Speed ramp: always add motion blur (tmix=frames=8) on fast segments
- Transitions: 0.15–0.3s max for shortform; dissolve for less than 10% of cuts

---

## 5. CONCRETE UPGRADE PLAN

### Phase 1 — IMMEDIATE WINS (1–2 days, no new architecture)

**P1.1: auto-editor integration**

File: `~/.claude/skills/video-editor/references/silence-removal.md`
```markdown
# Silence/Jump-Cut Auto-Removal

## Tool: auto-editor (4.4k stars, Unlicense)
pip install auto-editor

## Core commands
# Basic silence cut with 0.2s padding
auto-editor input.mp4 --margin 0.2sec --edit audio:threshold=4% -o cut.mp4

# Fast-forward silence (vlogger style)
auto-editor input.mp4 --when-silent speed:8 -o speed.mp4

# Export to DaVinci Resolve (non-destructive)
auto-editor input.mp4 --export davinci-resolve -o resolve.xml

# Export to Premiere Pro
auto-editor input.mp4 --export premiere -o premiere.xml
```

**P1.2: Kodak 2383 LUT — download and wire in**

Action: Download `Rec709 Kodak 2383 D55.cube` from `https://github.com/imnz730/LUTs/raw/master/Film%20Looks/Rec709%20Kodak%202383%20D55.cube`

Save to: `~/.claude/skills/video-generation/luts/Kodak2383_D55.cube`

File: `~/.claude/skills/video-generation/references/color-grading.md`
```markdown
# Color Grading — LUT + ffmpeg Recipes

## LUTs available in skills/video-generation/luts/
- Kodak2383_D55.cube — Hollywood print film (default recommendation)
- Film-Luts/ — G'MIC collection (clone from YahiaAngelo/Film-Luts)

## Apply LUT (add as final video filter before loudnorm pass)
ffmpeg -i input.mp4 \
  -vf "lut3d=file='~/.claude/skills/video-generation/luts/Kodak2383_D55.cube':interp=tetrahedral" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy graded.mp4

## LUT at 70% strength
ffmpeg -i input.mp4 -filter_complex \
  "[0:v]split[a][b];[a]lut3d=file='lut.cube'[lut];[b][lut]blend=all_expr='A*0.3+B*0.7'" \
  -c:v libx264 -crf 18 -c:a copy graded_partial.mp4

## Full film pipeline (LUT + lifted blacks + teal-orange + vignette + grain)
# (see technique library 3F for full command)

## Hald CLUT workflow
# 1. Generate: ffmpeg -f lavfi -i haldclutsrc=8 identity.png
# 2. Edit identity.png in any photo editor
# 3. Apply: ffmpeg -i video.mp4 -i graded.png -filter_complex haldclut output.mp4
```

**P1.3: captacity — animated captions (replaces SubtitleService)**

```bash
pip install captacity
```

File: `~/.claude/skills/video-editor/scripts/add_captions.py`
```python
#!/usr/bin/env python3
"""Add animated word-highlight captions to a video.
Usage: python add_captions.py input.mp4 output.mp4 [--style hormozi|mrbeast|minimal]
"""
import sys
import captacity

def add_captions(input_file, output_file, style='hormozi'):
    styles = {
        'hormozi': {'font_color': 'white', 'word_highlight_color': '#FF6B35',
                    'font_size': 130, 'line_count': 1},
        'mrbeast': {'font_color': 'yellow', 'word_highlight_color': 'red',
                    'font_size': 140, 'line_count': 1},
        'minimal': {'font_color': 'white', 'word_highlight_color': '#00FFFF',
                    'font_size': 100, 'line_count': 2},
    }
    cfg = styles.get(style, styles['hormozi'])

    captacity.add_captions(
        video_file=input_file,
        output_file=output_file,
        font='C:/Windows/Fonts/arialbd.ttf',
        font_size=cfg['font_size'],
        font_color=cfg['font_color'],
        stroke_width=4,
        stroke_color='black',
        shadow_strength=1.0,
        shadow_blur=0.1,
        highlight_current_word=True,
        word_highlight_color=cfg['word_highlight_color'],
        line_count=cfg['line_count'],
        padding=50,
    )
    print(f'Captions added: {output_file}')

if __name__ == '__main__':
    style = sys.argv[3] if len(sys.argv) > 3 else 'hormozi'
    add_captions(sys.argv[1], sys.argv[2], style)
```

### Phase 2 — CORE PIPELINE UPGRADES (3–7 days)

**P2.1: Beat-sync pipeline script**

```bash
pip install librosa
```

File: `~/.claude/skills/video-editor/scripts/beat_sync_edit.py`
```python
#!/usr/bin/env python3
"""Beat-synced video montage from clips + music.
Usage: python beat_sync_edit.py music.mp3 clip1.mp4 clip2.mp4 ... -o output.mp4
       Options: --beats-per-cut 2 --transition fade --xfade-dur 0.08
"""
import librosa
import numpy as np
import subprocess
import argparse
import os
import tempfile

def get_beat_times(audio_path, beats_per_cut=2):
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    cut_times = beat_times[::beats_per_cut].tolist()
    return cut_times, float(tempo)

def get_duration(filepath):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def trim_clip(clip, duration, index, tmpdir):
    out = os.path.join(tmpdir, f'seg_{index:04d}.mp4')
    subprocess.run(['ffmpeg', '-y', '-i', clip, '-ss', '0', '-t', str(duration),
                    '-c:v', 'libx264', '-crf', '20', '-an', out],
                   check=True, capture_output=True)
    return out, duration

def build_xfade_chain(trimmed, output, transition, xfade_dur, music_track):
    n = len(trimmed)
    inputs = []
    for path, _ in trimmed:
        inputs += ['-i', path]

    norm = ''.join(f'[{i}:v]settb=AVTB,setsar=1,fps=30[{i}v];' for i in range(n))
    fg_v, cumulative, last_v = [], 0.0, '0v'
    for i in range(1, n):
        cumulative += trimmed[i-1][1] - xfade_dur
        out_v = f'xv{i}' if i < n - 1 else 'outv'
        fg_v.append(f'[{last_v}][{i}v]xfade=transition={transition}:'
                    f'duration={xfade_dur}:offset={cumulative:.4f}[{out_v}]')
        last_v = out_v

    fc = norm + ';'.join(fg_v)
    cmd = (['ffmpeg', '-y'] + inputs +
           ['-filter_complex', fc, '-map', '[outv]',
            '-i', music_track, '-map', f'{n}:a',
            '-shortest', '-c:v', 'libx264', '-crf', '18',
            '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', output])
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('music')
    parser.add_argument('clips', nargs='+')
    parser.add_argument('-o', '--output', default='beat_sync_output.mp4')
    parser.add_argument('--beats-per-cut', type=int, default=2)
    parser.add_argument('--transition', default='fade')
    parser.add_argument('--xfade-dur', type=float, default=0.08)
    args = parser.parse_args()

    cut_times, bpm = get_beat_times(args.music, args.beats_per_cut)
    print(f'BPM: {bpm:.1f} | Cut points: {len(cut_times)}')

    with tempfile.TemporaryDirectory() as tmpdir:
        trimmed = []
        for i, (start, end) in enumerate(zip(cut_times, cut_times[1:])):
            clip = args.clips[i % len(args.clips)]
            dur = end - start
            trimmed.append(trim_clip(clip, dur, i, tmpdir))
        build_xfade_chain(trimmed, args.output, args.transition,
                          args.xfade_dur, args.music)

    print(f'Output: {args.output}')

if __name__ == '__main__':
    main()
```

**P2.2: WhisperX + ASS karaoke (quality captions)**

File: `~/.claude/skills/video-editor/scripts/karaoke_captions.py`
```python
#!/usr/bin/env python3
"""Generate animated karaoke-style captions from video.
Usage: python karaoke_captions.py input.mp4 output.mp4 [--lang ru] [--words-per-line 4]
Requires: conda env with whisperx + CUDA 12.8 (or CPU fallback)
"""
import sys, subprocess, argparse

def transcribe(video_path, lang, device='cpu'):
    import whisperx
    audio = whisperx.load_audio(video_path)
    compute = 'float16' if device == 'cuda' else 'int8'
    model = whisperx.load_model('large-v3', device, compute_type=compute)
    result = model.transcribe(audio, batch_size=16, language=lang)
    align_model, meta = whisperx.load_align_model(
        language_code=result['language'], device=device)
    result = whisperx.align(result['segments'], align_model, meta, audio, device)
    return result['segments']

def segments_to_ass(segments, resolution=(1080, 1920), words_per_line=4):
    W, H = resolution
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Viral,Arial Rounded MT Bold,90,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def ts(t):
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        cs = int((s % 1) * 100)
        return f'{int(h)}:{int(m):02d}:{int(s):02d}.{cs:02d}'

    events = []
    for seg in segments:
        words = seg.get('words', [])
        for i in range(0, len(words), words_per_line):
            chunk = words[i:i+words_per_line]
            if not chunk:
                continue
            t_start = chunk[0].get('start', seg['start'])
            t_end = chunk[-1].get('end', seg['end'])
            text = ' '.join(
                '{\\kf' + str(int((w.get('end', t_end) - w.get('start', t_start)) * 100)) + '}'
                + w['word'].strip().upper()
                for w in chunk
            )
            events.append(f'Dialogue: 0,{ts(t_start)},{ts(t_end)},Viral,,0,0,0,,{text}')

    return header + '\n'.join(events)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--lang', default='ru')
    parser.add_argument('--words-per-line', type=int, default=4)
    parser.add_argument('--device', default='cpu', choices=['cpu', 'cuda'])
    args = parser.parse_args()

    print('Transcribing...')
    segments = transcribe(args.input, args.lang, args.device)

    ass_path = args.input.replace('.mp4', '_captions.ass')
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(segments_to_ass(segments, words_per_line=args.words_per_line))
    print(f'ASS written: {ass_path}')

    subprocess.run([
        'ffmpeg', '-i', args.input, '-vf', f'ass={ass_path}',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
        '-c:a', 'copy', args.output, '-y'
    ], check=True)
    print(f'Output: {args.output}')

if __name__ == '__main__':
    main()
```

**P2.3: Auto-reframe script**

File: `~/.claude/skills/video-editor/scripts/reframe_9x16.py`
```python
#!/usr/bin/env python3
"""Auto-reframe 16:9 video to 9:16 for Shorts/Reels.
Usage: python reframe_9x16.py input.mp4 output.mp4 [--method center|yolo|saliency]
"""
import subprocess, sys, argparse

def center_crop(input_file, output_file):
    subprocess.run([
        'ffmpeg', '-i', input_file,
        '-vf', 'crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920',
        '-c:v', 'libx264', '-crf', '18', '-c:a', 'copy', output_file, '-y'
    ], check=True)

def yolo_crop(input_file, output_file):
    """Requires: pip install ultralytics opencv-python + Autocrop-vertical clone"""
    import os
    repo = '${WORKSPACE}/tools/Autocrop-vertical'  # adjust path
    subprocess.run([
        'python', f'{repo}/main.py',
        '-i', input_file, '-o', output_file,
        '--ratio', '9:16', '--quality', 'balanced'
    ], check=True)

def saliency_crop(input_file, output_file):
    """Requires: pip install pyautoflip"""
    from pyautoflip import reframe_video
    reframe_video(input_file, output_file, aspect_ratio=(9, 16), method='saliency')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--method', default='center', choices=['center', 'yolo', 'saliency'])
    args = parser.parse_args()

    methods = {'center': center_crop, 'yolo': yolo_crop, 'saliency': saliency_crop}
    methods[args.method](args.input, args.output)
    print(f'Reframed ({args.method}): {args.output}')

if __name__ == '__main__':
    main()
```

**P2.4: Speed ramp script**

File: `~/.claude/skills/video-editor/scripts/speed_ramp.py`
- Contains `build_speed_ramp()` function from Section 3I above.

**P2.5: xfade chain builder reference**

File: `~/.claude/skills/video-editor/references/xfade-transitions.md`
```markdown
# ffmpeg xfade Transitions Reference

## All 44 built-in transitions
FADES: fade, fadeblack, fadewhite, fadegrays
DISSOLVES: dissolve, distance
WIPES: wipeleft, wiperight, wipeup, wipedown
SLIDES: slideleft, slideright, slideup, slidedown
COVERS: coverleft, coverright, coverup, coverdown
REVEALS: revealleft, revealright, revealup, revealdown
SMOOTHS: smoothleft, smoothright, smoothup, smoothdown
CIRCLES: circleopen, circleclose, circlecrop
DIAGONALS: diagtl, diagtr, diagbl, diagbr
HORIZONTAL: hlslice, hrslice, hlwind, hrwind
VERTICAL: vuslice, vdslice, vuwind, vdwind
EFFECTS: hblur, radial, pixelize, zoomin
SQUEEZE: horzopen, horzclose, vertopen, vertclose

## Recommended for shortform (pacing: 0.15-0.25s)
- wipeleft/wiperight: directional energy, strong for beat hits
- slideup/slidedown: vertical momentum for mobile feel
- pixelize: digital/tech/AI content
- hblur: motion-blur cut simulation
- circleopen: dramatic scene reveals
- zoomin: urgency and emphasis

## GL transitions (npm install -g ffmpeg-concat)
crosszoom, dreamy, directionalwarp, GlitchDisplace, Ripple,
circleopen, GridFlip, squareswire, angular, radial, cube

## Glitch cuts (ffmpeg only)
rgbashift=rh=-8:gh=8 + noise=c0s=30 + xfade=pixelize

## xfade chain builder: see scripts/beat_sync_edit.py
```

### Phase 3 — MOTION GRAPHICS + SOCIAL UI (1–2 weeks)

**P3.1: Remotion social-UI templates**

File: `~/.claude/skills/video-generation/references/remotion-overlays.md`

Contents: Remotion setup guide + InstagramChrome.tsx component from Section 3E + ffmpeg composite command + render instructions.

**P3.2: movis motion graphics integration**

```bash
pip install movis
```

File: `~/.claude/skills/video-generation/scripts/motion_graphics.py`

Contains: `lower_third()`, `progress_bar()`, `like_counter_animation()`, `animated_title_card()` functions using movis, each outputting MP4 for ffmpeg overlay.

**P3.3: Manim integration**

```bash
pip install manim
# Also: install MiKTeX from miktex.org for LaTeX support on Windows
```

File: `~/.claude/skills/video-generation/references/manim-patterns.md`

Contents: TitleCard scene, data bar chart animation, LLM self-correction loop recipe (from habr.com/ru/articles/993630).

### Phase 4 — SCENE INTELLIGENCE (ongoing)

**P4.1: PySceneDetect for b-roll segmentation**

```bash
pip install scenedetect[opencv]
```

File: `~/.claude/skills/video-editor/scripts/scene_detect.py`
```python
from scenedetect import detect, AdaptiveDetector, split_video_ffmpeg

def detect_scenes(video_path, threshold=3.0):
    scene_list = detect(video_path, AdaptiveDetector(adaptive_threshold=threshold))
    print(f'Found {len(scene_list)} scenes')
    return scene_list  # list of (start_timecode, end_timecode)

def split_into_scenes(video_path, output_dir='.'):
    scenes = detect_scenes(video_path)
    split_video_ffmpeg(video_path, scenes, output_dir=output_dir)
    return scenes
```

**P4.2: Sound design automation**

```bash
pip install freesound-python
# Apply for free API key at freesound.org/apiv2/apply
```

File: `~/.claude/skills/video-editor/references/sound-design.md`

Contents: SFX download workflow, Freesound API recipes, sidechain ducking command, beat-aligned SFX placement, audio visualization overlays.

### Summary: Files to Create/Modify

| File Path | Action | Phase |
|-----------|--------|-------|
| `skills/video-editor/references/silence-removal.md` | CREATE | P1 |
| `skills/video-generation/luts/Kodak2383_D55.cube` | DOWNLOAD | P1 |
| `skills/video-generation/references/color-grading.md` | CREATE | P1 |
| `skills/video-editor/scripts/add_captions.py` | CREATE | P1 |
| `skills/video-editor/scripts/beat_sync_edit.py` | CREATE | P2 |
| `skills/video-editor/scripts/karaoke_captions.py` | CREATE | P2 |
| `skills/video-editor/scripts/reframe_9x16.py` | CREATE | P2 |
| `skills/video-editor/scripts/speed_ramp.py` | CREATE | P2 |
| `skills/video-editor/references/xfade-transitions.md` | CREATE | P2 |
| `skills/video-generation/references/remotion-overlays.md` | CREATE | P3 |
| `skills/video-generation/scripts/motion_graphics.py` | CREATE | P3 |
| `skills/video-generation/references/manim-patterns.md` | CREATE | P3 |
| `skills/video-editor/scripts/scene_detect.py` | CREATE | P4 |
| `skills/video-editor/references/sound-design.md` | CREATE | P4 |
| `skills/video-generation/SKILL.md` | UPDATE — add montage section | P2 |
| `skills/video-editor/SKILL.md` | UPDATE — add all new scripts | P2 |
| `rules/routing.md` | UPDATE — add beat-sync/reframe/captions triggers | P2 |

### New Dependencies

```bash
# Phase 1
pip install auto-editor captacity

# Phase 2
pip install librosa madmom scenedetect[opencv] moviepy freesound-python

# Phase 2 - WhisperX (requires conda + CUDA 12.8 for GPU; CPU fallback works)
conda create -n whisperx python=3.10
conda activate whisperx
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install whisperx

# Phase 3 (Node)
npm install -g ffmpeg-concat
npx create-video@latest  # Remotion project

# Phase 3 (Python)
pip install movis manim

# Phase 4
pip install pyautoflip
pip install ultralytics  # for Autocrop-vertical
```

---

## 6. RISKS / GOTCHAS

### Licensing

| Tool | Risk | Mitigation |
|------|------|------------|
| Remotion | BUSL — free for personal/OSS, $50/mo for companies $1M–$10M ARR | Use for internal tools; check ARR threshold |
| madmom | BSD-3 (OK) but GPL-3 transitive deps possible | Audit before commercial distribution |
| pycaps | No license specified yet (alpha) | Contact author or treat as use-at-risk for commercial |
| Autocrop-vertical | License not specified | Use internally; check before distribution |
| freesound SFX | CC-licensed content — always check individual file's CC type | Only use CC0 or CC-BY for commercial; confirm per download |
| Film-Luts (.cube files) | License varies per LUT creator | Use Kodak 2383 from imnz730 (open) or generate with spectral_film_lut |
| gl-transitions shaders | MIT/mixed per file | Check individual .glsl before use |

### Windows-Specific Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| madmom install fails | Needs Cython + Visual C++ Build Tools | `conda install madmom` or install VS Build Tools first |
| aubio has no wheel for Python 3.12+ | Binary not built | Use Python 3.11 or install from conda |
| WhisperX GPU mode | Needs CUDA 12.8 exact | Use conda env with matching CUDA; CPU mode works without |
| manim install incomplete | Missing MiKTeX for LaTeX | Install MiKTeX from miktex.org; not required for basic text animations |
| ffmpeg-concat GL rendering | Needs headless GL | Works on Windows with standard Node.js install; no extra config |
| BeatNet / PyAudio | PyAudio Windows wheel broken for Python 3.11+ | `pip install pipwin && pipwin install pyaudio` or use librosa instead |
| pycaps | Uses Playwright internally | `playwright install chromium` required after pip install |
| auto-editor PATH | Needs ffmpeg in system PATH | Add ffmpeg to Windows PATH; test with `ffmpeg -version` |
| Autocrop-vertical NVENC | Hardware encoding flag | Add `--encoder hw` flag; falls back to software if GPU unavailable |

### Heavy Dependency Warnings

| Dependency chain | Disk size | Notes |
|------------------|-----------|-------|
| WhisperX + CUDA | ~8–12 GB | Model weights + CUDA toolkit; use CPU mode on light tasks |
| manim + MiKTeX | ~4 GB | MiKTeX install is large on Windows |
| Remotion | ~500 MB | Chromium download on first render |
| YOLOv8 (ultralytics) | ~100–400 MB | Model weights auto-download on first run |
| ComfyUI-Darkroom | Requires ComfyUI + ~2 GB | Skip unless you need the 161-stock library; use pre-baked .cube files instead |
| minterpolate (ffmpeg) | CPU-intensive | Very slow on long clips without GPU; use for key moments only |

### Integration Gotchas

- **auto-editor `--export premiere`** produces XML, not MP4 — do not pipe directly to further ffmpeg processing; re-import in Premiere or use direct MP4 output.
- **captacity** uses local Whisper by default (downloads model on first run ~1.5 GB). Pass `openai_api_key` to use API instead and avoid local model.
- **WhisperX word timestamps** can have `None` for start/end on some words (forced alignment fails on certain phonemes) — always use `.get('start', seg['start'])` fallback.
- **ffmpeg lut3d on Windows** — .cube file path must use forward slashes or escaped backslashes in filter string: `lut3d=file='C:/path/to/lut.cube'`.
- **xfade offset calculation** — offset = cumulative duration MINUS transition duration, not cumulative duration. Off-by-xfade-duration error produces black frames.
- **atempo range** — ffmpeg atempo only accepts 0.5–2.0. For 4x fast, chain: `atempo=2.0,atempo=2.0`. For 0.25x slow, chain: `atempo=0.5,atempo=0.5`.
- **ASS karaoke on Windows ffmpeg** — font path in ASS Style must use the Windows font name (e.g., `Arial Rounded MT Bold`), not file path. The font must be installed system-wide.
- **Autocrop-vertical v1.4.1** — requires `ffmpeg` in system PATH (not just Python path). Test with `ffmpeg -version` in CMD before running.
- **Remotion BUSL** — the commercial license requirement applies to rendering infrastructure, not to viewing the output. Internal tooling for a company with >$1M ARR still requires a paid license.
- **PySceneDetect AdaptiveDetector** — `adaptive_threshold` default of 3.0 works for most content; lower to 1.5 for documentary/interview, raise to 6.0 for action/sports to avoid false positives.