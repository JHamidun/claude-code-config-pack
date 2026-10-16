#!/usr/bin/env python3
"""Outlook на этой машине через COM: почта, черновики в ветке, отложенная отправка,
вложения, флажки, категории, календарь, адресная книга.

Работает с УСТАНОВЛЕННЫМ классическим Outlook (учётка по умолчанию), пароль не нужен.
Нужны Windows и pywin32. Сетевой exchangelib не работает — не пробовать (см. /outlook).

ЧТЕНИЕ
    accounts                              учётки и хранилища
    folders                               дерево папок со счётчиками
    list   [--folder inbox] [--limit 15] [--unread] [--days N] [--ids]
    search "запрос" [--field subject|body|from|to|email] [--folder ...] [--days N]   email — SMTP отправителя
    read   <ref> [--full] [--html]
    thread <ref>                          все письма беседы (где лежат, кто, когда)
    outbox                                исходящие ТАБЛИЦЕЙ: отложено / в очереди / НЕ поставлено (письма не открываются)
    drafts [--limit 15]
    attachments <ref> [--save DIR] [--all]
ЧЕРНОВИКИ (ничего не отправляют)
    reply  <ref> [--all] (--text T | --text-file F | --html-file F) [--attach F]... [--replace-prev] [--show]
    new    --to A [--cc B] [--bcc C] --subject S (--text|--text-file|--html-file) [--attach F]... [--no-signature]
    edit   <ref> [--attach F] [--remove-attach ИМЯ] [--replace-attach ИМЯ=ФАЙЛ] [--subject S] [--to A] [--cc B]
           [--prepend-text T | --prepend-html F] [--yes — если письмо в «Исходящих»: снять, поправить, вернуть]
НАРУЖУ (только с --yes; без него — сухой прогон)
    schedule   <ref> --at "ГГГГ-ММ-ДД ЧЧ:ММ" [--yes]   отложенная отправка (время машины = МСК)
    unschedule <ref> [--keep-time]                      снять отложку: «Исходящие» → «Черновики», время сбрасывается
    send       <ref> [--yes]                            отправить черновик сейчас
ПОРЯДОК
    move <ref> --to ПАПКА · flag <ref> [--when today|tomorrow|week|nextweek|nodate|done] [--clear]
    category <ref> (--add X | --remove X) · mark <ref> (--read | --unread) · show <ref>
КАЛЕНДАРЬ И ЛЮДИ
    events [--days 7] [--from ГГГГ-ММ-ДД] · invites [--days 30]   неотвеченные приглашения
    event-new --subject S --start "ГГГГ-ММ-ДД ЧЧ:ММ" (--end ... | --minutes 60) [--location L] [--text T]
              [--attendees a@x,b@y] [--optional c@z] [--send --yes]
    free [ГГГГ-ММ-ДД] [--who адрес]       занятость по получасам
    whois "имя или адрес"                 карточка из адресной книги Exchange

<ref> — номер из последней выдачи этой же папки (--folder), EntryID, или выбор по
теме: --subject "часть темы" [--from "часть имени"] (берётся самое свежее письмо).
"""
from __future__ import annotations

import argparse
import datetime as dt
import html as htmllib
import os
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# OlDefaultFolders
FOLDERS = {"inbox": 6, "sent": 5, "outbox": 4, "drafts": 16, "deleted": 3, "junk": 23,
           "calendar": 9, "contacts": 10, "tasks": 13}
RU_ALIASES = {"входящие": "inbox", "отправленные": "sent", "исходящие": "outbox",
              "черновики": "drafts", "удаленные": "deleted", "удалённые": "deleted",
              "нежелательная почта": "junk", "календарь": "calendar"}
OL_MAIL = 43
# «Нет значения» у дат Outlook — 01.01.4501 (DeferredDeliveryTime, ExpiryTime, TaskDueDate…).
NO_DATE_YEAR = 4500
PT = "http://schemas.microsoft.com/mapi/proptag/"
P_FLAGS = PT + "0x0E070003"        # PR_MESSAGE_FLAGS; бит 0x4 (SUBMIT) = «поставлено в отправку»
P_DISPLAY_TO = PT + "0x0E04001F"
P_SENDER_SMTP = PT + "0x5D01001F"  # SMTP отправителя; у своих SenderEmailAddress — путь X500
MSGFLAG_SUBMIT = 0x4
# Расширения, на которых Outlook при отправке показывает МОДАЛЬНОЕ окно «потенциально небезопасные
# вложения»: Send() виснет, пока человек не ответит. Такие файлы кладём в .zip.
UNSAFE_EXT = {".py", ".pyw", ".js", ".vbs", ".bat", ".cmd", ".exe", ".ps1", ".msi", ".jar",
              ".scr", ".hta", ".lnk", ".dll", ".com", ".reg"}
STIL = "font-family:Calibri,sans-serif;font-size:11pt"

# Номер письма в <ref> — это номер из ПОСЛЕДНЕЙ выдачи (list/search/drafts/outbox/thread),
# а не позиция в папке: с --unread, --days и поиском нумерация папки не совпала бы.
CACHE = pathlib.Path(__file__).resolve().parent.parent / ".last_list.json"
CACHE_TTL_H = 12


def remember(ids: list, label: str) -> None:
    try:
        import json
        CACHE.write_text(json.dumps({"at": dt.datetime.now().isoformat(timespec="seconds"),
                                     "label": label, "ids": ids}), encoding="utf-8")
    except Exception:
        pass  # кэш — удобство, без него номера считаются по порядку папки


def recall():
    try:
        import json
        d = json.loads(CACHE.read_text(encoding="utf-8"))
        at = dt.datetime.fromisoformat(d["at"])
        if dt.datetime.now() - at > dt.timedelta(hours=CACHE_TTL_H):
            return None
        return d
    except Exception:
        return None


# ------------------------------------------------------------------ основа

def outlook():
    try:
        import win32com.client as win32
    except ImportError:
        raise SystemExit("нет pywin32: pip install pywin32")
    return win32.Dispatch("Outlook.Application")


def mapi(app=None):
    return (app or outlook()).GetNamespace("MAPI")


def local(t) -> dt.datetime | None:
    """pywin32 отдаёт время с меткой +00:00, а на деле это МЕСТНОЕ время машины (МСК).
    Метку срезаем, чтобы не пересчитывать его второй раз."""
    if t is None:
        return None
    try:
        v = dt.datetime(t.year, t.month, t.day, t.hour, t.minute, t.second)
    except Exception:
        return None
    return None if v.year > NO_DATE_YEAR else v


def fmt(t) -> str:
    v = local(t)
    return v.strftime("%Y-%m-%d %H:%M") if v else "—"


def to_ole(d: dt.datetime) -> dt.datetime:
    """Время, которое ПИШЕМ в Outlook (отложка, начало/конец встречи, FreeBusy).

    pywin32 переводит ЛЮБОЙ datetime в UTC, а Outlook читает полученное число как МЕСТНОЕ:
    наивное «08:00» ложится как 05:00 (−3 ч; проверено 04.10 на тестовом письме — и наивное,
    и aware с +03:00 дали 05:00). Верно — те же цифры настенных часов с меткой UTC."""
    return dt.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second, tzinfo=dt.timezone.utc)


