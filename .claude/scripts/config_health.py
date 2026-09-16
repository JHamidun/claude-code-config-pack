#!/usr/bin/env python3
"""Здоровье конфига: что заявлено, что существует, что запускается.

Линтер связности проверяет ссылки — ведут ли они в существующие файлы. Но файл
может существовать и при этом не работать: упасть на импорте, потребовать
пропавшую библиотеку, звать модель, которой больше нет. Разница между «файл на
месте» и «инструмент работает» и есть то, из-за чего навык считается живым,
пока его не позовут.

Скрипт проверяет три уровня, от дешёвого к дорогому:

    заявлено    навык обещает скрипт в своём описании
    существует  файл лежит на диске
    запускается --help отрабатывает без трассировки

Плюс ищет признаки устаревания: модели, которых больше нет, ссылки на удалённые
инструменты, даты в текстах старше полугода.

    python config_health.py                 # полная проверка
    python config_health.py --quick         # без запуска скриптов
    python config_health.py --json отчёт.json
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

C = pathlib.Path.home() / ".claude"

# Модели, которых больше нет или которые запрещены каноном конфига.
#
# ⚠️ 06.09.2026: регулярка ловила 3 снятые модели из 10 и потому была ЗЕЛЁНОЙ,
# пока в каноне полгода лежали шесть удалённых id под заголовком «доступны через
# API». Мимо неё проходили самые свежие снятия — 3.7 Sonnet, 3.5 Sonnet/Haiku,
# Opus 4.1, Opus 4, Sonnet 4. Зелёный сторож дороже отсутствующего: он закрывает
# вопрос. Дописано по таблице model-deprecations, сверено с живой страницей.
#
# ⚠️ 09.09.2026, второй раз то же самое — и снова сторож был ЗЕЛЁНЫМ.
# Список знал ровно одну снятую модель OpenAI (`dall-e-2`) и не знал НИ ОДНОЙ
# из десяти, снятых за 2026 год. Мимо проходил даже `dall-e-3` — тот самый, что
# реально стоял в конфиге. А `gpt-5-codex` шесть недель как был снят и лежал в
# рабочем скрипте `seo_pipeline.py`, где молча возвращал строку ошибки вместо
# анализа. Причина пропуска — не регулярка: см. SCAN_FILES ниже.
DEAD_MODELS = re.compile(
    r"\b(gpt-4-turbo|gpt-3\.5|text-davinci|"
    # Anthropic — сняты, вызов вернёт ошибку
    r"claude-3-opus|claude-3-sonnet|claude-3-haiku|claude-3-5-sonnet|claude-3-5-haiku|"
    r"claude-3-7-sonnet|claude-opus-4-1|claude-opus-4-20250514|claude-sonnet-4-20250514|"
    r"claude-2|claude-instant|"
    # OpenAI — сняты в 2026, вызов вернёт ошибку
    r"dall-e-[23]|"                                    # 12.05.2026
    r"codex-mini-latest|"                              # 12.02.2026
    r"gpt-5-codex|gpt-5\.[123]-codex(?:-max|-mini)?|"  # 23.07.2026, вся линейка
    r"o3-deep-research|o4-mini-deep-research|"         # 23.07.2026
    # Дефисы по краям обязательны: у Google своя, ЖИВАЯ модель
    # `gemini-2.5-computer-use-preview-10-2025`, и без якорей сторож обвинял её.
    r"(?<!-)computer-use-preview(?!-)|"                 # 23.07.2026, OpenAI
    # прочие провайдеры
    r"gemini-pro-vision|gemini-1\.5|gemini-2\.0-flash-exp|"
    r"gemini-2\.5-flash-image)\b", re.I)

# Ещё живые, но с НАЗНАЧЕННОЙ датой смерти. Отдельно от DEAD, потому что вызов
# сегодня работает — а через месяц не работает, и узнать об этом надо заранее,
# а не по ошибке в проде. Дата в значении, чтобы отчёт печатал «осталось N дней»
# и срочное само поднималось наверх.
RETIRING = {
    r"\bsora-2(?:-pro)?\b":                    ("2026-09-24", "у OpenAI видео закрывается целиком — Veo 3.1 или Seedance 2.5 (Runway)"),
    r"\bgpt-image-1\b(?!\.)":                  ("2026-10-23", "gpt-image-2.5-sunburst"),
    r"\bo4-mini\b|\bo3-mini\b|\bo1\b":         ("2026-10-23", "gpt-5.6-terra"),
    r"\bgpt-4\.1-nano\b":                      ("2026-10-23", "gpt-5.6-luna"),
    r"\bgpt-image-1\.5\b|\bgpt-image-1-mini\b": ("2026-12-01", "gpt-image-2.5-flare"),
    r"\bo3-pro\b|\bo3\b(?!-)":                 ("2026-12-11", "gpt-6-astra"),
    r"\bgpt-5(?:-mini|-nano|-pro)?\b(?!\.)|\bgpt-5\.2\b": ("2026-12-11", "gpt-5.6-sol"),
    r"\bwhisper-1\b|\bgpt-4o-transcribe\b":    ("2027-02-26", "gpt-transcribe"),
}

# Живые, но прошлого поколения: вызов не падает, а молча отдаёт вчерашнюю модель.
# Отдельный список, чтобы не путать с поломкой — предупреждение, а не ошибка.
LEGACY_MODELS = re.compile(
    r"\b(claude-fable-5(?!-1)|claude-opus-4-[5678]|claude-sonnet-4-[56]|"
    # ⚠️ Сюда НЕ вносить `gpt-5.6` и `gpt-4.1`: обе ТЕКУЩИЕ и рабочие.
    # Первая редакция их пометила, и сторож обвинил канон в устаревании.
    r"gpt-image-2(?!\.))\b", re.I)

# Строка, где модель названа не как рекомендация: запрет, пометка о старости,
# пример из шутки. Такие в счёт не идут.
EXCUSED = re.compile(
    r"(?i)запрещ|не использу|нельзя|устарел|legacy|deprecated|вместо неё|"
    r"больше нет|НЕ\s|dont-do|«|\bне\b.{0,12}\bбер[иё]|"
    # Здесь были НАСТОЯЩИЕ байты 0x08 вместо \b: граница слова когда-то
    # прошла через не-raw строку и стала backspace. Оговорка «не бери»
    # не срабатывала ни разу и не могла: в текстах backspace не встречается.
    #
    # Добавлено 09.09.2026: первый же прогон расширенного сторожа обвинил
    # МОИ ЖЕ свежие предупреждения («dall-e-2 и dall-e-3 сняты, вызов вернёт
    # ошибку»): «снят» в списке оговорок не значилось вовсе. Сторож,
    # ругающийся на предупреждение о снятии, учит игнорировать себя.
    r"снят|снимается|выключен|⛔|retire|shut ?down|мёртв|прошлое поколение|чужой")

# Файлы, где перечень мёртвых моделей и ЕСТЬ содержание, либо где лежит точный
# снимок чужого каталога. Исключаем по пути, а не оговорками: канон снятий
# обязан называть снятое поимённо, а правка чужого снимка его же и исказит.
EXEMPT_PATHS = {
    "config/models.md",           # канон: таблицы снятий с датами
    "scripts/config_health.py",   # этот файл: сами списки DEAD и RETIRING
}
# Целые ветки: реверс чужого API и архивы слияний.
# ⚠️ Канарейку `skills/_zz-*` сюда НЕ вносить, хотя рука тянется: подсадная
# модель обязана ловиться, иначе положительный контроль ничего не измеряет,
# и «0 снятых моделей» перестаёт что-либо означать.
EXEMPT_PREFIX = ("skills/claude-design-soul/", "skills/_merged-")

SCRIPT_CALL = re.compile(
    r"(?:python\d?|node|bun)\s+[\"'`]?([^\s\"'`|>&]*(?:scripts|tools)/[\w./-]+\.(?:py|mjs|js))")


def skills() -> list[pathlib.Path]:
    return sorted((C / "skills").glob("*/SKILL.md"))


# Каталоги, которые не наш конфиг: чужой код, кэши, сборки, скачанные каталоги
# шаблонов. Мёртвый id в чужом снимке — не наша поломка, а точный слепок чужого.
_SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "site-packages", "dist",
              "build", "__pycache__", ".next", ".mypy_cache", "assets", "output",
              "outputs", "catalog", "raw", "connectors", "logs", "cache"}


def scan_files() -> list[pathlib.Path]:
    """Файлы, где мёртвая модель означает поломку.

    ⚠️ Здесь была настоящая дыра, а не в списке моделей. Проверка читала ТОЛЬКО
    `skills/*/SKILL.md` — то есть документацию. Между тем вызов модели живёт в
    коде: `gpt-5-codex` был снят 23.07.2026 и шесть недель стоял в рабочем
    `skills/youtube-channel/scripts/descriptions/seo_pipeline.py`, а отчёт всё
    это время печатал «0 снятых моделей». Сторож проверял не то место и потому
    был хуже отсутствующего: он закрывал вопрос.

    Теперь берём и скрипты (`.py`/`.js`/`.mjs`/`.toml`/`.json`), и справочники
    (`references/*.md`), и агентов с командами. Глубина ограничена: навык живёт
    как `skills/<имя>/{SKILL.md, references/*, scripts/*}`, а четвёртый уровень
    почти всегда означает чужой код — обход всего дерева ~/.claude не
    заканчивается и за две минуты.
    """
    out: list[pathlib.Path] = []
    exts = {".md", ".py", ".js", ".mjs", ".toml", ".json", ".sh", ".ps1"}
    for root in ("skills", "agents", "commands", "rules", "config", "tools",
                 "scripts", "hooks", "workflows"):
        base = C / root
        if not base.is_dir():
            continue
        base_depth = len(base.parts)
        for p in base.rglob("*"):
            if len(p.parts) - base_depth > 4:
                continue
            if any(part in _SKIP_DIRS or part.startswith("_dropped")
                   for part in p.parts[base_depth:]):
                continue
            if p.is_file() and p.suffix.lower() in exts:
                out.append(p)
    return sorted(out)


def resolve(raw: str, skill_dir: pathlib.Path,
            cwd: pathlib.Path | None = None) -> pathlib.Path:
    p = raw.strip().strip("\"'`")
    for var in ("${CLAUDE_SKILL_DIR}", "$CLAUDE_SKILL_DIR", "${SKILL_DIR}"):
        p = p.replace(var, skill_dir.as_posix())
    if p.startswith("~/"):
        return pathlib.Path.home() / p[2:]
    if re.match(r"^[A-Za-z]:/", p):
        return pathlib.Path(p)
    return skill_dir / p


def runs(path: pathlib.Path, timeout: int = 45) -> tuple[bool, str]:
    """Отрабатывает ли --help без трассировки.

    Отказ с внятным сообщением («нет ключа») — это НЕ поломка: инструмент жив,
    ему просто нечем работать. Поломка — трассировка на импорте.
    """
    exe = {".py": [sys.executable], ".mjs": ["node"], ".js": ["node"]}.get(path.suffix)
    if not exe:
        return True, "не запускаемый"
    env = {k: v for k, v in os.environ.items()
           if not any(x in k.upper() for x in ("API", "TOKEN", "KEY", "SECRET"))}
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        r = subprocess.run(exe + [str(path), "--help"], capture_output=True, text=True,
                           timeout=timeout, env=env, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, "виснет"
    except Exception as e:
        return False, str(e)[:60]
    err = r.stderr or ""
    if "Traceback" in err:
        last = [l for l in err.strip().splitlines() if l.strip()][-1]
        return False, last[:80]
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="без запуска скриптов")
    ap.add_argument("--json", help="куда сохранить отчёт")
    a = ap.parse_args()

    promised, missing, stale, aging, soon = {}, {}, {}, {}, {}
    for sk in skills():
        name = sk.parent.name
        try:
            text = sk.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in SCRIPT_CALL.finditer(text):
            p = resolve(m.group(1), sk.parent)
            promised.setdefault(name, set()).add(p)
            if not p.exists():
                missing.setdefault(name, set()).add(m.group(1))

    # Модели ищем ОТДЕЛЬНЫМ проходом и по всем файлам, а не только по SKILL.md —
    # см. scan_files(). Ключ отчёта — путь относительно ~/.claude, чтобы было
    # видно, доку чинить или исполняемый код.
    # Обход дерева стоит десятки секунд, поэтому список берём ОДИН раз.
    # Первая редакция звала scan_files() ещё и в строке печати счётчика —
    # то есть обходила диск дважды ради одного числа.
    files_scanned = scan_files()
    for f in files_scanned:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = f.relative_to(C).as_posix()
        if rel in EXEMPT_PATHS or rel.startswith(EXEMPT_PREFIX):
            continue
        # Упоминание устаревшей модели — ещё не поломка. Её называют и когда
        # ЗАПРЕЩАЮТ, и когда помечают legacy, и внутри примера-шутки. Тревога
        # по трём таким случаям однажды увела разбираться туда, где всё верно.
        # Оговорка часто стоит НЕ на той строке, где модель: заголовок «Legacy —
        # не использовать», а под ним список идентификаторов. Построчная проверка
        # такой список считала рекомендацией и требовала переписать документ под
        # себя. Смотрим строку вместе с двумя предыдущими — там живёт лид-ин.
        dead, legacy = set(), set()
        lines = text.splitlines()
        for i, line in enumerate(lines):
            # Окно назад — 6 строк, а не 2. Оговорка про чужой каталог живёт
            # блоком-цитатой на пять-шесть строк, и при окне 2 сторож видел
            # только хвост блока: список под ним считался рекомендацией, хотя
            # прямо над ним написано «править нельзя». Расширение проверено
            # канарейкой — подсадная модель ловится по-прежнему.
            if any(EXCUSED.search(x) for x in lines[max(0, i - 6):i + 1]):
                continue
            dead.update(DEAD_MODELS.findall(line))
            legacy.update(LEGACY_MODELS.findall(line))
            for pat, (when, repl) in RETIRING.items():
                if re.search(pat, line, re.I):
                    soon.setdefault(when, {}).setdefault(rel, set()).add(repl)
        if dead:
            stale[rel] = sorted(dead)
        if legacy:
            aging[rel] = sorted(legacy)

    all_scripts = {p for s in promised.values() for p in s if p.exists()}
    print(f"  навыков: {len(skills())}")
    print(f"  из них обещают скрипты: {len(promised)}")
    print(f"  скриптов заявлено: {len(all_scripts)}")
    print(f"  ОБЕЩАНО, НО НЕТ НА ДИСКЕ: {sum(len(v) for v in missing.values())} "
          f"в {len(missing)} навыках")
    for n, v in sorted(missing.items())[:10]:
        print(f"    {n:28} {', '.join(sorted(v))[:60]}")
    print(f"\n  файлов проверено на модели: {len(files_scanned)}")
    print(f"  СНЯТЫЕ МОДЕЛИ (вызов вернёт ошибку) — в {len(stale)} файлах")
    # Исполняемое печатаем первым и целиком: мёртвый id в .md — устаревшая
    # инструкция, мёртвый id в .py — поломка, которая уже происходит.
    code = {k: v for k, v in stale.items() if not k.endswith(".md")}
    docs = {k: v for k, v in stale.items() if k.endswith(".md")}
    for n, v in sorted(code.items()):
        print(f"    ⛔ КОД  {n:52} {', '.join(v)[:44]}")
    for n, v in sorted(docs.items())[:10]:
        print(f"       док  {n:52} {', '.join(v)[:44]}")
    if len(docs) > 10:
        print(f"       … ещё {len(docs) - 10} док")

    if soon:
        today = datetime.date.today()
        print("\n  СНИМАЮТСЯ ПО РАСПИСАНИЮ (сегодня ещё работают):")
        for when in sorted(soon):
            left = (datetime.date.fromisoformat(when) - today).days
            mark = "🔥" if left <= 30 else "  "
            files = soon[when]
            repl = sorted({r for s in files.values() for r in s})
            print(f"   {mark} {when} (осталось {left:4} дн.) — {len(files)} файлов "
                  f"→ {', '.join(repl)[:60]}")
            # Срочное разворачиваем пофайлово: месяц — это когда чинить пора
            # сейчас, а не когда «надо иметь в виду».
            if left <= 30:
                for f in sorted(files)[:12]:
                    print(f"        {f}")
    print(f"\n  LEGACY (не падает, молча отдаёт вчерашнюю) — в {len(aging)} файлах")
    for n, v in sorted(aging.items())[:10]:
        print(f"    {n:52} {', '.join(v)[:44]}")

    broken = {}
    if not a.quick:
        print(f"\n  запускаю {len(all_scripts)} скриптов с --help…")
        with ThreadPoolExecutor(max_workers=8) as ex:
            for p, (ok, why) in zip(all_scripts, ex.map(runs, all_scripts)):
                if not ok:
                    broken[str(p)] = why
        print(f"  НЕ ЗАПУСКАЮТСЯ: {len(broken)} из {len(all_scripts)}")
        for p, why in sorted(broken.items())[:15]:
            print(f"    {pathlib.Path(p).name:34} {why[:56]}")

    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({
            "skills": len(skills()),
            "missing": {k: sorted(v) for k, v in missing.items()},
            "stale_models": stale,
            "broken": broken,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n  отчёт: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
