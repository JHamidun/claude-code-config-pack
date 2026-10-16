# -*- coding: utf-8 -*-
"""Реестр тем: --theme company|vibe.

Новая тема = файл themes/<имя>.py с объектом THEME (экземпляр themes.base.Theme
или наследника) + строка в REGISTRY. Контракт классов разметки — в base.py.
"""
import importlib

REGISTRY = {
    "company": "themes.company",   # корпоративная: светлый сине-фиолетовый градиент, медальоны
    "vibe": "themes.vibe",         # школа/курс: тёмная техно-тема с терракотой, частицы
}


def available():
    return sorted(REGISTRY)


def get_theme(name: str):
    if name not in REGISTRY:
        raise KeyError(f"нет темы «{name}»; есть: {', '.join(available())}")
    mod = importlib.import_module(REGISTRY[name])
    return mod.THEME
