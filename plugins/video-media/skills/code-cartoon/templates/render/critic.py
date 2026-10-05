"""External critic: Gemini watches the rendered cartoon (picture + sound) and lists problems with timecodes.

    python render/critic.py <video.mp4> <out.md> [--model gemini-3.1-pro-preview] [--script SCRIPT_v1.md]
                            [--style "рисованный карандашный мультик"] [--extra "на что смотреть особо"]

Paid API call (GOOGLE_API_KEY from ~/.claude/.credentials.master.env). The script/storyboard is the newest SCRIPT*.md in
the project root (or --script; falls back to voice/script.txt). The critic is useful on the PICTURE; about the sound it
has invented problems («нет эффектов» at a click peaking at -0.9 dB) — check every claim by a measurement or a still
before fixing anything.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / '.claude' / '.credentials.master.env')
os.environ.pop('GEMINI_API_KEY', None)               # conflicts with GOOGLE_API_KEY in the SDK
from google import genai  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


if len(sys.argv) < 3 or sys.argv[1].startswith('--'):
    raise SystemExit(__doc__)
video, out = sys.argv[1], Path(sys.argv[2])
model = arg('--model', 'gemini-3.1-pro-preview')
style = arg('--style', 'рисованный карандашный мультик, сделан кодом')
extra = arg('--extra', '')
script_path = Path(arg('--script')) if arg('--script') else (sorted(ROOT.glob('SCRIPT*.md'))[-1:] or [ROOT / 'voice' / 'script.txt'])[0]
script = script_path.read_text(encoding='utf-8') if script_path.exists() else '(сценарий не найден)'
pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', video], capture_output=True, text=True)
dur = float(json.loads(pr.stdout or '{}').get('format', {}).get('duration', 0))

client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
f = client.files.upload(file=video)
while f.state.name == 'PROCESSING':
    time.sleep(3)
    f = client.files.get(name=f.name)
prompt = f"""Ты — строгий режиссёр анимации и монтажёр. Перед тобой {style}, ~{dur:.0f} секунд, озвучка на русском.
Ниже — утверждённый сценарий с раскадровкой (тайминг в нём примерный).

{script}

Посмотри видео целиком со звуком и найди ПРОБЛЕМЫ, которые увидел бы зритель:
1. Где картинка не совпадает с тем, что говорит голос (действие раньше/позже слова больше чем на полсекунды, или не то действие).
2. Где кадр пустой, перегружен или непонятно, куда смотреть.
3. Где что-то дёргается, прыгает, исчезает рывком, наезжает друг на друга, обрезано краем кадра.
4. Где текст в кадре мелкий, нечитаемый или с ошибкой; есть ли текст в нижних 15 % кадра.
5. Звук: где эффект не попадает в действие, музыка мешает голосу, что-то режет слух, обрывы, щелчки.
6. История: понятна ли она без звука по картинке; самый слабый момент ролика; хорош ли последний кадр как постер.
{extra}
Формат ответа: markdown-таблица «таймкод (м:сс.с) | что не так | насколько заметно (сильно/средне/слегка) | как исправить»,
отсортировано по времени. Потом 3 строки: что в ролике лучше всего, что хуже всего, оценка 1–10 как готового ролика для соцсетей.
Не хвали ради вежливости. Не выдумывай: если не уверен, что увидел, — не пиши."""
r = client.models.generate_content(model=model, contents=[f, prompt])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(r.text, encoding='utf-8')
print(r.text[:6000])
print(f'\n-> {out} (script: {script_path.name}). Verify every claim before fixing: the critic invents sound problems.')
