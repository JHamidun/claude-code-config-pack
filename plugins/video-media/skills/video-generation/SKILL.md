---
name: video-generation
description: "AI-видео хаб: Veo, Sora, Seedance, Runway. Триггеры: «сгенерь видео», «оживи картинку», «оцени виральность». НЕ монтаж футажа→video-editor; промо продукта→video-shotcraft."
type: actionable
---

# Video Generation — единый хаб для AI-видео

Выбирает провайдера, держит auth, оркестрирует шесть фаз, накладывает аудио,
собирает финал. Детали по провайдерам — в `references/*.md`, чтобы не раздувать
контекст.

## Принцип экономии (главный)

Генерируем максимум через **свои** прямые API и подписки (дёшево или $0), а
bundled `hf.exe` (кредиты Higgsfield) дёргаем ТОЛЬКО для того, что напрямую
невозможно. `engines/higgsfield/scripts/router.py route(jst)` это и делает:
direct где можно, hf.exe только для эксклюзивов. Seedance доступен и через
hf.exe — но только как фолбэк, когда Runway в throttle.

## Что можно вызвать: весь конвейер, флоу или один атом

**(A) ВЕСЬ ПАЙПЛАЙН** → `scripts/run.py --brief b.json [--execute]` — см. §TURNKEY.

**(B) ФЛОУ (структурные, в `engines/higgsfield/`)** — промпт-инжиниринг их, но
генерация своими провайдерами. Полностью → `engines/higgsfield/ENGINE.md`:

| Флоу | Что | Точка входа |
|---|---|---|
| cinematic-5 | кино-нарратив (dramaturg→…→prompt-writer), мульти-клип | `prompt_builders.py` build_cinematic_5 |
| highMD/productMD/typographyMD/infographicMD/classicMD | моушн-дизайн (SANDWICH + доктрины камеры) | `prompt_builders.py sandwich --doctrine` |
| ugc / unboxing / tutorial / try-on | слот-борды, First-Word hook | ENGINE.md §UGC |
| tv-ad / podcast / cartoon | реклама / интервью / мульт | ENGINE.md + `subagents-*.md` |

**(C) АТОМЫ (вызываются по отдельности)**:

| Атом | Команда |
|---|---|
| keyframes (свои ключи) | `scripts/nano_banana_keyframes.py shots.json --out DIR` |
| промпт-кухня | `engines/higgsfield/scripts/prompt_builders.py {cinematic\|sandwich\|board}` |
| роутинг провайдера | `engines/higgsfield/scripts/router.py route <jst>` (direct vs hf) |
| клип i2v | `scripts/veo_image_to_video.py` · `scripts/runway_client.py generate` (Seedance/Kling $0) |
| озвучка / музыка | `scripts/elevenlabs_voiceover.py` · `scripts/lyria_music.py` / `elevenlabs_music.py` |
| сборка (атомы) | `engines/higgsfield/scripts/assemble.py {concat\|xfade_chain\|color_lut\|ken_burns\|burn_ass\|reframe_blurred_bg\|platform_export\|audio_duck\|whisper_srt}` |
| сборка (пайплайн VO+муз+brand) | `scripts/ffmpeg_assemble.py manifest.json --out final.mp4` |
| моушн-графика / соц-оверлеи | `scripts/motion_graphics.py` · `remotion-overlays/` |

**(D) HF-ЭКСКЛЮЗИВЫ** — единственное, чего нет напрямую; только через
`engines/higgsfield/bin/hf.exe`:

| Эксклюзив | Команда |
|---|---|
| Soul face-lock (рекуррентный AI-ведущий) | `hf soul-id create --soul-2 --image <id×5>` → `generate create text2image_soul_v2 --soul-id <ref>` |
| Virality Predictor (оценка хука) | `hf generate create brain_activity --video <≤16с>` |
| Marketing Studio / DTC (реклама с аватаром+товаром) | `hf marketing-studio {avatars,products,hooks} list` → `generate create marketing_studio_video` |
| reframe (AI-outpaint видео в новый аспект) | `hf generate create reframe --aspect_ratio 16:9 --video <id>` |

