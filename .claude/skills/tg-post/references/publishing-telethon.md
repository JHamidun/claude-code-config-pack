# Публикация в Telegram: отложка и Telethon

Полная механика доставки: отложка таймером на всегда включённом хосте, команды запуска и отмены, передача токена файлом, проверка результата, планирование через Telethon. Читай, когда пост согласован и идёт публикация. Правило «сначала апрув» действует всегда и лежит в `SKILL.md`.

## Оглавление

- ПЛАНИРОВАНИЕ И ПУБЛИКАЦИЯ В TELEGRAM (Telethon) ⭐
- Что умеет аккаунт с Telegram Premium
- Грабли Telethon 1.39 (почему нужен модуль, а не голый html_parse)
- Минимальный рецепт (карусель 18:00 + видео-догон 18:05)
- Личка / multi-message + markdown-конструктор раскрывашек (2026-06-13)
- Стандартный футер канала (3 ссылки) — константа `FOOTER_HTML`
- Концовка-голосование реакциями (паттерн)

---

### Отложка

**Bot API не умеет отложенные сообщения** — параметра `schedule_date` нет. Расписание через Telethon возможно только от аккаунта, а rich умеет только бот.


Решение: таймер на своём всегда включённом хосте (`ssh "$SERVER"`) — работает круглосуточно, ноутбук не нужен.

```bash
# на сервере /root/scheduled/
sleep <секунд до цели>
set -a; . /root/scheduled/tok.env; set +a     # токен из файла с правами 600
python3 tg_bot.py --token $TG_BOT_TOKEN rich --to @your_channel --md-file post.md
```

Запуск: `setsid nohup ./post_at_XXXX.sh > /dev/null 2>&1 < /dev/null &` — переживает отключение сессии.

**Токен передавать файлом, не аргументом:** в аргументах он виден в списке процессов всё время ожидания.

Проверить: `pgrep -af post_at_` · отменить: `pkill -f post_at_` · результат: `tail -3 /root/scheduled/post.log`

Время публикации: 7:12–7:22 МСК показали себя хорошо.


## ПЛАНИРОВАНИЕ И ПУБЛИКАЦИЯ В TELEGRAM (Telethon) ⭐

> Обновлено 2026-05-29. Готовый рабочий модуль: **`scripts/tg_rich_post.py`** (в папке этого скилла).
> `tg_client.py` НЕ умеет: альбомы (нет `send-album`), спойлеры, раскрывающиеся цитаты. Для богатых постов с каруселью — этот модуль.
>
> **Кампания «новость под ключ» (пост + карусель + сторис 9:16 + видео, одной цепочкой):**
> → `references/launch-campaign.md` — анатомия поста (хук → тезис → раскрывашки → цена+ссылка →
> рефлексия со спойлером → афоризм → голосование+CTA → футер 3-ссылки → хештеги), спойлер-логика
> (блюрить punchline, НЕ тезис), концовка-голосование, точные end-to-end команды.
> Готовый end-to-end пример собери сам из «Минимального рецепта» ниже — он полный.

### Что умеет аккаунт с Telegram Premium (без Premium лимиты жёстче)

- **Лимит подписи ~4096 символов** (Premium), не 1024. Длинный богатый пост влезает прямо в подпись альбома.
- **Текст без медиа от аккаунта проходит и за 5000+** знаков одним сообщением; подпись к медиа — жёстко 4096. Пост длиннее — либо без картинки, либо rich через бота (32 768).
- Обычный пост **не умеет таблиц и раскрывашек** — за ними в РЕЖИМ RICH.
- **Альбом ≤ 10 элементов**, фото И видео можно мешать в одной медиагруппе. Подпись — на первом элементе.
- Все фишки форматирования: жирный, ссылки, цитаты, **раскрывающиеся списки** (collapsed blockquote), **спойлер** (блюр).
- **Карусельные разборы/обзоры (review/roundup + карточки) — ВСЕГДА rich-формат, а не плоская «простыня».** Дважды посты-разборы выходили как стена абзацев с жирными подзаголовками — это провал. Дефолт по анатомии `references/launch-campaign.md`: хук → `<blockquote>`тезис → «детали в раскрывашках 👇» → по `<blockquote><b>КЕЙС N</b>…` (раскрывающийся) на каждый кейс → строка 3 ссылок → рефлексия с ОДНИМ спойлером (честный punchline, не тезис) → голосование 2-3 эмодзи → 3-ссылочный `FOOTER_HTML` → хештеги. **Весь пост — в ОДНУ подпись альбома (Premium ≤4096), без отдельного сообщения-«продолжения».** Перед планированием валидируй `build_caption` (нет исключения, ≤4096, спойлер найден).

### Грабли Telethon 1.39 (почему нужен модуль, а не голый html_parse)

| Фича | Тег | Парсит `html_parse`? | Как делать |
|------|-----|----------------------|-----------|
| Жирный / ссылка / код / цитата | `<b> <a href> <code> <blockquote>` | ✅ | как есть |
| **Раскрывающийся список** | `<blockquote expandable>` | ❌ флаг игнорится | после парсинга `e.collapsed = True` на нужных `MessageEntityBlockquote` |
| **Спойлер (блюр)** | `<spoiler>`, `<tg-spoiler>`, md `\|\|x\|\|` | ❌ entity не создаётся | вручную `MessageEntitySpoiler(offset,length)`, офсеты **UTF-16** = `len(s.encode('utf-16-le'))//2` |

