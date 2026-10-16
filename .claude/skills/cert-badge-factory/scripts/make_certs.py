# -*- coding: utf-8 -*-
"""Движок именных сертификатов: данные из конфига, вид из темы, рендер Playwright.

Данные и вид разделены: в конфиг вынесены ДАННЫЕ (программа, люди, номера,
подписант), в темы themes/<имя>.py — ВИД. Вся логика (склонение, кегль имени,
перекраска логотипов, номера, неразрывные предлоги, рендер) живёт здесь.

Запуск:
    S=~/.claude/skills/cert-badge-factory
    python $S/scripts/make_certs.py --theme vibe --config roster.json            # HTML всем
    python $S/scripts/make_certs.py --theme vibe --config roster.json --render   # + PNG 2× и PDF
    python $S/scripts/make_certs.py --theme vibe --config roster.json --samples  # 3 образца 1×
    python $S/scripts/make_certs.py --themes                                     # список тем

Конфиг — JSON (или .py с dict CONFIG), см. configs/*.json:
    program        название программы
    modules        [[метка, название, дата], …] — на листе не печатаются, из них
                   берётся число для subline (если subline не задан)
    hours          «6 академических часов»
    subline        «3 практикума · июль 2026» (необязательно)
    people         список ФИО; people_extra — второй список (пойдут следом)
    gender         {"ФИО": "f"|"m"} — переопределение, когда автоопределение не берёт
    cert_no        формат номера, «CERT-2026-{i:03d}»
    issuer         {"l1": "Выдан", "l2": "ООО «Ваша Компания»"}
    signer         {"name": …, "role": …, "image": "signature.png"} (путь от конфига
                   или от assets/; по умолчанию там заглушка — подставьте свою
                   подпись PNG с прозрачным фоном)
    brand          {"name": "Your", "tag": "School", "by": "by Your Name"} — подпись
                   рядом со знаком в шапке темы vibe (другие темы поле не читают)
    logos          [пути SVG] — иначе логотипы темы по умолчанию (заглушки в
                   assets/brand/: замените файлы своими логотипами)
    labels         {"title": …, "lead_in": …, "vol": …} — поверх меток темы
    out            каталог вывода (иначе рядом с конфигом, ./certificates)
    samples        [[i, "ФИО", "long"], …] — свои образцы для --samples

Вывод: <out>/_html/*.html, <out>/png/*.png (2×), <out>/pdf/*.pdf,
       <out>/_samples/<тема>_{long,mid,short}.{html,png} (1×).

ГОЧИ (оплачены временем, не повторять):
  · в колоночном flex тонкая полоска (height:1–2px) схлопывается в НОЛЬ —
    нужен flex:0 0 <высота>; на глаз не видно, ловит только check_layout.py;
  · смотреть рендер в РЕАЛЬНОМ масштабе (device_scale_factor=1) — --samples
    именно так и рендерит; в 2× дефекты не видны;
  · у SVG-элементов className — объект SVGAnimatedString, не строка (чекеры);
  · чёрная заливка в логотипе-SVG пропадает на тёмном фоне и желтит кремовым
    на светлом — цвет перекраски задаёт тема (logo_fill);
  · сложный фирменный знак в круге 12 мм — каша; мелким медальонам простые формы;
  · Inter и Manrope в %LOCALAPPDATA%/…/Fonts БИТЫЕ (303 КБ переводов строки),
    Chromium молча подставляет другой шрифт — темы с веб-шрифтами вшивают их
    data-URI (scripts/fonts.py), а движок печатает, что реально загрузилось;
  · `| head -N` на выводе скрипта убивает генератор по SIGPIPE — писать в лог.
"""
import io, os, sys, re, json, base64, argparse, importlib.util
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ASSETS = SKILL / "assets"
sys.path.insert(0, str(SKILL))
sys.path.insert(0, str(HERE))

import themes                      # noqa: E402
from fonts import fontface_css, families, FONTS_PROBE   # noqa: E402