**Не дублировать соседние скиллы:** настоящий lip-sync talking-head →
`heygen` (дополняет Soul, а не заменяется им); чистый монтаж → `video-editor`;
рилс из снятого видео блогера с AI-врезками ПОВЕРХ (creator — основа) →
`video-editor` `references/talking-head-broll-reel.md`; TTS без видео →
`elevenlabs`; картинка → `nano-banana-pro`; удалить объект из готового видео →
`void-video`; скачать чужое → `video-downloader`.

**Отклонено (2026-07-20):** inference.sh `belt` CLI — агрегатор 40+ видеомоделей.
Seedance и Veo уже здесь напрямую ($0 marginal), Wan достаётся через `replicate`.
Нового доступа к моделям ноль, а цена — второй платный аккаунт и `curl | sh`.

## TURNKEY — одна команда под ключ (`scripts/run.py`)

Даёшь бриф — оркестратор гонит весь пайплайн (intake → flow → промпт → route
DIRECT-first → параллельный fan-out keyframes+clips → аудио → ffmpeg →
платформенный экспорт) с **approval-гейтом перед дорогой стадией клипов**.

```bash
# DRY-RUN (по умолчанию — строит ПЛАН, ничего не тратит, пишет out/plan.json):
python scripts/run.py --flow cinematic --story "сюжет" --aspect 21:9 --platform youtube --duration 24
python scripts/run.py --brief brief.json            # полный бриф
# ЗАПУСК (keyframes → GATE → clips → audio → assemble; --yes снять гейт):
python scripts/run.py --brief brief.json --execute
```

Бриф (JSON): `{flow, brief, aspect, platform, duration, palette[], voiceover_text,
voice, music_prompt, scenes[], out_dir}`. flow ∈ cinematic / highMD / productMD /
typographyMD / infographicMD / classicMD / simple. Для сложного и творческого
оркеструй фазы сам.

### Battle-notes (заработано боем)

- **Текст и числа в хуке → PIL-оверлей + Ken Burns, НЕ image-моделью и НЕ i2v.**
  Nano/Veo гарбят цифры; крупное «$10 000 000» компонуй PIL (arialbd) на
  затемнённый фон → `ken_burns` (без AI-морфа текст остаётся чётким). Виральный
  хук всегда = число или имя крупно в первую секунду.
- **Runway 429 throttle — account-level, даже при sequential** → фолбэк на Veo
  (свой `GOOGLE_API_KEY`). Архитектура фолбэка реально спасает.
- **Veo ID:** рабочий `veo-3.0-fast-generate-001` (stable). 3.1 ТОЛЬКО как
  `veo-3.1-*-preview` (НЕ `-001`). `--duration` ∈ {4,6,8} (не 5). 9:16 = 720×1280
  (concat нормализует до 1080×1920).
- **brain_activity (virality) ≤16 секунд** — финал для проверки режь ≤15.5 с.
- **Git Bash `$PWD` = POSIX `/c/...`**, ffmpeg на Windows такой путь не откроет →
  в манифестах всегда `C:/...`.
- Цикл полировки: сделал → **контактка (ffmpeg tile) → смотреть глазами** →
  диагноз → фикс скрипта → пересобрать → virality-замер. Так hook 27 → 33.

## Provider selection — decision tree

| Задача | Провайдер | Почему | Цена |
|---|---|---|---|
| Default «просто оживи» | **Seedance 2.0** через Runway JWT | Flat 180 credits = $0 marginal на Unlimited; лучший motion из i2v | $0 (Unlimited) |
| Кириллический текст на кадре | **Sora** (OpenAI SDK) | Veo корёжит кириллицу в «иероглифы», Sora держит | ~$0.08/s |
| Cinematic 21:9 trailer с native аудио | **Veo 3.1 Full** | Native audio + 4K-grade composition | $0.40/s |
| Быстрый 5-секундный motion для соцсетей | **Veo 3.1 Fast** | Дешевле Full в 4×, для шортсов достаточно | $0.10/s |
| Image-to-video с lock'ом face/glyph | **Seedance + end_frame=first_frame** | Интерполяция между идентичными кадрами = только мелкие изменения | $0 |
| Talking head | **HeyGen Avatar V** (`heygen` skill) | Готовый avatar_id + voice_id, lip-sync из коробки | $0.0667/s |
| B-roll из готовой картинки без AI | **Ken Burns zoompan** (ffmpeg) | Бесплатно, мгновенно | $0 |
| Multi-shot cinematic narrative | **Seedance i2v + Nano Banana Pro keyframes** | Lock персонажа через reference image (1-2 лица) | $0 |
| 3-4 РЕАЛЬНЫХ лица в одном кадре | **GPT-Image-2 multi-ref → Seedance** | Nano держит 1-2, плывёт на 3-4; `/v1/images/edits` мультиреференс точнее → `references/keyframes-multiface.md` | $0 |
| Брендкит / UI-only без API | **Playwright MCP browser fallback** | `references/runway-seedance.md` §8 | $0 |

