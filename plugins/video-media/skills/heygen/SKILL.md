---
name: heygen
description: "HeyGen AI avatar video — Video Agent (prompt-to-video), precise avatar control (v2 API), AI video gen (VEO/Kling/Sora via Workflow Gateway), Starfish TTS, faceswap, video translate, Remotion integration"
---

# HeyGen Skill (v2.0)

## When to Use

- Создание видео с AI аватаром (говорящая голова)
- Prompt-to-video генерация через Video Agent API
- Презентации с аватаром + слайды/фон
- Маркетинговые и обучающие ролики
- Персонализированные видео-сообщения
- Локализация/перевод видео на другие языки
- AI-генерация видео без аватара (VEO, Kling, Sora, Runway, Seedance)
- Text-to-Speech через Starfish TTS (standalone аудио)
- Faceswap — замена лица в видео
- Transparent WebM для композитинга в Remotion
- Multi-scene pipeline: параллельная генерация сцен + локальная сборка
- Image-to-video генерация из референсного изображения

## API Configuration

```python
import requests
import os

HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
BASE_URL = "https://api.heygen.com"

headers = {
    "X-Api-Key": HEYGEN_API_KEY,
    "Content-Type": "application/json"
}
```

## Аватары User

| Название | Avatar ID |
|----------|-----------|
| User_Горизонталь_Сидячий | `YOUR_HEYGEN_AVATAR_ID_1` |
| User_Вертикаль_Сидячий | `YOUR_HEYGEN_AVATAR_ID_2` |

## Голоса User's (HeyGen)

| Название | Voice ID |
|----------|----------|
| User_pro voice | `YOUR_HEYGEN_VOICE_ID_1` |
| User_Нейтральный_123 | `YOUR_HEYGEN_VOICE_ID_2` |
| User_Сидячий - Voice 1 | `YOUR_HEYGEN_VOICE_ID_3` |
| User_Сидячий - Voice 2 | `YOUR_HEYGEN_VOICE_ID_4` |
| User_Сидячий - Voice 3 | `YOUR_HEYGEN_VOICE_ID_5` |

---

## Decision Tree: Which API to Use

| User Intent | API | Endpoint |
|------------|-----|----------|
| "Сделай видео про X" (описание идеи) | **Video Agent** | `POST /v1/video_agent/generate` |
| Конкретный аватар + точный скрипт + фоны | **v2 API** | `POST /v2/video/generate` |
| Multi-scene с разными фонами/позициями | **v2 API** (по сценам) | `POST /v2/video/generate` |
| Transparent WebM для композитинга | **v1 WebM** | `POST /v1/video.webm` |
| AI-генерация b-roll без аватара (VEO/Kling/Sora) | **Workflow Gateway** | `POST /v1/workflows/executions` |
| Замена лица в видео | **Faceswap** | `POST /v1/workflows/executions` |
| Standalone TTS (аудио без видео) | **Starfish TTS** | `POST /v1/audio/text_to_speech` |
| Перевод видео на другой язык | **Video Translate** | `POST /v2/video_translate` |

---

## 1. Video Agent API (Prompt-to-Video)

AI сам выбирает аватар, пишет скрипт, настраивает визуал, озвучку и каptions. Достаточно описать что нужно.

### Endpoint

```
POST https://api.heygen.com/v1/video_agent/generate
```

### Parameters

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `prompt` | string | Y | Текстовый промпт с описанием видео |
| `config` | object | | Конфигурация (см. ниже) |
| `config.duration_sec` | integer | | Длительность 5-300 секунд |
| `config.avatar_id` | string | | Конкретный аватар (иначе AI выберет) |
| `config.orientation` | string | | `"landscape"` или `"portrait"` |
| `files` | array | | Референсные файлы `[{asset_id: "..."}]` |
| `callback_id` | string | | ID для вебхуков (требует `callback_url`) |
| `callback_url` | string | | URL для уведомления о завершении |

### Prompt Optimizer

**Ключевой инсайт: Video Agent — это HTML-рендерер.** Описывай B-roll как motion graphics с глаголами действия ("SLAMS in", "COUNTS UP"), а не координатами ("upper-left, 48pt").

#### Структура промпта (FORMAT-TONE-AVATAR-STYLE-TEXT-SCENES-MUSIC-NARRATION)

```
FORMAT:    Тип видео, длительность, энергия
TONE:      Эмоциональный регистр, референсы
AVATAR:    Детальное описание (одежда + окружение + мониторы + свет), 60-100 слов
STYLE:     Именованная эстетика + цвета + типографика + правила движения + переходы
CRITICAL ON-SCREEN TEXT:  Точные строки для отображения на экране
SCENE-BY-SCENE:  Разбивка по сценам с VO и многослойными визуалами
MUSIC:     Жанр, референсные артисты, арка энергии
NARRATION STYLE:  Как произносить: быстро/медленно, где паузы
```

#### Типы сцен

| Type | Format | When to Use |
|------|--------|-------------|
| **A-ROLL** | Аватар говорит в камеру | Интро, ключевые мысли, CTA |
| **FULL SCREEN B-ROLL** | Без аватара — motion graphics | Data visualization, плотный контент |
| **A-ROLL + OVERLAY** | Split frame: аватар + контент | Данные + человеческая связь |

**Правила:** Никогда 3+ одинаковых типа подряд. Минимум 2 чистых B-roll сцены. VOICEOVER на КАЖДОЙ сцене (включая B-roll).

#### Visual Layer System (5 слоёв для B-roll)

