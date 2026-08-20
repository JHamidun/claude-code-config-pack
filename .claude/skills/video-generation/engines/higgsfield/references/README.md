# Higgsfield Supercomputer — справочник по агенту, его навыкам и API (индекс)

Как устроен агент Higgsfield Supercomputer («Claudesfield»): состав навыков и субагентов,
схемы инструментов, каталог моделей, контракты API. Материал собран из наблюдений за работой
продукта через сессию своей учётной записи (2026-06-07).
Источники и границы применимости → `supercomputer-architecture.md` §7e.

## Файлы
| Файл | Что |
|---|---|
| `supercomputer-architecture.md` | Архитектура: Claudesfield (Claude/Gemini оркестратор) + песочница исполнения + jobs API + Clerk/SSE/планировщик задач; §7a-7g |
| `agent-tool-schemas.md` | **ВСЕ инструменты** с параметрами: 7 higgsfield_* + enhancer + audio_generate + youtube_clipping + video_analyze + instagram/tiktok_research + ads + create/deploy_website + brand_analyzer + organic_marketing + terminal/process/web_*/extract_document/delegate_task/memory/schedule/todo/ask_user_question + upload/balance/attachments |
| `cinematic-subagents-schemas.md` | **5 кино-субагентов ПОЛНЫЕ JSON-схемы** (dramaturg/director/style-architect/shot-planner/prompt-writer) + 5-блочный prompt_text шаблон |
| `flow-skills-cinematic-classicMD.md` | cinematic-flow + classicMD-flow (полная оркестровка) |
| `flow-skills-motion-variants.md` | highMD / productMD / typographyMD / infographicMD + сводка камера-доктрин |
| `flow-skills-ugc-tvad.md` | ugc-flow + unboxing/tutorial/try-on/product + tv-ad |
| `flow-skills-other-employees.md` | podcast / ai-influencer / personal-clipper / cartoon / product-photoshoot / amazon |
| `skill-library-detail.md` | 14 utility/контентных скиллов (audio/songwriting/trend-picker/organic-marketing/youtube-content/infographic/design-md/creative-ideation/popular-web-designs/landing-page-flow/product-analyzer/soul-id/pdf/powerpoint/excalidraw/maps/youtube-research/image-gen/video-gen/text-gen) |
| `skill-montage-detail.md` | montage (дословная логика + ffmpeg) |
| `motion-designer-classicMD-board-prompt.md` | classicMD-board промпт (раскадровка) дословно |
| `flow-playbooks.md` | НАШИ runnable-рецепты на hf.exe (cinematic/motion/ugc/i2v) |
| `local-supercomputer.md` | как собрать сопоставимый пайплайн на своём стеке |
| `models_all.json` / `builtin_skills.json` / `builtin_employees.json` | справочники моделей и готовых ролей |
| `REPO_DIGEST.md` | гайд по CLI / Marketing / Soul + как повторить сценарии у себя |

## Покрытие (аудит)
- **Навыки: 20/21** ✓ (нет только `create-skill` — его тело недоступно снаружи; это внутренний meta-skill авторинга).
- **Employee-флоу: 21/21** ✓ (все кинематик/MD/UGC/tv-ad/podcast/cartoon/photoshoot/amazon/image/video/text).
- **Субагенты:** cinematic-5 — ПОЛНЫЕ JSON-схемы ✓; classicMD-board/clip — дословно ✓; остальные (~45: ugc-*, tv-ad-*, cartoon-* [11], highMD/productMD/typographyMD/infographicMD board/clip, vadapt-* [3]) — **названы в enhancer-enum + описаны в родительском флоу**, но БЕЗ индивидуальных per-agent JSON-схем.
- **Инструменты: 100%** ✓ (все 39 + enhancer flow-enum).
- **Модели: 51** ✓ (`models_all.json` + `hf model get`).

## Чего в справочнике нет
1. `create-skill` (тело) — недоступно снаружи (формат навыка при этом совпадает с нашим `skill-creator`).
2. **Индивидуальные JSON-схемы ~45 non-cinematic субагентов** (ugc/tv-ad/cartoon[11]/MD-board-clip/vadapt) — их роль и поведение описаны в родительских флоу, эталон схемы — cinematic-5.
3. Файлы-скрипты `gen_pdf.py`, `fetch_transcript.py`, `enhancers/*.md` — лежат в SKILL_DIR на стороне сервиса; в справочнике описаны только их команды и наблюдаемое поведение.

