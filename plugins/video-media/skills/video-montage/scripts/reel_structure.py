#!/usr/bin/env python3
"""План короткого видео: из сообщения — сетка блоков с таймингом.

На чём построено. Не на AIDA: та описывает убеждение покупателя (печатная реклама,
1898) и оптимизирует намерение купить — величину, которую лента не измеряет. Все три
площадки официально называют главным классом сигналов «зритель остался и досмотрел»:
TikTok — досмотр как «greater weight» (2020), Instagram — «watch all the way through»
и пересылки (2021, 2023), YouTube — «Viewed vs swiped away» (справка). Поэтому план
строится вокруг удержания:

    крючок 0–3 с  →  перехват 3–8 с  →  событие каждые 3–7 с  →  выдача  →  петля

Числовые пороги вроде «80% досмотра = вирусно» сюда НЕ заложены: официальных порогов
не существует, они гуляют по блогам без первоисточника. Заложены только те числа, у
которых источник есть, и каждое подписано — см. --why.

    python reel_structure.py --message "как мы за день собрали лендинг" --seconds 35
    python reel_structure.py --message "..." --seconds 45 --platform reels --goal shares
    python reel_structure.py --message "..." --hook contradiction --loop
    python reel_structure.py --list-hooks
    python reel_structure.py --message "..." --seconds 30 -o plan.json
    python reel_structure.py --message "..." --music track.mp3   # склейки в такт
"""
from __future__ import annotations
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


import argparse
import json
import pathlib
import subprocess
import sys

# Типы крючков. Статус всей таблицы — практика: контролируемых сравнений типов не
# существует. Косвенная опора — Loewenstein (1994): любопытство возникает, когда
# пробел в знании конкретен и ощущается закрываемым за время ролика.
HOOKS = {
    "question":     ("Прямой вопрос", "тот, который зритель задал бы сам", "экспертное, обучающее"),
    "contradiction":("Контр-тезис", "спор с общим мнением ниши", "ниша с устоявшимся «все знают»"),
    "result_first": ("Результат вперёд", "показать готовое, потом как", "туториал, до/после"),
    "negative":     ("Не делай X", "задевает то, что зритель уже делает", "советы"),
    "counter":      ("Цифра", "число задаёт контракт на структуру", "перечисление"),
    "segment":      ("Обращение к своим", "«если ты …» — сужает охват, растит удержание", "узкая аудитория"),
    "anomaly":      ("Визуальная аномалия", "работает до слов, в первые полсекунды", "любой формат"),
    "in_medias":    ("С середины действия", "без вступления, сразу кульминация процесса", "процесс, влог"),
    "open_loop":    ("Обещание на конец", "требует реально выдать, иначе теряешь доверие", "ролики 45 с+"),
    "stake":        ("Личная ставка", "«меня забанили за это» — поднимает значимость", "личный бренд"),
    "unfinished":   ("Оборванная фраза", "дочитка титра = удержание", "текстовые форматы"),
    "confession":   ("Признание", "«я три года делал это неправильно»", "экспертное с уязвимостью"),
    "demo":         ("Показ вместо слов", "предмет/экран делает то, о чём ролик", "продукт, инструмент"),
    "compare":      ("Два варианта рядом", "выбор в кадре с первой секунды", "сравнение, обзор"),
    "stat":         ("Неожиданное число", "число должно быть проверяемым, иначе шум", "аналитика, отчёт"),
}

# Какой крючок уместен под цель. Первый в списке — предлагаемый по умолчанию.
GOAL_HOOKS = {
    "watch":  ["in_medias", "anomaly", "result_first", "unfinished"],
    "shares": ["contradiction", "stat", "negative", "confession"],
    "profile":["segment", "stake", "question", "confession"],
    "learn":  ["counter", "question", "demo", "result_first"],
}

# Ограничения площадок. Только официально подтверждённое.
PLATFORMS = {
    "reels": {
        "max_s": 180,
        "reco_s": 90,
        "note": "лимит 3 мин (январь 2025); для показа не-подписчикам ориентир ≤90 с",
        "signals": "досмотр до конца, пересылки в личку, лайки, переход на страницу звука",
    },
    "shorts": {
        "max_s": 180,
        "reco_s": 60,
        "note": "лимит 3 мин (октябрь 2024); официального оптимума длины нет",
        "signals": "остался смотреть против свайпнул",
    },
    "tiktok": {
        "max_s": 600,
        "reco_s": 34,
        "note": "21–34 с — официальная рекомендация, но для In-Feed РЕКЛАМЫ (2021), не для органики",
        "signals": "досмотр, шеры, комментарии, подписки",
    },
    "vk": {
        "max_s": 180, "reco_s": 60,
        "note": "публичных данных о ранжировании нет — план строится по общей доктрине",
        "signals": "не опубликовано",
    },
}

