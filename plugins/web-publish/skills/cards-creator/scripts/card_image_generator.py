#!/usr/bin/env python3
"""
Card Image Generator — single-style image factory for @yourchannel carousels.

Same architecture as the manus-slides engine (whiteboard_generator.py): a task passes through a
STYLE TEMPLATE (a frozen prompt prefix that locks palette + render-style + character) BEFORE the
image model, so a whole deck comes out in ONE cohesive look. Ported here for cards + rebranded to
the YourName palette, with object styles forced onto a PLAIN bg so cut_bg.py can cut them.

Backend: OpenAI gpt-image-2 (gpt-image-2-2026-04-21, /v1/images/generations, b64_json).
Cutouts: cut() (rembg isnet) for integrated/bleed placement (gpt-image-2 has NO transparent bg).

CLI
  python card_image_generator.py templates                       # list styles + aliases
  python card_image_generator.py recommend "релиз новой модели"  # suggest styles for a topic
  python card_image_generator.py test "<subject>" photoreal-3d --cut --size 1024x1536
  python card_image_generator.py generate cards.json ./img       # whole deck, one style => cohesive

cards.json: {"template":"photoreal-3d","cards":[{"id":"bun","subject":"…","size":"1536x1024","cut":true}, …]}

Before writing a card's `subject`, pick the visual TECHNIQUE via references/visual-playbook.md
("рисовалка": info-type → приём → metaphor object). The image must ENCODE the idea, not decorate.
"""
import os, sys, io, json, base64, time
from pathlib import Path
import requests

CRED = os.path.expanduser("~/.claude/.credentials.master.env")
KEY = open(CRED, encoding="utf-8").read().split("OPENAI_API_KEY=")[1].split("\n")[0].strip()
MODEL = "gpt-image-2-2026-04-21"
DEFAULT = "photoreal-3d"

PALETTE = {"cream": "#YOUR_CREAM", "navy": "#YOUR_INK", "blue": "#YOUR_PRIMARY", "cyan": "#YOUR_ACCENT", "terra": "#CC7357"}

# brand invariant for CUTOUT object styles (subject on plain bg → rembg)
_CUT = (" Strict brand palette: warm cream (#YOUR_CREAM), deep navy (#YOUR_INK), electric blue (#YOUR_PRIMARY), "
        "bright cyan (#YOUR_ACCENT), terracotta (#CC7357). ONE clear central subject, balanced, generous space. "
        "NO text, NO words, NO logos, NO watermarks, NO UI chrome. PLAIN seamless near-white background, "
        "subject fully inside frame with margin, for easy cutout.\nSubject:\n")
# brand invariant for FULL-CARD-BACKGROUND styles (no cut — used full-bleed)
_FULL = (" Brand-adjacent tones (navy/blue/cyan/cream/terra). Full-bleed composition covering all corners, "
         "no empty white blocks. ONE clear subject/scene. NO text, NO logos, NO watermarks.\nSubject:\n")

TEMPLATES = {
    # --- cutout object styles (default workflow) ---
    "photoreal-3d":  "Photorealistic high-detail 3D product render. Glossy materials, soft studio lighting, "
                     "gentle contact shadow, shallow depth of field, premium tech-brand look." + _CUT,
    "flat-editorial":"Flat editorial vector illustration. Clean confident shapes, thick tidy outlines, subtle "
                     "grain, modern tech-magazine style, no photorealism, no 3D depth." + _CUT,
    "isometric":     "Isometric 3D illustration, 30-degree angle, clean geometric shapes, soft ambient occlusion, "
                     "technical but playful, no photorealism." + _CUT,
    "marker":        "Hand-drawn marker / sketch illustration — confident slightly-imperfect lines, like a smart "
                     "whiteboard diagram. Icons, arrows and small diagrams drawn with indigo-blue (#YOUR_PRIMARY) and "
                     "copper-orange (#CC7357) markers on clean white. Playful but precise, blueprint-of-an-idea feel." + _CUT,
    "chromatic":     "Playful tech-explainer 3D render — glossy colorful floating object with soft reflections and "
                     "subtle prism/sparkle accents, educational and engaging, light airy feel." + _CUT,
    "paper-craft":   "Layered paper-cut / pop-up craft 3D object, colorful folded paper with visible depth and soft "
                     "shadows between layers, slightly isometric, tactile handmade feel." + _CUT,
    # --- full-card-background styles (no cut; use behind/over text) ---
    "glamour":       "Luxury editorial scene on a rich dark navy cinematic background, dramatic moody lighting, a single "
                     "premium subject lit warmly, fashion-photography drama, minimal." + _FULL,
    "sketch":        "Hand-drawn white chalk on a deep-navy chalkboard, expressive imperfect strokes, doodle diagrams, "
                     "arrows and labels, playful but detailed, faint chalk dust." + _FULL,
    "real-photo":    "Photorealistic editorial photography, cinematic natural lighting, real-world subject, high detail, "
                     "shallow depth of field. Use when a metaphor reads clearer as a real photo than an illustration." + _FULL,
}

