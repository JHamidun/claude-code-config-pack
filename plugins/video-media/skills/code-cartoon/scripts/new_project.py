"""Scaffold a new code-cartoon project from the skill templates.

    python ~/.claude/skills/code-cartoon/scripts/new_project.py <dest dir | slug> [--ref ~/VideoJobs/cartoon-cc] [--no-ref]

A bare slug (no path, e.g. "bulb-promo") becomes ~/VideoJobs/<YYYY-MM-DD>-<slug>. The destination must be empty or absent.
Copies templates/ (engine, pencil, gloss when present, render, sound, timing, voice). A file named <name>_template.<ext>
is copied as <name>.<ext> — hero_template.js -> engine/hero.js, scenes_template.js -> pencil/scenes.js,
scenes3d_template.js -> gloss/scenes3d.js — and references to the template names inside .html files are rewritten.
Heavy assets are not stored in the skill: fonts/ and vendor/three/ are copied from the reference project (--ref), or, when
it is missing (--no-ref forces this), fetched: three@0.181.2 from cdn.jsdelivr.net (byte-identical to the reference r181),
JetBrains Mono from jsdelivr (GitHub v2.304), Manrope from Google Fonts, Segoe Print from C:/Windows/Fonts (on macOS and
Linux — Caveat from Google Fonts under the Segoe file names; CODE_CARTOON_NO_SYSTEM_FONTS=1 forces that path).
"""
import argparse
import datetime as dt
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL / 'templates'
REF = Path.home() / 'VideoJobs' / 'cartoon-cc'
JOBS = Path.home() / 'VideoJobs'
THREE_VERSION = '0.181.2'
THREE_FILES = {'three.module.js': 'build/three.module.js', 'three.core.js': 'build/three.core.js',
               'addons/environments/RoomEnvironment.js': 'examples/jsm/environments/RoomEnvironment.js',
               'addons/geometries/RoundedBoxGeometry.js': 'examples/jsm/geometries/RoundedBoxGeometry.js'}
FONTS = ['segoepr.ttf', 'segoeprb.ttf', 'JetBrainsMono-Regular.ttf', 'JetBrainsMono-Bold.ttf', 'Manrope-ExtraBold.ttf', 'Manrope-Bold.ttf']
UA = {'User-Agent': 'Mozilla/4.0 (code-cartoon scaffold)'}   # an old UA makes Google Fonts answer with TTF files
NO_SYSTEM_FONTS = bool(os.environ.get('CODE_CARTOON_NO_SYSTEM_FONTS'))  # test the macOS/Linux path on Windows