# ── склонение ────────────────────────────────────────────────────────────────
# Имена без отчества: пол по имени. Словарь короткий и растёт по мере
# встреч; что не в словаре и не решается фамилией — форма без рода.
FEMALE_NAMES = {
    # Женские
    "александра": True, "алевтина": True, "алина": True, "алиса": True,
    "алла": True, "альбина": True, "анастасия": True, "ангелина": True,
    "анна": True, "антонина": True, "валентина": True, "валерия": True,
    "варвара": True, "вера": True, "вероника": True, "виктория": True,
    "влада": True, "галина": True, "гульнара": True, "гульназ": True,
    "дарья": True, "диана": True, "дина": True, "ева": True, "евгения": True,
    "екатерина": True, "елена": True, "елизавета": True, "жанна": True,
    "зинаида": True, "зоя": True, "инга": True, "инна": True, "ирина": True,
    "камила": True, "карина": True, "кира": True, "кристина": True,
    "ксения": True, "лариса": True, "лидия": True, "лилия": True,
    "любовь": True, "людмила": True, "маргарита": True, "марина": True,
    "мария": True, "милана": True, "надежда": True, "наталия": True,
    "наталья": True, "нина": True, "оксана": True, "олеся": True,
    "ольга": True, "полина": True, "раиса": True, "регина": True,
    "римма": True, "светлана": True, "снежана": True, "софия": True,
    "софья": True, "таисия": True, "тамара": True, "татьяна": True,
    "ульяна": True, "фаина": True, "элина": True, "эльвира": True,
    "юлия": True, "яна": True, "алёна": True, "алена": True, "милена": True,
    "динара": True, "лейла": True, "мадина": True, "залина": True,
    # Мужские
    "александр": False, "алексей": False, "анатолий": False, "андрей": False,
    "антон": False, "аркадий": False, "артем": False, "артём": False,
    "артур": False, "борис": False, "вадим": False, "валентин": False,
    "валерий": False, "василий": False, "виктор": False, "виталий": False,
    "владимир": False, "владислав": False, "вячеслав": False, "геннадий": False,
    "георгий": False, "глеб": False, "григорий": False, "данила": False,
    "даниил": False, "денис": False, "дмитрий": False, "егор": False,
    "иван": False, "игорь": False, "илья": False, "кирилл": False,
    "константин": False, "лев": False, "леонид": False, "максим": False,
    "марат": False, "матвей": False, "михаил": False, "никита": False,
    "николай": False, "олег": False, "павел": False, "петр": False,
    "пётр": False, "роман": False, "руслан": False, "рустам": False,
    "святослав": False, "семен": False, "семён": False, "сергей": False,
    "станислав": False, "степан": False, "тимофей": False, "тимур": False,
    "фёдор": False, "федор": False, "филипп": False, "эдуард": False,
    "эмиль": False, "юрий": False, "ярослав": False,
    "айрат": False, "альберт": False, "ильдар": False, "ринат": False,
    "арсений": False, "аслан": False, "даня": False, "эрик": False,
    "евгений": False, "ильнур": False, "тарас": False, "ян": False,
    "раушания": True, "эльмира": True, "гузель": True, "лилия": True,
    "венера": True, "айгуль": True, "земфира": True, "лиана": True,
}

# Имена, по которым пол не определить: их носят и мужчины, и женщины, а
# сокращённая форма не говорит ничего. Такие ВСЕГДА дают форму без рода —
# лучше сухо, чем обратиться к человеку не в том роде на документе.
AMBIGUOUS_NAMES = {"женя", "саша", "валя", "слава", "ника", "юля",
                   "сима", "шура", "паша", "лера", "реган"}

# Имена латиницей: в анкетах их пишут и так. Держим отдельно, чтобы в
# кириллическом словаре не мешались.
FEMALE_NAMES.update({
    "ekaterina": True, "olga": True, "gulnaz": True, "anna": True,
    "maria": True, "elena": True, "irina": True, "natalia": True,
    "svetlana": True, "tatiana": True, "julia": True, "yulia": True,
    "alexander": False, "alexey": False, "dmitry": False, "sergey": False,
    "ivan": False, "mikhail": False, "andrey": False, "nikita": False,
    "pavel": False, "igor": False, "maxim": False, "denis": False,
})



