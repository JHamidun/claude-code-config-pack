# -*- coding: utf-8 -*-
"""Тема «vibe» — тёмная техно-тема для школы или курса («Your School»).

Палитра снята с живого сайта-образца замером вычисленных стилей, не на глаз:
  · фон body rgb(7,10,28) → #070A1C; карточки/плашки #14151C — почти чёрный, холодный
  · главный акцент — терракота #CC7357 (кнопки, слова в заголовках), тёмная #A4502F
  · второй акцент — голубой #4DABF7 (слова в заголовках, кикеры, знак H)
  · светлые #EEF1FB / #F6F4EF / белый; приглушённые #48506A / #5A6172 / #A6AAC6
  · Oswald 700/800 КАПСОМ в заголовках; Manrope 400–800 в тексте;
    JetBrains Mono в метках-кикерах («— СТАНЬ ТЕМ, КТО …», капс, разрядка, голубой)
  · декор — россыпь мелких треугольников (контурных и залитых, синих и белых)
    и крупный объект из частиц (мозг). На сертификате объект сдержаннее:
    мягкое облако-кольцо из частиц справа внизу и редкая россыпь по листу —
    фактура, а не иллюстрация.

Чем НЕ является: перекрашенной company. Другая типографика (узкий капсовый
заголовок и имя, моно-кикер), другой лист (карточка почти чёрная с тонкой
кромкой, без градиента), другой декор (частицы вместо медальонов и волн).

Шрифты — веб (Google Fonts через scripts/fonts.py, data-URI в HTML): Oswald
в системе нет, локальный Manrope битый (см. base.py). Движок печатает, какие
семейства реально загрузились — если «✗», лист набран подстановкой.

Знак: assets/brand/vibe_mark.svg — ромб в терракоте с угловыми скобками
(заглушка: замените файл своим знаком). Словесная часть («Your School» и
строка «by Your Name») набирается текстом рядом со знаком: у знака нет готового
горизонтального лого. Тексты берутся из поля brand конфига:
    "brand": {"name": "Your", "tag": "School", "by": "by Your Name"}
name — крупно (Oswald), tag — мелким моно справа от него, by — строка под ними.
SVG уже в фирменных цветах, чёрной заливки нет — logo_fill на нём не влияет.
"""
import re, math, random, html
from .base import Theme, BRAND_DIR

# ── палитра (снята с сайта-образца) ──────────────────────────────────────────────────
BG_PAGE = "#070A1C"
BG_CARD = "#14151C"
TERRA = "#CC7357"
TERRA_DARK = "#A4502F"
BLUE = "#4DABF7"
BLUE_DEEP = "#1779C9"
LIGHT = "#EEF1FB"
CREAM = "#F6F4EF"
MUTED = "#A6AAC6"
MUTED_DARK = "#5A6172"

FONTS = ("Oswald:wght@600;700", "Manrope:wght@400;700", "JetBrains Mono:wght@400;500")

