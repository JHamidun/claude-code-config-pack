#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tg_bot.py — полный инструмент Telegram Bot API: ВСЁ, что умеет бот, из CLI.

КЛЮЧЕВАЯ ИДЕЯ: в Bot API нет разницы между «в канал» и «подписчику в личку».
Это всё один параметр --to (chat_id):
  • канал           →  @username  или  -100<id>   (бот должен быть АДМИН с правом Post Messages)
  • подписчик/личка →  <user_id>   (бот может писать, только если юзер сам нажал /start)
  • супергруппа     →  -100<id>    (+ --thread <id> для темы форума / треда комментариев)
  • рассылка        →  команда broadcast по списку chat_id

Подкоманды:
  me           проверить токен (getMe)
  send         отправить сообщение/медиа (текст, фото, видео, аудио, голос, кружок, документ, GIF, стикер)
  album        медиа-группа (альбом до 10 фото/видео)
  poll         опрос / викторина (quiz)
  dice         кубик/эмодзи-игра
  location     геолокация (можно live)
  contact      контакт (vCard)
  edit         редактировать текст/подпись/кнопки уже отправленного БОТОМ сообщения
  pin/unpin    закрепить/открепить
  react        поставить реакцию-эмодзи
  copy         скопировать сообщение (без «переслано от»)
  forward      переслать сообщение
  delete       удалить сообщение
  broadcast    рассылка по списку подписчиков (сегменты, троттлинг, отчёт)
  updates      кто писал боту → собрать user_id подписчиков (getUpdates)
  link         построить t.me-ссылку на пост (в т.ч. приватный канал)
  listen       демо: живой бот с раскрывающимися inline-меню (callback) для подписчиков

ФОРМАТИРОВАНИЕ (по умолчанию HTML): <b> <i> <u> <s> <tg-spoiler> <code> <pre>
  <a href> <blockquote> <blockquote expandable> (раскрывающийся блок!) <tg-emoji>.
КНОПКИ — см. parse_button(): url / cb: / copy: / app: / switch: / switchcur:

Токен: --token принимает сам токен (123:ABC) ИЛИ имя из ~/.claude/.credentials.master.env
  (DEMO5, ACADEMY, COMPANY_SALES, FINANCE, LINKEDIN, DEMO3, YOUR_PROJECT, DIGITAL_BUDDY_V3, ...).

Глобальный флаг --dry-run печатает метод+payload и НИЧЕГО не отправляет (для проверки).

