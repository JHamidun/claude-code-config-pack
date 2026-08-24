---
name: shorts-pipeline
description: "YouTube Shorts с AI-аватаром: SRT-нарезка → HeyGen Avatar V → SubMagic → обложка → YT. Триггеры: «нарежь шортсы», «шорт из вебинара». НЕ субтитры к чужому видео→submagic."
---

# YouTube Shorts Pipeline (вебинар → shorts с твоим аватаром)

Конвейер для СВОЕГО канала: нарезанные фрагменты вебинара (SRT + MP4) превращаются в
виральные вертикальные shorts через HeyGen Avatar V + SubMagic, с обложкой и загрузкой.
Канал нигде не задаётся именем — он определяется твоим OAuth-токеном (`mine=True`).

## Что понадобится

| Что | Платно | Где взять | Без этого |
|---|---|---|---|
| `HEYGEN_API_KEY` | **да, ~$0.0667/сек** → ~$2 за 30-секундный ролик | app.heygen.com → Settings → API | нет генерации видео вообще |
| `HEYGEN_AVATAR_ID` | нужен свой обученный аватар (Avatar V eligible) | HeyGen → Avatars → Copy ID | нечего отрисовывать |
| `HEYGEN_VOICE_ID` | клон голоса — отдельная платная опция HeyGen | HeyGen → Voices → Copy ID | нечем озвучивать TTS-режимы |
| `SUBMAGIC_API_KEY` | да, ~$25/мес | submagic.co → платный план → API | нет субтитров и зумов (шаг 4) |
| `OPENAI_API_KEY` | да, копейки: ~$0.0005 за ролик | platform.openai.com/api-keys | нет анализа SRT (шаг 1) |
| YouTube OAuth-токен | нет | Google Cloud Console → YouTube Data API v3 | нет inventory/cleanup/stats/обложек |
| `pip install -r scripts/requirements.txt` | нет | — | — |

**Прикидка бюджета до старта:** пакет из 81 ролика ≈ **$162** только HeyGen.
Поэтому `--batch`/`--all` печатают оценку и отказываются работать без `--yes`
и при превышении `--max-cost` (умолчание $200). Баланс кошелька:
`heygen_avatar_v.py --check-wallet`.

## Настройка путей и бренда

Всё, что раньше было захардкожено, живёт в `scripts/config.py` и читается из окружения:

```bash
export SHORTS_HOME=~/shorts          # рабочий каталог: analysis.json, state, обложки, выход
export SHORTS_SOURCE=~/cuts          # нарезка: <SHORTS_SOURCE>/<video_id>/short_NN.srt + .mp4
export SHORTS_BRAND="МОЙ КАНАЛ"      # подпись на обложке; пусто — подписи не будет
export SHORTS_HASHTAGS="#тег1 #тег2" # хвост для описаний; пусто — режим hashtags откажет
export YOUTUBE_TOKEN_FILE=~/.claude/.youtube-oauth-token.json   # умолчание
```

Умолчание `SHORTS_HOME` — `./shorts-pipeline` в текущем каталоге. Ключи берутся из
окружения, а если рядом лежит `~/.claude/.credentials.master.env` — то и оттуда
(шаблон: `~/.claude/templates/.credentials.master.env.example`).

## Когда использовать

- «нарежь шортсы из вебинара»
- «прогони пакет нарезок через аватар»
- «сделай новый shorts со мной в кадре»
- «hook formula → re-script → новый ролик»
- «найди trigger-слова в скрипте»
- «удали мусорные шортсы с канала»

---

## TL;DR — типичные команды

