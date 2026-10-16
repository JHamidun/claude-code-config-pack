---
name: tg-bot-publish
description: "Публикация в Telegram через бота (Bot API, tg_bot.py): посты в канал, рассылка, кнопки. Триггеры: «пост в канал от бота». НЕ текст поста → tg-post."
keywords: telegram bot api, tg_bot.py, sendRichMessage, пост в канал от бота, бот админ канала, кнопка к посту, rich пост таблица, рассылка подписчикам, sendMessage, inline keyboard, broadcast, paid media stars, инвайт ссылка, вебхук, getFile, опрос от бота, кружок из видео, видеосообщение, sendVideoNote, video note, белые рамки у кружка, VOICE_MESSAGES_FORBIDDEN, ffmpeg квадрат 640, rich формат, кнопки внутри поста, tg-button-row, отступы между абзацами, распорка nbsp, хэштег стал заголовком, tg-time локальное время получателя, blockquote expandable, tg-collage слайдшоу, allow_paid_broadcast, заглушка на старых клиентах, флуд-лимит рассылки, 429 retry_after, картинка через media tg://photo
---

# TG Bot Publish — публикация и управление через бота (Bot API)

Операционный навык: как **публиковать и управлять** в Telegram через бота напрямую по Bot API.
Инструмент — единый CLI `~/.claude/tools/tg_bot.py` (Python + requests, без зависимостей кроме requests).

> Это НЕ копирайтинг (текст поста пишет [[tg-post]]) и НЕ разработка бота (см. `telegram-bot-toolkit`).
> Это «у меня есть бот-токен — опубликуй/разошли/настрой».

## Главный принцип

В Bot API **нет разницы между «в канал» и «подписчику в личку»** — везде один `chat_id` (`--to`):
- **канал** → `@username` или `-100<id>` (бот должен быть **админом** с правом *Post Messages*)
- **подписчик** → его `<user_id>` (бот пишет только если юзер сам нажал `/start`)
- **рассылка** → подкоманда CLI `tg_bot.py broadcast` по списку (это подкоманда скрипта, не слэш-команда)

Один инструмент покрывает оба сценария — меняется только `--to`.

## Токены

`--token` принимает сам токен (`123:ABC…`) ИЛИ **своё короткое имя бота**, которое резолвится
из `~/.claude/.credentials.master.env` (шаблон: `~/.claude/templates/.credentials.master.env.example`).
Имя ищется в четырёх видах: `BOT_TOKEN_<ИМЯ>`, `TELEGRAM_BOT_TOKEN_<ИМЯ>`,
`<ИМЯ>_TELEGRAM_BOT_TOKEN`, `<ИМЯ>`. Никакого встроенного реестра ботов нет — имя придумываешь ты:

```bash
# в ~/.claude/.credentials.master.env
BOT_TOKEN_MYBOT=123456:AAH…            # → --token MYBOT
BOT_TOKEN_SALESBOT=987654:AAG…         # → --token SALESBOT
```

Несколько ботов держи под разными именами: у бота-админа канала и бота для личек обычно
разные права, и перепутанный токен даёт не ошибку, а пост не в тот канал.
Проверка перед первой отправкой — `me`: отвечает именем бота, значит токен резолвится.
Токены в файле протухают (бота отозвали или пересоздали в @BotFather): `401` на `me` — токен
мёртв, возьми новый, а не доверяй списку в конфиге — начинай с `me`.

Глобальный `--dry-run` печатает payload и НЕ отправляет — всегда проверяй им перед боевой отправкой.

## Базовые сценарии

```bash
# проверить токен
python ~/.claude/tools/tg_bot.py --token MYBOT me

# ── ПОСТ В КАНАЛ (бот-админ) ──
# текст + форматирование + раскрывающийся блок + кнопка-переход на пост
python ~/.claude/tools/tg_bot.py --token MYBOT send --to @yourchannel \
  --text "<b>Заголовок</b>
<blockquote expandable>скрытый длинный текст</blockquote>" \
  --btn "Открыть пост|https://t.me/your_username/123" --pin

# фото-пост, спойлер, подпись над фото, две кнопки в ряд
python ~/.claude/tools/tg_bot.py --token MYBOT send --to @yourchannel --photo cover.jpg \
  --text "Подпись" --spoiler --caption-above \
  --btn-row "Сайт|https://your-domain.com ;; Промокод|copy:AI2026"

# ── RICH-ПОСТ (Bot API 10.1+; кнопки ВНУТРИ поста — 10.3): таблицы, заголовки, картинки ──
python ~/.claude/tools/tg_bot.py --token MYBOT rich --to @yourchannel --md-file post.md \
  --btn "Записаться|https://t.me/your_bot?start=src"
# (rich_message = {"markdown": "..."} — Telegram сам парсит markdown в блоки)
# До 32768 знаков, картинка блоком, кнопки внутри поста; подробности, лимиты,
# отступы и баги клиентов → references/rich-messages.md

# ── ПОДПИСЧИКУ В ЛИЧКУ / РАССЫЛКА ──
python ~/.claude/tools/tg_bot.py --token SALESBOT send --to 123456789 --text "Личное сообщение"
python ~/.claude/tools/tg_bot.py --token SALESBOT updates --out subs.txt   # собрать chat_id
python ~/.claude/tools/tg_bot.py --token SALESBOT --dry-run broadcast --to-file subs.txt \
  --text "<b>Анонс</b> 👇" --btn "Регистрация|https://your-domain.com/conf"
```

