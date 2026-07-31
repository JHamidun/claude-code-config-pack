# Veo 3.1 (Google GenAI) + Sora (OpenAI) — direct API

## §1 — Veo 3.1 setup

```python
import os
# CRITICAL: GEMINI_API_KEY в env конфликтует с GOOGLE_API_KEY,
# SDK читает не тот → Veo calls fail silently
os.environ.pop('GEMINI_API_KEY', None)

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
```

Модели:
- `veo-3.1-fast-generate-001` — $0.10/s, для шортсов
- `veo-3.1-generate-001` (Full) — $0.40/s, для cinematic

## §2 — Text-to-video

```python
op = client.models.generate_videos(
    model='veo-3.1-fast-generate-001',
    prompt='Quiet pause. Solitary figure in minimal interior. Locked tripod, 50mm anamorphic.',
    config=types.GenerateVideosConfig(
        aspect_ratio='9:16',  # или '16:9', '1:1'
        duration_seconds=5,
        number_of_videos=1,
        person_generation='allow_adult',
    ),
)

import time
while not op.done:
    time.sleep(10)
    op = client.operations.get(op)

video = op.response.generated_videos[0].video
client.files.download(file=video)
video.save('out.mp4')
```

## §3 — Image-to-video (keyframe)

```python
with open('keyframe.png', 'rb') as f:
    img_bytes = f.read()

op = client.models.generate_videos(
    model='veo-3.1-fast-generate-001',
    prompt='Eyes slowly open. Subtle head turn. Locked tripod, 50mm anamorphic.',
    image=types.Image(image_bytes=img_bytes, mime_type='image/png'),  # CRITICAL syntax
    config=types.GenerateVideosConfig(
        aspect_ratio='9:16',
        duration_seconds=5,
    ),
)
```

**Грабли:** `image=path_str` silently degrades to text-only generation. ВСЕГДА `types.Image(image_bytes=..., mime_type=...)`.

First и end frame нужны разные — Veo интерполирует motion (не как Seedance).

## §4 — Safety filter: NoneType silent rejects

Veo отвергает безобидные слова и возвращает `NoneType` вместо exception:

- `awkward silence` → NoneType
- `tension` → NoneType
- `lonely` → NoneType
- `empty room` → NoneType
- `shadow figure` → NoneType
- `dark` → NoneType (часто)

Soften-and-retry pattern:

```python
SAFETY_SOFTENER = {
    'awkward silence': 'quiet pause',
    'tension': 'stillness',
    'lonely': 'solitary',
    'empty room': 'minimal interior',
    'shadow figure': 'silhouette',
    'dark': 'dim',
}

def soften(prompt: str) -> str:
    for bad, good in SAFETY_SOFTENER.items():
        prompt = prompt.replace(bad, good)
    return prompt

def generate_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        op = run_veo(prompt)
        if op.response and op.response.generated_videos:
            return op
        prompt = soften(prompt)
    raise RuntimeError(f'Veo silently rejected after {max_retries} softening attempts')
```

## §5 — Concurrency ceiling

**Reliable max = 3 concurrent.** 5+ = `RESOURCE_EXHAUSTED` или silent empty responses.

```python
import asyncio
SEM = asyncio.Semaphore(3)

async def gen_one(prompt, img):
    async with SEM:
        return await run_veo_async(prompt, img)

results = await asyncio.gather(*[gen_one(p, i) for p, i in shots])
```

## §6 — Native audio caveat

Veo 3.1 Fast/Full ВСЕГДА генерит native ambient sound (+ optional music). Если будешь миксить external ElevenLabs VO:

**Option A** — strip Veo audio перед mix:

```bash
ffmpeg -i veo_out.mp4 -an -c:v copy veo_silent.mp4
```

**Option B** — миксить с native audio (бывает шумно, ducking обязателен).

## §7 — person_generation flags

| Flag | Поведение |
|---|---|
| `allow_adult` | OK для большинства narrative shots |
| `allow_all` | Включая детей — для детских книг (Terra) |
| `dont_allow` | Только окружение / абстракция |

Не передавать → дефолт `allow_adult`.

## §8 — Sora через OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

resp = client.videos.create(
    model='sora-2',
    prompt='Slow zoom over Cyrillic title text. ARRI Alexa, 50mm anamorphic.',
    duration_seconds=5,
    size='1920x1080',
)

# Poll
import time
while resp.status not in ('completed', 'failed'):
    time.sleep(10)
    resp = client.videos.retrieve(resp.id)

video_url = resp.output[0].url
```

## §9 — Provider selection: Veo vs Sora

| Use case | Provider | Почему |
|---|---|---|
| Кириллический текст в кадре | **Sora** | Veo корёжит кириллицу → «иероглифы» |
| Native audio из коробки | **Veo Full** | Sora native audio слабее |
| Cinematic 4K composition | **Veo Full** | Лучшая raw composition |
| Cheap shortform 5s | **Veo Fast** | $0.10/s vs Sora ~$0.08/s — близко, но Veo надёжнее |
| Длинные (>10s) | **Sora** | Veo cap 8s |

## §10 — Cost cheatsheet

| Model | Cost/sec | Typical 5s shot |
|---|---|---|
| Veo 3.1 Fast | $0.10 | $0.50 |
| Veo 3.1 Full | $0.40 | $2.00 |
| Sora 2 | ~$0.08 | $0.40 |
| Seedance 2.0 (Runway Unlimited) | $0 marginal | $0 |
