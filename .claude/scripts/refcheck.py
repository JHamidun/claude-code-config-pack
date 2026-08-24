#!/usr/bin/env python3
"""Ссылки на файлы справочников: какие из них ведут в пустоту.

Три предыдущие версии врали — по очереди 87, 28 и 11 «битых», и правдой была
только последняя цифра. Ошибались не на поломках конфига, а на разборе:

- `../соседний-навык/references/файл.md` считался своим;
- glob-шаблон `Glob("**/x/references/y.md")` в примере кода считался ссылкой;
- строка происхождения `ported_from: owner/repo (cro/references/form.md)`
  считалась локальным файлом.

Четвёртая ошибка вскрылась при независимой проверке: скрипт читал ТОЛЬКО
`skills/*/SKILL.md`, то есть отчёт «битых нет» покрывал около семидесяти
процентов дерева. Теперь обходятся ещё `references/`, `rules/`, `config/`,
`commands/`, `agents/`.

«Ноль битых» имеет силу ТОЛЬКО вместе с контрольной поломкой: `--canary`
подсаживает заведомо мёртвую ссылку, проверяет, что она найдена, и откатывает.
Без этого зелёный отчёт означает лишь то, что скрипт чего-то не заметил.

    python refcheck.py             # обойти всё
    python refcheck.py --canary    # то же + доказать, что детектор жив
    python refcheck.py --json f    # машинный отчёт
"""
from __future__ import annotations
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓, эмодзи) валит процесс UnicodeEncodeError —
# нередко на --help, то есть ДО любой полезной работы. errors="replace" оставляет
# вывод читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

# Проверять надо ТО дерево, которое публикуется, а не домашнюю папку автора:
# там всё на месте по определению, и линтер выдавал зелёный отчёт про чужую
# раскладку. Та же переменная, что у config_links.py.
C = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
SKILLS = C / "skills"

# Каталоги, которые к живому конфигу не относятся: архивы, черновики, чужой код.
# Сравнение идёт ПОДСТРОКОЙ, а не точным именем: могильники датированы
# (`_graveyard-stubs-20260718`), и точное сравнение их пропускало — отчёт
# распухал на 9 мёртвых ссылок в архиве, который никто не грузит.
SKIP = ("_merged-", "_graveyard", "scratchpad", "projects", "recovered-chats",
        "backups", "node_modules", ".git", "profiles", "_qa", "plugins", "catalog",
        "pack-overrides", "upstream", "official-repo")

PAT = re.compile(r"[\w./~$-]*references/[\w./-]+\.md")

# Имя навыка в бэктиках где-то рядом со ссылкой. Человек читает
# «`references/benchmarks.md` в `yandex-direct-pro-ru`» правильно, потому что
# видит оба куска сразу; разбор по одной ссылке — нет.
BACKTICKED = re.compile(r"`([a-z0-9][a-z0-9-]{2,})`")

# Корень дерева каталогов в код-блоке: строка вида `~/.claude/skills/имя/`
# или `skills/имя/` — сама по себе, заканчивается слэшем. Берётся ПОСЛЕДНЯЯ
# такая строка перед ссылкой: в одном блоке корень бывает один, но блоков в
# файле несколько.
TREE_ROOT = re.compile(r"^\s*([~$]?[\w./-]*/)\s*$", re.M)

# Документ О ТОМ, как называть справочники, приводит имена как ПРИМЕРЫ.
PROSE = re.compile(r"наприм|лучше, чем|вида |формата |раскладывать|назв", re.I)

# Строка о происхождении цитирует путь в ЧУЖОМ репозитории — он и не должен
# существовать локально. Слова добавлялись по фактическим ложным срабатываниям:
# «первоисточник: воркшоп …» и «возьми оригинал из репозитория owner/repo».
PROVENANCE = re.compile(
    r"ported_from|апстрим|upstream|порт апстрима|source:"
    r"|первоисточник|из воркшопа|воркшоп[а-я]*\s+`|репозитори", re.I)

# Ссылка, о которой САМ текст говорит, что файла ещё нет. Это не мёртвый
# маршрут, а честно помеченный пробел — но и не «всё в порядке»: место таким
# ссылкам в спорных, чтобы их было видно, а не в битых.
NOT_YET = re.compile(r"не создан|not created|пока нет файла|файла нет", re.I)

# Ссылка на файл соседнего навыка, названного словом (обычно «его» или именем
# навыка строкой выше). Голый `references/…` тут разрешать относительно СВОЕГО
# каталога неверно, но и битым он не является — помечаем отдельно.
NEIGHBOUR = re.compile(r"\bего\b|\bсоседн|\bскилл[ае]?\s+`|\bнавык[ае]?\s+`", re.I)

