#!/usr/bin/env python3
"""B-roll via Veo 3.1 Fast (text-to-video) — fallback when Runway explore is throttled.

3 concurrent ceiling. Safety softener on prompts. Strips nothing (we -an later).
Reuses broll/state.json; only generates shots missing a downloaded file.

Usage: python veo_runner.py shots_all.json [--model fast|31fast]
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

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

import json  # noqa: E402

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402


# Ключ — по требованию, а не при импорте. Раньше на верхнем уровне модуля стояли
# os.environ.pop("GEMINI_API_KEY") (мутация окружения ЛЮБОГО импортёра) и
# load_dotenv(...) (чтение файла с ключами), а клиент строился как
# os.environ["GOOGLE_API_KEY"] — без ключа это KeyError, по которому причину не понять.
def _google_api_key():
    """GOOGLE_API_KEY: окружение → ~/.claude/.credentials.master.env → внятный отказ."""
    if not os.environ.get("GOOGLE_API_KEY"):
        load_dotenv(Path.home() / ".claude" / ".credentials.master.env")
    os.environ.pop("GEMINI_API_KEY", None)  # конфликт SDK: приоритет у GOOGLE_API_KEY
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise SystemExit(
            "ОТКАЗ: не задан GOOGLE_API_KEY.\n"
            "  Где взять: aistudio.google.com/apikey\n"
            "  Как задать: export GOOGLE_API_KEY=... (или строка GOOGLE_API_KEY=... "
            "в ~/.claude/.credentials.master.env)"
        )
    return key

BASE = Path(__file__).parent
MODELS = {
    "fast": "veo-3.0-fast-generate-001",
    "31fast": "veo-3.1-fast-generate-preview",
}
MODEL = MODELS["31fast"]
CONC = 3

SOFTEN = {
    "awkward silence": "quiet pause", "tension": "stillness", "lonely": "solitary",
    "empty room": "minimal interior", "shadow figure": "silhouette", "dark room": "dim room",
    "greasy": "heavy", "grumpy": "weary", "frowning": "unsmiling",
}


def soften(p):
    for a, b in SOFTEN.items():
        p = p.replace(a, b)
    return p


def done_file(sid):
    f = BASE / "broll" / f"{sid}.mp4"
    return f.exists() and f.stat().st_size > 100_000


def main():
    shots = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "--model" in sys.argv:
        global MODEL
        MODEL = MODELS[sys.argv[sys.argv.index("--model") + 1]]
    client = genai.Client(api_key=_google_api_key())

    todo = [s for s in shots if not done_file(s["id"]) and s["id"] != "r2_s05a"]
    print(f"Veo {MODEL}: {len(todo)} shots", flush=True)

    active = {}  # sid -> operation
    queue = list(todo)
    fail = {}

    while queue or active:
        while queue and len(active) < CONC:
            s = queue.pop(0)
            sid = s["id"]
            try:
                op = client.models.generate_videos(
                    model=MODEL,
                    prompt=soften(s["prompt"]),
                    config=types.GenerateVideosConfig(aspect_ratio="9:16", number_of_videos=1),
                )
                active[sid] = op
                print(f"submitted {sid} (active={len(active)})", flush=True)
                time.sleep(2)
            except Exception as e:
                msg = str(e)
                print(f"submit err {sid}: {msg[:120]}", flush=True)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    queue.insert(0, s)
                    time.sleep(20)
                    break
                fail[sid] = msg[:200]

        if not active:
            continue
        time.sleep(12)
        for sid in list(active):
            op = active[sid]
            try:
                op = client.operations.get(op)
                active[sid] = op
            except Exception as e:
                print(f"poll err {sid}: {str(e)[:80]}", flush=True)
                continue
            if not op.done:
                continue
            try:
                vids = op.response.generated_videos if op.response else None
                if not vids:
                    print(f"EMPTY {sid} (safety NoneType?) — requeue softened", flush=True)
                    del active[sid]
                    fail[sid] = "empty_response"
                    continue
                video = vids[0].video
                client.files.download(file=video)
                out = BASE / "broll" / f"{sid}.mp4"
                video.save(str(out))
                print(f"DONE {sid} ({out.stat().st_size//1024}KB) [{len(active)-1} active, {len(queue)} queued]", flush=True)
            except Exception as e:
                print(f"save err {sid}: {str(e)[:120]}", flush=True)
                fail[sid] = str(e)[:200]
            del active[sid]

    print(f"ALL DONE. failures: {list(fail.keys())}", flush=True)
    if fail:
        (BASE / "broll" / "veo_fail.json").write_text(json.dumps(fail, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
