# -*- coding: utf-8 -*-
"""Коннектор RSSHub — публичные Telegram-каналы (издательства, книжные блоги).

RSSHub отдаёт RSS для Telegram-каналов: /telegram/channel/<slug>.
Настройка через .env:
  RSSHUB_BASE_URL   — адрес вашего RSSHub-инстанса (по умолчанию https://rsshub.app)
  RSSHUB_SSH_HOST   — (опц.) если инстанс закрыт и доступен только по SSH:
                      запрос пойдёт как `ssh <host> curl <base>/...`
Каналы берутся из book["telegram_channels"] (список slug без @), либо из
creds["RSSHUB_TG_CHANNELS"] (через запятую). Фильтрация постов — по anchors/exclude.
Если каналы не заданы или инстанс недоступен — коннектор возвращает [].
"""
import sys
import re
import html
import subprocess
import urllib.request
import ssl
import pathlib
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def _unescape(t):
    t = html.unescape(t or "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()


def _fetch(base, ssh_host, channel):
    url = f"{base.rstrip('/')}/telegram/channel/{channel}"
    if ssh_host:
        try:
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", ssh_host,
                                f"curl -sS --max-time 45 {url!r}"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            return r.stdout if r.returncode == 0 and "<?xml" in (r.stdout or "")[:200] else None
        except Exception:
            return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return urllib.request.urlopen(req, timeout=40, context=CTX).read().decode("utf-8", "replace")
    except Exception:
        return None


def _parse(xml_text, slug):
    clean = re.sub(r"<\?xml[^?]*\?>", "", xml_text, count=1).strip()
    try:
        root = ET.fromstring(clean)
    except Exception:
        try:
            root = ET.fromstring(xml_text.encode("utf-8"))
        except Exception:
            return []
    ch = root.find("channel")
    if ch is None:
        return []
    out = []
    for it in ch.findall("item"):
        def tx(tag):
            el = it.find(tag); return (el.text or "") if el is not None else ""
        out.append({"title": _unescape(tx("title")), "description": _unescape(tx("description")),
                    "link": tx("link").strip(), "pubDate": tx("pubDate")[:25], "slug": slug})
    return out


def _matches(item, book):
    hay = (item["title"] + " " + item["description"]).lower()
    if any(e.lower() in hay for e in book.get("exclude", [])):
        return False
    kws = [a.lower() for a in book.get("anchors", [])] + \
          [a.split()[0].lower() for a in book.get("authors", []) if len(a.split()[0]) > 3] + \
          ([book.get("title", "").lower()] if len(book.get("title", "")) > 4 else [])
    return any(k in hay for k in kws if k)


def collect(book, creds, limit=50):
    creds = creds or {}
    base = creds.get("RSSHUB_BASE_URL") or "https://rsshub.app"
    ssh_host = creds.get("RSSHUB_SSH_HOST") or ""
    channels = list(book.get("telegram_channels", []))
    extra = creds.get("RSSHUB_TG_CHANNELS", "")
    if extra:
        channels += [s.strip() for s in extra.split(",") if s.strip()]
    channels = list(dict.fromkeys(c for c in channels if c))
    if not channels:
        return []
    out = []
    for slug in channels:
        if len(out) >= limit:
            break
        xml_text = _fetch(base, ssh_host, slug)
        if not xml_text:
            continue
        for item in _parse(xml_text, slug):
            if len(out) >= limit:
                break
            if _matches(item, book):
                out.append(make_mention(channel="rsshub", type="Соцсеть", source=f"@{slug}",
                                        url=item["link"], title=item["title"], snippet=item["description"][:400],
                                        date=item["pubDate"], author=f"@{slug}", raw=item))
    return out


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
