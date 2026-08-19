---
name: video-generation
description: "AI-видео хаб: Veo, Sora, Seedance, Runway, Higgsfield. Триггеры: «сгенерь видео», «оживи картинку», «оцени виральность». НЕ монтаж футажа→video-editor."
type: actionable
---

# Video Generation — единый хаб для AI-видео

Хаб, который выбирает провайдер, держит auth, оркестрирует шесть фаз, накладывает аудио, собирает финал. Детали по провайдерам — в `references/*.md`, чтобы не раздувать контекст.

## CAPABILITY MAP — что умеет скилл (вызывай ЧАСТЬ или ВЕСЬ пайплайн)

> Три уровня вызова: **(A) весь пайплайн под ключ** · **(B) отдельный флоу** · **(C) отдельный атом/инструмент**. Экономия: всё через свои API; `hf.exe` — только для эксклюзивов (D).

**(A) ВЕСЬ ПАЙПЛАЙН — одна команда** → `scripts/run.py --brief b.json [--execute]` (intake→flow→промпт→route→keyframes+clips→audio→сборка→экспорт; approval-гейт; `--dry-run` по умолчанию). См. §TURNKEY.

**(B) ФЛОУ (структурные, в `engines/higgsfield/`)** — `ENGINE.md`:
| Флоу | Что | Точка входа |
|---|---|---|
| cinematic-5 | кино-нарратив (dramaturg→…→prompt-writer), мульти-клип | `prompt_builders.py` build_cinematic_5 |
| highMD/productMD/typographyMD/infographicMD/classicMD | моушн-дизайн (SANDWICH + доктрины камеры) | `prompt_builders.py sandwich --doctrine` |
| ugc / unboxing / tutorial / try-on | слот-борды, First-Word hook | ENGINE.md §UGC |
| tv-ad / podcast / cartoon | реклама / интервью / мульт | ENGINE.md + `subagents-*.md` |

**(C) АТОМЫ (вызываются по отдельности)**:
| Атом | Команда |
|---|---|
| keyframes (свои ключи) | `scripts/nano_banana_keyframes.py shots.json --out DIR` (Nano) |
| промпт-кухня | `engines/higgsfield/scripts/prompt_builders.py {cinematic\|sandwich\|board}` |
| роутинг провайдера | `engines/higgsfield/scripts/router.py route <jst>` (direct vs hf) |
| клип i2v | `scripts/veo_image_to_video.py` (Veo) · `scripts/runway_client.py generate` (Seedance/Kling $0) |
| озвучка / музыка | `scripts/elevenlabs_voiceover.py` · `scripts/lyria_music.py` / `elevenlabs_music.py` |
| сборка (атомы) | `engines/higgsfield/scripts/assemble.py {concat\|xfade_chain\|color_lut\|ken_burns\|burn_ass\|reframe_blurred_bg\|platform_export\|audio_duck\|whisper_srt}` |
| сборка (пайплайн VO+муз+brand) | `scripts/ffmpeg_assemble.py manifest.json --out final.mp4` |
| моушн-графика / соц-оверлеи | `scripts/motion_graphics.py` · `remotion-overlays/` |

**(D) HF-ЭКСКЛЮЗИВЫ (только `hf.exe`, через `engines/higgsfield/bin/hf.exe`)**:
| Эксклюзив | Команда |
|---|---|
| Soul face-lock (рекуррентный AI-ведущий) | `hf soul-id create --soul-2 --image <id×5>` → `generate create text2image_soul_v2 --soul-id <ref>` |
| Virality Predictor (оценка хука) | `hf generate create brain_activity --video <≤16с>` |
| Marketing Studio / DTC (реклама с аватаром+товаром) | `hf marketing-studio {avatars,products,hooks} list` → `generate create marketing_studio_video` |
| reframe (AI-outpaint видео в новый аспект) | `hf generate create reframe --aspect_ratio 16:9 --video <id>` |