WHY = """
Откуда числа и правила (каждое — с источником, остальное в план не заложено):

  первые секунды решают     TikTok for Business, PDF «9 Creative Tips» (2021): 63% роликов
                            с лучшим CTR доносят суть за первые 3 с.
                            Facebook (2016): из переживших 3 с — 65% смотрят ≥10 с.
                            Граница «3 секунды» — конвенция индустрии (единица счёта
                            просмотра в рекламном кабинете), не природная константа.
  досмотр — главный сигнал  TikTok Newsroom (2020): досмотр получает «greater weight».
                            Instagram (2021, 2023): «watch all the way through» + пересылки.
                            YouTube, справка: «Viewed vs swiped away».
  длина                     Официального оптимума нет ни у одной площадки. 21–34 с у TikTok —
                            про рекламу, а не про органику.
  событие каждые 3–7 с      Практика (сходятся независимые практики). Косвенная опора —
                            исследования восприятия монтажа: склейка перезапускает внимание.
  петля ради пересмотра     Практика. Пересмотры входят в время просмотра по определению,
                            но отдельным сигналом ранжирования официально не названы.

  НЕ заложено намеренно:    пороги «60/80% досмотра», «теряешь треть за 3 секунды»,
                            «внимание 8 секунд» — первоисточников нет.
"""


def beats(total: float, loop: bool) -> list[dict]:
    """Разложить длительность на блоки. Доли, а не секунды: план должен масштабироваться.

    Крючок держим коротким при любой длине — растянутый крючок и есть главная причина
    отвала. Выдача забирает последнюю пятую часть: если её сжать, обещание оказывается
    невыполненным, а это дороже, чем секунда лишнего тела.
    """
    hook = min(3.0, total * 0.12)
    rehook = min(5.0, total * 0.16)
    payoff = max(3.0, total * 0.20)
    tail = 1.2 if loop else 0.0
    body = max(total - hook - rehook - payoff - tail, total * 0.25)

    out = [
        {"block": "крючок", "start": 0.0, "dur": hook,
         "task": "дать конкретное обещание или показать аномалию",
         "fail": "вступление, логотип, «привет, сегодня я» — здесь уходит большинство"},
        {"block": "перехват", "start": hook, "dur": rehook,
         "task": "подтвердить, что обещание настоящее: первая порция сути",
         "fail": "пересказ крючка другими словами — зритель считывает пустоту"},
        {"block": "тело", "start": hook + rehook, "dur": body,
         "task": "события подряд: каждое добавляет то, чего не было",
         "fail": "ровный монолог без смены плана"},
        {"block": "выдача", "start": hook + rehook + body, "dur": payoff,
         "task": "выдать ровно то, что обещал крючок",
         "fail": "продающий призыв вместо обещанного — зритель свайпает, досмотр падает"},
    ]
    if loop:
        out.append({"block": "петля", "start": total - tail, "dur": tail,
                    "task": "последний кадр стыкуется с первым: пересмотр не заметен",
                    "fail": "затемнение и титры — они прямо говорят «можно уходить»"})
    return out


def events(start: float, dur: float, step_lo=3.0, step_hi=7.0, dense=False) -> list[float]:
    """Моменты, где обязано что-то произойти. Плотнее к концу тела — внимание проседает."""
    out, t = [], start
    n = 0
    while t < start + dur - 0.5:
        out.append(round(t, 2))
        k = (t - start) / max(dur, 0.01)
        step = step_hi - (step_hi - step_lo) * k        # к концу блока чаще
        t += step * (0.7 if dense else 1.0)
        n += 1
        if n > 200:
            break
    return out


