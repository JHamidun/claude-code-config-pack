---
name: submagic
description: SubtitleService AI video captions, B-roll, auto-editing for short-form content
---

# SubtitleService Skill

## Overview

SubtitleService - AI платформа для автоматических субтитров, B-roll и редактирования коротких видео (TikTok, Reels, Shorts).

## API Configuration

```python
import requests
import os

SUBMAGIC_API_KEY = os.getenv('SUBMAGIC_API_KEY')
BASE_URL = "https://api.submagic.co/v1"

headers = {
    "Authorization": f"Bearer {SUBMAGIC_API_KEY}",
    "Content-Type": "application/json"
}
```

## When to Use

- Автоматические субтитры для видео
- Генерация B-roll footage
- Автоматическое редактирование
- Оптимизация для соцсетей
- Viral-style captions

## Core Features

| Feature | Description |
|---------|-------------|
| **Auto Captions** | AI транскрипция + стилизация |
| **B-Roll** | Автоподбор stock footage |
| **Magic Zoom** | Динамические зумы |
| **Emojis** | Автоматические эмодзи |
| **Highlight Words** | Выделение ключевых слов |
| **Multi-style** | 20+ стилей субтитров |

## Caption Styles

| Style | Description | Best For |
|-------|-------------|----------|
| **Hormozi** | Bold, animated | Business, coaching |
| **MrBeast** | Colorful, dynamic | Entertainment |
| **Minimal** | Clean, simple | Professional |
| **Karaoke** | Word-by-word highlight | Music, storytelling |
| **Gradient** | Color transitions | Aesthetic content |
| **Neon** | Glowing effect | Gaming, tech |

## API Endpoints

### Upload Video

```python
def upload_video(video_path: str):
    """Upload video for processing"""
    with open(video_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/upload",
            headers={"Authorization": f"Bearer {SUBMAGIC_API_KEY}"},
            files=files
        )
    return response.json()

# Response:
# {"video_id": "vid_abc123", "duration": 45.5}
```

### Generate Captions

```python
def generate_captions(video_id: str, style: str = "hormozi"):
    """Generate styled captions"""
    payload = {
        "video_id": video_id,
        "caption_style": style,
        "options": {
            "highlight_keywords": True,
            "add_emojis": True,
            "language": "auto"  # Auto-detect
        }
    }

    response = requests.post(
        f"{BASE_URL}/captions/generate",
        headers=headers,
        json=payload
    )
    return response.json()

# Response:
# {"task_id": "task_xyz789", "status": "processing"}
```

### Add B-Roll

```python
def add_broll(video_id: str, keywords: list = None):
    """Auto-generate B-roll based on speech"""
    payload = {
        "video_id": video_id,
        "broll_settings": {
            "auto_detect": True,         # AI picks relevant footage
            "keywords": keywords,         # Manual keywords
            "density": "medium",          # low, medium, high
            "source": "stock"             # stock, ai_generated
        }
    }

    response = requests.post(
        f"{BASE_URL}/broll/generate",
        headers=headers,
        json=payload
    )
    return response.json()
```

### Apply Magic Zoom

```python
def apply_zoom_effects(video_id: str):
    """Add dynamic zoom effects"""
    payload = {
        "video_id": video_id,
        "zoom_settings": {
            "auto_detect_emphasis": True,
            "zoom_intensity": "medium",
            "smooth_transitions": True
        }
    }

    response = requests.post(
        f"{BASE_URL}/effects/zoom",
        headers=headers,
        json=payload
    )
    return response.json()
```

### Check Status & Download

```python
def get_task_status(task_id: str):
    """Check processing status"""
    response = requests.get(
        f"{BASE_URL}/tasks/{task_id}",
        headers=headers
    )
    return response.json()

# Response:
# {
#   "status": "completed",  # pending, processing, completed, failed
#   "download_url": "https://...",
#   "preview_url": "https://..."
# }
```

## Complete Workflow

