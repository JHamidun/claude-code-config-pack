---
name: video-generation
description: "AI-видео хаб: Veo, Seedance 2.5, Runway, Kling. Триггеры: «сгенерь видео», «оживи картинку», «виральность». НЕ: монтаж→video-editor; промо→video-shotcraft; картинки gpt-image-2.5→openai-dalle."
type: actionable
---

# Video Generation — единый хаб для AI-видео

## КУДА ИДТИ: маршрут по всему видео-кластеру (читать ПЕРВЫМ)

На «сделай ролик» претендуют шесть входов, и они делают РАЗНОЕ. Выбор идёт по одному
вопросу: **откуда берётся картинка** — её рисует модель, она уже снята, её рисует браузер.
Ошибка выбора стоит не промаха в стиле, а всего пайплайна: конвейер ролями и turnkey-run.py
не совместимы по артефактам, переиграть на середине нельзя.

| Что просят | Куда идти |
|---|---|
| «сгенерь видео / оживи картинку / сцена по описанию» — кадры рисует ИИ (Veo, Seedance 2.5, Runway, Kling) | **этот навык**, ниже по тексту |
| «вырежи паузы / склей / наложи субтитры / цветокор / сделай вертикалку» — футаж УЖЕ снят | `video-editor` |
| «собери рилс с нуля» 9:16 — бриф → сценарий → музыка → раскадровка → монтаж → приёмка, стадиями | `video-montage` (конвейер `workflows/reel-factory.js`; промпты стадий — `video-factory-pipeline`) |
| «промо продукта / видео из лендинга / шоурил» — кадры рисует браузер, Remotion + 153 рецепта | `video-shotcraft` |
| «выгрузи эту HTML-анимацию в MP4/GIF» — покадровый рендер готовой страницы | `video-export` |
| «нарежь шортсы из вебинара / шорт с владелец конфига» — SRT → HeyGen Avatar V → SubMagic → канал | `shorts-pipeline-владелец конфига` |
| «сделай полный ролик про X и выложи на YouTube» — тренд → сценарий → аватар → b-roll → загрузка | Agent `video-factory` |
| «сгенерь кейфрейм gpt-image-2.5 / отредактируй кадр по референсам / транскрипция / TTS у OpenAI» — нужна картинка или звук, не клип | `openai-dalle` |

**Граница с `openai-dalle` больше НЕ проходит по видео.** До сентября 2026 Sora была описана в
обоих навыках, и правило звучало «вендор назван и нужен вызов → `openai-dalle`». Правило мертво:
**24.09.2026 OpenAI выключает `sora-2`, `sora-2-pro`, все снапшоты и сам эндпоинт `/v1/videos`**,
замены не предложено — это уход продукта, а не переименование, и кода Sora в `openai-dalle`
уже нет. Туда теперь ходят за **картинками** (`gpt-image-2.5`: генерация и edit до 16 референсов,
прозрачный фон) и за звуком того же ключа (транскрипция, TTS, embeddings) — то есть за
кейфреймами и озвучкой, а не за клипом. Любое «сгенерь видео / оживи картинку» — сюда, назван
вендор или нет.

⚠️ **Приём «Sora, когда на кадре кириллица» больше невыполним.** Veo кириллицу корёжит, и
подменить его теперь нечем: единственное лечение — **не рисовать текст моделью**, а класть его
оверлеем на монтаже (PIL/drawtext поверх кадра, см. turnkey battle-notes ниже).

⚠️ **Имя `video-factory` носят ДВЕ разные вещи.** Agent `video-factory` (+ команда
`/video-factory`) — конвейер тренд → YouTube с аватаром HeyGen. Внутри `video-montage`
лежал одноимённый файл конвейера ролями — он переименован в `workflows/reel-factory.js`,
чтобы «запусти video-factory» не означало две разные программы.

Промпты стадий обоих конвейеров лежат в Skill `video-factory-pipeline`: сборка ролика —
`references/stage-1-brief.md` … `stage-8-qc.md`, тренд → YouTube —
`references/youtube-pipeline.md`. Отдельных агентов `vf-*` больше нет (сведены 2026-08-22).

---

Хаб, который выбирает провайдер, держит auth, оркестрирует шесть фаз, накладывает аудио, собирает финал. Детали по провайдерам — в `references/*.md`, чтобы не раздувать контекст.

