---
name: youtube-transcript
description: "Транскрипты роликов YouTube, саммари и разбор содержимого. Триггеры: «о чём это видео», «текст видео с ютуба», «саммари ролика»."
---

# YouTube Transcript Skill

## Overview

Извлечение транскриптов YouTube видео, создание саммари, анализ контента.

## When to Use

- Получение текста из YouTube видео
- Создание краткого содержания
- Анализ контента видео
- Извлечение ключевых моментов
- Research из видео-источников

## Installation

```bash
pip install youtube-transcript-api pytube
```

## Core Functions

### Get Transcript

```python
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats"""
    if 'youtu.be' in url:
        return url.split('/')[-1].split('?')[0]

    parsed = urlparse(url)
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
        elif parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        elif parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]

    return url  # Assume it's already a video ID

def get_transcript(video_url: str, language: str = 'en') -> list:
    """Get transcript for a YouTube video"""
    video_id = extract_video_id(video_url)

    try:
        # Try requested language first
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=[language]
        )
    except:
        # Fall back to auto-generated or any available
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'ru']).fetch()

    return transcript

# Usage
transcript = get_transcript("https://youtube.com/watch?v=dQw4w9WgXcQ")
# Returns: [{'text': '...', 'start': 0.0, 'duration': 2.5}, ...]
```

### Format Transcript

```python
def format_transcript(transcript: list, with_timestamps: bool = False) -> str:
    """Convert transcript to readable text"""
    if with_timestamps:
        lines = []
        for entry in transcript:
            minutes = int(entry['start'] // 60)
            seconds = int(entry['start'] % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            lines.append(f"{timestamp} {entry['text']}")
        return '\n'.join(lines)
    else:
        return ' '.join([entry['text'] for entry in transcript])

# With timestamps
formatted = format_transcript(transcript, with_timestamps=True)
# [00:00] Never gonna give you up
# [00:03] Never gonna let you down

# Plain text
plain = format_transcript(transcript)
# Never gonna give you up Never gonna let you down...
```

### Get Video Metadata

```python
from pytube import YouTube

def get_video_info(url: str) -> dict:
    """Get video metadata"""
    yt = YouTube(url)
    return {
        'title': yt.title,
        'author': yt.author,
        'length': yt.length,  # seconds
        'views': yt.views,
        'publish_date': yt.publish_date,
        'description': yt.description,
        'thumbnail_url': yt.thumbnail_url,
        'keywords': yt.keywords
    }

info = get_video_info("https://youtube.com/watch?v=...")
print(f"Title: {info['title']}")
print(f"Duration: {info['length'] // 60} minutes")
```

## Advanced Features

### Multi-language Transcripts

```python
def get_available_languages(video_url: str) -> list:
    """List available transcript languages"""
    video_id = extract_video_id(video_url)
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    languages = []
    for transcript in transcript_list:
        languages.append({
            'code': transcript.language_code,
            'name': transcript.language,
            'is_generated': transcript.is_generated,
            'is_translatable': transcript.is_translatable
        })
    return languages

def get_translated_transcript(video_url: str, target_lang: str) -> list:
    """Get transcript translated to target language"""
    video_id = extract_video_id(video_url)
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    # Find any translatable transcript
    for transcript in transcript_list:
        if transcript.is_translatable:
            return transcript.translate(target_lang).fetch()

    raise Exception("No translatable transcript found")
```

### Extract Key Moments

```python
def extract_chapters(description: str) -> list:
    """Extract timestamps/chapters from description"""
    import re

    # Match patterns like "0:00 - Intro" or "1:23:45 Topic"
    pattern = r'(\d{1,2}:)?(\d{1,2}):(\d{2})\s*[-–]?\s*(.+)'
    chapters = []

    for line in description.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            hours = int(match.group(1)[:-1]) if match.group(1) else 0
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            title = match.group(4).strip()

            total_seconds = hours * 3600 + minutes * 60 + seconds
            chapters.append({
                'timestamp': total_seconds,
                'title': title
            })

    return chapters
```

### Summarize with AI

```python
def summarize_transcript(transcript_text: str) -> str:
    """Summarize transcript using AI"""
    # Use with Claude, GPT, or other LLM
    prompt = f"""Summarize this video transcript:

{transcript_text[:10000]}  # Limit for context

Provide:
1. Main topic (1 sentence)
2. Key points (bullet list)
3. Actionable takeaways
"""
    # Call your preferred LLM here
    return call_llm(prompt)

def extract_key_quotes(transcript_text: str) -> list:
    """Extract notable quotes from transcript"""
    prompt = f"""Extract 5-7 most notable quotes from this transcript:

{transcript_text[:10000]}

Return as a list of quotes with approximate timestamps.
"""
    return call_llm(prompt)
```

## Complete Workflow

```python
def analyze_youtube_video(url: str) -> dict:
    """Complete video analysis"""

    # 1. Get metadata
    info = get_video_info(url)

    # 2. Get transcript
    transcript = get_transcript(url)
    text = format_transcript(transcript)

    # 3. Extract chapters
    chapters = extract_chapters(info['description'])

    # 4. Get summary
    summary = summarize_transcript(text)

    return {
        'title': info['title'],
        'author': info['author'],
        'duration': f"{info['length'] // 60} min",
        'chapters': chapters,
        'transcript': text,
        'summary': summary
    }

# Usage
analysis = analyze_youtube_video("https://youtube.com/watch?v=...")
print(f"# {analysis['title']}\n")
print(f"By: {analysis['author']}\n")
print(f"## Summary\n{analysis['summary']}\n")
print(f"## Full Transcript\n{analysis['transcript']}")
```

## Output Formats

### Markdown

```python
def to_markdown(analysis: dict) -> str:
    """Format analysis as markdown"""
    md = f"""# {analysis['title']}

**Author:** {analysis['author']}
**Duration:** {analysis['duration']}

## Summary
{analysis['summary']}

## Chapters
"""
    for ch in analysis['chapters']:
        mins = ch['timestamp'] // 60
        secs = ch['timestamp'] % 60
        md += f"- [{mins}:{secs:02d}] {ch['title']}\n"

    md += f"\n## Full Transcript\n{analysis['transcript']}"
    return md
```

### JSON

```python
import json

def to_json(analysis: dict) -> str:
    """Export as JSON"""
    return json.dumps(analysis, indent=2, ensure_ascii=False)
```

## Batch Processing

```python
def process_playlist(playlist_urls: list) -> list:
    """Process multiple videos"""
    results = []
    for url in playlist_urls:
        try:
            analysis = analyze_youtube_video(url)
            results.append({
                'url': url,
                'status': 'success',
                'data': analysis
            })
        except Exception as e:
            results.append({
                'url': url,
                'status': 'error',
                'error': str(e)
            })
    return results
```

## Error Handling

```python
from youtube_transcript_api import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)

def safe_get_transcript(url: str) -> dict:
    """Get transcript with error handling"""
    try:
        transcript = get_transcript(url)
        return {'success': True, 'transcript': transcript}
    except TranscriptsDisabled:
        return {'success': False, 'error': 'Transcripts are disabled for this video'}
    except NoTranscriptFound:
        return {'success': False, 'error': 'No transcript available'}
    except VideoUnavailable:
        return {'success': False, 'error': 'Video is unavailable or private'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## Tips

1. **Auto-generated vs Manual** - manual transcripts более точные
2. **Language fallback** - всегда имей fallback на другой язык
3. **Rate limiting** - не делай много запросов подряд
4. **Cache transcripts** - сохраняй для повторного использования
5. **Combine with LLM** - для саммари и анализа
