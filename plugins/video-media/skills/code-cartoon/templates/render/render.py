"""Render a canvas cartoon page to MP4: N headless Chromium pages draw interleaved frames (renderAt(t) is deterministic),
JPEG frames go to disk, then ffmpeg encodes (+ optional audio). Also dumps window.CUES (the sound cue sheet) to <out>.cues.json.

    python render/render.py <page.html> <out.mp4> [--fmt land|port] [--extra 'k=v&k2=v2'] [--fps 24] [--workers 6]
                            [--from 0] [--to <s>] [--audio mix.wav] [--q 95] [--keep] [--last-frame] [--http] [--gpu | --no-gpu]

Page contract: canvas#cv, global renderAt(t) (synchronous, deterministic), window.__ready === true, optional window.CUES,
global TIMING. pencil pages open from file://; gloss/ pages (ES modules) are served over http by an in-process server on a
free port and get the GPU flags (render/pagekit.py). A page error or a missing font/script aborts the render.
<out>.frames/ is wiped at the start and deleted after encoding unless --keep. Audio is padded with silence to the video
length (a short mix never trims the picture). At the end ffprobe prints what was actually written.
"""
import argparse
import base64
import json
import multiprocessing as mp
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from pagekit import GL_PROBE, is_fatal_console, page_url, timing_info


def worker(job):
    url, args, fmt, extra, frames, fps, outdir, q, wid = job
    W, H = (1080, 1920) if fmt == 'port' else (1920, 1080)
    t0 = time.time()
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=args)
        pg = b.new_page(viewport={'width': W, 'height': H})
        errs, notes = [], []
        pg.on('pageerror', lambda e: errs.append(str(e)))

        def on_console(m):
            loc = (m.location or {}).get('url', '')
            line = f'{m.type}: {m.text.strip().splitlines()[0] if m.text.strip() else ""}'[:200]
            (errs if is_fatal_console(m.type, m.text, loc) else notes).append(f'{line} {loc}'.strip())
        pg.on('console', on_console)
        pg.goto(url + f'?fmt={fmt}&{extra}')
        try:                               # the page sets __failed on a script error: stop at once, not after the timeout
            pg.wait_for_function('window.__ready === true || window.__failed === true', timeout=120000)
            ready = pg.evaluate('window.__ready === true')
        except Exception:
            ready = False
        if not ready:
            raise RuntimeError('page not ready: ' + ' | '.join((errs + notes)[:8]))
        if errs:
            raise RuntimeError('page broken while loading: ' + ' | '.join(errs[:5]))
        if args and wid == 0:
            notes.insert(0, 'webgl: ' + pg.evaluate(GL_PROBE))
        for f in frames:
            d = pg.evaluate(f"t => {{ renderAt(t); return document.getElementById('cv').toDataURL('image/jpeg', {q / 100}); }}", f / fps)
            (Path(outdir) / f'f{f:05d}.jpg').write_bytes(base64.b64decode(d.split(',', 1)[1]))
            if errs:
                raise RuntimeError(f'frame {f}: {errs[0]}')
        cues = pg.evaluate('window.CUES || []') if wid == 0 else None
        b.close()
    return wid, len(frames), time.time() - t0, cues, notes[:5]


def probe(out, expect_s):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate:format=duration',
                        '-of', 'json', str(out)], capture_output=True, text=True)
    info = json.loads(r.stdout or '{}')
    st = info.get('streams', [])
    v = next((s for s in st if s.get('codec_type') == 'video'), {})
    a = next((s for s in st if s.get('codec_type') == 'audio'), None)
    dur = float(info.get('format', {}).get('duration', 0))
    line = f"check: video {v.get('codec_name')} {v.get('width')}x{v.get('height')} {v.get('r_frame_rate')} fps, {dur:.3f} s; "
    line += f"audio {a.get('codec_name')} {a.get('sample_rate')} Hz" if a else 'audio: none'
    print(line)
    if abs(dur - expect_s) > 0.05:
        print(f'WARNING: duration {dur:.3f} s, expected {expect_s:.3f} s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('page'); ap.add_argument('out')
    ap.add_argument('--fmt', default='land', choices=['land', 'port']); ap.add_argument('--extra', default='')
    ap.add_argument('--fps', type=int, default=24); ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--from', dest='t0', type=float, default=0); ap.add_argument('--to', dest='t1', type=float, default=None)
    ap.add_argument('--audio', default=None); ap.add_argument('--q', type=int, default=95); ap.add_argument('--keep', action='store_true')
    ap.add_argument('--last-frame', action='store_true', help='also save the last frame of the MP4 as <out>.last.png (poster check)')
    ap.add_argument('--http', action='store_true', help='serve the page over http even if it is not under gloss/')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--gpu', dest='gpu', action='store_true', default=None); g.add_argument('--no-gpu', dest='gpu', action='store_false')
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur, draft = timing_info(a.page)
    if a.t1 is None and dur is None:
        raise SystemExit('no timing/timing.json: run timing/fake_timing.py (draft) or timing/build_timing.py, or pass --to')
    if draft:
        print('DRAFT timing (no voice): fine for previews, not for the final render')
    t1 = a.t1 if a.t1 is not None else dur
    allf = list(range(int(round(a.t0 * a.fps)), int(round(t1 * a.fps))))
    if not allf:
        raise SystemExit('nothing to render: check --from/--to')
    url, args, srv = page_url(a.page, use_http=True if a.http else None, use_gpu=a.gpu)
    print(f'{url}  {" ".join(args) or "(cpu canvas)"}')
    frames_dir = out.with_suffix('.frames')
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)
    workers = max(1, min(a.workers, len(allf)))
    chunks = [allf[i::workers] for i in range(workers)]          # interleaved: equal load per worker
    t0 = time.time()
    try:
        with mp.Pool(workers) as pool:
            res = pool.map(worker, [(url, args, a.fmt, a.extra, ch, a.fps, str(frames_dir), a.q, i) for i, ch in enumerate(chunks)])
    finally:
        if srv:
            srv.shutdown()
    cues = next(r[3] for r in res if r[0] == 0)
    for n in dict.fromkeys(n for r in res for n in r[4]):        # unique, in order (e.g. the WebGL renderer, shader warnings)
        print('page note:', n)
    out.with_suffix('.cues.json').write_text(json.dumps(cues, ensure_ascii=False), encoding='utf-8')
    got = len(list(frames_dir.glob('f*.jpg')))
    if got != len(allf):
        raise SystemExit(f'{got} frames on disk, expected {len(allf)}')
    print(f'{len(allf)} frames in {time.time() - t0:.0f} s ({(time.time() - t0) / len(allf) * 1000:.0f} ms/frame wall, {workers} workers); {len(cues)} cues')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(a.fps), '-start_number', str(allf[0]), '-i', str(frames_dir / 'f%05d.jpg')]
    if a.audio:
        cmd += ['-ss', str(a.t0), '-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-af', 'apad', '-shortest']
    cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(out)]
    subprocess.run(cmd, check=True)
    if not a.keep:
        shutil.rmtree(frames_dir)
    print('->', out)
    probe(out, len(allf) / a.fps)
    if a.last_frame:
        last = out.with_suffix('.last.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-1', '-i', str(out), '-update', '1', str(last)], check=True)
        print('->', last)


if __name__ == '__main__':
    main()
