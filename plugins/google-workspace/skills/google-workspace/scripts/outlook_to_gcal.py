#!/usr/bin/env python
"""Переносит встречи из рабочего Outlook в Google Календарь.

Зачем: слоты для брони считаются по занятости в Google, а половина рабочего дня
занята встречами Company, которые живут только в Outlook. Без переноса система
предложит клиенту время, на котором уже стоит планёрка.

Почему не с сервера: Exchange (mail.company.com) отвечает только на NTLM, пароля у
нас нет. Локальный Outlook отдаёт те же данные через COM без пароля вообще —
Windows уже вошла под этой учёткой. Поэтому синхронизация живёт на ноутбуке.

Встречи кладутся в ОТДЕЛЬНЫЙ календарь, а не в личный: так их видно отдельной
галочкой, и выключается всё одним движением, не разгребая, что откуда.

    python outlook_to_gcal.py --dry-run      # показать, ничего не меняя
    python outlook_to_gcal.py                # перенести
    python outlook_to_gcal.py --private      # без тем, только «Занято»
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

# Планировщик Windows запускает скрипт в консоли с кодировкой cp1251, и первый же
# print с «−», «…» или «·» роняет всё с UnicodeEncodeError — ДО единой записи в
# Google, при этом задача рапортует успех. Ловится только запуском из планировщика:
# из любого UTF-8 окружения скрипт отрабатывает нормально.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

TOKENS = [
    pathlib.Path.home() / ".claude" / "google_oauth_token_calendar.json",
    pathlib.Path.home() / ".claude" / "google_oauth_token.json",
]

# Куда отчитываться об успехе. Служба бронирования на сервере решает по этой
# отметке, можно ли верить занятости Company, и БЕЗ неё считает синк мёртвым —
# даже когда он отработал. Проверять свежесть по самим событиям календаря она
# не может: спокойная неделя в Company неотличима от умершего синка.
PULSE_DB = "yourname_academy"
PULSE_SSH = "your-server"
PULSE_CONTAINER = "transformai-postgres"
TZ = "UTC"
CAL_NAME = "Работа · Company (из Outlook)"

# Метка на событиях. По ней находим ранее перенесённое, чтобы не плодить копии
# и чтобы не тронуть то, что человек завёл в этом календаре руками.
MARK = "outlook_sync"


def report_pulse(added: int, updated: int, deleted: int, known_total: int) -> None:
    """Отметиться у службы бронирования: синк отработал, занятости можно верить.

    ПОЧЕМУ ЧЕРЕЗ SSH, А НЕ HTTP. Служба слушает 127.0.0.1 на сервере и наружу не
    смотрит; открывать её в интернет ради одной строки в сутки — менять большую
    поверхность на маленькое удобство. Ключ ssh уже есть и уже используется.

    ПРОВАЛ ОТЧЁТА НЕ РОНЯЕТ СИНХРОНИЗАЦИЮ: Google к этому моменту уже обновлён,
    и обрушить всё из-за недоступного сервера значило бы потерять сделанную
    работу. Но и промолчать нельзя — тогда «синк мёртв» и «отчёт не дошёл»
    выглядят одинаково, а лечатся по-разному. Поэтому провал печатается в лог
    явной строкой, которую видно в том же файле, что и остальной результат.
    """
    import subprocess

    sql = (
        "INSERT INTO meet_sync_health "
        "(source, last_ok, added, updated, deleted, known_total) "
        f"VALUES ('outlook', now(), {added}, {updated}, {deleted}, {known_total})"
    )
    cmd = ["ssh", PULSE_SSH,
           f"docker exec {PULSE_CONTAINER} psql -U transformai -d {PULSE_DB} "
           f"-v ON_ERROR_STOP=1 -c \"{sql}\""]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                           encoding="utf-8", errors="replace")
    except Exception as exc:                                    # noqa: BLE001
        print(f"ОТЧЁТ СЛУЖБЕ НЕ УШЁЛ ({type(exc).__name__}: {exc}); "
              "занятость Company будет считаться устаревшей")
        return
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip().splitlines()
        print(f"ОТЧЁТ СЛУЖБЕ НЕ УШЁЛ (код {r.returncode}): "
              f"{err[-1] if err else 'без вывода'}")
        return
    print("служба уведомлена: занятость Company свежая")


def service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    last = None
    for t in TOKENS:
        if not t.exists():
            continue
        data = json.loads(t.read_text(encoding="utf-8"))
        scopes = data.get("scopes") or []
        if not any(s.rstrip("/").endswith("/calendar") or "calendar.events" in s
                   for s in scopes):
            last = f"{t.name}: права на календарь только для чтения"
            continue
        creds = Credentials.from_authorized_user_info(data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            t.write_text(creds.to_json(), encoding="utf-8")
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    raise SystemExit(f"нет токена с правом ЗАПИСИ в календарь. {last or ''}")


def target_calendar(svc, create: bool) -> str:
    """Возвращает id календаря для рабочих встреч, при надобности заводит его."""
    page = None
    while True:
        r = svc.calendarList().list(pageToken=page, maxResults=250).execute()
        for c in r.get("items", []):
            if c.get("summary") == CAL_NAME:
                return c["id"]
        page = r.get("nextPageToken")
        if not page:
            break
    if not create:
        raise SystemExit(f"календарь «{CAL_NAME}» не найден (запуск без создания)")
    made = svc.calendars().insert(body={"summary": CAL_NAME, "timeZone": TZ}).execute()
    # Свой цвет: рабочее не должно сливаться с личным в общей сетке.
    try:
        svc.calendarList().patch(calendarId=made["id"],
                                 body={"colorId": "8"}).execute()
    except Exception:
        pass
    print(f"создан календарь «{CAL_NAME}»")
    return made["id"]


def outlook_items(days_back: int, days_ahead: int) -> list[dict]:
    """Встречи из Outlook за окно. Повторяющиеся разворачиваются в отдельные."""
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    items = ns.GetDefaultFolder(9).Items
    # Порядок важен: сначала Sort по [Start], потом IncludeRecurrences (наоборот — в 10 раз медленнее).
    items.Sort("[Start]")
    items.IncludeRecurrences = True

    lo = dt.datetime.now() - dt.timedelta(days=days_back)
    hi = dt.datetime.now() + dt.timedelta(days=days_ahead)

    # Дата в фильтре Jet — МЕСТНОЕ время в формате локали Windows (здесь ru-RU), без секунд.
    # Раньше здесь перебирали форматы и брали «первый, что вернул непустую выборку», начиная с
    # «мм/дд/гггг». Это ошибка: при русской локали «10/11/2026» читается как 10 ноября, и при дне
    # месяца ≤ 12 Outlook отдаёт НЕПУСТУЮ, но неверную выборку (разобрано 04.10.2026). Окно тогда
    # съезжало, встречи из реального окна не попадали в `seen`, и шаг «удалено» стирал их из
    # Google-календаря — слоты на записи оказывались свободными. Ближайшие опасные запуски были
    # 18.10, 19.10, 19.11.2026 и 9–12.01.2027.
    flt = f"[Start] >= '{lo:%d.%m.%Y %H:%M}' AND [Start] <= '{hi:%d.%m.%Y %H:%M}'"
    got = items.Restrict(flt)

    def count_of(sel, cap=20000) -> int:
        n, x = 0, sel.GetFirst()
        while x is not None and n < cap:
            n += 1
            x = sel.GetNext()
        return n

    # Страховка: то же окно вторым, независимым способом — DASL в UTC и в ISO-записи, которую
    # локаль не искажает. Не сошлись числа — окно разобрано неверно: ничего не меняем и не удаляем.
    off = dt.datetime.now().astimezone().utcoffset() or dt.timedelta(0)
    lo_u, hi_u = lo - off, hi - off
    q = "'"
    dasl = ('@SQL="urn:schemas:calendar:dtstart" >= ' + q + lo_u.strftime("%Y-%m-%d %H:%M") + q +
            ' AND "urn:schemas:calendar:dtstart" <= ' + q + hi_u.strftime("%Y-%m-%d %H:%M") + q)
    n_jet, n_dasl = count_of(items.Restrict(flt)), count_of(items.Restrict(dasl))
    if n_jet != n_dasl:
        raise SystemExit(f"Окно Outlook разобрано неоднозначно: Jet {n_jet} встреч, DASL {n_dasl}. "
                         f"Запуск остановлен, чтобы не удалить живые встречи из Google. "
                         f"Проверь формат даты локали Windows (outlook_to_gcal.py, outlook_items).")
    if n_jet == 0:
        raise SystemExit("Outlook не отдал ни одной встречи за окно — "
                         "проверь, что он запущен и учётка подключена")

    out, it = [], got.GetFirst()
    while it is not None:
        try:
            # Целодневные Outlook отдаёт с нулевым временем; на занятость они
            # влияют иначе, поэтому помечаем и не превращаем в слот.
            start = it.Start
            end = it.End
            out.append({
                "id": str(it.EntryID),
                "subject": (it.Subject or "").strip() or "(без темы)",
                "start": dt.datetime(start.year, start.month, start.day,
                                     start.hour, start.minute),
                "end": dt.datetime(end.year, end.month, end.day,
                                   end.hour, end.minute),
                "allday": bool(it.AllDayEvent),
                "location": (it.Location or "").strip(),
                # 1 = «под вопросом», 2 = «занят», 3 = «нет на месте»,
                # 0 = «свободен», 4 = «работаю в другом месте».
                # «Под вопросом» — занятость: так стоят все непринятые
                # приглашения, и 23.09 гостю предложили пт 14–18 поверх двух
                # таких планёрок Company (freeBusy прозрачные не видит).
                "busy": int(it.BusyStatus) in (1, 2, 3),
                "organizer": (getattr(it, "Organizer", "") or "").strip(),
            })
        except Exception:
            pass
        it = got.GetNext()
    return out


def rfc(d: dt.datetime) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def google_synced(svc, cal: str) -> dict:
    """Ранее перенесённые события, разложенные по ключу встречи Outlook.

    Берём весь календарь, а не окно: он наш и содержит только перенесённое.
    Окно по времени здесь однажды потеряло две трети событий — граница считалась
    в UTC, а встречи стоят в московском времени.
    """
    found, page = {}, None
    while True:
        r = svc.events().list(
            calendarId=cal,
            privateExtendedProperty=f"{MARK}=1",
            singleEvents=True, maxResults=2500, pageToken=page,
        ).execute()
        for ev in r.get("items", []):
            key = (ev.get("extendedProperties", {}).get("private", {})
                     .get("olid"))
            if key:
                found[key] = ev
        page = r.get("nextPageToken")
        if not page:
            break
    return found


def key_of(item: dict) -> str:
    """Ключ вхождения встречи.

    Одного EntryID мало: у повторяющейся встречи он ОДИН на всю серию, поэтому
    еженедельная планёрка на 12 недель вперёд давала двенадцать событий с
    одинаковым ключом. Они схлопывались в один, и каждый прогон переписывал
    их заново. Дата начала разводит вхождения.
    """
    return f"{item['id']}@{item['start']:%Y-%m-%dT%H:%M}"


def body_of(item: dict, private: bool) -> dict:
    title = "Занято" if private else item["subject"]
    b = {
        "summary": title,
        "extendedProperties": {"private": {MARK: "1", "olid": key_of(item)}},
        # Занятость — весь смысл переноса; свободные встречи слот не режут.
        "transparency": "opaque" if item["busy"] else "transparent",
        "reminders": {"useDefault": False, "overrides": []},
    }
    if not private and item["location"]:
        b["location"] = item["location"]
    if item["allday"]:
        b["start"] = {"date": item["start"].strftime("%Y-%m-%d")}
        b["end"] = {"date": (item["end"] or item["start"]).strftime("%Y-%m-%d")}
    else:
        b["start"] = {"dateTime": rfc(item["start"]), "timeZone": TZ}
        b["end"] = {"dateTime": rfc(item["end"]), "timeZone": TZ}
    return b


def same(ev: dict, want: dict) -> bool:
    """Совпадает ли уже перенесённое с тем, что в Outlook сейчас."""
    if (ev.get("summary") or "") != (want.get("summary") or ""):
        return False
    # Обычное значение Google в ответе опускает — отсутствие поля означает
    # «занято». Без этой поправки каждый прогон переписывал все встречи заново.
    if (ev.get("transparency") or "opaque") != (want.get("transparency") or "opaque"):
        return False
    for side in ("start", "end"):
        a, b = ev.get(side, {}), want[side]
        if "date" in b:
            if a.get("date") != b["date"]:
                return False
        else:
            # Google возвращает время со смещением: сравниваем без него.
            if (a.get("dateTime") or "")[:19] != b["dateTime"][:19]:
                return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--back", type=int, default=7, help="дней назад (по умолчанию 7)")
    ap.add_argument("--ahead", type=int, default=90, help="дней вперёд (по умолчанию 90)")
    ap.add_argument("--private", action="store_true",
                    help="писать «Занято» вместо темы встречи")
    ap.add_argument("--dry-run", action="store_true", help="показать, ничего не меняя")
    a = ap.parse_args()

    if sys.platform != "win32":
        raise SystemExit("Outlook читается только на Windows — на сервере этого пути нет")

    items = outlook_items(a.back, a.ahead)
    print(f"Outlook: {len(items)} встреч за окно −{a.back}…+{a.ahead} дней")

    svc = service()
    cal = target_calendar(svc, create=not a.dry_run)
    have = google_synced(svc, cal)
    print(f"Google: {len(have)} уже перенесённых")

    add = upd = keep = 0
    seen = set()
    for it in items:
        k = key_of(it)
        seen.add(k)
        want = body_of(it, a.private)
        old = have.get(k)
        if old is None:
            add += 1
            if not a.dry_run:
                svc.events().insert(calendarId=cal, body=want).execute()
        elif not same(old, want):
            upd += 1
            if not a.dry_run:
                svc.events().update(calendarId=cal, eventId=old["id"],
                                    body=want).execute()
        else:
            keep += 1

    # Встречу отменили в Outlook — она должна исчезнуть и здесь, иначе слот
    # останется занятым навсегда.
    gone = [ev for k, ev in have.items() if k not in seen]
    for ev in gone:
        if not a.dry_run:
            svc.events().delete(calendarId=cal, eventId=ev["id"]).execute()

    head = "БЕЗ ИЗМЕНЕНИЙ · " if a.dry_run else ""
    print(f"{head}добавлено {add} · обновлено {upd} · без изменений {keep} · "
          f"удалено {len(gone)}")
    if a.dry_run and (add or upd or gone):
        shown = 0
        for it in items:
            if key_of(it) not in have and shown < 5:
                print(f"  + {it['start']:%d.%m %H:%M} {it['subject']}")
                shown += 1
    if not a.dry_run:
        report_pulse(added=add, updated=upd, deleted=len(gone),
                     known_total=len(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
