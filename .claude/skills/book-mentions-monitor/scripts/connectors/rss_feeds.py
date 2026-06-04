# -*- coding: utf-8 -*-
"""Generic RSS-коннектор — произвольные RSS/Atom-фиды профильных медиа.

Список фидов берётся из book["rss_feeds"] (список URL) и/или
creds["RSS_FEEDS"] (через запятую). Парсит RSS 2.0 и Atom, фильтрует
записи по anchors/exclude книги. Без ключей, только urllib.
Пример фидов: книжные/детлит медиа, культурные разделы СМИ, блоги издательств.
"""
import sys
import re
import html
import ssl
import urllib.request
import pathlib
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.mention import make_mention

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def _clean(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(t or ""))).strip()


def _fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return urllib.request.urlopen(req, timeout=30, context=CTX).read()
    except Exception:
        return None


def _parse(raw):
    """Возвращает список {title, link, desc, date} для RSS 2.0 и Atom."""
    items = []
    try:
        root = ET.fromstring(raw)
    except Exception:
        return items
    tag = root.tag.lower()
    # RSS 2.0
    ch = root.find("channel")
    if ch is not None:
        for it in ch.findall("item"):
            g = lambda t: (it.findtext(t) or "")
            items.append({"title": _clean(g("title")), "link": g("link").strip(),
                          "desc": _clean(g("description")), "date": g("pubDate")[:25]})
        return items
    # Atom
    if tag.endswith("feed"):
        nsm = {"a": "http://www.w3.org/2005/Atom"}
        for e in root.findall("a:entry", nsm):
            link_el = e.find("a:link", nsm)
            link = link_el.get("href") if link_el is not None else ""
            items.append({"title": _clean(e.findtext("a:title", "", nsm)),
                          "link": (link or "").strip(),
                          "desc": _clean(e.findtext("a:summary", "", nsm) or e.findtext("a:content", "", nsm)),
                          "date": (e.findtext("a:updated", "", nsm) or "")[:25]})
    return items


def _relevant(item, book):
    hay = (item["title"] + " " + item["desc"]).lower()
    if any(e.lower() in hay for e in book.get("exclude", [])):
        return False
    kws = [a.lower() for a in book.get("anchors", [])] + \
          [a.split()[0].lower() for a in book.get("authors", []) if len(a.split()[0]) > 3]
    title = book.get("title", "").lower()
    if len(title) > 6:
        kws.append(title)
    return any(k in hay for k in kws if k)


def collect(book, creds, limit=50):
    feeds = list(book.get("rss_feeds", []))
    extra = (creds or {}).get("RSS_FEEDS", "")
    if extra:
        feeds += [u.strip() for u in extra.split(",") if u.strip()]
    feeds = list(dict.fromkeys(f for f in feeds if f))
    out = []
    for url in feeds:
        if len(out) >= limit:
            break
        raw = _fetch(url)
        if not raw:
            continue
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        for item in _parse(raw):
            if len(out) >= limit:
                break
            if item["title"] and _relevant(item, book):
                out.append(make_mention(channel="rss", type="СМИ", source=host,
                                        url=item["link"], title=item["title"],
                                        snippet=item["desc"][:400], date=item["date"], raw=item))
    return out


if __name__ == "__main__":
    from lib._smoke import run_smoke
    run_smoke(collect)