| Layer | Purpose | Examples |
|-------|---------|---------|
| **L1** | Background | Текстура, grid, градиент |
| **L2** | Hero content | Главный заголовок/число |
| **L3** | Supporting data | Карточки, статистики, буллеты |
| **L4** | Information bar | Тикеры, лейблы, цитаты |
| **L5** | Effects | Частицы, глитчи, анимация сетки |

Каждый B-roll: 4+ слоёв. Каждый элемент ДВИГАЕТСЯ.

#### Motion Vocabulary

**High Energy:** SLAMS, CRASHES, PUNCHES, STAMPS, SHATTERS
**Medium Energy:** CASCADE, SLIDES, DROPS, FILLS, DRAWS
**Low Energy:** types on, fades in, FLOATS, morphs, COUNTS UP

#### Timing Guidelines

| Content Type | Duration |
|--------------|----------|
| Hook/Intro (A-roll) | 6-10 sec |
| Data-heavy B-roll | 10-15 sec (NEVER <=5s) |
| A-roll + Overlay | 8-12 sec |
| CTA / Close (A-roll) | 6-8 sec |

**Pace:** ~150 words/min. Social clip: 30-45s (5-7 scenes) | Briefing: 60-75s (7-9 scenes) | Deep dive: 90-120s (10-13 scenes).

#### 20 Visual Styles (краткий справочник)

| # | Style | Mood | Best For |
|---|-------|------|----------|
| 1 | Soft Signal (Sagmeister) | Intimate, warm | Personal stories |
| 2 | Warm Grain (Eksell) | Organic, friendly | Sustainability |
| 3 | Quiet Drama (Ray) | Humanist | Profiles |
| 4 | Heritage Reel (Cassandre) | Nostalgic | History |
| 5 | Silk Route (Abedini) | Flowing | Global affairs |
| 6 | **Swiss Pulse** (Muller-Brockmann) | Clinical, precise | **Data-heavy** |
| 7 | Geometric Bold (Tanaka) | Minimal, elegant | Lifestyle |
| 8 | Velvet Standard (Vignelli) | Premium | Luxury, investors |
| 9 | **Digital Grid** (Crouwel) | Systematic | **Tech, infra** |
| 10 | Contact Sheet (Brodovitch) | Editorial | Journalism |
| 11 | Folk Frequency (Terrazas) | Cultural | Festivals |
| 12 | Earth Pulse (Ghariokwu) | Grounded | Community |
| 13 | Dream State (Tomaszewski) | Surreal | Philosophy |
| 14 | Play Mode (Ahn Sang-soo) | Playful | Entertainment |
| 15 | Carnival Surge (Lins) | Euphoric | Milestones |
| 16 | Shadow Cut (Hillmann) | Dark | Investigations |
| 17 | **Deconstructed** (Brody) | Industrial, raw | **Tech news** |
| 18 | Maximalist Type (Scher) | Loud, kinetic | Launches |
| 19 | Data Drift (Anadol) | Futuristic | AI/tech |
| 20 | Red Wire (Tartakover) | Urgent | Breaking news |

**Пример стиля в промпте:**
```
STYLE — DECONSTRUCTED (Brody): Dark grey #1a1a1a, rust orange #D4501E.
Type at angles, overlapping. Gritty textures, scan-line glitch.
Smash cuts with flash frames.
```

#### What Doesn't Work

- **Layout language** — координаты вызывают чёрные кадры: "`UPPER-LEFT: headline in 48pt`"
- **Named artists without specs** — "`Ikko Tanaka style`" = ничего. Переводи в конкретные правила
- **B-roll <= 5 seconds** — слишком коротко, чёрные экраны. Минимум 10s
- **Content as list** — всегда синтезируй в story, не буллеты

#### Style Performance (из 40+ видео)

| Rank | Style | Strength |
|------|-------|----------|
| 1 | Deconstructed (Brody) | Most reliable across all topics |
| 2 | Swiss Pulse (Muller-Brockmann) | Best for data-heavy |
| 3 | Digital Grid (Crouwel) | Strong for tech |
| 4 | Geometric Bold (Tanaka) | Elegant and versatile |
| 5 | Maximalist Type (Scher) | High energy, use sparingly |

### Example: Video Agent Python

```python
def generate_with_video_agent(
    prompt: str,
    duration_sec: int | None = None,
    avatar_id: str | None = None,
    orientation: str | None = None
) -> str:
    """Generate video via Video Agent. Returns video_id."""
    request_body = {"prompt": prompt}

    config = {}
    if duration_sec:
        config["duration_sec"] = duration_sec
    if avatar_id:
        config["avatar_id"] = avatar_id
    if orientation:
        config["orientation"] = orientation

    if config:
        request_body["config"] = config

    response = requests.post(
        f"{BASE_URL}/v1/video_agent/generate",
        headers=headers,
        json=request_body
    )

    data = response.json()
    if data.get("error"):
        raise Exception(f"Video Agent failed: {data['error']}")

    return data["data"]["video_id"]
```

---

## 2. Avatar Video (v2 API — Precise Control)

Полный контроль: конкретный аватар, точный скрипт, фон, стиль, позиция, мультисцены.

### Create Video (POST /v2/video/generate)

#### Top-Level Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `video_inputs` | array | Y | Массив сцен (1-50 элементов) |
| `dimension` | object | | `{width, height}` |
| `title` | string | | Название видео |
| `test` | boolean | | Тест-режим (водяной знак, без кредитов) |
| `caption` | boolean | | Включить авто-субтитры |
| `callback_id` | string | | ID для вебхуков |
| `callback_url` | string | | URL для уведомления |
| `folder_id` | string | | ID папки хранения |

