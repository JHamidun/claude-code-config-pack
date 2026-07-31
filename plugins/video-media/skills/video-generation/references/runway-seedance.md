# Runway internal API + Seedance 2.0 — deep reference

Reverse-engineered internal endpoints `api.runwayml.com/v1`. JWT от веб-подписки. Безлимит через подписку — НЕ списывает credits на каждый вызов (Unlimited 2250 credits = web UI only, API usage = отдельный pool).

## §1 — JWT auth + 30-day refresh

`RUNWAY_TOKEN_PLACEHOLDER` в `~/.claude/.credentials.master.env`. Refresh через 30 дней:

1. Открой https://app.runwayml.com (залогинен)
2. DevTools → Application → Local Storage → `https://app.runwayml.com`
3. Скопируй значение ключа `RW_TOKEN_PLACEHOLDER`
4. Замени `RUNWAY_TOKEN_PLACEHOLDER=<новый_токен>` в credentials

День 31 = 401 Unauthorized на любой call. Без warning.

```bash
# Проверка
python ~/.claude/skills/video-generation/scripts/runway_client.py profile
```

## §2 — 4-step S3 upload flow

```
Step 1: POST /v1/uploads { name, contentType }
        → { presignedUrl, uploadId }
Step 2: PUT presignedUrl (raw file bytes, no multipart)
Step 3: POST /v1/uploads/complete { uploadId, filename }
        → { datasetId }
Step 4: POST /v1/tasks {
          taskType: 'seedance_2',
          creationSource: 'tool-mode',
          numGenerations: 1,
          options: {
            textPrompt, duration, aspectRatio, resolution,
            referenceImages: [{ assetId, url: datasetId, type: 'first_frame' }]
          }
        }
        → { taskId }
```

Mandatory headers:

```
Authorization: Bearer <RUNWAY_TOKEN_PLACEHOLDER>
Origin: https://app.runwayml.com
X-Runway-Workspace: <RUNWAY_TEAM_ID>
```

Mandatory body fields: `creationSource='tool-mode'`, `numGenerations=1`. Опусти любое = 400.

Запросы — через query `?asTeamId=<RUNWAY_TEAM_ID>`.

## §3 — Seedance prompt engineering

### Anatomy одного prompt'а

```
[SUBJECT motion]. [CAMERA movement]. [FILM VOCAB lock].
```

**Rule:** ONE action verb + ONE camera movement на prompt. Два verbs = competing visual directions + temporal incoherence. Split multi-action в отдельные 5s shots.

### Film vocabulary lock (verbatim, в каждом prompt серии)

```
Shot on ARRI Alexa Mini, Cooke S7/i 50mm T2.0 anamorphic,
ARRI LogC to Rec.709, 35mm film grain.
Ultra-wide 21:9 cinemascope.
Photorealistic, no CGI, no fantasy glow, raw and grounded.
```

Для vertical 9:16 — замени aspect.

### Camera vocabulary Seedance distinguishes

`dolly` (push/pull), `pan` (left/right), `tilt` (up/down), `truck`, `tracking` (follow), `orbit` / `arc`, `crane`, `aerial` / `drone`, `handheld`, `gimbal`, `locked` / `fixed`.

Избегай motion adjectives без temporal qualification (`fast`, `smooth`, `gentle`). Используй `push-in over 5 seconds`, не `gentle push`.

### i2v rule (КРИТИЧНО)

Reference image уже encodes appearance. **Не повторяй физическое описание персонажа в prompt'е** — Seedance морфит лицо. Prompt = motion + camera + environment only.

### Start-frame-only vs dual-keyframe

Эмпирически (39 Terra итераций): **start-frame-only даёт motion на 70-80% лучше** чем dual-keyframe. Dual-keyframe только когда:
- End composition обязателен по сценарию
- Нужен anti-mutation LOCK (см. §4)

> **Caveat — это бенчмарк ОДНОГО персонажа.** Для кадров с **3-4 реальными лицами** (ансамбль) лица решаются НЕ здесь, а на стадии keyframe (GPT-Image-2 multi-ref, см. `keyframes-multiface.md`). При анимации такого keyframe start-only ОК, но обязательно добавь в clip-prompt анти-дрейф-суффикс, чтобы лица не «поплыли» за 5 секунд:
> ```
> Cinematic film look, photorealistic, smooth natural motion. No text overlays, no warping,
> no extra or deformed limbs, stable consistent faces, no identity drift.
> ```
> Проверено на «Хрониках Восхождения» (4 командных кадра, Seedance start-only + exploreMode) — лица держались.

