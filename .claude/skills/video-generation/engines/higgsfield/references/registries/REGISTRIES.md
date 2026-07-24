# Higgsfield — реестры за `*_id` параметрами (камеры/позы/стили/маркетинг)

Каталоги значений для object-параметров (`camera_model_id`, `pose_preset_id`, `style_id`, `hook_id`…).
**Источники с разной надёжностью** (важно):
- ✅ **ЖИВЫЕ из `hf.exe`** (реальные UUID): marketing-studio hooks/settings/avatars/ad-formats → `ms_*.json` рядом.
- ✅ **modes** — из официального публичного репо `higgsfield-ai/skills` (marketing-modes.md).
- ✅ **camera rig** (тела/линзы/фокусные/диафрагмы + prompt-токены) — ПОДТВЕРЖДЕНО исходником `Anil-matcha/Open-Higgsfield-AI/src/lib/promptUtils.js` + офиц. докой (1:1). Механизм `_id`→текст + функция-сборщик ниже.
- 🟠 **AI Stylist pose/background/outfit + style_id** — из warm-chat, ИЛЛЮСТРАТИВНЫЕ слаги (агент реконструировал из фронта; точные API-id проверять `hf` при наличии команды / network-tab веб-UI).

## 1. Cinematic Studio — Camera Rig (`camera_*_id` → prompt-токен)
Механизм: выбранный `_id` бэкенд переводит в текст-модификатор в промпт. → можно воспроизвести БЕЗ их API, просто дописав токен.
**Camera body (`camera_model_id`):**
| Label | Prompt-токен |
|---|---|
| Modular 8K Digital | modular 8K digital cinema camera |
| Full-Frame Cine Digital | full-frame digital cinema camera |
| Grand Format 70mm Film | grand format 70mm film camera |
| Studio Digital S35 | Super 35 studio digital camera |
| Classic 16mm Film | classic 16mm film camera |
| Premium Large Format Digital | premium large-format digital cinema camera |
**Lens (`camera_lens_id`):** Creative Tilt (creative tilt lens effect) · Compact Anamorphic · Extreme Macro · 70s Cinema Prime (1970s cinema prime lens) · Classic Anamorphic · Premium Modern Prime · Warm Cinema Prime (warm-toned cinema prime) · Swirl Bokeh Portrait · Vintage Prime · Halation Diffusion (halation diffusion filter) · Clinical Sharp Prime (ultra-sharp clinical prime).
**Focal (`camera_focal_length_id`):** 8mm (ultra-wide) · 14mm (wide-angle) · 24mm (wide dynamic) · 35mm (natural cinematic) · 50mm (standard portrait) · 85mm (classic portrait).
**Aperture (`camera_aperture_id`):** f/1.4 (shallow DoF, creamy bokeh) · f/4 (balanced) · f/11 (deep focus, sharp FG→BG).
→ Забрать как **пресет-словарь камеры** в наш image/video промпт-билдер (NB Pro/cinematic keyframes).

## 2. AI Stylist (🟠 иллюстративные слаги)
**Pose:** casual_standing · editorial_lean · runway_walk · sitting_relaxed · closeup_adjustment · dynamic_turn · high_fashion_pose · product_forward.
**Background:** minimal_studio · luxury_loft · vintage_street · modern_office · nature_overcast · urban_industrial · coastal_morning · desert_sand.
**Outfit (wardrobe matrix):** streetwear_oversized · preppy_equestrian · quiet_luxury · coastal_minimal · sporty_jersey · editorial_cool · leather_grit · boho_soft.

## 3. Soul Cinema / MS Image — `style_id` (🟠 иллюстративные)
classic_ugc (UGC, iPhone-селфи) · premium_editorial (журнальная ретушь) · scifi_neon (cyberpunk) · vintage_35mm (плёночное зерно) · minimal_dtc (белый фон Amazon/Shopify) · cinematic_noir (ЧБ/синие тени, дым) · vibrant_pop (80-е, насыщенный) · soft_dreamy (мягкий фокус, пастель).

