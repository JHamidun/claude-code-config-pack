// lib.js — palette (by roles), format switch, paper and reusable doodles for the pencil style.
// Every doodle draws in world coordinates with the pen; p = draw-on progress 0..1, id = seed prefix (stable boiling).
// Doodles are copied from <эталон>/pencil/lib.js (only the generic ones; story props stay there).
(function (G) {
  'use strict';
  const K = G.K, P = G.PEN;
  const ELL = P.ellipse, RECT = P.rect;

  // ---------- palettes: scenes paint with ROLES (PAL.accent1, PAL.warm), never with hex ----------
  // Roles: paper, line, soft (secondary line), guide (construction lines), grid, accent1..3 (cool accents before the turn),
  // warm / warm2 (kept for the payoff after the turn), dark (true = dark paper: hatch the light, glow allowed),
  // glow (0 = none), warmTint (paper tint after the turn), vignette. The other keys keep the reference doodles working.
  // The whole film is recoloured by one line: ?pal=chalk in the URL (render.py --extra "pal=chalk") or DEFAULT_THEME below.
  const THEMES = {
    notebook: {
      name: 'notebook', dark: false, glow: 0, paper: '#F4F0E5', line: '#2D2B2A', soft: '#8C8680', guide: '#86AEDD',
      grid: 'rgba(96,146,205,0.13)', accent1: '#2F6FD6', accent2: '#36A852', accent3: '#D9412E', warm: '#F2C314', warm2: '#F08A24',
      warmTint: '#F6D9A8', vignette: 'rgba(60,45,25,0.16)',
      blue: '#2F6FD6', cyan: '#1FA2D8', red: '#D9412E', green: '#36A852', yellow: '#F2C314', orange: '#F08A24',
      pink: '#EE8FA6', brown: '#8A5A2B', violet: '#7B5BD6', warmPaper: '#F7EBD3',
    },
    chalk: {
      name: 'chalk', dark: true, glow: 0.6, paper: '#26352E', line: '#ECEDE6', soft: '#A9B2AC', guide: '#6F8F84',
      grid: null, accent1: '#8FD3F4', accent2: '#B6E388', accent3: '#F49AC1', warm: '#FFE066', warm2: '#FFB347',
      warmTint: '#3B4A2E', vignette: 'rgba(0,0,0,0.35)',
      blue: '#8FD3F4', cyan: '#9EE6E0', red: '#F49AC1', green: '#B6E388', yellow: '#FFE066', orange: '#FFB347',
      pink: '#F7B8D2', brown: '#D8B48A', violet: '#C9B6F2', warmPaper: '#2E3B2E',
    },
  };
  const DEFAULT_THEME = 'notebook';
  const PAL = Object.assign({}, THEMES[new URLSearchParams(location.search).get('pal')] || THEMES[DEFAULT_THEME]);
  G.THEMES = THEMES;
  G.PAL = PAL;
  const LP = (a, b) => (G.FMT === 'port' ? b : a);           // layout value per format: LP(landscape, portrait)
  G.LP = LP;
  // colored-pencil tint of the whole sheet: 0 = graphite, 1 = colored. Scenes set it every frame (LIB.setTint);
  // the owner prefers colored pencil throughout (05.10) — graphite only for a «sketch before it comes alive» moment.
  let T = 1;
  const setTint = k => { T = K.clamp(k); };

  // paper + grid over the whole visible world rect: the frame clear, called by camera() first in every scene
  function paperWorld(pen, cam, warm) {
    const ctx = pen.ctx;
    const base = G.CW / (G.FMT === 'port' ? 1080 : 1920);
    const hw = G.CW / 2 / (base * cam.zoom) + 40, hh = G.CH / 2 / (base * cam.zoom) + 40;
    const x0 = cam.x - hw, y0 = cam.y - hh;
    ctx.fillStyle = pen.paperPat; ctx.fillRect(x0, y0, hw * 2, hh * 2);
    if (warm > 0) { ctx.globalAlpha = 0.22 * warm; ctx.fillStyle = PAL.warmTint; ctx.fillRect(x0, y0, hw * 2, hh * 2); ctx.globalAlpha = 1; }
    if (!PAL.grid) return;
    const gs = 48;                                           // notebook grid (printed: crisp, faint)
    ctx.strokeStyle = PAL.grid; ctx.lineWidth = 1.2 / cam.zoom;
    ctx.beginPath();
    for (let x = Math.floor(x0 / gs) * gs; x < x0 + hw * 2; x += gs) { ctx.moveTo(x, y0); ctx.lineTo(x, y0 + hh * 2); }
    for (let y = Math.floor(y0 / gs) * gs; y < y0 + hh * 2; y += gs) { ctx.moveTo(x0, y); ctx.lineTo(x0 + hw * 2, y); }
    ctx.stroke();
  }
  function vignette(ctx) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const g = ctx.createRadialGradient(G.CW / 2, G.CH / 2, Math.min(G.CW, G.CH) * 0.45, G.CW / 2, G.CH / 2, Math.hypot(G.CW, G.CH) * 0.62);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, PAL.vignette);
    ctx.fillStyle = g; ctx.fillRect(0, 0, G.CW, G.CH);
  }
  // glow only for accents and only on dark paper (style DNA); on light paper it just draws
  function glow(pen, fn, color, blur = 22) {
    if (!PAL.dark || !PAL.glow) return fn();
    const ctx = pen.ctx; ctx.save(); ctx.shadowColor = color; ctx.shadowBlur = blur * PAL.glow;
    try { return fn(); } finally { ctx.restore(); }
  }

  // ---------- generic doodles ----------
  function crossOut(pen, x, y, w, h, p, id, color) {
    pen.line([[x - w / 2, y - h / 2], [x + w / 2, y + h / 2]], { w: 7, color: color || PAL.line, id: id + 'a', p: K.inv(0, 0.5, p), gaps: 0, boil: 1.4 });
    pen.line([[x + w / 2, y - h / 2], [x - w / 2, y + h / 2]], { w: 7, color: color || PAL.line, id: id + 'b', p: K.inv(0.5, 1, p), gaps: 0, boil: 1.4 });
  }
  function arrow(pen, a, b, p, id, o = {}) {
    const mx = (a[0] + b[0]) / 2 + (o.bend || 0) * (b[1] - a[1]) * 0.25, my = (a[1] + b[1]) / 2 - (o.bend || 0) * (b[0] - a[0]) * 0.25;
    const C = P.spline([a, [mx, my], b], 10);
    pen.line(C, { w: o.w || 3, color: o.color, id, p, gaps: 0 });
    if (p > 0.95) {
      const n = C.length, q = C[n - 1], r = C[n - 4], ang = Math.atan2(q[1] - r[1], q[0] - r[0]), L = o.head || 18;
      pen.line([[q[0] - Math.cos(ang - 0.5) * L, q[1] - Math.sin(ang - 0.5) * L], q, [q[0] - Math.cos(ang + 0.5) * L, q[1] - Math.sin(ang + 0.5) * L]], { w: o.w || 3, color: o.color, id: id + 'h', gaps: 0, taper: false });
    }
  }
  function sparkle(pen, x, y, r, p, id, color) {
    for (let k = 0; k < 4; k++) {
      const a = k * Math.PI / 2;
      pen.line([[x + Math.cos(a) * r * 0.35, y + Math.sin(a) * r * 0.35], [x + Math.cos(a) * r, y + Math.sin(a) * r]], { w: 3, color, id: id + k, p, gaps: 0 });
    }
  }
  function card(pen, x, y, w, h, p, id, o = {}) {
    const R = RECT(x, y, w, h, o.r == null ? 16 : o.r);
    pen.paper(R);
    if (o.fill) pen.fill(R, { color: o.fill, alpha: (o.fillAlpha || 0.35) * (o.fillK == null ? 1 : o.fillK), id: id + 'f', p: o.fillP == null ? 1 : o.fillP });
    if (o.shade !== false) {
      const sh = [[x + w, y + 14], [x + w + 12, y + 26], [x + w + 12, y + h + 12], [x + 26, y + h + 12], [x + 14, y + h], [x + w, y + h]];
      pen.hatch(P.toPath(sh), P.bbox(sh), { color: PAL.line, alpha: 0.4 * p, gap: 4.5, w: 1.2, id: id + 'sh', angle: -0.8, len: 30 });
    }
    pen.shape(R, { w: o.w || 3, id: id + 'o', p, gaps: 1, color: o.color });
    return R;
  }
  // terminal window: lines [str | {t, c}] typed one after another while prog goes 0..1
  function terminal(pen, x, y, w, h, lines, prog, id, o = {}) {
    const R = card(pen, x, y, w, h, K.inv(0, 0.25, prog), id, { r: 18, fill: o.fill || (T > 0 ? '#D3E2F6' : null), fillAlpha: o.fill ? 0.12 : 0.45 * T });
    if (prog > 0.2) {
      pen.line([[x, y + 52], [x + w, y + 52]], { w: 2.4, id: id + 'bar', p: K.inv(0.2, 0.3, prog), gaps: 0 });
      [0, 1, 2].forEach(i => { const dot = ELL(x + 30 + i * 28, y + 26, 8, 8); if (T > 0) pen.solid(dot, ['#FF5F57', '#FEBC2E', '#28C840'][i], 0.85 * T); pen.shape(dot, { w: 2.2, id: id + 'dot' + i, p: K.inv(0.22, 0.3, prog), gaps: 0, passes: 1 }); });
      if (o.title) pen.text(o.title, x + w - 26, y + 36, { size: 26, font: 'code', align: 'right', id: id + 'tt', p: K.inv(0.25, 0.35, prog), alpha: 0.75 });
    }
    const n = lines.length, size = o.size || 30, lh = o.lh || size * 1.55;
    lines.forEach((ln, i) => {
      const lp = K.inv(0.3 + i * 0.7 / n, 0.3 + (i + 1) * 0.7 / n, prog);
      if (lp <= 0) return;
      const txt = typeof ln === 'string' ? ln : ln.t, color = typeof ln === 'string' ? null : ln.c;
      pen.text(txt, x + 30, y + 96 + i * lh, { size, font: 'code', color, id: id + 'l' + i, p: lp });
    });
    return R;
  }
  function stickPerson(pen, x, y, s, id, p, typing, color) {
    const ctx = pen.ctx; ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    const hd = ELL(0, -98, 16, 17); pen.paper(hd); if (T > 0) pen.fill(hd, { color: '#F2B98C', alpha: 0.6 * T, id: id + 'hf' }); pen.shape(hd, { w: 2.6, id: id + 'hd', p, gaps: 0 });
    const bodyC = T > 0.5 ? (color || PAL.accent1) : null;
    pen.line([[0, -80], [0, -40]], { w: 3.4, id: id + 'bd', p, gaps: 0, color: bodyC });
    const k = typing ? Math.sin(pen.d * 1.7) * 6 : 0;
    pen.line([[0, -70], [26, -56 + k], [44, -52]], { w: 2.6, id: id + 'a1', p, gaps: 0, color: bodyC });
    pen.line([[0, -70], [22, -50 - k], [40, -46]], { w: 2.6, id: id + 'a2', p, gaps: 0, color: bodyC });
    pen.line([[0, -40], [-6, -10], [-2, 0]], { w: 2.6, id: id + 'l1', p, gaps: 0 });
    ctx.restore();
  }
  function calendar(pen, x, y, s, label, p, id, o = {}) {
    const ctx = pen.ctx; ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    const b = RECT(-80, -70, 160, 150, 12); pen.paper(b);
    if (o.fill) pen.fill(b, { color: o.fill, alpha: 0.35, id: id + 'f' });
    pen.shape(b, { w: 3, id: id + 'b', p, gaps: 0 });
    const topC = o.topColor || (T > 0.5 ? PAL.red : null);
    const top = RECT(-80, -70, 160, 38, 12); pen.hatch(P.toPath(top), P.bbox(top), { color: topC || PAL.line, alpha: topC ? 0.8 : 0.45, gap: 3, w: 1.4, id: id + 'top', p });
    [-40, 40].forEach((dx, i) => pen.line([[dx, -84], [dx, -56]], { w: 4, id: id + 'ring' + i, p, gaps: 0 }));
    pen.text(String(label), 0, 52, { size: o.size || 66, font: 'handb', align: 'center', id: id + 'n' + label, p: K.inv(0.4, 1, p) });
    if (o.sub) pen.text(o.sub, 0, -42, { size: 22, font: 'hand', align: 'center', id: id + 'sub', color: '#FFFFFF', p: K.inv(0.4, 1, p) });
    ctx.restore();
  }
  // frame with perforation; inner() is clipped into the frame («picture inside a picture»)
  function filmFrame(pen, x, y, w, h, p, id, inner, o = {}) {
    const ctx = pen.ctx;
    const R = RECT(x, y, w, h, 6); pen.paper(R);
    if (inner) { ctx.save(); ctx.clip(P.toPath(R)); inner(); ctx.restore(); }
    pen.shape(R, { w: o.w || 3, id: id + 'o', p, gaps: 0, color: o.color });
    if (o.holes !== false) {
      for (const yy of [y - 22, y + h + 6]) {
        const band = RECT(x, yy, w, 16, 3);
        pen.shape(band, { w: 2, id: id + 'b' + yy, p, gaps: 0, passes: 1 });
        for (let k = 0; k < Math.floor(w / 32); k++) { const hl = RECT(x + 10 + k * 32, yy + 4, 14, 8, 2); pen.solid(hl, PAL.line, 0.6 * p); }
      }
    }
    return R;
  }
  // landscape (1600x900 design box scaled into w x h): sun, hills, house, tree. Returns key points for the scene.
  function landscape(pen, x, y, w, h, o, id) {
    const ctx = pen.ctx;
    const p = o.p == null ? 1 : o.p, sx = w / 1600, sy = h / 900;
    ctx.save(); ctx.translate(x, y); ctx.scale(sx, sy);
    const lw = o.lw || 1;
    const sun = o.sun || [1220, 220], sr = 120;
    const sunP = ELL(sun[0], sun[1], sr, sr);
    pen.paper(sunP);
    if (o.sunColor) pen.fill(sunP, { color: o.sunColor, alpha: 0.9 * (o.sunFill == null ? 1 : o.sunFill), id: id + 'sunf' + o.sunColor, gap: 3.6, w: 3 });
    else pen.hatch(P.toPath(sunP), P.bbox(sunP), { color: PAL.line, alpha: 0.25, gap: 6, w: 1.4 * lw, id: id + 'sunh' });
    pen.shape(sunP, { w: 4 * lw, id: id + 'sun', p, gaps: 0, color: o.sunColor ? o.sunLine || o.sunColor : null });
    for (let k = 0; k < 12; k++) {
      const a = k / 12 * Math.PI * 2 + 0.13, r1 = sr + 26, r2 = sr + 62 + (k % 2) * 20;
      pen.line([[sun[0] + Math.cos(a) * r1, sun[1] + Math.sin(a) * r1], [sun[0] + Math.cos(a) * r2, sun[1] + Math.sin(a) * r2]], { w: 4.5 * lw, id: id + 'ray' + k, p, gaps: 0, color: o.sunColor ? o.sunLine || o.sunColor : null });
    }
    const far = P.spline([[-40, 560], [300, 430], [620, 520], [980, 410], [1330, 500], [1660, 440]], 10);
    pen.line(far, { w: 3 * lw, id: id + 'far', p, alpha: 0.7 });
    const near = P.spline([[-40, 700], [260, 600], [560, 660], [900, 590], [1240, 660], [1660, 600]], 10);
    const ground = near.concat([[1660, 950], [-40, 950]]);
    pen.paper(ground);
    if (o.color) pen.fill(ground, { color: '#7DBF4E', alpha: 0.45 * o.color, id: id + 'gf' });
    pen.hatch(P.toPath(ground), P.bbox(ground), { color: PAL.line, alpha: 0.16, gap: 7, w: 1.3 * lw, id: id + 'gh', angle: -0.4 });
    pen.line(near, { w: 4 * lw, id: id + 'near', p });
    const hx = 1020, hy = 640;
    const wall = RECT(hx, hy - 150, 190, 150, 2); pen.paper(wall);
    if (o.color) pen.fill(wall, { color: '#F2C9A0', alpha: 0.5 * o.color, id: id + 'wf' });
    pen.shape(wall, { w: 3.6 * lw, id: id + 'wall', p, gaps: 0 });
    const roof = [[hx - 24, hy - 150], [hx + 95, hy - 250], [hx + 214, hy - 150], [hx - 24, hy - 150]];
    pen.paper(roof);
    if (o.color) pen.fill(roof, { color: PAL.red, alpha: 0.6 * o.color, id: id + 'rf' });
    else pen.hatch(P.toPath(roof), P.bbox(roof), { color: PAL.line, alpha: 0.4, gap: 4, w: 1.3 * lw, id: id + 'rh' });
    pen.shape(roof, { w: 3.6 * lw, id: id + 'roof', p, gaps: 0 });
    const win = RECT(hx + 24, hy - 118, 52, 48, 3); pen.paper(win); if (o.color) pen.fill(win, { color: PAL.yellow, alpha: 0.6 * o.color, id: id + 'winf' });
    pen.shape(win, { w: 3 * lw, id: id + 'win', p, gaps: 0 });
    pen.line([[hx + 50, hy - 118], [hx + 50, hy - 70]], { w: 2.4 * lw, id: id + 'wx', p, gaps: 0, passes: 1 });
    const door = RECT(hx + 116, hy - 92, 44, 92, 3); pen.paper(door); pen.shape(door, { w: 3 * lw, id: id + 'door', p, gaps: 0 });
    const tx = 700, ty = 640;
    pen.line([[tx, ty], [tx + 4, ty - 120]], { w: 8 * lw, id: id + 'trunk', p });
    const crown = P.spline([[tx - 80, ty - 150], [tx - 60, ty - 240], [tx + 10, ty - 280], [tx + 90, ty - 230], [tx + 95, ty - 150], [tx + 10, ty - 110]], 8, true);
    pen.paper(crown);
    if (o.color) pen.fill(crown, { color: PAL.green, alpha: 0.55 * o.color, id: id + 'cf' });
    pen.hatch(P.toPath(crown), P.bbox(crown), { color: PAL.line, alpha: 0.25, gap: 5, w: 1.3 * lw, id: id + 'ch' });
    pen.shape(crown, { w: 3.6 * lw, id: id + 'crown', p });
    ctx.restore();
    return { sun: [x + sun[0] * sx, y + sun[1] * sy], sunR: sr * sx, house: [x + (hx + 95) * sx, y + (hy - 120) * sy], tree: [x + tx * sx, y + (ty - 200) * sy], hill: [x + 260 * sx, y + 600 * sy], sx, sy };
  }
  function magnifier(pen, x, y, r, ang, p, id, inner) {
    const ctx = pen.ctx;
    const lens = ELL(x, y, r, r);
    if (inner) { ctx.save(); ctx.clip(P.toPath(lens)); inner(); ctx.restore(); }
    pen.shape(lens, { w: 7, id: id + 'l', p, gaps: 0 });
    const a = [x + Math.cos(ang) * r, y + Math.sin(ang) * r], b = [x + Math.cos(ang) * (r * 2.1), y + Math.sin(ang) * (r * 2.1)];
    const hd = [[a[0] - Math.sin(ang) * 12, a[1] + Math.cos(ang) * 12], [b[0] - Math.sin(ang) * 15, b[1] + Math.cos(ang) * 15], [b[0] + Math.sin(ang) * 15, b[1] - Math.cos(ang) * 15], [a[0] + Math.sin(ang) * 12, a[1] - Math.cos(ang) * 12]];
    pen.paper(hd); pen.hatch(P.toPath(hd), P.bbox(hd), { color: PAL.line, alpha: 0.5, gap: 3, w: 1.4, id: id + 'hh' });
    pen.shape(hd, { w: 3, id: id + 'h', p, gaps: 0 });
  }
  function ruler(pen, x, y, w, secs, p, id, o = {}) {
    pen.line([[x, y], [x + w, y]], { w: 4, id: id + 'base', p, gaps: 0 });
    for (let k = 0; k <= secs; k++) {
      const xx = x + w * k / secs, q = K.inv(k / (secs + 1), (k + 1) / (secs + 1), p);
      pen.line([[xx, y - 18], [xx, y + 18]], { w: 3, id: id + 't' + k, p: q, gaps: 0 });
      pen.text(String(k) + (o.unit && k === secs ? ' ' + o.unit : ''), xx, y + 62, { size: o.size || 40, font: 'handb', align: 'center', id: id + 'n' + k, p: q, color: o.hi === k ? PAL.blue : null });
      if (o.minor) for (let m = 1; m < o.minor && k < secs; m++) { const mx = xx + w / secs * m / o.minor; pen.line([[mx, y - 8], [mx, y + 8]], { w: 1.8, id: id + 'm' + k + '_' + m, p: q, gaps: 0, passes: 1 }); }
    }
  }
  function playhead(pen, x, y0, y1, id, color) {
    pen.line([[x, y0], [x, y1]], { w: 4, id: id + 'l', gaps: 0, color: color || PAL.blue });
    const tri = [[x - 16, y0 - 22], [x + 16, y0 - 22], [x, y0], [x - 16, y0 - 22]];
    pen.solid(tri, color || PAL.blue, 0.9); pen.shape(tri, { w: 2.4, id: id + 't', gaps: 0, color: color || PAL.blue });
  }
  // audio waveform bars; o.gaps = [[u0,u1]] quiet parts, o.cut 0..1 removes them and closes ranks
  function waveform(pen, x, y, w, h, o, id) {
    const n = Math.floor(w / 9), r = K.rngOf(id, 'wave');
    const gaps = o.gaps || [];
    const amp = [];
    for (let i = 0; i < n; i++) { const u = i / n; const quiet = gaps.some(([a, b]) => u >= a && u < b); amp.push(quiet ? 0.04 : 0.25 + 0.75 * Math.pow(r(), 0.7) * (0.6 + 0.4 * Math.sin(i * 0.37))); }
    const cut = o.cut || 0;
    let removed = 0; const xs = [];
    for (let i = 0; i < n; i++) {
      const u = i / n; const quiet = gaps.some(([a, b]) => u >= a && u < b);
      xs.push(x + (i - removed * cut) * 9);
      if (quiet) removed++;
    }
    const path = new Path2D();
    for (let i = 0; i < n; i++) {
      const u = i / n; const quiet = gaps.some(([a, b]) => u >= a && u < b);
      if (quiet && cut > 0.5) continue;
      const a = amp[i] * h / 2 * (quiet ? 1 - cut : 1);
      path.moveTo(xs[i], y - a); path.lineTo(xs[i], y + a);
    }
    const ctx = pen.ctx;
    ctx.strokeStyle = pen.pattern(o.color || PAL.line); ctx.lineWidth = 4.2; ctx.lineCap = 'round'; ctx.globalAlpha = (o.p == null ? 1 : o.p) * 0.9 * (pen.alphaMul == null ? 1 : pen.alphaMul);
    const j = K.rngOf(id, pen.d)(); ctx.save(); ctx.translate((j - 0.5) * 1.2, 0); ctx.stroke(path); ctx.restore(); ctx.globalAlpha = 1;
    return xs;
  }
  // laptop; screen(x, y, w, h) draws into the clipped screen (a place for a dive into the next scene)
  function laptop(pen, x, y, s, open, p, id, screen, col) {
    const ctx = pen.ctx; ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    const base = [[-120, 0], [120, 0], [140, 18], [-140, 18], [-120, 0]];
    pen.paper(base); pen.hatch(P.toPath(base), P.bbox(base), { color: PAL.line, alpha: 0.35, gap: 3.5, w: 1.2, id: id + 'bh' }); pen.shape(base, { w: 2.6, id: id + 'b', p, gaps: 0 });
    const h = 150 * open;
    if (open > 0.05) {
      const lid = RECT(-112, -h, 224, h, 8); pen.paper(lid);
      if (col > 0) pen.fill(lid, { color: '#DCE8F7', alpha: 0.6 * col, id: id + 'lf' });
      if (screen && open > 0.6) { ctx.save(); ctx.clip(P.toPath(RECT(-100, -h + 12, 200, h - 24, 4))); screen(-100, -h + 12, 200, h - 24); ctx.restore(); }
      pen.shape(lid, { w: 2.8, id: id + 'lid', p, gaps: 0 });
    }
    ctx.restore();
  }

  G.LIB = { setTint, paperWorld, vignette, glow, crossOut, arrow, sparkle, card, terminal, stickPerson, calendar, filmFrame, landscape, magnifier, ruler, playhead, waveform, laptop };
})(window);
