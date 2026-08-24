# -*- coding: utf-8 -*-
"""
Generic Perplexity batch research template.

Прогоняет Perplexity Max по списку сущностей (компании / люди / темы / домены)
батчами по N штук в одном запросе с маркером "## Тип N:" → парсит обратно → пишет
отдельный .md на каждую сущность (idempotent).

USAGE:
    # 1. Сложи список в queue.json в work_dir:
    #    [{"id": "1234567890", "name": "крупный банк", "context": "банки"}, ...]
    #    Поля: id (обязательно, уникальный), name (обязательно), context (опц.)
    #
    # 2. Адаптируй build_prompt() под свой юзкейс (компании/люди/темы/...)
    #    и не забудь поменять MARKER_TYPE — должен совпадать в промпте и в parse_response.
    #
    # 3. Запусти:
    #    python batch_research_template.py /path/to/work_dir
    #
    # 4. После прогона собери результаты:
    #    python ~/.claude/skills/perplexity/scripts/sync_results.py /path/to/work_dir
    #
    # ENV-переменные (опционально):
    #    BATCH=5             — размер батча
    #    WORKERS=3           — параллельных запросов
    #    TIMEOUT=300         — таймаут на батч (сек)
    #    MODE_PRIMARY=pro    — основной режим (pro / auto / reasoning)
    #    MODE_FALLBACK=      — fallback режим (пусто = без fallback)
    #    SLEEP=0             — пауза между батчами (сек, gentle mode = 1)
"""

import sys, io, json, os, subprocess, time, concurrent.futures, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ---------------- CONFIG ----------------

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
QUEUE_FILE = os.path.join(WORK_DIR, 'queue.json')
OUT_DIR = WORK_DIR  # .md files go straight into work_dir

BATCH = int(os.getenv('BATCH', '5'))
WORKERS = int(os.getenv('WORKERS', '3'))
TIMEOUT = int(os.getenv('TIMEOUT', '300'))
MODE_PRIMARY = os.getenv('MODE_PRIMARY', 'pro')
MODE_FALLBACK = os.getenv('MODE_FALLBACK', '').strip()
SLEEP = float(os.getenv('SLEEP', '0'))

# Маркер для structuring/parsing. Меняй если хочешь Person/Topic/Site и т.п.
# Должен совпадать в build_prompt() и в parse_response().
MARKER_TYPE = 'Компания'  # альтернативы: Person | Company | Topic | Site

PPLX_CLI = os.path.expanduser('~/.claude/skills/perplexity/pplx-max.py')

# ---------------- PROMPT ----------------

def build_prompt(batch):
    """Build batch prompt. ADAPT THIS to your use case."""
    items = []
    for idx, p in enumerate(batch, start=1):
        line = f"{idx}. **{p['name']}**"
        if p.get('context'):
            line += f' — {p["context"]}'
        items.append(line)

    items_str = '\n'.join(items)
    return f'''Подготовь краткие досье (по 150-200 слов на каждую) по этим {len(batch)} сущностям на 2026 год:

{items_str}

Для **каждой** дай ровно такую структуру:

## {MARKER_TYPE} {{N}}: {{Название}} [{{ID}}]

**Поле 1:** ключевая информация.
**Поле 2:** свежие события 2025-2026.
**Поле 3:** триггеры / зацепки.

Со ссылками [1][2]. Кратко по делу. **Не пропускай ни одну сущность из списка.**'''


# ---------------- PARSER ----------------

# Regex поддерживает кириллицу/латиницу и оба разделителя (## и ##)
_split_pat = re.compile(rf'\n(?=## ?(?:{MARKER_TYPE}|Company|Person|Topic|Site)\s*\d)')
_match_pat = re.compile(rf'## ?(?:{MARKER_TYPE}|Company|Person|Topic|Site)\s*(\d+)[:.\s-]+(.+?)(?=\n)')


def parse_response(text, batch):
    """Split response into per-entity chunks by ## Type N: marker."""
    chunks = _split_pat.split(text)
    results = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m = _match_pat.match(chunk)
        if not m:
            continue
        n = int(m.group(1))
        if 1 <= n <= len(batch):
            results[batch[n - 1]['id']] = chunk
    return results


# ---------------- WORKER ----------------

