#!/usr/bin/env python3
"""
plugins_gc.py — сборщик мусора для кэша плагинов Claude Code
(~/.claude/plugins, ~2.2 ГБ, из них большая часть — хлам).

Как устроен кэш
---------------
  plugins/
    installed_plugins.json      <- ЕДИНСТВЕННЫЙ источник правды: какая версия
                                   каждого плагина активна (поле installPath)
    cache/<marketplace>/<plugin>/<version>/   <- установленные версии; актуальна
                                   только та, на которую указывает installPath,
                                   остальные — остатки прошлых обновлений
    cache/temp_git_*            <- брошенные временные git-клоны установщика
    cache/temp_subdir_*         <- то же самое, другой вид временных папок
    marketplaces/<name>/        <- рабочие копии каталогов маркетплейсов (НЕ трогаем)
    marketplaces/temp_*         <- брошенные временные клоны маркетплейсов
    marketplaces/*.bak          <- бэкап старой копии маркетплейса
    data/                       <- данные плагинов (сессии, куки и т.п.) — НЕ трогаем
    blocklist.json.*.tmp        <- недописанные temp-файлы рядом с blocklist.json

Что проверено перед написанием скрипта (2026-08-17):
  - settings.json (enabledPlugins) ссылается только на имена вида
    name@marketplace — БЕЗ версий и БЕЗ путей;
  - settings.local.json и ~/.claude.json не содержат путей в plugins/cache;
  - значит, единственные версионные ссылки живут в installed_plugins.json.

Правила безопасности
--------------------
  1. По умолчанию — dry-run: только печатает, что было бы удалено.
     Реальное удаление — ТОЛЬКО с явным ключом --apply.
  2. Версия, на которую указывает installPath хоть одной записи
     installed_plugins.json, не удаляется НИКОГДА (даже если плагин
     выключен в enabledPlugins — иначе сломается его повторное включение).
  3. Перед удалением каждый кандидат дополнительно ищется по подстроке
     в settings.json / settings.local.json / ~/.claude.json — если путь
     где-то упомянут, кандидат пропускается с пометкой.
  4. data/ и живые папки маркетплейсов не рассматриваются вовсе.

Использование
-------------
  python plugins_gc.py            # показать план (dry-run)
  python plugins_gc.py --apply    # реально удалить
  python plugins_gc.py --no-sizes # dry-run без подсчёта размеров (быстро)
"""
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
import json
import os
import shutil
import stat
import sys
from pathlib import Path

PLUGINS = Path.home() / ".claude" / "plugins"
CACHE = PLUGINS / "cache"
MARKETPLACES = PLUGINS / "marketplaces"

# Файлы, в которых на всякий случай ищем текстовые упоминания кандидатов.
# Проверка избыточная (см. док-строку), но дешёвая — оставлена как страховка.
CONFIG_FILES = [
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude" / "settings.local.json",
    Path.home() / ".claude.json",
]


def norm(p) -> str:
    """Нормализация пути для сравнения на Windows: абсолютный, нижний регистр,
    прямые слэши. Только так installPath из JSON совпадёт с путём с диска."""
    return os.path.normpath(str(p)).replace("\\", "/").lower()


def dir_size(path: Path) -> int:
    """Размер дерева в байтах. Символические ссылки не обходим, ошибки
    (битые файлы, длинные пути) молча пропускаем — для оценки этого хватает."""
    total = 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} GB"


def load_referenced_paths():
    """Читаем installed_plugins.json и возвращаем:
    - множество нормализованных installPath (защищённые версии),
    - сырой словарь плагинов (для отчёта)."""
    f = PLUGINS / "installed_plugins.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    referenced = {}
    for name, entries in data.get("plugins", {}).items():
        for e in entries:
            ip = e.get("installPath")
            if ip:
                referenced[norm(ip)] = name
    return referenced, data


def load_enabled_plugins():
    """Множество включённых плагинов (name@marketplace) из settings.json."""
    f = Path.home() / ".claude" / "settings.json"
    try:
        s = json.loads(f.read_text(encoding="utf-8"))
        return {k for k, v in s.get("enabledPlugins", {}).items() if v}
    except (OSError, json.JSONDecodeError):
        return set()


def config_mentions(candidate: Path, config_texts) -> bool:
    """Ищем упоминание пути кандидата в конфигах — в обоих стилях слэшей.
    Ищем именно уникальный хвост пути (relative от ~/.claude/plugins),
    а не голое имя версии вроде '1.0.0', чтобы не ловить ложные совпадения."""
    rel = str(candidate.relative_to(PLUGINS))
    variants = [rel.replace("\\", "/"), rel.replace("/", "\\"),
                rel.replace("\\", "\\\\")]  # JSON экранирует бэкслэши
    for text in config_texts:
        for v in variants:
            if v.lower() in text:
                return True
    return False


