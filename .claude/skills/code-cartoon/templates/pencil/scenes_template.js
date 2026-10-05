// scenes_template.js — two sample scenes of the pencil style (new_project.py copies it to pencil/scenes.js).
// Story (voice/script.txt): «Этот герой нарисован кодом: каждая линия — строчка программы. | Скажи одну фразу — и лампочка
// загорится. Остальной кадр не сдвинется ни на пиксель. Так работает мультик кодом.»
// What it shows: paper world + camera, construction lines, draw-on with p, boiling on twos, handwriting synced to the voice
// word by word, a talking and blinking hero, a dive into an object that is the first object of the next scene (chained
// transition), the turn at ~40 % with the warm accent saved for it, the «nothing else moved» freeze, a static poster, CUES.
// Rules: every time comes from the voice (W('слово'), K.scene) — never seconds of one voice take; everything is drawn
// from tt = K.twos(t) (12 drawings a second); ids are stable per object; no Math.random.
'use strict';
const { clamp, lerp, inv, E, tw, word: W, mouthAt } = K;
let pen;
const CUES = [];                // sound cue sheet {t, k, g}: render.py dumps it to <out>.cues.json, sound/synth.py plays it
window.CUES = CUES;
const cue = (t, k, g = 1, extra) => CUES.push(Object.assign({ t: +t.toFixed(3), k, g }, extra || {}));

// ---------- timing anchors (all from TIMING) ----------
const S1_END_TICK = K.lastTick('s1_intro');                    // last drawing of scene 1
const S2_START_TICK = K.firstTick('s2_light');                 // first drawing of scene 2
const DIVE0 = S1_END_TICK - 0.75, DIVE1 = S1_END_TICK - 1 / 12; // the dive ends one drawing (2 frames) before the cut
const PULL0 = S2_START_TICK + 1 / 12, PULL1 = PULL0 + 0.9;      // scene 2 holds the same framing, then pulls back
const TURN = W('загорится').s + 0.25;                          // the click: the bulb lights up
// colored pencil from this moment (0 = from the first frame: the owner's choice 05.10, «понравился карандаш, когда он
// был цветным»). Put TURN here for the methodology's arc «graphite and cold before the turn, colored and warm after».
const COLOR_FROM = 0;
const colorAt = tt => (COLOR_FROM <= 0 ? 1 : E.ioQ(inv(COLOR_FROM, COLOR_FROM + 0.6, tt)));
let TINT = 1;
const FREEZE0 = W('Остальной').s - 0.05, FREEZE1 = W('пиксель').e + 0.3;
const POSTER0 = W('Так').s - 0.1, LAST = W('кодом', 2).e;      // «кодом» is said twice: the 2nd one ends the voice

// deterministic blinks every 2.4–4.3 s (seeded, not tied to one voice take)
const BLINKS = (() => { const r = K.rngOf('blinks'), out = []; for (let t = 1.3; t < TIMING.duration; t += 2.4 + r() * 1.9) out.push(t); return out; })();
const blinkAt = t => { for (const b of BLINKS) { const d = Math.abs(t - b); if (d < 0.13) return 1 - d / 0.13; } return 0; };
const heroBase = (tt, o) => Object.assign({ blink: blinkAt(tt), mouth: mouthAt(tt), id: 'hero', color: TINT }, o);

// ---------- layout: every number through LP(landscape, portrait); text stays above the 85 % line (land y < 378, port y < 672)
const BULB = { x: LP(330, 190), y: LP(-110, -520), s: LP(1, 1.15) };
const S1 = { hero: { x: LP(-430, 0), y: LP(360, 400), s: LP(1.25, 1.55) }, title: { x: LP(330, 0), y: LP(300, 600), size: LP(96, 92) },
  card: { x: LP(-900, -480), y: LP(-470, -880), w: LP(660, 960), h: 150, size: LP(72, 64) } };
// scene 2 moves the hero and the card: the change is hidden while the camera is inside the bulb. Anything that is inside
// the shared framing at the cut must look the same on both sides of it (here: only the bulb).
const S2 = { hero: { x: LP(-220, -150), y: LP(380, 420), s: LP(1.2, 1.45) }, title: { x: LP(430, 0), y: LP(300, 620), size: LP(112, 104) },
  card: { x: LP(-900, -480), y: LP(-470, -880), w: LP(860, 960), h: 150, size: LP(64, 58) } };
