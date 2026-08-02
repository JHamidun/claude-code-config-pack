#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live-браузер daemon: headed Chromium с CDP-портом, живёт в фоне.
Каждая сессия Claude Code поднимает СВОЙ порт -> сколько угодно параллельных
браузеров, не конфликтует с MCP playwright-плагином (тот singleton).

Запуск (в фоне):
  python browser_daemon.py --port 9456 --profile live-a --url https://example.com

Управление — через bdo.py (connect_over_cdp по тому же порту).
Остановить: `python bdo.py --port 9456 quit`, стоп-файл `state/STOP_<port>` или убить процесс.

РЕСУРС-ГАРД (конвенция ваше локальное хранилище памяти):
  - ручной запуск, НЕ крон;
  - BELOW_NORMAL приоритет процесса (psutil, если стоит);
  - лестница простоя: лишние вкладки -> 5 мин, браузер -> 5 мин (daemon засыпает, замер: ~62 МБ вместо ~260 МБ с браузером),
    сессия -> 10 мин без активности (процесс выходит, reason=session_idle);
  - рестарт браузера при RSS > 1500 МБ (утечки в долгих сессиях);
  - стоп-файл `state/STOP_<port>` = чистое завершение;
  - состояние в `state/session-<port>.json`: status + reason, намеренная остановка
    отличается от падения (`python bdo.py --port N health` -> 200/503).
