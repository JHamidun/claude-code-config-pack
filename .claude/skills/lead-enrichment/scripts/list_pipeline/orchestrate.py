# -*- coding: utf-8 -*-
"""Orchestrator — runs stages 01→04 with checkpoints.

Usage:
    python orchestrate.py --input my_list.xlsx --output enriched.xlsx \
        --workdir ${HOME}/.claude/scratchpad/prospect-2026-06

    # Skip research (CRM-only enrichment):
    python orchestrate.py --input my_list.xlsx --output enriched.xlsx --skip-research

    # Resume — same workdir, will skip done stages:
    python orchestrate.py --input my_list.xlsx --output enriched.xlsx --workdir <same>

    # Force re-run all:
    python orchestrate.py --input my_list.xlsx --output enriched.xlsx --force
"""
import sys, io, os, json, time, subprocess, argparse
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_checkpoint(path):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding='utf-8'))
        except Exception:
            pass
    return {'stages': {}}


def save_checkpoint(path, state):
    state['updated_at'] = datetime.now().isoformat()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def run_stage(name, cmd):
    print(f'\n>>> Stage {name}: {" ".join(cmd[:4])}...')
    t0 = time.time()
    result = subprocess.run(cmd)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f'<<< Stage {name} FAILED (rc={result.returncode}, {elapsed:.0f}s)')
        return False, elapsed
    print(f'<<< Stage {name} OK ({elapsed:.0f}s)')
    return True, elapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='source xlsx/csv with company list')
    ap.add_argument('--output', required=True, help='final enriched.xlsx')
    ap.add_argument('--workdir', default='', help='where to write intermediates (default: alongside output)')
    ap.add_argument('--sheets', default='', help='xlsx sheets to parse (comma-separated)')
    ap.add_argument('--research-limit', type=int, default=500,
                    help='cap on cold-tier (A) by rev2024. Use 0 for no research')
    ap.add_argument('--skip-research', action='store_true', help='skip stage 3 entirely')
    ap.add_argument('--linkedin', default='', help='linkedin.json path (optional)')
    ap.add_argument('--bitrix-url', default='https://we.company.example')
    ap.add_argument('--inn-field', default='UF_CRM_INN')
    ap.add_argument('--product-hint', default='', help='hint for Perplexity prompt')
    ap.add_argument('--force', action='store_true', help='re-run all stages, ignore checkpoint')
    args = ap.parse_args()

    input_abs = os.path.abspath(args.input)
    if not os.path.exists(input_abs):
        raise SystemExit(f'Input not found: {input_abs}')
    output_abs = os.path.abspath(args.output)
    workdir = os.path.abspath(args.workdir) if args.workdir else os.path.join(os.path.dirname(output_abs), '_prospect_workdir')
    os.makedirs(workdir, exist_ok=True)

    chk_path = os.path.join(workdir, 'checkpoint.json')
    state = load_checkpoint(chk_path)
    input_mtime = os.path.getmtime(input_abs)

    if args.force or state.get('input_mtime') != input_mtime:
        state = {
            'stages': {},
            'input_path': input_abs,
            'input_mtime': input_mtime,
            'started_at': datetime.now().isoformat(),
        }

    extracted_path = os.path.join(workdir, 'extracted.json')
    bitrix_path = os.path.join(workdir, 'bitrix_data.json')
    research_dir = os.path.join(workdir, 'research')
    research_results = os.path.join(research_dir, 'results.json')
    research_queue = os.path.join(research_dir, 'queue.json')

    py = sys.executable or 'python'

    # ===== Stage 1: extract =====
    if state['stages'].get('extract', {}).get('done') and os.path.exists(extracted_path):
        rows_count = state['stages']['extract'].get('rows', '?')
        print(f'[1/4] extract: SKIP (already done, {rows_count} rows)')
    else:
        cmd = [py, os.path.join(SCRIPT_DIR, '01_extract.py'),
               '--input', input_abs, '--output', extracted_path]
        if args.sheets:
            cmd.extend(['--sheets', args.sheets])
        ok, elapsed = run_stage('1/4 extract', cmd)
        if not ok:
            save_checkpoint(chk_path, state)
            raise SystemExit('extract failed')
        rows = json.load(open(extracted_path, encoding='utf-8'))
        state['stages']['extract'] = {
            'done': True, 'ts': datetime.now().isoformat(),
            'rows': len(rows), 'elapsed_sec': round(elapsed),
        }
        save_checkpoint(chk_path, state)

    # ===== Stage 2: match Bitrix =====
    if state['stages'].get('match', {}).get('done') and os.path.exists(bitrix_path):
        matched = state['stages']['match'].get('matched', '?')
        print(f'[2/4] match: SKIP (already done, {matched} INNs matched)')
    else:
        cmd = [py, os.path.join(SCRIPT_DIR, '02_match_bitrix.py'),
               '--input', extracted_path, '--output', bitrix_path,
               '--inn-field', args.inn_field, '--bitrix-url', args.bitrix_url]
        ok, elapsed = run_stage('2/4 match', cmd)
        if not ok:
            save_checkpoint(chk_path, state)
            raise SystemExit('match failed')
        bd = json.load(open(bitrix_path, encoding='utf-8'))
        state['stages']['match'] = {
            'done': True, 'ts': datetime.now().isoformat(),
            'matched': len(bd.get('by_inn', {})),
            'elapsed_sec': round(elapsed),
        }
        save_checkpoint(chk_path, state)

    # ===== Stage 3: research =====
    if args.skip_research or args.research_limit == 0:
        print(f'[3/4] research: SKIP (--skip-research or limit=0)')
        state['stages']['research'] = {'done': True, 'skipped': True}
        save_checkpoint(chk_path, state)
    elif state['stages'].get('research', {}).get('done') and os.path.exists(research_results):
        ok_count = state['stages']['research'].get('ok', '?')
        print(f'[3/4] research: SKIP (already done, {ok_count} OK)')
    else:
        cmd = [py, os.path.join(SCRIPT_DIR, '03_research_perplexity.py'),
               '--input', extracted_path, '--bitrix', bitrix_path,
               '--workdir', research_dir, '--output', research_results,
               '--limit', str(args.research_limit)]
        if args.product_hint:
            cmd.extend(['--product-hint', args.product_hint])
        ok, elapsed = run_stage('3/4 research', cmd)
        if not ok:
            print('[!] research stage non-zero, but partial cache may exist — continuing to build')
        if os.path.exists(research_results):
            res = json.load(open(research_results, encoding='utf-8'))
            ok_count = sum(1 for v in res.values() if v.get('status') == 'ok')
            state['stages']['research'] = {
                'done': ok, 'ts': datetime.now().isoformat(),
                'ok': ok_count, 'total': len(res),
                'elapsed_sec': round(elapsed),
            }
        save_checkpoint(chk_path, state)

    # ===== Stage 4: build =====
    cmd = [py, os.path.join(SCRIPT_DIR, '04_build_xlsx.py'),
           '--input', extracted_path, '--bitrix', bitrix_path,
           '--output', output_abs, '--bitrix-url', args.bitrix_url]
    if args.input.lower().endswith(('.xlsx', '.xlsm')):
        cmd.extend(['--source-xlsx', input_abs])
    if os.path.exists(research_results):
        cmd.extend(['--research', research_results])
    if os.path.exists(research_queue):
        cmd.extend(['--research-queue', research_queue])
    if args.linkedin and os.path.exists(args.linkedin):
        cmd.extend(['--linkedin', os.path.abspath(args.linkedin)])
    ok, elapsed = run_stage('4/4 build', cmd)
    if not ok:
        save_checkpoint(chk_path, state)
        raise SystemExit('build failed')
    state['stages']['build'] = {
        'done': True, 'ts': datetime.now().isoformat(),
        'output': output_abs, 'elapsed_sec': round(elapsed),
    }
    save_checkpoint(chk_path, state)

    print(f'\n=== ALL DONE ===')
    print(f'Workdir:    {workdir}')
    print(f'Final xlsx: {output_abs}')


if __name__ == '__main__':
    main()
