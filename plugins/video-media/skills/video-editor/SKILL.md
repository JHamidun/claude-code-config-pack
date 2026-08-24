---
name: video-editor
description: "Видеомонтаж FFmpeg+Python: тишина, субтитры, рефрейм 9:16. Триггеры: «вырежи паузы», «склей видео», «наложи музыку». НЕ AI-генерация→video-generation."
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
| `transitions_pro.py` | 8 переходов, которых во встроенном наборе НЕТ | ffmpeg |
| `music_map.py` | карта трека: темп, такты, секции, дропы → сетка склеек | librosa |
| `font_catalog.py` | каталог шрифтов + подбор под роль в кадре | fontTools |
| `fetch_fonts.py` | докачать свободные шрифты с кириллицей | fontTools |
| `../video-generation/scripts/motion_graphics.py` | like-counter/progress/countdown/lower-third/pop | ffmpeg+PIL |

> `karaoke_captions.py` авто-ужимает кегль на строку (`fit_size`) — длинные RU-слова больше НЕ вылезают за экран.

### transitions_pro.py — то, чего ffmpeg не умеет сам

`zoom-punch` (удар зумом, скорости совпадают на склейке) · `shake-cut` (толчок камеры с
затуханием) · `light-leak` (смена прячется в пересвете) · `film-burn` (прожиг плёнки) ·
`blur-dissolve` (подмена в мути) · `rgb-slide` (разъезд каналов) · `luma-wipe` (вытеснение
по яркости) · `speed-ramp-cut` (разгон в склейку, торможение из неё).

```bash
python scripts/transitions_pro.py a.mp4 b.mp4 -o out.mp4 --effect zoom-punch --dur 0.2
python scripts/transitions_pro.py --list
```

Пропорции: короткий удар 0,15–0,25 с читается как акцент, длинный 0,6–1,0 с — как смена
главы. Между ними пусто: 0,4 с выглядит ошибкой темпа.

**Грабля ffmpeg.** Часть параметров (`gblur sigma`, `rgbashift rh/bh`, `colorlevels`)
выражения со временем НЕ принимает — падает на «Error applying option». Но в справке
(`ffmpeg -h filter=gblur`) у них стоит флаг `T` = параметром можно управлять командами.
Решение — расписание через `sendcmd`, **интервалы разделяются `;`**, запятая разделяет
команды внутри одного интервала (с запятой всё склеивается и время уезжает в имя цели).

### music_map.py — монтаж следует за музыкой, а не за метрономом

`beat_sync_edit.py` режет по битам равномерно: на вступлении столько же склеек, сколько
на кульминации. `music_map.py` разбирает трек на секции (вступление / нарастание / пик /
дроп / брейк / финал) и назначает каждой свою плотность склеек и класс перехода.

```bash
python scripts/music_map.py track.mp3 -o map.json --plot map.png
python scripts/music_map.py track.mp3 --cuts          # только моменты склеек
```

Сильную долю берём не счётом, а по силе онсетов (madmom под свежий Python не ставится).
Референсный и рабочий трек разбираются одинаково — чужую структуру можно снять и
приложить к своему материалу.

### Шрифты: каталог собирается локально

Название шрифта не говорит, есть ли в нём кириллица, — половина модных гротесков даёт
пустые квадраты. `font_catalog.py` сканирует шрифты твоей машины и кладёт каталог в
`scripts/fonts_catalog.json` (готовый в пак не входит — в нём абсолютные пути, первым
делом прогони `scan`): кириллицу проверяет по таблице символов, вес берёт из метрик, а
моноширинность — сравнением ширин глифов.

```bash
python scripts/font_catalog.py scan                    # собрать/обновить каталог
python scripts/font_catalog.py stats
python scripts/font_catalog.py pick caption --cyrillic # путь к файлу для ffmpeg
python scripts/fetch_fonts.py                          # докачать 70 семейств OFL
```

Роли: `display` (слово на весь экран) · `caption` (субтитры) · `body` · `numeric`
(моно, чтобы счётчик не дёргался) · `accent` (засечки для цитаты).

Ищет в системных каталогах своей ОС (Windows / macOS / Linux, на Linux — с
подпапками) и в 60 шрифтах под OFL, которые лежат в самом паке
(`skills/canvas-design/canvas-fonts`), — то есть что-то найдётся на любой машине.
Если не нашлось ничего, `scan` **не пишет пустой каталог**, а выходит с кодом 2 и
печатает, какие каталоги проверил: пустой каталог потом читается как «нет шрифта
под эту роль», хотя на деле шрифтов нет вообще.

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
Разбор референс-рилса (соц-UI оверлеи) → `references/reel-teardown-ui-overlay.md`.
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
