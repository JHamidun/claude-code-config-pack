#!/usr/bin/env python3
"""Генерация видео напрямую у первоисточника — без платформ-посредников.

Зачем. Сервисы вроде Higgsfield берут деньги за обёртку над теми же моделями и режут
управление: часть параметров они не отдают, промпт молча переписывают своим
«улучшателем», а результат живёт в их аккаунте. У нас есть ключи к самим моделям —
значит посредник не нужен, а параметры доступны все.

Что подключено:
    Veo 3.1 (Google)   — три ветки: полная, быстрая, лёгкая; кадр-в-видео, звук в кадре
    Sora 2 (OpenAI)    — включая Pro; длиннее и послушнее к сложным сценам
    кадры              — Nano Banana Pro и 3.1 Flash Image, для первого кадра сцены

Модели просят по-разному, поэтому разница спрятана внутрь: снаружи одни и те же
аргументы, а на выходе всегда файл на диске.

    python direct_video.py models                       # что доступно по ключам
    python direct_video.py gen "кадр…" -o out.mp4 --engine veo --seconds 8 --aspect 9:16
    python direct_video.py gen "кадр…" -o out.mp4 --engine sora --seconds 12
    python direct_video.py gen "кадр…" -o out.mp4 --engine veo --first-frame start.png
    python direct_video.py frame "описание" -o kadr.png --aspect 9:16
    python direct_video.py plan shots.json -o dir/      # пачкой по плану кадров

Деньги тратятся на каждый вызов — поэтому без --yes скрипт печатает, что собирается
сделать, и останавливается.
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
import base64
import json
import mimetypes
import pathlib
import sys
import time
import urllib.error
import urllib.request

ENV = pathlib.Path.home() / ".claude" / ".credentials.master.env"
GOOGLE = "https://generativelanguage.googleapis.com/v1beta"
OPENAI = "https://api.openai.com/v1"

VEO = {
    "veo":      "veo-3.1-generate-preview",
    "veo-fast": "veo-3.1-fast-generate-preview",
    "veo-lite": "veo-3.1-lite-generate-preview",
}
SORA = {"sora": "sora-2", "sora-pro": "sora-2-pro"}
IMAGE = {"pro": "gemini-3-pro-image", "flash": "gemini-3.1-flash-image-preview"}

# Sora принимает не любой размер, а перечень. Просим соотношение — подставляем ближайший.
SORA_SIZE = {"16:9": "1280x720", "9:16": "720x1280", "1:1": "720x720"}


def creds() -> dict:
    out = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def call(url: str, *, data=None, headers=None, method=None, timeout=180):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        return json.loads(raw) if raw[:1] in (b"{", b"[") else raw
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"{url.split('?')[0]} → HTTP {e.code}\n  {detail}")


def b64_image(path: str) -> tuple[str, str]:
    p = pathlib.Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return base64.b64encode(p.read_bytes()).decode(), mime


# --- Veo ------------------------------------------------------------------------------

def veo_generate(key: str, model: str, prompt: str, out: pathlib.Path, *,
                 seconds: int, aspect: str, first_frame: str | None,
                 negative: str | None, resolution: str) -> pathlib.Path:
    """Veo работает долгой операцией: запрос принимают, а файл забираешь потом."""
    inst: dict = {"prompt": prompt}
    if first_frame:
        b, mime = b64_image(first_frame)
        inst["image"] = {"bytesBase64Encoded": b, "mimeType": mime}
    # Про людей в кадре модель решает сама: значения этого параметра у разных веток Veo
    # различаются, и неподдерживаемое валит запрос целиком («allow_adult ... not
    # supported»). Не передаём — работает везде.
    params = {"aspectRatio": aspect, "durationSeconds": seconds,
              "resolution": resolution}
    if negative:
        params["negativePrompt"] = negative

    op = call(f"{GOOGLE}/models/{model}:predictLongRunning?key={key}",
              data={"instances": [inst], "parameters": params})
    name = op.get("name")
    if not name:
        raise SystemExit(f"Veo не вернул операцию: {str(op)[:300]}")

    print(f"    операция принята, жду результат", end="", flush=True)
    waited = 0
    while waited < 900:
        time.sleep(10)
        waited += 10
        st = call(f"{GOOGLE}/{name}?key={key}", timeout=60)
        if st.get("done"):
            print()
            if "error" in st:
                raise SystemExit(f"Veo отказал: {json.dumps(st['error'], ensure_ascii=False)[:400]}")
            resp = st.get("response", {})
            vids = (resp.get("generateVideoResponse", {}).get("generatedSamples")
                    or resp.get("generatedSamples") or resp.get("predictions") or [])
            if not vids:
                raise SystemExit(f"Veo вернул пустой результат: {json.dumps(resp)[:400]}")
            v = vids[0]
            uri = (v.get("video", {}) or {}).get("uri") or v.get("uri")
            if uri:
                data = call(f"{uri}&key={key}" if "?" in uri else f"{uri}?key={key}", timeout=300)
                out.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())
            elif v.get("bytesBase64Encoded"):
                out.write_bytes(base64.b64decode(v["bytesBase64Encoded"]))
            else:
                raise SystemExit(f"не нашёл видео в ответе: {json.dumps(v)[:300]}")
            return out
        print(".", end="", flush=True)
    raise SystemExit("Veo не ответил за 15 минут")


# --- Sora -----------------------------------------------------------------------------

def sora_generate(key: str, model: str, prompt: str, out: pathlib.Path, *,
                  seconds: int, aspect: str, first_frame: str | None) -> pathlib.Path:
    h = {"Authorization": f"Bearer {key}"}
    body = {"model": model, "prompt": prompt,
            "seconds": str(seconds), "size": SORA_SIZE.get(aspect, "720x1280")}
    if first_frame:
        # Кадр-основа передаётся отдельным полем; формат отличается от Veo намеренно.
        b, mime = b64_image(first_frame)
        body["input_reference"] = f"data:{mime};base64,{b}"

    job = call(f"{OPENAI}/videos", data=body, headers=h)
    jid = job.get("id")
    if not jid:
        raise SystemExit(f"Sora не приняла задание: {str(job)[:300]}")

    print("    задание принято, жду результат", end="", flush=True)
    waited = 0
    while waited < 1800:
        time.sleep(10)
        waited += 10
        st = call(f"{OPENAI}/videos/{jid}", headers=h, timeout=60)
        status = st.get("status")
        if status == "completed":
            print()
            data = call(f"{OPENAI}/videos/{jid}/content", headers=h, timeout=300)
            out.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())
            return out
        if status in ("failed", "cancelled"):
            print()
            raise SystemExit(f"Sora: {status} — {json.dumps(st.get('error') or {}, ensure_ascii=False)[:300]}")
        print(".", end="", flush=True)
    raise SystemExit("Sora не ответила за 30 минут")


# --- кадр -----------------------------------------------------------------------------

def make_frame(key: str, model: str, prompt: str, out: pathlib.Path, aspect: str) -> pathlib.Path:
    r = call(f"{GOOGLE}/models/{model}:generateContent?key={key}",
             data={"contents": [{"parts": [{"text": prompt}]}],
                   "generationConfig": {"responseModalities": ["IMAGE", "TEXT"],
                                        "imageConfig": {"aspectRatio": aspect}}})
    for cand in r.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            d = part.get("inlineData") or part.get("inline_data")
            if d and d.get("data"):
                out.write_bytes(base64.b64decode(d["data"]))
                return out
    raise SystemExit(f"кадр не пришёл: {json.dumps(r)[:400]}")


# --- команды --------------------------------------------------------------------------

def cmd_models(K: dict) -> int:
    gk = K.get("GOOGLE_API_KEY") or K.get("GEMINI_API_KEY")
    if gk:
        r = call(f"{GOOGLE}/models?key={gk}")
        names = [m["name"].split("/")[-1] for m in r.get("models", [])]
        print("  Google:")
        for n in names:
            if "veo" in n:
                print(f"    видео    {n}")
        for n in names:
            if "image" in n:
                print(f"    кадры    {n}")
    if K.get("OPENAI_API_KEY"):
        r = call(f"{OPENAI}/models", headers={"Authorization": f"Bearer {K['OPENAI_API_KEY']}"})
        so = [m["id"] for m in r.get("data", []) if "sora" in m["id"]]
        print("  OpenAI:")
        for n in so:
            print(f"    видео    {n}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("models", help="что доступно по ключам")

    p = sub.add_parser("gen", help="сгенерировать кадр видео")
    p.add_argument("prompt")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--engine", default="veo", choices=list(VEO) + list(SORA))
    p.add_argument("--seconds", type=int, default=8)
    p.add_argument("--aspect", default="9:16", choices=["16:9", "9:16", "1:1"])
    p.add_argument("--resolution", default="1080p", choices=["720p", "1080p"])
    p.add_argument("--first-frame", help="картинка-основа: сцена начнётся с неё")
    p.add_argument("--negative", help="чего в кадре быть не должно (только Veo)")
    p.add_argument("--yes", action="store_true", help="не спрашивать подтверждения")

    p = sub.add_parser("frame", help="сгенерировать статичный кадр")
    p.add_argument("prompt")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--aspect", default="9:16")
    p.add_argument("--model", default="pro", choices=list(IMAGE))
    p.add_argument("--yes", action="store_true")

    p = sub.add_parser("plan", help="пачкой по файлу плана кадров")
    p.add_argument("planfile", help="JSON: [{id, prompt, seconds, aspect, first_frame, engine}]")
    p.add_argument("-o", "--outdir", default="shots")
    p.add_argument("--engine", default="veo-fast")
    p.add_argument("--yes", action="store_true")

    a = ap.parse_args()
    K = creds()

    if a.cmd == "models":
        return cmd_models(K)

    gk = K.get("GOOGLE_API_KEY") or K.get("GEMINI_API_KEY") or ""
    ok = K.get("OPENAI_API_KEY", "")

    if a.cmd == "frame":
        if not a.yes:
            print(f"  сгенерирую кадр моделью {IMAGE[a.model]}, {a.aspect} → {a.out}")
            print("  это платный вызов; повтори с --yes")
            return 0
        out = make_frame(gk, IMAGE[a.model], a.prompt, pathlib.Path(a.out), a.aspect)
        print(f"  готово: {out}  ({out.stat().st_size/1024:.0f} КБ)")
        return 0

    if a.cmd == "gen":
        engine = a.engine
        model = VEO.get(engine) or SORA[engine]
        if not a.yes:
            print(f"  движок {model}, {a.seconds} с, {a.aspect}"
                  + (f", первый кадр {a.first_frame}" if a.first_frame else ""))
            print(f"  промпт: {a.prompt[:160]}")
            print("  это платный вызов; повтори с --yes")
            return 0
        out = pathlib.Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"  {model}: {a.seconds} с, {a.aspect}")
        if engine in VEO:
            veo_generate(gk, model, a.prompt, out, seconds=a.seconds, aspect=a.aspect,
                         first_frame=a.first_frame, negative=a.negative,
                         resolution=a.resolution)
        else:
            sora_generate(ok, model, a.prompt, out, seconds=a.seconds, aspect=a.aspect,
                          first_frame=a.first_frame)
        print(f"  готово: {out}  ({out.stat().st_size/1048576:.1f} МБ)")
        return 0

    if a.cmd == "plan":
        shots = json.loads(pathlib.Path(a.planfile).read_text(encoding="utf-8"))
        if isinstance(shots, dict):
            shots = shots.get("shots") or shots.get("beats") or []
        outdir = pathlib.Path(a.outdir)
        if not a.yes:
            total = sum(s.get("seconds", 8) for s in shots)
            print(f"  кадров {len(shots)}, суммарно {total} с, движок по умолчанию {a.engine}")
            for s in shots[:6]:
                print(f"    {s.get('id','?'):>10}  {s.get('seconds',8)}с  {str(s.get('prompt',''))[:90]}")
            print("  это платные вызовы; повтори с --yes")
            return 0
        outdir.mkdir(parents=True, exist_ok=True)
        done = []
        for i, s in enumerate(shots, 1):
            sid = s.get("id") or f"shot_{i:02d}"
            dst = outdir / f"{sid}.mp4"
            if dst.exists() and dst.stat().st_size > 10_000:
                print(f"  [{i}/{len(shots)}] {sid}: уже есть, пропускаю")
                done.append(dst)
                continue
            eng = s.get("engine") or a.engine
            model = VEO.get(eng) or SORA[eng]
            print(f"  [{i}/{len(shots)}] {sid}: {model}, {s.get('seconds', 8)} с")
            try:
                if eng in VEO:
                    veo_generate(gk, model, s["prompt"], dst,
                                 seconds=s.get("seconds", 8), aspect=s.get("aspect", "9:16"),
                                 first_frame=s.get("first_frame"), negative=s.get("negative"),
                                 resolution=s.get("resolution", "1080p"))
                else:
                    sora_generate(ok, model, s["prompt"], dst,
                                  seconds=s.get("seconds", 8), aspect=s.get("aspect", "9:16"),
                                  first_frame=s.get("first_frame"))
                done.append(dst)
            except SystemExit as e:
                # Один провалившийся кадр не должен ронять всю пачку: остальные дороже.
                print(f"        ✗ {str(e)[:160]}")
        print(f"\n  готово кадров: {len(done)} из {len(shots)} → {outdir}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