# ── вёрстка ──────────────────────────────────────────────────────────────────
# Лист A4 портрет; карточка inset 7 мм, скругление 6 мм (меньше, чем у
# company: техно-тема, не «мягкая» карточка), тонкая светлая кромка 1px.
# Правило колоночного flex: тонкие полоски несут flex:0 0 <высота>, иначе
# схлопываются в ноль (ловит только check_layout.py).
CSS = """
@page { size:210mm 297mm; margin:0; }
*{margin:0;padding:0;box-sizing:border-box;}
body{
  width:210mm;height:297mm;position:relative;overflow:hidden;
  font-family:'Manrope','Segoe UI','Arial',sans-serif;
  background:%(BG_PAGE)s;color:%(LIGHT)s;
  -webkit-font-smoothing:antialiased;
}
.card{position:absolute;inset:7mm;border-radius:6mm;overflow:hidden;
  background:%(BG_CARD)s;
  box-shadow:inset 0 0 0 1px rgba(238,241,251,.09);}

/* ── декор: слой размером с лист, координаты — миллиметры листа ─────────── */
.decor{position:absolute;left:-7mm;top:-7mm;width:210mm;height:297mm;z-index:1;
  pointer-events:none;}
/* мягкое свечение под облаком частиц — как подсветка мозга на сайте-образце, но тише */
.glow{position:absolute;border-radius:50%;
  background:radial-gradient(closest-side,rgba(41,169,255,.13),rgba(41,169,255,.05) 55%,rgba(41,169,255,0));}
.particles{position:absolute;inset:0;width:100%;height:100%;display:block;}

/* парящие логотипы ИИ-инструментов курса: круглые «стеклянные» медальоны в
   слое декора. Класс .medal — чтобы check_medals.py мерил наезд на текст. */
.medal{position:absolute;border-radius:50%;display:flex;align-items:center;justify-content:center;
  background:rgba(20,21,28,.78);
  box-shadow:inset 0 0 0 .25mm rgba(238,241,251,.16),0 0 3.2mm rgba(41,169,255,.16);}
.medal svg{width:52%;height:52%;display:block;}
.medal svg, .medal svg *{fill:currentColor;}

/* ── контент ─────────────────────────────────────────────────────────────── */
.wrap{position:absolute;inset:0;z-index:3;display:flex;flex-direction:column;
  padding:15mm 13mm 14mm 13mm;}

/* шапка: знак V + словесная часть слева, «СЕРТИФИКАТ» справа */
.head{display:flex;align-items:center;justify-content:space-between;flex:0 0 auto;}
.logos{display:flex;align-items:center;gap:0;}
.logos .vmark{height:9.2mm;display:block;}
.logos .wm{margin-left:.7mm;display:flex;flex-direction:column;justify-content:center;}
.logos .wm1{font-family:'Oswald',sans-serif;font-weight:700;font-size:17pt;line-height:1;
  color:%(LIGHT)s;letter-spacing:.01em;display:flex;align-items:baseline;}
.logos .wm-ac{font-family:'JetBrains Mono',monospace;font-weight:500;font-size:8.6pt;
  line-height:1;color:%(LIGHT)s;margin-left:1.8mm;letter-spacing:.04em;}
.logos .wm2{font-family:'JetBrains Mono',monospace;font-weight:400;font-size:8.6pt;
  line-height:1;color:%(MUTED)s;margin-top:1.3mm;display:flex;align-items:baseline;
  letter-spacing:.04em;}
/* титул служебный: капс Oswald, как заголовки сайта-образца, но скромнее имени */
.title{font-family:'Oswald',sans-serif;font-size:33pt;font-weight:700;line-height:1;
  letter-spacing:.06em;text-transform:uppercase;color:%(LIGHT)s;white-space:nowrap;
  padding-top:1mm;}

/* смысловой блок.
   Плотность 14.09: кегли по листу подняты на 12–18%, отступ от шапки срезан с
   27 до 21 мм — «текст покрупнее, меньше пустого пространства, больше фокуса
   на надписях». Подъём кеглей двигает низ блока вниз, поэтому медальоны n8n и
   huggingface отодвинуты (см. AI_SPOTS); зазор меряет check_medals.py. */
.body{margin-top:21mm;flex:0 0 auto;}
/* кикер — моно, капс, разрядка, голубой, с тире: строка вида «— ПОДТВЕРЖДАЕТ, ЧТО» */
.lead-in{font-family:'JetBrains Mono',monospace;font-weight:500;font-size:10.5pt;
  line-height:1.5;letter-spacing:.14em;text-transform:uppercase;color:%(BLUE)s;}
/* герой документа: Oswald капсом, кегль под длину, строка всегда одна */
.name{margin-top:4mm;font-family:'Oswald',sans-serif;font-size:{name_size}pt;font-weight:600;
  line-height:1.1;letter-spacing:.015em;text-transform:uppercase;color:%(LIGHT)s;
  white-space:nowrap;}
.name.long{text-transform:none;letter-spacing:0;}
.did{margin-top:5.5mm;font-size:14pt;line-height:1.5;color:%(MUTED)s;}
/* название программы — терракота капсом: акцентное слово заголовка сайта */
.prog{margin-top:1.6mm;font-family:'Oswald',sans-serif;font-size:31pt;font-weight:700;
  line-height:1.1;letter-spacing:.02em;text-transform:uppercase;color:%(TERRA)s;
  max-width:172mm;}
.prog.long{text-transform:none;letter-spacing:0;font-size:28.5pt;}
/* пояснение к названию обычными словами: сертификат предъявляют вне курса, где
   «вайбкодинг» ещё не общее слово. Светлее .did, но тише .hours — подпись к
   заголовку, а не ещё одна строка реквизитов. Интерлиньяж не ниже 1.3:
   check_type.py требует этого для кеглей 13–20px. */
/* max-width — вся колонка (170 мм): при 150 мм выбранная формулировка
   («по профессиональной работе с нейросетями и ИИ-инструментами», 182 мм
   набором 14.5pt) переносилась на вторую строку и опускала блок на 7 мм —
   до наезда на n8n и huggingface. Строка обязана быть ОДНОЙ. */
.prog-sub{margin-top:2mm;font-size:14.5pt;font-weight:400;line-height:1.4;
  color:%(LIGHT)s;max-width:170mm;}
.vol{margin-top:4.5mm;font-size:14pt;line-height:1.5;color:%(MUTED)s;}
.hours{margin-top:1.2mm;font-size:19pt;font-weight:700;line-height:1.3;color:%(LIGHT)s;}
.sub{margin-top:1.6mm;font-family:'JetBrains Mono',monospace;font-size:10.5pt;
  line-height:1.5;letter-spacing:.02em;color:%(MUTED)s;}

/* подвал: слева «Выдан», справа подпись над линией — оба по нижней кромке */
.foot{margin-top:auto;display:flex;align-items:flex-end;justify-content:space-between;
  gap:10mm;flex:0 0 auto;}
.issuer{flex:0 1 auto;min-width:0;}
.issuer .l1{font-size:15pt;font-weight:700;line-height:1.36;color:%(LIGHT)s;}
.issuer .l2{font-size:12.5pt;line-height:1.5;color:%(MUTED)s;margin-top:.6mm;}
/* номер — моно, разрядка, голубой: реквизит в стиле меток сайта-образца.
   Непрозрачность была .72 — контраст 4.2:1 на тёмной карточке, ниже порога
   читаемости для мелкого текста (4.5:1), и это единственная строка, которую
   человек переписывает руками при проверке. Поднято до полного цвета: 7.4:1. */
.issuer .cno{font-family:'JetBrains Mono',monospace;font-size:9.4pt;line-height:1.5;
  letter-spacing:.08em;color:%(BLUE)s;margin-top:1.6mm;}
.sign{flex:0 0 80mm;width:80mm;display:flex;flex-direction:column;}
/* росчерк по центру линии: прижатый влево занимал 57% её длины, и правая треть
   читалась как недотянутый элемент */
.sign-img{height:15mm;flex:0 0 15mm;margin-bottom:-2.4mm;display:flex;align-items:flex-end;
  justify-content:center;}
.sign-img img{height:100%;display:block;filter:brightness(0) invert(1);opacity:.96;}
/* flex:0 0 1px обязателен — в колоночном flex линия схлопывается в ноль.
   Линия терракотовая — единственный тёплый штрих в подвале */
.sign-line{height:1px;flex:0 0 1px;width:100%;background:rgba(204,115,87,.85);}
.sign-name{font-size:15pt;font-weight:700;line-height:1.36;color:%(LIGHT)s;margin-top:5.4mm;}
.sign-role{font-size:12.5pt;line-height:1.5;color:%(MUTED)s;margin-top:.6mm;}
"""
# Подстановка палитры — по токенам %(NAME)s регэкспом, а НЕ оператором %:
# в CSS есть свои проценты (width:100%), и «%» падает на них с TypeError.
CSS = re.sub(r"%\((\w+)\)s", lambda m: globals()[m.group(1)], CSS)


