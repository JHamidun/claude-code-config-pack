"""PNG stills of a canvas page at given times (look at them before showing anything to a human).

    python render/still.py <page.html> <out_prefix> <t1,t2,...> [land|port] [extra-query] [--det] [--http] [--gpu | --no-gpu]
      -> <out_prefix>_<t:06.2f>.png   (the folder of out_prefix is created)
    e.g. python render/still.py pencil/index.html st/p 0.5,2.5,5 port
         python render/still.py pencil/index.html st/sheet 0.5 land "scenes=test_doodles.js"

--det renders every time twice (as given, then in reverse order) and compares the pixels: catches Math.random, clocks and
state that leaks between frames (renderAt must be a pure function of t). If the page never becomes ready, prints
NOT READY + the console: the quickest way to see a JS error. gloss/ pages are served over http (render/pagekit.py).
"""
import base64
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from pagekit import GL_PROBE, page_url

flags = {f for f in sys.argv[1:] if f.startswith('--')}
pos = [x for x in sys.argv[1:] if not x.startswith('--')]
if len(pos) < 3:
    raise SystemExit(__doc__)
page, out, ts = Path(pos[0]).resolve(), pos[1], [float(x) for x in pos[2].split(',') if x.strip()]
fmt = pos[3] if len(pos) > 3 else 'land'
extra = pos[4] if len(pos) > 4 else ''
W, H = (1080, 1920) if fmt == 'port' else (1920, 1080)
Path(out).parent.mkdir(parents=True, exist_ok=True)
gpu = True if '--gpu' in flags else False if '--no-gpu' in flags else None
url, args, srv = page_url(page, use_http=True if '--http' in flags else None, use_gpu=gpu)
JS = "t => { renderAt(t); return document.getElementById('cv').toDataURL('image/png'); }"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=args)
    pg = b.new_page(viewport={'width': W, 'height': H})
    msgs = []
    pg.on('console', lambda m: msgs.append(f'{m.type}: {(m.text.strip().splitlines() or [""])[0][:200]}'))
    pg.on('pageerror', lambda e: msgs.append('ERR ' + str(e)))
    pg.goto(url + f'?fmt={fmt}&{extra}')
    try:                                   # the page sets __failed on a script error: no need to wait for the timeout
        pg.wait_for_function('window.__ready === true || window.__failed === true', timeout=60000)
        ready = pg.evaluate('window.__ready === true')
    except Exception:
        ready = False
    if not ready:
        print('NOT READY'); [print(m) for m in msgs[:30]]
        b.close()
        raise SystemExit(1)
    if args:
        print('webgl:', pg.evaluate(GL_PROBE))
    shots, failed = {}, False
    for t in ts:
        try:
            shots[t] = pg.evaluate(JS, t)
        except Exception as e:                                  # renderAt threw at this t
            print(f'renderAt({t:g}) threw: {str(e).splitlines()[0]}')
            failed = True
            break
        Path(f'{out}_{t:06.2f}.png').write_bytes(base64.b64decode(shots[t].split(',', 1)[1]))
        print(f'{out}_{t:06.2f}.png')
    if '--det' in flags and not failed:
        bad = [t for t in reversed(ts) if pg.evaluate(JS, t) != shots[t]]
        print('determinism: ' + ('OK, ' + str(len(ts)) + ' frames identical when re-rendered in reverse order' if not bad else 'FAILED at t = ' + ', '.join(f'{t:g}' for t in sorted(bad)) + ' (Math.random, a clock or state kept between frames)'))
        failed = failed or bool(bad)
    for m in list(dict.fromkeys(msgs))[:20]:
        print(m)
    b.close()
if srv:
    srv.shutdown()
if failed or any(m.startswith('ERR ') for m in msgs):
    print('FAILED: page errors above')
    raise SystemExit(1)
print('ok')