Примеры — внизу файла (EXAMPLES) и в TG_BOT_CAPABILITIES.md.
"""
import argparse
import json
import os
import re
import sys
import time
from typing import Any

import requests

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]  # Windows cp1251 → UTF-8
    except Exception:
        pass

CRED_PATH = os.path.expanduser("~/.claude/.credentials.master.env")
API = "https://api.telegram.org/bot{token}/{method}"

# Bot API 10.1 (11.06.2026): rich-сообщения. Лимит сырого markdown — символы, не байты.
RICH_MAX_CHARS = 32768

# Какие поля в каком методе несут файл — для авто-выбора метода в `send`.
MEDIA_METHODS = {
    "photo": "sendPhoto",
    "video": "sendVideo",
    "audio": "sendAudio",
    "voice": "sendVoice",
    "video_note": "sendVideoNote",
    "document": "sendDocument",
    "animation": "sendAnimation",
    "sticker": "sendSticker",
}


# ─────────────────────────────────────────────────────────────────────────────
# TOKEN / TRANSPORT
# ─────────────────────────────────────────────────────────────────────────────
def load_token(token_arg: str) -> str:
    """token_arg = сам токен (есть ':') ИЛИ имя бота, резолвится из credentials."""
    if token_arg and ":" in token_arg:
        return token_arg
    env = {}
    if os.path.exists(CRED_PATH):
        with open(CRED_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    env.update(os.environ)
    name = (token_arg or "").upper()
    for c in (token_arg, f"BOT_TOKEN_{name}", f"TELEGRAM_BOT_TOKEN_{name}",
              f"{name}_TELEGRAM_BOT_TOKEN", name):
        if c and c in env and ":" in env[c]:
            return env[c]
    sys.exit(f"❌ Токен не найден для '{token_arg}'. Передай сам токен (123:ABC...) "
             f"или имя из credentials (DEMO5 / ACADEMY / COMPANY_SALES / FINANCE ...).")


def _multipart_clean(payload: dict) -> dict:
    """Для multipart: dict/list → json, bool → 'true'/'false', None убрать."""
    out = {}
    for k, v in payload.items():
        if v is None:
            continue
        if isinstance(v, bool):
            out[k] = "true" if v else "false"
        elif isinstance(v, (dict, list)):
            out[k] = json.dumps(v, ensure_ascii=False)
        else:
            out[k] = v
    return out


def api(token: str, method: str, payload: dict, files=None, dry=False) -> Any:
    payload = {k: v for k, v in payload.items() if v is not None}
    if dry:
        print(f"— DRY RUN — {method}\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        if files:
            print("files:", list(files))
        return {"dry": True}
    url = API.format(token=token, method=method)
    if files:
        r = requests.post(url, data=_multipart_clean(payload), files=files, timeout=120)
    else:
        r = requests.post(url, json=payload, timeout=120)
    data = r.json()
    if not data.get("ok"):
        # 429 → подождать и повторить один раз
        if data.get("error_code") == 429:
            retry = data.get("parameters", {}).get("retry_after", 3)
            time.sleep(retry + 1)
            return api(token, method, payload, files=files, dry=dry)
        raise TelegramError(method, data.get("error_code"), data.get("description"))
    return data["result"]


class TelegramError(Exception):
    def __init__(self, method, code, desc):
        self.code, self.desc = code, desc
        super().__init__(f"{method}: {code} {desc}")


# ─────────────────────────────────────────────────────────────────────────────
# BUTTONS  (inline keyboard)
# ─────────────────────────────────────────────────────────────────────────────
def parse_button(spec: str) -> dict:
    """'Текст|значение' → InlineKeyboardButton. Тип по префиксу значения:
        http/https/tg://      → url
        cb:DATA               → callback_data (нужен запущенный бот, см. listen)
        copy:TEXT             → copy_text (копирует текст в буфер по тапу)
        app:URL               → web_app (мини-приложение)
        switch:QUERY          → switch_inline_query (выбрать чат и вставить)
        switchcur:QUERY       → switch_inline_query_current_chat
       без префикса и не URL  → callback_data
    """
    if "|" not in spec:
        sys.exit(f"❌ Кнопка должна быть 'Текст|значение', получено: {spec!r}")
    text, val = (x.strip() for x in spec.split("|", 1))
    if re.match(r"^(https?|tg)://", val):
        return {"text": text, "url": val}
    if val.startswith("copy:"):
        return {"text": text, "copy_text": {"text": val[5:]}}
    if val.startswith("app:"):
        return {"text": text, "web_app": {"url": val[4:]}}
    if val.startswith("switchcur:"):
        return {"text": text, "switch_inline_query_current_chat": val[10:]}
    if val.startswith("switch:"):
        return {"text": text, "switch_inline_query": val[7:]}
    if val.startswith("cb:"):
        return {"text": text, "callback_data": val[3:]}
    return {"text": text, "callback_data": val}


def build_markup(btn_rows: list, btns: list):
    """btn_rows: список строк-рядов 'Т|з ;; Т|з'. btns: одиночные (каждая = свой ряд)."""
    keyboard = []
    for row in (btn_rows or []):
        keyboard.append([parse_button(b) for b in row.split(";;") if b.strip()])
    for b in (btns or []):
        keyboard.append([parse_button(b)])
    return {"inline_keyboard": keyboard} if keyboard else None


# ─────────────────────────────────────────────────────────────────────────────
# SHARED OPTION HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def parse_mode_of(args):
    if getattr(args, "plain", False):
        return None
    if getattr(args, "md", False):
        return "MarkdownV2"
    return "HTML"


def link_preview_of(args):
    if getattr(args, "no_preview", False):
        return {"is_disabled": True}
    opts = {}
    if getattr(args, "preview_large", False):
        opts["prefer_large_media"] = True
    if getattr(args, "preview_small", False):
        opts["prefer_small_media"] = True
    if getattr(args, "preview_above", False):
        opts["show_above_text"] = True
    return opts or None


def read_text(args) -> str:
    if getattr(args, "text_file", None):
        with open(args.text_file, encoding="utf-8") as f:
            return f.read()
    return getattr(args, "text", "") or ""


def add_common_send_flags(sp, with_media=True):
    sp.add_argument("--to", required=True, help="@channel / -100<id> / <user_id>")
    sp.add_argument("--text", default="", help="Текст или подпись (HTML по умолч.)")
    sp.add_argument("--text-file", help="Файл с текстом/HTML (для длинных постов)")
    sp.add_argument("--plain", action="store_true", help="Без форматирования")
    sp.add_argument("--md", action="store_true", help="MarkdownV2 вместо HTML")
    sp.add_argument("--btn", action="append", default=[], metavar="Текст|знач",
                    help="Кнопка (каждая на своём ряду). Повторяемый.")
    sp.add_argument("--btn-row", action="append", default=[], metavar="'Т|з ;; Т|з'",
                    help="Ряд из нескольких кнопок (разделитель ;;). Повторяемый.")
    sp.add_argument("--silent", action="store_true", help="Без звука (disable_notification)")
    sp.add_argument("--protect", action="store_true", help="Запретить пересылку/сохранение")
    sp.add_argument("--effect", help="message_effect_id (анимация, только в личке)")
    sp.add_argument("--reply-to", type=int, help="Ответить на message_id")
    sp.add_argument("--thread", type=int, help="message_thread_id (тема форума / тред комментов)")
    sp.add_argument("--pin", action="store_true", help="Закрепить после отправки")
    sp.add_argument("--pin-loud", action="store_true", help="При --pin закрепить со звуком")
    if with_media:
        for f in MEDIA_METHODS:
            sp.add_argument(f"--{f.replace('_', '-')}", help=f"{f}: путь к файлу / URL / file_id")
        sp.add_argument("--spoiler", action="store_true", help="has_spoiler (медиа под спойлером)")
        sp.add_argument("--caption-above", action="store_true", help="Подпись НАД медиа")
        sp.add_argument("--no-preview", action="store_true", help="Отключить превью ссылок (текст)")
        sp.add_argument("--preview-large", action="store_true", help="Крупное превью ссылки")
        sp.add_argument("--preview-small", action="store_true", help="Мелкое превью ссылки")
        sp.add_argument("--preview-above", action="store_true", help="Превью над текстом")


def base_payload(args) -> dict:
    """Общие message-level поля."""
    p: dict = {"chat_id": args.to}
    if getattr(args, "silent", False):
        p["disable_notification"] = True
    if getattr(args, "protect", False):
        p["protect_content"] = True
    if getattr(args, "effect", None):
        p["message_effect_id"] = args.effect
    if getattr(args, "thread", None):
        p["message_thread_id"] = args.thread
    if getattr(args, "reply_to", None):
        p["reply_parameters"] = {"message_id": args.reply_to, "allow_sending_without_reply": True}
    return p


def media_file_arg(value):
    """Локальный путь → (files-обёртка). URL/file_id → строка-параметр."""
    if value and os.path.exists(value):
        return ("file", open(value, "rb"))
    return value


def maybe_pin(token, args, result, dry):
    if getattr(args, "pin", False) and isinstance(result, dict) and result.get("message_id"):
        api(token, "pinChatMessage", {
            "chat_id": args.to, "message_id": result["message_id"],
            "disable_notification": not getattr(args, "pin_loud", False),
        }, dry=dry)


# ─────────────────────────────────────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────────────────────────────────────
def cmd_me(token, args):
    me = api(token, "getMe", {}, dry=args.dry_run)
    print(json.dumps(me, ensure_ascii=False, indent=2))


def cmd_send(token, args):
    text = read_text(args)
    pm = parse_mode_of(args)
    markup = build_markup(args.btn_row, args.btn)
    p = base_payload(args)
    if markup:
        p["reply_markup"] = markup

    # выбрать медиа-метод, если задан файл
    media_field = next((f for f in MEDIA_METHODS if getattr(args, f, None)), None)
    if media_field:
        method = MEDIA_METHODS[media_field]
        val = getattr(args, media_field)
        files = None
        f = media_file_arg(val)
        if isinstance(f, tuple):  # локальный файл → multipart upload
            files = {media_field: f[1]}
        else:                     # URL / file_id → строкой в payload
            p[media_field] = f
        # подпись (кроме video_note/sticker — у них нет caption)
        if media_field not in ("video_note", "sticker"):
            p["caption"] = text
            if pm:
                p["parse_mode"] = pm
            if args.caption_above:
                p["show_caption_above_media"] = True
        if media_field in ("photo", "video", "animation") and args.spoiler:
            p["has_spoiler"] = True
        else:
            p.pop("has_spoiler", None)
        result = api(token, method, p, files=files, dry=args.dry_run)
    else:
        if not text:
            sys.exit("❌ Нужен --text/--text-file или медиа (--photo/--video/...)")
        p["text"] = text
        if pm:
            p["parse_mode"] = pm
        lp = link_preview_of(args)
        if lp:
            p["link_preview_options"] = lp
        result = api(token, "sendMessage", p, dry=args.dry_run)

    maybe_pin(token, args, result, args.dry_run)
    _report_sent(result, args)


def cmd_rich(token, args):
    """Rich-пост (Bot API 10.1): таблицы, заголовки, списки, код, <details>,
    формулы, картинки в тексте — из СЫРОГО markdown. Telegram сам парсит разметку.
    Пока рендерится только в ботах (и в каналах, где бот — админ)."""
    md = read_text(args)
    if getattr(args, "md", None):
        md = args.md
    if getattr(args, "md_file", None):
        with open(args.md_file, encoding="utf-8") as fh:
            md = fh.read()

    p = base_payload(args)
    if getattr(args, "blocks_json", None):       # escape hatch: готовое дерево блоков
        with open(args.blocks_json, encoding="utf-8") as fh:
            p["rich_message"] = json.load(fh)
    else:
        if not md:
            sys.exit("❌ Нужен --md / --md-file / --text-file (сырой markdown) или --blocks-json")
        if len(md) > RICH_MAX_CHARS:
            sys.exit(f"❌ Rich-сообщение > {RICH_MAX_CHARS} символов (сейчас {len(md)}). Сократи/разбей.")
        low = md.lower()
        if "<details" in low and ("$$" in md or "\\(" in md):
            print("⚠️  <details> + формула роняет Telegram Desktop — проверь на десктопе перед публикой.")
        if any("一" <= ch <= "鿿" for ch in md):
            print("⚠️  CJK-иероглифы в rich иногда искажаются в Telegram Desktop.")
        p["rich_message"] = {"markdown": md}      # ← ключевая форма: Telegram парсит markdown сам

    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    lp = link_preview_of(args)
    if lp:
        p["link_preview_options"] = lp

    try:
        result = api(token, "sendRichMessage", p, dry=args.dry_run)
    except TelegramError as e:
        if e.code == 404 or "not found" in (e.desc or "").lower():
            sys.exit("❌ sendRichMessage недоступен (нужен Bot API 10.1+, 11.06.2026). "
                     "Обычные посты — командой `send`.")
        raise
    maybe_pin(token, args, result, args.dry_run)
    _report_sent(result, args)


def cmd_album(token, args):
    media = []
    files = {}
    paths = args.files
    if not (2 <= len(paths) <= 10):
        sys.exit("❌ album: от 2 до 10 файлов")
    pm = parse_mode_of(args)
    for i, path in enumerate(paths):
        is_video = path.lower().endswith((".mp4", ".mov", ".m4v", ".webm"))
        item: dict = {"type": "video" if is_video else "photo"}
        if os.path.exists(path):
            key = f"file{i}"
            files[key] = open(path, "rb")
            item["media"] = f"attach://{key}"
        else:
            item["media"] = path  # URL / file_id
        if args.spoiler:
            item["has_spoiler"] = True
        if i == 0 and args.text:
            item["caption"] = args.text
            if pm:
                item["parse_mode"] = pm
        media.append(item)
    p = base_payload(args)
    p["media"] = media
    api(token, "sendMediaGroup", p, files=files or None, dry=args.dry_run)
    print(f"✅ Альбом отправлен: {len(media)} элементов" if not args.dry_run else "(dry)")


def cmd_poll(token, args):
    p = base_payload(args)
    p["question"] = args.question
    p["options"] = [{"text": o} for o in args.option]
    p["is_anonymous"] = not args.public
    if args.multiple:
        p["allows_multiple_answers"] = True
    if args.quiz:
        p["type"] = "quiz"
        p["correct_option_id"] = args.correct
        if args.explanation:
            p["explanation"] = args.explanation
            p["explanation_parse_mode"] = "HTML"
    result = api(token, "sendPoll", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_dice(token, args):
    p = base_payload(args)
    p["emoji"] = args.emoji
    result = api(token, "sendDice", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_location(token, args):
    p = base_payload(args)
    p.update({"latitude": args.lat, "longitude": args.lon})
    if args.live:
        p["live_period"] = args.live
    result = api(token, "sendLocation", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_contact(token, args):
    p = base_payload(args)
    p.update({"phone_number": args.phone, "first_name": args.first_name})
    if args.last_name:
        p["last_name"] = args.last_name
    result = api(token, "sendContact", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_edit(token, args):
    markup = build_markup(args.btn_row, args.btn)
    p: dict = {"chat_id": args.to, "message_id": args.msg_id}
    if args.text or args.text_file:
        if getattr(args, "rich", False):          # rich-редактирование на месте (Bot API 10.1)
            p["rich_message"] = {"markdown": read_text(args)}
            if markup:
                p["reply_markup"] = markup
            api(token, "editMessageText", p, dry=args.dry_run)
            print(f"✅ Rich-текст #{args.msg_id} обновлён")
            return
        p["text"] = read_text(args)
        pm = parse_mode_of(args)
        if pm:
            p["parse_mode"] = pm
        if markup:
            p["reply_markup"] = markup
        api(token, "editMessageText", p, dry=args.dry_run)
        print(f"✅ Текст #{args.msg_id} обновлён")
    elif args.caption is not None:
        p["caption"] = args.caption
        pm = parse_mode_of(args)
        if pm:
            p["parse_mode"] = pm
        if markup:
            p["reply_markup"] = markup
        api(token, "editMessageCaption", p, dry=args.dry_run)
        print(f"✅ Подпись #{args.msg_id} обновлена")
    else:
        if markup:
            p["reply_markup"] = markup
        api(token, "editMessageReplyMarkup", p, dry=args.dry_run)
        print(f"✅ Кнопки #{args.msg_id} обновлены")


def cmd_pin(token, args):
    api(token, "pinChatMessage", {"chat_id": args.to, "message_id": args.msg_id,
                                   "disable_notification": not args.loud}, dry=args.dry_run)
    print(f"📌 Закреплено #{args.msg_id}")


def cmd_unpin(token, args):
    p = {"chat_id": args.to}
    if args.msg_id:
        p["message_id"] = args.msg_id
    api(token, "unpinChatMessage", p, dry=args.dry_run)
    print("📌 Откреплено")


def cmd_react(token, args):
    emojis = [{"type": "emoji", "emoji": e} for e in args.emoji]
    api(token, "setMessageReaction", {"chat_id": args.to, "message_id": args.msg_id,
                                       "reaction": emojis, "is_big": args.big}, dry=args.dry_run)
    print(f"👍 Реакция {' '.join(args.emoji)} → #{args.msg_id}")


def cmd_copy(token, args):
    p = {"chat_id": args.to, "from_chat_id": args.from_chat, "message_id": args.msg_id}
    if args.text:
        p["caption"] = args.text
        p["parse_mode"] = "HTML"
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    r = api(token, "copyMessage", p, dry=args.dry_run)
    print(f"✅ Скопировано → {args.to}: #{r.get('message_id')}")


def cmd_forward(token, args):
    r = api(token, "forwardMessage", {"chat_id": args.to, "from_chat_id": args.from_chat,
                                      "message_id": args.msg_id,
                                      "disable_notification": args.silent,
                                      "protect_content": args.protect}, dry=args.dry_run)
    print(f"✅ Переслано → {args.to}: #{r.get('message_id')}")


def cmd_delete(token, args):
    ids = args.msg_id
    if len(ids) > 1:                                # deleteMessages — один батч-вызов (до 100)
        api(token, "deleteMessages", {"chat_id": args.to, "message_ids": ids}, dry=args.dry_run)
    else:
        api(token, "deleteMessage", {"chat_id": args.to, "message_id": ids[0]}, dry=args.dry_run)
    print(f"🗑 Удалено: {len(ids)} сообщ.")


def cmd_updates(token, args):
    """Кто писал боту → собрать chat_id подписчиков (для рассылки)."""
    res: Any = api(token, "getUpdates", {"limit": 100, "timeout": 0}, dry=False)
    seen: dict = {}
    for u in res:
        msg = u.get("message") or u.get("callback_query", {}).get("message") or {}
        chat = msg.get("chat") or u.get("callback_query", {}).get("from") or {}
        cid = chat.get("id")
        if cid and cid not in seen:
            name = chat.get("username") or " ".join(
                filter(None, [chat.get("first_name"), chat.get("last_name")])) or str(cid)
            seen[cid] = name
    if not seen:
        print("Пусто. getUpdates видит только свежие апдейты (≤24ч) и не работает при webhook.")
        return
    print(f"Подписчиков в буфере: {len(seen)}")
    for cid, name in seen.items():
        print(f"{cid}\t{name}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for cid, name in seen.items():
                f.write(f"{cid}\t{name}\n")
        print(f"→ сохранено в {args.out}")


def cmd_link(token, args):
    """t.me-ссылка на пост. Для приватного канала нужен токен (getChat)."""
    if token:
        chat = api(token, "getChat", {"chat_id": args.to}, dry=False)
        uname = chat.get("username")
        if uname:
            print(f"https://t.me/{uname}/{args.msg_id}")
        else:
            cid = str(chat["id"])
            internal = cid[4:] if cid.startswith("-100") else cid.lstrip("-")
            print(f"https://t.me/c/{internal}/{args.msg_id}")
    else:
        print(f"https://t.me/{args.to.lstrip('@')}/{args.msg_id}")


def cmd_broadcast(token, args):
    """Рассылка по списку chat_id (подписчики). Сегмент = заранее отфильтрованный файл."""
    targets = []
    if args.to_file:
        with open(args.to_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    targets.append(line.split("\t")[0].split()[0])
    if args.to:
        targets += [t.strip() for t in args.to.split(",") if t.strip()]
    targets = list(dict.fromkeys(targets))
    if not targets:
        sys.exit("❌ Нет получателей (--to-file или --to)")

    text = read_text(args)
    pm = parse_mode_of(args)
    markup = build_markup(args.btn_row, args.btn)
    photo = getattr(args, "photo", None)

    print(f"📣 Рассылка на {len(targets)} получателей "
          f"(delay {args.delay}s){' [DRY]' if args.dry_run else ''}")
    ok = blocked = failed = 0
    for i, cid in enumerate(targets, 1):
        try:
            p = {"chat_id": cid}
            if photo:
                p["photo"] = photo
                if text:
                    p["caption"] = text
                    if pm:
                        p["parse_mode"] = pm
                if markup:
                    p["reply_markup"] = markup
                api(token, "sendPhoto", p, dry=args.dry_run)
            else:
                p["text"] = text
                if pm:
                    p["parse_mode"] = pm
                if markup:
                    p["reply_markup"] = markup
                if args.silent:
                    p["disable_notification"] = True
                api(token, "sendMessage", p, dry=args.dry_run)
            ok += 1
        except TelegramError as e:
            if e.code == 403:           # бот заблокирован / юзер не стартовал
                blocked += 1
            else:
                failed += 1
                if failed <= 5:
                    print(f"  ✗ {cid}: {e.code} {e.desc}")
        if i % 25 == 0:
            print(f"  ... {i}/{len(targets)}  ok={ok} blocked={blocked} fail={failed}")
        time.sleep(args.delay)
    print(f"✅ Готово: доставлено {ok}, заблокировали {blocked}, ошибок {failed}")


def cmd_listen(token, _args):
    """Демо живого бота: /start → меню с РАСКРЫВАЮЩИМСЯ списком (callback edit).
    Показывает интерактив для подписчиков. Ctrl+C — выход."""
    print("👂 listen: жду сообщений. /start в боте → меню. Ctrl+C для выхода.")
    collapsed = {"inline_keyboard": [[{"text": "▾ Показать программу", "callback_data": "expand"}]]}
    expanded_text = ("<b>Программа</b>\n"
                     "<blockquote expandable>1. Открытие\n2. Доклады\n3. Нетворкинг\n"
                     "4. Воркшопы\n5. Афтепати</blockquote>")
    offset = 0
    try:
        while True:
            ups = api(token, "getUpdates", {"offset": offset, "timeout": 25}, dry=False)
            for u in ups:
                offset = u["update_id"] + 1
                if "message" in u and (u["message"].get("text", "")).startswith("/start"):
                    api(token, "sendMessage", {
                        "chat_id": u["message"]["chat"]["id"],
                        "text": "Привет! Это демо раскрывающегося меню 👇",
                        "reply_markup": collapsed})
                elif "callback_query" in u:
                    cq = u["callback_query"]
                    chat_id = cq["message"]["chat"]["id"]
                    mid = cq["message"]["message_id"]
                    if cq["data"] == "expand":
                        api(token, "editMessageText", {
                            "chat_id": chat_id, "message_id": mid, "text": expanded_text,
                            "parse_mode": "HTML",
                            "reply_markup": {"inline_keyboard": [[{"text": "▴ Свернуть", "callback_data": "collapse"}]]}})
                    else:
                        api(token, "editMessageText", {
                            "chat_id": chat_id, "message_id": mid,
                            "text": "Привет! Это демо раскрывающегося меню 👇",
                            "reply_markup": collapsed})
                    api(token, "answerCallbackQuery", {"callback_query_id": cq["id"]}, dry=False)
    except KeyboardInterrupt:
        print("\n👋 Выход.")


# ═════════════════════════════════════════════════════════════════════════════
# РАСШИРЕНИЕ (разведка Bot API 8.2→10.1): жизненный цикл, контент, админка,
# инвайты, монетизация, вебхуки. Простые обёртки над api().
# ═════════════════════════════════════════════════════════════════════════════
def _jarg(v):
    """Распарсить JSON-аргумент (InputMedia, BotCommand[], LabeledPrice[], …)."""
    return json.loads(v) if v else None


def _ok(label):
    print(f"✅ {label}")


def _dump(result):
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ── A. Жизненный цикл сообщений ──────────────────────────────────────────────
def cmd_edit_media(token, args):
    """editMessageMedia — подменить фото/видео в уже отправленном посте."""
    media = {"type": args.type, "media": args.media}
    if args.caption:
        media["caption"] = args.caption
        media["parse_mode"] = "HTML"
    files = None
    if os.path.exists(args.media):                  # локальный файл → attach
        media["media"] = "attach://m0"
        files = {"m0": open(args.media, "rb")}
    p = {"chat_id": args.to, "message_id": args.msg_id, "media": media}
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    api(token, "editMessageMedia", p, files=files, dry=args.dry_run)
    _ok(f"Медиа в #{args.msg_id} заменено")


def cmd_stop_poll(token, args):
    """stopPoll — закрыть опрос и получить финальные результаты."""
    p = {"chat_id": args.to, "message_id": args.msg_id}
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    r = api(token, "stopPoll", p, dry=args.dry_run)
    if not args.dry_run:
        _dump(r)


def cmd_copy_batch(token, args):
    """copyMessages — батч-копирование (до 100, сохраняет альбомы)."""
    ids = [int(x) for x in args.msgs.split(",")]
    p = {"chat_id": args.to, "from_chat_id": args.from_chat, "message_ids": ids}
    if args.remove_caption:
        p["remove_caption"] = True
    if args.silent:
        p["disable_notification"] = True
    api(token, "copyMessages", p, dry=args.dry_run)
    _ok(f"Скопировано {len(ids)} сообщ. → {args.to}")


def cmd_forward_batch(token, args):
    """forwardMessages — батч-пересылка (до 100, строго по возрастанию)."""
    ids = sorted(int(x) for x in args.msgs.split(","))
    p = {"chat_id": args.to, "from_chat_id": args.from_chat, "message_ids": ids}
    if args.thread:
        p["message_thread_id"] = args.thread
    if args.silent:
        p["disable_notification"] = True
    if args.protect:
        p["protect_content"] = True
    api(token, "forwardMessages", p, dry=args.dry_run)
    _ok(f"Переслано {len(ids)} сообщ. → {args.to}")


def cmd_react_del(token, args):
    """deleteMessageReaction — снять одну реакцию бота."""
    api(token, "deleteMessageReaction", {
        "chat_id": args.to, "message_id": args.msg_id,
        "reaction": {"type": "emoji", "emoji": args.reaction}}, dry=args.dry_run)
    _ok(f"Реакция {args.reaction} снята с #{args.msg_id}")


def cmd_react_clear(token, args):
    """deleteAllMessageReactions — снять все реакции."""
    api(token, "deleteAllMessageReactions",
        {"chat_id": args.to, "message_id": args.msg_id}, dry=args.dry_run)
    _ok(f"Все реакции сняты с #{args.msg_id}")


# ── B. Контент ───────────────────────────────────────────────────────────────
def cmd_action(token, args):
    """sendChatAction — индикатор «печатает/загружает…»."""
    p = {"chat_id": args.to, "action": args.action}
    if args.thread:
        p["message_thread_id"] = args.thread
    api(token, "sendChatAction", p, dry=args.dry_run)
    _ok(f"Статус «{args.action}» → {args.to}")


def cmd_venue(token, args):
    """sendVenue — карточка именованного места."""
    p = base_payload(args)
    p.update({"latitude": args.lat, "longitude": args.lon,
              "title": args.title, "address": args.address})
    for k, a in (("foursquare_id", "fsq_id"), ("foursquare_type", "fsq_type"),
                 ("google_place_id", "gplace_id"), ("google_place_type", "gplace_type")):
        if getattr(args, a, None):
            p[k] = getattr(args, a)
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    result = api(token, "sendVenue", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_live_photo(token, args):
    """sendLivePhoto — живое фото (Bot API 10.0). Точные 8 параметров."""
    p = {"chat_id": args.to}
    f = media_file_arg(args.live_photo)
    files = None
    if isinstance(f, tuple):
        files = {"live_photo": f[1]}
    else:
        p["live_photo"] = f
    if args.text:
        p["caption"] = args.text
        p["parse_mode"] = "HTML"
        if args.caption_above:
            p["show_caption_above_media"] = True
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    result = api(token, "sendLivePhoto", p, files=files, dry=args.dry_run)
    _report_sent(result, args)


def cmd_paid_media(token, args):
    """sendPaidMedia — платный пост под Stars (1–25000)."""
    p = base_payload(args)
    p.update({"star_count": args.stars, "media": _jarg(args.media)})
    if args.text:
        p["caption"] = args.text
        p["parse_mode"] = "HTML"
    if args.payload:
        p["payload"] = args.payload
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    result = api(token, "sendPaidMedia", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_invoice(token, args):
    """sendInvoice — инвойс-сообщение (деньги или Stars=XTR)."""
    p = {"chat_id": args.to, "title": args.title, "description": args.desc,
         "payload": args.payload, "currency": args.currency, "prices": _jarg(args.prices)}
    if args.provider_token:
        p["provider_token"] = args.provider_token
    markup = build_markup(args.btn_row, args.btn)
    if markup:
        p["reply_markup"] = markup
    result = api(token, "sendInvoice", p, dry=args.dry_run)
    _report_sent(result, args)


def cmd_gift(token, args):
    """sendGift — подарок юзеру/каналу с баланса Stars."""
    p = {"gift_id": args.gift_id}
    if args.user:
        p["user_id"] = int(args.user)
    if args.to:
        p["chat_id"] = args.to
    if args.pay_for_upgrade:
        p["pay_for_upgrade"] = True
    if args.text:
        p["text"] = args.text
        p["text_parse_mode"] = "HTML"
    api(token, "sendGift", p, dry=args.dry_run)
    _ok(f"Подарок {args.gift_id} отправлен")


# ── C. Файлы / разведка ──────────────────────────────────────────────────────
def cmd_get_file(token, args):
    """getFile — резолв file_id в путь; опц. скачать."""
    r = api(token, "getFile", {"file_id": args.file_id}, dry=args.dry_run)
    if args.dry_run:
        return
    fp = r.get("file_path")
    url = f"https://api.telegram.org/file/bot{token}/{fp}"
    print(f"file_path: {fp}\nurl: {url}")
    if args.download:
        data = requests.get(url, timeout=120).content
        with open(args.download, "wb") as fh:
            fh.write(data)
        _ok(f"Скачано → {args.download} ({len(data)} байт)")


def cmd_user_photos(token, args):
    """getUserProfilePhotos — фото профиля юзера."""
    p = {"user_id": int(args.user)}
    if args.offset:
        p["offset"] = args.offset
    if args.limit:
        p["limit"] = args.limit
    _dump(api(token, "getUserProfilePhotos", p, dry=args.dry_run))


# ── D. Админка чата ──────────────────────────────────────────────────────────
def cmd_admins(token, args):
    p = {"chat_id": args.to}
    if args.with_bots:
        p["return_bots"] = True
    _dump(api(token, "getChatAdministrators", p, dry=args.dry_run))


def cmd_count(token, args):
    r = api(token, "getChatMemberCount", {"chat_id": args.to}, dry=args.dry_run)
    if not args.dry_run:
        print(f"Участников: {r}")


def cmd_member(token, args):
    _dump(api(token, "getChatMember",
              {"chat_id": args.to, "user_id": int(args.user)}, dry=args.dry_run))


def cmd_ban(token, args):
    p = {"chat_id": args.to, "user_id": int(args.user)}
    if args.until:
        p["until_date"] = args.until
    if args.revoke_messages:
        p["revoke_messages"] = True
    api(token, "banChatMember", p, dry=args.dry_run)
    _ok(f"Забанен {args.user}")


def cmd_unban(token, args):
    p = {"chat_id": args.to, "user_id": int(args.user)}
    if args.only_if_banned:
        p["only_if_banned"] = True
    api(token, "unbanChatMember", p, dry=args.dry_run)
    _ok(f"Разбанен {args.user}")


def cmd_restrict(token, args):
    p = {"chat_id": args.to, "user_id": int(args.user), "permissions": _jarg(args.perms)}
    if args.until:
        p["until_date"] = args.until
    api(token, "restrictChatMember", p, dry=args.dry_run)
    _ok(f"Ограничен {args.user}")


def cmd_promote(token, args):
    p = {"chat_id": args.to, "user_id": int(args.user)}
    for flag in ("can_post_messages", "can_edit_messages", "can_delete_messages",
                 "can_pin_messages", "can_manage_chat", "can_invite_users",
                 "can_restrict_members", "can_promote_members", "can_manage_video_chats",
                 "can_manage_direct_messages"):
        if getattr(args, flag, False):
            p[flag] = True
    api(token, "promoteChatMember", p, dry=args.dry_run)
    _ok(f"Права обновлены для {args.user}")


def cmd_perms(token, args):
    p = {"chat_id": args.to, "permissions": _jarg(args.perms)}
    api(token, "setChatPermissions", p, dry=args.dry_run)
    _ok("Права чата обновлены")


def cmd_set_title(token, args):
    api(token, "setChatTitle", {"chat_id": args.to, "title": args.title}, dry=args.dry_run)
    _ok("Название обновлено")


def cmd_set_desc(token, args):
    api(token, "setChatDescription",
        {"chat_id": args.to, "description": args.description or ""}, dry=args.dry_run)
    _ok("Описание обновлено")


def cmd_set_photo(token, args):
    with open(args.photo, "rb") as fh:
        api(token, "setChatPhoto", {"chat_id": args.to}, files={"photo": fh}, dry=args.dry_run)
    _ok("Аватар обновлён")


def cmd_unpin_all(token, args):
    api(token, "unpinAllChatMessages", {"chat_id": args.to}, dry=args.dry_run)
    _ok("Все закрепы сняты")


# ── E. Инвайты / заявки ──────────────────────────────────────────────────────
def cmd_invite_create(token, args):
    p = {"chat_id": args.to}
    if args.name:
        p["name"] = args.name
    if args.expire:
        p["expire_date"] = args.expire
    if args.limit:
        p["member_limit"] = args.limit
    if args.join_request:
        p["creates_join_request"] = True
    r = api(token, "createChatInviteLink", p, dry=args.dry_run)
    if not args.dry_run:
        print(r.get("invite_link"))


def cmd_invite_edit(token, args):
    p = {"chat_id": args.to, "invite_link": args.link}
    if args.name:
        p["name"] = args.name
    if args.expire:
        p["expire_date"] = args.expire
    if args.limit:
        p["member_limit"] = args.limit
    if args.join_request:
        p["creates_join_request"] = True
    _dump(api(token, "editChatInviteLink", p, dry=args.dry_run))


def cmd_invite_revoke(token, args):
    api(token, "revokeChatInviteLink",
        {"chat_id": args.to, "invite_link": args.link}, dry=args.dry_run)
    _ok("Ссылка отозвана")


def cmd_invite_export(token, args):
    r = api(token, "exportChatInviteLink", {"chat_id": args.to}, dry=args.dry_run)
    if not args.dry_run:
        print(r)


def cmd_join_approve(token, args):
    api(token, "approveChatJoinRequest",
        {"chat_id": args.to, "user_id": int(args.user)}, dry=args.dry_run)
    _ok(f"Заявка {args.user} одобрена")


def cmd_join_decline(token, args):
    api(token, "declineChatJoinRequest",
        {"chat_id": args.to, "user_id": int(args.user)}, dry=args.dry_run)
    _ok(f"Заявка {args.user} отклонена")


# ── F. Монетизация (read / link) ─────────────────────────────────────────────
def cmd_invoice_link(token, args):
    p = {"title": args.title, "description": args.desc, "payload": args.payload,
         "currency": args.currency, "prices": _jarg(args.prices)}
    if args.provider_token:
        p["provider_token"] = args.provider_token
    if args.sub_period:
        p["subscription_period"] = args.sub_period
    r = api(token, "createInvoiceLink", p, dry=args.dry_run)
    if not args.dry_run:
        print(r)


def cmd_star_balance(token, args):
    _dump(api(token, "getMyStarBalance", {}, dry=args.dry_run))


def cmd_star_tx(token, args):
    p = {}
    if args.offset:
        p["offset"] = args.offset
    if args.limit:
        p["limit"] = args.limit
    _dump(api(token, "getStarTransactions", p, dry=args.dry_run))


def cmd_gifts(token, args):
    _dump(api(token, "getAvailableGifts", {}, dry=args.dry_run))


# ── G. Бот-конфиг / вебхуки ──────────────────────────────────────────────────
def cmd_set_commands(token, args):
    p = {"commands": _jarg(args.commands)}
    if args.scope:
        p["scope"] = _jarg(args.scope)
    if args.lang:
        p["language_code"] = args.lang
    api(token, "setMyCommands", p, dry=args.dry_run)
    _ok("Меню команд обновлено")


def cmd_menu_button(token, args):
    p = {"chat_id": args.to} if args.to else {}
    p["menu_button"] = _jarg(args.button)
    api(token, "setChatMenuButton", p, dry=args.dry_run)
    _ok("Кнопка меню обновлена")


def cmd_webhook_set(token, args):
    p = {"url": args.url}
    if args.secret:
        p["secret_token"] = args.secret
    if args.allowed:
        p["allowed_updates"] = _jarg(args.allowed)
    if args.drop_pending:
        p["drop_pending_updates"] = True
    if args.max_conn:
        p["max_connections"] = args.max_conn
    if args.ip:
        p["ip_address"] = args.ip
    api(token, "setWebhook", p, dry=args.dry_run)
    _ok(f"Вебхук установлен: {args.url or '(снят)'}")


def cmd_webhook_delete(token, args):
    p = {}
    if args.drop_pending:
        p["drop_pending_updates"] = True
    api(token, "deleteWebhook", p, dry=args.dry_run)
    _ok("Вебхук снят (long-polling доступен)")


def cmd_webhook_info(token, args):
    _dump(api(token, "getWebhookInfo", {}, dry=args.dry_run))


# ── H. Rich draft / inline ───────────────────────────────────────────────────
def cmd_rich_draft(token, args):
    """sendRichMessageDraft — стриминговое rich-превью (только личка)."""
    md = read_text(args)
    if getattr(args, "md", None):
        md = args.md
    if getattr(args, "md_file", None):
        with open(args.md_file, encoding="utf-8") as fh:
            md = fh.read()
    p = {"chat_id": args.to, "draft_id": args.draft_id}
    p["rich_message"] = _jarg(args.rich_json) if args.rich_json else {"markdown": md}
    api(token, "sendRichMessageDraft", p, dry=args.dry_run)
    _ok(f"Rich-draft #{args.draft_id} отправлен")


def cmd_prep_inline(token, args):
    """savePreparedInlineMessage — пред-сохранить shareable inline-результат."""
    p = {"user_id": int(args.user), "result": _jarg(args.result)}
    for flag in ("allow_user", "allow_group", "allow_channel"):
        if getattr(args, flag, False):
            p[{"allow_user": "allow_user_chats", "allow_group": "allow_group_chats",
               "allow_channel": "allow_channel_chats"}[flag]] = True
    _dump(api(token, "savePreparedInlineMessage", p, dry=args.dry_run))


# ═════════════════════════════════════════════════════════════════════════════
# ПОЛНОЕ ПОКРЫТИЕ Bot API — data-driven реестр оставшихся методов.
# Каждая запись: (cmd, method, help, params, show, okmsg)
#   params: список (flag, api_key, kind, required); kind: s=str i=int b=bool j=json f=file
#   show=True → печатать JSON-ответ; иначе _ok(okmsg).
# Генерация подпарсеров и диспетча — в register_simple()/main().
# ═════════════════════════════════════════════════════════════════════════════
def _simple(method, spec, show=False, okmsg=None):
    def h(token, args):
        p, files = {}, {}
        for flag, key, kind, _req in spec:
            v = getattr(args, flag.replace("-", "_"), None)
            if kind == "b":
                if v:
                    p[key] = True
                continue
            if v is None:
                continue
            if kind == "j":
                p[key] = _jarg(v)
            elif kind == "f":
                if os.path.exists(v):
                    files[key] = open(v, "rb")
                else:
                    p[key] = v
            else:
                p[key] = v
        r = api(token, method, p, files=files or None, dry=args.dry_run)
        if args.dry_run:
            return
        if show:
            _dump(r)
        else:
            _ok(okmsg or f"{method} ✓")
    return h


# chat=("to","chat_id","s",True); user=("user","user_id","i",True); biz=("biz","business_connection_id","s",True)
REGISTRY = [
    # ── Профиль/конфиг бота ──────────────────────────────────────────────
    ("set-name", "setMyName", "Имя бота (+локализация)", [("name", "name", "s", False), ("lang", "language_code", "s", False)], False, "Имя бота обновлено"),
    ("get-name", "getMyName", "Текущее имя бота", [("lang", "language_code", "s", False)], True, None),
    ("set-bot-desc", "setMyDescription", "Описание бота (в пустом чате)", [("description", "description", "s", False), ("lang", "language_code", "s", False)], False, "Описание обновлено"),
    ("get-bot-desc", "getMyDescription", "Текущее описание бота", [("lang", "language_code", "s", False)], True, None),
    ("set-bot-short", "setMyShortDescription", "Краткое описание (профиль/шеринг)", [("description", "short_description", "s", False), ("lang", "language_code", "s", False)], False, "Краткое описание обновлено"),
    ("get-bot-short", "getMyShortDescription", "Текущее краткое описание", [("lang", "language_code", "s", False)], True, None),
    ("get-commands", "getMyCommands", "Текущее меню команд", [("scope", "scope", "j", False), ("lang", "language_code", "s", False)], True, None),
    ("del-commands", "deleteMyCommands", "Удалить меню команд", [("scope", "scope", "j", False), ("lang", "language_code", "s", False)], False, "Меню команд удалено"),
    ("get-menu-button", "getChatMenuButton", "Текущая кнопка меню", [("to", "chat_id", "s", False)], True, None),
    ("set-default-rights", "setMyDefaultAdministratorRights", "Дефолтные admin-права бота", [("rights", "rights", "j", False), ("for-channels", "for_channels", "b", False)], False, "Дефолтные права обновлены"),
    ("get-default-rights", "getMyDefaultAdministratorRights", "Дефолтные admin-права", [("for-channels", "for_channels", "b", False)], True, None),
    ("set-bot-photo", "setMyProfilePhoto", "Фото профиля бота", [("photo", "photo", "j", True)], False, "Фото профиля обновлено"),
    ("del-bot-photo", "removeMyProfilePhoto", "Удалить фото профиля бота", [], False, "Фото профиля удалено"),
    ("logout", "logOut", "Выход из облачного сервера (миграция)", [], False, "logOut выполнен"),
    ("close-bot", "close", "Закрыть инстанс (миграция на локальный сервер)", [], False, "close выполнен"),

    # ── Модерация+ ───────────────────────────────────────────────────────
    ("set-admin-title", "setChatAdministratorCustomTitle", "Звание админу", [("to", "chat_id", "s", True), ("user", "user_id", "i", True), ("title", "custom_title", "s", True)], False, "Звание установлено"),
    ("ban-channel", "banChatSenderChat", "Бан канала-отправителя (спам)", [("to", "chat_id", "s", True), ("sender-chat", "sender_chat_id", "i", True)], False, "Канал-отправитель забанен"),
    ("unban-channel", "unbanChatSenderChat", "Разбан канала-отправителя", [("to", "chat_id", "s", True), ("sender-chat", "sender_chat_id", "i", True)], False, "Канал-отправитель разбанен"),
    ("set-member-tag", "setChatMemberTag", "Тег обычному участнику", [("to", "chat_id", "s", True), ("user", "user_id", "i", True), ("tag", "tag", "s", False)], False, "Тег установлен"),

    # ── Чат+ ─────────────────────────────────────────────────────────────
    ("del-photo", "deleteChatPhoto", "Удалить аватар чата", [("to", "chat_id", "s", True)], False, "Аватар удалён"),
    ("leave", "leaveChat", "Бот покидает чат", [("to", "chat_id", "s", True)], False, "Бот покинул чат"),
    ("set-chat-stickers", "setChatStickerSet", "Привязать стикер-пак к супергруппе", [("to", "chat_id", "s", True), ("set-name", "sticker_set_name", "s", True)], False, "Пак привязан"),
    ("del-chat-stickers", "deleteChatStickerSet", "Отвязать стикер-пак супергруппы", [("to", "chat_id", "s", True)], False, "Пак отвязан"),
    ("user-boosts", "getUserChatBoosts", "Бусты юзера в чате", [("to", "chat_id", "s", True), ("user", "user_id", "i", True)], True, None),

    # ── Подписочные инвайты (монетизация канала) ─────────────────────────
    ("sub-invite-create", "createChatSubscriptionInviteLink", "Платная Stars-подписка на канал", [("to", "chat_id", "s", True), ("period", "subscription_period", "i", True), ("price", "subscription_price", "i", True), ("name", "name", "s", False)], True, None),
    ("sub-invite-edit", "editChatSubscriptionInviteLink", "Правка названия подписочной ссылки", [("to", "chat_id", "s", True), ("link", "invite_link", "s", True), ("name", "name", "s", False)], True, None),

    # ── Монетизация+ / подарки ───────────────────────────────────────────
    ("refund", "refundStarPayment", "Возврат Stars за платёж", [("user", "user_id", "i", True), ("charge-id", "telegram_payment_charge_id", "s", True)], False, "Возврат выполнен"),
    ("star-sub", "editUserStarSubscription", "Отмена/возобновление Stars-подписки", [("user", "user_id", "i", True), ("charge-id", "telegram_payment_charge_id", "s", True), ("cancel", "is_canceled", "b", False)], False, "Подписка обновлена"),
    ("gift-premium", "giftPremiumSubscription", "Подарить Premium за Stars", [("user", "user_id", "i", True), ("months", "month_count", "i", True), ("star-count", "star_count", "i", True), ("text", "text", "s", False)], False, "Premium подарен"),
    ("user-gifts", "getUserGifts", "Подарки юзера", [("user", "user_id", "i", True), ("offset", "offset", "s", False), ("limit", "limit", "i", False)], True, None),
    ("chat-gifts", "getChatGifts", "Подарки канала", [("to", "chat_id", "s", True), ("offset", "offset", "s", False), ("limit", "limit", "i", False)], True, None),
    ("gift-convert", "convertGiftToStars", "Конвертировать подарок в Stars (бизнес)", [("biz", "business_connection_id", "s", True), ("owned-gift-id", "owned_gift_id", "s", True)], False, "Подарок конвертирован"),
    ("gift-upgrade", "upgradeGift", "Апгрейд подарка до уникального (бизнес)", [("biz", "business_connection_id", "s", True), ("owned-gift-id", "owned_gift_id", "s", True), ("keep-details", "keep_original_details", "b", False), ("star-count", "star_count", "i", False)], False, "Подарок апгрейднут"),
    ("gift-transfer", "transferGift", "Передать уникальный подарок (бизнес)", [("biz", "business_connection_id", "s", True), ("owned-gift-id", "owned_gift_id", "s", True), ("user", "new_owner_chat_id", "i", True), ("star-count", "star_count", "i", False)], False, "Подарок передан"),

    # ── Форум-топики ─────────────────────────────────────────────────────
    ("forum-create", "createForumTopic", "Создать тему форума", [("to", "chat_id", "s", True), ("name", "name", "s", True), ("icon-color", "icon_color", "i", False), ("icon-emoji", "icon_custom_emoji_id", "s", False)], True, None),
    ("forum-edit", "editForumTopic", "Переименовать/сменить иконку темы", [("to", "chat_id", "s", True), ("thread", "message_thread_id", "i", True), ("name", "name", "s", False), ("icon-emoji", "icon_custom_emoji_id", "s", False)], False, "Тема обновлена"),
    ("forum-close", "closeForumTopic", "Закрыть тему", [("to", "chat_id", "s", True), ("thread", "message_thread_id", "i", True)], False, "Тема закрыта"),
    ("forum-reopen", "reopenForumTopic", "Открыть тему", [("to", "chat_id", "s", True), ("thread", "message_thread_id", "i", True)], False, "Тема открыта"),
    ("forum-delete", "deleteForumTopic", "Удалить тему со всеми сообщениями", [("to", "chat_id", "s", True), ("thread", "message_thread_id", "i", True)], False, "Тема удалена"),
    ("forum-unpin-all", "unpinAllForumTopicMessages", "Снять все закрепы в теме", [("to", "chat_id", "s", True), ("thread", "message_thread_id", "i", True)], False, "Закрепы темы сняты"),
    ("forum-icons", "getForumTopicIconStickers", "Доступные иконки тем", [], True, None),
    ("gen-edit", "editGeneralForumTopic", "Переименовать тему General", [("to", "chat_id", "s", True), ("name", "name", "s", True)], False, "General переименован"),
    ("gen-close", "closeGeneralForumTopic", "Закрыть General", [("to", "chat_id", "s", True)], False, "General закрыт"),
    ("gen-reopen", "reopenGeneralForumTopic", "Открыть General", [("to", "chat_id", "s", True)], False, "General открыт"),
    ("gen-hide", "hideGeneralForumTopic", "Скрыть General", [("to", "chat_id", "s", True)], False, "General скрыт"),
    ("gen-unhide", "unhideGeneralForumTopic", "Показать General", [("to", "chat_id", "s", True)], False, "General показан"),

    # ── Игры ─────────────────────────────────────────────────────────────
    ("send-game", "sendGame", "Отправить игру", [("to", "chat_id", "i", True), ("game", "game_short_name", "s", True)], True, None),
    ("game-score", "setGameScore", "Установить счёт игрока", [("user", "user_id", "i", True), ("score", "score", "i", True), ("to", "chat_id", "i", False), ("msg-id", "message_id", "i", False), ("force", "force", "b", False)], False, "Счёт установлен"),
    ("game-scores", "getGameHighScores", "Таблица рекордов", [("user", "user_id", "i", True), ("to", "chat_id", "i", False), ("msg-id", "message_id", "i", False)], True, None),

    # ── Верификация (орг-верификатор) ────────────────────────────────────
    ("verify-user", "verifyUser", "Верифицировать юзера", [("user", "user_id", "i", True), ("description", "custom_description", "s", False)], False, "Юзер верифицирован"),
    ("verify-chat", "verifyChat", "Верифицировать чат", [("to", "chat_id", "s", True), ("description", "custom_description", "s", False)], False, "Чат верифицирован"),
    ("unverify-user", "removeUserVerification", "Снять верификацию юзера", [("user", "user_id", "i", True)], False, "Верификация снята"),
    ("unverify-chat", "removeChatVerification", "Снять верификацию чата", [("to", "chat_id", "s", True)], False, "Верификация снята"),

    # ── Managed-боты ─────────────────────────────────────────────────────
    ("managed-get", "getManagedBotAccessSettings", "Настройки доступа managed-бота", [], True, None),
    ("managed-set", "setManagedBotAccessSettings", "Изменить доступ managed-бота", [("settings", "access_settings", "j", True)], False, "Доступ обновлён"),

    # ── Модерация предложки канала (suggested posts) ─────────────────────
    ("post-approve", "approveSuggestedPost", "Одобрить предложенный пост", [("to", "chat_id", "i", True), ("msg-id", "message_id", "i", True), ("send-date", "send_date", "i", False)], False, "Предложенный пост одобрен"),
    ("post-decline", "declineSuggestedPost", "Отклонить предложенный пост", [("to", "chat_id", "i", True), ("msg-id", "message_id", "i", True), ("comment", "comment", "s", False)], False, "Предложенный пост отклонён"),

    # ── Live-локация ─────────────────────────────────────────────────────
    ("edit-live-loc", "editMessageLiveLocation", "Обновить координаты live-точки", [("to", "chat_id", "s", True), ("msg-id", "message_id", "i", True), ("lat", "latitude", "s", True), ("lon", "longitude", "s", True), ("live", "live_period", "i", False)], False, "Координаты обновлены"),
    ("stop-live-loc", "stopMessageLiveLocation", "Остановить live-локацию", [("to", "chat_id", "s", True), ("msg-id", "message_id", "i", True)], False, "Live-локация остановлена"),

    # ── Live-хендлеры (нужен свежий query_id из listen/webhook) ──────────
    ("answer-inline", "answerInlineQuery", "Ответ на inline-запрос (нужен query_id)", [("query-id", "inline_query_id", "s", True), ("results", "results", "j", True), ("cache-time", "cache_time", "i", False)], False, "Inline-ответ отправлен"),
    ("answer-webapp", "answerWebAppQuery", "Ответ Web App (нужен query_id)", [("query-id", "web_app_query_id", "s", True), ("result", "result", "j", True)], True, None),
    ("answer-shipping", "answerShippingQuery", "Ответ на shipping-запрос", [("query-id", "shipping_query_id", "s", True), ("ok", "ok", "b", False), ("options", "shipping_options", "j", False), ("error", "error_message", "s", False)], False, "Shipping-ответ отправлен"),
    ("answer-precheckout", "answerPreCheckoutQuery", "Подтверждение/отказ оплаты", [("query-id", "pre_checkout_query_id", "s", True), ("ok", "ok", "b", False), ("error", "error_message", "s", False)], False, "Pre-checkout обработан"),
    ("answer-guest", "answerGuestQuery", "Ответ на гостевой запрос", [("query-id", "guest_query_id", "s", True), ("result", "result", "j", False)], True, None),
    ("answer-joinreq-query", "answerChatJoinRequestQuery", "Обработать запрос-заявку", [("query-id", "chat_join_request_query_id", "s", True), ("result", "result", "j", False)], True, None),
    ("join-webapp", "sendChatJoinRequestWebApp", "Mini App перед заявкой", [("query-id", "chat_join_request_query_id", "s", True), ("title", "title", "s", False)], True, None),
    ("save-kbd-button", "savePreparedKeyboardButton", "Сохранить кнопку клавиатуры Mini App", [("button", "button", "j", True)], True, None),
    ("user-audios", "getUserProfileAudios", "Аудио профиля юзера", [("user", "user_id", "i", True), ("offset", "offset", "i", False), ("limit", "limit", "i", False)], True, None),
    ("msg-draft", "sendMessageDraft", "Стриминговый текстовый черновик", [("to", "chat_id", "s", True), ("draft-id", "draft_id", "i", True), ("text", "text", "s", True)], False, "Черновик отправлен"),

    # ── Чеклисты (бизнес) ────────────────────────────────────────────────
    ("send-checklist", "sendChecklist", "Чеклист от бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("to", "chat_id", "i", True), ("checklist", "checklist", "j", True)], True, None),
    ("edit-checklist", "editMessageChecklist", "Редактировать чеклист", [("biz", "business_connection_id", "s", True), ("to", "chat_id", "i", True), ("msg-id", "message_id", "i", True), ("checklist", "checklist", "j", True)], True, None),

    # ── Бизнес-аккаунты ──────────────────────────────────────────────────
    ("biz-get", "getBusinessConnection", "Инфо о бизнес-подключении", [("biz", "business_connection_id", "s", True)], True, None),
    ("biz-read", "readBusinessMessage", "Отметить сообщение прочитанным", [("biz", "business_connection_id", "s", True), ("to", "chat_id", "i", True), ("msg-id", "message_id", "i", True)], False, "Отмечено прочитанным"),
    ("biz-delete", "deleteBusinessMessages", "Удалить сообщения бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("msgs", "message_ids", "j", True)], False, "Сообщения удалены"),
    ("biz-set-name", "setBusinessAccountName", "Имя бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("first", "first_name", "s", True), ("last", "last_name", "s", False)], False, "Имя обновлено"),
    ("biz-set-username", "setBusinessAccountUsername", "Username бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("username", "username", "s", False)], False, "Username обновлён"),
    ("biz-set-bio", "setBusinessAccountBio", "Bio бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("bio", "bio", "s", False)], False, "Bio обновлено"),
    ("biz-set-photo", "setBusinessAccountProfilePhoto", "Фото бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("photo", "photo", "j", True), ("public", "is_public", "b", False)], False, "Фото обновлено"),
    ("biz-del-photo", "removeBusinessAccountProfilePhoto", "Удалить фото бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("public", "is_public", "b", False)], False, "Фото удалено"),
    ("biz-gift-settings", "setBusinessAccountGiftSettings", "Настройки подарков бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("show-button", "show_gift_button", "b", False), ("accepted", "accepted_gift_types", "j", True)], False, "Настройки подарков обновлены"),
    ("biz-star-balance", "getBusinessAccountStarBalance", "Баланс Stars бизнес-аккаунта", [("biz", "business_connection_id", "s", True)], True, None),
    ("biz-transfer-stars", "transferBusinessAccountStars", "Перевести Stars боту", [("biz", "business_connection_id", "s", True), ("stars", "star_count", "i", True)], False, "Stars переведены"),
    ("biz-gifts", "getBusinessAccountGifts", "Подарки бизнес-аккаунта", [("biz", "business_connection_id", "s", True), ("offset", "offset", "s", False), ("limit", "limit", "i", False)], True, None),

    # ── Истории (бизнес) ─────────────────────────────────────────────────
    ("story-post", "postStory", "Опубликовать историю (бизнес)", [("biz", "business_connection_id", "s", True), ("content", "content", "j", True), ("active-period", "active_period", "i", True), ("caption", "caption", "s", False)], True, None),
    ("story-edit", "editStory", "Редактировать историю", [("biz", "business_connection_id", "s", True), ("story-id", "story_id", "i", True), ("content", "content", "j", True), ("caption", "caption", "s", False)], True, None),
    ("story-delete", "deleteStory", "Удалить историю", [("biz", "business_connection_id", "s", True), ("story-id", "story_id", "i", True)], False, "История удалена"),

    # ── Стикер-сеты ──────────────────────────────────────────────────────
    ("sticker-upload", "uploadStickerFile", "Загрузить файл стикера → file_id", [("user", "user_id", "i", True), ("sticker", "sticker", "f", True), ("format", "sticker_format", "s", True)], True, None),
    ("stickerset-create", "createNewStickerSet", "Создать стикер-набор", [("user", "user_id", "i", True), ("name", "name", "s", True), ("title", "title", "s", True), ("stickers", "stickers", "j", True), ("type", "sticker_type", "s", False)], False, "Набор создан"),
    ("sticker-add", "addStickerToSet", "Добавить стикер в набор", [("user", "user_id", "i", True), ("name", "name", "s", True), ("sticker", "sticker", "j", True)], False, "Стикер добавлен"),
    ("sticker-pos", "setStickerPositionInSet", "Переместить стикер в наборе", [("sticker", "sticker", "s", True), ("position", "position", "i", True)], False, "Позиция изменена"),
    ("sticker-del", "deleteStickerFromSet", "Удалить стикер из набора", [("sticker", "sticker", "s", True)], False, "Стикер удалён"),
    ("sticker-replace", "replaceStickerInSet", "Заменить стикер в наборе", [("user", "user_id", "i", True), ("name", "name", "s", True), ("old-sticker", "old_sticker", "s", True), ("sticker", "sticker", "j", True)], False, "Стикер заменён"),
    ("sticker-emojis", "setStickerEmojiList", "Эмодзи стикера", [("sticker", "sticker", "s", True), ("emojis", "emoji_list", "j", True)], False, "Эмодзи обновлены"),
    ("sticker-keywords", "setStickerKeywords", "Ключевые слова стикера", [("sticker", "sticker", "s", True), ("keywords", "keywords", "j", False)], False, "Ключевые слова обновлены"),
    ("sticker-mask", "setStickerMaskPosition", "Позиция маски стикера", [("sticker", "sticker", "s", True), ("mask", "mask_position", "j", False)], False, "Маска обновлена"),
    ("stickerset-title", "setStickerSetTitle", "Заголовок набора", [("name", "name", "s", True), ("title", "title", "s", True)], False, "Заголовок обновлён"),
    ("stickerset-thumb", "setStickerSetThumbnail", "Миниатюра набора", [("name", "name", "s", True), ("user", "user_id", "i", True), ("thumbnail", "thumbnail", "f", False), ("format", "format", "s", True)], False, "Миниатюра обновлена"),
    ("emoji-set-thumb", "setCustomEmojiStickerSetThumbnail", "Миниатюра custom-emoji набора", [("name", "name", "s", True), ("custom-emoji-id", "custom_emoji_id", "s", False)], False, "Миниатюра обновлена"),
    ("stickerset-del", "deleteStickerSet", "Удалить набор", [("name", "name", "s", True)], False, "Набор удалён"),
    ("stickerset-get", "getStickerSet", "Инфо о наборе", [("name", "name", "s", True)], True, None),
    ("custom-emoji", "getCustomEmojiStickers", "Инфо о custom emoji", [("ids", "custom_emoji_ids", "j", True)], True, None),
]


def register_simple(sub):
    for cmd, method, helptext, spec, _show, _ok in REGISTRY:
        sp = sub.add_parser(cmd, help=f"{helptext} ({method})")
        for flag, _key, kind, req in spec:
            if kind == "b":
                sp.add_argument(f"--{flag}", action="store_true")
            elif kind == "i":
                sp.add_argument(f"--{flag}", type=int, required=req)
            else:
                sp.add_argument(f"--{flag}", required=req)


SIMPLE_DISPATCH = {cmd: _simple(method, spec, show, okmsg)
                   for cmd, method, _h, spec, show, okmsg in REGISTRY}


# ─────────────────────────────────────────────────────────────────────────────
def _report_sent(result, args):
    if args.dry_run:
        return
    mid = result.get("message_id")
    chat = result.get("chat", {})
    uname = chat.get("username")
    where = f"https://t.me/{uname}/{mid}" if uname else f"chat {chat.get('id')} • #{mid}"
    print(f"✅ Отправлено: {where}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        description="Полный инструмент Telegram Bot API (в канал / подписчику — единый --to)",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=EXAMPLES)
    p.add_argument("--token", help="Сам токен (123:ABC) или имя бота из credentials")
    p.add_argument("--dry-run", action="store_true", help="Показать payload, ничего не отправлять")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("me", help="Проверить токен (getMe)")

    s = sub.add_parser("send", help="Отправить сообщение/медиа")
    add_common_send_flags(s)

    s = sub.add_parser("rich", help="Rich-пост Bot API 10.1: таблицы/заголовки/код/details из markdown")
    s.add_argument("--to", required=True, help="@channel / -100<id> / <user_id>")
    s.add_argument("--md", help="Сырой markdown инлайн")
    s.add_argument("--md-file", help="Файл с markdown (## заголовки, | таблицы |, ```код```, <details>)")
    s.add_argument("--text", default="", help="Алиас markdown-текста")
    s.add_argument("--text-file", help="Алиас --md-file")
    s.add_argument("--blocks-json", help="Готовый JSON rich_message ({\"blocks\":[...]}) — escape hatch")
    s.add_argument("--btn", action="append", default=[], metavar="Текст|знач")
    s.add_argument("--btn-row", action="append", default=[], metavar="'Т|з ;; Т|з'")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")
    s.add_argument("--effect")
    s.add_argument("--reply-to", type=int)
    s.add_argument("--thread", type=int)
    s.add_argument("--no-preview", action="store_true")
    s.add_argument("--preview-large", action="store_true")
    s.add_argument("--preview-small", action="store_true")
    s.add_argument("--preview-above", action="store_true")
    s.add_argument("--pin", action="store_true")
    s.add_argument("--pin-loud", action="store_true")

    s = sub.add_parser("album", help="Медиа-группа (2–10 фото/видео)")
    s.add_argument("--to", required=True)
    s.add_argument("files", nargs="+", help="Пути/URL файлов")
    s.add_argument("--text", default="", help="Подпись (на первом элементе)")
    s.add_argument("--plain", action="store_true")
    s.add_argument("--md", action="store_true")
    s.add_argument("--spoiler", action="store_true")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")
    s.add_argument("--thread", type=int)
    s.add_argument("--reply-to", type=int)

    s = sub.add_parser("poll", help="Опрос / викторина (quiz)")
    s.add_argument("--to", required=True)
    s.add_argument("--question", required=True)
    s.add_argument("--option", action="append", required=True, help="Вариант (повторяемый, ≥2)")
    s.add_argument("--public", action="store_true", help="Не анонимный")
    s.add_argument("--multiple", action="store_true", help="Несколько ответов")
    s.add_argument("--quiz", action="store_true", help="Режим викторины")
    s.add_argument("--correct", type=int, default=0, help="Индекс правильного (quiz)")
    s.add_argument("--explanation", help="Пояснение (quiz)")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")
    s.add_argument("--thread", type=int)
    s.add_argument("--reply-to", type=int)

    s = sub.add_parser("dice", help="Кубик/эмодзи-игра 🎲🎯🏀⚽🎳🎰")
    s.add_argument("--to", required=True)
    s.add_argument("--emoji", default="🎲")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")
    s.add_argument("--thread", type=int)
    s.add_argument("--reply-to", type=int)

    s = sub.add_parser("location", help="Геолокация")
    s.add_argument("--to", required=True)
    s.add_argument("--lat", type=float, required=True)
    s.add_argument("--lon", type=float, required=True)
    s.add_argument("--live", type=int, help="live_period сек (60–86400)")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")
    s.add_argument("--thread", type=int)
    s.add_argument("--reply-to", type=int)

    s = sub.add_parser("contact", help="Контакт")
    s.add_argument("--to", required=True)
    s.add_argument("--phone", required=True)
    s.add_argument("--first-name", required=True)
    s.add_argument("--last-name")
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")
    s.add_argument("--thread", type=int)
    s.add_argument("--reply-to", type=int)

    s = sub.add_parser("edit", help="Редактировать текст/подпись/кнопки сообщения бота")
    s.add_argument("--to", required=True)
    s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--text", default="")
    s.add_argument("--text-file")
    s.add_argument("--caption", help="Новая подпись (для медиа)")
    s.add_argument("--plain", action="store_true")
    s.add_argument("--md", action="store_true")
    s.add_argument("--rich", action="store_true", help="Редактировать как rich (markdown→таблицы/код)")
    s.add_argument("--btn", action="append", default=[])
    s.add_argument("--btn-row", action="append", default=[])

    s = sub.add_parser("pin", help="Закрепить сообщение")
    s.add_argument("--to", required=True)
    s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--loud", action="store_true", help="Со звуком")

    s = sub.add_parser("unpin", help="Открепить (без --msg-id → последнее)")
    s.add_argument("--to", required=True)
    s.add_argument("--msg-id", type=int)

    s = sub.add_parser("react", help="Реакция-эмодзи")
    s.add_argument("--to", required=True)
    s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--emoji", nargs="+", default=["👍"])
    s.add_argument("--big", action="store_true")

    s = sub.add_parser("copy", help="Скопировать сообщение (без «переслано от»)")
    s.add_argument("--to", required=True)
    s.add_argument("--from-chat", required=True)
    s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--text", help="Новая подпись")
    s.add_argument("--plain", action="store_true")
    s.add_argument("--md", action="store_true")
    s.add_argument("--btn", action="append", default=[])
    s.add_argument("--btn-row", action="append", default=[])

    s = sub.add_parser("forward", help="Переслать сообщение")
    s.add_argument("--to", required=True)
    s.add_argument("--from-chat", required=True)
    s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true")

    s = sub.add_parser("delete", help="Удалить сообщения")
    s.add_argument("--to", required=True)
    s.add_argument("--msg-id", type=int, nargs="+", required=True)

    s = sub.add_parser("broadcast", help="Рассылка по списку подписчиков")
    s.add_argument("--to-file", help="Файл chat_id (по строке; # коммент; id<TAB>name ок)")
    s.add_argument("--to", help="chat_id через запятую")
    s.add_argument("--text", default="")
    s.add_argument("--text-file")
    s.add_argument("--photo", help="Фото (URL/file_id для скорости рассылки)")
    s.add_argument("--plain", action="store_true")
    s.add_argument("--md", action="store_true")
    s.add_argument("--btn", action="append", default=[])
    s.add_argument("--btn-row", action="append", default=[])
    s.add_argument("--silent", action="store_true")
    s.add_argument("--delay", type=float, default=0.05, help="Пауза между отправками, сек")

    s = sub.add_parser("updates", help="Кто писал боту → собрать chat_id (getUpdates)")
    s.add_argument("--out", help="Сохранить список в файл")

    # ── A. Жизненный цикл ────────────────────────────────────────────────
    s = sub.add_parser("edit-media", help="Заменить медиа в отправленном посте (editMessageMedia)")
    s.add_argument("--to", required=True); s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--media", required=True, help="Путь/URL/file_id")
    s.add_argument("--type", default="photo", choices=["photo", "video", "animation", "audio", "document"])
    s.add_argument("--caption"); s.add_argument("--btn", action="append", default=[])
    s.add_argument("--btn-row", action="append", default=[])

    s = sub.add_parser("stop-poll", help="Закрыть опрос и получить результаты (stopPoll)")
    s.add_argument("--to", required=True); s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--btn", action="append", default=[]); s.add_argument("--btn-row", action="append", default=[])

    s = sub.add_parser("copy-batch", help="Батч-копирование сообщений (copyMessages, до 100)")
    s.add_argument("--to", required=True); s.add_argument("--from-chat", required=True)
    s.add_argument("--msgs", required=True, help="id,id,id"); s.add_argument("--remove-caption", action="store_true")
    s.add_argument("--silent", action="store_true")

    s = sub.add_parser("forward-batch", help="Батч-пересылка (forwardMessages, до 100)")
    s.add_argument("--to", required=True); s.add_argument("--from-chat", required=True)
    s.add_argument("--msgs", required=True); s.add_argument("--thread", type=int)
    s.add_argument("--silent", action="store_true"); s.add_argument("--protect", action="store_true")

    s = sub.add_parser("react-del", help="Снять одну реакцию бота (deleteMessageReaction)")
    s.add_argument("--to", required=True); s.add_argument("--msg-id", type=int, required=True)
    s.add_argument("--reaction", required=True, help="эмодзи")

    s = sub.add_parser("react-clear", help="Снять все реакции (deleteAllMessageReactions)")
    s.add_argument("--to", required=True); s.add_argument("--msg-id", type=int, required=True)

    # ── B. Контент ───────────────────────────────────────────────────────
    s = sub.add_parser("action", help="Индикатор «печатает…» (sendChatAction)")
    s.add_argument("--to", required=True)
    s.add_argument("--action", default="typing", choices=["typing", "upload_photo", "record_video",
                   "upload_video", "record_voice", "upload_voice", "upload_document", "choose_sticker",
                   "find_location", "record_video_note", "upload_video_note"])
    s.add_argument("--thread", type=int)

    s = sub.add_parser("venue", help="Карточка места (sendVenue)")
    s.add_argument("--to", required=True); s.add_argument("--lat", type=float, required=True)
    s.add_argument("--lon", type=float, required=True); s.add_argument("--title", required=True)
    s.add_argument("--address", required=True); s.add_argument("--fsq-id"); s.add_argument("--fsq-type")
    s.add_argument("--gplace-id"); s.add_argument("--gplace-type")
    s.add_argument("--btn", action="append", default=[]); s.add_argument("--btn-row", action="append", default=[])
    s.add_argument("--silent", action="store_true"); s.add_argument("--protect", action="store_true")
    s.add_argument("--thread", type=int); s.add_argument("--reply-to", type=int)

    s = sub.add_parser("live-photo", help="Живое фото (sendLivePhoto, Bot API 10.0)")
    s.add_argument("--to", required=True); s.add_argument("--live-photo", required=True, help="Путь/URL/file_id")
    s.add_argument("--text", default=""); s.add_argument("--caption-above", action="store_true")
    s.add_argument("--btn", action="append", default=[]); s.add_argument("--btn-row", action="append", default=[])

    s = sub.add_parser("paid-media", help="Платный пост под Stars (sendPaidMedia)")
    s.add_argument("--to", required=True); s.add_argument("--stars", type=int, required=True, help="1–25000")
    s.add_argument("--media", required=True, help="JSON: InputPaidMedia[]"); s.add_argument("--text", default="")
    s.add_argument("--payload"); s.add_argument("--btn", action="append", default=[])
    s.add_argument("--btn-row", action="append", default=[]); s.add_argument("--silent", action="store_true")
    s.add_argument("--protect", action="store_true"); s.add_argument("--thread", type=int)

    s = sub.add_parser("invoice", help="Инвойс-сообщение (sendInvoice; XTR=Stars)")
    s.add_argument("--to", required=True); s.add_argument("--title", required=True)
    s.add_argument("--desc", required=True); s.add_argument("--payload", required=True)
    s.add_argument("--currency", required=True, help="XTR для Stars"); s.add_argument("--prices", required=True, help="JSON: LabeledPrice[]")
    s.add_argument("--provider-token"); s.add_argument("--btn", action="append", default=[])
    s.add_argument("--btn-row", action="append", default=[])

    s = sub.add_parser("gift", help="Подарок юзеру/каналу (sendGift)")
    s.add_argument("--user"); s.add_argument("--to"); s.add_argument("--gift-id", required=True)
    s.add_argument("--pay-for-upgrade", action="store_true"); s.add_argument("--text")

    # ── C. Файлы / разведка ──────────────────────────────────────────────
    s = sub.add_parser("get-file", help="Резолв file_id → путь, опц. скачать (getFile)")
    s.add_argument("--file-id", required=True); s.add_argument("--download", help="Путь для сохранения")

    s = sub.add_parser("user-photos", help="Фото профиля юзера (getUserProfilePhotos)")
    s.add_argument("--user", required=True); s.add_argument("--offset", type=int); s.add_argument("--limit", type=int)

    # ── D. Админка ───────────────────────────────────────────────────────
    s = sub.add_parser("admins", help="Список админов (getChatAdministrators)")
    s.add_argument("--to", required=True); s.add_argument("--with-bots", action="store_true")

    s = sub.add_parser("count", help="Число участников (getChatMemberCount)")
    s.add_argument("--to", required=True)

    s = sub.add_parser("member", help="Статус участника (getChatMember)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)

    s = sub.add_parser("ban", help="Бан участника (banChatMember)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)
    s.add_argument("--until", type=int, help="until_date (unix ts)"); s.add_argument("--revoke-messages", action="store_true")

    s = sub.add_parser("unban", help="Разбан (unbanChatMember)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)
    s.add_argument("--only-if-banned", action="store_true")

    s = sub.add_parser("restrict", help="Ограничить участника (restrictChatMember)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)
    s.add_argument("--perms", required=True, help="JSON: ChatPermissions"); s.add_argument("--until", type=int)

    s = sub.add_parser("promote", help="Назначить/снять админа (promoteChatMember)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)
    s.add_argument("--can-post", dest="can_post_messages", action="store_true")
    s.add_argument("--can-edit", dest="can_edit_messages", action="store_true")
    s.add_argument("--can-delete", dest="can_delete_messages", action="store_true")
    s.add_argument("--can-pin", dest="can_pin_messages", action="store_true")
    s.add_argument("--can-manage-chat", dest="can_manage_chat", action="store_true")
    s.add_argument("--can-invite", dest="can_invite_users", action="store_true")
    s.add_argument("--can-restrict", dest="can_restrict_members", action="store_true")
    s.add_argument("--can-promote", dest="can_promote_members", action="store_true")
    s.add_argument("--can-manage-video", dest="can_manage_video_chats", action="store_true")
    s.add_argument("--can-manage-dm", dest="can_manage_direct_messages", action="store_true")

    s = sub.add_parser("perms", help="Дефолтные права чата (setChatPermissions)")
    s.add_argument("--to", required=True); s.add_argument("--perms", required=True, help="JSON: ChatPermissions")

    s = sub.add_parser("set-title", help="Переименовать чат (setChatTitle)")
    s.add_argument("--to", required=True); s.add_argument("--title", required=True)

    s = sub.add_parser("set-desc", help="Описание чата (setChatDescription)")
    s.add_argument("--to", required=True); s.add_argument("--description")

    s = sub.add_parser("set-photo", help="Аватар чата (setChatPhoto)")
    s.add_argument("--to", required=True); s.add_argument("--photo", required=True, help="Путь к файлу")

    s = sub.add_parser("unpin-all", help="Снять все закрепы (unpinAllChatMessages)")
    s.add_argument("--to", required=True)

    # ── E. Инвайты / заявки ──────────────────────────────────────────────
    s = sub.add_parser("invite-create", help="Создать инвайт-ссылку (createChatInviteLink)")
    s.add_argument("--to", required=True); s.add_argument("--name"); s.add_argument("--expire", type=int)
    s.add_argument("--limit", type=int); s.add_argument("--join-request", action="store_true")

    s = sub.add_parser("invite-edit", help="Правка инвайт-ссылки (editChatInviteLink)")
    s.add_argument("--to", required=True); s.add_argument("--link", required=True)
    s.add_argument("--name"); s.add_argument("--expire", type=int); s.add_argument("--limit", type=int)
    s.add_argument("--join-request", action="store_true")

    s = sub.add_parser("invite-revoke", help="Отозвать ссылку (revokeChatInviteLink)")
    s.add_argument("--to", required=True); s.add_argument("--link", required=True)

    s = sub.add_parser("invite-export", help="Перегенерировать primary-ссылку (exportChatInviteLink)")
    s.add_argument("--to", required=True)

    s = sub.add_parser("join-approve", help="Одобрить заявку (approveChatJoinRequest)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)

    s = sub.add_parser("join-decline", help="Отклонить заявку (declineChatJoinRequest)")
    s.add_argument("--to", required=True); s.add_argument("--user", required=True)

    # ── F. Монетизация ───────────────────────────────────────────────────
    s = sub.add_parser("invoice-link", help="Pay-ссылка t.me без сообщения (createInvoiceLink)")
    s.add_argument("--title", required=True); s.add_argument("--desc", required=True)
    s.add_argument("--payload", required=True); s.add_argument("--currency", required=True)
    s.add_argument("--prices", required=True, help="JSON: LabeledPrice[]"); s.add_argument("--provider-token")
    s.add_argument("--sub-period", type=int, help="subscription_period сек")

    s = sub.add_parser("star-balance", help="Баланс Stars бота (getMyStarBalance)")

    s = sub.add_parser("star-tx", help="История Stars-транзакций (getStarTransactions)")
    s.add_argument("--offset", type=int); s.add_argument("--limit", type=int)

    s = sub.add_parser("gifts", help="Каталог подарков (getAvailableGifts)")

    # ── G. Конфиг / вебхуки ──────────────────────────────────────────────
    s = sub.add_parser("set-commands", help="Меню слэш-команд бота (setMyCommands)")
    s.add_argument("--commands", required=True, help="JSON: BotCommand[]")
    s.add_argument("--scope", help="JSON: BotCommandScope"); s.add_argument("--lang")

    s = sub.add_parser("menu-button", help="Кнопка меню в поле ввода (setChatMenuButton)")
    s.add_argument("--to"); s.add_argument("--button", required=True, help="JSON: MenuButton")

    s = sub.add_parser("webhook-set", help="Установить вебхук (setWebhook)")
    s.add_argument("--url", required=True, help="пустая строка = снять"); s.add_argument("--secret")
    s.add_argument("--allowed", help="JSON-массив allowed_updates"); s.add_argument("--drop-pending", action="store_true")
    s.add_argument("--max-conn", type=int); s.add_argument("--ip")

    s = sub.add_parser("webhook-delete", help="Снять вебхук → long-polling (deleteWebhook)")
    s.add_argument("--drop-pending", action="store_true")

    s = sub.add_parser("webhook-info", help="Статус вебхука (getWebhookInfo) — почему нет апдейтов")

    # ── H. Rich draft / inline ───────────────────────────────────────────
    s = sub.add_parser("rich-draft", help="Стриминговое rich-превью, только личка (sendRichMessageDraft)")
    s.add_argument("--to", required=True); s.add_argument("--draft-id", type=int, required=True)
    s.add_argument("--md"); s.add_argument("--md-file"); s.add_argument("--text", default="")
    s.add_argument("--text-file"); s.add_argument("--rich-json", help="Готовый JSON rich_message")

    s = sub.add_parser("prep-inline", help="Пред-сохранить inline-результат (savePreparedInlineMessage)")
    s.add_argument("--user", required=True); s.add_argument("--result", required=True, help="JSON: InlineQueryResult")
    s.add_argument("--allow-user", action="store_true"); s.add_argument("--allow-group", action="store_true")
    s.add_argument("--allow-channel", action="store_true")

    s = sub.add_parser("link", help="t.me-ссылка на пост")
    s.add_argument("--to", required=True)
    s.add_argument("--msg-id", type=int, required=True)

    s = sub.add_parser("listen", help="Демо живого бота с раскрывающимся меню")

    register_simple(sub)   # ← +все методы из REGISTRY (полное покрытие Bot API)
    return p


def main():
    args = build_parser().parse_args()
    # link для публичного канала может работать без токена
    needs_token = not (args.cmd == "link" and not args.token)
    token = load_token(args.token) if (args.token or needs_token) else None
    if needs_token and not token:
        token = load_token(args.token)

    dispatch = {
        "me": cmd_me, "send": cmd_send, "rich": cmd_rich, "album": cmd_album,
        "poll": cmd_poll, "dice": cmd_dice,
        "location": cmd_location, "contact": cmd_contact, "edit": cmd_edit, "pin": cmd_pin,
        "unpin": cmd_unpin, "react": cmd_react, "copy": cmd_copy, "forward": cmd_forward,
        "delete": cmd_delete, "broadcast": cmd_broadcast, "updates": cmd_updates,
        "link": cmd_link, "listen": cmd_listen,
        # A. жизненный цикл
        "edit-media": cmd_edit_media, "stop-poll": cmd_stop_poll, "copy-batch": cmd_copy_batch,
        "forward-batch": cmd_forward_batch, "react-del": cmd_react_del, "react-clear": cmd_react_clear,
        # B. контент
        "action": cmd_action, "venue": cmd_venue, "live-photo": cmd_live_photo,
        "paid-media": cmd_paid_media, "invoice": cmd_invoice, "gift": cmd_gift,
        # C. файлы/разведка
        "get-file": cmd_get_file, "user-photos": cmd_user_photos,
        # D. админка
        "admins": cmd_admins, "count": cmd_count, "member": cmd_member, "ban": cmd_ban,
        "unban": cmd_unban, "restrict": cmd_restrict, "promote": cmd_promote, "perms": cmd_perms,
        "set-title": cmd_set_title, "set-desc": cmd_set_desc, "set-photo": cmd_set_photo,
        "unpin-all": cmd_unpin_all,
        # E. инвайты/заявки
        "invite-create": cmd_invite_create, "invite-edit": cmd_invite_edit,
        "invite-revoke": cmd_invite_revoke, "invite-export": cmd_invite_export,
        "join-approve": cmd_join_approve, "join-decline": cmd_join_decline,
        # F. монетизация
        "invoice-link": cmd_invoice_link, "star-balance": cmd_star_balance,
        "star-tx": cmd_star_tx, "gifts": cmd_gifts,
        # G. конфиг/вебхуки
        "set-commands": cmd_set_commands, "menu-button": cmd_menu_button,
        "webhook-set": cmd_webhook_set, "webhook-delete": cmd_webhook_delete,
        "webhook-info": cmd_webhook_info,
        # H. rich draft / inline
        "rich-draft": cmd_rich_draft, "prep-inline": cmd_prep_inline,
    }
    dispatch.update(SIMPLE_DISPATCH)   # ← все методы из REGISTRY
    try:
        dispatch[args.cmd](token, args)
    except TelegramError as e:
        sys.exit(f"❌ {e}")


EXAMPLES = """
Примеры:
  # проверить токен
  python tg_bot.py --token DEMO5 me

  # ── В КАНАЛ (бот-админ) ──
  # пост с форматированием + раскрывающийся блок + кнопка на пост
  python tg_bot.py --token DEMO5 send --to @yourchannel \\
      --text "<b>Заголовок</b>\\n<blockquote expandable>Длинный текст, скрыт под «показать ещё»</blockquote>" \\
      --btn "Открыть пост|https://t.me/your_username/123" --pin

  # фото-пост со спойлером, подпись над фото, две кнопки в ряд
  python tg_bot.py --token DEMO5 send --to @yourchannel --photo cover.jpg \\
      --text "Подпись" --spoiler --caption-above \\
      --btn-row "Сайт|https://your-domain.com ;; Промокод|copy:AI2026"

  # видео в канал
  python tg_bot.py --token DEMO5 send --to @yourchannel --video clip.mp4 --text "Запись"

  # ── RICH-ПОСТ (Bot API 10.1): таблицы / заголовки / код / списки из markdown ──
  python tg_bot.py --token ACADEMY rich --to @yourchannel --md-file post.md
  python tg_bot.py --token ACADEMY rich --to 123456789 --md "## Итоги
