# Flow Playbooks — наши локальные «сотрудники» поверх hf.exe

Рабочие рецепты, реконструированные из реверса Higgsfield-флоу (наблюдением за их employees) и
переложенные на наш стек: `hf.exe` (генерация) + Nano/GPT Image (кейфреймы) + наш `video-editor`/ffmpeg (монтаж)
+ ElevenLabs/Suno (звук). Цель — запускать «сделай кинематографичный ролик / motion-design интро / UGC» и
получать качество их Supercomputer, но своими руками и моделями напрямую.

Общий конвейер (как у них): **бриф → prompt-enhance → [storyboard] → keyframe(s) → video (Seedance/Veo) → montage**.
Ключевые переиспользуемые блоки — ниже (§A LOCK, §B MDCM, §C prompt-схемы), потом 4 готовых флоу.

---

## §A. LOCK-система (консистентность серии кадров) — вшивать в КАЖДЫЙ промпт серии

```
SUBJECT LOCK   — один герой/объект во всех кадрах (тот же персонаж/форма/продукт)
MATERIAL LOCK  — единый материал/фактура (напр. refractive liquid-chrome+neon caustics)
STYLE LOCK     — единый рендер-язык (напр. premium sculpted 3D на dark void, controlled bloom)
PALETTE LOCK   — 3 доминирующих цвета (hex), сэмплированные из первого кадра
ATMOSPHERE LOCK— настроение в 3-5 словах (futuristic, quiet-power, luminous…)
CAMERA/FILM LOCK (для photoreal) — ARRI Alexa Mini LF, Leica Summilux 40mm f/2.0, LogC→Rec709, fine grain
```
Без LOCK serpentine-морфинг и «разъезд» стиля между кадрами. Это их главный приём консистентности
(подтверждено: cinematic-flow Soul-anchor + classicMD LOCKS RECAP).

## §B. MDCM — Master Camera Doctrine (анти-клише движения)

```
ПО УМОЛЧАНИЮ: камера ДЕРЖИТ статику на 4-5 из 6 шотов; движение — ВНУТРИ кадра
(субъект дышит 0.6-0.9Hz / пульсирует / материал трансформируется / типографика смещается).
МОЖНО: медленный micro-drift 1-3см dolly + parallax (FG/MG/BG 100/75/50) на ≤2 шотах.
ЗАПРЕЩЕНО: hyperkinetic chaos, whip-pan, vertigo pull, crash-out reveal, shatter push-through,
           speed-ramp+stutter, crash zoom, slow-mo (если не просили).
ПЕРЕХОДЫ между шотами = match-cut морфы: LIGHT SWEEP / DRAMATIC OBJECT MORPH / HALFTONE MORPH /
           INK FLOW / DRAMATIC UNFURL / CHROME DUST DISPERSE.
```

## §C. Prompt-схемы

### C1. Cinematic (их `cinematic-dramaturg`) — для одиночного/мультишот киношного клипа
```
Camera: <body+lens+stop>. Camera Style: <движение, что запрещено>. Light: <источники, направления, без fill>.
Style & Mood: <палитра, атмосфера, погода/частицы, bloom/haze>.
Acting: micro-pauses before reactions, precise eye-line, wet living eyes with catch-lights, breath/chest rise.
Narrative Summary: <1 предложение арки>.
Scene Setup: <окружение, реквизит, размещение камеры: дистанция+высота+lens>.
Dynamic Description: <мультишот: каждый = lens (24/35/40/75mm) + камера-мув + действие + СКОРОСТЬ км/ч;
  переходы как "Hard Cut to <lens>, <angle>"; "Cut on the pulse">.
Audio: <слоёный саунд-дизайн: ambient + foley + mechanical + room tone>.
Негативы: No subtitles. No text overlay. No captions. No title cards. No watermarks.
```

### C2. Motion-design storyboard sheet (их `classicMD-board`) — 6-панельный лист одним изображением
6 панелей 3×2, sheet 3:2, dark void + hairline gutters. Pattern A {01,03,05} = текстовые панели (панчи 2-4 слова).
Realism ban (силуэты/3D/2D, не photoreal). Min-text ≥10-12% высоты панели. Каждая панель: CONTENT / NARRATIVE
BEAT (hook→develop→escalate→sustain→build→resolve) / INTERNAL CHOREOGRAPHY (%/Hz) / TEXT / LIGHT (type+direction+does)
/ EFFECTS / PARALLAX. Бренд-wordmark на P06. Полный шаблон → `motion-designer-classicMD-board-prompt.md`.