Конфликт keyframing'а решён явно: **Veo/Sora** интерполируют motion → нужны
РАЗНЫЕ first/end frame; **Seedance** мутирует мелкие детали → `end_frame=first_frame`
LOCK даёт anti-mutation для татуировок, глифов, лиц.

## Auth & credentials

Всё в `~/.claude/.credentials.master.env`:

| Переменная | Для чего |
|---|---|
| `GOOGLE_API_KEY` | Veo 3.1 (google-genai SDK) |
| `GEMINI_API_KEY` | **КОНФЛИКТ** с GOOGLE_API_KEY. `os.environ.pop('GEMINI_API_KEY', None)` ПЕРЕД `import genai` |
| `GOOGLE_CLOUD_PROJECT_ID` | Lyria 2 через Vertex AI |
| `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` | Абсолютный путь к service-account JSON для Lyria (НЕ конфликтует с GOOGLE_API_KEY) |
| `RUNWAY_TOKEN_PLACEHOLDER` | Runway internal API. **30 дней TTL**. Refresh: app.runwayml.com → DevTools → Application → localStorage → `RW_TOKEN_PLACEHOLDER` |
| `RUNWAY_TEAM_ID` | `?asTeamId=<id>` для большинства эндпоинтов |
| `ELEVENLABS_API_KEY` | TTS + Music |
| `OPENAI_API_KEY` | Sora через OpenAI SDK |
| `HEYGEN_API_KEY` | Avatar V (через `heygen` skill) |
| `SUBMAGIC_API_KEY` | EN-субтитры (`x-api-key: sk-...`, НЕ Bearer) |

