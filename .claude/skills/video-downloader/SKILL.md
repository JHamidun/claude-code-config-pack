---
name: video-downloader
description: "Скачивание видео с YouTube и других площадок через yt-dlp. Триггеры: «скачай видео», «выкачай ролик», «yt-dlp», «сохрани с ютуба», «download video». НЕ текст→youtube-transcript."
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

### ffmpeg — обязателен для всего, что качается в хорошем качестве

YouTube отдаёт 1080p и выше **раздельными потоками**: видео без звука + звук без видео.
Склеивает их не yt-dlp, а ffmpeg. Любой формат со знаком `+` (`bestvideo+bestaudio`,
`bestvideo[height<=1080]+bestaudio`, `-x --audio-format mp3`) без ffmpeg работать не будет.

И это **тихий** отказ: yt-dlp не падает. Он печатает одну строку предупреждения в общий
поток, молча берёт единый прогрессивный формат — обычно 360p или 720p — и завершается
с кодом 0. Файл на месте, «скачано успешно», качество не то. На Windows ffmpeg по
умолчанию нет, так что это состояние по умолчанию.

Проверь ДО скачивания — команда падает, если ffmpeg нет:

```bash
ffmpeg -version >/dev/null 2>&1 || { echo "ffmpeg НЕ НАЙДЕН: качество будет ограничено одним прогрессивным потоком (360p/720p), склейка 1080p+ и извлечение аудио не сработают"; exit 1; }
```

```powershell
# PowerShell
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { throw "ffmpeg НЕ НАЙДЕН: 1080p+ склеить нечем, yt-dlp молча скачает 360p/720p" }
```

Установка: `winget install Gyan.FFmpeg` (Windows), `brew install ffmpeg` (macOS),
`sudo apt install ffmpeg` (Debian/Ubuntu). Если ffmpeg стоит, но не в PATH —
`yt-dlp --ffmpeg-location "C:\path\to\ffmpeg\bin"`.

Нет возможности поставить ffmpeg — скажи об этом вслух и качай осознанно одним потоком:
`yt-dlp -f "best[ext=mp4]/best" URL`. Тогда ограничение названо, а не спрятано.

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
import shutil
import yt_dlp

def download_video(url: str, output_path: str = "."):
    """Download video from URL"""
    fmt = 'bestvideo+bestaudio/best'

    # Без ffmpeg ветка `bestvideo+bestaudio` неисполнима, и yt-dlp тихо
    # сваливается в `/best` — один прогрессивный поток, 360p/720p, код возврата 0.
    # Лучше отказать здесь, чем отдать не то качество под видом успеха.
    if '+' in fmt and not shutil.which('ffmpeg'):
        raise RuntimeError(
            "ffmpeg не найден, а формат требует склейки видео+аудио.\n"
            "Поставь ffmpeg (winget install Gyan.FFmpeg / brew install ffmpeg / "
            "apt install ffmpeg), либо осознанно запроси один поток: "
            "format='best[ext=mp4]/best' (тогда качество будет ограничено ~720p)."
        )

    options = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'format': fmt,
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

Каждая строка со знаком `+` требует ffmpeg (см. раздел Installation). Без него
yt-dlp не падает, а берёт то, что удаётся скачать одним потоком.

```bash
# Best video + best audio  (нужен ffmpeg)
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
    """Download audio only. Требует ffmpeg: перекодирует его постпроцессор."""
    import shutil
    if not shutil.which('ffmpeg'):
        # Без ffmpeg постпроцессор не отработает, а исходный webm/m4a останется
        # лежать под видом результата — «mp3, который не mp3».
        raise RuntimeError(
            f"ffmpeg не найден — извлечь {format} невозможно. "
            "Поставь ffmpeg или скачивай исходную дорожку как есть "
            "(format='bestaudio', без postprocessors)."
        )

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

Конфиг, положенный не туда, **не вызывает ошибки**: yt-dlp просто не находит файл и
качает с дефолтами. Снаружи это выглядит как «настройки не работают», и понять,
что дело в пути, по выводу невозможно. Поэтому сначала — где именно он лежит,
потом — как убедиться, что его подхватили.

**Путь (первый найденный побеждает):**

| ОС | Куда класть |
|---|---|
| Linux / macOS | `~/.config/yt-dlp/config` |
| Windows | `%APPDATA%\yt-dlp\config` (то есть `C:\Users\<имя>\AppData\Roaming\yt-dlp\config`) |

`~/.config/yt-dlp/config` работает и на Windows тоже — yt-dlp сам разворачивает `~`
и проверяет XDG-каталог первым (проверено на 2026.08.19). Но путь с `~` надо
**создавать** в оболочке, которая его понимает: PowerShell и Git Bash — да,
`cmd.exe` — нет, там `mkdir ~\.config\yt-dlp` заведёт настоящую папку с именем `~`
в текущем каталоге, и конфиг окажется невидим. В cmd бери `%APPDATA%`.

**Проверка, что конфиг подхвачен** — обязательный шаг, а не необязательный:

```bash
yt-dlp -v --simulate "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>&1 | grep "User config"
```

- строка `[debug] User config "<путь>": ['--restrict-filenames', ...]` — конфиг прочитан,
  в скобках видно, какие именно опции из него взялись;
- **пустой вывод** — файла по этому пути нет. Ошибки не будет никогда: это и есть
  тот случай, когда «всё работает», а настройки не применяются.

Содержимое:

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
