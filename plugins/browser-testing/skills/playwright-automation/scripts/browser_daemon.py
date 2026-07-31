#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live-браузер daemon: headed Chromium с CDP-портом, живёт в фоне.
Каждая сессия Claude Code поднимает СВОЙ порт -> сколько угодно параллельных
браузеров, не конфликтует с MCP playwright-плагином (тот singleton).

Запуск (в фоне):
  python browser_daemon.py --port 9456 --profile live-a --url https://example.com

Управление — через bdo.py (connect_over_cdp по тому же порту).
Остановить: убить процесс или `python bdo.py --port 9456 quit`.
"""
import argparse, pathlib, sys, time, signal
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent / "profiles"
BASE.mkdir(exist_ok=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9456, help="CDP remote-debugging порт (уникальный на сессию)")
    ap.add_argument("--profile", default="live", help="имя persistent-профиля (логины сохраняются)")
    ap.add_argument("--url", default="about:blank", help="стартовый URL")
    ap.add_argument("--headless", action="store_true", help="без окна (RuTube палит — НЕ использовать для него)")
    ap.add_argument("--channel", default=None, help="channel браузера, напр. chrome (реальный Chrome вместо Chromium)")
    a = ap.parse_args()

    profile_dir = BASE / a.profile
    profile_dir.mkdir(exist_ok=True)
    args = [f"--remote-debugging-port={a.port}", "--disable-blink-features=AutomationControlled",
            "--no-first-run", "--no-default-browser-check"]
    with sync_playwright() as p:
        kwargs = dict(
            user_data_dir=str(profile_dir),
            headless=a.headless,
            args=args,
            viewport={"width": 1440, "height": 900},
        )
        if a.channel:
            kwargs["channel"] = a.channel
        ctx = p.chromium.launch_persistent_context(**kwargs)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(a.url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"[daemon] стартовый goto не удался: {e}", flush=True)
        print(f"[daemon] LIVE on CDP port {a.port} | profile={a.profile} | pages={len(ctx.pages)}", flush=True)
        print(f"[daemon] управляй: python bdo.py --port {a.port} <cmd>", flush=True)
        # держим браузер живым
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
        finally:
            ctx.close()

if __name__ == "__main__":
    main()
