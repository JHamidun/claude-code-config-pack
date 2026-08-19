#!/usr/bin/env python3
"""Собрать вертикальный ролик формата «персонаж плюс титры» — без единой склейки.

Формат разобран покадрово на ленте, которая стабильно собирает десятки и сотни тысяч
просмотров. Устройство неожиданное: за семьдесят секунд там НЕТ ни одной смены кадра.
Детектор сцен не находит склеек ни при каком пороге. Ритм создают три слоя поверх
неподвижного фона:

    фон       белый в мелкую сетку, не меняется никогда — по нему узнают ленту
    персонаж  внизу, переключает позы; поза держится несколько секунд
    титр      посередине, меняется каждые 1–1,5 с — это и есть монтаж
    стикер    сверху, буквально иллюстрирует произносимую фразу

Отсюда следствие для сборки: резать нечего. Нужен один кадр и расписание слоёв, а
привычный монтаж со склейками этому формату только мешает — фон один и тот же, и
склейка читается как сбой, а не как ритм.

    python build_mascot_reel.py script.json -o out/
    python build_mascot_reel.py script.json -o out/ --duration 24

Файл сценария — список реплик:
    {"lines": [
       {"text": "СЕГОДНЯ Я СЭКОНОМЛЮ", "accent": "СЭКОНОМЛЮ",
        "pose": "explain", "sticker": "money.png", "badge": "≈ пара тысяч ₽"},
       ...
    ]}
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).parent
SKILLS = HERE.parent.parent

# Ритм волнообразный, а не ровный. Первая попытка была вдвое медленнее оригинала,
# вторая — разогнана до метронома: смена каждые 0,6 с превращает ролик в пулемёт.
# В оригинале быстрые перечисления по 0,4–0,6 с чередуются с фиксацией на 2–3 с,
# и именно перепад создаёт ощущение живого монтажа. Длительность задаётся в самом
# сценарии построчно; это значение — только запасное.
LINE_SECONDS = 0.9


def data_uri(p: pathlib.Path) -> str:
    """Картинка внутрь страницы: рендерер снимает локальный файл, внешние ссылки не нужны."""
    ext = p.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext or 'png'}"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def build_html(lines: list[dict], poses: dict, stickers: dict, *,
               width: int, height: int, per_line: float, font: str,
               mouths: dict | None = None, visemes: list | None = None,
               fps: float = 30) -> str:
    """Одна страница: фон, персонаж, титр, стикер. Всё расписание — в данных сцены."""
    mouths = mouths or {}
    visemes = visemes or []
    payload = []
    t = 0.0
    for ln in lines:
        payload.append({
            "text": ln.get("text", ""),
            "accent": ln.get("accent", ""),
            "pose": ln.get("pose", "explain"),
            "sticker": ln.get("sticker"),
            "widget": ln.get("widget"),
            "badge": ln.get("badge"),
            "start": round(t, 2),
            "end": round(t + ln.get("seconds", per_line), 2),
        })
        t += ln.get("seconds", per_line)
    # Поза держится дольше одной реплики, поэтому её толчок отсчитывается от момента
    # смены позы, а не от начала строки — иначе персонаж дёргается на каждом титре.
    pose_start = payload[0]["start"] if payload else 0.0
    for i, it in enumerate(payload):
        if i and it["pose"] != payload[i - 1]["pose"]:
            pose_start = it["start"]
        it["poseStart"] = pose_start

    return f"""<!doctype html>
