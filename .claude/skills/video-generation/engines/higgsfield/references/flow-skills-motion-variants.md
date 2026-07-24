# Higgsfield motion-design flow variants — highMD / productMD / typographyMD / infographicMD (full)

4 варианта моушн-флоу (Motion Designer employees). Общий каркас всех: **Stage A (moodboard 4-up ИЛИ upload) →
Stage B (<name>-board → gpt_image_2 storyboard) → Stage C (<name>-clip → seedance_2_0)**. Различаются доктриной
камеры/правилами. Сабагенты board/clip вызываются через `higgsfield_enhancer`. Снято debug-disclosure (warm chat).

## highMD-flow (Premium Motion / MDH High-Energy)
- **Realism Ban** (герой = абстрактная геометрия/материалы бренда, без людей/кожи).
- **Master-camera = HYPERKINETIC CHAOS** (противоположность classicMD!): Vertigo Pull · Crash-out Reveal · Shatter Push-through · Hyperkinetic Orbital Sweep (360°-вращения, взрывные наезды).
- **Transitions ≥4/5 = VFX-морфы:** Dramatic Particle Dissolve · Light Sweep · Collapse · Push-through (обычные склейки/наплывы ЗАПРЕЩЕНЫ).
- Stage A: A1 (upload реф → foundation_media_id+url, мудборд пропускается) / A2 (4-up moodboard маркер «HIGH MOTION» → ask_user_question выбор). Stage B `highMD-board` (inputs: foundation_source="moodboard-pick"|"image-attached", logo_source, brand_mode) → gpt_image_2 6-панель 3×2. Stage C `highMD-clip` → seedance_2_0 **count=2**.
- Seedance prompt: плотный английский **250-300 слов** (динамика, текстуры материалов, траектории камеры, конкретные Match-cut переходы между 6 сценами).

## productMD-flow (Track B / MDC8) — ЕДИНСТВЕННЫЙ с разрешённым фотореализмом
- **Обяз. реальное фото продукта** (автоген «похожего» запрещён). **Без людей** (человек юзает продукт → редирект в `tv-ad`).
- **Scale Alternation:** строгое чередование масштабов (Wide→Macro→Medium→Special→Medium→Macro→Overhead→Wide→Medium endcard), никаких 2 одинаковых подряд.
- **Special Beat:** 4-й кадр из 9 = сложный физ-трюк (взрыв-схема / bullet-time / спираль Фибоначчи / пролёт камеры сквозь продукт).
- **Диегетический текст:** интегрирован в окружение/поверхность продукта; оверлеи только в кадрах 01/08/09, строго белые.
- Stage 0 upload→UUID. Stage A **Character/Product Sheet** (5-6 ракурсов в ряд, тех-подписи, материалы, hex-палитра = «производственная библия», геом. стабильность) — апрув. Stage B `productMD-board` → gpt_image_2 **9-shot 3×3**. Stage C `productMD-clip` → seedance_2_0 **count=1** (sheet даёт точность с 1 дубля); в `medias[]` ТОЛЬКО storyboard (двойное прикрепление sheet+board ЛОМАЕТ Seedance).
- Seedance prompt: **~600 слов**, 4-слойный сэндвич (правила геометрии + покадровые планы с физикой света/материалов + замок удержания + правила заморозки последних секунд).

## typographyMD-flow (Type-As-Subject)
- **Текст = субъект:** буквы движутся/трансформируются/распадаются/собираются как 3D-тело (НЕЛЬЗЯ текст поверх статики или банальный перелистываемый текст).
- 2 регистра: **2d-editorial** (бумага, halftone, сдержанная палитра, Tier 2) · **kinetic-3d** (глянцевые/металлические/хромированные буквы, Tier 1 Premium 3D).
- Scene Variation: каждый из 6 кадров — РАЗНЫЕ слова/фразы (без зацикливания) + ≥4 разных масштаба.
- Stage A (A1 upload шрифт/стиль / A2 moodboard «TYPOGRAPHY»). Stage B `typographyMD-board`→gpt_image_2 6-панель. Stage C `typographyMD-clip`→seedance_2_0 **count=2**.
- Seedance prompt: **~250-300 слов**, фокус на анимации БУКВ внутри кадра; камера очень плавный Slow elegant glide ИЛИ статична (движение букв доминирует над камерой).

## infographicMD-flow (анимированная инфографика / KPI / dashboards)
- **HR-2 числовые заголовки:** цифры/проценты ($420, 84%) гигантского размера = главные герои; мелкие подписи увеличить или удалить.
- **HR-5 запрет выдуманных данных:** только переданные пользователем числа; выдумывать Q1-Q4/статусы ЗАПРЕЩЕНО; нет данных → `ask_user_question`.
- **Layered Reveals:** графики строятся последовательно (оси → рост столбцов → загорается число); движение несёт смысл.
- Stage A (A1 upload скриншот дашборда [рекоменд.] / A2 moodboard «INFOGRAPHIC»). Stage B `infographicMD-board` (inputs обяз. `metric_values_from_brief` — массив точных чисел) → gpt_image_2 6-панель. Stage C `infographicMD-clip`→seedance_2_0 **count=2**.
- Seedance prompt: Data state transitions между сценами; камера стабильна; Match-cut (столбчатая→линейная через перетекание материала = Dramatic Object Morph).

## Сводка камера-доктрин (забрать как пресеты)
| Flow | Камера | Subject | Кадров | count |
|---|---|---|---|---|
| classicMD | hold-steady (MDCM, internal choreography) | абстракт | 6 (3×2) | 2 |
| highMD | **Hyperkinetic Chaos** (Vertigo/Crash/Shatter/Orbital) | абстракт/материалы | 6 | 2 |
| typographyMD | статична / slow glide (буквы движутся) | текст-3D | 6 | 2 |
| productMD | Scale Alternation + Special Beat | реальный продукт (photoreal OK) | 9 (3×3) | 1 |
| infographicMD | стабильна, Layered Reveals | цифры/графики | 6 | 2 |
| cinematic | DP-driven (style-architect) | персонажи/сюжет | 4/8/12 | — |
→ Это готовый набор «режимов» для нашего video-generation: выбираешь доктрину под задачу.
