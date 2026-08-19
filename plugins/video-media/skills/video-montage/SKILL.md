---
name: video-montage
description: "Конвейер ролика ролями: бриф→сценарий→музыка→раскадровка→монтаж; reels 9:16. Триггеры: «собери рилс», «рилс с нуля». НЕ: футаж→video-editor; AI-сцены→video-generation."
---

# Video Montage — Full Production Pipeline

> **Windows-адаптация (стек пользователя):** `python` вместо `python3`; headless Chrome = `"C:/Program Files/Google/Chrome/Application/chrome.exe"` (те же флаги); временные файлы → scratchpad, не `/tmp`; ElevenLabs-ключ `ELEVENLABS_API_KEY` из `~/.claude/.credentials.master.env`, свой голос — см. навык `elevenlabs`; правило кодека то же: только `libx264 + yuv420p`. WhisperX уже стоит (см. `video-editor` karaoke_captions). Смежное: монтаж готового футажа → `video-editor`; AI-генерация сцен → `video-generation`; музыка → `ace-step`/`suno`; публикация в Telegram-канал → `tg-bot-publish` (через своего бота), в остальные соцсети — своим публикатором (например, Postiz self-hosted), готовой обёртки в паке нет.

Everything you need to produce vertical reels (9:16, 1080x1920, 30fps) with Claude Code — from raw footage to published content.

---

## 0. Конвейер целиком: одна задача — весь ролик

Когда просьба звучит как «сделай ролик про X», а не как отдельная операция монтажа, не
выбирай инструменты вручную — запускай конвейер. Он сам разберёт задачу на роли и
проведёт её от брифа до готового файла.

```
Workflow({
  scriptPath: '~/.claude/skills/video-montage/workflows/video-factory.js',
  args: { brief: 'как за день собрали лендинг вайбкодингом',
          seconds: 35, platform: 'reels', goal: 'watch',
          workdir: '~/Videos/video-factory/lending-35s' }
})
```

Обрыв не страшен: `Workflow({scriptPath, resumeFromRunId})` продолжит с места, а готовые
кадры помечены в конверте и второй раз не оплачиваются.

**Роли и порядок** (полностью — `references/pipeline-architecture.md`):

```
бриф ─┬─ сценарий ─┐
      └─ музыка ───┴─ раскадровка ─ кадры (волнами по 4) ─ монтаж ─ контроль
```

Сценарий и музыка идут одновременно; кадры независимы друг от друга и обрабатываются
волнами — больше шести агентов разом упирается в ограничение сервера. Барьеры стоят
только там, где они честно нужны: раскадровке нужны и структура, и сетка долей.

**Единый документ между ролями** — `schemas/production.schema.json`. Каждая роль пишет
свой раздел и не трогает чужие; это и делает параллельность возможной, и позволяет
перезапускать этапы поодиночке.

**Ремесленная часть** — в каталоге приёмов, 79 записей с источником и статусом
доказательности у каждой:

```bash
python scripts/techniques.py stats
python scripts/techniques.py find "не держится внимание"
python scripts/techniques.py for-block крючок
```

**Структура ролика** строится не по AIDA: та описывает убеждение покупателя (печатная
реклама, 1898) и оптимизирует намерение купить — величину, которую лента не измеряет.
Площадки официально называют главным сигналом досмотр, поэтому план строится вокруг
удержания:

```bash
python scripts/reel_structure.py --message "…" --seconds 35 --goal shares --music track.mp3
python scripts/reel_structure.py --why      # откуда взято каждое число
```

### Приёмка: посмотреть и послушать готовый файл

Последний шаг любого ролика — не «сборка прошла без ошибок», а собственный просмотр и
прослушивание. Сборка молчит о том, что видно и слышно с первой секунды: у персонажа
белый прямоугольник вместо фона, титры серые в момент появления, речь не совпадает с
картинкой, последние семь секунд немые. Всё это даёт нулевой код возврата.

```bash
python scripts/review_cut.py reel.mp4 -o review/ --listen
```

Выдаёт контактный лист (весь ролик одной сеткой — открыть и посмотреть), замеры звука
(громкость, пики, тишина) и разбор дорожки на слух. Три источника не заменяют друг
друга: замеры не слышат кашу в речи, слух не видит призрака в кадре, глаз не измеряет
перегруз. Возраст файла печатается первой строкой — если рендер упал, на диске лежит
прошлая сборка, и приёмка бодро отчитается по ней.

