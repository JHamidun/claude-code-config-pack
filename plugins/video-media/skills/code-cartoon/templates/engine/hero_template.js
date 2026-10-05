// hero_template.js — a small generic hero drawn with the PEN API (copied to engine/hero.js by new_project.py).
//   const a = HERO.draw(pen, cfg)  ->  anchor points in the caller's coordinates: { handL, handR, mouth, eyeL, eyeR, top }
// cfg (all optional, see DEF): x, y, s, dir (±1 mirror), lean (rad), squash (+ flattens, - stretches), look [-1..1, -1..1],
//   blink 0..1, brow -1..1, mouth 0..1 (feed K.mouthAt(t)), shape 'smile'|'o'|'flat', color 0..1 (graphite -> coloured
//   pencil), reveal 0..1 (draw-on), armL / armR {sh, el} (shoulder / elbow angle, rad), legs [liftL, liftR], id (seed prefix).
//
// How to build your own hero (the full-size example is engine/hero_egg.js — the skill author's mascot):
//  1. Local coordinates: origin between the feet on the ground, y down; at s = 1 the hero is ~330 units tall.
//     Draw the character once as SVG in a 512 box (or trace a sticker), keep the path strings as constants and map
//     SVG -> local with L(x, y) = [x - OX, y - OY]; sample paths with PEN.svgPts(d, step) (cached), like hero_egg.js.
//  2. Draw back to front. Every part: pen.paper(shape) (hides what is behind and keeps the paper texture) ->
//     tone(shape, colour, greyAlpha) (graphite hatch fades out while coloured-pencil cross-hatch fades in with cfg.color)
//     -> pen.shape(outline, { id: id + 'part', p: rv(a, b) }). Tone is hatching, never a flat fill.
//  3. Ids are boil seeds: id + part name, stable for the whole film. Two heroes on screen at once need different cfg.id,
//     otherwise both boil identically and read as a copy-paste.
//  4. cfg.reveal draws the hero on; every part has its own window rv(a, b), so the drawing builds up like a sketch.
//  5. Limbs are 2-segment chains: angles in radians in canvas axes (0 = right, +PI/2 = down). Props go at the hand.
//     Return the points scenes need (hands, mouth) in the caller's coordinates instead of writing them on cfg.
//  6. Check the hero sheet before animating: python render/still.py pencil/index.html st/sheet 0.5 land "scenes=test_doodles.js"
(function (G) {
  'use strict';
  const K = G.K, P = G.PEN;

  const COL = {
    body: '#7CC3EA', bodyLine: '#2A5F8F', belly: '#EAF6FB', cheek: '#EE8FA6', shoe: '#F08A24', sprout: '#4FA83D',
    eye: '#FFFFFF', pupil: '#1E1A16', mouth: '#3A1E16', tongue: '#E06C7A',
  };
  const DEF = {
    x: 0, y: 0, s: 1, dir: 1, lean: 0, squash: 0, look: [0, 0], blink: 0, brow: 0, mouth: 0, shape: 'smile',
    color: 0, reveal: 1, armL: { sh: 2.2, el: -0.35 }, armR: { sh: 0.94, el: 0.35 }, legs: [0, 0], id: 'hero',
  };
  // body outline: an egg-ish blob through hand-placed points (a perfect circle reads as vector art)
  const BODY = P.spline([[0, -284], [62, -268], [104, -222], [114, -160], [100, -98], [58, -56], [0, -44], [-60, -56],
    [-102, -100], [-112, -164], [-100, -226], [-58, -268]], 7, true);
  const BELLY = P.ellipse(4, -118, 58, 46, 0.05);
  const SHADE = BODY.map(([x, y]) => [x * 0.96 - 24, y * 0.98 - 14]);   // body shifted up-left: crescent shadow mask

  function chainPts(base, a, l1, l2) {           // shoulder -> elbow -> hand
    const el = [base[0] + Math.cos(a.sh) * l1, base[1] + Math.sin(a.sh) * l1];
    const ang = a.sh + a.el;
    return [base, el, [el[0] + Math.cos(ang) * l2, el[1] + Math.sin(ang) * l2]];
  }
  function tube(C, w0, w1) {                        // centerline -> closed tube polygon, width w0 -> w1
    const Lf = [], Rt = [];
    for (let i = 0; i < C.length; i++) {
      const a = C[Math.max(0, i - 1)], b = C[Math.min(C.length - 1, i + 1)];
      let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
      const w = K.lerp(w0, w1, i / (C.length - 1));
      Lf.push([C[i][0] - ty * w, C[i][1] + tx * w]); Rt.push([C[i][0] + ty * w, C[i][1] - tx * w]);
    }
    return Lf.concat(Rt.reverse());
  }

  function draw(pen, cfg0 = {}) {
    const c = Object.assign({}, DEF, cfg0);
    c.armL = Object.assign({}, DEF.armL, cfg0.armL); c.armR = Object.assign({}, DEF.armR, cfg0.armR);
    const ctx = pen.ctx, id = c.id, col = K.clamp(c.color), g = pen.pal.line;
    const rv = (a, b) => K.inv(a, b, c.reveal);                // draw-on window of one part
    const tone = (Pts, color, greyAlpha, o = {}) => {          // graphite tone -> coloured pencil
      const path = P.toPath(Pts), bb = P.bbox(Pts), p = o.p == null ? 1 : o.p;
      if (greyAlpha > 0 && col < 1) pen.hatch(path, bb, { color: g, alpha: greyAlpha * (1 - col), gap: o.gap || 5.5, w: 1.3, len: 50, id: id + o.k + 'g', p });
      if (col > 0 && color) pen.hatch(path, bb, { color, alpha: (o.alpha || 0.7) * col, gap: o.cgap || 3.6, w: 2.4, len: 55, cross: true, crossAngle: 0.55, id: id + o.k + 'c', angle: o.angle == null ? -0.9 : o.angle, p });
      return path;
    };
    // local -> caller coordinates (same order as the ctx calls below)
    const ca = Math.cos(c.lean), sa = Math.sin(c.lean), qx = 1 + c.squash * 0.55, qy = 1 - c.squash;
    const toCaller = ([px, py]) => { const x = px * qx, y = py * qy; return [c.x + (x * ca - y * sa) * c.s * c.dir, c.y + (x * sa + y * ca) * c.s]; };

    ctx.save();
    ctx.translate(c.x, c.y);
    ctx.scale(c.s * c.dir, c.s);
    ctx.rotate(c.lean);
    ctx.scale(qx, qy);

    // ground shadow
    const sh = P.ellipse(0, 4, 100, 14);
    pen.hatch(P.toPath(sh), P.bbox(sh), { color: g, alpha: (pen.pal.dark ? 0.16 : 0.35) * rv(0.85, 1), gap: 5, w: 1.2, angle: -0.3, id: id + 'shadow', len: 40 });

    // legs + shoes
    for (const side of [-1, 1]) {
      const lift = side < 0 ? c.legs[0] : c.legs[1];
      const leg = tube([[side * 36, -60], [side * 40, -32 - lift * 0.5], [side * 44, -10 - lift]], 7, 6.5);
      pen.paper(leg); tone(leg, COL.body, 0.12, { k: 'leg' + side, p: rv(0.6, 0.75) });
      pen.shape(leg, { w: 2.2, id: id + 'leg' + side, p: rv(0.5, 0.65), gaps: 0 });
      const shoe = P.ellipse(side * 52, -7 - lift, 22, 10, side * 0.08);
      pen.paper(shoe); tone(shoe, COL.shoe, 0.3, { k: 'shoe' + side, p: rv(0.6, 0.75), alpha: 0.85 });
      pen.shape(shoe, { w: 2.4, id: id + 'shoe' + side, p: rv(0.5, 0.65), gaps: 0 });
    }

    // body: tone, belly, then the shading. Light comes from the top left: on light paper hatch the shadow crescent
    // (lower right), on dark paper (pal.dark) hatch the lit part instead — the line colour is light there.
    const pBody = pen.paper(BODY);
    tone(BODY, COL.body, 0.22, { k: 'body', p: rv(0.3, 0.55) });
    pen.paper(BELLY); tone(BELLY, COL.belly, 0, { k: 'belly', p: rv(0.35, 0.5), alpha: 0.8 });
    ctx.save(); ctx.clip(pBody);
    if (pen.pal.dark) ctx.clip(P.toPath(SHADE.map(([x, y]) => [x * 0.86 - 10, y * 0.9 - 30])));
    else { const cres = new Path2D(); cres.rect(-300, -400, 600, 500); cres.addPath(P.toPath(SHADE)); ctx.clip(cres, 'evenodd'); }
    pen.hatch(pBody, P.bbox(BODY), { color: col > 0.5 && !pen.pal.dark ? COL.bodyLine : g, alpha: pen.pal.dark ? 0.22 : 0.3, gap: 5, w: 1.3, id: id + 'shade', p: rv(0.4, 0.6), len: 40, angle: -1.1 });
    ctx.restore();
    pen.shape(BODY, { w: 3.4, color: col > 0.5 ? COL.bodyLine : g, id: id + 'body', p: rv(0, 0.35), gaps: 1 });
    pen.shape(BELLY, { w: 1.5, alpha: 0.5, id: id + 'bellyo', p: rv(0.3, 0.45), gaps: 1, passes: 1 });

    // cheeks (coloured only)
    if (col > 0) for (const bx of [-74, 74]) {
      const b = P.ellipse(bx, -142, 15, 8);
      pen.hatch(P.toPath(b), P.bbox(b), { color: COL.cheek, alpha: 0.6 * col, gap: 2.6, w: 2, id: id + 'cheek' + bx, angle: -0.4, len: 20 });
    }

    // eyes: white, pupil follows look, blink squashes the eye
    const bl = K.clamp(c.blink), ry = 27 * (1 - bl * 0.92);
    for (const ex of [-40, 40]) {
      const e = P.ellipse(ex, -186, 24, Math.max(2, ry));
      pen.paper(e);
      pen.shape(e, { w: 2.6, id: id + 'eye' + ex, p: rv(0.45, 0.6), gaps: 0 });
      if (bl < 0.75) {
        const lx = K.clamp(c.look[0], -1, 1) * 9, ly = K.clamp(c.look[1], -1, 1) * 9 * (ry / 27);
        const pu = P.ellipse(ex + lx, -184 + ly, 10, 10 * (ry / 27));
        pen.solid(pu, COL.pupil, rv(0.6, 0.66));
        const hi = P.ellipse(ex + lx - 3.5, -187 + ly, 3, 3 * (ry / 27));
        ctx.globalAlpha = rv(0.62, 0.68); ctx.fillStyle = '#FFFDF6'; ctx.fill(P.toPath(hi)); ctx.globalAlpha = 1;
      } else {
        pen.line([[ex - 22, -186], [ex, -180], [ex + 22, -186]], { w: 2.6, id: id + 'shut' + ex, gaps: 0 });
      }
    }
    // brows
    const by = -7 * c.brow;
    pen.line([[-58, -222 + by + 3], [-42, -228 + by], [-24, -223 + by]], { w: 3.2, id: id + 'browL', p: rv(0.6, 0.68), gaps: 0 });
    pen.line([[24, -223 + by], [42, -228 + by], [58, -222 + by + 3]], { w: 3.2, id: id + 'browR', p: rv(0.6, 0.68), gaps: 0 });

    // mouth: closed smile, or opened by cfg.mouth (talking), or 'o' (surprise)
    const m = K.clamp(c.mouth), mp = rv(0.66, 0.76), my = -128, mw = 22 + m * 6;
    if (c.shape === 'o') {
      const o = P.ellipse(0, my + 2, 9 + m * 3, 11 + m * 6);
      pen.solid(o, COL.mouth, 0.9 * mp); pen.shape(o, { w: 2.4, id: id + 'mo', p: mp, gaps: 0 });
    } else if (m < 0.08) {
      const lift = c.shape === 'flat' ? 1 : 11;
      pen.line(P.spline([[-mw, my - 2], [0, my + lift], [mw, my - 2]], 6), { w: 3, id: id + 'smile', p: mp, gaps: 0 });
    } else {
      const open = 4 + m * 22;
      const top = P.spline([[-mw, my - 3], [0, my + 2], [mw, my - 3]], 6);
      const bot = P.spline([[mw, my - 3], [0, my + open + 6], [-mw, my - 3]], 6);
      const shp = top.concat(bot);
      pen.solid(shp, COL.mouth, 0.92 * mp);
      if (col > 0 && m > 0.3) pen.solid(P.ellipse(0, my + open * 0.72, mw * 0.5, open * 0.28), COL.tongue, 0.85 * col * mp);
      pen.shape(shp, { w: 2.6, id: id + 'mouth', p: mp, gaps: 0 });
    }

    // sprout on top (the hero's «idea» antenna)
    const sp = rv(0.72, 0.86);
    if (sp > 0) {
      const stem = P.spline([[0, -282], [-4, -306], [4, -330]], 6);
      pen.line(stem, { w: 3, id: id + 'stem', p: sp, gaps: 0, color: col > 0.5 ? '#2E6E26' : null });
      for (const side of [-1, 1]) {
        const lf = P.spline([[2, -326], [side * 18, -350], [side * 40, -344], [side * 26, -326], [2, -326]], 6);
        pen.paper(lf); tone(lf, COL.sprout, 0.3, { k: 'leaf' + side, p: sp, alpha: 0.9, cgap: 2.6 });
        pen.shape(lf, { w: 2.2, id: id + 'leaf' + side, p: sp, gaps: 0 });
      }
    }

    // arms (in front of the body): 2-segment chains, round hands
    const hands = {};
    for (const side of ['L', 'R']) {
      const a = side === 'L' ? c.armL : c.armR, ap = rv(0.8, 0.96);
      const C = chainPts(side === 'L' ? [-100, -142] : [100, -142], a, 52, 46);
      hands[side] = C[2];
      if (ap <= 0) continue;
      const arm = tube(P.spline(C, 6), 7, 5.6);
      pen.paper(arm); tone(arm, COL.body, 0.18, { k: 'arm' + side, p: ap, alpha: 0.6 });
      pen.shape(arm, { w: 2.2, id: id + 'arm' + side, p: ap, gaps: 0 });
      const hd = P.ellipse(C[2][0], C[2][1], 11, 10.5);
      pen.paper(hd); tone(hd, COL.body, 0.2, { k: 'hand' + side, p: ap, alpha: 0.6 });
      pen.shape(hd, { w: 2.2, id: id + 'hand' + side, p: ap, gaps: 0 });
    }
    ctx.restore();
    return { handL: toCaller(hands.L), handR: toCaller(hands.R), mouth: toCaller([0, my]), eyeL: toCaller([-40, -186]), eyeR: toCaller([40, -186]), top: toCaller([0, -340]) };
  }

  G.HERO = { draw, COL, DEF };
})(window);