const WIDE = { x: 0, y: 0, zoom: 1 };
const BULB_CAM = () => camOnRect(BULB.x, BULB.y - 8 * BULB.s, 320 * BULB.s, 390 * BULB.s);    // the shared framing at the cut

function SETUP() {
  pen = new PEN.Pen(ctx, CW, CH, PAL);
  // scene 1
  cue(0, 'pencil_long', 0.6);
  cue(W('нарисован').s, 'scribble', 0.6); cue(W('кодом').s, 'scribble', 0.5);
  cue(W('каждая').s, 'type_run', 0.6); cue(W('строчка').s, 'pencil_long', 0.45);
  cue(DIVE0, 'zoom', 0.8);
  // scene 2
  cue(PULL0, 'zoom_out', 0.6);
  cue(W('Скажи').s, 'type_run', 0.7);
  cue(TURN, 'click', 1.0); cue(TURN + 0.02, 'shine', 0.9); cue(TURN + 0.05, 'color_fill', 0.7);
  cue(W('Остальной').s, 'scan', 0.6);
  scanMarks().forEach(m => cue(m.t, 'tick', 0.6));
  cue(W('Так').s, 'pencil_long', 0.5); cue(LAST, 'chime', 0.9);
}

// ---------- camera ----------
function camera(c, warm = TINT) {
  K.applyCamera(ctx, CW, CH, c, CW / (FMT === 'port' ? 1080 : 1920));
  LIB.paperWorld(pen, c, warm);                                // paints the paper: first call of every scene
}
const camKeys = (t, keys, ease = E.ioC) => {                   // [[time, cam], ...]
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) return K.lerpCam(keys[i - 1][1], keys[i][1], ease(inv(keys[i - 1][0], keys[i][0], t)));
  return keys[keys.length - 1][1];
};
// camera whose frame fits the world rect (cx, cy, w, h)
const camOnRect = (cx, cy, w, h) => ({ x: cx, y: cy, zoom: Math.min((FMT === 'port' ? 1080 : 1920) / w, (FMT === 'port' ? 1920 : 1080) / h) });

// ---------- helpers ----------
// handwriting synced to the voice: items [[shown text, timing word, occurrence]], each written while its word is spoken
function writeWords(tt, items, x, y, o) {
  const font = o.font || 'hand', gap = pen.textW(' ', o.size, font);
  const widths = items.map(([txt]) => pen.textW(txt, o.size, font));
  let cx = o.align === 'center' ? x - (widths.reduce((a, b) => a + b, 0) + gap * (items.length - 1)) / 2 : x;
  items.forEach(([txt, w, n], i) => {
    const wd = W(w, n || 1);
    const p = o.p != null ? o.p : tw(tt, wd.s - 0.05, Math.max(0.25, wd.e - wd.s + 0.05), E.lin);
    if (p > 0) pen.text(txt, cx, y, { size: o.size, font, color: o.color, id: o.id + i, p });
    cx += widths[i] + gap;
  });
}
// the bulb doodle: p = draw-on, light 0..1 (warm accent only after the turn), shared by both scenes (same id = same boil)
function bulb(x, y, s, p, light, id) {
  if (p <= 0) return;
  const ctx = pen.ctx; ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const glass = PEN.spline([[0, -165], [62, -150], [100, -100], [100, -40], [70, 10], [46, 46], [44, 80], [-44, 80], [-46, 46], [-70, 10], [-100, -40], [-100, -100], [-62, -150]], 6, true);
  if (light > 0) for (let k = 0; k < 12; k++) {                // rays grow with the light
    const a = k / 12 * Math.PI * 2 + 0.26, r1 = 128, r2 = 128 + (34 + (k % 2) * 22) * light;
    pen.line([[Math.cos(a) * r1, -62 + Math.sin(a) * r1], [Math.cos(a) * r2, -62 + Math.sin(a) * r2]], { w: 4.5, color: PAL.warm2, id: id + 'ray' + k, gaps: 0 });
  }
  if (p > 0.3) pen.paper(glass);                               // occlusion only once the outline is mostly drawn
  if (light > 0) LIB.glow(pen, () => pen.fill(glass, { color: PAL.warm, alpha: 0.9 * light, id: id + 'lit', gap: 3.4, w: 2.8 }), PAL.warm);
  else pen.hatch(PEN.toPath(glass), PEN.bbox(glass), { color: PAL.line, alpha: 0.13, gap: 7, w: 1.2, id: id + 'gh', p: inv(0.55, 1, p) });
  pen.shape(glass, { w: 3.6, id: id + 'glass', p: inv(0, 0.5, p), color: light > 0.5 ? PAL.warm2 : null });
  pen.line([[-24, 80], [-20, 12], [-12, -22], [-4, 2], [4, -22], [12, 2], [20, -22], [24, 80]], { w: 2.4, id: id + 'fil', p: inv(0.4, 0.7, p), gaps: 0, color: light > 0.3 ? PAL.warm2 : null });
  for (let k = 0; k < 3; k++) {                                // screw base
    const b = PEN.rect(-46 + k * 3, 84 + k * 22, 92 - k * 6, 20, 8);
    pen.paper(b); pen.hatch(PEN.toPath(b), PEN.bbox(b), { color: PAL.line, alpha: 0.3, gap: 4, w: 1.2, id: id + 'bh' + k, p: inv(0.6 + k * 0.1, 0.8 + k * 0.1, p) });
    pen.shape(b, { w: 2.6, id: id + 'band' + k, p: inv(0.55 + k * 0.1, 0.75 + k * 0.1, p), gaps: 0 });
  }
  const tip = PEN.ellipse(0, 156, 18, 9);
  pen.solid(tip, PAL.line, 0.8 * inv(0.85, 1, p)); pen.shape(tip, { w: 2.2, id: id + 'tip', p: inv(0.85, 1, p), gaps: 0 });
  ctx.restore();
}
// the «0 px» marks: where the scan line passes and when (shared by the picture and the cue sheet)
function scanMarks() {
  const x0 = LP(-960, -540), x1 = LP(960, 540), t0 = W('Остальной').s, t1 = W('пиксель').s + 0.2;
  const pts = [[S2.hero.x + 230, S2.hero.y - 220 * S2.hero.s], [LP(-190, -300), LP(-240, -640)], [LP(480, 330), LP(-90, -300)]];
  return pts.map(([x, y]) => ({ x, y, t: lerp(t0, t1, clamp((x - x0) / (x1 - x0))) }));
}