# Отчёт-рисёрч перечисляет файлы, которые ПРЕДЛАГАЕТСЯ создать. Это план работ,
# а не маршрут: такого файла на диске и не должно быть, «битой ссылкой» он не
# является.
PLANNED = re.compile(
    r"\bCREATE\b|\bTODO\b|планир|предлага|надо создать|to create"
    # Отчёт-рисёрч диктует содержимое будущего файла заголовком «File: `путь`»
    # и следом блоком кода. Это ТЗ на создание, а не ссылка на существующее.
    r"|^\s*File:\s*`|IMMEDIATE WINS|^#+\s*Phase\s*\d",
    re.I | re.M)


def exists(p: Path) -> bool:
    if p.exists():
        return True
    # Имена на диске бывают в NFD — сравнение без нормализации промахивается.
    parent = p.parent
    if not parent.is_dir():
        return False
    want = unicodedata.normalize("NFC", p.name)
    return any(unicodedata.normalize("NFC", c.name) == want for c in parent.iterdir())


def candidates(raw: str, base: Path, skill_dir: Path | None,
               ctx: str = "") -> list[Path]:
    """Все прочтения пути, каждое из которых человек счёл бы верным.

    Одного прочтения мало, и это выяснилось на трёх разных формах сразу:

    - вложенный навык (`skills/linkedin-post-writer/references/linkedin-hook-
      extractor/SKILL.md`) пишет `references/x.md`, имея в виду СВОЙ каталог,
      а не корень родителя;
    - файл, сам лежащий в `references/`, ссылается на СОСЕДА той же папки;
    - манифест движка (`engines/higgsfield/ENGINE.md`) считает `references/`
      своим, хотя формально живёт внутри чужого навыка.

    Ссылка считается битой, только если НИ ОДНО прочтение не находит файл.
    """
    r = raw.lstrip("`").strip()
    if r.startswith("~/.claude/"):
        return [C / r[len("~/.claude/"):]]
    # `$HOME/.claude/...` — регулярка съедает `$`, остаётся `HOME/.claude/...`
    for pre in ("$HOME/.claude/", "HOME/.claude/"):
        if r.startswith(pre):
            return [C / r[len(pre):]]
    if r.startswith("skills/"):
        return [SKILLS / r[len("skills/"):]]
    if r.startswith(".claude/"):
        return [C / r[len(".claude/"):]]
    if r.startswith("../") or r.startswith("./"):
        return [(base / r).resolve()]

    out = [base / r]                      # от каталога самого файла
    if base.name == "references":
        out.append(base.parent / r)       # сосед по той же папке references/
        out.append(base / r.split("/", 1)[-1])
    if skill_dir:
        out.append(skill_dir / r)         # от корня навыка
        head = r.split("/")[0]
        if head == skill_dir.name:
            out.append(skill_dir / r[len(head) + 1:])
    out.append(C / r)                     # путь от корня ~/.claude
    head = r.split("/")[0]
    if (SKILLS / head).is_dir():
        out.append(SKILLS / r)            # `имя-навыка/references/файл.md`
    else:
        # Укороченный путь во вложенный движок: `higgsfield/references/x.md`
        # вместо `video-generation/engines/higgsfield/references/x.md`.
        # Ищем такой хвост под skills/ — но только если голова похожа на имя
        # каталога, иначе перебор становится дорогим и ложноположительным.
        for cand in SKILLS.glob(f"*/*/{head}"):
            if cand.is_dir():
                out.append(cand / r[len(head) + 1:])
    # Навык, названный в бэктиках рядом: «… `references/x.md` в `имя-навыка`».
    for name in BACKTICKED.findall(ctx):
        if (SKILLS / name).is_dir():
            out.append(SKILLS / name / r)
    return out


def resolve(raw: str, base: Path, skill_dir: Path | None, ctx: str = "") -> Path | None:
    for c in candidates(raw, base, skill_dir, ctx):
        if exists(c):
            return c
    return None


WALK_ERRORS: list[str] = []
_FILES_CACHE: list[Path] | None = None


def invalidate_files() -> None:
    """Сбросить кэш обхода. Нужен ровно в одном месте — вокруг канарейки,
    которая создаёт и убирает файл прямо во время работы."""
    global _FILES_CACHE
    _FILES_CACHE = None


