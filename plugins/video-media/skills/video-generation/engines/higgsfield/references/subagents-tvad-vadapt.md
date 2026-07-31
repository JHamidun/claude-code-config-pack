# TV-Ad (4) + Video-Adapt (3) sub-agents — финал реестра

## tv-ad-script (7-Panel Beats)
Сценарий 15с 16:9, формат problem-solution/lifestyle/high-energy + Product DNA. **7 панелей** (Shot01 Hook/Problem → 02-05 Development/применение → 06 Payoff → 07 Packshot+лого). Покадрово VO/on-camera dialogue + Foley. Screen integration (is_screen_bearing → крупная графика на дисплее). Выход = текстовая структура (НЕ JSON): `LOGLINE / AD TYPE / TONE(heartfelt|witty|dramatic|aspirational|playful) / DURATION / HERO / WORLD / BEAT SHEET (per-shot Visual "ENTIRE 16:9 frame fills with..." + Audio + Sound design) / MANDATORY TAIL FREEZE 13.7-15s`.

## tv-ad-character
`text2image_soul_v2` 3:4 2k. Одежда **palette-locked** по HEX брендбука. Белая циклорама (для интеграции).
`A professional studio medium-shot of [gender] actor matching HERO. Wearing [wardrobe in brand color #HEX]. Clean white cyclorama. Profoto silk-diffused key upper-left, soft rim. ARRI Alexa Mini LF, cinematic color science, raw skin. No scene context.`

## tv-ad-location
`gpt_image_2` 16:9 2k, brand palette echo в свете/caustics.
`Cinematic wide establishing shot of empty premium [location type]. Structured geometry, deep space, high ceiling. Lighting: volumetric shafts through frosted glass, caustic reflections tinted brand #HEX. High contrast, desaturated silver, dark shadows. Cinema 4D Octane / ARRI ProRes 4K. No people.`

## tv-ad-seedance (Anti-bleed 4-layer sandwich)
`@Image1 location, @Image2 product, @Image3 hero, @Image4 logo. Animate as ONE continuous 16:9 commercial. STYLE: ARRI Alexa LF, ProRes 4K, 180° motion blur. SCENE: env of @Image1. CHOREOGRAPHY 15s: Shot01 "ENTIRE 16:9 frame fills with [...]" hero @Image3 [action] CAMERA+LIGHT → Shot02 hard-cut close-up @Image2 → ... → Shot07 packshot logo @Image4 over @Image1 + @Image2. AUDIO: narrator '[VO]', Foley cues. 13.7-15s SILENT TAIL FREEZE pixel-identical.` Anti-bleed = удержание лица/геометрии все 7 сцен.

## vadapt-* (видео-адаптация, шаг C) — рерайт чанков с токенами `<<image_N>>`
Все три выдают `{chunks:[{chunk_index,start_sec,end_sec,monologue,visual_prompt}]}`, сохраняя тайминги оригинала.
- **vadapt-adapt-avatar:** замена персонажа → `<<image_3>>` (аватар) в `<<image_1>>` (локация); рерайт действий/мимики под физику нового аватара.
- **vadapt-adapt-product:** замена продукта → `<<image_2>>`; адаптация рук под форму/вес/размер, окружение под гамму продукта.
- **vadapt-adapt-preserve:** БЕЗ рерайта — оригинальный текст 100% verbatim, только разметка токенами `<<image_1/2/3>>` в местах упоминания объектов.

→ Токен-система `<<image_N>>` (vadapt) vs `@ImageN` (генерация) — два синтаксиса привязки референсов.
