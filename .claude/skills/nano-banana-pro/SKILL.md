---
name: nano-banana-pro
description: "Prompt engineering Nano Banana Pro (Gemini Image): реставрация фото, VK-креативы без VPN. Триггеры: «восстанови фото», «шакальная фотка»."
---

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

# Nano Banana Pro / Gemini Image Ultra - Prompt Engineering Guide

> **See Also:**
> - **[image-generation](image-generation.md)** - General prompt engineering for all image generators
> - **[gemini-3-pro](gemini-3-pro.md)** - Full Gemini suite: Imagen 3, Veo 2, TTS, Live API
> - **[openai-dalle](openai-dalle.md)** - OpenAI suite: DALL-E 3, Sora 2, Whisper
> - **[references/vk-ads-creatives.md](references/vk-ads-creatives.md)** - VK Ads сюрреалист-креативы (метод эксперта, Магритт/Дали) через Gemini вместо DALL-E 3 — без VPN из РФ, выше качество

## Multi-Image Consistency via Reference Chaining (CRITICAL)

Nano Banana Pro / Gemini Image **НЕ сохраняет identity** между separate `generate_content` calls. Каждый вызов = independent generation. Для multi-frame consistency (keyframes для image-to-video, серия иллюстраций, character lock) нужен reference-chaining.

### Pattern: forward chaining + periodic re-anchor

```python
# Новый SDK (канон dont-do: НЕ google.generativeai). Ключ: GOOGLE_API_KEY (не GEMINI_API_KEY — конфликт SDK).
import os
os.environ.pop('GEMINI_API_KEY', None)
from google import genai
from google.genai import types

client = genai.Client()  # берёт GOOGLE_API_KEY из env
MODEL = 'gemini-3-pro-image-preview'
CFG = types.GenerateContentConfig(response_modalities=['IMAGE', 'TEXT'])

def img_part(resp):
    return next(p.inline_data for p in resp.candidates[0].content.parts if p.inline_data)

# Шаг 1: generate первый keyframe
resp1 = client.models.generate_content(model=MODEL, config=CFG,
    contents=['Watercolor children illustration of a small figure in a misty forest. 21:9 cinemascope.'])
img1 = img_part(resp1)

# Шаг 2: feed output back as reference
resp2 = client.models.generate_content(model=MODEL, config=CFG, contents=[
    types.Part.from_bytes(data=img1.data, mime_type='image/png'),
    'Same character, same style. Now standing at edge of glowing river.'
])
img2 = img_part(resp2)

# Шаг 3: chain forward
resp3 = client.models.generate_content(model=MODEL, config=CFG, contents=[
    types.Part.from_bytes(data=img2.data, mime_type='image/png'),
    'Same character, same style. Now kneeling beside ancient glyph stone.'
])
img3 = img_part(resp3)

# Шаг 4: RE-ANCHOR к img1 (НЕ к img3), иначе drift
resp4 = client.models.generate_content(model=MODEL, config=CFG, contents=[
    types.Part.from_bytes(data=img1.data, mime_type='image/png'),   # ← anchor!
    'Same character, same style. Now walking through cloud-tops at dawn.'
])
```

### Drift behaviour

Forward-chaining alone drifts после ~4 hops:
- Hop 1-2: identity tight
- Hop 3-4: minor stylistic shifts
- Hop 5+: noticeable face / proportion drift

**Re-anchor каждые 3 шага к original output1** стабилизирует multi-frame consistency.

### Parallelism ceiling

**~4 concurrent `generate_content` calls reliable.** 5+ = `RESOURCE_EXHAUSTED`.

```python
import asyncio
SEM = asyncio.Semaphore(4)

async def gen_one(ref_img, prompt):
    async with SEM:
        return await model.generate_content_async([ref_img, prompt])
```

### 21:9 cinemascope native support

Nano Banana Pro **natively** генерит 21:9 cinemascope без post-crop. GPT Image 1.5 cap = 3:2 (post-crop теряет composition).

Для cinematic trailers с заранее заданным aspect — Nano Banana Pro единственный mainstream option без crop-loss.

```python
resp = model.generate_content([
    'Ultra-wide 21:9 cinemascope shot. Photorealistic. The figure walks through misty ruins.'
])
```

### Universal pattern: reference image works across providers

Generate ОДИН раз, reuse через Seedance / Veo / Sora / GPT Image. Separate reference per character для multi-character series.

Подробнее по image-to-video использованию keyframes → `video-generation/SKILL.md` Phase 4 (keyframing rules).

## Photo Restoration (Low-Quality → HD)

Use this template to restore old/blurry/compressed photos while preserving identity, pose, and composition. Works best with Nano Banana Pro / Gemini 3 Pro Image.

### Master Template (RU)

