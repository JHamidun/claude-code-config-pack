---
name: telegram-bot-toolkit
description: "Разработка Telegram-ботов: python-telegram-bot, Telethon, деплой; антипаттерн бот-воронки из TG Ads. Триггеры: «напиши бота», «deploy бота»."
keywords: telegram, bot, python-telegram-bot, telethon, scenes, middleware, webhooks, deployment, debugging, бот как коллектор, антипаттерн бот-воронки, бот из TG Ads, воронка через бот
---

# Telegram Bot Toolkit

Разработка, отладка и деплой Telegram-ботов на Python (python-telegram-bot,
Telethon).

> **Бота планируют как воронку из TG Ads?** Прочитай
> `references/tg-ads-bot-funnel.md` ДО написания кода: 80% бот-воронок из платного
> трафика убыточны, и правильный ответ — не «написать бота лучше», а поменять место
> бота в воронке (TG Ads → лендинг с регистрацией → бот для прогрева).
> Смежное: `telegram-ads-pro-ru`, `manychat-funnel-ru`.

## ConversationHandler: четыре поломки

Все четыре выглядят как «бот завис» и все четыре чинятся в объявлении хендлера.

1. **`per_user=True, per_chat=True`** — без них сцены разных юзеров лезут друг в
   друга, и баг проявляется только когда в боте больше одного человека, то есть на
   проде.
2. **`filters.TEXT & ~filters.COMMAND`** в состояниях. С голым `filters.TEXT`
   состояние съедает `/start` как обычный текст, и юзер не может выйти. Это и есть
   классическое «застрял в онбординге».
3. **Команды в `fallbacks`** (`/start`, `/cancel`) — аварийный выход из любого
   состояния. Без него единственный способ выйти — удалить чат.
4. **`per_message=False`**, если состояния ловят сообщения, а не callback-и.

## Порядок хендлеров

Группы обрабатываются по возрастанию, и порядок здесь не косметика: команда,
зарегистрированная после ConversationHandler, до неё просто не доходит.

```python
app.add_handler(MessageHandler(filters.ALL, log_all_updates), group=-1)   # видеть всё
app.add_handler(MessageHandler(filters.ALL, check_auth),      group=0)
app.add_handler(CommandHandler('start', start_command),       group=1)    # ДО conversation
app.add_handler(CommandHandler('help',  help_command),        group=1)
app.add_handler(conversation_handler,                          group=2)
app.add_handler(MessageHandler(filters.TEXT, unknown),        group=999)  # ловит остальное
```

## Callback queries

`await query.answer()` — **первой строкой** обработчика, до любой логики. Пока
callback не отвечен, у юзера крутится часик на кнопке, и он жмёт её ещё раз.

## Гонки и утечки

- **Критические секции** (баланс, платежи) — `asyncio.Lock` на `user_id`. Два
  быстрых сообщения от одного юзера обрабатываются параллельно, и списание
  проходит дважды.
- **`context.user_data.clear()`** при завершении conversation + периодическая
  чистка юзеров, у которых `last_seen` старше суток. Иначе в long-polling
  `user_data` растёт до перезапуска процесса.
- **`app.add_error_handler(...)`** обязателен: логировать с `exc_info=True` и
  ответить юзеру человеческим текстом с подсказкой `/start`. Без него ошибка
  выглядит как молчание бота.

## Деплой

- **Разработка** — `app.run_polling(allowed_updates=Update.ALL_TYPES)`.
- **Прод** — webhook: FastAPI-эндпоинт `POST /webhook`, внутри
  `Update.de_json(await request.json(), app.bot)` → `app.process_update(update)`,
  плюс `await app.bot.set_webhook(url=..., allowed_updates=Update.ALL_TYPES)`.
  Отдельный `GET /health` — для healthcheck контейнера.
- **Ограничения webhook.** Порты только 443, 80, 88, 8443; редиректы не
  поддерживаются, wildcard-сертификаты могут не работать. `secret_token` (1–256
  знаков `A-Za-z0-9_-`) приходит в заголовке `X-Telegram-Bot-Api-Secret-Token` —
  сверять его в эндпоинте. `max_connections` — от 1 до 100 (по умолчанию 40).
  `getUpdates` и webhook взаимоисключающи; необработанные апдейты Telegram хранит
  не дольше 24 часов.
- **Конфиг** — `pydantic_settings.BaseSettings` с `env_file=".env"`. Токен в коде
  не хранится никогда; в Docker передаётся через `environment`.

## Версии библиотек и новинки Bot API

Состояние на 03.10.2026 (сверяй с PyPI): python-telegram-bot 22.8 (12.06.2026) —
Bot API 10.0; aiogram 3.31.0 (26.08.2026) — Bot API 10.3. Версии старше (например,
python-telegram-bot 21.6 и aiogram 3.24.0) новых методов не покрывают:
стриминг-черновики, rich-сообщения, ephemeral, guest- и managed-боты. Выход —
обновить библиотеку либо слать сырой HTTP-запрос, как это делает
`tools/tg_bot.py`.