def gender(fio: str, overrides=None):
    """'f' | 'm' | None. None — когда пол не восстановить (фамилия + инициал)."""
    if overrides and fio in overrides:
        return overrides[fio]
    parts = fio.split()
    # Отчество стоит то последним («Сидорова Мария Сергеевна»), то вторым
    # («Мария Сергеевна Сидорова») — смотрим оба места. Раньше проверялось
    # только последнее слово, и второй порядок оставался без рода.
    if len(parts) >= 3:
        for patr in (parts[-1], parts[1]):
            if patr.endswith(("овна", "евна", "ична", "инична", "кызы")):
                return "f"
            if patr.endswith(("ович", "евич", "ьич", "оглы")):
                return "m"
    # Имя стоит то первым («Алексей Смирнов»), то вторым («Смирнова
    # Светлана») — в анкетах пишут и так, и так. Поэтому смотрим ОБА слова:
    # раньше проверялось только второе, и у половины тиража род не
    # определялся вовсе.
    if len(parts) >= 2:
        for part in (parts[0], parts[1]):
            low = part.lower().rstrip(".")
            if not low or part.endswith("."):
                continue
            if low in AMBIGUOUS_NAMES:
                return None
            by_name = FEMALE_NAMES.get(low)
            if by_name is not None:
                return "f" if by_name else "m"
    # У шаблонного листа имя пустое (его подставляет Accredible своим атрибутом),
    # и разбор рода падал здесь на parts[0] с IndexError.
    if parts and parts[0].lower().endswith(("ова", "ева", "ина", "ская", "цкая")):
        return "f"
    return None


def did_phrase(fio: str, overrides=None) -> str:
    """«Коваленко О.» — род не угадать, поэтому конструкция без глагола."""
    g = gender(fio, overrides)
    if g == "f":
        return "прошла программу"
    if g == "m":
        return "прошёл программу"
    return "участник программы"


def glue_prepositions(s: str) -> str:
    """Однобуквенные предлоги и союзы клеятся к следующему слову неразрывным
    пробелом — иначе название переносится как «…интеллект в / работе»."""
    return re.sub(r" ([вискоуа]) ", " \\1\u00a0", s)


# ── ресурсы ──────────────────────────────────────────────────────────────────
def data_uri(p: Path, mime: str) -> str:
    if not p or not p.exists():
        return ""
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def logo_uri(p: Path, fill: str) -> str:
    """SVG логотипа под фон карточки: чёрная заливка словесной части
    перекрашивается в цвет темы (logo_fill). Фирменные цвета не трогаются.
    Тёмная тема → светлый (#EEF1FB), светлый градиент → чистый белый
    (кремовый на нём желтит)."""
    if not p or not p.exists():
        return ""
    svg = p.read_text(encoding="utf-8")
    for black in ('fill="black"', 'fill="#000000"', 'fill="#000"'):
        svg = svg.replace(black, f'fill="{fill}"')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def resolve(p, base: Path):
    """Путь из конфига: абсолютный · от каталога конфига · от assets/ · от assets/brand/."""
    if not p:
        return None
    q = Path(p)
    for cand in ([q] if q.is_absolute() else [base / q, ASSETS / q, ASSETS / "brand" / q]):
        if cand.exists():
            return cand
    return base / q


# ── конфиг ───────────────────────────────────────────────────────────────────
def load_config(path: Path) -> dict:
    if path.suffix == ".py":
        spec = importlib.util.spec_from_file_location("cert_config", path)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        cfg = dict(mod.CONFIG)
    else:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["_dir"] = path.parent
    cfg.setdefault("people", []); cfg.setdefault("people_extra", [])
    cfg.setdefault("modules", []); cfg.setdefault("gender", {})
    cfg.setdefault("issuer", {}); cfg.setdefault("signer", {}); cfg.setdefault("labels", {})
    cfg.setdefault("cert_no", "CERT-{i:03d}")
    if not cfg.get("subline") and cfg["modules"]:
        cfg["subline"] = f"{len(cfg['modules'])} модулей"
    cfg.setdefault("subline", "")
    # Пояснение к названию программы обычными словами: брендовое имя («Интенсив
    # по вайбкодингу») понятно внутри курса, а сертификат предъявляют снаружи.
    # Пустое — строки на листе нет вовсе (пустой div сдвигал бы блок отступом).
    cfg.setdefault("program_sub", "")
    return cfg