#### video_inputs[].character Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `type` | string | Y | `"avatar"` или `"talking_photo"` |
| `avatar_id` | string | Y* | ID аватара (*required для type="avatar") |
| `talking_photo_id` | string | Y* | ID фото (*required для type="talking_photo") |
| `avatar_style` | string | | `"normal"`, `"closeUp"`, `"circle"`, `"voice_only"` |
| `scale` | number | | Масштаб аватара |
| `offset` | object | | Позиция `{x, y}` |

#### video_inputs[].voice Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `type` | string | Y | `"text"`, `"audio"`, `"silence"` |
| `voice_id` | string | Y* | ID голоса (*для type="text") |
| `input_text` | string | Y* | Скрипт (*для type="text") |
| `audio_url` | string | Y* | URL аудио (*для type="audio") |
| `duration` | number | Y* | Длительность в сек (*для type="silence") |
| `speed` | number | | Скорость речи 0.5-2.0 (default 1.0) |
| `pitch` | number | | Тон голоса -20 до 20 (default 0) |

#### video_inputs[].background Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `type` | string | | `"color"`, `"image"`, `"video"` |
| `value` | string | | Hex-цвет (для type="color") |
| `url` | string | | URL картинки/видео |
| `fit` | string | | `"cover"` или `"contain"` |

#### Dimensions

```python
dimensions = {
    "landscape": {"width": 1920, "height": 1080},  # 16:9
    "portrait": {"width": 1080, "height": 1920},   # 9:16 (TikTok, Reels)
    "square": {"width": 1080, "height": 1080},     # 1:1 (Instagram)
}
```

#### Python Example

```python
def create_video(avatar_id: str, voice_id: str, script: str,
                 background: dict | None = None,
                 dimension: dict | None = None,
                 test: bool = False) -> str:
    """Generate video with avatar. Returns video_id."""
    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal"
            },
            "voice": {
                "type": "text",
                "input_text": script,
                "voice_id": voice_id
            },
            "background": background or {"type": "color", "value": "#FFFFFF"}
        }],
        "dimension": dimension or {"width": 1920, "height": 1080},
        "test": test,
    }

    response = requests.post(
        f"{BASE_URL}/v2/video/generate",
        headers=headers,
        json=payload
    )
    data = response.json()
    if data.get("error"):
        raise Exception(data["error"])
    return data["data"]["video_id"]
```

### Video Status Polling

```python
import time

def wait_for_video(video_id: str, poll_interval: int = 10, timeout: int = 1200) -> str:
    """Poll until video is ready. Returns video_url."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{BASE_URL}/v2/videos/{video_id}",
            headers={"X-Api-Key": HEYGEN_API_KEY}
        )
        data = resp.json()["data"]
        status = data["status"]
        print(f"  [{video_id[:8]}] status={status}")

        if status == "completed":
            return data["video_url"]
        elif status == "failed":
            raise RuntimeError(f"Video {video_id} failed: {data.get('failure_message')}")

        time.sleep(poll_interval)

    raise TimeoutError(f"Video {video_id} timed out after {timeout}s")
```

### Break Tags in Scripts

Паузы в скрипте через SSML `<break>` теги:

```python
script = "Welcome to our demo. <break time=\"1s\"/> Let me show you the features."
# Multiple pauses
script = "First point. <break time=\"1.5s\"/> Second point. <break time=\"1s\"/> Third."
```

**Правила:** `<break time="Xs"/>` где X — секунды. Обязательно пробелы до и после тега.

### Captions (built-in)

```python
# Simple
payload = {
    "video_inputs": [...],
    "caption": True,  # auto-captions с дефолтным стилем
}

# Styled
payload = {
    "video_inputs": [...],
    "caption": {
        "enabled": True,
        "style": {
            "font_family": "Arial",
            "font_size": 32,
            "font_color": "#FFFFFF",
            "background_color": "rgba(0, 0, 0, 0.7)",
            "position": "bottom",  # "top" or "bottom"
        }
    },
}
```

**Social media:** для TikTok/Reels — position="top" (нижняя часть занята UI), font_size=42.

### Text Overlays (через v2 API scene background)

Для текста поверх аватара — используй фоновое изображение с текстом или Remotion-композитинг.

### Transparent WebM (POST /v1/video.webm)

Для прозрачного фона (alpha channel) — overlay аватара на другом контенте.

**Когда нужен WebM:**
- Аватар поверх screen recording (Loom-style)
- Аватар floating над видео-контентом
- True alpha compositing

**НЕ нужен WebM для:**
- Аватар с overlays/текстом поверх (используй MP4)
- Picture-in-picture с solid background
- Стандартные presenter видео

#### WebM Request Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `avatar_pose_id` | string | Y | ID позы аватара |
| `avatar_style` | string | Y | `"normal"` или `"closeUp"` only (НЕ circle) |
| `input_text` | string | Y* | Скрипт (*или input_audio) |
| `voice_id` | string | Y* | ID голоса (*с input_text) |
| `input_audio` | string | Y* | URL аудио (*или input_text) |
| `dimension` | object | | `{width, height}` (default 1280x720) |

```python
def create_transparent_video(avatar_pose_id: str, voice_id: str, script: str) -> str:
    """Generate transparent WebM video. Returns video_id."""
    payload = {
        "avatar_pose_id": avatar_pose_id,
        "avatar_style": "normal",
        "input_text": script,
        "voice_id": voice_id,
        "dimension": {"width": 1920, "height": 1080}
    }
    resp = requests.post(f"{BASE_URL}/v1/video.webm", headers=headers, json=payload)
    return resp.json()["data"]["video_id"]
```

