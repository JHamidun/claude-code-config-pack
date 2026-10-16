# -*- coding: utf-8 -*-
"""
SVG -> PNG через headless Chrome/Edge (на этой машине это самый надёжный
рендерер SVG с кириллицей и системными шрифтами; cairosvg на Windows требует
нативный cairo, resvg не установлен).

Приём: SVG инлайнится в HTML-обёртку с точным пиксельным размером,
скриншот делается с --window-size = размеру листа в пикселях при нужном DPI.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SHEET_W_MM, SHEET_H_MM = 420, 297

BROWSERS = [
    os.environ.get("CHROMIUM_PATH", ""),
    # Linux (сервер, apt chromium)
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    # Windows (локальная разработка)
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


def svg_to_png(svg_path, png_path, dpi=200):
    # png_path обязан быть абсолютным: chrome --screenshot пишет относительный
    # путь относительно СВОЕГО cwd, а не нашего
    svg_path, png_path = Path(svg_path).resolve(), Path(png_path).resolve()
    w_px = round(SHEET_W_MM / 25.4 * dpi)      # 420 мм @200dpi = 3307
    h_px = round(SHEET_H_MM / 25.4 * dpi)      # 297 мм @200dpi = 2339

    svg = svg_path.read_text(encoding="utf-8")
    # переопределяем габариты корневого <svg> на пиксели
    svg = re.sub(r'width="[^"]+" height="[^"]+"',
                 f'width="{w_px}" height="{h_px}"', svg, count=1)
    html = (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<style>html,body{{margin:0;padding:0;background:#fff}}</style>'
            f'</head><body>{svg}</body></html>')

    browser = next((b for b in BROWSERS if b and Path(b).exists()), None) \
        or shutil.which("chromium") or shutil.which("chromium-browser")
    if browser is None:
        raise RuntimeError("Не найден Chrome/Edge/Chromium для рендера PNG")

    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "sheet.html"
        page.write_text(html, encoding="utf-8")
        cmd = [
            browser, "--headless=new", "--disable-gpu",
            "--force-device-scale-factor=1", "--hide-scrollbars",
            "--default-background-color=FFFFFFFF",
            f"--window-size={w_px},{h_px}",
            f"--screenshot={png_path}",
            page.as_uri(),
        ]
        if os.name != "nt":  # контейнер: chromium без user namespaces
            cmd[1:1] = ["--no-sandbox", "--disable-dev-shm-usage"]
        res = subprocess.run(cmd, capture_output=True, timeout=120)
        if not png_path.exists():
            raise RuntimeError(
                f"Скриншот не создан: {res.stderr.decode(errors='replace')[:500]}")
    return png_path
