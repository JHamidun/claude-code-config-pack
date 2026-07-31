# -*- coding: utf-8 -*-
"""
Sync .md files into results.json after batch_research_template.py run.

USAGE:
    python sync_results.py /path/to/work_dir

Reads queue.json + all *.md files in work_dir → writes results.json:
{
    "{id}": {
        "name": "...",
        "status": "ok" | "pending",
        "text": "...",       # only if status=ok
        ...any other fields from queue.json passed through
    },
    ...
}
"""
import sys, io, json, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WORK_DIR = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
QUEUE_FILE = os.path.join(WORK_DIR, 'queue.json')
RESULTS_FILE = os.path.join(WORK_DIR, 'results.json')


def main():
    if not os.path.exists(QUEUE_FILE):
        sys.exit(f'ERROR: {QUEUE_FILE} not found')

    queue = json.load(open(QUEUE_FILE, encoding='utf-8'))
    results = {}

    for p in queue:
        if 'id' not in p:
            continue
        eid = p['id']
        md_path = os.path.join(WORK_DIR, f'{eid}.md')

        entry = {k: v for k, v in p.items() if k != 'id'}
        entry['status'] = 'pending'
        entry['text'] = ''

        if os.path.exists(md_path):
            try:
                text = open(md_path, encoding='utf-8').read()
                if len(text) > 300 and 'ERROR' not in text[:50] and 'TIMEOUT' not in text[:50]:
                    entry['status'] = 'ok'
                    entry['text'] = text
            except Exception as e:
                entry['status'] = f'read_error: {e}'

        results[eid] = entry

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for v in results.values() if v['status'] == 'ok')
    pending = sum(1 for v in results.values() if v['status'] == 'pending')
    errors = len(results) - ok - pending

    print(f'Wrote {RESULTS_FILE}')
    print(f'  OK:      {ok}/{len(results)}')
    print(f'  Pending: {pending}')
    if errors:
        print(f'  Errors:  {errors}')


if __name__ == '__main__':
    main()