| Метрика | Знач |
|---|---|
| MRR | 600K |
- [x] таблица рендерится нативно" --btn "Подробнее|https://your-domain.com"

  # альбом из 3 фото
  python tg_bot.py --token DEMO5 album --to @yourchannel a.jpg b.jpg c.jpg --text "Галерея"

  # опрос и викторина
  python tg_bot.py --token DEMO5 poll --to @yourchannel --question "Идём?" --option Да --option Нет
  python tg_bot.py --token DEMO5 poll --to @yourchannel --quiz --question "2+2?" \\
      --option 3 --option 4 --correct 1 --explanation "Это четыре"

  # ── ПОДПИСЧИКУ В ЛИЧКУ / РАССЫЛКА ──
  # одному подписчику (он должен был нажать /start у бота)
  python tg_bot.py --token COMPANY_SALES send --to 123456789 --text "Личное сообщение"

  # собрать chat_id написавших боту
  python tg_bot.py --token COMPANY_SALES updates --out subs.txt

  # рассылка по сегменту с кнопкой (DRY — проверить без отправки)
  python tg_bot.py --token COMPANY_SALES --dry-run broadcast --to-file subs.txt \\
      --text "<b>Анонс</b> конференции 👇" --btn "Регистрация|https://your-domain.com/conf"

  # ── РЕДАКТИРОВАНИЕ / ИНТЕРАКТИВ ──
  # поменять кнопки у уже опубликованного БОТОМ поста
  python tg_bot.py --token DEMO5 edit --to @yourchannel --msg-id 123 \\
      --btn "Новая ссылка|https://t.me/your_username/130"

  # живой бот с раскрывающимся меню (callback-кнопки) для подписчиков
  python tg_bot.py --token DEMO5 listen
"""

if __name__ == "__main__":
    main()
