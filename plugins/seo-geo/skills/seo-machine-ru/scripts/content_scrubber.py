#!/usr/bin/env python3
"""Очистка текста от AI-водяных знаков и типографских артефактов (RU).

Удаляет невидимые Unicode-символы (zero-width, BOM, узкие пробелы),
нормализует тире и кавычки под русскую типографику, чинит пробелы.
Универсальная логика (язык-агностична для невидимых символов),
пунктуация настроена под русский.

CLI:
    python content_scrubber.py <file.md>            # печатает очищенный текст
    python content_scrubber.py <file.md> --in-place # перезаписывает файл
    python content_scrubber.py --report <file.md>   # что нашлось, без правки
"""
import argparse
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Невидимые / служебные символы, которые часто оставляют LLM и copy-paste
INVISIBLE = {
    "": "",   # zero-width space
    "": "",   # zero-width non-joiner
    "": "",   # zero-width joiner
    "": "",   # BOM / zero-width no-break space
    "⁠": "",   # word joiner
    "­": "",   # soft hyphen
    " ": " ",  # narrow no-break space -> обычный nbsp
    " ": "\n",      # line separator
    " ": "\n\n",    # paragraph separator
}


def strip_invisible(text: str) -> str:
    for bad, good in INVISIBLE.items():
        text = text.replace(bad, good)
    # любые прочие Cf (format) символы
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text


def _is_structural(line: str) -> bool:
    """Markdown-строки, которые нельзя трогать дефис-нормализацией:
    разделители frontmatter / горизонтальная черта (---) и
    разделитель таблицы (|---|---|)."""
    s = line.strip()
    if re.fullmatch(r"-{3,}", s):                 # frontmatter fence / <hr>
        return True
    if "|" in s and re.fullmatch(r"[\s|:\-]+", s):  # table separator row
        return True
    return False


def normalize_dashes(text: str) -> str:
    """RU-типографика: '-' между цифрами и в диалогах оставляем,
    но злоупотребление em-dash (—) у LLM заменяем на нормальную пунктуацию,
    если их подозрительно много. Заменяем '--' на тире, чистим пробелы вокруг тире.
    Структурные строки markdown (--- и |---|) пропускаем."""
    out = []
    for line in text.split("\n"):
        if _is_structural(line):
            out.append(line)
            continue
        ln = line.replace("--", " — ")
        ln = re.sub(r"\s*—\s*", " — ", ln)
        ln = re.sub(r"—\s*—", "—", ln)
        out.append(ln)
    return "\n".join(out)


def normalize_quotes(text: str) -> str:
    """Прямые кавычки -> ёлочки (внешний уровень) для русского текста."""
    # очень простая эвристика: парные "..." -> «...»
    def repl(m):
        return "«" + m.group(1) + "»"
    return re.sub(r'"([^"\n]{1,200}?)"', repl, text)


def fix_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # пробел перед знаками препинания
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip() + "\n"


def count_emdash(text: str) -> int:
    return text.count("—")


def scrub(text: str, quotes: bool = False) -> str:
    text = strip_invisible(text)
    text = normalize_dashes(text)
    if quotes:
        text = normalize_quotes(text)
    text = fix_spaces(text)
    return text


def report(text: str) -> dict:
    invisible_found = {
        name: text.count(ch)
        for ch, name in (
            ("", "zero-width-space"),
            ("", "BOM"),
            ("­", "soft-hyphen"),
            (" ", "narrow-nbsp"),
        )
        if text.count(ch)
    }
    return {
        "invisible": invisible_found,
        "em_dashes": count_emdash(text),
        "double_hyphens": len(re.findall(r"--", text)),
        "straight_quotes": len(re.findall(r'"', text)),
    }


def main():
    ap = argparse.ArgumentParser(description="Очистка текста от AI-артефактов (RU)")
    ap.add_argument("file")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--quotes", action="store_true", help="прямые кавычки -> ёлочки")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as f:
        text = f.read()

    if args.report:
        import json
        print(json.dumps(report(text), ensure_ascii=False, indent=2))
        return

    cleaned = scrub(text, quotes=args.quotes)
    if args.in_place:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"scrubbed in place: {args.file}", file=sys.stderr)
    else:
        sys.stdout.write(cleaned)


if __name__ == "__main__":
    main()
