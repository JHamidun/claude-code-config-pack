"""Reviewed SRT to measured two-line ASS; optional separate captioned export."""
import argparse
import re
from pathlib import Path
from PIL import ImageFont
from common import writable, write_json, read_json, run, audio_hash, encoder, frame_args


def seconds(s):
    h, m, sec = s.replace(',', '.').split(':')
    return int(h)*3600 + int(m)*60 + float(sec)


def cues(path):
    result, last = [], 0
    for block in re.split(r'\n\s*\n', Path(path).read_text(encoding='utf-8-sig').strip()):
        lines = block.splitlines()
        if len(lines) < 3 or ' --> ' not in lines[1]:
            raise ValueError('Invalid SRT cue')
        a, b = lines[1].split(' --> ')
        start, end = seconds(a), seconds(b)
        if not 0 <= start < end or start < last:
            raise ValueError('Invalid or overlapping caption timings')
        # Keep the reviewed line breaks; wrap() splits on any whitespace, so the default
        # (re-wrap by measured width) is unchanged, while --keep-breaks can honour them.
        result.append((start, end, '\n'.join(line.strip() for line in lines[2:])))
        last = end
    return result


def wrap(text, font, width):
    rows, row = [], ''
    for word in text.split():
        if font.getlength(word) > width:
            raise ValueError('A caption word exceeds the safe width')
        candidate = (row + ' ' + word).strip()
        if row and font.getlength(candidate) > width:
            rows.append(row); row = word
        else:
            row = candidate
    if row:
        rows.append(row)
    if len(rows) > 2:
        raise ValueError('Cue exceeds two lines; split with reviewed audio timings')
    return rows


def color(hexcode):
    h = hexcode.lstrip('#')
    if not re.fullmatch('[0-9A-Fa-f]{6}', h):
        raise ValueError('Use #RRGGBB caption color')
    return h[4:6] + h[2:4] + h[0:2]


def stamp(t):
    cs = round(t*100)
    return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'


def caption_parts(start, end, regions):
    points = sorted({start, end} | {t for r in regions for t in [r['start'], r['end']] if start < t < end})
    for a, b in zip(points, points[1:]):
        yield a, b, next((r for r in regions if r['start'] <= (a+b)/2 < r['end']), {})


def term_pattern(terms):
    """Literal terms; a trailing * stands for any word ending ("задач*" matches задачу, задачей)."""
    parts = [re.escape(t).replace(r'\*', r'\w*') for t in sorted(terms, key=len, reverse=True)]
    return re.compile(r'(?<!\w)(' + '|'.join(parts) + r')(?!\w)', re.I) if parts else None


def ass_scale(font_path):
    """libass sizes a font by ascent+descent, PIL by em: widths from PIL need this factor.

    Without it a pill placed under a word drifts by a few pixels per character.
    """
    try:
        from fontTools.ttLib import TTFont
        with TTFont(str(font_path)) as f:
            return f['head'].unitsPerEm / (f['hhea'].ascent - f['hhea'].descent)
    except Exception:
        return 1.0


def pill(width, height, radius=7):
    w, h, r = round(width), round(height), radius
    return (f'm {r} 0 l {w-r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h-r} b {w} {h} {w} {h} {w-r} {h} '
            f'l {r} {h} b 0 {h} 0 {h} 0 {h-r} l 0 {r} b 0 0 0 0 {r} 0')


def rows_for(text, font, width, keep_breaks):
    """Reviewed SRT line breaks when asked and they fit; otherwise measured re-wrap."""
    if keep_breaks:
        rows = [r for r in text.split('\n') if r.strip()]
        if 1 <= len(rows) <= 2 and all(font.getlength(r) <= width for r in rows):
            return rows
    return wrap(text, font, width)


