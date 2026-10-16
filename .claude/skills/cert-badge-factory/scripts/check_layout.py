# -*- coding: utf-8 -*-
"""Машинная проверка вёрстки сертификатов — меряет геометрию в браузере.

Появился после того, как полоска под именем две итерации имела высоту НОЛЬ
(в колоночном flex тонкие элементы схлопываются), а на глаз это было незаметно.
Смотреть один-два превью и считать, что остальные такие же, — ненадёжно.

Проверяет по каждому файлу:
  · имя не вылезло за правое поле и не обрезано по ширине
  · тексты в карточках не подрезаны по высоте
  · полоска под именем имеет ненулевую высоту
  · контент влезает в лист по высоте
  · декоративные элементы не пересекают контентные

Запуск:
    python check_layout.py                # проверить _html/*.html
    python check_layout.py _var/A_*.html  # проверить конкретные файлы
"""
import sys, glob
from pathlib import Path

sys.stderr.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent

PROBE = """() => {
  const out = [];
  const W = document.body.clientWidth, H = document.body.clientHeight;
  const q = s => document.querySelector(s);

  const name = q('.name');
  if (name) {
    const b = name.getBoundingClientRect();
    if (b.right > W - 30) out.push(`имя за правым полем (${Math.round(b.right)} > ${W-30})`);
    if (name.scrollWidth > name.clientWidth + 1) out.push('имя обрезано по ширине');
    if (b.height < 8) out.push('имя схлопнулось');
  } else out.push('НЕТ .name');

  document.querySelectorAll('.mod .t, .skill, .tl-item').forEach((el, i) => {
    if (el.scrollHeight > el.clientHeight + 1) out.push(`блок ${i+1} обрезан по высоте`);
  });

  const u = q('.uline');
  if (u && u.getBoundingClientRect().height < 1) out.push('линия под именем схлопнулась');

  const w = q('.wrap');
  if (w && w.scrollHeight > w.clientHeight + 2)
    out.push(`контент не влезает по высоте (+${Math.round(w.scrollHeight - w.clientHeight)}px)`);

  // правая панель режет своё переполнение (overflow:hidden) — .wrap его не видит
  const pn = q('.panel');
  if (pn && pn.scrollHeight > pn.clientHeight + 1)
    out.push(`панель не влезает по высоте (+${Math.round(pn.scrollHeight - pn.clientHeight)}px)`);
  const lf = q('.left');
  if (lf && lf.scrollHeight > lf.clientHeight + 1)
    out.push(`левая колонка не влезает по высоте (+${Math.round(lf.scrollHeight - lf.clientHeight)}px)`);

  // тонкие полоски и разделители: в колоночном flex схлопываются в ноль
  for (const [n, s] of [['разделитель логотипов','.logos .sep'], ['линия подписи','.sign-line'],
                        ['разделитель панели','.pdiv']]) {
    const e = q(s); if (!e) continue;
    const b = e.getBoundingClientRect();
    if (b.width < .5 || b.height < .5) out.push(`${n} схлопнулся (${b.width.toFixed(1)}×${b.height.toFixed(1)})`);
  }

  // печать целиком внутри панели — кольцевой текст не должен резаться краем
  const md = q('.medal');
  if (md && pn) {
    const a = md.getBoundingClientRect(), p = pn.getBoundingClientRect();
    if (a.left < p.left || a.right > p.right || a.top < p.top || a.bottom > p.bottom)
      out.push('печать выходит за панель');
  }

  // декор не должен пересекать контент
  const overlaps = (a, b) => a && b &&
    !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
  const R = s => { const e = q(s); return e ? e.getBoundingClientRect() : null; };
  const decor = [['медальон','.medal'], ['гильош','.guilloche'], ['констелляция','.constellation']];
  const content = [['имя','.name'], ['карточки','.mods'], ['подпись','.sign'],
                   ['программа','.prog'], ['пояснение к программе','.prog-sub'],
                   ['навыки','.skills']];
  for (const [dn, ds] of decor) for (const [cn, cs] of content) {
    const d = R(ds), c = R(cs);
    if (d && c && overlaps(d, c)) out.push(`${dn} пересекает: ${cn}`);
  }
  return out;
}"""


def main():
    pats = sys.argv[1:] or ["_html/*.html"]
    files = []
    for p in pats:
        files += sorted(glob.glob(str(HERE / p)) or glob.glob(p))
    if not files:
        sys.stderr.write("нечего проверять\n"); return

    from playwright.sync_api import sync_playwright
    bad = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1123, "height": 794})
        for f in files:
            pg.goto(Path(f).resolve().as_uri())
            # веб-шрифты (тема vibe, data-URI) грузятся асинхронно: без ожидания
            # геометрия меряется по подстановке и врёт в обе стороны
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(130)
            issues = pg.evaluate(PROBE)
            if issues:
                bad.append((Path(f).stem, issues))
        b.close()

    sys.stderr.write(f"проверено файлов: {len(files)}\n")
    if not bad:
        sys.stderr.write("✓ дефектов вёрстки не найдено\n")
        return
    for n, issues in bad:
        sys.stderr.write(f"  !! {n}\n")
        for i in issues:
            sys.stderr.write(f"       · {i}\n")
    sys.stderr.write(f"\nфайлов с дефектами: {len(bad)} из {len(files)}\n")


if __name__ == "__main__":
    main()
