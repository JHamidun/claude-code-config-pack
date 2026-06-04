# -*- coding: utf-8 -*-
"""Стандартный smoke-блок для коннекторов (без личных данных).
Грузит тест-книгу из config/book.example.yaml и ключи из .env, печатает результат."""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def run_smoke(collect):
    from lib.creds import load_creds
    try:
        import yaml
    except ImportError:
        print("Нужен pyyaml: pip install pyyaml")
        return
    book = yaml.safe_load((ROOT / "config" / "book.example.yaml").read_text(encoding="utf-8"))
    res = collect(book, load_creds(), 50) or []
    print(f"smoke: получено {len(res)} упоминаний")
    for m in res[:2]:
        print("  -", (m.get("title") or "")[:70], "|", m.get("source", ""), "|", m.get("url", "")[:60])