Что появилось у ботов в 2026: `sendMessageDraft` (стриминг ответа; доступен всем
ботам с Bot API 9.5), Rich Messages (10.1), guest mode и bot-to-bot (10.0),
managed bots (9.6), ephemeral-сообщения (10.2/10.3), guard-боты для заявок на
вступление (10.1), темы в личных чатах (9.3/9.4), кастомные эмодзи и цвета кнопок
(9.4). Методы Mini App работают только с родного домена приложения (с 20.07.2026;
отключается в @BotFather). Подробнее — скилл `tg-bot-publish`.

**Лимит ботов на аккаунт — 20, у Premium — 40** (`bots_create_limit_default` /
`_premium`; проверено 13.09.2026: на Premium аккаунт упирается именно в 40).
Managed bots (`bots.createBot`, Bot API 9.6) этот лимит **не обходят**: тот же
владелец, та же ошибка `BOT_CREATE_LIMIT_EXCEEDED`. Переключатель Bot Management
Mode живёт в мини-приложении @BotFather.

## Публичный LLM-бот: ловушки

Когда бот публичный (один токен — много юзеров) и управляется LLM с tool-calling,
стандартный wiki python-telegram-bot не покрывает ничего из этого списка.
Реализация каждого пункта → `references/multi-tenant-llm-bot.md`.

- **Секрет юзера (BYOK) не должен попасть в контекст LLM.** Оттуда он уедет в
  `history.jsonl` и во все последующие промпты. Перехватывать ввод FSM-флагом в
  `profile.json` ДО вызова агента, шифровать Fernet, в ответе не эхоить значение.
- **Данные — по папке на `tg_user_id`**, не глобальными таблицами: удаление юзера
  должно быть одной `rm -rf`, а не DELETE по десятку таблиц.
- **Shortcuts — reply keyboard, не inline.** Кнопка reply-клавиатуры приходит
  обычным текстом и идёт в тот же tool-routing, что и свободный ввод. У
  `callback_query` нет text content — это отдельный поток и отдельный роутинг.
  Inline оставить только для действий над конкретным объектом (✅ Опубликовать /
  ✏️ Edit), где нужен `callback_data`. Клавиатуру (`reply_markup=persistent_menu()`)
  передавать в каждом ответе агента — иначе она пропадает.
- **`parse_mode=HTML` + конвертер markdown→HTML.** LLM генерит `**bold**`;
  `Markdown` устарел, `MarkdownV2` требует экранировать `_*[]()~>#+-=|{}.!`.
  Без конвертера юзер видит буквальные звёздочки. `MarkdownV2` тоже рабочий, но
  только с экранированием; у легаси-`Markdown` нет вложенности, подчёркивания,
  зачёркивания, спойлера, цитат, `custom_emoji` и `date_time`. В конвертере сначала
  `html.escape(text, quote=False)` (иначе `&`, `<`, `>` приводят к ошибке Bot API
  400 «can't parse entities»), потом замены `**`→`<b>` и остальные. Гонять только
  при `parse_mode=HTML` — иначе двойная конверсия. Код → в reference.
- **В memory писать `tool_calls`, а не только тексты.** Иначе следующий ход агента
  не помнит `draft_ts` / `job_id` из предыдущего tool-вызова. При кросс-провайдерном
  fallback смотри orphan-tool-message filter в скилле `multi-model-gateway`.
- **Бета-доступ — whitelist.** `data/whitelist.txt` (один `tg_user_id` на строку),
  проверка перед dispatch, включается переменной `WHITELIST_ON=1`.
- **`MSYS_NO_PATHCONV=1` при тестах из Git bash на Windows.** MSYS превращает
  `/start` в `C:/Program Files/Git/start` ДО запуска Python, и бот получает мусор:
  ```bash
  MSYS_NO_PATHCONV=1 python tg_client.py send @bot "/start"
  ```
  Альтернатива — звать Telethon из Python без bash-прослойки.

## Telethon: каналы и лимиты

**Поиск реальных каналов** (вместо LLM-галлюцинаций) — MTProto `SearchRequest`:

```python
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.types import Channel

result = await client(SearchRequest(q=query, limit=limit))
chans = [c for c in result.chats
         if isinstance(c, Channel) and (c.broadcast or c.megagroup)]
```

Фильтр `broadcast or megagroup` нужен, чтобы попали и каналы, и супергруппы;
различать их потом по этим же полям.

**FloodWait.** `SearchRequest` и `iter_messages` под нагрузкой дают
`FloodWaitError(seconds=N)`. Ждать и ретраить при `e.seconds <= 20`, иначе падать
с человекочитаемой ошибкой «retry later». Плюс в system prompt агента:
`"Call discover_channels AT MOST 2 times per user message"` — без этого LLM
выпускает 6 запросов на одно сообщение юзера и flood-wait накапливается.

**`iter_messages` одинаков для channel и megagroup**, `get_entity(@username)`
резолвит оба. Разница в метриках: у супергруппы `msg.views = 0`, но есть
`msg.reactions`. Поэтому виральность считать по всем трём сигналам:

```python
virality = views + 3 * reactions + 5 * forwards
```

## Ссылки

- [python-telegram-bot docs](https://docs.python-telegram-bot.org/) ·
  [код-сниппеты wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets)
- [Telegram Bot API](https://core.telegram.org/bots/api) ·
  [Telethon docs](https://docs.telethon.dev/)
