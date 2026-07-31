# Montage toolkit — профессиональный монтаж (scripts + craft)

Набор инструментов «как у профи»: динамическая нарезка, beat-sync, виральные субтитры,
переходы, цветокор, авто-рефрейм, speed ramps, sound design, motion graphics.
Собран из глубокого ресёрча (полный ландшафт инструментов и ВСЕ рецепты →
`references/montage-research-report.md`; разбор референс-рилса → `references/reel-teardown-DV08xLPjPOx.md`).

## Скрипты (video-editor/scripts/ и video-generation/scripts/)

| Скрипт | Что делает | Зависимости | Статус |
|---|---|---|---|
| `silence_cut.py` | Вырезать тишину / jump-cut (auto-editor или чистый ffmpeg) | auto-editor (✓) | ✓ |
| `beat_sync_edit.py` | Нарезка клипов под биты музыки + xfade + loudnorm | librosa (✓) | ✓ tested |
| `karaoke_captions.py` | **Виральные субтитры** word-by-word (WhisperX→ASS \kf→burn) | whisperx+torch (✓) | ✓ (модель качается при 1-м запуске ~3ГБ) |
| `add_captions.py` | Субтитры через captacity (быстрый путь) | captacity + **moviepy<2** | ⚠ нужен отд. venv (moviepy 2.x ломает) |
| `transitions.py` | xfade-цепочка (44 перехода) + flash/glitch/whip | ffmpeg | ✓ tested |
| `color_grade.py` | LUT (Kodak 2383) / teal-orange / film pipeline | ffmpeg + bundled LUT | ✓ tested |
| `reframe_9x16.py` | Авто-рефрейм 16:9→9:16 (center/yolo/saliency) | center: ffmpeg ✓; yolo: ultralytics ✓; saliency: pyautoflip | ✓ center tested |
| `speed_ramp.py` | Слоумо/ускорение + motion blur + true-slowmo | ffmpeg | ✓ tested |
| `scene_detect.py` | Детекция сцен/шотов + split | scenedetect (✓) | ✓ tested |
| `sfx.py` | Freesound SFX поиск/скачивание + место на таймлайне + ducking | ffmpeg (+ FREESOUND_API_KEY) | ✓ (нужен ключ) |
| `../video-generation/scripts/motion_graphics.py` | like-counter / progress / countdown / lower-third / pop (Cyrillic-safe) | ffmpeg+PIL | ✓ tested |

Все скрипты — CLM, `python <script> --help`. Пути с двоеточием в ffmpeg-фильтрах **экранируются** (`C\:/...`), запуск на Windows — через PowerShell (Git Bash калечит пути, см. windows.md §10).

## Быстрые сценарии

```bash
# 1. Сырая запись → убрать паузы → субтитры → цветокор → вертикаль
python video-editor/scripts/silence_cut.py raw.mp4 cut.mp4
python video-editor/scripts/karaoke_captions.py cut.mp4 cap.mp4 --lang ru --style hormozi
python video-editor/scripts/color_grade.py cap.mp4 graded.mp4 --lut kodak2383 --strength 0.7
python video-editor/scripts/reframe_9x16.py graded.mp4 final.mp4 --method yolo

# 2. Музыкальный клип-нарезка под биты
python video-editor/scripts/beat_sync_edit.py music.mp3 b1.mp4 b2.mp4 b3.mp4 -o clip.mp4 --beats-per-cut 2 --transition wipeleft

# 3. Промо как в референс-рилсе: соц-UI оверлей + pop-элементы
#    (Remotion IG/TG-хром → overlay; затем motion_graphics pop)
python video-generation/scripts/motion_graphics.py pop in.mp4 out.mp4 --text "СКИДКА 50%" --at 3
python video-generation/scripts/motion_graphics.py like-counter out.mp4 out2.mp4 --to 15000 --start 1 --end 4
```

## THE CRAFT — кодифицируемые правила монтажа (из ресёрча)

**Хук (0–3с):** выполнить обещание ИЛИ паттерн-интеррапт за 3с, ≤12 слов. Нужно ≥2 из 4: любопытство · паттерн-интеррапт · самореферентность · эмоция. Спикерский хук ВСЕГДА в паре с визуальным (жирный титр / резкий срез / zoom-punch).

**Темп:** новый визуал/срез каждые **3–6с** без исключений. Цикл напряжение→разрядка: быстрые срезы + рост звука → пауза + пейофф → повтор. Убирать: слова-паразиты, паузы >0.3с, повторы, любой план >8с без интеррапта. Цель Shorts: 70–100% досмотра (<30% = провал темпа).

**Срезы:** **J-cut** (звук следующей сцены ДО видео-среза — антиципация) · **L-cut** (звук текущей под след. видео — контекст) · **match cut** (форма/движение совпадают) · **punch-in** 10–15% (max 20%) · **jump cut** (убрать паузы, оставить 0.1–0.2с поля у речи).