### Липсинк без сторонних платформ

Пока рот на рисунке неподвижен, персонаж читается как мёртвая картинка — это первое,
за что цепляется глаз. Рот открывается по громкости голоса; фонемы для рисованного
персонажа не нужны, так делают в рисованной анимации с начала звукового кино.

```bash
python scripts/mouth_map.py ./poses -o mouth.json --draw check/   # где рот на каждой позе
python scripts/voice_envelope.py voice.mp3 --fps 30 --duration 20 -o env.json
python scripts/cutout.py ./poses -o ./poses_cut                   # убрать фон
python scripts/cutout.py ./stickers -o ./stickers_cut --outline 14 # наклейка с каймой
```

Разметку рта обязательно смотреть глазами через `--draw`: модель отвечает уверенно и
в тех случаях, когда промахнулась.

### Озвучка, попадающая в титры

Монолитная озвучка расходится с картинкой: диктор говорит со своей скоростью, титры
идут со своей. Каждая фраза синтезируется отдельно и ставится в момент своего титра, а
хронометраж подгоняется под реальную речь.

```bash
python scripts/voice_timed.py script.json -o voice.mp3 --duration 20 --retime script_fit.json
```

`--retime` возвращает сценарий, ужатый под то, как реально звучит речь: без него
половина ролика — паузы, и на слух он затянут, хотя каждый кусок нормальный.

## Requirements

- **ffmpeg** (with libass, drawtext filters)
- **whisper** (OpenAI Whisper CLI)
- **Python 3** with Pillow (`pip install Pillow`)
- **ElevenLabs API key** (for TTS voiceover)
- **yt-dlp** (for downloading reference reels)

---

## 1. Subtitles

### 1.1 Extract audio

Always extract to 16kHz mono WAV before running Whisper:

```bash
ffmpeg -y -i video.MOV -ar 16000 -ac 1 -c:a pcm_s16le /tmp/subs/audio.wav
```

### 1.2 Whisper transcription

**Model selection:**

| Model | When to use | Speed |
|-------|-------------|-------|
| `small` | Quick QA checks, short clips | Fast |
| `medium` | Solo speech (one person talking to camera) | Medium |
| `large-v3` | Multi-speaker, AI assistant responses (Grok, ChatGPT TTS playback), quiet/distant audio | Slow (~10x vs medium) |

**Always use `--initial_prompt`** with domain-specific words to reduce hallucinations:

```bash
# Solo speech
whisper audio.wav --model medium --language ru --output_format srt --output_dir /tmp/subs/ \
  --initial_prompt "your domain words here, product names, slang terms"

# With AI assistant / multi-speaker
whisper audio.wav --model large-v3 --language ru --output_format srt --output_dir /tmp/subs/ \
  --initial_prompt "speaker names, AI names, product names, technical terms"
```

### 1.3 Error correction

**NEVER use raw Whisper output.** Always review every line manually.

Common Whisper error patterns:

| Pattern | Example |
|---------|---------|
| Brand names garbled | "код-код-экси" → "Claude Code, Codex" |
| Slang misheard | "позадрочишь" → "позадротишь" |
| Numbers as words mixed up | "сторилл соус" → "сто рилсов" |
| Spelling errors | "конкатинировать" → "конкатенировать" |
| TTS responses missing | Quiet AI voice not transcribed → re-run with `large-v3` |
| Word boundaries wrong | "вайп-код и шпродук" → "вайб-кодить продукт" |

**Protocol:** Save corrected SRT as `audio_corrected.srt` — this is the source of truth.

### 1.4 SRT → ASS conversion

Use the bundled script `scripts/gen_subs.py` to convert SRT to ASS with word chunking (3 words per subtitle segment for TikTok-style pacing):

```bash
# Impact style (default — bold TikTok/meme):
python3 scripts/gen_subs.py input.srt output.ass

# Helvetica style (clean talking-head):
python3 scripts/gen_subs.py input.srt output.ass --font helvetica

# With time offset (e.g. 5s intro):
python3 scripts/gen_subs.py input.srt output.ass --offset 5.0

# 2 words per chunk for slower pacing:
python3 scripts/gen_subs.py input.srt output.ass --max-words 2
```

**Font styles:**