**(E) СОСЕДНИЕ СКИЛЛЫ (не дублировать):** talking-head с НАСТОЯЩИМ lip-sync → **`heygen`** (Avatar V/IV, 175 langs translate, lipsync — отдельный скилл, дополняет Soul); чистый монтаж → `video-editor`; **рилс из снятого видео блогера + AI-врезки ПОВЕРХ** (creator = основа, AI поверх, не full-AI) → `video-editor` `skills/video-editor/references/talking-head-broll-reel.md`; TTS без видео → `elevenlabs`; картинка → `nano-banana-pro`.

**Rejected (2026-07-20):** inference.sh `belt` CLI (github.com/inference-sh/skills, 628★) — aggregator for 40+ video models incl. Seedance/Wan/Veo. Seedance and Veo are already direct here ($0 marginal via Runway Unlimited / own GOOGLE_API_KEY); Wan is already reachable via `replicate` skill (`wan-video/wan-2.2-*`). Zero net-new model access, second paywalled account + `curl | sh` installer — not adopted.

## Когда использовать

Срабатывает на любую фразу про видео:
- "сгенерь видео / ролик / шортс / reels / TikTok / YouTube Short"
- "оживи картинку / image-to-video / animated illustration"
- "буктрейлер / cinematic trailer / living book cover"
- "Veo / Sora / Seedance / Runway / Kling / Pika"
- "vertical / 9:16 / 21:9 / cinemascope / square"

Когда НЕ использовать:
- Чистый text-to-speech без видео → `elevenlabs`
- Чистая генерация картинки → `nano-banana-pro` / `image-generation`
- Talking-head шортсы пользователя под YouTube → `shorts-pipeline-user` (готовая обвязка Avatar V + SubMagic + триггер-чек)
- Чистый монтаж готовых клипов (без AI-генерации) → `video-editor`
- Удалить объект из существующего видео → `void-video`
- Скачать чужое видео → `video-downloader`

## ROUTING-MAP — какую часть хаба грузить (читай только нужную ветку, остальное lazy)

> **ПРИНЦИП ЭКОНОМИИ (главный):** генерируем МАКСимально через СВОИ прямые API / подписки / скиллы (дёшево или $0),
> а bundled `hf.exe` (токены/кредиты Higgsfield) дёргаем ТОЛЬКО для того, что напрямую невозможно (HF-эксклюзивы).
> `engines/higgsfield/scripts/router.py` это и делает: `route(jst)` → direct где можно, hf.exe только для 🔴.

