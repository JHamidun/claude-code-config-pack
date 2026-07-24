# MD-clip sub-agents — Seedance prompt templates (highMD/productMD/typographyMD/infographicMD-clip)

Финальные Seedance-промпт-райтеры моушн-флоу. **Универсальный 4-слойный SANDWICH-шаблон `prompt_text`** (единый
английский абзац), с доктрин-специфичными блоками. Это эталон промпта Seedance из раскадровки → забрать в наш video-gen.

## УНИВЕРСАЛЬНЫЙ SANDWICH (все *MD-clip)
1. **LAYER 1 (Opening, анти-grid):** `CRITICAL: Animate as ONE single continuous full-frame [aspect] cinematic film. @Image1 is a PLANNING BRIEF — translate every panel into an individual cinematic shot that occupies the complete [aspect] screen, one shot at a time. Use @Image1 ONLY as visual reference for composition/palette/identity — NEVER render the storyboard sheet itself, its chrome layer, panel borders, or grid layout as scene content.`
2. **STYLE & PALETTE/SYSTEM BLOCK** (доктрин-специфично, см. ниже) + `Palette: [HEX1],[HEX2],[HEX3]` + камера/оптика.
3. **CHOREOGRAPHY SHOTS (1..N)** — каждый кадр:
   - **LAYER 2 (Prefix):** `ENTIRE [aspect] frame fills with [shot subject + composition].`
   - `SUBJECT: [subject + action verbs] + CAMERA: [named move] + LIGHT: [setup] + PARALLAX: [FG 100% / MG 60% / BG 25%]`
   - текст-кадры: `TEXT IN FRAME: '[glyphs]' — bold kinetic typography, [position]. TEXT PERSISTENCE: remains visible throughout.`
   - стыки: `TRANSITION [time]: [named morph/whip-pan] — [source] dissolves through [particles] and reassembles as [target] over 0.4-0.6s.`
4. **LAYER 3 (Final Shot Lock)** (в последнем кадре): `THIS FINAL SHOT IS A SINGLE FULL-FRAME COMPOSITION FILLING THE ENTIRE [aspect] SCREEN. The frame surface is pure brand-reveal scene content corner to corner.`
5. **LAYER 4 (Final Reminder):** `FINAL OUTPUT REMINDER: ONE single continuous full-frame [aspect] cinematic film. Each shot is a complete fullscreen scene with [camera doctrine] and DRAMATIC MATCH-CUT TRANSITIONS between scenes.`
6. **MANDATORY TAIL FREEZE:** `13.7-15s MANDATORY SILENT TAIL PAUSE: hold final endcard composition completely silently, full brightness/saturation, camera motionless, subtle ambient room-tone drone only.`
7. **AUDIO SPECIFICS:** `Audio: ambient SFX only, no dialogue, no music (music in post). Sound cues: [per-shot timecode SFX]. SFX-only, speech absent.`
Выход: JSON (prompt_text + closing_shot + elements_used + duration, как cinematic-prompt-writer).

## highMD-clip (кинетический бренд, 6 кадров 3×2, 250-300 слов)
Style block: `High-energy, hyperkinetic brand reel. Action-tier CGI commercial register. Saturated high contrast. Shot on ARRI Alexa Mini LF, 180-degree shutter motion blur, fine 35mm grain.` Камера: **Hyperkinetic Chaos** (Vertigo Pull/Crash-out Reveal/Drop-dive Past/Whip-pan Smear). **Variety Mandate:** соседние кадры ≠ ось (X→Y→вращение→зависание→наезд). Transitions = Dramatic Particle Dissolve (хром-пыль/глитч).

## productMD-clip (премиум продукт, 9 кадров 3×3, ~600 слов)
Setup: `15-second [luxury chiaroscuro | athletic dynamic] product commercial for [BRAND]. Subject: product from @Image1, engineering-grade identity. Background: [void black #000000 | light gray #DDDDDD]. Lighting: volumetric beams + dust motes. Camera: Bot&Dolly Iris robotic arm precision.` Камера: **роборука** (Bot&Dolly snap / Programmed orbital sweep / Mechanical lift-and-rotate 45° / Vertical Y-axis crane), без тряски. Оверлеи ТОЛЬКО shots 01/08/09 (белый), 02-07 = чистая съёмка. Special Beat кадр 4.

## typographyMD-clip (шрифт-герой, 6 кадров, 250-300 слов)
Style: `Typography-driven brand reel. [2d-editorial | kinetic-3d] register. Massive 3D letterforms filling 80% of frame. Studio lighting, soft DoF.` Камера: **статика/Drift lock-on/slow glide** (движутся буквы, не камера). **TEXT REVEAL:** `letters '[copy]' bleed onto frame via [ink-bloom/brush-draw/typewriter-type/scale-punch] over 0.5s, then holds frame coordinates.` Transitions: INK FLOW / HALFTONE MORPH / DRAMATIC UNFURL (буквы слова A → буквы слова B). Каждый кадр = разные слова.

## infographicMD-clip (данные/графики)
Тот же SANDWICH; камера стабильна, Layered Reveals (оси→рост столбцов→загорается число); Data state transitions между сценами через Dramatic Object Morph (столбчатая→линейная перетеканием материала); только реальные числа (HR-5).

→ Забрать **SANDWICH-шаблон** как наш генератор Seedance-промптов из раскадровки + библиотеку camera-доктрин и transition-морфов.
