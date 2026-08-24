"""Channel avatar concepts from YOUR OWN reference photo.

SELF-CONTAINED: telethon NOT needed. Uses PIL + requests + gpt-image-2 (OPENAI_API_KEY from
~/.claude/.credentials.master.env). Face likeness is preserved via the /v1/images/edits endpoint
(pass the reference photo). Output PNGs land in ./avatars (CWD) by default.

Concepts (the brand line + glow treatments tested 2026-05-29, B-variants were the favourites):
  brand    — PIL composite: real circular face on brand radial bg + cyan ring (max likeness)
  showcards— host holding a frying pan with a glowing AI-brain egg yolk ("cooking AI")
  rim      — showcards + cyan rim-light tracing the body contour
  circle   — showcards inside a luminous glowing cyan halo disc
  symbols  — showcards + floating holographic code symbols  >  [] {} <> /  around the head
  char3d   — Pixar-quality stylized 3D character portrait, navy bg + cyan rim
  tech     — cinematic portrait, navy bg + circuit glow + bokeh

USAGE
-----
  python gen_avatar.py <photo.jpg> [concepts] [out_dir]
    <photo.jpg>  reference photo (e.g. ./photo.jpg)
    concepts     comma list (default: brand,showcards,rim,circle,symbols) or 'all'
    out_dir      default ./avatars
  env AVATAR_PHOTO      reference photo, instead of argv[1]
  env AVATAR_PROP       one sentence describing your channel's prop/scene (default: frying pan)
  env AVATAR_FACE_NOTE  optional hint about your look ("wearing glasses") — the likeness itself
                        comes from the photo, no appearance is hardcoded here
Set the chosen avatar via Telethon separately (UploadProfilePhoto / EditPhoto) — not here.
"""
import sys, io, os, base64, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

CRED = os.path.expanduser('~/.claude/.credentials.master.env')
MODEL = 'gpt-image-2-2026-04-21'


def _key():
    return open(CRED, encoding='utf-8').read().split('OPENAI_API_KEY=')[1].split('\n')[0].strip()


# Внешность НЕ описывается словами: likeness держит сама референсная фотография
# (эндпоинт /v1/images/edits получает её файлом). Словесный портрет здесь был бы
# описанием конкретного человека — чужой студент получил бы чужое лицо.
# Нужна подсказка модели («в очках», «седая борода») — env AVATAR_FACE_NOTE.
_NOTE = os.environ.get('AVATAR_FACE_NOTE', '').strip()
FACE = ("Keep the SAME face from the reference photo EXACTLY — same features, same hair, "
        "same skin tone, same age, same expression."
        + (f" {_NOTE}" if _NOTE else ""))
# Сюжетный реквизит канала. Свой — через env AVATAR_PROP (одно предложение).
PROP = os.environ.get(
    'AVATAR_PROP',
    " The subject is a cheerful host holding a small frying pan; inside the pan a sunny-side-up egg"
    " whose yolk is a glowing blue AI brain / neural orb with faint circuit lines — 'cooking AI'.")
BG = " Deep navy background with faint glowing cyan circuit-board traces. Premium, clean, editorial. NO text."