| Style | Font | Size | Outline | Best for |
|-------|------|------|---------|----------|
| `impact` | Impact Bold | 90pt | 8px black | Meme/TikTok style, voiceover reels |
| `helvetica` | Helvetica Neue Bold | 80pt | 3px black | Talking head, conversations, clean look |

### 1.5 Bake subtitles into video

```bash
ffmpeg -y -i source_video.MOV \
  -vf "format=yuv420p,ass=subs.ass" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  output_with_subs.mp4
```

**Important:** Always use `libx264 + format=yuv420p`. Never use `hevc_videotoolbox` — files may not open in iCloud/QuickTime.

---

## 2. TTS Voiceover (ElevenLabs)

### 2.1 Core rule: never monolithic

Never generate a single TTS call for speech longer than 15 seconds. Always split into segments — this gives you control over pacing and prevents phrase-mushing.

### 2.2 Segment your script

Tag each phrase with a pause type:

```
[seg] First sentence of your script. [pause:short]
[seg] Second sentence, same topic. [pause:medium]
[seg] New topic begins here. [pause:long]
[seg] The big conclusion or CTA.
```

### 2.3 Pause presets

| Pause | Duration | When to use |
|-------|----------|-------------|
| short | 0.16s | Between regular phrases within same topic |
| medium | 0.34s | Between topics or sections |
| long | 0.55s | Before CTA, key numbers, dramatic conclusion |

Generate silence files:

```bash
ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 0.16 -q:a 9 silence_short.mp3
ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 0.34 -q:a 9 silence_medium.mp3
ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 0.55 -q:a 9 silence_long.mp3
```

### 2.4 Generate each segment

```bash
curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/YOUR_VOICE_ID" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your segment text here.",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
      "stability": 0.5,
      "similarity_boost": 0.75,
      "style": 0.0,
      "use_speaker_boost": true
    }
  }' --output segment_01.mp3
```

**Tuning tips:**
- Increase `style` to 0.2-0.4 for energetic/emotional delivery
- Increase `stability` to 0.6-0.7 for calm/measured narration
- Never exceed `style: 0.8` — distortion

### 2.5 Concatenate with pauses

Build a concat list:

```
file 'segment_01.mp3'
file 'silence_short.mp3'
file 'segment_02.mp3'
file 'silence_medium.mp3'
file 'segment_03.mp3'
```

Concat and adjust tempo:

```bash
ffmpeg -y -f concat -safe 0 -i concat.txt -c:a libmp3lame -q:a 2 vo_raw.mp3
ffmpeg -y -i vo_raw.mp3 -af "atempo=1.20" vo_final.mp3
```

**Tempo range:** 1.15-1.25x is natural. Never exceed 1.40x — causes distortion.

### 2.6 Anti-patterns

- Monolithic TTS for >15s speech — phrases will mush together
- Relying on punctuation alone for pacing — ElevenLabs ignores most pauses
- atempo > 1.40x — distorted robot voice
- Skipping silence files — natural speech has pauses

---

## 3. Video Assembly

### 3.1 Clip preparation

**CFR 30fps normalization (CRITICAL):**

Every clip must be constant frame rate before concatenation. VFR + CFR = freeze frames and duplicates.

```bash
ffmpeg -y -i clip.MOV \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -c:v libx264 -crf 18 -preset fast \
  -color_range 2 -colorspace bt709 -color_trc bt709 -color_primaries bt709 \
  -c:a aac -b:a 192k \
  clip_prepped.mp4
```

**iPhone vertical clips:** ffprobe may show 1920x1080 + rotation=-90. Always extract a frame to verify orientation before using.

```bash
ffmpeg -ss 1 -i clip.MOV -vframes 1 /tmp/check_orientation.jpg
```

### 3.2 Ken Burns effect

For static images or single-shot clips, add slow zoom to keep visuals interesting. Max 5-7 seconds per static shot.

```bash
ffmpeg -y -loop 1 -i photo.jpg -t 6 \
  -vf "scale=1120:1992,zoompan=z='min(zoom+0.0008,1.05)':d=180:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,fps=30" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p \
  ken_burns.mp4
```

### 3.3 Visual-narrative sync

When editing voiceover reels, match visuals to what the narrator is talking about:
- ~80% of clips should directly illustrate the current topic
- ~20% can be cutaway clips (gym, walking, typing) for visual variety between topics