```python
import time

def process_video_for_social(video_path: str, style: str = "hormozi"):
    """Complete video enhancement for social media"""

    # 1. Upload
    upload_result = upload_video(video_path)
    video_id = upload_result['video_id']
    print(f"Uploaded: {video_id}")

    # 2. Generate captions
    caption_result = generate_captions(video_id, style)

    # 3. Add B-roll
    broll_result = add_broll(video_id)

    # 4. Apply zoom effects
    zoom_result = apply_zoom_effects(video_id)

    # 5. Wait for processing
    task_id = caption_result['task_id']
    while True:
        status = get_task_status(task_id)
        print(f"Status: {status['status']}")

        if status['status'] == 'completed':
            return status['download_url']
        elif status['status'] == 'failed':
            raise Exception("Processing failed")

        time.sleep(5)

# Usage
result_url = process_video_for_social(
    "raw_video.mp4",
    style="mrbeast"
)
print(f"Download: {result_url}")
```

## Caption Configuration

```python
caption_options = {
    # Style
    "style": "hormozi",           # Caption template
    "font": "Montserrat Bold",    # Font family
    "font_size": 48,              # Size in pixels

    # Colors
    "text_color": "#FFFFFF",
    "highlight_color": "#FFD700", # For keywords
    "background_color": None,     # Transparent

    # Animation
    "animation": "pop",           # pop, fade, slide, bounce
    "word_by_word": True,         # Karaoke style

    # Position
    "position": "bottom",         # top, center, bottom
    "margin_bottom": 100,         # Pixels from edge

    # Features
    "highlight_keywords": True,
    "add_emojis": True,
    "remove_filler_words": True,  # Remove "um", "uh"
    "profanity_filter": True
}
```

## Platform Presets

```python
platform_presets = {
    "tiktok": {
        "aspect_ratio": "9:16",
        "duration_max": 60,
        "caption_position": "center",
        "style": "trending"
    },
    "instagram_reels": {
        "aspect_ratio": "9:16",
        "duration_max": 90,
        "caption_position": "center",
        "style": "clean"
    },
    "youtube_shorts": {
        "aspect_ratio": "9:16",
        "duration_max": 60,
        "caption_position": "bottom",
        "style": "bold"
    },
    "twitter": {
        "aspect_ratio": "16:9",
        "duration_max": 140,
        "caption_position": "bottom",
        "style": "minimal"
    }
}

def optimize_for_platform(video_id: str, platform: str):
    """Apply platform-specific settings"""
    preset = platform_presets[platform]
    payload = {
        "video_id": video_id,
        "output_settings": preset
    }
    return requests.post(
        f"{BASE_URL}/optimize",
        headers=headers,
        json=payload
    ).json()
```

## Batch Processing

```python
def batch_process(video_paths: list, style: str = "hormozi"):
    """Process multiple videos"""
    tasks = []

    for path in video_paths:
        upload = upload_video(path)
        caption = generate_captions(upload['video_id'], style)
        tasks.append({
            "video_id": upload['video_id'],
            "task_id": caption['task_id'],
            "source": path
        })

    # Wait for all
    results = []
    for task in tasks:
        while True:
            status = get_task_status(task['task_id'])
            if status['status'] == 'completed':
                results.append({
                    "source": task['source'],
                    "url": status['download_url']
                })
                break
            time.sleep(5)

    return results
```

## Integration Pipeline

```python
# Full content pipeline:

# 1. Record/generate video with HeyGen
video = heygen_generate_video(script)

# 2. Add captions with SubtitleService
captioned = submagic_add_captions(video, style="hormozi")

# 3. Post to social via n8n
n8n_post_to_social(captioned, platforms=["tiktok", "reels"])
```

## Use Cases

| Use Case | Features |
|----------|----------|
| **Podcast clips** | Captions + B-roll + zoom |
| **Course content** | Clean captions + keywords |
| **Product demos** | Minimal style + highlights |
| **Vlogs** | Dynamic zoom + emojis |
| **Ads** | Bold style + CTA highlights |

## Pricing