CONCEPTS = {
    'showcards': f"Square Telegram channel avatar, centered. {FACE}{PROP}{BG}",
    'rim': f"Square Telegram channel avatar, centered. {FACE}{PROP} A bright cyan-blue RIM LIGHT "
           f"traces the CONTOUR of the subject's body, shoulders and head — a glowing silhouette "
           f"edge-light against the dark navy. No circle, no ring.{BG}",
    'circle': f"Square Telegram channel avatar, centered. {FACE}{PROP} The whole portrait sits inside "
              f"a soft LUMINOUS GLOWING CIRCLE of cyan-blue light (a radiant halo disc behind and "
              f"around the subject), against the deep navy.{BG}",
    'symbols': f"Square Telegram channel avatar, centered. {FACE}{PROP} Floating around and above the "
               f"subject's head: small glowing holographic code symbols — a greater-than sign, square "
               f"brackets, curly braces, angle brackets and slashes — in bright cyan and electric blue, "
               f"like sparks of code (these few symbols are the ONLY text/glyphs).{BG}",
    'char3d': f"Square channel avatar, head and shoulders, centered. A glossy photorealistic 3D "
              f"character portrait of the SAME person from the reference ({FACE}) Pixar-quality "
              f"stylized 3D render, deep navy background with electric-blue and bright cyan rim light, "
              f"soft studio shadows. Premium, clean. No text.",
    'tech': f"Square channel avatar, centered. Cinematic portrait of the SAME person from the reference "
            f"photo ({FACE}) confident friendly expression, deep navy background with subtle cyan "
            f"circuit-light glow and soft bokeh, premium tech brand vibe. No text.",
}


def brand_composite(photo, out):
    """Real face, circular, on brand blue->navy radial + cyan ring. Perfect likeness, on-brand."""
    LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS
    yy, xx = np.mgrid[0:1024, 0:1024]
    d = np.clip(np.sqrt((xx - 512) ** 2 + (yy - 360) ** 2) / 760, 0, 1)[..., None]
    c1, c2 = np.array([45, 47, 232]), np.array([1, 3, 52])  # #3B5BDB -> #0B1021
    bg = Image.fromarray((c1 * (1 - d) + c2 * d).astype('uint8'))
    im = Image.open(photo).convert('RGB'); w, h = im.size; s = min(w, h)
    face = im.crop(((w - s) // 2, (h - s) // 2 - int(s * 0.05), (w - s) // 2 + s,
                    (h - s) // 2 + s - int(s * 0.05))).resize((720, 720), LANCZOS)
    mask = Image.new('L', (720, 720), 0); ImageDraw.Draw(mask).ellipse((0, 0, 720, 720), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1))
    ring = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((148, 148, 876, 876), outline=(41, 169, 255, 255), width=10)
    bg.paste(face, (152, 150), mask); bg = bg.convert('RGBA'); bg.alpha_composite(ring)
    bg.convert('RGB').save(out); print('  ok brand', flush=True)


def edit(photo, key, name, prompt, out):
    print('gen', name, flush=True)
    with open(photo, 'rb') as f:
        r = requests.post('https://api.openai.com/v1/images/edits',
            headers={'Authorization': f'Bearer {key}'},
            files={'image[]': ('ref.jpg', f.read(), 'image/jpeg')},
            data={'model': MODEL, 'prompt': prompt, 'size': '1024x1024', 'quality': 'high', 'n': 1},
            timeout=300)
    if r.status_code != 200:
        print(f'  ERR {r.status_code}: {r.text[:200]}', flush=True); return
    b64 = r.json()['data'][0].get('b64_json')
    if b64:
        open(out, 'wb').write(base64.b64decode(b64)); print(f'  ok {name}', flush=True)


if __name__ == '__main__':
    photo = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get('AVATAR_PHOTO'))
    if not photo or not os.path.exists(photo):
        sys.exit('usage: python gen_avatar.py <photo.jpg> [concepts|all] [out_dir]  (or set AVATAR_PHOTO)')
    want = (sys.argv[2] if len(sys.argv) > 2 else 'brand,showcards,rim,circle,symbols')
    out_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.getcwd(), 'avatars')
    os.makedirs(out_dir, exist_ok=True)
    names = list(CONCEPTS) + ['brand'] if want == 'all' else [x.strip() for x in want.split(',')]
    for n in names:
        if n == 'brand':
            brand_composite(photo, os.path.join(out_dir, 'avatar_brand.png'))
        elif n in CONCEPTS:
            edit(photo, _key(), n, CONCEPTS[n], os.path.join(out_dir, f'avatar_{n}.png'))
        else:
            print('  ? unknown concept:', n)
    print('DONE ->', out_dir)