def fetch(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def google_ttf(family, weight):
    css = fetch(f'https://fonts.googleapis.com/css?family={family}:{weight}&subset=cyrillic,latin').decode('utf-8')
    urls = re.findall(r'url\((https://[^)]+\.ttf)\)', css)
    if not urls:
        raise RuntimeError(f'Google Fonts returned no TTF url for {family} {weight}')
    return fetch(urls[0])


def font_fallback(name, dest):
    """One font file from the system or the network; returns a note or raises."""
    if name.startswith('segoepr'):
        src = Path('C:/Windows/Fonts') / name
        if src.exists() and not NO_SYSTEM_FONTS:
            shutil.copy2(src, dest)
            return f'{name}: copied from C:/Windows/Fonts'
        # Segoe Print exists only on Windows: elsewhere the hand font is Caveat (Google Fonts, OFL, has Cyrillic), saved
        # under the same file name so the pages need no change. Caveat is narrower: check caption widths on the sheet.
        data = google_ttf('Caveat', 700 if name == 'segoeprb.ttf' else 400)
        note = f'{name}: Segoe Print not found — Caveat from Google Fonts saved under this name'
    elif name.startswith('JetBrainsMono'):
        data = fetch(f'https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@v2.304/fonts/ttf/{name}')
        note = None
    else:
        data = google_ttf('Manrope', 800 if 'ExtraBold' in name else 700)
        note = None
    if data[:4] not in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
        raise RuntimeError(f'{name}: downloaded data is not a font')
    dest.write_bytes(data)
    return (note or f'{name}: downloaded') + f' ({len(data) // 1024} KB)'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dest')
    ap.add_argument('--ref', default=str(REF), help='reference project with fonts/ and vendor/three/')
    ap.add_argument('--no-ref', action='store_true', help='ignore the reference project: fetch fonts and three.js')
    a = ap.parse_args()

    dest = Path(a.dest)
    if re.fullmatch(r'[\w.-]+', a.dest):
        dest = JOBS / f'{dt.date.today():%Y-%m-%d}-{a.dest}'
    dest = dest.resolve()
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f'refusing: {dest} is not empty')
    if not TEMPLATES.is_dir():
        raise SystemExit(f'no templates at {TEMPLATES}')
    ref = None if a.no_ref else Path(a.ref)
    if ref is not None and not ref.is_dir():
        print(f'reference project {ref} not found: fonts and three.js will be fetched')
        ref = None

    # 1) templates (the _template marker is dropped from file names)
    renamed, copied = {}, []
    for src in sorted(TEMPLATES.rglob('*')):
        if src.is_dir() or '__pycache__' in src.parts or src.suffix == '.pyc':
            continue
        rel = src.relative_to(TEMPLATES)
        new_name = re.sub(r'_template(?=\.[^.]+$)', '', rel.name)
        if new_name != rel.name:
            renamed[rel.name] = new_name
        out = dest / rel.parent / new_name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        copied.append(out.relative_to(dest).as_posix())
    for html in dest.rglob('*.html'):
        txt = html.read_text(encoding='utf-8')
        new = txt
        for old, nn in renamed.items():
            new = new.replace(old, nn)
        if new != txt:
            html.write_text(new, encoding='utf-8')
    (dest / 'out').mkdir(exist_ok=True)

    # 2) fonts
    notes = []
    fdir = dest / 'fonts'
    fdir.mkdir(exist_ok=True)
    if ref is not None and (ref / 'fonts').is_dir():
        for f in sorted((ref / 'fonts').glob('*.tt[fc]')):
            shutil.copy2(f, fdir / f.name)
        notes.append(f'fonts: copied from {ref / "fonts"}')
    for name in FONTS:
        if not (fdir / name).exists():
            try:
                notes.append(font_fallback(name, fdir / name))
            except Exception as e:                       # the page will report 'font not loaded'; render.py refuses to render
                notes.append(f'MISSING {name}: {e}')

    # 3) three.js (only the files the gloss page imports)
    tdir = dest / 'vendor' / 'three'
    if ref is not None and all((ref / 'vendor' / 'three' / r).exists() for r in THREE_FILES):
        for r in THREE_FILES:
            (tdir / r).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ref / 'vendor' / 'three' / r, tdir / r)
        notes.append(f'three.js: copied from {ref / "vendor" / "three"}')
    else:
        for r, path in THREE_FILES.items():
            (tdir / r).parent.mkdir(parents=True, exist_ok=True)
            try:
                data = fetch(f'https://cdn.jsdelivr.net/npm/three@{THREE_VERSION}/{path}')
                if data.lstrip()[:2] not in (b'/*', b'im'):
                    raise RuntimeError('unexpected content')
                (tdir / r).write_bytes(data)
            except Exception as e:
                notes.append(f'MISSING vendor/three/{r}: {e}')
        notes.append(f'three.js: three@{THREE_VERSION} from cdn.jsdelivr.net')

    # 4) README with the next steps
    gloss = (dest / 'gloss' / 'index.html').exists()
    (dest / 'README.md').write_text(readme(dest, gloss), encoding='utf-8')

    print(f'project: {dest}')
    print(f'{len(copied)} template files' + (f'; renamed: ' + ', '.join(f'{o} -> {n}' for o, n in renamed.items()) if renamed else ''))
    for n in notes:
        print(' ', n)
    if any(n.startswith('MISSING') for n in notes):
        print('WARNING: some assets are missing (see above): the pages will report «font not loaded» / fail to load three.js')
    print('next: cd "%s" && python timing/fake_timing.py && python render/still.py pencil/index.html st/p 0.5,2.5,5 land' % dest)
    print('      (full list of steps: README.md)')


