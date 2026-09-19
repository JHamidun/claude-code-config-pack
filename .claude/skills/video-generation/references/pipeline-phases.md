# Фазы 3–5b: стиль, кейфреймы, генерация, аудио, сборка

Рабочие детали середины пайплайна: лок визуального стиля, правила кейфрейминга, быстрые рецепты по каждому провайдеру, режим поэтапного апрува, аудиоблок и FFmpeg-сборка. Читай ту фазу, на которой находишься; углублённые версии — `references/keyframes-multiface.md`, `references/audio.md`, `references/assembly.md`.

## Оглавление

- Phase 3 — Visual style lock
- Phase 4 — Keyframing rules
- Phase 5 — Generation, per-provider quick recipes
- Veo Fast (через Google GenAI SDK) — в рецепте ниже стоит стабильная 3.0
- Seedance через Runway JWT (default по замыслу — сейчас гейт закрыт)
- ~~Sora через OpenAI SDK~~ — продукт закрывается 24.09.2026
- HeyGen Avatar V (владелец конфига talking head)
- Ken Burns fallback (zoompan)
- Phase 5b — Staged approval mode (optional)
- 4 sub-tools вместо `enqueue_video(...)`
- Stage artefacts persistence
- Минимальная state machine
- Editing patterns
- Apply-stage tone rules
- Self-test перед approval
- Audio block
- ElevenLabs TTS — владелец конфига voice (production settings)
- ElevenLabs Music (descriptor substitution only)
- Suno — длинный оркестровый score / песня (headless)
- Lyria 2 через Vertex AI (OAuth2 service account)
- Ducking — два подхода
- FFmpeg assembly — production recipes
- Concat clips (без re-encode, 65× realtime)
- Concat anullsrc fix (КРИТИЧНО)
- Amix silent-truncation fix (КРИТИЧНО)
- XFade chain (РОВНО 2 input per xfade)
- Ken Burns zoompan (бесплатный B-roll из still'а)
- Brand-card overlay через PIL (Windows-safe, кириллица OK)
- 3-tier compression strategy

---

## Phase 3 — Visual style lock

Lock film vocabulary в КАЖДОМ prompt'е серии для visual continuity:

```
Shot on ARRI Alexa Mini, Cooke S7/i 50mm T2.0 anamorphic,
ARRI LogC to Rec.709, 35mm film grain.
Ultra-wide 21:9 cinemascope (или 9:16 для vertical).
Photorealistic, no CGI, no fantasy glow, raw and grounded.
```

Без этого Seedance даст «digital morphing» вместо «cinematic motion».

## Phase 4 — Keyframing rules

**Universal:**
- Generate keyframes отдельно (Nano Banana Pro / **`gemini-3.1-flash-image-preview`** fast-path / gpt-image-2-2026-04-21 для колоризации ЧБ **и для 3-4 реальных лиц в кадре** → `references/keyframes-multiface.md`)
- Lock ONE character через reference image, переиспользуй в ВСЕХ shot'ах серии
- Identity NOT preserved между separate generate_content calls — см. `nano-banana-pro` skill про reference-chaining
- 21:9 cinemascope — Nano Banana Pro native, GPT Image 1.5 max 3:2 (post-crop = loss)

**Auto-scale scenes под VO длительность (для VO-driven pipelines):**

Когда длительность ролика диктуется voiceover'ом (объяснялки, шортсы, посты-под-видео), считай N клипов **из** аудио, а не задавай вручную:

```python
voice_dur = audio_duration(tts_mp3)        # из ElevenLabs response или ffprobe
scenes    = max(1, int((voice_dur + 7.9) / 8))   # ceil(dur / 8) при Veo 8s clips
```

Тогда видео всегда ≥ голоса и `tpad` safety (см. `references/assembly.md` §14) не нужен. Альтернатива — фиксированное N сцен + tpad freeze-frame на разницу.

**`gemini-3.1-flash-image-preview` fast-path для keyframes:**

Когда нужны быстрые drafts/refs без Nano Banana Pro pro-grade quality (или Nano недоступен):

```python
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key={GOOGLE_API_KEY}'
payload = {
    'contents': [{'role': 'user', 'parts': [{
        'text': prompt + '. vertical portrait 9:16 composition, shorts format'
    }]}],
    'generationConfig': {'responseModalities': ['IMAGE']},
}
# Response: candidates[0].content.parts[*].inlineData.{data: base64, mimeType}
```

Грабли: aspect ratio **не отдельный параметр**, добавь хинт в текст промпта (`9:16 vertical`, `1:1 square`, `16:9 horizontal`).

**Veo (interpolation):**
- Передавай keyframe как `types.Image(image_bytes=f.read(), mime_type='image/png')` — path string silently degrades to text-only
- РАЗНЫЕ first_frame и end_frame нужны для motion

**Seedance (mutation-prone):**
- Эмпирика ниже снята на **Seedance 2.0** (Terra, май 2026). На 2.5 не переснята — считай ориентиром, а не законом.
- **Start-frame-only лучше dual-keyframe на 70-80%** (эмпирически 39 итераций Terra, ОДИН персонаж)
- **3-4 реальных лица:** лица решаются на стадии keyframe (GPT-Image-2 multi-ref), анимируй start-only + анти-дрейф-суффикс `stable consistent faces, no identity drift` + медленное движение → `keyframes-multiface.md`
- Dual-keyframe только когда end-composition mandatory ИЛИ для anti-mutation lock
- `end_frame = first_frame` LOCK → small detail changes only, без морфинга глифов
- JFIF → JPG конвертация ОБЯЗАТЕЛЬНА перед upload: `ffmpeg -y -i in.jfif out.jpg`
- API param = `end_frame`, **НЕ** `last_frame` (UI label обманывает)

Полный Seedance гайд → `references/runway-seedance.md`.

## Phase 5 — Generation, per-provider quick recipes

### Veo Fast (через Google GenAI SDK)

```python
import os
os.environ.pop('GEMINI_API_KEY', None)  # CRITICAL: ДО import
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

with open('keyframe.png', 'rb') as f:
    img_bytes = f.read()

op = client.models.generate_videos(
    model='veo-3.0-fast-generate-001',  # stable; 3.1 only as -preview ids
    prompt='Quiet pause. Solitary figure breathes. Locked tripod, 50mm anamorphic.',
    image=types.Image(image_bytes=img_bytes, mime_type='image/png'),
    config=types.GenerateVideosConfig(
        aspect_ratio='9:16',
        duration_seconds=5,
        number_of_videos=1,
    ),
)

# Poll
import time
while not op.done:
    time.sleep(10)
    op = client.operations.get(op)

video = op.response.generated_videos[0].video
client.files.download(file=video)
video.save('shot_01.mp4')
```

**Параллелизм Veo: ceiling = 3 concurrent.** 5+ = `RESOURCE_EXHAUSTED` или silent empty responses.

**Safety filter NoneType:** Veo молча возвращает NoneType (не exception) на безобидные слова. Soften-and-retry:

```python
SAFETY_SOFTENER = {
    'awkward silence': 'quiet pause',
    'tension': 'stillness',
    'lonely': 'solitary',
    'empty room': 'minimal interior',
    'shadow figure': 'silhouette',
    'dark': 'dim',
}

def soften(prompt):
    for bad, good in SAFETY_SOFTENER.items():
        prompt = prompt.replace(bad, good)
    return prompt
```

Полная Veo/Sora справка → `references/veo-direct.md`.

### Seedance через Runway JWT (default по замыслу — сейчас гейт закрыт)

> ⚠️ **Проверено 09.09.2026: дефолтный путь не работает.** `RUNWAY_JWT` истёк 31.07.2026 и лежит просроченным 40 дней — любой вызов отдаёт 401. Здесь раньше стояло просто «(default)», без оговорок, и это вводило в заблуждение: пайплайн выглядел рабочим из коробки, а на деле падал на первом же запросе.
>
> **Снять новый токен может не помочь.** 22.06.2026 подписка уже сваливалась на free plan, и Runway отказывал и в `exploreMode`, и в stable (разбор 22.06.2026). Порядок диагностики: `runway_client.py token-status` (offline-проверка срока, сеть не нужна) → **план** в `/v1/profile` → и только потом новый токен. Автоматики обновления нет нигде: только руками, `localStorage.RW_USER_TOKEN` на app.runwayml.com.

**Версия Seedance.** Сам код вызова не менялся — `generate_seedance()` теперь **сам определяет версию** через `/v1/profile/features`, хардкода версии в клиенте нет. Фон: у Seedance 2.0 появилась преемница **Seedance 2.5** (вход текст/картинка/видео/аудио, 4–30 с либо Auto, 480p/720p/1080p, до 50 референсов за генерацию = 30 картинок + 10 видео + 10 аудио, встроенный звук, четыре режима Reference / Keyframe / Edit / Extend, мультикадр из одной генерации). Снята ли 2.0 — Runway нигде не сказал, сказано только «2.5 — преемник 2.0». ⚠️ **API-слаг официальные страницы не называют вовсе** (в справке только имена нод интерфейса), поэтому не подставляй идентификатор вроде `seedance_2_5` руками — полагайся на автоопределение. Режимы, кредиты и грабли → `references/runway-seedance.md`.

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py generate \
  --prompt "The figure slowly turns. Locked camera. ARRI Alexa, 50mm anamorphic." \
  --image C:/proj/keyframes/ch1_v3.jpg \
  --duration 5 --aspect 9:16 --resolution 720p \
  --download out_ch1.mp4
```

Или из Python:

```python
import sys
sys.path.insert(0, str(Path.home() / '.claude/skills/video-generation/scripts'))
from runway_client import RunwayClient

c = RunwayClient()
task = c.generate_seedance(
    prompt='The figure slowly turns. Locked camera. ARRI Alexa, 50mm anamorphic.',
    image_path='C:/proj/keyframes/ch1_v3.jpg',
    duration=5,
    aspect_ratio='9:16',
    resolution='720p',
    wait=True,
)
url = c.list_artifacts(task)[0]
c.download(url, 'out_ch1.mp4')
```

**Параллелизм Seedance:** credits-mode до ~30 concurrent (списывает пул); `exploreMode=True` бесплатно, но троттлит ~3 — ⚠️ «бесплатно» верно только на живом ПЛАТНОМ плане: 22.06.2026 подписка сваливалась на free, и Runway отказывал и в explore, и в stable; Seedance 2.5 на free недоступна вовсе. **Кредит списывается при ОТПРАВКЕ задачи, не при скачивании**; остановка раннера не «жжёт кадры», SUCCEEDED-задачи добираются по `task_id`. Подробно (recovery, THROTTLED≠failed) → `references/runway-seedance.md` §12.

Гoтчи + 7 mutation patterns + CHARACTER blocklist → `references/runway-seedance.md`.

### ⛔ Sora через OpenAI SDK — раздела больше нет

Здесь стояло «Для RU с кириллицей на кадре» со ссылкой на `veo-direct.md` §Sora.
Ссылка вела в свою же противоположность: в §8 того файла Sora давно помечена
снятой. Тот, кто читал фазы, получал рекомендацию, которую справочник по ссылке
отменял — и это худший вид расхождения, потому что оба текста выглядят свежими.

24.09.2026 OpenAI выключает `sora-2`, `sora-2-pro`, все снапшоты и сам эндпоинт
`/v1/videos`. **Замены нет ни у кого**, и приём «Sora ради кириллицы» невыполним:
Veo её тоже корёжит. Русский текст — **оверлеем на монтаже** (PIL/drawtext),
у модели просить кадр без надписей.

### HeyGen Avatar V (владелец конфига talking head)

```python
# avatar_id=<id своего аватара из кабинета HeyGen>
# voice_id=<id своего голоса из кабинета HeyGen>
# engine=avatar_v, 9:16, 1080p, $0.0667/sec
# Готовая обвязка в `shorts-pipeline-владелец конфига` skill
```

### Ken Burns fallback (zoompan)

```bash
ffmpeg -loop 1 -i still.jpg -vf "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1080x1920,fps=25" \
  -t 5 -c:v libx264 -pix_fmt yuv420p out.mp4
```

## Phase 5b — Staged approval mode (optional)

Когда юзер хочет утверждать **до** того как pipeline сожжёт Veo-кредиты на mediocre сценах — разбей monolithic Phase 5 на 4 отдельных этапа с пер-стадийным approval.

**Когда применять:**

- Долгий cinematic trailer где storyboard критичен (4×8s × $0.10 = $3.20 на mediocre dump)
- Personal brand видео где director-style tone matters
- Заказчик хочет ревью промежуточных артефактов
- LLM-director впервые пробует тему (избегаем «ragged sofa» итераций по 5 минут)

**Когда не применять:**

- Auto-publish ленты (нет юзера которому показывать)
- Шортсы под расписание (latency важнее качества)
- Talking-head владелец конфига (HeyGen сам решает кадр)

### 4 sub-tools вместо `enqueue_video(...)`

| # | Tool | Что делает | Что вернуть юзеру |
|---|---|---|---|
| 1 | `write_voiceover_script(draft_ts, target_seconds=30, instruction?)` | LLM сжимает источник в скрипт VO ~N×2.4 слов | Текст скрипта на approval |
| 2 | `generate_storyboard(draft_ts, scenes=4, voiceover_text?, style_notes?)` | LLM-director → N visual prompts с tone rules (`director-rules.md`) | Нумерованный список сцен на approval |
| 3 | `generate_scene_references(draft_ts, prompts?)` | Параллельный fan-out `gemini-3.1-flash-image-preview` (или Nano Banana Pro) | Альбом из N картинок на approval |
| 4 | `render_final_video(draft_ts, format='shorts')` | Берёт **сохранённые артефакты**, гонит Veo+TTS+mix+caps | Финальный mp4 |

Re-run одной стадии **не дёргает остальные**. Edit storyboard через `style_notes="мягче, без человека в кадре 3"` — пересоберёт только Phase 2, картинки и видео остаются ждать.

### Stage artefacts persistence

```text
~/<workspace>/<task>/stages/<draft_ts>/
  voiceover.json     # {"text": "...", "target_sec": 30}
  storyboard.json    # {"prompts": ["...", ...], "lang": "ru"}
  references.json    # {"paths": ["abs/path1.jpg", ...]}
```

`render_final_video` читает все три JSON'а; если хоть один missing — возвращает `{"error": "missing stages: storyboard"}` без расхода credits.

### Минимальная state machine

```python
STAGES = ['voiceover', 'storyboard', 'references', 'final']

def next_stage(task_dir):
    done = {s for s in STAGES if (task_dir / f'{s}.json').exists()}
    for s in STAGES:
        if s not in done:
            return s
    return None  # all done

# В UI: если done={voiceover, storyboard} — спрашивай approval перед references
```

### Editing patterns

**Скрипт VO слишком длинный:** `write_voiceover_script(draft_ts, target_seconds=20, instruction="cut to 1 example, drop the framing")`.

**Сцена 3 не нравится:** `generate_storyboard(draft_ts, scenes=4, style_notes="третью сделай без человека вообще — только деталь крупным планом")`. Удалить старую references.json чтобы пересобрать картинки.

**Картинка 2 не нравится:** добавить tool `regenerate_reference(draft_ts, idx)` (точечный re-run). MVP — просто `generate_scene_references(prompts=[saved_prompts])` пересоберёт все.

### Apply-stage tone rules

В Stage 2 ОБЯЗАТЕЛЬНО подмешать `references/director-rules.md` §1 (anti-cliché tone) и §2 (audience cue) в director system prompt. Без этого LLM по дефолту выдаёт «угрюмый человек на рваном диване».

### Self-test перед approval

После Stage 2 прогнать lint на каждый prompt — см. `director-rules.md` §4 forbidden tokens. Если матч — re-run автоматически с `style_notes` указывающим на найденные клише.

Полная справка → `references/director-rules.md`.

## Audio block

### ElevenLabs TTS — владелец конфига voice (production settings)

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))

audio = client.text_to_speech.convert(
    voice_id=os.getenv('ELEVENLABS_VOICE_ID'),  # свой голос: id клона из кабинета ElevenLabs
    text='Сегодня разберём, как…',
    model_id='eleven_multilingual_v2',
    voice_settings={
        'stability': 0.55,
        'similarity_boost': 0.80,
        'style': 0.15,
        'use_speaker_boost': True,
    },
)

with open('vo.mp3', 'wb') as f:
    for chunk in audio:
        f.write(chunk)
```

**Эмпирика для RU:** EN voices через `eleven_multilingual_v2` на русском тексте дают тембр лучше нативных RU voices (владелец конфига shortform pattern): Matthew Villain `bwCXcoVxWNYMlC6Esa8u` (усталый/character), **George `JBFqnCBsd6RMkjVDRZzb` (тёплый рассказчик — поздравления/трибьюты)**, Brian (корпоративный). Ударение в RU — combining acute U+0301 (`што́рма`), см. `references/audio.md` §3.

Полная справка по голосам → `elevenlabs` skill.

### ElevenLabs Music (descriptor substitution only)

```python
# 30s hard cap per generation
audio = client.music.compose(
    prompt='Dark mystery cinematic underscore, low strings, sub-bass pulse, no melody',
    music_length_ms=30000,        # ← НЕ length_ms (даёт TypeError в текущем SDK)
    force_instrumental=True,       # надёжнее чем "no vocals" в тексте
    model_id='music_v1',
)
```

**Named-artist policy:** `'in the style of [Artist]'`, `'[Artist]-style vocal'`, `'sounds like [Track] by [Artist]'` → **content_policy_violation**. Только дескрипторы.

Для длиннее 30s: 2×30s сегментов с narrative handoff в prompt ("continues from dark mystery into battle"), direct concat **без crossfade** (jarring на музыке).

### Suno — длинный оркестровый score / песня (headless)

Когда нужен **60s+ score с полной драматургией** (шторм→триумф) или **песня со словами** — это Suno, а не ElevenLabs Music. Полный headless-клиент (Clerk auth, generate/download без браузера) — в **`suno` skill**. Сборочные уроки (2 дубля/запрос, CDN 403-loop, климакс-нарезка длинного трека под короткое видео) → `references/audio.md` §4b. Для трибьютов предпочтителен **инструментал Suno + ElevenLabs закадр**, статический баланс (без sidechain) — см. assembly ниже.

### Lyria 2 через Vertex AI (OAuth2 service account)

```python
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
import os, json, base64

creds = service_account.Credentials.from_service_account_file(
    os.environ['GOOGLE_SERVICE_ACCOUNT_KEY_PATH'],
    scopes=['https://www.googleapis.com/auth/cloud-platform'],
)
session = AuthorizedSession(creds)

PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT_ID']
url = (f'https://us-central1-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}'
       f'/locations/us-central1/publishers/google/models/lyria-002:predict')

# CRITICAL: seed и sample_count > 1 ВЗАИМОИСКЛЮЧАЮЩИ → 400
# Используй ОДНО из двух, не оба.
body = {
    'instances': [{
        'prompt': 'Dark mystery cinematic underscore, low strings, sub-bass pulse',
        'negative_prompt': 'vocals, lyrics',
        'sample_count': 1,
        # 'seed': 42,  # НЕЛЬЗЯ вместе с sample_count > 1
    }],
}

resp = session.post(url, json=body, timeout=300)
resp.raise_for_status()

# Output: base64 WAV, 30s, 48kHz stereo, commercial-safe
audio_b64 = resp.json()['predictions'][0]['bytesBase64Encoded']
with open('bgm.wav', 'wb') as f:
    f.write(base64.b64decode(audio_b64))
```

API key → **401 UNAUTHENTICATED**. Нужен именно service account.

Для длинного BGM: генерируй несколько 30s сэмплов и склеивай через `acrossfade`:

```bash
ffmpeg -i bgm_01.wav -i bgm_02.wav -filter_complex \
  "[0:a][1:a]acrossfade=d=1.5:c1=tri:c2=tri[out]" \
  -map "[out]" bgm_long.wav
```

### Ducking — два подхода

**Подход 1 — volume scaling (production-tested на Terra/Amber):**

```bash
ffmpeg -i music.wav -i vo.mp3 -filter_complex \
  "[0:a]volume=0.3[m];[1:a]volume=1.2[v];[m][v]amix=inputs=2:duration=first:normalize=0[out]" \
  -map "[out]" -t 60 mix.wav
```

**Подход 2 — sidechaincompress (для тонкого ducking'а):**

```bash
ffmpeg -i music.wav -i vo.mp3 -filter_complex \
  "[1:a]asplit=2[sc][v];[0:a][sc]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=350:makeup=2[m];[m][v]amix=inputs=2:normalize=0[out]" \
  -map "[out]" mix.wav
```

`normalize=0` **обязательно** — без него amix делит output на N inputs, VO утоплен в музыке.

Финальный broadcast pass:

```bash
ffmpeg -i mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11" final_audio.wav
```

## FFmpeg assembly — production recipes

### Concat clips (без re-encode, 65× realtime)

```bash
# clips.txt:
# file 'clip_01.mp4'
# file 'clip_02.mp4'

ffmpeg -f concat -safe 0 -i clips.txt -c copy concat.mp4
```

Работает только если все clips идентичны codec/resolution/fps.

### Concat anullsrc fix (КРИТИЧНО)

concat-demuxer **тихо дропает ВСЁ аудио**, если у любого клипа нет audio stream. Pre-pad silent аудио:

```bash
ffmpeg -i silent_clip.mp4 -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
  -c:v copy -c:a aac -shortest patched.mp4
```

### Amix silent-truncation fix (КРИТИЧНО)

`amix duration=longest` на самом деле обрезает по shortest. Fix:

```bash
ffmpeg -i vo.mp3 -i music.wav -filter_complex \
  "[0:a]apad[narr];[narr][1:a]amix=inputs=2:duration=first:dropout_transition=0,volume=1.2[out]" \
  -map "[out]" -t 57 mix.wav  # -t enforces target length
```

### XFade chain (РОВНО 2 input per xfade)

```bash
# 3 clips, 5s каждый, 0.4s fade
ffmpeg -i clip_01.mp4 -i clip_02.mp4 -i clip_03.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.4:offset=4.6[v01];\
   [v01][2:v]xfade=transition=fade:duration=0.4:offset=9.2[vout]" \
  -map "[vout]" out.mp4
```

`offset = clip_duration - fade_duration`. 4-й клип → ещё один шаг.

### Ken Burns zoompan (бесплатный B-roll из still'а)

```bash
ffmpeg -loop 1 -i still.jpg -vf \
  "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1080x1920,fps=25" \
  -t 5 -c:v libx264 -pix_fmt yuv420p kenburns.mp4
```

### Brand-card overlay через PIL (Windows-safe, кириллица OK)

ffmpeg `drawtext` ломается на Windows + кириллица. Рендерим текст в transparent PNG через PIL:

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 64)  # ABSOLUTE path mandatory
text = 'Ваш канал'

bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
x = (W - tw) // 2 - bbox[0]
y = (H - th) // 2 - bbox[1]

draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
img.save('overlay.png')
```

```bash
ffmpeg -i video.mp4 -i overlay.png -filter_complex \
  "[0:v][1:v]overlay=0:0:enable='between(t,0,3)'" -c:a copy branded.mp4
```

### 3-tier compression strategy

| Tier | Use | Preset | CRF | Resolution |
|---|---|---|---|---|
| Archive | Master copy | `slower` | 18 | 4K |
| Presentation | Client review | `medium` | 20 | 2.5K |
| Social | YouTube/IG/TikTok | `medium` | 22 | 1080p |

```bash
# Social tier
ffmpeg -i master.mp4 -c:v libx264 -preset medium -crf 22 \
  -vf "scale=1080:-2" -c:a aac -b:a 192k -movflags +faststart social.mp4
```

