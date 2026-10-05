// test_doodles.js — hero sheet + every LIB doodle on one page: check a new hero / doodle / palette before animating.
//   python render/still.py pencil/index.html st/sheet 0.5 land "scenes=test_doodles.js"            (hero + doodles)
//   python render/still.py pencil/index.html st/sheet 0.5 land "scenes=test_doodles.js&pal=chalk"   (another palette)
// Optional query: &mouth=0.6 (hero mouth), &reveal=0.5 (draw-on). Any JS error shows up as NOT READY + the message.
'use strict';
let pen;
function SETUP() { pen = new PEN.Pen(ctx, CW, CH, PAL); }
function renderAt(t) {
  pen.frame(t);
  const port = FMT === 'port';
  K.applyCamera(ctx, CW, CH, { x: 0, y: 0, zoom: 1 }, CW / (port ? 1080 : 1920));
  LIB.paperWorld(pen, { x: 0, y: 0, zoom: 1 }, 0);
  const m = Number(QS.get('mouth') || 0.5), rv = Number(QS.get('reveal') || 1);
  // three heroes: graphite, coloured and talking, surprised with arms up (different ids = different boil)
  const hy = port ? -420 : -60, hs = 0.8, hx = port ? [-350, 0, 350] : [-800, -490, -180];
  HERO.draw(pen, { x: hx[0], y: hy, s: hs, color: 0, reveal: rv, id: 'hA' });
  const a = HERO.draw(pen, { x: hx[1], y: hy, s: hs, color: 1, mouth: m, look: [0.7, -0.3], reveal: rv, id: 'hB', armR: { sh: -1.2, el: -0.6 } });
  HERO.draw(pen, { x: hx[2], y: hy, s: hs, color: 1, shape: 'o', blink: 0, brow: 0.8, reveal: rv, id: 'hC', armL: { sh: 4.2, el: 0.5 }, armR: { sh: -1.25, el: -0.55 }, legs: [0, 14] });
  LIB.sparkle(pen, a.handR[0], a.handR[1] - 20, 22, 1, 'handmark', PAL.accent3);       // anchor point returned by HERO.draw
  pen.text('hero.js', hx[1], hy + 70, { size: 40, font: 'handb', align: 'center', id: 'lbl0', color: PAL.accent1 });
  // doodles
  const cell = (cx, cy, label, fn) => { fn(cx, cy); pen.text(label, cx, cy + (port ? 150 : 135), { size: 30, font: 'code', align: 'center', id: 'lbl' + label, alpha: 0.7 }); };
  const G = port
    ? [[-360, 0], [0, 0], [360, 0], [-360, 330], [0, 330], [360, 330], [-360, 660], [0, 660], [360, 660], [-360, -760], [0, -760], [360, -760]]
    : [[160, -330], [460, -330], [760, -330], [160, -20], [460, -20], [760, -20], [-760, 300], [-460, 300], [-160, 300], [160, 300], [460, 300], [760, 300]];
  const items = [
    ['card', (x, y) => LIB.card(pen, x - 110, y - 70, 220, 140, 1, 'dcard', { fill: PAL.accent1, fillAlpha: 0.3 })],
    ['arrow', (x, y) => LIB.arrow(pen, [x - 110, y + 40], [x + 110, y - 40], 1, 'darrow', { bend: 0.6, color: PAL.accent3 })],
    ['crossOut', (x, y) => { LIB.card(pen, x - 90, y - 60, 180, 120, 1, 'dx0', { shade: false }); LIB.crossOut(pen, x, y, 200, 140, 1, 'dx1', PAL.accent3); }],
    ['sparkle', (x, y) => { LIB.sparkle(pen, x - 50, y, 40, 1, 'ds0', PAL.warm2); LIB.sparkle(pen, x + 50, y - 30, 28, 1, 'ds1', PAL.accent1); }],
    ['terminal', (x, y) => LIB.terminal(pen, x - 130, y - 90, 260, 180, ['> hi', { t: 'ok', c: PAL.accent2 }], 1, 'dterm', { size: 26 })],
    ['calendar', (x, y) => LIB.calendar(pen, x, y, 0.8, 21, 1, 'dcal', { topColor: PAL.accent3 })],
    ['filmFrame', (x, y) => LIB.filmFrame(pen, x - 120, y - 70, 240, 135, 1, 'dfilm', () => LIB.landscape(pen, x - 120, y - 70, 240, 135, { lw: 2.2, color: 1, sunColor: PAL.warm }, 'dland'))],
    ['magnifier', (x, y) => LIB.magnifier(pen, x - 20, y - 20, 60, 0.8, 1, 'dmag', null)],
    ['ruler', (x, y) => LIB.ruler(pen, x - 120, y, 240, 4, 1, 'drul', { size: 28, minor: 2, unit: 'с' })],
    ['playhead+wave', (x, y) => { LIB.waveform(pen, x - 120, y, 240, 80, { gaps: [[0.4, 0.55]] }, 'dwave'); LIB.playhead(pen, x - 20, y - 60, y + 50, 'dph'); }],
    ['laptop', (x, y) => LIB.laptop(pen, x, y + 50, 0.8, 1, 1, 'dlap', (sx, sy, sw, sh) => pen.text('{ }', sx + sw / 2, sy + sh * 0.65, { size: 48, font: 'codeb', align: 'center', id: 'dlapt', color: PAL.accent1 }), 1)],
    ['stickPerson', (x, y) => LIB.stickPerson(pen, x, y + 60, 1.2, 'dstick', 1, true)],
  ];
  items.forEach(([label, fn], i) => cell(G[i][0], G[i][1], label, fn));
  pen.text('palette: ' + PAL.name, port ? 0 : 460, port ? 900 : -470, { size: 36, font: 'hand', align: 'center', id: 'palname', color: PAL.soft });
  LIB.vignette(ctx);
}