## Реестр субагентов — покрыт полностью
Доп. файлы субагентов: `cinematic-subagents-schemas.md` (5), `subagents-md-clips.md` (4), `subagents-md-boards.md` (4),
`subagents-cartoon-11.md` (11), `subagents-ugc-11.md` (11), `subagents-tvad-vadapt.md` (4+3), classicMD-board/clip (в motion-designer-classicMD-board-prompt.md + cinematic-classicMD).
**Итог субагентов: ~45/45 ✓** (cinematic 5, classicMD board+clip, highMD/productMD/typographyMD/infographicMD board+clip [8], cartoon [11], ugc [11], tv-ad [4], vadapt [3]).
**Чего нет:** тело `create-skill` (недоступно снаружи) + файлы-скрипты `gen_pdf.py`/`fetch_transcript.py`/`enhancers/*.md` (лежат на стороне сервиса; описаны их команды и шаблоны выходов).
**Универсальные паттерны (across субагентов):** SANDWICH 4-layer (clip) · board_specs JSON + brand_reveal R1-R8 + chess_pattern (board) · @ImageN привязка + строгий медиа-порядок · base→stylize консистентность · STYLE LOCK константа · State Ledger/Frame Distinction · <<image_N>> токены (vadapt) · MANDATORY TAIL FREEZE 13.7-15s · Audio SFX-only.

## CLI hf.exe и эксклюзивные режимы (2026-06-07, доп.)
- `hf-cli-anatomy.md` — устройство CLI (Go/Cobra): дерево команд (account/auth/generate/model/marketing-studio/product-photoshoot/marketplace-cards/soul-id/upload/workspace); авторизация через OAuth device-flow; контракт jobs-API (POST /jobs, /jobs/cost, поллинг, /assets/{id}/detail, отдача с CloudFront CDN); схемы параметров под каждую модель приходят с сервера (`hf model get`).
- `exclusive-models-soul-ms-virality.md` — актуальные схемы параметров и поведение Soul Cast (character_params: budget/genre/age/era/gender) / Soul Location (Location Color Directive) / Marketing Studio + DTC Ads Engine (webproducts/brand-kits/avatars/hooks/9 mode) / Virality Predictor brain_activity (Markdown-отчёт по удержанию). Эти режимы есть только в hf.exe.
- `model-provider-map.md` — (генерится workflow) карта 51 модель → прямой провайдер → есть ли к нему доступ → рецепт вызова.

## model-provider-map.md готов (workflow из 5 агентов, веб-проверка 2026-06-07)
51 модель → прямой провайдер. 🟢 ~30 доступны напрямую при уже имеющихся ключах: Veo/Nano (Google), Seedance 2.0 + Kling (Runway), Seedream/Wan/Hailuo/Flux/Recraft/Topaz (Replicate), GPT-Image (OpenAI), rembg + Topaz локально на своей GPU. 🟡 нужен отдельный ключ: Grok (через Replicate), z_image (AIMLAPI), kling_omni (WaveSpeed/fal), sam_3d (fal). 🔴 только через hf.exe: Soul / Marketing Studio-DTC / Virality / ai_stylist / skin_enhancer / Cinema-Studio-shots / reframe / draw_to_video / marketplace / product-photoshoot.

## Скрипты обработки медиа в песочнице (4 батча, 2026-06-07)
- `sandbox-media-scripts.md` — постер/миниатюры/grid, concat/конверт, watermark/copyright, faststart/HLS, curl(download/multipart/presigned), аудио(ducking/loudnorm/fade), субтитры(SRT/ASS-караоке), цветокор(lut3d/eq), speed(slow-mo/boomerang/GIF), image(PIL upscale/overlay/ffprobe), переходы(xfade+glitch), композ(chromakey/blend/PiP), веб(TanStack+bun build+wrangler deploy), документы(soffice pptx→pdf, pdftoppm, @excalidraw/utils, puppeteer-screenshot).
- `sandbox-audio-sticker-mask.md` — Audio-Gen API (/v1/audio/generate voiceover/translate + /v1/jobs/status), Suno API (/v1/music/generate chirp-v3-5 + /v1/music/tasks), прозрачный экспорт (webm yuva420p/apng/transparent-gif/rembg-видео), sprite-sheet (ffmpeg tile + PIL atlas), маски (alphamerge/maskedmerge/SAM center-point).

## Скрипты песочницы, батч 5 — sandbox-camera-audio-transcribe.md
Камера-движения (Ken Burns zoompan / whip-pan crop+gblur+sin(t) / параллакс dual-zoompan) · стабилизация vidstab 2-pass · интерполяция minterpolate (60fps boost + 0.25x slow-mo) · умный авто-рефрейм 16:9→9:16 (MediaPipe face-detection → динамич. crop-выражение) · голос-чистка (afftdn+silenceremove, highpass/anequalizer/deesser/compand) · аудио-визуалайзеры (showwaves/showspectrum) · whisper large-v3 word_timestamps → SRT/ASS-караоке.