# ── декор: частицы ───────────────────────────────────────────────────────────
# Треугольник задаётся явными вершинами (polygon), а не transform+scale:
# при scale масштабируется и обводка, и контурные частицы разной величины
# получают разную толщину линии. Координаты — миллиметры листа.
def _tri(x, y, s, ang):
    pts = []
    for k in range(3):
        a = ang + k * 2 * math.pi / 3
        pts.append(f"{x + s * math.cos(a):.2f},{y + s * math.sin(a):.2f}")
    return " ".join(pts)


# Облако частиц: не гауссово пятно, а мягкое кольцо (r≈N(24,9) мм) — у мозга
# на сайте-образце частицы гуще по контуру, чем в середине. Слегка сплюснуто и
# повёрнуто, чтобы не читалось как правильный круг.
CLOUD = dict(cx=152.0, cy=200.0, r_mean=24.0, r_sd=9.0, n=470, squash=0.82, tilt=-0.28)
FOOT_Y = 236.0      # ниже — подвал (подпись, реквизиты): частиц облака там нет
SEED = 7            # детерминированная россыпь: одинаковый лист при каждом запуске


def particles_svg(seed: int = SEED) -> str:
    rnd = random.Random(seed)
    out = []

    def emit(x, y, s, op, color, outline):
        if not (8 <= x <= 202 and 8 <= y <= 289):
            return
        pts = _tri(x, y, s, rnd.uniform(0, 2 * math.pi))
        if outline:
            out.append(f'<polygon points="{pts}" fill="none" stroke="{color}" '
                       f'stroke-width=".22" stroke-linejoin="round" opacity="{op:.2f}"/>')
        else:
            out.append(f'<polygon points="{pts}" fill="{color}" opacity="{op:.2f}"/>')

    def pick_color(p_light, p_terra):
        u = rnd.random()
        if u < p_terra: return TERRA
        if u < p_terra + p_light: return LIGHT
        return BLUE if rnd.random() < .6 else BLUE_DEEP

    # 1) облако-кольцо справа внизу
    c = CLOUD
    ct, st = math.cos(c["tilt"]), math.sin(c["tilt"])
    for _ in range(c["n"]):
        r = max(0.0, rnd.gauss(c["r_mean"], c["r_sd"]))
        a = rnd.uniform(0, 2 * math.pi)
        dx, dy = r * math.cos(a), r * math.sin(a) * c["squash"]
        x = c["cx"] + dx * ct - dy * st
        y = c["cy"] + dx * st + dy * ct
        if y > FOOT_Y:
            continue
        # плотность и яркость — по близости к кольцу
        near = math.exp(-((r - c["r_mean"]) / 9.0) ** 2)
        s = 0.45 + rnd.random() ** 2 * 1.9
        op = 0.14 + 0.52 * near * rnd.uniform(.55, 1.0)
        emit(x, y, s, op, pick_color(p_light=.16, p_terra=.05), outline=rnd.random() < .28)
    # несколько крупных контурных — на сайте-образце масштабы частиц смешаны
    for _ in range(7):
        r = rnd.gauss(c["r_mean"] + 4, 6); a = rnd.uniform(0, 2 * math.pi)
        dx, dy = r * math.cos(a), r * math.sin(a) * c["squash"]
        x = c["cx"] + dx * ct - dy * st; y = c["cy"] + dx * st + dy * ct
        if y > FOOT_Y: continue
        emit(x, y, rnd.uniform(3.0, 5.2), rnd.uniform(.12, .22),
             LIGHT if rnd.random() < .4 else BLUE, outline=True)

    # 2) поток частиц снизу к облаку — как у мозга на сайте-образце есть «ствол», а у
    # ленты company — вход снизу. Идёт по зазору подвала между реквизитами
    # (x ≤ 71 мм) и подписью (блок 80 мм у правого поля: x ≥ 110 мм; сама
    # картинка подписи y 245–262 мм), поэтому текст и росчерк не задевает.
    for _ in range(150):
        t = rnd.random() ** 0.85                     # гуще у облака
        # кривая (94,290) → (106,252) → (132,222) — квадратичный Безье
        p0, p1, p2 = (94.0, 290.0), (106.0, 252.0), (132.0, 222.0)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        spread = 5.5 + 9.0 * t
        x += rnd.gauss(0, spread); y += rnd.gauss(0, spread * .6)
        if x < 78 or (y > 240 and x > 108):         # не лезть в реквизиты и подпись
            continue
        s = 0.45 + rnd.random() ** 2 * 1.6
        op = (0.10 + 0.30 * t) * rnd.uniform(.6, 1.0)
        emit(x, y, s, op, pick_color(p_light=.18, p_terra=.04), outline=rnd.random() < .35)

    # 3) россыпь по всему листу — фактура. Смещение вправо было сильным
    # (показатель .72) и оставляло нижнюю левую четверть голой: шесть значков
    # висели на пустом фоне, лист перевешивал вправо. Показатель поднят к
    # равномерному, количество увеличено — пустота заполняется, но облако
    # справа остаётся главным.
    for _ in range(190):
        x = 8 + 194 * (rnd.random() ** 0.92)
        y = 8 + 281 * rnd.random()
        s = 0.6 + rnd.random() ** 1.5 * 2.2
        op = rnd.uniform(.08, .26)
        emit(x, y, s, op, pick_color(p_light=.28, p_terra=.05), outline=rnd.random() < .55)

    return ('<svg class="particles" viewBox="0 0 210 297">' + "".join(out) + '</svg>')


