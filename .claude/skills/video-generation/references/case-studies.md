# Production case studies

Реальные пайплайны, точные конфиги, реальные таймлайны. Используй как baseline для оценки новых проектов.

## Case 1 — Terra book trailer (Example Publisher, май 2026)

**Бриф:** 4 «живые обложки» для книги «Example Book Title» Example Author, 9:16, по 5 секунд каждая. Стейкхолдер — [Stakeholder] <contact@company.ru>.

### Конфиг

| Параметр | Значение |
|---|---|
| Aspect ratio | 9:16 vertical |
| Длительность | 4 × 5s = 20s total |
| Keyframe source | gpt-image-2-2026-04-21 (колоризация ЧБ обложек) |
| Video provider | Seedance 2.0 через Runway JWT |
| Keyframe strategy | `end_frame=first_frame` LOCK для глифов и persistence лица |
| Iterations | 39 Seedance generations + 27 keyframe versions (ch4 reached v19) |
| Wall-clock | ~14 hours active |
| Cost | $0 marginal (Runway Unlimited) |
| Delivery | Yandex Disk public folder + Outlook draft стейкхолдеру |

### Pipeline

```
1. Получили 4 ЧБ обложки (1 на главу) от Example Publisher
2. gpt-image-2 prompt: 'Colorize this children book cover in lush watercolor palette, preserve composition, no added elements'
3. Nano Banana Pro variations: 4 alt keyframe per chapter (lock film vocab)
4. Lock film vocabulary verbatim:
   'Watercolor children illustration aesthetic, soft ambient lighting,
    locked tripod composition, 35mm cinematic feel, no CGI, gentle natural motion'
5. Seedance JWT, end_frame=first_frame LOCK (anti-mutation на mystical glyphs)
6. Iteration loop per chapter:
   - Review motion (search 7 mutation patterns в `references/runway-seedance.md`)
   - Patch prompt из mutation table
   - Re-submit
   - Если character morph — re-anchor к v0 keyframe
7. Yandex Disk: создал folder `/terra-final/`, raw PUT (НЕ multipart), public link once
8. Outlook draft → Drafts (НЕ Send): ссылки + ТЗ + ask на feedback
```

### Грабли (учтены в SKILL.md)

- Seedance мутировал глифы → fix через end_frame=first_frame LOCK
- Cyrillic путь `видео Анимация/` ломал Yandex — пересоздал ASCII `terra-final/`
- Multipart Yandex дал 0-byte file → raw PUT
- Один keyframe (Глава 4) потребовал v19 итераций — другие хватило v3-v5

### Локальная структура

```
./work/<project>/            # напр. ./work/terra-final/
├── keyframes/
│   ├── ch1_v0_grey.jpg            # оригинал ЧБ
│   ├── ch1_v1_color.png           # gpt-image-2 colorization
│   ├── ch1_v3_final.png           # Nano Banana Pro final
│   └── ...
├── videos/
│   ├── ch1_final.mp4
│   └── ...
├── _runway_archive/                # все task_id + FAILED + rejected
├── _backup_v1/, _backup_v2/        # snapshot перед re-animate
├── Не одобренные варианты генерации/  # human-curated reject pile
└── video_tasks_v3.json             # state machine
```

## Case 2 — Amber cinematic trailer (Chronicles of Amber, 2026)

**Бриф:** 12-scene cinematic trailer 21:9 cinemascope по серии книг Желязны.

### Конфиг

| Параметр | Значение |
|---|---|
| Aspect ratio | 21:9 ultra-wide |
| Длительность | 55 sec total (12 scenes × ~4.5s) |
| Keyframe source | Nano Banana Pro 21:9 native |
| Video provider | Seedance 2.0 через Runway browser UI (до JWT API) |
| Parallel strategy | 4 concurrent VSCode instances, каждый держит tab Runway |
| Wall-clock | ~6 hours active |
| Cost | $0 (Runway Unlimited) |

### Pipeline

```
1. Lock character: первый успешный generation Corwin → save crop как reference image
2. Reference image используется в ВСЕХ subsequent generations (single-ref mode)
3. Storyboard 12 shots, ONE action + ONE camera per shot:
   - quiet acceleration shock climax quiet (energy pacing)
4. Nano Banana Pro 21:9 native (GPT Image не даёт >3:2 без crop-loss)
5. Reference-chaining: output→ref→next, re-anchor каждые 3 шага к original
6. 4 параллельных VSCode instances, каждый дёргает Runway UI вручную
   (subjective quality review каждого clip'а — automation там фейлится)
7. ElevenLabs Music: 2×30s сегментов с handoff prompt
   'Continues from dark mystery into battle'
8. XFade chain 12 clips, sidechain ducking under VO
9. 3-tier compression: archive 4K + presentation 2.5K + social 1080p
```

### Урок для будущих проектов