### C3. Motion-design clip (их `classicMD-clip`) — Seedance-промпт из раскадровки
```
CRITICAL: один непрерывный full-frame 16:9 фильм, НЕ панель-грид. Раскадровка = ПЛАНИРОВОЧНЫЙ бриф; каждый
панель → full-frame шот edge-to-edge. НИКОГДА не показывать сам лист/границы/номера/таймкоды.
<MDCM §B>. Пошотно 0-1s/1-2s/…: STATIC + CHOREOGRAPHY + TEXT (ABSOLUTE TEXT LOCK: текст читается ТОЧНО как
указано, zero deformation) + LIGHT + EFFECTS + PARALLAX, с именованными TRANSITION между.
Tail-freeze: последние кадры pixel-identical (clean tail под монтаж). Audio: SFX-only, no music/VO. No autosubs.
```

---

## ФЛОУ 1 — Cinematic clip (их Cinematic Director)
**Когда:** кино-ролик, продукт/персонаж в движении, 1 шот или короткая сцена.
```bash
HF="${HOME}/.claude/skills/higgsfield/bin/hf.exe"
# 1) (опц.) консистентный герой — Soul ID
"$HF" soul-id create --name hero --soul-cinematic --image p1.jpg --image p2.jpg ; "$HF" soul-id wait <id>
# 2) keyframe (Nano Banana Pro / GPT Image 2), вшить §A LOCK
"$HF" generate create gpt_image_2 --prompt "<scene>, <PALETTE/STYLE LOCK>" --aspect_ratio 9:16 --resolution 2k --wait
# 3) video Seedance из кейфрейма, промпт по §C1
"$HF" generate create seedance_2_0 --prompt "<C1 cinematic prompt>" --start-image kf.png \
  --duration 5 --aspect_ratio 9:16 --resolution 720p --genre epic --wait
# 4) montage (наш) — музыка+сабы+9:16: python ~/.claude/skills/video-editor/...  (ASS-караоке лучше их drawtext)
```

## ФЛОУ 2 — Motion-design intro (их Motion Designer, classicMD)
**Когда:** бренд-интро, 5с, абстрактный/3D/типографика.
```bash
# 1) moodboard 4 стиля (GPT Image 2 3:2) — "4 DIFFERENT motion-design styles, 2x2 board, dark+neon"
"$HF" generate create gpt_image_2 --prompt "<moodboard prompt>" --aspect_ratio 3:2 --resolution 2k --wait
# 2) storyboard sheet 6-панелей по §C2 (GPT Image 2 3:2 2K), foundation = выбранный кадр moodboard
"$HF" generate create gpt_image_2 --prompt "<C2 classicMD-board, foundation=...>" --aspect_ratio 3:2 --resolution 2k --wait
# 3) clip по §C3 (Seedance 2.0 16:9 1080p 5s) из раскадровки
"$HF" generate create seedance_2_0 --prompt "<C3 classicMD-clip>" --aspect_ratio 16:9 --resolution 1080p --duration 5 --wait
# 4) (опц.) SFX-only через procedural BGM / ElevenLabs SFX; reframe под платформу
```

## ФЛОУ 3 — UGC / product short (их UGC/Unboxing/Tutorial/TV-Ad)
**Когда:** реклама/обзор продукта с «человеком».
```bash
# Marketing Studio (их движок) напрямую:
"$HF" marketing-studio products fetch --url <shop-url> --wait        # импорт товара
"$HF" marketing-studio avatars list --json                          # выбрать аватар
printf '[{"id":"<avatar>","type":"preset"}]' > /tmp/a.json ; printf '["<product>"]' > /tmp/p.json
"$HF" generate create marketing_studio_video --avatars @/tmp/a.json --product_ids @/tmp/p.json \
  --mode ugc_unboxing --duration 15 --aspect_ratio 9:16 --wait
# Альтернатива (наш контроль): Soul-аватар пользователя (HeyGen) + i2v продукта Seedance + наш монтаж.
```

## ФЛОУ 4 — Quick i2v (их Video/Image Generator) — оживить кадр
**Когда:** есть картинка, надо движение; обход затыка Runway.
```bash
"$HF" generate create seedance_2_0 --prompt "<motion + camera по §B>" --start-image img.png \
  --duration 5 --aspect_ratio 9:16 --resolution 720p --wait
# виральность готового: "$HF" generate create brain_activity --video final.mp4 --wait
```

---

## Что взять в video-generation skill (апгрейд)
- §A LOCK → в Phase 3 (Visual style lock) — расширить нашу «film vocabulary» полной LOCK-системой.
- §C2 storyboard-sheet-first → дешёвый ревью раскадровки одним изображением ДО генерации видео.
- §B MDCM + banned-list → в `director-rules.md` (анти-клише движения).
- §C1/§C3 prompt-схемы → шаблоны промптов для Seedance/Veo.
- Procedural BGM (`video-editor/references/procedural-bgm.md`) → бесплатная подложка под превью.
