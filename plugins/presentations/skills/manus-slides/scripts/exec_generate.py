"""Bridge manifest -> image model -> bind for exec_sketch.py. Makes PAID provider calls.

The engine itself stays offline; this script is the only place that talks to a provider.
Keys come from the environment (OPENAI_API_KEY for gpt-image-*, GOOGLE_API_KEY for gemini-*),
optionally loaded from ~/.claude/.credentials.master.env; they never enter prompts, sidecars or logs.

    python exec_generate.py <job>/deck.json [--prompts <job>/prompts] [--ids a,b] [--model M] [--parallel 4]

The prompt is always the manifest's current one (exec_sketch.make_prompt). --prompts, when given,
must match it: a stale plan folder is refused instead of paying for the wrong slide.
Default selection: every slide that is unbound or whose binding went stale.
Existing art/<id>.png is reused only if art/<id>.json says it was drawn from exactly this prompt
and the file is unchanged; art drawn for an older prompt is moved to art/superseded/ and redrawn.
Default model gpt-image-2.5-sunburst (~$0.04 per 1920x1088 slide); cheaper:
gemini-3.1-flash-image-preview. Bindings record the model that actually drew the image.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

import exec_sketch as engine

OPENAI = ('gpt-image-',)
GEMINI = ('gemini-', 'nano-banana')


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize(image: Image.Image) -> Image.Image:
    """1920x1088 (the provider's 16-multiple) -> exact 1920x1080 by trimming 4 px top and bottom.

    Anything else is kept as is: the engine letterboxes non-16:9 art instead of stretching it.
    """
    image = image.convert('RGB')
    if image.size == (1920, 1088):
        return image.crop((0, 4, 1920, 1084))
    return image


def keys():
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.expanduser('~/.claude/.credentials.master.env'))
    except ImportError:                             # python-dotenv is optional: plain env vars work too
        pass
    os.environ.pop('GEMINI_API_KEY', None)          # conflicts with GOOGLE_API_KEY in google-genai


def key(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f'{name} is not set: export it or add {name}=... to ~/.claude/.credentials.master.env')
    return value


def call(model: str, prompt: str) -> tuple[Image.Image, dict]:
    if model.startswith(OPENAI):
        from openai import OpenAI
        r = OpenAI(api_key=key('OPENAI_API_KEY')).images.generate(
            model=model, prompt=prompt, size='1920x1088', quality='high')
        usage = r.usage.model_dump() if getattr(r, 'usage', None) else None
        return Image.open(io.BytesIO(base64.b64decode(r.data[0].b64_json))), {'usage': usage}
    if model.startswith(GEMINI):
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key('GOOGLE_API_KEY'))
        r = client.models.generate_content(model=model, contents=prompt, config=types.GenerateContentConfig(
            response_modalities=['IMAGE', 'TEXT'], image_config=types.ImageConfig(aspect_ratio='16:9')))
        for part in r.candidates[0].content.parts:
            if part.inline_data and (part.inline_data.mime_type or '').startswith('image/'):
                return Image.open(io.BytesIO(part.inline_data.data)), {}
        raise RuntimeError('Model returned no image')
    raise ValueError('Unknown model family: ' + model)


def sidecar(out: Path) -> dict | None:
    path = out.with_suffix('.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


def reusable(prompt: str, out: Path) -> dict | None:
    """The sidecar of art that may be reused for this prompt, or None when there is no art.

    Raises ValueError when art exists but its provenance does not prove it matches: no sidecar,
    another prompt, or the PNG changed after generation (a hand-placed file is not a model answer).
    """
    if not out.exists():
        return None
    meta = sidecar(out)
    if not meta:
        raise ValueError(f'{out.name} has no provenance (no {out.stem}.json): bind it with exec_sketch.py bind')
    if meta.get('prompt_sha256') != sha_text(prompt):
        raise ValueError(f'{out.name} was drawn for another prompt')
    if meta.get('image_sha256') != hashlib.sha256(out.read_bytes()).hexdigest():
        raise ValueError(f'{out.name} changed after generation')
    return meta


def supersede(out: Path) -> Path:
    """Move art drawn for an older prompt out of the way instead of deleting it."""
    meta = sidecar(out) or {}
    target = out.parent / 'superseded' / f'{out.stem}-{str(meta.get("prompt_sha256", "unknown"))[:8]}.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(out), target)
    if out.with_suffix('.json').is_file():
        shutil.move(str(out.with_suffix('.json')), target.with_suffix('.json'))
    return target


def generate(model: str, prompt: str, out: Path) -> dict:
    raw, extra = call(model, prompt)
    returned = list(raw.size)
    image = normalize(raw)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, 'PNG')                          # a real PNG whatever the provider sent (JPEG happens)
    meta = {'model': model, 'returned': returned, 'saved': list(image.size), 'prompt_sha256': sha_text(prompt),
            'image_sha256': hashlib.sha256(out.read_bytes()).hexdigest(), **extra}
    out.with_suffix('.json').write_text(json.dumps(meta, indent=1), encoding='utf-8')
    return meta


def select(deck: dict, ids_arg: str | None) -> list[str]:
    slides = {s['id']: s for s in deck['slides']}
    if ids_arg is None:
        return [sid for sid, s in slides.items()
                if not s.get('binding') or s['binding'].get('art_signature') != engine.signature(deck, s)]
    ids = list(dict.fromkeys(x.strip() for x in ids_arg.split(',') if x.strip()))
    if not ids:
        raise SystemExit('--ids is empty; omit it to take every unbound or stale slide')
    unknown = [i for i in ids if i not in slides]
    if unknown:
        raise SystemExit('Unknown slide IDs: ' + ', '.join(unknown))
    return ids


def main(argv=None) -> int:
    engine.utf8_stdio()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('manifest', type=Path)
    p.add_argument('--prompts', type=Path, help='plan output to cross-check; refused if it no longer matches')
    p.add_argument('--ids', help='comma-separated slide IDs; default: every unbound or stale slide')
    p.add_argument('--model', default='gpt-image-2.5-sunburst')
    p.add_argument('--art', type=Path, help='where raw art goes; default <job>/art')
    p.add_argument('--parallel', type=int, default=4)
    p.add_argument('--no-bind', action='store_true')
    a = p.parse_args(argv)
    manifest = a.manifest.resolve()
    deck = engine.load(manifest)
    art = engine.writable((a.art or manifest.parent / 'art').resolve())
    ids = select(deck, a.ids)
    if not ids:
        print(json.dumps({'status': 'nothing to do: every slide is bound and fresh'}))
        return 0
    slides = {s['id']: s for s in deck['slides']}
    prompts = {i: engine.make_prompt(deck, slides[i]).strip() for i in ids}
    if a.prompts:
        stale = [i for i in ids if not (a.prompts / f'{i}.txt').is_file()
                 or (a.prompts / f'{i}.txt').read_text(encoding='utf-8').strip() != prompts[i]]
        if stale:
            raise SystemExit('Plan folder is stale or incomplete for: ' + ', '.join(stale) + '; re-run exec_sketch.py plan')
    # Pre-flight every reuse decision before the first paid call.
    plan, reuse = {}, {}
    for i in ids:
        out = art / f'{i}.png'
        try:
            meta = reusable(prompts[i], out)
        except ValueError as error:
            if 'another prompt' not in str(error):
                raise SystemExit(f'{error}; or move it away to regenerate')
            print(json.dumps({'id': i, 'status': 'superseded', 'moved_to': str(supersede(out))}, ensure_ascii=False))
            meta = None
        if meta:
            reuse[i] = meta
        else:
            plan[i] = out
    if plan:
        keys()
        with ThreadPoolExecutor(max(1, a.parallel)) as pool:
            done = dict(zip(plan, pool.map(lambda i: generate(a.model, prompts[i], plan[i]), plan)))
    else:
        done = {}
    for i in ids:
        meta = reuse.get(i) or done[i]
        print(json.dumps({'id': i, 'status': 'reused' if i in reuse else 'generated', 'model': meta.get('model'),
                          'returned': meta.get('returned')}, ensure_ascii=False))
    if not a.no_bind:
        for i in ids:                                # sequential: bind rewrites the manifest
            meta = reuse.get(i) or done[i]
            print(json.dumps(engine.bind(manifest, i, art / f'{i}.png', meta.get('model') or a.model), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
