# Higgsfield: приёмы и флоу, перенесённые в наш пайплайн (заметки от 2026-06-07)

Приёмы, отмеченные при работе с Higgsfield Supercomputer через сессию своей учётной записи, и то, как они ложатся на наш пайплайн.
**Движок целиком (флоу + скрипты + реестры) теперь внутри скилла → `../engines/higgsfield/ENGINE.md`.**
Полные рецепты + команды → `../engines/higgsfield/references/flow-playbooks.md`. Здесь — краткая выжимка «что вшить в наши фазы».

## В Phase 3 (Visual style lock) — расширить до полной LOCK-системы
Вшивать в КАЖДЫЙ промпт серии (приём консистентности — cinematic-flow Soul-anchor + classicMD LOCKS):
```
SUBJECT LOCK (один герой) · MATERIAL LOCK (материал/фактура) · STYLE LOCK (рендер-язык) ·
PALETTE LOCK (3 hex из 1-го кадра) · ATMOSPHERE LOCK (3-5 слов) · CAMERA/FILM LOCK (ARRI+Leica+lens+stop для photoreal)
```

## В Phase 4 (Keyframing) — storyboard-sheet-first
Перед генерацией видео генерить **6-панельный storyboard-лист одним изображением** (GPT Image 2, 3:2, 2K) —
дёшево ревьюить раскадровку до дорогих видео-генераций. Шаблон листа (`classicMD-board`) →
`../engines/higgsfield/references/motion-designer-classicMD-board-prompt.md`. Опционально: сначала 4-стилевой moodboard 2×2.

## В director-rules — MDCM (Master Camera Doctrine, анти-клише движения)
```
Камера ДЕРЖИТ статику 4-5/6 шотов; движение ВНУТРИ кадра (субъект дышит 0.6-0.9Hz / материал трансформируется).
≤2 шота: micro-drift 1-3см dolly + parallax FG/MG/BG 100/75/50.
ЗАПРЕТ: hyperkinetic, whip-pan, vertigo pull, crash-out, shatter push-through, speed-ramp+stutter, crash zoom, slow-mo.
Переходы = match-cut морфы: LIGHT SWEEP / OBJECT MORPH / HALFTONE MORPH / INK FLOW / UNFURL / CHROME DUST DISPERSE.
```

## Prompt-схемы → шаблоны для Seedance/Veo
- **Cinematic** (`cinematic-dramaturg`): Camera→Camera Style→Light→Style&Mood→Acting(catch-lights)→Narrative→Scene Setup→Dynamic(мультишот: lens 24/35/40/75mm + скорость км/ч + "Hard Cut")→Audio→негативы.
- **Motion-clip** (`classicMD-clip`): «один непрерывный full-frame фильм, НЕ грид»; пошотно STATIC+CHOREOGRAPHY+TEXT(ABSOLUTE TEXT LOCK)+LIGHT+EFFECTS+PARALLAX + именованные TRANSITION; tail-freeze под монтаж; SFX-only; no autosubs.

## Звук
Procedural BGM чистым ffmpeg (локальная подложка под превью) → `video-editor/references/procedural-bgm.md`.
Настоящий трек → elevenlabs Music / Lyria / локальный ace-step (см. `audio.md`).

## Провайдер
Seedance доступен через bundled `engines/higgsfield/bin/hf.exe`.

**Приоритет пересмотрен 09.09.2026.** Раньше здесь стояло: «фолбэк к Runway-JWT, когда Runway в throttle (иначе всегда Runway $0)».
Это вводило в заблуждение дважды: Runway-путь сейчас закрыт не «иногда», а полностью — `RUNWAY_JWT` истёк 31.07.2026, все вызовы дают 401;
и «всегда Runway $0» перестало быть правдой ещё 22.06.2026, когда подписка свалилась на free plan и Runway отказал и в explore, и в stable.
Пока токен и план не восстановлены, **hf.exe — рабочий путь, а не фолбэк**. Восстановление Runway по порядку:
`runway_client.py token-status` (offline-проверка срока) → план в `/v1/profile` → новый токен руками из `localStorage.RW_USER_TOKEN`
на app.runwayml.com (автоматики обновления нет нигде). Как только Runway ожил — приоритет возвращается к нему, он дешевле.

Цены hf: 720p 4.5 cr/s (fast 3.5), 1080p 9 — то есть hf платный, и выбор теперь не «$0 против $0», а осознанный расход кредитов.
Какая версия Seedance стоит за hf.exe (2.0 или 2.5) — не проверено; у Runway версию с недавних пор определяет
сам `generate_seedance()` через `/v1/profile/features`.
Virality-проверка финала: `hf generate create brain_activity --video`.