# Страховка кегля имени: если строка всё-таки шире колонки (подменённый
# шрифт, новая длинная фамилия) — ужимаем, пока не влезет. Общая для тем.
# ОБЯЗАТЕЛЬНО после document.fonts.ready: веб-шрифт из data-URI грузится
# асинхронно, и страховка, запущенная при парсинге, меряла ширину ПОДСТАНОВКИ
# (Segoe капсом шире Oswald) — ужимала имя на треть, а потом приходил Oswald,
# и «кегль 28pt» на листе оказывался 21pt. Калибровка таблицы по такому
# рендеру дала бы ложные числа (так и случилось 12.09, поймано замером).
SCRIPT = """<script>
(function(){
  function fit(){
    var el=document.querySelector('.name'); if(!el) return;
    var guard=0, size=parseFloat(getComputedStyle(el).fontSize);
    while(el.scrollWidth>el.clientWidth && size>13 && guard++<80){
      size-=0.5; el.style.fontSize=size+'px';
    }
  }
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(fit);
})();
</script>"""


class Builder:
    def __init__(self, theme, cfg: dict):
        self.theme, self.cfg = theme, cfg
        base = cfg["_dir"]
        logos = [resolve(p, base) for p in cfg.get("logos") or []] or list(theme.default_logos)
        self.logo_uris = [u for u in (logo_uri(p, theme.logo_fill) for p in logos) if u]
        for p, u in zip(logos, (logo_uri(p, theme.logo_fill) for p in logos)):
            sys.stderr.write(f"логотип {p.name}: {'✓' if u else '✗ НЕТ'}\n")
        sign = resolve(cfg["signer"].get("image", "signature.png"), base)
        self.sign_uri = data_uri(sign, "image/png")
        sys.stderr.write(f"подпись {sign.name if sign else '—'}: {'✓' if self.sign_uri else '✗ НЕТ'}\n")
        self.fonts_css = fontface_css(theme.fonts)
        self.labels = {**theme.labels, **cfg["labels"]}

    def build_one(self, i: int, fio: str, outdir: Path, stem=None) -> Path:
        t, cfg = self.theme, self.cfg
        ctx = {**cfg, "i": i, "fio": fio}
        program = cfg["program"]
        vars = dict(
            fonts_css=self.fonts_css,
            css=t.render_css(fio),
            decor=t.decor_html(ctx),
            logos=t.logos_html(self.logo_uris, ctx),
            title=self.labels["title"], lead_in=self.labels["lead_in"], vol=self.labels["vol"],
            name=fio, name_cls=" long" if len(fio) > t.caps_limit else "",
            # В русском глагол зависит от пола, в английском — нет. Поэтому
            # конфиг может задать фразу прямо (cfg["did"]), и тогда род не
            # выясняется вовсе: «completed the programme» для всех.
            verb=cfg.get("did") or did_phrase(fio, cfg["gender"]),
            program=glue_prepositions(program),
            prog_cls=" long" if len(program) > t.caps_limit else "",
            program_sub=(f'<div class="prog-sub">{glue_prepositions(cfg["program_sub"])}</div>'
                         if cfg.get("program_sub") else ""),
            hours=cfg["hours"], subline=cfg["subline"],
            issuer_l1=cfg["issuer"].get("l1", self.labels.get("issuer_l1", "Выдан")),
            issuer_l2=cfg["issuer"].get("l2", ""),
            cno=cfg["cert_no"].format(i=i),
            sign=f'<img src="{self.sign_uri}" alt="">' if self.sign_uri else "",
            sign_name=cfg["signer"].get("name", ""), sign_role=cfg["signer"].get("role", ""),
            script=SCRIPT,
        )
        html = t.html(vars)
        slug = stem or f"{i:02d}_" + re.sub(r"[^\w\-]+", "_", fio.replace(" ", "_"))
        outdir.mkdir(parents=True, exist_ok=True)
        p = outdir / f"{slug}.html"
        io.open(p, "w", encoding="utf-8").write(html)
        return p