**Workflow:**
1. Write a timeline: `0:00-0:15 topic A, 0:15-0:40 topic B, 0:40-1:00 CTA`
2. Assign clips to each slot based on topic
3. Alternate camera angles (handheld vs tripod) for variety

### 3.4 Concatenation

**Same codec (all prepped to libx264):**

```bash
# concat.txt:
file 'clip1_prepped.mp4'
file 'clip2_prepped.mp4'
file 'clip3_prepped.mp4'

ffmpeg -y -f concat -safe 0 -i concat.txt -c copy body.mp4
```

**Different codecs (filter_complex):**

```bash
ffmpeg -y -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 18 -c:a aac -b:a 192k \
  body.mp4
```

### 3.5 Intro/outro overlays

Layer PNG elements over video using overlay filter with timing:

```bash
ffmpeg -y -i bg_video.mp4 -i title.png -i logo.png \
  -filter_complex "
    [0:v][1:v]overlay=x=(W-w)/2:y=300:enable='between(t,0,5)'[tmp];
    [tmp][2:v]overlay=x=(W-w)/2:y=800:enable='between(t,1,5)'
  " \
  -c:v libx264 -crf 18 -c:a copy \
  intro.mp4
```

### 3.6 YAML-driven batch builds

Structure your episodes as YAML for repeatable builds:

```yaml
id: ep_001
vo: voiceover/ep001_clean.mp3
bgm: assets/bgm.mp3
bgm_vol: 0.08
clips:
  - file: clip_a.mp4
    ss: 0
    to: 8
  - file: clip_b.mp4
    ss: 5
    to: 15
  - file: clip_c.mp4
    ss: 0
    to: 10
subtitles: subs/ep001.srt
```

---

## 4. Text Reels

### 4.1 Format

B-roll video clip + styled text overlay + background music. No voiceover. Used for quotes, tips, stats, listicles.

### 4.2 Text overlay

Use the bundled script `scripts/gen_text_overlay.py`:

```bash
# Centered text with Helvetica:
python3 scripts/gen_text_overlay.py --text "Your quote here" --output overlay.png

# Impact font, 72pt:
python3 scripts/gen_text_overlay.py --text "Bold statement" --output overlay.png --font Impact --font-size 72

# Lower third position:
python3 scripts/gen_text_overlay.py --text "Subscribe" --output overlay.png --position lower_third

# Long text (auto-reduces font if too tall):
python3 scripts/gen_text_overlay.py --text "Very long text that would overflow..." --output overlay.png --max-chars 25
```

Features: 11 font presets, auto font-size reduction (stops at 36pt), sentence-aware word wrap, outline + shadow, three position presets (center, lower_third, upper_third).

### 4.3 Background dimming

Dim the b-roll clip so text is readable:

```bash
# dim = 0.27 means 27% black overlay (good default for text reels)
ffmpeg -y -i clip.mp4 -i text_overlay.png \
  -filter_complex "
    [0:v]drawbox=c=black@0.27:t=fill[dimmed];
    [dimmed][1:v]overlay=0:0
  " \
  -c:v libx264 -crf 18 -c:a copy \
  text_reel.mp4
```

### 4.4 Source audio from trending reels

Extract audio from a trending reel to reuse its music/vibe:

```bash
yt-dlp -f bestaudio -o "source_audio.%(ext)s" "https://www.instagram.com/reel/ABC123/"
# or extract from already downloaded video:
ffmpeg -y -i trending_reel.mp4 -vn -c:a copy source_audio.m4a
```

Mix with your clip:

```bash
ffmpeg -y -i text_reel_silent.mp4 -i source_audio.m4a \
  -filter_complex "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first[a]" \
  -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 192k \
  text_reel_final.mp4
```

---

## 5. Audio

### 5.1 BGM mixing

| Content type | BGM volume |
|-------------|-----------|
| Voiceover reel | 5-8% |
| Text reel (no voice) | 15-20% |
| Dramatic moment | 3-5% (duck under key phrase) |

```bash
ffmpeg -y -i body.mp4 -i bgm.mp3 \
  -filter_complex "
    [1:a]aloop=loop=-1:size=2e+09,atrim=duration=60,volume=0.08[bgm];
    [0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]
  " \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k \
  final.mp4
```

### 5.2 SFX timing

Place a sound effect at a specific timestamp:

