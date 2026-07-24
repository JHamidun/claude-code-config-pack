#!/usr/bin/env python3
"""excalidraw-flowchart · render.py
Render a .excalidraw file to PNG via Playwright (headless) so the agent can SEE
the diagram and iterate. No persistent server — opens excalidraw.com, injects the
scene into localStorage, reloads, screenshots, closes.

Usage:
  python render.py diagram.excalidraw --out diagram.png
  python render.py diagram.excalidraw            # → diagram.png next to input

Requires: playwright (pip install playwright && playwright install chromium).
Note: excalidraw.com is loaded offline-capable; if network-blocked, point --url at a
local excalidraw build. First run may need `playwright install chromium`.
"""
import argparse, json, os, sys


def render(scene_path, out_path, url, wait_ms):
    from playwright.sync_api import sync_playwright  # lazy import for clean error

    with open(scene_path, "r", encoding="utf-8") as fh:
        scene = json.load(fh)
    elements = scene.get("elements", scene if isinstance(scene, list) else [])
    app_state = scene.get("appState", {}) or {}
    app_state.setdefault("viewBackgroundColor", "#ffffff")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000},
                                device_scale_factor=2)
        page.goto(url, wait_until="domcontentloaded")
        # inject scene into the exact localStorage keys excalidraw.com reads on boot
        page.evaluate(
            """([els, st]) => {
                localStorage.setItem('excalidraw', JSON.stringify(els));
                localStorage.setItem('excalidraw-state', JSON.stringify(st));
            }""",
            [elements, app_state],
        )
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(wait_ms)
        # zoom-to-fit so the whole scene is in frame, then screenshot the canvas
        try:
            page.keyboard.press("Shift+1")  # Excalidraw: zoom to fit
            page.wait_for_timeout(400)
        except Exception:
            pass
        canvas = page.query_selector("canvas") or page
        canvas.screenshot(path=out_path)
        browser.close()
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--out", default=None)
    ap.add_argument("--url", default="https://excalidraw.com")
    ap.add_argument("--wait", type=int, default=1500, help="ms to wait for render")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.scene)[0] + ".png"
    try:
        render(a.scene, out, a.url, a.wait)
    except ImportError:
        sys.stderr.write("playwright not installed — run: pip install playwright && playwright install chromium\n")
        sys.exit(2)
    sys.stderr.write(f"rendered {out}\n")


if __name__ == "__main__":
    main()
