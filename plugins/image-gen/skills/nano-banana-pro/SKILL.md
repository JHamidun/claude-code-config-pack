---
name: nano-banana-pro
description: "Prompt engineering Nano Banana Pro (Gemini Image): перерендер и реставрация фото, VK-креативы без VPN. Триггеры: «восстанови фото», «шакальная фотка». НЕ апскейл→image-enhancer."
---

> ⚠️ **NO-KEY GUARD (обязательно):** этот функционал требует ОПЦИОНАЛЬНОГО стороннего API-ключа. Перед вызовом проверь ключ в `.credentials.master.env`. Если ключ отсутствует, пустой или placeholder (`your_*_api_key`) — **НЕ проси пользователя оплатить счёт, включить биллинг или купить API**. Скажи одной строкой: «Эта функция опциональна и требует свой API-ключ (например, бесплатный ключ на aistudio.google.com); из коробки всё остальное работает по подписке Claude» — и предложи альтернативу или продолжай без неё.

# Nano Banana Pro / Gemini Image Ultra — Prompt Engineering

> **See Also:**
> - **[image-generation](../image-generation/SKILL.md)** — общий промпт-инжиниринг картинок (камеры/объективы/свет/JSON-формат — там; сводка съёмочных параметров для фотореализма — `references/photo-prompt-catalog.md`)
> - **[gemini-3-pro](../gemini-3-pro/SKILL.md)** — полный Gemini-стек
> - **[references/vk-ads-creatives.md](references/vk-ads-creatives.md)** — VK Ads сюрреалист-креативы (метод эксперта, Магритт/Дали) через Gemini вместо DALL-E 3: без VPN из РФ, выше качество

## Multi-Image Consistency via Reference Chaining (CRITICAL)

Nano Banana Pro / Gemini Image **НЕ сохраняет identity** между отдельными `generate_content`-вызовами — каждый вызов независим. Для серий (keyframes под image-to-video, иллюстрации, character lock) нужен reference-chaining.

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

# Шаг 1: первый keyframe
resp1 = client.models.generate_content(model=MODEL, config=CFG,
    contents=['Watercolor children illustration of a small figure in a misty forest. 21:9 cinemascope.'])
img1 = img_part(resp1)

# Шаг 2-3: output предыдущего шага как reference
resp2 = client.models.generate_content(model=MODEL, config=CFG, contents=[
    types.Part.from_bytes(data=img1.data, mime_type='image/png'),
    'Same character, same style. Now standing at edge of glowing river.'
])

# Шаг 4: RE-ANCHOR к img1 (НЕ к последнему выходу), иначе drift
resp4 = client.models.generate_content(model=MODEL, config=CFG, contents=[
    types.Part.from_bytes(data=img1.data, mime_type='image/png'),   # ← anchor!
    'Same character, same style. Now walking through cloud-tops at dawn.'
])
```

**Drift:** чистый forward-chaining уплывает после ~4 хопов (1-2 — identity tight; 3-4 — мелкие сдвиги стиля; 5+ — заметный дрейф лица/пропорций). **Re-anchor каждые 3 шага к оригинальному output1** стабилизирует серию.

**Потолок параллелизма: ~4 одновременных `generate_content`.** 5+ = `RESOURCE_EXHAUSTED`. `asyncio.Semaphore(4)`.

**21:9 cinemascope — нативно**, без post-crop (GPT Image 1.5 упирается в 3:2, кроп теряет композицию). Для cinematic-трейлеров с заданным aspect Nano Banana Pro — единственный mainstream-вариант без crop-loss.

**Reference переносим между провайдерами:** сгенерируй ОДИН раз — reuse через Seedance / Veo / Sora / GPT Image. Для multi-character серии — отдельный reference на каждого персонажа. Keyframing под image-to-video → `video-generation/SKILL.md` Phase 4.

## Photo Restoration (шакальная фотка → HD)

> **Граница с `image-enhancer` — «восстанови фото» ловят оба навыка, а делают разное.**
> Различие проходит НЕ по «где ИИ» — в `image-enhancer` тоже есть нейросеть (Real-ESRGAN), — а по
> тому, **переписывается ли содержание кадра**. Здесь модель **рисует кадр заново**, досочиняя из
> своего прайора детали, которых в пикселях уже нет: поры кожи, пряди, блики в глазах. Лицо при
> этом надо УДЕРЖАТЬ промптом — само оно не сохраняется. В `image-enhancer` любой шаг остаётся
> обработкой сигнала (LANCZOS, denoise, CLAHE, super-resolution): он доращивает те пиксели, что
> есть, и композицию с лицом не трогает по построению. Правило: **нужны детали, которых в
> исходнике нет → сюда; надо просто увеличить и почистить имеющееся → `image-enhancer`.**
> Для документов, юридических и исторических снимков перерендер неуместен: он выдаёт
> правдоподобное, а не бывшее.

Реставрация старых/размытых/пережатых фото с сохранением идентичности, позы и композиции. Мастер-шаблон (RU) — заполни СУБЪЕКТ и КАДРИРОВАНИЕ:

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

Английская версия шаблона (формулировки выверены, не переводить на лету) → `references/photo-restoration-en.md`.

### Вариации

- **Portrait close-up:** КАДРИРОВАНИЕ → `Close-up (поясной план)`, камера → `135mm f/2.0`.
- **Full-body:** `Full Body`, камера `35mm f/2.8`, свет `Natural Soft Light`.
- **Ч/Б → цвет:** добавить `Колоризация: исторически точные цвета эпохи [1950s/1980s/...]` — указание эпохи даёт лучшие цвета, чем generic «восстанови цвета».
- **Групповое фото:** добавить `Сохранить идентичность КАЖДОГО человека отдельно, без смешения черт`.

### Правила реставрации

1. **Всегда прикладывай исходник** — Nano Banana нужен визуальный reference, не описание.
2. **Не описывай человека подробно** — черты диктует исходник; словами только неизменяемое (очки, борода, шрам). Иначе модель «додумает» лицо по описанию.
3. **Сначала тест на кропе лица** — качество реставрации плавает; проверь на кропе прежде чем гнать полный кадр.
4. **Финал — только Pro-моделью** (Nano Banana Pro / Gemini 3 Pro Image), не Flash Image: максимум деталей.

## Каталог параметров съёмки

Конкретные камеры и объективы (85mm f/1.4 → портрет, Hasselblad X2D → фэшн), схемы света
(Rembrandt / butterfly / split), плёночные стоки (Portra 400, Cinestill 800T), JSON-схема
промпта и шаблоны под e-commerce / editorial / архитектуру — **`references/photo-prompt-catalog.md`**.
Читать, когда фотореализм задаётся техникой съёмки; для реставрации не нужно — там параметры
уже в мастер-шаблоне выше.
