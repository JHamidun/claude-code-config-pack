---
name: watch-video
description: "Агент «смотрит» видео — кадры с таймкодами + транскрипт, отвечает по тому, что ВИДНО на экране (слайды, UI, демо). Триггеры: «посмотри видео», «что показывают на экране/в демо», «разбери вебинар со слайдами», «что за UI в ролике конкурента», «проанализируй YouTube визуально», «watch video». НЕ: только текст→youtube-transcript/deepgram; скачать→video-downloader; монтаж→video-editor."
metadata:
  version: 1.0.0
  created: 2026-07-19
  ported_from: bradautomates/claude-video (механика /watch, без кода репо)
  reuses: video-downloader (yt-dlp), deepgram, youtube-transcript, video-editor (ffmpeg)
---

# Watch Video — визуальный разбор видео

Отличие от youtube-transcript/deepgram: те дают только ТЕКСТ. Здесь агент получает **кадры с таймкодами как изображения** + транскрипт — и отвечает на вопросы про то, что на экране (слайды, UI, демо, код, графики).

## Пайплайн (всё уже установлено: yt-dlp, ffmpeg, whisper/Deepgram)

1. **Скачать** (или взять локальный файл):
   ```bash
   yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" --write-auto-subs --sub-langs "ru,en" -o "%(id)s.%(ext)s" <URL>
   ```
   Нативные субтитры (`--write-auto-subs`) — бесплатный транскрипт; Whisper/Deepgram — только если субтитров нет.
2. **Извлечь кадры** ffmpeg по выбранному режиму (ниже), в `scratchpad/<video-id>/frames/`.
3. **Ужать кадры** до ширины 512px (лимит-friendly для image-input):
   ```bash
   ffmpeg -i frame.png -vf "scale=512:-2" frame_s.jpg
   ```
   Имя файла = таймкод (`frame_03m15s.jpg`) — чтобы ссылаться на момент.
4. **Дедуп** статичных кадров (говорящая голова, застывший слайд) — перцептуальное сравнение или просто реже sample.
5. **Read кадры** (Claude читает изображения) + транскрипт с таймкодами → ответ со ссылками на MM:SS.

## 4 режима токен-бюджета

| Режим | Извлечение | Кадров | ~img-токенов | Когда |
|-------|-----------|--------|--------------|-------|
| **transcript** | без кадров, только субтитры/Whisper | 0 | 0 | Вопрос по содержанию речи — это режим youtube-transcript |
| **efficient** | быстрые keyframes (I-frames) | ≤50 | ~10K | Быстрый визуальный обзор: «о чём ролик, что показывают» |
| **balanced** (дефолт) | scene-change detection | ≤100 | ~20K | Разбор вебинара/демо: слайды, переходы, UI |
| **token-burner** | scene-aware без лимита кадров | все сцены | ~23K+ | Плотный разбор: каждый слайд/экран важен (конкурентный teardown) |

Команды ffmpeg:

```bash
# efficient — только keyframes
ffmpeg -skip_frame nokey -i in.mp4 -vsync vfr -frame_pts 1 frames/kf_%04d.png

# balanced / token-burner — по смене сцены (порог 0.3; burner: 0.2 и без head-лимита)
ffmpeg -i in.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr frames/sc_%04d.png

# равномерный fallback (нет явных сцен): 1 кадр в N сек, потолок 2 fps
ffmpeg -i in.mp4 -vf "fps=1/10,scale=512:-2" frames/u_%04d.jpg
```

Таймкоды кадров — из `showinfo` (pts_time в stderr) либо из fps-арифметики.

## Опции разбора

- `--start/--end`: сначала `ffmpeg -ss <start> -to <end> -c copy cut.mp4` — режь ДО извлечения кадров, экономит всё.
- Текст на экране мелкий (код, таблицы) → scale 768–1024px вместо 512 только для нужных кадров.
- Длинное видео (>30 мин) → сначала transcript-режим, найди интересные диапазоны, потом balanced только на них.

## Когда что

- Разбор вебинара со слайдами, teardown конкурентного YouTube, «что за продукт в ролике», проверка своего видео перед публикацией → этот скилл.
- Чисто «что сказали» → `youtube-transcript` / `deepgram`.
- Скачать и всё → `video-downloader`.
- Тренд-скан превью/хуков → `trend-engine` (сюда — когда нужно заглянуть внутрь ролика).
