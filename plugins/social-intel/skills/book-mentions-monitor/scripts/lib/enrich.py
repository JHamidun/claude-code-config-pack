# -*- coding: utf-8 -*-
"""Обогащение упоминаний: релевантность (лемма+якоря), тип/уровень/категория,
тональность-fallback, МедиаИндекс. LLM-дизамбигуация/тональность — отдельно (оркестратор)."""
import json, math, pathlib, re
from lib.mention import domain

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = ROOT.parent / "config"

# --- лемматизация из seo-machine (pymorphy3), с fallback ---
try:
    from lib.keyword_analyzer_ru import tokens as _tokens, norm_phrase as _norm_phrase, count_phrase as _count_phrase
    _LEM = True
except Exception:
    _LEM = False
    def _tokens(t): return re.findall(r"[а-яёa-z]+", (t or "").lower())
    def _norm_phrase(p): return tuple((p or "").lower().split())
    def _count_phrase(toks, ph):
        s = " ".join(toks); return s.count(ph.lower()) if ph else 0

try:
    from lib.content_scrubber import scrub as _scrub
except Exception:
    def _scrub(t): return re.sub(r"\s+", " ", t or "").strip()


def load_registry():
    p = CFG / "media-registry.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"domains": {}, "aggregators": [], "shops": [], "social_domains": {}, "reach_estimate": {}}


def _text(m):
    return " ".join([m.get("title", ""), m.get("snippet", ""), m.get("source", ""), m.get("url", "")])


def _fix_mojibake(t):
    """Чинит UTF-8, ошибочно прочитанный как cp1251 (mojibake вида «Ð...Ñ...» → нормальный текст)."""
    if not t:
        return t
    moji = sum(c in "РСÐÑђ" for c in t)
    if moji / max(len(t), 1) > 0.15:
        try:
            fixed = t.encode("cp1251").decode("utf-8")
            if sum(c in "РСÐÑ" for c in fixed) < moji:
                return fixed
        except Exception:
            pass
    return t


def scrub_mention(m):
    m["title"] = _scrub(_fix_mojibake(m.get("title", "")))
    m["snippet"] = _scrub(_fix_mojibake(m.get("snippet", "")))
    return m


def relevance(m, book):
    """Дешёвый pre-LLM фильтр (леммы + якоря + минус-слова). Opus уточняет позже."""
    txt = _text(m).lower()
    toks = _tokens(txt)
    title_ph = " ".join(_norm_phrase(book.get("title", "")))
    has_title = _count_phrase(toks, title_ph) > 0 or (len(book.get("title", "")) > 5 and book.get("title", "").lower() in txt)
    anchors = [a.lower() for a in book.get("anchors", [])]
    has_anchor = any(a in txt for a in anchors) or any(_count_phrase(toks, " ".join(_norm_phrase(a))) > 0 for a in anchors)
    if not (has_title or has_anchor):
        return False
    # минус-слова: если есть и нет якоря — отбросить
    excl = [e.lower() for e in book.get("exclude", [])]
    if any(e in txt for e in excl) and not has_anchor:
        return False
    return True


def classify_source(m, reg):
    d = domain(m)
    ch = m.get("channel", "")
    soc = reg.get("social_domains", {})
    # соцсети/видео/читательские по каналу или домену
    if ch in ("vk", "dzen", "telegram", "rsshub", "instagram", "tiktok", "reddit"):
        m["_type"] = "Соцсеть"
    elif ch == "youtube":
        m["_type"] = "Видео"
    elif ch == "livelib":
        m["_type"] = "Читательский"
    elif ch == "marketplace" or any(s in d for s in reg.get("shops", [])):
        m["_type"] = "Магазин"
    elif any(a in d for a in reg.get("aggregators", [])):
        m["_type"] = "Агрегатор"
    else:
        m["_type"] = m.get("type") or "СМИ"
    # уровень/категория/город из реестра
    info = reg.get("domains", {}).get(d, {})
    m["_level"] = info.get("level", "Федеральный" if m["_type"] in ("СМИ", "Агрегатор") else "—")
    m["_category"] = info.get("category", {"Соцсеть": soc.get(d, "Соцсеть"), "Видео": "YouTube",
                                            "Читательский": "LiveLib", "Магазин": "Маркетплейс"}.get(m["_type"], "Интернет-СМИ"))
    m["_city"] = info.get("city", "")
    if info.get("name") and not m.get("source"):
        m["source"] = info["name"]
    return m


POS = ["лучш", "топ-100", "топ 100", "победител", "рекоменд", "любим", "восхищ", "прекрасн",
       "подар", "новинк", "выбор", "интересн", "важн", "классн", "успех", "номинац", "восторг", "роскошн"]
NEG = ["скандал", "провал", "критик", "плох", "запрет", " иск ", " суд ", "ошибк", "претензи", "разочаров", "фейк"]


def tone_rule(m):
    t = _text(m).lower()
    if any(n in t for n in NEG):
        return "Негатив"
    if any(p in t for p in POS):
        return "Позитив"
    return "Нейтрал"


def media_index(m, n_reprint=0):
    """МедиаИндекс упоминания = заметность. f(охват, тональность, роль, цитирование, перепечатки)."""
    r = m.get("_reach") or 0
    wt = {"Позитив": 1.0, "Нейтрал": 0.5, "Негатив": -1.0}.get(m.get("_tone", "Нейтрал"), 0.5)
    wr = 1.5 if m.get("_role") == "Главная" else 1.0
    wc = 1.3 if m.get("_cite") == "Да" else 1.0
    eng = (m.get("views") or 0) * 0.0001 + (m.get("likes") or 0) * 0.01 + (m.get("reposts") or 0) * 0.05
    base = math.log10(r + 10) + math.log10(eng + 1)
    return round(base * wt * wr * wc / math.sqrt(n_reprint + 1), 2)


def enrich_all(mentions, book, reg=None):
    reg = reg or load_registry()
    for m in mentions:
        scrub_mention(m)
        m["_relevant"] = relevance(m, book)
        classify_source(m, reg)
        m.setdefault("_role", "Эпизодическая")
        m.setdefault("_genre", "Новость")
        m.setdefault("_cite", "Нет")
        m.setdefault("_is_target", m["_relevant"])
        # охват-оценка из реестра (если reach.py не проставил)
        if "_reach" not in m:
            d = domain(m)
            m["_reach"] = next((v for k, v in reg.get("reach_estimate", {}).items() if k in d), 0)
    return mentions