def files() -> list[Path]:
    """Обход дерева. `Path.rglob` под конкурентной нагрузкой отдавал НЕПОЛНЫЙ
    список — замерена потеря 75 файлов из 2071, когда рядом крутились восемь
    параллельных проверок. Ошибки чтения каталога pathlib проглатывает молча,
    поэтому недобор выглядел как «в дереве стало меньше файлов», а отчёт всё
    равно печатал «БИТЫХ: 0». Зелёный вердикт над неполным обходом опаснее
    красного: он закрывает вопрос.

    `os.walk` с `onerror` делает сбой видимым — каждая непрочитанная папка
    попадает в `WALK_ERRORS` и печатается в отчёте.
    """
    import os

    global _FILES_CACHE
    if _FILES_CACHE is not None:
        return _FILES_CACHE

    WALK_ERRORS.clear()
    out = []
    for sub in ("skills", "rules", "config", "commands", "agents", "docs"):
        d = C / sub
        if not d.is_dir():
            continue
        for root, dirs, names in os.walk(d, onerror=lambda e: WALK_ERRORS.append(str(e))):
            if any(s in root for s in SKIP):
                dirs[:] = []
                continue
            for n in names:
                if not n.endswith(".md"):
                    continue
                p = Path(root) / n
                if any(s in str(p) for s in SKIP):
                    continue
                out.append(p)
    _FILES_CACHE = out
    return out


def check_coverage(n_files: int) -> bool:
    """Обход считается достоверным, только если он не просел против прошлого раза.

    Счётчик «файлов обойдено» сам по себе ни с чем не сверялся — он скакал
    2071→1996 и молчал. Здесь он сверяется с прошлым прогоном: просадка больше
    2% означает, что часть дерева не читалась, и «БИТЫХ: 0» о ней ничего не
    говорит.
    """
    state = C / ".refcheck-coverage"
    prev = None
    try:
        prev = int(state.read_text(encoding="utf-8").strip())
    except Exception:
        pass

    ok = True
    if WALK_ERRORS:
        print(f"  ⚠ каталогов не прочитано: {len(WALK_ERRORS)}")
        for e in WALK_ERRORS[:5]:
            print(f"      {e}")
        ok = False
    if prev and n_files < prev * 0.98:
        print(f"  ⚠ ОБХОД НЕПОЛОН: {n_files} файлов против {prev} в прошлый раз "
              f"(−{prev - n_files}). Отчёт о ссылках недостоверен — повтори без "
              f"параллельной нагрузки.")
        ok = False
    else:
        try:
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(str(max(n_files, prev or 0)), encoding="utf-8")
        except Exception:
            pass
    return ok


def scan() -> tuple[int, list[dict], list[dict]]:
    broken, soft, total = [], [], 0
    for p in files():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        parts = p.relative_to(C).parts
        skill_dir = SKILLS / parts[1] if parts[0] == "skills" and len(parts) > 1 else None
        seen = set()
        for m in PAT.finditer(text):
            raw = m.group(0)
            if m.start() and text[m.start() - 1] == "*":
                continue                                   # glob-шаблон, не ссылка
            nl = text.rfind("\n", 0, m.start()) + 1
            ne = text.find("\n", m.end())
            line = text[nl:ne if ne > 0 else len(text)]
            # Целевой навык почти всегда назван НЕ в той же строке, а строкой
            # выше («см. скилл `yandex`», следом отступом — `references/x.md`).
            # Классификация по одной строке давала два десятка ложных
            # срабатываний, поэтому контекст берётся окном вокруг совпадения.
            ctx = text[max(0, nl - 320):min(len(text), (ne if ne > 0 else len(text)) + 320)]
            # Дерево каталогов в код-блоке: корень отдельной строкой, дети с
            # отступом. Человек читает верно, разбор по одной ссылке — нет:
            # `references/youtube-pipeline.md` под шапкой
            # `~/.claude/skills/video-factory-pipeline/` резолвился относительно
            # каталога ФАЙЛА и объявлялся битым. Нотация обычная, и правильнее
            # научить ей проверялку, чем расставлять полные пути в каждом дереве.
            roots = TREE_ROOT.findall(text[max(0, nl - 400):nl])
            if roots and resolve(roots[-1].rstrip("/") + "/" + raw,
                                 p.parent, skill_dir, "") is not None:
                continue
            if PROVENANCE.search(ctx) or PLANNED.search(ctx):
                continue                     # цитата чужого пути или план работ
            if raw in seen:
                continue
            seen.add(raw)
            total += 1
            if resolve(raw, p.parent, skill_dir, ctx) is None:
                rec = {"file": str(p.relative_to(C)), "line": text[:m.start()].count("\n") + 1,
                       "ref": raw, "text": line.strip()[:120]}
                (soft if NEIGHBOUR.search(ctx) or PROSE.search(ctx)
                 or NOT_YET.search(line)
                 else broken).append(rec)
    return total, broken, soft