Проверка JWT (день 31 = 401):

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py profile
```

## Pipeline — 6 фаз

```
1. Intake          → бриф, длительность, аспект, платформа, бюджет, голос
2. Storyboard      → текстовый сценарий по shot'ам, длительность каждого
3. Visual style    → lock film vocabulary, generate keyframes
4. Clip planning   → выбор провайдера на каждый shot, prompts с motion+camera
5. Generation      → parallel fan-out (Veo×3 / Seedance batch / TTS / Music)
6. Assembly        → ffmpeg concat+xfade, amix+ducking, loudnorm, compression tier
```

Готовые шаблоны роликов (буктрейлер, cinematic-серия, соцшортс, оживление
иллюстрации) и реальные тайминги/бюджеты проектов → `references/workflow-templates.md`.

## Phase 3 — Visual style lock

Одну и ту же плёночную формулу вписывать в КАЖДЫЙ промпт серии — без неё Seedance
даёт «digital morphing» вместо кино, и кадры серии не склеиваются между собой:

```
Shot on ARRI Alexa Mini, Cooke S7/i 50mm T2.0 anamorphic,
ARRI LogC to Rec.709, 35mm film grain.
Ultra-wide 21:9 cinemascope (или 9:16 для vertical).
Photorealistic, no CGI, no fantasy glow, raw and grounded.
```

## Phase 4 — Keyframing rules

**Universal:**

- Keyframes генерь отдельно: Nano Banana Pro / `gemini-3.1-flash-image-preview`
  (fast-path) / gpt-image-2-2026-04-21 (колоризация ЧБ **и** 3-4 реальных лица →
  `references/keyframes-multiface.md`).
- Lock ONE character через reference image и переиспользуй во ВСЕХ shot'ах серии.
  Identity НЕ сохраняется между отдельными вызовами generate_content — про
  reference-chaining см. `nano-banana-pro`.
- 21:9 cinemascope — Nano Banana Pro native; GPT Image 1.5 максимум 3:2, пост-кроп
  = потеря кадра.

**Auto-scale сцен под длительность VO.** Когда хронометраж диктует озвучка,
считай число клипов ИЗ аудио, а не задавай вручную — тогда видео всегда ≥ голоса
и `tpad`-заплатка (`references/assembly.md` §14) не нужна:

```python
voice_dur = audio_duration(tts_mp3)              # ElevenLabs response или ffprobe
scenes    = max(1, int((voice_dur + 7.9) / 8))   # ceil(dur / 8) при Veo 8s clips
```

**Fast-path `gemini-3.1-flash-image-preview`** (быстрые драфты, когда Nano
недоступен): `POST https://generativelanguage.googleapis.com/v1beta/models/
gemini-3.1-flash-image-preview:generateContent?key=$GOOGLE_API_KEY`,
`generationConfig.responseModalities=['IMAGE']`, ответ в
`candidates[0].content.parts[*].inlineData.{data:base64, mimeType}`.
Грабли: **аспект не отдельный параметр** — хинт идёт словами в текст промпта
(`9:16 vertical`, `1:1 square`).

**Veo / Sora (интерполяция):** keyframe передавать как
`types.Image(image_bytes=f.read(), mime_type='image/png')` — строка-путь молча
деградирует в text-only; для motion нужны РАЗНЫЕ first_frame и end_frame.

**Seedance (склонен мутировать):**

- **Start-frame-only лучше dual-keyframe на 70-80%** (эмпирика: 39 итераций, один персонаж).
- 3-4 реальных лица решаются на стадии keyframe (GPT-Image-2 multi-ref), анимация
  start-only + суффикс `stable consistent faces, no identity drift` + медленное движение.
- Dual-keyframe только когда end-композиция обязательна ИЛИ для anti-mutation lock.
- JFIF → JPG перед upload обязательно: `ffmpeg -y -i in.jfif out.jpg`.
- Параметр API = `end_frame`, **НЕ** `last_frame` — подпись в UI обманывает.

Полный Seedance-гайд (7 mutation patterns, CHARACTER blocklist) →
`references/runway-seedance.md`.

## Phase 5 — рецепты по провайдерам

### Veo 3.1 Fast (Google GenAI SDK)

```python
import os
os.environ.pop('GEMINI_API_KEY', None)  # CRITICAL: ДО import
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
op = client.models.generate_videos(
    model='veo-3.0-fast-generate-001',   # stable; 3.1 только как -preview
    prompt='Quiet pause. Solitary figure breathes. Locked tripod, 50mm anamorphic.',
    image=types.Image(image_bytes=open('keyframe.png','rb').read(), mime_type='image/png'),
    config=types.GenerateVideosConfig(aspect_ratio='9:16', duration_seconds=5, number_of_videos=1),
)
while not op.done:                        # поллинг обязателен, ответ асинхронный
    time.sleep(10); op = client.operations.get(op)
video = op.response.generated_videos[0].video
client.files.download(file=video); video.save('shot_01.mp4')
```

**Параллелизм Veo: потолок 3 concurrent.** 5+ → `RESOURCE_EXHAUSTED` или молча
пустые ответы.

**Safety filter возвращает NoneType, а не исключение** — и срабатывает на
безобидных словах. Прогоняй промпт через замену до отправки:

```python
SAFETY_SOFTENER = {'awkward silence': 'quiet pause', 'tension': 'stillness',
                   'lonely': 'solitary', 'empty room': 'minimal interior',
                   'shadow figure': 'silhouette', 'dark': 'dim'}
```

Полная Veo/Sora справка → `references/veo-direct.md`. Sora берём для RU с
кириллицей на кадре (там же §Sora).

### Seedance через Runway JWT (default)

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py generate \
  --prompt "The figure slowly turns. Locked camera. ARRI Alexa, 50mm anamorphic." \
  --image C:/proj/keyframes/ch1_v3.jpg \
  --duration 5 --aspect 9:16 --resolution 720p \
  --download out_ch1.mp4
```

Из Python — тот же класс: `sys.path.insert(0, str(Path.home()/'.claude/skills/
video-generation/scripts'))`, `from runway_client import RunwayClient`,
`c.generate_seedance(..., wait=True)` → `c.list_artifacts(task)[0]` → `c.download(...)`.

