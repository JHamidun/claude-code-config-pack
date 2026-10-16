# -*- coding: utf-8 -*-
"""Контракт темы сертификата.

Тема отвечает за ВИД: палитру, шрифты, декор, логотипы, кегль имени под свою
гарнитуру и (при желании) собственный HTML-скелет. Движок (scripts/make_certs.py)
отвечает за ДАННЫЕ и логику: список людей, склонение, номера, рендер, проверки.

Классы разметки — общий контракт с чекерами scripts/check_*.py, менять нельзя
без правки чекеров:
  .card   карточка на подложке          .wrap    контентный слой (flex-колонка)
  .decor  слой декора под контентом     .medal   круглый медальон (если есть)
  .head .logos .title                   .logos .sep — разделитель логотипов
  .body .lead-in .name .did .prog .prog-sub .vol .hours .sub
          .prog-sub — пояснение к названию программы обычными словами
          (для предъявления вне курса); пустое — блока в HTML нет вовсе
  .foot .issuer .l1 .l2 .cno            .sign .sign-img .sign-line .sign-name .sign-role

ГОЧИ, которые здесь уже оплачены (не повторять):
  · в колоночном flex тонкая полоска (height:1–2px) схлопывается в НОЛЬ —
    ей нужен flex:0 0 <высота>; на глаз незаметно, ловит только check_layout.py;
  · смотреть рендер в РЕАЛЬНОМ масштабе (device_scale_factor=1): в 2× дефекты
    (наложения, схлопнутые линии) не видны;
  · у SVG-элементов className — SVGAnimatedString, а не строка: обход DOM
    в чекерах берёт .baseVal;
  · чёрная заливка логотипа-SVG пропадает на тёмном фоне и желтит кремовым
    на светлом — цвет перекраски (logo_fill) выбирается под фон темы;
  · сложный фирменный знак (пробовали Perplexity) в круге 12 мм — каша из
    линий; для мелких медальонов нужны простые формы;
  · Inter и Manrope в %LOCALAPPDATA%/Microsoft/Windows/Fonts БИТЫЕ (303 КБ
    переводов строки) — Chromium молча подставляет другой шрифт. Тема с
    веб-шрифтами объявляет их в `fonts`, движок вшивает data-URI (scripts/
    fonts.py) и печатает, какие семейства реально загрузились.
"""
from dataclasses import dataclass, field
from pathlib import Path
from string import Template

SKILL_DIR = Path(__file__).resolve().parent.parent
BRAND_DIR = SKILL_DIR / "assets" / "brand"

# Общий скелет. Подстановка — string.Template ($var), поэтому фигурные скобки
# в CSS и JS экранировать не нужно. Тема может подменить целиком (self.template),
# сохранив имена классов из контракта выше.
DEFAULT_TEMPLATE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>Сертификат — $name</title><style>$fonts_css$css</style></head><body>
<div class="card">
  <div class="decor">$decor</div>

  <div class="wrap">
    <div class="head">
      <div class="logos">$logos</div>
      <div class="title">$title</div>
    </div>

    <div class="body">
      <div class="lead-in">$lead_in</div>
      <div class="name$name_cls">$name</div>
      <div class="did">$verb</div>
      <div class="prog$prog_cls">$program</div>
      $program_sub
      <div class="vol">$vol</div>
      <div class="hours">$hours</div>
      <div class="sub">$subline</div>
    </div>

    <div class="foot">
      <div class="issuer">
        <div class="l1">$issuer_l1</div>
        <div class="l2">$issuer_l2</div>
        <div class="cno">$cno</div>
      </div>
      <div class="sign">
        <div class="sign-img">$sign</div>
        <div class="sign-line"></div>
        <div class="sign-name">$sign_name</div>
        <div class="sign-role">$sign_role</div>
      </div>
    </div>
  </div>
</div>
$script
</body></html>"""


@dataclass
class Theme:
    name: str
    css: str                                 # CSS темы; "{name_size}" → кегль в pt
    fonts: tuple = ()                        # Google Fonts: ('Oswald:wght@600;700', …)
    logo_fill: str = "#FFFFFF"               # во что перекрашивать чёрный в SVG логотипов
    default_logos: tuple = ()                # Path'ы логотипов шапки по умолчанию
    labels: dict = field(default_factory=lambda: {
        "title": "Сертификат",
        "lead_in": "Сертификат подтверждает, что",
        "vol": "в объёме",
        "issuer_l1": "Выдан",
    })
    template: str = DEFAULT_TEMPLATE
    # Длиннее этого — капс снимается (класс .long): капс стирает силуэт слова,
    # на кириллице сильнее; check_type.py ругается на капс длиннее 40 знаков.
    caps_limit: int = 40

    # ── что тема переопределяет ────────────────────────────────────────────
    def name_size(self, fio: str) -> float:
        """Кегль имени (pt) под длину: строка обязана идти одной строкой."""
        n = len(fio)
        if n <= 14: return 42
        if n <= 20: return 36
        if n <= 25: return 31.5
        if n <= 29: return 28
        if n <= 33: return 24.5
        return 22.5

    def decor_html(self, ctx: dict) -> str:
        """HTML слоя декора (внутри .decor). ctx — конфиг + данные человека."""
        return ""

    def logos_html(self, uris: list, ctx: dict) -> str:
        """Шапка: логотипы через тонкий разделитель."""
        parts = []
        for i, u in enumerate(uris):
            if i:
                parts.append('<div class="sep"></div>')
            parts.append(f'<img src="{u}" alt="">')
        return "".join(parts)

    def render_css(self, fio: str) -> str:
        return self.css.replace("{name_size}", str(self.name_size(fio)))

    def html(self, vars: dict) -> str:
        return Template(self.template).safe_substitute(vars)
