# -*- coding: utf-8 -*-
"""Цифровые бейджи под Accredible / Open Badges: картинка PNG + файлы массовой выдачи.

Что делает
----------
1. Рисует КАРТИНКУ бейджа (HTML → Playwright → PNG) в двух темах:
     company — сине-фиолетовый градиент корпоративных сертификатов (#3B3B95 → #5050C7 → #6464F8),
              круглый знак из assets/brand/company_mark.svg, словесный знак —
              assets/brand/company_wordmark.svg (обе — заглушки: замените файлы
              своими логотипами);
     vibe   — тёмный #14151C, терракота #CC7357, голубой #4DABF7, кремовый #F6F4EF,
              знак из assets/brand/vibe_mark.svg (заглушка), подпись рядом со знаком —
              из --brand-name / --brand-tag / --brand-by; шрифты Oswald (капс) + Manrope.
   На картинке НЕТ фамилии получателя: по правилам Accredible картинка бейджа общая
   для всех получателей группы, а имя, почта и дата живут в метаданных credential
   (см. references/accredible.md, раздел «Почему на картинке нет имени»).

2. Собирает CSV для массовой выдачи в кабинете Accredible (Credentials → Create
   Credentials → Upload Spreadsheet). Колонки — ровно те, что Accredible называет
   обязательными: Recipient Name, Recipient Email, Issue Date (+ Group ID для
   выдачи в несколько групп). Дата — в формате YYYY/MM/DD, один из трёх, которые
   принимает импорт; при загрузке этот формат нужно выбрать в выпадашке.

3. По желанию — JSON-пачки для POST /v2/credentials/bulk_create (до 30 штук в запросе).

Требования Accredible к картинке (help.accredible.com, «How Do I Design a Digital
Badge?», 29.05.2024): PNG, квадрат, не меньше 256×256, оптимально 400×400,
прозрачный фон рекомендуется, слишком большие файлы тормозят у получателей.
Поэтому дефолт — 400×400, прозрачный фон за кругом.

Шрифты — файлы assets/fonts/*.woff2 (Google Fonts, SIL OFL, латиница + кириллица),
встроены в HTML как base64. Системные Inter/Manrope бывают битыми (на машине автора
это были файлы из одних переводов строки), Chromium молча подставляет другой шрифт —
здесь после рендера проверяется, что нужное семейство реально загрузилось, иначе
в stderr будет «ШРИФТ НЕ ПРИМЕНИЛСЯ».

Примеры
-------
  python make_badges.py --theme company --title "Искусственный интеллект в работе" \
      --level "Практикум" --year 2026 --out badge_company_ai.png
  python make_badges.py --theme vibe --title "Вайбкодинг: старт" --level "Уровень 1" \
      --year 2026 --brand-name Your --brand-tag School --brand-by "by Your Name" \
      --out badge_vibe_start.png
  python make_badges.py --samples                # четыре образца + контактный лист
                                                 # в ./badge_samples/ (рядом с вами, не в навыке)
  python make_badges.py --roster roster.txt --csv --out roster_accredible.csv \
      --issue-date 2026-09-12 [--group-id 123456]
  python make_badges.py --roster roster.txt --api-json --group-id 123456 --out batch.json

Формат ростера: по строке на человека, «ФИО;почта» (разделитель ; , или таб),
строки с # и без почты пропускаются. Можно .csv с шапкой — шапка распознаётся
по отсутствию @ во втором поле.
"""
import sys, re, csv, json, html, math, base64, random, argparse, tempfile
import datetime as dt
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
BRAND = SKILL / "assets" / "brand"
FONTS = SKILL / "assets" / "fonts"
# Образцы и бейджи по умолчанию — в текущей папке, а не внутри навыка: каталог
# навыка может быть только для чтения (плагин, кэш) и затирается при обновлении.
SAMPLES = Path.cwd() / "badge_samples"

SIZE_DEFAULT = 400   # оптимум по Accredible
SIZE_MIN = 256       # минимум по Accredible
BULK_BATCH = 30      # лимит /v2/credentials/bulk_create

