# Higgsfield Engine — внутри `video-generation`

Движок Higgsfield = вендорский CLI `bin/hf.exe` (Windows v0.1.40) под своей учётной записью
+ локальный пайплайн сборки роликов на нашем стеке. Сюда мастер-`SKILL.md` направляет когда:
**структурный флоу** (cinematic-5 / motion-design MD-варианты / UGC / TV-ad / podcast / cartoon) ИЛИ **HF-эксклюзив**
(Soul Cast/Location, Marketing Studio/DTC, Virality Predictor, Cinema Studio, ai_stylist, reframe, draw_to_video).

Два режима доступа:
- **(A) Локальная оркестрация** — собираем ролик по тому же пайплайну, а генерацию по возможности ведём напрямую у провайдеров на своих ключах: `scripts/prompt_builders.py` (промпт-кухня) → `scripts/router.py` (выбор провайдера) → `scripts/assemble.py` (ffmpeg). Дефолт.
- **(B) Прямой hf.exe** — для HF-эксклюзивов и быстрого raw-доступа к 51 модели.

Устройство пайплайна, модели и цены → `references/supercomputer-architecture.md`. Как это собрано на нашем стеке → `references/local-supercomputer.md`.

---

## (A) ЛОКАЛЬНАЯ ОРКЕСТРАЦИЯ — 6 фаз
```
1. Intake     → тип ролика, длительность, аспект, платформа, бюджет, голос
2. Flow select→ выбрать флоу (таблица) → его камера-доктрина + шаблон
3. Prompt     → scripts/prompt_builders.py: cinematic-5 / SANDWICH-clip / board_specs / camera-rig
4. Model route→ scripts/router.py: прямой провайдер (свои ключи) ИЛИ hf.exe (эксклюзив)
5. Generate   → keyframes (gpt_image_2/nano) → видео (Seedance/Veo) параллельно
6. Assemble   → scripts/assemble.py + ../../scripts/ffmpeg_assemble.py → платформенный экспорт
```

### Flow selection (доктрина камеры → шаблон → раскадровка)
| Запрос | Flow | Доктрина | Шаблон (prompt_builders) | Раскадровка |
|---|---|---|---|---|
| Кино-трейлер, сюжет, персонажи | cinematic | DP-driven (style-architect) | `build_cinematic_5` конвейер | 4/8/12 кадров |
| Брендовый промо, энергия | highMD | **Hyperkinetic Chaos** (Vertigo/Crash/Whip) | `build_sandwich_prompt highMD` | 6 (3×2) |
| Продукт, реклама | productMD | Bot&Dolly роборука + Special Beat кадр4 | `sandwich productMD` ~600 слов | 9 (3×3) character-sheet |
| Кинетик-типографика | typographyMD | статика, движутся буквы | `sandwich typographyMD` + TEXT REVEAL | 6 |
| Данные/инфографика | infographicMD | стабильна, Layered Reveals HR-5 | `sandwich infographicMD` (metric_values) | 6 |
| Чистый моушн (классика) | classicMD | **hold-steady MDCM** (противоположность highMD) | `sandwich classicMD` | 6 |
| Talking-head отзыв | ugc | слот-борд 3×9:16, First-Word hook | ugc-board/clip | 3 слота |
| Распаковка/туториал/примерка | ugc-unboxing/tutorial/try-on | 4-слот 21:9, канон-арки | соотв. ugc-* | 4 слота |
| Премиум реклама с актёром | tv-ad | 3 формата + Screen Lock + GATE | tv-ad-script(7-панель)+seedance | 7 |
| Подкаст/интервью | podcast | 5-фаз composite + Shot Algebra(180°) | hero-plates→seated→storyboard→chunks | 4-panel |
| Мультфильм | cartoon | Style Formula КОНСТАНТА, base→stylize | cartoon-11 конвейер | scene-parse |
> Доктрины classicMD-HOLD и highMD-HYPERKINETIC — **намеренно противоположны, обе выбираемы по флоу.** Детали → `references/flow-skills-*.md`, `subagents-*.md`, кукбук → `flows.md`.

### Промпт-кухня (`scripts/prompt_builders.py`, stdlib-only)
- `build_cinematic_prompt(base,camera,lens,focal,aperture)` — camera-rig (6 камер/11 линз/6 фокусных/3 диафрагмы → токены). Дефолт Modular 8K / Creative Tilt / 35mm / f1.4. CLI: `cinematic --base`.
- `build_sandwich_prompt(shots,doctrine,palette,aspect)` — 4-слойный SANDWICH Seedance-промпт. CLI: `sandwich --doctrine --shots N`.
- `build_board_spec(doctrine,palette,panels,brand)` — board_specs для gpt_image_2 (chess_pattern, brand_reveal R1-R8). CLI: `board`.
- `build_cinematic_5(brief)` — 5-агентный конвейер (dramaturg→director→style-architect→shot-planner→prompt-writer), функция.
- `ENHANCE_TAGS` / `QUICK_PROMPTS` / `TAIL_FREEZE` (13.7-15s) / `DOCTRINE_BLOCKS` (5) / `BRAND_REVEAL_CATALOG` (R1-R8).

