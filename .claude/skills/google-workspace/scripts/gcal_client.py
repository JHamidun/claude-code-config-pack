#!/usr/bin/env python3
"""Google Календарь: что запланировано, где свободно, поставить событие.

Права на календарь живут в ОТДЕЛЬНОМ токене. Общий `google_oauth_token.json`
их не содержит — в нём только диск, и попытка прочитать им календарь кончается
отказом. Из-за этого календарь дважды объявляли недоступным и поднимали
авторизацию заново через браузер, хотя нужный токен уже лежал рядом.

    python gcal_client.py today
    python gcal_client.py week
    python gcal_client.py list --days 30
    python gcal_client.py free --days 7 --from 10:00 --to 19:00 --min 60
    python gcal_client.py add "Созвон с командой" --start "2026-08-20 15:00" --dur 60
    python gcal_client.py calendars
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import datetime as dt
import os
import pathlib
import sys

# Календарные права выданы именно этому файлу. Порядок важен: сначала специальный
# токен, и только если его нет — общий, где прав может не оказаться.
TOKENS = [
    pathlib.Path.home() / ".claude" / "google_oauth_token_calendar.json",
    pathlib.Path.home() / ".claude" / "google_oauth_token.json",
]
# Часовой пояс — из окружения: у каждого свой, зашивать чужой неверно.
TZ = os.environ.get("CLAUDE_CALENDAR_TZ", "UTC")


def service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import json

    last = None
    for t in TOKENS:
        if not t.exists():
            continue
        data = json.loads(t.read_text(encoding="utf-8"))
        scopes = data.get("scopes") or []
        if not any("calendar" in s for s in scopes):
            last = f"{t.name}: прав на календарь нет ({len(scopes)} других)"
            continue
        creds = Credentials.from_authorized_user_info(data)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            t.write_text(creds.to_json(), encoding="utf-8")
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    raise SystemExit(f"нет токена с правами на календарь. {last or ''}")


def rfc(d: dt.datetime) -> str:
    return d.isoformat() + "Z"


def events(svc, days: int, cal: str = "primary") -> list:
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    r = svc.events().list(calendarId=cal, timeMin=rfc(now),
                          timeMax=rfc(now + dt.timedelta(days=days)),
                          singleEvents=True, orderBy="startTime",
                          maxResults=2500).execute()
    return r.get("items", [])


def when(ev: dict) -> tuple:
    """Начало и конец события. Событие на весь день записано датой, а не временем."""
    s, e = ev.get("start", {}), ev.get("end", {})
    if "dateTime" in s:
        f = "%Y-%m-%dT%H:%M:%S%z"
        a = dt.datetime.strptime(s["dateTime"][:22] + s["dateTime"][23:], f)
        b = dt.datetime.strptime(e["dateTime"][:22] + e["dateTime"][23:], f)
        return a, b, False
    a = dt.datetime.fromisoformat(s.get("date", "1970-01-01"))
    b = dt.datetime.fromisoformat(e.get("date", "1970-01-01"))
    return a.replace(tzinfo=dt.timezone.utc), b.replace(tzinfo=dt.timezone.utc), True


def show(items: list) -> None:
    if not items:
        print("  пусто")
        return
    day = None
    for ev in items:
        a, b, allday = when(ev)
        d = a.date()
        if d != day:
            day = d
            print(f"\n  {d:%d.%m %a}")
        t = "весь день" if allday else f"{a:%H:%M}–{b:%H:%M}"
        who = ev.get("organizer", {}).get("email", "")
        tail = f"   [{len(ev.get('attendees', []))} уч.]" if ev.get("attendees") else ""
        print(f"    {t:12} {ev.get('summary', '(без названия)')[:58]}{tail}")


def free_slots(items: list, days: int, h_from: str, h_to: str, minutes: int) -> None:
    """Окна, куда влезает встреча нужной длины.

    Считается по будням в заданных часах: занятость берётся из событий, остальное
    свободно. События на весь день закрывают день целиком.
    """
    fh, fm = (int(x) for x in h_from.split(":"))
    th, tm = (int(x) for x in h_to.split(":"))
    busy = []
    for ev in items:
        a, b, allday = when(ev)
        if ev.get("transparency") == "transparent":
            continue                    # помечено как «свободен»
        busy.append((a.replace(tzinfo=None), b.replace(tzinfo=None), allday))

    today = dt.datetime.now().replace(second=0, microsecond=0)
    found = 0
    for i in range(days):
        d = (today + dt.timedelta(days=i)).date()
        if d.weekday() >= 5:
            continue
        start = dt.datetime.combine(d, dt.time(fh, fm))
        end = dt.datetime.combine(d, dt.time(th, tm))
        if i == 0:
            start = max(start, today)
        if start >= end:
            continue
        day_busy = sorted((max(a, start), min(b, end)) for a, b, ad in busy
                          if a.date() <= d <= (b - dt.timedelta(seconds=1)).date()
                          and (ad or (a < end and b > start)))
        cur, slots = start, []
        for a, b in day_busy:
            if a - cur >= dt.timedelta(minutes=minutes):
                slots.append((cur, a))
            cur = max(cur, b)
        if end - cur >= dt.timedelta(minutes=minutes):
            slots.append((cur, end))
        if slots:
            print(f"  {d:%d.%m %a}: " + ", ".join(f"{a:%H:%M}–{b:%H:%M}" for a, b in slots))
            found += len(slots)
    print(f"\n  окон не короче {minutes} мин: {found}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["today", "week", "list", "free", "add", "calendars"])
    ap.add_argument("title", nargs="?", help="название события для add")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--cal", default="primary")
    ap.add_argument("--start", help="для add: «2026-08-20 15:00»")
    ap.add_argument("--dur", type=int, default=60, help="для add: минут")
    ap.add_argument("--from", dest="h_from", default="10:00")
    ap.add_argument("--to", dest="h_to", default="19:00")
    ap.add_argument("--min", dest="minutes", type=int, default=60)
    a = ap.parse_args()

    svc = service()

    if a.cmd == "calendars":
        for c in svc.calendarList().list().execute().get("items", []):
            mark = "→" if c.get("primary") else " "
            print(f"  {mark} {c.get('summary', '')[:44]:46} {c['id']}")
        return 0

    if a.cmd == "add":
        if not a.title or not a.start:
            raise SystemExit("нужны название и --start")
        s = dt.datetime.strptime(a.start, "%Y-%m-%d %H:%M")
        body = {"summary": a.title,
                "start": {"dateTime": s.isoformat(), "timeZone": TZ},
                "end": {"dateTime": (s + dt.timedelta(minutes=a.dur)).isoformat(),
                        "timeZone": TZ}}
        ev = svc.events().insert(calendarId=a.cal, body=body).execute()
        print(f"  создано: {ev.get('summary')} {s:%d.%m %H:%M} (+{a.dur} мин)")
        print(f"  {ev.get('htmlLink')}")
        return 0

    days = {"today": 1, "week": 7}.get(a.cmd, a.days)
    items = events(svc, days, a.cal)

    if a.cmd == "free":
        free_slots(items, days, a.h_from, a.h_to, a.minutes)
        return 0

    print(f"  событий за {days} дн.: {len(items)}")
    show(items)
    return 0


if __name__ == "__main__":
    sys.exit(main())