THEMES = ("company", "vibe")

# ── шрифты ───────────────────────────────────────────────────────────────────
# Google Fonts отдаёт вариативные woff2, у каждого семейства два субсета.
UNICODE = {
    "lat": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, "
           "U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, "
           "U+2212, U+2215, U+FEFF, U+FFFD",
    "cyr": "U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116",
}
FONT_WEIGHTS = {"Oswald": "200 700", "Manrope": "200 800", "Inter": "100 900"}


def font_css(*families):
    out, missing = [], []
    for fam in families:
        got = False
        for sub, rng in UNICODE.items():
            p = FONTS / f"{fam}-{sub}.woff2"
            if not p.exists():
                continue
            got = True
            b64 = base64.b64encode(p.read_bytes()).decode()
            out.append(
                f"@font-face{{font-family:'{fam}';font-style:normal;"
                f"font-weight:{FONT_WEIGHTS.get(fam, '100 900')};font-display:block;"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng};}}")
        if not got:
            missing.append(fam)
    if missing:
        sys.stderr.write(f"⚠ нет файлов шрифтов в {FONTS}: {', '.join(missing)} — "
                         "Chromium подставит системный\n")
    return "\n".join(out)


# ── логотипы ─────────────────────────────────────────────────────────────────
def _svg_root(svg, cls):
    """Снять width/height ТОЛЬКО с корневого <svg>, добавить класс.
    Внутри файлов есть <rect width=…> в clipPath — их трогать нельзя."""
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    m = re.search(r"<svg\b[^>]*>", svg)
    tag = re.sub(r'\s(?:width|height)="[^"]*"', "", m.group(0))
    tag = tag.replace("<svg", f'<svg class="{cls}" preserveAspectRatio="xMidYMid meet"', 1)
    return svg[:m.start()] + tag + svg[m.end():]


def svg_logo(name, cls, recolor=None):
    """Родной SVG из assets/brand с перекраской заливок под фон.
    recolor: {"black": "#FFFFFF"} — чёрная словесная часть пропадает на тёмном."""
    p = BRAND / name
    if not p.exists():
        sys.stderr.write(f"⚠ нет логотипа {p}\n")
        return ""
    svg = p.read_text(encoding="utf-8")
    for src, dst in (recolor or {}).items():
        svg = re.sub(rf'fill="{re.escape(src)}"', f'fill="{dst}"', svg, flags=re.I)
    return _svg_root(svg, cls)


def company_mark(blob="#FFFFFF", letter="#4747B4"):
    """Круглый знак из assets/brand/company_mark.svg — только он, без словесной
    части. В мелком круге длинный wordmark превращается в кашу, а простой знак
    читается и в 64 px. Правило файла: первый <path> — фон знака, остальные —
    рисунок поверх. Фон красим в белый, рисунок — в цвет середины градиента,
    чтобы знак не сливался с фоном бейджа."""
    p = BRAND / "company_mark.svg"
    if not p.exists():
        sys.stderr.write(f"⚠ нет логотипа {p}\n")
        return ""
    svg = p.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', svg)
    paths = re.findall(r"<path\b[^>]*?/>", svg, re.S)
    if not vb or not paths:
        sys.stderr.write(f"⚠ {p.name}: нужны viewBox и хотя бы один <path .../>\n")
        return ""
    body = []
    for k, tag in enumerate(paths):
        color = blob if k == 0 else letter
        tag = re.sub(r'\sfill="[^"]*"', "", tag)            # старую заливку убираем
        body.append(tag.replace("<path", f'<path fill="{color}"', 1))
    return (f'<svg class="mark" viewBox="{vb.group(1)}" preserveAspectRatio="xMidYMid meet" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(body)}</svg>')


# ── вёрстка ──────────────────────────────────────────────────────────────────
# Все размеры — доли стороны квадрата var(--s), чтобы 256/400/600 рисовались одинаково.
BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:var(--s);height:var(--s);background:transparent;overflow:hidden;
  -webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