def glow_html() -> str:
    c = CLOUD
    d = 118.0
    return (f'<div class="glow" style="left:{c["cx"] - d / 2:.1f}mm;top:{c["cy"] - d / 2 - 4:.1f}mm;'
            f'width:{d:.1f}mm;height:{d:.1f}mm"></div>')


# ── декор: парящие логотипы инструментов курса ─────────────────────────────
# Раскладка фиксированная, не случайная: лист одинаковый при каждой сборке, и
# медальоны гарантированно обходят текст. Проверяет это check_medals.py.
# Зоны (мм листа), перемерены рендером 14.09 ПОСЛЕ уплотнения листа (кегли
# +12–18%, пояснительная строка под названием): текстовый блок кончается на
# y 147.1 (низ .sub) — на 12.7 мм ниже прежнего, подвал начинается с y 244.6.
# Поэтому верхний ряд значков опущен: n8n 152→162, huggingface 153→163,
# perplexity 147→154 — иначе они наезжали на последние строки текста (замер
# показывал зазор −7.8 мм у n8n). Диаметры подняты на ~10%: лист стал плотнее
# сверху, и мелкие значки в пустой середине смотрелись потерянно.
# Орбита прежняя — вокруг облака частиц (152,200), «инструменты вокруг мозга».
# Двухстрочная пояснительная строка снова опустит блок и упрётся в значки,
# это ловит check_medals.py.
# Hermes (Nous Research) места не получил: его favicon.svg — текстовый символ ☤,
# который браузер набирает любым шрифтом, а logo.png — иллюстрация-маскот, не знак.
# Рисовать кадуцей самим — выдумывать чужой бренд, поэтому файла в ассетах нет и
# слот пропускается.
AI_DIR = BRAND_DIR.parent / "ai_logos"
# (файл, cx, cy, диаметр мм, непрозрачность, цвет знака). Непрозрачность не ниже .78:
# при .60–.66 GitHub, Docker, Telegram и ElevenLabs на листе читались бледно.
AI_SPOTS = [
    ("claude",       152, 170, 16.5, 1.00, TERRA),   # главный инструмент — крупнее и в фирменной терракоте
    ("openai",       116, 192, 14.0, .95, LIGHT),
    ("cursor",       186, 184, 13.0, .92, LIGHT),
    ("googlegemini", 176, 222, 13.0, .94, BLUE),
    ("deepseek",     128, 223, 12.0, .88, LIGHT),
    ("perplexity",   183, 154, 11.0, .82, LIGHT),   # 189 выносило кружок за правое поле контента (190 мм)
    ("hermes",       181, 120, 10.0, .82, LIGHT),
    ("github",        60, 172, 13.0, .90, LIGHT),
    ("n8n",           30, 162, 12.0, .84, LIGHT),
    ("telegram",      78, 205, 12.5, .90, BLUE),
    ("docker",        27, 200, 11.0, .80, LIGHT),
    ("huggingface",   95, 163, 11.0, .80, LIGHT),
    ("elevenlabs",    48, 228, 10.0, .78, LIGHT),
]


