// hero_egg.js — the skill author's mascot (copy of <эталон>/engine/hero.js), the full-size example of a hero.
// Same API as engine/hero.js: HERO.draw(pen, cfg). To use the mascot, load ../engine/hero_egg.js instead of
// ../engine/hero.js in pencil/index.html (and in gloss/index.html). Extra cfg here: shape 'grin', fills, sleep, sweat,
// scroll/spatula/laurel/airpods, scrollText, legs, brow, lean, dir. Note: cfg.pan is unused; hand points are not returned.
// hero.js — the skill author's mascot: fried-egg Socrates in a toga, nerd glasses, laurel, scroll «# prompt», spatula.
// Proportions follow the vector sticker handcraft_egg.svg (512 box);
// local origin = between the feet on the ground (SVG x 256, y 430). At s = 1 the hero is ~340 px tall.
(function (G) {
  'use strict';
  const K = G.K, P = G.PEN;
  const OX = 256, OY = 430;
  const L = (x, y) => [x - OX, y - OY];
  const S = (d, step = 4) => P.svgPts(d, step).map(p => L(p[0], p[1]));

  const D_OUTER = 'M 150 200 Q 130 175 145 145 Q 158 122 188 110 Q 215 100 245 105 Q 275 100 305 108 Q 332 117 350 138 Q 365 158 360 188 Q 372 215 365 240 Q 372 280 360 320 Q 345 360 320 385 Q 290 405 256 405 Q 222 405 195 388 Q 168 368 155 335 Q 142 305 148 270 Q 138 240 150 200 Z';
  const D_INNER = 'M 158 205 Q 142 182 158 156 Q 172 138 196 128 Q 220 120 246 124 Q 273 120 298 128 Q 322 138 338 156 Q 352 175 348 198 Q 358 220 352 246 Q 358 280 348 314 Q 335 350 312 374 Q 287 392 256 392 Q 224 392 200 376 Q 178 358 168 330 Q 156 302 162 272 Q 152 238 158 205 Z';
  const D_TOGA = 'M 168 296 Q 178 290 200 294 Q 220 296 240 294 Q 258 292 278 294 Q 300 297 322 295 Q 342 290 350 298 Q 354 320 350 348 Q 346 372 338 386 Q 320 398 290 394 Q 256 395 225 394 Q 195 396 178 386 Q 168 370 164 348 Q 162 322 168 296 Z';
  const D_TRIM = 'M 170 300 Q 200 296 240 298 Q 270 296 322 298 Q 342 296 350 304';
  // the toga drape crosses the chest diagonally (as on the stickers): sash from the right shoulder down to the left hip
  const D_SASH = 'M 300 296 Q 270 330 236 350 Q 205 368 176 380';

  const COL = {
    crisp: '#C98A3C', crispDark: '#8A5A22', white: '#F2E6C9', yolk: '#F39A1E', yolkHi: '#FFD45A', pupil: '#1E1A16',
    toga: '#E9E1D0', gold: '#C9A227', goldDark: '#8A6F1C', badge: '#2D40D8', blush: '#F48FA8', leaf: '#7FA236',
    leafGold: '#C9A227', olive: '#1B1F4A', wood: '#7A4A22', metal: '#8F959C', parch: '#E6CC8E', airpod: '#F4F4F4',
    tongue: '#D9606E', mouth: '#3A1E16', cyan: '#1FA2D8',
  };

  function rot(p, c, a) { const s = Math.sin(a), co = Math.cos(a), x = p[0] - c[0], y = p[1] - c[1]; return [c[0] + x * co - y * s, c[1] + x * s + y * co]; }
  function offsetPoly(C, hw) {           // centerline -> closed tube polygon
    const Lft = [], Rgt = [];
    for (let i = 0; i < C.length; i++) {
      const a = C[Math.max(0, i - 1)], b = C[Math.min(C.length - 1, i + 1)];
      let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
      const w = typeof hw === 'function' ? hw(i / (C.length - 1)) : hw;
      Lft.push([C[i][0] - ty * w, C[i][1] + tx * w]); Rgt.push([C[i][0] + ty * w, C[i][1] - tx * w]);
    }
    return Lft.concat(Rgt.reverse());
  }

  // default pose
  const DEF = {
    x: 0, y: 0, s: 1, dir: 1, squash: 0, lean: 0, look: [0, 0], blink: 0, brow: 0, mouth: 0, shape: 'smile', smile: 1,
    armL: { sh: -2.35, el: 0.35 }, armR: { sh: -0.25, el: -0.3 }, scroll: true, spatula: true, spatAng: 0.1,
    laurel: true, airpods: true, legs: [0, 0], color: 0, reveal: 1, id: 'hero', scrollText: ['# prompt', '$ AI', '> hello'],
    pan: false, sweat: 0,
  };

  function draw(pen, cfg0) {
    const c = Object.assign({}, DEF, cfg0);
    c.armL = Object.assign({}, DEF.armL, cfg0.armL); c.armR = Object.assign({}, DEF.armR, cfg0.armR);
    const ctx = pen.ctx, id = c.id, col = K.clamp(c.color), g = pen.pal.line;
    const rv = (a, b) => K.inv(a, b, c.reveal);            // draw-on window of a part
    // tone fill: graphite tone hatch fades out as colored pencil fades in
    const fp = c.fills == null ? 1 : c.fills;
    const tone = (Pts, color, greyAlpha, o = {}) => {
      const path = P.toPath(Pts), bb = P.bbox(Pts);
      const p = Math.min(o.p == null ? 1 : o.p, fp);
      if (greyAlpha > 0 && col < 1) pen.hatch(path, bb, Object.assign({ color: g, alpha: greyAlpha * (1 - col), gap: o.gap || 5.5, w: 1.3, len: 50, id: id + (o.k || 't') + 'g', p }, o.grey || {}));
      if (col > 0 && color) pen.hatch(path, bb, { color, alpha: (o.alpha || 0.7) * col, gap: o.cgap || 3.6, w: o.cw || 2.4, len: 55, cross: true, crossAngle: 0.55, id: id + (o.k || 't') + 'c', angle: o.angle == null ? -0.9 : o.angle, p });
      return path;
    };

    ctx.save();
    ctx.translate(c.x, c.y);
    ctx.scale(c.s * c.dir, c.s);
    ctx.rotate(c.lean);
    ctx.scale(1 + c.squash * 0.55, 1 - c.squash);

    // ground shadow
    const sh = P.ellipse(0, 4, 92, 13);
    pen.hatch(P.toPath(sh), P.bbox(sh), { p: fp, color: g, alpha: 0.35 * rv(0.85, 1), gap: 5, w: 1.2, angle: -0.3, id: id + 'shadow', len: 40 });

    // legs + feet (legs: [lift left, lift right] in units)
    if (rv(0.55, 0.7) > 0) {
      for (const side of [-1, 1]) {
        const lift = side < 0 ? c.legs[0] : c.legs[1];
        const top = [side * 30, -34], foot = [side * 36, -6 - lift];
        const leg = offsetPoly([top, [side * 33, -20 - lift * 0.5], foot], 6.5);
        pen.paper(leg); tone(leg, COL.white, 0.12, { k: 'leg' + side, p: rv(0.6, 0.75) });
        pen.shape(leg, { w: 2.2, id: id + 'leg' + side, p: rv(0.55, 0.7), gaps: 0 });
        const f = P.ellipse(foot[0] + side * 6, foot[1] + 2, 17, 8);
        pen.paper(f); tone(f, COL.crisp, 0.2, { k: 'foot' + side, p: rv(0.6, 0.75) });
        pen.shape(f, { w: 2.4, id: id + 'foot' + side, p: rv(0.55, 0.7), gaps: 0 });
      }
    }

    // body: crisp ring, egg white, shading
    const outer = S(D_OUTER, 5), inner = S(D_INNER, 5);
    const pOuter = P.toPath(outer);
    pen.paper(pOuter);
    tone(outer, COL.crisp, 0.32, { k: 'crisp', gap: 4.5, p: rv(0.3, 0.5), cgap: 3.2 });
    const pInner = pen.paper(inner);
    // egg-white shading on the right and bottom (light from top-left)
    ctx.save(); ctx.clip(pInner);
    if (col > 0) pen.hatch(pInner, P.bbox(inner), { color: COL.white, alpha: 0.32 * col, gap: 5, w: 2, id: id + 'white', len: 60 });
    // shadow crescent on the right/bottom: inside the white, outside a copy of it moved up-left
    const moved = inner.map(([x, y]) => [x * 0.97 - 26, y * 0.98 - 16]);
    const cres = new Path2D(); cres.rect(-400, -500, 800, 600); cres.addPath(P.toPath(moved));
    ctx.clip(cres, 'evenodd');
    pen.hatch(pInner, P.bbox(inner), { color: col > 0.5 ? '#B89A62' : g, alpha: 0.3, gap: 5, w: 1.3, id: id + 'shade', p: Math.min(rv(0.45, 0.6), fp), len: 40, angle: -1.1 });
    ctx.restore();
    pen.shape(outer, { w: 3.4, color: col > 0.5 ? COL.crispDark : g, id: id + 'outer', p: rv(0, 0.3), gaps: 1 });
    pen.shape(inner, { w: 1.6, alpha: 0.55, id: id + 'inner', p: rv(0.12, 0.35), gaps: 2, passes: 1 });
    for (const [bx, by, br] of [[148, 220, 4], [365, 200, 5], [144, 280, 5], [362, 290, 4]]) {
      const b = P.ellipse(...L(bx, by), br, br);
      pen.shape(b, { w: 1.6, id: id + 'bump' + bx, p: rv(0.25, 0.35), gaps: 0, passes: 1 });
    }

    // toga with diagonal drape, gold trim, greek key, folds
    const toga = S(D_TOGA, 5);
    pen.paper(toga);
    tone(toga, COL.toga, 0.1, { k: 'toga', p: rv(0.5, 0.65), alpha: 0.45 });
    const togaShade = P.ellipse(...L(318, 360), 60, 50);
    ctx.save(); ctx.clip(P.toPath(toga));
    pen.hatch(P.toPath(togaShade), P.bbox(togaShade), { color: g, alpha: 0.18, gap: 6, w: 1.1, id: id + 'togash', p: Math.min(rv(0.5, 0.65), fp), len: 40 });
    ctx.restore();
    pen.shape(toga, { w: 2.8, id: id + 'toga', p: rv(0.32, 0.5), gaps: 1 });
    pen.line(S(D_SASH, 4), { w: 2.2, id: id + 'sash', p: rv(0.4, 0.52), alpha: 0.75 });
    pen.line(S(D_TRIM, 4), { w: 3.2, color: col > 0.3 ? COL.gold : g, alpha: col > 0.3 ? 0.95 : 0.6, id: id + 'trim', p: rv(0.42, 0.55) });
    for (let k = 0; k < 8; k++) {
      const x0 = 180 + k * 20;
      const key = [L(x0, 384), L(x0 + 6, 384), L(x0 + 6, 378), L(x0 + 3, 378), L(x0 + 3, 382), L(x0 + 7, 382)];
      pen.line(key, { w: 1.5, color: col > 0.3 ? COL.gold : g, alpha: 0.75, id: id + 'gk' + k, p: rv(0.5 + k * 0.01, 0.56 + k * 0.01), passes: 1, gaps: 0, taper: false });
    }
    for (const [x0, x1] of [[200, 200], [282, 284], [322, 320]]) pen.line([L(x0, 312), L(x0 + 5, 345), L(x1, 380)], { w: 1.3, alpha: 0.35, id: id + 'fold' + x0, p: rv(0.52, 0.6), passes: 1 });

    // H badge
    const badge = P.rect(...L(239, 318), 34, 34, 8);
    pen.paper(badge);
    tone(badge, COL.badge, 0.55, { k: 'badge', gap: 2.8, cgap: 2.2, alpha: 0.95, p: rv(0.55, 0.65) });
    pen.shape(badge, { w: 2.2, id: id + 'badge', p: rv(0.52, 0.6), gaps: 0 });
    const hc = '#F7F1E3';
    pen.line([L(247, 326), L(247, 345)], { w: 3, color: hc, alpha: rv(0.62, 0.66), id: id + 'h1', gaps: 0, passes: 1 });
    pen.line([L(265, 326), L(265, 345)], { w: 3, color: hc, alpha: rv(0.62, 0.66), id: id + 'h2', gaps: 0, passes: 1 });
    pen.line([L(247, 336), L(265, 336)], { w: 3, color: hc, alpha: rv(0.62, 0.66), id: id + 'h3', gaps: 0, passes: 1 });

    // face: blush, brows, mouth
    if (col > 0) for (const bx of [180, 332]) { const b = P.ellipse(...L(bx, 250), 15, 8); pen.hatch(P.toPath(b), P.bbox(b), { color: COL.blush, alpha: 0.55 * col, gap: 2.6, w: 2, id: id + 'blush' + bx, angle: -0.4, len: 20 }); }
    const by = -6 * c.brow;
    pen.line([L(197, 168 + by + 2), L(213, 161 + by - (c.brow > 0.5 ? 3 : 0)), L(229, 167 + by)], { w: 3.4, id: id + 'browL', p: rv(0.68, 0.74), gaps: 0 });
    pen.line([L(283, 167 + by), L(299, 161 + by - (c.brow > 0.5 ? 3 : 0)), L(315, 168 + by + 2)], { w: 3.4, id: id + 'browR', p: rv(0.68, 0.74), gaps: 0 });
    drawMouth(pen, c, rv(0.74, 0.8), col);

    // eyes = yolks (behind the glasses)
    for (const [ex, side] of [[213, 'L'], [299, 'R']]) {
      const e = L(ex, 195);
      const bl = K.clamp(c.blink);
      const ry = 26 * (1 - bl * 0.92);
      const yolk = P.ellipse(e[0], e[1], 26, ry);
      pen.paper(yolk);
      tone(yolk, COL.yolk, 0.38, { k: 'yolk' + side, gap: 3.6, cgap: 2.4, alpha: 0.9, p: rv(0.62, 0.72) });
      if (col > 0) { const hi = P.ellipse(e[0] - 8, e[1] - 9 * (ry / 26), 9, 6 * (ry / 26), -0.4); pen.hatch(P.toPath(hi), P.bbox(hi), { color: COL.yolkHi, alpha: 0.85 * col, gap: 2, w: 2.2, id: id + 'yhi' + side, len: 14 }); }
      pen.shape(yolk, { w: 2.4, id: id + 'yolk' + side, p: rv(0.6, 0.68), gaps: 0, color: col > 0.5 ? '#9A4A0A' : g });
      if (bl < 0.75) {
        const lx = K.clamp(c.look[0], -1, 1) * 9, ly = K.clamp(c.look[1], -1, 1) * 8 * (ry / 26);
        const pu = P.ellipse(e[0] + lx, e[1] + ly, 9, 9 * (ry / 26));
        pen.solid(pu, COL.pupil, rv(0.7, 0.74));
        pen.shape(pu, { w: 1.4, id: id + 'pu' + side, gaps: 0, passes: 1, alpha: rv(0.7, 0.74) });
        const sp = P.ellipse(e[0] + lx - 3, e[1] + ly - 3 * (ry / 26), 2.8, 2.8 * (ry / 26));
        ctx.globalAlpha = rv(0.72, 0.76); ctx.fillStyle = '#FFFDF6'; ctx.fill(P.toPath(sp)); ctx.globalAlpha = 1;
      } else {
        pen.line([[e[0] - 22, e[1]], [e[0], e[1] + 5], [e[0] + 22, e[1]]], { w: 2.6, id: id + 'shut' + side, gaps: 0 });
      }
    }
    // glasses
    for (const ex of [213, 299]) {
      const fr = P.ellipse(...L(ex, 195), 32, 32);
      pen.shape(fr, { w: 5.2, color: '#1E1E22', id: id + 'gl' + ex, p: rv(0.76, 0.84), gaps: 0 });
      const rf = [L(ex - 18, 176), L(ex - 10, 170)];
      pen.line(rf, { w: 2.2, color: '#FFFFFF', alpha: 0.75 * rv(0.84, 0.86), id: id + 'rf' + ex, gaps: 0, passes: 1 });
    }
    pen.line([L(245, 191), L(256, 187), L(267, 191)], { w: 4.5, color: '#1E1E22', id: id + 'bridge', p: rv(0.82, 0.86), gaps: 0 });
    pen.line([L(181, 188), L(166, 183)], { w: 3.4, color: '#1E1E22', id: id + 'tL', p: rv(0.84, 0.86), gaps: 0 });
    pen.line([L(331, 188), L(346, 183)], { w: 3.4, color: '#1E1E22', id: id + 'tR', p: rv(0.84, 0.86), gaps: 0 });
    // airpods
    if (c.airpods) for (const ax of [156, 356]) {
      const bud = P.ellipse(...L(ax, 200), 9, 11), stem = P.rect(...L(ax - 3, 206), 6, 15, 3);
      pen.paper(bud); pen.paper(stem);
      pen.shape(bud, { w: 1.8, id: id + 'ap' + ax, p: rv(0.84, 0.88), gaps: 0, passes: 1 });
      pen.shape(stem, { w: 1.6, id: id + 'aps' + ax, p: rv(0.84, 0.88), gaps: 0, passes: 1 });
    }
    // laurel
    if (c.laurel) drawLaurel(pen, c, rv(0.86, 0.95), col);

    // arms + props
    drawArm(pen, c, 'R', rv(0.88, 0.96), col, tone);
    drawArm(pen, c, 'L', rv(0.88, 0.96), col, tone);
    if (c.sleep > 0) {
      for (let k = 0; k < 3; k++) {
        const ph = ((pen.d / 12 * 0.5 + k / 3) % 1);
        pen.text('z', 120 + k * 26 + ph * 30, -330 - ph * 120 - k * 30, { size: 26 + k * 10, font: 'handb', id: id + 'z' + k, alpha: c.sleep * Math.sin(ph * Math.PI) });
      }
    }
    if (c.sweat > 0) {
      const sw = [L(345, 150), L(352, 162), L(347, 170), L(340, 162), L(345, 150)];
      pen.paper(sw); if (col > 0) pen.fill(sw, { color: COL.cyan, alpha: 0.6 * col * c.sweat, id: id + 'sw' }); pen.shape(sw, { w: 1.8, alpha: c.sweat, id: id + 'swo', gaps: 0 });
    }
    ctx.restore();
  }

  function drawMouth(pen, c, p, col) {
    const id = c.id, m = K.clamp(c.mouth);
    const cx = 0, cy = 268 - OY, w = c.shape === 'grin' ? 34 : 26;
    if (c.shape === 'o') {
      const o = P.ellipse(cx, cy + 4, 9 + m * 3, 10 + m * 6);
      pen.solid(o, COL.mouth, 0.9 * p); pen.shape(o, { w: 2.4, id: id + 'mo', p, gaps: 0 });
      return;
    }
    if (m < 0.08 && c.shape !== 'grin') {
      const lift = c.shape === 'flat' ? 2 : 12 * c.smile;
      pen.line([[cx - w, cy], [cx, cy + lift], [cx + w, cy]].length ? P.spline([[cx - w, cy - 1], [cx, cy + lift], [cx + w, cy - 1]], 6) : [], { w: 3, id: id + 'smile', p, gaps: 0 });
      return;
    }
    const open = 4 + m * 20;
    const top = P.spline([[cx - w, cy - 2], [cx, cy + 3 * c.smile], [cx + w, cy - 2]], 6);
    const bot = P.spline([[cx + w, cy - 2], [cx, cy + open + 8 * c.smile], [cx - w, cy - 2]], 6);
    const shape = top.concat(bot);
    pen.solid(shape, COL.mouth, 0.92 * p);
    if (col > 0 && m > 0.25) { const tg = P.ellipse(cx, cy + open * 0.75, w * 0.5, open * 0.3); pen.solid(tg, COL.tongue, 0.85 * col * p); }
    pen.shape(shape, { w: 2.6, id: id + 'mouth', p, gaps: 0 });
  }

  // pointed leaf (lens shape) centred at (qx,qy), half-length len, half-width wd, angle a
  function leafPts(qx, qy, len, wd, a) {
    const ca = Math.cos(a), sa = Math.sin(a), out = [];
    const pt = (u, side) => { const x = u * len, y = side * wd * Math.sqrt(Math.max(0, 1 - u * u)) * (1 - 0.25 * u); return [qx + x * ca - y * sa, qy + x * sa + y * ca]; };
    for (let k = 0; k <= 16; k++) out.push(pt(k / 8 - 1, -1));
    for (let k = 15; k >= 1; k--) out.push(pt(k / 8 - 1, 1));
    return out;
  }

  function drawLaurel(pen, c, p, col) {
    if (p <= 0) return;
    const id = c.id;
    pen.line(S('M 168 138 Q 256 88 344 138', 4), { w: 2, color: col > 0.3 ? COL.goldDark : pen.pal.line, alpha: 0.7, id: id + 'larc', p });
    const leaves = [[176, 148, 6, -40], [184, 138, 7, -35], [194, 128, 7, -28], [206, 118, 8, -20], [219, 110, 8, -12], [232, 104, 8, -6], [246, 100, 8, -2]];
    leaves.forEach(([x, y, rx, a], i) => {
      for (const side of [1, -1]) {
        const lx = side > 0 ? x : 512 - x, la = (side > 0 ? a : -a) * Math.PI / 180;
        // pointed leaf (lens shape) instead of an ellipse
        const lf = leafPts(...L(lx, y), rx * 1.4, 4.6, la);
        const kk = K.inv(i / 7, i / 7 + 0.3, p);
        if (kk <= 0) continue;
        pen.paper(lf);
        if (col > 0) pen.hatch(P.toPath(lf), P.bbox(lf), { color: i % 2 ? COL.leafGold : COL.leaf, alpha: 0.9 * col, gap: 2, w: 2, id: id + 'lf' + i + side, len: 14 });
        else pen.hatch(P.toPath(lf), P.bbox(lf), { color: pen.pal.line, alpha: 0.3, gap: 3, w: 1.1, id: id + 'lfg' + i + side, len: 12 });
        pen.shape(lf, { w: 1.6, id: id + 'lfo' + i + side, p: kk, gaps: 0, passes: 1 });
      }
    });
    const ol = P.ellipse(...L(256, 96), 5.5, 5.5);
    pen.solid(ol, col > 0.3 ? COL.olive : '#2A2A30', p);
  }

  function drawArm(pen, c, side, p, col, tone) {
    if (p <= 0) return;
    const id = c.id + 'arm' + side, a = side === 'L' ? c.armL : c.armR;
    const shoulder = side === 'L' ? L(170, 318) : L(340, 310);
    const l1 = 46, l2 = 42;
    const elbow = [shoulder[0] + Math.cos(a.sh) * l1, shoulder[1] + Math.sin(a.sh) * l1];
    const ang2 = a.sh + a.el;
    const hand = [elbow[0] + Math.cos(ang2) * l2, elbow[1] + Math.sin(ang2) * l2];
    const C = P.spline([shoulder, elbow, hand], 6);
    // props behind the hand
    if (side === 'L' && c.scroll) drawScroll(pen, c, hand, ang2, p, col);
    if (side === 'R' && c.spatula) drawSpatula(pen, c, hand, p, col);
    const tube = offsetPoly(C, u => 6.2 - u * 1.2);
    pen.paper(tube);
    tone(tube, COL.crisp, 0.18, { k: 'arm' + side, p, cgap: 3, alpha: 0.6 });
    pen.shape(tube, { w: 2.2, id, p, gaps: 0 });
    const hd = P.ellipse(hand[0], hand[1], 9.5, 9);
    pen.paper(hd); tone(hd, COL.crisp, 0.2, { k: 'hand' + side, p, cgap: 3, alpha: 0.6 });
    pen.shape(hd, { w: 2.2, id: id + 'h', p, gaps: 0 });
    c['_hand' + side] = hand;
  }

  function drawScroll(pen, c, hand, ang, p, col) {
    const ctx = pen.ctx, id = c.id + 'scroll';
    ctx.save(); ctx.translate(hand[0], hand[1]); ctx.rotate(-0.12);
    const W = 78, H = 88, x0 = -W + 6, y0 = -H / 2 - 4;   // the hand grips the right edge of the scroll
    const body = P.rect(x0, y0, W, H, 3);
    pen.paper(body);
    if (col > 0) pen.fill(body, { color: COL.parch, alpha: 0.55 * col, id: id + 'f' });
    else pen.hatch(P.toPath(body), P.bbox(body), { color: pen.pal.line, alpha: 0.12, gap: 6, w: 1.1, id: id + 'g' });
    pen.shape(body, { w: 2.2, id: id + 'o', p, gaps: 0 });
    for (const yy of [y0, y0 + H]) {
      const roll = P.rect(x0 - 5, yy - 6, W + 10, 12, 6);
      pen.paper(roll); if (col > 0) pen.fill(roll, { color: '#D6B66E', alpha: 0.7 * col, id: id + 'r' + yy });
      pen.shape(roll, { w: 2.2, id: id + 'ro' + yy, p, gaps: 0 });
    }
    c.scrollText.forEach((ln, i) => {
      pen.text(ln, x0 + 8, y0 + 22 + i * 18, { size: 13, font: 'codeb', color: i === 2 && col > 0.3 ? COL.cyan : '#3A2A18', id: id + 't' + i, p: K.inv(0.6, 1, p) });
    });
    ctx.restore();
  }

  function drawSpatula(pen, c, hand, p, col) {
    const ctx = pen.ctx, id = c.id + 'spat';
    ctx.save(); ctx.translate(hand[0], hand[1]); ctx.rotate(c.spatAng);
    const handle = P.rect(-5, -96, 10, 104, 4);
    pen.paper(handle);
    if (col > 0) pen.fill(handle, { color: COL.wood, alpha: 0.8 * col, id: id + 'w', angle: 1.4 }); else pen.hatch(P.toPath(handle), P.bbox(handle), { color: pen.pal.line, alpha: 0.35, gap: 4, w: 1.1, id: id + 'wg', angle: 1.4 });
    pen.shape(handle, { w: 2, id: id + 'ho', p, gaps: 0 });
    const head = [[-24, -96], [24, -96], [27, -142], [-27, -142], [-24, -96]];
    pen.paper(head);
    if (col > 0) pen.fill(head, { color: COL.metal, alpha: 0.55 * col, id: id + 'm' }); else pen.hatch(P.toPath(head), P.bbox(head), { color: pen.pal.line, alpha: 0.18, gap: 5, w: 1.1, id: id + 'mg' });
    pen.shape(head, { w: 2.4, id: id + 'mo', p, gaps: 0 });
    for (const sx of [-12, 0, 12]) pen.line([[sx, -104], [sx * 1.05, -134]], { w: 1.8, alpha: 0.8, id: id + 'sl' + sx, gaps: 0, passes: 1, p });
    c._spatTip = [hand[0] + Math.sin(c.spatAng) * 120, hand[1] - Math.cos(c.spatAng) * 120];
    ctx.restore();
  }

  G.HERO = { draw, COL, DEF, L };
})(window);