// ======================= S1: the hero is drawn by code =======================
function s1(tt) {
  let cam = camKeys(tt, [[0, WIDE], [DIVE0, { x: LP(20, 0), y: LP(-10, -20), zoom: 1.05 }]], E.lin);   // slow push
  if (tt > DIVE0) cam = K.lerpCam(cam, BULB_CAM(), E.ioC(inv(DIVE0, DIVE1, tt)));                    // dive into the bulb
  camera(cam);
  const h = S1.hero;
  // the cover frame is not empty: the sketch is already under way at t = 0, construction lines fade after 1.2 s
  const gk = 1 - tw(tt, 1.2, 1.0);
  pen.guides([
    PEN.ellipse(h.x, h.y - 165 * h.s, 112 * h.s, 120 * h.s),
    [[h.x, h.y - 360 * h.s], [h.x, h.y + 20]],
    [[h.x - 200 * h.s, h.y + 4], [h.x + 200 * h.s, h.y + 4]],
    PEN.ellipse(h.x - 40 * h.s, h.y - 186 * h.s, 26 * h.s, 28 * h.s), PEN.ellipse(h.x + 40 * h.s, h.y - 186 * h.s, 26 * h.s, 28 * h.s),
    PEN.ellipse(BULB.x, BULB.y - 62 * BULB.s, 104 * BULB.s, 104 * BULB.s),
  ], gk, 's1g');
  const point = E.outBack(tw(tt, W('каждая').s, 0.35));
  HERO.draw(pen, heroBase(tt, {
    x: h.x, y: h.y, s: h.s, reveal: lerp(0.45, 1, tw(tt, 0, 1.6, E.outQ)), look: tt < W('каждая').s ? [0.2, -0.1] : [0.9, -0.4],
    armR: { sh: lerp(0.94, -0.6, point), el: lerp(0.35, -0.5, point) },          // points at the bulb
    squash: 0.012 * Math.sin(tt * 2.4),
  }));
  // handwriting, word by word with the voice
  const T = S1.title;
  writeWords(tt, [['нарисован', 'нарисован'], ['кодом', 'кодом', 1]], T.x, T.y, { size: T.size, color: PAL.accent1, align: 'center', id: 's1t' });
  // «каждая линия — строчка программы»: a code line is typed, then the bulb is drawn on by it.
  // During the dive the card slides off and the arrow un-draws: at the cut only the bulb is left in the framing.
  const C = S1.card, ca = W('каждая').s - 0.15, away = E.inQ(tw(tt, DIVE0, 0.45, E.lin));
  if (tt > ca && away < 1) {
    ctx.save(); ctx.translate(0, -away * LP(560, 480));
    LIB.card(pen, C.x, C.y, C.w, C.h, tw(tt, ca, 0.3, E.lin), 's1card', { r: 22 });
    pen.text('> bulb.draw()', C.x + 36, C.y + C.h * 0.66, { size: C.size, font: 'code', id: 's1code', p: tw(tt, W('каждая').s, W('линия').e - W('каждая').s, E.lin) });
    ctx.restore();
    const a0 = LP([C.x + C.w + 20, C.y + C.h / 2], [C.x + C.w * 0.3, C.y + C.h + 20]);
    LIB.arrow(pen, a0, [BULB.x - 130 * BULB.s, BULB.y - 120 * BULB.s], tw(tt, W('строчка').s - 0.2, 0.4, E.lin) * (1 - away), 's1arrow', { bend: LP(-0.5, 0.4), color: PAL.accent1 });
  }
  const bp = Math.max(0.12 * (1 - gk), tw(tt, W('строчка').s, W('программы').e - W('строчка').s + 0.2, E.lin));
  bulb(BULB.x, BULB.y, BULB.s, bp, 0, 'bulb');
}

