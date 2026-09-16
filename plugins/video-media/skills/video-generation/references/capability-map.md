# Карта возможностей и связи с соседними навыками

Полный разбор трёх уровней вызова (весь пайплайн / отдельный флоу / отдельный атом), список структурных флоу движка Higgsfield и таблица «какой соседний навык за что отвечает». Читай, когда решаешь, какую часть хаба задействовать или к какому навыку уйти.

## CAPABILITY MAP — что умеет скилл (вызывай ЧАСТЬ или ВЕСЬ пайплайн)

> Три уровня вызова: **(A) весь пайплайн под ключ** · **(B) отдельный флоу** · **(C) отдельный атом/инструмент**. Экономия: всё через свои API; `hf.exe` — только для эксклюзивов (D).

**(A) ВЕСЬ ПАЙПЛАЙН — одна команда** → `scripts/run.py --brief b.json [--execute]` (intake→flow→промпт→route→keyframes+clips→audio→сборка→экспорт; approval-гейт; `--dry-run` по умолчанию). См. §TURNKEY.

**(B) ФЛОУ (структурные, в `engines/higgsfield/`)** — `ENGINE.md`:
| Флоу | Что | Точка входа |
|---|---|---|
| cinematic-5 | кино-нарратив (dramaturg→…→prompt-writer), мульти-клип | `prompt_builders.py` build_cinematic_5 |
| highMD/productMD/typographyMD/infographicMD/classicMD | моушн-дизайн (SANDWICH + доктрины камеры) | `prompt_builders.py sandwich --doctrine` |
| ugc / unboxing / tutorial / try-on | слот-борды, First-Word hook | ENGINE.md §UGC |
| tv-ad / podcast / cartoon | реклама / интервью / мульт | ENGINE.md + `subagents-*.md` |

**(C) АТОМЫ (вызываются по отдельности)**:
| Атом | Команда |
|---|---|
| keyframes (свои ключи) | `scripts/nano_banana_keyframes.py shots.json --out DIR` (Nano) |
| промпт-кухня | `engines/higgsfield/scripts/prompt_builders.py {cinematic\|sandwich\|board}` |
| роутинг провайдера | `engines/higgsfield/scripts/router.py route <jst>` (direct vs hf) |
| клип i2v | `scripts/veo_image_to_video.py` (Veo) · `scripts/runway_client.py generate` (Seedance 2.5/Kling — **кредиты Runway, не $0**: 20/30/68 за секунду 480p/720p/1080p, и только на живой платной подписке; сперва `token-status` и план в `/v1/profile`) |
| озвучка / музыка | `scripts/elevenlabs_voiceover.py` · `scripts/lyria_music.py` / `elevenlabs_music.py` |
| сборка (атомы) | `engines/higgsfield/scripts/assemble.py {concat\|xfade_chain\|color_lut\|ken_burns\|burn_ass\|reframe_blurred_bg\|platform_export\|audio_duck\|whisper_srt}` |
| сборка (пайплайн VO+муз+brand) | `scripts/ffmpeg_assemble.py manifest.json --out final.mp4` |
| моушн-графика / соц-оверлеи | `scripts/motion_graphics.py` · `remotion-overlays/` |

**(D) HF-ЭКСКЛЮЗИВЫ (только `hf.exe`, через `engines/higgsfield/bin/hf.exe`)**:
| Эксклюзив | Команда |
|---|---|
| Soul face-lock (рекуррентный AI-ведущий) | `hf soul-id create --soul-2 --image <id×5>` → `generate create text2image_soul_v2 --soul-id <ref>` |
| Virality Predictor (оценка хука) | `hf generate create brain_activity --video <≤16с>` |
| Marketing Studio / DTC (реклама с аватаром+товаром) | `hf marketing-studio {avatars,products,hooks} list` → `generate create marketing_studio_video` |
| reframe (AI-outpaint видео в новый аспект) | `hf generate create reframe --aspect_ratio 16:9 --video <id>` |