До JWT API browser-tabs strategy был оптимален. Сейчас 90% случаев лучше JWT (`runway_client.py`) + asyncio.gather. Browser-tabs остаётся valuable для UI-only workflows (brand kits, новые провайдеры без API, ручная quality review).

## Case 3 — ConferenceX announcement (30s social, май 2026)

**Бриф:** 30s announcement video для конференции ConferenceX в Telegram + LinkedIn.

### Конфиг

| Параметр | Значение |
|---|---|
| Format | 9:16 1080p |
| Длительность | 30s |
| Avatar | HeyGen Avatar V, свой аватар |
| Captions | SubMagic EN-only с **обязательной trigger-word чисткой** |
| Cost | ~$2 (Avatar V $0.0667 × 30s = $2) |
| Wall-clock | ~45 min |

### HeyGen Avatar V config (пресет под вертикальный шортс)

```python
import os
avatar_id = os.environ['HEYGEN_AVATAR_ID']   # свой аватар, look_id
voice_id  = os.environ['HEYGEN_VOICE_ID']    # свой голос HeyGen
engine = 'avatar_v'
aspect_ratio = '9:16'
resolution = '1080p'
# Cost: $0.0667/sec
```

Аватары и голоса — ТВОИ: пак не поставляется ни с какими. Свои id берутся в
кабинете HeyGen (https://app.heygen.com/avatars и `/voices`) либо запросами
`GET /v3/avatars/looks?group_id=<group>` и `GET /v3/voices`; кладутся в
`HEYGEN_AVATAR_ID` / `HEYGEN_VOICE_ID` в `~/.claude/.credentials.master.env`.
Полный разбор запроса — `skills/heygen/SKILL.md`.

### Pitfall — «пайвот» → 🍺

SubMagic трансформирует «пайвот» (pivot, бизнес-разворот) в beer emoji 🍺. Pre-TTS чистка ОБЯЗАТЕЛЬНА:

```bash
python ~/.claude/skills/shorts-pipeline-user/scripts/trigger_word_check.py script.txt
```

17 RU-триггеров. Замены в скрипте: «разворот концепции», «ротация», «трансформация».

## Case 5 — Corporate tribute «видео-трибьют руководителю»

**Бриф:** запоминающееся корпоративное видео-поздравление руководителю компании-клиента от команды. Эпик с реальным лицом героя + 9 лиц команды.

**Сюжет:** капитан ведёт корабль сквозь шторм → секретный остров → восхождение на гору → пещера-библиотека → знание возвращается в мир. Герой ролика = капитан, заказчик = со-капитан в ансамбле. Плюс одна внутренняя пасхалка команды (узнаваемый предмет как «реликвия» в одной из сцен).

### Конфиг

| Параметр | Значение |
|---|---|
| Aspect / длит. | 21:9 cinemascope, ~60s (12 сцен ×5s + титр) |
| Keyframes (1 лицо) | Nano Banana Pro `gemini-3-pro-image-preview` + reference-фото |
| **Keyframes (3-4 лица)** | **GPT-Image-2 `gpt-image-2-2026-04-21`** через `/v1/images/edits` multi-ref (см. `keyframes-multiface.md`) |
| Video | Runway Seedance 2.0, **start-only, exploreMode=True** (бесплатно), 5s, 720p, anti-drift суффикс |
| Голос | ElevenLabs **George** `JBFqnCBsd6RMkjVDRZzb`, RU, `eleven_multilingual_v2` (0.35/0.85/0.35) |
| Музыка | **Suno** (Pro-аккаунт), оркестровый инструментал, климакс-нарезка 62s |
| Сборка | ffmpeg: xfade 0.4 + per-line VO `adelay` поверх музыки (vol 2.8/0.42) + `loudnorm I=-14` + PIL-титр |
| Экспорт | `TRIBUTE_master.mp4` (4K) + `TRIBUTE_1080p.mp4` (lanczos upscale) |
| Cost | $0 (Runway exploreMode + ElevenLabs/Suno подписки) |

### Что было трудно и как решилось (ядро уроков)

1. **Лица команды.** Главная боль. Nano держит 1-2 лица, на 3-4 даёт «похожих незнакомцев» — заказчик людей не узнаёт. Решение: командные кадры переделали в **GPT-Image-2 multi-ref** (`image[]` multipart), 3 варианта/сцена, человек выбрал. Подробно → `keyframes-multiface.md`.
2. **«Постановочное фото».** GPT-Image-2 держит лица, но строит групповое фото в камеру → лечится киношным суффиксом (`candid film still, mid-action, NOT looking at camera, ARRI/Deakins`).
3. **Hero/ensemble баланс.** Заказчик хочет быть заметным, но не единственным — команда тоже должна занимать внимание. Формулировать «hero most prominent, team also prominent as ensemble», не «выделить одного».
4. **Кредиты Runway.** Сначала credits-mode исчерпал пул → переключили на `exploreMode=True` (бесплатно). Урок: кредит списывается при **отправке**, не скачивании; стоп раннера не «жжёт кадры»; keyframe-картинки независимы от видео-задач; SUCCEEDED-задачи добираются по `task_id`. (Юзер дважды ругался — см. `runway-seedance.md` §12.)
5. **НЕ глушить чужие задачи.** Никогда не останавливать идущую генерацию без спроса — владелец задач воспринимает это как порчу его работы.
6. **Музыка vs песня.** Сначала думали Suno-песню со словами → заказчику сгенерированный текст не понравился, выбрали инструментал + закадровый голос. Длинный Suno-трек обрезали по климаксу (`analyze_cut.py`).
7. **RU-ударение в TTS.** `што́рма` — combining acute U+0301 в тексте; правка `vo_11` на «все до единого». Грабли: print строки с диакритикой упал на cp1251 (см. `windows.md`).

### Локальная структура

```
./work/<project>/                     # напр. ./work/tribute/
├── SCENARIO.md                       # раскадровка 12 сцен + титр
├── refs/                             # client_main.jpg, user_hero.jpg, team_*.jpg (10 лиц)
├── keyframes/final/sc01-12.png       # утверждённые (микс Nano + GPT-Image-2)
├── videos/  videos/_review/          # клипы + все варианты для выбора (НЕ удалять)
├── audio/   vo_01-12.mp3 (George) + music_suno2_cut.mp3
├── scripts/ gen_keyframes.py gen_team_gpt_cine.py animate_subset.py gen_vo.py
│            gen_music.py analyze_cut.py contact_sheet.py assemble.py cred.py
├── TRIBUTE_master.mp4  TRIBUTE_1080p.mp4
```

### Урок для будущих трибьютов

Multi-face — это **итеративный** процесс (вариации + ручное вето), не one-shot. Лица решаются на стадии keyframe (GPT-Image-2), а не анимации. Голос/музыка/текст — отдельные стадии с approval юзера; signature = «от команды», не персональная.

## Case 4 — Reference 77s vertical pipeline

Generic template для шортсов / explainer'ов:

```
T+0       Брифинг → план shot'ов
T+0:45    Keyframes (Nano Banana Pro batch 4 concurrent)
T+1:00    Параллельный fan-out:
            • Veo 3.1 Fast × 3 concurrent (15 secs of video в 1 пас)
            • ElevenLabs TTS своим клоном (77s VO)
            • ElevenLabs Music (30s × 3 sample)
T+3:00    Finish parallel
T+3:30    FFmpeg assembly: concat -c copy + amix + loudnorm + brand card
T+4:00    Final compression (Tier 3 social), upload
```

Итог: **~4 минуты wall-clock** на 77s 9:16 vertical, ~$8 Veo Fast + $0 audio (если ElevenLabs subscription).

## Project structure template (универсальный)

Для любого multi-shot проекта:

```
project_name/
├── keyframes/
│   ├── <shot>_v0_<source>.jpg
│   ├── <shot>_v1_<modification>.png
│   └── ...
├── videos/
│   ├── <shot>_<version>.mp4
│   └── final.mp4
├── audio/
│   ├── vo_<shot>.mp3
│   ├── music_<segment>.wav
│   └── final_mix.wav
├── scripts/
│   ├── 01_keyframes.py
│   ├── 02_generate.py
│   ├── 03_assemble.sh
│   └── upload.py
├── _runway_archive/                  # все task_id + FAILED для diff
├── _backup_v1/, _backup_v2/         # snapshot перед re-animate
├── _rejected_variants/              # human-curated reject pile (ASCII path!)
└── video_tasks.json                 # state machine для resume
```

### `video_tasks.json` schema

```json
{
  "phase": "Phase5_Generation",
  "clips": [
    {
      "id": "ch1",
      "prompt": "...",
      "keyframe_version": 3,
      "task_ids": ["bb199695-..."],
      "urls": ["https://cdn.runwayml.com/..."],
      "status": "DONE"
    }
  ],
  "last_updated": "2026-05-30T12:34:56Z"
}
```

Script resume: skip DONE, poll RUNNING, submit unstarted. Спасает на pipelines с throttling до 30+ минут.

## Delivery patterns

### Publish-once Yandex Disk

Создай folder ОДИН раз, public link статичен. Каждая новая итерация автоматически появляется в folder'е. Стейкхолдеру ссылка не меняется (10-40 revisions).

### Outlook draft (НЕ send)

Draft в Outlook с:
- ТЗ что в видео
- ссылка на Yandex Disk
- explicit ask на feedback (что именно проверить)

Сохрани в Drafts, не send. Стейкхолдер reply'ит в email thread.

Пример для Terra: draft [Stakeholder] `<contact@company.ru>` с 4 ссылками + блок «что хотим узнать».