## Что умеет хаб

Три уровня вызова: **(A) весь пайплайн под ключ** (`scripts/run.py --brief b.json [--execute]`) ·
**(B) отдельный флоу** движка Higgsfield · **(C) отдельный атом/инструмент**. Разбор всех уровней,
список флоу и таблица соседних навыков — `references/capability-map.md`.

## Когда использовать

Срабатывает на любую фразу про видео:
- "сгенерь видео / ролик / шортс / reels / TikTok / YouTube Short"
- "оживи картинку / image-to-video / animated illustration"
- "буктрейлер / cinematic trailer / living book cover"
- "Veo / Seedance / Runway / Kling / Pika" (Sora больше не вариант — эндпоинт OpenAI выключается 24.09.2026)
- "vertical / 9:16 / 21:9 / cinemascope / square"

Когда НЕ использовать:
- Чистый text-to-speech без видео → `elevenlabs`
- Чистая генерация картинки → `nano-banana-pro` / `image-generation`
- Talking-head шортсы владелец конфига под YouTube → `shorts-pipeline-владелец конфига` (готовая обвязка Avatar V + SubMagic + триггер-чек)
- Чистый монтаж готовых клипов (без AI-генерации) → `video-editor`
- Ролик 9:16 «с нуля» конвейером ролей (бриф→сценарий→музыка→раскадровка→монтаж) → `video-montage`
- Промо-ролик продукта на Remotion (кадры рисует браузер, не модель) → `video-shotcraft`
- Удалить объект из существующего видео → `void-video`
- Скачать чужое видео → `video-downloader`

## ROUTING-MAP — какую часть хаба грузить (читай только нужную ветку, остальное lazy)

> **ПРИНЦИП ЭКОНОМИИ (главный):** генерируем МАКСимально через СВОИ прямые API / подписки / скиллы (дёшево или $0),
> а bundled `hf.exe` (токены/кредиты Higgsfield) дёргаем ТОЛЬКО для того, что напрямую невозможно (HF-эксклюзивы).
> `engines/higgsfield/scripts/router.py` это и делает: `route(jst)` → direct где можно, hf.exe только для 🔴.

