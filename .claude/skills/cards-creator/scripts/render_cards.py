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
import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

HTML_FILE = Path(sys.argv[1] if len(sys.argv) > 1 else "series.html").resolve()
OUT = HTML_FILE.parent / "png"
OUT.mkdir(exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1080, "height": 1350},
                                        device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(HTML_FILE.as_uri())
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(900)
        cards = await page.query_selector_all(".card")
        print(f"Found {len(cards)} cards in {HTML_FILE.name}")
        for i, card in enumerate(cards, start=1):
            outfile = OUT / f"series-{i:02d}.png"
            await card.screenshot(path=str(outfile), omit_background=False)
            print(f"  saved {outfile.name}")
        await browser.close()
        print(f"Done -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