ALIASES = {"3d": "photoreal-3d", "default": "photoreal-3d", "premium": "photoreal-3d",
           "flat": "flat-editorial", "vector": "flat-editorial", "icon": "flat-editorial",
           "iso": "isometric", "technical": "isometric",
           "exec": "marker", "exec-sketch": "marker", "whiteboard": "marker", "diagram": "marker", "hand-drawn": "marker",
           "playful": "chromatic", "explainer": "chromatic", "rainbow": "chromatic",
           "paper": "paper-craft", "popup": "paper-craft",
           "luxury": "glamour", "fashion": "glamour", "dark": "glamour",
           "chalk": "sketch", "doodle": "sketch",
           "photo": "real-photo"}

# topic keyword → suggested templates (ported from manus recommend engine, card-tuned)
RECOMMEND = {
    "релиз": ["photoreal-3d", "chromatic"], "launch": ["photoreal-3d", "chromatic"], "новая модель": ["photoreal-3d"],
    "новост": ["photoreal-3d", "flat-editorial"], "анонс": ["chromatic", "photoreal-3d"],
    "сравнен": ["flat-editorial", "isometric"], "бенчмарк": ["flat-editorial"],
    "процесс": ["isometric", "marker"], "архитектур": ["isometric", "marker"], "как работает": ["marker", "isometric"],
    "концепт": ["marker", "flat-editorial"], "идея": ["marker"], "диаграмма": ["marker"], "схема": ["marker", "isometric"],
    "премиум": ["glamour", "photoreal-3d"], "luxury": ["glamour"], "дорог": ["glamour"],
    "весело": ["chromatic", "paper-craft"], "playful": ["chromatic"], "объясни": ["chromatic", "marker"],
    "личн": ["sketch", "real-photo"], "мнение": ["sketch"], "история": ["sketch", "paper-craft"],
    "человек": ["real-photo"], "портрет": ["real-photo"], "команда": ["real-photo"],
    "деньги": ["photoreal-3d", "flat-editorial"], "скорость": ["photoreal-3d"], "рост": ["photoreal-3d", "isometric"],
}


def resolve(t):
    t = (t or DEFAULT).strip(); t = ALIASES.get(t, t)
    return t if t in TEMPLATES else DEFAULT


def recommend(topic):
    tl = (topic or "").lower(); hits = []
    for kw, styles in RECOMMEND.items():
        if kw in tl:
            hits += styles
    seen, out = set(), []
    for s in hits:
        if s not in seen:
            seen.add(s); out.append(s)
    return out[:4] or ["photoreal-3d", "flat-editorial", "marker"]


def build_prompt(subject, template):
    return TEMPLATES[resolve(template)] + subject


def gen_image(subject, out_path, template=DEFAULT, size="1024x1024", quality="high", retries=3):
    full = build_prompt(subject, template)
    for a in range(retries):
        r = requests.post("https://api.openai.com/v1/images/generations",
                          headers={"Authorization": f"Bearer {KEY}"},
                          json={"model": MODEL, "prompt": full, "size": size, "quality": quality, "n": 1},
                          timeout=300)
        if r.status_code == 200:
            b64 = r.json()["data"][0].get("b64_json")
            if b64:
                Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                open(out_path, "wb").write(base64.b64decode(b64)); return True
        print(f"  [ERR {r.status_code}] attempt {a+1}: {r.text[:160]}", flush=True); time.sleep(4)
    return False


def cut(path):
    """rembg cutout -> <name>_t.png (transparent, tight-cropped) for integrated/bleed placement."""
    from rembg import remove, new_session
    from PIL import Image
    sess = new_session("isnet-general-use")
    out = remove(Image.open(path).convert("RGBA"), session=sess, alpha_matting=True,
                 alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=20)
    bb = out.getbbox()
    if bb:
        out = out.crop(bb)
    dst = str(path).rsplit(".", 1)[0] + "_t.png"; out.save(dst); return dst


def generate_from_config(cfg_path, out_dir):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    template = cfg.get("template", DEFAULT); out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    print(f"Template: {resolve(template)} | {len(cfg['cards'])} cards")
    done = []
    for i, c in enumerate(cfg["cards"], 1):
        cid = c.get("id", f"card_{i:02d}"); p = out / f"{cid}.png"
        print(f"[{i}/{len(cfg['cards'])}] {cid} ...", flush=True)
        if gen_image(c["subject"], p, c.get("template", template), c.get("size", "1024x1024")):
            if c.get("cut"):
                cut(p); print(f"    cut -> {cid}_t.png", flush=True)
            done.append(str(p)); print("    ok", flush=True)
        else:
            done.append(None); print("    FAILED", flush=True)
    return done


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == "templates":
        print("TEMPLATES (cutout = plain bg for rembg; full = card background):")
        for k in TEMPLATES:
            kind = "full" if k in ("glamour", "sketch", "real-photo") else "cutout"
            al = [a for a, v in ALIASES.items() if v == k]
            print(f"  {k:14} [{kind}]  aliases: {al}")
    elif cmd == "recommend":
        print("Suggested:", recommend(sys.argv[2] if len(sys.argv) > 2 else ""))
    elif cmd == "test":
        subject = sys.argv[2]
        template = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else DEFAULT
        size = sys.argv[sys.argv.index("--size") + 1] if "--size" in sys.argv else "1024x1024"
        out = Path("./test_card.png")
        if gen_image(subject, out, template, size):
            print("OK ->", out)
            if "--cut" in sys.argv:
                print("cut ->", cut(out))
        else:
            print("FAILED")
    elif cmd == "generate":
        generate_from_config(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "./img")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
