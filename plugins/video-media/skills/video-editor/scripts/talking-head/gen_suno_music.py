#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Suno music via real-Chrome Playwright (captcha-safe) + headless CDN download.

Profile already logs in via injected __client cookie (confirmed: create UI renders).
Simple mode: fill Song Description, toggle Instrumental, click Create.
Then poll feed headless and download cdn1.suno.ai/{id}.mp3.
"""
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
sys.path.insert(0, str(Path.home() / ".claude/skills/suno/scripts"))
from suno_client import SunoClient  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
DBG = BASE / "audio" / "suno_debug"
DBG.mkdir(exist_ok=True)
PROFILE = Path(r"${HOME}\.claude\skills\playwright-automation\profiles\suno_real")

DESC = ("Energetic upbeat modern promo background, punchy tight drums, deep sub-bass pulse, "
        "bright plucky synth hook, confident forward momentum, percussive groove, 124 BPM, "
        "clean polished production, motivational, instrumental")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def clips_list(sc, limit=20):
    data = sc.list_clips(limit=limit)
    return data.get("clips") or data.get("items") or data.get("data") or []


def shot(page, name):
    try:
        page.screenshot(path=str(DBG / name), timeout=8000, animations="disabled")
    except Exception:
        pass


def main():
    sc = SunoClient()
    before_ids = {c["id"] for c in clips_list(sc)}
    log(f"clips before: {len(before_ids)}")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            channel="chrome",
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx.add_cookies([
            {"name": "__client", "value": os.environ["SUNO_CLIENT_COOKIE"],
             "domain": "auth.suno.com", "path": "/", "httpOnly": True, "secure": True, "sameSite": "None"},
        ])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(20000)
        page.goto("https://suno.com/create", wait_until="commit", timeout=60000)

        # Wait for create UI by text, not screenshot
        try:
            page.get_by_text("Song Description").first.wait_for(timeout=60000)
            log("create UI rendered")
        except Exception:
            log(f"create UI NOT rendered; url={page.url}")
            shot(page, "01_fail.png")
            ctx.close()
            sys.exit(4)
        shot(page, "01_loaded.png")

        # Fill description (Simple mode default). Find the description textarea.
        filled = False
        tas = page.locator("textarea")
        n = tas.count()
        log(f"{n} textareas")
        for i in range(n):
            el = tas.nth(i)
            try:
                ph = (el.get_attribute("placeholder") or "").lower()
            except Exception:
                ph = ""
            if "lyric" in ph:
                continue
            try:
                el.click(timeout=5000)
                el.fill(DESC, timeout=8000)
                filled = True
                log(f"filled textarea[{i}] ph={ph!r}")
                break
            except Exception as e:
                log(f"fill textarea[{i}] failed: {str(e)[:80]}")
        if not filled:
            shot(page, "02_nofill.png")
            ctx.close()
            sys.exit(2)
        shot(page, "02_filled.png")

        # Instrumental toggle — find switch labelled Instrumental
        try:
            inst = page.get_by_text("Instrumental", exact=True).first
            box = inst.bounding_box()
            # the toggle switch is usually right next to the label
            sw = page.locator('button[role="switch"], [role="switch"]')
            done = False
            for i in range(sw.count()):
                el = sw.nth(i)
                bb = el.bounding_box()
                if bb and box and abs(bb["y"] - box["y"]) < 40:
                    state = el.get_attribute("aria-checked") or el.get_attribute("data-state") or ""
                    if state in ("false", "unchecked", ""):
                        el.click()
                        log(f"instrumental ON (was {state!r})")
                    else:
                        log(f"instrumental already {state!r}")
                    done = True
                    break
            if not done:
                inst.click()
                log("clicked Instrumental label directly")
        except Exception as e:
            log(f"instrumental toggle issue: {str(e)[:100]} (DESC says instrumental)")
        shot(page, "03_toggled.png")

        # Create
        clicked = False
        for sel in ['button[aria-label="Create song"]', 'button:has-text("Create")']:
            loc = page.locator(sel)
            for i in range(loc.count()):
                btn = loc.nth(i)
                try:
                    if btn.is_visible() and btn.is_enabled():
                        btn.click(timeout=8000)
                        clicked = True
                        log(f"clicked create via {sel}[{i}]")
                        break
                except Exception as e:
                    log(f"create click {sel}[{i}]: {str(e)[:60]}")
            if clicked:
                break
        if not clicked:
            shot(page, "04_nobtn.png")
            ctx.close()
            sys.exit(3)

        page.wait_for_timeout(20000)
        shot(page, "05_after_create.png")
        ctx.close()

    # Headless poll
    log("polling for new clips...")
    new_ids = []
    for _ in range(40):
        time.sleep(15)
        new = [c for c in clips_list(sc) if c["id"] not in before_ids]
        if new:
            new_ids = [c["id"] for c in new]
            log(f"new: {{ {', '.join(c['id'][:8] + ':' + str(c.get('status')) for c in new)} }}")
            if all(c.get("status") == "complete" for c in new):
                break
            if any(c.get("status") == "error" for c in new):
                log("clip errored")
                break
    done = 0
    for cid in new_ids:
        out = BASE / "audio" / f"suno_{cid[:8]}.mp3"
        try:
            sc.download(cid, str(out))
            log(f"downloaded {out.name} ({out.stat().st_size//1024}KB)")
            done += 1
        except Exception as e:
            log(f"download fail {cid}: {str(e)[:80]}")
    log(f"SUNO DONE: {done} tracks")


if __name__ == "__main__":
    main()
