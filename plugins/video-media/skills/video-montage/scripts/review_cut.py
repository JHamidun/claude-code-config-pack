#!/usr/bin/env python3
"""Приёмка готового ролика: посмотреть и послушать, а не поверить на слово.

Зачем нужен отдельный шаг. Ролик собирается по плану, а план проверить нельзя — он
описывает намерение. Проверить можно только то, что реально записалось в файл: там
бывает и чёрный кадр вместо картинки, и голос, ушедший под музыку, и перегруз, и
тишина в конце. Всё это соберётся без единой ошибки в логе и будет выглядеть как
успешная сборка.

Скрипт готовит две вещи, которые человек (или модель) может воспринять напрямую:

    контактный лист  — сетка кадров через равные промежутки, видно весь ролик разом
    замеры звука     — громкость по стандарту вещания, пики, доля тишины, баланс

Оценки скрипт не выносит: он показывает то, что есть, и отмечает места, которые
стоит посмотреть внимательно.

    python review_cut.py reel.mp4 -o review/
    python review_cut.py reel.mp4 -o review/ --tiles 20
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys


def probe(path: pathlib.Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True).stdout
    return json.loads(out or "{}")


def contact_sheet(src: pathlib.Path, dst: pathlib.Path, tiles: int,
                  duration: float, cols: int = 5) -> pathlib.Path:
    """Сетка кадров: весь ролик одной картинкой.

    Равные промежутки, а не сцены: в формате без склеек детектор сцен не находит
    ничего, и «по сценам» лист получился бы из одного кадра.
    """
    rows = max(1, -(-tiles // cols))
    step = max(duration / tiles, 0.04)
    out = dst / "contact.jpg"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src),
         "-vf", f"fps=1/{step:.4f},scale=300:-1,tile={cols}x{rows}:margin=6:padding=4:color=#dddddd",
         "-frames:v", "1", "-q:v", "3", str(out)],
        check=True, capture_output=True)
    return out


def audio_stats(src: pathlib.Path) -> dict:
    """Громкость по стандарту вещания и пики — то, из-за чего ролик звучит тихо или рвано."""
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(src), "-af",
         "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    s, e = r.rfind("{"), r.rfind("}")
    data = json.loads(r[s:e + 1]) if s >= 0 and e > s else {}

    # Доля тишины: если её много, где-то потерялась дорожка или остался пустой хвост.
    sil = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(src), "-af",
         "silencedetect=noise=-45dB:d=0.35", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    quiet = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", sil)]
    data["silence_total"] = round(sum(quiet), 2)
    data["silence_chunks"] = len(quiet)
    return data


def extract_audio(src: pathlib.Path, dst: pathlib.Path) -> pathlib.Path:
    """Отдельная звуковая дорожка — чтобы её можно было прослушать целиком."""
    out = dst / "audio.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                    "-vn", "-b:a", "160k", str(out)], check=True, capture_output=True)
    return out


LISTEN_PROMPT = """Это звуковая дорожка вертикального ролика для ленты. Послушай её и
ответь коротко, по-русски, без вступлений и без похвал.

1. Разборчива ли речь — не глотаются ли окончания, нет ли каши.
2. Не забивает ли музыка голос; не выпирают ли звуковые эффекты.
3. Есть ли провалы: места, где ничего не звучит дольше секунды.
4. Ровная ли громкость или отдельные куски заметно тише либо громче.
5. Звучит ли диктор естественно или слышна машинная интонация — в каких словах.
6. Что бы ты исправил в первую очередь. ОДИН пункт.