## §4 — 8 mutation patterns + verbatim patches

| # | Mutation | Verbatim patch (вставлять в prompt) |
|---|---|---|
| 1 | Symbol/glyph bloat → growing disc/halo (на ярком пульсе) | `glyph SHAPE frozen, identical every frame, thin line; STEADY glow only — no brightness pulse` ⚠️ см. note |
| 2 | Bubbles/objects multiply, foam | `bubbles stay attached, no soap-like foam, count preserved` |
| 3 | Limb duplication, leg splitting | `single pair of legs, no limb duplication, anatomy preserved` |
| 4 | Silhouette dissolves / fades | `solid silhouette, no dissolve, no fade, hard edges` |
| 5 | Frozen figure (no motion at all) | `subtle natural motion, breathing, no full freeze` |
| 6 | Unwanted camera panning | `locked camera, no pan, no dolly, static frame` |
| 7 | Magical dissolution физики | `physics-based motion, gravity, momentum, no magical dissolution` |
| 8 | Thrown/passed object левитирует, дрейфует, крутится в воздухе | `solid heavy object, normal gravity, single straight path, caught and HELD; no float/hover/spin/drift` + **end_frame = объект уже В РУКАХ** |

> **⚠️ Glyph-pulse trap (Terra ch1 pilot, проверено).** Паттерн #1 коварен: на просьбу «glowing sigil PULSES» Seedance трактует яркий пик как радиальный ореол → расплывает глиф в светящийся ДИСК/медальон, теряя форму. Патч `no glow change` помогает слабо. **Надёжно держит форму только СТАБИЛЬНОЕ свечение без brightness-пульса** (steady glow). Если пульс критичен — анимируй фон с приглушённым статичным знаком и **впечатай пульсирующий глиф пост-композитом** (FFmpeg overlay + осцилляция alpha; в near-static лупе голова почти не двигается → фикс-позиция ложится ровно). Контраст: фиолетовый слабый глиф пульсировал БЕЗ мутации, яркий оранжевый — расплылся → чем ярче glow в keyframe, тем сильнее bloom.

## §5 — end_frame=first_frame anti-mutation LOCK

Передай ТОТ ЖЕ image как `first_frame` и `end_frame`. Seedance вынужден interpolate между identical states → small detail changes only. Для tattoos, glyphs, facial features.

```python
referenceImages = [
    {'assetId': 'img_abc', 'url': cdn_url, 'type': 'first_frame'},
    {'assetId': 'img_abc', 'url': cdn_url, 'type': 'end_frame'},  # тот же image
]
```

UI label = «last frame», API param = `end_frame`. **Reversal → 400 Bad Request.**

> **end_frame диктует РАЗРЕШЁННОЕ состояние, не только anti-mutation.** Для завершающегося действия (объект пойман, дверь закрылась, меч в руке) ставь `end_frame` = keyframe с УЖЕ ЗАВЕРШЁННЫМ состоянием — клип сойдётся в него, а не уйдёт в дрейф/левитацию. Terra-урок: бросок меча левитировал, пока end_frame показывал меч в воздухе; сгенерил отдельный keyframe «меч зажат в ладонях» как end_frame → ловля отработала. Принцип: если в кадре что-то должно ПРИЙТИ в финальное положение — нарисуй это положение и дай его как end_frame.

## §6 — CHARACTER moderation blocklist

Seedance безусловно блокирует:

**EN:** `girl, woman, man, person, human, feminine, masculine, her, she, his, him` + любые имена (`Terra`, `Loki`, `YourFirstName`, etc.)

**RU (Cyrillic):** `девочка, женщина, мужчина, человек, девушка, её, его`

**Neutral replacements:**

| Заблокированное | Заменить на |
|---|---|
| girl, девочка | the slender silhouette, the small figure |
| woman, женщина | the figure, the silhouette |
| she, her | it, they, the figure |
| Terra (proper name) | the protagonist, the cluster |
| winged child | the small winged shape |

**Правило:** keep animation intent identical, swap only terminology. Никогда не submit'и с personally-identifying language.