```bash
# Шаг 0 — проверь баланс HeyGen (≥ $5 на один ролик, ~$165 на пакет из 81)
python ~/.claude/skills/shorts-pipeline/scripts/heygen_avatar_v.py --check-wallet

# Шаг 1 — нарезка SRT в фабричной папке + GPT анализ
python ~/.claude/skills/shorts-pipeline/scripts/analyze_srt.py

# Шаг 2 — сделать один shorts из конкретного key (mode tts-clean — default)
python ~/.claude/skills/shorts-pipeline/scripts/full_pipeline.py 0HCAhzgS27Y/short_01

# Шаг 3 — batch первых 5 viable (пакет платный → --yes обязателен, сперва печатается оценка)
python ~/.claude/skills/shorts-pipeline/scripts/full_pipeline.py --batch 5 --mode tts-clean --yes

# Шаг 4 — весь пакет (на сутки работы HeyGen/SubMagic); 81 ролик ≈ $162
python ~/.claude/skills/shorts-pipeline/scripts/full_pipeline.py --all --mode tts-clean --yes

# Mode real-audio (свой живой голос вместо TTS) — нужна папка с mp3 на каждый key
python ~/.claude/skills/shorts-pipeline/scripts/full_pipeline.py --all --mode real-audio --audio-dir ~/voices/ --yes

# Cleanup канала (удаление необратимо → снимок не старше 24 ч + --yes)
python ~/.claude/skills/shorts-pipeline/scripts/inventory.py
python ~/.claude/skills/shorts-pipeline/scripts/cleanup.py --action plan
python ~/.claude/skills/shorts-pipeline/scripts/cleanup.py --action delete --yes --limit 50

# Stats канала
python ~/.claude/skills/shorts-pipeline/scripts/stats.py
```

---

## Pipeline (5 этапов)

```
┌─────────┐   ┌──────────────┐   ┌───────────────────┐   ┌──────────────┐   ┌──────────┐
│   SRT   │→  │ analyze_srt  │→  │ trigger_word_check│→  │   HeyGen     │→  │ SubMagic │→ cover_gen → upload
│ webinar │   │  (GPT-4.1)   │   │  (anti-«пиво»)    │   │  Avatar V    │   │ Hormozi2 │
│ cuts    │   │  hook,title  │   │  pivot→разворот   │   │  9:16 1080p  │   │ magicBr= │
│         │   │  loop_close  │   │                   │   │  $0.0667/sec │   │  FALSE   │
└─────────┘   └──────────────┘   └───────────────────┘   └──────────────┘   └──────────┘
```

### Stage 1 — SRT analysis (`analyze_srt.py`)

GPT-модель читает каждый `.srt` в `$SHORTS_SOURCE/<video_id>/short_NN.srt` и возвращает JSON:

```json
{
  "topic": "...", "gist": "...", "keep": true,
  "hook_formula": "Contradiction Hook",
  "hook_3s": "переписанные первые 3 сек",
  "title": "<40 chars curiosity-gap",
  "on_screen_text": "3-5 СЛОВ КРУПНО",
  "loop_close": "...последняя фраза, замыкающая на hook",
  "tags": "тег1,тег2,..."
}
```

Output: `$SHORTS_HOME/analysis.json` (инкрементальный — повторный запуск пропускает уже проанализированные).

Cost: ~$0.0005 за ролик. Пакет на 87 нарезок ≈ $0.05.

### Stage 2 — Trigger-word check (`trigger_word_check.py`)

Сканирует скрипт на «опасные» термины ДО отправки в HeyGen TTS:

| Trigger | Заменяется на | Почему |
|---------|---------------|--------|
| `pivot` | `разворот концепции` | TTS слышит как «пиво» → SubMagic ставит 🍺 |
| `roadmap` | `дорожная карта` | TTS читает «р-о-а-д-м-ап» побуквенно |
| `pipeline` | `пайплайн` | избегаем «пипелайн» от автокоррекции |
| `launch` | `запуск` | TTS «лаунч» неестественен |
| `fine-tuning` | `дообучение` | смесь языков ломает TTS |
| `CustDev` | `кастдев` | TTS «С-Ц-У-С-Т-Д-Е-В» побуквенно |
| `PMF` | `product-market fit` | три буквы плохо звучат |
| `ROI` | `РОИ` | аббревиатура — лучше расшифровать |

