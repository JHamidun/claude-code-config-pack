# -*- coding: utf-8 -*-
"""Проверка типографики — меряет ВЫЧИСЛЕННЫЕ кегли в браузере.

Появился после того, как заказчик сказал «текст мелкий», а замер показал семь
кеглей ниже пола читаемости (от 8.3 до 10.9 px при норме 11). На глаз это
неотличимо от «просто аккуратно», числом — очевидно.

Пол по канону design-taste, пункт 18:
  · тело — не ниже 14px (норма 16)
  · функциональный текст (подписи, метки, даты, ячейки) — не ниже 11px,
    и пол держится даже в подвале
  · исключения: sup/sub, sr-only, код; здесь — микротекст-лента защитного узора

Плюс ловит родню из пунктов 17 и 19:
  · интерлиньяж тела ниже 1.3 (строки слипаются)
  · трекинг вне диапазона -0.04em … +0.05em для НЕ-капсовых блоков
  · блоки капса длиннее 40 знаков (капс стирает силуэт слова, на кириллице сильнее)

Запуск:
    python check_type.py                  # _html/*.html
    python check_type.py _var/LEAN_*.html
    python check_type.py --floor 12       # поднять требуемый пол
"""
import sys, glob, argparse
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent

# Что не обязано соблюдать пол читаемости — и почему именно это.
# Канон (п. 18) выводит пол для текста, который ЧИТАЮТ. Гравировка на печати и
# защитный узор по краю читаются не построчно, а опознаются как элемент бланка:
# на настоящей печати кольцевая надпись тоже мельче основного текста.
# Исключение узкое и названо поимённо — расширять его «чтобы стало зелено» нельзя,
# это будет выхолащивание проверки, а не её настройка.
EXEMPT = ".microtext, .medal, .guilloche, .seal"

# Интерлиньяж 1.5-1.7 — правило для ТЕЛА. У дисплейных кеглей плотная выключка
# норма: чем крупнее шрифт, тем меньше нужен просвет. Поэтому проверяем полосу
# 13-20px, а имя в 30-42pt под правило не подводим.
BODY_MIN, BODY_MAX = 13.0, 20.0

PROBE = """(cfg) => {
  const {floor, exempt, bodyMin, bodyMax} = cfg;
  const small = [], lead = [], track = [], caps = [];
  const seen = new Set();

  // у SVG-элементов className — объект SVGAnimatedString, а не строка
  const nameOf = el => (typeof el.className === 'string' && el.className)
    || (el.className && el.className.baseVal) || el.tagName.toLowerCase();

  document.querySelectorAll('*').forEach(el => {
    if (el.closest(exempt)) return;
    // только элементы с собственным непустым текстом
    const own = [...el.childNodes]
      .filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ').trim();
    if (!own) return;

    const s = getComputedStyle(el);
    const px = parseFloat(s.fontSize);
    const sample = own.slice(0, 42);
    const key = nameOf(el) + '|' + px + '|' + sample;
    if (seen.has(key)) return;
    seen.add(key);

    if (px < floor) small.push({cls: nameOf(el), px: +px.toFixed(1), sample});

    const lh = parseFloat(s.lineHeight);
    if (lh && px >= bodyMin && px <= bodyMax && lh / px < 1.3)
      lead.push({cls: nameOf(el), ratio: +(lh / px).toFixed(2), sample});

    const isCaps = s.textTransform === 'uppercase';
    const ls = parseFloat(s.letterSpacing);
    const isMono = /mono|consolas|courier/i.test(s.fontFamily);
    if (!isCaps && !isMono && ls && px) {
      const em = ls / px;
      if (em < -0.04 || em > 0.05)
        track.push({cls: nameOf(el), em: +em.toFixed(3), sample});
    }
    if (isCaps && own.length > 40)
      caps.push({cls: nameOf(el), len: own.length, sample});
  });
  return {small, lead, track, caps};
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="*", default=["_html/*.html"])
    ap.add_argument("--floor", type=float, default=11.0,
                    help="пол кегля в px для функционального текста (по умолчанию 11)")
    a = ap.parse_args()

    files = []
    for p in (a.patterns or ["_html/*.html"]):
        files += sorted(glob.glob(str(HERE / p)) or glob.glob(p))
    if not files:
        sys.stderr.write("нечего проверять\n"); return

    from playwright.sync_api import sync_playwright
    agg = {"small": {}, "lead": {}, "track": {}, "caps": {}}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1123, "height": 794})
        for f in files:
            pg.goto(Path(f).resolve().as_uri())
            pg.evaluate("document.fonts.ready")   # веб-шрифты тем грузятся асинхронно
            pg.wait_for_timeout(120)
            r = pg.evaluate(PROBE, {"floor": a.floor, "exempt": EXEMPT, "bodyMin": BODY_MIN, "bodyMax": BODY_MAX})
            for kind in agg:
                for item in r[kind]:
                    k = (item.get("cls"), item.get("px") or item.get("ratio")
                         or item.get("em") or item.get("len"))
                    agg[kind].setdefault(k, item)
        b.close()

    sys.stderr.write(f"проверено файлов: {len(files)} · пол кегля {a.floor}px "
                     f"(исключение: {EXEMPT})\n\n")
    ok = True

    if agg["small"]:
        ok = False
        sys.stderr.write(f"!! КЕГЛЬ НИЖЕ ПОЛА — {len(agg['small'])} шт.\n")
        for it in sorted(agg["small"].values(), key=lambda x: x["px"]):
            sys.stderr.write(f"   {it['px']:5.1f}px  .{it['cls'][:28]:30} «{it['sample'][:34]}»\n")
    if agg["lead"]:
        ok = False
        sys.stderr.write(f"\n!! ИНТЕРЛИНЬЯЖ НИЖЕ 1.3 — {len(agg['lead'])} шт.\n")
        for it in agg["lead"].values():
            sys.stderr.write(f"   {it['ratio']:5.2f}   .{it['cls'][:28]:30} «{it['sample'][:34]}»\n")
    if agg["track"]:
        ok = False
        sys.stderr.write(f"\n!! ТРЕКИНГ ВНЕ ДИАПАЗОНА — {len(agg['track'])} шт.\n")
        for it in agg["track"].values():
            sys.stderr.write(f"   {it['em']:+.3f}em .{it['cls'][:28]:30} «{it['sample'][:34]}»\n")
    if agg["caps"]:
        ok = False
        sys.stderr.write(f"\n!! ДЛИННЫЙ КАПС (>40 знаков) — {len(agg['caps'])} шт.\n")
        for it in agg["caps"].values():
            sys.stderr.write(f"   {it['len']:3} зн. .{it['cls'][:28]:30} «{it['sample'][:34]}»\n")

    if ok:
        sys.stderr.write("✓ типографика чистая: кегли выше пола, интерлиньяж и трекинг в норме,\n"
                         "  длинных капсовых блоков нет\n")


if __name__ == "__main__":
    main()
