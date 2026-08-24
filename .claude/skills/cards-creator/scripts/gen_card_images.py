#!/usr/bin/env python3
"""
Generate editorial illustrations for carousel cards via OpenAI gpt-image-2.

Model id that works (verified 2026-05-29): gpt-image-2-2026-04-21
Endpoint:  POST https://api.openai.com/v1/images/generations   (text-only)
           POST https://api.openai.com/v1/images/edits          (with a reference photo)
Key:       OPENAI_API_KEY from ~/.claude/.credentials.master.env
Returns:   data[0].b64_json  -> decode -> .png

The STYLE constant locks the brand palette so a whole series looks cohesive
(cream / deep-navy / electric-blue / cyan / terracotta), flat editorial vector,
NO text/logos. gpt-image-2 follows it well.

low-cost alternative (no OpenAI spend): local-gateway /studio/image with Gemini
"Nano Banana" (gemini-3.1-flash-image-preview) — see the local-gateway skill.

Usage:
    # edit IMAGES dict below, then:
    python gen_card_images.py                 # writes <name>.png into CWD
    python gen_card_images.py /out/dir        # writes into given dir
"""
import sys
import io
import os
import base64
from pathlib import Path
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ключ — лениво и с громким отказом. Раньше здесь на верхнем уровне модуля стояло
# open(...).read().split("OPENAI_API_KEY=")[1]: у того, кто не завёл ключ, простой
# импорт файла падал с `IndexError: list index out of range` — по такому тексту
# причину не найти.
_KEY = None


def get_key():
    """OPENAI_API_KEY: окружение → ~/.claude/.credentials.master.env → внятный отказ."""
    global _KEY
    if _KEY is None:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            cred = Path(os.environ.get("CLAUDE_CREDENTIALS_ENV")
                        or os.path.expanduser("~/.claude/.credentials.master.env"))
            if cred.exists():
                for line in cred.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if line.startswith("OPENAI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not key:
            raise SystemExit(
                "ОТКАЗ: не задан OPENAI_API_KEY.\n"
                "  Где взять: platform.openai.com/api-keys\n"
                "  Как задать: export OPENAI_API_KEY=... (или строка OPENAI_API_KEY=... "
                "в ~/.claude/.credentials.master.env)"
            )
        _KEY = key
    return _KEY


MODEL = 'gpt-image-2-2026-04-21'

STYLE = (" Editorial vector illustration in a modern tech-magazine style. "
         "Strictly limited palette: warm cream background (#F1F3F5), deep navy (#0B1021), "
         "electric blue (#3B5BDB) and bright cyan (#4DABF7) accents, small touches of "
         "terracotta (#CC7357). Clean flat shapes, subtle grain, confident geometry, generous "
         "negative space. NO text, NO words, NO logos, NO watermarks. Centered, balanced composition.")

# name -> scene prompt (STYLE is appended automatically)
IMAGES = {
    "illustration": "A clear central concept illustration relevant to the card topic.",
}


def gen(name, scene, out_dir, size='1024x1536', quality='high', ref=None):
    print(f"Generating {name} ...", flush=True)
    prompt = scene + STYLE
    if ref:
        with open(ref, 'rb') as f:
            r = requests.post('https://api.openai.com/v1/images/edits',
                              headers={'Authorization': f'Bearer {get_key()}'},
                              files={'image[]': ('ref.jpg', f.read(), 'image/jpeg')},
                              data={'model': MODEL, 'prompt': prompt, 'size': size,
                                    'quality': quality, 'n': 1}, timeout=300)
    else:
        r = requests.post('https://api.openai.com/v1/images/generations',
                          headers={'Authorization': f'Bearer {get_key()}'},
                          json={'model': MODEL, 'prompt': prompt, 'size': size,
                                'quality': quality, 'n': 1}, timeout=300)
    if r.status_code != 200:
        print(f'  ERROR {r.status_code}: {r.text[:400]}', flush=True)
        return False
    b64 = r.json()['data'][0].get('b64_json')
    if not b64:
        print(f'  no b64: {r.json()["data"][0]}', flush=True)
        return False
    path = os.path.join(out_dir, f'{name}.png')
    with open(path, 'wb') as f:
        f.write(base64.b64decode(b64))
    print(f'  OK -> {path}', flush=True)
    return True


if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    ok = sum(gen(n, s, out_dir) for n, s in IMAGES.items())
    print(f'\nDONE {ok}/{len(IMAGES)}')