```
ДИРЕКТИВА: Выполнить реставрацию ультра-верности и кинематографический
перерендеринг изображения-источника. Главная цель — «Аналитическая
Реконструкция Микро-Деталей» на основе источника низкого качества.

СУБЪЕКТ: [описание основного субъекта — человек/объект/животное]
КРИТИЧЕСКИ ВАЖНО: Структура лица, идентичное выражение и точная поза
должны СТРОГО СОВПАДАТЬ с предоставленным изображением-источником.
Требуется 100%-ная верность идентичности.

РЕКОНСТРУИРУЕМЫЕ ДЕТАЛИ:
- Экстремальное восстановление текстур кожи (поры, микро-морщины)
- Реалистичные индивидуализированные пряди волос
- Кристально чистые глаза с чёткими бликами
- Чистые и чётко очерченные края одежды и аксессуаров

СЦЕНА: Точная копия оригинальной композиции.
КАДРИРОВАНИЕ: [Close-up | Medium Shot | Full Body], Правило Трети.
ОКРУЖЕНИЕ: Реконструкция оригинального фона. Увеличить глубину резкости
для разделения субъекта и окружения, устранить артефакты и шум.

ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:
- КАМЕРА: Объектив 85 мм, апертура f/1.8 (bokeh)
- ОСВЕЩЕНИЕ: Сбалансированное Кинематографическое (Rembrandt Lighting),
  высокий контраст, детали в тенях сохранены, точные зеркальные блики
- КАЧЕСТВО: 8K, Фотореалистичные Текстуры, ProRes, Студийная Чёткость

ОРИЕНТИР: Прикрепленное изображение — ЕДИНСТВЕННЫЙ источник структуры
и идентичности. НЕ додумывать черты.

НЕГАТИВНЫЙ ПРОМПТ: Размытость, нечёткость, визуальный шум, артефакты
сжатия, изменение идентичности, изменение выражения, изменение позы,
изменение одежды, добавление объектов, перерисовка, вид рисунка или
картины, низкое разрешение, AI-look, uncanny valley.
```

### Master Template (EN)

```
DIRECTIVE: Execute ultra-fidelity restoration and cinematic re-render of
the source image. Primary goal — "Analytical Micro-Detail Reconstruction"
from the low-quality source.

SUBJECT: [main subject description]
CRITICAL: Facial structure, identical expression, and exact pose must
STRICTLY MATCH the source image. 100% identity fidelity required.

RECONSTRUCTED DETAILS:
- Extreme recovery of natural skin textures (visible pores, micro-wrinkles)
- Realistic individualized hair strands
- Crystal-clear eyes with defined catchlights
- Clean, well-defined edges on clothing and accessories

SCENE: Exact copy of original composition.
FRAMING: [Close-up | Medium Shot | Full Body], Rule of Thirds.
ENVIRONMENT: Reconstruct original background. Increase DOF for subtle
but clear subject/environment separation. Eliminate artifacts and noise.

TECHNICAL SPECS:
- CAMERA: 85mm lens, f/1.8 aperture (soft bokeh)
- LIGHTING: Balanced Cinematic Lighting (Rembrandt), high contrast,
  preserved shadow detail, precise specular highlights
- OUTPUT QUALITY: 8K resolution, photoreal textures, ProRes quality,
  studio clarity, poster-grade realism

REFERENCE: Attached image is the ONLY reference for structure and
identity. Do not invent features.

NEGATIVE PROMPT: Blur, softness, visual noise, compression artifacts,
identity change, expression change, pose change, clothing change,
added objects, repainting, painterly look, low resolution, AI-look,
uncanny valley.
```

### Variations

**Portrait close-up:** Change `КАДРИРОВАНИЕ` to `Close-up (поясной план)`, camera to `135mm f/2.0`.

**Full-body restoration:** `Full Body`, camera `35mm f/2.8`, lighting `Natural Soft Light`.

**B&W → Color:** Add `Колоризация: исторически точные цвета эпохи [1950s/1980s/etc.]`.

**Group photo:** Add `Сохранить идентичность КАЖДОГО человека отдельно, без смешения черт`.

### Tips

1. **Always attach the source image** — Nano Banana needs visual reference, not just description
2. **Specify era for B&W** — "1960s photo" gives better color choices than generic "restore colors"
3. **Don't over-describe the person** — let the source image dictate features; describe only unchangeable traits (glasses, beard, scar)
4. **Test with a crop first** — restoration quality varies; try a face-only crop before full image
5. **Use Ultra model for final** — Nano Banana Pro / Gemini 3 Pro Image, not Flash Image, for max detail

## Каталог параметров съёмки

Конкретные камеры и объективы (85mm f/1.4 → портрет, Hasselblad X2D → фэшн), схемы света
(Rembrandt / butterfly / split), плёночные стоки (Portra 400, Cinestill 800T), JSON-схема
промпта и шаблоны под e-commerce / editorial / архитектуру — **`references/photo-prompt-catalog.md`**.
Читать, когда фотореализм задаётся техникой съёмки; для реставрации не нужно — там параметры
уже в мастер-шаблоне выше.
