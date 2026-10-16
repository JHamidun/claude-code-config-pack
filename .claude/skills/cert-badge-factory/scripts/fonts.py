# -*- coding: utf-8 -*-
"""Веб-шрифты для тем: Google Fonts → локальный кэш → @font-face с data-URI.

Зачем это вообще:
  · файлы Inter и Manrope в %LOCALAPPDATA%/Microsoft/Windows/Fonts БИТЫЕ
    (все ровно ~303 КБ — это переводы строки, а не глифы). Chromium молча
    уходит в подстановку, и «Manrope» на рендере оказывается Segoe UI.
    Поэтому тема НЕ полагается на системные шрифты — тянет свои;
  · Oswald в системе нет вовсе;
  · подключать шрифт как url(file:///...) со страницы file:// нельзя —
    Chromium блокирует такую загрузку CORS-политикой (origin 'null'),
    ошибка видна только в консоли, на листе — подстановка. Поэтому шрифты
    вшиваются в HTML data-URI: файл самодостаточен, одинаково рендерится
    в движке, в чекерах и в браузере получателя.

Кэш: assets/fonts/<slug>.css (+ *.woff2 рядом). Первый вызов ходит в сеть
(fonts.googleapis.com, нужен UA настоящего Chrome — иначе отдадут ttf без
unicode-range). Дальше — офлайн.

Берём только сабсеты latin / cyrillic / cyrillic-ext: vietnamese, greek и
latin-ext нам не нужны, а каждый сабсет — это ещё ~20 КБ base64 в каждом
из десятков HTML.
"""
import re, sys, base64, hashlib, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE.parent / "assets" / "fonts"
KEEP_SUBSETS = ("latin", "cyrillic", "cyrillic-ext")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _fetch(url: str, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def _slug(specs) -> str:
    return hashlib.sha1("|".join(specs).encode()).hexdigest()[:12]


def _ensure_cached(specs) -> Path:
    """Возвращает путь к CSS в кэше, скачивая при необходимости."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    css_path = FONT_DIR / f"{_slug(specs)}.css"
    if css_path.exists():
        return css_path
    q = "&".join("family=" + s.replace(" ", "+") for s in specs)
    url = f"https://fonts.googleapis.com/css2?{q}&display=block"
    sys.stderr.write(f"шрифты: тяну из Google Fonts ({', '.join(specs)})\n")
    css = _fetch(url)
    # блоки идут парами «/* subset */ @font-face {...}»
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)
    if not blocks:
        raise RuntimeError("Google Fonts вернул CSS без сабсетов — проверь UA/ответ")
    out = []
    for subset, block in blocks:
        if subset not in KEEP_SUBSETS:
            continue
        m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not m:
            continue
        furl = m.group(1)
        fname = hashlib.sha1(furl.encode()).hexdigest()[:16] + ".woff2"
        fpath = FONT_DIR / fname
        if not fpath.exists():
            fpath.write_bytes(_fetch(furl, binary=True))
        out.append(f"/* {subset} */\n" + block.replace(furl, fname))
    css_path.write_text("\n".join(out), encoding="utf-8")
    sys.stderr.write(f"шрифты: закэшировано {len(out)} файлов → {FONT_DIR}\n")
    return css_path


def fontface_css(specs) -> str:
    """@font-face для списка спецификаций вида 'Oswald:wght@600;700'
    с шрифтами, вшитыми data-URI. Пустой список → пустая строка."""
    if not specs:
        return ""
    css = _ensure_cached(list(specs)).read_text(encoding="utf-8")

    def inline(m):
        p = FONT_DIR / m.group(1)
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f"url(data:font/woff2;base64,{b64})"
    return re.sub(r"url\(([\w]+\.woff2)\)", inline, css)


def families(specs):
    """['Oswald:wght@600;700'] → ['Oswald'] — для проверки загрузки."""
    return [s.split(":")[0] for s in specs]


# Проверка, что шрифт РЕАЛЬНО применился, а не подставился. document.fonts
# .check() врёт: возвращает true и когда @font-face с таким именем нет вовсе
# (значит, «доступен системный»). Смотрим статус каждого FontFace по имени.
FONTS_PROBE = """(fams) => {
  const st = {};
  for (const f of document.fonts) {
    const k = f.family.replace(/["']/g, '');
    if (!fams.includes(k)) continue;
    st[k] = st[k] || {loaded: 0, total: 0};
    st[k].total++; if (f.status === 'loaded') st[k].loaded++;
  }
  return fams.map(f => [f, st[f] ? st[f].loaded : -1, st[f] ? st[f].total : 0]);
}"""


if __name__ == "__main__":
    specs = sys.argv[1:] or ["Oswald:wght@600;700", "Manrope:wght@400;700",
                             "JetBrains Mono:wght@400;500"]
    css = fontface_css(specs)
    n = css.count("@font-face")
    sys.stderr.write(f"@font-face блоков: {n}, размер CSS: {len(css)//1024} КБ\n")
