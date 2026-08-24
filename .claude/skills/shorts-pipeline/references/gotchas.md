# Gotchas — shorts-pipeline

Hard-won knowledge from running this pipeline on 87 shorts. Read before debugging.

---

## 1. The «пиво» bug (Pivot → Beer 🍺)

**Симптом:** в русской речи произносится «pivot». SubMagic mistranscribes слово как «пиво» (beer), и при `magicBrolls=true` добавляет 🍺 emoji в видео.

**Что НЕ помогает:**
- ❌ `dictionary: ["pivot", "пайвот"]` в SubMagic API. Dictionary помогает только распознать **новые** термины в реальном аудио — не исправляет уже mistranscribed слова.
- ❌ Replace в готовом SubMagic-видео. У SubMagic API НЕТ `PATCH /projects/{id}` для редактирования caption-текста. Только Web UI.
- ❌ Перегенерация с `magicBrolls=false` — эмодзи уйдёт, но **текст caption всё равно** будет «пиво».
- ❌ Real-audio lipsync (real-audio mode). Даже если живой человек произносит «pivot» безупречно — SubMagic всё равно mistranscribes audio → caption «пиво».

**Что помогает:**
- ✅ **Replace в скрипте ДО TTS.** `trigger_word_check.py --fix` подменит `pivot` → `разворот концепции` ДО отправки в HeyGen. SubMagic больше не услышит трогающее слово.
- ✅ Default mode = `tts-clean` (а не голый `tts`).
- ✅ Если уже сгенерирован — **полная перегенерация с clean script**, без попыток патчить готовое видео.

**Полный список trigger-слов:** см. `scripts/trigger_word_check.py` (TRIGGERS list). Добавлять новые при обнаружении.

---

## 2. SubMagic `magicBrolls: false` обязателен

```python
body = {
    "templateName": "Hormozi 2",
    "magicBrolls": False,  # ← вот это
    "magicZooms": True,
    "cleanAudio": True,
    ...
}
```

**Почему:** `magicBrolls=true` добавляет emoji + GIF B-rolls по ключевым словам в caption. При любой mistranscription (например, «пиво») оно тут же появляется визуально. Лучше иметь голый caption, чем «пиво» 🍺.

`magicZooms=true` оставляем — это безобидные авто-зумы на акцентах.
`cleanAudio=true` оставляем — noise reduction, не трогает текст.

---

## 3. SubMagic Hormozi 2 — почему именно эта тема

- **Hormozi 2** — крупные жёлтые/белые субтитры, word-by-word highlight, читается на мобильных без VPN/peek.
- **Hormozi 1** — слишком агрессивный (большие зелёные subtitles), не подходит под спокойный нарратив.
- **Cinematic** — слишком тонкий, теряется на мобильных.

Если хочется другую тему — пробовать только после A/B на 3-5 шортсах.

---

## 4. HeyGen Avatar V — engine field обязателен

Аватар из `$HEYGEN_AVATAR_ID` должен быть **Avatar V eligible** (в кабинете HeyGen это видно на карточке аватара). Чтобы получить V-quality, а не legacy stale-look, нужно явно:

```python
"engine": {"type": "avatar_v"},
"aspect_ratio": "9:16",
"dimension": {"width": 1080, "height": 1920},
```

Без `engine.type=avatar_v` HeyGen падает на default engine → видео идёт со старым `look-around` артефактом губ.

---

## 5. HeyGen voice_id — два варианта

| voice_id | Описание | Когда брать |
|----------|----------|-------------|
| `$HEYGEN_VOICE_ID` | твой основной голос | TTS modes (default) |
| `--voice-id <второй id>` | запасной клон того же голоса | если основной звучит «роботом» на конкретном тексте |

У HeyGen клоны одного и того же голоса звучат по-разному в зависимости от поколения
движка: заведи два и держи id второго под рукой — это дешевле, чем перегенерировать
ролик и разбираться, «почему сегодня как робот».

В `real-audio` mode voice_id не нужен — передаём audio_asset_id.

---

## 6. Pricing — $0.0667/sec Avatar V

| Длина | $/short | 81 shorts |
|-------|---------|-----------|
| 20 sec | $1.33 | $108 |
| **30 sec** | **$2.00** | **$162** ← план |
| 45 sec | $3.00 | $243 |
| 60 sec | $4.00 | $324 |

**Wallet check:** `python heygen_avatar_v.py --check-wallet`. Держи на кошельке 2-3× от оценки пакета: перегенерация из-за слабого хука — обычное дело, а HeyGen списывает за каждый отрисованный ролик.

⚠️ **Превышение длительности TTS** = реальный rip-off. Скрипт `script.split()` ~75 слов = ~30 sec при 150wpm. Длиннее — урезай в скрипте, не растягивай TTS speed=0.85.

---

## 7. SubMagic вход — HeyGen signed URL напрямую

**НЕ нужно** скачивать HeyGen mp4 и перезаливать в SubMagic. SubMagic поддерживает `videoUrl` с public URL — HeyGen signed URL работает.

```python
submagic_create(heygen_url, title)  # signed URL прямо от HeyGen
```

Экономит 100-300 МБ трафика на short.

---

## 8. SubMagic — `directUrl` vs `downloadUrl` vs `outputUrl`

API ответ нестабилен в названии поля для готового видео. Чекать в порядке приоритета:

```python
url = (j.get('downloadUrl')
       or j.get('download_url')
       or j.get('outputUrl')
       or j.get('directUrl'))
```