### Model routing (`scripts/router.py`) — выбор провайдера
`route(jst)` решает: прямой провайдер (свои ключи) ИЛИ hf.exe (эксклюзив). 36 routes + 4 алиаса.
- 🟢 **Прямо:** Veo (GOOGLE_API_KEY) · **Seedance 2.0 + Kling через Runway ⭐** (workhorse) · Nano/GPT-Image/flux/recraft/seedream/wan/hailuo/grok (Google/OpenAI/Replicate) · rembg+Topaz локально на своей GPU.
- 🔴 **hf.exe:** Soul Cast/Location/cinematic, text2image_soul_v2, Marketing Studio/DTC (9 ad-режимов), Virality (brain_activity), Cinema Studio, reframe, draw_to_video, z_image (пока нет ключа).
- HF-кредиты ТОЛЬКО на 🔴. `python scripts/router.py table` — вся таблица.

### Сборка (`scripts/assemble.py` 18 атомов + `../../scripts/ffmpeg_assemble.py` пайплайн)
- **`assemble.py`** — атомарные ffmpeg-операции: poster/concat/reframe_blurred_bg/xfade_chain/color_lut/audio_duck/loudnorm/burn_ass/transparent_webm/apng/ken_burns/beat_sync_cut/**platform_export**(-14 LUFS/GOP 2s/h264 high@4.2)/showwaves/whisper_srt.
- **`../../scripts/ffmpeg_assemble.py`** (хаба) — полный пайплайн VO+музыка(sidechain)+brand-card+concat из JSON-манифеста. Используй когда нужен голос+музыка+брендкард; `assemble.py` — для точечных операций.

### Quick start
```bash
cd engines/higgsfield/scripts
python prompt_builders.py sandwich --doctrine highMD --shots 6 --aspect 9:16 --palette "#0a0a0a,#00e5ff,#ff003c"
python router.py route seedance_2_0     # → Runway
python router.py route soul_cast        # → hf.exe (эксклюзив)
python assemble.py platform_export raw.mp4 final_reels.mp4
```

---

## (B) ПРЯМОЙ hf.exe — raw-доступ к 51 модели

### Bootstrap
```bash
HF="./bin/hf"                     # вендорский Go-бинарь, в репозитории его НЕТ (*.exe в .gitignore).
                                  # Взять релиз github.com/higgsfield-ai/cli (v0.1.40+) и положить в bin/
"$HF" account status              # своя учётная запись и её тариф
"$HF" auth login                  # только если "Session expired" (device flow)
"$HF" model list --json           # live-каталог (51). schema: "$HF" model get <jst> --json
```
Токен `HIGGSFIELD_ACCESS_TOKEN` — в `.credentials.master.env` (Clerk, живёт через refresh).

### Core pattern
```bash
"$HF" generate create <job_set_type> --prompt "..." [media flags] [params] --wait
# печатает URL. --json машинный вывод. медленные: --wait-timeout 20m
```
Медиа-флаги (локальный путь авто-upload ИЛИ UUID): `--image --start-image --end-image --video --audio`.

### Модель под задачу (job_set_type)
**Видео:** `seedance_2_0` (дефолт, i2v 4-15с; `--start-image --duration --aspect_ratio 9:16 --resolution 720p --genre epic --mode std|fast`; 720p≈4.5 cr/s, fast 3.5) · `veo3_1`/`veo3_1_lite` (`--aspect_ratio 16:9|9:16 --duration 4|6|8`) · `kling3_0` (`--start-image --end-image`) · `cinematic_studio_3_0` (max fidelity) · `minimax_hailuo` (физика/бюджет) · `marketing_studio_video` (реклама/UGC) · `brain_activity` (**Virality**, `--video ./ad.mp4` без prompt).
**Изображение:** `gpt_image_2` (дефолт, текст/UI, `--aspect_ratio --resolution 2k`) · `nano_banana_2`(Pro)/`nano_banana_flash`(2) (`--image` до 8 реф; ⚠ UI «Nano Banana Pro» = jst `nano_banana_flash`) · `text2image_soul_v2`/`soul_cinematic` (`--soul-id <ref> --quality 2k`) · `soul_location` · `soul_cast` · `seedream_v4_5` · `z_image` · `recraft_v4_1` · `flux_2` · `flux_kontext`.
Полный список+IDs → `references/models_all.json` (51) + param-схемы → `references/model-params-full.md`. Цены → `references/supercomputer-architecture.md` §4 + `references/registries/job-sets-costs.json`.

### Примеры
```bash
"$HF" generate create seedance_2_0 --prompt "slow push-in, cinematic" --start-image ./kf.png --duration 5 --aspect_ratio 9:16 --resolution 720p --genre epic --wait
"$HF" generate create gpt_image_2 --prompt "neon city, on-image text" --aspect_ratio 1:1 --resolution 2k --wait
"$HF" generate create brain_activity --video ./final.mp4 --wait   # virality: score, peak hook, sustain, report
```

### Прямой jobs API (без CLI)
`POST fnf.higgsfield.ai/jobs {job_set_type, params}` (Bearer = HIGGSFIELD_ACCESS_TOKEN) → poll `GET /jobs/{id}/status` → `GET /assets/{id}/detail`. CLI-контракт целиком → `references/hf-cli-anatomy.md`.

### Errors
`Session expired`→`auth login` · `not enough credits`→модель требует кредитов, которых нет на тарифе учётной записи · `Unknown params`→`model get <jst> --json` · `Missing medias` на brain_activity→`--video`.

---

## ЭКСКЛЮЗИВЫ (канон — только hf.exe, не воспроизвести напрямую)
Схемы → `references/exclusive-models-soul-ms-virality.md`.
- **Soul** (консистентное лицо): `soul-id create --name X --soul-2 --image p1..p5 [--soul-cinematic]` → `soul-id wait <id>` → `generate create text2image_soul_v2 --soul-id <ref> --quality 2k`. character_params{budget:10,age,genre,era,gender}; Location Color Directive обязателен для soul_location.
- **Marketing Studio / DTC:** discovery `marketing-studio {avatars,products,hooks,settings,ad-formats} list --json`; импорт `marketing-studio products fetch --url <url> --wait`; ген `generate create marketing_studio_video --avatars @a.json --product_ids @p.json --mode ugc --duration 15 --aspect_ratio 9:16 --wait`. 9 режимов (ugc/ugc_how_to/ugc_unboxing/product_showcase/product_review/tv_spot/wild_card/ugc_virtual_try_on/virtual_try_on). Каталоги UUID → `references/registries/ms_*.json`.
- **Virality Predictor:** `generate create brain_activity --video <url|path>` → Markdown retention-отчёт.
- **AI Stylist** (примерка): outfits 206 / poses 11 / backgrounds 11 (UUID) → `references/registries/ai-stylist-*.tsv`.
- MCP-коннектор (desktop-Claude): `https://mcp.higgsfield.ai/mcp`.

## Реестры (UUID → `references/registries/`)
Soul style_id 200 (`soul-styles.tsv`, host cms.higgsfield.ai) · AI-Stylist outfits 206 / poses 11 / backgrounds 11 · TTS voices 60 (`voices.json`) · video-styles 5 · marketing hooks 9/settings 14/avatars 20/ad-formats 42 (`ms_*.json`) · costs (`job-sets-costs.json`) · модели param-схемы (`references/model-params-full.json`). Эндпоинты+метод → `references/registries/registries-LIVE.md`.

## Граница возможностей
Часть логики живёт на стороне сервиса и снаружи недоступна — системные промпты субагентов и оркестратора. Для локального флоу это не блокер: **поведение и шаблоны вывода ~45 субагентов описаны по наблюдениям за работой продукта**, результат получается эквивалентный (→ `subagents-*.md`, `cinematic-subagents-schemas.md`).

## References (внутри engines/higgsfield/references/)
supercomputer-architecture · local-supercomputer · flow-playbooks · flow-skills-{cinematic-classicMD,motion-variants,ugc-tvad,other-employees} · cinematic-subagents-schemas · subagents-{md-clips,md-boards,cartoon-11,ugc-11,tvad-vadapt} · motion-designer-classicMD-board-prompt · agent-tool-schemas · skill-{library,montage}-detail · model-params-full(.md/.json) · model-provider-map · exclusive-models-soul-ms-virality · hf-cli-anatomy · sandbox-{media-scripts,camera-audio-transcribe,creative-effects,titles-assembly-platform,ai-image-postproc,audio-sticker-mask} · REPO_DIGEST · models_all.json · builtin_{skills,employees}.json · registries/ (12) · official-repo/ (20).
