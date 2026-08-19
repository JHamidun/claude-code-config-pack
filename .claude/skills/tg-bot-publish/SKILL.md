---
name: tg-bot-publish
description: "Публикация и управление в Telegram ЧЕРЕЗ БОТА (Bot API), CLI tg_bot.py: посты в канал, rich-вёрстка (таблицы/картинки), рассылка подписчикам, inline-кнопки, админка, Stars, вебхуки. НЕ: текст поста→tg-post; разработка→telegram-bot-toolkit; user-аккаунт→tg_client.py."
keywords: telegram bot api, tg_bot.py, sendRichMessage, пост в канал от бота, бот админ канала, кнопка к посту, rich пост таблица, рассылка подписчикам, sendMessage, inline keyboard, broadcast, paid media stars, инвайт ссылка, вебхук, getFile, опрос от бота
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
- **рассылка** → подкоманда CLI `broadcast` по списку

Один инструмент покрывает оба сценария — меняется только `--to`.

## Токены

`--token` принимает сам токен (`123:ABC…`) ИЛИ имя бота из `~/.claude/.credentials.master.env`
(`BOT_TOKEN_*`, `TELEGRAM_BOT_TOKEN_*`, `*_TELEGRAM_BOT_TOKEN`).
Живые на 2026-06: **ACADEMY, COMPANY_SALES, DEMO3, YOUR_LEADGEN_BOT**. Отозваны (401): DEMO5, FINANCE.

Глобальный `--dry-run` печатает payload и НЕ отправляет — всегда проверяй им перед боевой отправкой.

## Базовые сценарии

```bash
# проверить токен
python tg_bot.py --token ACADEMY me

# ── ПОСТ В КАНАЛ (бот-админ) ──
# текст + форматирование + раскрывающийся блок + кнопка-переход на пост
python tg_bot.py --token ACADEMY send --to @yourchannel \
  --text "<b>Заголовок</b>
<blockquote expandable>скрытый длинный текст</blockquote>" \
  --btn "Открыть пост|https://t.me/your_username/123" --pin

# фото-пост, спойлер, подпись над фото, две кнопки в ряд
python tg_bot.py --token ACADEMY send --to @yourchannel --photo cover.jpg \
  --text "Подпись" --spoiler --caption-above \
  --btn-row "Сайт|https://your-domain.com ;; Промокод|copy:AI2026"

# ── RICH-ПОСТ (Bot API 10.1): таблицы / заголовки / картинки в посте ──
python tg_bot.py --token ACADEMY rich --to @yourchannel --md-file post.md
# (rich_message = {"markdown": "..."} — Telegram сам парсит markdown в блоки)

# ── ПОДПИСЧИКУ В ЛИЧКУ / РАССЫЛКА ──
python tg_bot.py --token COMPANY_SALES send --to 123456789 --text "Личное сообщение"
python tg_bot.py --token COMPANY_SALES updates --out subs.txt          # собрать chat_id
python tg_bot.py --token COMPANY_SALES --dry-run broadcast --to-file subs.txt \
  --text "<b>Анонс</b> 👇" --btn "Регистрация|https://your-domain.com/conf"
```

## Карта команд (163 — ПОЛНОЕ покрытие Bot API, 173/173 метода)

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

`python tg_bot.py --help` — полный список; у каждой подкоманды свой `--help`.
Большинство команд из реестра — обёртки над одним методом Bot API; структурные параметры передаются JSON-аргументом (`--stickers '[...]'`, `--content '{...}'`, `--results '[...]'`).

## Форматирование (HTML, по умолчанию в `send`)

`<b> <i> <u> <s>` · `<tg-spoiler>` · `<code> <pre>` · `<blockquote>` / **`<blockquote expandable>`** (раскрывающийся блок) · `<a href>` · `<tg-emoji>`.

## Кнопки (`--btn "Текст|значение"`, ряд — `--btn-row "A|… ;; B|…"`)

`url`(http/tg) · `copy:текст` · `app:url`(web-app) · `switch:` · `switchcur:` · `cb:`(callback — оживает только при запущенном боте, см. `listen`). **В канале работают URL/copy/app**; callback — для интерактива в личке.

## Ключевые грабли

- Юзеру нельзя написать первым — только после его `/start` (иначе 403).
- `getUpdates`/`listen` ⟂ webhook: при активном вебхуке апдейтов нет → диагностика `webhook-info`, снять `webhook-delete`.
- Кнопку нельзя пришить к посту, опубликованному руками — только к посту, отправленному ботом.
- Rich: лимит 32768 символов; `<details>`+формула роняет Telegram Desktop; CJK искажается; рендерится только в ботах/каналах с ботом-админом.
- `forwardMessages`/`copyMessages` — id строго по возрастанию, до 100; `sendPaidMedia` — 1–25000 Stars; `rich-draft` — только личка + ненулевой draft_id.
- JSON-аргументы для структур: `--media`(InputPaidMedia[]) `--prices`(LabeledPrice[]) `--perms`(ChatPermissions) `--commands`(BotCommand[]) `--button`(MenuButton) `--result`(InlineQueryResult).

## Справочники (progressive disclosure)

- **`~/.claude/tools/TG_BOT_API_REFERENCE.md`** — разведка возможностей и полный справочник Bot API: что доступно one-shot vs нужен живой бот, форматирование, кнопки, рассылка, rich, новинки 2025-2026 по версиям, полный список 62 команд.
- **`~/.claude/tools/TG_BOT_API_REFERENCE.md`** — детальный справочник всех 173 методов Bot API (назначение, версия, все параметры, что возвращает, грабли). Сюда смотреть когда нужен точный параметр метода или метод вне CLI.

## Границы (что НЕ через этот навык)

- Текст/копирайтинг поста → [[tg-post]] (потом опубликовать готовое — этим навыком).
- Разработка интерактивного бота с нуля (handlers, scenes, deploy) → `telegram-bot-toolkit`.
- Чтение истории, парсинг участников, действия от ЛИЧНОГО аккаунта → `~/.claude/tools/tg_client.py` (Telethon, user-API — кнопки слать НЕ может).
- Публикация через сторонний сервис SocialPublisher → `socialpublisher-post`.
- Вне скоупа CLI (есть в REFERENCE, но не зашиты): создание стикер-сетов, бизнес-аккаунты, passport, forum-топики CRUD, live-хендлеры платежей/inline.