Активность пишет bdo.py (`state/activity-<port>`), daemon её только читает — нет гонок.
"""
import argparse, json, os, pathlib, sys, time, traceback

sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent / "profiles"
BASE.mkdir(exist_ok=True)
STATE = pathlib.Path(__file__).resolve().parent.parent / "state"
STATE.mkdir(exist_ok=True)

# --- пороги (совпадают с лестницей camofox-подхода) ---
TAB_IDLE_SEC = 300        # лишние вкладки закрываются через 5 мин простоя
BROWSER_IDLE_SEC = 300    # браузер закрывается через 5 мин простоя (daemon остаётся жить)
SESSION_IDLE_SEC = 600    # 10 мин без активности -> daemon выходит
MAX_RSS_MB = 1500         # рестарт браузера при превышении
POLL_SEC = 5


def state_path(port): return STATE / f"session-{port}.json"
def activity_path(port): return STATE / f"activity-{port}"
def stop_path(port): return STATE / f"STOP_{port}"


def read_activity(port, default):
    try:
        return float(activity_path(port).read_text().strip())
    except Exception:
        return default


def write_state(port, **kw):
    data = {"port": port, "updated": time.time(), "pid": os.getpid()}
    data.update(kw)
    try:
        state_path(port).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def browser_rss_mb():
    """RSS всего дерева процессов браузера (дочерние процессы daemon'а)."""
    try:
        import psutil
    except ImportError:
        return -1.0
    try:
        me = psutil.Process()
        total = sum(c.memory_info().rss for c in me.children(recursive=True))
        return round(total / 1048576, 1)
    except Exception:
        return -1.0


def set_low_priority():
    try:
        import psutil
        p = psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
        try:
            p.ionice(psutil.IOPRIO_LOW if os.name == "nt" else psutil.IOPRIO_CLASS_IDLE)
        except Exception:
            pass
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9456, help="CDP remote-debugging порт (уникальный на сессию)")
    ap.add_argument("--profile", default="live", help="имя persistent-профиля (логины сохраняются)")
    ap.add_argument("--url", default="about:blank", help="стартовый URL")
    ap.add_argument("--headless", action="store_true", help="без окна (RuTube палит — НЕ использовать для него)")
    ap.add_argument("--channel", default=None, help="channel браузера, напр. chrome (реальный Chrome вместо Chromium)")
    ap.add_argument("--proxy", default=None, help="прокси для браузера, напр. socks5://127.0.0.1:1085 (гео-мост, канал агента не трогает)")
    ap.add_argument("--idle-timeout", type=int, default=BROWSER_IDLE_SEC, help="сек простоя до закрытия браузера (0 = никогда)")
    ap.add_argument("--session-timeout", type=int, default=SESSION_IDLE_SEC, help="сек простоя до выхода daemon (0 = никогда)")
    ap.add_argument("--tab-idle", type=int, default=TAB_IDLE_SEC, help="сек простоя до закрытия лишних вкладок (0 = никогда)")
    ap.add_argument("--max-rss-mb", type=int, default=MAX_RSS_MB, help="рестарт браузера при RSS выше, МБ (0 = никогда)")
    a = ap.parse_args()

    profile_dir = BASE / a.profile
    profile_dir.mkdir(exist_ok=True)
    args = [f"--remote-debugging-port={a.port}", "--disable-blink-features=AutomationControlled",
            "--no-first-run", "--no-default-browser-check"]
    kwargs = dict(user_data_dir=str(profile_dir), headless=a.headless, args=args,
                  viewport={"width": 1440, "height": 900})
    if a.channel:
        kwargs["channel"] = a.channel
    if a.proxy:
        kwargs["proxy"] = {"server": a.proxy}

    low = set_low_priority()
    stop_path(a.port).unlink(missing_ok=True)
    restarts = 0

    with sync_playwright() as p:
        ctx = None

        def launch(reason):
            nonlocal ctx
            ctx = p.chromium.launch_persistent_context(**kwargs)
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            try:
                pg.goto(a.url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e:
                print(f"[daemon] стартовый goto не удался: {e}", flush=True)
            print(f"[daemon] browser UP ({reason}) port={a.port} profile={a.profile} pages={len(ctx.pages)}", flush=True)

        def shutdown_browser(reason):
            nonlocal ctx
            if ctx is not None:
                try:
                    ctx.close()
                except Exception:
                    pass
                ctx = None
            print(f"[daemon] browser DOWN ({reason})", flush=True)

        launch("startup")
        # отсчёт простоя стартует ПОСЛЕ запуска браузера (холодный старт профиля бывает долгим)
        activity_path(a.port).write_text(str(time.time()), encoding="utf-8")
        print(f"[daemon] LIVE on CDP port {a.port} | low_priority={low} | "
              f"idle={a.idle_timeout}s session={a.session_timeout}s max_rss={a.max_rss_mb}MB", flush=True)
        print(f"[daemon] управляй: python bdo.py --port {a.port} <cmd>", flush=True)
        write_state(a.port, status="ok", reason="startup", profile=a.profile, browser_up=True,
                    last_activity=time.time(), rss_mb=browser_rss_mb(), restarts=0)

        status, reason = "ok", "running"
        try:
            while True:
                time.sleep(POLL_SEC)
                now = time.time()
                last = read_activity(a.port, now)
                idle = now - last

                if stop_path(a.port).exists():
                    status, reason = "stopped", "stop_file"
                    break

                if ctx is None:
                    # спим: просыпаемся, если пришла свежая активность (bdo дёрнул команду)
                    if idle < a.idle_timeout:
                        restarts += 1
                        launch("wake_on_activity")
                        write_state(a.port, status="ok", reason="wake_on_activity", profile=a.profile,
                                    browser_up=True, last_activity=last, rss_mb=browser_rss_mb(), restarts=restarts)
                        continue
                    if a.session_timeout and idle > a.session_timeout:
                        status, reason = "stopped", "session_idle"
                        break
                    write_state(a.port, status="sleeping", reason="idle_timeout", profile=a.profile,
                                browser_up=False, last_activity=last, rss_mb=browser_rss_mb(), restarts=restarts)
                    continue

                # браузер жив
                rss = browser_rss_mb()
                if a.max_rss_mb and rss > a.max_rss_mb:
                    shutdown_browser(f"rss {rss}MB > {a.max_rss_mb}MB")
                    restarts += 1
                    launch("rss_restart")
                    write_state(a.port, status="ok", reason="rss_restart", profile=a.profile, browser_up=True,
                                last_activity=last, rss_mb=browser_rss_mb(), restarts=restarts)
                    continue

                if a.tab_idle and idle > a.tab_idle and ctx is not None and len(ctx.pages) > 1:
                    for extra in ctx.pages[:-1]:
                        try:
                            extra.close()
                        except Exception:
                            pass
                    print(f"[daemon] закрыты лишние вкладки (простой {int(idle)}с)", flush=True)

                if a.idle_timeout and idle > a.idle_timeout:
                    shutdown_browser(f"idle {int(idle)}s")
                    write_state(a.port, status="sleeping", reason="idle_timeout", profile=a.profile,
                                browser_up=False, last_activity=last, rss_mb=browser_rss_mb(), restarts=restarts)
                    continue

                write_state(a.port, status="ok", reason="running", profile=a.profile, browser_up=True,
                            last_activity=last, idle_sec=round(idle), rss_mb=rss, restarts=restarts)
        except KeyboardInterrupt:
            status, reason = "stopped", "keyboard_interrupt"
        except Exception as e:
            status, reason = "crashed", f"{type(e).__name__}: {str(e)[:160]}"
            traceback.print_exc()
        finally:
            shutdown_browser(reason)
            write_state(a.port, status=status, reason=reason, profile=a.profile, browser_up=False,
                        last_activity=read_activity(a.port, time.time()), rss_mb=0, restarts=restarts)
            stop_path(a.port).unlink(missing_ok=True)
            print(f"[daemon] EXIT status={status} reason={reason}", flush=True)


if __name__ == "__main__":
    main()
