# talking-head reel — все скрипты пайплайна

Шаблоны из проекта creator-reels (2026-06). Рабочая папка = `$REEL_DIR` (или cwd), исходные MOV =
`$REEL_SRC`. Полный гайд → `../../references/talking-head-broll-reel.md`.

```bash
export REEL_DIR=/path/to/work    # промежуточные файлы тут (build/, audio/, broll/, final/)
export REEL_SRC="/path/to/Telegram Desktop"   # папка с исходными MOV
```

## Порядок пайплайна (блогер = основа, AI поверх)

| # | Скрипт | Что делает |
|---|---|---|
| 1 | `gemini_select_takes.py` | Gemini выбирает лучший чистый дубль под каждую строку скрипта (по прокси) |
| 2 | `build_from_selection.py` | нарезка чистой основы (видео+звук вместе) + snap границ к тишине |
| 3a | `deepgram_transcribe.py` | Deepgram Nova-3 word-тайминги (НЕ схлопывает повторы; чанки 30с) |
| 3b | `verbatim_audit.py` · `gemini_verbatim.py` | дословный аудит — ловит дубли, что ASR прячет |
| 3c | `trim_glitches.py` | хирургический рез найденных дублей/фрагментов (+ afade на стыках) |
| 4 | `gemini_plan.py` | пошаговый монтаж-план (face vs broll сегменты по смыслу) |
| 5 | `broll_runner.py` · `veo_runner.py` | генерация b-roll: Runway Seedance (throttle/recovery) / Veo 3.1 Fast (escape) |
| 5b | `gen_music_sfx.py` · `gen_suno_music.py` | музыка-бед + SFX (ElevenLabs) / Suno через Playwright |
| 6 | `author_from_plan.py` | раскладка клипов по плану (fx/переходы/SFX) |
| 7 | `make_captions.py` | караоке word-pop ASS (динамический кегль — не вылезает) |
| 8 | `assemble_overlay.py` | основа + b-roll поверх окнами + микс + грейд + концовка |

## Вспомогательные / альтернативные

| Скрипт | Что |
|---|---|
| `cut_video.py` | основа по дублям БЕЗ внутренней silence-чистки (грубее build_from_selection) |
| `build_base_tight.py` | основа по дублям + убрать ТОЛЬКО длинные паузы внутри (jump-cut, синхрон цел) |
| `build_edl.py` · `cut_audio.py` | EDL по тишине + сборка ТОЛЬКО аудио-VO (для full-AI рилсов без лица блогера) |
| `build_full_vo.py` · `remap_words.py` · `remap_words_base.py` | склейка VO+концовка, ремап слов на финальный таймлайн |
| `transcribe_raw.py` · `transcribe_clean.py` | WhisperX батч (raw / чистые основы) — для ЛОКАЛИЗАЦИИ, не финальной верификации |
| `assemble_reel.py` · `author_timeline.py` | full-AI b-roll сборка (xfade-цепочка, БЕЗ основы-блогера) — другой жанр |
| `author_overlays.py` | ранняя segmap-раскладка оверлеев (до gemini_plan; author_from_plan лучше) |
| `gemini_analyze.py` | ⚠️ глитч-детект по тайм-кодам — ГАЛЛЮЦИНИРУЕТ, не доверять; используй verbatim_audit |

## QA-хелперы (проверять КАЖДУЮ итерацию до отправки)

| Скрипт | Что |
|---|---|
| `qa_contact_sheet.py VIDEO` | контактка всего ролика (1 кадр / 3.5с) — b-roll/субтитры/грейд/стыки одним взглядом |
| `grade_preview.py VIDEO --t <bright-ts>` | 4 варианта грейда бок-о-бок на ярком кадре — выбрать силу затемнения |
| `audio_balance_check.py VIDEO --gap <music-only-ts>` | объективно: музыка тише голоса или нет (volumedetect) |

## Cheat-sheet правок клиента → reference (talking-head-broll-reel.md, раздел «Cheat-sheet»)

Самое частое: «светлая» → grade highlight 0.72; «музыка громко» → music_gain 0.15 + ducking ratio 7;
«эффекты громко» → sfx_gain ×0.2. **Двигай заметно (×2 / 25-30%), клиент чувствует слабее цифр.**

## Ключевые гочи (детали в reference)

- **Deepgram Nova-3, не WhisperX** для детекта повторов (Whisper схлопывает «далее далее»).
- **zoompan d=1**, не d=N (d=N замораживает видео в фото).
- Субтитры: динамический кегль (не вылезают за экран).
- Музыка под голос: `volume=0.26` + sidechaincompress ratio 5; голос `1.22`; SFX `×0.3`.
- Грейд: спад светов до LUT (яркое лицо/одежда не выбиваются).
- Runway Unlimited = explore-only (credits 400) → троттл → Veo 3.1 Fast escape.
