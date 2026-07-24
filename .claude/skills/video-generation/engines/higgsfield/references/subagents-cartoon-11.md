# Cartoon-flow — 11 sub-agents (полный мульт-пайплайн через higgsfield_enhancer)

Пайплайн: scene-parse → style-formula → [character/location/prop]-base → -stylize → shot-plan → clip-plan → seedance-clip.

1. **cartoon-scene-parse** — старт-разбор. Мультиязычный вход, реестр на английском. Формат single-video(≤15с)/multi-clip. JSON: `{narrative_summary, characters[{shorthand:"the silver-haired woman",gender,age_band,description,from_upload}], locations[{shorthand,interior_exterior,time_of_day,description,from_upload}], props_candidates[{shorthand,description,should_lock,from_upload}], style_direction{preset_hint: anime|classic-2d|3d…}}`.
2. **cartoon-style-formula** — «закон рисовки» (80-100 слов). **STYLE LOCK: константа**, копируется без изменений во все stylize-шаги.
3. **cartoon-character-base** — фотореалистичная анатомия персонажа. `soul_cinematic` 3:4 2k, нейтральный серый #DDDDDD, без стиля/камеры/фона (чистая анатомия).
4. **cartoon-character-stylize** — наложение формулы на портрет. `seedream_v5_lite` 3:4 high, base в medias; держит черты лица, адаптирует геометрию (cell-shading, аниме-глаза, обводка).
5. **cartoon-location-base** — фотореалистичный фон без персонажей. `soul_cinematic` 16:9 2k (геометрия/перспектива/свет).
6. **cartoon-location-stylize** — фон под формулу. `seedream_v5_lite` 16:9 high.
7. **cartoon-prop-base** — изолированный предмет. `soul_cinematic` 1:1 2k, серый фон.
8. **cartoon-prop-stylize** — предмет под формулу. `seedream_v5_lite` 1:1 high. Промпт: `[Style Formula] applied to object in @Image1. Re-render the isolated prop, transforming materials/outlines/lighting into [preset] style. Plain neutral background.`
9. **cartoon-shot-plan** — монтаж на клипы 8-15с (multi-clip), Frame Distinction. Текст-артефакт: `## SHOT PLAN: [Title] / Clip N (timecode) / Location / Characters / Action Beat / Camera / Transition to next [INK FLOW…]`.
10. **cartoon-clip-plan** — покадровые beats. JSON: `{clip_index, duration_seconds, location{shorthand,media_id}, characters[{shorthand,media_id,initial_position}], props[], is_fresh_open, beats[{timecode_range,action_description,camera_move}], sound_design}`.
11. **cartoon-seedance-clip** — финальный Seedance-промпт. **Медиа-порядок: Локация→Переходная локация→Персонажи→Предметы** (нарушение ломает @Image привязку). Шаблон:
```
CRITICAL: Animate as ONE single continuous full-frame 16:9 cartoon film. @Image1 is the environment. @Image2 is the character. Translate every storyboard panel into fullscreen motion.
STYLE: [Style Formula verbatim].
SCENE: Set on environment of @Image1. Character @Image2 initially positioned [initial_position].
ANIMATION SEQUENCES:
- 0:00-0:04: [beat1 positive-only] + CAMERA: [move].
- 0:04-0:12: [beat2 + lip-sync/expressions] + CAMERA: [move].
AUDIO: [sound_design]. Finished cartoon SFX-only, no speech.
```
→ Приём base→stylize (фотореал-заготовка → стилизация по формуле-константе через seedream) = сильный паттерн консистентной рисовки.
