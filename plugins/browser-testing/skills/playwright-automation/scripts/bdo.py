#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bdo — browser do. Управление live-браузером (browser_daemon.py) через CDP.
Stateless: подключается к запущенному daemon по порту, делает одно действие, отключается
(браузер остаётся жить). Параллелится — у каждой сессии свой --port.

Команды:
  goto <url>                     — перейти (+ авто-проверка на антибот-заслон)
  click <selector>               — клик (text=.. | css | role=.. | "Текст кнопки")
  fill <selector> <value>        — заполнить поле
  type <selector> <text>         — печатать по символу (триггерит JS)
  press <key>                    — нажать клавишу (Enter, Escape, ...)
  snap                           — список кликабельных элементов (что можно нажать)
  aria [offset]                  — aria-снапшот окном 80K + хвост 5K (пагинация не теряется)
  blocked                        — проверить страницу на антибот-заслон (exit 3 если забанен)
  text [selector]                — innerText страницы/элемента (окном + хвост)
  shot [file]                    — скриншот (default: live_shot.png в CWD)
  eval <js>                      — выполнить JS, вернуть результат
  scroll <px>                    — прокрутить (px, можно отрицательное)
  url                            — текущий URL + title
  tabs                           — список вкладок
  newtab <url>                   — новая вкладка
  wait <selector|ms>             — ждать селектор или мс
  upload <selector> <file>       — загрузить файл в input
  health                         — состояние daemon; exit 0 = живой (ok/sleeping),
                                   2 = штатно остановлен (intentional=true),
                                   1 = упал / убит жёстко (status=dead при протухшем state)
  quit                           — закрыть браузер (daemon завершится)