## Скрипты песочницы, батч 6 — sandbox-creative-effects.md
Film grain+vignette · halation/bloom (screen-blend) · VHS · хром-аберрация rgbashift · datamosh (I-frame drop) · light leaks · dither Floyd-Steinberg · scene-detect (select gt scene 0.4) · nlmeans/hqdn3d денойз · unsharp · deflicker. (стандартные ffmpeg-рецепты, к специфике Higgsfield не относятся — общий cookbook).

## Скрипты песочницы, батч 7 — sandbox-titles-assembly-platform.md
Титры-анимация (typewriter trunc(t*15) / slide-in lower-third drawbox if(t) / fade alpha / end-card CTA) · multi-clip xfade накопит-offset + beat-sync python (нарезка по таймкодам→concat+audio) · color-match (colorlevels WB / curves vintage / lut3d S-Log3→Rec709) · ⭐платформенный пресет TikTok/Reels H.264 high@4.2 GOP=2s -14 LUFS · aspect (blurred-bg fill / letterbox-pad / safe-zones оверлей top220/sidebar/bottom400).

## Скрипты песочницы, батч 8 — sandbox-ai-image-postproc.md
GFPGAN v1.4 (face-restore) · Real-ESRGAN x4 (super-res, CLI+py, tile=400/FP16) · LaMa (inpaint/object-removal, pad×8/бинар маска) · SD-Diffusers outpaint (canvas expand+mask) · Depth-Anything (depth→2.5D parallax) · DDColor/Zhang-Caffe (colorize) · VGG fast-neural (style). ⚠️ Стандартные опенсорс-модели (к специфике Higgsfield не относятся) — запускаются локально на своей GPU или через Replicate. Cookbook для image-enhancer/void-video.

## Статус батчей
Батчи 6-8 — общий ffmpeg/AI cookbook, к Higgsfield не привязан. Специфика продукта (флоу, субагенты, схемы инструментов, модели, эксклюзивные режимы, системные вызовы ffmpeg/curl/API) описана в батчах 1-5 и в основной части справочника.

## Реестры и официальный репозиторий (2026-06-07)
- `registries/REGISTRIES.md` — каталоги за *_id: ✅camera rig (6 камер/11 линз/6 фокусных/3 диафрагмы + prompt-токены + `buildNanoBananaPrompt()` — ВЕРИФИЦ. из Anil-matcha/Open-Higgsfield-AI promptUtils.js + офиц.доки) · ✅marketing hooks/settings/avatars/ad-formats (ЖИВЫЕ UUID в `registries/ms_*.json`) · ✅modes · 🟠AI-Stylist pose/outfit/style_id (серверные, иллюстративно).
- `registries/ms_{ad-formats,hooks,settings,avatars}.json` — живые реестры (42/9/14/20, реальные UUID).
- `registries/openhf_models_dump.json` — выгрузка каталога t2i-моделей открытого клона (Muapi).
- `official-repo/` (19 файлов из github.com/higgsfield-ai/skills) — COOKBOOK (3 рецепта), model-catalog, prompt-engineering, media-inputs, marketing-{modes,avatars,setup-items,dtc-ads,brand-kits,products,ad-references}, soul-id-SKILL+photo-guide, product-photoshoot/marketplace-cards/generate SKILL, CLAUDE/README.
- Публичные источники: репозиторий github.com/higgsfield-ai/skills (его копия — в `official-repo/`) + github Anil-matcha/Open-Higgsfield-AI (открытый клон на Muapi, там же camera promptUtils.js).

## Каталоги, снятые запросами из сессии своей учётной записи (2026-06-07) → registries/registries-LIVE.md
- ✅ `/voices?size=200` → 60 TTS-голосов (real voice_id) → `voices.json`
- ✅ `/outfits?app_slug=ai-stylist&size=300` → 206 outfit-пресетов (real UUID) → `ai-stylist-outfits.tsv`
- ✅ `/styles?size=200` → 5 видео-стилей (real UUID) · ✅ `/job-sets/costs` → `job-sets-costs.json`
- Паттерн каталогов: `/<resource>?app_slug=<app>&size=N` (app AI Stylist = `ai-stylist`).
- ❌ Не покрыто: эндпоинты AI Stylist `poses`/`backgrounds` и каталог Soul `style_id` — путь подобрать не удалось, данные подгружаются только пикером в интерфейсе. Слаги вида `streetwear_oversized` / `casual_standing`, которые предлагает агент, проверены и не существуют (реальные outfits — именованные вещи с UUID).