## Карта команд (163 подкоманды; покрыто 173 из 185 методов Bot API 10.3 по сверке 03.10.2026 — это НЕ «полное покрытие», список пробелов ниже)

| Группа | Команды |
|---|---|
| Контент/цикл | `send rich album poll dice location contact venue live-photo edit edit-media pin unpin unpin-all react react-del react-clear copy copy-batch forward forward-batch delete stop-poll action broadcast updates link listen` |
| Админка канала | `admins count member ban unban restrict promote perms set-title set-desc set-photo set-admin-title ban-channel unban-channel set-member-tag del-photo leave user-boosts` |
| Инвайты/заявки | `invite-create/edit/revoke/export join-approve join-decline sub-invite-create sub-invite-edit post-approve post-decline` |
| Монетизация (Stars) | `invoice invoice-link paid-media gift gifts star-balance star-tx refund star-sub gift-premium user-gifts chat-gifts gift-convert gift-upgrade gift-transfer` |
| Стикер-сеты | `sticker-upload stickerset-create sticker-add sticker-pos sticker-del sticker-replace sticker-emojis sticker-keywords sticker-mask stickerset-title stickerset-thumb emoji-set-thumb stickerset-del stickerset-get custom-emoji set-chat-stickers del-chat-stickers` |
| Профили ботов флота | `set-name get-name set-bot-desc get-bot-desc set-bot-short get-bot-short get-commands del-commands menu-button get-menu-button set-default-rights get-default-rights set-bot-photo del-bot-photo set-commands` |
| Форум-топики | `forum-create/edit/close/reopen/delete/unpin-all forum-icons gen-edit/close/reopen/hide/unhide` |
| Бизнес-аккаунт + истории | `biz-get biz-read biz-delete biz-set-name/username/bio/photo biz-del-photo biz-gift-settings biz-star-balance biz-transfer-stars biz-gifts story-post/edit/delete send-checklist edit-checklist` |
| Файлы/разведка | `get-file user-photos user-audios` |
| Вебхуки/сервер | `webhook-set webhook-delete webhook-info logout close-bot managed-get managed-set` |
| Верификация/игры | `verify-user verify-chat unverify-user unverify-chat send-game game-score game-scores` |
| Live-хендлеры (нужен свежий `*_query_id` из `listen`/webhook) | `answer-inline answer-webapp answer-shipping answer-precheckout answer-guest answer-joinreq-query join-webapp save-kbd-button msg-draft edit-live-loc stop-live-loc` |
| Rich-стриминг/inline | `rich-draft prep-inline` |
| Не покрыто CLI (сверка 03.10.2026) | 10.2: `editEphemeralMessageText/Media/Caption/ReplyMarkup`, `deleteEphemeralMessage` + параметр `ephemeral_message_parameters` у `send*` (в 10.3 заменил `receiver_user_id`/`callback_query_id`); 10.3: `can_stop`/`keep_on_stop` у `sendMessageDraft`/`sendRichMessageDraft`, право `can_send_welcome_messages` у `promoteChatMember`, `DisabledButton`, `force_reply` у inline-клавиатуры; 10.0: `getUserPersonalChatMessages`; 9.6: `getManagedBotToken`, `replaceManagedBotToken`; 9.3: `repostStory`; 8.0: `setUserEmojiStatus`; 6.8: `unpinAllGeneralForumTopicMessages`; `setPassportDataErrors`. Звать сырым `tg_bot.api(token, "<метод>", {...})` |

`python ~/.claude/tools/tg_bot.py --help` — полный список; у каждой подкоманды свой `--help`.
Большинство команд из реестра — обёртки над одним методом Bot API; структурные параметры передаются JSON-аргументом (`--stickers '[...]'`, `--content '{...}'`, `--results '[...]'`).