CLI:
```bash
python trigger_word_check.py script.txt          # scan, exit 1 if found
python trigger_word_check.py script.txt --fix    # auto-replace → script.clean.txt
python trigger_word_check.py - --fix             # stdin → stdout (для пайпа)
python trigger_word_check.py - --list            # показать все правила (path обязателен даже здесь; «-» = заглушка, stdin не читается)
```

### Stage 3 — HeyGen Avatar V (`heygen_avatar_v.py`) — 3 режима

| Mode | Описание | Когда брать |
|------|----------|-------------|
| `tts` | HeyGen Russian TTS на скрипт. Быстро, дёшево. Читает «pivot»→«пиво». | Если уверен в чистоте скрипта. Не рекомендуется. |
| `tts-clean` | trigger_word_check.py --fix → HeyGen TTS. **Default.** | 95% случаев. Безопасный TTS. |
| `real-audio` | Загрузить заранее записанный mp3 → `/v3/assets` → lipsync Avatar V. | Когда нужен твой живой голос, а не TTS (premium short). |

**HeyGen config (всегда):**

```python
{
  "video_inputs": [{
    "character": {"type": "avatar", "avatar_id": "<$HEYGEN_AVATAR_ID>", "avatar_style": "normal"},
    "voice": {...},
  }],
  "dimension": {"width": 1080, "height": 1920},  # 9:16, 1080p
  "aspect_ratio": "9:16",
  "engine": {"type": "avatar_v"}  # КРИТИЧНО — без этого падает на legacy
}
```

**Avatar/voice IDs — только свои, дефолта в коде нет:**

| Field | Откуда | Notes |
|-------|--------|-------|
| `avatar_id` | `$HEYGEN_AVATAR_ID` — HeyGen → Avatars → Copy ID | аватар должен быть **Avatar V eligible**, иначе качество откатится к legacy |
| `voice_id` | `$HEYGEN_VOICE_ID` — HeyGen → Voices → Copy ID | дефолтный голос генерации |
| второй голос | `--voice-id <id>` явным аргументом | пригодится, если основной звучит «роботом»: держи запасной id под рукой |

Чужой `avatar_id` в коде — не мелочь: он либо не пройдёт авторизацию, либо отрисует
чужое лицо за твои деньги. Поэтому скрипты падают с внятным отказом, а не подставляют
что-то по умолчанию.

**Pricing:**

```
$0.0667 / sec   →   $2.00 per 30-sec short   →   ~$162 за пакет из 81 ролика
Держи на кошельке 2-3× от оценки пакета: перегенерация из-за плохого хука — обычное дело.
Баланс: heygen_avatar_v.py --check-wallet
```

Mode `real-audio` стоит столько же — HeyGen биллит per-second Avatar V независимо от типа voice.

### Stage 4 — SubMagic (в конвейере — `full_pipeline.py`; `submagic_process.py` — одиночный прогон)

> `submagic_process.py` конвейерным этапом не является: это отдельный прогон «есть готовое видео
> по URL — нужны только субтитры и зумы». Раньше он был непараметризованным пробником с зашитым
> чужим названием проекта и одним и тем же путём выхода (второй запуск затирал первый) и передавал
> запрещённый `dictionary`. Переписан: `--title`, `--out`, `--language`, `--template` — аргументы,
> `dictionary` убран совсем. Для пакетной работы всё равно `full_pipeline.py`.

Captions + zooms + clean audio. **КРИТИЧЕСКАЯ настройка `magicBrolls=False`** — иначе SubMagic ставит emoji 🍺/🚀/💰 по mistranscribed словам.

