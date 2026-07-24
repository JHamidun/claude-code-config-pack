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
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY = open(os.path.expanduser('~/.claude/.credentials.master.env'), encoding='utf-8') \
    .read().split('OPENAI_API_KEY=')[1].split('\n')[0].strip()
MODEL = 'gpt-image-2-2026-04-21'

STYLE = (" Editorial vector illustration in a modern tech-magazine style. "
         "Strictly limited palette: warm cream background (#YOUR_CREAM), deep navy (#YOUR_INK), "
         "electric blue (#YOUR_PRIMARY) and bright cyan (#YOUR_ACCENT) accents, small touches of "
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
                              headers={'Authorization': f'Bearer {KEY}'},
                              files={'image[]': ('ref.jpg', f.read(), 'image/jpeg')},
                              data={'model': MODEL, 'prompt': prompt, 'size': size,
                                    'quality': quality, 'n': 1}, timeout=300)
    else:
        r = requests.post('https://api.openai.com/v1/images/generations',
                          headers={'Authorization': f'Bearer {KEY}'},
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
