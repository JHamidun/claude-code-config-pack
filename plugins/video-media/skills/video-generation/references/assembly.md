# FFmpeg cookbook для AI-видео

## §1 — amix silent-truncation bug (CRITICAL)

`amix duration=longest` **на самом деле обрезает по shortest** input, несмотря на название. Lost minutes of debugging.

**Правильный recipe:**

```bash
ffmpeg -i vo.mp3 -i music.wav -filter_complex \
  "[0:a]apad[narr];[narr][1:a]amix=inputs=2:duration=first:dropout_transition=0,volume=1.2[out]" \
  -map "[out]" -t 57 mix.wav
```

Ключи:
- `apad` на shorter input — pad нулями до конца
- `duration=first` — теперь longest реально работает
- `-t 57` — explicit target length (страховка)

## §2 — concat anullsrc fix (CRITICAL)

concat-demuxer **тихо дропает ВСЁ аудио** если у любого клипа нет audio stream. Pre-pad silent аудио до concat:

```bash
ffmpeg -i silent_clip.mp4 \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -c:v copy -c:a aac -shortest patched.mp4
```

**Точные параметры важны:** `channel_layout=stereo`, `sample_rate=48000`, `-c:a aac` — иначе concat compatibility ломается.

## §3 — amix normalize=0 rule (CRITICAL)

Без `normalize=0` amix делит output на N inputs (6 voices = -6dB каждый, VO утоплен в музыке).

```bash
ffmpeg -i v1.mp3 -i v2.mp3 -i v3.mp3 -i music.wav -filter_complex \
  "[0:a]volume=3.0[a];[1:a]volume=3.0[b];[2:a]volume=3.0[c];[3:a]volume=1.0[m];\
   [a][b][c][m]amix=inputs=4:normalize=0[out]" \
  -map "[out]" mix.wav
```

`normalize=0` + manual `volume=X` per track = controlled mix.

## §4 — Sidechain compress ducking

Альтернатива volume scaling — duck music под VO automatically:

```bash
ffmpeg -i music.wav -i vo.mp3 -filter_complex \
  "[1:a]asplit=2[sc][v];\
   [0:a][sc]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=350:makeup=2[m];\
   [m][v]amix=inputs=2:normalize=0[out]" \
  -map "[out]" mix.wav
```

Параметры:
- `threshold=0.04` — точка срабатывания
- `ratio=8` (или `10` heavier)
- `attack=15` ms — быстро срабатывает
- `release=350-400` ms — sustained tones удерживают duck
- `makeup=2` — компенсация level loss

## §5 — Loudnorm broadcast standard

Для YouTube, IG, TikTok (platforms enforce -14 LUFS):

```bash
ffmpeg -i mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11" final.wav
```

Для 2-pass (точнее):

```bash
# Pass 1
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2> stats.json
# Pass 2 — измерения из stats.json
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=...:measured_TP=...:measured_LRA=...:measured_thresh=...:offset=... final.wav
```

## §6 — XFade chain (РОВНО 2 input per xfade)

xfade принимает строго 2 inputs. Для 3+ — цепочка:

```bash
ffmpeg -i clip_01.mp4 -i clip_02.mp4 -i clip_03.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.4:offset=4.6[v01];\
   [v01][2:v]xfade=transition=fade:duration=0.4:offset=9.2[vout]" \
  -map "[vout]" out.mp4
```

**`offset` = (предыдущая длительность видеоряда) - fade_duration.** Для clip_01=5s + fade 0.4s → offset=4.6 для перехода к clip_02. Затем 5+5-0.4-0.4=9.2 для clip_03.

Если ошибиться с offset — visible gap или overlap.

**Разные длительности клипов** — считай offset кумулятивно (НЕ `k*(D-F)`):

```python
cum, offsets = 0.0, []
for dur in durations[:-1]:          # все кроме последнего
    cum += dur
    offsets.append(round(cum - F, 3))   # F = fade duration
# total = sum(durations) - F*(n-1)
```

При одинаковых клипах формула вырождается в `offset_k = k*(D-F)` (см. `assemble.py` проекта [Client] — 12 клипов + титр, 13 xfade в цепочке).

## §7 — Concat -c copy (65× realtime)

Если все clips идентичны codec/resolution/fps:

```bash
# clips.txt
# file 'clip_01.mp4'
# file 'clip_02.mp4'
# file 'clip_03.mp4'

ffmpeg -f concat -safe 0 -i clips.txt -c copy out.mp4
```

Без re-encode → 65× realtime. Не работает если кодеки разные — тогда `-c:v libx264 -c:a aac`.

## §8 — Ken Burns zoompan

```bash
ffmpeg -loop 1 -i still.jpg \
  -vf "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1080x1920,fps=25" \
  -t 5 -c:v libx264 -pix_fmt yuv420p kenburns.mp4
```

Параметры:
- `z='min(zoom+0.0015,1.5)'` — slow zoom, max 1.5×
- `d=125` — frame count = duration × fps (5s × 25fps = 125)
- `s=1080x1920` — output resolution (vertical)
- `-t 5` — итоговая длительность