def render(pages, png_dir: Path, pdf_dir: Path = None, scale=2, font_families=()):
    """pages: [html_path]. PNG именуются по stem файла.
    Лист портретный: вьюпорт 794×1123 = 210×297 мм при 96 dpi."""
    from playwright.sync_api import sync_playwright
    png_dir.mkdir(parents=True, exist_ok=True)
    if pdf_dir:
        pdf_dir.mkdir(parents=True, exist_ok=True)
    checked = False
    with sync_playwright() as pw:
        # Без этих флагов Chromium печёт в PNG субпиксельное сглаживание: у
        # мелкого текста левая кромка штриха уходит в синий, правая в оранжевый.
        # На экране в 100% незаметно, но при зуме и на печати это цветная
        # бахрома по буквам — поймано вычиткой листов, не чекерами.
        b = pw.chromium.launch(args=["--disable-lcd-text", "--font-render-hinting=none",
                                     "--force-color-profile=srgb"])
        pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
        for p in pages:
            pg.goto(p.resolve().as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(200)
            if font_families and not checked:
                # какие семейства РЕАЛЬНО загрузились (см. fonts.py: .check() врёт)
                for fam, loaded, total in pg.evaluate(FONTS_PROBE, list(font_families)):
                    ok = loaded > 0
                    sys.stderr.write(f"шрифт {fam:16} {'✓' if ok else '✗ ПОДСТАНОВКА'} "
                                     f"({loaded}/{total} face)\n")
                checked = True
            pg.screenshot(path=str(png_dir / f"{p.stem}.png"))
            if pdf_dir:
                pg.pdf(path=str(pdf_dir / f"{p.stem}.pdf"),
                       width="210mm", height="297mm", print_background=True,
                       margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()


# Три образца по длине имени: самое длинное, среднее, фамилия с инициалом.
DEFAULT_SAMPLES = [
    (1, "Ивановская Александра Владимировна", "long"),
    (2, "Петров Никита Андреевич", "mid"),
    (3, "Коваленко О.", "short"),
]


def main():
    ap = argparse.ArgumentParser(description="именные сертификаты: тема + конфиг → HTML/PNG/PDF")
    ap.add_argument("--theme", default="company", help=f"тема: {', '.join(themes.available())}")
    ap.add_argument("--config", help="roster.json или config.py с dict CONFIG")
    ap.add_argument("--out", help="каталог вывода (по умолчанию из конфига или ./certificates у конфига)")
    ap.add_argument("--render", action="store_true", help="PNG 2× и PDF всем")
    ap.add_argument("--samples", action="store_true",
                    help="три образца в <out>/_samples/<тема>_*.png в реальном масштабе 1×")
    ap.add_argument("--themes", action="store_true", help="перечислить темы и выйти")
    a = ap.parse_args()

    if a.themes:
        for n in themes.available():
            sys.stderr.write(f"  {n}\n")
        return
    if not a.config:
        ap.error("нужен --config")

    theme = themes.get_theme(a.theme)
    cfg = load_config(Path(a.config).resolve())
    out = Path(a.out).resolve() if a.out else \
        (resolve(cfg["out"], cfg["_dir"]) if cfg.get("out") else cfg["_dir"] / "certificates")
    sys.stderr.write(f"тема: {theme.name} · конфиг: {Path(a.config).name} · вывод: {out}\n")
    bld = Builder(theme, cfg)

    if a.samples:
        sdir = out / "_samples"
        samples = [tuple(s) for s in cfg.get("samples") or DEFAULT_SAMPLES]
        pages = []
        for i, fio, tag in samples:
            p = bld.build_one(i, fio, sdir, stem=f"{theme.name}_{tag}")
            pages.append(p)
            sys.stderr.write(f"  {p.stem:14} {fio:36} кегль {theme.name_size(fio)}pt\n")
        render(pages, sdir, scale=1, font_families=families(theme.fonts))
        sys.stderr.write(f"\nобразцы 1× → {sdir}\n")
        return

    everyone = [(f, "основной") for f in cfg["people"]] + \
               [(f, "доп.") for f in cfg["people_extra"]]
    if not everyone:
        sys.stderr.write("в конфиге нет people\n"); return
    html_dir = out / "_html"
    pages = []
    for i, (fio, src) in enumerate(everyone, 1):
        p = bld.build_one(i, fio, html_dir)
        pages.append(p)
        g = {"f": "ж", "m": "м", None: "?"}[gender(fio, cfg["gender"])]
        sys.stderr.write(f"  {i:2}. {fio:36} [{g}] {src:8} → {p.name}\n")
    sys.stderr.write(f"\nHTML: {len(pages)} шт. → {html_dir}\n")

    if not a.render:
        sys.stderr.write("рендер пропущен (--render)\n")
        return
    render(pages, out / "png", out / "pdf", scale=2, font_families=families(theme.fonts))
    sys.stderr.write(f"PNG и PDF готовы: {len(pages)} × 2 → {out}\n")


if __name__ == "__main__":
    main()