1. **Прямая генерация (DEFAULT)** — Veo (GOOGLE_API_KEY) · Seedance 2.5 + Kling (Runway; ⚠️ **не $0**, см. ниже) · HeyGen Avatar · keyframes (Nano/GPT-Image) · аудио (ElevenLabs/Lyria/Suno) · монтаж (ffmpeg). → **остаёшься в этом SKILL.md + `references/*`** (6-фаз пайплайн, decision-tree ниже, 40-строчная gotcha-таблица, audio/assembly рецепты, scripts/*).
   ⚠️ Здесь стояло «Seedance 2.0 + Kling (Runway Unlimited = $0 marginal) · Sora (OpenAI)». Оба факта врали: Sora выключается 24.09.2026, а «$0 marginal» держался на подписке Unlimited, которая **ещё 22.06.2026 сваливалась на free plan** (разбор 22.06.2026: Runway отказывал и в explore, и в stable). Считать генерацию бесплатной по факту наличия ключа нельзя — **сначала план в `/v1/profile`, потом стоимость в кредитах**.
2. **Структурный флоу Higgsfield** (его промпт-инжиниринг, но генерация — СВОИМИ провайдерами!) — cinematic-5, motion-design (highMD/productMD/typographyMD/infographicMD/classicMD), UGC/unboxing/tutorial/try-on, TV-ad, podcast, cartoon. → открой **`engines/higgsfield/ENGINE.md`** режим (A): `prompt_builders.py` строит промпт → `router.py` гонит через Runway/Veo/Replicate (НЕ hf) → `assemble.py`/`ffmpeg_assemble.py` собирает.
3. **HF-эксклюзив (только тут тратим hf.exe)** — Soul Cast/Location/ID, Marketing Studio/DTC, Virality Predictor (brain_activity), Cinema Studio, ai_stylist, reframe, draw_to_video. → **`engines/higgsfield/ENGINE.md`** режим (B). Это единственное, чего нет напрямую.
   ⚠️ **Ветке (B) нужен вход в Higgsfield CLI.** Без него `./bin/hf.exe account status` отвечает `Error: Not authenticated`, а `~/.config/higgsfield/credentials.json` отсутствует. **`HIGGSFIELD_ACCESS_TOKEN` в окружении бинарь НЕ читает** — `router.py` его подкладывает, и всё равно приходит отказ авторизации, который выглядит как проблема модели. Перед первым HF-эксклюзивом: `cd engines/higgsfield && ./bin/hf.exe auth login` (Clerk device-flow, подтверждение в браузере), затем `./bin/hf.exe account status` для проверки плана и кредитов.

**Приоритет провайдеров пересмотрен 09.09.2026 — «иначе всегда Runway $0» больше не действует.**
Раньше тут стояло: «Seedance доступен через hf.exe, но только как фолбэк когда Runway в throttle».
Сегодня Runway не в throttle, а **лежит**: `RUNWAY_JWT` истёк 31.07.2026 и провалялся просроченным
40 дней, все вызовы отдают 401. Порядок на сейчас:

- **Veo (`GOOGLE_API_KEY`)** — единственная ветка, живая без ручных действий. Дефолт, пока Runway не восстановлен.
- **Runway / Seedance 2.5** — только после ручного обновления токена. ⚠️ **Обновление может НЕ помочь**, и
  это главная ловушка: 22.06.2026 подписка уже сваливалась на free plan, и Runway отказывал и в explore,
  и в stable — при полностью валидном токене. Поэтому порядок такой: **сперва убедиться, что план платный**
  (кабинет на app.runwayml.com или `/v1/profile` со свежим токеном), и лишь потом считать ветку рабочей —
  иначе новый `RW_USER_TOKEN` снят зря, а отказ выглядит как «проблема модели». Автоматики обновления нет
  нигде: только руками через localStorage. Срок токена офлайн — `runway_client.py token-status`.
- **hf.exe (Higgsfield)** — фолбэк, но и он **не залогинен** (см. ⚠️ в п.3 выше). Требует такого же ручного
  входа, поэтому «фолбэком на автомате» не является.

## TURNKEY — одна команда под ключ (`scripts/run.py`)

Не хочешь собирать вручную — дай бриф, и оркестратор прогонит весь пайплайн сам (intake → flow → промпт → route DIRECT-first → параллельный fan-out keyframes+clips → аудио → ffmpeg → платформенный экспорт), с **approval-гейтом** перед дорогой стадией клипов.

```bash
# DRY-RUN (по умолчанию — строит ПЛАН, ничего не тратит, пишет out/plan.json):
python scripts/run.py --flow cinematic --story "сюжет" --aspect 21:9 --platform youtube --duration 24
python scripts/run.py --brief brief.json            # полный бриф (flow/palette/voiceover_text/music_prompt/scenes)
# ЗАПУСК (keyframes → GATE → clips → audio → assemble; --yes снять гейт):
python scripts/run.py --brief brief.json --execute
```
Бриф (JSON): `{flow, brief, aspect, platform, duration, palette[], voiceover_text, voice, music_prompt, scenes[], out_dir}`. flow ∈ cinematic / highMD / productMD / typographyMD / infographicMD / classicMD / simple. Под капотом зовёт `prompt_builders` (промпт), `router` (DIRECT vs hf), `nano_banana_keyframes`/`runway_client`/`veo_image_to_video` (генерация своими ключами), `elevenlabs_voiceover`/`lyria_music` (аудио), `ffmpeg_assemble`+`engines/.../assemble.py` (сборка). hf.exe — только если флоу требует эксклюзив. Для сложного/творческого — оркеструй фазы сам по ROUTING-MAP ниже.

⚠️ **Ловушка имени в плане (деньги за кадр).** В `plan.json` и в выводе `run.py` строка вида `Keyframes : DIRECT via google-genai (nano_banana_2)` означает **Nano Banana Pro** (`gemini-3-pro-image-preview`), а НЕ дешёвую NB2. Внутренние алиасы `router.py` не совпадают с каноном `config/models.md`: `nano_banana_2` = Pro (дорого), `nano_banana_flash` = «Nano Banana 2» / `gemini-3.1-flash-image-preview` (дефолт канона, дёшево). Читая план — сверяйся с этой парой, а не с именем.

### Turnkey battle-notes (заработано боем на @your_channel, 2026-06)
- **Текст/числа в хуке → PIL-оверлей + Ken Burns, НЕ image-моделью и НЕ i2v.** Nano/Veo гарбят цифры; крупное «$48 000 000» компонуй PIL (arialbd) на затемнённый bg → `ken_burns` (без AI-морфа = текст чёткий). Виральный хук всегда = число/имя крупно в 1-ю секунду (топ-шортсы канала так и сделаны).
- **Runway → Veo фолбэк теперь на ДВА разных отказа, и путать их нельзя.** `429` — throttle (account-level, даже sequential), проходит сам, resubmit не нужен. `401` — мёртвая авторизация (истёкший JWT; отдельно возможен отказ по free-плану, но КАКОЙ код он отдаёт — не проверено, в записи 22.06.2026 стоит только «отказывал и в explore, и в stable»), и ожиданием не лечится: это ручной вход, а не «попробуй позже». Код различает их отдельно; фолбэк на Veo (свой `GOOGLE_API_KEY`) спасает в обоих случаях, но в 401 без человека Runway не вернётся.
- **Veo ID:** рабочий `veo-3.0-fast-generate-001` (stable). 3.1 ТОЛЬКО как `veo-3.1-*-preview` (НЕ `-001`) — и все три (`veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`, `veo-3.1-lite-generate-preview`) **в статусе Preview, не GA**: выпущены 15.10.2025 (full и fast) и 31.03.2026 (lite), дата снятия не объявлена. Preview означает, что ID может пропасть без предупреждения — держи `veo-3.0-fast-generate-001` как запасной. Veo `--duration` ∈ {4,6,8} (не 5). Veo 9:16 = 720×1280 (concat нормализует до 1080×1920).
- **brain_activity (virality) ≤16 секунд** — финал для проверки режь ≤15.5с.
- **Git Bash `$PWD` = POSIX `/c/...`** ffmpeg на Windows не откроет → в манифестах/путях всегда `C:/...` (или PowerShell).
- Цикл полировки: сделал → **контактка (ffmpeg tile) → смотреть глазами** → диагноз → фикс скрипта/скилла → пересобрать → virality-замер. Так v1 hook 27 → v2 hook 33.

## Provider selection — decision tree

| Задача | Провайдер | Почему | Цена |
|---|---|---|---|
| Default «просто оживи» | **Seedance 2.5** через Runway JWT — ⚠️ токен просрочен с 31.07.2026, до восстановления фактический дефолт **Veo** | Лучший motion из i2v; 4 режима, мультикадр из одной генерации | **68 кред/с** (1080p) · 30 (720p) · 20 (480p); входное видео +половина ставки |
| Кириллический текст на кадре | **никакая модель** — текст оверлеем на монтаже | Veo корёжит кириллицу в «иероглифы», а Sora, которой это лечили, выключается 24.09.2026 | $0 (PIL/drawtext, см. battle-notes) |
| Cinematic 21:9 trailer с native аудио | **Veo 3.1 Full** | Native audio + 4K-grade composition | $0.40/s |
| Быстрый 5-секундный motion для соцсетей | **Veo 3.1 Fast** | Дешевле Full в 4×, качество для шортсов достаточно | $0.10/s |
| Image-to-video с lock'ом face/glyph | **Seedance + end_frame=first_frame** | Forces interpolation между identical — small detail changes only | ставка Seedance (см. 1-ю строку) |
| Talking head владелец конфига | **HeyGen Avatar V** (`heygen` skill) | Готовый avatar_id + voice_id, lip-sync из коробки | $0.0667/s |
| B-roll из готовой картинки без AI-генерации | **Ken Burns zoompan** (ffmpeg) | Бесплатно, мгновенно, для slow-pan «оживления» | $0 |
| Multi-shot cinematic narrative | **Seedance 2.5 i2v + Nano Banana Pro keyframes** | Lock characters через reference image (1-2 лица); у 2.5 несколько сцен и ракурсов выходят ИЗ ОДНОЙ генерации, без склейки клипов | ставка Seedance |
| 3–4 РЕАЛЬНЫХ лица в одном кадре | **GPT-Image-2.5 multi-ref → Seedance** | Nano держит 1-2, плывёт на 3-4; GPT `/v1/images/edits` мультиреференс точнее (до 16 референсов). См. `references/keyframes-multiface.md` | ставка Seedance |
| Брендкит / UI-only workflow без API | **Playwright MCP browser fallback** | См. `references/runway-seedance.md` §8 | по плану подписки (не $0 на free) |

Конфликт keyframing'а решён явно:
- **Veo** интерполирует motion → нужны РАЗНЫЕ first/end frame. (Раньше в этой строке рядом стояла Sora — её больше нет.)
- **Seedance** склонен мутировать мелкие детали → `end_frame=first_frame` LOCK даёт anti-mutation для tattoos/глифов/лиц. Приём снят на **2.0**; в 2.5 первый и последний кадр задаются режимом **Keyframe**, но работает ли там тот же трюк с ОДИНАКОВЫМИ кадрами — **не проверено**, доки такого не обещают.

### Seedance 2.5 — что изменилось против 2.0 (снято с официальных страниц Runway 09.09.2026)

- **Четыре режима, а не один**: `Reference` (комбинировать картинки, видео и аудио, у каждого входа своя роль; лимит 50 указан для генерации в целом, не для этого режима отдельно) · `Keyframe` (первый + последний кадр) · `Edit` (менять готовое видео промптом или наброском) · `Extend` (продлевать готовое видео вперёд ИЛИ назад).
- **Вход**: текст, картинка, видео, аудио. **Длительность** 4–30 с либо Auto. **Кадры**: Auto, 21:9, 16:9, 4:3, 1:1, 3:4, 9:16. Выход MP4/MOV.
- **Референсы**: до 50 за генерацию = 30 картинок + 10 видео (по 30 с) + 10 аудио. В режиме Keyframe первый и последний кадр идут **дополнительно** к этим 50.
- **Кредиты**: 1080p — 68/с, 720p — 30/с, 480p — 20/с; входное видео добавляет половину ставки (+34 / +15 / +10 за секунду входа).
- **Звук встроенный**, тумблер Audio есть во всех четырёх режимах. Апскейл — отдельным шагом после генерации.
- **Мультикадр**: несколько сцен, ракурсов и смен темпа выходят из ОДНОЙ генерации — склеивать отдельные клипы не нужно.
- ⚠️ **Edit** берёт у исходного видео и пропорции, и длину: управления длительностью нет, разрешение недоступно. **Extend** возвращает ТОЛЬКО новый кусок (продлил 30 с на 5 — получил клип на 5 с, оригинал не меняется), склейка на нас.
- ⚠️ **Таймкоды в промпте задают темп, а не точку монтажа**: действие встанет рядом с секундой, не на ней. Кадровая точность — только в посте.
- ⚠️ **Наброски (sketch)** в Edit/Extend попадают в промпт как `"@Image 1 at ss:SS"`; в Edit работают лучше, чем в Extend.
- ⚠️ **Разрешения противоречат сами себе**: таблица спеков в справке даёт 480p/720p/1080p (и там же прайс за 1080p), а FAQ на продуктовой странице — «480p and 720p». Верить таблице, но держать в уме расхождение.
- ⚠️ **API-идентификатора Seedance 2.5 официальные страницы НЕ называют** — ни одного слага, только имена нод в интерфейсе («Seedance 2.5», «Seedance 2.5 (Edit/Extend Video)»). Не выдавай `seedance_2_5` за официальный ID; версию определяет `runway_client.py` через `/v1/profile/features`.
- ⚠️ Снята ли Seedance 2.0 — **нигде не сказано**. Известно только, что 2.5 — преемник 2.0.
- Доступна на всех платных планах; на free — нет. Это ещё одна причина проверять план ПЕРЕД генерацией.

## Auth & credentials

Всё в `~/.claude/.credentials.master.env`:

| Переменная | Для чего |
|---|---|
| `GOOGLE_API_KEY` | Veo 3.1 (google-genai SDK) |
| `GEMINI_API_KEY` | **КОНФЛИКТ** с GOOGLE_API_KEY. `os.environ.pop('GEMINI_API_KEY', None)` ПЕРЕД `import genai` |
| `GOOGLE_CLOUD_PROJECT_ID` | Lyria 2 через Vertex AI |
| `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` | Абсолютный путь к service-account JSON для Lyria (НЕ конфликт с GOOGLE_API_KEY) |
| `RUNWAY_JWT` | Runway internal API. **30 дней TTL**, обновление ТОЛЬКО руками: app.runwayml.com → DevTools → Application → localStorage → `RW_USER_TOKEN`. ⚠️ **Истёк 31.07.2026, лежит просроченным — все вызовы дают 401.** Автоматики обновления нет нигде |
| `RUNWAY_TEAM_ID` | `?asTeamId=<id>` параметр для большинства endpoints |
| `ELEVENLABS_API_KEY` | TTS + Music |
| `OPENAI_API_KEY` | Кейфреймы `gpt-image-2.5`, транскрипция, TTS (→ `openai-dalle`). Для видео **больше не годится**: `/v1/videos` и обе `sora-2*` выключаются 24.09.2026 |
| `HEYGEN_API_KEY` | Avatar V (через `heygen` skill) |
| `SUBMAGIC_API_KEY` | EN-субтитры (`x-api-key: sk-...`, НЕ Bearer) |

Проверка JWT (день 31 = 401) — **два шага, и порядок важен**:

```bash
# 1) срок токена офлайн, без сети и без 401 в логах:
python ~/.claude/skills/video-generation/scripts/runway_client.py token-status
# 2) живой профиль И ПЛАН (free plan отказывает даже с валидным токеном):
python ~/.claude/skills/video-generation/scripts/runway_client.py profile
```

Гейт стоит и в `runway_mcp.py` (`get_client()`), и в `/health` у `local-gateway` — они честно
скажут «токен просрочен», а не отдадут 401 из середины генерации.

## Pipeline overview — 6 фаз

```
1. Intake          → бриф, длительность, аспект, платформа, бюджет, голос
2. Storyboard      → текстовый сценарий по shot'ам, длительность каждого
3. Visual style    → lock film vocabulary (см. §Visual lock), generate keyframes
4. Clip planning   → выбор провайдера на каждый shot, prompts с motion+camera
5. Generation      → parallel fan-out (Veo×3 / Seedance batch / TTS / Music)
6. Assembly        → ffmpeg concat+xfade, amix+ducking, loudnorm, compression tier
```

Reference timeline для 77s 9:16 vertical:
- Keyframes: **45–60 sec** (Nano Banana Pro batch до 4 parallel)
- Generation parallel: **120 sec** (Veo 3 concurrent + voice + music)
- Assembly: **30–50 sec** (concat -c copy 65x realtime + final loudnorm pass)
- **Wall-clock: ~4 минуты**

Детали фаз 3–5b (визуальный стиль, кейфреймы, генерация по провайдерам, поэтапный апрув, аудио, FFmpeg-сборка) — `references/pipeline-phases.md`. Открывай на нужной фазе.

## Known gotchas — master table

| # | Gotcha | Provider | Где детали |
|---|---|---|---|
| 1 | `GEMINI_API_KEY` env conflict — pop ДО import | Veo | `references/veo-direct.md` |
| 2 | Veo safety filter возвращает NoneType, не exception | Veo | `references/veo-direct.md` |
| 3 | Veo `types.Image(image_bytes=..., mime_type='image/png')` — path string silently degrades | Veo | `references/veo-direct.md` |
| 4 | Veo concurrent ceiling = 3, 5+ = RESOURCE_EXHAUSTED | Veo | `references/veo-direct.md` |
| 5 | Veo всегда генерит native audio — `-an` strip для внешнего VO | Veo | `references/veo-direct.md` |
| 6 | ~~Sora > Veo для кириллицы~~ — приём мёртв (Sora выключается 24.09.2026). Кириллица на кадре — только оверлеем в монтаже | Veo | `references/windows.md` (PIL-оверлей) |
| 7 | Seedance CHARACTER moderation: girl/woman/девочка/имена → 400 | Seedance | `references/runway-seedance.md` |
| 8 | Seedance `end_frame=first_frame` LOCK = anti-mutation | Seedance | `references/runway-seedance.md` |
| 9 | API param = `end_frame`, UI label = `last frame` — НЕ путать | Runway | `references/runway-seedance.md` |
| 10 | textPrompt hard cap 3500 chars | Runway | `references/runway-seedance.md` |
| 11 | JFIF → JPG/PNG конвертация обязательна перед upload | Runway | `references/runway-seedance.md` |
| 12 | Runway JWT 30-day TTL, day 31 = 401 | Runway | `references/runway-seedance.md` |
| 13 | Mandatory headers: creationSource, numGenerations, X-Runway-Workspace | Runway | `references/runway-seedance.md` |
| 14 | Start-frame-only 70-80% better motion (Seedance эмпирически) | Seedance | `references/runway-seedance.md` |
| 15 | ONE action ONE camera per prompt | Seedance | `references/runway-seedance.md` |
| 16 | Не повторять описание персонажа в i2v prompt — морфит face | Seedance | `references/runway-seedance.md` |
| 17 | Unlimited subscription credits ≠ API billing pool | Runway | `references/runway-seedance.md` |
| 18 | Nano Banana identity NOT preserved между calls — reference-chain | Image | `nano-banana-pro` skill |
| 19 | Lyria 2 — service account ONLY, API key = 401 | Audio | `references/audio.md` |
| 20 | Lyria 2: seed и sample_count>1 взаимоисключающи | Audio | `references/audio.md` |
| 21 | Lyria 2 — 30s WAV per sample, длинные через acrossfade | Audio | `references/audio.md` |
| 22 | ElevenLabs Music 30s hard cap | Audio | `references/audio.md` |
| 23 | ElevenLabs Music named-artist → content_policy_violation | Audio | `references/audio.md` |
| 24 | ffmpeg `amix duration=longest` обрезает по SHORTEST — apad + -t | FFmpeg | `references/assembly.md` |
| 25 | ffmpeg concat дропает ВСЁ аудио если один клип без audio — anullsrc | FFmpeg | `references/assembly.md` |
| 26 | ffmpeg `amix normalize=0` обязательно | FFmpeg | `references/assembly.md` |
| 27 | ffmpeg xfade принимает РОВНО 2 input | FFmpeg | `references/assembly.md` |
| 28 | Windows subprocess: `encoding='utf-8', errors='replace'` | Windows | `references/windows.md` |
| 29 | Windows ffmpeg drawtext + кириллица = крах, workaround через PIL | Windows | `references/windows.md` |
| 30 | Yandex Disk multipart upload = 0-byte file, нужен raw PUT | Delivery | `references/windows.md` |
| 31 | SubMagic «пайвот» → 🍺 на RU, обязательная trigger-word чистка | Captions | `submagic` skill |
| 32 | Playwright MCP clipboard = `navigator.clipboard.writeText()` | Browser | `references/windows.md` |
| 33 | ElevenLabs Music param = `music_length_ms` + `force_instrumental=True` + `model_id='music_v1'` (НЕ `length_ms` → TypeError) | Audio | `references/audio.md` §2 |
| 34 | Runway кредит списывается при ОТПРАВКЕ, не скачивании; стоп раннера не «жжёт кадры»; SUCCEEDED добирается по task_id | Runway | `references/runway-seedance.md` §12 |
| 35 | НЕ останавливать чужую идущую генерацию без спроса (user-trust); НЕ resubmit на client-timeout (THROTTLED≠failed) | Runway | `references/runway-seedance.md` §12 |
| 36 | Nano держит 1-2 лица, плывёт на 3-4 → GPT-Image-2.5 multi-ref (до 16 референсов) для ансамбля; итеративно + вето | Image | `references/keyframes-multiface.md` |
| 37 | Контактный лист для vision-ревью ≤ 2000px шириной (иначе read падает) | Image | `references/keyframes-multiface.md` |
| 38 | RU TTS ударение через combining acute U+0301; print такой строки падает на cp1251 (numeric format) | Audio/Win | `references/audio.md` §3 |
| 39 | Glyph-pulse trap: «pulsing sigil» → bloom в disc/медальон; форму держит только STEADY glow (без brightness-пульса) или post-composite | Seedance | `references/runway-seedance.md` §4 #1 |
| 40 | Thrown/passed object левитирует и дрейфует; end_frame диктует resolved state → дай keyframe «объект уже в руках / действие завершено» | Seedance | `references/runway-seedance.md` §4 #8 + §5 |

Шаблоны потоков и таймлайны реальных проектов — `references/workflow-templates.md`.

## Reference files (lazy-loaded)

- `references/pipeline-phases.md` — фазы 3–5b целиком: визуальный стиль, кейфрейминг, рецепты по провайдерам, поэтапный апрув, аудиоблок, FFmpeg-сборка
- `references/capability-map.md` — три уровня вызова, список флоу Higgsfield, таблица соседних навыков
- `references/workflow-templates.md` — шаблоны потоков и таймлайны реальных проектов
- `references/higgsfield-flows.md` — техники Higgsfield, вшитые в наши фазы (выжимка) → полный движок `engines/higgsfield/ENGINE.md`
- `engines/higgsfield/ENGINE.md` — **движок Higgsfield**: 6-фаз оркестрация + 11 флоу + hf.exe CLI + scripts/{prompt_builders,router,assemble}.py + references/ (60+) + registries/ (real UUID)

- `references/runway-seedance.md` — Runway JWT API + Seedance prompt engineering + browser fallback
- `references/veo-direct.md` — Veo 3.1 Fast/Full (⚠️ раздел про Sora там устарел: эндпоинт OpenAI `/v1/videos` выключается 24.09.2026)
- `references/audio.md` — Lyria 2 (your-server OAuth) + ElevenLabs Music/TTS voice IDs + Suno climax-cut + RU ударения
- `references/keyframes-multiface.md` — несколько РЕАЛЬНЫХ лиц в кадре (GPT-Image-2.5 multi-ref vs Nano, биометрия, hero/ensemble)
- `references/director-rules.md` — скелет промпта под кадр (7 слотов: Subject / Action / Scene / Style / Dialogue / Sounds / Negative), anti-cliché правила тона, audience cue под RU, self-check раскадровки
- `references/i2v-cost-lipsync-notes.md` — image-to-video: стоимость, липсинк, ограничения провайдеров
- `references/color-grading.md` — LUT (Kodak 2383) + teal-orange + film look + hald CLUT + color match
- `references/remotion-overlays.md` — соц-UI оверлеи (Instagram/Telegram chrome) React→alpha webm→composite
- `references/motion-graphics.md` — motion graphics 3 уровня: ffmpeg / movis / Manim
- `references/assembly.md` — FFmpeg cookbook (amix, concat, xfade, loudnorm, per-line VO, compression)
- `references/windows.md` — Windows-specific (subprocess encoding, PIL paths, Yandex multipart, кириллические paths)
- `references/case-studies.md` — verbatim-конфиги прошлых проектов

## Scripts

Полный состав `scripts/` — 16 файлов, все перечислены ниже.

- `scripts/run.py` — turnkey-оркестратор всего пайплайна (см. раздел TURNKEY выше)
- `scripts/direct_video.py` — **генерация напрямую у первоисточника, без посредников** (`models` / `gen` / `frame` / `plan`); ровно главный принцип экономии этого хаба — начинай с него
- `scripts/runway_client.py` — Python class `RunwayClient` (mig из `runway-api/scripts/`); `token-status` проверяет срок JWT офлайн, версия Seedance определяется автоматически через `/v1/profile/features`
- `scripts/runway_mcp.py` — MCP server обёртка (8 runway_* tools); в `get_client()` стоит гейт на просроченный токен — отказ приходит сразу и по-человечески, а не 401 из середины генерации
- `scripts/veo_runner.py` · `scripts/veo_image_to_video.py` — Veo t2v и i2v
- `scripts/nano_banana_keyframes.py` — батч keyframes (Nano/Gemini)
- `scripts/broll_runner.py` — B-roll пачкой
- `scripts/elevenlabs_voiceover.py` · `scripts/elevenlabs_music.py` · `scripts/lyria_music.py` — озвучка и музыка
- `scripts/captions_ass.py` — субтитры ASS
- `scripts/motion_graphics.py` — motion graphics (см. `references/motion-graphics.md`)
- `scripts/ffmpeg_assemble.py` — финальная сборка
- `scripts/climax_cut.py` — climax-aware нарезка длинного аудио под короткий ролик (Suno/Lyria → 60s)
- `scripts/extract_chat_session.py` — добыча знаний из прошлых JSONL-сессий по topic-regex (для апдейта скилла)

CLI quick check JWT (срок — офлайн, план — по сети):

```bash
python ~/.claude/skills/video-generation/scripts/runway_client.py token-status
python ~/.claude/skills/video-generation/scripts/runway_client.py profile
```