**Параллелизм Seedance:** credits-mode до ~30 concurrent; `exploreMode=True`
бесплатно, но троттлит ~3. **Кредит списывается при ОТПРАВКЕ задачи, не при
скачивании** — остановка раннера не «жжёт кадры», SUCCEEDED-задачи добираются по
`task_id`. Recovery и «THROTTLED ≠ failed» → `references/runway-seedance.md` §12.

### HeyGen Avatar V

`engine=avatar_v`, 9:16, 1080p, $0.0667/сек; avatar_id + voice_id берутся из
своей учётки. Готовая обвязка — в скилле `heygen`.

## Phase 5b — постадийное утверждение (опционально)

Разбивает монолитную фазу 5 на четыре стадии с approval после каждой — чтобы
пайплайн не сжёг Veo-кредиты на посредственных сценах (4×8s × $0.10 = $3.20 за
один неудачный дубль).

**Когда:** длинный cinematic, где важна раскадровка; персональный бренд, где
важен тон; заказчик хочет ревью промежуточного. **Когда нет:** автопубликация без
человека; шортсы по расписанию (latency важнее); talking-head (HeyGen сам решает кадр).

| # | Стадия | Что делает | Что показать на approval |
|---|---|---|---|
| 1 | `write_voiceover_script(draft_ts, target_seconds=30)` | сжимает источник в VO ~N×2.4 слов | текст скрипта |
| 2 | `generate_storyboard(draft_ts, scenes=4, style_notes?)` | LLM-режиссёр → N визуальных промптов | нумерованный список сцен |
| 3 | `generate_scene_references(draft_ts, prompts?)` | fan-out `gemini-3.1-flash-image-preview` | альбом из N картинок |
| 4 | `render_final_video(draft_ts, format='shorts')` | берёт СОХРАНЁННЫЕ артефакты → Veo+TTS+mix+caps | финальный mp4 |

Артефакты лежат в `<task>/stages/<draft_ts>/{voiceover,storyboard,references}.json`;
`render_final_video` читает все три и при нехватке возвращает
`{"error": "missing stages: storyboard"}` **не тратя кредиты**. Перезапуск одной
стадии не дёргает остальные: правка через `style_notes="третью сцену без человека
в кадре"` пересоберёт только раскадровку, картинки и видео останутся ждать (чтобы
пересобрать и картинки — удалить `references.json`).

В стадии 2 ОБЯЗАТЕЛЬНО подмешивать `references/director-rules.md` §1 (anti-cliché)
и §2 (audience cue) в промпт режиссёра — без этого LLM по умолчанию выдаёт
«угрюмого человека на рваном диване». После стадии 2 прогнать промпты через lint
на forbidden tokens (§4 там же) и при матче перезапустить со `style_notes`.

## Audio

### ElevenLabs TTS

```python
audio = client.text_to_speech.convert(
    voice_id='<your_voice_id>', text='Сегодня разберём, как…',
    model_id='eleven_multilingual_v2',
    voice_settings={'stability': 0.55, 'similarity_boost': 0.80,
                    'style': 0.15, 'use_speaker_boost': True},
)
```

**Эмпирика для RU:** EN-голоса через `eleven_multilingual_v2` на русском тексте
дают тембр лучше нативных RU-голосов. George `JBFqnCBsd6RMkjVDRZzb` — тёплый
рассказчик (поздравления, трибьюты); Matthew Villain `bwCXcoVxWNYMlC6Esa8u` —
усталый/характерный. Ударение в RU — combining acute U+0301 (`што́рма`),
`references/audio.md` §3. Голоса целиком → скилл `elevenlabs`.

### ElevenLabs Music

```python
audio = client.music.compose(
    prompt='Dark mystery cinematic underscore, low strings, sub-bass pulse, no melody',
    music_length_ms=30000,      # ← НЕ length_ms (TypeError в текущем SDK)
    force_instrumental=True,    # надёжнее, чем «no vocals» в тексте
    model_id='music_v1',
)
```

30 секунд — жёсткий потолок на генерацию. Длиннее: два отрезка по 30 с с
narrative handoff в промпте («continues from dark mystery into battle») и
**прямой concat без crossfade** — на музыке кроссфейд слышен как склейка.

