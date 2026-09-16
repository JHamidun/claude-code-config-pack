# Veo 3.1 (Google GenAI) — direct API

> Sora (OpenAI) остаётся в файле только как §8: продукт выключается 24.09.2026,
> рабочего рецепта под него здесь больше нет. Второй живой провайдер видео —
> Seedance 2.5 у Runway, его прайс и состояние доступа в §9–§10.

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

**Проверено на ai.google.dev 09.09.2026** — идентификаторы, статус и даты выпуска.
Все три — Preview, GA у Veo 3.1 нет:

- `veo-3.1-fast-generate-preview` — шортсы (15.10.2025)
- `veo-3.1-generate-preview` (Full) — cinematic (15.10.2025)
- `veo-3.1-lite-generate-preview` — (31.03.2026)

Цены ниже — **из прежней редакции и НЕ перепроверены** сегодня: Fast $0.10/s,
Full $0.40/s. Про lite цены нет вовсе — здесь стояло «самая дешёвая из трёх»,
а это догадка по имени, попавшая под штамп «проверено».

⚠️ До 09.09.2026 здесь стояли `veo-3.1-fast-generate-001` и `veo-3.1-generate-001`.
Суффикс `-001` бывает у GA-моделей, а Veo 3.1 в GA не выходила: на ai.google.dev
перечислены ровно три идентификатора, и все они `-preview`. Скопированный отсюда
ID указывал на модель, которой в списке нет, — и ошибка выглядела как проблема
ключа, а не как опечатка в доке. Дата снятия preview-версий не объявлена.

## §2 — Text-to-video

```python
op = client.models.generate_videos(
    model='veo-3.1-fast-generate-preview',
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
    model='veo-3.1-fast-generate-preview',
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

## §8 — ⛔ Sora: рецепта больше нет, продукт закрывается 24.09.2026

OpenAI выключает **весь Videos API целиком**: модели `sora-2`, `sora-2-pro`, все
датированные снапшоты и сам эндпоинт `/v1/videos`. Замены он не предложил — это
не переименование, а уход с рынка.

Рабочий код отсюда убран намеренно. Он проживёт пятнадцать дней и всё это время
будет выглядеть исправным, а потом отдаст ошибку эндпоинта, по которой поломку
принимают за свою.

**Чем это било именно здесь.** Sora брали ровно за одно: **кириллицу на кадре**,
которую Veo корёжит. Этой замены нет ни у кого. Значит, приём меняется, а не
провайдер: русский текст кладём **оверлеем на монтаже** (`video-editor`,
`remotion-overlays`), а у модели просим кадр без надписей.

Остаток кода Sora живёт в `scripts/direct_video.py` до самой даты, но за гейтом:
после 24.09 он отказывается работать внятным текстом, а не разбором чужого 404.

<details>
<summary>Как звался вызов (для чтения старых логов, не для копирования)</summary>

```python
resp = client.videos.create(model='sora-2', prompt='...',
                            duration_seconds=5, size='1920x1080')
```

⚠️ Даже эта строка была неверной: боевой `direct_video.py` слал `seconds` и
`size`, а не `duration_seconds` — то есть пример в доке не работал и до снятия.
</details>
```

## §9 — Provider selection: Veo vs Seedance

| Use case | Provider | Почему |
|---|---|---|
| Кириллический текст в кадре | **ни один** — надпись оверлеем на монтаже | Veo корёжит кириллицу, а Sora выключается 24.09.2026 (§8) и замены ей нет |
| Native audio из коробки | **Veo Full** или **Seedance 2.5** | у Seedance тумблер Audio есть во всех четырёх режимах |
| Кинематографичная композиция | **Veo Full** | Лучшая raw composition. Здесь стояло «4K» — в доках Gemini API это не подтверждено |
| Cheap shortform 5s | **Veo Fast** | $0.10/s, платится деньгами, а не остатком кредитов Runway |
| Длинные (>10s) | **Seedance 2.5** | 4–30 с (или Auto) из одной генерации; у Veo cap 8s |
| Несколько сцен и ракурсов в одном ролике | **Seedance 2.5** | мультикадр выходит ИЗ ОДНОЙ генерации, склеивать клипы не надо |

⚠️ Строки про Sora («кириллица → Sora», «>10 с → Sora») стояли здесь до
09.09.2026 и противоречили §8 этого же файла, где продукт уже помечен снятым.
Тот, кто читал таблицу, а не §8, уходил строить пайплайн на закрывающемся API.

## §10 — Cost cheatsheet

| Model | Cost/sec | Typical 5s shot |
|---|---|---|
| Veo 3.1 Fast | $0.10 | $0.50 |
| Veo 3.1 Full | $0.40 | $2.00 |
| ~~Sora 2~~ | — | продукт выключается 24.09.2026, см. §8 |
| Seedance 2.5 @ 480p | 20 кредитов Runway | 100 кредитов |
| Seedance 2.5 @ 720p | 30 кредитов Runway | 150 кредитов |
| Seedance 2.5 @ 1080p | 68 кредитов Runway | 340 кредитов |

Входное видео (режимы Reference / Edit / Extend) добавляет **половину ставки за
каждую секунду входа**: +10 / +15 / +34 кредита в секунду для 480p / 720p / 1080p.

⚠️ Расхождение на самих страницах Runway: таблица спеков в справке перечисляет
480p, 720p и 1080p (и тут же даёт цену за 1080p), а FAQ на продуктовой странице
говорит про «480p and 720p». Считать по таблице, но не удивляться, если 1080p не
окажется в интерфейсе.

⚠️ **«$0 marginal» — то, что здесь стояло до 09.09.2026, и это было верно только
при живой платной подписке.** Строка «Seedance 2.0 (Runway Unlimited) | $0
marginal | $0» приглашала считать Runway бесплатным по умолчанию, тогда как
кредиты у него расходуются всегда, а «бесплатность» держалась ровно на одном
условии — оплаченном плане. На сегодня условие не выполняется: `RUNWAY_JWT`
просрочен с 31.07.2026 (40 дней), любой вызов отдаёт 401, и ещё 22.06.2026
подписка уже сваливалась на free plan, где Runway отказывал и в explore, и в
stable. Порядок проверки — сперва **план** в `/v1/profile`, только потом токен
(`runway_client.py token-status` — offline-проверка срока). Обновление токена
само по себе может ничего не вернуть, если план не платный.