### Avatar Styles

| Style | Description | WebM Support |
|-------|-------------|:---:|
| `normal` | Full body, standard framing | Y |
| `closeUp` | Close-up, more expressive | Y |
| `circle` | Circular frame (talking head) | N |
| `voice_only` | Audio only, no video | N/A |

### Avatar Details & Default Voice

```python
def get_avatar_details(avatar_id: str) -> dict:
    """Get avatar details including default_voice_id."""
    resp = requests.get(
        f"{BASE_URL}/v2/avatar/{avatar_id}/details",
        headers={"X-Api-Key": HEYGEN_API_KEY}
    )
    return resp.json()["data"]

# Usage: avatar's pre-matched voice
details = get_avatar_details("josh_lite3_20230714")
voice_id = details["default_voice_id"]  # guaranteed gender match + natural lip sync
```

### Templates

HeyGen поддерживает шаблоны для повторяемого создания видео с разными параметрами.

### Script Length Limits

| Tier | Max Characters |
|------|----------------|
| Free | ~500 |
| Creator | ~1,500 |
| Team | ~3,000 |
| Enterprise | ~5,000+ |

---

## 3. Workflow Gateway (AI Video Generation — 13 Providers)

Генерация AI-видео из текстового промпта БЕЗ аватара. B-roll, product shots, cinematic clips.

### Endpoint

```
POST https://api.heygen.com/v1/workflows/executions
```

### All 13 Providers

| Provider | Value | Description |
|----------|-------|-------------|
| **VEO 3.1** | `"veo_3_1"` | Google VEO 3.1 (default, highest quality) |
| VEO 3.1 Fast | `"veo_3_1_fast"` | Faster VEO 3.1 variant |
| VEO 3 | `"veo3"` | Google VEO 3 |
| VEO 3 Fast | `"veo3_fast"` | Faster VEO 3 variant |
| VEO 2 | `"veo2"` | Google VEO 2 |
| Kling Pro | `"kling_pro"` | Kling Pro model |
| Kling V2 | `"kling_v2"` | Kling V2 model |
| Sora V2 | `"sora_v2"` | OpenAI Sora V2 |
| Sora V2 Pro | `"sora_v2_pro"` | OpenAI Sora V2 Pro |
| Runway Gen-4 | `"runway_gen4"` | Runway Gen-4 |
| Seedance Lite | `"seedance_lite"` | Seedance Lite |
| Seedance Pro | `"seedance_pro"` | Seedance Pro |
| LTX Distilled | `"ltx_distilled"` | LTX Distilled (fastest) |

### Request Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `workflow_type` | string | Y | `"GenerateVideoNode"` |
| `input.prompt` | string | Y | Описание видео |
| `input.provider` | string | | Провайдер (default: `"veo_3_1"`) |
| `input.aspect_ratio` | string | | `"16:9"`, `"9:16"`, `"1:1"` |
| `input.reference_image_url` | string | | URL референсного изображения (image-to-video) |
| `input.tail_image_url` | string | | URL изображения для последнего кадра |
| `input.config` | object | | Provider-specific overrides |

### Image-to-Video

```python
def generate_ai_video(
    prompt: str,
    provider: str = "veo_3_1",
    aspect_ratio: str = "16:9",
    reference_image_url: str | None = None,
) -> str:
    """Generate AI video via Workflow Gateway. Returns execution_id."""
    payload = {
        "workflow_type": "GenerateVideoNode",
        "input": {
            "prompt": prompt,
            "provider": provider,
            "aspect_ratio": aspect_ratio,
        },
    }
    if reference_image_url:
        payload["input"]["reference_image_url"] = reference_image_url

    resp = requests.post(
        f"{BASE_URL}/v1/workflows/executions",
        headers=headers,
        json=payload,
    )
    return resp.json()["data"]["execution_id"]
```

### Status Polling

```python
def wait_for_workflow(execution_id: str, poll_interval: int = 10, timeout: int = 600) -> dict:
    """Poll workflow execution until done. Returns output dict."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{BASE_URL}/v1/workflows/executions/{execution_id}",
            headers={"X-Api-Key": HEYGEN_API_KEY}
        )
        data = resp.json()["data"]
        status = data["status"]

        if status == "completed":
            return data["output"]
        elif status == "failed":
            raise RuntimeError(f"Workflow {execution_id} failed: {data.get('error')}")
        elif status == "not_found":
            raise RuntimeError(f"Workflow {execution_id} not found")

        time.sleep(poll_interval)

    raise TimeoutError(f"Workflow {execution_id} timed out after {timeout}s")
```

### Completed Response Format

```json
{
  "data": {
    "execution_id": "node-gw-v1d2e3o4",
    "status": "completed",
    "output": {
      "video": {
        "video_url": "https://resource.heygen.ai/generated/video.mp4",
        "video_id": "abc123"
      },
      "asset_id": "asset-xyz789"
    }
  }
}
```

---

## 4. Faceswap

Замена лица из source image в target video через GPU AI.

### Endpoint

```
POST https://api.heygen.com/v1/workflows/executions
```

### Request Fields

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `workflow_type` | string | Y | `"FaceswapNode"` |
| `input.source_image_url` | string | Y | URL фото с лицом для замены |
| `input.target_video_url` | string | Y | URL видео для применения замены |

### Python