```bash
ffmpeg -y -i body.mp4 -i sfx.mp3 \
  -filter_complex "
    [1:a]volume=0.25,adelay=2000|2000[sfx];
    [0:a][sfx]amix=inputs=2:duration=first[a]
  " \
  -map 0:v -map "[a]" -c:v copy -c:a aac \
  body_with_sfx.mp4
```

`adelay=2000|2000` = 2 seconds delay (in milliseconds, both channels).

### 5.3 VO cleanup

**Find silences > 0.3s:**

```bash
ffmpeg -i vo.mp3 -af "silencedetect=noise=-30dB:d=0.3" -f null - 2>&1 | grep "silence_end"
```

**Find stumbles via word timestamps:**

```bash
whisper vo.mp3 --model small --language ru --word_timestamps True --output_format json --output_dir /tmp/
```

**Trim silence at start (iPhone recordings often have 0.5-1.5s silence):**

```bash
# Find where speech starts:
ffmpeg -i vo.mp3 -af "silencedetect=n=-40dB:d=0.1" -f null - 2>&1 | grep "silence_end"
# Trim (e.g., silence ends at 0.8s):
ffmpeg -y -i vo.mp3 -ss 0.8 -c:a copy vo_trimmed.mp3
```

---

## 6. Color and Format

### 6.1 iPhone HDR handling

iPhone records HEVC with HLG/bt2020 10-bit color. Most players/browsers can't display this correctly.

**Check source format:**

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,pix_fmt,color_space,color_transfer,color_primaries \
  video.MOV
```

If you see `bt2020` / `arib-std-b67` / `yuv420p10le` — it's HDR, needs conversion.

### 6.2 SDR conversion

Always transcode to bt709 8-bit for delivery:

```bash
ffmpeg -y -i hdr_video.MOV \
  -vf "format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -movflags +faststart \
  sdr_output.mp4
```

### 6.3 Color preservation

On every libx264 encode, tag color properly to prevent gradual desaturation:

```
-color_range 2 -colorspace bt709 -color_trc bt709 -color_primaries bt709
```

### 6.4 Codec selection

| Use case | Codec | CRF | Notes |
|----------|-------|-----|-------|
| Master delivery | libx264 | 18 | Always |
| Telegram/compressed | libx264 | 28-30 | Scale to 720p if needed for <50MB |
| Preview | libx264 | 30 | Quick check |
| Never | hevc_videotoolbox | — | Files may not open in iCloud/QuickTime |

Always add `-movflags +faststart` for web playback.

---

## 7. QA and Delivery

### 7.1 Frame extraction

Always visually check your output before delivery:

```bash
# Extract frames at key timestamps
for t in 1 5 10 20 30; do
  ffmpeg -y -ss $t -i final.mp4 -vframes 1 -q:v 2 /tmp/check_t${t}s.jpg
done
```

Verify:
- Subtitles visible and correctly positioned?
- Correct font and outline?
- No artifacts, no double-baked text from prior renders?
- Overlays positioned correctly?

### 7.2 Whisper verification

Run Whisper on the final export to verify speech matches your script:

```bash
whisper final.mp4 --model small --language ru --output_format txt --output_dir /tmp/qa/
```

### 7.3 Ending truncation check

The `-shortest` flag can silently cut the last phrase. Always verify:

```bash
# Check duration
ffprobe -v error -show_entries format=duration -of csv=p=0 final.mp4

# Whisper-verify last 10 seconds
ffmpeg -y -sseof -10 -i final.mp4 -vn -c:a pcm_s16le /tmp/ending.wav 2>/dev/null
whisper /tmp/ending.wav --model small --output_format txt --output_dir /tmp/qa/
```

### 7.4 Export formats

**Master:**
```bash
# 1080x1920, high quality
ffmpeg -y -i assembled.mp4 \
  -c:v libx264 -crf 18 -preset medium \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  master.mp4
```

**Compressed (Telegram / <50MB):**
```bash
ffmpeg -y -i master.mp4 \
  -vf "scale=720:1280" \
  -c:v libx264 -crf 28 \
  -c:a aac -b:a 96k \
  -movflags +faststart \
  compressed.mp4
```

---

## 8. Word-Accurate Sync (music, rap, fast slang)

For talking-head VO the chunky Whisper segment timings (§1) are fine. But when subtitles or pop-up cards must land on the **exact word** (music videos, rap, fast slang), segment timings drift ±1–2s and look broken. Use **word-level DTW timestamps** and map your *known-correct* text onto them.

```bash
ffmpeg -y -i master.mp4 -vn -ar 16000 -ac 1 master.wav
whisper master.wav --model medium --language ru --word_timestamps True \
  --output_format json --output_dir wt --fp16 False