def rm_tree(path: Path):
    """Удаление дерева с обходом read-only атрибутов (внутри .git это норма)."""
    def on_error(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError as e:
            print(f"    !! не удалилось: {p}: {e}", file=sys.stderr)
    shutil.rmtree(path, onerror=on_error)


def main():
    ap = argparse.ArgumentParser(description="GC кэша плагинов Claude Code")
    ap.add_argument("--apply", action="store_true",
                    help="реально удалить (без этого ключа — только показ)")
    ap.add_argument("--no-sizes", action="store_true",
                    help="не считать размеры (быстрый показ списка)")
    args = ap.parse_args()

    if not CACHE.is_dir():
        sys.exit(f"Нет каталога {CACHE} — нечего чистить.")

    referenced, raw = load_referenced_paths()
    enabled = load_enabled_plugins()

    # Тексты конфигов для контрольной проверки упоминаний (в нижнем регистре).
    config_texts = []
    for f in CONFIG_FILES:
        try:
            config_texts.append(f.read_text(encoding="utf-8", errors="replace").lower())
        except OSError:
            pass

    candidates = []   # (категория, Path)
    skipped = []      # кандидаты, отклонённые страховкой по конфигам
    keep_versions = []  # защищённые версии (для отчёта)

    # --- 1. Временные папки установщика в cache/ ---------------------------
    for d in sorted(CACHE.iterdir()):
        if d.is_dir() and (d.name.startswith("temp_git_") or d.name.startswith("temp_subdir_")):
            candidates.append(("cache/temp*", d))

    # --- 2. Старые версии плагинов: cache/<mp>/<plugin>/<version> ----------
    for mp in sorted(CACHE.iterdir()):
        if not mp.is_dir() or mp.name.startswith("temp_"):
            continue
        for plugin in sorted(mp.iterdir()):
            if not plugin.is_dir():
                continue
            for version in sorted(plugin.iterdir()):
                if not version.is_dir():
                    continue
                if norm(version) in referenced:
                    keep_versions.append(version)   # активная версия — не трогаем
                else:
                    candidates.append(("старые версии", version))

    # --- 3. Временные клоны и бэкапы в marketplaces/ -----------------------
    if MARKETPLACES.is_dir():
        for d in sorted(MARKETPLACES.iterdir()):
            if d.is_dir() and (d.name.startswith("temp_") or d.name.endswith(".bak")):
                candidates.append(("marketplaces/temp+bak", d))

    # --- 4. Недописанные tmp-файлы blocklist -------------------------------
    for f in sorted(PLUGINS.glob("blocklist.json.*.tmp")):
        candidates.append(("blocklist tmp", f))

    # --- Страховка: путь упомянут в каком-либо конфиге → не удаляем --------
    final = []
    for cat, p in candidates:
        if p.is_dir() and config_mentions(p, config_texts):
            skipped.append((cat, p))
        else:
            final.append((cat, p))

    # --- Отчёт --------------------------------------------------------------
    mode = "APPLY — УДАЛЯЮ" if args.apply else "DRY-RUN — только показываю"
    print(f"=== plugins_gc | режим: {mode} ===\n")

    # Сколько занимают активные версии (для контекста, их не трогаем)
    if not args.no_sizes:
        keep_enabled = keep_disabled = 0
        for v in keep_versions:
            name = referenced[norm(v)]
            sz = dir_size(v)
            if name in enabled:
                keep_enabled += sz
            else:
                keep_disabled += sz
        print(f"ОСТАЁТСЯ (активные версии по installed_plugins.json):")
        print(f"  включённые плагины ({len(enabled)}): {human(keep_enabled)}")
        print(f"  установленные, но выключенные:      {human(keep_disabled)}")
        print(f"  всего защищённых версий: {len(keep_versions)}\n")

    by_cat = {}
    total = 0
    print("К УДАЛЕНИЮ:")
    for cat, p in final:
        sz = 0 if args.no_sizes else (dir_size(p) if p.is_dir() else p.stat().st_size)
        total += sz
        by_cat.setdefault(cat, [0, 0])
        by_cat[cat][0] += 1
        by_cat[cat][1] += sz

    for cat, (cnt, sz) in sorted(by_cat.items(), key=lambda x: -x[1][1]):
        print(f"  {cat:<22} {cnt:>5} объектов  {human(sz):>10}")
    print(f"  {'ИТОГО':<22} {len(final):>5} объектов  {human(total):>10}")

    if skipped:
        print("\nПРОПУЩЕНО страховкой (путь упомянут в конфиге — не трогаю):")
        for cat, p in skipped:
            print(f"  [{cat}] {p}")

    # Детальный список старых версий — их немного и они самые «рискованные»,
    # покажем поимённо, чтобы глазами убедиться, что активных среди них нет.
    old = [p for cat, p in final if cat == "старые версии"]
    if old:
        print(f"\nСтарые версии поимённо ({len(old)}):")
        for p in old:
            print(f"  {p.relative_to(CACHE)}")

    if not args.apply:
        print("\nНичего не удалено. Для удаления: python plugins_gc.py --apply")
        return

    # --- Удаление -----------------------------------------------------------
    print("\nУдаляю...")
    freed = 0
    for cat, p in final:
        try:
            if p.is_dir():
                rm_tree(p)
            else:
                p.unlink()
            freed += 1
        except OSError as e:
            print(f"  !! ошибка на {p}: {e}", file=sys.stderr)
    print(f"Готово: удалено {freed} из {len(final)} объектов, "
          f"освобождено ~{human(total)}.")


if __name__ == "__main__":
    main()