<meta charset="utf-8">
<title>ролик</title>
<style>
  @font-face {{ font-family: 'Mascot'; src: url('{font}'); font-display: block; }}
  html, body {{ margin: 0; padding: 0; background: #fff; overflow: hidden; }}
  #root {{
    width: {width}px; height: {height}px; position: relative; overflow: hidden;
    background-color: #fafafa;
    /* Сетка — постоянная часть кадра: по ней узнают ленту, поэтому она не анимируется */
    background-image:
      linear-gradient(rgba(0,0,0,.045) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,0,0,.045) 1px, transparent 1px);
    background-size: 46px 46px;
    font-family: 'Mascot', system-ui, sans-serif;
  }}
  .sticker {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {int(height * 0.10)}px; width: {int(width * 0.46)}px;
    filter: drop-shadow(0 10px 24px rgba(0,0,0,.16));
    opacity: 0;
  }}
  .badge {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {int(height * 0.075)}px;
    background: #e8402a; color: #fff; font-weight: 800;
    font-size: {int(height * 0.019)}px; letter-spacing: .3px;
    padding: 5px 13px; border-radius: 999px; white-space: nowrap;
    box-shadow: 0 4px 14px rgba(232,64,42,.34); opacity: 0;
  }}
  #title {{
    position: absolute; left: 6%; width: 88%;
    top: {int(height * 0.385)}px;
    text-align: center; font-weight: 900; line-height: 1.06;
    font-size: {int(height * 0.030)}px; letter-spacing: -.3px;
    text-shadow: 0 2px 10px rgba(255,255,255,.9);
    color: #17171a; text-transform: uppercase;
  }}
  #title .accent {{ color: #e8402a; }}

  .hero {{
    position: absolute; left: 50%; transform: translateX(-50%);
    bottom: 0; height: {int(height * 0.46)}px; opacity: 0;
  }}
  /* Рот рисуется в том же стиле, что и персонаж: чёрный контур губ, тёмная полость,
     зубы, язык. Плоское пятно без обводки поверх рисованного лица читается как
     наклейка — контур здесь не украшение, а условие того, что рот выглядит частью
     рисунка. Форма меняется покадрово под звуки речи. */
  .mouth {{
    position: absolute; transform: translate(-50%, -50%);
    overflow: visible; pointer-events: none;
  }}
  .widget {{
    position: absolute; left: 50%; transform: translateX(-50%);
    top: {int(height * 0.115)}px; width: {int(width * 0.72)}px;
    background: #fff; border-radius: 18px; opacity: 0;
    box-shadow: 0 18px 48px rgba(0,0,0,.14), 0 2px 6px rgba(0,0,0,.06);
    overflow: hidden; font-size: {int(height * 0.0155)}px;
  }}
  .widget .bar {{
    height: {int(height * 0.022)}px; background: #f1f1f4;
    display: flex; align-items: center; gap: 6px; padding: 0 12px;
  }}
  .widget .dot {{ width: 9px; height: 9px; border-radius: 50%; background: #d7d7dd; }}
  .widget .body {{ padding: 14px 16px; color: #17171a; }}
  /* Терминал: тёмный, моноширинный — узнаётся мгновенно, объяснять не нужно */
  .widget.term {{ background: #14161a; }}
  .widget.term .bar {{ background: #21242b; }}
  .widget.term .body {{ color: #d6f5c8; font-family: ui-monospace, Consolas, monospace;
                        white-space: pre-wrap; line-height: 1.5; }}
  .widget .cursor {{ display: inline-block; width: .55em; height: 1.05em;
                     background: #7ee36a; vertical-align: -.16em; }}
  .widget .row {{ display: flex; align-items: center; gap: 10px; padding: 7px 0;
                  border-bottom: 1px solid #f0f0f3; }}
  .widget .row:last-child {{ border-bottom: 0; }}
  .widget .tick {{ width: {int(height * 0.017)}px; height: {int(height * 0.017)}px;
                   border-radius: 50%; background: #e8402a; color: #fff;
                   display: flex; align-items: center; justify-content: center;
                   font-size: .62em; flex: 0 0 auto; }}
  .widget .num {{ font-weight: 900; font-size: 2.1em; letter-spacing: -1px; }}
  #timer {{
    position: absolute; right: 18px; top: 16px;
    background: rgba(255,255,255,.92); color: #17171a;
    font-weight: 700; font-size: {int(height * 0.016)}px;
    padding: 4px 10px; border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,.10);
  }}
</style>
<div id="root">
  <div id="timer">0:00</div>
</div>
<script>
const LINES = {json.dumps(payload, ensure_ascii=False)};
const POSES = {json.dumps({k: data_uri(v) for k, v in poses.items()}, ensure_ascii=False)};
const STICKERS = {json.dumps({k: data_uri(v) for k, v in stickers.items()}, ensure_ascii=False)};
const MOUTHS = {json.dumps(mouths, ensure_ascii=False)};
const VISEMES = {json.dumps(visemes, ensure_ascii=False)};  // форма рта по кадрам
const VOICE_FPS = {fps};

const root = document.getElementById('root');
const BASE_TITLE_PX = {int(height * 0.030)};

// Персонажи заводятся один раз и только показываются-прячутся: пересоздавать картинку
// на каждом кадре — значит заново её декодировать, и рендер встаёт.
// Персонаж — не просто картинка, а картинка со ртом поверх. Рот отдельным слоем,
// потому что рисунок неподвижен, а говорить он должен: пока рот не открывается под
// голос, персонаж читается зрителем как мёртвая иллюстрация, а не как спикер.
const heroEls = {{}}, mouthEls = {{}};
for (const [name, src] of Object.entries(POSES)) {{
  const wrap = document.createElement('div');
  wrap.className = 'hero';
  const img = document.createElement('img');
  img.src = src; img.style.height = '100%'; img.style.display = 'block';
  wrap.appendChild(img);
  const m = MOUTHS[name];
  if (m) {{
    // Положение задано в долях от картинки, поэтому переживает любое масштабирование.
    // Рот — рисунок из нескольких частей, а не один элемент: полость, зубы, язык и
    // контур губ живут по отдельности, потому что на разных звуках видны по-разному.
    const box = document.createElement('div');
    box.className = 'mouth';
    box.style.left = (m.cx * 100).toFixed(2) + '%';
    box.style.top  = (m.cy * 100).toFixed(2) + '%';
    box.style.width = (m.w * 100 * 1.06).toFixed(2) + '%';
    box.innerHTML =
      '<svg viewBox="0 0 100 70" style="width:100%;height:auto;overflow:visible">'
      + '<defs><clipPath id="cl_' + name + '">'
      + '<ellipse class="cav" cx="50" cy="35" rx="26" ry="4"/></clipPath></defs>'
      // Заплатка цветом кожи закрывает нарисованный рот. Без неё свой рот ложится
      // поверх чужого: губы персонажа остаются на месте, полость появляется внутри
      // них, и это читается как дыра, а не как открытый рот. Мягкий край — чтобы
      // заплатка не выделялась прямоугольником на бороде.
      + '<defs><filter id="sm_' + name + '" x="-30%" y="-30%" width="160%" height="160%">'
      +   '<feGaussianBlur stdDeviation="1.6"/></filter></defs>'
      + '<ellipse class="patch" cx="50" cy="35" rx="49" ry="9" fill="' + (m.skin || '#eebb9b')
      +   '" filter="url(#sm_' + name + ')"/>'
      + '<ellipse class="cav" cx="50" cy="35" rx="26" ry="4" fill="#54202a"/>'
      + '<g clip-path="url(#cl_' + name + ')">'
      +   '<rect class="tt" x="0" y="0" width="100" height="12" fill="#f6f1ea"/>'
      +   '<rect class="tb" x="0" y="58" width="100" height="12" fill="#e8e0d6"/>'
      +   '<ellipse class="tg" cx="50" cy="66" rx="24" ry="13" fill="#c4676f"/>'
      + '</g>'
      + '<ellipse class="lipline" cx="50" cy="35" rx="26" ry="4" fill="none" '
      +   'stroke="#3a2a26" stroke-width="1.6" opacity="0.75"/>'
      + '</svg>';
    wrap.appendChild(box);
    mouthEls[name] = {{
      box,
      cav: box.querySelectorAll('.cav'),
      patch: box.querySelector('.patch'),
      lipline: box.querySelector('.lipline'),
      tt: box.querySelector('.tt'),
      tb: box.querySelector('.tb'),
      tg: box.querySelector('.tg'),
    }};
  }}
  root.appendChild(wrap); heroEls[name] = wrap;
}}
const stickerEls = {{}};
for (const [name, src] of Object.entries(STICKERS)) {{
  const img = document.createElement('img');
  img.className = 'sticker'; img.src = src;
  root.appendChild(img); stickerEls[name] = img;
}}
// Виджеты-интерфейсы. Живут в разметке, поэтому текст внутри можно печатать по буквам
// и менять числа — картинкой так не сделать.
const WIDGETS = {{
  terminal: '<div class="bar"><i class="dot"></i><i class="dot"></i><i class="dot"></i></div>'
          + '<div class="body" id="w-term"></div>',
  checklist: '<div class="body">'
          + '<div class="row"><span class="tick">1</span><span>разобрать чужой продакшн</span></div>'
          + '<div class="row"><span class="tick">2</span><span>снять параметры замерами</span></div>'
          + '<div class="row"><span class="tick">3</span><span>собрать своим стеком</span></div>'
          + '</div>',
  counter: '<div class="body" style="text-align:center">'
          + '<div class="num" id="w-num">0</div>'
          + '<div style="opacity:.55;margin-top:2px">генераций</div></div>',
}};
const widgetEls = {{}};
for (const [name, html] of Object.entries(WIDGETS)) {{
  const el = document.createElement('div');
  el.className = 'widget' + (name === 'terminal' ? ' term' : '');
  el.innerHTML = html;
  root.appendChild(el); widgetEls[name] = el;
}}

const badge = document.createElement('div');
badge.className = 'badge'; root.appendChild(badge);
const title = document.createElement('div');
title.id = 'title'; root.appendChild(title);


const ease = (t) => 1 - Math.pow(1 - Math.min(Math.max(t, 0), 1), 3);
// Формы рта. Размеры в координатах рисунка рта (100 в ширину, 70 в высоту).
// rx/ry — половины ширины и высоты отверстия, tt/tb — сколько видно верхних и нижних
// зубов, tg — язык, cy — вертикальный центр: на закрытых звуках рот сидит выше, на
// открытых челюсть уходит вниз.
const SHAPES = {{
  rest:   {{ rx: 46, ry: 1.0, tt: 0,  tb: 0, tg: 0,  cy: 35 }},
  closed: {{ rx: 46, ry: 0.4, tt: 0,  tb: 0, tg: 0,  cy: 35 }},   // м, б, п
  wide:   {{ rx: 44, ry: 17,  tt: 9,  tb: 4, tg: 10, cy: 39 }},   // а, я
  mid:    {{ rx: 45, ry: 9,   tt: 8,  tb: 0, tg: 0,  cy: 37 }},   // э, е, к, г, х, р
  narrow: {{ rx: 47, ry: 4,   tt: 6,  tb: 0, tg: 0,  cy: 36 }},   // и, ы, й
  round:  {{ rx: 28, ry: 14,  tt: 3,  tb: 0, tg: 6,  cy: 38 }},   // о, ё
  small:  {{ rx: 21, ry: 9,   tt: 0,  tb: 0, tg: 0,  cy: 37 }},   // у, ю
  teeth:  {{ rx: 42, ry: 3,   tt: 7,  tb: 0, tg: 0,  cy: 35 }},   // ф, в
  tongue: {{ rx: 40, ry: 8,   tt: 6,  tb: 0, tg: 9,  cy: 37 }},   // л, т, д, н
  hiss:   {{ rx: 44, ry: 3,   tt: 6,  tb: 0, tg: 0,  cy: 36 }},   // с, з, ш, щ, ж, ц, ч
}};
// Текущее положение губ. Живёт между кадрами: губы подходят к цели, а не прыгают.
const mouthNow = {{ rx: 46, ry: 1.0, tt: 0, tb: 0, tg: 0, cy: 35 }};

// Затухающая пружина: значение перелетает цель и возвращается. Ровно то, чего не
// хватало — без неё появление читается как подмена картинки, а не как движение.
const springAt = (x, damp = 9, freq = 15) => {{
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  return 1 - Math.exp(-damp * x) * Math.cos(freq * x);
}};
// Уход: ускоряющееся падение вниз с потерей плотности — предмет покидает кадр,
// а не выключается.
const leave = (x) => Math.min(Math.max(x, 0), 1);

function draw(t) {{
  // Камера дышит: медленный наезд внутри реплики, сброс на смене. Неподвижный кадр
  // поверх неподвижного фона — главная причина, по которой ролик выглядит презентацией.
  const idx = LINES.findIndex((l) => t >= l.start && t < l.end);
  const cur = idx >= 0 ? LINES[idx] : LINES[LINES.length - 1];

  // Титр появляется с коротким перелётом: масштаб уходит выше единицы и возвращается
  // за четыре кадра. Плавный въезд читается как медленный, а нужен щелчок.
  const age = t - cur.start;
  const life = cur.end - cur.start;
  const inT = ease(age / Math.min(0.10, life * 0.28));
  // Уход занимает долю от срока титра, а не фиксированные 0,2 с. Короткий титр
  // живёт всего треть секунды: с постоянным уходом он половину времени бледнеет и
  // на экране выглядит серым призраком вместо чёрного слова.
  const fade = Math.min(0.20, life * 0.22);
  const out = Math.max(0, (age - (life - fade)) / fade);
  const pop = 0.72 + 0.28 * springAt(Math.min(age / 0.52, 1), 6, 11);
  const dropY = leave(out) * leave(out) * 26;               // ускоряющееся падение
  const html = cur.accent && cur.text.includes(cur.accent)
    ? cur.text.replace(cur.accent, '<span class="accent">' + cur.accent + '</span>')
    : cur.text;
  // Кегль подбирается под длину: фиксированный размер либо мельчит короткую фразу,
  // либо ломает длинную переносами. В оригинале он тоже гуляет — от 3 до 5% высоты.
  const plain = cur.text.split(String.fromCharCode(10)).join(' ');
  const scaleByLen = plain.length <= 10 ? 1.22 : plain.length <= 16 ? 1.06
                   : plain.length <= 24 ? 0.94 : 0.82;
  title.style.fontSize = (BASE_TITLE_PX * scaleByLen).toFixed(1) + 'px';
  title.innerHTML = html;
  title.style.opacity = inT * (1 - leave(out) * 0.9);
  title.style.transform = 'scale(' + pop.toFixed(3) + ') translateY(' + dropY.toFixed(1) + 'px)';


  // Персонаж живёт своим расписанием: поза держится дольше титра и меняется на
  // смысловых переломах, а не вместе с каждой строкой. Совпадение всех трёх слоёв в
  // один момент — главная причина, по которой ролик читается как метроном.
  // Внутри позы кадр слегка дышит: на образце 8–17% пикселей меняются за 0,4–1 с,
  // и без этого статичная иллюстрация читается как зависшая картинка.
  const breathe = 1 + 0.006 * Math.sin(t * 2.1);
  // Смена позы — не подмена картинки, а движение: новая поза приходит с толчком снизу
  // и коротким перелётом по масштабу. Раньше именно здесь ролик выдавал себя.
  const poseAge = t - cur.poseStart;
  const swap = springAt(Math.min(poseAge / 0.60, 1), 6, 10);
  const swapScale = 0.92 + 0.08 * swap;
  const swapY = (1 - swap) * 34;
  for (const [name, el] of Object.entries(heroEls)) {{
    const on = name === cur.pose;
    el.style.opacity = on ? 1 : 0;
    // Без плавного перехода: на кроссфейде обе позы одновременно полупрозрачны,
    // и в кадр попадает призрак — герой просвечивает сам сквозь себя. Движение
    // при смене даёт толчок пружиной, а не растворение.
    el.style.transition = 'none';
    if (on) el.style.transform = 'translateX(-50%) translateY(' + swapY.toFixed(1)
      + 'px) scale(' + (breathe * swapScale).toFixed(4) + ')';
  }}

  // Рот принимает форму того звука, который звучит в этот кадр. Формы приходят
  // готовым списком по кадрам; здесь остаётся перевести имя формы в размеры и
  // плавно к ним подойти — мгновенная подмена размеров даёт дёрганье.
  const vi = Math.round(t * VOICE_FPS);
  const want = SHAPES[VISEMES[vi] || 'rest'] || SHAPES.rest;
  // Губы догоняют цель за пару кадров: мышцы не переставляются мгновенно, и без
  // этого запаздывания артикуляция читается как мигание картинок.
  for (const k of ['rx', 'ry', 'tt', 'tb', 'tg', 'cy']) {{
    mouthNow[k] += (want[k] - mouthNow[k]) * 0.5;
  }}
  const mm = MOUTHS[cur.pose];
  const mouthEl = mouthEls[cur.pose];
  if (mouthEl && mm) {{
    const rx = mouthNow.rx, ry = Math.max(mouthNow.ry, 0.3);
    for (const e of mouthEl.cav) {{
      e.setAttribute('rx', rx.toFixed(2));
      e.setAttribute('ry', ry.toFixed(2));
      e.setAttribute('cy', mouthNow.cy.toFixed(2));
    }}
    // Зубы и язык видны ровно настолько, насколько открыт рот: на сомкнутых губах
    // они не должны просвечивать сквозь контур.
    mouthEl.tt.setAttribute('height', Math.max(0, mouthNow.tt).toFixed(2));
    mouthEl.tt.setAttribute('y', (mouthNow.cy - ry).toFixed(2));
    mouthEl.tb.setAttribute('height', Math.max(0, mouthNow.tb).toFixed(2));
    mouthEl.tb.setAttribute('y', (mouthNow.cy + ry - mouthNow.tb).toFixed(2));
    mouthEl.tg.setAttribute('ry', Math.max(0.5, mouthNow.tg).toFixed(2));
    mouthEl.tg.setAttribute('cy', (mouthNow.cy + ry * 0.55).toFixed(2));
    mouthEl.lipline.setAttribute('rx', rx.toFixed(2));
    mouthEl.lipline.setAttribute('ry', ry.toFixed(2));
    mouthEl.lipline.setAttribute('cy', mouthNow.cy.toFixed(2));
    // Совсем сомкнутый рот не рисуем вовсе: видна нарисованная линия губ.
    // Заплатка видна всегда: нарисованный рот должен быть закрыт и на сомкнутых
    // звуках, иначе на них проступает исходная линия губ поверх нашей.
    mouthEl.box.style.opacity = 1;
  }}
  // Стикер: свой вход, чуть позже титра, чтобы глаз читал их по очереди
  const sAge = age - 0.05;
  const sIn = ease(sAge / 0.12);
  const sPop = 0.64 + 0.36 * springAt(Math.min(Math.max(sAge, 0) / 0.58, 1), 5.5, 10);
  // Парение: пока элемент в кадре, он еле заметно качается. Абсолютно неподвижный
  // предмет поверх статичного фона выглядит приклеенным.
  const float = Math.sin(t * 1.9) * 5;
  for (const [name, el] of Object.entries(stickerEls)) {{
    const on = name === cur.sticker;
    el.style.opacity = on ? sIn : 0;
    el.style.transform = 'translateX(-50%) translateY(' + (on ? (float + dropY * 1.4) : 0).toFixed(1) + 'px) scale(' + (on ? sPop : 0.9).toFixed(3) + ')';
    if (on) el.style.opacity = sIn * (1 - leave(out) * 0.85);
  }}

  // Живые части интерфейса: терминал печатает построчно, счётчик крутит число.
  // Оба привязаны ко времени реплики, а не к своему таймеру — иначе при перемотке
  // рендерера они покажут не то, что должно быть на этом кадре.
  for (const [name, el] of Object.entries(widgetEls)) {{
    const on = name === cur.widget;
    el.style.opacity = on ? sIn : 0;
    el.style.transform = 'translateX(-50%) translateY(' + (on ? (float + dropY * 1.4) : 0).toFixed(1) + 'px) scale(' + (on ? sPop : 0.9).toFixed(3) + ')';
    if (on) el.style.opacity = sIn * (1 - leave(out) * 0.85);
  }}
  if (cur.widget === 'terminal') {{
    const script = 'claude: разбираю ролик…' + String.fromCharCode(10)
                 + '> найдено склеек: 0' + String.fromCharCode(10)
                 + '> титр меняется: 1.1 с' + String.fromCharCode(10)
                 + '> слоёв поверх кадра: 3';
    const chars = Math.floor(Math.min(age / 1.1, 1) * script.length);
    document.getElementById('w-term').innerHTML =
      script.slice(0, chars).split('<').join('&lt;') + '<span class="cursor"></span>';
  }}
  if (cur.widget === 'counter') {{
    const p = Math.min(age / 1.2, 1);
    const val = Math.floor(115447 * (1 - Math.pow(1 - p, 3)));
    document.getElementById('w-num').textContent = val.toLocaleString('ru-RU');
  }}

  badge.textContent = cur.badge || '';
  badge.style.opacity = cur.badge ? sIn : 0;

  const camZoom = 1 + 0.018 * (age / Math.max(life, 0.01));
  root.style.transform = 'scale(' + camZoom.toFixed(4) + ')';
  root.style.transformOrigin = '50% 46%';

  const total = Math.floor(t);
  document.getElementById('timer').textContent =
    '0:' + String(total).padStart(2, '0') + '.' + String(Math.floor((t % 1) * 10));
}}

window.__setTime = (t) => draw(t);
draw(0);
</script>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="JSON со списком реплик")
    ap.add_argument("-o", "--out", default="reel", help="куда собирать")
    ap.add_argument("--poses", help="папка с позами персонажа")
    ap.add_argument("--mouths", help="разметка рта от mouth_map.py")
    ap.add_argument("--visemes", help="формы рта по кадрам от visemes.py")
    ap.add_argument("--fps", type=float, default=30,
                    help="частота кадров, с которой снята огибающая")
    ap.add_argument("--stickers", help="папка со стикерами")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--per-line", type=float, default=LINE_SECONDS)
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.script).read_text(encoding="utf-8"))
    lines = data.get("lines") or []
    if not lines:
        raise SystemExit("в сценарии нет реплик")

    posedir = pathlib.Path(a.poses or data.get("poses_dir") or "mascot")
    stickdir = pathlib.Path(a.stickers or data.get("stickers_dir") or "stickers")
    poses = {p.stem: p for p in posedir.glob("*.png") if not p.stem.startswith(("sheet", "ref", "wave_preview"))}
    if not poses:
        raise SystemExit(f"нет поз персонажа в {posedir}")
    stickers = {p.stem: p for p in stickdir.glob("*.png")} if stickdir.is_dir() else {}

    # Шрифт: жирный гротеск с кириллицей — титр несёт всю нагрузку, тонкий рассыпается
    font_file = None
    fonts = SKILLS / "video-editor" / "assets" / "fonts"
    for cand in ("Unbounded", "Montserrat", "GolosText", "Onest", "Rubik"):
        hits = sorted(fonts.glob(f"{cand}*.ttf"))
        if hits:
            font_file = hits[0]; break
    if not font_file:
        raise SystemExit(f"не нашёлся жирный шрифт с кириллицей в {fonts}")

    outdir = pathlib.Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(font_file, outdir / "font.ttf")

    # Разметка рта и огибающая голоса — необязательные: без них рот просто останется
    # неподвижным, а всё остальное соберётся как прежде.
    mouths = json.loads(pathlib.Path(a.mouths).read_text(encoding="utf-8")) if a.mouths else {}
    visemes = json.loads(pathlib.Path(a.visemes).read_text(encoding="utf-8")) if a.visemes else []
    if mouths and not visemes:
        print("  разметка рта есть, а форм рта нет — рот останется неподвижным")

    html = build_html(lines, poses, stickers,
                      width=a.width, height=a.height,
                      per_line=a.per_line, font="./font.ttf",
                      mouths=mouths, visemes=visemes, fps=a.fps)
    (outdir / "index.html").write_text(html, encoding="utf-8")

    total = sum(l.get("seconds", a.per_line) for l in lines)
    print(f"  реплик: {len(lines)}, поз: {len(poses)}, стикеров: {len(stickers)}")
    print(f"  шрифт: {font_file.name}")
    print(f"  длительность: {total:.1f} с")
    print(f"  собрано: {outdir / 'index.html'}")
    print(f"\n  снять видео:\n    node {SKILLS / 'video-export' / 'scripts' / 'render.mjs'} "
          f"{outdir / 'index.html'} --out {outdir / 'reel.mp4'} --duration {total:.1f} --fps 30")
    return 0


if __name__ == "__main__":
    sys.exit(main())
