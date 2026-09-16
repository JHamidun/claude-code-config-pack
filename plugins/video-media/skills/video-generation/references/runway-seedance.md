# Runway internal API + Seedance 2.5 — deep reference

Что здесь: как ходить в `api.runwayml.com/v1` из скриптов, как устроен upload и создание задачи, промпт-инжиниринг Seedance, известные ограничения и коды ошибок.

Доступ — по JWT из сессии своей учётной записи Runway (см. §1).

> **Правка 09.09.2026: файл был написан под Seedance 2.0, вышла 2.5 (преемник, тот же ByteDance внутри Runway).** Что здесь врало и почему это было опасно:
> - заголовок и §11 подавали `seedance_2` как единственный taskType — код молча продолжал звать старую модель после выхода 2.5;
> - §7 давал длительность «5–10 s типичные» — у 2.5 диапазон 4–30 s либо Auto, то есть половина возможностей была невидима;
> - §12 считал Seedance «180 credits/job flat» — у 2.5 официальный прайс **посекундный**, и на 30-секундном 1080p ошибка в оценке бюджета кратная;
> - §1 обещал «401 без warning» — теперь warning есть (`token-status`), а вот молчаливая проблема переехала в другое место: план.
>
> Внутренний API (§2 upload flow, §9 endpoint catalog, §12 recovery, §13 state file) **не устарел** — эндпоинты, заголовки и поллинг те же.
> Снята ли 2.0 с обслуживания — **официально нигде не сказано**. Известно только, что 2.5 объявлена преемником.

## §1 — JWT auth + 30-day refresh

`RUNWAY_TOKEN_PLACEHOLDER` в `~/.claude/.credentials.master.env`. Refresh через 30 дней:

1. Открой https://app.runwayml.com (залогинен)
2. DevTools → Application → Local Storage → `https://app.runwayml.com`
3. Скопируй значение ключа `RW_TOKEN_PLACEHOLDER`
4. Замени `RUNWAY_TOKEN_PLACEHOLDER=<новый_токен>` в credentials

Автоматики обновления нет нигде: только руками через localStorage. День 31 = 401 Unauthorized на любой call.

**Warning теперь ЕСТЬ — проверка срока без сети** (раньше здесь стояло «без warning», и просрочку ловили только по 401 в середине батча):

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py token-status   # разбирает exp в самом JWT
python ~/.claude/skills/video-generation/scripts/runway_client.py profile        # план + кто залогинен (нужна сеть)
```

Тот же гейт стоит в `runway_mcp.py get_client()` и в `/health` у local-gateway — просроченный токен виден до вызова, а не после.

> ⚠️ **Свежий токен может НЕ помочь — сначала смотри ПЛАН, потом снимай токен.** 22.06.2026 подписка свалилась на free plan, и Runway отказывал одинаково и в explore, и в stable — при валидном токене. Seedance 2.5 доступна на **всех платных планах и недоступна на free**, так что «обновил токен, всё равно не работает» — это чаще всего план, а не токен. Порядок диагностики: `profile` (план) → `token-status` (срок) → уже потом поход в localStorage.
>
> **Состояние на 09.09.2026: `RUNWAY_JWT` истёк 31.07.2026, лежит просроченным 40 дней, все вызовы дают 401.** Интеграция не проверена вживую после обновления — считать её рабочей нельзя, пока не пройдены оба шага выше.

## §2 — 4-step S3 upload flow

```
Step 1: POST /v1/uploads { name, contentType }
        → { presignedUrl, uploadId }
Step 2: PUT presignedUrl (raw file bytes, no multipart)
Step 3: POST /v1/uploads/complete { uploadId, filename }
        → { datasetId }
Step 4: POST /v1/tasks {
          taskType: <feature из /v1/profile/features, НЕ хардкод>,
          creationSource: 'tool-mode',
          numGenerations: 1,
          options: {
            textPrompt, duration, aspectRatio, resolution,
            referenceImages: [{ assetId, url: datasetId, type: 'first_frame' }]
          }
        }
        → { taskId }