Для pan вместо zoom: `x='iw*(0.5-zoom)/4':y='ih*(0.5-zoom)/4'`.

## §9 — 3-tier compression strategy

| Tier | Use | Cmd |
|---|---|---|
| Archive | Master, 4K | `ffmpeg -i in.mp4 -c:v libx264 -preset slower -crf 18 archive.mp4` |
| Presentation | Client review, 2.5K | `ffmpeg -i in.mp4 -c:v libx264 -preset medium -crf 20 -vf scale=2560:-2 presentation.mp4` |
| Social | YouTube/IG/TikTok 1080p | `ffmpeg -i in.mp4 -c:v libx264 -preset medium -crf 22 -vf scale=1080:-2 -c:a aac -b:a 192k -movflags +faststart social.mp4` |

`-movflags +faststart` для social — moves moov atom to front для instant streaming.

## §10 — PIL textbbox centering formula

Для overlay через ffmpeg `-i video.mp4 -i text_overlay.png -filter_complex "[0:v][1:v]overlay=0:0"`.

Генерация text PNG с pixel-perfect centering:

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920  # canvas
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 64)  # ABSOLUTE path для Windows
text = 'Your Channel Name'

bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]

# КРИТИЧНО: компенсация bbox offset (у шрифта собственный padding)
x = (W - tw) // 2 - bbox[0]
y = (H - th) // 2 - bbox[1]

draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
img.save('overlay.png')
```

Без `- bbox[0]` / `- bbox[1]` текст смещён на font's own bbox offset (visible на короткой строке).

## §11 — Aspect ratio padding (vertical from horizontal)

```bash
# 16:9 → 9:16 с blurred sides
ffmpeg -i in_16x9.mp4 -filter_complex \
  "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,boxblur=20:1,crop=1080:1920[bg];\
   [0:v]scale=1080:-2[fg];\
   [bg][fg]overlay=(W-w)/2:(H-h)/2" \
  out_9x16.mp4
```

## §12 — Извлечение first frame

```bash
ffmpeg -i video.mp4 -vframes 1 -q:v 2 first_frame.jpg
```

Используй для Seedance end_frame=first_frame LOCK без re-render keyframe'а.

## §13 — Sanity check audio levels

```bash
ffmpeg -i mix.wav -af ebur128=peak=true -f null -
```

Ищи `Integrated loudness: I: -14 LUFS` (target). Если -23 — overcompressed quiet. Если -10 — overdriven.

## §14 — tpad voice-cover safety (CRITICAL для long-VO)

**Симптом.** Финальный mp4 обрывается раньше, чем закончилась озвучка. Картинка чёрная, а голос ещё что-то говорит.

**Причина.** N клипов Veo по 8s = 8N секунд видео. Если ElevenLabs voiceover длиннее (например, 32s видео vs 45s голоса), `ffmpeg -shortest` обрежет голос до длительности видеоряда. Без `-shortest` будет audio после видео (чёрный экран). Оба варианта плохие.

**Решение.** **Заморозить последний кадр** на разницу через `tpad=stop_mode=clone`. Видео тянется до конца голоса, аудио не обрывается, последний осмысленный кадр висит холдом.

### Recipe — voice + video (no music)

```bash
VOICE_DUR=$(ffprobe -v error -show_entries format=duration \
            -of default=noprint_wrappers=1:nokey=1 voice.mp3)
VIDEO_DUR=$(ffprobe -v error -show_entries format=duration \
            -of default=noprint_wrappers=1:nokey=1 video.mp4)
EXTRA=$(awk "BEGIN {print ($VOICE_DUR - $VIDEO_DUR) + 0.2}")

ffmpeg -y -i video.mp4 -i voice.mp3 \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=$EXTRA[v]" \
  -map "[v]" -map 1:a \
  -c:v libx264 -preset veryfast -crf 22 \
  -c:a aac \
  out.mp4
```

`stop_duration=$EXTRA` — на сколько секунд продолжать последний кадр. Если video уже **длиннее** голоса, `EXTRA` будет отрицательный — тогда фильтр пропусти (`vfilter = "null"`).

### Recipe — voice + music + tpad (production)

```bash
ffmpeg -y -i video.mp4 -i voice.mp3 -i music.mp3 \
  -filter_complex "
    [0:v]tpad=stop_mode=clone:stop_duration=$EXTRA[v];
    [2:a]aloop=loop=-1:size=2e9,volume=0.12[bg];
    [1:a][bg]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]
  " \
  -map "[v]" -map "[aout]" \
  -c:v libx264 -preset veryfast -crf 22 \
  -c:a aac \
  out.mp4
```

Ключи:
- `tpad` + `stop_mode=clone` → freeze-frame extension
- `aloop=loop=-1:size=2e9` → loop music если короче VO
- `amix duration=first` → длительность по VO (первый input), музыка следует
- `normalize=0` → не делить громкость пополам (см. §3)

### Python helper

```python
import subprocess

def audio_duration(path: str) -> float:
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', path],
        capture_output=True, text=True, timeout=30,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0

