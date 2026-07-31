# 51 Higgsfield-моделей → прямой провайдер (что бить напрямую, что оставить на hf.exe)

Карта на 2026-06-07 (веб-проверка model-id/цен). Цель: звать модели **своими ключами** (дешевле / уже есть),
`hf.exe` — только под HF-эксклюзивы. Твой стек: GOOGLE_API_KEY · RUNWAY_TOKEN_PLACEHOLDER (Unlimited = flat) · OPENAI_API_KEY ·
Replicate · локальный your GPU (rembg/Topaz бесплатно). НЕТ: xAI, BFL, Topaz, Recraft, MiniMax, Kuaishou, AIMLAPI/PiAPI, WaveSpeed, fal.

> ⚠️ Поправка маппинга Nano Banana (по `models_all.json` display_name): `nano_banana`=«Nano Banana» (база), `nano_banana_flash`=«Nano Banana 2»=`gemini-3.1-flash-image-preview`, `nano_banana_2`=«Nano Banana Pro»=`gemini-3-pro-image-preview`.

## 🟢 БИТЬ НАПРЯМУЮ — есть у тебя, дешевле/равно (≈30 моделей)

### Видео
| HF jst | Модель | Прямой путь | Цена напрямую vs HF |
|---|---|---|---|
| `veo3` `veo3_1` `veo3_1_lite` | Google Veo 3/3.1/Lite | **GOOGLE_API_KEY** google-genai `veo-3.1-generate-001` / `-fast-generate-001` / `-lite-generate-preview` | Fast $0.10/с, Lite ~$0.05/с — **3-4× дешевле** HF |
| `seedance_2_0` | ByteDance Seedance 2.0 | **RUNWAY_TOKEN_PLACEHOLDER** (Unlimited) `seedance-2.0` | **$0 marginal** (flat) vs ~$1.25 HF ⭐ |
| `seedance1_5` | Seedance 1.5 Pro | Replicate `bytedance/seedance-1.5-pro` | $0.022/с fast vs ~$1.25 HF |
| `kling2_6` `kling3_0` | Kuaishou Kling 2.6/3.0 | **RUNWAY_TOKEN_PLACEHOLDER** `kling-2.6-pro`/`kling-3.0` (или Replicate `kwaivgi/kling-v2.6`/`kling-v3-omni-video`) | **$0 marginal** (Runway flat) ⭐ |
| `wan2_6` `wan2_7` | Alibaba Wan 2.6/2.7 | Replicate `wan-video/wan-2.6-i2v` / `wan-2.7-i2v`/`-r2v`/`-image`/`-image-pro`(4K) | ~$0.10-0.15/с ≈ HF |
| `minimax_hailuo` | MiniMax Hailuo 02/2.3 | Replicate `minimax/hailuo-02` | $0.27/6с — HF чуть дешевле, но без credit-lock. ⚠️ применяй rembg (тёмный градиент, [[hailuo-dark-gradient-rembg-only-fix-2026-06-06]]) |

### Изображения
| HF jst | Модель | Прямой путь | Цена |
|---|---|---|---|
| `gpt_image_2` | OpenAI GPT-Image-2 | **OPENAI_API_KEY** `gpt-image-2` | $0.006-0.21/img — **3-6× дешевле** HF ⭐ |
| `openai_hazel` | GPT-Image-1.5 (Hazel) | **OPENAI_API_KEY** `gpt-image-1.5` | ~−50% vs HF |
| `nano_banana_flash` | Nano Banana 2 | **GOOGLE_API_KEY** `gemini-3.1-flash-image-preview` (response_modalities IMAGE,TEXT) | $0.045-0.151/img ≈ HF |
| `nano_banana_2` | Nano Banana **Pro** | **GOOGLE_API_KEY** `gemini-3-pro-image-preview` | $0.134/img (HF ~$0.068 ≈ 2× дешевле для plain-gen → см. ниже) |
| `seedream_v4_5` `seedream_v5_lite` | ByteDance Seedream 4.5/5-lite | Replicate `bytedance/seedream-4.5` / `seedream-5-lite` | $0.035-0.05/img ≈ HF |
| `flux_2` | BFL FLUX.2 | Replicate `black-forest-labs/flux-2-pro` (или `-dev`) | ~$0.04/img — дешевле/равно |
| `flux_kontext` | FLUX.1 Kontext (edit) | Replicate `black-forest-labs/flux-kontext-pro` | ~$0.04/edit ≈ |
| `recraft_v4_1` | Recraft V4.1 | Replicate `recraft-ai/recraft-v4` (v4.1 проверить slug) | $0.04/img ≈ |