.badge{position:absolute;inset:0;border-radius:50%;overflow:hidden}
.edge,.ring{position:absolute;border-radius:50%;pointer-events:none}
.mark-wrap{position:absolute;left:50%;transform:translateX(-50%);display:flex;
  align-items:center;justify-content:center}
.mark-wrap svg,.mark-wrap .mark{width:100%;height:100%;display:block}
.title{position:absolute;display:flex;align-items:center;justify-content:center;
  text-align:center;overflow:hidden}
.title span{display:block;max-width:100%;hyphens:none;overflow-wrap:normal;word-break:normal}
.level{position:absolute;left:15%;right:15%;display:flex;justify-content:center}
.level span{display:inline-block;white-space:nowrap}
.foot{position:absolute;left:0;right:0;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start}
.foot svg{display:block}
"""

def vibe_particles_svg(seed=11, n=210):
    """Фон бейджа: та же россыпь треугольников, что на сертификате (themes/vibe.py).

    Плоский чёрный круг выглядел пустым. Здесь координаты — проценты стороны
    (viewBox 0 0 100 100), чтобы фон одинаково работал на 256, 400 и 600 px.
    Центральная полоса (где имя программы и пилюля уровня) разрежена: частицы
    там оставлены редкие и бледные, иначе текст теряет контраст.
    """
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r = 47 * (rnd.random() ** 0.62)          # гуще к краю круга
        x, y = 50 + r * math.cos(a), 50 + r * math.sin(a)
        in_text = 12 <= x <= 88 and 33 <= y <= 72   # зона заголовка и пилюли
        if in_text and rnd.random() < 0.82:
            continue
        s = 0.5 + rnd.random() ** 1.7 * 2.1
        op = (0.07 + 0.26 * rnd.random()) * (0.45 if in_text else 1.0)
        u = rnd.random()
        color = "#CC7357" if u < 0.10 else ("#F6F4EF" if u < 0.42 else "#4DABF7")
        pts = []
        ang = rnd.uniform(0, 2 * math.pi)
        for k in range(3):
            t = ang + k * 2 * math.pi / 3
            pts.append(f"{x + s * math.cos(t):.2f},{y + s * math.sin(t):.2f}")
        pts = " ".join(pts)
        if rnd.random() < 0.42:                   # часть — контуром, как на листе
            out.append(f'<polygon points="{pts}" fill="none" stroke="{color}" '
                       f'stroke-width=".22" opacity="{op:.2f}"/>')
        else:
            out.append(f'<polygon points="{pts}" fill="{color}" opacity="{op:.2f}"/>')
    return ('<svg class="particles" viewBox="0 0 100 100" preserveAspectRatio="none">'
            + "".join(out) + "</svg>")


THEME_CSS = {
    # Светлый сине-фиолетовый градиент сверху вниз — тот же, что на сертификате.
    "company": """