**Named-artist policy:** `'in the style of [Artist]'`, `'sounds like [Track] by
[Artist]'` → `content_policy_violation`. Только дескрипторы.

### Suno — длинный score или песня

60 c+ с полной драматургией (шторм→триумф) или песня со словами — это Suno, а не
ElevenLabs Music или локальный `ace-step`; сборочные уроки (2 дубля на
запрос, CDN 403-loop, климакс-нарезка) → `references/audio.md` §4b.

### Lyria 2 (Vertex AI)

Только service account: API key → **401 UNAUTHENTICATED**.

```python
creds = service_account.Credentials.from_service_account_file(
    os.environ['GOOGLE_SERVICE_ACCOUNT_KEY_PATH'],
    scopes=['https://www.googleapis.com/auth/cloud-platform'])
session = AuthorizedSession(creds)
url = (f'https://us-central1-aiplatform.googleapis.com/v1/projects/'
       f'{os.environ["GOOGLE_CLOUD_PROJECT_ID"]}/locations/us-central1'
       f'/publishers/google/models/lyria-002:predict')
body = {'instances': [{'prompt': '...', 'negative_prompt': 'vocals, lyrics',
                       'sample_count': 1}]}   # seed и sample_count>1 ВЗАИМОИСКЛЮЧАЮЩИ → 400
audio = base64.b64decode(session.post(url, json=body, timeout=300)
                         .json()['predictions'][0]['bytesBase64Encoded'])
```

Выход: base64 WAV, 30 с, 48 kHz stereo, commercial-safe. Длинный BGM — несколько
сэмплов через `acrossfade=d=1.5:c1=tri:c2=tri`.

### Ducking и финальный уровень

```bash
# простой: масштабирование громкостей (проверено в проде)
ffmpeg -i music.wav -i vo.mp3 -filter_complex \
  "[0:a]volume=0.3[m];[1:a]volume=1.2[v];[m][v]amix=inputs=2:duration=first:normalize=0[out]" \
  -map "[out]" -t 60 mix.wav

# тонкий: sidechain — музыка приседает под голосом
ffmpeg -i music.wav -i vo.mp3 -filter_complex \
  "[1:a]asplit=2[sc][v];[0:a][sc]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=350:makeup=2[m];[m][v]amix=inputs=2:normalize=0[out]" \
  -map "[out]" mix.wav

ffmpeg -i mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11" final_audio.wav
```

`normalize=0` **обязательно**: без него amix делит выход на число входов и голос
тонет в музыке.

## FFmpeg assembly

```bash
# concat без re-encode (~65× realtime) — только если все клипы идентичны по кодеку/размеру/fps
ffmpeg -f concat -safe 0 -i clips.txt -c copy concat.mp4     # строки: file 'clip_01.mp4'
```

**Concat молча дропает ВСЁ аудио**, если хоть у одного клипа нет audio-дорожки.
Заранее подшить тишину:

```bash
ffmpeg -i silent_clip.mp4 -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -c:v copy -c:a aac -shortest patched.mp4
```

**`amix duration=longest` на деле обрезает по shortest.** Лечится apad + явным `-t`:

```bash
ffmpeg -i vo.mp3 -i music.wav -filter_complex \
  "[0:a]apad[narr];[narr][1:a]amix=inputs=2:duration=first:dropout_transition=0,volume=1.2[out]" \
  -map "[out]" -t 57 mix.wav
```

**xfade принимает РОВНО 2 входа** — цепочка строится по шагам,
`offset = clip_duration - fade_duration`:

```bash
ffmpeg -i clip_01.mp4 -i clip_02.mp4 -i clip_03.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.4:offset=4.6[v01];\
   [v01][2:v]xfade=transition=fade:duration=0.4:offset=9.2[vout]" \
  -map "[vout]" out.mp4
```

**Ken Burns из статичной картинки** (бесплатный B-roll):

```bash
ffmpeg -loop 1 -i still.jpg -vf "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1080x1920,fps=25" \
  -t 5 -c:v libx264 -pix_fmt yuv420p kenburns.mp4
```

**Титры и брендкарты — через PIL, не drawtext:** ffmpeg `drawtext` на Windows
ломается о кириллицу. Рендерим текст в прозрачный PNG (`ImageFont.truetype` с
АБСОЛЮТНЫМ путём вроде `C:/Windows/Fonts/arial.ttf`), центруем по `draw.textbbox`
с вычитанием `bbox[0]`/`bbox[1]` (без этого текст уезжает на величину внутреннего
отступа глифа), и накладываем:

