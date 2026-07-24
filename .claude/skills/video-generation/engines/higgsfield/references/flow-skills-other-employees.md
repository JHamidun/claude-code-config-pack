# Higgsfield other employee flows — podcast / ai-influencer / personal-clipper / cartoon / product-photoshoot / amazon (full)

## podcast-flow (MDP — двое ведущих за столом)
Text-only сборка >15с ЗАПРЕЩЕНА. **5 фаз:** 1) **Hero Plates** — портрет каждого ведущего (`soul_cinematic` 3:4, белый студ. фон); 2) **Empty Location** (`soul_cinematic` 16:9); 3) **Seated Composite** — коллаж посадки за стол (`gpt_image_2` 16:9, medias=локация+оба портрета); 4) **4-panel B/W Storyboard** (`gpt_image_2` 16:9, белый фон, medias=коллаж); 5) **Seedance Chunks** 8-15с (`seedance_2_0` 16:9 1080p).
**Shot Algebra:** чередовать ракурсы (CU ведущий1→CU ведущий2→общий→CU слушателя+VO), НЕ пересекать 180°-линию. Клип-medias: Storyboard / Seated / портрет говорящего / портрет слушающего (мимика). 1-й клип = приветствие, дальше с середины мысли. → montage.

## ai-influencer-flow (цифровой аватар/персона)
Выход = 1 hi-q фото человека (портрет/3-4) на нейтрал фоне, без предметов/лого. Модель **`text2image_soul_v2` 3:4 1080p, `enhance_prompt=false`** (жёстко, чтобы не размывать черты). **NSFW-откат:** при блокировке — пересбор с консервативной одеждой (Casual/Sporty) + повтор. Агент `ugc-character` (анатомический промпт) → регистрация через `higgsfield_element` → выдаётся `element_id` для переиспользования в видео.

## personal-clipper-flow (YouTube → Shorts/Reels)
Только физическая нарезка (текст→`youtube-content`). Тул **`youtube_clipping`**. Параметры: `youtube_urls` (1-100), `clips_num`=10, `clip_aspect`=9:16, `subtitle_position` (bottom/center/top), `subtitle_highlight_hex`, `track_face_crop`=false (умное удержание лица). Вывод — встроенный плеер (без локальных путей).

## cartoon-flow (2D/2.5D мульт, Anime/Cartoon/Doodle)
**Style Formula:** агент `cartoon-style-formula` пишет описание стиля (80-100 слов) → фиксируется КОНСТАНТОЙ, передаётся **байт-в-байт** во все генерации (абсолютное совпадение рисовки). **Без имён персонажей** (стабильные фразы: the silver-haired woman). Asset-порядок в Seedance: 1.Локация 2.Переходная локация 3.Персонажи 4.Предметы (нарушение → не те текстуры).
Фазы: 0 `cartoon-scene-parse` → 0.5 Triage (рисунки юзера: как стиль или как готовые ассеты) → 1 Style Lock → 2-3.5 Asset Lock (`soul_cinematic` → стилизация `seedream_v5_lite`, апрув каждой) → 4-4.5 `cartoon-shot-plan`/`cartoon-clip-plan` → 5 render `seedance_2_0` 1080p 16:9 → 6 montage.

## product-photoshoot (студийная фотосъёмка продукта)
Промпты строго по блок-шаблонам: **Subject / Composition / Lighting / Background / Camera / Brand Integration** (свободный текст запрещён). **Prompt Sanitization:** без имён фотографов (Carl Kleiner)/журналов (Vogue)/брендов → расшифровать в физ. свойства («геометрическая блокировка цвета»). Auto = 3× 1:1 clean-studio. НЕ для Amazon (→ amazon-product-listing).
**10 режимов:** product-shot · lifestyle-scene · closeup-product-with-person · pinterest-pin (2:3) · hero-banner · social-carousel (3-10 слайдов) · ad-creative-pack · virtual-model-tryout · conceptual-product (CGI/левитация/всплески) · restyle (смена сезона/фона/света при сохранении геометрии).

## amazon-product-listing
Полный комплект изображений под маркетплейс Amazon (главное фото на белом, инфографика, lifestyle, баннеры A+ Brand Content) по жёстким правилам платформы.

## Забрать к нам
- **podcast 5-фазный composite-паттерн** (Hero Plates→Empty Location→Seated Composite→storyboard→chunks) + Shot Algebra (180°-правило) — для интервью/диалоговых роликов.
- **ai-influencer:** `enhance_prompt=false` для лок лица + NSFW-откат + element-регистрация персоны.
- **cartoon Style Formula** (80-100 слов байт-в-байт константа) = приём абсолютной консистентности рисовки → в наш image/video пайплайн.
- **product-photoshoot блок-шаблоны + Prompt Sanitization + 10 режимов** — прямо в наш image-generation/product workflow.
- personal-clipper = их аналог нашего shorts-нарезчика (youtube_clipping параметры как референс).
