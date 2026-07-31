# Higgsfield Local — flow cookbook (готовые пайплайны)

Каждый флоу = последовательность: **prompt_builders → router (генерация) → assemble**. Камера-доктрины и шаблоны — из реверса
(`references/flow-skills-*.md`, `references/subagents-*.md`). Модель выбирает `router.py` (direct где можно, hf.exe для эксклюзивов).

## cinematic (кино-трейлер, сюжет)
Конвейер cinematic-5: dramaturg (Want/Mask/Tell, tension_curve) → director (motifs/rhythm/bold_image) → style-architect (film_lock: sensor/lens/light, DP-ref) → shot-planner (beats, Frame Distinction, State Ledger) → prompt-writer (5-блочный prompt_text).
```
# 5-агентный конвейер (dramaturg→...→prompt-writer) = функция:
python -c "import prompt_builders as p,json; print(json.dumps(p.build_cinematic_5('<сюжет>'),ensure_ascii=False,indent=1))"
# на отдельный кадр — camera-rig (6 камер/11 линз/6 фокусных/3 диафрагмы):
python scripts/prompt_builders.py cinematic --base "<кадр>" --camera "Modular 8K" --lens "Creative Tilt" --focal 35 --aperture f1.4
# keyframes: Soul/nano (router) → видео: Seedance 2.0 (Runway, $0) или Veo 3.1 (cinematic+audio)
python scripts/router.py generate seedance_2_0 --prompt "<shot>" --image kf.jpg --aspect 21:9
python scripts/assemble.py concat clips.txt out.mp4 ; assemble.py platform_export out.mp4 final.mp4
```
Soul-anchoring (опц.): `hf soul-id create` → персонаж в каждом кадре (face-lock).

## highMD / classicMD / typographyMD / infographicMD / productMD (моушн-дизайн)
1. Раскадровка одним изображением: `build_board_spec` → gpt_image_2 (router) лист 3×2 (или 3×3 для productMD).
2. Анимация: `build_sandwich_prompt --doctrine <X>` → Seedance 2.0 (Runway, count=2; productMD count=1).
```
python scripts/prompt_builders.py board --doctrine highMD --palette "#000,#00e5ff,#ff003c" > board.txt
python scripts/router.py generate gpt_image_2 --prompt "$(cat board.txt)" --aspect 16:9   # storyboard sheet
python scripts/prompt_builders.py sandwich --doctrine highMD --aspect 9:16 --palette "#000,#00e5ff,#ff003c" > clip.txt
python scripts/router.py generate seedance_2_0 --prompt "$(cat clip.txt)" --image sheet.jpg --aspect 9:16
python scripts/assemble.py platform_export raw.mp4 final.mp4
```
Доктрины: highMD=Hyperkinetic Chaos · classicMD=hold-steady · typographyMD=буквы движутся · infographicMD=Layered Reveals (HR-5 metric_values) · productMD=Bot&Dolly+Special Beat кадр4 (нужно реал-фото продукта → character-sheet).

## ugc / unboxing / tutorial / try-on / product (слот-борды)
product-analyzer → ugc-character (text2image_soul_v2 3:4) → слот-борд (gpt_image_2: 3×9:16 или 4×9:16) → ugc-clip (Seedance 9:16). First-Word hook (без OK/So/Um). Канон-арки: unboxing Packed→Reveal→Focus→Satisfaction; try-on Pre→Wear→Texture(hands-free)→Pose (No Mirrors); tutorial Step-N сквозная нумерация. lip-sync на говорящих кадрах, VO на close-up. → `assemble.py concat` + CTA-tail.

## tv-ad (премиум реклама)
brand-analyzer (сайт→бренд-бук) → GATE tv-ad-script (7-панель+Packshot) → tv-ad-character(soul_v2, palette-locked)+tv-ad-location(gpt_image_2) → GATE tv-ad-seedance (Anti-bleed 4-layer, medias порядок Локация→Продукт→Герой→Бренд = @Image1..4). Screen Lock для устройств. 3 формата: problem-solution/lifestyle/high-energy.

## podcast (двое за столом)
5 фаз: Hero Plates (soul_cinematic 3:4) → Empty Location (16:9) → Seated Composite (gpt_image_2, medias=локация+портреты) → 4-panel B/W storyboard → Seedance chunks 8-15с. Shot Algebra (CU1→CU2→общий→слушатель+VO, не пересекать 180°). → montage.

## cartoon (мульт)
scene-parse (JSON-реестр) → style-formula (80-100 слов, КОНСТАНТА байт-в-байт) → [char/loc/prop]-base (soul_cinematic) → -stylize (seedream_v5_lite по формуле) → shot-plan/clip-plan (beats) → seedance-clip (@Image1 loc/@Image2 char, медиа-порядок Loc→Trans→Chars→Props). Без имён персонажей.

## Эксклюзивы (только hf.exe)
```
hf generate create soul_cast --prompt "<character_params>" --aspect 16:9      # Soul-видео персонаж
hf generate create marketing_studio_video --mode ugc --product_ids ... --hook_id ...   # DTC реклама
hf generate create brain_activity --video <url>                               # Virality Predictor → отчёт
hf soul-id create --name X --soul-2 --image f1..f5                            # обучить лицо (face-lock)
```

## Аудио (router/hf или свои ключи)
TTS: ElevenLabs (YourFirstName voice YOUR_ELEVENLABS_VOICE_ID) ИЛИ hf voices (60, voices.json). Музыка: ElevenLabs Music / Lyria 2.
Микс: `assemble.py audio_duck video music out` (sidechaincompress) → `loudnorm -14`.

## Дефолты (их, проверенные)
Seedance 720p, Veo Fast 5s, NB resolution:2k, карусель=параллельные вызовы, Audio: секция обязательна в Seedance,
TAIL FREEZE 13.7-15s, платформенный экспорт -14 LUFS / GOP 2с / h264 high@4.2.