def _ai_svg(name, color):
    f = AI_DIR / f"{name}.svg"
    if not f.exists():
        return None
    s = f.read_text(encoding="utf-8")
    s = re.sub(r"<title>.*?</title>", "", s, flags=re.S)
    # у Simple Icons заливка не задана (по умолчанию чёрная — пропадёт на тёмном)
    # Цвет задаёт CSS (.medal color → fill:currentColor). Раньше здесь был
    # регэксп r"<svg\b": при вставке патчем «\b» записался в файл настоящим
    # символом backspace (0x08), шаблон не совпадал, и все знаки остались ЧЁРНЫМИ.
    # str.replace экранирования не имеет — ломаться нечему.
    s = s.replace("<svg", '<svg fill="currentColor"', 1)
    return s


def ai_logos_html() -> str:
    out = []
    for name, cx, cy, d, op, color in AI_SPOTS:
        svg = _ai_svg(name, color)
        if svg is None:           # знака нет в ассетах — место просто пустое
            continue
        out.append(f'<div class="medal ai-{name}" style="left:{cx - d / 2:.1f}mm;top:{cy - d / 2:.1f}mm;'
                   f'width:{d:.1f}mm;height:{d:.1f}mm;opacity:{op:.2f};color:{color}">{svg}</div>')
    return "".join(out)


