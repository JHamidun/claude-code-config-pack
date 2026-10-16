#!/usr/bin/env python3
# TEMPLATE (from creator-reels pipeline). Working dir = $REEL_DIR or cwd; source MOVs = $REEL_SRC.
# See ../../references/talking-head-broll-reel.md for the full pipeline.
"""Author a reel timeline from an ordered beat list.

Distributes body_dur across body slots (weighted), accounting for xfade overlaps so
the body visual length == body VO length. Appends the ending slot (real footage).
Places SFX whooshes on the punchiest transitions + an impact on the hook.

Edit BEATS_R1 / BEATS_R2 below; run: python author_timeline.py r1
"""
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

import json
import os
import sys
from pathlib import Path

BASE = Path(os.environ.get("REEL_DIR") or Path.cwd())
FPS = 30

OVERLAP = {  # must match assemble_reel.TRANS
    "hard": 0.06, "fade": 0.28, "flash": 0.22, "zoom": 0.32, "wipel": 0.30,
    "wiper": 0.30, "slidel": 0.30, "slideu": 0.30, "smoothl": 0.32, "circle": 0.34, "dissolve": 0.30,
}

# (clip, weight, fx, trans, sfx_on_cut)
BEATS_R1 = [
    ("r1_s01", 1.0, "in",   "hard",  "impact"),   # hook: если бы я был психологом
    ("r1_s02", 1.3, "in",   "hard",  None),       # хотел больше клиентов, вот что бы делал
    ("r1_s03", 1.4, "left", "zoom",  "whoosh"),    # начал снимать рилсы
    ("r1_s04", 0.9, "in",   "flash", "whoosh"),    # приходят звезды (SUV/paparazzi)
    ("r1_s05a", 0.8, "left", "hard", None),        # Джиган
    ("r1_s05b", 0.8, "in",   "hard", None),        # Тимати
    ("r1_s05c", 0.9, "out",  "hard", None),        # Тиньков
    ("r1_s06", 1.3, "in",   "zoom",  "whoosh"),    # аватары звезд (3D head)
    ("r1_s07", 1.1, "in",   "hard",  None),        # разбираю их загоны
    ("r1_s08", 1.2, "out",  "flash", "ding"),      # формат завирусится (hearts)
    ("r1_s09", 1.3, "in",   "hard",  None),        # репост в сторис
    ("r1_s10", 1.5, "in",   "zoom",  "whoosh"),    # зритель: офигеть, мне поможет
    ("r1_s11", 1.0, "right","hard",  None),        # тг-бот (paper planes)
    ("r1_s12", 0.9, "in",   "hard",  None),        # мини-приложение (emoji)
    ("r1_s13", 1.2, "in",   "hard",  None),        # прожить эмоцию (breathing)
    ("r1_s14", 1.2, "out",  "flash", "whoosh"),    # лид-магнит (magnet)
    ("r1_s15", 1.1, "in",   "hard",  None),        # диагностика (laptop wave)
    ("r1_s16", 1.2, "in",   "zoom",  "impact"),    # забирайте (psychologist smirk)
]

BEATS_R2 = [
    ("r2_s01", 1.1, "in",   "hard",  "impact"),   # hook: если бы я был нутрициологом
    ("r2_s03", 1.2, "left", "zoom",  "whoosh"),    # начал снимать рилсы
    ("r2_s04", 1.2, "in",   "hard",  None),        # какой рацион каждому типу
    ("r2_s05b", 1.4, "in",  "flash", "whoosh"),    # работяга на заводе: стрипня, ворчать
    ("r2_s06", 1.3, "left", "hard",  None),        # предприниматель в суете
    ("r2_s07", 1.4, "in",   "hard",  None),        # офисный планктон: кофе печеньки
    ("r2_s08", 1.0, "in",   "zoom",  "whoosh"),    # резко врывался в кадр
    ("r2_s09", 1.4, "in",   "hard",  "ding"),      # здоровее добрее (plating meal)
    ("r2_s10", 1.2, "out",  "flash", None),        # покупал всё что хотите (happy couple)
    ("r2_s11", 1.6, "in",   "hard",  None),        # эмоция уверенности - доверие
    ("r2_s13", 1.4, "right","zoom",  "whoosh"),    # тг-бот мини-апка (food app)
    ("r2_s16", 1.3, "in",   "flash", "ding"),      # виртуальное яблочко (green apple)
    ("r2_s15", 1.2, "in",   "hard",  None),        # диагностика (nutritionist wave)
    ("r2_s17", 1.3, "in",   "hard",  None),        # платное сопровождение (handshake)
    ("r2_s18", 1.3, "in",   "zoom",  "impact"),    # забирайте (nutritionist smirk)
]

