#!/usr/bin/env python3
"""Озвучка, попадающая в титры.

Обычный путь — сложить весь текст в одну реплику и наложить её на ролик — даёт
расхождение, которое не видно в логах и не слышно при беглой проверке: диктор
проговаривает текст за одно время, а титры идут за другое. К середине ролика голос
обгоняет картинку на несколько секунд, а в конце наступает тишина, пока титры ещё
меняются.

Здесь каждая фраза синтезируется отдельно и ставится ровно в тот момент, когда её
титр появляется на экране. Если фраза не влезает в отведённое ей окно, она не
обрезается: скрипт сообщает, на сколько она длиннее, — это повод поправить сценарий,
а не подгонять звук растяжением, от которого голос звучит неестественно.

    python voice_timed.py script.json -o voice_timed.mp3
    python voice_timed.py script.json -o voice_timed.mp3 --voice <id>
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

ENV = pathlib.Path.home() / ".claude" / ".credentials.master.env"


def creds() -> dict:
    out = {}
    for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def phrases(lines: list[dict], per_line: float) -> list[dict]:
    """Собрать титры во фразы: говорить надо связно, а титры нарезаны мелко под ритм.

    Границей фразы служит либо конец предложения по смыслу, либо пауза между титрами.
    Подряд идущие короткие титры («сто», «пятнадцать», «тысяч генераций») произносятся
    одной фразой — иначе диктор рубит счёт на отдельные слова.
    """
    out, buf, start = [], [], 0.0
    t = 0.0
    for i, ln in enumerate(lines):
        if not buf:
            start = t
        buf.append(ln.get("text", "").replace("\n", " ").strip())
        t += ln.get("seconds", per_line)
        last = i + 1 >= len(lines)
        long_enough = len(" ".join(buf)) >= 24
        # Окно фразы ограничено и по времени. Иначе несколько титров склеиваются в одну
        # короткую реплику, она произносится за три секунды в окне на пять, и в ролике
        # появляется провал: музыка играет, а речи нет. Детектор тишины его не находит.
        # Допуск обязателен: длительности складываются дробями, и разница выходит
        # 3.19999… там, где по сценарию ровно 3.2 — строгое сравнение окно не закрывает.
        # Длиннее окно — живее интонация: на фразе в два слова синтез не успевает
        # построить мелодию и читает её ровным тоном. Пять секунд дают ему
        # достаточно контекста, а титры внутри фразы всё равно меняются своим ритмом.
        window_full = t - start >= 5.0 - 1e-6
        if last or window_full or (long_enough and ln.get("seconds", per_line) >= 1.2):
            out.append({"text": " ".join(buf), "start": round(start, 2),
                        "end": round(t, 2)})
            buf = []
    return out


def readable(text: str) -> str:
    """Титры набраны прописными — диктор читает их плоско, будто перечисляет.

    Для звука нужен обычный вид текста: заглавная в начале, точка в конце. Смысл тот
    же, а интонация появляется — синтез опирается на регистр и знаки препинания.
    """
    s = " ".join(text.split())
    if s.isupper():
        s = s.capitalize()
    return s if s.endswith((".", "!", "?", "…")) else s + "."


def retime(data: dict, ph: list[dict], durs: list[float], per_line: float,
           pause: float, out_path: str) -> None:
    """Подогнать длительности титров под то, как реально звучит речь.

    Сценарий задаёт время на глаз, а диктор говорит со своей скоростью. Расхождение
    накапливается в паузы: титр висит, а звучит тишина — и ролик читается затянутым,
    хотя каждый кусок по отдельности нормальный.

    Каждой фразе выделяется ровно её длительность плюс короткая пауза, а внутри фразы
    время делится между титрами в прежней пропорции — ритм смены титров сохраняется.
    """
    lines = data["lines"]
    # Сопоставить титры фразам: фразы идут подряд и покрывают весь сценарий.
    idx, t = 0, 0.0
    groups: list[list[int]] = []
    for p in ph:
        g = []
        while idx < len(lines) and t < p["end"] - 1e-6:
            g.append(idx)
            t += lines[idx].get("seconds", per_line)
            idx += 1
        groups.append(g)

    total_before = sum(l.get("seconds", per_line) for l in lines)
    for g, dur in zip(groups, durs):
        if not g:
            continue
        old = sum(lines[i].get("seconds", per_line) for i in g)
        new = dur + pause
        k = new / old if old else 1.0
        for i in g:
            lines[i]["seconds"] = round(lines[i].get("seconds", per_line) * k, 2)

    total_after = sum(l.get("seconds", per_line) for l in lines)
    pathlib.Path(out_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  пересчитанный сценарий: {out_path}")
    print(f"    было {total_before:.1f} с → стало {total_after:.1f} с "
          f"(речь плотнее на {total_before - total_after:.1f} с)")
    short = [l["text"][:22] for l in lines if l.get("seconds", 0) < 0.28]
    if short:
        print(f"    слишком короткие титры (<0.28 с), глаз не успеет прочесть: "
              f"{', '.join(short)}")


def say(text: str, api: str, voice: str, out: pathlib.Path,
        model: str = "eleven_multilingual_v2") -> tuple[float, dict]:
    """Одна фраза голосом.

    Модель по умолчанию выбрана прослушиванием, а не по описанию. Более новая
    eleven_v3 считается выразительнее, но на коротких рубленых фразах ролика читает
    их с длинными паузами и звучит отрывистее — сравнение двух дорожек на слух дало
    обратный ожидаемому результат. Переключается ключом --model.
    """
    settings = ({"stability": 0.4, "similarity_boost": 0.8, "use_speaker_boost": True}
                if model == "eleven_v3"
                else {"stability": 0.32, "similarity_boost": 0.85, "style": 0.22,
                      "use_speaker_boost": True})
    body = {"text": text, "model_id": model, "voice_settings": settings}
    # Ответ с выравниванием: кроме звука приходит время начала и конца КАЖДОЙ буквы.
    # Это то, из чего делается настоящий липсинк — рот повторяет звуки речи, а не
    # громкость. По громкости рот открывается на любом звуке одинаково, и получается
    # челюсть-щелкунчик вместо артикуляции.
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps",
        data=json.dumps(body).encode(),
        headers={"xi-api-key": api, "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    out.write_bytes(base64.b64decode(d["audio_base64"]))

    al = d.get("normalized_alignment") or d.get("alignment") or {}
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(out)],
                         capture_output=True, text=True).stdout.strip()
    return float(dur or 0), al


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--voice", help="идентификатор голоса ElevenLabs")
    ap.add_argument("--per-line", type=float, default=0.9)
    ap.add_argument("--duration", type=float, help="общая длина дорожки")
    ap.add_argument("--retime", help="куда сохранить сценарий, подогнанный под речь")
    ap.add_argument("--align", help="куда сохранить тайминги букв для липсинка")
    ap.add_argument("--model", default="eleven_multilingual_v2",
                    help="модель озвучки ElevenLabs")
    ap.add_argument("--pause", type=float, default=0.32,
                    help="пауза после каждой фразы, с")
    a = ap.parse_args()

    K = creds()
    api = K.get("ELEVENLABS_API_KEY", "")
    voice = a.voice or K.get("ELEVENLABS_VOICE_ID_RU") or "MWyJiWDobXN8FX3CJTdE"
    if not api:
        raise SystemExit("нет ключа ElevenLabs")

    data = json.loads(pathlib.Path(a.script).read_text(encoding="utf-8"))
    lines = data["lines"]
    ph = phrases(lines, a.per_line)
    total = a.duration or sum(l.get("seconds", a.per_line) for l in lines)
    print(f"  титров: {len(lines)} → фраз для озвучки: {len(ph)}, ролик {total:.1f} с")

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        parts, over, align = [], [], []
        for i, p in enumerate(ph):
            f = tmp / f"p{i:02d}.mp3"
            dur, al = say(readable(p["text"]), api, voice, f, a.model)
            # Тайминги букв приходят от начала фразы — сдвигаем их в время ролика.
            chars = al.get("characters", [])
            cs = al.get("character_start_times_seconds", [])
            ce = al.get("character_end_times_seconds", [])
            for j, c in enumerate(chars):
                align.append({"c": c, "s": round(p["start"] + cs[j], 3),
                              "e": round(p["start"] + ce[j], 3)})
            window = p["end"] - p["start"]
            flag = ""
            if dur > window + 0.25:
                over.append((p["text"][:34], round(dur - window, 2)))
                flag = f"  ← длиннее окна на {dur - window:.1f} с"
            print(f"  {p['start']:5.1f}–{p['end']:5.1f} с  «{p['text'][:42]}»  "
                  f"{dur:.1f} с{flag}")
            parts.append((p["start"], f, dur))

        # Каждая фраза задерживается на свой момент и подмешивается — так порядок
        # и паузы задаются расписанием титров, а не длиной синтеза.
        ins, filt, mix = [], [], []
        for i, (start, f, _) in enumerate(parts):
            ins += ["-i", str(f)]
            ms = int(start * 1000)
            filt.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
            mix.append(f"[a{i}]")
        graph = (";".join(filt) + ";" + "".join(mix)
                 + f"amix=inputs={len(parts)}:duration=longest:dropout_transition=0,"
                 + f"apad=whole_dur={total:.2f}[out]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins,
                        "-filter_complex", graph, "-map", "[out]",
                        "-b:a", "192k", a.out], check=True)

    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", a.out],
                       capture_output=True, text=True).stdout.strip()
    print(f"\n  дорожка: {a.out}, {float(d or 0):.1f} с")

    if a.align:
        pathlib.Path(a.align).write_text(
            json.dumps(align, ensure_ascii=False), encoding="utf-8")
        print(f"  тайминги букв: {a.align} ({len(align)} символов) — для липсинка")

    if a.retime:
        retime(data, ph, [p[2] for p in parts], a.per_line, a.pause, a.retime)
    if over:
        print("  не помещаются в свои окна — стоит укоротить текст или дать больше времени:")
        for txt, extra in over:
            print(f"    «{txt}» на {extra} с")
    return 0


if __name__ == "__main__":
    sys.exit(main())