.badge{background:linear-gradient(180deg,#3B3B95 0%,#4646B0 30%,#5050C7 55%,#5B5BE0 78%,#6464F8 100%)}
.edge{inset:0;border:calc(var(--s)*0.006) solid #2C2C7C}
.ring{inset:calc(var(--s)*0.042);border:calc(var(--s)*0.006) solid rgba(255,255,255,.34)}
.mark-wrap{top:calc(var(--s)*0.135);width:calc(var(--s)*0.20);height:calc(var(--s)*0.20)}
.title{left:calc(var(--s)*0.16);right:calc(var(--s)*0.16);top:calc(var(--s)*0.365);
  height:calc(var(--s)*0.26);font-family:'Inter',sans-serif;font-weight:600;
  color:#FFFFFF;letter-spacing:-0.012em}
.title span{font-size:calc(var(--s)*0.082);line-height:1.12}
.level{top:calc(var(--s)*0.648)}
.level span{font-family:'Inter',sans-serif;font-weight:600;font-size:calc(var(--s)*0.038);
  line-height:1;letter-spacing:.11em;text-transform:uppercase;color:#FFFFFF;
  padding:.5em 1.05em;border:calc(var(--s)*0.005) solid rgba(255,255,255,.66);border-radius:999px}
.foot{top:calc(var(--s)*0.775)}
.foot .wordmark{width:calc(var(--s)*0.40);height:auto}
.foot .year{margin-top:calc(var(--s)*0.018);font-family:'Inter',sans-serif;font-weight:500;
  font-size:calc(var(--s)*0.036);line-height:1;letter-spacing:.06em;color:rgba(255,255,255,.85)}
""",
    # Тёмная карточка школы или курса: терракотовое кольцо, кремовый капс Oswald.
    # Фон не плоский: россыпь треугольников и мягкое свечение снизу-справа —
    # тот же приём, что на сертификате (слой .decor темы vibe).
    "vibe": """
.badge{background:#14151C}
.particles{position:absolute;inset:0;width:100%;height:100%;display:block}
.glow{position:absolute;left:32%;top:40%;width:76%;height:76%;border-radius:50%;
  background:radial-gradient(closest-side,rgba(41,169,255,.16),rgba(41,169,255,.05) 55%,rgba(41,169,255,0));
  pointer-events:none}
.edge{inset:0;border:calc(var(--s)*0.022) solid #CC7357}
.ring{inset:calc(var(--s)*0.058);border:calc(var(--s)*0.004) solid rgba(246,244,239,.18)}
.mark-wrap{top:calc(var(--s)*0.135);width:calc(var(--s)*0.215);height:calc(var(--s)*0.20)}
.title{left:calc(var(--s)*0.16);right:calc(var(--s)*0.16);top:calc(var(--s)*0.365);
  height:calc(var(--s)*0.26);font-family:'Oswald',sans-serif;font-weight:600;
  text-transform:uppercase;color:#F6F4EF;letter-spacing:.045em}
.title span{font-size:calc(var(--s)*0.092);line-height:1.06}
.level{top:calc(var(--s)*0.648)}
.level span{font-family:'Manrope',sans-serif;font-weight:700;font-size:calc(var(--s)*0.037);
  line-height:1;letter-spacing:.15em;text-transform:uppercase;color:#4DABF7;
  padding:.5em 1.05em;border:calc(var(--s)*0.005) solid rgba(41,169,255,.6);border-radius:999px}
.foot{top:calc(var(--s)*0.772)}
/* Подвал — логотип целиком: знак, рядом крупное название и мелкое моно-слово
   (brand.name и brand.tag), ниже строка «by …» (brand.by) и год. Название
   вразрядку и знак рядом с годом читались как «H 2026» и смысла не несли. */
.foot .logo{display:flex;align-items:center;justify-content:center}
.foot .logo .vmark{width:calc(var(--s)*0.072);height:calc(var(--s)*0.072);display:block}
.foot .logo .wm{margin-left:calc(var(--s)*0.006);display:flex;flex-direction:column;
  justify-content:center}
.foot .logo .wm1{font-family:'Oswald',sans-serif;font-weight:700;
  font-size:calc(var(--s)*0.052);line-height:1;color:#F6F4EF;letter-spacing:.01em;
  display:flex;align-items:baseline}
.foot .logo .wm-ac{font-family:'JetBrains Mono',monospace;font-weight:500;
  font-size:calc(var(--s)*0.028);line-height:1;color:#F6F4EF;
  margin-left:calc(var(--s)*0.012);letter-spacing:.04em}
.foot .logo .wm2{font-family:'JetBrains Mono',monospace;font-weight:400;
  font-size:calc(var(--s)*0.028);line-height:1;color:rgba(246,244,239,.66);
  margin-top:calc(var(--s)*0.010);display:flex;align-items:baseline;letter-spacing:.04em}
.foot .logo .wm2 .year{margin-left:calc(var(--s)*0.026);color:rgba(246,244,239,.5)}
.foot .row{display:flex;align-items:center;gap:calc(var(--s)*0.02);margin-top:calc(var(--s)*0.028)}
.foot .row svg{width:calc(var(--s)*0.058);height:calc(var(--s)*0.056)}
.foot .year{font-family:'Manrope',sans-serif;font-weight:600;font-size:calc(var(--s)*0.034);
  line-height:1;letter-spacing:.1em;color:rgba(246,244,239,.72);text-transform:uppercase}
""",
}

# Подгон кегля: заголовок ужимается, пока не влезет в свой блок не более чем
# в maxLines строк и ни одно слово не вылезет за ширину. Итоговый кегль пишется
# в data-fs — Python читает его и предупреждает, если упёрлись в минимум.
FIT_JS = """
window.__ready=false;
function fit(id,maxLines,minPx,widthOnly){
  const box=document.getElementById(id); if(!box) return;
  const sp=box.querySelector('span'); if(!sp) return;
  let fs=parseFloat(getComputedStyle(sp).fontSize);
  const lh=parseFloat(getComputedStyle(sp).lineHeight)/fs;
  const maxH=box.clientHeight, maxW=box.clientWidth;
  while(true){
    sp.style.fontSize=fs+'px';
    const fitsW = sp.getBoundingClientRect().width<=maxW+0.5 && sp.scrollWidth<=maxW+0.5;
    let ok = fitsW;
    if(!widthOnly){
      const h=sp.getBoundingClientRect().height;
      ok = fitsW && h<=maxH+0.5 && Math.round(h/(fs*lh))<=maxLines;
    }
    if(ok || fs<=minPx) break;
    fs-=1;
  }
  sp.dataset.fs=fs;
  sp.dataset.lines=widthOnly?1:Math.round(sp.getBoundingClientRect().height/(fs*lh));
}
/* пилюля уровня: у неё padding, поэтому считать строки по высоте нельзя —
   только ширина (иначе она ужимается до минимума, было 7px вместо 15) */
document.fonts.ready.then(()=>{ fit('title',3,9,false); fit('level',1,7,true); window.__ready=true; });
"""


DEFAULT_BRAND = {"name": "Your", "tag": "School", "by": "by Your Name"}


def build_html(theme, title, level, year, size, brand=None):
    """brand — {"name", "tag", "by"}: подпись рядом со знаком в подвале темы vibe
    (тема company её не читает). Не заданное берётся из DEFAULT_BRAND."""
    if theme == "company":
        fonts = font_css("Inter")
        mark = company_mark()
        wordmark = svg_logo("company_wordmark.svg", "wordmark",
                            {"black": "#FFFFFF", "#000000": "#FFFFFF", "#000": "#FFFFFF"})
        foot = f'{wordmark}<div class="year">{html.escape(str(year))}</div>' if year else wordmark
    else:
        fonts = font_css("Oswald", "Manrope", "JetBrains Mono")
        b = {**DEFAULT_BRAND, **{k: v for k, v in (brand or {}).items() if v}}
        mark = svg_logo("vibe_mark.svg", "mark")
        vsmall = svg_logo("vibe_mark.svg", "vmark")
        year_txt = f'<span class="year">{html.escape(str(year))}</span>' if year else ""
        # Подвал — логотип целиком: знак, рядом название и мелкое моно-слово,
        # ниже строка «by …» и год. Знак при этом стоит на бейдже дважды (крупно
        # сверху и мелко внизу): так логотип узнаваем и в 64 px.
        foot = (f'<div class="logo">{vsmall}<div class="wm">'
                f'<div class="wm1">{html.escape(b["name"])}'
                f'<span class="wm-ac">{html.escape(b["tag"])}</span></div>'
                f'<div class="wm2">{html.escape(b["by"])}{year_txt}</div>'
                f'</div></div>')
    level_html = (f'<div class="level" id="level"><span>{html.escape(level)}</span></div>'
                  if level else "")
    # фон-декор есть только у тёмной темы: на светлом градиенте company частицы
    # превращаются в грязь
    decor = (f'<div class="glow"></div>{vibe_particles_svg()}' if theme == "vibe" else "")
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<style>:root{{--s:{size}px}}
{fonts}
{BASE_CSS}
{THEME_CSS[theme]}
</style></head><body>
<div class="badge">
  {decor}
  <div class="mark-wrap">{mark}</div>
  <div class="title" id="title"><span>{html.escape(title)}</span></div>
  {level_html}
  <div class="foot">{foot}</div>
</div>
<div class="ring"></div>
<div class="edge"></div>
<script>{FIT_JS}</script>
</body></html>"""


REQUIRED_FONTS = {"company": ["Inter"], "vibe": ["Oswald", "Manrope"]}


def render(jobs, size):
    """jobs: [(theme, html_path, png_path)]. Реальный масштаб (device_scale_factor=1):
    в 2× дефекты мелкого кегля не видно. Фон прозрачный (omit_background)."""
    from playwright.sync_api import sync_playwright
    results = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
        for theme, hp, pp in jobs:
            pg.goto(Path(hp).resolve().as_uri())
            pg.wait_for_function("window.__ready===true", timeout=20000)
            pg.wait_for_timeout(120)
            loaded = set(pg.evaluate(
                "[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)"))
            info = pg.evaluate("""() => {const t=document.querySelector('#title span');
                const l=document.querySelector('#level span');
                return {fs:t&&t.dataset.fs, lines:t&&t.dataset.lines, lfs:l&&l.dataset.fs}}""")
            pp.parent.mkdir(parents=True, exist_ok=True)
            pg.screenshot(path=str(pp), omit_background=True)
            missing = [f for f in REQUIRED_FONTS[theme] if f not in loaded]
            results.append((pp, info, missing))
        b.close()
    return results


def verify_png(path, size):
    """Квадрат, RGBA, углы прозрачные — то, что Accredible ждёт от файла."""
    try:
        from PIL import Image
    except ImportError:
        return "PIL нет — размер не проверен"
    im = Image.open(path)
    ok_size = im.size == (size, size)
    rgba = im.mode == "RGBA"
    corner = im.getpixel((2, 2))[3] == 0 if rgba else False
    return (f"{im.size[0]}×{im.size[1]} {im.mode}"
            f"{' ✓квадрат' if ok_size else ' ✗НЕ квадрат'}"
            f"{' ✓прозрачный угол' if corner else ' ✗угол непрозрачный'}")


def make_badge(theme, title, level, year, out, size, keep_html=False, brand=None):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = build_html(theme, title, level, year, size, brand)
    if keep_html:
        hp = out.with_suffix(".html")
    else:
        hp = Path(tempfile.mkdtemp(prefix="badge_")) / (out.stem + ".html")
    hp.write_text(doc, encoding="utf-8")
    (pp, info, missing), = render([(theme, hp, out)], size)
    report(pp, info, missing, size)
    if not keep_html:
        try:
            hp.unlink(); hp.parent.rmdir()
        except OSError:
            pass
    return out


def report(pp, info, missing, size):
    fs = float(info.get("fs") or 0); lines = info.get("lines")
    warn = ""
    if missing:
        warn += f"  ⚠ ШРИФТ НЕ ПРИМЕНИЛСЯ: {', '.join(missing)}"
    if fs and fs <= 10:
        warn += f"  ⚠ кегль упёрся в минимум ({fs:.0f}px) — заголовок слишком длинный"
    sys.stderr.write(f"{pp.name:28} кегль {fs:.1f}px/{lines} стр · {verify_png(pp, size)}{warn}\n")


# ── контактный лист: как бейдж выглядит в профиле — крошечным ────────────────
def contact_sheet(pngs, out, sizes=(400, 120, 64, 40)):
    from PIL import Image, ImageDraw
    pad = 24
    cells = [(s, bg) for s in sizes for bg in ("#FFFFFF", "#1B1F2A")]
    w = pad + sum(s + pad for s, _ in cells)
    h = pad + len(pngs) * (sizes[0] + pad)
    sheet = Image.new("RGB", (w, h), "#E9E9EE")
    d = ImageDraw.Draw(sheet)
    y = pad
    for p in pngs:
        im = Image.open(p).convert("RGBA")
        x = pad
        for s, bg in cells:
            tile = Image.new("RGB", (s, sizes[0]) if s == sizes[0] else (s, s), bg)
            th = tile.size[1]
            small = im.resize((s, s), Image.LANCZOS)
            tile.paste(small, (0, 0), small)
            sheet.paste(tile, (x, y + (sizes[0] - th)))
            d.text((x, y + sizes[0] + 4), f"{s}px", fill="#333")
            x += s + pad
        d.text((pad, y - 14), Path(p).name, fill="#333")
        y += sizes[0] + pad
    sheet.save(out)
    return out


# ── ростер → CSV / JSON для Accredible ───────────────────────────────────────
def read_roster(path):
    p = Path(path)
    rows = []
    if p.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        ws = load_workbook(p, read_only=True).active
        lines = [[str(c).strip() if c is not None else "" for c in r] for r in ws.iter_rows(values_only=True)]
    else:
        text = p.read_text(encoding="utf-8-sig")
        lines = [[c.strip().strip('"') for c in re.split(r"[;\t,]", ln)] for ln in text.splitlines()]
    for cells in lines:
        cells = [c for c in cells if c]
        if not cells or cells[0].startswith("#"):
            continue
        if len(cells) < 2:
            sys.stderr.write(f"  пропуск (нет почты): {' '.join(cells)}\n")
            continue
        name, email = cells[0], cells[1]
        if "@" not in email:
            if "@" in name:
                name, email = email, name
            else:
                sys.stderr.write(f"  пропуск (шапка или нет почты): {' | '.join(cells[:2])}\n")
                continue
        rows.append((" ".join(name.split()), email.strip().lower()))
    return rows


def write_csv(rows, out, issue_date, group_id=None):
    """Колонки ровно как в шаблоне Accredible. Дата YYYY/MM/DD — один из трёх
    принимаемых форматов; при импорте выбрать его же в поле формата даты.
    UTF-8 без BOM: BOM прилипает к первому заголовку и ломает распознавание."""
    d = issue_date.strftime("%Y/%m/%d")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        head = ["Recipient Name", "Recipient Email", "Issue Date"] + (["Group ID"] if group_id else [])
        w.writerow(head)
        for name, email in rows:
            w.writerow([name, email, d] + ([group_id] if group_id else []))
    return out


def write_api_json(rows, out, issue_date, group_id):
    """Пачки для POST /v2/credentials/bulk_create — не больше 30 в запросе."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(0, len(rows), BULK_BATCH):
        chunk = rows[i:i + BULK_BATCH]
        payload = {"credentials": [
            {"recipient": {"name": n, "email": e}, "group_id": int(group_id),
             "issued_on": issue_date.strftime("%Y-%m-%d")} for n, e in chunk]}
        fp = out if len(rows) <= BULK_BATCH else out.with_name(f"{out.stem}_{i // BULK_BATCH + 1:02d}{out.suffix}")
        fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append(fp)
    return files


# ── образцы ──────────────────────────────────────────────────────────────────
SAMPLE_SET = [
    ("company", "Искусственный интеллект в работе", "Практикум", "badge_company_ai_v_rabote"),
    ("company", "Вайбкодинг и ИИ-агенты", "Модуль 03", "badge_company_vibecoding"),
    ("vibe", "Вайбкодинг: старт", "Уровень 1", "badge_vibe_start"),
    ("vibe", "AI Agents Builder", "Level 2", "badge_vibe_agents"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=THEMES, help="company | vibe")
    ap.add_argument("--title", help="короткое название достижения (до ~35 знаков)")
    ap.add_argument("--level", default="", help="уровень/модуль, если есть")
    ap.add_argument("--year", default=str(dt.date.today().year))
    ap.add_argument("--size", type=int, default=SIZE_DEFAULT, help=f"сторона квадрата, px (мин {SIZE_MIN}, оптимум {SIZE_DEFAULT})")
    ap.add_argument("--out", help="куда писать PNG / CSV / JSON")
    ap.add_argument("--keep-html", action="store_true", help="оставить HTML рядом с PNG")
    ap.add_argument("--brand-name", help="тема vibe: крупное название рядом со знаком (по умолчанию Your)")
    ap.add_argument("--brand-tag", help="тема vibe: мелкое моно-слово справа от названия (School)")
    ap.add_argument("--brand-by", help="тема vibe: строка под названием («by Your Name»)")
    ap.add_argument("--samples", action="store_true", help="четыре образца + контактный лист в ./badge_samples/")
    ap.add_argument("--roster", help="список «ФИО;почта» (.txt/.csv/.xlsx)")
    ap.add_argument("--csv", action="store_true", help="CSV для Upload Spreadsheet в кабинете")
    ap.add_argument("--api-json", action="store_true", help="JSON-пачки для /v2/credentials/bulk_create")
    ap.add_argument("--issue-date", help="YYYY-MM-DD, по умолчанию сегодня")
    ap.add_argument("--group-id", help="ID группы Accredible (для JSON обязателен, для CSV — если выдача в несколько групп)")
    a = ap.parse_args()

    if a.size < SIZE_MIN:
        ap.error(f"--size меньше минимума Accredible ({SIZE_MIN})")
    brand = {"name": a.brand_name, "tag": a.brand_tag, "by": a.brand_by}

    # ── ростер
    if a.roster:
        rows = read_roster(a.roster)
        sys.stderr.write(f"ростер: {len(rows)} чел.\n")
        date = dt.datetime.strptime(a.issue_date, "%Y-%m-%d").date() if a.issue_date else dt.date.today()
        if a.csv or not a.api_json:
            out = a.out or Path(a.roster).with_name(Path(a.roster).stem + "_accredible.csv")
            p = write_csv(rows, out, date, a.group_id)
            sys.stderr.write(f"CSV → {p}\n")
            print(Path(p).read_text(encoding="utf-8")[:600])
        if a.api_json:
            if not a.group_id:
                ap.error("--api-json требует --group-id")
            out = a.out if (a.out and a.out.endswith(".json")) else Path(a.roster).with_name(Path(a.roster).stem + "_bulk.json")
            for fp in write_api_json(rows, out, date, a.group_id):
                sys.stderr.write(f"JSON → {fp}\n")
        return

    # ── образцы
    if a.samples:
        SAMPLES.mkdir(exist_ok=True)
        jobs = []
        tmp = Path(tempfile.mkdtemp(prefix="badges_"))
        for theme, title, level, stem in SAMPLE_SET:
            hp = tmp / f"{stem}.html"
            hp.write_text(build_html(theme, title, level, a.year, a.size, brand), encoding="utf-8")
            jobs.append((theme, hp, SAMPLES / f"{stem}.png"))
        for pp, info, missing in render(jobs, a.size):
            report(pp, info, missing, a.size)
        sheet = contact_sheet([j[2] for j in jobs], SAMPLES / "contact_sheet.png")
        sys.stderr.write(f"контактный лист → {sheet}\n")
        return

    # ── один бейдж
    if not (a.theme and a.title):
        ap.error("нужны --theme и --title (или --samples / --roster)")
    # срез и re.sub вынесены из f-строки: обратная косая внутри {…} — SyntaxError
    # на Python 3.10 и 3.11 (разрешено только с 3.12)
    slug = re.sub(r"[^\w]+", "_", a.title)[:40]
    out = a.out or SAMPLES / f"badge_{a.theme}_{slug}.png"
    make_badge(a.theme, a.title, a.level, a.year, out, a.size, a.keep_html, brand)


if __name__ == "__main__":
    main()