> **Граница с навыком `submagic` — SubMagic зовут оба, и это не дубль.** Там **вендорский
> API-справочник**: все параметры, Magic Clips, публикация, любое видео на любом языке, решения
> по настройкам ещё не приняты. Здесь SubMagic — **один этап зафиксированного конвейера канала**,
> где всё уже решено: свой аватар, шаблон Hormozi 2, своя обложка, свой state.json, RU-язык.
> Признак в формулировке: **назвали чужой файл или ролик «поставь субтитры / нарежь на клипы» →
> `submagic`; сказали «шортс со мной / нарежь шортсы из вебинара» → сюда.**
>
> **`magicBrolls` = `False` везде.** Значение когда-то расходилось между навыком `submagic`
> и скриптами этого конвейера; приведено к `False` — это и документированный дефолт самого API,
> и обязательное значение для русской дорожки (разбор инцидента «pivot»→«пиво»→🍺 в
> `references/gotchas.md` §1–2). Включать только явно и только на транскрипте, прочитанном глазами.

```python
{
  "title": "...",
  "language": "ru",
  "videoUrl": heygen_signed_url,   # НЕ нужно скачивать-перезаливать
  "templateName": "Hormozi 2",
  "magicZooms": True,
  "magicBrolls": False,            # ← КРИТИЧНО (см. gotchas)
  "cleanAudio": True
}
```

**Почему НЕ `dictionary`:** `["pivot", "пайвот"]` в SubMagic dictionary помогает только распознать НОВЫЕ слова. Уже mistranscribed `pivot→пиво` оно НЕ исправит. Единственное решение — clean script ДО TTS.

**SubMagic НЕ имеет** `PATCH /projects/{id}` для редактирования caption-текста. Если поймали «пиво» — только перегенерация с clean script. См. `references/gotchas.md`.

### Stage 5 — Cover (`cover_gen.py`)

PIL-рендер 1080×1920: navy gradient + matrix dots + headline + подпись бренда из `$SHORTS_BRAND`
(переменная не задана — подписи просто нет; чужое имя на своей обложке хуже, чем её отсутствие).

```bash
python cover_gen.py --title "$4M за 10 дней" --out cover.png
python cover_gen.py --bulk $SHORTS_HOME/analysis.json --out-dir covers/
```

Template: `templates/cover_navy.py` (функция `render_shorts_cover(title, out_path)`).

### Stage 6 — YT upload (`thumb_upload.py` + ручной upload видео)

`thumb_upload.py` — только обложки на уже залитые ролики. Сам upload видео — вручную через YT Studio
либо своим скриптом на YouTube Data API v3 (`videos.insert`), тем же токеном, что и остальные шаги.

YT quota: thumbnail = 50/upload. 100/day реально, выше — quotaExceeded.

---

## Hook formulas

GPT в `analyze_srt.py` выбирает одну из 7 формул и кладёт её имя в поле `hook_formula`.

| Формула | Когда |
|---------|-------|
| **Curiosity Gap** | Сенсация без раскрытия |
| **Mistake Callout** | Обучающий контент |
| **Fast Result** | Конкретный quick-win |
| **Direct Question** | Completion bias 5-7 сек |
| **Mid-Action Open** | Начало с 30% точки |
| **Contradiction** | Когнитивный диссонанс |
| **Visual Surprise** | Visual-first контент |

Примеры под каждую формулу и полный guide — в навыке `viral-shorts-playbook` (§1),
если он есть в твоей сборке. Дублировать их сюда нельзя: два набора примеров расходятся
молча, и правка в одном месте не доезжает до второго.

⚠️ **Имена формул — словарь скрипта, и его никто не проверяет.** Список выше — тот,
что перечислен в промпте `analyze_srt.py` (строки 41-47); оттуда GPT кладёт имя в
`hook_formula`. Валидации в коде НЕТ — чужое название молча уедет в analysis.json и
дальше по пайплайну, никто не упадёт. Поэтому словарь держим один — тот, что выше.
Встретишь в другом источнике иные названия (`Direct Question on-screen`, `Visual Pattern
Break` — то же самое другими словами) — приводи к списку выше, а не заводи второй словарь.