```bash
ffmpeg -i video.mp4 -i overlay.png -filter_complex \
  "[0:v][1:v]overlay=0:0:enable='between(t,0,3)'" -c:a copy branded.mp4
```

**Три уровня компрессии:**

| Tier | Назначение | Preset | CRF | Размер |
|---|---|---|---|---|
| Archive | мастер-копия | `slower` | 18 | 4K |
| Presentation | ревью клиентом | `medium` | 20 | 2.5K |
| Social | YouTube/IG/TikTok | `medium` | 22 | 1080p + `-movflags +faststart` |

## Known gotchas — master table

| # | Gotcha | Provider | Где детали |
|---|---|---|---|
| 1 | `GEMINI_API_KEY` env conflict — pop ДО import | Veo | `references/veo-direct.md` |
| 2 | Veo safety filter возвращает NoneType, не exception | Veo | `references/veo-direct.md` |
| 3 | Veo `types.Image(image_bytes=..., mime_type=...)` — path string silently degrades | Veo | `references/veo-direct.md` |
| 4 | Veo concurrent ceiling = 3, 5+ = RESOURCE_EXHAUSTED | Veo | `references/veo-direct.md` |
| 5 | Veo всегда генерит native audio — `-an` strip для внешнего VO | Veo | `references/veo-direct.md` |
| 6 | Sora > Veo для кириллицы на кадре | Sora | `references/veo-direct.md` |
| 7 | Seedance CHARACTER moderation: girl/woman/девочка/имена → 400 | Seedance | `references/runway-seedance.md` |
| 8 | Seedance `end_frame=first_frame` LOCK = anti-mutation | Seedance | `references/runway-seedance.md` |
| 9 | API param = `end_frame`, UI label = `last frame` — НЕ путать | Runway | `references/runway-seedance.md` |
| 10 | textPrompt hard cap 3500 chars | Runway | `references/runway-seedance.md` |
| 11 | JFIF → JPG/PNG конвертация обязательна перед upload | Runway | `references/runway-seedance.md` |
| 12 | Runway JWT 30-day TTL, day 31 = 401 | Runway | `references/runway-seedance.md` |
| 13 | Mandatory headers: creationSource, numGenerations, X-Runway-Workspace | Runway | `references/runway-seedance.md` |
| 14 | Start-frame-only 70-80% better motion (Seedance эмпирически) | Seedance | `references/runway-seedance.md` |
| 15 | ONE action ONE camera per prompt | Seedance | `references/runway-seedance.md` |
| 16 | Не повторять описание персонажа в i2v prompt — морфит face | Seedance | `references/runway-seedance.md` |
| 17 | Unlimited subscription credits ≠ API billing pool | Runway | `references/runway-seedance.md` |
| 18 | Nano Banana identity NOT preserved между calls — reference-chain | Image | `nano-banana-pro` skill |
| 19 | Lyria 2 — service account ONLY, API key = 401 | Audio | `references/audio.md` |
| 20 | Lyria 2: seed и sample_count>1 взаимоисключающи | Audio | `references/audio.md` |
| 21 | Lyria 2 — 30s WAV per sample, длинные через acrossfade | Audio | `references/audio.md` |
| 22 | ElevenLabs Music 30s hard cap | Audio | `references/audio.md` |
| 23 | ElevenLabs Music named-artist → content_policy_violation | Audio | `references/audio.md` |
| 24 | ffmpeg `amix duration=longest` обрезает по SHORTEST — apad + -t | FFmpeg | `references/assembly.md` |
| 25 | ffmpeg concat дропает ВСЁ аудио если один клип без audio — anullsrc | FFmpeg | `references/assembly.md` |
| 26 | ffmpeg `amix normalize=0` обязательно | FFmpeg | `references/assembly.md` |
| 27 | ffmpeg xfade принимает РОВНО 2 input | FFmpeg | `references/assembly.md` |
| 28 | Windows subprocess: `encoding='utf-8', errors='replace'` | Windows | `references/windows.md` |
| 29 | Windows ffmpeg drawtext + кириллица = крах, workaround через PIL | Windows | `references/windows.md` |
| 30 | Облачный диск: multipart upload = 0-byte file, нужен raw PUT | Delivery | `references/windows.md` |
| 31 | SubMagic «пайвот» → 🍺 на RU, обязательная trigger-word чистка | Captions | `submagic` skill |
| 32 | Playwright MCP clipboard = `navigator.clipboard.writeText()` | Browser | `references/windows.md` |
| 33 | ElevenLabs Music param = `music_length_ms` + `force_instrumental=True` + `model_id='music_v1'` (НЕ `length_ms` → TypeError) | Audio | `references/audio.md` §2 |
| 34 | Runway кредит списывается при ОТПРАВКЕ, не скачивании; стоп раннера не «жжёт кадры»; SUCCEEDED добирается по task_id | Runway | `references/runway-seedance.md` §12 |
| 35 | НЕ останавливать чужую идущую генерацию без спроса; НЕ resubmit на client-timeout (THROTTLED≠failed) | Runway | `references/runway-seedance.md` §12 |
| 36 | Nano держит 1-2 лица, плывёт на 3-4 → GPT-Image-2 multi-ref для ансамбля; итеративно + вето | Image | `references/keyframes-multiface.md` |
| 37 | Контактный лист для vision-ревью ≤ 2000px шириной (иначе read падает) | Image | `references/keyframes-multiface.md` |
| 38 | RU TTS ударение через combining acute U+0301; print такой строки падает на cp1251 | Audio/Win | `references/audio.md` §3 |
| 39 | Glyph-pulse trap: «pulsing sigil» → bloom в диск/медальон; форму держит только STEADY glow или post-composite | Seedance | `references/runway-seedance.md` §4 #1 |
| 40 | Брошенный/переданный объект левитирует и дрейфует; end_frame диктует resolved state → дай keyframe «объект уже в руках» | Seedance | `references/runway-seedance.md` §4 #8 + §5 |