---

## 9. Cleanup operations — массовое удаление

**Production stats (May 2026):**
- 44 шортса удалено за одну сессию (`--threshold 100`, criteria: <100 views >14d OR 0 views >7d)
- 401 шорт остался, median 732 views (с 707 поднялось — ушли «нулёвки»)
- YT quota: каждое `videos.delete` = 50 quota. Дневной лимит 10K → max 200 deletes/day

**Порядок:**
1. `inventory.py` — обновить `all_shorts.json` + `cleanup_candidates.json`
2. `cleanup.py --action plan` — посмотреть кандидатов
3. `cleanup.py --action delete --yes --limit 50` — удалить (батчем до quota)
4. Если ходит quotaExceeded — `progress.json` сохранён, на следующий день продолжишь

⚠️ Шаг 1 нельзя пропускать, и это проверяется кодом: `delete`/`delete-old` отказываются
работать по снимку старше 24 часов. Критерий «0 просмотров старше 7 дней» верен только на
момент `inventory.py` — за сутки ролик может залететь, а `videos.delete` необратим.
`--yes` тоже обязателен: раньше `--action delete` начинал сносить сразу, без вопроса.

---

## 10. YT API thumbnail upload — 50 quota/call

`thumb_upload.py` грузит обложки. 50 quota × 100 thumbs = 5K quota. Параллельно с delete (50 ea) или description update (50 ea) — легко выжрать дневные 10K за 100 операций.

**Безопасный paint:** 50-100 thumbs/day, остальное на следующий день. Progress в `_yt_shorts_thumbs_done.json`.

---

## 11. Cleanup state files (где лежит прогресс)

Все — внутри `$SHORTS_HOME` (умолчание `./shorts-pipeline`), имена заданы в `scripts/config.py`:

| Файл | Что |
|------|-----|
| `channel_shorts.json` | Полный snapshot канала (видео id, title, views) |
| `cleanup_candidates.json` | Список к удалению (output `inventory.py`) |
| `cleanup_progress.json` | `{"deleted": [...], "updated": [...]}` |
| `thumbs_done.json` | Залитые thumbnails (список id) |
| `analysis.json` | GPT-анализ SRT |
| `out/state.json` | Pipeline state — idempotent re-run |

Если очень нужно начать с нуля — удали соответствующий json.

---

## 12. Trigger-word check не ловит транслитерацию

Например «пайвот» (русскими буквами) ловится — добавлено в TRIGGERS. Но если кто-то пишет «п-и-в-о-т» через дефис или «pıvot» с турецкой ı — regex `\b...\b` не сработает. Чинить вручную через `--list` + расширение TRIGGERS.

---

## 13. Idempotency state.json — единственный источник истины

Все стадии пайплайна (HeyGen create, HeyGen wait, SubMagic create, SubMagic wait, download, cover) пишут в `state.json` по ходу. Падение посередине → следующий запуск продолжает с того же места.

**Don't delete `state.json` lightly** — потеряешь HeyGen `video_id` и заплатишь второй раз за тот же короткий.

Поле `heygen_video_id` до 2026-08-22 обещалось этим файлом и docstring'ом, но кодом
**никогда не записывалось**. Теперь пишется, и при падении после создания ролика печатается
`!! ОПЛАЧЕНО, НО НЕ ЗАБРАНО: video_id=…` — следующий запуск подхватывает готовое видео
(`heygen_avatar_v.py --video-id <id>`) вместо второй оплаты.

---

## 16. HeyGen signed URL нельзя брать «последней строкой stdout» (чинено 2026-08-22)

`full_pipeline.heygen_run()` парсил вывод раннера как `lines[-1]`. Но раннер вызывается с
`--out` И `--print-url`, а после ссылки печатает ещё `→ download to …` и `saved: …mp4 (NNNKB)`.
В `state.json` уезжала строка `saved: C:\…mp4 (4KB)`, она же уходила в SubMagic как `videoUrl`.

Цена ошибки: HeyGen к этому моменту уже отрисовал ролик ($2), SubMagic отбивал запрос,
batch-цикл печатал `FAIL` и шёл дальше — 81 ролик × $2 при нулевом выходе. Повторный запуск
не спасал: `heygen_url` в state уже непустой → ветка «✓ HeyGen cached» → тот же мусор в SubMagic.

Контракт теперь явный, метками:

```
VIDEO_ID=<id>       сразу после создания (= чек об оплате)
SIGNED_URL=<url>    после готовности
```

Нет метки `SIGNED_URL=` → `full_pipeline` падает громко, а не подставляет случайную строку.

---

## 14. Шортсы с `keep:false` — НЕ виралят даже после re-script

GPT-4o-mini в `analyze_srt.py` маркирует `keep:false` если SRT-фрагмент бессвязный или вырван из середины фразы без контекста. **Не пытайся прогонять их через pipeline вручную** — script.build_script даст бессвязный hook.

87 → 81 viable (`keep:true`) — 6 шортсов сразу в мусор. Это нормально.

---

## 15. analyze_srt.py использует GPT-4.1-mini

Скрипту нужен `OPENAI_API_KEY` (окружение или `~/.claude/.credentials.master.env` — см. `scripts/config.py`). Модель — дешёвая mini-линейка, ~$0.0005 за ролик; 87 нарезок ≈ $0.05 на анализ. Запускать по мере появления новых SRT в `$SHORTS_SOURCE/`.
