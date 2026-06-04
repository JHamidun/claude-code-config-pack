"""Generate one emotion variation of the mascot via OpenAI image edits API.

Sends master reference + variable "CHANGE FOR THIS EMOTION" prompt + invariant
CONSTRAINTS block. This keeps character identity stable across 75 generations.

Usage:
    python gen_emotion.py --master ./mascot/master.png \
        --emotion-name 01-fire \
        --change "Mascot is fired up. Small flames around the egg edges..." \
        --constraints ../references/character-constraints.txt \
        --out ./emotions/01-fire.png

ENV:
    OPENAI_API_KEY
    OPENAI_IMAGE_MODEL  (default: gpt-image-1)
"""
import sys, io, os, base64, argparse, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from _config import openai_key, openai_image_model


def gen_emotion(master_path: str, emotion_name: str, change_prompt: str,
                constraints: str, out: str,
                size: str = '1024x1024', quality: str = 'high'):
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    full_prompt = f"""Variation of the SAME mascot character shown in the reference image.
Keep the character DESIGN and ALL accessories IDENTICAL to the reference.
Only change the EMOTION and POSE as described below. The result must be
visually consistent with the reference — same character, same outfit, same
companion, same base, same props.

CHANGE FOR THIS EMOTION: {change_prompt}

{constraints}
"""
    with open(master_path, 'rb') as f:
        ref_bytes = f.read()

    print(f'[{emotion_name}] generating via {openai_image_model()}...')
    r = requests.post(
        'https://api.openai.com/v1/images/edits',
        headers={'Authorization': f'Bearer {openai_key()}'},
        files={'image[]': ('master.png', ref_bytes, 'image/png')},
        data={'model': openai_image_model(),
              'prompt': full_prompt,
              'size': size,
              'quality': quality,
              'n': 1},
        timeout=600,
    )
    if r.status_code != 200:
        print(f'  ERR {r.status_code}: {r.text[:300]}')
        return False
    d = r.json()['data'][0]
    b64 = d.get('b64_json')
    if not b64:
        print(f'  no b64_json')
        return False
    with open(out, 'wb') as f:
        f.write(base64.b64decode(b64))
    print(f'  OK → {out} ({os.path.getsize(out)}b)')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--master', required=True)
    ap.add_argument('--emotion-name', required=True)
    ap.add_argument('--change', required=True, help='CHANGE FOR THIS EMOTION prompt')
    ap.add_argument('--constraints', help='Path to invariant CONSTRAINTS text file')
    ap.add_argument('--constraints-text', help='Inline CONSTRAINTS text')
    ap.add_argument('--out', required=True)
    ap.add_argument('--size', default='1024x1024')
    ap.add_argument('--quality', default='high')
    args = ap.parse_args()
    if args.constraints:
        c = open(args.constraints, encoding='utf-8').read()
    elif args.constraints_text:
        c = args.constraints_text
    else:
        c = ''
    ok = gen_emotion(args.master, args.emotion_name, args.change, c, args.out,
                     args.size, args.quality)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