```python
def faceswap(source_image_url: str, target_video_url: str) -> str:
    """Swap face from source image into target video. Returns execution_id."""
    payload = {
        "workflow_type": "FaceswapNode",
        "input": {
            "source_image_url": source_image_url,
            "target_video_url": target_video_url,
        },
    }
    resp = requests.post(
        f"{BASE_URL}/v1/workflows/executions",
        headers=headers,
        json=payload,
    )
    return resp.json()["data"]["execution_id"]
```

### Chain Pattern: AvatarInferenceNode -> FaceswapNode

```python
# Step 1: Generate avatar video
avatar_exec = requests.post(
    f"{BASE_URL}/v1/workflows/executions",
    headers=headers,
    json={
        "workflow_type": "AvatarInferenceNode",
        "input": {
            "avatar": {"avatar_id": "Angela-inblackskirt-20220820"},
            "audio_list": [{"audio_url": "https://example.com/speech.mp3"}],
        },
    },
).json()["data"]["execution_id"]

# Step 2: Wait for avatar video
output = wait_for_workflow(avatar_exec)
avatar_video_url = output["video"]["video_url"]

# Step 3: Swap in custom face
faceswap_exec = faceswap(
    source_image_url="https://example.com/custom-face.jpg",
    target_video_url=avatar_video_url,
)
faceswap_output = wait_for_workflow(faceswap_exec)
final_url = faceswap_output["video_url"]
```

**Tips:** Clear front-facing photo, single face, high resolution. Processing: 1-3 min.

---

## 5. Starfish TTS (Text-to-Speech)

Standalone аудио-генерация. Отдельный API от видео-голосов.

### List Voices (GET /v1/audio/voices)

> **NB:** Это `GET /v1/audio/voices` — отдельный от `GET /v2/voices` (видео-голоса). Не все видео-голоса поддерживают Starfish TTS.

```python
def list_tts_voices() -> list:
    """List voices compatible with Starfish TTS."""
    resp = requests.get(
        f"{BASE_URL}/v1/audio/voices",
        headers={"X-Api-Key": HEYGEN_API_KEY}
    )
    data = resp.json()
    if data.get("error"):
        raise Exception(data["error"])
    return data["data"]["voices"]
```

**Response voice fields:** `voice_id`, `name`, `language`, `gender`, `preview_audio_url`, `support_pause`, `support_locale`, `type`.

### Generate Speech (POST /v1/audio/text_to_speech)

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `text` | string | Y | Текст для озвучки |
| `voice_id` | string | Y | ID голоса из `/v1/audio/voices` |
| `speed` | number | | Скорость 0.5-1.5 (default 1.0) |
| `pitch` | integer | | Тон -50 до 50 (default 0) |
| `locale` | string | | Акцент для multilingual голосов (e.g. `"pt-BR"`) |
| `elevenlabs_settings` | object | | Расширенные настройки для ElevenLabs голосов |

#### ElevenLabs Settings (optional)

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | `"eleven_v3"`, `"eleven_turbo_v2_5"`, etc. |
| `similarity_boost` | number | Voice similarity 0.0-1.0 |
| `stability` | number | Output consistency 0.0-1.0 |
| `style` | number | Style intensity 0.0-1.0 |

```python
def text_to_speech(
    text: str,
    voice_id: str,
    speed: float = 1.0,
    pitch: int = 0,
    locale: str | None = None,
) -> dict:
    """Generate speech audio. Returns {audio_url, duration, word_timestamps}."""
    payload = {"text": text, "voice_id": voice_id, "speed": speed, "pitch": pitch}
    if locale:
        payload["locale"] = locale

    resp = requests.post(
        f"{BASE_URL}/v1/audio/text_to_speech",
        headers=headers,
        json=payload,
    )
    data = resp.json()
    if data.get("error"):
        raise Exception(data["error"])
    return data["data"]
```

### word_timestamps in Response

Ответ содержит таймстампы каждого слова — идеально для синхронизации субтитров или timed text overlays.

```json
{
  "data": {
    "audio_url": "https://resource2.heygen.ai/text_to_speech/.../id=365d46bb.wav",
    "duration": 5.526,
    "request_id": "p38QJ52hfgNlsYKZZmd9",
    "word_timestamps": [
      { "word": "<start>", "start": 0.0, "end": 0.0 },
      { "word": "Hey", "start": 0.079, "end": 0.219 },
      { "word": "there,", "start": 0.239, "end": 0.459 },
      { "word": "welcome", "start": 0.479, "end": 0.739 },
      { "word": "to", "start": 0.759, "end": 0.859 },
      { "word": "our", "start": 0.879, "end": 0.979 },
      { "word": "demo.", "start": 0.999, "end": 1.279 },
      { "word": "<end>", "start": 5.526, "end": 5.526 }
    ]
  }
}
```

### SSML Break Tags

Те же правила что и в видео: `<break time="1.5s"/>` с пробелами до и после.

---

## 6. Video Translate

Перевод и дублирование видео с lip-sync.

### Submit (POST /v2/video_translate)

| Field | Type | Req | Description |
|-------|------|:---:|-------------|
| `video_url` | string | Y* | URL видео (*или `video_id`) |
| `video_id` | string | Y* | HeyGen video ID (*или `video_url`) |
| `output_language` | string | Y | Целевой язык (e.g. `"es-ES"`) |
| `title` | string | | Название |
| `translate_audio_only` | boolean | | Только аудио, без lip-sync (быстрее) |
| `speaker_num` | number | | Количество спикеров |
| `callback_id` | string | | ID для вебхуков |
| `callback_url` | string | | URL уведомления |

