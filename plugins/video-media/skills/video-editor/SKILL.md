---
name: video-editor
description: Local video editing via FFmpeg. Concat, music overlay, trim, effects. No server required.
type: actionable
---

# Video Editor (Local FFmpeg)

CLI для видеомонтажа. Работает локально через FFmpeg, сервер не нужен.

## Prerequisites

- FFmpeg installed (`winget install ffmpeg` / `brew install ffmpeg` / `apt install ffmpeg`)
- Python 3.x (no pip dependencies — stdlib only)

## CLI

```bash
python ~/.claude/skills/video-editor/video_editor.py <command> [args]
```

## Commands

### Склейка видео

```bash
python ~/.claude/skills/video-editor/video_editor.py concat \
  video1.mp4 video2.mp4 video3.mp4 \
  --music \
  --music-volume 0.3 \
  --transition fade \
  -o result.mp4
```

### Обработка видео (фильтры + музыка)

```bash
python ~/.claude/skills/video-editor/video_editor.py process \
  input.mp4 \
  --music \
  --brightness 1.1 \
  --contrast 1.2 \
  --saturation 1.3 \
  -o result.mp4
```

### Обрезка видео

```bash
python ~/.claude/skills/video-editor/video_editor.py trim \
  input.mp4 \
  --start 00:00:10 \
  --end 00:01:30 \
  -o clip.mp4
```

### Информация о видео

```bash
python ~/.claude/skills/video-editor/video_editor.py probe input.mp4
```

### Пул музыки

```bash
python ~/.claude/skills/video-editor/video_editor.py music-pool
```

## Parameters

### concat
| Param | Default | Description |
|-------|---------|-------------|
| `videos` | required | 2+ видеофайлов |
| `--music` | false | Наложить фоновую музыку |
| `--custom-music` | — | Свой трек (mp3/wav) |
| `--music-volume` | 0.3 | Громкость музыки (0.0-1.0) |
| `--transition` | none | none / fade / dissolve |
| `--transition-duration` | 0.5 | Длительность перехода (сек) |
| `-o` | auto | Выходной файл |

### process
| Param | Default | Description |
|-------|---------|-------------|
| `video` | required | Видеофайл |
| `--music` | false | Наложить музыку |
| `--custom-music` | — | Свой трек |
| `--music-volume` | 0.3 | Громкость |
| `--brightness` | 1.0 | Яркость (0.0-2.0) |
| `--contrast` | 1.0 | Контраст (0.0-2.0) |
| `--saturation` | 1.0 | Насыщенность (0.0-3.0) |
| `-o` | auto | Выходной файл |

### trim
| Param | Default | Description |
|-------|---------|-------------|
| `video` | required | Видеофайл |
| `--start` | 0 | Начало (HH:MM:SS или секунды) |
| `--end` | end | Конец |
| `-o` | auto | Выходной файл |

## Music Pool

Положи mp3/wav/ogg/m4a файлы в `music/` рядом со скриптом.
Рандомный выбор с anti-repeat (последние 5 не повторяются).

## Notes

- `transition=none` — быстрый concat без перекодирования (`-c copy`)
- `transition=fade` — xfade FFmpeg filter, требует re-encode (медленнее)
- Если fade падает — автоматический fallback на простой concat
- Никаких зависимостей кроме FFmpeg и Python stdlib
- Temp файлы чистятся автоматически