Если чего-то не слышно — так и пиши, не додумывай."""


def listen(path: pathlib.Path) -> str:
    """Отдать дорожку модели, которая слышит звук.

    Замеры показывают уровни, но не слышимость: дорожка бывает в норме по числам и
    при этом с кашей в речи, машинной интонацией или музыкой поверх голоса. Числа и
    слух отвечают на разные вопросы, поэтому нужны оба.
    """
    import base64
    import json as _json
    import urllib.request

    env = pathlib.Path.home() / ".claude" / ".credentials.master.env"
    key = ""
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("GOOGLE_API_KEY="):
            key = line.split("=", 1)[1].strip()
    if not key:
        return "нет ключа для прослушивания"

    body = {"contents": [{"parts": [
        {"inlineData": {"mimeType": "audio/mpeg",
                        "data": base64.b64encode(path.read_bytes()).decode()}},
        {"text": LISTEN_PROMPT}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2000}}
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.7-flash:generateContent?key={key}",
        data=_json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            d = _json.loads(r.read())
    except Exception as e:            # сеть или квота — приёмка не должна падать из-за этого
        return f"прослушать не вышло: {e}"
    return "".join(p.get("text", "")
                   for c in d.get("candidates", [])
                   for p in c.get("content", {}).get("parts", [])).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--tiles", type=int, default=20, help="сколько кадров на лист")
    ap.add_argument("--listen", action="store_true",
                    help="прослушать дорожку, а не только измерить её")
    a = ap.parse_args()

    src = pathlib.Path(a.video)
    if not src.exists():
        raise SystemExit(f"нет файла: {src}")
    dst = pathlib.Path(a.out)
    dst.mkdir(parents=True, exist_ok=True)

    info = probe(src)
    fmt = info.get("format", {})
    dur = float(fmt.get("duration", 0) or 0)
    vs = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))

    # Возраст файла в выводе не для красоты: если рендер упал, на диске остаётся
    # прошлая сборка, приёмка проверяет её и рапортует об успехе. Свежесть — первое,
    # что надо увидеть.
    import time
    age_min = (time.time() - src.stat().st_mtime) / 60
    stamp = (f"собран {age_min:.0f} мин назад" if age_min >= 1
             else f"собран {age_min * 60:.0f} с назад")
    print(f"  {src.name}: {vs.get('width')}×{vs.get('height')}, {dur:.1f} с, "
          f"{int(float(fmt.get('size', 0)) / 1024)} КБ, {stamp}")
    if age_min > 10:
        print("  ← файл не свежий: возможно, последняя сборка не дошла до записи")
    if not has_audio:
        print("  ЗВУКОВОЙ ДОРОЖКИ НЕТ — ролик немой")

    sheet = contact_sheet(src, dst, a.tiles, dur)
    print(f"  контактный лист: {sheet}   ← посмотреть глазами")

    if has_audio:
        snd = extract_audio(src, dst)
        st = audio_stats(src)
        loud = float(st.get("input_i", 0) or 0)
        peak = float(st.get("input_tp", 0) or 0)
        print(f"  звук: {snd}   ← прослушать")
        print(f"    громкость {loud:.1f} LUFS (норма для лент −14), пик {peak:.1f} dBTP")
        print(f"    тишина: {st.get('silence_total', 0)} с "
              f"в {st.get('silence_chunks', 0)} местах из {dur:.1f} с")
        # Не вердикт, а поводы посмотреть внимательнее.
        if loud and loud < -18:
            print("    ← тише нормы: в ленте прозвучит глухо рядом с соседними роликами")
        if peak > -0.5:
            print("    ← пики у самого верха: возможен хрип на телефонном динамике")
        if st.get("silence_total", 0) > dur * 0.25:
            print("    ← четверть ролика тишина: проверь, не потерялась ли дорожка")

        if a.listen:
            print("\n  на слух:")
            heard = listen(snd)
            (dst / "listen.md").write_text(heard, encoding="utf-8")
            for ln in heard.splitlines():
                print("    " + ln)

    print("\n  дальше: открыть контактный лист и прослушать дорожку — "
          "сборка без ошибок не значит, что получилось")
    return 0


if __name__ == "__main__":
    sys.exit(main())