### Upscale / утилиты
| HF jst | Модель | Прямой путь | Цена |
|---|---|---|---|
| `topaz_image` | Topaz Photo AI | Replicate `topazlabs/image-upscale` **ИЛИ локальный Topaz на your-GPU** | $0.05/24MP (Replicate −25% vs Topaz API; локально = $0) ⭐ |
| `topaz_video` | Topaz Video (Astra/Starlight) | Replicate `topazlabs/video-upscale` **ИЛИ локальный Topaz Video AI на your-GPU** | локально бесплатно ⭐ |
| `image_background_remover` | rembg (U2Net/BiRefNet) | **ЛОКАЛЬНО** `pip install rembg[gpu]` (уже юзаешь) | **$0** ⭐ |
| `sam_3_video` | Meta SAM 3.1 (remove bg/segment) | fal `fal-ai/sam-3-1/video` или Replicate `lucataco/sam3-video` | $0.005/16 кадров (fal дешевле) |

## 🟡 НУЖЕН КЛЮЧ, которого нет (но дёшево, если завести)
| HF jst | Модель | Где взять напрямую | Заметка |
|---|---|---|---|
| `grok_image` `grok_video` `grok_video_v15` | xAI Grok Imagine | **через Replicate** `xai/grok-imagine-image` / `xai/grok-imagine-video` (твой Replicate-токен работает!) | $0.02/img, $0.05-0.14/с — **3-5× дешевле** HF. v1.5 = preview (2026-06-03), проверь доступность |
| `z_image` | Alibaba Z-Image Turbo | AIMLAPI `alibaba/z-image-turbo` или PiAPI | $0.04/img. Нет на Replicate → нужен AIMLAPI/PiAPI ключ, иначе hf |
| `kling_omni_image` | Kling O1 Image (мульти-реф 4K) | WaveSpeedAI `kwaivgi/kling-image-o1` или fal | $0.028/img. Нет на Replicate/Runway → нужен WaveSpeed/fal, иначе hf |
| `sam_3_3d` | Meta SAM 3D | fal `fal-ai/sam-3/3d-body` (objects в beta) или self-host на your-GPU | $0.065/gen; локально бесплатно (your VRAM) |

## 🔴 ОСТАВИТЬ hf.exe — HF-эксклюзивы (нет прямого аналога)
| HF jst | Почему |
|---|---|
| `soul_cast` `soul_location` `soul_cinematic` `soul_cinema_studio` | HF-fine-tune Soul + element-консистентность (character_params genre/era). → `exclusive-models-soul-ms-virality.md` |
| `marketing_studio_image/video` `ms_image` + DTC Ads Engine | backend: webproduct-парсер, brand-kit extractor, hooks/avatars база, 9 ad-режимов |
| `brain_activity` (Virality Predictor) | проприетарная база трендов TikTok/Reels + retention-модель → Markdown-отчёт |
| `nano_banana_2_ai_stylist` | Nano Banana 2 + pose/background preset registry + outfit library (оркестровка) |
| `nano_banana_2_skin_enhancer` | skin-retouch diffusion + Topaz 4K в одном вызове |
| `nano_banana_2_shots` / `cinematic_studio_2_5/3_0/image/video/_v2` | Cinema Studio: 70+ камера-пресетов (Bullet Time/360/FPV/Crash Zoom) + multi-shot sequencing. Низ = Seedance/Veo (есть напрямую), но пресет-оркестровка — HF |
| `reframe` | AI-outpaint смены аспекта (не кроп). Прямой аналог — Runway Expand Video только Enterprise ($500+/мес). ffmpeg-кроп теряет контент |
| `draw_to_video` | canvas-аннотации (рисуешь стрелки движения) → motion-control. Нет публичного API на canvas-вход |
| `marketplace-cards` `product-photoshoot` | backend prompt-enhance + приватные marketplace-шаблоны (возвращают nano_banana_2 промпты) |
| `image_auto` `llm_text` `marketing_studio_*` | HF-роутеры/обвязки |

## ⭐ Главные выводы (деньги)
1. **Seedance 2.0 + Kling 2.6/3.0 через Runway Unlimited = $0 marginal** — это рабочие лошадки видео, гони их через Runway, НЕ через HF-кредиты.
2. **GPT Image напрямую = 3-6× дешевле** HF-кредитов (OPENAI_API_KEY).
3. **Veo напрямую (Fast/Lite) = 3-4× дешевле** (GOOGLE_API_KEY).
4. **rembg + Topaz локально на your-GPU = бесплатно** (bg-remove, upscale).
5. **Grok через твой Replicate-токен** (не нужен xAI-ключ) = 3-5× дешевле.
6. HF-кредиты тратить ТОЛЬКО на эксклюзивы (Soul, Marketing Studio/DTC, Virality, Cinema Studio пресеты, reframe, draw-to-video) + где у тебя нет ключа (z_image, kling-omni-image).
7. Nano Banana Pro plain-gen: HF-кредит (~$0.068) ≈ 2× дешевле прямого GA ($0.134) — если кредиты в бюджете, plain-картинки Pro можно и через hf; но для пайплайнов/батча — напрямую.