```

- Flatten `wt/<name>.json` → `segments[].words[]` into `(start, end, word)`.
- Whisper mishears slang/English loanwords (a foreign brand or tech term comes back as a phonetic Cyrillic guess). **Don't trust its text** — align *your* correct lyrics to the word stream with `difflib.SequenceMatcher`, carry the correct text, borrow each matched word's time. Interpolate words Whisper dropped; force times monotonic.
- **The track almost never starts at t=0** — there's usually an instrumental intro (commonly 2–3s). Anchoring on real word-times handles this automatically; never hard-code a start offset.

**Sped-up playback compensation:** if audio recorded at 1.0× is played back faster in the edit (e.g. a voice message played at 1.5×, a screen-recording at 2×), subs generated at 1.0× progressively run late. Multiply every cue time by `1/speed` (1.5× → ×0.667). If you also re-speed the audio yourself, `atempo=<speed>` the audio **and** `setpts=PTS/<speed>` the video, then recompute every downstream cue/overlay window.

## 9. Pop-up Dictionary / Term Cards

iOS-notification-style cards that pop up to define a term **exactly when it's said** — great for slang/jargon explainer reels.

1. **Render each card to a transparent PNG** via headless Chrome (full-frame 1080×1920 canvas, content positioned with CSS):
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
     --force-device-scale-factor=1 --default-background-color=00000000 \
     --window-size=1080,1920 --screenshot=card.png file://card.html
   ```
2. **Time each card** with the word-sync engine (§8): `start = word_time`, `end = min(start+HOLD, next_card_start, DURATION)` — a card is cut the instant the next card appears. `HOLD≈4s` is the max dwell.
3. **Overlay as a HARD CUT**, never an alpha fade:
   ```
   overlay=0:0:enable='between(t,START,END)'
   ```
   ⚠️ **Never `fade=alpha` a single-frame PNG** — libass/overlay freezes its alpha at 0 and the card never shows. Use `enable=` only.
4. **Key images by term name, not loop index.** If you sort cards by time, an index-keyed `img_{i}.png` maps to the wrong term after any re-sort. Keep a `{term: path}` map.

## 10. Image Sourcing for Cards & Overlays

*What kind* of image matters more than the fetch. **AI-generated faces, named people, and brands look bad** — use real images for those:

| Subject | Source |
|---|---|
| Named person (Elon Musk, Paul Graham) | REAL photo — Wikipedia REST `…/api/rest_v1/page/summary/<Title>` → `originalimage` |
| Brand / company logo (WeWork, YC) | REAL logo — MediaWiki `prop=images`, **filter filenames on the brand token** (else you grab `Commons-logo.svg`); prefer `.svg`→`.png` |
| Role-type people (HR, investor, mentor) | REAL stock photo — Wikimedia Commons file search (`gsrnamespace=6`), accept only real color photos |
| Abstract concept / object / metaphor | AI generation is fine here |

