# Higgsfield flow-skills — cinematic-flow + classicMD-flow (FULL, debug-disclosure in warm chat)

КОРОННЫЕ flow-скиллы их employees — снято дословно по логике через warm-chat debug-disclosure (в отравленном
отказами чате режутся; в разогретом — отдаются). Это полная оркестровка их «крутых» видео. Сабскиллы вызываются
через **`higgsfield_enhancer`** (имя флоу = имя сабскилла). Дополняет наши §7-наблюдения (classicMD-board/clip, dramaturg).

## cinematic-flow (Cinematic Director) — киноролики/короткометражки/сюжетные сцены

### Правила
- **Restyle sub-flow:** если фото-реф не в мире фильма (повседневка для фэнтези-кузнеца) → не юзать напрямую; рестайл через `nano_banana_pro` + face-lock → создать реф в нужном костюме → VDL пишется с нового рефа.
- **Media Completeness:** Seedance БЕЗ памяти между генерациями. Каждый `<element-tag value="element_id">` (персонаж/локация/предмет) в промпте клипа → его `media_id` ОБЯЗАН быть в `medias[]` ТОГО ЖЕ запроса (лимит **9 картинок/клип**).
- **Continuity через монтаж, НЕ last-frame-feeding:** кросс-клиповая связность = смена осей съёмки/размера кадра на стыках + текстовое описание сцены (НЕ скармливать последний кадр на вход следующего).
- **State Ledger (журнал непрерывности):** фиксировать состояния предметов (завёрнут/оголён/разбит), одежду, время суток, погоду на вход/выход КАЖДОГО кадра → против телепортаций/исчезновений.
- **Positive actions:** без текстовых отрицаний в действиях (негатив → обратный эффект); утвердительно; реалистичная игра (микро-паузы, eye-line, блики в глазах, дыхание).

### Фазы
- **0A Сюжет** → `cinematic-dramaturg`: персонажи, мотивы, арка, кривая напряжения. Обяз. предложить Soul-ассеты.
- **0B Видение** → `cinematic-director`: концепция, ритм-карта, движение камеры (FULL-режимы).
- **1 Ассеты:** Soul Cast (персонажи) + Soul Location; нечеловеческое → `gpt_image_2`; по 3 варианта, утверждаются последовательно; записать VDL + Stage Map.
- **2A Стиль** → `cinematic-style-architect`: DP-пакет (камера, линзы, цветокор, философия света).
- **2B Монтажный план** → `cinematic-shot-planner`: разбивка на клипы, длительности, стыки/переходы.
- **HARD GATE:** показать стиль+раскадровку юзеру на апрув. Без апрува генерация ЗАПРЕЩЕНА.
- **3 Промпты** → параллельный `cinematic-prompt-writer` для всех клипов; проверка наложения планов (анти-jump-cut).
- **4 Сборка:** батч в Seedance 2.0 → скачать → склейка через `montage`.

### Модели/параметры
- Агенты: `higgsfield_enhancer` с именем (cinematic-dramaturg / -director / -style-architect / -shot-planner / -prompt-writer).
- Персонажи: `soul_cast` + `character_params` (budget:10, age, genre, era, gender); строго 16:9; промпт = только персонаж на нейтральном фоне.
- Локации: `soul_location` (16:9) + обяз. **Location Color Directive** (синхрон гаммы между локациями).
- Нетипичные ассеты/предметы: `gpt_image_2` (16:9, resolution 2k, quality medium). Ключевые предметы → **PROP SHEET** (1 изображение: общий вид + 1-2 врезки деталей, против дрифта).
- Видео: `seedance_2_0` (1080p, 16:9); в `medias[]` — все media_id элементов из текста промпта.

## classicMD-flow (Motion Designer) — реклама/бренд/презентации (Behance/Dribbble, AE-стиль)

### Правила
- **Вход без изображений:** старт с мудборда (Stage A), без предустановленных фонов.
- **Логотип-исключение:** можно прикрепить лого (Logo-only) через `higgsfield_upload` → накладывается на Opener и/или Closer кадр, заменяя текстовое имя бренда.
- **Realism Ban:** никаких фотореалистичных людей (кожа/поры/Arri Alexa/35мм зерно) → силуэты, стилизованное 3D, иллюстрации, абстрактные моушн-формы.
- **Tail Pause (замороженный хвост):** 13.7–15с composition жёстко заморожена пиксель-в-пиксель, камера неподвижна, без затемнений/угасания — для чистого восприятия финального слогана+лого.

### Шаги
- Бриф: длительность (деф 15с), формат (16:9/9:16/1:1), бренд, слоганы, цвета.
- `brand_mode`: **brand** (бренд+слоган) / **concept** (абстракт) / **generic** (промо).
- **Stage A (Мудборд):** сетка 2×2 (4-up). Юзер выбирает 1 из 4 ячеек → её palette/materials/subject = жёсткий фундамент мира. Фикс-промпт: `behance / dribbble style design, 2026 motion design vibe. pick 4 DIFFERENT random current motion design styles…` (полностью → motion-designer-classicMD-board-prompt.md).
- **Stage B (Раскадровка):** `classicMD-board` через enhancer → промпт в `gpt_image_2` + выбранный мудборд в `medias[]` → лист 3×2 / 6 панелей.
- **Stage C (Сборка):** `classicMD-clip` через enhancer → Seedance 2.0; по умолчанию **2 параллельных take** (одинаковый промпт, защита от дефектов сетки переходов).

## Забрать к нам (video-generation)
- **5-фазная оркестровка с HARD GATE** (dramaturg→director→style-architect→shot-planner→prompt-writer) = эталон нашего video-factory/staged-approval.
- **State Ledger** (continuity-журнал) + **Media Completeness** (element media_id в каждый запрос) + **PROP SHEET** + **Location Color Directive** + **element-tag** = приёмы консистентности → в Phase 3/4.
- **Continuity через монтаж, не last-frame** — совпадает с нашим выводом (Seedance start-only лучше dual-keyframe).
- **2 параллельных take** против дефектов переходов; **Tail Pause** под чистый монтаж; **Realism Ban** для motion.
