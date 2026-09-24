"""Shared deterministic I/O, subprocess limits and media metadata."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


def resolve(root, value):
    p = Path(value).expanduser()
    return (p if p.is_absolute() else Path(root) / p).resolve()


def writable(path):
    p = Path(path).expanduser().resolve()
    # Agent configuration and skill install locations are never job state.
    protected = [Path.home() / n for n in ('.claude', '.codex', '.agents')]
    protected.append(SKILL)
    if any(p == q.resolve() or q.resolve() in p.parents for q in protected):
        raise ValueError(f'Output is inside a read-only source/skill: {p}')
    return p


def stop_check(root):
    markers = [Path(root) / 'STOP']
    if os.environ.get('SKETCH_BATCH_STOP'):
        markers.append(Path(os.environ['SKETCH_BATCH_STOP']))
    if any(p.exists() for p in markers):
        raise InterruptedError('STOP requested; checkpoint retained')


def terminate(p):
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
    else:
        import signal
        os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()


def run(command, log, root, cwd=None, timeout=1800):
    """Only this process tree is stopped; never shell-interpolate filenames."""
    stop_check(root)
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w', encoding='utf-8') as f:
        p = subprocess.Popen([str(x) for x in command], cwd=cwd, stdout=f, stderr=f,
            creationflags=getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0),
            start_new_session=os.name != 'nt')
        deadline = time.monotonic() + timeout
        try:
            while p.poll() is None:
                stop_check(root)
                if time.monotonic() > deadline:
                    raise TimeoutError(f'Process timed out; log: {log}')
                time.sleep(.25)
            if p.returncode:
                raise RuntimeError(f'Process failed ({p.returncode}); log: {log}')
        except BaseException:
            if p.poll() is None:
                terminate(p)
            raise


def probe(path, ffprobe='ffprobe'):
    return json.loads(subprocess.check_output([ffprobe, '-v', 'error', '-show_streams',
        '-show_format', '-of', 'json', str(path)], timeout=60))


def video_stream(path):
    return next(s for s in probe(path)['streams'] if s['codec_type'] == 'video')


def audio_hash(path):
    return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map',
        '0:a:0', '-c:a', 'copy', '-f', 'hash', '-hash', 'sha256', '-'], timeout=180).decode().strip()


def encoder(name='libx264'):
    if name == 'h264_nvenc':
        return ['-c:v', name, '-preset', 'p5', '-rc', 'vbr', '-cq', '17', '-b:v', '0']
    if name == 'libx264':
        return ['-c:v', name, '-preset', 'fast', '-crf', '18', '-threads', '2']
    raise ValueError('encoder must be libx264 or h264_nvenc')


def frame_args():
    return ['-pix_fmt', 'yuv420p', '-color_range', 'tv', '-colorspace', 'bt709',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart']
