# -*- coding: utf-8 -*-
"""SVG → PNG через headless Chrome/Edge/Chromium (надёжная кириллица и локальные шрифты).
Формат читается из атрибутов width/height SVG (мм) — листы разных форматов рендерятся правильно."""

import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

BROWSERS = [
    os.environ.get("CHROMIUM_PATH", ""),
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def _find_browser():
    for b in BROWSERS:
        if b and Path(b).exists():
            return b
    for name in ("chrome", "chromium", "chromium-browser", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    import glob
    for pat in (os.path.expanduser(r"~\AppData\Local\ms-playwright\chromium-*\chrome-win64\chrome.exe"),
                os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome")):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return None


def svg_size_mm(svg):
    m = re.search(r'width="([\d.]+)mm"\s+height="([\d.]+)mm"', svg)
    if not m:
        raise ValueError("SVG без width/height в мм")
    return float(m.group(1)), float(m.group(2))


def svg_to_png(svg_path, png_path, dpi=150):
    svg_path, png_path = Path(svg_path).resolve(), Path(png_path).resolve()
    svg = svg_path.read_text(encoding="utf-8")
    w_mm, h_mm = svg_size_mm(svg)
    w_px, h_px = round(w_mm / 25.4 * dpi), round(h_mm / 25.4 * dpi)
    svg = re.sub(r'width="[^"]+" height="[^"]+"', f'width="{w_px}" height="{h_px}"', svg, count=1)
    html = (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<style>html,body{{margin:0;padding:0;background:#fff}}</style></head><body>{svg}</body></html>')
    browser = _find_browser()
    if browser is None:
        raise RuntimeError("Не найден Chrome/Edge/Chromium для рендера PNG")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "sheet.html"
        profile = Path(td) / "chrome-profile"
        page.write_text(html, encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--force-device-scale-factor=1",
               "--hide-scrollbars", "--default-background-color=FFFFFFFF", "--allow-file-access-from-files",
               f"--user-data-dir={profile}", f"--window-size={w_px},{h_px}",
               f"--screenshot={png_path}", page.as_uri()]
        if os.name != "nt":
            cmd[1:1] = ["--no-sandbox", "--disable-dev-shm-usage"]
        res = subprocess.run(cmd, capture_output=True, timeout=180)
        stderr = res.stderr.decode(errors="replace")[:400]
        if res.returncode != 0:
            png_path.unlink(missing_ok=True)
            raise RuntimeError(f"Chromium завершился с кодом {res.returncode}: {stderr}")
        if not png_path.exists():
            raise RuntimeError("Скриншот не создан: " + stderr)
        head = png_path.read_bytes()[:24]
        ok = head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR"
        wh = struct.unpack(">II", head[16:24]) if ok else (0, 0)
        if png_path.stat().st_size < 1024 or not ok or wh != (w_px, h_px):
            png_path.unlink(missing_ok=True)
            raise RuntimeError(f"Некорректный PNG: dimensions={wh}, expected={(w_px, h_px)}")
    return png_path
