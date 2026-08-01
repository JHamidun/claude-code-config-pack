---
name: video-editor
description: "Локальный видеомонтаж на FFmpeg+Python: вырезка тишины/дублей, виральные субтитры, переходы, цветокор/LUT, авто-рефрейм 16:9→9:16, overlay-рил talking-head + AI b-roll. Триггеры: «вырежи паузы», «рилс из видео блогера». НЕ: генерация AI-видео→video-generation."
type: actionable
---

# Video Editor (Local FFmpeg + Python)

CLI для видеомонтажа. Базовые операции — stdlib-only (`video_editor.py`). **Профессиональный монтаж** (динамическая нарезка, beat-sync, виральные субтитры, переходы, цветокор, авто-рефрейм, speed ramps, sound design, motion graphics) — набор скриптов в `scripts/`, индекс и правила ремесла в **`references/montage-toolkit.md`**.

## Professional montage toolkit (scripts/)

| Скрипт | Что | Deps |
|---|---|---|
| `silence_cut.py` | вырезать тишину/jump-cut (auto-editor / ffmpeg) | auto-editor |
| `beat_sync_edit.py` | нарезка под биты музыки + xfade + loudnorm | librosa |
| `karaoke_captions.py` | виральные word-by-word субтитры (WhisperX→ASS) | whisperx+torch |
| `transitions.py` | 44 xfade + flash/glitch/whip | ffmpeg |
| `color_grade.py` | LUT (Kodak 2383) / teal-orange / film look | ffmpeg + bundled LUT |
| `reframe_9x16.py` | авто-рефрейм 16:9→9:16 (center/yolo/saliency) | ffmpeg / ultralytics |
| `speed_ramp.py` | слоумо/ускорение + motion blur + true-slowmo | ffmpeg |
| `scene_detect.py` | детекция сцен/шотов + split | scenedetect |
| `sfx.py` | Freesound SFX + place + sidechain ducking | ffmpeg (+API key) |
| `add_captions.py` | captacity-субтитры (требует moviepy<2, отд. venv) | captacity |
| `../video-generation/scripts/motion_graphics.py` | like-counter/progress/countdown/lower-third/pop | ffmpeg+PIL |

> `karaoke_captions.py` авто-ужимает кегль на строку (`fit_size`) — длинные RU-слова больше НЕ вылезают за экран.

## Talking-head + AI b-roll reel (блогер = основа, AI поверх)

Рилс из снятого видео блогера + AI-врезки ПОВЕРХ (не full-AI). Полный 8-шаговый пайплайн +
правила (звук ИЗ видео, Gemini ОТБИРАЕТ дубли, **верификация Deepgram а не Whisper**) →
**`references/talking-head-broll-reel.md`**. Скрипты-шаблоны в `scripts/talking-head/`:

| Скрипт | Что |
|---|---|
| `gemini_select_takes.py` | Gemini выбирает лучший чистый дубль под каждую строку скрипта |
| `build_from_selection.py` | нарезка чистой основы + snap границ к тишине (видео+звук вместе) |
| `deepgram_transcribe.py` | Deepgram Nova-3 word-тайминги (НЕ схлопывает повторы; чанки 30с) |
| `verbatim_audit.py` / `gemini_verbatim.py` | дословный аудит — ловит дубли, что ASR прячет |
| `trim_glitches.py` | хирургический рез найденных дублей/фрагментов (+ afade на стыках) |
| `gemini_plan.py` | пошаговый монтаж-план (face vs broll сегменты по смыслу) |
| `author_from_plan.py` | раскладка клипов по плану (fx/переходы/SFX) |
| `assemble_overlay.py` | основа + b-roll поверх окнами + микс + грейд + концовка |
| `qa_contact_sheet.py` · `grade_preview.py` · `audio_balance_check.py` | QA: контактка / варианты грейда / баланс музыка-голос — проверять каждую итерацию |

> **Ревизии клиента:** cheat-sheet «жалоба → крутилка» в `references/talking-head-broll-reel.md` («светлая»→grade 0.72; «музыка громко»→music_gain 0.15+duck ratio 7; «эффекты громко»→sfx ×0.2). **Двигай заметно (×2 / 25-30%) — клиент чувствует слабее цифр.**

Полный гайд + готовые пайплайны + правила ремесла → **`references/montage-toolkit.md`**.
Ландшафт инструментов и ВСЕ рецепты → `references/montage-research-report.md`.
Разбор референс-рилса (соц-UI оверлеи) → `references/reel-teardown-DV08xLPjPOx.md`.
Соц-UI оверлеи (Remotion) + цвет + motion graphics → скилл `video-generation` references.

> **2 критичные гочи (заработаны боем):** `zoompan d=N` ЗАМОРАЖИВАЕТ видео в фото → для зума на видео `d=1`; субтитры вылезали за экран → динамический кегль. Детали в montage-toolkit.md.

> Windows: ffmpeg-фильтры с путями → экранируй двоеточие (`C\:/...`); запускай через **PowerShell** (Git Bash калечит пути). См. `video-generation/references/windows.md`.

---

# Базовые операции (video_editor.py, stdlib-only)

CLI для простого монтажа. Работает локально через FFmpeg, сервер не нужен.

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
