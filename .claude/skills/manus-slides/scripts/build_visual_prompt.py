#!/usr/bin/env python3
"""Сборка промпта для кадра из структурного описания.

Промпт собирается пятью слоями, и стиль идёт ПОСЛЕДНИМ: сначала модель узнаёт, что
снимаем, и только потом — как это выглядит. Порядок взят из практики съёмки: оператор
сперва выбирает оптику и крупность, грейд накладывают в конце.

    слой 1  оптика      угол обзора и наблюдаемый результат
    слой 2  движение    крупность плана, ход камеры
    слой 3  субъект     что в кадре, где стоит, куда смотрит
    слой 4  свет        схема света, цветовая температура
    слой 5  стиль       художественная манера — в самом конце

Три правила, ради которых это переписано (взяты из разбора производственного архива
полнометражного ИИ-фильма и проверены на нём):

1. **Оптика задаётся углом обзора и НАБЛЮДАЕМЫМ результатом**, а не диафрагмой и ISO.
   Модель училась на подписях к кадрам, а не на метаданных съёмки: «фон растворён в
   тёплую дымку» она понимает, «f/1.4» — нет.
2. **Замок против сползания оптики.** Без явного запрета длиннофокусный кадр к концу
   сцены сам собой становится широкоугольным. Запрет пишется прямо.
3. **Пространство описывается измеримо.** «Рядом», «около», «где-то там» модель толкует
   как хочет; «в метре от машины», «ладонь на капоте» — однозначно. Направление тела и
   направление взгляда задаются ОТДЕЛЬНО: это разные вещи.

    python build_visual_prompt.py --subject "команда за столом смотрит на график" \\
        --role deliver_payload --light golden_hour --style editorial --aspect 16:9

    python build_visual_prompt.py --subject "герой у сгоревшей машины" --content portrait \\
        --fov 29 --blocking "стоит в метре от машины, ладонь на капоте" \\
        --gaze "смотрит на собеседника" --facing "корпус развёрнут к камере вполоборота"

    python build_visual_prompt.py --json shots.json     # пачкой по плану кадров
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
import sys

# --- слой 1: оптика -------------------------------------------------------------------
# Углы обзора вместо фокусных расстояний: фокусное имеет смысл только вместе с размером
# матрицы, а угол обзора — самодостаточен. К каждому — описание наблюдаемого результата.

FOV = {
    "107": ("широкоугольный прямолинейный",
            "107° diagonal field of view, wide rectilinear lens character, camera 0.5 to 0.8 m "
            "from the foreground subject. Immediate foreground looms large, environment spreads "
            "to all frame edges, deep edge-to-edge focus, straight lines stay straight, "
            "no fisheye curve"),
    "84":  ("классический широкий",
            "84° diagonal field of view, classic wide-angle lens character, camera 1 to 1.5 m "
            "from the subject. Natural perspective expansion, foreground body presence feels "
            "larger and closer, environment visible to the frame edges, deep readable spatial "
            "context, architectural lines stay rectilinear"),
    "47":  ("нормальный",
            "47° diagonal field of view, standard normal lens character, camera 3 to 5 m from "
            "the subject, natural human-eye perspective. No obvious distortion, natural face and "
            "body proportions, background readable but not exaggerated"),
    "29":  ("короткий телевик, портретный",
            "29° diagonal field of view, short telephoto portrait lens character, camera 4 to 6 m "
            "from the subject. Close framing achieved through lens reach, not physical proximity. "
            "Subject razor-sharp, background compressed close behind them and dissolved into "
            "creamy bokeh, the subject pops clearly from the environment"),
    "18":  ("классический телевик",
            "18° diagonal field of view, classic telephoto lens character, camera 6 to 8 m from "
            "the subject. Strong background compression, distant elements stacked closer behind "
            "the subject, razor-thin focus on the eyes, foreground and background melt into soft "
            "bokeh, the image feels observed from a distance"),
    "macro": ("макро вблизи",
            "macro lens character, camera 20 to 40 cm from the subject, natural human-eye "
            "perspective on a small object. The subject fills the frame, surface texture and "
            "fine detail are the point of the shot, background falls away immediately behind "
            "the plane of focus, no perspective distortion on the object itself"),
    "8":   ("сверхдлинный, наблюдение",
            "8° diagonal field of view, super-telephoto observation lens character, camera 20 to "
            "25 m from the subject. Extreme background compression flattened into a soft colour "
            "wash, only the subject is sharp. Foreground occlusion is mandatory: blurred objects "
            "occupy the lower 30 to 45 percent of frame as oversized dark bokeh shapes"),
}

# Замок против сползания оптики. Пишется прямо в промпт: без него кадр к концу сцены
# самопроизвольно меняет характер оптики.
ANTI_DRIFT = {
    "tele": "No part of this shot becomes wide-angle or normal-lens coverage. Wider framing is "
            "achieved by the camera being farther away with the same long-lens reach, not by "
            "switching lenses. The background stays compressed and dissolved in every frame.",
    "wide": "No part of this shot becomes telephoto portrait coverage. The environment stays "
            "visible around the subject, the camera remains physically close, and the image keeps "
            "wide-angle spatial expansion with deep readable context.",
    "normal": "No extreme wide distortion, no telephoto compression. The image stays natural, "
              "grounded, and human-eye neutral.",
}

# Тип содержания кадра → уместный угол обзора. Смешивать классы в одном кадре нельзя:
# портрет плюс география плюс макродеталь в одном бите и вызывают сползание оптики.
CONTENT_FOV = {
    "portrait_intimate": "84", "portrait_medium": "29", "portrait_tight": "18",
    "observation": "8", "action": "47", "action_wide": "84",
    "geography": "107",
    # Деталь снимают двумя разными способами, и это разные кадры: макро — камера в
    # десятках сантиметров, длиннофокусная деталь — в метрах. Руки на клавиатуре, экран,
    # предмет на столе — это макро; деталь, выхваченная из сцены издалека, — телевик.
    "detail_close": "macro", "detail": "29", "detail_tight": "18",
}
CONTENT_RU = {
    "portrait_intimate": "лицо крупно, но с обстановкой",
    "portrait_medium": "средний портрет",
    "portrait_tight": "тесный эмоциональный крупный план",
    "observation": "наблюдение издалека",
    "action": "естественное документальное действие",
    "action_wide": "действие в среде",
    "geography": "крупная география места",
    "detail_close": "предмет вблизи: руки, экран, вещь на столе",
    "detail": "деталь, выхваченная издалека",
    "detail_tight": "деталь тесно, издалека",
}

SHOT_SIZE = {
    "extreme_wide": "extreme wide shot, vast environment dwarfing the subject",
    "wide": "wide shot capturing the full scene",
    "medium_wide": "medium-wide shot, subject framed with surroundings",
    "medium": "medium shot from the waist up",
    "medium_close": "medium close-up from the chest up",
    "close_up": "close-up on the face or key detail",
    "extreme_close_up": "extreme close-up on fine texture",
    "over_shoulder": "over-the-shoulder perspective",
    "insert": "insert shot isolating one detail",
    "establishing": "establishing shot that sets the location",
}

MOVEMENT = {
    "static": "locked-off camera, no movement",
    "pan_left": "smooth pan to the left", "pan_right": "smooth pan to the right",
    "tilt_up": "gentle tilt upward", "tilt_down": "gentle tilt downward",
    "dolly_in": "slow dolly pushing in toward the subject",
    "dolly_out": "slow dolly pulling back from the subject",
    "tracking_left": "tracking shot moving left alongside the subject",
    "tracking_right": "tracking shot moving right alongside the subject",
    "crane_up": "crane rising above the scene",
    "crane_down": "crane descending toward the scene",
    "handheld": "handheld camera with natural micro-shake",
    "steadicam": "floating steadicam glide",
    "whip_pan": "fast whip pan with motion blur",
    "orbital": "orbital move circling the subject",
    "zoom_in": "optical zoom tightening on the subject",
    "zoom_out": "optical zoom widening from the subject",
    "rack_focus": "rack focus shifting attention between planes",
}

LIGHTING = {
    "high_key": "bright high-key lighting, soft shadows",
    "low_key": "low-key lighting, deep shadows, single source",
    "natural": "natural daylight",
    "golden_hour": "golden hour sunlight, long warm shadows",
    "blue_hour": "blue hour twilight, cool ambient glow",
    "tungsten_warm": "warm tungsten practicals",
    "neon": "neon signage lighting, saturated colour spill",
    "silhouette": "backlit silhouette against a bright field",
    "rim_lit": "rim light separating subject from background",
    "volumetric": "volumetric shafts of light through haze",
    "overcast_soft": "soft overcast light, no hard shadows",
}

DOF = {
    "shallow": "shallow depth of field, background falls away",
    "medium": "moderate depth of field",
    "deep": "deep focus, foreground and background both sharp",
}

COLOR_TEMP = {"warm": "warm colour temperature", "neutral": "neutral colour balance",
              "cool": "cool colour temperature"}

# Роль кадра в рассказе задаёт умолчания: у доказательства и у призыва разная оптика.
ROLE_DEFAULTS = {
    "establish_context": {"size": "establishing", "move": "static", "dof": "deep",
                          "content": "geography"},
    "introduce_subject": {"size": "medium", "move": "dolly_in", "dof": "shallow",
                          "content": "portrait_medium"},
    "build_tension":     {"size": "medium_close", "move": "dolly_in", "dof": "shallow",
                          "light": "low_key", "content": "portrait_tight"},
    "deliver_payload":   {"size": "close_up", "move": "static", "dof": "shallow",
                          "content": "portrait_tight"},
    "transition":        {"size": "wide", "move": "whip_pan", "dof": "medium",
                          "content": "action_wide"},
    "emotional_beat":    {"size": "close_up", "move": "static", "dof": "shallow",
                          "light": "golden_hour", "content": "portrait_tight"},
    "evidence":          {"size": "insert", "move": "static", "dof": "medium",
                          "content": "detail"},
    "comparison":        {"size": "medium_wide", "move": "static", "dof": "deep",
                          "content": "action"},
    "resolution":        {"size": "wide", "move": "crane_up", "dof": "deep",
                          "content": "geography"},
    "call_to_action":    {"size": "medium", "move": "static", "dof": "medium",
                          "light": "high_key", "content": "portrait_medium"},
}

# Слова, которые модель толкует как хочет. Замена обязательна там, где важно, кто где стоит.
VAGUE = ("рядом", "около", "возле", "где-то", "неподалёку", "поблизости",
         "near", "around", "beside", "somewhere", "nearby", "in the area")

FIRST_FRAME_LOCK = ("The first visible frame already contains all required subjects in their "
                    "correct positions. No empty establishing frame, no delayed reveal.")


def fov_order(k: str) -> tuple:
    """Порядок для показа: от самого широкого к длинному, макро — отдельно в конце."""
    return (1, 0) if not k.isdigit() else (0, -int(k))


def _p(table: dict, key: str | None) -> str | None:
    return table.get(key) if key else None


def lens_class(fov: str) -> str:
    if fov in ("29", "18", "8"):
        return "tele"
    if fov in ("84", "107"):
        return "wide"
    return "normal"     # сюда же макро: искажений перспективы у него нет


def build_prompt(
    subject: str, *,
    role: str | None = None, size: str | None = None, move: str | None = None,
    light: str | None = None, dof: str | None = None, color_temp: str | None = None,
    texture: str | None = None, style: str | None = None, aspect: str | None = None,
    still: bool = False, text_on_image: str | None = None,
    content: str | None = None, fov: str | None = None,
    blocking: str | None = None, gaze: str | None = None, facing: str | None = None,
    first_frame_lock: bool = False, anti_drift: bool = True,
) -> tuple[str, list[str]]:
    """Собрать промпт. Возвращает промпт и список замечаний к постановке."""
    d = ROLE_DEFAULTS.get(role or "", {})
    size = size or d.get("size")
    move = move or d.get("move")
    light = light or d.get("light")
    dof = dof or d.get("dof")
    content = content or d.get("content")
    fov = fov or CONTENT_FOV.get(content or "", "47")

    notes: list[str] = []
    parts: list[str] = []

    # Слой 1 — оптика: угол обзора и наблюдаемый результат
    _, lens_text = FOV.get(fov, FOV["47"])
    cam = [lens_text]
    p = _p(DOF, dof)
    if p:
        cam.append(p)
    parts.append(". ".join(cam))

    # Слой 2 — крупность и ход камеры. Для статичной картинки ход не пишем: модель всё
    # равно рисует один кадр, а слово «наезд» только зашумляет.
    frame = []
    p = _p(SHOT_SIZE, size)
    if p:
        frame.append(p)
    if not still:
        p = _p(MOVEMENT, move)
        if p:
            frame.append(p)
    if frame:
        parts.append(", ".join(frame))

    # Слой 3 — субъект и его положение в пространстве
    subj = subject.strip()
    if texture:
        subj = f"{subj}, {texture}"
    parts.append(subj)

    # Оптика и содержание должны говорить об одном. Если кадр объявлен деталью, а в
    # описании перечислено несколько объектов или планов, модель выберет описание и
    # снимет сцену — оптика останется словами. Проверено прогоном: «руки на клавиатуре
    # и на втором экране страница» при макро-оптике дали обычный средний план.
    if content in ("detail_close", "detail", "detail_tight"):
        # Одной запятой достаточно: деталь описывается одним оборотом («пальцы на
        # клавише»), а запятая почти всегда вводит второй объект или второй план.
        parts_count = subj.count(",") + subj.lower().count(" и ") + subj.count(";")
        if parts_count >= 1:
            notes.append("кадр объявлен деталью, но в описании несколько объектов — "
                         "модель снимет сцену, а не деталь; оставь один предмет или "
                         "смени тип содержания")

    spatial = []
    if blocking:
        spatial.append(blocking.strip())
        if any(w in blocking.lower() for w in VAGUE):
            notes.append("в описании положения есть расплывчатые слова — замени на измеримое "
                         "(«в метре от машины», «ладонь на капоте»)")
    # Направление тела и направление взгляда — разные вещи, пишутся отдельно.
    if facing:
        spatial.append(facing.strip())
    if gaze:
        spatial.append(gaze.strip())
    if spatial:
        # Каждое утверждение о положении — отдельное предложение с заглавной: слитный
        # поток модель читает как одно размытое описание, а нам нужны раздельные факты.
        parts.append(". ".join(s[0].upper() + s[1:] if s else s for s in spatial))
    elif not still and size in ("medium", "medium_close", "close_up", "over_shoulder"):
        notes.append("для кадра с людьми не задано положение и направление взгляда — "
                     "модель расставит их произвольно")

    # Слой 4 — свет
    lights = []
    p = _p(LIGHTING, light)
    if p:
        lights.append(p)
    p = _p(COLOR_TEMP, color_temp)
    if p:
        lights.append(p)
    if lights:
        parts.append(", ".join(lights))

    prompt = ". ".join(s[0].upper() + s[1:] if s else s for s in parts if s) + "."

    if first_frame_lock:
        prompt += " " + FIRST_FRAME_LOCK
    if anti_drift and not still:
        prompt += " " + ANTI_DRIFT[lens_class(fov)]

    # Точный текст просим отдельным предложением и в кавычках — внутри описания сцены
    # модель растворяет его и рисует похожую по смыслу надпись вместо нужной.
    if text_on_image:
        prompt += f' Render the exact text "{text_on_image}" clearly and legibly.'

    # Слой 5 — стиль ПОСЛЕДНИМ. Вынесенный вперёд, он подминает всё: кадры выходят на
    # одно лицо, различается только подпись.
    if style:
        prompt += f" Style: {style}."
    if aspect:
        prompt += f" Aspect ratio {aspect}."
    return prompt, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subject", help="что в кадре, своими словами")
    ap.add_argument("--role", choices=sorted(ROLE_DEFAULTS), help="роль в рассказе — задаёт умолчания")
    ap.add_argument("--content", choices=sorted(CONTENT_FOV), help="тип содержания — задаёт оптику")
    ap.add_argument("--fov", choices=sorted(FOV, key=fov_order), help="угол обзора вручную")
    ap.add_argument("--size", choices=sorted(SHOT_SIZE))
    ap.add_argument("--move", choices=sorted(MOVEMENT))
    ap.add_argument("--light", choices=sorted(LIGHTING))
    ap.add_argument("--dof", choices=sorted(DOF))
    ap.add_argument("--color-temp", choices=sorted(COLOR_TEMP))
    ap.add_argument("--texture", help="фактура: плёночное зерно, матовый пластик…")
    ap.add_argument("--style", help="художественная манера")
    ap.add_argument("--aspect", help="16:9, 9:16, 1:1")
    ap.add_argument("--still", action="store_true", help="статичная картинка: ход камеры не писать")
    ap.add_argument("--text", dest="text_on_image", help="точный текст в кадре")
    ap.add_argument("--blocking", help="где кто стоит — измеримо, а не «рядом»")
    ap.add_argument("--gaze", help="куда направлен взгляд")
    ap.add_argument("--facing", help="куда развёрнут корпус")
    ap.add_argument("--first-frame-lock", action="store_true",
                    help="все субъекты уже в первом кадре, без пустого вступления")
    ap.add_argument("--no-anti-drift", action="store_true",
                    help="снять замок против сползания оптики")
    ap.add_argument("--json", help="файл с массивом кадров — собрать пачкой")
    ap.add_argument("--lenses", action="store_true", help="показать банк углов обзора")
    args = ap.parse_args()

    if args.lenses:
        for f, (ru, text) in sorted(FOV.items(), key=lambda x: fov_order(x[0])):
            print(f"  {f:>5}{'°' if f.isdigit() else ' '}  {ru}")
            print(f"        {text[:150]}…")
        print("\n  тип содержания → угол:")
        for c, f in CONTENT_FOV.items():
            print(f"    {c:16s} {f:>5}{'°' if f.isdigit() else ' '}   {CONTENT_RU[c]}")
        return 0

    if args.json:
        data = json.loads(pathlib.Path(args.json).read_text(encoding="utf-8"))
        shots = data if isinstance(data, list) else data.get("shots") or data.get("beats") or []
        common_style = data.get("style") if isinstance(data, dict) else None
        common_aspect = data.get("aspect") if isinstance(data, dict) else None
        out = []
        for i, s in enumerate(shots, 1):
            if not s.get("subject"):
                print(f"  кадр {i}: нет поля subject — пропускаю", file=sys.stderr)
                continue
            prompt, notes = build_prompt(
                s["subject"], role=s.get("role"), size=s.get("size"), move=s.get("move"),
                light=s.get("light"), dof=s.get("dof"), color_temp=s.get("color_temp"),
                texture=s.get("texture"), style=s.get("style") or common_style,
                aspect=s.get("aspect") or common_aspect, still=bool(s.get("still")),
                text_on_image=s.get("text_on_screen") or s.get("text"),
                content=s.get("content"), fov=s.get("fov"), blocking=s.get("blocking"),
                gaze=s.get("gaze"), facing=s.get("facing"),
                first_frame_lock=bool(s.get("first_frame_lock")))
            rec = {"id": s.get("id") or f"shot_{i:02d}", "prompt": prompt}
            if notes:
                rec["notes"] = notes
                for n in notes:
                    print(f"  {rec['id']}: {n}", file=sys.stderr)
            out.append(rec)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if not args.subject:
        ap.error("нужен --subject, --json или --lenses")

    prompt, notes = build_prompt(
        args.subject, role=args.role, size=args.size, move=args.move, light=args.light,
        dof=args.dof, color_temp=args.color_temp, texture=args.texture, style=args.style,
        aspect=args.aspect, still=args.still, text_on_image=args.text_on_image,
        content=args.content, fov=args.fov, blocking=args.blocking, gaze=args.gaze,
        facing=args.facing, first_frame_lock=args.first_frame_lock,
        anti_drift=not args.no_anti_drift)
    print(prompt)
    for n in notes:
        print(f"\n  ⚠ {n}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