## Форматирование (HTML, по умолчанию в `send`)

`<b> <i> <u> <s>` · `<tg-spoiler>` · `<code> <pre>` · `<blockquote>` / **`<blockquote expandable>`** (раскрывающийся блок) · `<a href>` · `<tg-emoji>`.

Дата и время получателя (Bot API 9.5): `<tg-time unix="1647531900" format="wDT">22:45 завтра</tg-time>`; в MarkdownV2 — `![22:45 завтра](tg://time?unix=1647531900&format=wDT)`. Формат — строка по регулярному выражению `r|w?[dD]?[tT]?` (`r` относительное и не сочетается с другими, `w` день недели, `d`/`D` дата коротко/длинно, `t`/`T` время коротко/длинно); пустой формат — текст как есть. Кастомные эмодзи (`<tg-emoji>`, `icon_custom_emoji_id` у кнопок, 9.4) работают только если у владельца бота есть Telegram Premium или у бота куплены юзернеймы на Fragment. `blockquote` и `expandable_blockquote` не вкладываются друг в друга; в `pre`/`code` другие сущности вкладывать нельзя.

## Кнопки (`--btn "Текст|значение"`, ряд — `--btn-row "A|… ;; B|…"`)

`url`(http/tg) · `copy:текст` · `app:url`(web-app) · `switch:` · `switchcur:` · `cb:`(callback — оживает только при запущенном боте, см. `listen`). **В канале работают URL и copy**; `app:` (web_app) — ТОЛЬКО в личке с ботом («Available only in private chats between a user and the bot»), Mini App в канале открывай url-кнопкой на direct link `https://t.me/<bot>/<app>?startapp=<param>`; `switchcur:` в каналах не поддержан; callback нужен запущенный бот (`listen`/webhook), ограничения «только личка» у него в доках нет.

## Кружки (видеосообщения) из обычного видео

Кружок — не видеофайл, а **отдельный тип** `sendVideoNote`. Отправить mp4 как `--video` и
получить кружок нельзя: будет прямоугольник с белыми полями.

**1. Перекодировать: строго квадрат, H.264, ≤60 с.** Проверено на ролике
(1080×1080 HEVC, 32 МБ → 640×640 H.264, **2 МБ**, 34,5 с):

```bash
# исходник УЖЕ квадратный
ffmpeg -y -v error -i исходник.mp4 -vf "scale=640:640:flags=lanczos" \
  -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -r 30 -profile:v main \
  -c:a aac -b:a 96k -ac 1 -movflags +faststart krug.mp4

# исходник НЕ квадратный — сперва обрезать по центру короткой стороной
ffmpeg -y -v error -i исходник.mp4 \
  -vf "crop='min(iw,ih)':'min(iw,ih)',scale=640:640:flags=lanczos" \
  -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -r 30 -profile:v main \
  -c:a aac -b:a 96k -ac 1 -movflags +faststart krug.mp4
```

640 px бот примет, но «без пересжатия» первоисточником не подтверждается: app-config `round_video_encoding` рекомендует для кружка diameter 384, video_bitrate 1000 кбит/с, audio_bitrate 64 кбит/с, max_size 12 МБ (12582912 Б); лимит самого Bot API — 50 МБ, длина ≤1 мин, `video_note` по URL не принимается (только file_id/загрузка). `-profile:v main` и
`yuv420p` обязательны: HEVC и 10-битный цвет клиенты не принимают.

**2. Отправить.** CLI умеет это штатно (проверено сухим прогоном — метод `sendVideoNote`):

```bash
python ~/.claude/tools/tg_bot.py --token MYBOT send --to @yourchannel --video-note krug.mp4 \
  --btn "Зарегистрироваться|https://t.me/your_bot"
```

**3. Для рассылки — один раз залить и дальше гонять `file_id`.** Слать 2 МБ каждому из
тысяч получателей — это часы и упор в лимиты. Залить себе в личку с ботом, забрать
`result.video_note.file_id`, служебное сообщение удалить (`delete`). CLI в ответ печатает
только ссылку на сообщение, поэтому `file_id` достаётся сырым вызовом из Python:

```python
import os, sys
sys.path.insert(0, os.path.expanduser("~/.claude/tools"))
import tg_bot

token = tg_bot.load_token("MYBOT")                 # то же имя, что в --token
r = tg_bot.api(token, "sendVideoNote", {"chat_id": MY_USER_ID},
               files={"video_note": open("krug.mp4", "rb")})
print(r["video_note"]["file_id"], r["message_id"])   # file_id — в рассылку, message_id — в delete
```