def canary() -> bool:
    """Доказать, что детектор жив: подсадить мёртвую ссылку и найти её.

    Пробник — ОДНОРАЗОВЫЙ каталог, а не живой навык. Прежняя версия дописывала
    фальшивую ссылку в `skills/verifier/SKILL.md` и убирала её в `finally`.
    Дважды прогон убивали по таймауту, а `finally` при SIGTERM не отрабатывает —
    мусор оставался в рабочем файле. Тот же приём в соседней проверке уже привёл
    к тому, что подсаженная строка с личными данными пережила убийство процесса
    и осталась в публикуемом файле.

    Одноразовый каталог безопасен по построению: он ничего не ломает и виден по
    имени. Но правила «`_` в SKIP» здесь НЕТ — в SKIP перечислены конкретные
    подстроки (`_merged-`, `_graveyard`), голого `_` среди них нет, и пробник
    обходится наравне со всем прочим (иначе канарейка не нашла бы себя).
    Поэтому переживший убийство каталог выглядит в листинге как настоящий навык —
    это происходило. От публикации его закрывает правило `.claude/skills/
    _refcheck-probe/` в `.gitignore`, а не обход; самолечение ниже убирает его с
    диска при следующем прогоне.
    """
    probe_dir = SKILLS / "_refcheck-probe"

    # Самолечение: убираем хвост прошлого прогона ДО начала, а не только после.
    # `finally` не выполняется при SIGTERM, и убитый прогон оставляет пробник на
    # диске — он попадает в листинг навыков и выглядит как настоящий навык.
    # Так уже случалось дважды за день. Чистка на входе делает переживший хвост
    # самоустраняющимся при следующем же запуске, без участия человека.
    if probe_dir.exists():
        for leftover in probe_dir.iterdir():
            leftover.unlink(missing_ok=True)
        probe_dir.rmdir()
        print("  (убран пробник от прошлого прогона — тот был убит до чистки)")

    probe_dir.mkdir(parents=True, exist_ok=True)
    invalidate_files()
    victim = probe_dir / "SKILL.md"
    try:
        victim.write_text(
            '---\nname: _refcheck-probe\ndescription: "одноразовый пробник"\n---\n\n'
            "Контроль: `references/заведомо-нет-такого.md`\n", encoding="utf-8")
        _, br, _ = scan()
        found = any("заведомо-нет-такого" in b["ref"] for b in br)
    finally:
        victim.unlink(missing_ok=True)
        invalidate_files()
        try:
            probe_dir.rmdir()
        except OSError:
            pass
    # Диагноз при непойманной канарейке был неверен: «детектор не жив» отправляет
    # чинить регэкспы, тогда как втрое чаще ломается ОБХОД — pathlib молча отдаёт
    # неполный список под нагрузкой. Поэтому сначала называем обе версии и
    # печатаем счётчик, по которому их различить.
    if found:
        print("  контрольная поломка: НАЙДЕНА — детектор жив")
    else:
        n = len(files())
        print("  контрольная поломка: НЕ НАЙДЕНА — ОТЧЁТ НЕДЕЙСТВИТЕЛЕН")
        print(f"      обойдено файлов: {n}. Если число заметно меньше обычного —")
        print("      сломан ОБХОД (параллельная нагрузка), а не детектор ссылок.")
        print("      Повтори без других тяжёлых процессов, прежде чем чинить регэкспы.")
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--canary", action="store_true", help="доказать, что детектор ловит")
    ap.add_argument("--json", help="куда сохранить отчёт")
    a = ap.parse_args()

    alive = canary() if a.canary else None
    total, broken, soft = scan()
    n_files = len(files())
    covered = check_coverage(n_files)
    print(f"  файлов обойдено: {n_files}   ссылок разобрано: {total}")
    # «БИТЫХ: 0» печаталось всегда — в том числе когда 75 файлов не читались
    # вовсе. Число битых имеет смысл ТОЛЬКО над полным обходом, поэтому при
    # неполном оно не выводится: пусть лучше не будет цифры, чем будет ложная.
    if covered:
        print(f"  БИТЫХ: {len(broken)}   спорных (ссылка на соседний навык): {len(soft)}")
    else:
        print(f"  БИТЫХ: не считается — обход неполон (нашлось {len(broken)}, "
              f"но это не про всё дерево)")
    for b in broken:
        print(f"    ✗ {b['file']}:{b['line']}  {b['ref']}")
    for s in soft:
        print(f"    ? {s['file']}:{s['line']}  {s['ref']}  ← {s['text'][:70]}")
    if a.json:
        Path(a.json).write_text(json.dumps({"total": total, "broken": broken, "soft": soft},
                                           ensure_ascii=False, indent=1), encoding="utf-8")
    # Неполный обход — такой же провал, как непойманная канарейка: и то и другое
    # значит «мы не знаем, целы ли ссылки». Раньше провалом считалась только
    # канарейка, и просевший обход возвращал 0.
    if (a.canary and not alive) or not covered:
        return 2
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
