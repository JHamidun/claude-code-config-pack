"""Sequential project manifest with bounded stages and resumable outputs."""
import argparse
import os
import sys
from pathlib import Path
from common import read_json, write_json, resolve, writable, run, stop_check
from contract import load, require


def execute(file, start=False, keep_going=False):
    file = Path(file).resolve(); root = file.parent
    jobs = read_json(file)['jobs']
    require(jobs, 'Batch has no jobs')
    seen = {k: set() for k in ['id', 'config', 'work', 'output']}
    plans = []
    state_dirs = []
    for job in jobs:
        config = resolve(root, job['config']); c = load(config)
        for k, value in [('id', job['id']), ('config', config), ('work', c['_work']), ('output', c['_output'])]:
            require(value not in seen[k], f'Duplicate batch {k}: {value}'); seen[k].add(value)
        for folder in [c['_work'], c['_output']]:
            require(all(folder != old and folder not in old.parents and old not in folder.parents for old in state_dirs),
                    'Batch work/output directories must be disjoint')
            state_dirs.append(folder)
        plans.append((job['id'], config))
    print(f'{len(plans)} lessons, sequential; start={start}', flush=True)
    if not start:
        for job, config in plans:
            print(job, config)
        return
    work = writable(root / 'batch-work'); work.mkdir(exist_ok=True)
    os.environ['SKETCH_BATCH_STOP'] = str(root / 'STOP')
    report = {'jobs': [], 'status': 'running'}
    for i, (job, config) in enumerate(plans):
        stop_check(root)
        try:
            run([sys.executable, '-B', Path(__file__).with_name('pipeline.py'), config, '--start'],
                work / f'job-{i:04d}.log', root, timeout=21600)
            report['jobs'].append({'id': job, 'status': 'technical_pass', 'editorial_review': 'pending'})
        except (RuntimeError, TimeoutError) as e:
            report['jobs'].append({'id': job, 'status': 'failed', 'error': str(e)})
            report['status'] = 'failed'
            write_json(work / 'status.json', report)
            if not keep_going:
                raise
        write_json(work / 'status.json', report)
    report['status'] = 'failed' if any(j['status'] == 'failed' for j in report['jobs']) else 'technical_pass'
    write_json(work / 'status.json', report)
    if report['status'] == 'failed':
        raise RuntimeError('One or more batch lessons failed')


def main():
    p = argparse.ArgumentParser(); p.add_argument('manifest'); p.add_argument('--start', action='store_true')
    p.add_argument('--continue-on-error', action='store_true'); a = p.parse_args()
    execute(a.manifest, a.start, a.continue_on_error)


if __name__ == '__main__':
    main()