`broadcast` кружки не умеет (только текст и фото): дальше `send --to <chat_id> --video-note <file_id>`
по списку получателей, с паузой между отправками (лимиты рассылки — в «Ключевых граблях» ниже).

### Грабли кружков

- **Подписи у кружка НЕТ** (`caption` игнорируется) — текст идёт **отдельным сообщением
  следом**. Кнопку можно пришить к любому из двух, но осмысленный порядок:
  кружок молча → текст с кнопкой.
- 🚨 **`Bad Request: VOICE_MESSAGES_FORBIDDEN` — это не поломка**, а настройка приватности
  получателя (закрыт приём голосовых и видеосообщений). На живой базе подписчиков —
  около **10%** получателей. Узнать заранее нельзя. Поэтому **текст-спутник должен читаться
  самостоятельно**: без «посмотрите видео выше» — каждый десятый видео не увидит.
- Отказ кружка не должен рвать рассылку: отправлять текст **независимо** от исхода
  `sendVideoNote`, иначе десятая часть базы не получит вообще ничего.
- Число доставленных кружков в сводке рассылки **не видно**, если она считает только текстовые
  сообщения: веди свой счёт отдельно — сколько `sendVideoNote` прошло и сколько упало с
  `VOICE_MESSAGES_FORBIDDEN`.
- Длиннее 60 с Telegram не принимает; звук лучше моно (`-ac 1`) — в кружке стерео не нужно.

## Ключевые грабли

- Юзеру нельзя написать первым — только после его `/start` (иначе 403). Исключения по докам: заявка на вступление (`ChatJoinRequest.user_chat_id` годится 5 минут, пока заявка не обработана), guest mode (10.0 — бот отвечает в чате, где его упомянули), общение бот↔бот при включённом Bot-to-Bot режиме в @BotFather (10.0); бизнес-бот отвечает в чатах владельца аккаунта, где за последние 24 часа было входящее (`BusinessConnection.rights.can_reply`).
- `getUpdates`/`listen` ⟂ webhook: при активном вебхуке апдейтов нет → диагностика `webhook-info`, снять `webhook-delete`.
- Платформенные новинки 2026, которых нет в навыке (сверка 03.10.2026): **Communities** (Bot API 10.2) — бот только видит (`Community`, `ChatFullInfo.community`, служебные `community_chat_added/removed/joined`), методов создания нет; **Welcome Messages** (25.08.2026, Desktop 7.1) — приветствие для новых участников группы/канала владельцы чата задают в приложении, у бота-админа есть право `can_send_welcome_messages` (10.3); **Guest mode** (10.0) — бот отвечает в чате, где его упомянули (до 3 гостевых ботов на сообщение); **Ephemeral messages** (10.2/10.3) — ответ виден одному участнику группы, слать можно в течение 15 с после его действия; **Join request queries / guard-боты** (10.1) — `answerChatJoinRequestQuery`, `sendChatJoinRequestWebApp`; **Business** — с 10.0 бизнес-боты управляют аккаунтом и без Premium у владельца, `BusinessConnection.can_reply` заменён `rights` (9.0); **темы в личных чатах** (9.3/9.4) — `has_topics_enabled`, `createForumTopic` и `message_thread_id` в личке; **Mini App** — методы работают только с родного домена приложения с 20.07.2026 (отключается в @BotFather).
- Кнопку нельзя пришить к посту, опубликованному руками — только к посту, отправленному ботом.
- Лимиты (сверка 03.10.2026): текст 1–4096 знаков, подпись 0–1024 (у rich — 32 768 на весь пост), альбом 2–10, опрос 1–12 вариантов. Загрузка файла ботом (multipart) ≤50 МБ, фото ≤10 МБ; по URL — фото ≤5 МБ, остальное ≤20 МБ, `sendDocument` по URL — только .PDF и .ZIP, `sendVoice` по URL — audio/ogg ≤1 МБ (1–20 МБ уйдёт как файл); по `file_id` лимитов нет; скачивание `getFile` ≤20 МБ; на своём Bot API-сервере — загрузка до 2000 МБ и скачивание без лимита. У пользовательских аккаунтов (Telethon): файл до 2 ГБ, у Premium — до 4 ГБ (telegram.org/faq, faq_premium; точно по app-config `upload_max_fileparts` 4000/8000 частей по 512 КБ = 2000/4000 МиБ, т.е. 2 097 152 000 / 4 194 304 000 байт), подпись 1024, у Premium 4096.
- **Rich** (подробно → `references/rich-messages.md`, у каждого факта там пометка источника: дока / наша отправка / наш вывод / не подтверждено): 32768 знаков, 500 блоков. Одиночный перенос строки СКЛЕИВАЕТСЯ — абзац через пустую строку, жёсткий перенос — два пробела в конце. 🚨 Хэштег в начале строки становится заголовком, экранировать `\#`. Картинка — только отдельным блоком: либо по ссылке, доступной серверам Telegram (S3 REG.RU не подходит), либо своим файлом через поле `media` + `tg://photo?id=`. 🚨 Нет у бота права слать медиа в чат — падает ВЕСЬ вызов. Настроек отступа в API нет вовсе; распорка — пустой абзац с U+00A0. Старые клиенты видят заглушку, Desktop до 7.1 не показывает кнопки внутри поста; на iOS роняет картинка в `<tg-collage>`, а кнопка внутри `<details>` не открывает ссылку. Rich-текст, по заявке пользователя на bugs.telegram.org (/c/63413, тип Suggestion, не подтверждено Telegram), не копируется на Android (нет пункта «Копировать») — промокод дублировать кнопкой `copy_text` и текстом. Telethon такое сообщение отдаёт с пустым `message`, но содержимое читается в `m.rich_message.blocks`. **Рассылка:** 1 сообщение/с в один чат, ~30/с суммарно, на 429 спать `retry_after`; платный `allow_paid_broadcast` требует от 10 000 Stars (API) до 100 000 Stars + 100 000 MAU (FAQ) — небольшому боту недоступен; `message_id` каждой отправки сохранять, иначе потом не исправить.
- `forwardMessages`/`copyMessages` — id строго по возрастанию, до 100; `sendPaidMedia` — 1–25000 Stars; `rich-draft` — только личка + ненулевой draft_id.
- Видео в большой чат/канал сервер может отложить сам (с 01.12.2024): тогда `message_id` = 0, сообщение лежит в отложенных и пока не отправится, его нельзя использовать — ссылку `t.me/<канал>/0` из `_report_sent` строить нельзя. `sendVideoNote` по URL не принимается. Черновики `sendMessageDraft`/`sendRichMessageDraft` живут ~30 с: итог надо отправить `sendMessage`/`sendRichMessage`; `can_stop` + `keep_on_stop` (10.3) показывают получателю кнопку «стоп» и шлют апдейт `stopped_message_generation`.
- JSON-аргументы для структур: `--media`(InputPaidMedia[]) `--prices`(LabeledPrice[]) `--perms`(ChatPermissions) `--commands`(BotCommand[]) `--button`(MenuButton) `--result`(InlineQueryResult).

