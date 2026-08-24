#!/usr/bin/env python3
"""Render carousel cards from an HTML deck into 1080x1350 retina PNGs.

Each `.card` element in the HTML is screenshotted separately, in document order,
to ./png/series-NN.png (NN = 01, 02, ...). Works with the reference-channel-style decks
built from cards-creator/handoff/cards/styles.css.

Usage:
    pip install playwright && playwright install chromium   # once
    python render_cards.py [deck.html]                      # default: series.html
    # output -> <deck dir>/png/series-NN.png

Notes:
- device_scale_factor=2 -> crisp on retina; each PNG ~1-2 MB (Telegram-friendly).
- 900 ms settle wait lets Google webfonts load before screenshotting.
- Album max = 10 cards. Keep the deck <= 10 `.card` blocks.
"""
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

import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# Аргументы и каталог вывода разбираются в main(), а не при импорте: раньше
# `import render_cards` читал sys.argv чужого процесса и создавал каталог ./png.
async def render(html_file: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1080, "height": 1350},
                                        device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(html_file.as_uri())
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(900)
        cards = await page.query_selector_all(".card")
        print(f"Found {len(cards)} cards in {html_file.name}")
        if not cards:
            # Тихий провал: браузер отработал, кадров ноль, PNG не появились.
            # Отказ должен быть слышен, иначе человек увидит «Done» и пустую папку.
            await browser.close()
            print(f"ОТКАЗ: в {html_file} нет ни одного блока `.card` — рендерить нечего.")
            return 1
        for i, card in enumerate(cards, start=1):
            outfile = out_dir / f"series-{i:02d}.png"
            await card.screenshot(path=str(outfile), omit_background=False)
            print(f"  saved {outfile.name}")
        await browser.close()
        print(f"Done -> {out_dir}")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    html_file = Path(argv[0] if argv else "series.html").resolve()
    if not html_file.is_file():
        print(f"ОТКАЗ: нет файла {html_file}\n  Usage: python render_cards.py [deck.html]")
        return 2
    return asyncio.run(render(html_file, html_file.parent / "png"))


if __name__ == "__main__":
    raise SystemExit(main())
