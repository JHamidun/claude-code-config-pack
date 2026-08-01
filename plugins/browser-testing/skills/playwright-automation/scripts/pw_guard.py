#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pw_guard — три защиты для скрапинга: окно снапшота, детектор блокировки, skip антибот-фреймов.

Зависимостей нет (только playwright/patchright, который уже нужен вызывающему).
Работает и с playwright, и с patchright — принимает любой page-объект.

1. window_snapshot(page, offset, max_chars, tail_chars)
   aria-снапшот большой страницы = сотни тысяч символов; MCP отдаёт их в контекст ЦЕЛИКОМ.
   Режем окном, но ВСЕГДА подклеиваем хвост — пагинация и навигация живут в подвале.
2. is_blocked(page) -> (bool, reason)
   Пустой результат скрапера неотличим от «ничего не нашлось». Ловим бан явно.
3. SKIP_FRAME_PATTERNS — антибот-фреймы висят по таймауту и засоряют снапшот.

CLI-самопроверка:  python pw_guard.py <url>
"""
from __future__ import annotations

import re
import sys

__all__ = [
    "SKIP_FRAME_PATTERNS",
    "should_skip_frame",
    "aria_snapshot",
    "window_snapshot",
    "BLOCK_PATTERNS",
    "is_blocked",
    "BlockedError",
]

# --- 3. skip-лист антибот-фреймов -------------------------------------------------
# Эти iframe'ы либо висят по таймауту, либо дают мусор в снапшоте (капчи, трекеры).
SKIP_FRAME_PATTERNS = (
    "recaptcha",
    "px-iframe",
    "px-captcha",
    "perimeterx",
    "captcha",
    "hcaptcha",
    "arkose",
    "funcaptcha",
    "datadome",
    "gstatic",
    "extensions.shopifycdn",
)


def should_skip_frame(url: str) -> bool:
    u = (url or "").lower()
    return any(p in u for p in SKIP_FRAME_PATTERNS)


# --- 1. окно снапшота -------------------------------------------------------------
def aria_snapshot(page, include_frames: bool = True, frame_timeout: int = 3000) -> str:
    """aria-снапшот главного фрейма + дочерних (антибот-фреймы пропускаются)."""
    parts = []
    try:
        parts.append(page.locator("body").aria_snapshot(timeout=frame_timeout * 3))
    except Exception as e:  # noqa: BLE001 - снапшот не должен ронять пайплайн
        parts.append(f"# aria-snapshot main frame failed: {str(e)[:120]}")
    if include_frames:
        for fr in getattr(page, "frames", [])[1:]:
            url = getattr(fr, "url", "") or ""
            if should_skip_frame(url):
                parts.append(f"# [frame skipped: antibot] {url[:120]}")
                continue
            try:
                snap = fr.locator("body").aria_snapshot(timeout=frame_timeout)
            except Exception as e:  # noqa: BLE001
                parts.append(f"# [frame failed] {url[:120]}: {str(e)[:80]}")
                continue
            if snap and snap.strip():
                parts.append(f"# [frame] {url[:160]}\n{snap}")
    return "\n".join(parts)


def window_snapshot(source, offset: int = 0, max_chars: int = 80000,
                    tail_chars: int = 5000, **snap_kwargs) -> dict:
    """Окно текста/снапшота с обязательным хвостом.

    source — page-объект (снимет aria) или готовая строка.
    Возвращает {text, next_offset, total, truncated, offset, window_chars, tail_chars}.
    Хвост подклеивается ВСЕГДА при обрезке: пагинация («Next», «Следующая», «→ 2 3 4»)
    и футер-навигация живут в конце документа — потеряв их, дальше идти нечем.
    """
    text = source if isinstance(source, str) else aria_snapshot(source, **snap_kwargs)
    total = len(text)
    offset = max(0, min(int(offset), total))
    max_chars = max(1, int(max_chars))
    tail_chars = max(0, int(tail_chars))

    window = text[offset:offset + max_chars]
    end = offset + len(window)
    truncated = end < total

    out = window
    tail_len = 0
    if truncated:
        tail_start = max(end, total - tail_chars) if tail_chars else total
        skipped = tail_start - end
        out += (f"\n\n--- [truncated at char {end} of {total}; "
                f"{skipped} chars omitted; next_offset={end}] ---\n")
        if tail_start < total:
            tail = text[tail_start:]
            tail_len = len(tail)
            out += f"--- [tail: last {tail_len} chars, from char {tail_start}] ---\n{tail}"

    return {
        "text": out,
        "offset": offset,
        "next_offset": end if truncated else None,
        "total": total,
        "truncated": truncated,
        "window_chars": len(window),
        "tail_chars": tail_len,
    }


# --- 2. детектор блокировки -------------------------------------------------------
# (имя, regex). Регистронезависимо, ищем в title + видимом тексте страницы.
BLOCK_PATTERNS = (
    ("google_unusual_traffic", r"Our systems have detected unusual traffic"),
    ("google_about_this_page", r"About this page"),
    ("google_search_trouble", r"If you are having trouble accessing Google Search"),
    ("google_sg_rel", r"SG_REL"),
    ("cloudflare_just_a_moment", r"Just a moment"),
    ("cloudflare_checking_browser", r"Checking your browser|Checking if the site connection is secure"),
    ("cloudflare_attention", r"Attention Required|Sorry, you have been blocked"),
    ("cloudflare_error_code", r"Cloudflare Ray ID|Error 10\d\d\b"),
    ("datadome", r"datadome|geo\.captcha-delivery\.com"),
    ("perimeterx", r"perimeterx|px-captcha|Access to this page has been denied"),
    ("hcaptcha", r"hcaptcha|hCaptcha solve|Please verify you are a human"),
    ("recaptcha_wall", r"Please complete the security check|I'm not a robot|Я не робот"),
    ("akamai_kasada", r"Reference #\d+\.\w+|Kasada|Pardon Our Interruption"),
    ("http_403_wall", r"Access Denied|403 Forbidden|You don't have permission to access"),
    ("rate_limited", r"Too Many Requests|429 Too Many|Rate limit exceeded"),
    ("ru_access_restricted", r"Доступ ограничен|Доступ запрещ[её]н|Доступ к ресурсу ограничен"),
    ("ru_suspicious_activity", r"Подозрительная активность|Обнаружена подозрительная|"
                              r"Мы заметили необычн|Подтвердите, что вы не робот"),
    ("ru_captcha", r"Введите символы с картинки|Пройдите проверку|SmartCaptcha"),
    ("ru_blocked_bot", r"Ваш IP заблокирован|Запрос заблокирован|слишком много запросов"),
)

_COMPILED = tuple((name, re.compile(rx, re.IGNORECASE)) for name, rx in BLOCK_PATTERNS)


class BlockedError(RuntimeError):
    """Страница отдала антибот-заслон, а не контент. Явная ошибка вместо пустого результата."""


def is_blocked(page, max_text: int = 20000) -> tuple[bool, str]:
    """(blocked, reason). Вызывать ПОСЛЕ goto — до парсинга результата.

    Проверяет title + начало innerText. Пустое тело (< 40 символов) тоже подозрительно:
    это ровно тот silent failure, где «забанили» неотличимо от «ничего не нашлось».
    """
    try:
        title = page.title() or ""
    except Exception:  # noqa: BLE001
        title = ""
    try:
        body = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
    except Exception:  # noqa: BLE001
        body = ""
    haystack = f"{title}\n{body[:max_text]}"

    for name, rx in _COMPILED:
        m = rx.search(haystack)
        if m:
            return True, f"{name}: {m.group(0)[:80]!r} (title={title[:60]!r})"

    if len(body.strip()) < 40:
        try:
            html_len = page.evaluate("() => document.documentElement.outerHTML.length")
        except Exception:  # noqa: BLE001
            html_len = -1
        return True, f"empty_body: innerText={len(body.strip())} chars, html={html_len} (title={title[:60]!r})"

    return False, ""


def assert_not_blocked(page) -> None:
    """Бросает BlockedError с причиной. Использовать вместо молчаливого пустого результата."""
    blocked, reason = is_blocked(page)
    if blocked:
        raise BlockedError(f"{getattr(page, 'url', '?')} -> {reason}")


# --- CLI-самопроверка -------------------------------------------------------------
def _main(argv):
    url = argv[1] if len(argv) > 1 else "https://example.com"
    try:
        from patchright.sync_api import sync_playwright  # type: ignore
        flavor = "patchright"
    except ImportError:
        from playwright.sync_api import sync_playwright  # type: ignore
        flavor = "playwright"
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(1500)
        blocked, reason = is_blocked(pg)
        raw = aria_snapshot(pg)
        w = window_snapshot(raw)
        print(f"[{flavor}] {url}")
        print(f"blocked={blocked} reason={reason}")
        print(f"raw_chars={w['total']} -> window_chars={len(w['text'])} truncated={w['truncated']} "
              f"next_offset={w['next_offset']} tail_chars={w['tail_chars']}")
        br.close()


if __name__ == "__main__":
    _main(sys.argv)
