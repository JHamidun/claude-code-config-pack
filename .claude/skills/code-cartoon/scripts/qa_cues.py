"""Cue sheet vs the drawing grid. On twos a drawing changes only at multiples of 1/12 s, so an event placed at time t
becomes visible at ceil(t*12)/12 and its sound (placed at t) comes EARLY by up to 83 ms.

    python qa_cues.py <out.cues.json> [--tol 0.040]
Prints how many cues lead their picture by more than the tolerance and the worst ones. A cue already snapped to the
grid and rounded by toFixed(3) (71/12 -> 5.917, 0.33 ms past the tick) counts as on the grid, not as 83 ms early."""
import json
import math
import sys

SLACK = 0.01                        # in ticks (0.83 ms): toFixed(3) rounding of a grid time stays on that tick
if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
    raise SystemExit(__doc__)
cues = json.load(open(sys.argv[1], encoding='utf-8'))
if not cues:
    raise SystemExit('empty cue sheet: the page defines no window.CUES')
tol = float(sys.argv[sys.argv.index('--tol') + 1]) if '--tol' in sys.argv else 0.040
lead = [(math.ceil(c['t'] * 12 - SLACK) / 12 - c['t'], c) for c in cues]
bad = sorted([x for x in lead if x[0] > tol], key=lambda x: -x[0])
print(f'{len(cues)} cues, {len(bad)} lead the drawing by > {tol * 1000:.0f} ms, max lead {max(l for l, _ in lead) * 1000:.0f} ms')
for l, c in bad[:12]:
    print(f"  t={c['t']:7.3f}  {c['k']:12s} sound {l * 1000:3.0f} ms before the drawing changes")