### Supported Languages (12)

| Language | Code |
|----------|------|
| English (US) | `en-US` |
| Spanish (Spain) | `es-ES` |
| Spanish (Mexico) | `es-MX` |
| French | `fr-FR` |
| German | `de-DE` |
| Italian | `it-IT` |
| Portuguese (Brazil) | `pt-BR` |
| Japanese | `ja-JP` |
| Korean | `ko-KR` |
| Chinese (Mandarin) | `zh-CN` |
| Hindi | `hi-IN` |
| Arabic | `ar-SA` |

### v4 Advanced (vocabulary, brand_voice_id, instruction, etc.)

```python
# Advanced translation with custom vocabulary and multiple languages
advanced_config = {
    "input_video_id": "original_video_id",
    "output_languages": ["es-ES", "fr-FR", "de-DE"],
    "name": "Multi-language translations",
    "vocabulary": ["YourCompanyGPT", "SuperWidget", "Pro Max"],  # preserve as-is
    "brand_voice_id": "brand_voice_id",
    "instruction": "Keep technical terms in English",
    "speaker_num": 2,
    "enable_speech_enhancement": True,
    "disable_music_track": False,
    "srt_key": "path/to/custom.srt",
    "srt_role": "input",  # "input" or "output"
    "translate_audio_only": False,
    "enable_video_stretching": True,
}
```

### Status Polling

```python
def wait_for_translation(translate_id: str, poll_interval: int = 30, timeout: int = 1800) -> str:
    """Poll translation status. Returns translated video_url. Timeout 30 min."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{BASE_URL}/v2/video_translate/{translate_id}",
            headers={"X-Api-Key": HEYGEN_API_KEY}
        )
        data = resp.json()["data"]
        status = data["status"]

        if status == "completed":
            return data["video_url"]
        elif status == "failed":
            raise RuntimeError(f"Translation failed: {data.get('message')}")

        print(f"  Translation status: {status}...")
        time.sleep(poll_interval)

    raise TimeoutError(f"Translation {translate_id} timed out")
```

---

## 7. Photo Avatars

### Generate AI Photo

HeyGen поддерживает создание AI-фотографий для talking photo аватаров.

### Create Avatar from Photo (Talking Photo)

```python
# В video_inputs используй talking_photo вместо avatar:
scene = {
    "character": {
        "type": "talking_photo",
        "talking_photo_id": "your_talking_photo_id"
    },
    "voice": {
        "type": "text",
        "input_text": "Hello from a photo avatar!",
        "voice_id": "voice_id_here"
    }
}
```

### Avatar IV (latest)

Новейшая версия аватаров HeyGen. Проверяй поле `tags: ["AVATAR_IV"]` в ответе avatar details.

---

## 8. Assets & Upload

### Upload (POST upload.heygen.com/v1/asset)

```python
def upload_asset(file_path: str) -> str:
    """Upload file to HeyGen. Returns asset URL."""
    import mimetypes
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://upload.heygen.com/v1/asset",
            headers={"X-Api-Key": HEYGEN_API_KEY},
            files={"file": (os.path.basename(file_path), f, mime_type)}
        )
    data = resp.json()
    if data.get("error"):
        raise Exception(data["error"])
    return data["data"]["url"]
```

---

## 9. Webhooks

### Register (POST /v1/webhook/endpoint.add)

```python
def register_webhook(url: str, events: list[str] | None = None) -> dict:
    """Register webhook for video completion events."""
    payload = {"url": url}
    if events:
        payload["events"] = events

    resp = requests.post(
        f"{BASE_URL}/v1/webhook/endpoint.add",
        headers=headers,
        json=payload,
    )
    return resp.json()
```

Альтернатива polling — получай уведомления по HTTP когда видео готово.

---

## 10. Remotion Integration

### Choosing Format

| Composition | Recommended | Why |
|-------------|-------------|-----|
| Avatar + overlays поверх | **MP4** + background | Overlays идут сверху, transparency не нужна |
| Loom-style (avatar over screen recording) | **WebM** + `closeUp` | Нужна прозрачность, circle mask в CSS |
| Avatar floating над видео | **WebM** (transparent) | Нужно видеть контент за аватаром |
| Full-screen avatar | **MP4** + background | Стандартный подход |

### Key Rules

- **Всегда `OffthreadVideo`** вместо `Video` — frame-accurate rendering, без jitter
- WebM с `transparent` prop для альфа-канала
- Match dimensions: HeyGen output = Remotion composition
- HeyGen default 25 fps — учитывай при настройке Remotion fps
- Генерация 10-15+ мин — work in parallel, используй placeholder

### Remotion Composition Example

```tsx
import { OffthreadVideo, AbsoluteFill, Sequence } from "remotion";

export const AvatarWithOverlays: React.FC<{
  avatarVideoUrl: string;
}> = ({ avatarVideoUrl }) => {
  return (
    <AbsoluteFill>
      {/* Layer 1: Avatar video */}
      <OffthreadVideo
        src={avatarVideoUrl}
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      />

      {/* Layer 2: Animated title after 1s */}
      <Sequence from={30}>
        <div style={{
          position: "absolute", top: 50, left: 50,
          color: "white", fontSize: 48, fontWeight: "bold",
        }}>
          Welcome!
        </div>
      </Sequence>
    </AbsoluteFill>
  );
};
```

### Loom-Style: Circle Avatar Over Screen Recording

