#!/usr/bin/env python3
"""Тесты submit.py — фикс 09-H9-1.

Zero-dependency (stdlib): бинарный артефакт больше НЕ уходит кашей из U+FFFD с
ложным «принято» — он честно отклоняется (SystemExit != 0). Текстовый файл
по-прежнему читается корректно.

Запуск: python test_submit.py   (в CI — .github/workflows/sdat-submit-test.yml)
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("submit_mod", HERE / "submit.py")
assert _spec and _spec.loader
submit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(submit)

failures: list[str] = []


def expect_die(fn) -> None:
    """Утверждает, что fn() честно завершается (die → SystemExit с кодом != 0)."""
    try:
        fn()
    except SystemExit as e:
        assert e.code not in (0, None), "die() должен выходить с ненулевым кодом"
        return
    raise AssertionError("ожидался честный отказ (SystemExit), но его не было")


def t_text_ok() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "answer.md"
        f.write_text("# Моя сдача\nПривет, мир 🌍\n", encoding="utf-8")
        content, name = submit.read_text_artifact(str(f))
        assert "Привет, мир" in content, content
        assert name == "answer.md", name


def t_binary_nul_rejected() -> None:
    # PDF-подобный файл с NUL-байтами — раньше уходил кашей, теперь отказ.
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "scan.pdf"
        f.write_bytes(b"%PDF-1.7\x00\x00\xff\xfe\x00binary\x00stuff\x00")
        expect_die(lambda: submit.read_text_artifact(str(f)))


def t_binary_invalid_utf8_rejected() -> None:
    # PNG-заголовок + невалидный UTF-8 хвост — честный отказ.
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "pic.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n\xff\xd8\xff\xe0invalid\xc3\x28tail")
        expect_die(lambda: submit.read_text_artifact(str(f)))


def t_oversized_rejected() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "big.txt"
        f.write_bytes(b"a" * (submit.MAX_CONTENT_BYTES + 1))
        expect_die(lambda: submit.read_text_artifact(str(f)))


def t_empty_rejected() -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "blank.md"
        f.write_text("   \n\t\n", encoding="utf-8")
        expect_die(lambda: submit.read_text_artifact(str(f)))


TESTS = [
    ("текстовый файл читается как UTF-8", t_text_ok),
    ("бинарь (NUL) отклоняется честно", t_binary_nul_rejected),
    ("невалидный UTF-8 отклоняется честно", t_binary_invalid_utf8_rejected),
    ("файл > 2 МБ отклоняется", t_oversized_rejected),
    ("пустой файл отклоняется", t_empty_rejected),
]

for name, fn in TESTS:
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(name)
        print(f"FAIL  {name}: {e}")

if failures:
    print(f"\n{len(failures)} тест(ов) упало")
    sys.exit(1)
print(f"\nвсе тесты прошли ({len(TESTS)})")