**(E) СОСЕДНИЕ СКИЛЛЫ (не дублировать):** talking-head с НАСТОЯЩИМ lip-sync → **`heygen`** (Avatar V/IV, 175 langs translate, lipsync — отдельный скилл, дополняет Soul); чистый монтаж → `video-editor`; **рилс из снятого видео блогера + AI-врезки ПОВЕРХ** (creator = основа, AI поверх, не full-AI) → `video-editor` `skills/video-editor/references/talking-head-broll-reel.md`; TTS без видео → `elevenlabs`; картинка → `nano-banana-pro`.

**Rejected (2026-07-20, обоснование пересмотрено 2026-09-08 — решение прежнее):**
inference.sh `belt` CLI (github.com/inference-sh/skills, 628★) — агрегатор 40+ видео-моделей, включая Seedance/Wan/Veo. Не берём.

Изначально главным доводом было «Seedance и так есть напрямую, $0 marginal через Runway Unlimited». **Этот довод ослаб и больше не несущий:** «$0» держалось на живой платной подписке, а на 09.09.2026 `RUNWAY_JWT` просрочен с 31.07 (40 дней, все вызовы 401), и ещё 22.06.2026 подписка сваливалась на free plan, где Runway отказывал и в explore, и в stable. Прямой доступ к Seedance сейчас не работает, и делать вид, что аргумент цел, нельзя.

Что довод держит по-прежнему:
- **нулевой net-new доступ к моделям** — Veo идёт по своему `GOOGLE_API_KEY` и от Runway не зависит; Wan достаётся через скилл `replicate` (`wan-video/wan-2.2-*`); Seedance у Runway, и агрегатор его не удешевляет, а перепродаёт;
- **второй платный аккаунт** — ещё одна подписка, которая точно так же может протухнуть;
- **установщик `curl | sh`** — исполняемый код с чужого хоста без пинов.

Пересматривать имеет смысл только если владелец решит, что Runway не восстанавливаем: тогда вопрос «чем заменить Seedance» встаёт заново и агрегатор идёт в сравнение наравне с остальными. Пока это выбор владельца, а не следствие поломки токена.


## Cross-references — что где живёт

| Skill | За что отвечает | Когда дёргать |
|---|---|---|
| `nano-banana-pro` | Keyframes, 21:9 cinemascope, multi-image consistency via reference chaining | Phase 3-4 (visual style + keyframes) |
| `image-generation` | Общий гайд по prompt engineering для image gen | Fallback когда Nano Banana Pro не подходит |
| `elevenlabs` | TTS, Music, voice IDs, settings | Phase 5 audio |
| `suno` | Длинный оркестровый score / песня (headless Clerk API) | Phase 5 audio — 60s+ score или вокал |
| `heygen` | Avatar V владелец конфига talking heads | Когда нужен говорящий аватар |
| `submagic` | Платные EN-субтитры (с пиво-bug warning) | Phase 6 captions для EN-контента |
| `shorts-pipeline-владелец конфига` | Готовая обвязка Avatar V + SubMagic + RU trigger check (`skills/shorts-pipeline-владелец конфига/scripts/trigger_word_check.py`) | Перед SubMagic на RU тексте — обязательно |
| `video-editor` | Чистый монтаж готовых клипов на your-server:3124 | Если нужен external assembly service |
| `void-video` | Удаление объектов из готового видео | Post-production cleanup |
| `video-downloader` | yt-dlp скачать чужое видео | Источник для re-edit |
| `runway-api` (archived) | Старое имя — переехал сюда в `scripts/runway_client.py` | — |
| `seedance-runway` (archived) | Browser-automation fallback → `references/runway-seedance.md` §8 | UI-only providers |
| `video-generation` (archived) | Старый монолитный хаб → разбит на этот SKILL.md + references/ | — |
| **`engines/higgsfield/`** (встроенный движок) | Реверс Supercomputer Higgsfield + локальная реплика: структурные флоу (cinematic-5/MD/UGC/TV-ad/podcast/cartoon), промпт-кухня, model-router (direct-first), HF-эксклюзивы (Soul/Marketing/Virality) через bundled hf.exe | Ветки 2-3 ROUTING-MAP — структурный флоу или эксклюзив |

