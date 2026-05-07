---
name: video-downloader
description: Download videos from YouTube and other platforms with yt-dlp
---

# Video Downloader Skill

## Overview

Скачивание видео с YouTube и других платформ с помощью yt-dlp.

## When to Use

- Скачивание видео для оффлайн просмотра
- Извлечение аудио из видео
- Скачивание плейлистов
- Архивирование контента
- Конвертация форматов

## Installation

```bash
# pip
pip install yt-dlp

# brew (macOS)
brew install yt-dlp

# winget (Windows)
winget install yt-dlp

# Update
yt-dlp -U
```

## Basic Usage

### Command Line

```bash
# Download video (best quality)
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID"

# Download with specific format
yt-dlp -f "bestvideo+bestaudio" URL

# Download audio only
yt-dlp -x --audio-format mp3 URL

# Download playlist
yt-dlp -o "%(playlist_title)s/%(title)s.%(ext)s" URL

# Download specific quality
yt-dlp -f "bestvideo[height<=720]+bestaudio" URL
```

### Python

```python
import yt_dlp

def download_video(url: str, output_path: str = "."):
    """Download video from URL"""
    options = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

# Usage
download_video("https://www.youtube.com/watch?v=VIDEO_ID", "./downloads")
```

## Format Selection

### List Available Formats

```bash
yt-dlp -F URL
```

Output:
```
ID  EXT   RESOLUTION FPS |   FILESIZE   TBR PROTO
251 webm  audio only      │  3.5MiB  128k https
140 m4a   audio only      │  3.3MiB  128k https
137 mp4   1920x1080   30  │ 45.2MiB  2674k https
136 mp4   1280x720    30  │ 12.4MiB  734k https
```

### Format Codes

```bash
# Best video + best audio
yt-dlp -f "bestvideo+bestaudio" URL

# Best format under 50MB
yt-dlp -f "best[filesize<50M]" URL

# 720p or lower
yt-dlp -f "bestvideo[height<=720]+bestaudio" URL

# Prefer mp4
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" URL

# Audio only, best quality
yt-dlp -f "bestaudio" URL
```

## Output Templates

```bash
# Basic filename
yt-dlp -o "%(title)s.%(ext)s" URL

# With channel name
yt-dlp -o "%(channel)s - %(title)s.%(ext)s" URL

# Organized by date
yt-dlp -o "%(upload_date)s/%(title)s.%(ext)s" URL

# Playlist organization
yt-dlp -o "%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s" URL

# Sanitize filename
yt-dlp -o "%(title).100s.%(ext)s" --restrict-filenames URL
```

### Template Variables

| Variable | Description |
|----------|-------------|
| `%(title)s` | Video title |
| `%(id)s` | Video ID |
| `%(ext)s` | Extension |
| `%(channel)s` | Channel name |
| `%(uploader)s` | Uploader name |
| `%(upload_date)s` | Upload date (YYYYMMDD) |
| `%(duration)s` | Duration in seconds |
| `%(view_count)s` | View count |
| `%(playlist)s` | Playlist name |
| `%(playlist_index)s` | Index in playlist |

## Audio Extraction

```bash
# Extract to MP3
yt-dlp -x --audio-format mp3 URL

# Best audio quality
yt-dlp -x --audio-quality 0 --audio-format mp3 URL

# To specific format
yt-dlp -x --audio-format flac URL  # FLAC
yt-dlp -x --audio-format m4a URL   # M4A/AAC
yt-dlp -x --audio-format wav URL   # WAV

# With metadata
yt-dlp -x --audio-format mp3 --embed-thumbnail --add-metadata URL
```

## Python Examples

### Download with Progress

```python
import yt_dlp

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        print(f"\rDownloading: {percent} at {speed}", end='')
    elif d['status'] == 'finished':
        print('\nDone!')

def download_with_progress(url: str):
    options = {
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
```

### Get Video Info

```python
def get_video_info(url: str) -> dict:
    """Get video metadata without downloading"""
    options = {
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'title': info.get('title'),
            'duration': info.get('duration'),
            'view_count': info.get('view_count'),
            'uploader': info.get('uploader'),
            'upload_date': info.get('upload_date'),
            'description': info.get('description'),
            'thumbnail': info.get('thumbnail'),
            'formats': len(info.get('formats', [])),
        }

info = get_video_info("https://youtube.com/watch?v=...")
print(f"Title: {info['title']}")
print(f"Duration: {info['duration']} seconds")
```

### Download Playlist

```python
def download_playlist(url: str, output_dir: str):
    """Download entire playlist"""
    options = {
        'outtmpl': f'{output_dir}/%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s',
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'ignoreerrors': True,  # Skip failed videos
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
```

### Download Audio Only

```python
def download_audio(url: str, output_dir: str = ".", format: str = "mp3"):
    """Download audio only"""
    options = {
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
```

## Supported Sites

yt-dlp поддерживает 1000+ сайтов:

```bash
# List all supported sites
yt-dlp --list-extractors

# Major platforms:
# - YouTube, YouTube Music
# - Vimeo
# - TikTok
# - Twitter/X
# - Instagram
# - Facebook
# - Reddit
# - Twitch (VODs, clips)
# - SoundCloud
# - Spotify (podcasts)
# - And many more...
```

## Advanced Options

### Rate Limiting & Retries

```bash
# Limit download speed
yt-dlp -r 1M URL  # 1 MB/s

# Retry on error
yt-dlp --retries 10 URL

# Sleep between requests
yt-dlp --sleep-interval 5 URL
```

### Authentication

```bash
# With cookies
yt-dlp --cookies cookies.txt URL

# Username/password
yt-dlp -u USERNAME -p PASSWORD URL

# Browser cookies (auto-extract)
yt-dlp --cookies-from-browser chrome URL
```

### Subtitles

```bash
# Download subtitles
yt-dlp --write-subs URL

# Auto-generated subtitles
yt-dlp --write-auto-subs URL

# Specific language
yt-dlp --sub-langs en,ru --write-subs URL

# Embed in video
yt-dlp --embed-subs URL
```

### Metadata

```bash
# Embed thumbnail
yt-dlp --embed-thumbnail URL

# Embed metadata
yt-dlp --embed-metadata URL

# Write info JSON
yt-dlp --write-info-json URL

# Write description
yt-dlp --write-description URL
```

## Config File

Create `~/.config/yt-dlp/config`:

```
# Default format
-f bestvideo[height<=1080]+bestaudio/best

# Output template
-o ~/Videos/%(uploader)s/%(title)s.%(ext)s

# Embed metadata
--embed-metadata
--embed-thumbnail

# Subtitles
--write-auto-subs
--sub-langs en

# Restrict filenames
--restrict-filenames

# Ignore errors
--ignore-errors
```

## Tips

1. **Use config file** - сохраняй частые опции
2. **Check formats first** - `-F` перед скачиванием
3. **Browser cookies** - для приватного контента
4. **Archive file** - `--download-archive` для пропуска скачанного
5. **Concurrent** - `--concurrent-fragments` для ускорения
6. **SponsorBlock** - `--sponsorblock-remove` для удаления рекламы
7. **Update regularly** - сайты меняют API
