"""Frame-exact panel replacement, optional arbitrary logos, copied master audio."""
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from common import resolve, encoder, frame_args, run, video_stream, write_json, digest

# Fitted to a reference lesson render: under a panel the stage goes 196 -> 229 over ~50 px,
# 214 beside it. Mean profile error 0.7 levels.
SHADOW = {'blur': 20, 'dy': 6, 'opacity': .25}


def rounded(path, w, h, radius):
    im = Image.new('L', (w * 3, h * 3))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * 3 - 1, h * 3 - 1), radius=radius * 3, fill=255)
    im.resize((w, h), Image.Resampling.LANCZOS).save(path)


def shadow(path, w, h, radius, blur=SHADOW['blur'], dy=SHADOW['dy'], opacity=SHADOW['opacity']):
    """Soft external shadow PNG for a rounded panel; returns the margin to offset it by."""
    m = blur * 3 + dy
    alpha = Image.new('L', (w + 2 * m, h + 2 * m), 0)
    ImageDraw.Draw(alpha).rounded_rectangle((m, m + dy, m + w - 1, m + dy + h - 1), radius=radius, fill=round(255 * opacity))
    im = Image.new('RGBA', alpha.size, (0, 0, 0, 0))
    im.putalpha(alpha.filter(ImageFilter.GaussianBlur(blur)))
    im.save(path)
    return m


def wants_shadow(item):
    """A rounded floating panel casts a shadow unless told otherwise; square full-bleed ones do not."""
    return item.get('shadow', int(item.get('radius', 22)) > 0)


def color_filter(meta):
    space = meta.get('color_space')
    if space in ['bt470bg', 'smpte170m']:
        matrix = 'bt601'
    elif space == 'bt709':
        matrix = 'bt709'
    else:
        raise ValueError(f'Unknown panel color matrix: {space}; inspect before encoding')
    r = meta.get('color_range')
    if r not in ['pc', 'tv']:
        raise ValueError('Unknown panel color range; inspect before encoding')
    return f'scale=in_range={"full" if r == "pc" else "limited"}:out_range=limited:in_color_matrix={matrix}:out_color_matrix=bt709,format=yuv420p'


def compose(c, target):
    v, work = c['video'], c['_work']
    fps = v['fps']
    inputs = ['-threads', '2', '-i', str(c['_base'])]
    graph = ['[0:v]setpts=PTS-STARTPTS,setsar=1[base]']
    count, previous, layers = 1, 'base', 0
    for s in c['scenes']:
        path = work / 'clips' / f'{s["id"]}.mp4'
        inputs += ['-threads', '2', '-i', str(path)]
        si = count; count += 1
        ps = s['placements']
        graph.append(f'[{si}:v]setpts=PTS-STARTPTS,split={len(ps)}' + ''.join(f'[src{layers+i}]' for i in range(len(ps))))
        conversion = color_filter(video_stream(path))
        for p in ps:
            n = layers; layers += 1
            x, y, w, h = map(int, p['rect'])
            mask = work / f'mask-{n}.png'
            rounded(mask, w, h, int(p.get('radius', 22)))
            inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(mask)]
            mi = count; count += 1
            enable = f"enable='gte(n,{p['start']})*lt(n,{p['end']})'"
            if wants_shadow(p):
                shade = work / f'shadow-{n}.png'
                m = shadow(shade, w, h, int(p.get('radius', 22)))
                inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(shade)]
                graph.append(f"[{count}:v]format=rgba[sh{n}];[{previous}][sh{n}]overlay={x - m}:{y - m}:{enable}:format=yuv420[shaded{n}]")
                count += 1; previous = f'shaded{n}'
            graph += [f'[src{n}]scale={w}:{h}:flags=lanczos,{conversion}[rgb{n}]',
                      f'[{mi}:v]format=gray[m{n}]',
                      f'[rgb{n}][m{n}]alphamerge,setpts=PTS-STARTPTS+{s["start"]}/{fps}/TB[layer{n}]',
                      f"[{previous}][layer{n}]overlay={x}:{y}:{enable}:format=yuv420[out{n}]"]
            previous = f'out{n}'
    for i, logo in enumerate(c.get('branding', {}).get('logos', [])):
        path = resolve(c['_root'], logo['path'])
        inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(path)]
        x, y, w, h = map(int, logo['rect'])
        graph.append(f'[{count}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,format=rgba,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x00000000[logo{i}]')
        enable = '+'.join(f'gte(n,{a})*lt(n,{b})' for a, b in logo.get('intervals', [[0, v['frames']]]))
        graph.append(f"[{previous}][logo{i}]overlay={x}:{y}:enable='{enable}':format=yuv420[br{i}]")
        count += 1; previous = f'br{i}'
    graph.append(f'[{previous}]format=yuv420p,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709,setsar=1[final]')
    graph_path = work / 'compose.ffgraph'
    graph_path.write_text(';'.join(graph), encoding='utf-8')
    run(['ffmpeg', '-hide_banner', '-y', '-filter_complex_threads', '2', *inputs,
         '-filter_complex_script', str(graph_path), '-map', '[final]', '-map', '0:a:0',
         '-c:a', 'copy', '-frames:v', str(v['frames']), *encoder(c.get('encoder', 'libx264')),
         *frame_args(), str(target)], work / 'compose.log', c['_root'], timeout=c.get('timeout_seconds', 1800))


def export_sidecars(c, final):
    if c.get('subtitle_file'):
        shutil.copy2(resolve(c['_root'], c['subtitle_file']), c['_output'] / 'subtitles.srt')
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(final), '-frames:v', '1', '-q:v', '2',
        str(c['_output'] / 'Preview.jpg')], c['_work'] / 'preview.log', c['_root'], timeout=60)
    paths = [c['_base'], c['_config']] + [resolve(c['_root'], x['path']) for x in c['sources'].values()]
    paths += [resolve(c['_root'], x) for x in c['fonts'].values()]
    paths += [resolve(c['_root'], x['path']) for x in c.get('branding', {}).get('logos', [])]
    write_json(c['_output'] / 'manifest.json', {'project': c['id'], 'video': c['video'],
        'sources': {str(p): digest(p) for p in paths}, 'output': str(final), 'output_sha256': digest(final),
        'audio': 'Bitstream copy from approved base', 'logos': len(c.get('branding', {}).get('logos', [])),
        'scene_ids': [s['id'] for s in c['scenes']]})