| Plan | Videos/month | Features |
|------|--------------|----------|
| Starter | 10 | Basic captions |
| Pro | 50 | All styles + B-roll |
| Business | 200 | Priority + API |
| Enterprise | Unlimited | Custom styles |

## Tips

1. **Качество аудио** - чистый звук = точные субтитры
2. **Короткие клипы** - 15-60 сек оптимально
3. **Hormozi style** - для бизнес/образовательного контента
4. **B-roll умеренно** - не перегружай визуально
5. **Тест стилей** - разные аудитории = разные стили

## Free Alternative: Whisper + ASS Captions

When your subtitle API is unavailable or you need offline/free captions, use Whisper + ASS format.

### Pipeline

```python
import whisper
import json

# 1. Transcribe with word-level timestamps
model = whisper.load_model("base")
result = model.transcribe("audio.mp3", language="ru", word_timestamps=True)

# 2. Extract words with timing
words = []
for segment in result["segments"]:
    for w in segment.get("words", []):
        words.append({"word": w["word"].strip(), "start": w["start"], "end": w["end"]})

# 3. Group into display chunks (4 words per group)
def group_words(words, group_size=4):
    groups = []
    for i in range(0, len(words), group_size):
        chunk = words[i:i+group_size]
        groups.append({
            "words": chunk,
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
            "text": " ".join(w["word"] for w in chunk)
        })
    return groups

groups = group_words(words)
```

### ASS Word-Highlight Format

```python
def generate_ass(groups, output_path, width=1080, height=1920):
    margin_v = int(height * 0.75)  # 25% from bottom

    header = f"""[Script Info]
Title: Captions
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,3,3,0,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt_time(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        cs = int((s % 1) * 100)
        return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

    events = []
    for group in groups:
        for i, active_word in enumerate(group["words"]):
            parts = []
            for j, w in enumerate(group["words"]):
                if j == i:
                    parts.append(r"{\c&H00FFFF&\b1\fs80}" + w["word"] + r"{\r}")
                else:
                    parts.append(w["word"])
            text = " ".join(parts)
            start = fmt_time(active_word["start"])
            end = fmt_time(active_word["end"])
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))

generate_ass(groups, "captions.ass")
```

### Burn into Video

```bash
ffmpeg -i video.mp4 -vf "ass=captions.ass" -c:a copy output_with_subs.mp4 -y
```

### Decision Table: SubtitleService vs Whisper+ASS

| Criteria | SubtitleService | Whisper + ASS |
|----------|----------|---------------|
| Cost | Paid (10-200 videos/month) | Free |
| Style | 6 professional styles (Hormozi, MrBeast...) | Basic word-highlight |
| B-roll | Auto stock footage insertion | None |
| Zoom effects | Magic Zoom | None |
| Offline | No (cloud API) | Yes (local Whisper) |
| Languages | Auto-detect | Specify language |
| Best for | Social media (TikTok, Reels, Shorts) | Budget/offline, long-form |
| Emoji support | Auto emoji insertion | Manual only |

### Using HeyGen Starfish word_timestamps

When using HeyGen Starfish TTS (POST /v1/audio/text_to_speech), the response includes `word_timestamps`:

```json
{
  "audio_url": "https://...",
  "duration": 5.526,
  "word_timestamps": [
    {"word": "Hey", "start": 0.079, "end": 0.219},
    {"word": "everyone", "start": 0.219, "end": 0.558}
  ]
}
```

Convert to SRT:

```python
def timestamps_to_srt(word_timestamps, group_size=4, output="captions.srt"):
    # Filter out <start>/<end> markers
    words = [w for w in word_timestamps if not w["word"].startswith("<")]
    groups = [words[i:i+group_size] for i in range(0, len(words), group_size)]

    lines = []
    for idx, group in enumerate(groups, 1):
        start = group[0]["start"]
        end = group[-1]["end"]
        text = " ".join(w["word"] for w in group)
        lines.append(f"{idx}")
        lines.append(f"{_srt_time(start)} --> {_srt_time(end)}")
        lines.append(text)
        lines.append("")

    with open(output, "w") as f:
        f.write("\n".join(lines))

def _srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
```