Там же известное расхождение внутри самого скрипта: строка 6 пишет `Mid-Action`,
строка 45 — `Mid-Action Open`. Канон для этого поля — `Mid-Action Open`.

---

## Loop technique + 30% Rule — что делает этот пайплайн

Теория обеих техник (loop, abrupt ending, 30% Rule, визуальный стиль) — в навыке
`viral-shorts-playbook`, §2-4. Ниже — только то, что этот конвейер реально исполняет,
и контракты полей: без соседнего навыка он работает.

**Loop.** Поле `loop_close` из `analyze_srt.py` — финальная фраза, замыкающая на хук
(audio + visual). Финальный фрейм режется тем же crop, что и первый, иначе петля
видна и спайка retention не будет.

**Abrupt ending — обязательно на монтаже:**
- Резать аудио + видео на 2-3 фонеме незаконченного слова
- БЕЗ fade-out, чистый hard-cut
- НЕ «спасибо за просмотр» / outro — убивает average % viewed

**30% Rule на входе.** GPT в `analyze_srt.py` переписывает первые 3 сек
**обязательно**: оригинальный SRT почти всегда начинается со «slow build»
(«Привет, друзья, сегодня поговорим…») — это убийственный паттерн, из-за него
ролик не проходит порог свайпов и охват режется.

---

## Cleanup operations

Замер на живом канале (один прогон чистки):

| Метрика | Было | Стало |
|---------|------|-------|
| Шортсов на канале | 445 | 401 |
| Удалено | — | 44 |
| Median views | 707 | 732 |

Critera для удаления (см. `inventory.py`):
- `<100 views >14 days old` — давно лежит, не залетело
- `0 views >7 days old` — алгоритм даже не показал
- `'Пустой транскрипт'` / `untitled` / `draft` — мусор
- Дубликаты по title — оставляем highest-views

**Quota:** YT `videos.delete` = 50 quota. 200 deletes/day max при 10K daily quota.

```bash
python inventory.py                                 # snapshot канала + candidates
python cleanup.py --action plan                     # показать что удалить
python cleanup.py --action delete --yes --limit 50  # удалить (батчем)
```

Порядок обязателен: `inventory.py` → `plan` → `delete --yes`. Снимок старше 24 часов
скрипт не примет — просмотры в нём уже неверные, а удаление роликов необратимо.

Progress в `$SHORTS_HOME/cleanup_progress.json` — quotaExceeded → продолжишь завтра.

---

## Cost calculator (HeyGen + SubMagic)

```
HeyGen Avatar V:  $0.0667 / sec  (talking head)
30-sec short:    $2.00 HeyGen
81 shorts × 30s: ~$162 HeyGen
Wallet target:   2-3× от оценки пакета — перегенерация из-за слабого хука обычна
Проверить:       heygen_avatar_v.py --check-wallet

SubMagic:        зависит от плана (шаблон Hormozi 2 — стандарт)
                 ~$25/month, unlimited shorts.
```

⚠️ Не растягивай TTS длительность — HeyGen биллит каждую секунду. 75 слов = ~30 сек, дальше урезай скрипт, не TTS speed.

---

## CLI reference

### `analyze_srt.py`
Анализирует все `.srt` в `$SHORTS_SOURCE/` через GPT. Каталога нет — скрипт отказывает
с подсказкой, какую переменную задать, а не падает трейсбеком.

```bash
python analyze_srt.py            # incremental — пропускает уже проанализированные
```

### `trigger_word_check.py`
```bash
python trigger_word_check.py script.txt              # scan only, exit 1 if found
python trigger_word_check.py script.txt --fix        # write script.clean.txt
echo "pivot к новой модели" | python trigger_word_check.py - --fix  # stdin pipe
python trigger_word_check.py - --list                # show all rules (позиционный path обязателен всегда)
```