```tsx
export const LoomStyle: React.FC<{
  screenRecordingUrl: string;
  avatarWebmUrl: string; // via /v1/video.webm, avatar_style: "closeUp"
}> = ({ screenRecordingUrl, avatarWebmUrl }) => (
  <AbsoluteFill>
    <OffthreadVideo src={screenRecordingUrl} style={{ width: "100%", height: "100%" }} />
    <OffthreadVideo
      src={avatarWebmUrl}
      transparent
      style={{
        position: "absolute", bottom: 40, left: 40,
        width: 180, height: 180,
        borderRadius: "50%", overflow: "hidden", objectFit: "cover",
      }}
    />
  </AbsoluteFill>
);
```

---

## Multi-Scene Pipeline

Когда нужно длинное видео с разными фонами — генерируй каждую сцену отдельно в HeyGen, потом собирай локально через video_editor.py.

**Почему отдельные клипы:**
- Полный контроль per-scene: разные фоны, позиции, длительности
- Можно микшировать HeyGen-клипы с AI b-roll (VEO/Sora)
- Локальная сборка бесплатна — не тратишь кредиты на ре-рендеры

### Step 1: Generate N scene clips in parallel

```python
import os
import time
import requests

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
BASE_URL = "https://api.heygen.com/v2"
headers = {"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"}


def generate_scene(scene: dict, avatar_id: str, voice_id: str) -> str:
    """Submit one scene to HeyGen. Returns video_id."""
    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": scene.get("avatar_style", "normal"),
                "scale": scene.get("scale", 0.4),
                "position": scene.get("position", {"x": 0.5, "y": 0.85}),
            },
            "voice": {
                "type": "text",
                "input_text": scene["script"],
                "voice_id": voice_id,
                "speed": scene.get("speed", 1.0),
            },
            "background": scene["background"],
        }],
        "dimension": {"width": scene.get("width", 1920), "height": scene.get("height", 1080)},
    }
    resp = requests.post(f"{BASE_URL}/video/generate", headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["data"]["video_id"]


def wait_and_download(video_id: str, output_path: str, poll_interval: int = 10) -> str:
    """Poll until HeyGen job is done, then download to output_path."""
    while True:
        status_resp = requests.get(f"{BASE_URL}/video/{video_id}", headers=headers)
        data = status_resp.json()["data"]
        state = data["status"]

        if state == "completed":
            video_url = data["video_url"]
            content = requests.get(video_url).content
            with open(output_path, "wb") as f:
                f.write(content)
            print(f"Downloaded: {output_path}")
            return output_path
        elif state == "failed":
            raise RuntimeError(f"HeyGen job {video_id} failed: {data.get('error')}")

        print(f"  [{video_id[:8]}] status={state}, waiting {poll_interval}s...")
        time.sleep(poll_interval)


def generate_multi_scene(scenes: list, avatar_id: str, voice_id: str,
                         output_dir: str = ".") -> list:
    """
    Generate all scenes in parallel (submit all, then poll all).
    Returns list of downloaded clip paths in scene order.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Submit all scenes at once
    jobs = []
    for i, scene in enumerate(scenes):
        video_id = generate_scene(scene, avatar_id, voice_id)
        jobs.append({"index": i, "video_id": video_id,
                     "output": os.path.join(output_dir, f"scene_{i+1:02d}.mp4")})
        print(f"Submitted scene {i+1}/{len(scenes)}: {video_id}")

    # Poll all until done
    clips = [None] * len(jobs)
    pending = list(jobs)
    while pending:
        still_pending = []
        for job in pending:
            try:
                path = wait_and_download(job["video_id"], job["output"], poll_interval=0)
                clips[job["index"]] = path
            except RuntimeError:
                still_pending.append(job)
        if still_pending:
            pending = still_pending
            time.sleep(10)
        else:
            break

    return clips
```

### Step 2: Assemble with video_editor.py

```python
import subprocess


def assemble_scenes(clip_paths: list, output_path: str,
                    transition: str = "fade", transition_duration: float = 0.3) -> str:
    """Concat HeyGen clips locally using video_editor.py (FFmpeg)."""
    cmd = [
        "python",
        os.path.expanduser("~/.claude/skills/video-editor/video_editor.py"),
        "concat",
        *clip_paths,
        "--transition", transition,
        "--transition-duration", str(transition_duration),
        "-o", output_path,
    ]
    subprocess.run(cmd, check=True)
    return output_path
```

### Step 3: Full orchestration example

```python
# Define scenes
scenes = [
    {
        "script": "Привет! Сегодня я расскажу вам о новом продукте.",
        "background": {"type": "color", "value": "#0f0f1a"},
        "avatar_style": "normal",
    },
    {
        "script": "Ключевые преимущества: скорость, простота, результат.",
        "background": {"type": "image", "url": "https://example.com/slide2.png"},
        "avatar_style": "circle",
        "position": {"x": 0.8, "y": 0.8},
    },
    {
        "script": "Попробуйте бесплатно по ссылке в описании.",
        "background": {"type": "color", "value": "#1a0f0f"},
    },
]

AVATAR_ID = "YOUR_HEYGEN_AVATAR_ID_1"  # User_Горизонталь_Сидячий
VOICE_ID = "YOUR_HEYGEN_VOICE_ID_1"    # User_pro voice

# 1. Generate all scenes in parallel
clips = generate_multi_scene(scenes, AVATAR_ID, VOICE_ID, output_dir="./heygen_clips")

# 2. Assemble into one video
final = assemble_scenes(clips, "final_video.mp4", transition="fade")

# 3. Optional: add captions via SubtitleService
# add_submagic_captions(final, "final_with_subs.mp4", style="hormozi")

print(f"Done: {final}")
```

