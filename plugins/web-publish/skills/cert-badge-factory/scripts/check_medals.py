# -*- coding: utf-8 -*-
"""Пересечения ВСЕХ медальонов со ВСЕМИ текстовыми строками.

check_layout.py сверяет с текстом только первый .medal (querySelector) и
только четыре контентных блока. Здесь — каждый медальон против каждой
строки текста: для текста берутся прямоугольники Range.getClientRects(),
то есть реальные строки, а не бокс блока с полями (у .prog max-width 172 мм,
его бокс шире самих строк).

Запуск:
    python check_medals.py                 # _html/*.html
    python check_medals.py _var/LEK_*.html
"""
import sys, glob
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent

TEXT = [".title", ".logos", ".lead-in", ".name", ".did", ".prog", ".prog-sub", ".vol", ".hours",
        ".sub", ".issuer .l1", ".issuer .l2", ".issuer .cno", ".sign-img",
        ".sign-line", ".sign-name", ".sign-role"]

PROBE = """(sel) => {
  const out = [];
  const lineRects = el => {
    // строки текста, а не бокс блока
    const r = document.createRange(); r.selectNodeContents(el);
    const rs = [...r.getClientRects()].filter(b => b.width > 0 && b.height > 0);
    return rs.length ? rs : [el.getBoundingClientRect()];
  };
  const hit = (a, b) => !(a.right <= b.left || a.left >= b.right ||
                          a.bottom <= b.top || a.top >= b.bottom);
  const medals = [...document.querySelectorAll('.medal')];
  medals.forEach((m, i) => {
    const mb = m.getBoundingClientRect();
    const icon = m.querySelector('svg');
    const name = `медальон ${i+1} (${m.className.replace('medal ','')})`;
    if (mb.width < 1 || mb.height < 1) out.push(`${name} схлопнулся`);
    if (!icon || icon.getBoundingClientRect().width < 1) out.push(`${name}: значок не отрисован`);
    for (const s of sel) for (const el of document.querySelectorAll(s)) {
      for (const lb of lineRects(el)) {
        if (hit(mb, lb)) {
          const dx = Math.min(mb.right, lb.right) - Math.max(mb.left, lb.left);
          const dy = Math.min(mb.bottom, lb.bottom) - Math.max(mb.top, lb.top);
          out.push(`${name} пересекает ${s} на ${dx.toFixed(0)}×${dy.toFixed(0)} px`);
        }
      }
    }
  });
  return {n: medals.length, out};
}"""


def main():
    pats = sys.argv[1:] or ["_html/*.html"]
    files = []
    for p in pats:
        files += sorted(glob.glob(str(HERE / p)) or glob.glob(p))
    if not files:
        sys.stderr.write("нечего проверять\n"); return

    from playwright.sync_api import sync_playwright
    bad, n_medals = [], 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 794, "height": 1123})
        for f in files:
            pg.goto(Path(f).resolve().as_uri())
            pg.evaluate("document.fonts.ready")   # веб-шрифты тем грузятся асинхронно
            pg.wait_for_timeout(130)
            r = pg.evaluate(PROBE, TEXT)
            n_medals = r["n"]
            if r["out"]:
                bad.append((Path(f).stem, r["out"]))
        b.close()

    sys.stderr.write(f"проверено файлов: {len(files)} · медальонов на листе: {n_medals} · "
                     f"текстовых селекторов: {len(TEXT)}\n")
    if not bad:
        sys.stderr.write("✓ пересечений медальонов с текстом нет\n"); return
    for n, issues in bad:
        sys.stderr.write(f"  !! {n}\n")
        for i in issues:
            sys.stderr.write(f"       · {i}\n")
    sys.stderr.write(f"\nфайлов с пересечениями: {len(bad)} из {len(files)}\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