### `heygen_avatar_v.py`
```bash
python heygen_avatar_v.py --check-wallet
python heygen_avatar_v.py --mode tts        --text "..."          --out raw.mp4
python heygen_avatar_v.py --mode tts-clean  --text-file s.txt     --out raw.mp4
python heygen_avatar_v.py --mode real-audio --audio v.mp3         --out raw.mp4
python heygen_avatar_v.py --mode tts --text "..." --voice-id <второй voice_id>  # запасной голос
python heygen_avatar_v.py --video-id <id> --out raw.mp4   # забрать УЖЕ оплаченный ролик
```

Stdout-контракт для вызывающих: `VIDEO_ID=<id>` (сразу после создания — это чек об оплате)
и `SIGNED_URL=<url>` (после готовности). Парсить надо метки, а не «последнюю строку»: при
`--out` после ссылки печатаются ещё две строки про скачивание.

### `submagic_process.py` — одиночный прогон готового видео через SubMagic
```bash
python submagic_process.py <video_url> --title "Название" --out final.mp4
python submagic_process.py <video_url>          # выход: $SHORTS_HOME/out/<project_id>.mp4
```
Принимает прямой URL (в т.ч. signed URL от HeyGen — перезаливать не надо). Для пакета — `full_pipeline.py`.

### `cover_gen.py`
```bash
python cover_gen.py --title "Заголовок" --out cover.png
python cover_gen.py --bulk $SHORTS_HOME/analysis.json --out-dir covers/
python cover_gen.py --from-channel $SHORTS_HOME/channel_shorts.json --out-dir covers/
```

### `full_pipeline.py`
```bash
python full_pipeline.py <key>                                # one short (гейт не нужен)
python full_pipeline.py --batch 5 --mode tts-clean --yes     # first 5 viable
python full_pipeline.py --all --mode tts-clean --yes         # весь пакет; 81 ролик ≈ $162
python full_pipeline.py --all --mode real-audio --audio-dir voices/ --yes
python full_pipeline.py <key> --out-dir custom/              # custom output
python full_pipeline.py --all --yes --max-cost 400           # поднять потолок осознанно
```

Гейт пакета (`--batch`/`--all`): проверяются непустые `HEYGEN_API_KEY` и `SUBMAGIC_API_KEY`
(иначе HeyGen спишет, а принять результат будет некому), печатается оценка `N × ~$2`,
отказ при превышении `--max-cost` (умолчание $200) и отказ без `--yes`. `--max-fails`
(умолчание 3) рвёт цикл после трёх провалов подряд: системная поломка повторится на
каждом ролике, а HeyGen за каждый уже спишет.

State (`state.json` в `--out-dir`) — idempotent re-runs. Если упало посередине → следующий
запуск продолжает. В state пишется `heygen_video_id`: если ролик уже отрисован (= оплачен),
но не забран, следующий запуск подхватывает его вместо второй оплаты.

### `inventory.py` / `cleanup.py` / `stats.py` / `thumb_upload.py`
```bash
python inventory.py                                  # snapshot канала + candidates
python cleanup.py --action plan                      # show candidates
python cleanup.py --action delete --yes --limit 50   # delete using inventory candidates
python cleanup.py --action hashtags --limit 200      # add hashtags batch
python stats.py                                      # top-15 + median + recent 14d
python thumb_upload.py 100                           # bulk upload 100 covers
```

`delete`/`delete-old` отказываются работать без `--yes` и по снимку старше 24 часов
(`--allow-stale`, если осознанно). Причина в критерии: «0 просмотров старше 7 дней» верно
только на момент `inventory.py`, за сутки ролик может залететь, а `videos.delete`
необратим. `--limit` теперь ограничивает и удаление, не только хэштеги.

---

## File layout