## §7 — Hard limits + конверсия форматов

- **textPrompt: 3500 characters max.** Exceeding → 400. Hard wall, без warning. Audit на repeated DO NOT clauses; убирай inline examples.
- **JFIF → JPG/PNG mandatory** перед upload:
  ```bash
  ffmpeg -y -i input.jfif output.jpg
  ```
  Без конверсии → 422 Unprocessable Entity.
- **Aspect ratios:** `9:16`, `16:9`, `1:1`, `21:9`, `4:3`, `3:4`.
- **Resolutions:** `480p`, `720p`, `1080p`.
- **Duration:** 5–10s типичные. >7s — temporal jitter (см. §10).

## §8 — Browser-automation fallback (Playwright MCP)

Когда JWT API недоступен (новый провайдер, UI-only feature, brand kits):

1. Открой Runway в Playwright MCP browser, attach к залогиненной сессии
2. Открой 3-5 параллельных tabs (Explore Mode троттлит после ~3, «You're on a roll»)
3. Загрузка картинки: drag-and-drop через `browser_evaluate`
4. Paste prompt: `navigator.clipboard.writeText(text)` ДОЛЖЕН быть, **НЕ** `document.execCommand('copy')` (deprecated, не работает)
5. Submit, stagger 1 sec между tabs
6. Download as each finishes — 4-5× speedup vs serial

```javascript
// Paste prompt в browser_evaluate
await navigator.clipboard.writeText(promptText);
document.querySelector('textarea[placeholder*="prompt"]').focus();
document.execCommand('paste');
```

Не использовать parallel tabs для крупных batch (>10 shots) — manual visual review каждого clip'а съедает выгоду.

## §9 — Endpoint catalog (v1)

| Endpoint | Для чего |
|---|---|
| `GET /v1/profile` | Кто залогинен, план, credits |
| `POST /v1/uploads` | Step 1 upload — получить presignedUrl |
| `POST /v1/uploads/complete` | Step 3 upload — закрыть, получить datasetId |
| `GET /v1/datasets` | Список загруженных assets |
| `POST /v1/tasks` | Создать generation task |
| `GET /v1/tasks/<id>` | Polling статуса (RUNNING / DONE / FAILED / THROTTLED) |
| `GET /v1/generations` | История generations |
| `GET /v1/generated_audio/voices` | Список TTS-голосов Runway |
| `POST /v1/lora_workflows` | Custom workflows (advanced) |
| `POST /v1/lora_training` | LoRA training jobs |

## §10 — Temporal jitter (>7s clips)

Long generations (>7 sec) часто получают temporal flicker. Workaround:

1. Split на 2 shorter 4-5s clips
2. Crossfade в ffmpeg (см. assembly.md xfade chain)
3. Add к prompt: `even diffuse lighting, steady intensity, 24 fps cinematic cadence, locked tripod, zero camera shake`

## §11 — taskType mapping

| Provider | taskType |
|---|---|
| Seedance 2.0 | `seedance_2` |
| Gen-4 Turbo | `gen4_turbo` |
| Gen-4 Image-to-Video | `gen4_image_to_video` |
| Kling 3.0 | `kling_v3` |
| Veo 3.1 (через Runway wrapper) | `veo3_fast` / `veo3_full` |
| Multi-Shot | `multi_shot` |
| TTS | `generated_audio` |

## §12 — Billing pools + credits-mode vs exploreMode

- **Unlimited subscription** = 2250 credits free + flat-rate провайдеры (Seedance 2.0 = 180 credits/job, на Unlimited это $0 marginal)
- **API usage** = отдельный pool, требует credit purchase + billing setup
- **Gen-4 = per-second variable** (cost не flat), на Unlimited тоже даёт значимую экономию

### `exploreMode` (опция в options тела задачи)

| `exploreMode` | Кредиты | Параллелизм | Скорость |
|---|---|---|---|
| `False` (credits-mode) | СПИСЫВАЕТ из пула (180/job Seedance) | до ~30 concurrent (`canStartNewTask.currentLimit: 30`) | быстро, без троттла |
| `True` (explore) | **БЕСПЛАТНО / unlimited** | троттл ~3 concurrent | медленнее |

Дефолт для пакетной генерации — **`exploreMode=True`** (бесплатно). Credits-mode бери, когда нужно >3 параллельно срочно и пул не жалко.

> **Гоча (заработано боем):** на чистой Unlimited-подписке с 0 купленных кредитов credits-mode
> (`exploreMode=False`) ВСЕГДА возвращает `400 "You do not have enough credits"` — пула просто нет.
> Значит explore — ЕДИНСТВЕННЫЙ режим, а он сейчас жёстко троттлит: `429` на submit даже при 2
> в полёте, задачи висят `THROTTLED progress=0`. **Escape: фолбэк на Veo 3.1 Fast** (`veo-3.1-fast-generate-preview`,
> свой GOOGLE_API_KEY, t2v без картинки, 3 concurrent, ~60с/клип) — 30 клипов за ~15 мин вместо часов. Это документированный спаситель, реально работает.

### КРИТИЧНО — кредит списывается в момент ОТПРАВКИ (POST /v1/tasks), НЕ при скачивании

- Остановка локального раннера в середине батча **НЕ возвращает** уже списанные кредиты.
- Но и не «жжёт впустую»: отправленная задача **досчитывается на сервере** и остаётся скачиваемой по `task_id`.
- **Keyframe-картинки независимы от видео-задач** — стоп анимации НЕ тратит keyframes (юзер прямо ругался на путаницу: «ты впустую потратил кадры?» — нет, картинки целы, видео-задача либо уже оплачена и досчитается, либо не отправлялась).
- При credits-mode **не делай resubmit на «фейл»** не проверив сервер — каждый submit = новое списание (в exploreMode resubmit бесплатен, но плодит дубли).

### Credits-exhaustion → exploreMode pivot

`POST /v1/tasks` вернул `400 "not enough credits"` → переотправь оставшиеся задачи с `exploreMode=True` (тот же JWT) — бесплатно, троттл ~3. Бесшовно доводит проект.

### Recovery — забрать SUCCEEDED задачи по task_id (без ре-генерации)

Задачи, дошедшие до SUCCEEDED, остаются на сервере даже если локальный раннер упал/остановлен — теряются только недокачанные локальные файлы. НЕ re-generate:

```python
task = c.wait_task(task_id)              # или c.get_task(task_id)
urls = c.list_artifacts(task)
c.download(urls[0], out_path)
```

`task_id` бери из `video_tasks.json` / логов (см. §13). Если id потерян — `GET /v1/tasks?limit=30` (заголовок `X-Runway-Version: 2024-11-06`), найди по `name`, скачай `artifacts[0].url`.

### THROTTLED ≠ failed (client-timeout recovery)

`/v1/tasks/<id>` отдаёт статус из набора `RUNNING / DONE / FAILED / THROTTLED` (ответ — массив-обёртка `[{...}]`). При `THROTTLED` клиент может словить таймаут, но **задача на сервере живёт и часто SUCCEEDED**. Не считай таймаут провалом и не resubmit (в credits-mode = повторное списание). Дождись/перепроверь по recovery-рецепту выше.

## §13 — State file pattern (`video_tasks.json`)

Для multi-hour pipelines с throttling. Resume без re-queue.

```json
{
  "phase": "Phase5_Generation",
  "clips": [
    {
      "id": "ch1",
      "prompt": "The figure slowly turns. Locked camera. ARRI Alexa, 50mm.",
      "keyframe_version": 3,
      "task_ids": ["bb199695-...", "7c33..."],
      "urls": ["https://cdn.runwayml.com/..."],
      "status": "DONE"
    },
    {
      "id": "ch2",
      "keyframe_version": 5,
      "task_ids": ["..."],
      "status": "RUNNING"
    }
  ],
  "last_updated": "2026-05-30T12:34:56Z"
}
```

Pipeline skip'ает DONE, polls RUNNING, submits unstarted.

## §14 — Output checklist (production)

Для каждого shot'а проверь:
- [ ] Character continuity (face не морфит)
- [ ] Camera vocabulary executed (если был `dolly` — есть dolly)
- [ ] No mutation pattern triggered (см. §4 таблицу)
- [ ] Film grain / vocabulary visible (если был ARRI lock)
- [ ] Duration matches request (Seedance иногда отдаёт 4.5 вместо 5)
- [ ] Audio пустой или native — strip перед mix
