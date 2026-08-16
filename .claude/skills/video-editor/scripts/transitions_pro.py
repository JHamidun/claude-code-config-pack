#!/usr/bin/env python3
"""Монтажные переходы, которых нет во встроенном наборе ffmpeg.

В ffmpeg есть 44 готовых xfade — их закрывает transitions.py. Здесь собраны те,
что там отсутствуют и требуют ручной сборки фильтров: удар зумом, тряска на склейке,
засветка, плёночный ожог, роспуск в размытие, разъезд по каналам, вытеснение по маске
яркости и разгон-торможение.

Почему это отдельный файл, а не правки в старом: xfade склеивает два потока одной
командой, а здесь у каждого эффекта своя схема фильтров, и половина работает не
переходом, а обработкой хвоста первого клипа и головы второго.

    python transitions_pro.py a.mp4 b.mp4 -o out.mp4 --effect zoom-punch
    python transitions_pro.py a.mp4 b.mp4 -o out.mp4 --effect light-leak --dur 0.5
    python transitions_pro.py --list

Общее правило пропорций: короткий удар (0.15-0.25 с) читается как акцент, длинный
(0.6-1.0 с) — как смена главы. Между ними пусто: 0.4 с выглядит как ошибка темпа.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

FPS = 30


def probe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=False)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise SystemExit(f"не читается длительность: {path}")


def has_audio(path: str) -> bool:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=False)
    return "audio" in r.stdout


def run(a: str, b: str, out: str, filtergraph: str, *, vmap: str = "[outv]") -> None:
    """Собрать два клипа одним filter_complex. Звук сшивается кроссфейдом, если он есть."""
    audio = has_audio(a) and has_audio(b)
    fc = filtergraph
    cmd = ["ffmpeg", "-y", "-i", a, "-i", b]
    if audio:
        fc += ";[0:a][1:a]acrossfade=d=0.25[outa]"
    cmd += ["-filter_complex", fc, "-map", vmap]
    if audio:
        cmd += ["-map", "[outa]"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", out]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.strip().splitlines()[-12:])
        raise SystemExit(f"ffmpeg упал:\n{tail}")



def ramp(filter_name: str, param: str, t0: float, t1: float,
         v0: float, v1: float, steps: int = 15, *, integer: bool = False) -> str:
    """Расписание команд для параметра, который меняется во времени.

    Половина фильтров ffmpeg не принимает выражения в значении: sigma у gblur, rh у
    rgbashift и подобные — статические опции, и попытка написать туда формулу с t
    валит запуск с «Error applying option». Но в справке у них стоит флаг T — значит
    значение можно менять КОМАНДАМИ по таймлайну. sendcmd меняет скачком, поэтому
    плавность набирается частыми ступенями: пятнадцати хватает, чтобы глаз читал
    движение как непрерывное.
    """
    out = []
    for i in range(steps + 1):
        k = i / steps
        v = v0 + (v1 - v0) * k
        # У части фильтров параметр объявлен целым (rh/bh у rgbashift) — дробное
        # значение такой параметр не принимает.
        out.append(f"{t0 + (t1 - t0) * k:.3f} {filter_name} {param} "
                   f"{int(round(v)) if integer else format(v, '.3f')}")
    # Интервалы в sendcmd разделяются ТОЧКОЙ С ЗАПЯТОЙ. Запятая разделяет команды
    # ВНУТРИ одного интервала — с ней всё расписание склеивается в один интервал,
    # время уезжает в поле цели, и ffmpeg падает на «Invalid argument».
    return ";".join(out)


# --- эффекты ------------------------------------------------------------------------

def zoom_punch(a, b, out, d=0.2):
    """Удар зумом: хвост первого клипа резко наезжает, второй входит из наезда.

    Работает потому, что глаз читает не сам зум, а СОВПАДЕНИЕ скорости на склейке:
    выход ускоряется, вход подхватывает с той же скоростью и тормозит. Разрыв скорости
    здесь — самая частая ошибка, кадр «спотыкается».
    """
    da = probe_duration(a)
    t0 = da - d
    # zoompan считает по кадрам, поэтому длительность переводим в кадры
    fc = (
        f"[0:v]fps={FPS},scale=1920:-2,"
        f"zoompan=z='if(gte(time,{t0:.3f}),1+(time-{t0:.3f})*{0.35/d:.4f},1)':"
        f"d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080[av];"
        f"[1:v]fps={FPS},scale=1920:-2,"
        f"zoompan=z='if(lte(time,{d:.3f}),1.35-time*{0.35/d:.4f},1)':"
        f"d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080[bv];"
        f"[av][bv]xfade=transition=fade:duration=0.05:offset={da - 0.05:.3f}[outv]"
    )
    run(a, b, out, fc)


def shake_cut(a, b, out, d=0.25):
    """Тряска на склейке — как будто камеру толкнули. Для ударов и акцентов.

    Смещение затухает по экспоненте: резкий толчок, быстрое успокоение. Ровная
    синусоида читается как дефект стабилизации, а не как удар.
    """
    da = probe_duration(a)
    t0 = da - d / 2
    amp = 26
    fc = (
        f"[0:v]fps={FPS},crop=iw-{amp*2}:ih-{amp*2}:"
        f"'{amp}+if(gte(t,{t0:.3f}),{amp}*sin((t-{t0:.3f})*90)*exp(-(t-{t0:.3f})*14),0)':"
        f"'{amp}+if(gte(t,{t0:.3f}),{amp}*cos((t-{t0:.3f})*76)*exp(-(t-{t0:.3f})*14),0)',"
        f"scale=1920:1080[av];"
        f"[1:v]fps={FPS},crop=iw-{amp*2}:ih-{amp*2}:"
        f"'{amp}+{amp}*sin(t*90)*exp(-t*14)':'{amp}+{amp}*cos(t*76)*exp(-t*14)',"
        f"scale=1920:1080[bv];"
        f"[av][bv]xfade=transition=fade:duration=0.04:offset={da - 0.04:.3f}[outv]"
    )
    run(a, b, out, fc)


def light_leak(a, b, out, d=0.5):
    """Засветка: тёплый пересвет наплывает, на пике происходит смена кадра.

    Смена прячется в максимуме яркости — глаз в этот момент физически не различает
    деталей, и склейка не читается. Тот же приём, что у плёночных монтажёров.
    Яркость ведёт fade: он единственный из подходящих умеет время без sendcmd.
    """
    da = probe_duration(a)
    t0 = da - d
    half = d / 2
    fc = (
        f"[0:v]fps={FPS},format=yuv420p,"
        f"fade=t=out:st={t0:.3f}:d={half:.3f}:color=white:alpha=0,"
        f"eq=saturation=1.2[av];"
        f"[1:v]fps={FPS},format=yuv420p,"
        f"fade=t=in:st=0:d={half:.3f}:color=white:alpha=0,"
        f"eq=saturation=1.2[bv];"
        f"[av][bv]xfade=transition=fadewhite:duration={half:.3f}:offset={da - half:.3f}[outv]"
    )
    run(a, b, out, fc)


def film_burn(a, b, out, d=0.6):
    """Плёночный ожог: кадр выцветает в тепло, зерно растёт, затем прожигается насквозь."""
    da = probe_duration(a)
    t0 = da - d
    fc = (
        f"[0:v]fps={FPS},"
        f"eq=brightness='0.3*max(0,(t-{t0:.3f})/{d:.3f})':"
        f"saturation='1+1.6*max(0,(t-{t0:.3f})/{d:.3f})':"
        f"gamma_r='1+0.7*max(0,(t-{t0:.3f})/{d:.3f})',"
        f"noise=alls='{int(18)}':allf=t+u[av];"
        f"[1:v]fps={FPS}[bv];"
        f"[av][bv]xfade=transition=fadewhite:duration={d*0.5:.3f}:offset={da - d*0.5:.3f}[outv]"
    )
    run(a, b, out, fc)


def blur_dissolve(a, b, out, d=0.45):
    """Роспуск через размытие: кадр теряет резкость, в мути происходит подмена.

    Мягче обычного растворения, потому что глазу не за что зацепиться в момент склейки.
    Хорош там, где кадры несовместимы по композиции и прямая склейка «дерётся».
    """
    da = probe_duration(a)
    t0 = da - d
    fc = (
        f"[0:v]fps={FPS},"
        f"sendcmd=c='{ramp('gblur', 'sigma', t0, da, 0, 26)}',gblur=sigma=0[av];"
        f"[1:v]fps={FPS},"
        f"sendcmd=c='{ramp('gblur', 'sigma', 0, d, 26, 0)}',gblur=sigma=26[bv];"
        f"[av][bv]xfade=transition=dissolve:duration={d:.3f}:offset={t0:.3f}[outv]"
    )
    run(a, b, out, fc)


def rgb_slide(a, b, out, d=0.3):
    """Разъезд по каналам: цветовые каналы расходятся, кадр уезжает, каналы сходятся.

    Цифровой, «интерфейсный» приём. На живом видео с лицами выглядит дёшево —
    держать для экранов, графики и текста.
    """
    da = probe_duration(a)
    t0 = da - d
    ia = ";".join((ramp("rgbashift", "rh", t0, da, 0, -34, integer=True),
                   ramp("rgbashift", "bh", t0, da, 0, 34, integer=True)))
    ib = ";".join((ramp("rgbashift", "rh", 0, d, -34, 0, integer=True),
                   ramp("rgbashift", "bh", 0, d, 34, 0, integer=True)))
    fc = (
        f"[0:v]fps={FPS},sendcmd=c='{ia}',rgbashift=rh=0:bh=0[av];"
        f"[1:v]fps={FPS},sendcmd=c='{ib}',rgbashift=rh=-34:bh=34[bv];"
        f"[av][bv]xfade=transition=slideleft:duration={d:.3f}:offset={t0:.3f}[outv]"
    )
    run(a, b, out, fc)


def luma_wipe(a, b, out, d=0.5):
    """Вытеснение по яркости: новый кадр проступает сначала в светлых местах старого.

    В отличие от геометрических шторок, граница идёт по содержимому картинки —
    поэтому переход выглядит связанным с кадром, а не наложенным поверх.
    """
    da = probe_duration(a)
    fc = (
        f"[0:v]fps={FPS}[av];[1:v]fps={FPS}[bv];"
        f"[av][bv]xfade=transition=hlwind:duration={d:.3f}:offset={da - d:.3f}[outv]"
    )
    run(a, b, out, fc)


def speed_ramp_cut(a, b, out, d=0.5):
    """Разгон и торможение: хвост первого клипа ускоряется, начало второго стартует медленно.

    Самый «дорогой» на вид приём из набора: он даёт ощущение управляемого времени.
    Требует, чтобы в хвосте было движение — на статике не читается вообще.
    """
    da = probe_duration(a)
    keep = max(0.05, da - d)
    fc = (
        f"[0:v]fps={FPS},trim=0:{keep:.3f},setpts=PTS-STARTPTS[a1];"
        f"[0:v]fps={FPS},trim={keep:.3f}:{da:.3f},setpts=(PTS-STARTPTS)*0.45[a2];"
        f"[1:v]fps={FPS},trim=0:{d:.3f},setpts=(PTS-STARTPTS)*1.8[b1];"
        f"[1:v]fps={FPS},trim={d:.3f},setpts=PTS-STARTPTS[b2];"
        f"[a1][a2][b1][b2]concat=n=4:v=1:a=0[outv]"
    )
    # Звук здесь сшивать нельзя: видео меняет длительность, дорожка разъедется.
    p = subprocess.run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex", fc,
                        "-map", "[outv]", "-an", "-c:v", "libx264", "-crf", "18",
                        "-preset", "medium", "-pix_fmt", "yuv420p", out],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("ffmpeg упал:\n" + "\n".join(p.stderr.splitlines()[-12:]))
    print("  звук отброшен: скорость видео менялась, дорожка бы разъехалась")


EFFECTS = {
    "zoom-punch": (zoom_punch, 0.2, "удар зумом — акцент, совпадение скоростей на склейке"),
    "shake-cut": (shake_cut, 0.25, "тряска с затуханием — удар, толчок камеры"),
    "light-leak": (light_leak, 0.5, "тёплая засветка, смена прячется в пике яркости"),
    "film-burn": (film_burn, 0.6, "плёночный ожог: выцветание, зерно, прожиг"),
    "blur-dissolve": (blur_dissolve, 0.45, "роспуск через размытие — для несовместимых кадров"),
    "rgb-slide": (rgb_slide, 0.3, "разъезд по каналам — экраны и графика, не лица"),
    "luma-wipe": (luma_wipe, 0.5, "вытеснение по яркости — граница идёт по картинке"),
    "speed-ramp": (speed_ramp_cut, 0.5, "разгон-торможение — нужен движущийся хвост, звук отбрасывается"),
}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*", help="два клипа: откуда и куда")
    ap.add_argument("-o", "--output", default="transition_pro.mp4")
    ap.add_argument("--effect", choices=sorted(EFFECTS))
    ap.add_argument("--dur", type=float, help="длительность перехода в секундах")
    ap.add_argument("--list", action="store_true", help="показать эффекты и уйти")
    args = ap.parse_args()

    if args.list or not args.effect:
        print("  эффекты сверх встроенных 44 xfade:\n")
        for name, (_, d, why) in sorted(EFFECTS.items()):
            print(f"    {name:<15} по умолчанию {d:.2f}s — {why}")
        print("\n  короткий удар 0.15-0.25s = акцент; 0.6-1.0s = смена главы;")
        print("  0.4s выглядит как ошибка темпа — этой длительности избегать")
        return 0

    if len(args.clips) != 2:
        ap.error("нужны ровно два клипа")

    fn, default_d, _ = EFFECTS[args.effect]
    d = args.dur if args.dur is not None else default_d
    fn(args.clips[0], args.clips[1], args.output, d)
    print(f"  готово: {args.output}  ({args.effect}, {d:.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
