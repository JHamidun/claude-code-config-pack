"""Generate a master mascot reference image via OpenAI gpt-image-1/2 (1024×1024).

The reference is the visual source-of-truth: facial structure, palette, accessories,
companion, base, props. Used later by `gen_emotion.py` as input ref so all 75
emotion variations stay visually consistent (same character, same outfit, same
companion, same base — only emotion/pose/particles change).

Usage:
    python gen_mascot_reference.py --prompt-file ../references/sample-mascot-prompt.txt \
        --out ./mascot/master.png
    python gen_mascot_reference.py --prompt "Sticker mascot illustration..." \
        --out ./mascot/master.png --size 1024x1024

ENV:
    OPENAI_API_KEY        (required)
    OPENAI_IMAGE_MODEL    (default: gpt-image-2.5-sunburst)

Стикеру нужен прозрачный фон, и с 2.5 он вышел из беты — но работает ТОЛЬКО с
png/webp: попросить transparent и отдать jpeg значит молча получить белую
подложку, которую потом вырезают руками.
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import sys, io, os, base64, argparse, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from _config import openai_key, openai_image_model


def gen(prompt: str, out: str, size: str = '1024x1024', quality: str = 'high',
        transparent: bool = False):
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    print(f'Generating mascot reference via {openai_image_model()}...')
    body = {'model': openai_image_model(),
            'prompt': prompt,
            'size': size,
            'quality': quality,
            'n': 1}
    if transparent:
        # background=transparent действует только на png/webp; на jpeg API
        # ошибки не даст, а фон вернёт белый — поэтому формат задаём явно.
        body['background'] = 'transparent'
        body['output_format'] = 'png'
    r = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers={'Authorization': f'Bearer {openai_key()}',
                 'Content-Type': 'application/json'},
        json=body,
        timeout=600,
    )
    if r.status_code != 200:
        print(f'ERROR {r.status_code}: {r.text[:600]}')
        sys.exit(1)
    d = r.json()['data'][0]
    b64 = d.get('b64_json')
    if not b64:
        print(f'No b64_json in response: {d}')
        sys.exit(1)
    with open(out, 'wb') as f:
        f.write(base64.b64decode(b64))
    print(f'OK → {out} ({os.path.getsize(out)}b)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt', help='Inline prompt text')
    ap.add_argument('--prompt-file', help='Path to prompt file')
    ap.add_argument('--out', required=True, help='Output PNG path')
    ap.add_argument('--size', default='1024x1024',
                    help='любые стороны, кратные 16, до 3840x2160; либо auto')
    ap.add_argument('--quality', default='high',
                    choices=['low', 'medium', 'high', 'xhigh', 'max', 'auto'],
                    help='xhigh и max появились в gpt-image-2.5')
    ap.add_argument('--transparent', action='store_true',
                    help='прозрачный фон (принудительно png)')
    args = ap.parse_args()
    if args.prompt_file:
        prompt = open(args.prompt_file, encoding='utf-8').read()
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit('--prompt or --prompt-file required')
    gen(prompt, args.out, args.size, args.quality, args.transparent)


if __name__ == '__main__':
    main()
