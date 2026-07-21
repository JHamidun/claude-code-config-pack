---
name: nano-banana-pro
description: "Nano Banana Pro / Gemini Image Ultra - Prompt Engineering Guide"
---

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

# Nano Banana Pro / Gemini Image Ultra - Prompt Engineering Guide

> **See Also:**
> - **[image-generation](image-generation.md)** - General prompt engineering for all image generators
> - **[gemini-3-pro](gemini-3-pro.md)** - Full Gemini suite: Imagen 3, Veo 2, TTS, Live API
> - **[openai-dalle](openai-dalle.md)** - OpenAI suite: DALL-E 3, Sora 2, Whisper

## Overview

This skill provides expert-level prompts for photorealistic and creative image generation using Nano Banana Pro (Gemini Pro Image Ultra).

## Core Prompt Categories

### 1. Photorealism & Professional Photography

#### Camera & Equipment Specifications
```
Ultra-sharp, full-color large-format image shot with [Camera] and [Lens]
```

**Best Cameras:**
- Sony A7III, Sony A7R IV - detail & dynamic range
- Canon EOS R5 - fast autofocus, video
- Nikon Z9 - sports, action
- Hasselblad X2D - medium format, fashion
- RED V-Raptor - cinematic

**Best Lenses:**
- 85mm f/1.4 - portraits, bokeh
- 50mm f/1.2 - natural perspective
- 35mm f/1.4 - environmental portraits
- 24-70mm f/2.8 - versatility
- 70-200mm f/2.8 - compression, sports

#### Lighting Setups
```
Three-point lighting setup:
- Key light at 45 degrees (warm, 5600K)
- Fill light at -30 degrees (soft, 50% intensity)
- Rim light from behind (golden, highlights hair/shoulders)
- Vignette effect for focus
```

**Lighting Terms:**
- Golden Hour - warm, soft, magical
- Blue Hour - cool, moody, cinematic
- Rembrandt lighting - triangle shadow on cheek
- Butterfly lighting - shadow under nose, beauty
- Loop lighting - slight shadow on opposite side
- Split lighting - dramatic half-face shadow

#### Film Aesthetics
```
Shot on [Film Stock], [ISO], natural film grain
```

**Film Stocks:**
- Kodak Portra 400 - warm skin tones, wedding
- Kodak Ektar 100 - vivid colors, landscape
- Fuji Pro 400H - soft pastels, fashion
- Ilford HP5 - classic B&W, street
- Cinestill 800T - cinematic, tungsten, halation

### 2. Portrait Prompts

#### Professional Headshot
```json
{
  "subject": {
    "age": 35,
    "gender": "female",
    "expression": "confident smile, eyes engaged",
    "skin": "natural texture with visible pores, subtle makeup",
    "hair": "styled professionally, individual strands visible"
  },
  "photography": {
    "camera": "Sony A7III",
    "lens": "85mm f/1.4",
    "aperture": "f/2.0",
    "lighting": "soft natural light from large window, reflector fill"
  },
  "style": {
    "background": "clean gradient, subtle bokeh",
    "color_grade": "neutral with slight warmth",
    "quality": "8K resolution, ultra-sharp focus on eyes"
  },
  "preserve_original": true
}
```

#### Emotional Film Photography
```
Golden Hour portrait of [subject], shot on Kodak Portra 400
Natural backlight creating golden rim around hair
Soft catchlights in eyes, natural skin texture
Expression: [emotion] - subtle, genuine
Background: [setting] with beautiful bokeh
Film grain: subtle, organic
```

#### 2000s Mirror Selfie (Nostalgia)
```json
{
  "era": "2000s",
  "setting": "bathroom mirror selfie",
  "subject": {
    "clothing": ["low-rise jeans", "baby tee", "chunky belt"],
    "accessories": ["flip phone", "dangly earrings", "butterfly clips"],
    "pose": "classic mirror selfie angle"
  },
  "aesthetics": {
    "quality": "early digital camera, slight blur",
    "flash": "direct flash, harsh shadows",
    "color": "slightly oversaturated",
    "timestamp": "bottom right corner"
  }
}
```

### 3. Creative & Experimental

#### Dense Crowd Compositions
```
Aerial view of massive crowd gathered in [location]
Thousands of people, each with distinct features and clothing
"Where's Waldo" style complexity
Every person has unique appearance, no repetition
Photorealistic quality, natural lighting
```

#### Temporal Consistency (Age Progression)
```
Photo series of same person aging through the years:
- Age 20: [description]
- Age 40: [description]
- Age 60: [description]
- Age 80: [description]
Keep facial features exactly consistent across all ages
Same bone structure, eye shape, unique characteristics
```

#### Recursive/Infinite Loop (Droste Effect)
```
Image containing itself recursively (Droste effect)
[Subject] holding a frame showing the same scene
Infinite regression, each iteration smaller but detailed
Mathematical precision in the recursion
```