def overlay_voice_with_safety(video, voice, music, out, music_vol=0.12):
    vdur = audio_duration(video)
    adur = audio_duration(voice)
    if adur > vdur + 0.3:
        vfilter = f'tpad=stop_mode=clone:stop_duration={adur - vdur + 0.2}'
    else:
        vfilter = 'null'

    if music:
        fc = (f'[0:v]{vfilter}[v];'
              f'[2:a]aloop=loop=-1:size=2e9,volume={music_vol}[bg];'
              f'[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]')
        cmd = ['ffmpeg', '-y', '-i', video, '-i', voice, '-i', music,
               '-filter_complex', fc,
               '-map', '[v]', '-map', '[aout]',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
               '-c:a', 'aac', out]
    else:
        fc = f'[0:v]{vfilter}[v]'
        cmd = ['ffmpeg', '-y', '-i', video, '-i', voice,
               '-filter_complex', fc,
               '-map', '[v]', '-map', '1:a',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
               '-c:a', 'aac', out]
    subprocess.run(cmd, check=True, capture_output=True)
```

### Когда НЕ нужен tpad

- AI-видео pipeline где **сцены планируются под длину VO**: `scenes = ceil(voice_dur / 8)` (см. SKILL.md Phase 4 auto-scale). Тогда video всегда ≥ voice и `EXTRA` отрицателен.
- Talking-head (HeyGen, YourFirstName avatar): провайдер сам синхронизирует видео по длине TTS.

**Используй когда:** статичный план сцен + переменная длина TTS. Особенно после edit-pass где voiceover сделали длиннее.

## §15 — Per-line VO поверх музыки, статический баланс (cinematic tribute)

Альтернатива ducking'у (§3/§4): когда закадр — это **N отдельных реплик по сценам** поверх одного оркестрового трека, и pumping sidechain мешает интимной подаче. Каждую реплику кладём по таймкоду её сцены через `adelay`, музыку держим тихо и ровно. Это рецепт «клиентского трибьюта» (`assemble.py`), давший чистый mix:

```python
# scene_start[n] = когда стартует реплика n (привязка к началу сцены + 0.3с)
scene_start = {n: round((n - 1) * (D - F) + 0.3, 2) for n in range(1, N + 1)}
scene_start[N] = 53.0          # финальную строку — поверх титра, не по формуле

a_inputs = ["-i", "music_cut.mp3"] + sum([["-i", f"vo_{n:02d}.mp3"] for n in range(1, N+1)], [])
af = [f"[0:a]atrim=0:{total},afade=t=out:st={total-3}:d=3,volume=0.42[m]"]   # музыка тихо и ровно
mix = ["[m]"]
for n in range(1, N + 1):
    ms = int(scene_start[n] * 1000)
    af.append(f"[{n}:a]adelay={ms}|{ms},volume=2.8[v{n}a]")                   # VO громко, по таймкоду
    mix.append(f"[v{n}a]")
af.append("".join(mix) + f"amix=inputs={N+1}:duration=first:dropout_transition=0:normalize=0[mx]")
af.append("[mx]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
# ffmpeg -y *a_inputs -filter_complex ";".join(af) -map "[aout]" -t total final_audio.wav
```

Ключи: `adelay=ms|ms` (оба канала!), `normalize=0` (см. §3) + ручные `volume` (музыка ~0.42, VO ~2.8), один финальный `loudnorm I=-14`. Музыка `volume=0.42` фоном, голос всегда наверху — без дыхания компрессора.

## §16 — Title card с виньеткой (PIL, кириллица) + Ken Burns fallback на отсутствующий клип

**Титр-карточка** как 13-й «клип» в той же xfade-цепочке (а не overlay) — чище переход в финал. Фон с лёгкой виньеткой через построчный градиент:

```python
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (W, H), (8, 10, 14)); dr = ImageDraw.Draw(img)
for i in range(H):                                   # мягкое радиальное свечение
    a = int(18 * (1 - abs(i - H/2) / (H/2)))
    dr.line([(0, i), (W, i)], fill=(8 + a, 10 + a, 16 + a))
f1 = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(W * 0.045))   # абсолютный путь!
f2 = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   int(W * 0.024))
# центрирование с компенсацией bbox (см. §10), title fill (245,238,220), подпись (212,180,120) золотом
# затем: ffmpeg -loop 1 -i title.png -t D -vf "fps=24,format=yuv420p,fade=t=in:st=0:d=0.6" title.mp4
```

**Ken Burns fallback на отсутствующий/битый клип:** если для сцены N нет видео (генерация не дошла), не роняй сборку — оживи keyframe зумом, чтобы хронометраж не поехал:

```python
if os.path.exists(clip) and os.path.getsize(clip) > 10000:
    normalize(clip, dst)            # обрезать/скейлить под canonical W×H
else:
    kenburns(f"{KF}/sc{N:02d}.png", dst)   # zoompan из keyframe (см. §8)
```

Canonical size бери из первого реального клипа (`ffprobe stream=width,height`), форсь чётные `W -= W%2; H -= H%2` — иначе libx264 ругается.
