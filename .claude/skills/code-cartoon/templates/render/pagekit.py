"""Page helpers shared by render.py and still.py: the project root, how to open a page, an in-process static server.

Pencil pages open from file://. Pages that import ES modules (three.js: everything under gloss/, or any page with
type="module" / an importmap) cannot load from file:// — they are served over http from the project root by a
ThreadingHTTPServer started inside the calling process on a free port (no fixed port, nothing to keep running in the
background, no clash with another project's server) and get the GPU flags for WebGL in headless Chromium.
"""
import functools
import http.server
import re
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPU_ARGS = ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader']
# explicit types: on Windows the registry can map .js to text/plain, and Chromium refuses such a module script
MIME = {'.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm',
        '.html': 'text/html', '.css': 'text/css', '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff': 'font/woff',
        '.woff2': 'font/woff2', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml',
        '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.hdr': 'application/octet-stream', '.wav': 'audio/wav'}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME}

    def log_message(self, *args):
        pass


def needs_http(page):
    p = Path(page).resolve()
    if 'gloss' in p.parts:
        return True
    try:
        html = p.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return False
    return bool(re.search(r'type\s*=\s*["\']?(module|importmap)', html))


def serve(root=ROOT):
    """Static server for root on 127.0.0.1:<free port>, in a daemon thread; dies with the process."""
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(_QuietHandler, directory=str(root)))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def page_url(page, use_http=None, use_gpu=None):
    """-> (url, chromium args, server or None). use_http / use_gpu: None = decide from the page."""
    p = Path(page).resolve()
    if not p.exists():
        raise SystemExit(f'page not found: {p}')
    http_mode = needs_http(p) if use_http is None else use_http
    srv = None
    if http_mode:
        try:
            rel = p.relative_to(ROOT).as_posix()
        except ValueError:
            raise SystemExit(f'{p} is outside the project root {ROOT}: the http mode serves the project root only')
        srv = serve(ROOT)
        url = f'http://127.0.0.1:{srv.server_address[1]}/{rel}'
    else:
        url = p.as_uri()
    gpu = http_mode if use_gpu is None else use_gpu
    return url, (GPU_ARGS if gpu else []), srv


# which WebGL renderer the page really gets: «ANGLE (NVIDIA ..., D3D11)» = GPU, «SwiftShader» = software (several times slower)
GL_PROBE = """() => { const c = document.createElement('canvas'); const gl = c.getContext('webgl2') || c.getContext('webgl');
  if (!gl) return 'no WebGL'; const e = gl.getExtension('WEBGL_debug_renderer_info');
  return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); }"""


def is_fatal_console(msg_type, text, url=''):
    """Console errors that mean a broken page (missing font / script / scenes file), not a harmless warning."""
    if msg_type != 'error':
        return False
    if 'favicon' in (url or '') or 'favicon' in text:
        return False
    return any(s in text for s in ('font not loaded', 'scenes file not found', 'Failed to load resource', 'Uncaught'))


def timing_info(page):
    """(duration, draft) from timing/timing.json; falls back to a timing.js next to the page, then pencil/timing.js."""
    import json
    cands = [ROOT / 'timing' / 'timing.json', Path(page).resolve().parent / 'timing.js', ROOT / 'pencil' / 'timing.js']
    for c in cands:
        if c.exists():
            txt = c.read_text(encoding='utf-8')
            data = json.loads(txt.split('=', 1)[1].rstrip().rstrip(';') if c.suffix == '.js' else txt)
            return data['duration'], bool(data.get('draft'))
    return None, False