Все команды: python bdo.py --port 9456 <cmd> [args]
Окно снапшота: --offset N --max-chars N --tail-chars N (дефолт 0 / 80000 / 5000).
Заслон антибота: goto/blocked дают exit 3 и явную причину; --allow-blocked = только warning.
"""
import argparse, sys, json, pathlib, time
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pw_guard import window_snapshot, is_blocked  # noqa: E402

STATE = pathlib.Path(__file__).resolve().parent.parent / "state"
WAKE_WAIT_SEC = 25  # daemon поднимает уснувший браузер за один цикл (~5 с)

# health: daemon пишет состояние каждые POLL_SEC=5 с. Если запись протухла —
# процесс убит жёстко (kill -9, сон машины, BSOD) и не успел записать финальный
# статус. Без этой проверки health вечно рапортует последний «ok» о мёртвом daemon.
STATE_STALE_SEC = 30
# Намеренная остановка (не инцидент) против падения (инцидент).
INTENTIONAL_REASONS = ("stop_file", "session_idle", "keyboard_interrupt", "bdo quit")


def touch_activity(port):
    """Отметить активность — daemon по ней держит браузер живым / будит уснувший."""
    try:
        STATE.mkdir(exist_ok=True)
        (STATE / f"activity-{port}").write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass


def pid_alive(pid):
    """True/False/None (не смогли проверить — psutil не стоит)."""
    if not pid:
        return None
    try:
        import psutil
        return psutil.pid_exists(int(pid))
    except Exception:
        return None


def read_state(port):
    try:
        return json.loads((STATE / f"session-{port}.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def connect(p, port):
    """Подключиться к daemon; если браузер спит по idle-таймауту — подождать пробуждения."""
    deadline = time.time() + WAKE_WAIT_SEC
    last_err = ""
    while True:
        try:
            return p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        except Exception as e:
            last_err = str(e)[:80]
            st = read_state(port)
            if st.get("status") in ("sleeping",) and time.time() < deadline:
                time.sleep(2)
                continue
            st_txt = f" [daemon status={st.get('status')} reason={st.get('reason')}]" if st else ""
            print(f"ERR: не подключиться к браузеру на порту {port}. Запущен ли daemon?{st_txt} ({last_err})")
            sys.exit(1)


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


def report_block(pg, allow):
    """Явная ошибка вместо пустого результата (silent failure)."""
    blocked, reason = is_blocked(pg)
    if blocked:
        print(f"{'WARN' if allow else 'ERR'} blocked: {reason}")
        if not allow:
            sys.exit(3)
    return blocked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9456)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--max-chars", type=int, default=80000)
    ap.add_argument("--tail-chars", type=int, default=5000)
    ap.add_argument("--allow-blocked", action="store_true", help="антибот-заслон = warning, не ошибка")
    ap.add_argument("cmd")
    ap.add_argument("rest", nargs="*")
    a = ap.parse_args()
    r = a.rest

    if a.cmd == "health":
        st = read_state(a.port)
        if not st:
            print(json.dumps({"code": 503, "status": "unknown", "reason": "no state file",
                              "intentional": False, "port": a.port}, ensure_ascii=False))
            sys.exit(1)

        status = st.get("status")
        reason = str(st.get("reason") or "")
        stale = round(time.time() - float(st.get("updated") or 0), 1)
        st["stale_sec"] = stale
        st["pid_alive"] = pid_alive(st.get("pid"))

        if status in ("ok", "sleeping"):
            # Живым считаем только того, кто СЕЙЧАС пишет состояние.
            if stale > STATE_STALE_SEC or st["pid_alive"] is False:
                st.update(status="dead", code=503, intentional=False,
                          reason=f"state stale {stale}s (was {status!r}/{reason!r}); "
                                 f"daemon killed without clean shutdown")
                print(json.dumps(st, ensure_ascii=False))
                sys.exit(1)
            st.update(code=200, intentional=False)
            print(json.dumps(st, ensure_ascii=False))
            sys.exit(0)

        # Не работает. Различаем «мы сами остановили» и «упало».
        intentional = status == "stopped" and any(x in reason for x in INTENTIONAL_REASONS)
        st.update(code=503, intentional=intentional)
        print(json.dumps(st, ensure_ascii=False))
        # 0/non-zero контракт прежний; 2 отделяет штатный стоп от инцидента.
        sys.exit(2 if intentional else 1)

    touch_activity(a.port)

    with sync_playwright() as p:
        browser = connect(p, a.port)
        pg = active_page(browser)

        try:
            if a.cmd == "goto":
                pg.goto(r[0], wait_until="domcontentloaded", timeout=30000)
                print(f"OK goto {pg.url}")
                report_block(pg, a.allow_blocked)
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
            elif a.cmd == "aria":
                off = int(r[0]) if r and r[0].lstrip("-").isdigit() else a.offset
                w = window_snapshot(pg, offset=off, max_chars=a.max_chars, tail_chars=a.tail_chars)
                print(f"[aria] total={w['total']} chars, window={w['offset']}..{w['offset'] + w['window_chars']}"
                      f"{', next_offset=' + str(w['next_offset']) if w['truncated'] else ' (полный)'}")
                print(w["text"])
            elif a.cmd == "blocked":
                blocked, reason = is_blocked(pg)
                print(json.dumps({"url": pg.url, "blocked": blocked, "reason": reason}, ensure_ascii=False))
                if blocked and not a.allow_blocked:
                    sys.exit(3)
            elif a.cmd == "text":
                raw = pg.locator(r[0]).inner_text() if r else pg.evaluate("() => document.body.innerText")
                w = window_snapshot(raw, offset=a.offset,
                                    max_chars=a.max_chars if a.max_chars != 80000 else 4000,
                                    tail_chars=a.tail_chars if a.tail_chars != 5000 else 500)
                print(w["text"])
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
                report_block(np, a.allow_blocked)
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
                (STATE / f"STOP_{a.port}").write_text("bdo quit", encoding="utf-8")
                browser.contexts[0].close()
                print("OK quit (браузер закрыт, daemon завершится: reason=stop_file)")
            else:
                print(f"ERR неизвестная команда: {a.cmd}")
                sys.exit(2)
        except SystemExit:
            raise
        except Exception as e:
            print(f"ERR {a.cmd}: {str(e)[:200]}")
            sys.exit(1)


if __name__ == "__main__":
    main()