## Reference files (lazy-loaded)

- `engines/higgsfield/ENGINE.md` — движок Higgsfield: 6-фаз оркестрация, 11 флоу,
  hf.exe CLI, `scripts/{prompt_builders,router,assemble}.py`, registries с реальными UUID
- `references/higgsfield-flows.md` — выжимка техник Higgsfield, вшитых в наши фазы
- `references/runway-seedance.md` — Runway JWT API + Seedance prompt engineering + browser fallback
- `references/veo-direct.md` — Veo 3.1 Fast/Full + Sora через OpenAI SDK
- `references/audio.md` — Lyria 2 OAuth + ElevenLabs Music/TTS + Suno climax-cut + RU ударения
- `references/keyframes-multiface.md` — несколько РЕАЛЬНЫХ лиц в кадре
- `references/director-rules.md` — anti-cliché тон, audience cue, forbidden tokens
- `references/workflow-templates.md` — шаблоны роликов + реальные тайминги и бюджеты
- `references/color-grading.md` — LUT (Kodak 2383), teal-orange, film look, hald CLUT
- `references/remotion-overlays.md` — соц-UI оверлеи React→alpha webm→composite
- `references/motion-graphics.md` — три уровня: ffmpeg / movis / Manim
- `references/assembly.md` — FFmpeg cookbook целиком
- `references/windows.md` — Windows-специфика (subprocess encoding, PIL paths, кириллические пути)
- `references/case-studies.md` — verbatim-конфиги прошлых проектов
- `references/i2v-cost-lipsync-notes.md` — стоимость i2v и заметки по lip-sync

## Scripts

`run.py` (оркестратор под ключ) · `runway_client.py` (класс RunwayClient) ·
`runway_mcp.py` (MCP-обёртка, 8 runway_* tools) · `veo_runner.py`,
`veo_image_to_video.py`, `direct_video.py` · `nano_banana_keyframes.py` ·
`elevenlabs_voiceover.py`, `elevenlabs_music.py`, `lyria_music.py` ·
`ffmpeg_assemble.py`, `motion_graphics.py`, `captions_ass.py`, `broll_runner.py` ·
`climax_cut.py` (климакс-нарезка длинного аудио под короткий ролик) ·
`extract_chat_session.py` (добыча знаний из прошлых JSONL-сессий по topic-regex).