```
~/.claude/skills/shorts-pipeline/
├── SKILL.md                       # this file
├── scripts/
│   ├── config.py                  # ЕДИНАЯ настройка: пути, ключи, avatar/voice id, бренд
│   ├── analyze_srt.py             # SRT → analysis.json (GPT)
│   ├── trigger_word_check.py      # anti-«пиво» scanner
│   ├── heygen_avatar_v.py         # 3 modes (tts/tts-clean/real-audio)
│   ├── submagic_process.py        # SubMagic одиночным прогоном (параметризован)
│   ├── cover_gen.py               # CLI wrapper around PIL template
│   ├── full_pipeline.py           # orchestrator (all stages + state.json)
│   ├── inventory.py               # YT channel snapshot + cleanup candidates
│   ├── cleanup.py                 # delete + hashtags batch
│   ├── stats.py                   # channel performance snapshot
│   ├── thumb_upload.py            # bulk thumbnail upload
│   └── requirements.txt
├── templates/
│   └── cover_navy.py              # PIL navy gradient cover (1080×1920)
├── handoff/
│   └── analysis_example.json      # example output of analyze_srt.py
└── references/
    ├── rescript_examples.md       # 5 re-script examples (top-tier shorts)
    └── gotchas.md                 # «пиво» bug + 14 other gotchas
```

Виральная теория (hook formulas, 30% rule, loop, abrupt ending) здесь НЕ лежит — она
в навыке `viral-shorts-playbook`. Побайтовые копии тут когда-то были и разошлись с
оригиналом: два экземпляра одного research'а начинают советовать разное, причём молча.

---

## Что залетает и как публиковать

### Тематическая матрица (S/A/B/C-tier для AI/tech на русском)

| Tier | Topics | Avg views |
|------|--------|-----------|
| S | DeepSeek, Elon Musk/xAI, NVIDIA | 15K-580K |
| A | OpenAI/GPT, Google/Gemini, Apple AI | 5K-30K |
| B | Business automation, AI tools, money | 2K-10K |
| C | Generic AI news, tutorials | <2K |

### 30% Rule + визуальный стиль

Overlay ≥60pt, smash cuts, Ken Burns, film grain, удержание до 25 секунд — подробно
в `viral-shorts-playbook`, §4. Здесь не дублируем сознательно.

### Publishing optimization

| Param | Best value |
|-------|-----------|
| Day | Friday > Wednesday |
| Time | 06:00-08:00 по времени основной аудитории (утренняя дорога) |
| Title | <40 chars, declarative, без вопроса |
| Hashtags | 4-6 штук: 2 широких по нише + 2 узких по теме ролика + свой брендовый (`$SHORTS_HASHTAGS`) |
| Thumbnail | navy gradient cover (PIL) |

Полный guide — навык `viral-shorts-playbook`.

---

## Gotchas → `references/gotchas.md`

15 hard-won правил. Главные:

1. **«пиво» bug** — НЕ patch'ится через SubMagic dictionary. Только clean script ДО TTS.
2. `magicBrolls: false` — обязательно. Иначе emoji 🍺 на mistranscribed.
3. HeyGen `engine.type=avatar_v` — без этого качество = legacy stale-look.
4. SubMagic вход — HeyGen signed URL напрямую, не нужен re-upload.
5. SubMagic нет PATCH для caption edit — только полная перегенерация.
6. State.json — единственный источник правды для idempotency. Не удаляй без причины.

---

## Связанные скиллы

- **`heygen`** — общий HeyGen-обёртка (здесь — специализированный код под этот конвейер)
- **`elevenlabs`** — если переходим на ElevenLabs TTS (текущий pipeline использует HeyGen внутренний TTS)
- **`youtube-analytics`** — что работает на канале, какие топики залетают
- **`video-editor`** — FFmpeg монтаж (если нужны post-effects к SubMagic-output)
- **`trend-engine`** — найти что обсуждают сегодня → новые темы для shorts
