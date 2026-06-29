# -*- coding: utf-8 -*-
"""Загрузка ключей/настроек. Источники по приоритету:
1) переменные окружения (os.environ);
2) файл .env в корне скилла (рядом с SKILL.md);
3) файл .env в текущей рабочей директории.
Никаких личных путей и захардкоженных секретов — всё через .env (см. .env.example)."""
import os
import pathlib

SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _parse_env(path):
    out = {}
    try:
        for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def load_creds():
    """Возвращает словарь {KEY: value} из env + .env-файлов."""
    creds = {}
    for env_file in (SKILL_ROOT / ".env", pathlib.Path.cwd() / ".env"):
        if env_file.exists():
            for k, v in _parse_env(env_file).items():
                creds.setdefault(k, v)
    # переменные окружения имеют приоритет
    for k, v in os.environ.items():
        creds[k] = v
    return creds