#### Coordinate-Based Generation
```
Photograph taken at exact coordinates:
Latitude: [X], Longitude: [Y]
Time: [HH:MM], Date: [YYYY-MM-DD]
Season: [season]
Weather conditions: [weather]
Capture the atmosphere and location authentically
```

#### Conceptual Interpretations
```
"How [profession] sees [object]"
Example: "How engineers see the Golden Gate Bridge"
- Show technical annotations
- Structural analysis overlays
- Material specifications
- Force vectors and stress points
```

### 4. Technical Best Practices

#### Face Preservation (Critical for consistency)
```
ALWAYS include in prompts for consistent faces:
- "Keep facial features exactly consistent"
- "preserve_original: true"
- "Same bone structure, eye shape, nose, lips"
- Reference specific features to maintain
```

#### Detail Emphasis
```
Request micro-details:
- "Individual hair strands visible"
- "Natural skin pores and texture"
- "Fabric fibers and weave pattern"
- "Reflections in eyes showing light source"
- "Subtle imperfections for realism"
```

#### Quality Specifiers
```
Resolution & Quality keywords:
- "8K resolution"
- "Ultra-sharp"
- "RAW quality"
- "Uncompressed"
- "Professional retouching"
- "Magazine quality"
```

### 5. Structured JSON Prompt Format

For maximum control, use JSON structure:

```json
{
  "image_type": "portrait | landscape | product | abstract",
  "subject": {
    "description": "detailed subject description",
    "age": "approximate age if person",
    "expression": "emotional state",
    "clothing": ["item1", "item2"],
    "accessories": ["item1", "item2"],
    "pose": "body position description"
  },
  "environment": {
    "setting": "location description",
    "time_of_day": "golden hour | midday | night | etc",
    "weather": "sunny | overcast | rain | etc",
    "background": "background details"
  },
  "photography": {
    "camera": "camera model",
    "lens": "lens specification",
    "aperture": "f-stop value",
    "shutter_speed": "if relevant",
    "iso": "ISO value",
    "film_stock": "if film aesthetic"
  },
  "lighting": {
    "type": "natural | studio | mixed",
    "key_light": "main light description",
    "fill_light": "fill light if any",
    "rim_light": "rim/back light if any",
    "color_temperature": "warm | neutral | cool"
  },
  "style": {
    "color_grade": "color palette description",
    "mood": "emotional tone",
    "quality": "resolution and sharpness",
    "post_processing": "editing style"
  },
  "constraints": {
    "preserve_original": true,
    "avoid": ["elements to avoid"],
    "emphasis": ["elements to emphasize"]
  }
}
```

### 6. Use Case Templates

#### E-commerce Product
```
Professional product photography of [product]
White seamless background, soft diffused lighting
Multiple catch lights for dimension
Sharp focus throughout, no shadows on background
8K resolution, color-accurate
```

#### Social Media Portrait
```
Instagram-worthy portrait of [subject]
[Setting] with aesthetic background
Natural posing, candid feel
Soft editing, skin smoothing (subtle)
Square format, centered composition
Warm color grade, slight lift in shadows
```

#### Editorial Fashion
```
High-fashion editorial shot for [magazine]
Model wearing [outfit] in [setting]
Dramatic lighting, strong shadows
Bold color story: [colors]
Shot by [photographer style reference]
Full-length, dynamic pose
```

#### Real Estate/Architecture
```
Architectural photography of [building/interior]
Wide-angle lens (24mm), straight verticals
HDR technique, balanced exposure
Blue hour exterior / natural light interior
Clean, aspirational aesthetic
Remove distracting elements
```

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

### When to Use

| Input | Best For |
|-------|----------|
| Old family photos | Restoration with identity preservation |
| Low-res screenshots | Upscaling with detail recovery |
| Compressed JPEGs | Artifact removal + micro-detail recovery |
| Scanned prints | Texture reconstruction, scratch removal |
| Blurry phone photos | Sharpness + studio-grade re-render |

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

## Quick Reference Card

| Goal | Key Terms |
|------|-----------|
| Sharp portrait | 85mm f/1.4, eye focus, catchlights |
| Cinematic | 35mm, shallow DOF, film grain, color grade |
| Natural | Golden hour, soft light, candid pose |
| Professional | Studio lighting, clean background, sharp |
| Vintage | Film stock, grain, era-specific styling |
| Dramatic | High contrast, Rembrandt lighting, shadows |
| Soft/Dreamy | Backlit, overexposed background, pastel |

## Common Mistakes to Avoid

1. **Vague descriptions** - Be specific about every element
2. **Missing lighting** - Always specify light source and quality
3. **Generic cameras** - Name specific equipment for realism
4. **Ignoring background** - Background affects entire image mood
5. **Skipping texture** - Request micro-details for realism
6. **No color direction** - Specify color palette and temperature