Set a real `User-Agent` (contact email) on Wikimedia requests or you get 403. Square every image to a uniform size (logos → *contain* on transparent square with ~14% margin so they're never cropped; faces/products → *cover* center-crop on white). Spot-check each fetched image — a wrong-subject Wikipedia lead image is common.

## 11. Music-Video Lip-Sync

Assemble a music video from several phone takes performed/lip-synced to a finished track.

- **Auto-sync each take to the track by waveform** (GCC-PHAT cross-correlation of the clip audio vs the master): returns the clip's offset into the track. Strong lock ⇒ the clip frame at clip-time `t` belongs at track-time `offset + t`; place it there and lip-sync lands.
- **Decide audio source per section — LIP-SYNCED vs LIVE-SPOKEN, not intro vs verse:**
  - *Lip-synced* (he mouths along to playback): use **only the clean master track**; never layer the clip's own audio under it.
  - *Live-spoken* (actually speaking to camera, no track playing): **keep the clip's own audio** — the master would de-sync his face by 1–2s.
- **Gapless clean-track assembly:** lay ONE continuous master segment over the whole timeline (no per-segment audio jumps) and trim each *video* segment so the segment durations sum to the matching span of the song. Anchor on word-times (§8).
- **Music intro card:** open on the song cover + a title card while the **track plays from its very start**, then cut to the performer exactly on the first lyric. Take the pre-first-lyric audio as the intro bed (`-t <cut> -vn`), build a cover+title clip of that duration, then concat `intro + main` where main starts at `<cut>`. Since intro-audio = track[0:cut] and main-audio = track[cut:], the music is **gapless** across the join — only the picture changes.

## 12. Safe Zones (1080×1920) — keep content off the UI

Platform UI (caption, name, progress bar, engagement buttons) overlaps the frame edges. Keep all key visuals — subtitles, cards, logos — inside the safe area:

| Margin | Instagram/FB Reels | TikTok | Use |
|---|---|---|---|
| Top | 220px (min 108) | 108px | profile / search UI |
| Bottom | 420px (min 320) | 320px | caption, name, progress bar |
| Left | 60px | 60px | — |
| **Right** | 120px | **120px** | like/comment/share column |

**Cross-platform safe rectangle: 900×1400, centered.** Center cards/overlays with **symmetric** left/right margins. Set subtitle vertical position via the ASS style `MarginV` so text sits above the bottom zone.

⚠️ **If you uniquify afterwards (§13), the center-crop zooms ~×1.075 and eats these margins — pre-compensate** by placing content with extra inset, then re-measure on the final uniq'd frame (not the base).

## 13. Uniquify for Reposts (anti-fingerprint)

To re-upload an edited reel without the platform flagging it as duplicate/previously-shared, you must break three detection layers: **visual CNN embeddings**, **audio fingerprint**, and **perceptual hash + metadata**. Simple crop / brightness / re-encode / metadata-strip alone do NOT work (the CNNs are trained to be invariant).

For reels with **burned-in cards or subtitle boxes**, use this *low-distortion* transform — it leans on invisible disruptors and avoids barrel distortion/vignette (those bend the straight edges of your cards):

```bash
ffmpeg -y -i in.mp4 \
  -vf "crop=iw*0.93:ih*0.93,scale=1080:1920:flags=lanczos,\
hue=h=6,eq=brightness=0.008:contrast=1.015:saturation=1.03,\
noise=c0s=6:c0f=t+u" \
  -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -g 18 -bf 3 \
  -c:a aac -b:a 192k -ac 2 -ar 48000 -map_metadata -1 -movflags +faststart \
  out.mp4
```

- **Temporal grain (`noise … c0f=t`)** is the workhorse — unique per-frame texture wrecks the CNN embedding every frame, near-invisible.
- **Center crop 93%** drops the original edge pixels + changes framing (no warp = clean card edges).
- **`hue`, GOP `-g 18`, `-map_metadata -1`** hit color, temporal-segment boundaries, and the binary/metadata layer.
- **Never flip/mirror** (reverses baked-in text) and **never change audio speed/pitch** (de-syncs voice; pitch-shift is detected at ~97% anyway — just re-encode).
- If it's *still* flagged, escalate grain `c0s=8` and `hue=h=9` before reaching for any geometric warp.

### The three detection layers

| Layer | What it matches | What breaks it |
|---|---|---|
| **Visual CNN embedding** | Trained to be invariant to crop / brightness / re-encode — those alone do NOT work | Per-frame temporal grain, hue shift, slight geometric warp (barrel), vignette |
| **Audio fingerprint** | Acoustic fingerprint of the soundtrack (Shazam-style); survives re-encode | A faint, imperceptible noise bed mixed under the audio; full re-encode |
| **Perceptual hash + metadata** | File hash, container metadata, GOP/keyframe layout | `-map_metadata -1`, codec/bitrate change, GOP change (`-g 18 -bf 3`) |

### Audio layer (don't skip it)

A picture-only uniquify still leaves the **soundtrack fingerprint** intact — that alone can flag the repost. Mix in a faint noise bed that's inaudible but shifts the acoustic fingerprint, then fully re-encode:

```bash
# generate ~ -45 dB noise the length of the clip, mix under the original audio
ffmpeg -y -i in.mp4 \
  -filter_complex "anoisesrc=color=pink:amplitude=0.004[n];\
[0:a][n]amix=inputs=2:duration=first:weights='1 0.05'[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 out.mp4
```

- **Pink noise at ~0.4% amplitude** sits below the perceptual floor on a music/voice track but changes the fingerprint. Bump `amplitude` to `0.008` if still matched.
- **Never pitch/tempo shift** to dodge audio matching — it de-syncs the voice and is detected ~97% of the time anyway. The noise bed + re-encode is enough.

### Aggressive variant (no baked-in graphics)

When the reel has **no cards/subtitle boxes to protect** (plain talking-head or B-roll), you can add geometric warp for a stronger break — barrel distortion + off-center crop + vignette bend the frame in ways the CNN can't normalize:

```bash
ffmpeg -y -i in.mp4 \
  -vf "lenscorrection=k1=0.04:k2=0.02,\
crop=iw*0.95:ih*0.95:(iw*0.03):(ih*0.028),scale=1080:1920:flags=lanczos,\
hue=h=4,eq=brightness=0.01:contrast=1.02:saturation=1.04,\
noise=c0s=4:c0f=t+u,vignette=PI/6" \
  -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -g 18 -bf 3 \
  -c:a aac -b:a 192k -ac 2 -ar 48000 -map_metadata -1 -movflags +faststart \
  out.mp4
```

| Filter | Layer hit | Effect |
|---|---|---|
| `lenscorrection k1/k2` | visual | gentle barrel warp — bends geometry the CNN can't undo |
| `crop … (iw*0.03):(ih*0.028)` | visual + hash | off-center crop drops edge pixels, shifts framing |
| `hue` + `eq` | visual | color-space shift |
| `noise c0s=4 c0f=t` | visual | per-frame temporal grain |
| `vignette=PI/6` | visual | edge darkening — alters global luminance signature |
| `-g 18 -bf 3` | hash | changes keyframe/GOP layout |
| `-map_metadata -1` | metadata | strips container tags |

⚠️ **Do NOT use this variant on reels with cards or subtitle boxes** — `lenscorrection` and `vignette` curl the straight edges and you'll see warped rectangles + corner pixels. Use the low-distortion transform above for those.

## 14. Hard Rules (Learned the Hard Way)

1. **CFR before concat** — ALL segments must be constant 30fps before any concatenation. VFR + CFR = freeze frames, duplicated frames, audio drift.

2. **Never overlay on baked text** — if a video already has burned-in subtitles, never add more on top. Always rebuild from source layers. Double-baked subs produce ghost text.

3. **Max 3 versions rule** — if after v3 the result still doesn't work, stop and diagnose systematically. Don't keep patching symptoms — find the root cause.

4. **Diagnose before rebuild** — run ffprobe, extract frames, check logs BEFORE starting a new build attempt.

5. **Subtitle text must be manually verified** — Whisper (even large-v3) makes plausible-looking errors. Never trust raw output.

6. **VO silence at start** — iPhone recordings always have 0.5-1.5s silence at the beginning. Always detect and trim.

7. **Match visuals to narration** — when the narrator says "email", show email. When they say "product", show the product. 80% topic-matched clips, 20% cutaways.

8. **Check orientation before using clips** — ffprobe metadata can lie about rotation. Always extract a frame and look at it.

9. **Never use `hevc_videotoolbox` for final delivery** — QuickTime and iCloud may refuse to open the file. Use `libx264 + yuv420p` always.

10. **Always `movflags +faststart`** — without this, the video won't stream properly on web/mobile.

11. **Word-sync needs word timestamps** — for music/rap/fast slang, chunky Whisper segments drift ±1–2s. Use `--word_timestamps True` and map your correct text onto the word stream. Never assume the track starts at t=0.

12. **Never alpha-fade a single-frame PNG overlay** — alpha freezes at 0 and it never shows. Use `overlay=…:enable='between(t,a,b)'` (hard cut).

13. **Key per-item images by name, not index** — sorting/re-timing a card list silently maps the wrong image to the wrong item otherwise.

14. **Real images for real people & brands** — AI-generated faces and logos look bad. Fetch real photos/logos for anything named; reserve AI generation for abstract concepts/objects.

15. **Respect safe zones, and pre-compensate if you uniquify** — keep content inside top 220 / bottom 420 / left 60 / right 120 (§12). The anti-fingerprint center-crop (§13) zooms in and eats those margins — inset extra, then measure on the final output.

16. **Uniquify without warping baked graphics** — for reels with burned-in cards/subs, skip barrel distortion + vignette (they bend card edges); lean on temporal grain + hue + crop + metadata strip. Never flip or change audio speed/pitch.
