# -*- coding: utf-8 -*-
"""Контракт упоминания (mention) + хелперы нормализации/дедупа.
ВСЕ коннекторы возвращают list[dict] этого формата (см. make_mention)."""
import re
import urllib.parse

# Канонические значения
TYPES = ["СМИ", "Агрегатор", "Соцсеть", "Читательский", "Видео", "Магазин"]
CHANNELS = [
    "googlenews", "serpapi_news", "serpapi_web", "yandex",
    "vk", "dzen", "telegram", "rsshub",
    "livelib", "marketplace", "youtube", "instagram", "tiktok", "reddit",
]

def make_mention(channel, *, type="СМИ", source="", url="", title="", snippet="",
                 date="", author="", lang="ru", views=None, likes=None, reposts=None,
                 comments=None, rating=None, rating_count=None, raw=None):
    """Единый конструктор упоминания. Коннекторы зовут его на каждую находку."""
    return {
        "channel": channel, "type": type, "source": source or "",
        "url": url or "", "title": (title or "").strip(), "snippet": (snippet or "").strip(),
        "date": date or "", "author": author or "", "lang": lang,
        # соц-метрики
        "views": views, "likes": likes, "reposts": reposts, "comments": comments,
        # читательские
        "rating": rating, "rating_count": rating_count,
        # сырьё
        "raw": raw or {},
    }

# ---------- нормализация ----------
def norm_url(u):
    u = (u or "").split("#")[0]
    # YouTube/watch различаются только query ?v=ID — сохраняем идентификатор видео
    mv = re.search(r"[?&]v=([\w-]{6,})", u)
    base = u.split("?")[0].rstrip("/").lower()
    base = re.sub(r"^https?://(www\.)?", "", base)
    return f"{base}?v={mv.group(1)}" if mv else base

def domain(m):
    u = m.get("url", "")
    if u:
        try:
            d = urllib.parse.urlparse(u if "//" in u else "//" + u, scheme="https").netloc
            return d.replace("www.", "").lower()
        except Exception:
            pass
    return (m.get("source", "") or "").lower()

def norm_title(t):
    return re.sub(r"[^а-яёa-z0-9 ]", "", (t or "").lower()).strip()

# ---------- дедуп по url/заголовку ----------
def dedupe(mentions):
    """Грубый дедуп по нормализованному url ИЛИ заголовку. Сохраняет первое вхождение."""
    seen_u, seen_t, out = set(), set(), []
    for m in mentions:
        nu, nt = norm_url(m.get("url", "")), norm_title(m.get("title", ""))
        if nu and nu in seen_u:
            continue
        if nt and len(nt) > 12 and nt in seen_t:
            continue
        if nu:
            seen_u.add(nu)
        if nt:
            seen_t.add(nt)
        out.append(m)
    return out