def generate(source, font_path, output, width, height, size, safe_width, x, y, ink, accent, terms, regions=None,
             highlight='color', pill_color='#FFD43B', keep_breaks=False):
    font = ImageFont.truetype(str(font_path), size)
    family = font.getname()[0]
    fg, mark = color(ink), color(accent)
    if highlight not in ('color', 'pill'):
        raise ValueError('highlight must be color or pill')
    pattern, scale, pill_fill = term_pattern(terms), ass_scale(font_path), color(pill_color)
    head = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{family},{size},&H00{fg},&H00{mark},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events, checks = [], []
    regions = sorted(regions or [], key=lambda r: r['start'])
    last = 0
    for r in regions:
        if not 0 <= last <= r['start'] < r['end']:
            raise ValueError('Invalid or overlapping caption regions')
        last = r['end']
    for start, end, text in cues(source):
        for a, b, region in caption_parts(start, end, regions):
            point_x, point_y = region.get('x', x), region.get('y', y)
            point_size = region.get('size', size)
            measured = ImageFont.truetype(str(font_path), point_size)
            rows = rows_for(text, measured, region.get('safe_width', safe_width), keep_breaks)
            if not rows:
                raise ValueError('Empty caption')
            if point_y < 0 or point_y + len(rows) * point_size * 1.5 > height:
                raise ValueError('Caption vertical bounds exceed frame')
            extent = max(measured.getlength(r) for r in rows)
            if point_x - extent / 2 < 0 or point_x + extent / 2 > width:
                raise ValueError('Caption horizontal bounds exceed frame')
            safe = [r.replace('\\', '＼').replace('{', '(').replace('}', ')') for r in rows]
            local_fg, local_mark = color(region.get('ink', ink)), color(region.get('accent', accent))
            if highlight == 'pill':
                # The lesson style: every row its own event, and a rounded marker plate under the
                # first term of the cue (one per cue, not every match), text stays in ink colour.
                gap = round(point_size * 1.3)
                top = point_y if len(safe) == 2 else point_y + round(gap / 2 - 3)
                marked = False
                for i, row in enumerate(safe):
                    row_y = top + i * gap
                    hit = pattern.search(row) if pattern and not marked else None
                    if hit:
                        left = point_x - measured.getlength(row) * scale / 2
                        px = left + measured.getlength(row[:hit.start()]) * scale - 5
                        pw = measured.getlength(hit.group()) * scale + 10
                        plate = pill(pw, round(point_size * 1.2))
                        events.append(f'Dialogue: 0,{stamp(a)},{stamp(b)},Default,,0,0,0,,'
                                      f'{{\\an7\\pos({px:.1f},{row_y + 1})\\p1\\1c&H{pill_fill}&\\bord0\\shad0\\fad(110,80)}}{plate}')
                        marked = True
                    events.append(f'Dialogue: 1,{stamp(a)},{stamp(b)},Default,,0,0,0,,'
                                  f'{{\\an8\\pos({point_x},{row_y})\\fs{point_size}\\1c&H{local_fg}&\\fad(110,80)}}{row}')
                checks.append({'start': a, 'end': b, 'lines': len(rows), 'width': extent, 'x': point_x, 'y': top,
                               'highlighted': marked})
                continue
            rendered = r'\N'.join(safe)
            if pattern:
                rendered = pattern.sub(
                    lambda m: '{\\1c&H' + local_mark + '&}' + m.group() + '{\\1c&H' + local_fg + '&}', rendered)
            events.append(f'Dialogue: 0,{stamp(a)},{stamp(b)},Default,,0,0,0,,{{\\an8\\pos({point_x},{point_y})\\fs{point_size}\\1c&H{local_fg}&\\fad(100,80)}}{rendered}')
            checks.append({'start': a, 'end': b, 'lines': len(rows), 'width': extent, 'x': point_x, 'y': point_y})
    Path(output).write_text(head + '\n'.join(events), encoding='utf-8-sig')
    write_json(Path(output).with_suffix('.layout.json'), checks)


def main():
    p = argparse.ArgumentParser(); p.add_argument('srt'); p.add_argument('--font', required=True); p.add_argument('--output', required=True)
    p.add_argument('--width', type=int, default=1920); p.add_argument('--height', type=int, default=1080)
    p.add_argument('--size', type=int, default=38); p.add_argument('--safe-width', type=int, default=1400)
    p.add_argument('--x', type=int, default=960); p.add_argument('--y', type=int, default=920)
    p.add_argument('--ink', default='#303236'); p.add_argument('--accent', default='#B38A00'); p.add_argument('--terms', nargs='*', default=[])
    p.add_argument('--video'); p.add_argument('--render'); p.add_argument('--start', action='store_true')
    p.add_argument('--regions', help='JSON array of explicit time-specific caption placement overrides')
    p.add_argument('--encoder', default='libx264')
    p.add_argument('--highlight', choices=['color', 'pill'], default='color',
                   help='color: recolour the term; pill: marker plate under the first term of each cue (lesson style)')
    p.add_argument('--pill-color', default='#FFD43B')
    p.add_argument('--keep-breaks', action='store_true',
                   help='use the reviewed SRT line breaks when each row fits the safe width (max two rows)')
    a = p.parse_args(); out = writable(a.output)
    if out in [Path(a.srt).resolve(), Path(a.font).resolve()]:
        raise ValueError('ASS must not overwrite a source')
    out.parent.mkdir(parents=True, exist_ok=True)
    generate(a.srt, a.font, out, a.width, a.height, a.size, a.safe_width, a.x, a.y, a.ink, a.accent, a.terms,
             read_json(a.regions) if a.regions else None, a.highlight, a.pill_color, a.keep_breaks)
    if a.render:
        if not a.video:
            raise ValueError('--video is required with --render')
        target, source = writable(a.render), Path(a.video).resolve()
        if target == source:
            raise ValueError('Do not overwrite uncaptioned master')
        if not a.start:
            print('ASS ready; pass --start to burn into a new video'); return
        # Use fixed working filenames to keep filter-path escaping independent of user paths.
        import shutil
        render_dir = out.parent / 'caption-render'; render_dir.mkdir(exist_ok=True)
        shutil.copy2(out, render_dir / 'captions.ass')
        (render_dir / 'fonts').mkdir(exist_ok=True)
        shutil.copy2(a.font, render_dir / 'fonts' / Path(a.font).name)
        target.parent.mkdir(parents=True, exist_ok=True)
        run(['ffmpeg', '-hide_banner', '-y', '-i', str(source), '-vf', 'ass=captions.ass:fontsdir=fonts',
             *encoder(a.encoder), *frame_args(), '-c:a', 'copy', str(target)], render_dir / 'render.log', out.parent, cwd=render_dir)
        if audio_hash(source) != audio_hash(target):
            raise RuntimeError('Caption render changed audio')
    print(out)


if __name__ == '__main__':
    main()
