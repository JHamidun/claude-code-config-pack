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
    OPENAI_IMAGE_MODEL    (default: gpt-image-1)
"""
import sys, io, os, base64, argparse, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from _config import openai_key, openai_image_model


def gen(prompt: str, out: str, size: str = '1024x1024', quality: str = 'high'):
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    print(f'Generating mascot reference via {openai_image_model()}...')
    r = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers={'Authorization': f'Bearer {openai_key()}',
                 'Content-Type': 'application/json'},
        json={'model': openai_image_model(),
              'prompt': prompt,
              'size': size,
              'quality': quality,
              'n': 1},
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
    ap.add_argument('--size', default='1024x1024')
    ap.add_argument('--quality', default='high')
    args = ap.parse_args()
    if args.prompt_file:
        prompt = open(args.prompt_file, encoding='utf-8').read()
    elif args.prompt:
        prompt = args.prompt
    else:
        raise SystemExit('--prompt or --prompt-file required')
    gen(prompt, args.out, args.size, args.quality)


if __name__ == '__main__':
    main()