def readme(dest, gloss):
    g = ''
    if gloss:
        g = """
Глянцевое 3D: `gloss/index.html` (ES-модули three.js). render.py и still.py сами поднимают для него http-сервер внутри
процесса на свободном порту и включают GPU-флаги — отдельный `python -m http.server` не нужен:

    python render/still.py gloss/index.html st/g 0.5,2.5,5 land
    python render/render.py gloss/index.html out/gloss_land_v1.mp4 --audio sound/mix.wav --last-frame
"""
    return f"""# {dest.name} — мультик кодом

Проект развёрнут из навыка `code-cartoon` (`~/.claude/skills/code-cartoon/`): порядок работы, ДНК стиля, грабли — там.
Здесь — рабочая копия шаблона: две сцены-образца (`pencil/scenes.js`) и типовой герой (`engine/hero.js`).

```
voice/script.txt            текст озвучки (показ на экране; пары {{показ|произношение}}, цифры только в парах)
timing/timing_config.json   сцены (имя, первое слово), паузы после слов, слово поворота, lead/tail
timing/fake_timing.py       ЧЕРНОВОЙ тайминг без голоса (draft: true)
timing/build_timing.py      настоящий тайминг из voice/words.json + voice/voice.wav -> voice_final.wav
engine/                     core.js (время, случайность с зерном, камера), pencil.js (карандаш), hero.js (герой),
                            hero_egg.js (маскот автора: подключить вместо hero.js в index.html)
pencil/index.html           страница; ?fmt=land|port  ?scenes=<файл>  ?pal=notebook|chalk
pencil/scenes.js            сцены: SCENES = {{имя из timing_config: функция}}; CUES — лист звуков
pencil/test_doodles.js      лист героя и всех заготовок lib.js: ?scenes=test_doodles.js
render/                     still.py (кадры PNG, --det), sheet.py (контактный лист), render.py (MP4), critic.py (Gemini, платно)
sound/synth.py              звук кодом по листу CUES + музыка по тактам, -15 LUFS, пик -1,5 dBTP
fonts/, vendor/three/       шрифты и three.js (скопированы из эталона или скачаны)
```

## Шаги

1. Текст: `voice/script.txt`; сцены и паузы: `timing/timing_config.json`. Владелец утверждает текст ДО озвучки.
2. Черновой тайминг (без голоса, без затрат): `python timing/fake_timing.py`
3. Кадры и лист — смотреть глазами до показа человеку:

       python render/still.py pencil/index.html st/p 0.5,2.5,5,8,12 land --det
       python render/still.py pencil/index.html st/pp 0.5,2.5,5,8,12 port
       python render/sheet.py st/sheet.png 5 0.25 st/p_*.png

4. Голос (после «ок» на текст; навык `elevenlabs`): `python voice/voice.py voice --dry-run`, потом
   `python voice/voice.py voice --takes 3` (голос — `--voice-key ИМЯ_ПЕРЕМЕННОЙ`, по умолчанию `ELEVENLABS_VOICE_ID`),
   затем `python timing/build_timing.py` — сцены берут время из слов, ничего не переписывается.
5. Лист звуков без полного рендера: `python render/render.py pencil/index.html out/cues.mp4 --to 0.1 --workers 1`
6. Звук: `python sound/synth.py out/cues.cues.json timing/timing.json timing/voice_final.wav sound/mix.wav`
   (без голоса: `none` вместо voice_final.wav).
7. Рендер: `python render/render.py pencil/index.html out/pencil_land_v1.mp4 --audio sound/mix.wav --last-frame`
   и `--fmt port` для 9:16. В конце render.py печатает ffprobe: размер, fps, длину, звук.
8. Внешний критик (платный вызов Gemini, утверждения про звук проверять замером):
   `python render/critic.py out/pencil_land_v1.mp4 out/critic_v1.md`
9. Превью — только владельцу; наружу — только после явного «публикуй».
{g}"""


if __name__ == '__main__':
    sys.exit(main())
