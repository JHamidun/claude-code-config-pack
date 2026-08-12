#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llms_txt — прeflight перед краулингом документации.

Многие проекты уже отдают готовый срез доков для LLM по /llms.txt (индекс со ссылками)
и /llms-full.txt (весь текст одним файлом). Спросить их — одна секунда;
краулить сайт — минуты и мусор. Поэтому это ПЕРВЫЙ шаг, а не запасной.

Главная ловушка: SPA-сайты отдают 200 + HTML на ЛЮБОЙ путь, включая несуществующий
/llms.txt. Наивная проверка "status == 200" даёт ложное «нашли» и скармливает
модели вёрстку вместо доков. Поэтому валидируем ТЕЛО, а не код ответа.

Зависимостей нет (stdlib: urllib).

API:
    from llms_txt import discover, parse, fetch
    r = discover("https://docs.example.com")   # -> dict, r["found"] bool
    doc = parse(r["text"])                     # -> {title, summary, sections, links}

CLI:
    python llms_txt.py <url> [--full] [--json] [--save DIR] [--quiet]
    python llms_txt.py <url1> <url2> ...       # батч-проверка
"""
from __future__ import annotations

import gzip
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

__all__ = ["CANDIDATES", "discover", "fetch", "parse", "looks_like_llms_txt"]

# Порядок важен: сначала индекс (дёшево), потом полный текст (может быть мегабайты).
CANDIDATES = ("/llms.txt", "/llms-full.txt")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Сколько байт тянем для валидации/индекса. llms-full.txt бывает 10+ МБ —
# без потолка это утечка контекста и времени.
PROBE_BYTES = 256 * 1024
MAX_BYTES = 8 * 1024 * 1024

_HTML_HEAD = re.compile(r"^\s*(<!doctype\s+html|<html\b|<\?xml|<head\b|<body\b)", re.I)
_HTML_TAGS = re.compile(r"</(html|head|body|div|script|nav|header)\s*>", re.I)
_MD_LINK = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_H1 = re.compile(r"^#\s+(.+)$", re.M)
_H2 = re.compile(r"^##\s+(.+)$", re.M)
_QUOTE = re.compile(r"^>\s?(.+)$", re.M)


def looks_like_llms_txt(body: str, content_type: str = "") -> tuple[bool, str]:
    """(ok, reason). Отличает настоящий llms.txt от SPA-заглушки и 404-страницы.

    Судим по телу: content-type у статики часто врёт (text/html на .txt),
    а SPA отдаёт 200 на что угодно.
    """
    if not body or not body.strip():
        return False, "empty body"
    head = body[:2000]
    if _HTML_HEAD.search(head) or len(_HTML_TAGS.findall(body[:20000])) >= 3:
        return False, "HTML page (SPA catch-all / 404 page), not a text index"
    ct = (content_type or "").lower()
    if "html" in ct and not head.lstrip().startswith("#"):
        return False, f"content-type={ct.split(';')[0]} and body has no markdown heading"
    if len(body.strip()) < 40:
        return False, f"too short ({len(body.strip())} chars)"
    # Спецификация llms.txt: H1-заголовок + список markdown-ссылок.
    # Достаточно любого внятного markdown-сигнала — часть сайтов кладёт голый текст доков.
    if _H1.search(body) or _H2.search(body) or _MD_LINK.search(body):
        return True, "ok"
    if body.count("\n") >= 5 and "http" in body:
        return True, "plain text with links (non-canonical but usable)"
    return False, "no markdown headings or links — does not look like a docs index"


def _get(url: str, timeout: float = 12.0, limit: int = PROBE_BYTES) -> dict:
    """GET с потолком по байтам. Возвращает {status, url, ctype, text, error, truncated}."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/plain, text/markdown, text/*;q=0.9, */*;q=0.5",
        "Accept-Encoding": "gzip",
    })
    out = {"status": 0, "url": url, "ctype": "", "text": "", "error": "",
           "truncated": False, "bytes": 0}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out["status"] = resp.status
            out["url"] = resp.geturl()
            out["ctype"] = resp.headers.get("Content-Type", "")
            raw = resp.read(limit + 1)
            if resp.headers.get("Content-Encoding", "").lower() == "gzip":
                try:
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                except Exception:  # noqa: BLE001 — битый gzip = не наш файл
                    pass
            if len(raw) > limit:
                out["truncated"] = True
                raw = raw[:limit]
            out["bytes"] = len(raw)
            out["text"] = raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        out["status"] = e.code
        out["error"] = f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 — DNS/TLS/таймаут: причина нужна текстом
        out["error"] = f"{type(e).__name__}: {str(e)[:120]}"
    return out


def _base_candidates(url: str) -> list[str]:
    """Кандидаты: рядом с указанным путём (docs.x/ru/ -> /ru/llms.txt) и в корне."""
    if "://" not in url:
        url = "https://" + url
    p = urllib.parse.urlsplit(url)
    root = f"{p.scheme}://{p.netloc}"
    bases = []
    path = p.path or "/"
    if not path.endswith("/"):
        path = path.rsplit("/", 1)[0] + "/"
    if path not in ("/", ""):
        bases.append(root + path.rstrip("/"))
    bases.append(root)
    seen, out = set(), []
    for b in bases:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


