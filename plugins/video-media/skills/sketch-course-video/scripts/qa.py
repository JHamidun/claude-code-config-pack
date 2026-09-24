"""Technical checks and contact sheets; never falsely certify perceptual sync."""
import subprocess
from fractions import Fraction
from PIL import Image, ImageDraw
from common import probe, audio_hash, digest, write_json, run


def check_clip(path, width, height, fps, frames):
    m = probe(path)
    v = next(s for s in m['streams'] if s['codec_type'] == 'video')
    if (v['width'], v['height'], Fraction(v['r_frame_rate']), int(v['nb_frames'])) != (width, height, fps, frames):
        raise ValueError(f'Video contract mismatch: {path}')
    return m


def verify(c, final):
    v = c['video']; out = c['_output']; work = c['_work']
    meta = check_clip(final, v['width'], v['height'], v['fps'], v['frames'])
    vs = next(s for s in meta['streams'] if s['codec_type'] == 'video')
    au = next(s for s in meta['streams'] if s['codec_type'] == 'audio')
    if vs.get('pix_fmt') != 'yuv420p' or vs.get('color_space') != 'bt709' or vs.get('color_range') != 'tv':
        raise ValueError('Unexpected final pixel/color format')
    if abs(float(vs.get('start_time', 0))) > 1 / v['fps'] or abs(float(au.get('start_time', 0))) > .03:
        raise ValueError('Unexpected stream timestamp origin')
    if abs(float(meta['format']['duration']) - v['frames'] / v['fps']) > .1:
        raise ValueError('Duration mismatch (possibly audio extends beyond edit)')
    log = work / 'decode.log'
    run(['ffmpeg', '-v', 'error', '-xerror', '-threads', '2', '-i', str(final), '-f', 'null', '-'],
        log, c['_root'], timeout=1800)
    if log.read_text(encoding='utf-8').strip():
        raise ValueError(f'Decoder reported errors: {log}')
    ah = audio_hash(final)
    if ah != audio_hash(c['_base']):
        raise ValueError('Audio changed during visual-only assembly')
    times = {0, v['frames'] - 1}
    for s in c['scenes']:
        span = s['end'] - s['start']
        times.update(s['start'] + round(span * p) for p in [.25, .5, .75])
        for p in s['placements']:
            times.update([p['start'] - 1, p['start'], p['end'] - 1, p['end']])
    times = sorted(n for n in times if 0 <= n < v['frames'])
    frames = out / 'qa-frames'; frames.mkdir(exist_ok=True)
    thumb_w, thumb_h = 384, round(384 * v['height'] / v['width'])
    sheet = Image.new('RGB', (thumb_w * 4, (thumb_h + 22) * ((len(times) + 3) // 4)), '#e9e5de')
    draw = ImageDraw.Draw(sheet)
    for i, n in enumerate(times):
        dest = frames / f'{n:06d}.jpg'
        run(['ffmpeg', '-v', 'error', '-y', '-ss', str(n / v['fps']), '-i', str(final),
             '-frames:v', '1', '-q:v', '2', str(dest)], work / 'frame.log', c['_root'], timeout=60)
        with Image.open(dest) as im:
            x, y = i % 4 * thumb_w, i // 4 * (thumb_h + 22)
            sheet.paste(im.resize((thumb_w, thumb_h)), (x, y))
            draw.text((x + 6, y + thumb_h + 3), f'{n / v["fps"]:.3f}s / {n}', fill='black')
    sheet.save(out / 'Contact-sheet.jpg', quality=93)
    report = {'technical_status': 'PASS', 'editorial_review': 'pending', 'video': v,
              'full_decode': 'PASS', 'audio_bitstream_identical': True, 'audio_sha256': ah,
              'output_sha256': digest(final), 'review_frames': times,
              'scope': 'Metadata, full decode, exact audio hash, generated contact sheet. Not lip-sync/listening approval.'}
    write_json(out / 'QA.json', report)
    return report
