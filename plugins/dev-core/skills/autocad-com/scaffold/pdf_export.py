# -*- coding: utf-8 -*-
"""
PDF-альбом из SVG-листов через headless Chromium --print-to-pdf. Листы разных форматов (A3, A2, A3×3, A4×N)
собираются в один документ: на каждый уникальный размер — именованная @page, лист привязан через `page:`.
Порядок страниц = порядок файлов NN_<id>.svg.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path

from render_png import _find_browser, svg_size_mm


def _print_to_pdf(html_text, pdf_path, timeout=300):
    pdf_path = Path(pdf_path).resolve()
    browser = _find_browser()
    if browser is None:
        raise RuntimeError("Не найден Chrome/Edge/Chromium для печати PDF")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "album.html"
        profile = Path(td) / "chrome-profile"
        page.write_text(html_text, encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
               f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}", page.as_uri()]
        if os.name != "nt":
            cmd[1:1] = ["--no-sandbox", "--disable-dev-shm-usage"]
        res = subprocess.run(cmd, capture_output=True, timeout=timeout)
        stderr = res.stderr.decode(errors="replace")[:400]
        if res.returncode != 0:
            pdf_path.unlink(missing_ok=True)
            raise RuntimeError(f"Chromium завершился с кодом {res.returncode}: {stderr}")
        if not pdf_path.exists():
            raise RuntimeError("PDF не создан: " + stderr)
        head = pdf_path.read_bytes()[:5]
        if head != b"%PDF-" or pdf_path.stat().st_size < 1024:
            pdf_path.unlink(missing_ok=True)
            raise RuntimeError(f"Некорректный PDF: signature={head!r}")
    return pdf_path


def pdf_page_count(pdf_path):
    data = Path(pdf_path).read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?!s)", data))


def build_album_pdf(svg_dir_or_files, out_pdf):
    """svg_dir_or_files — папка (все *.svg по имени) ИЛИ явный список путей в порядке альбома (предпочтительно:
    список по реестру не тянет устаревшие файлы из папки)."""
    if isinstance(svg_dir_or_files, (list, tuple)):
        files = [Path(f) for f in svg_dir_or_files]
    else:
        files = sorted(Path(svg_dir_or_files).glob("*.svg"))
    if not files:
        raise FileNotFoundError(f"нет SVG: {svg_dir_or_files}")
    pages, css = [], []
    sizes = {}
    for f in files:
        svg = f.read_text(encoding="utf-8")
        w, h = svg_size_mm(svg)
        key = f"p{int(w)}x{int(h)}"
        if key not in sizes:
            sizes[key] = (w, h)
            css.append(f"@page {key}{{size:{w}mm {h}mm;margin:0}} .{key}{{page:{key};width:{w}mm;height:{h}mm}}")
        pages.append(f'<div class="sheet {key}">{svg}</div>')
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;padding:0;background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}'
            '.sheet{display:block;overflow:hidden;page-break-after:always;break-after:page}'
            '.sheet svg{display:block;width:100%;height:100%}'
            + "".join(css) + '</style></head><body>' + "".join(pages) + '</body></html>')
    p = _print_to_pdf(html, out_pdf)
    n = pdf_page_count(p)
    if n != len(files):
        raise RuntimeError(f"в PDF {n} страниц, ожидалось {len(files)}")
    return p


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "out/demo_flat/svg"
    p = build_album_pdf(d, Path(d).parent / "album.pdf")
    print(p, pdf_page_count(p), "страниц")