## 4. Marketing Studio — ЖИВЫЕ реестры (hf.exe, реальные UUID в JSON)
- **ad-formats** (42) → `ms_ad-formats.json`: Headline/Special Offer/Customer Quote/Key Features/Benefits/Social Proof/Then vs Now/Star Review/Stat Surround/Comparison Table/Press Screenshot/Whiteboard Explainer/UGC Side-by-Side/… (type=headline).
- **hooks** (9) → `ms_hooks.json`: Product Hit (stunt), Spicy (subtle), Interview (subtle)… — с ПОЛНЫМИ промптами + video-превью.
- **settings** (14) → `ms_settings.json`: Bedroom/Nature/Gym/Bathroom/Kitchen/Office/Street/In Car (realistic) + Airplane Wing/Roofing/Volcano Rim/Tiny Reviewer/Car Roof/Train Surf (unrealistic) — с промптами.
- **avatars** (20) → `ms_avatars.json`: Jayden/Stefan/Mei/Yuna/Adriana/Clara/Maria/Sofia/Valentina/Jia/Lily/Tae/Felix/Malik/Liam/Joon/Erik/Nia/Hana/Ryu (preset, gender).
- **modes** (`--mode`, из офиц. репо): ugc(✅hook/setting) · ugc_how_to(✅) · ugc_unboxing(✅) · product_showcase(❌) · product_review(✅) · tv_spot(❌) · wild_card(❌) · ugc_virtual_try_on(✅) · virtual_try_on(❌). Дефолт ugc. URL Click-to-Ad: `products fetch --url` → `generate create marketing_studio_video --url`.

→ JSON-файлы рядом (`ms_ad-formats/hooks/settings/avatars.json`) = реальные UUID для прямых вызовов. Камера-риг = словарь промпт-токенов (без API). Связано [[../model-params-full.md]], [[../exclusive-models-soul-ms-virality.md]].

---

## ✅ ВЕРИФИКАЦИЯ камеры + ТОЧНЫЙ механизм (из исходника Anil-matcha/Open-Higgsfield-AI `src/lib/promptUtils.js`)
Камера-данные выше ПОДТВЕРЖДЕНЫ 1:1 официальной докой (anil-matcha-open-higgsfield-ai.mintlify.app/guides/camera-controls) + исходным кодом клона. Дефолт: Modular 8K Digital / Creative Tilt Lens / 35mm / f/1.4.

**Механизм `_id`→промпт (буквально, забрать в наш image/video билдер):**
```js
// CAMERA_MAP/LENS_MAP/FOCAL_PERSPECTIVE/APERTURE_EFFECT — см. таблицы выше (label→token)
function buildNanoBananaPrompt(basePrompt, camera, lens, focalLength, aperture) {
  return [
    basePrompt,
    `shot on a ${CAMERA_MAP[camera]}`,
    `using a ${LENS_MAP[lens]} at ${focalLength}mm (${FOCAL_PERSPECTIVE[focalLength]})`,
    `aperture ${aperture}`,
    APERTURE_EFFECT[aperture],
    "cinematic lighting", "natural color science", "high dynamic range",
    "professional photography, ultra-detailed, 8K resolution"
  ].filter(Boolean).join(", ");
}
```
**ENHANCE_TAGS** (готовые наборы): quality=[professional photography, ultra-detailed, 8K resolution, high dynamic range, award-winning]; lighting=[cinematic lighting, golden hour, dramatic studio lighting, soft diffused light, neon glow, volumetric rays]; mood=[moody atmosphere, serene and peaceful, epic and dramatic, warm and cozy, dark and mysterious]; style=[photorealistic, oil painting, watercolor, digital art, concept art, anime, cyberpunk].
**QUICK_PROMPTS:** Portrait(85mm shallow DoF) · Landscape(golden hour wide) · Product(white bg studio) · Fantasy(volumetric concept-art) · Sci-Fi(neon cyberpunk rain) · Food(editorial warm) · Architecture(dramatic angles) · Fashion(Vogue editorial).

## Источники-резервы (опенсорс-клоны Higgsfield, для дальнейшего)
- **github.com/Anil-matcha/Open-Higgsfield-AI** (= Open-Generative-AI) — Muapi-клон: `src/lib/promptUtils.js` (камера-токены ✅), `models_dump.json` (69KB дамп моделей), `CinemaStudio.js`, `MarketingStudio.jsx`, `public/assets/cinema/*.webp` (превью камер/линз). Форки: tocasoft, sunnychase, bloxy-studios, clicworld-andre.
- **github.com/higgsfield-ai/skills** (офиц., клонирован → `_higgsfield_re/hf_skills_repo`): 4 CLI-скилла + model-catalog.md + prompt-engineering.md + marketing-*.md + COOKBOOK.md.
- docs: anil-matcha-open-higgsfield-ai.mintlify.app/guides/{camera-controls,model-selection} · unifically.com/models/higgsfield-cinematic-studio-image.
- ⚠️ AI Stylist pose/background/outfit + Soul style_id — НЕ в клонах (серверные Higgsfield); слаги выше = иллюстративные.