// ======================= S2: one phrase lights the bulb; nothing else moves =======================
function s2(tt) {
  camera(K.lerpCam(BULB_CAM(), WIDE, E.ioC(inv(PULL0, PULL1, tt))), Math.max(TINT, tw(tt, TURN, 0.6)));   // paper warm (always, if COLOR_FROM = 0)
  const lit = tt >= TURN, light = lit ? tw(tt, TURN, 0.25, E.outQ) : 0, freeze = tt >= FREEZE0 && tt < FREEZE1;
  const dLive = pen.d;
  if (freeze) pen.d = Math.floor(FREEZE0 * 12 + 1e-6);          // freeze the boil: the picture is the same drawing
  // the prompt card: the phrase is typed while it is said
  const C = S2.card, pa = W('Скажи').s - 0.15;
  if (tt > pa) {
    LIB.card(pen, C.x, C.y, C.w, C.h, tw(tt, pa, 0.3, E.lin), 's2card', { r: 22 });
    pen.text('> лампочка: жёлтая', C.x + 36, C.y + C.h * 0.66, { size: C.size, font: 'code', id: 's2code', color: lit ? PAL.warm2 : null, p: tw(tt, W('Скажи').s, W('фразу').e - W('Скажи').s + 0.2, E.lin) });
    if (tt > W('фразу').e && !lit && pen.d % 2 === 0) {       // blinking cursor until Enter
      const cx = C.x + 36 + pen.textW('> лампочка: жёлтая', C.size, 'code') + 10;
      pen.line([[cx, C.y + C.h * 0.28], [cx, C.y + C.h * 0.74]], { w: 4, id: 's2cursor', gaps: 0 });
    }
  }
  // the hero: talks, presses Enter on the turn, colours up (graphite -> coloured pencil), waves on the poster
  // arms: up on the click, down again before the freeze starts (a frozen frame must not move), the right one waves on
  // the poster; the wave fades in and out with the last sentence, so the poster holds still
  const pop = E.outBack(inv(TURN, TURN + 0.3, tt));
  const relaxEnd = Math.max(TURN + 0.35, Math.min(TURN + 1.15, FREEZE0 - 0.05)), relax = E.ioQ(inv(relaxEnd - 0.4, relaxEnd, tt));
  const raise = E.outBack(inv(POSTER0, POSTER0 + 0.35, tt)), upL = pop * (1 - relax), upR = Math.max(upL, raise);
  const wave = Math.sin((tt - POSTER0) * 9) * 0.3 * Math.sin(Math.PI * inv(POSTER0, LAST, tt));
  const hero = HERO.draw(pen, heroBase(tt, {
    x: S2.hero.x, y: S2.hero.y, s: S2.hero.s, color: Math.max(TINT, tw(tt, TURN, 0.5)), mouth: freeze ? 0 : mouthAt(tt), blink: freeze ? 0 : blinkAt(tt),
    look: lit ? [0.8, -0.9] : tt < W('лампочка').s ? [-0.6, -0.8] : [0.8, -0.8], shape: lit && tt < TURN + 0.7 ? 'o' : 'smile', brow: lit ? 0.7 : 0.1,
    armR: { sh: lerp(0.94, -1.25, upR) + wave, el: lerp(0.35, -0.55, upR) }, armL: { sh: lerp(2.2, 4.2, upL), el: lerp(-0.35, 0.5, upL) },
    squash: lit && tt < TURN + 0.3 ? -0.08 * Math.sin(Math.PI * inv(TURN, TURN + 0.3, tt)) : 0,
  }));
  // thought dots from the hero's head (HERO.draw returns anchor points) to the bulb
  const dk = tw(tt, PULL1 - 0.2, 0.5, E.lin);
  for (let i = 0; i < 3; i++) {
    const u = (i + 1) / 4, x = lerp(hero.top[0], BULB.x - 110 * BULB.s, u), y = lerp(hero.top[1], BULB.y + 60 * BULB.s, u) - Math.sin(u * Math.PI) * 40;
    if (dk > i / 3) pen.shape(PEN.ellipse(x, y, 8 + i * 5, 8 + i * 5), { w: 2.6, id: 's2dot' + i, gaps: 0, p: inv(i / 3, (i + 1) / 3, dk) });
  }
  bulb(BULB.x, BULB.y, BULB.s, 1, light, 'bulb');
  // the click: a burst ring around the bulb (0.5 s), then sparkles stay
  if (lit) {
    const f = 1 - inv(TURN, TURN + 0.5, tt), cx = BULB.x, cy = BULB.y - 62 * BULB.s;
    if (f > 0) { const r = (150 + (1 - f) * 160) * BULB.s; pen.line(PEN.ellipse(cx, cy, r, r), { w: 6 * f + 1, color: PAL.warm2, id: 's2ring', gaps: 0, closed: true, alpha: f }); }
    [[-1.05, 230], [-0.35, 250], [0.5, 235], [2.6, 240]].forEach(([a, r], i) => LIB.sparkle(pen, cx + Math.cos(a) * r * BULB.s, cy + Math.sin(a) * r * BULB.s, 24, tw(tt, TURN + 0.1 + i * 0.08, 0.2, E.lin), 's2sp' + i, PAL.warm2));
  }
  pen.d = dLive;                                                 // the scan line and the labels keep boiling
  // «остальной кадр не сдвинется ни на пиксель»: a scan line + «0 px» where nothing moved
  if (tt > W('Остальной').s && tt < POSTER0) {
    const t0 = W('Остальной').s, t1 = W('пиксель').s + 0.2, out = 1 - tw(tt, POSTER0 - 0.35, 0.3, E.lin);
    const sx = lerp(LP(-960, -540), LP(960, 540), E.ioQ(inv(t0, t1, tt)));
    if (tt < t1) pen.line([[sx, LP(-560, -1000)], [sx, LP(560, 1000)]], { w: 3.5, color: PAL.accent1, id: 's2scan', gaps: 0, alpha: 0.85 });
    scanMarks().forEach((m, i) => { if (tt >= m.t) pen.text('0 px', m.x, m.y, { size: LP(64, 60), font: 'handb', color: PAL.accent1, id: 's2zpx' + i, p: tw(tt, m.t, 0.3, E.lin), alpha: 0.95 * out }); });
  }
  // the poster (last >= 3 s): title written with the last sentence, then nothing fast moves
  if (tt > POSTER0) {
    const T = S2.title;
    writeWords(tt, [['Мультик', 'мультик'], ['кодом', 'кодом', 2]], T.x, T.y, { size: T.size, font: 'sans', align: 'center', id: 's2t' });
    const wd = pen.textW('Мультик кодом', T.size, 'sans');
    pen.line([[T.x - wd / 2, T.y + 26], [T.x + wd / 2, T.y + 18]], { w: 7, color: PAL.warm2, id: 's2under', gaps: 0, p: tw(tt, W('кодом', 2).s, 0.45, E.lin) });
  }
}

// ---------- scene table: names must match TIMING.scenes (timing/timing_config.json) ----------
const SCENES = { s1_intro: s1, s2_light: s2 };
function renderAt(t) {
  pen.frame(t);
  const tt = K.twos(t);
  TINT = colorAt(tt); LIB.setTint(TINT);                       // colored pencil (see COLOR_FROM)
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const sc = TIMING.scenes.find(s => t >= s.start && t < s.end) || TIMING.scenes[TIMING.scenes.length - 1];
  const fn = SCENES[sc.name];
  if (!fn) throw new Error('no scene function for «' + sc.name + '»: TIMING.scenes and SCENES must list the same names');
  fn(tt, t);
  LIB.vignette(ctx);
}