def try_query(prompt, mode):
    """Run pplx-max.py once. Return text or None."""
    try:
        # sys.executable, а не строка 'python': имя интерпретатора разное на разных ОС.
        # На macOS 12.3+ бинаря `python` нет вовсе, на Ubuntu 22.04+ — без пакета
        # python-is-python3. Захардкоженное имя давало `FileNotFoundError: 'python'`,
        # который здесь ловится общим `except Exception` и превращается в «сущность не
        # обработалась» — то есть КАЖДЫЙ батч тихо помечался ошибкой запроса, а не
        # отсутствием интерпретатора. sys.executable всегда указывает на тот Python,
        # которым запущен этот же скрипт.
        result = subprocess.run(
            [sys.executable, PPLX_CLI, '--mode', mode, prompt],
            capture_output=True, text=True, timeout=TIMEOUT,
            encoding='utf-8', errors='replace',
        )
        if result.returncode != 0:
            return None, f'rc={result.returncode}: {result.stderr[:200]}'
        text = result.stdout.strip()
        if len(text) < 200:
            return None, f'too_short: {text[:200]}'
        return text, None
    except subprocess.TimeoutExpired:
        return None, 'timeout'
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def research_batch(batch):
    """Process one batch. Returns (batch, dict_id_to_md, err)."""
    prompt = build_prompt(batch)
    text, err = try_query(prompt, MODE_PRIMARY)

    if text is None and MODE_FALLBACK:
        time.sleep(2)
        text, err = try_query(prompt, MODE_FALLBACK)

    if text is None:
        return batch, None, err

    per_entity = parse_response(text, batch)
    for eid, chunk in per_entity.items():
        path = os.path.join(OUT_DIR, f'{eid}.md')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(chunk)
    return batch, per_entity, None


# ---------------- MAIN ----------------

def load_queue():
    """Load queue.json, filter already-done entities."""
    if not os.path.exists(QUEUE_FILE):
        sys.exit(f'ERROR: {QUEUE_FILE} not found. '
                 'Create it as [{"id": "...", "name": "...", "context": "..."}, ...]')
    queue = json.load(open(QUEUE_FILE, encoding='utf-8'))

    remaining = []
    done = 0
    for p in queue:
        if 'id' not in p or 'name' not in p:
            print(f'WARN: skipping item without id/name: {p}')
            continue
        md_path = os.path.join(OUT_DIR, f"{p['id']}.md")
        if os.path.exists(md_path):
            try:
                content = open(md_path, encoding='utf-8').read()
                if len(content) > 300 and 'ERROR' not in content[:50] and 'TIMEOUT' not in content[:50]:
                    done += 1
                    continue
            except Exception:
                pass
        remaining.append(p)
    return queue, remaining, done


def main():
    queue, remaining, done = load_queue()

    print(f'Work dir: {WORK_DIR}')
    print(f'Total queue: {len(queue)}')
    print(f'Already done: {done}')
    print(f'Remaining: {len(remaining)}')
    print(f'Config: BATCH={BATCH} WORKERS={WORKERS} TIMEOUT={TIMEOUT}s '
          f'MODE={MODE_PRIMARY}{" → "+MODE_FALLBACK if MODE_FALLBACK else ""} SLEEP={SLEEP}s')

    if not remaining:
        print('Nothing to do.')
        return

    batches = [remaining[i:i+BATCH] for i in range(0, len(remaining), BATCH)]
    print(f'Batches: {len(batches)}\n')

    t0 = time.time()
    saved = 0
    failed_batches = 0

    if WORKERS == 1:
        # Sequential mode (gentle)
        for i, batch in enumerate(batches, start=1):
            _, per_entity, err = research_batch(batch)
            elapsed = time.time() - t0
            names = ', '.join(p['name'][:20] for p in batch)
            if per_entity:
                saved += len(per_entity)
                eta = elapsed / i * (len(batches) - i)
                print(f'[{i}/{len(batches)}] OK {len(per_entity)}/{len(batch)} '
                      f'(saved={saved}, eta={eta:.0f}s) | {names[:90]}')
            else:
                failed_batches += 1
                print(f'[{i}/{len(batches)}] FAIL ({(err or "?")[:60]}) | {names[:90]}')
            if SLEEP > 0:
                time.sleep(SLEEP)
    else:
        # Parallel mode
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futures = {ex.submit(research_batch, b): b for b in batches}
            for i, fut in enumerate(concurrent.futures.as_completed(futures), start=1):
                batch = futures[fut]
                try:
                    _, per_entity, err = fut.result()
                except Exception as e:
                    err = str(e); per_entity = None
                elapsed = time.time() - t0
                names = ', '.join(p['name'][:20] for p in batch)
                if per_entity:
                    saved += len(per_entity)
                    eta = elapsed / i * (len(batches) - i)
                    print(f'[{i}/{len(batches)}] OK {len(per_entity)}/{len(batch)} '
                          f'(saved={saved}, eta={eta:.0f}s) | {names[:90]}')
                else:
                    failed_batches += 1
                    print(f'[{i}/{len(batches)}] FAIL ({(err or "?")[:60]}) | {names[:90]}')

    elapsed = time.time() - t0
    print(f'\nDone in {elapsed:.0f}s ({elapsed/60:.1f} min).')
    print(f'Saved: {saved}/{len(remaining)} entities.')
    print(f'Failed batches: {failed_batches}/{len(batches)}.')
    if failed_batches > 0:
        print(f'\nTip: rerun in gentle mode to mop up the tail:')
        print(f'  WORKERS=1 BATCH=3 MODE_PRIMARY=auto MODE_FALLBACK=pro SLEEP=1 \\')
        print(f'    python {os.path.basename(__file__)} {WORK_DIR}')


if __name__ == '__main__':
    main()