**Beat-sync:** 120 BPM → срез каждые 0.5с; 90 BPM → 0.67с; ±2 кадра допуск. **Даунбит (начало такта) = смена сцены**, обычные биты = срезы b-roll, онсеты = места SFX. Хард-кат на даунбит = стабильность; на апбит = напряжение.

**Open-loop структура:** `[0-3] ХУК (назвать результат/проблему, не показывая)` → `[4-15] ЦЕННОСТЬ (кредибилити)` → `[16-60] БИЛД (шаги + мини-петли)` → `[50%] РЕ-ЭНГЕЙДЖ (интеррапт + повтор обещания)` → `[финал] ПЕЙОФФ + хук следующего видео`.

**Визуал:** субтитры ≥6% высоты кадра, контрастная подложка, 3–5 слов; punch-in max 20%; виньетка чуть заметная (angle=PI/5); один LUT на серию (последним фильтром); на ускорении всегда motion blur (`tmix=frames=8`); переходы 0.15–0.3с для shortform, dissolve <10% склеек.

## Talking-head + AI b-roll overlay (блогер = основа, AI поверх)

Отдельный жанр: снятое видео блогера + его синхронный звук = ОСНОВА, AI-клипы накладываются
ПОВЕРХ окнами. Полный 8-шаговый пайплайн + скрипты → **`references/talking-head-broll-reel.md`**
(`scripts/talking-head/`). Ключевое: «убрать паузы» = jump-cut видео+аудио ВМЕСТЕ (синхрон цел),
звук ИЗ видео а не кроится отдельно; Gemini ОТБИРАЕТ лучший дубль фразы (не ищет глитчи —
галлюцинирует); **верификация Deepgram Nova-3, не Whisper**.

## Чистка звука из «грязных» многодублевых исходников

- **WhisperX СХЛОПЫВАЕТ повторы** → слепое пятно. «Далее я бы предлож… Далее я бы предложил»
  Whisper пишет ОДИН раз; дубль остаётся в звуке, транскрипт врёт что чисто. **Используй
  Deepgram Nova-3** (`scripts/talking-head/deepgram_transcribe.py`) — не схлопывает. Гоча:
  на полном длинном файле дропает первые ~15с → чанки по 30с + ретрай на 408.
- Скрытые повторы также ловит Gemini verbatim на коротких клипах (`verbatim_audit.py`).
- Хирургический рез найденного: `trim_glitches.py` (диапазоны + afade на стыках). После —
  ре-транскрипция до чистого end-to-end.

## ⚠️ zoompan d=N ЗАМОРАЖИВАЕТ видео (критичная гоча)

`zoompan=...:d=N` на ВИДЕОвходе держит первый входной кадр N раз → клип превращается в
СТАТИЧНОЕ ФОТО с зумом («оживлённое фото вместо видео» — заказчик ловит сразу). `d` = сколько
выходных кадров на КАЖДЫЙ входной. Для движущегося зума на ВИДЕО (сохранить нативное движение):

```
# ВЕРНО — d=1: один выходной кадр на входной, движение сохранено, зум по 'on'
zoompan=z='min(1.0+0.0012*on,1.14)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30
# НЕВЕРНО — d=125: заморозка первого кадра
```

`crop` с `t` в w/h НЕ работает (crop размеры статичны, анимируется только x/y). Скорость зума
нормировать под длину: `rate = Z / (dur*fps)`.

## ⚠️ Субтитры вылезают за экран

`WrapStyle 2` + фикс. кегль → длинные RU-слова («ПРАВДОПОДОБНОСТИ») уезжают за 1080px.
`karaoke_captions.py` теперь авто-ужимает кегль на строку (`fit_size`: `size=SAFE_W/(len*0.60)`,
SAFE_W = W−2·70) + WrapStyle 0 (перенос-страховка). Проверять на самом длинном слове.

## Что мы НЕ ставили / гочи

- **ffmpeg-concat** (GL-переходы, Node) — не собрался на Windows (node-gyp). Замена: `transitions.py` (44 ffmpeg xfade) + **xfade-easing** (GLSL без перекомпиляции, expression-режим) — см. research-report §3D.
- **captacity** — несовместим с moviepy 2.x → используем `karaoke_captions.py` (WhisperX). Если нужен captacity: отдельный venv с `moviepy<2`.
- **madmom/aubio** (downbeats) — нет колёс под Python 3.13. `beat_sync_edit.py --downbeats` тихо откатывается на librosa-биты.
- **Kodak LUT** содержал `LUT_3D_INPUT_RANGE` (ffmpeg lut3d не понимает) → `color_grade.py` авто-санирует любой .cube (убирает строку во временную копию).
- Цвет — ВСЕГДА последним шагом (после монтажа, перед финальным loudnorm).
- Freesound SFX — лицензии CC пофайлово (для коммерции только CC0/CC-BY).
- Remotion — BUSL, но бесплатно до $1M ARR (наш случай). См. `video-generation/references/remotion-overlays.md`.