def since_utc(days: int) -> str:
    """Начало местных суток N дней назад — строкой для DASL. DASL сравнивает в UTC, а
    «мм/дд/гггг» при русской локали читается как дд/мм и молча отдаёт почти всё."""
    mid = (dt.datetime.now() - dt.timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    return mid.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def jet_dt(d: dt.datetime) -> str:
    """Дата для Jet-фильтра (Restrict по [Start] и т.п.): местное время в формате локали
    Windows (здесь ru-RU «дд.мм.гггг чч:мм», без секунд). Другая локаль — OUTLOOK_JET_DATE_FMT."""
    return d.strftime(os.environ.get("OUTLOOK_JET_DATE_FMT", "%d.%m.%Y %H:%M"))


def rus_day(d: dt.datetime) -> str:
    return ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")[d.weekday()]


def is_outbox(folder) -> bool:
    return folder.Name.lower() in ("исходящие", "outbox")


def outbox_rows(ns) -> list:
    """«Исходящие» БЕЗ открытия писем — только таблица содержимого.

    Получение объекта письма из «Исходящих» (GetItemFromID, перебор Items, чтение свойств)
    снимает его с отправки: бит SUBMIT флагов гаснет, значок становится «черновиком», и
    отложенное письмо утром не уходит (так однажды чуть не пропало письмо клиенту). Таблица этого
    не делает. Время по имени столбца — местное; proptag-столбцы — UTC."""
    t = ns.GetDefaultFolder(4).GetTable()
    t.Columns.RemoveAll()
    for c in ("Subject", "EntryID", "DeferredDeliveryTime", "LastModificationTime", P_FLAGS, P_DISPLAY_TO):
        t.Columns.Add(c)
    rows = []
    while not t.EndOfTable:
        r = t.GetNextRow()
        row = {}
        for key, col in (("subject", "Subject"), ("eid", "EntryID"), ("defer", "DeferredDeliveryTime"),
                         ("mod", "LastModificationTime"), ("flags", P_FLAGS), ("to", P_DISPLAY_TO)):
            try:
                row[key] = r[col]
            except Exception:
                row[key] = None
        row["subject"] = row["subject"] or ""
        row["flags"] = row["flags"] or 0
        rows.append(row)
    return rows


def queued_ids(ns) -> set:
    """EntryID писем, которые СЕЙЧАС стоят в «Исходящих» в очереди на отправку."""
    return {r["eid"] for r in outbox_rows(ns) if r["flags"] & MSGFLAG_SUBMIT}


def outbox_state(r, now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now()
    queued = bool(r["flags"] & MSGFLAG_SUBMIT)
    defer = local(r["defer"])
    if queued and defer and defer > now:
        return f"⏰ отложено до {defer:%Y-%m-%d %H:%M} — поставлено в отправку"
    if queued:
        return "в очереди на отправку (уйдёт при ближайшей синхронизации)"
    if defer and defer > now:
        return (f"⚠ время отложки стоит ({defer:%Y-%m-%d %H:%M}), но письмо НЕ поставлено в отправку "
                f"(значок черновика) — само не уйдёт; поставить: schedule … --yes")
    return "⚠ НЕ поставлено в отправку (черновик, лежащий в «Исходящих»)"


def verify_queued(ns, subject: str, at: dt.datetime | None = None) -> bool:
    """Подтверждение отправки/отложки ТОЛЬКО по таблице: письмо с такой темой в «Исходящих»
    с битом SUBMIT (и, если задано, с нужным временем отложки)."""
    for r in outbox_rows(ns):
        if r["subject"] != subject or not r["flags"] & MSGFLAG_SUBMIT:
            continue
        if at is None or local(r["defer"]) == at:
            print(f"  ✓ в «Исходящих»: {outbox_state(r)}")
            return True
    return False


def refuse_unsafe(item) -> None:
    bad = [x.FileName for x, inl in real_attachments(item)
           if not inl and pathlib.Path(x.FileName or "").suffix.lower() in UNSAFE_EXT]
    if bad:
        raise SystemExit(f"  вложения {', '.join(bad)}: при отправке Outlook покажет модальное окно «потенциально "
                         f"небезопасные вложения» и зависнет. Положите их в .zip (edit --replace-attach ИМЯ=файл.zip).")


def get_folder(ns, name: str):
    key = RU_ALIASES.get(name.lower(), name.lower())
    if key in FOLDERS:
        return ns.GetDefaultFolder(FOLDERS[key])
    root = ns.GetDefaultFolder(6).Parent
    stack = [(root, 0)]
    while stack:  # обход на два уровня — глубже рабочие папки не лежат
        f, depth = stack.pop()
        for sub in f.Folders:
            if sub.Name.lower() == name.lower():
                return sub
            if depth < 2:
                stack.append((sub, depth + 1))
    raise SystemExit(f"нет такой папки: {name}")


def sort_key_for(folder) -> str:
    # У календаря нет ReceivedTime — ключ зависит от того, что лежит в папке.
    kind = folder.DefaultItemType
    if kind == 1:
        return "[Start]"
    if kind in (2, 3):
        return "[LastModificationTime]"
    # В «Черновиках» и «Исходящих» ReceivedTime бессмыслен — сортируем по правке.
    return "[LastModificationTime]" if folder.Name.lower() in (
        "черновики", "исходящие", "drafts", "outbox") else "[ReceivedTime]"


def sorted_items(folder):
    # folder.Items при КАЖДОМ обращении — новая коллекция: сортировать сохранённую ссылку.
    items = folder.Items
    items.Sort(sort_key_for(folder), True)
    return items


def smtp_of_sender(m) -> str:
    """У писем изнутри Exchange в SenderEmailAddress лежит LDAP-путь (/O=…).
    Настоящий адрес — через GetExchangeUser(); не вышло — отображаемое имя."""
    try:
        addr = m.SenderEmailAddress or ""
    except Exception:
        addr = ""
    if addr and not addr.startswith("/"):
        return addr
    try:
        eu = m.Sender.GetExchangeUser()
        if eu is not None and eu.PrimarySmtpAddress:
            return eu.PrimarySmtpAddress
    except Exception:
        pass
    try:
        return m.SenderName or "?"
    except Exception:
        return "?"


def pick(app, a, allow_queued: bool = False, queued_needs_yes: bool = True):
    """<ref>: EntryID, номер из последней выдачи или --subject/--from (самое свежее).

    Письмо, стоящее в «Исходящих» в очереди на отправку, открывать НЕЛЬЗЯ: получение его
    объекта снимает письмо с отправки (опыт 04.10). Команды, которые идут на это
    сознательно (schedule, unschedule, edit), передают allow_queued=True; и тогда без --yes письмо
    тоже НЕ открывается (сухой прогон не имеет права снять отправку — поймано тестом 04.10:
    `edit` без --yes снимал письмо с очереди до всякой проверки). unschedule идёт с
    queued_needs_yes=False: это отмена отправки, безопасная сторона."""
    ns = mapi(app)
    folder = get_folder(ns, getattr(a, "folder", "inbox") or "inbox")
    ref = getattr(a, "ref", None)
    subj = (getattr(a, "subject_sel", None) or "").lower()
    sender = (getattr(a, "from_sel", None) or "").lower()
    eid = None
    if ref and len(ref) > 40:
        eid = ref
    elif ref and ref.isdigit():
        n = int(ref)
        cached = recall()
        if cached and 1 <= n <= len(cached["ids"]):
            print(f"  (№{n} из последней выдачи «{cached['label']}» от {cached['at'][11:16]})")
            eid = cached["ids"][n - 1]
        elif is_outbox(folder):
            rows = sorted(outbox_rows(ns), key=lambda r: local(r["mod"]) or dt.datetime.min, reverse=True)
            if not 1 <= n <= len(rows):
                raise SystemExit(f"в «Исходящих» писем: {len(rows)}, номера {n} нет")
            eid = rows[n - 1]["eid"]
        else:
            print(f"  (выдачи в кэше нет — номер {n} считаю по порядку папки «{folder.Name}»)")
            return sorted_items(folder).Item(n)
    elif subj or sender:
        if is_outbox(folder):
            for r in sorted(outbox_rows(ns), key=lambda r: local(r["mod"]) or dt.datetime.min, reverse=True):
                if subj in r["subject"].lower():
                    eid = r["eid"]
                    break
            if eid is None:
                raise SystemExit(f"в «Исходящих» нет письма с темой ~ «{subj}»")
        else:
            n = 0
            for m in sorted_items(folder):
                n += 1
                if n > 2000:
                    break
                try:
                    if subj and subj not in (m.Subject or "").lower():
                        continue
                    if sender and sender not in (getattr(m, "SenderName", "") or "").lower():
                        continue
                    return m
                except Exception:
                    continue
            raise SystemExit(f"в «{folder.Name}» не нашлось письма: тема ~ «{subj}», от ~ «{sender}»")
    else:
        raise SystemExit("укажите письмо: номер из выдачи, EntryID или --subject")
    row = next((r for r in outbox_rows(ns) if r["eid"] == eid and r["flags"] & MSGFLAG_SUBMIT), None)
    if row is not None:
        if not allow_queued:
            raise SystemExit("  письмо стоит в «Исходящих» в очереди на отправку: открытие его через Outlook снимает "
                             "его с очереди. Посмотреть: outbox. Снять отложку: unschedule. Править: edit … --yes.")
        if queued_needs_yes and not getattr(a, "yes", False):
            print(f"  письмо в «Исходящих»: «{row['subject']}» → {row['to']}\n  {outbox_state(row)}")
            raise SystemExit("  действие снимет его с отправки и поставит заново — не открываю без --yes (сухой прогон "
                             "для письма из очереди невозможен: любое открытие снимает очередь). Повторите с --yes.")
    return ns.GetItemFromID(eid)


def mode_for(folder) -> str:
    """Какое время показывать: в «Отправленных» — когда ушло, в «Черновиках» и
    «Исходящих» — когда правили, в остальных — когда пришло."""
    name = folder.Name.lower()
    if name in ("отправленные", "sent items", "sent"):
        return "sent"
    if name in ("черновики", "исходящие", "drafts", "outbox"):
        return "modified"
    return "received"


def line(m, n: int, mode: str = "received") -> str:
    try:
        if m.Class != OL_MAIL:
            when, who = fmt(m.LastModificationTime), ""
        else:
            when = fmt({"sent": m.SentOn, "modified": m.LastModificationTime}.get(mode, m.ReceivedTime))
            who = smtp_of_sender(m) if mode == "received" else f"→ {str(m.To)[:32]}"
        unread = "•" if getattr(m, "UnRead", False) and mode == "received" else " "
        att = f" 📎{m.Attachments.Count}" if m.Attachments.Count else ""
        sched = ""
        if mode == "modified" and m.Class == OL_MAIL and local(m.DeferredDeliveryTime):
            sched = f"  ⏰{fmt(m.DeferredDeliveryTime)}"
        return f"  [{n}] {when}  {who[:34]:<36}{unread} {str(m.Subject)[:56]}{att}{sched}"
    except Exception as e:
        return f"  [{n}] пропущено ({type(e).__name__})"


def show_list(items, limit: int, ids: bool = False, mode: str = "received", label: str = "") -> int:
    n = 0
    seen = []
    for m in items:
        n += 1
        if n > limit:
            n -= 1
            break
        try:
            seen.append(m.EntryID)
        except Exception:
            seen.append("")
        print(line(m, n, mode))
        if ids:
            print(f"        id: {seen[-1]}")
    remember(seen, label)
    return n


def text_to_html(text: str) -> str:
    paras = [p.strip("\n") for p in re.split(r"\n\s*\n", text.strip())]
    out = []
    for p in paras:
        safe = htmllib.escape(p).replace("\n", "<br>")
        out.append(f'<p style="{STIL}">{safe}</p>')
    return "<div>" + "".join(out) + "</div>"


def content_html(a) -> str:
    if getattr(a, "html_file", None):
        return pathlib.Path(a.html_file).read_text(encoding="utf-8")
    if getattr(a, "text_file", None):
        return text_to_html(pathlib.Path(a.text_file).read_text(encoding="utf-8"))
    if getattr(a, "text", None):
        return text_to_html(a.text)
    raise SystemExit("нужен текст: --text, --text-file или --html-file")


def first_line(a) -> str:
    """Первая строка нового текста — по ней узнаются наши прежние черновики."""
    if getattr(a, "text", None):
        src = a.text
    elif getattr(a, "text_file", None):
        src = pathlib.Path(a.text_file).read_text(encoding="utf-8")
    else:
        src = re.sub(r"<[^>]+>", "\n", pathlib.Path(a.html_file).read_text(encoding="utf-8"))
    for ln in src.splitlines():
        if ln.strip():
            return htmllib.unescape(ln.strip())[:80]
    return ""


def insert_after_body(html: str, piece: str) -> str:
    """Вставка сразу после <body>: подпись Outlook и цитата ветки остаются ниже.
    Присваивать Body (простой текст) нельзя — письмо станет plain text, и пропадут
    подпись с логотипом и разметка цитаты."""
    m = re.search(r"<body[^>]*>", html or "", re.I)
    return (html[:m.end()] + piece + html[m.end():]) if m else piece + (html or "")


def attach_all(item, files) -> None:
    for f in files or []:
        p = pathlib.Path(f).resolve()
        if not p.exists():
            raise SystemExit(f"нет файла для вложения: {p}")
        item.Attachments.Add(str(p))
        warn = ("  ⚠ Outlook при отправке покажет окно «небезопасные вложения»; CLI такое не отправит — положите в .zip"
                if p.suffix.lower() in UNSAFE_EXT else "")
        sz = p.stat().st_size
        print(f"  вложено: {p.name} ({f'{sz} Б' if sz < 1024 else f'{sz // 1024} КБ'}){warn}")


def real_attachments(item):
    """(вложение, встроенное_ли). Встроенная картинка подписи: PR_ATTACHMENT_HIDDEN, либо есть
    Content-ID и «cid:<id>» встречается в HTML письма. Имя файла не критерий: image001.png бывает
    и настоящим вложением."""
    try:
        html = (item.HTMLBody or "").lower()
    except Exception:
        html = ""
    out = []
    for i in range(1, item.Attachments.Count + 1):
        at = item.Attachments.Item(i)
        hidden, cid = False, ""
        try:
            hidden = bool(at.PropertyAccessor.GetProperty(PT + "0x7FFE000B"))
        except Exception:
            pass
        try:
            cid = at.PropertyAccessor.GetProperty(PT + "0x3712001F") or ""
        except Exception:
            pass
        out.append((at, hidden or (bool(cid) and ("cid:" + cid.lower()) in html)))
    return out


def wait_for(cond, tries: int = 40, delay: float = 0.25):
    for _ in range(tries):
        time.sleep(delay)
        v = cond()
        if v:
            return v
    return None


def send_with_inline_guard(app, item) -> None:
    """Send() падает на черновике, открытом как ВСТРОЕННЫЙ ответ в области чтения
    («нельзя использовать со встроенным элементом ответа»). В представлении «беседа»
    ClearSelection тоже запрещён, поэтому уводим окно на другую папку: ответ
    закрывается с сохранением. Отправляем и возвращаем папку на место."""
    try:
        item.Send()
        return
    except Exception as e:
        if "встроенн" not in str(e) and "inline" not in str(e).lower():
            raise
    ex = app.ActiveExplorer()
    prev = ex.CurrentFolder
    inl = ex.ActiveInlineResponse
    if inl is not None:
        inl.Save()
    ns = mapi(app)
    ex.CurrentFolder = ns.GetDefaultFolder(5 if prev.Name.lower() not in ("отправленные", "sent items") else 6)
    time.sleep(1.5)
    fresh = ns.GetItemFromID(item.EntryID)
    fresh.Send()
    time.sleep(1.0)
    ex.CurrentFolder = prev
    print("  (черновик был открыт в области чтения — окно Outlook на секунду переключилось и вернулось)")


def parse_at(s: str) -> dt.datetime:
    for f in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return dt.datetime.strptime(s, f)
        except ValueError:
            continue
    raise SystemExit(f"не понял время «{s}» — нужно «ГГГГ-ММ-ДД ЧЧ:ММ»")


def where(item) -> str:
    try:
        return item.Parent.FolderPath.split("\\")[-1]
    except Exception:
        return "?"


# ------------------------------------------------------------------ чтение

def cmd_accounts(a) -> int:
    ns = mapi()
    print("  учётки:")
    for acc in ns.Accounts:
        print(f"    {acc.DisplayName}  <{acc.SmtpAddress}>")
    print("  хранилища:")
    try:  # перечисление хранилищ у Exchange иногда падает на втором элементе — берём по индексу
        for i in range(1, ns.Stores.Count + 1):
            try:
                print(f"    {ns.Stores.Item(i).DisplayName}")
            except Exception as e:
                print(f"    (хранилище {i} не открылось: {type(e).__name__})")
    except Exception as e:
        print(f"    (список хранилищ недоступен: {type(e).__name__})")
    return 0


def cmd_folders(a) -> int:
    ns = mapi()
    root = ns.GetDefaultFolder(6).Parent
    print(f"  {root.Name}")
    for f in root.Folders:
        try:
            unread = f"  непроч. {f.UnReadItemCount}" if f.UnReadItemCount else ""
            print(f"    {f.Name[:44]:<46} {f.Items.Count:>6}{unread}")
            for sub in f.Folders:
                print(f"      └ {sub.Name[:40]:<42} {sub.Items.Count:>6}")
        except Exception:
            continue
    return 0


def cmd_list(a) -> int:
    ns = mapi()
    f = get_folder(ns, a.folder)
    if is_outbox(f):
        print("  «Исходящие» показываю таблицей: открытие писем оттуда снимает их с очереди отправки\n")
        return cmd_outbox(a)
    items = sorted_items(f)
    if a.unread:
        items = items.Restrict("[UnRead] = True")
    if a.days:
        items = items.Restrict(f"@SQL=\"urn:schemas:httpmail:datereceived\" >= '{since_utc(a.days)}'")
    print(f"  {f.Name}: всего {f.Items.Count}, непрочитанных {f.UnReadItemCount}\n")
    show_list(items, a.limit, a.ids, mode_for(f), f"список «{f.Name}»")
    return 0


# Поиск по подстроке — только DASL (@SQL со схемными именами). Простой синтаксис
# «[Subject] like '%…%'» Outlook отвергает: «Условие неверно».
DASL = {"subject": "urn:schemas:httpmail:subject",
        "body": "urn:schemas:httpmail:textdescription",
        "from": "urn:schemas:httpmail:fromname",
        "to": "urn:schemas:httpmail:displayto",
        # SMTP отправителя: fromemail у писем изнутри Exchange хранит путь X500 и находит 0 писем
        "email": P_SENDER_SMTP}


def cmd_search(a) -> int:
    ns = mapi()
    f = get_folder(ns, a.folder)
    if is_outbox(f):
        raise SystemExit("в «Исходящих» поиск не делаю: открытие писем оттуда снимает их с очереди. Смотрите: outbox")
    q = a.query.replace("'", "").replace('"', "")
    key = DASL[a.field]
    flt = f"@SQL=(\"{key}\" like '%{q}%')"
    if a.days:
        flt += f" AND (\"urn:schemas:httpmail:datereceived\" >= '{since_utc(a.days)}')"
    items = sorted_items(f).Restrict(flt)
    print(f"  поиск {a.field} ~ «{a.query}» в «{f.Name}»\n")
    n = show_list(items, a.limit, a.ids, mode_for(f), f"поиск «{a.query}» в «{f.Name}»")
    print(f"\n  показано: {n}")
    return 0


def cmd_read(a) -> int:
    app = outlook()
    m = pick(app, a)
    print(f"  папка: {where(m)}")
    if m.Class == OL_MAIL:
        print(f"  от:    {smtp_of_sender(m)}")
        print(f"  кому:  {m.To}")
        if m.CC:
            print(f"  копия: {m.CC}")
        print(f"  дата:  {fmt(m.ReceivedTime)}")
        if local(m.DeferredDeliveryTime):
            print(f"  ⏰ отложенная отправка: {fmt(m.DeferredDeliveryTime)}")
        if m.Categories:
            print(f"  категории: {m.Categories}")
        if getattr(m, "IsMarkedAsTask", False):
            print(f"  🚩 флажок, срок: {fmt(m.TaskDueDate)}")
    print(f"  тема:  {m.Subject}")
    print(f"  id:    {m.EntryID}")
    att = [(x.FileName, x.Size, inl) for x, inl in real_attachments(m)]
    if att:
        print("  вложения: " + "; ".join(f"{n} ({s // 1024} КБ){' [картинка подписи]' if i else ''}" for n, s, i in att))
    print()
    body = str(m.HTMLBody if a.html else m.Body)
    print(body if a.full else body[:3000])
    if not a.full and len(body) > 3000:
        print(f"\n  … обрезано, всего {len(body)} символов (--full)")
    return 0


def cmd_thread(a) -> int:
    app = outlook()
    m = pick(app, a)
    conv = m.GetConversation()
    if conv is None:
        print("  беседы нет (письмо не в ветке или хранилище не поддерживает беседы)")
        return 0
    table = conv.GetTable()
    rows = []
    while not table.EndOfTable:
        r = table.GetNextRow()
        rows.append(r("EntryID"))
    print(f"  беседа «{m.ConversationTopic}»: {len(rows)} писем\n")
    remember(rows, f"беседа «{m.ConversationTopic}»")
    ns = mapi(app)
    queued = queued_ids(ns)
    for i, eid in enumerate(rows, 1):
        if eid in queued:
            print(f"  [{i}] Исходящие      (стоит в очереди на отправку — не открываю: это снимает его с отправки)")
            continue
        try:
            it = ns.GetItemFromID(eid)
            when = fmt(it.ReceivedTime) if it.Sent else "черновик/исходящее"
            who = smtp_of_sender(it) if it.Sent else "(я)"
            sched = f"  ⏰ {fmt(it.DeferredDeliveryTime)}" if local(getattr(it, "DeferredDeliveryTime", None)) else ""
            print(f"  [{i}] {where(it):<14} {when:<20} {who[:30]:<32} {str(it.Subject)[:50]}{sched}")
            if a.ids:
                print(f"        id: {eid}")
        except Exception as e:
            print(f"  [{i}] не открылось ({type(e).__name__})")
    return 0


def cmd_outbox(a) -> int:
    """В «Исходящих» отложенное письмо, письмо в очереди и письмо, снятое с очереди, выглядят
    почти одинаково. Различают только таблица флагов и время отложки — читаем ИМЕННО их."""
    ns = mapi()
    rows = sorted(outbox_rows(ns), key=lambda r: local(r["mod"]) or dt.datetime.min, reverse=True)
    print(f"  Исходящие: {len(rows)}\n")
    for n, r in enumerate(rows, 1):
        print(f"  [{n}] {outbox_state(r)}\n      кому: {r['to']}  · тема: {r['subject']}")
        if getattr(a, "ids", False):
            print(f"      id: {r['eid']}")
    if not rows:
        print("  пусто")
    remember([r["eid"] for r in rows], "исходящие")
    return 0


def cmd_drafts(a) -> int:
    ns = mapi()
    f = ns.GetDefaultFolder(16)
    print(f"  Черновики: {f.Items.Count}\n")
    show_list(sorted_items(f), a.limit, a.ids, "modified", "черновики")
    return 0


def cmd_attachments(a) -> int:
    app = outlook()
    m = pick(app, a)
    rows = real_attachments(m)
    if not rows:
        print("  вложений нет")
        return 0
    out = pathlib.Path(a.save) if a.save else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    for at, inline in rows:
        mark = " [картинка подписи]" if inline else ""
        print(f"  {at.FileName} ({at.Size // 1024} КБ){mark}")
        if out and (a.all or not inline):
            dst = out / at.FileName
            at.SaveAsFile(str(dst))
            print(f"    → {dst}")
    return 0


# ------------------------------------------------------------------ черновики

def drop_stale(ns, subject_part: str, first: str) -> int:
    """Убирает НАШ прежний черновик той же темы с той же первой строкой — иначе
    копятся двойники со старыми вложениями."""
    if not first:
        return 0
    removed = 0
    for it in list(ns.GetDefaultFolder(16).Items):
        try:
            if subject_part.lower() in (it.Subject or "").lower() and first in (it.Body or "")[:300]:
                print(f"  убираю прежний черновик от {fmt(it.LastModificationTime)}")
                it.Delete()
                removed += 1
        except Exception:
            continue
    return removed


def cmd_reply(a) -> int:
    """Ответ В ВЕТКЕ: открываем письмо в окне и жмём «Ответить (всем)» самим Outlook.
    Так черновик получает подпись, цитату и свойства беседы. Выделить письмо из кода
    в представлении «беседа» Outlook не даёт — поэтому окно, а не Explorer."""
    app = outlook()
    ns = mapi(app)
    src = pick(app, a)
    piece = content_html(a)
    subj_core = re.sub(r"^\s*((re|fw|fwd|ответ|пересл)\s*:\s*)+", "", src.Subject or "", flags=re.I)
    if a.replace_prev:
        drop_stale(ns, subj_core, first_line(a))
    reply, win = None, None
    try:
        src.Display()
        win = wait_for(lambda: (lambda i: i if i is not None and getattr(i.CurrentItem, "EntryID", None) == src.EntryID else None)(app.ActiveInspector()))
        if win is not None:
            before = app.Inspectors.Count
            win.CommandBars.ExecuteMso("ReplyAll" if a.all else "Reply")
            reply = wait_for(lambda: (lambda i: i.CurrentItem if i is not None and app.Inspectors.Count > before
                                      and i.CurrentItem.Class == OL_MAIL and not i.CurrentItem.Sent else None)(app.ActiveInspector()))
    except Exception as e:
        print(f"  окно ответа не открылось ({type(e).__name__}: {e}) — отвечаю программно, подпись может не добавиться")
    if reply is None:
        reply = src.ReplyAll() if a.all else src.Reply()
    reply.HTMLBody = insert_after_body(reply.HTMLBody or "", piece)
    attach_all(reply, a.attach)
    reply.Save()
    if win is not None:
        try:
            win.Close(1)  # окно исходного письма — без изменений
        except Exception:
            pass
    print(f"\n  черновик ответа сохранён (не отправлен): {reply.Subject}")
    print(f"  кому: {reply.To}{'  · копия: ' + reply.CC if reply.CC else ''}")
    print(f"  вложений: {len([1 for _, i in real_attachments(reply) if not i])}")
    print(f"  id: {reply.EntryID}")
    if a.show:
        reply.Display()
    else:
        try:
            reply.Close(0)  # olSave
        except Exception:
            pass
    return 0


def cmd_new(a) -> int:
    app = outlook()
    ns = mapi(app)
    piece = content_html(a)
    if a.replace_prev:
        drop_stale(ns, a.subject, first_line(a))
    m = app.CreateItem(0)
    if not a.no_signature:
        m.Display()  # подпись по умолчанию Outlook вставляет только при показе письма
    m.To, m.CC, m.BCC, m.Subject = a.to, a.cc, a.bcc, a.subject
    m.HTMLBody = insert_after_body(m.HTMLBody or "", piece)
    attach_all(m, a.attach)
    m.Save()
    print(f"  черновик сохранён (не отправлен): {m.Subject}\n  кому: {m.To}\n  id: {m.EntryID}")
    if a.show:
        m.Display()
    else:
        try:
            m.Close(0)
        except Exception:
            pass
    return 0


def find_attachment(item, name: str):
    for i in range(1, item.Attachments.Count + 1):
        at = item.Attachments.Item(i)
        if at.FileName == name or name.lower() in (at.FileName or "").lower():
            return at
    return None


def cmd_edit(a) -> int:
    app = outlook()
    ns = mapi(app)
    m = pick(app, a, allow_queued=True)
    in_outbox = is_outbox(m.Parent)
    sched = local(m.DeferredDeliveryTime)
    subject = m.Subject
    if in_outbox:
        print(f"  письмо в «Исходящих»{', отложено до ' + sched.strftime('%Y-%m-%d %H:%M') if sched else ''}")
        if not a.yes:
            print("  править письмо из «Исходящих» = снять с отправки и поставить заново. Повторите с --yes.")
            return 1
        if sched and sched <= dt.datetime.now():
            raise SystemExit("время отложки уже прошло — после правки письмо ушло бы сразу; поставьте новое через schedule")
        m = m.Move(ns.GetDefaultFolder(16))
        print("  снято с отправки и перенесено в «Черновики»")
    for spec in a.replace_attach or []:
        if "=" not in spec:
            raise SystemExit(f"--replace-attach ИМЯ=ФАЙЛ, а не «{spec}»")
        old, new = spec.split("=", 1)
        at = find_attachment(m, old)
        if at is None:
            raise SystemExit(f"во вложениях нет «{old}»")
        print(f"  снято: {at.FileName}")
        at.Delete()
        attach_all(m, [new])
    for name in a.remove_attach or []:
        at = find_attachment(m, name)
        if at is None:
            raise SystemExit(f"во вложениях нет «{name}»")
        print(f"  снято: {at.FileName}")
        at.Delete()
    attach_all(m, a.attach)
    if a.subject:
        m.Subject = a.subject
        subject = a.subject
    if a.to:
        m.To = a.to
    if a.cc is not None:
        m.CC = a.cc
    if a.prepend_text or a.prepend_html:
        piece = text_to_html(a.prepend_text) if a.prepend_text else pathlib.Path(a.prepend_html).read_text(encoding="utf-8")
        m.HTMLBody = insert_after_body(m.HTMLBody or "", piece)
    m.Save()
    names = ", ".join(x.FileName for x, inl in real_attachments(m) if not inl)
    if in_outbox:
        refuse_unsafe(m)
        if sched:
            m.DeferredDeliveryTime = to_ole(sched)   # время возвращаем тем же способом, что и ставили
            m.Save()
        send_with_inline_guard(app, m)
        del m
        time.sleep(2)
        if not verify_queued(ns, subject, sched):
            print("  ⚠ в «Исходящих» письмо не подтверждено — проверьте: outbox")
            return 2
    print("  вложения: " + (names or "нет"))
    return 0


# ------------------------------------------------------------------ наружу

def cmd_schedule(a) -> int:
    app = outlook()
    ns = mapi(app)
    m = pick(app, a, allow_queued=True)
    at = parse_at(a.at)
    if at <= dt.datetime.now():
        raise SystemExit("время в прошлом — письмо ушло бы сразу")
    subject, to = m.Subject, m.To
    print(f"  «{subject}» → {to}\n  отправка: {at:%Y-%m-%d %H:%M} (время машины, МСК)")
    if not a.yes:
        print("  сухой прогон: письмо не тронуто. Поставить — с --yes")
        return 1
    refuse_unsafe(m)
    if is_outbox(m.Parent):
        m = m.Move(ns.GetDefaultFolder(16))     # письмо уже снято с очереди открытием; правим как черновик
    m.DeferredDeliveryTime = to_ole(at)         # настенные часы через UTC-метку, иначе −3 ч
    m.Save()
    send_with_inline_guard(app, m)
    del m                                       # после Send() объект письма больше не трогаем
    time.sleep(2)
    if verify_queued(ns, subject, at):
        return 0
    print("  ⚠ письмо с такой темой и временем в «Исходящих» не подтверждено — проверьте: outbox")
    return 2


def cmd_unschedule(a) -> int:
    app = outlook()
    ns = mapi(app)
    if not (a.ref and len(a.ref) > 40):
        a.folder = "outbox"
    m = pick(app, a, allow_queued=True, queued_needs_yes=False)
    if not is_outbox(m.Parent):
        raise SystemExit("письмо не в «Исходящих»")
    when = fmt(m.DeferredDeliveryTime)
    moved = m.Move(ns.GetDefaultFolder(16))
    if not a.keep_time:
        # Время отложки обнуляем (4501-01-01 = «не задано»): иначе, нажав потом «Отправить» в
        # Outlook, человек получил бы письмо в очереди до прежнего часа.
        moved.DeferredDeliveryTime = dt.datetime(4501, 1, 1, tzinfo=dt.timezone.utc)
        moved.Save()
    print(f"  снято с отправки (было отложено до {when}), лежит в «Черновиках»"
          f"{'; время отложки сохранено в письме (--keep-time)' if a.keep_time else '; время отложки сброшено'}"
          f"\n  id: {moved.EntryID}")
    print("  вернуть: schedule <id> --at \"…\" --yes")
    return 0


def cmd_send(a) -> int:
    app = outlook()
    ns = mapi(app)
    m = pick(app, a)                            # письмо из очереди «Исходящих» сюда не пускаем
    sched = local(m.DeferredDeliveryTime)
    subject, to, cc = m.Subject, m.To, m.CC
    print(f"  «{subject}» → {to}{'  · копия: ' + cc if cc else ''}")
    print(f"  вложения: {', '.join(x.FileName for x, inl in real_attachments(m) if not inl) or 'нет'}")
    if sched and sched > dt.datetime.now():
        print(f"  у письма стоит отложка: уйдёт {sched:%Y-%m-%d %H:%M}")
    if not a.yes:
        print("  сухой прогон: НЕ отправлено. Отправить — с --yes")
        return 1
    refuse_unsafe(m)
    send_with_inline_guard(app, m)
    del m
    time.sleep(2)
    if not verify_queued(ns, subject):
        print("  ✓ в «Исходящих» письма с этой темой нет — Outlook уже отправил его (проверьте «Отправленные»)")
    return 0


# ------------------------------------------------------------------ порядок

def cmd_move(a) -> int:
    app = outlook()
    m = pick(app, a)
    dst = get_folder(mapi(app), a.to)
    if where(m).lower() in ("исходящие", "outbox") and local(m.DeferredDeliveryTime):
        print("  ⚠ письмо отложено — перенос снимает отложенную отправку")
    m.Move(dst)
    print(f"  перенесено в «{dst.Name}»")
    return 0


MARK = {"today": 0, "tomorrow": 1, "week": 2, "nextweek": 3, "nodate": 4, "done": 5}  # OlMarkInterval


def cmd_flag(a) -> int:
    app = outlook()
    m = pick(app, a)
    if not m.Sent and where(m).lower() in ("черновики", "drafts"):
        raise SystemExit("  флажок «К исполнению» Outlook ставит только на отправленные и полученные письма, "
                         "не на черновики")
    if a.clear:
        m.ClearTaskFlag()
        m.Save()
        print("  флажок снят")
        return 0
    m.MarkAsTask(MARK[a.when])
    m.Save()
    print(f"  🚩 флажок: {a.when}, срок {fmt(m.TaskDueDate)}")
    return 0


def cmd_category(a) -> int:
    app = outlook()
    m = pick(app, a)
    # Разделитель категорий в Outlook — «; » (разделитель списка Windows), запятая бывает внутри
    # имени. Разбираем по обоим, склеиваем так, как хранит сам Outlook.
    cats = [c.strip() for c in re.split(r"[;,]", m.Categories or "") if c.strip()]
    if a.add and a.add not in cats:
        cats.append(a.add)
    if a.remove:
        cats = [c for c in cats if c != a.remove]
    m.Categories = "; ".join(cats)
    m.Save()
    print(f"  категории: {m.Categories or '—'}")
    return 0


def cmd_mark(a) -> int:
    app = outlook()
    m = pick(app, a)
    m.UnRead = bool(a.unread)
    m.Save()
    print("  отмечено непрочитанным" if a.unread else "  отмечено прочитанным")
    return 0


def cmd_show(a) -> int:
    app = outlook()
    m = pick(app, a)
    m.Display()
    print(f"  открыто в Outlook: {m.Subject}")
    return 0


# ------------------------------------------------------------------ календарь и люди

def calendar_items(ns, start: dt.datetime, end: dt.datetime, cap: int = 500):
    """События и повторы календаря в окне [start, end). Порядок критичен: сначала Sort по [Start],
    потом IncludeRecurrences (наоборот — 10× медленнее, без Sort — неверный набор). Верхняя граница
    обязательна: ряды без конца при IncludeRecurrences бесконечны. Jet сравнивает в МЕСТНОМ времени;
    даты — «дд.мм.гггг чч:мм» без секунд (секунды дают 0 строк, «мм/дд» молча искажается).
    Обход GetFirst/GetNext с потолком: Count у развёрнутого набора бессмыслен (2147483647)."""
    items = ns.GetDefaultFolder(9).Items
    items.Sort("[Start]")
    items.IncludeRecurrences = True
    sel = items.Restrict(f"[Start] < '{jet_dt(end)}' AND [End] > '{jet_dt(start)}'")
    out = []
    it = sel.GetFirst()
    while it is not None and len(out) < cap:
        out.append(it)
        it = sel.GetNext()
    return out


def cmd_events(a) -> int:
    ns = mapi()
    start = dt.datetime.strptime(a.from_, "%Y-%m-%d") if a.from_ else dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + dt.timedelta(days=a.days)
    n = 0
    for it in calendar_items(ns, start, end):
        s_, e_ = local(it.Start), local(it.End)
        if s_ is None or e_ is None:
            continue
        n += 1
        meet = "встреча" if it.MeetingStatus in (1, 3) else "событие"
        ans = {2: " (под вопросом)", 4: " (отклонено)", 5: " (БЕЗ ОТВЕТА)"}.get(it.ResponseStatus, "")
        loc = f" · {it.Location}" if it.Location else ""
        print(f"  {rus_day(s_)} {s_:%d.%m %H:%M}–{e_:%H:%M}  {str(it.Subject)[:60]}{loc}  ({meet}){ans}")
    if not n:
        print("  событий нет")
    return 0


def cmd_invites(a) -> int:
    """Приглашения, на которые ещё не ответили (ResponseStatus=5). Фильтр по ResponseStatus в Restrict
    молча даёт 0 — поэтому отбор в Python."""
    ns = mapi()
    start = dt.datetime.now()
    n = 0
    for it in calendar_items(ns, start, start + dt.timedelta(days=a.days)):
        if it.ResponseStatus != 5:
            continue
        n += 1
        print(f"  {rus_day(local(it.Start))} {local(it.Start):%d.%m %H:%M}–{local(it.End):%H:%M}  {str(it.Subject)[:56]}  · организатор: {it.Organizer}")
    print(f"\n  без ответа: {n}" if n else "  неотвеченных приглашений нет")
    return 0


def cmd_event_new(a) -> int:
    app = outlook()
    start = parse_at(a.start)
    end = parse_at(a.end) if a.end else start + dt.timedelta(minutes=a.minutes)
    ap = app.CreateItem(1)  # olAppointmentItem
    ap.Subject = a.subject
    ap.Start, ap.End = to_ole(start), to_ole(end)   # через UTC-метку, иначе встреча сдвинется на −3 ч
    if a.location:
        ap.Location = a.location
    if a.text:
        ap.Body = a.text
    people = [x.strip() for x in (a.attendees or "").split(",") if x.strip()]
    optional = [x.strip() for x in (a.optional or "").split(",") if x.strip()]
    if people or optional:
        ap.MeetingStatus = 1  # olMeeting
        for p in people:
            ap.Recipients.Add(p).Type = 1   # обязательный
        for p in optional:
            ap.Recipients.Add(p).Type = 2   # необязательный
        ap.Recipients.ResolveAll()
    if (people or optional) and a.send:
        print(f"  встреча «{a.subject}» {start:%Y-%m-%d %H:%M}–{end:%H:%M}, участники: {', '.join(people + optional)}")
        if not a.yes:
            print("  сухой прогон: приглашения НЕ отправлены. Отправить — с --yes")
            return 1
        ap.Send()
        print("  ✓ приглашения отправлены")
        return 0
    ap.Save()
    kind = "черновик встречи (приглашения не отправлены)" if (people or optional) else "событие"
    print(f"  ✓ {kind}: «{a.subject}» {start:%Y-%m-%d %H:%M}–{end:%H:%M}\n  id: {ap.EntryID}")
    return 0


FB = {"0": "свободно", "1": "под вопросом", "2": "занято", "3": "нет на месте", "4": "работает в другом месте"}


def cmd_free(a) -> int:
    ns = mapi()
    day = dt.datetime.strptime(a.date, "%Y-%m-%d") if a.date else dt.datetime.now()
    who = a.who or ns.CurrentUser.Name
    r = ns.CreateRecipient(who)
    if not r.Resolve():
        raise SystemExit(f"не нашёл в адресной книге: {who}")
    # Строка идёт с 00:00 даты начала, по MinPerChar минут на знак, всего 29 суток; время в аргументе
    # игнорируется. Аргумент — через to_ole (наивная дата сдвинулась бы на сутки назад).
    s_ = r.FreeBusy(to_ole(day.replace(hour=0, minute=0, second=0, microsecond=0)), 30, True)
    slots = s_[:48]
    print(f"  {r.Name} · {day:%d.%m.%Y} (по 30 мин, 08:00–21:00)")
    cur, start = None, 0
    for i in range(16, 42):
        st = slots[i] if i < len(slots) else "0"
        if st != cur:
            if cur is not None and cur != "0":
                print(f"    {start // 2:02d}:{30 * (start % 2):02d}–{i // 2:02d}:{30 * (i % 2):02d}  {FB.get(cur, cur)}")
            cur, start = st, i
    if cur not in (None, "0"):
        print(f"    {start // 2:02d}:{30 * (start % 2):02d}–21:00  {FB.get(cur, cur)}")
    if set(slots[16:42]) <= {"0"}:
        print("    весь день свободен")
    return 0


def cmd_whois(a) -> int:
    ns = mapi()
    r = ns.CreateRecipient(a.query)
    if not r.Resolve():
        raise SystemExit(f"в адресной книге не найдено: {a.query}")
    ae = r.AddressEntry
    eu = None
    try:
        eu = ae.GetExchangeUser()
    except Exception:
        pass
    if eu is None:
        print(f"  {ae.Name}  <{ae.Address}>")
        return 0
    for label, attr in [("имя", "Name"), ("почта", "PrimarySmtpAddress"), ("должность", "JobTitle"),
                        ("отдел", "Department"), ("офис", "OfficeLocation"),
                        ("рабочий тел.", "BusinessTelephoneNumber"), ("мобильный", "MobileTelephoneNumber")]:
        v = getattr(eu, attr, "") or ""
        if v:
            print(f"  {label}: {v}")
    return 0


# ------------------------------------------------------------------ разбор аргументов

def add_ref(p):
    p.add_argument("ref", nargs="?", help="номер из выдачи, EntryID")
    p.add_argument("--subject", dest="subject_sel", help="выбрать по части темы (самое свежее)")
    p.add_argument("--from", dest="from_sel", help="и по части имени отправителя")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default="inbox", help="inbox|sent|drafts|outbox|deleted|junk или имя папки")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("accounts").set_defaults(fn=cmd_accounts)
    sub.add_parser("folders").set_defaults(fn=cmd_folders)

    p = sub.add_parser("list"); p.add_argument("--limit", type=int, default=15)
    p.add_argument("--unread", action="store_true"); p.add_argument("--days", type=int, default=0)
    p.add_argument("--ids", action="store_true"); p.set_defaults(fn=cmd_list)

    p = sub.add_parser("search"); p.add_argument("query")
    p.add_argument("--field", default="subject", choices=list(DASL))
    p.add_argument("--days", type=int, default=0); p.add_argument("--limit", type=int, default=20)
    p.add_argument("--ids", action="store_true"); p.set_defaults(fn=cmd_search)

    p = sub.add_parser("read"); add_ref(p); p.add_argument("--full", action="store_true")
    p.add_argument("--html", action="store_true"); p.set_defaults(fn=cmd_read)

    p = sub.add_parser("thread"); add_ref(p); p.add_argument("--ids", action="store_true"); p.set_defaults(fn=cmd_thread)
    p = sub.add_parser("outbox"); p.add_argument("--ids", action="store_true"); p.set_defaults(fn=cmd_outbox)
    p = sub.add_parser("drafts"); p.add_argument("--limit", type=int, default=15)
    p.add_argument("--ids", action="store_true"); p.set_defaults(fn=cmd_drafts)

    p = sub.add_parser("attachments"); add_ref(p); p.add_argument("--save")
    p.add_argument("--all", action="store_true", help="и картинки подписи тоже"); p.set_defaults(fn=cmd_attachments)

    def body_args(q):
        q.add_argument("--text"); q.add_argument("--text-file"); q.add_argument("--html-file")
        q.add_argument("--attach", action="append", default=[])
        q.add_argument("--replace-prev", action="store_true", help="убрать наш прежний черновик той же темы")
        q.add_argument("--show", action="store_true", help="открыть черновик в Outlook после сохранения")

    p = sub.add_parser("reply"); add_ref(p); p.add_argument("--all", action="store_true"); body_args(p); p.set_defaults(fn=cmd_reply)
    p = sub.add_parser("new"); p.add_argument("--to", required=True); p.add_argument("--cc", default="")
    p.add_argument("--bcc", default=""); p.add_argument("--subject", required=True)
    p.add_argument("--no-signature", action="store_true"); body_args(p); p.set_defaults(fn=cmd_new)

    p = sub.add_parser("edit"); add_ref(p)
    p.add_argument("--attach", action="append", default=[]); p.add_argument("--remove-attach", action="append", default=[])
    p.add_argument("--replace-attach", action="append", default=[])
    p.add_argument("--new-subject", dest="subject"); p.add_argument("--to"); p.add_argument("--cc")
    p.add_argument("--prepend-text"); p.add_argument("--prepend-html")
    p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_edit)

    p = sub.add_parser("schedule"); add_ref(p); p.add_argument("--at", required=True)
    p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_schedule)
    p = sub.add_parser("unschedule"); add_ref(p); p.add_argument("--keep-time", action="store_true", help="не сбрасывать время отложки в письме"); p.set_defaults(fn=cmd_unschedule)
    p = sub.add_parser("send"); add_ref(p); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_send)

    p = sub.add_parser("move"); add_ref(p); p.add_argument("--to", required=True); p.set_defaults(fn=cmd_move)
    p = sub.add_parser("flag"); add_ref(p); p.add_argument("--when", default="today", choices=list(MARK))
    p.add_argument("--clear", action="store_true"); p.set_defaults(fn=cmd_flag)
    p = sub.add_parser("category"); add_ref(p); p.add_argument("--add"); p.add_argument("--remove"); p.set_defaults(fn=cmd_category)
    p = sub.add_parser("mark"); add_ref(p); g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--read", action="store_true"); g.add_argument("--unread", action="store_true"); p.set_defaults(fn=cmd_mark)
    p = sub.add_parser("show"); add_ref(p); p.set_defaults(fn=cmd_show)

    p = sub.add_parser("events"); p.add_argument("--days", type=int, default=7)
    p.add_argument("--from", dest="from_"); p.set_defaults(fn=cmd_events)
    p = sub.add_parser("invites"); p.add_argument("--days", type=int, default=30); p.set_defaults(fn=cmd_invites)
    p = sub.add_parser("event-new"); p.add_argument("--subject", required=True); p.add_argument("--start", required=True)
    p.add_argument("--end"); p.add_argument("--minutes", type=int, default=60); p.add_argument("--location")
    p.add_argument("--text"); p.add_argument("--attendees"); p.add_argument("--optional")
    p.add_argument("--send", action="store_true"); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_event_new)
    p = sub.add_parser("free"); p.add_argument("date", nargs="?"); p.add_argument("--who"); p.set_defaults(fn=cmd_free)
    p = sub.add_parser("whois"); p.add_argument("query"); p.set_defaults(fn=cmd_whois)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
