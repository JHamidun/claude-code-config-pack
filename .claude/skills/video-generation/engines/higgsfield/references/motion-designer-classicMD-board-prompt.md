# Higgsfield Motion Designer — `classicMD-board` internal system-prompt (captured verbatim 2026-06-07)

Снято observe-by-execution: Motion Designer (`classicMD-flow`) запускает под-скилл **`classicMD-board`**,
который генерит **6-панельную раскадровку (storyboard sheet)** через **GPT Image 2 (3:2, High, 2K)** перед
анимацией. Сначала step "moodboard" (4-style 2x2 board), затем этот storyboard-генератор по выбранному кадру.
Это полноценный production-промпт с LOCK-системой и плейсхолдерами — отличная база для нашего motion/storyboard.

Пайплайн: `4-style moodboard (GPT Image 2 3:2)` → `classicMD-board: 6-panel storyboard (GPT Image 2 3:2 2K)` → анимация панелей.

## Полный промпт (как выдал агент)

```
1. OPENING — Generate a designed 15s motion design storyboard sheet — 6 panel compositions BUILT FROM <moodboard> (a 4-up moodboard).

2. FOUNDATION DECLARATION — BUILD FROM the TOP-LEFT frame of <moodboard> as foundation. The picked frame IS the visual world of this storyboard. Ignore the other 3 frames.

3. GRID LAYOUT — 6 panels in 3×2 grid — 3 cols × 2 rows HORIZONTAL. TOP ROW: 01,02,03. BOTTOM ROW: 04,05,06. Sheet aspect 3:2 horizontal. Background matches picked frame: deep near-black void + soft vignette + faint speckle/noise. Thin 1pt hairline gutters, 12-20px gap. NO panel borders.

4. MIN-TEXT RULE (HR-2) — Any in-panel text ≥10-12% panel height cap-height. Latin sub-labels, tracked monospace dates, location tags, faux-data chips STRIPPED. Headlines + brand wordmarks at full scale only.

5. REALISM BAN (HR-3) — Photoreal humans / documentary / ARRI Alexa / 35mm grain / real-skin pores = BANNED. Use silhouettes / abstract human forms / stylized 3D / illustrated 2D / motion-trace / particle figures / lit volumetric silhouettes. Motion design is DESIGN, not photography.

6. TEXT-ANCHOR MANDATE — Pattern A {01,03,05} = text panels. Punch-lines (2-4 words) fitting foundation world:
   01 (invitation/setup), 03 (verb/action), 05 (revelation/mid-state). Typography: bold modern geometric sans (condensed ok), high-contrast white with subtle cyan/magenta edge glow within foundation lighting; no subtext.

7. VISUAL-CONCEPT ARC (Visual World Lock):
   SUBJECT LOCK — single hero entity across all 6 panels.
   MATERIAL LOCK — consistent material (e.g. refractive liquid-chrome/glass + neon caustics).
   STYLE LOCK — premium sculpted 3D motion render on dark void; controlled bloom, crisp spec, negative space.
   PALETTE LOCK — 3 dominant colors sampled from picked frame (e.g. #07080B void, #22C8FF cyan, #B53CFF magenta).
   ATMOSPHERE LOCK — futuristic, quiet-power, sleek, luminous, digital-organic.

8. SCENE VARIATION MANDATE — Subject LOCK ≠ Same-Scene LOCK. 6 DIFFERENT moments/scales/angles within the world. ≥3 distinct framings from {extreme macro / close detail / medium / wide / vista / aerial}. Each panel = NEW scene context.

9. MASTER CAMERA DOCTRINE (MDCM = internal choreography primary) — Camera HOLDS on 4-5/6 panels; motion from elements within frame (subject breathes/shifts/pulses, typographic mass shifts, material transforms). Optional slow micro-drift (1-3cm dolly+parallax) on ≤2 panels. BANNED: hyperkinetic chaos, vertigo pull, whip-pan smear, drop-dive past, crash-out reveal, shatter push-through, speed ramps+stutter. Panel transitions = VFX match-cut morphs (dramatic object morph / halftone morph / ink flow / dramatic unfurl / light sweep / chrome dust disperse).

10. CHROME TIER (b) PANEL-CAPTIONS — Panel labels below thumbnails with timecodes in small monospace ("01  0:00-0:01"). Top header: "5s MOTION STORYBOARD" left + "<PROJECT> · <THEME>" right. Bottom: "TONE: ...  ·  STYLE: ...".

11. PHOTOGRAPHIC FRAME PURITY (Rule 10) — Each panel contains ONLY: (a) scene composition, (b) punch-line typography per chess pattern, (c) brand wordmark on P06 if brand_mode=brand. NO document-metadata chips (CHAPTER/JOURNAL/SECTOR/EDITION/version/date stamps). Sheet-level metadata in chrome margins OUTSIDE frames.

12. PANEL CONTENT — per-panel breakdown (5s total, 6 beats). Each panel = schema:
   CONTENT / NARRATIVE BEAT (hook→develop→escalate→sustain→build→resolve) / INTERNAL CHOREOGRAPHY (% scale-breath, Hz, caustic drift, droplet motion) / TEXT / LIGHT (TYPE + DIRECTION + DOES) / EFFECTS (bloom, DOF, chromatic aberration micro, light sweep, chrome-dust) / PARALLAX.
   (Panels 01-06 with exact timecodes 0:00-0:01 ... 0:04.5-0:05, hook on P01, brand wordmark on P06.)

13. LOGO ASSET HANDLING — if logo_source=="none": skip, don't reference logo image.

14. PANEL 06 CLOSER ROUTE — brand_mode=="brand" + no logo: Route 1 ATMOSPHERIC INTEGRATED CLOSER. Brand wordmark = clean typography 15-22% panel height, integrated in closing scene. brand_tagline null → no tagline.

15. LOCKS RECAP — PALETTE / STYLE / SUBJECT / MATERIAL / ATMOSPHERE locks restated.

"Direct like a motion design genius — concept arc TRANSFORMS across 6 panels (hook→develop→reveal) WITHIN the foundation world. NOT 6 disconnected decorations."
```

## Что забрать к нам
- **LOCK-система** (SUBJECT/MATERIAL/STYLE/PALETTE/ATMOSPHERE) для консистентности серии кадров — в наш video-generation Phase 3.
- **Storyboard-sheet first**: генерить 6-панельный лист одним изображением (GPT Image 2 3:2) ДО анимации — дёшево ревьюить раскадровку.
- **MDCM camera doctrine** (internal choreography vs camera move) + banned-list — анти-клише.
- **HR-rules** (min-text, realism-ban) + **chess-pattern** текстовых панелей {01,03,05}.
- Плейсхолдеры: `<moodboard>`, `brand_mode`, `logo_source`, `brand_tagline` — параметризация флоу.

Параллельно у Motion Designer step-0 = **4-style moodboard** (см. supercomputer-architecture.md §7c / EMPLOYEES_CAPTURE.md).