def discover(url: str, *, timeout: float = 12.0, candidates=CANDIDATES,
             limit: int = PROBE_BYTES) -> dict:
    """Пробует llms.txt-эндпоинты. Возвращает первый прошедший валидацию.

    {found, url, variant, text, bytes, truncated, tried:[{url,status,ok,reason}]}
    found=False — корректная деградация: зовущий идёт краулить как раньше.
    """
    tried = []
    for base in _base_candidates(url):
        for cand in candidates:
            full = base + cand
            r = _get(full, timeout=timeout, limit=limit)
            if r["status"] != 200:
                tried.append({"url": full, "status": r["status"],
                              "ok": False, "reason": r["error"] or f"HTTP {r['status']}"})
                continue
            ok, reason = looks_like_llms_txt(r["text"], r["ctype"])
            tried.append({"url": r["url"], "status": 200, "ok": ok, "reason": reason})
            if ok:
                return {"found": True, "url": r["url"], "variant": cand.strip("/"),
                        "text": r["text"], "bytes": r["bytes"],
                        "truncated": r["truncated"], "ctype": r["ctype"], "tried": tried}
    return {"found": False, "url": None, "variant": None, "text": "",
            "bytes": 0, "truncated": False, "ctype": "", "tried": tried}


def fetch(url: str, *, timeout: float = 30.0, limit: int = MAX_BYTES) -> dict:
    """Скачать конкретный llms.txt/llms-full.txt целиком (с валидацией тела)."""
    r = _get(url, timeout=timeout, limit=limit)
    ok, reason = (False, r["error"] or f"HTTP {r['status']}")
    if r["status"] == 200:
        ok, reason = looks_like_llms_txt(r["text"], r["ctype"])
    return {"found": ok, "url": r["url"], "reason": reason, "text": r["text"] if ok else "",
            "bytes": r["bytes"], "truncated": r["truncated"]}


def parse(text: str) -> dict:
    """Разбор llms.txt: title, summary (блок цитаты), секции H2 -> ссылки."""
    title = ""
    m = _H1.search(text or "")
    if m:
        title = m.group(1).strip()
    q = _QUOTE.search(text or "")
    summary = q.group(1).strip() if q else ""

    sections, links = [], []
    # Режем по H2; всё до первого H2 — преамбула.
    chunks = re.split(r"^##\s+", text or "", flags=re.M)
    for i, chunk in enumerate(chunks):
        if i == 0:
            name, body = "(preamble)", chunk
        else:
            name, _, body = chunk.partition("\n")
            name = name.strip()
        items = []
        for lm in _MD_LINK.finditer(body):
            item = {"title": lm.group(1).strip(), "url": lm.group(2).strip(),
                    "desc": (lm.group(3) or "").strip(), "section": name}
            # описание после ссылки в стиле спеки: "[t](u): описание"
            if not item["desc"]:
                tail = body[lm.end():lm.end() + 300].lstrip()
                if tail.startswith(":"):
                    item["desc"] = tail[1:].strip().split("\n")[0][:280]
            items.append(item)
            links.append(item)
        if items or (i > 0 and name):
            sections.append({"name": name, "links": items})

    return {"title": title, "summary": summary, "sections": sections,
            "links": links, "n_links": len(links), "chars": len(text or "")}


# ------------------------------ CLI ------------------------------
def _cli(argv) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__.split("CLI:")[-1].strip())
        return 2

    save_dir = None
    if "--save" in argv:
        i = argv.index("--save")
        if i + 1 < len(argv):
            save_dir = argv[i + 1]
            args = [a for a in args if a != save_dir]

    cands = ("/llms-full.txt", "/llms.txt") if "--full" in flags else CANDIDATES
    results = []
    for target in args:
        r = discover(target, candidates=cands,
                     limit=MAX_BYTES if "--full" in flags else PROBE_BYTES)
        doc = parse(r["text"]) if r["found"] else {}
        rec = {"domain": target, "found": r["found"], "url": r["url"],
               "variant": r["variant"], "bytes": r["bytes"], "truncated": r["truncated"],
               "title": doc.get("title", ""), "n_links": doc.get("n_links", 0),
               "sections": [s["name"] for s in doc.get("sections", [])][:12],
               "tried": r["tried"]}
        results.append(rec)
        if save_dir and r["found"]:
            import pathlib
            d = pathlib.Path(save_dir)
            d.mkdir(parents=True, exist_ok=True)
            host = urllib.parse.urlsplit(r["url"]).netloc.replace(":", "_")
            fp = d / f"{host}.{r['variant']}.txt"
            fp.write_text(r["text"], encoding="utf-8")
            rec["saved"] = str(fp)

    if "--json" in flags:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        for rec in results:
            if rec["found"]:
                print(f"[FOUND] {rec['domain']} -> {rec['url']}")
                print(f"        title={rec['title']!r} links={rec['n_links']} "
                      f"bytes={rec['bytes']}{' (truncated)' if rec['truncated'] else ''}")
                if rec["sections"]:
                    print(f"        sections: {', '.join(rec['sections'])}")
                if rec.get("saved"):
                    print(f"        saved: {rec['saved']}")
            else:
                print(f"[NONE ] {rec['domain']} — llms.txt нет, идём краулить как обычно")
                for t in rec["tried"]:
                    print(f"        tried {t['url']} -> {t['status']} {t['reason']}")
    return 0 if any(r["found"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
