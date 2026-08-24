# -*- coding: utf-8 -*-
"""
cross_chapter_metrics.py — проверка плотности ключевых терминов, side-blocks,
cliffhanger-стыков по всем главам книги.

Состав глав, сквозные термины и маркер side-block берутся из `$BOOK_ROOT/book.json`
(секция `metrics`), а не из кода: скрипт общий для любой книги.
Образец с пояснениями — `../templates/book.example.json`.

Usage:
    BOOK_ROOT=./book python cross_chapter_metrics.py --version v13.2

Environment:
    BOOK_ROOT — путь к корню книги (обязателен)
"""
import io, os, sys, re, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# Работа — в main(), под `if __name__ == "__main__"`. На верхнем уровне модуля
# только определения: импорт этого файла (линтер с исполнением, автодополнение
# в редакторе, `python -c "import ..."`) не должен ничего запускать и писать.
def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        # --help must not touch the filesystem or build anything: print the module
        # docstring and exit before any work starts.
        print(__doc__ or 'no docstring')
        sys.exit(0)

    # --- CONFIG ---

    _book_root_env = os.environ.get('BOOK_ROOT')
    if not _book_root_env:
        sys.exit(
            'BOOK_ROOT не задан.\n'
            'Это путь к корню книги — папке, внутри которой лежат chapters/ и book.json.\n'
            '  Windows:  set BOOK_ROOT=C:\\path\\to\\book\n'
            '  bash:     export BOOK_ROOT=./book'
        )
    BOOK_ROOT = Path(_book_root_env).expanduser()
    CHAPTERS_DIR = BOOK_ROOT / 'chapters'

    CONFIG_PATH = BOOK_ROOT / 'book.json'
    if not CONFIG_PATH.exists():
        sys.exit(
            'Нет файла %s.\n'
            'Скопируй образец и заполни своим:\n'
            '  cp ../templates/book.example.json "%s"' % (CONFIG_PATH, CONFIG_PATH)
        )
    with io.open(CONFIG_PATH, encoding='utf-8') as _f:
        CFG = json.load(_f)

    M = CFG.get('metrics') or {}
    if not M.get('chapters_order') or not M.get('key_terms'):
        sys.exit(
            'В %s нет секции "metrics" с полями chapters_order и key_terms.\n'
            'Без них считать нечего: скрипт не знает ни порядка глав, ни сквозных терминов.\n'
            'См. ../templates/book.example.json' % CONFIG_PATH
        )

    VERSION = os.environ.get('BOOK_VERSION_TAG', 'v1')
    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--version' and i + 1 < len(sys.argv) - 1:
            VERSION = sys.argv[i + 2]
            break
        if arg.startswith('--version='):
            VERSION = arg.split('=', 1)[1]
            break

    # Порядок глав книги для чтения (slug'и папок в chapters/)
    CHAPTERS_ORDER = list(M['chapters_order'])

    # Сквозные термины: «как называть в отчёте» -> регулярка поиска.
    # Правило от книги не зависит: термин концентрируется в главе, где вводится,
    # и появляется 0-2 раза в остальных.
    KEY_TERMS = dict(M['key_terms'])

    # Маркер врезки, которая должна быть в каждой содержательной главе
    # (у каждой книги свой; пустая строка отключает проверку F2).
    SIDE_BLOCK = M.get('side_block') or ''

    # Главы, в которых врезка обязательна (back-matter и манифест обычно исключают)
    SIDE_BLOCK_REQUIRED = list(M.get('side_block_required') or [])

    # Порядок отката по версиям, если файла запрошенной версии нет
    FALLBACK_VERSIONS = list(M.get('fallback_versions') or ['FINAL', 'proofread'])


    def load_chapter_text(slug, version):
        """Load chapter file content (try v-N first, fall back through versions)."""
        ch_dir = CHAPTERS_DIR / slug
        candidates = [ch_dir / f'DRAFT.{version}.md']
        for ver in FALLBACK_VERSIONS:
            candidates.append(ch_dir / ('FINAL.md' if ver == 'FINAL' else f'DRAFT.{ver}.md'))
        for p in candidates:
            if p.exists():
                return p.read_text(encoding='utf-8'), p.name
        return None, None


    def count_term(text, regex):
        return len(re.findall(regex, text, re.IGNORECASE))


    def extract_ending(text, n_chars=300):
        """Get last n_chars of chapter body (strip frontmatter and source-trace)."""
        # Strip frontmatter
        text = re.sub(r'^---\n.*?\n---\n+', '', text, count=1, flags=re.DOTALL)
        # Strip source-trace
        text = re.sub(r'<!--\s*source-trace:.*?-->\s*', '', text, flags=re.DOTALL)
        # Strip PROOFREAD-NOTES
        text = re.sub(r'PROOFREAD[\-\s]?NOTES?:[\s\S]*$', '', text)
        text = text.rstrip()
        return text[-n_chars:].strip() if len(text) > n_chars else text.strip()


    def extract_opening(text, n_chars=300):
        """Get first n_chars of chapter body (after H1, frontmatter)."""
        text = re.sub(r'^---\n.*?\n---\n+', '', text, count=1, flags=re.DOTALL)
        text = re.sub(r'^#\s+[^\n]+\n+', '', text.lstrip(), count=1)
        # Skip blockquote epigraph
        text = re.sub(r'^>[^\n]*\n(>[^\n]*\n)*\n+', '', text, count=1)
        return text[:n_chars].strip()


    # --- METRICS ---

    print(f"\n=== Cross-chapter metrics for {VERSION} ===\n")
    print(f"BOOK_ROOT: {BOOK_ROOT}")
    print(f"Chapters: {len(CHAPTERS_ORDER)}\n")

    # F1. Term density
    print("=== F1. Плотность ключевых терминов по главам ===\n")
    header = f"{'Глава':<32} | " + " | ".join(f"{name[:10]:>10}" for name in KEY_TERMS.keys())
    print(header)
    print('-' * len(header))

    for slug in CHAPTERS_ORDER:
        text, fname = load_chapter_text(slug, VERSION)
        if text is None:
            print(f"{slug:<32} | MISSING")
            continue
        counts = [count_term(text, regex) for regex in KEY_TERMS.values()]
        row = f"{slug:<32} | " + " | ".join(f"{c:>10d}" for c in counts)
        print(row)

    # F2. Side-block presence
    if not SIDE_BLOCK or not SIDE_BLOCK_REQUIRED:
        print("\n=== F2. Side-block — пропущена (в book.json не задан metrics.side_block) ===\n")
        SIDE_BLOCK_REQUIRED = []
    else:
        print(f"\n=== F2. Side-block '{SIDE_BLOCK}' ===\n")
    for slug in SIDE_BLOCK_REQUIRED:
        text, fname = load_chapter_text(slug, VERSION)
        if text is None:
            print(f"[MISSING-FILE] {slug}")
            continue
        if re.search(SIDE_BLOCK, text):
            print(f"[OK]      {slug}")
        else:
            print(f"[MISSING] {slug}  ← side-block not found")

    # F3. Cliffhanger → opening stykov
    print("\n=== F3. Cliffhanger → opening стыки ===\n")
    for i in range(len(CHAPTERS_ORDER) - 1):
        curr = CHAPTERS_ORDER[i]
        nxt = CHAPTERS_ORDER[i + 1]
        curr_text, _ = load_chapter_text(curr, VERSION)
        nxt_text, _ = load_chapter_text(nxt, VERSION)
        if curr_text is None or nxt_text is None:
            continue
        print(f"--- {curr} → {nxt} ---")
        print(f"  ENDING ({curr}):")
        print(f"    {extract_ending(curr_text, 250)[:250]}...")
        print(f"  OPENING ({nxt}):")
        print(f"    {extract_opening(nxt_text, 250)[:250]}...")
        print()

    # F4. Word count delta from previous version
    print("=== F4. Word count по версиям ===\n")
    print(f"{'Глава':<32} | {'v-prev':>8} | {'v13':>8} | {'Δ':>6}")
    print('-' * 60)
    for slug in CHAPTERS_ORDER:
        ch_dir = CHAPTERS_DIR / slug
        files = sorted(ch_dir.glob('DRAFT.v*.md'))
        if len(files) >= 2:
            prev = files[-2].read_text(encoding='utf-8')
            curr = files[-1].read_text(encoding='utf-8')
            prev_w = len(re.findall(r'\b\w+\b', prev))
            curr_w = len(re.findall(r'\b\w+\b', curr))
            delta = curr_w - prev_w
            pct = (delta / prev_w * 100) if prev_w > 0 else 0
            print(f"{slug:<32} | {prev_w:>8d} | {curr_w:>8d} | {pct:+5.1f}%")
        elif len(files) == 1:
            curr = files[0].read_text(encoding='utf-8')
            curr_w = len(re.findall(r'\b\w+\b', curr))
            print(f"{slug:<32} | {'-':>8} | {curr_w:>8d} | {'-':>6}")

    print("\n=== Done ===\n")


if __name__ == "__main__":
    main()