```

> **`taskType` больше не хардкодится.** Раньше здесь стояло `'seedance_2'` — строка пережила выход 2.5 и молча гоняла старую модель. Теперь `runway_client.py` спрашивает `GET /v1/profile/features`, собирает все ключи `seedance*` и берёт самый свежий по номеру версии (`seedance_feature()`); константа `SEEDANCE_FALLBACK = "seedance_2_5"` — только запасной вариант, если профиль не отдал ни одной фичи. Подробнее — §11.

Mandatory headers:

```
Authorization: Bearer <RUNWAY_TOKEN_PLACEHOLDER>
Origin: https://app.runwayml.com
X-Runway-Workspace: <RUNWAY_TEAM_ID>
```

Mandatory body fields: `creationSource='tool-mode'`, `numGenerations=1`. Опусти любое = 400.

Запросы — через query `?asTeamId=<RUNWAY_TEAM_ID>`.

## §2.5 — ЧЕТЫРЕ режима Seedance 2.5 (Reference / Keyframe / Edit / Extend)

У 2.0 в этом файле был описан по сути один сценарий: картинка + промпт → клип. У 2.5 режимов **четыре**, и половина ловушек ниже растёт именно из того, что режим выбран не тот.

Вход модели: **текст, картинка, видео, аудио**. Звук встроенный — тумблер Audio есть **во всех четырёх режимах** (отдельная TTS-задача под озвучку больше не обязательна).

| Режим | Что делает | Когда брать |
|---|---|---|
| **Reference** | Комбинирует картинки/видео/аудио, у каждого входа своя роль (персонаж, локация, стиль, голос) | Собрать сцену из готовых ассетов, держать персонажа между шотами |
| **Keyframe** | Первый и последний кадр, промптом задаётся движение между ними | Точная композиция начала и конца; anti-mutation LOCK (§5) — это внутренности именно этого режима |
| **Edit** | Меняет готовое видео промптом или наброском поверх кадра | Заменить объект, убрать деталь, перекрасить — без ре-генерации с нуля |
| **Extend** | Продлевает готовое видео **вперёд ИЛИ назад** | Добить длину, дорастить предысторию до имеющегося кадра |

**Референсы: до 50 за генерацию** = 30 картинок + 10 видео (по 30 с) + 10 аудио. В режиме **Keyframe первый и последний кадр идут ДОПОЛНИТЕЛЬНО** к этим 50 — они не съедают лимит.

**Мультикадр.** Несколько сцен, смена ракурсов и смена темпа выходят **из ОДНОЙ генерации** — склеивать отдельные клипы не нужно. Это меняет планирование: раньше раскадровка резалась на 5-секундные шоты именно потому, что модель не умела иначе (§3, §10). Теперь «шот = генерация» — выбор, а не ограничение.

**Upscale — отдельный шаг после генерации**, не опция внутри задачи.

### Три ловушки (каждая ломает пайплайн молча)

1. **Extend возвращает ТОЛЬКО новый кусок.** Продлил 30-секундное видео на 5 секунд — на выходе клип на **5 секунд**, оригинал не меняется и в ответ не входит. Склейка — твоя, в ffmpeg. Пайплайн, который ждёт «оригинал + хвост» одним файлом, получит пятисекундный огрызок и посчитает это провалом генерации.
2. **Таймкоды в промпте задают ТЕМП, а не точку монтажа.** Написал «на 00:03 герой оборачивается» — действие встанет **рядом** с третьей секундой, не на ней. Кадровая точность достигается **только в посте**. Не строй на таймкодах в промпте синхрон с музыкой или репликой.
3. **Edit не даёт менять ни длину, ни пропорции.** Он берёт у исходного видео и aspect ratio, и длительность; управления duration нет, разрешение недоступно. Хочешь другой формат или другой хронометраж — это не Edit, это новая генерация.

### Наброски (sketch) в Edit / Extend

Рисунок поверх кадра подмешивается в промпт как ссылка вида `"@Image 1 at ss:SS"`. **Лучше работают в Edit**, чем в Extend.

> ⚠️ Всё в этом разделе — **имена и поведение из интерфейса** (Tools / Workflows / Agent, ноды «Seedance 2.5» и «Seedance 2.5 (Edit/Extend Video)»). Официальные API-слаги режимов Runway не публикует; как режим ложится на `options` внутреннего `/v1/tasks` — **не проверено**, снимай с сетевой панели при первой же живой сессии.

## §3 — Seedance prompt engineering

### Anatomy одного prompt'а

```
[SUBJECT motion]. [CAMERA movement]. [FILM VOCAB lock].
```

**Rule:** ONE action verb + ONE camera movement на prompt. Два verbs = competing visual directions + temporal incoherence. Split multi-action в отдельные 5s shots.

> На 2.5 «резать на шоты» — уже не единственный путь: несколько сцен и ракурсов выходят из одной генерации (§2.5). Правило «один глагол на один шот» от этого не отменяется, но применяется **внутри шота**, а не к целому клипу.

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
> Проверено на «клиентском трибьюте» (4 командных кадра, Seedance start-only + exploreMode) — лица держались.

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

> Это внутренности режима **Keyframe** (§2.5). Первый и последний кадр не расходуют лимит в 50 референсов.

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

**Правило:** меняй только термины — описание движения и камеры оставляй как есть, иначе поедет смысл кадра. Персональных данных в prompt'е быть не должно.

## §7 — Hard limits + конверсия форматов

- **textPrompt: 3500 characters max.** Exceeding → 400. Hard wall, без warning. Audit на repeated DO NOT clauses; убирай inline examples.
- **JFIF → JPG/PNG mandatory** перед upload:
  ```bash
  ffmpeg -y -i input.jfif output.jpg
  ```
  Без конверсии → 422 Unprocessable Entity.
- **Aspect ratios (2.5):** `Auto`, `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`. Выход — MP4 или MOV.
- **Resolutions:** `480p`, `720p`, `1080p` — по таблице спеков в справке Runway.
  ⚠️ **Страницы Runway противоречат друг другу:** FAQ на продуктовой странице говорит «480p and 720p», таблица спеков даёт три разрешения и там же прайс за 1080p. Верить таблице, но 1080p проверять по факту ответа задачи, а не по обещанию.
- **Duration (2.5): 4–30 s либо `Auto`.** Здесь стояло «5–10 s типичные» — цифра от 2.0, из-за неё половина диапазона выглядела недоступной. Оговорка §10 про temporal jitter >7 s — **наблюдение на 2.0**, на 2.5 не перепроверялось; длинные клипы гоняй, но смотри глазами.
- **Референсы:** до 50 за генерацию (30 картинок + 10 видео по 30 с + 10 аудио), кадры Keyframe — сверх лимита (§2.5).
- **План:** Seedance 2.5 доступна на всех платных планах, на free — нет.

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

> Замер сделан на **2.0**, у которой потолок был 10 s. У 2.5 диапазон 4–30 s и есть мультикадр в одной генерации (§2.5) — на ней это **не перепроверялось**. Не переноси вывод автоматически: сгенерируй один длинный клип и посмотри, а не режь заранее.

Long generations (>7 sec) часто получают temporal flicker. Workaround:

1. Split на 2 shorter 4-5s clips
2. Crossfade в ffmpeg (см. assembly.md xfade chain)
3. Add к prompt: `even diffuse lighting, steady intensity, 24 fps cinematic cadence, locked tripod, zero camera shake`

## §11 — taskType mapping

> ⚠️ **Официального API-идентификатора Seedance 2.5 не существует в публичных доках.** Ни справка, ни продуктовая страница не называют ни одного слага — там только имена из интерфейса (Tools, Workflows, Agent) и ноды «Seedance 2.5» / «Seedance 2.5 (Edit/Extend Video)». Поэтому `seedance_2_5` — **наша догадка-фолбэк, а не документированный ID**, и выдавать её за официальную нельзя.
>
> Рабочий путь: **спросить у аккаунта.** `runway_client.py` дёргает `GET /v1/profile/features`, собирает ключи `seedance*` и берёт самый свежий по номеру версии:
> ```bash
> python ~/.claude/skills/video-generation/scripts/runway_client.py features    # что реально включено на аккаунте
> ```
> Если профиль не отдал ни одной фичи `seedance*` — клиент печатает предупреждение и падает на `SEEDANCE_FALLBACK = "seedance_2_5"`. Хардкод в своём коде не заводи: ровно на этом 2.0 пережила выход 2.5 и работала «успешно» на старой модели.

| Provider | taskType |
|---|---|
| Seedance | из `/v1/profile/features` (см. врезку). Исторически 2.0 = `seedance_2`; для 2.5 НАША константа-заглушка `SEEDANCE_FALLBACK = "seedance_2_5"` в runway_client.py — НИ РАЗУ не проверена живым вызовом (токен мёртв 40 дней, всё отвечает 401) |
| Gen-4 Turbo | `gen4_turbo` |
| Gen-4 Image-to-Video | `gen4_image_to_video` |
| Kling 3.0 | `kling_v3` |
| Veo 3.1 (через Runway wrapper) | `veo3_fast` / `veo3_full` |
| Multi-Shot | `multi_shot` |
| TTS | `generated_audio` |

## §12 — Пулы кредитов + credits-mode vs exploreMode

- **Unlimited subscription** = 2250 credits free + flat-rate провайдеры (на Unlimited это $0 marginal)
- **API usage** = отдельный pool, требует credit purchase + billing setup
- **Gen-4 = per-second variable** (cost не flat), на Unlimited тоже даёт значимую экономию

### Прайс Seedance 2.5 — ПОСЕКУНДНЫЙ, не за задачу

Здесь стояло «Seedance 2.0 = 180 credits/job» — плоская ставка. У 2.5 плоской ставки нет, и на длинных клипах старая цифра занижала бюджет в разы (30 с в 1080p — это не 180, а 2040 кредитов):

| Разрешение | Кредитов за секунду | + за секунду ВХОДНОГО видео |
|---|---|---|
| 1080p | 68 | +34 |
| 720p | 30 | +15 |
| 480p | 20 | +10 |

Входное видео (режимы Edit / Extend / видео-референс) добавляет **половину ставки за каждую свою секунду**. Считать надо обе стороны: 10-секундный Extend поверх 30-секундного исходника в 720p при буквальном чтении ставки = 10×30 + 30×15, а не 10×30. На реальном счёте эта арифметика не сверялась — токен просрочен (§1); перед большим батчем прогони один короткий клип и посмотри списание.

### `exploreMode` (опция в options тела задачи)

| `exploreMode` | Кредиты | Параллелизм | Скорость |
|---|---|---|---|
| `False` (credits-mode) | СПИСЫВАЕТ из пула (у 2.5 — посекундно, см. таблицу выше) | до ~30 concurrent (`canStartNewTask.currentLimit: 30`) | быстро, без троттла |
| `True` (explore) | **БЕСПЛАТНО / unlimited** | троттл ~3 concurrent | медленнее |

Дефолт для пакетной генерации — **`exploreMode=True`**: пакет всё равно упирается не в скорость, а в ручной просмотр клипов. Credits-mode — когда срочно нужно >3 параллельно.

> **Гоча (заработано боем):** на чистой Unlimited-подписке с 0 купленных кредитов credits-mode
> (`exploreMode=False`) ВСЕГДА возвращает `400 "You do not have enough credits"` — пула просто нет.
> Значит explore — ЕДИНСТВЕННЫЙ режим, а он сейчас жёстко троттлит: `429` на submit даже при 2
> в полёте, задачи висят `THROTTLED progress=0`. **Escape: фолбэк на Veo 3.1 Fast** (`veo-3.1-fast-generate-preview`,
> свой GOOGLE_API_KEY, t2v без картинки, 3 concurrent, ~60с/клип) — 30 клипов за ~15 мин вместо часов. Это документированный спаситель, реально работает.
>
> **Про запасные аэродромы, состояние на 09.09.2026:**
> - Veo 3.1 в Gemini API — три ID: `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview`. **Все три — Preview, не GA** (выпущены 15.10.2025 full и fast, 31.03.2026 lite; дата снятия не объявлена). То есть фолбэк сам стоит на превью-модели — держи это в уме, планируя длинный проект.
> - **Sora как фолбэка больше нет:** 24.09.2026 OpenAI выключает `sora-2`, `sora-2-pro`, все снапшоты и сам эндпоинт `/v1/videos`. Замены OpenAI не предложил — это уход продукта, а не переименование.
> - Из-за этого умер и прежний приём «кириллица на кадре → гнать через Sora»: **Veo кириллицу корёжит**, и лечится это теперь только оверлеем текста на монтаже.

### КРИТИЧНО — кредит списывается в момент ОТПРАВКИ (POST /v1/tasks), НЕ при скачивании

- Остановка локального раннера в середине батча **НЕ возвращает** уже списанные кредиты.
- Но и не «жжёт впустую»: отправленная задача **досчитывается на сервере** и остаётся скачиваемой по `task_id`.
- **Keyframe-картинки независимы от видео-задач** — остановка анимации keyframes не тратит: картинки остаются, а видео-задача либо уже списана и досчитается, либо не отправлялась.
- При credits-mode **не делай resubmit на «фейл»** не проверив сервер — каждый submit = новое списание (в exploreMode resubmit пул не расходует, но плодит дубли).

### Пул исчерпан → переход на exploreMode

`POST /v1/tasks` вернул `400 "not enough credits"` → переотправь оставшиеся задачи с `exploreMode=True` (тот же JWT), с поправкой на троттл ~3 параллельных.

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
- [ ] Audio пустой или native — strip перед mix (у 2.5 звук встроенный и тумблер есть во всех режимах: решай явно, генерить его или нет)

Дополнительно для 2.5:
- [ ] **Extend:** на выходе только новый кусок — оригинал подклеен вручную, длина итога = исходник + продление
- [ ] **Edit:** пропорции и длина совпали с исходником (управления ими нет — если ждал другие, это была не та задача)
- [ ] Действия по таймкодам стоят там, где нужно, **после монтажа**, а не по обещанию промпта
- [ ] Разрешение реально то, что запрашивал (1080p подтверждён ответом задачи, а не FAQ)
- [ ] Мультикадр не съехал: смены ракурса внутри одной генерации не порвали персонажа
