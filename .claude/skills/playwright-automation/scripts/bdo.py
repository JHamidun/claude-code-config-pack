#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bdo — browser do. Управление live-браузером (browser_daemon.py) через CDP.
Stateless: подключается к запущенному daemon по порту, делает одно действие, отключается
(браузер остаётся жить). Параллелится — у каждой сессии свой --port.

Команды:
  goto <url>                     — перейти
  click <selector>               — клик (text=.. | css | role=.. | "Текст кнопки")
  fill <selector> <value>        — заполнить поле
  type <selector> <text>         — печатать по символу (триггерит JS)
  press <key>                    — нажать клавишу (Enter, Escape, ...)
  snap                           — список кликабельных элементов (что можно нажать)
  text [selector]                — innerText страницы/элемента
  shot [file]                    — скриншот (default: live_shot.png в CWD)
  eval <js>                      — выполнить JS, вернуть результат
  scroll <px>                    — прокрутить (px, можно отрицательное)
  url                            — текущий URL + title
  tabs                           — список вкладок
  newtab <url>                   — новая вкладка
  wait <selector|ms>             — ждать селектор или мс
  upload <selector> <file>       — загрузить файл в input
  quit                           — закрыть браузер (daemon завершится)

Все команды: python bdo.py --port 9456 <cmd> [args]
"""
import argparse, sys, json, pathlib
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

def active_page(browser):
    # последняя страница последнего контекста = активная вкладка
    ctxs = browser.contexts
    if not ctxs:
        raise RuntimeError("нет контекстов в браузере")
    pages = ctxs[0].pages
    return pages[-1] if pages else ctxs[0].new_page()

SNAP_JS = """() => {
  const out = [];
  const sel = 'a,button,input,select,textarea,[role=button],[role=link],[role=tab],[role=menuitem],[onclick],[contenteditable=true]';
  const els = [...document.querySelectorAll(sel)];
  let i = 0;
  for (const el of els) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') continue;
    const txt = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().slice(0, 60);
    let s = '';
    if (el.id) s = '#' + CSS.escape(el.id);
    else if (el.getAttribute('aria-label')) s = `[aria-label="${el.getAttribute('aria-label')}"]`;
    else if (el.getAttribute('data-test')) s = `[data-test="${el.getAttribute('data-test')}"]`;
    else if (txt) s = `text=${txt}`;
    out.push({ i: i++, tag: el.tagName.toLowerCase(), type: el.type || '', text: txt, selector: s });
    if (i > 80) break;
  }
  return out;
}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9456)
    ap.add_argument("cmd")
    ap.add_argument("rest", nargs="*")
    a = ap.parse_args()
    r = a.rest

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{a.port}")
        except Exception as e:
            print(f"ERR: не подключиться к браузеру на порту {a.port}. Запущен ли daemon? ({str(e)[:80]})")
            sys.exit(1)
        pg = active_page(browser)

        try:
            if a.cmd == "goto":
                pg.goto(r[0], wait_until="domcontentloaded", timeout=30000)
                print(f"OK goto {pg.url}")
            elif a.cmd == "click":
                pg.click(r[0], timeout=15000)
                print(f"OK click {r[0]} -> {pg.url}")
            elif a.cmd == "fill":
                pg.fill(r[0], r[1], timeout=15000)
                print(f"OK fill {r[0]}")
            elif a.cmd == "type":
                pg.type(r[0], r[1], delay=30, timeout=15000)
                print(f"OK type {r[0]}")
            elif a.cmd == "press":
                pg.keyboard.press(r[0])
                print(f"OK press {r[0]}")
            elif a.cmd == "snap":
                els = pg.evaluate(SNAP_JS)
                print(json.dumps(els, ensure_ascii=False, indent=1))
            elif a.cmd == "text":
                if r:
                    print(pg.locator(r[0]).inner_text()[:4000])
                else:
                    print(pg.evaluate("() => document.body.innerText")[:4000])
            elif a.cmd == "shot":
                fp = r[0] if r else "live_shot.png"
                pg.screenshot(path=fp, full_page=("--full" in r))
                print(f"OK shot {pathlib.Path(fp).resolve()}")
            elif a.cmd == "eval":
                res = pg.evaluate(r[0] if r[0].strip().startswith("(") else f"() => ({r[0]})")
                print(json.dumps(res, ensure_ascii=False)[:4000] if not isinstance(res, str) else res[:4000])
            elif a.cmd == "scroll":
                px = int(r[0]) if r else 600
                pg.evaluate(f"() => window.scrollBy(0, {px})")
                print(f"OK scroll {px}")
            elif a.cmd == "url":
                print(json.dumps({"url": pg.url, "title": pg.title()}, ensure_ascii=False))
            elif a.cmd == "tabs":
                print(json.dumps([{"i": i, "url": x.url, "title": x.title()} for i, x in enumerate(browser.contexts[0].pages)], ensure_ascii=False, indent=1))
            elif a.cmd == "newtab":
                np = browser.contexts[0].new_page()
                np.goto(r[0], wait_until="domcontentloaded", timeout=30000)
                print(f"OK newtab {np.url}")
            elif a.cmd == "wait":
                arg = r[0]
                if arg.isdigit():
                    pg.wait_for_timeout(int(arg))
                else:
                    pg.wait_for_selector(arg, timeout=20000)
                print(f"OK wait {arg}")
            elif a.cmd == "upload":
                pg.set_input_files(r[0], r[1])
                print(f"OK upload {r[1]} -> {r[0]}")
            elif a.cmd == "quit":
                browser.contexts[0].close()
                print("OK quit (браузер закрыт)")
            else:
                print(f"ERR неизвестная команда: {a.cmd}")
                sys.exit(2)
        except Exception as e:
            print(f"ERR {a.cmd}: {str(e)[:200]}")
            sys.exit(1)

if __name__ == "__main__":
    main()