1. **Прямая генерация (DEFAULT)** — Veo (GOOGLE_API_KEY) · Seedance 2.0 + Kling (Runway Unlimited = $0 marginal) · Sora (OpenAI) · HeyGen Avatar · keyframes (Nano/GPT-Image) · аудио (ElevenLabs/Lyria/Suno) · монтаж (ffmpeg). → **остаёшься в этом SKILL.md + `references/*`** (6-фаз пайплайн, decision-tree ниже, 38-строчная gotcha-таблица, audio/assembly рецепты, scripts/*).
2. **Структурный флоу Higgsfield** (его промпт-инжиниринг, но генерация — СВОИМИ провайдерами!) — cinematic-5, motion-design (highMD/productMD/typographyMD/infographicMD/classicMD), UGC/unboxing/tutorial/try-on, TV-ad, podcast, cartoon. → открой **`engines/higgsfield/ENGINE.md`** режим (A): `prompt_builders.py` строит промпт → `router.py` гонит через Runway/Veo/Replicate (НЕ hf) → `assemble.py`/`ffmpeg_assemble.py` собирает.
3. **HF-эксклюзив (только тут тратим hf.exe)** — Soul Cast/Location/ID, Marketing Studio/DTC, Virality Predictor (brain_activity), Cinema Studio, ai_stylist, reframe, draw_to_video. → **`engines/higgsfield/ENGINE.md`** режим (B). Это единственное, чего нет напрямую.

Seedance тоже доступен через hf.exe — но только как **фолбэк** когда Runway в throttle (иначе всегда Runway $0).

## TURNKEY — одна команда под ключ (`scripts/run.py`)

Не хочешь собирать вручную — дай бриф, и оркестратор прогонит весь пайплайн сам (intake → flow → промпт → route DIRECT-first → параллельный fan-out keyframes+clips → аудио → ffmpeg → платформенный экспорт), с **approval-гейтом** перед дорогой стадией клипов.

```bash
# DRY-RUN (по умолчанию — строит ПЛАН, ничего не тратит, пишет out/plan.json):
python scripts/run.py --flow cinematic --story "сюжет" --aspect 21:9 --platform youtube --duration 24
python scripts/run.py --brief brief.json            # полный бриф (flow/palette/voiceover_text/music_prompt/scenes)
# ЗАПУСК (keyframes → GATE → clips → audio → assemble; --yes снять гейт):
python scripts/run.py --brief brief.json --execute
```
Бриф (JSON): `{flow, brief, aspect, platform, duration, palette[], voiceover_text, voice, music_prompt, scenes[], out_dir}`. flow ∈ cinematic / highMD / productMD / typographyMD / infographicMD / classicMD / simple. Под капотом зовёт `prompt_builders` (промпт), `router` (DIRECT vs hf), `nano_banana_keyframes`/`runway_client`/`veo_image_to_video` (генерация своими ключами), `elevenlabs_voiceover`/`lyria_music` (аудио), `ffmpeg_assemble`+`engines/.../assemble.py` (сборка). hf.exe — только если флоу требует эксклюзив. Для сложного/творческого — оркеструй фазы сам по ROUTING-MAP ниже.

### Turnkey battle-notes (заработано боем на @YourUsername, 2026-06)
- **Текст/числа в хуке → PIL-оверлей + Ken Burns, НЕ image-моделью и НЕ i2v.** Nano/Veo гарбят цифры; крупное «$48 000 000» компонуй PIL (arialbd) на затемнённый bg → `ken_burns` (без AI-морфа = текст чёткий). Виральный хук всегда = число/имя крупно в 1-ю секунду (топ-шортсы канала так и сделаны).
- **Runway 429 throttle (account-level, даже sequential) → фолбэк на Veo** (свой GOOGLE_API_KEY). Архитектура фолбэка реально спасает.
- **Veo ID:** рабочий `veo-3.0-fast-generate-001` (stable). 3.1 ТОЛЬКО как `veo-3.1-*-preview` (НЕ `-001`). Veo `--duration` ∈ {4,6,8} (не 5). Veo 9:16 = 720×1280 (concat нормализует до 1080×1920).
- **brain_activity (virality) ≤16 секунд** — финал для проверки режь ≤15.5с.
- **Git Bash `$PWD` = POSIX `/c/...`** ffmpeg на Windows не откроет → в манифестах/путях всегда `C:/...` (или PowerShell).
- Цикл полировки: сделал → **контактка (ffmpeg tile) → смотреть глазами** → диагноз → фикс скрипта/скилла → пересобрать → virality-замер. Так v1 hook 27 → v2 hook 33.

## Provider selection — decision tree

| Задача | Провайдер | Почему | Цена |
|---|---|---|---|
| Default «просто оживи» | **Seedance 2.0** через Runway JWT | Flat 180 credits = $0 marginal на Unlimited; лучший motion из i2v | $0 (Unlimited) |
| Кириллический текст на кадре | **Sora** (OpenAI SDK) | Veo корёжит кириллицу в «иероглифы», Sora держит | ~$0.08/s |
| Cinematic 21:9 trailer с native аудио | **Veo 3.1 Full** | Native audio + 4K-grade composition | $0.40/s |
| Быстрый 5-секундный motion для соцсетей | **Veo 3.1 Fast** | Дешевле Full в 4×, качество для шортсов достаточно | $0.10/s |
| Image-to-video с lock'ом face/glyph | **Seedance + end_frame=first_frame** | Forces interpolation между identical — small detail changes only | $0 |
| Talking head YourFirstName | **HeyGen Avatar V** (`heygen` skill) | Готовый avatar_id + voice_id, lip-sync из коробки | $0.0667/s |
| B-roll из готовой картинки без AI-генерации | **Ken Burns zoompan** (ffmpeg) | Бесплатно, мгновенно, для slow-pan «оживления» | $0 |
| Multi-shot cinematic narrative | **Seedance i2v + Nano Banana Pro keyframes** | Lock characters через reference image (1-2 лица) | $0 |
| 3–4 РЕАЛЬНЫХ лица в одном кадре | **GPT-Image-2 multi-ref → Seedance** | Nano держит 1-2, плывёт на 3-4; GPT `/v1/images/edits` мультиреференс точнее. См. `references/keyframes-multiface.md` | $0 |
| Брендкит / UI-only workflow без API | **Playwright MCP browser fallback** | См. `references/runway-seedance.md` §8 | $0 |

Конфликт keyframing'а решён явно:
- **Veo / Sora** интерполируют motion → нужны РАЗНЫЕ first/end frame.
- **Seedance** склонен мутировать мелкие детали → `end_frame=first_frame` LOCK даёт anti-mutation для tattoos/глифов/лиц.

## Auth & credentials

Всё в `~/.claude/.credentials.master.env`:

| Переменная | Для чего |
|---|---|
| `GOOGLE_API_KEY` | Veo 3.1 (google-genai SDK) |
| `GEMINI_API_KEY` | **КОНФЛИКТ** с GOOGLE_API_KEY. `os.environ.pop('GEMINI_API_KEY', None)` ПЕРЕД `import genai` |
| `GOOGLE_CLOUD_PROJECT_ID` | Lyria 2 через your-server AI |
| `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` | Абсолютный путь к service-account JSON для Lyria (НЕ конфликт с GOOGLE_API_KEY) |
| `RUNWAY_TOKEN_PLACEHOLDER` | Runway internal API. **30 дней TTL**. Refresh: app.runwayml.com → DevTools → Application → localStorage → `RW_TOKEN_PLACEHOLDER` |
| `RUNWAY_TEAM_ID` | `?asTeamId=<id>` параметр для большинства endpoints |
| `ELEVENLABS_API_KEY` | TTS + Music |
| `OPENAI_API_KEY` | Sora через OpenAI SDK |
| `HEYGEN_API_KEY` | Avatar V (через `heygen` skill) |
| `SUBMAGIC_API_KEY` | EN-субтитры (`x-api-key: sk-...`, НЕ Bearer) |

Проверка JWT (день 31 = 401):

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py profile
```

## Pipeline overview — 6 фаз

```
1. Intake          → бриф, длительность, аспект, платформа, бюджет, голос
2. Storyboard      → текстовый сценарий по shot'ам, длительность каждого
3. Visual style    → lock film vocabulary (см. §Visual lock), generate keyframes
4. Clip planning   → выбор провайдера на каждый shot, prompts с motion+camera
5. Generation      → parallel fan-out (Veo×3 / Seedance batch / TTS / Music)
6. Assembly        → ffmpeg concat+xfade, amix+ducking, loudnorm, compression tier
```

Reference timeline для 77s 9:16 vertical:
- Keyframes: **45–60 sec** (Nano Banana Pro batch до 4 parallel)
- Generation parallel: **120 sec** (Veo 3 concurrent + voice + music)
- Assembly: **30–50 sec** (concat -c copy 65x realtime + final loudnorm pass)
- **Wall-clock: ~4 минуты**

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

**Veo / Sora (interpolation):**
- Передавай keyframe как `types.Image(image_bytes=f.read(), mime_type='image/png')` — path string silently degrades to text-only
- РАЗНЫЕ first_frame и end_frame нужны для motion

**Seedance (mutation-prone):**
- **Start-frame-only лучше dual-keyframe на 70-80%** (эмпирически 39 итераций Terra, ОДИН персонаж)
- **3-4 реальных лица:** лица решаются на стадии keyframe (GPT-Image-2 multi-ref), анимируй start-only + анти-дрейф-суффикс `stable consistent faces, no identity drift` + медленное движение → `keyframes-multiface.md`
- Dual-keyframe только когда end-composition mandatory ИЛИ для anti-mutation lock
- `end_frame = first_frame` LOCK → small detail changes only, без морфинга глифов
- JFIF → JPG конвертация ОБЯЗАТЕЛЬНА перед upload: `ffmpeg -y -i in.jfif out.jpg`
- API param = `end_frame`, **НЕ** `last_frame` (UI label обманывает)

Полный Seedance гайд → `references/runway-seedance.md`.

## Phase 5 — Generation, per-provider quick recipes

### Veo 3.1 Fast (через Google GenAI SDK)

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

### Seedance через Runway JWT (default)

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

**Параллелизм Seedance:** credits-mode до ~30 concurrent (списывает пул); `exploreMode=True` бесплатно, но троттлит ~3. **Кредит списывается при ОТПРАВКЕ задачи, не при скачивании**; остановка раннера не «жжёт кадры», SUCCEEDED-задачи добираются по `task_id`. Подробно (recovery, THROTTLED≠failed) → `references/runway-seedance.md` §12.

Гoтчи + 7 mutation patterns + CHARACTER blocklist → `references/runway-seedance.md`.

### Sora через OpenAI SDK

Для RU с кириллицей на кадре. См. `references/veo-direct.md` §Sora.

### HeyGen Avatar V (YourFirstName talking head)

```python
# avatar_id=YOUR_HEYGEN_AVATAR_ID
# voice_id=YOUR_HEYGEN_VOICE_ID
# engine=avatar_v, 9:16, 1080p, $0.0667/sec
# Готовая обвязка в `shorts-pipeline-user` skill
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
- Talking-head YourFirstName (HeyGen сам решает кадр)

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

### ElevenLabs TTS — YourFirstName voice (production settings)

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))

audio = client.text_to_speech.convert(
    voice_id = 'YOUR_HEYGEN_VOICE_ID',  # YourFirstName clone
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

**Эмпирика для RU:** EN voices через `eleven_multilingual_v2` на русском тексте дают тембр лучше нативных RU voices (YourFirstName shortform pattern): Matthew Villain `bwCXcoVxWNYMlC6Esa8u` (усталый/character), **George `JBFqnCBsd6RMkjVDRZzb` (тёплый рассказчик — поздравления/трибьюты)**, Brian (корпоративный). Ударение в RU — combining acute U+0301 (`што́рма`), см. `references/audio.md` §3.

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

### Lyria 2 через your-server AI (OAuth2 service account)

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
text = 'Your Channel Name'

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

## Known gotchas — master table

| # | Gotcha | Provider | Где детали |
|---|---|---|---|
| 1 | `GEMINI_API_KEY` env conflict — pop ДО import | Veo | `references/veo-direct.md` |
| 2 | Veo safety filter возвращает NoneType, не exception | Veo | `references/veo-direct.md` |
| 3 | Veo `types.Image(image_bytes=..., mime_type='image/png')` — path string silently degrades | Veo | `references/veo-direct.md` |
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
| 30 | Yandex Disk multipart upload = 0-byte file, нужен raw PUT | Delivery | `references/windows.md` |
| 31 | SubMagic «пайвот» → 🍺 на RU, обязательная trigger-word чистка | Captions | `submagic` skill |
| 32 | Playwright MCP clipboard = `navigator.clipboard.writeText()` | Browser | `references/windows.md` |
| 33 | ElevenLabs Music param = `music_length_ms` + `force_instrumental=True` + `model_id='music_v1'` (НЕ `length_ms` → TypeError) | Audio | `references/audio.md` §2 |
| 34 | Runway кредит списывается при ОТПРАВКЕ, не скачивании; стоп раннера не «жжёт кадры»; SUCCEEDED добирается по task_id | Runway | `references/runway-seedance.md` §12 |
| 35 | НЕ останавливать чужую идущую генерацию без спроса (user-trust); НЕ resubmit на client-timeout (THROTTLED≠failed) | Runway | `references/runway-seedance.md` §12 |
| 36 | Nano держит 1-2 лица, плывёт на 3-4 → GPT-Image-2 multi-ref для ансамбля; итеративно + вето | Image | `references/keyframes-multiface.md` |
| 37 | Контактный лист для vision-ревью ≤ 2000px шириной (иначе read падает) | Image | `references/keyframes-multiface.md` |
| 38 | RU TTS ударение через combining acute U+0301; print такой строки падает на cp1251 (numeric format) | Audio/Win | `references/audio.md` §3 |
| 39 | Glyph-pulse trap: «pulsing sigil» → bloom в disc/медальон; форму держит только STEADY glow (без brightness-пульса) или post-composite | Seedance | `references/runway-seedance.md` §4 #1 |
| 40 | Thrown/passed object левитирует и дрейфует; end_frame диктует resolved state → дай keyframe «объект уже в руках / действие завершено» | Seedance | `references/runway-seedance.md` §4 #8 + §5 |

## Reference timelines (real projects)

| Проект | Output | Iterations | Wall-clock | Cost |
|---|---|---|---|---|
| Terra book trailer | 4 living covers 9:16, 5s each | 39 Seedance + 27 keyframe versions | ~14h active | $0 (Unlimited) |
| Terra ch1 dynamic pilot | 2 раскадровки × (narrative ~10s + loop 5s) = 4 ролика 2:3 | 7 keyframe + edit-fix глифов + 9 Seedance (2 фикса: меч-левитация, glyph-pulse) | ~1 день | $0 (Unlimited) |
| Amber cinematic trailer | 12 scenes 21:9 | parallel-tabs 4 VSCode | ~6h active | $0 |
| ConferenceX announcement | 30s Avatar V + SubMagic | 1 pass + 1 trigger-fix | ~45 min | ~$2 |
| Client tribute (Хроники Восхождения) | 60s 21:9, 12 сцен + титр, 12 реальных лиц | GPT-Image-2 multi-ref + Seedance start-only (exploreMode) | ~1 день | $0 |
| YourFirstName shortform (Avatar V) | 60s 9:16 1080p | 1 pass | ~3 min | ~$4 |
| **Reference 77s vertical** | **77s 9:16** | **3 parallel + 1 keyframe pass** | **~4 min** | **~$8 Veo Fast** |

Полные кейсы → `references/case-studies.md`.

## Workflow templates

### Template A — Book trailer (Terra-style, 4×5s 9:16)

```
1. Колоризация ЧБ обложек через gpt-image-2-2026-04-21 (4 главы → 4 цветных keyframe)
2. Nano Banana Pro batch: 4 keyframe variants per chapter (lock film vocab)
3. Seedance JWT API: 4 параллельных задачи, end_frame=first_frame LOCK на glyphs
4. Iterate per chapter: review → patch prompt из 7 mutation patterns → re-submit
5. Concat -c copy + xfade chain между главами
6. ElevenLabs YourFirstName VO (1 длинный narration трек) + Lyria 2 BGM (2×30s + acrossfade)
7. Sidechain ducking → loudnorm I=-14
8. Tier 1 archive (CRF 18, 4K) + Tier 3 social (CRF 22, 1080p)
9. Upload в Yandex Disk (raw PUT, ASCII path), Outlook draft со ссылкой
```

### Template B — Cinematic narrative (Amber-style, 12 scenes 21:9)

```
1. Storyboard text 12 shots (one action, one camera per shot)
2. Lock character reference image (single crop из первого успешного generation)
3. Nano Banana Pro 21:9 native: keyframes для каждого shot'а с ref-image-chaining
   re-anchor к первому output каждые 3 шага против drift
4. Seedance параллельный batch (3-5 concurrent), Explore Mode throttles ~3
5. Storyboard pacing injection: quiet→acceleration→shock→climax→quiet
6. ElevenLabs Music 2×30s (handoff prompt, direct concat без crossfade)
7. xfade chain 12 clips, sidechain ducking, loudnorm
8. 3-tier compression
```

### Template C — Social shorts 9:16 (быстро, дёшево)

```
1. 1 keyframe (Nano Banana Pro 9:16)
2. Veo 3.1 Fast 5s ($0.50)
3. ElevenLabs YourFirstName TTS (60s VO)
4. Lyria 2 1×30s BGM или royalty-free
5. amix volume scaling + loudnorm
6. Brand card overlay через PIL
7. Tier 3 (CRF 22, 1080p, faststart)
```

### Template D — Live-illustration B-roll (для статей / лонгридов)

```
1. Готовая иллюстрация → Ken Burns zoompan (ffmpeg, $0)
ИЛИ
2. Iллюстрация → Seedance i2v + end_frame=first_frame LOCK (мягкое оживление без морфинга)
3. Без аудио или 1 BGM track
4. Tier 3 social, embed в статью
```

## Cross-references — что где живёт

| Skill | За что отвечает | Когда дёргать |
|---|---|---|
| `nano-banana-pro` | Keyframes, 21:9 cinemascope, multi-image consistency via reference chaining | Phase 3-4 (visual style + keyframes) |
| `image-generation` | Общий гайд по prompt engineering для image gen | Fallback когда Nano Banana Pro не подходит |
| `elevenlabs` | TTS, Music, voice IDs, settings | Phase 5 audio |
| `suno` | Длинный оркестровый score / песня (headless Clerk API) | Phase 5 audio — 60s+ score или вокал |
| `heygen` | Avatar V YourFirstName talking heads | Когда нужен говорящий аватар |
| `submagic` | Платные EN-субтитры (с пиво-bug warning) | Phase 6 captions для EN-контента |
| `shorts-pipeline-user` | Готовая обвязка Avatar V + SubMagic + RU trigger check (`skills/shorts-pipeline-user/scripts/trigger_word_check.py`) | Перед SubMagic на RU тексте — обязательно |
| `video-editor` | Чистый монтаж готовых клипов на your-server:3124 | Если нужен external assembly service |
| `void-video` | Удаление объектов из готового видео | Post-production cleanup |
| `video-downloader` | yt-dlp скачать чужое видео | Источник для re-edit |
| `runway-api` (archived) | Старое имя — переехал сюда в `scripts/runway_client.py` | — |
| `seedance-runway` (archived) | Browser-automation fallback → `references/runway-seedance.md` §8 | UI-only providers |
| `video-generation` (archived) | Старый монолитный хаб → разбит на этот SKILL.md + references/ | — |
| **`engines/higgsfield/`** (встроенный движок) | Реверс Supercomputer Higgsfield + локальная реплика: структурные флоу (cinematic-5/MD/UGC/TV-ad/podcast/cartoon), промпт-кухня, model-router (direct-first), HF-эксклюзивы (Soul/Marketing/Virality) через bundled hf.exe | Ветки 2-3 ROUTING-MAP — структурный флоу или эксклюзив |

## Reference files (lazy-loaded)

- `references/higgsfield-flows.md` — техники Higgsfield, вшитые в наши фазы (выжимка) → полный движок `engines/higgsfield/ENGINE.md`
- `engines/higgsfield/ENGINE.md` — **движок Higgsfield**: 6-фаз оркестрация + 11 флоу + hf.exe CLI + scripts/{prompt_builders,router,assemble}.py + references/ (60+) + registries/ (real UUID)

- `references/runway-seedance.md` — Runway JWT API + Seedance prompt engineering + browser fallback
- `references/veo-direct.md` — Veo 3.1 Fast/Full + Sora через OpenAI SDK
- `references/audio.md` — Lyria 2 (your-server OAuth) + ElevenLabs Music/TTS voice IDs + Suno climax-cut + RU ударения
- `references/keyframes-multiface.md` — несколько РЕАЛЬНЫХ лиц в кадре (GPT-Image-2 multi-ref vs Nano, биометрия, hero/ensemble)
- `references/color-grading.md` — LUT (Kodak 2383) + teal-orange + film look + hald CLUT + color match
- `references/remotion-overlays.md` — соц-UI оверлеи (Instagram/Telegram chrome) React→alpha webm→composite
- `references/motion-graphics.md` — motion graphics 3 уровня: ffmpeg / movis / Manim
- `references/assembly.md` — FFmpeg cookbook (amix, concat, xfade, loudnorm, per-line VO, compression)
- `references/windows.md` — Windows-specific (subprocess encoding, PIL paths, Yandex multipart, кириллические paths)
- `references/case-studies.md` — Terra + Amber + ConferenceX + Client tribute verbatim configs и таймлайны

## Scripts

- `scripts/runway_client.py` — Python class `RunwayClient` (mig из `runway-api/scripts/`)
- `scripts/runway_mcp.py` — MCP server обёртка (8 runway_* tools)
- `scripts/climax_cut.py` — climax-aware нарезка длинного аудио под короткий ролик (Suno/Lyria → 60s)
- `scripts/extract_chat_session.py` — добыча знаний из прошлых JSONL-сессий по topic-regex (для апдейта скилла)

CLI quick check JWT:

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py profile
```