### Decision: single multi-slide vs separate scenes

| Approach | When to use |
|---------------------------------|----------------------------------------------------------------------------------|
| Single `video_inputs` array | Simple presentation, same layout per slide, no b-roll |
| Separate clips + local assembly | Different layouts per scene, mixing with AI video, re-render individual scenes |

---

## Integration with Other Skills

| Step | Tool | What it does |
|------|------|-------------|
| 1 | Claude / GPT | Генерация скрипта |
| 2 | Gamma / Manus Slides | Генерация слайдов / презентаций |
| 3 | **HeyGen** (Video Agent или v2 API) | Avatar видео |
| 4 | **HeyGen** (Workflow Gateway) | AI b-roll (VEO/Kling/Sora) |
| 5 | video_editor.py | Склейка, переходы, overlay |
| 6 | **HeyGen** (Starfish TTS) | Standalone озвучка |
| 7 | SubtitleService | Каptions / субтитры |
| 8 | **HeyGen** (Video Translate) | Локализация |
| 9 | **HeyGen** (Faceswap) | Замена лица |
| 10 | Remotion | Программный композитинг |
| 11 | ElevenLabs | Альтернативная озвучка |
| 12 | Deepgram | Транскрипция |

```python
# Полный pipeline пример:
# 1. Generate script with Claude
script = generate_script_with_claude(topic)

# 2. Generate slides with Gamma
slides = create_presentation_with_gamma(script)

# 3. Create avatar video with HeyGen
video = generate_avatar_video(script)

# 4. Add AI b-roll via Workflow Gateway
broll = generate_ai_video("cinematic product shot", provider="veo_3_1")

# 5. Assemble with video_editor.py
final = assemble_scenes([video, broll], "final.mp4")

# 6. Add captions with SubtitleService
final_video = add_captions_with_submagic(final)

# 7. Translate to Spanish
spanish = translate_video({"video_url": final_video, "output_language": "es-ES"})
```

---

## Complete API Endpoint Map

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/video_agent/generate` | Video Agent (prompt-to-video) |
| `POST` | `/v2/video/generate` | Avatar video (precise control) |
| `POST` | `/v1/video.webm` | Transparent WebM video |
| `GET` | `/v2/videos/{video_id}` | Video status & download URL |
| `GET` | `/v2/videos` | List account videos |
| `DELETE` | `/v2/videos/{video_id}` | Delete video |
| `GET` | `/v2/avatars` | List avatars |
| `GET` | `/v2/avatar/{avatar_id}/details` | Avatar details + default voice |
| `GET` | `/v2/avatar_group.list` | List avatar groups |
| `GET` | `/v2/avatar_group/{id}/avatars` | Avatars in group |
| `GET` | `/v2/voices` | List video voices |
| `GET` | `/v1/audio/voices` | List Starfish TTS voices |
| `POST` | `/v1/audio/text_to_speech` | Starfish TTS generation |
| `POST` | `/v1/workflows/executions` | Workflow Gateway (video gen, faceswap) |
| `GET` | `/v1/workflows/executions/{id}` | Workflow status |
| `POST` | `/v2/video_translate` | Submit video translation |
| `GET` | `/v2/video_translate/{id}` | Translation status |
| `POST` | `upload.heygen.com/v1/asset` | Upload asset (image/video/audio) |
| `POST` | `/v1/webhook/endpoint.add` | Register webhook |
| `POST` | `/v2/voice/clone` | Clone voice from audio |

---

## Pricing & Credits

| Plan | Credits/month | Best For |
|------|---------------|----------|
| Free | 1 credit | Testing |
| Creator | 15 credits | Individuals |
| Business | 60 credits | Teams |
| Enterprise | Unlimited | Large orgs |

**Tips:** `test: true` в payload = watermarked video, 0 credits. Используй для разработки.

---

## Tips

1. **Короткие предложения** — лучшая синхронизация губ
2. **Паузы** — `<break time="1s"/>` для естественных пауз (пробелы до и после!)
3. **Тест голоса** — проверь произношение терминов перед продакшном
4. **Фон 16:9** — для презентаций используй landscape
5. **Portrait 9:16** — для TikTok/Reels
6. **Default voice** — используй `default_voice_id` аватара для наилучшего lip-sync
7. **Timeout 20 min** — генерация занимает 10-15+ мин, не ставь маленький timeout
8. **test: true** — тестируй без траты кредитов (водяной знак)
9. **Prompt Optimizer** — разница между средним и профессиональным результатом = качество промпта
10. **B-roll >= 10s** — короче 5 секунд = чёрные кадры
11. **Motion verbs** — SLAMS, CASCADE, COUNTS UP вместо координат
12. **Layer system** — 4+ слоёв на каждый B-roll, каждый элемент двигается
13. **Scene rotation** — чередуй A-roll / B-roll / Overlay, никогда 3+ одинаковых
14. **VOICEOVER everywhere** — каждая сцена включая B-roll должна иметь озвучку
15. **Word timestamps** — используй `word_timestamps` из TTS для субтитров
16. **Parallel generation** — submit все сцены сразу, poll все параллельно
17. **WebM only for transparency** — для обычных видео используй MP4
18. **OffthreadVideo** — в Remotion всегда `OffthreadVideo`, не `Video`
19. **URL expiration** — HeyGen URLs живут ~24 часа, скачивай для повторного использования
20. **Deconstructed style** — самый надёжный визуальный стиль для Video Agent
