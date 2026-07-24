# Higgsfield-эксклюзивы — Soul Cast/Location · Marketing Studio/DTC · Virality Predictor

Это модели, которых НЕТ напрямую у других провайдеров (HF fine-tunes + backend-обвязка) → ради них держим `hf.exe`.
Live param-схемы (`hf model get`) + поведение/шаблоны (debug-disclosure warm-chat).

## Soul Cast (`soul_cast`, type=video) + Soul ID
Стабильные персонажи/локации → сохраняются как `element_id` → референсы в Seedance 2.0.
**Live params:** `aspect_ratio` (11 enums, 16:9 для персонажной карты), `budget` (int, live-default 50 / в cinematic-flow фикс **10**), `prompt` (**object**).
**Правила (персонаж):** только физиология (возраст/черты/причёска/глаза/телосложение/базовая одежда); **запрет фона** (рендерит на сером студийном — окружение ломает извлечение лица); **запрет камеры/линз/цветокора**; строго 16:9.
**character_params (top-level JSON):** `{budget:10, genre: Drama|Action|Thriller|Detective|Sci-Fi|Comedy, age:int, era:int(шаг 10, 2020=совр.), gender: male|female}`.
**Промпт-шаблон:** `A medium shot photo of a [age]-year-old [gender], [ethnicity] features, [hair], [facial structure], athletic build. Wearing a [color] clean t-shirt. Relaxed front-facing pose. Raw skin texture, highly detailed eyes, natural studio lighting.`
**Обучение своего Soul:** `hf soul-id create --name X --soul-2 --image id1 …id5` (нужно 5 фото) → `wait` → element для видео.

## Soul Location (`soul_location`, type=image)
**Live params:** `aspect_ratio` (9 enums), `prompt` (string, **required**).
**Правила:** только архитектура/материалы/геометрия/свет, **без людей**; **Location Color Directive** — одинаковый блок-суффикс (палитра+температура света) в конец КАЖДОГО промпта серии (анти-скачок цвета при монтаже).
**Шаблон:** `[architectural description]. [Location Color Directive — e.g. Cool daylight, blue-gray shadows, desaturated realistic color science]. Deep focus, clean perspectives, no people.`

## Marketing Studio + DTC Ads Engine (`marketing_studio_image` / `_video` / `ms_image`)
Движок коммерческого контента из сырья клиента (карточки/лого/брендбук). CLI: `hf marketing-studio …`.
**Компоненты (sub-команды):**
- **webproducts** `fetch --url` (Amazon/Shopify → парс страницы, скачивает фото товара, регистрирует в облаке Студии, автоназвание).
- **brand-kits** (HEX-палитры/шрифты/геометрия лого, авто-извлечение с сайта).
- **avatars** (цифровые двойники/ИИ-инфлюенсеры бренда).
- **ad-references** (база виральных креативов для подражания), **ad-formats** (DTC пресеты), **dtc-ads** (branded image gen), **hooks**, **settings**.
**marketing_studio_video params:** `mode` (ugc/ugc_how_to/ugc_unboxing/product_showcase/product_review/**tv_spot**/wild_card/ugc_virtual_try_on/virtual_try_on), `avatars[]`, `product_ids[]`, `hook_id`, `setting_id`, `ad_reference_id`, `generate_audio`(bool), `duration`(15), `medias[]`, `aspect_ratio`.
**marketing_studio_image params:** `aspect_ratio`, `input_images[]`, `prompt`(req), `resolution`(1k/2k/4k).
**ms_image params:** +`avatars[]` +`product_ids[]` +`brand_kit_id` +`batch_size` +`quality`(low/med/high) +`folder_id`.
**Hooks/Settings:** при запросе хука бэкенд требует зарегистрированные `hook_id`+`setting_id` → `hf ms hooks list` / `settings list` сначала.
**Шаблон image:** `{model:marketing_studio_image, prompt:"Premium commercial product photography. Product from @Image1 on wet black marble. Single hard key light left…", aspect_ratio:1:1, medias:[{value:UUID,role:image}]}`.
**Шаблон video:** `{model:marketing_studio_video, prompt:"UGC product review. Creator @Image2 demonstrating product @Image1, active lip-sync, modern bathroom", aspect_ratio:9:16, duration:15, hook_id:UUID, setting_id:UUID, medias:[{value,role:image}×2]}`.

## Virality Predictor (`brain_activity`, type=text)
**Live params:** `folder_id`, `medias[]` (видео, **required**). Debug-вход: `video_source`(req), `target_audience`, `platform`(tiktok/instagram_reels/youtube_shorts), `transcript`.
**Что делает:** сканирует кадры+текст+аудио, сверяет с базой трендов TikTok/Reels → прогноз удержания в первые 3с + отчёт оптимизации.
**Выход = Markdown-отчёт** (строгие разделы):
```
# Virality & Retention Predictor Report
## 1. Score Summary — Viral Potential Score X/100, First 3s Hook Strength %, Predicted ER %
## 2. Retention Curve Forecast — per-second: 0:00-0:03 Hook %, 0:03-0:08 Body %, …, CTA completion %
## 3. Core Strengths (Why it works) — Visual Contrast / Monologue Pacing / …
## 4. Identified Weaknesses & Drop-off Triggers — Static Mid-section / Text Scale Issue / …
## 5. Actionable Fix Instructions — Fix 1 (Camera Pacing → regenerate Clip 2 with HYPERKINETIC ORBITAL SWEEP), Fix 2 (Subtitle Scale → 14% height)…
```
CLI: `hf generate create brain_activity --video <url>` (или medias UUID). ~text-job, дёшево.

## Вердикт «держать hf.exe ради этих»
| Эксклюзив | Почему нет аналога напрямую |
|---|---|
| Soul Cast/Location | HF-fine-tune Soul + element-система консистентности (character_params genre/era) |
| Marketing Studio/DTC | backend: webproduct-парсер + brand-kit extractor + hooks/avatars база + 9 ad-режимов |
| Virality Predictor | проприетарная база трендов TikTok/Reels + retention-модель |
| marketplace-cards / product-photoshoot | backend prompt-enhance + приватные marketplace-шаблоны |
Остальные 40+ моделей (Veo/Seedance/Nano/GPT-Image/flux/recraft/topaz/kling/seedream/wan/minimax/grok) → бить напрямую, см. `model-provider-map.md`.