## Справочники (progressive disclosure)

- **`references/rich-messages.md`** — rich-сообщения целиком: синтаксис блоков и inline, кнопки внутри поста (10.3), картинки по ссылке и через `media` + `tg://photo?id=`, лимиты, отступы и читаемость, открытые карточки багов клиентов, флуд-лимиты рассылки и почему платный режим недоступен небольшому боту. У каждого факта пометка источника. Сверено с живой докой 14–15.09.2026 и перепроверено 03.10.2026 (changelog, @BotNews, блог): новее Bot API 10.3 (24.08.2026) ничего нет.
- **`~/.claude/tools/TG_BOT_API_REFERENCE.md`** (~270 КБ) — детальный справочник всех **173 методов**
  Bot API: назначение, версия, все параметры, что возвращает, грабли; у каждого метода помечено,
  покрыт ли он CLI-командой. Сюда смотреть, когда нужен точный параметр метода.
  Читать выборочно (`grep -n "<метод>"` → нужный раздел), а не целиком: файл в контекст не влезет.

## Границы (что НЕ через этот навык)

- Текст/копирайтинг поста → [[tg-post]] (потом опубликовать готовое — этим навыком).
- Разработка интерактивного бота с нуля (handlers, scenes, deploy) → `telegram-bot-toolkit`.
- Чтение истории, парсинг участников, действия от ЛИЧНОГО аккаунта → `~/.claude/tools/tg_client.py` (Telethon, user-API — кнопки слать НЕ может).
- Публикация через сторонний планировщик соцсетей (сразу в несколько площадок, отложка) → `postiz`, `publora-post`.
- Вне скоупа CLI (есть в REFERENCE, но не зашиты): passport (`setPassportDataErrors`), эфемерные сообщения 10.2 (`editEphemeral*`, `deleteEphemeralMessage`), `getUserPersonalChatMessages`, `getManagedBotToken`/`replaceManagedBotToken`, `repostStory`, `setUserEmojiStatus`, `unpinAllGeneralForumTopicMessages`. Стикер-сеты, бизнес-аккаунты и истории, CRUD форум-топиков и live-хендлеры платежей/inline УЖЕ зашиты через реестр `REGISTRY` (см. карту команд выше).