SFX_FILE = {
    "whoosh": "audio/sfx_whoosh.mp3", "whoosh2": "audio/sfx_whoosh2.mp3",
    "impact": "audio/sfx_impact.mp3", "ding": "audio/sfx_ding.mp3",
    "pop": "audio/sfx_pop.mp3", "riser": "audio/sfx_riser.mp3", "click": "audio/sfx_click.mp3",
}


def body_dur(reel):
    vo = BASE / "audio" / f"vo_{reel}.wav"
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(vo)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    reel = sys.argv[1]
    beats = BEATS_R1 if reel == "r1" else BEATS_R2
    bdur = body_dur(reel)

    # only keep beats whose clip exists; warn otherwise
    avail = []
    for b in beats:
        clip = BASE / "broll" / f"{b[0]}.mp4"
        if clip.exists() and clip.stat().st_size > 100_000:
            avail.append(b)
        else:
            print(f"  MISSING {b[0]} — skipped", file=sys.stderr)
    if not avail:
        print("no clips available yet", file=sys.stderr)
        sys.exit(1)

    # total overlap consumed across body cuts (slot i>0 entering)
    total_ov = sum(OVERLAP.get(b[3], 0.06) for b in avail[1:])
    # plus overlap of ending entering body (ending trans handled separately, add its overlap to body budget)
    end_trans = "flash"
    end_ov = OVERLAP[end_trans]
    # body visual must equal bdur; visual_len = sum(dur) - total_ov  => sum(dur) = bdur + total_ov
    budget = bdur + total_ov
    wsum = sum(b[1] for b in avail)
    slots = []
    sfx = []
    t = 0.0  # running visual start time of each cut (for sfx placement)
    for i, b in enumerate(avail):
        clip, w, fx, trans, sx = b
        dur = round(budget * w / wsum, 3)
        dur = max(dur, 1.6)
        slots.append({"clip": f"broll/{clip}.mp4", "dur": dur, "fx": fx, "trans": trans})
        # sfx placed at the cut INTO this slot
        if sx:
            ov = OVERLAP.get(trans, 0.06) if i > 0 else 0.0
            at = max(0.0, t - ov + 0.02)
            sfx.append({"file": SFX_FILE[sx], "at": round(at, 3), "gain": 0.8 if sx != "impact" else 0.6})
        t += dur - (OVERLAP.get(avail[i + 1][3], 0.06) if i + 1 < len(avail) else 0.0)

    # ending slot (real footage), enters with flash + whoosh
    end_dur = 12.75
    slots.append({"clip": "broll/ending.mp4", "dur": end_dur, "fx": "none", "trans": end_trans})
    body_visual = bdur  # by construction
    sfx.append({"file": SFX_FILE["whoosh2"], "at": round(body_visual - end_ov, 3), "gain": 0.9})

    tl = {
        "fps": FPS,
        "music": "audio/suno_f3955f4e.mp3",
        "music_gain": 0.15,
        "slots": slots,
        "sfx": sfx,
    }
    out = BASE / f"timeline_{reel}.json"
    out.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{reel}: {len(slots)} slots ({len(avail)} body + ending), body budget {budget:.1f}s, "
          f"sum_dur {sum(s['dur'] for s in slots):.1f}s, {len(sfx)} sfx -> {out.name}")


if __name__ == "__main__":
    main()