def music_beats(path: str) -> dict | None:
    """Сетку склеек взять из музыки, если трек задан."""
    tool = pathlib.Path(__file__).parent.parent.parent / "video-editor" / "scripts" / "music_map.py"
    if not tool.exists():
        return None
    # Разбор трека занимает секунды, поэтому результат кладём рядом с ним и
    # переиспользуем: один и тот же трек в проекте разбирается один раз.
    tmp = pathlib.Path(path).with_suffix(".map.json")
    if not tmp.exists():
        r = subprocess.run([sys.executable, str(tool), path, "-o", str(tmp)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not tmp.exists():
            return None
    return json.loads(tmp.read_text(encoding="utf-8"))


def snap(times: list[float], grid: list[float]) -> list[float]:
    """Притянуть события к ближайшей доле: склейка мимо доли читается как ошибка."""
    if not grid:
        return times
    out = []
    for t in times:
        out.append(min(grid, key=lambda g: abs(g - t)))
    return sorted(set(round(x, 2) for x in out))


def build(message: str, seconds: float, platform: str, goal: str,
          hook: str | None, loop: bool, music: str | None) -> dict:
    p = PLATFORMS[platform]
    warn = []
    if seconds > p["max_s"]:
        warn.append(f"{seconds:.0f} с превышает лимит площадки ({p['max_s']} с)")
    if platform == "tiktok" and abs(seconds - 34) > 20:
        warn.append("для TikTok есть официальная рекомендация 21–34 с, но она про рекламу — "
                    "для органики это не норматив")

    hook = hook or GOAL_HOOKS[goal][0]
    plan = beats(seconds, loop)
    body = next(b for b in plan if b["block"] == "тело")
    ev = events(body["start"], body["dur"], dense=(seconds <= 20))

    grid = []
    m = music_beats(music) if music else None
    if m:
        grid = m.get("downbeats") or m.get("beats") or []
        ev = snap(ev, grid)

    for b in plan:
        b["start"] = round(b["start"], 2)
        b["dur"] = round(b["dur"], 2)
        b["end"] = round(b["start"] + b["dur"], 2)

    return {
        "message": message,
        "seconds": seconds,
        "platform": platform,
        "platform_note": p["note"],
        "ranking_signals": p["signals"],
        "goal": goal,
        "hook": {"type": hook, "name": HOOKS[hook][0], "how": HOOKS[hook][1],
                 "fits": HOOKS[hook][2],
                 "alternatives": [h for h in GOAL_HOOKS[goal] if h != hook]},
        "loop": loop,
        "blocks": plan,
        "event_times": ev,
        "music": ({"file": m["file"], "bpm": m["tempo_bpm"], "bar_s": m["bar_s"],
                   "drops": m["drops"]} if m else None),
        "warnings": warn,
    }


def render(plan: dict) -> str:
    L = []
    L.append(f"  {plan['message']}")
    L.append(f"  {plan['seconds']:.0f} с · {plan['platform']} · цель: {plan['goal']}"
             + ("  · с петлёй" if plan["loop"] else ""))
    L.append(f"  площадка ранжирует по: {plan['ranking_signals']}")
    L.append(f"  {plan['platform_note']}")
    h = plan["hook"]
    L.append(f"\n  крючок: {h['name']} — {h['how']}")
    L.append(f"          уместен: {h['fits']}")
    L.append(f"          если не пойдёт: {', '.join(HOOKS[a][0] for a in h['alternatives'])}")
    if plan["music"]:
        mu = plan["music"]
        L.append(f"\n  музыка: {mu['bpm']} BPM, такт {mu['bar_s']:.2f} с, "
                 f"дропы {', '.join(f'{d:.0f}с' for d in mu['drops']) or '—'}"
                 f"  (склейки притянуты к тактам)")
    L.append("")
    for b in plan["blocks"]:
        L.append(f"   {b['start']:5.1f}–{b['end']:5.1f}  {b['block']:9s} {b['task']}")
        L.append(f"                    ✗ {b['fail']}")
    L.append(f"\n  события в теле: {', '.join(f'{t:.1f}' for t in plan['event_times'])}")
    L.append("  (в каждой точке — смена плана, новый факт, титр или движение; "
             "пустая точка читается как провал темпа)")
    for w in plan["warnings"]:
        L.append(f"\n  ⚠ {w}")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--message", help="о чём ролик, одной фразой")
    ap.add_argument("--seconds", type=float, default=35)
    ap.add_argument("--platform", choices=sorted(PLATFORMS), default="reels")
    ap.add_argument("--goal", choices=sorted(GOAL_HOOKS), default="watch",
                    help="watch=досмотр, shares=пересылки, profile=подписка, learn=обучение")
    ap.add_argument("--hook", choices=sorted(HOOKS), help="навязать тип крючка")
    ap.add_argument("--loop", action="store_true", help="замкнуть конец на начало")
    ap.add_argument("--music", help="трек — притянуть склейки к тактам")
    ap.add_argument("-o", "--out", help="сохранить план в JSON")
    ap.add_argument("--list-hooks", action="store_true")
    ap.add_argument("--why", action="store_true", help="откуда взяты правила и числа")
    a = ap.parse_args()

    if a.why:
        print(WHY)
        return 0
    if a.list_hooks:
        for k, (name, how, fits) in HOOKS.items():
            print(f"  {k:14s} {name:22s} {how}")
            print(f"                 уместен: {fits}")
        return 0
    if not a.message:
        ap.error("нужен --message (или --list-hooks / --why)")

    plan = build(a.message, a.seconds, a.platform, a.goal, a.hook, a.loop, a.music)
    print(render(plan))
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
        print(f"\n  план: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
