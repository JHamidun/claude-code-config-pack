"""Execute a reviewed edit map: separate camera/screen/mic into a new base."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageColor
from common import read_json, write_json, resolve, writable, run, encoder, frame_args, probe, digest, stop_check
from contract import require, box
from compose import rounded, shadow, wants_shadow
from qa import check_clip


def gradient(path, width, height, center, edge):
    yy, xx = np.mgrid[0:height, 0:width]
    d = np.clip(np.sqrt(((xx / width - .53) / .8) ** 2 + ((yy / height - .33) / 1.2) ** 2), 0, 1)
    a, b = np.array(ImageColor.getrgb(center)), np.array(ImageColor.getrgb(edge))
    Image.fromarray(np.uint8(a * (1 - d[..., None]) + b * d[..., None])).save(path)


def availability(path, start, duration, kind='video', track=0):
    data = probe(path)
    streams = [s for s in data['streams'] if s['codec_type'] == kind]
    require(len(streams) > track, f'Missing {kind} track {track}: {path}')
    length = float(streams[track].get('duration', data['format'].get('duration', 0)))
    require(start >= 0 and start + duration <= length + .05, f'Edit exceeds {kind} source: {path}')


def make_segment(root, work, spec, video, enc):
    fps, frames = video['fps'], spec['frames']
    duration = frames / fps
    width, height = video['width'], video['height']
    folder = work / spec['id']; folder.mkdir(exist_ok=True)
    audio = resolve(root, spec['audio']['path'])
    availability(audio, spec['audio']['in'], duration, 'audio', spec['audio'].get('track', 0))
    all_inputs = [audio] + [resolve(root, layer['path']) for layer in spec['layers']]
    for p in all_inputs:
        require(p.is_file(), f'Missing input: {p}')
    key = hashlib.sha256(json.dumps({'segment': spec, 'video': video, 'encoder': enc,
        'script': digest(Path(__file__)), 'compose': digest(Path(__file__).with_name('compose.py')), 'inputs': {str(p): digest(p) for p in all_inputs}}, sort_keys=True).encode()).hexdigest()
    stamp, clip, sound = folder / 'cache.json', folder / 'video.mp4', folder / 'audio.wav'
    if stamp.is_file() and clip.is_file() and sound.is_file():
        old = read_json(stamp)
        if old.get('key') == key and old.get('video') == digest(clip) and old.get('audio') == digest(sound):
            check_clip(clip, width, height, fps, frames)
            return clip, sound
    stage = folder / 'stage.png'
    bg = spec.get('background', '#E9E5DE')
    if isinstance(bg, str):
        Image.new('RGB', (width, height), bg).save(stage)
    else:
        gradient(stage, width, height, bg['center'], bg['edge'])
    inputs = ['-loop', '1', '-framerate', str(fps), '-i', str(stage)]
    graph, previous, count = ['[0:v]format=rgba[stage]'], 'stage', 1
    for i, layer in enumerate(spec['layers']):
        require(box(layer['rect'], width, height), 'Layer outside frame')
        x, y, w, h = map(int, layer['rect'])
        path = resolve(root, layer['path'])
        if layer['kind'] == 'image':
            inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(path)]
        else:
            require(layer['kind'] == 'video', 'Layer kind must be video or image')
            availability(path, layer.get('in', 0), duration)
            inputs += ['-threads', '2', '-ss', str(layer.get('in', 0)), '-i', str(path)]
        source = count; count += 1
        filters = f'[{source}:v]setpts=PTS-STARTPTS,fps={fps}'
        if layer.get('crop'):
            # Validated like rect: these values go straight into the filter graph, where a
            # string such as "1;movie=..." would add a filter instead of cropping.
            require(len(layer['crop']) == 4 and all(type(n) is int and n >= 0 for n in layer['crop'])
                    and layer['crop'][2] > 0 and layer['crop'][3] > 0, 'Layer crop must be four non-negative integers')
            cx, cy, cw, ch = layer['crop']
            filters += f',crop={cw}:{ch}:{cx}:{cy}'
        filters += ',format=rgba'
        if layer.get('key'):
            k = layer['key']
            require(0 <= k['similarity'] <= 1 and 0 <= k['blend'] <= 1, 'Bad key parameters')
            require(k['color'].startswith('0x') and len(k['color']) == 8 and all(x in '0123456789abcdefABCDEF' for x in k['color'][2:]), 'Bad key color')
            filters += f',colorkey={k["color"]}:{k["similarity"]}:{k["blend"]},despill=green'
        if layer.get('fit', 'contain') == 'cover':
            cy = 'ih-oh' if layer.get('anchor', 'bottom') == 'bottom' else '(ih-oh)/2'
            filters += f',scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}:(iw-ow)/2:{cy}'
        else:
            require(layer.get('fit', 'contain') == 'contain', 'Unknown fit mode')
            filters += f',scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x00000000'
        graph.append(filters + f'[fg{i}]')
        panel = folder / f'panel-{i}.png'
        colors = layer.get('panel', {'center': bg if isinstance(bg, str) else bg['center'], 'edge': bg if isinstance(bg, str) else bg['edge']})
        gradient(panel, w, h, colors['center'], colors['edge'])
        inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(panel)]
        pi = count; count += 1
        mask = folder / f'mask-{i}.png'; rounded(mask, w, h, layer.get('radius', 22))
        inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(mask)]
        mi = count; count += 1
        require(type(layer.get('shadow', False)) is bool, 'Layer shadow must be true or false')
        if wants_shadow(layer):
            shade = folder / f'shadow-{i}.png'
            m = shadow(shade, w, h, int(layer.get('radius', 22)))
            inputs += ['-loop', '1', '-framerate', str(fps), '-i', str(shade)]
            graph.append(f'[{count}:v]format=rgba[sh{i}];[{previous}][sh{i}]overlay={x - m}:{y - m}:format=auto[shaded{i}]')
            count += 1; previous = f'shaded{i}'
        graph += [f'[{pi}:v][fg{i}]overlay=0:0:format=auto[panel{i}]',
                  f'[{mi}:v]format=gray[mask{i}]', f'[panel{i}][mask{i}]alphamerge[rounded{i}]',
                  f'[{previous}][rounded{i}]overlay={x}:{y}:format=auto[layer{i}]']
        previous = f'layer{i}'
    graph.append(f'[{previous}]scale=out_range=limited:out_color_matrix=bt709,format=yuv420p,setsar=1[final]')
    g = folder / 'filter.ffgraph'; g.write_text(';'.join(graph), encoding='utf-8')
    run(['ffmpeg', '-hide_banner', '-y', '-filter_complex_threads', '2', *inputs,
         '-filter_complex_script', str(g), '-map', '[final]', '-an', '-frames:v', str(frames),
         *encoder(enc), *frame_args(), str(clip)], folder / 'video.log', root)
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(spec['audio']['in']), '-i', str(audio),
         '-map', f'0:a:{spec["audio"].get("track", 0)}', '-af', f'asetpts=PTS-STARTPTS,aresample=48000,apad,atrim=duration={duration}',
         '-ac', '2', '-c:a', 'pcm_s16le', str(sound)], folder / 'audio.log', root)
    check_clip(clip, width, height, fps, frames)
    write_json(stamp, {'key': key, 'video': digest(clip), 'audio': digest(sound)})
    return clip, sound


def execute(config, start=False):
    file = Path(config).resolve(); root = file.parent; c = read_json(file)
    require(c['schema_version'] == 1, 'Unsupported raw edit schema')
    v = c['video']; segments = c['segments']
    require(all(type(v[k]) is int and v[k] > 0 for k in ['width', 'height', 'fps', 'frames']), 'Invalid video clock')
    require(v['width'] % 2 == 0 and v['height'] % 2 == 0, 'Video dimensions must be even')
    require(bool(segments), 'Edit has no segments')
    require(sum(s['frames'] for s in segments) == v['frames'], 'Segment frames do not sum to output')
    require(len({s['id'] for s in segments}) == len(segments), 'Duplicate segment ID')
    import re
    require(all(re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', s['id']) for s in segments), 'Unsafe segment ID')
    require(all(type(s['frames']) is int and s['frames'] > 0 for s in segments), 'Invalid segment frames')
    output = writable(resolve(root, c['output'])); work = writable(resolve(root, c.get('work', 'raw-work')))
    require(output.suffix.lower() == '.mp4', 'Base output must have an .mp4 extension')
    sources = {resolve(root, s['audio']['path']) for s in segments}
    sources.update(resolve(root, layer['path']) for s in segments for layer in s['layers'])
    require(output not in sources, 'Cannot overwrite source with master')
    print(f'Raw edit: {len(segments)} segments, {v["frames"]/v["fps"]:.3f}s -> {output}', flush=True)
    if not start:
        return
    work.mkdir(parents=True, exist_ok=True); output.parent.mkdir(parents=True, exist_ok=True)
    pairs = []
    for s in segments:
        stop_check(root)
        pairs.append(make_segment(root, work, s, v, c.get('encoder', 'libx264')))
        write_json(work / 'checkpoint.json', {'last_segment': s['id']})
    for i, name in enumerate(['video', 'audio']):
        lines = ["file '" + str(p[i].as_posix()).replace("'", "'\\''") + "'" for p in pairs]
        (work / f'{name}.ffconcat').write_text('\n'.join(lines), encoding='utf-8')
    candidate = output.with_name(output.stem + '.partial.mp4')
    run(['ffmpeg', '-hide_banner', '-y', '-f', 'concat', '-safe', '0', '-i', str(work / 'video.ffconcat'),
         '-f', 'concat', '-safe', '0', '-i', str(work / 'audio.ffconcat'), '-map', '0:v:0', '-map', '1:a:0',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', str(v['frames']/v['fps']),
         '-movflags', '+faststart', str(candidate)], work / 'master.log', root)
    check_clip(candidate, v['width'], v['height'], v['fps'], v['frames'])
    os.replace(candidate, output)
    cursor, mapping = 0, []
    for s in segments:
        mapping.append({'id': s['id'], 'final_start': cursor, 'final_end': cursor+s['frames'], 'source_audio': s['audio'], 'source_layers': s['layers']})
        cursor += s['frames']
    write_json(work / 'edit-map.json', {'video': v, 'segments': mapping, 'output': str(output),
        'sha256': digest(output), 'perceptual_sync_review': 'pending'})
    print(output, flush=True)


def main():
    p = argparse.ArgumentParser(); p.add_argument('config'); p.add_argument('--start', action='store_true')
    a = p.parse_args(); execute(a.config, a.start)


if __name__ == '__main__':
    main()
