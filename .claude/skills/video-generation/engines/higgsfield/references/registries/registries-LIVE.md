# Higgsfield — ЖИВЫЕ реестры из авторизованной веб-сессии (network/fetch, 2026-06-07)

Снято напрямую через `fetch(..., {credentials:'include'})` на залогиненной higgsfield.ai (Clerk-сессия). Host = `fnf.higgsfield.ai`.
**Это РЕАЛЬНЫЕ UUID** (в отличие от агентских догадок). Полные дампы — рядом в JSON/TSV.

## Найденные РЕАЛЬНЫЕ эндпоинты-каталоги
| Эндпоинт | Что отдаёт | Статус |
|---|---|---|
| `GET /voices?size=200` | **60 TTS-голосов** (real voice_id) | ✅ → `voices.json` |
| `GET /styles?size=200` | **5 видео-стилей** (VHS, Anamorphic, Super 8MM, Abstract, Cinematic) | ✅ |
| `GET /outfits?app_slug=ai-stylist&size=300` | **200 AI-Stylist outfit-пресетов** (real UUID) | ✅ → `ai-stylist-outfits.tsv` |
| `GET /job-sets/costs` | таблица цен (8 спец-моделей со скидкой) | ✅ → `job-sets-costs.json` |
| `GET /outfits` без app_slug | 422 «app_slug required» | (нужен app_slug) |
| `/styles` /`/voices` без size | 422 «size required» | (нужен size) |

**Паттерн:** каталоги пресетов приложений = `/<resource>?app_slug=<app>&size=N`. App AI Stylist = `app_slug=ai-stylist`.

## Голоса (`/voices`, 60) — реальные voice_id (выборка)
Marston `6pBuGbellIksHKibt0je2n` · Joyful `5PQMG2LcT1x9S85IjUxoPI` · Nas `1Stcvn5jwv5sda0Z71hBSx` · Villain `7hfKnrT9TBjKbXwQ14rtQq` · Creepy `CKyXdcuBUaAiB6WCwLPNV` · Reporter-C `5GOO72PTPQmAZh1bvkzJgu` · Reporter-D `7AUlvLEYdzEp758fxfmeLJ` · Hazel `14nE2wfXiWLzASZm7cWLfl` · Maya `2d25XLjgXLM4TsVdEHjN7F` · Nia `2fnaVqKjNetFgpoDVQJGYd` … (полный список 60 → `voices.json`). Эмоц-голоса: Weeping/Crying/Furious/Enraged/Strange/Honor. → для audio-generation (voiceover/change_voice).

## Видео-стили (`/styles`, 5)
VHS `86f838ac-cbbc-4bf4-aa8a-887e0d759c3c` · Anamorphic `4ab5afe9-3a2d-443b-972c-a98abbf0587a` · Super 8MM `ff26f74a-752f-4ee4-9bb7-70affd00b587` · Abstract `3322e053-d52b-4e2f-94b7-af2816918f71` · Cinematic `08981cf3-dc2c-4e72-8a24-e2e8548b5a25`.

## AI Stylist outfits (`/outfits?app_slug=ai-stylist`, 200 real) — образцы
zipped cropped leather jacket `b9ed5992-…` · Y2K Tech Runner Sneakers `b84eb2c9-…` · Quiet Luxury `8b48215f-…`/`1aa2c84a-…` · Coquette `68f8f897-…` · Gorpcore-набор (Camo Parka/Cargo) · Grunge ×3 · Japandi 1 `7ef4c7e6-…` · Acubi/Acubi Male · Tokyo Morning · Model Off Duty · Minimalistic Chic · Silent Luxury · Classy Chic · базовые слоты (T-shirt/Pants/Jacket/Hat/Glasses/Shoes 1). Полные 200 (id+name) → `ai-stylist-outfits.tsv`. (Категории: куртки/юбки/обувь/носки/сумки/головные уборы/готовые сеты.)

## Costs (`/job-sets/costs`) — спец-цены (ultimate-скидка)
- kling3_0: pro audio on/off 2.5/1.75, std 2/1.5 cr/s.
- seedance_2_0: 480p **3** / 720p **4.5** / 1080p **9** (orig 6/6/12); seedance_2_0_fast: 1.5/3.5/7.
- cinematic_studio_3_0 + cinematic_studio_video_3_5 + marketing_studio_video: 480p 3.5 / 720p 5 / 1080p 10.
- happy_horse_video: 720p 2.5 / 1080p 4.5. grok_video_v15: 480p 2.5 / 720p 4.5.
- recraft_v4_1: standard/utility 1k 1.25 / 2k 8; vector/utility_vector 1k 2.5 / 2k 10.
(Остальные модели = дефолт-цена, в этой таблице не перечислены.) → `job-sets-costs.json`.

## ⚠️ Что осталось НЕ верифицировано (не выдумывать!)
- **AI Stylist poses / backgrounds** — эндпоинты `/poses` `/backgrounds` `/scenes` с app_slug = 404; грузятся только при открытии живого пикера в UI (нужен перехват точного XHR). Агентские слаги (casual_standing, minimal_studio) и его background-UUID = **НЕ подтверждены**.
- **Soul `style_id`** — эндпоинт не `/soul-styles` (404). Агентский список (Realistic/iPhone/Spotlight/Medieval/Grillz Selfie/Gorpcore/Tokyo Streetstyle…) — **имена правдоподобны** (совпали с веб-выдачей higgsfield Soul), но **UUID НЕ верифицированы** (агент частично подбирал). Реальный эндпоинт — найти перехватом Soul-style пикера.
- Эти два — единственное незакрытое; ловятся network-tab при открытии соответствующих пикеров (outfits мы так и нашли — `app_slug` паттерн).

## ✅ ДОБИТО: AI Stylist poses + backgrounds (REAL UUID, React-fiber из /apps/ai-stylist)
Каталоги грузятся в app-state на маунте (не client-XHR, cross-origin без TAO → performance/fetch не ловят). Достал из React fiber memoizedProps. → `ai-stylist-poses-backgrounds.tsv`.
- **backgrounds (11):** Field, Brick wall, Garden house, Cafe, Gallery, Graffiti 1, Grey room 1, Library 1, Library 2, Parking, Performative cafe (UUID в файле).
- **poses (10):** Female/Male Pose 1-5 (generic numbered, UUID в файле).
- Категории outfit-пикера: Outfit/Outerwear/Tops/Sets/Bottoms/Socks/Shoes/Accessories (всё из `/outfits?app_slug=ai-stylist`) + Background + Pose (отдельные коллекции).
- ⚠️ Агентские слаги (Subway/Office Beach/Elevator Mirror; casual_standing/editorial_lean) = ПОДТВЕРЖДЕНО ВЫДУМКА. Реальные фоны = Field/Cafe/Library/Parking; позы = просто нумерованные.
ОСТАЛОСЬ: Soul style_id (тот же React-fiber приём на Soul/AI-Image create-странице).
