#!/usr/bin/env python3
"""Yandex API CLI helper for Claude Code.

Usage:
    python yandex_api.py metrika report --metrics "ym:s:visits" --date1 "7daysAgo" --date2 "today"
    python yandex_api.py metrika goals
    python yandex_api.py disk ls [path]
    python yandex_api.py disk info
    python yandex_api.py disk upload <local_path> <remote_path>
    python yandex_api.py disk download <remote_path> <local_path>
    python yandex_api.py disk delete <path>
    python yandex_api.py disk large-files [--limit 20]
    python yandex_api.py disk cleanup-trash
    python yandex_api.py webmaster sites
    python yandex_api.py webmaster queries <host_id> [--date_from] [--date_to]
    python yandex_api.py iot devices
    python yandex_api.py iot action <device_id> <capability> <value>
    python yandex_api.py iot scenarios
    python yandex_api.py direct campaigns
    python yandex_api.py direct stats --date_from "2024-01-01" --date_to "2024-01-31"
    python yandex_api.py audience segments
    python yandex_api.py telemost create <title>
    python yandex_api.py telemost list
    python yandex_api.py calendar events [--days 7]
    python yandex_api.py wordstat create "keyword1" "keyword2"
    python yandex_api.py wordstat get <report_id>
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

# Ключи берутся из окружения. Файл .credentials.master.env — просто удобный способ
# держать их в одном месте; заведи его из templates/.credentials.master.env.example.
# Путь переопределяется через CREDENTIALS_ENV, если хранишь ключи где-то ещё.
try:
    from dotenv import load_dotenv
    _env = os.getenv("CREDENTIALS_ENV") or (Path.home() / ".claude" / ".credentials.master.env")
    load_dotenv(_env)
except ImportError:
    pass  # переменные окружения и без dotenv работают

TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
COUNTER_ID = os.getenv("YANDEX_METRIKA_COUNTER_ID")

if not TOKEN or TOKEN == "PLACEHOLDER":
    print("ERROR: YANDEX_OAUTH_TOKEN not set or is PLACEHOLDER.")
    client_id = os.getenv("YANDEX_OAUTH_CLIENT_ID")
    if not client_id:
        print("1) Register your OWN app: https://oauth.yandex.ru/client/new")
        print("   Tick the scopes you need (metrika / direct / disk / webmaster / iot).")
        print("   A foreign client_id will not work.")
        print("2) Put its id into YANDEX_OAUTH_CLIENT_ID and rerun for the token URL.")
    else:
        print("Get token: https://oauth.yandex.ru/authorize?response_type=token"
              f"&client_id={client_id}")
    sys.exit(1)

HEADERS = {"Authorization": f"OAuth {TOKEN}"}


def api_get(url, params=None, extra_headers=None):
    h = {**HEADERS, **(extra_headers or {})}
    resp = requests.get(url, headers=h, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_post(url, json_data=None, extra_headers=None):
    h = {**HEADERS, **(extra_headers or {})}
    resp = requests.post(url, headers=h, json=json_data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_put(url, params=None, extra_headers=None):
    h = {**HEADERS, **(extra_headers or {})}
    resp = requests.put(url, headers=h, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json() if resp.content else {"status": "ok"}


def api_delete(url, params=None):
    resp = requests.delete(url, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    return {"status": "deleted"}


def pp(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


# === METRIKA ===

def metrika_report(args):
    params = {
        "ids": args.counter or COUNTER_ID,
        "metrics": args.metrics,
        "date1": args.date1,
        "date2": args.date2,
    }
    if args.dimensions:
        params["dimensions"] = args.dimensions
    if args.sort:
        params["sort"] = args.sort
    if args.limit:
        params["limit"] = args.limit
    pp(api_get("https://api-metrika.yandex.net/stat/v1/data", params))


def metrika_goals(args):
    counter = args.counter or COUNTER_ID
    pp(api_get(f"https://api-metrika.yandex.net/management/v1/counter/{counter}/goals"))


def metrika_counters(args):
    pp(api_get("https://api-metrika.yandex.net/management/v1/counters"))


def metrika_segments(args):
    counter = args.counter or COUNTER_ID
    pp(api_get(f"https://api-metrika.yandex.net/management/v1/counter/{counter}/apisegment/segments"))


# === DISK ===

DISK_BASE = "https://cloud-api.yandex.net/v1/disk"


def disk_info(args):
    pp(api_get(DISK_BASE))


def disk_ls(args):
    path = args.path if args.path else "/"
    params = {"path": path, "limit": args.limit or 50, "sort": "-modified"}
    pp(api_get(f"{DISK_BASE}/resources", params))


def disk_upload(args):
    resp = api_get(f"{DISK_BASE}/resources/upload",
                   {"path": args.remote_path, "overwrite": "true"})
    upload_url = resp["href"]
    with open(args.local_path, "rb") as f:
        r = requests.put(upload_url, data=f, timeout=300)
        r.raise_for_status()
    print(f"Uploaded {args.local_path} -> {args.remote_path}")


def disk_download(args):
    resp = api_get(f"{DISK_BASE}/resources/download", {"path": args.remote_path})
    download_url = resp["href"]
    r = requests.get(download_url, timeout=300)
    r.raise_for_status()
    with open(args.local_path, "wb") as f:
        f.write(r.content)
    print(f"Downloaded {args.remote_path} -> {args.local_path}")


def disk_delete(args):
    pp(api_delete(f"{DISK_BASE}/resources", {"path": args.path, "permanently": args.permanent}))


def disk_large_files(args):
    pp(api_get(f"{DISK_BASE}/resources/files",
               {"limit": args.limit or 20, "sort": "-size"}))


def disk_cleanup_trash(args):
    pp(api_delete(f"{DISK_BASE}/trash/resources"))


def disk_mkdir(args):
    pp(api_put(f"{DISK_BASE}/resources", {"path": args.path}))


# === WEBMASTER ===

WM_BASE = "https://api.webmaster.yandex.net/v4"


def _wm_user_id():
    data = api_get(f"{WM_BASE}/user")
    return data["user_id"]


def webmaster_sites(args):
    uid = _wm_user_id()
    pp(api_get(f"{WM_BASE}/user/{uid}/hosts"))


def webmaster_queries(args):
    uid = _wm_user_id()
    params = {}
    if args.date_from:
        params["date_from"] = args.date_from
    if args.date_to:
        params["date_to"] = args.date_to
    pp(api_get(f"{WM_BASE}/user/{uid}/hosts/{args.host_id}/search-queries/all", params))


def webmaster_backlinks(args):
    uid = _wm_user_id()
    pp(api_get(f"{WM_BASE}/user/{uid}/hosts/{args.host_id}/links/external/samples"))


# === IOT ===

IOT_BASE = "https://api.iot.yandex.net/v1.0"


def iot_devices(args):
    pp(api_get(f"{IOT_BASE}/user/info"))


def iot_action(args):
    value = args.value
    if value.lower() in ("true", "on", "1"):
        value = True
    elif value.lower() in ("false", "off", "0"):
        value = False
    payload = {
        "devices": [{
            "id": args.device_id,
            "actions": [{
                "type": args.capability,
                "state": {"instance": "on", "value": value}
            }]
        }]
    }
    pp(api_post(f"{IOT_BASE}/devices/actions", payload))


def iot_scenarios(args):
    data = api_get(f"{IOT_BASE}/user/info")
    scenarios = data.get("scenarios", [])
    pp(scenarios)


def iot_run_scenario(args):
    pp(api_post(f"{IOT_BASE}/scenarios/{args.scenario_id}/actions"))


# === DIRECT ===

DIRECT_BASE = "https://api.direct.yandex.com/json/v5"
DIRECT_HEADERS = {"Accept-Language": "ru"}


def direct_campaigns(args):
    payload = {
        "method": "get",
        "params": {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Status", "State", "DailyBudget",
                           "StartDate", "EndDate", "Statistics"]
        }
    }
    pp(api_post(f"{DIRECT_BASE}/campaigns", payload, DIRECT_HEADERS))


def direct_stats(args):
    payload = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": args.date_from,
                "DateTo": args.date_to
            },
            "FieldNames": ["CampaignName", "Impressions", "Clicks", "Cost", "Ctr", "AvgCpc"],
            "ReportName": "Claude Code Report",
            "ReportType": "CAMPAIGN_PERFORMANCE_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES"
        }
    }
    h = {**HEADERS, **DIRECT_HEADERS, "returnMoneyInMicros": "false", "skipReportHeader": "true"}
    resp = requests.post(f"{DIRECT_BASE}/reports", headers=h,
                         json=payload, timeout=60)
    if resp.status_code == 200:
        print(resp.text)
    elif resp.status_code == 201:
        print("Report queued, retry in a few seconds")
    elif resp.status_code == 202:
        print("Report in progress, retry in a few seconds")
    else:
        resp.raise_for_status()


# === AUDIENCE ===

def audience_segments(args):
    pp(api_get("https://api-audience.yandex.ru/v1/management/segments"))


# === TELEMOST ===

TELEMOST_BASE = "https://cloud-api.yandex.net/v1/telemost"


def telemost_create(args):
    pp(api_post(f"{TELEMOST_BASE}/conferences",
                {"access_level": "PUBLIC", "title": args.title}))


def telemost_list(args):
    pp(api_get(f"{TELEMOST_BASE}/conferences"))


# === CALENDAR (CalDAV) ===

def calendar_events(args):
    try:
        import caldav
        from datetime import datetime, timedelta
    except ImportError:
        print("ERROR: 'caldav' not installed. Run: pip install caldav")
        sys.exit(1)

    email = os.getenv("YANDEX_EMAIL", "")
    client = caldav.DAVClient(
        url="https://caldav.yandex.ru",
        username=email,
        password=TOKEN
    )
    principal = client.principal()
    calendars = principal.calendars()

    days = int(args.days) if args.days else 7
    now = datetime.now()
    events = []
    for cal in calendars:
        for event in cal.date_search(start=now, end=now + timedelta(days=days)):
            events.append(str(event.data))

    if events:
        for e in events:
            print(e)
            print("---")
    else:
        print(f"No events in next {days} days")


# === WORDSTAT ===

WORDSTAT_BASE = "https://api.direct.yandex.com/v4/json/"


def wordstat_create(args):
    payload = {
        "method": "CreateNewWordstatReport",
        "param": {"Phrases": args.keywords},
        "token": TOKEN
    }
    # Direct API v4 requires UTF-8 body bytes (error 501 "Request encoding is not UTF8")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(WORDSTAT_BASE, data=body,
                         headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30)
    pp(resp.json())


def wordstat_get(args):
    payload = {
        "method": "GetWordstatReport",
        "param": int(args.report_id),
        "token": TOKEN
    }
    resp = requests.post(WORDSTAT_BASE, json=payload, timeout=30)
    pp(resp.json())


def wordstat_list(args):
    payload = {
        "method": "GetWordstatReportList",
        "token": TOKEN
    }
    resp = requests.post(WORDSTAT_BASE, json=payload, timeout=30)
    pp(resp.json())


# === CLI ===

def main():
    parser = argparse.ArgumentParser(description="Yandex API CLI")
    sub = parser.add_subparsers(dest="service", required=True)

    # -- Metrika --
    m = sub.add_parser("metrika")
    ms = m.add_subparsers(dest="action", required=True)

    mr = ms.add_parser("report")
    mr.add_argument("--metrics", default="ym:s:visits,ym:s:pageviews,ym:s:users")
    mr.add_argument("--dimensions", default="ym:s:date")
    mr.add_argument("--date1", default="7daysAgo")
    mr.add_argument("--date2", default="today")
    mr.add_argument("--counter")
    mr.add_argument("--sort")
    mr.add_argument("--limit", type=int)
    mr.set_defaults(func=metrika_report)

    mg = ms.add_parser("goals")
    mg.add_argument("--counter")
    mg.set_defaults(func=metrika_goals)

    mc = ms.add_parser("counters")
    mc.set_defaults(func=metrika_counters)

    mseg = ms.add_parser("segments")
    mseg.add_argument("--counter")
    mseg.set_defaults(func=metrika_segments)

    # -- Disk --
    d = sub.add_parser("disk")
    ds = d.add_subparsers(dest="action", required=True)

    di = ds.add_parser("info")
    di.set_defaults(func=disk_info)

    dl = ds.add_parser("ls")
    dl.add_argument("path", nargs="?", default="/")
    dl.add_argument("--limit", type=int, default=50)
    dl.set_defaults(func=disk_ls)

    du = ds.add_parser("upload")
    du.add_argument("local_path")
    du.add_argument("remote_path")
    du.set_defaults(func=disk_upload)

    dd = ds.add_parser("download")
    dd.add_argument("remote_path")
    dd.add_argument("local_path")
    dd.set_defaults(func=disk_download)

    ddel = ds.add_parser("delete")
    ddel.add_argument("path")
    ddel.add_argument("--permanent", action="store_true")
    ddel.set_defaults(func=disk_delete)

    dlf = ds.add_parser("large-files")
    dlf.add_argument("--limit", type=int, default=20)
    dlf.set_defaults(func=disk_large_files)

    dct = ds.add_parser("cleanup-trash")
    dct.set_defaults(func=disk_cleanup_trash)

    dmk = ds.add_parser("mkdir")
    dmk.add_argument("path")
    dmk.set_defaults(func=disk_mkdir)

    # -- Webmaster --
    w = sub.add_parser("webmaster")
    ws = w.add_subparsers(dest="action", required=True)

    wsi = ws.add_parser("sites")
    wsi.set_defaults(func=webmaster_sites)

    wq = ws.add_parser("queries")
    wq.add_argument("host_id")
    wq.add_argument("--date_from")
    wq.add_argument("--date_to")
    wq.set_defaults(func=webmaster_queries)

    wb = ws.add_parser("backlinks")
    wb.add_argument("host_id")
    wb.set_defaults(func=webmaster_backlinks)

    # -- IoT --
    i = sub.add_parser("iot")
    is_ = i.add_subparsers(dest="action", required=True)

    idev = is_.add_parser("devices")
    idev.set_defaults(func=iot_devices)

    iact = is_.add_parser("action")
    iact.add_argument("device_id")
    iact.add_argument("capability")
    iact.add_argument("value")
    iact.set_defaults(func=iot_action)

    isc = is_.add_parser("scenarios")
    isc.set_defaults(func=iot_scenarios)

    irun = is_.add_parser("run-scenario")
    irun.add_argument("scenario_id")
    irun.set_defaults(func=iot_run_scenario)

    # -- Direct --
    dr = sub.add_parser("direct")
    drs = dr.add_subparsers(dest="action", required=True)

    drc = drs.add_parser("campaigns")
    drc.set_defaults(func=direct_campaigns)

    drst = drs.add_parser("stats")
    drst.add_argument("--date_from", required=True)
    drst.add_argument("--date_to", required=True)
    drst.set_defaults(func=direct_stats)

    # -- Audience --
    au = sub.add_parser("audience")
    aus = au.add_subparsers(dest="action", required=True)

    auseg = aus.add_parser("segments")
    auseg.set_defaults(func=audience_segments)

    # -- Telemost --
    t = sub.add_parser("telemost")
    ts = t.add_subparsers(dest="action", required=True)

    tcr = ts.add_parser("create")
    tcr.add_argument("title")
    tcr.set_defaults(func=telemost_create)

    tls = ts.add_parser("list")
    tls.set_defaults(func=telemost_list)

    # -- Calendar --
    c = sub.add_parser("calendar")
    cs = c.add_subparsers(dest="action", required=True)

    cev = cs.add_parser("events")
    cev.add_argument("--days", default="7")
    cev.set_defaults(func=calendar_events)

    # -- Wordstat --
    wst = sub.add_parser("wordstat")
    wsts = wst.add_subparsers(dest="action", required=True)

    wstc = wsts.add_parser("create")
    wstc.add_argument("keywords", nargs="+")
    wstc.set_defaults(func=wordstat_create)

    wstg = wsts.add_parser("get")
    wstg.add_argument("report_id")
    wstg.set_defaults(func=wordstat_get)

    wstl = wsts.add_parser("list")
    wstl.set_defaults(func=wordstat_list)

    args = parser.parse_args()
    try:
        args.func(args)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