- При `formatting_entities=` НЕ передавать `parse_mode=` (взаимоисключающи).
- `schedule=` — tz-aware datetime; строй в `MSK = timezone(timedelta(hours=3))`.
- **Никогда не удаляй чужие отложенные посты** — `list_scheduled()` только показывает.
- channel = `'your_channel'` (свой @username канала без собаки); сессия — файл `~/.claude/telegram_session`
  (создастся при первом входе); `TELETHON_API_ID` / `TELETHON_API_HASH` — свои, берутся на my.telegram.org → API development tools, кладутся в переменные окружения.
- Картинки карточек строит cards-creator → `cards-creator/scripts/render_cards.py`.

### Минимальный рецепт (карусель 18:00 + видео-догон 18:05)

```python
import asyncio; from datetime import datetime
import sys; sys.path.insert(0, os.path.expanduser('~/.claude/skills/tg-post/scripts'))
from tg_rich_post import client, schedule_album, schedule_media, list_scheduled, MSK, FOOTER_HTML

HTML = """Хук...
<blockquote>Цитата — остаётся обычной (первый blockquote).</blockquote>
<blockquote><b>📊 СПИСОК</b>
строка 1
строка 2</blockquote>
Оригинал — <a href="https://...">тут</a>.
Если честно: ФРАЗА_СПОЙЛЕРА_ДОСЛОВНО конец.

""" + FOOTER_HTML

async def main():
    c = client(); await c.start()
    await list_scheduled(c, 'your_channel')                       # отчёт, не удалять
    await schedule_album(c, 'your_channel',
        files=[f'png/series-{i:02d}.png' for i in range(1,10)],
        html=HTML, when=datetime(2026,5,29,18,0,tzinfo=MSK),
        spoilers=['ФРАЗА_СПОЙЛЕРА_ДОСЛОВНО'])    # 1-й blockquote = цитата, остальные раскрывающиеся
    await schedule_media(c, 'your_channel', 'C:/.../clip.mp4',
        when=datetime(2026,5,29,18,5,tzinfo=MSK), caption='Короткий коммент')
    await c.disconnect()
asyncio.run(main())
```

Верификация после планирования: `GetScheduledHistoryRequest` → у нужного msg.id проверь `collapsed` флаги блок-цитат, наличие `MessageEntitySpoiler` и `MessageEntityTextUrl`.

### Личка / multi-message + markdown-конструктор раскрывашек (2026-06-13)

> Кейс: подробный разбор отправляли **в личку** (не канал, не альбом). Анатомия из `launch-campaign.md` тут не подходит — другой контейнер, другие правила.

- **Сворачивание — ТОЛЬКО визуальное; лимит 4096/сообщение оно НЕ уменьшает.** Раскрывашка прячет текст под заголовок, но символы считаются полностью. Вывод: для длинного богатого контента в личке **НЕ ужимай текст, чтобы «влезло» — разбивай на несколько сообщений**, в каждом — свёрнутые блоки. (Реальная ошибка этой сессии: урезал разбор ради «2 сообщений» → потерял половину содержания; пришлось переслать полную версию.)
- **Свёрнутый blockquote показывает первую строку как тизер** → первой строкой блока делай явный жирный заголовок (`**🔴 Главное …**`).
- **Альтернатива HTML — markdown-конструктор** (когда не хочется писать HTML; удобно для ad-hoc личек). Парсишь markdown каждого куска отдельно и сшиваешь, сдвигая офсеты по UTF-16-курсору, на quote-куски вешаешь `MessageEntityBlockquote(collapsed=True)`:

```python
from telethon.extensions import markdown
from telethon.tl.types import MessageEntityBlockquote
u16 = lambda s: len(s.encode('utf-16-le')) // 2
def build(parts):                 # parts: [{'kind':'text'|'quote','md':..,'collapsed':True}]
    full, ents, cur = "", [], 0
    for i, p in enumerate(parts):
        clean, pe = markdown.parse(p['md'])
        for e in pe: e.offset += cur; ents.append(e)
        if p['kind'] == 'quote':
            ents.append(MessageEntityBlockquote(offset=cur, length=u16(clean),
                                                collapsed=p.get('collapsed', True)))
        full += clean; cur += u16(clean)
        if i != len(parts)-1: full += "\n\n"; cur += u16("\n\n")
    ents.sort(key=lambda e: e.offset)
    return full, ents
# await client.send_message(entity, full, formatting_entities=ents, link_preview=False)
```
Жирный/курсив **внутри** blockquote работают (перекрытие entity допустимо). При `formatting_entities=` markdown в тексте уже НЕ парсится — `full` должен быть clean.
- **`tg_client.py send`** (голый CLI) шлёт дефолтным markdown Telethon → **жирный/курсив/`код`/ссылки рендерятся**, а **blockquote / спойлер / подчёрк / зачёрк — НЕТ** (только entity вручную, см. выше). `>`-цитаты дефолтный парсер тоже не понимает.
- **Заменить уже отправленную серию в личке:** `await client.delete_messages(entity, [ids], revoke=True)` (revoke = удалить у обоих) → отправить заново. Это про СВОИ сообщения; чужие отложки не трогать (правило выше).

### Стандартный футер канала (3 ссылки) — константа `FOOTER_HTML`

Шаблон: подставь свои канал, бота и сайт (или убери лишние строки).
Значение живёт в `scripts/tg_rich_post.py` — правится там один раз.

```
⚡️ <Название канала> — t.me/your_channel
📲 <что даёт бот> — t.me/your_bot
📰 <что на сайте> — your-site.example.com
```

### Концовка-голосование реакциями (паттерн)

```
Что думаете?

🔥 — <вариант 1>
🤔 — <вариант 2>
🙌 — <вариант 3>

<вопрос к аудитории>? Делитесь в комментариях
```
Реакции и вопрос ВСЕГДА подгонять под тему конкретного поста — не копировать дословно с другого поста.