class VibeTheme(Theme):
    def decor_html(self, ctx):
        return glow_html() + particles_svg(ctx.get("seed", SEED)) + ai_logos_html()

    def logos_html(self, uris, ctx):
        """Знак + словесная часть бренда: «Your School» и «by Your Name».
        Тексты — из ctx["brand"] (см. докстринг модуля), по умолчанию заглушки."""
        v = uris[0] if uris else ""
        b = ctx.get("brand") or {}
        name = html.escape(str(b.get("name", "Your")))
        tag = html.escape(str(b.get("tag", "School")))
        by = html.escape(str(b.get("by", "by Your Name")))
        mark = f'<img class="vmark" src="{v}" alt="{name} {tag}">' if v else ""
        return (mark +
                '<div class="wm">'
                f'<div class="wm1">{name}<span class="wm-ac">{tag}</span></div>'
                f'<div class="wm2">{by}</div>'
                '</div>')

    def name_size(self, fio):
        """Oswald 600 капсом: гарнитура узкая, поэтому кегль крупнее, чем у
        Segoe в company. Линейка — «Ивановская Александра Владимировна» (33 зн.)
        в колонке 172 мм; промерено рендером (см. отчёт сборки темы)."""
        # Замер 12.09 (после починки страховки, см. make_certs.SCRIPT): Oswald 600
        # капсом с трекингом .015em — 0.54–0.56 em на знак, то есть КАК Segoe
        # строчными в company. Колонка 643px: pt ≈ 815 / n с запасом 5%.
        # 14.09: лист уплотнён (кегли +12–18%), имя подросло вместе с ним, но
        # только там, где это допускает та же формула 815/n: у 20 знаков потолок
        # 40.7pt, поэтому вместо общего подъёма добавлена ступень 16–17 знаков
        # (потолок 48pt).
        # Граница первой ступени 14→15 знаков: при 14 имена вроде «Соколова
        # Полина» и «Кузнецов Михаил» (по 15) получали 46pt против 50pt у
        # остальных имён партии — на соседних листах разница в 8% видна глазом, а запаса
        # хватало (строка 596 из 643 px). Поймала вычитка листов, не чекеры:
        # каждый лист по отдельности был безупречен, дефект жил В СРАВНЕНИИ.
        n = len(fio)
        if n <= 15: return 50
        if n <= 17: return 46
        if n <= 20: return 40
        if n <= 25: return 32
        if n <= 29: return 28
        if n <= 33: return 24.5
        if n <= 40: return 20
        return 22        # >40 знаков: капс снимается (.long), строчные уже


THEME = VibeTheme(
    name="vibe",
    css=CSS,
    fonts=FONTS,
    logo_fill=LIGHT,               # для сторонних логотипов с чёрной заливкой
    default_logos=(BRAND_DIR / "vibe_mark.svg",),
    labels={
        "title": "Сертификат",
        "lead_in": "— подтверждает, что",
        "vol": "в объёме",
        "issuer_l1": "Выдан",
    },
)
