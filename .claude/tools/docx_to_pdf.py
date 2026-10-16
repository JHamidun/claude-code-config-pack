#!/usr/bin/env python
"""DOCX → PDF через установленный Word (COM). Без облака и без LaTeX.

    python docx_to_pdf.py file1.docx file2.docx
"""
from __future__ import annotations

import pathlib
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

WD_FORMAT_PDF = 17


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Укажи .docx файлы")

    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        for arg in sys.argv[1:]:
            src = pathlib.Path(arg).resolve()
            if not src.exists():
                print(f"[!] нет файла: {src}", file=sys.stderr)
                continue
            dst = src.with_suffix(".pdf")
            doc = word.Documents.Open(str(src), ReadOnly=True)
            try:
                doc.SaveAs(str(dst), FileFormat=WD_FORMAT_PDF)
                print(f"OK  {dst.name}  ({dst.stat().st_size // 1024} KB)")
            finally:
                doc.Close(False)
    finally:
        word.Quit()


if __name__ == "__main__":
    main()
