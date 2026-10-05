// pencil.js — the hand-drawn look in code (methodology «Мультики кодом», section 3):
// (template copy of <эталон>/engine/pencil.js; API unchanged + pen.alphaMul for fading a group)
//  * on twos: every random choice is seeded by the drawing index d = floor(t*12), so lines re-trace 12 times a second;
//  * boiling lines: each drawing re-jitters every stroke a little; re-render gives the same pixels;
//  * pressure ribbon: a stroke is a filled ribbon that thins at the ends, with a lighter second sketch pass,
//    occasional pencil lifts and an overshoot past the start on closed shapes;
//  * hatching instead of fills (shadow hatching on light paper), graphite grain, worn paper, construction lines.
(function (G) {
  'use strict';
  const K = G.K;

  // ---------- geometry helpers ----------
  function resample(pts, step) {
    const out = [pts[0]];
    let carry = 0;
    for (let i = 1; i < pts.length; i++) {
      const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
      const dx = x1 - x0, dy = y1 - y0, seg = Math.hypot(dx, dy);
      if (seg < 1e-6) continue;
      let u = step - carry;
      while (u <= seg) { out.push([x0 + dx * u / seg, y0 + dy * u / seg]); u += step; }
      carry = seg - (u - step);
    }
    const last = pts[pts.length - 1], pl = out[out.length - 1];
    if (Math.hypot(last[0] - pl[0], last[1] - pl[1]) > step * 0.3) out.push(last);
    return out;
  }
  function polyLen(P) { let s = 0; for (let i = 1; i < P.length; i++) s += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); return s; }
  const ellipse = (cx, cy, rx, ry, rot = 0, a0 = 0, a1 = Math.PI * 2, n = 0) => {
    const N = n || Math.max(16, Math.round((rx + ry) * Math.abs(a1 - a0) / 6));
    const c = Math.cos(rot), s = Math.sin(rot), P = [];
    for (let i = 0; i <= N; i++) {
      const a = a0 + (a1 - a0) * i / N, x = Math.cos(a) * rx, y = Math.sin(a) * ry;
      P.push([cx + x * c - y * s, cy + x * s + y * c]);
    }
    return P;
  };
  const rect = (x, y, w, h, r = 0) => {
    if (!r) return [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]];
    const P = [], q = (cx, cy, a0) => { for (let i = 0; i <= 6; i++) { const a = a0 + i / 6 * Math.PI / 2; P.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); } };
    q(x + w - r, y + r, -Math.PI / 2); q(x + w - r, y + h - r, 0); q(x + r, y + h - r, Math.PI / 2); q(x + r, y + r, Math.PI); P.push(P[0]);
    return P;
  };
  // Catmull-Rom through control points
  function spline(C, samples = 8, closed = false) {
    const P = [], n = C.length;
    const get = i => closed ? C[(i + n) % n] : C[Math.max(0, Math.min(n - 1, i))];
    const last = closed ? n : n - 1;
    for (let i = 0; i < last; i++) {
      const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
      for (let k = 0; k < samples; k++) {
        const t = k / samples, t2 = t * t, t3 = t2 * t;
        P.push([0, 1].map(j => 0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)));
      }
    }
    P.push(closed ? C[0] : C[n - 1]);
    return P;
  }
  const xf = (P, f) => P.map(p => f(p[0], p[1]));
  function toPath(P, closed = true) { const p = new Path2D(); p.moveTo(P[0][0], P[0][1]); for (let i = 1; i < P.length; i++) p.lineTo(P[i][0], P[i][1]); if (closed) p.closePath(); return p; }
  function bbox(P) { let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (const [x, y] of P) { if (x < x0) x0 = x; if (y < y0) y0 = y; if (x > x1) x1 = x; if (y > y1) y1 = y; } return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }; }

  const svgCache = new Map();
  function svgPts(d, step = 4) {
    const key = step + '|' + d;
    if (svgCache.has(key)) return svgCache.get(key);
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg'), path = document.createElementNS(NS, 'path');
    path.setAttribute('d', d); svg.appendChild(path); svg.style.position = 'absolute'; svg.style.left = '-9999px';
    document.body.appendChild(svg);
    const L = path.getTotalLength(), n = Math.max(4, Math.ceil(L / step)), P = [];
    for (let i = 0; i <= n; i++) { const q = path.getPointAtLength(L * i / n); P.push([q.x, q.y]); }
    svg.remove();
    svgCache.set(key, P);
    return P;
  }

  // ---------- textures ----------
  function makeNoise(size, seed) {
    const c = document.createElement('canvas'); c.width = c.height = size;
    const x = c.getContext('2d'), img = x.createImageData(size, size), r = K.rngOf('noise', seed);
    for (let i = 0; i < size * size; i++) {
      const v = r();
      img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = 0;
      img.data[i * 4 + 3] = Math.round(255 * (0.42 + 0.58 * Math.pow(v, 0.55)));    // graphite: most pixels dark, some skipped
    }
    x.putImageData(img, 0, 0);
    // streaks along the stroke direction (paper tooth)
    x.globalCompositeOperation = 'destination-out';
    for (let i = 0; i < 260; i++) {
      x.globalAlpha = 0.25 + r() * 0.4; x.fillRect(r() * size, r() * size, 1 + r() * 2, 0.6 + r());
    }
    return c;
  }
  function makePaperTile(size, pal) {
    const c = document.createElement('canvas'); c.width = c.height = size;
    const x = c.getContext('2d'), r = K.rngOf('paper', pal.name);
    x.fillStyle = pal.paper; x.fillRect(0, 0, size, size);
    const img = x.getImageData(0, 0, size, size);
    for (let i = 0; i < size * size; i++) {
      const g = (r() - 0.5) * 9 + (r() < 0.012 ? -18 * r() : 0);
      img.data[i * 4] += g; img.data[i * 4 + 1] += g; img.data[i * 4 + 2] += g * 0.9;
    }
    x.putImageData(img, 0, 0);
    // fibres (wrapped so the tile repeats)
    x.lineCap = 'round';
    for (let i = 0; i < 70; i++) {
      const x0 = r() * size, y0 = r() * size, a = r() * 6.28, l = 6 + r() * 26;
      x.strokeStyle = r() < 0.5 ? 'rgba(120,100,70,0.10)' : 'rgba(255,255,255,0.25)'; x.lineWidth = 0.6 + r() * 0.6;
      for (const [ox, oy] of [[0, 0], [-size, 0], [size, 0], [0, -size], [0, size]]) {
        x.beginPath(); x.moveTo(x0 + ox, y0 + oy); x.quadraticCurveTo(x0 + ox + Math.cos(a) * l * 0.5 + 3, y0 + oy + Math.sin(a) * l * 0.5 - 2, x0 + ox + Math.cos(a) * l, y0 + oy + Math.sin(a) * l); x.stroke();
      }
    }
    return c;
  }

  class Pen {
    constructor(ctx, W, H, pal) {
      this.ctx = ctx; this.W = W; this.H = H; this.pal = pal;
      this.noise = makeNoise(256, 1);
      this.pats = new Map();
      this.paperTile = makePaperTile(512, pal);
      this.paperPat = ctx.createPattern(this.paperTile, 'repeat');
      this.t = 0; this.d = 0; this.boilAmp = 1; this.wMul = 1.2;
      this.alphaMul = 1;   // fade a whole group: every stroke, fill, paper and letter multiplies its alpha by it
    }
    frame(t) { this.t = t; this.d = Math.floor(t * 12 + 1e-6); }
    pattern(color) {
      let p = this.pats.get(color);
      if (p) return p;
      const c = document.createElement('canvas'); c.width = c.height = 256;
      const x = c.getContext('2d');
      x.fillStyle = color; x.fillRect(0, 0, 256, 256);
      x.globalCompositeOperation = 'destination-in'; x.drawImage(this.noise, 0, 0);
      p = this.ctx.createPattern(c, 'repeat');
      this.pats.set(color, p);
      return p;
    }

    // ---------- the pencil stroke ----------
    // pts in current coordinates. o: w, color, alpha, id, boil, p (draw-on progress 0..1), closed, gaps, taper, passes, step
    line(pts, o = {}) {
      if (!pts || pts.length < 2) return;
      const prog = o.p == null ? 1 : o.p;
      if (prog <= 0.001) return;
      const ctx = this.ctx, w = (o.w == null ? 3 : o.w) * this.wMul, alpha = o.alpha == null ? 0.9 : o.alpha;
      const step = o.step || Math.max(2.5, Math.min(7, w * 1.4));
      const boil = (o.boil == null ? 1 : o.boil) * this.boilAmp;
      let P = resample(o.closed ? pts.concat([pts[0]]) : pts, step);
      if (o.closed && o.over !== false) P = P.concat(P.slice(1, Math.max(2, Math.round(P.length * 0.06))));
      if (prog < 1) P = P.slice(0, Math.max(2, Math.round(P.length * prog)));
      const L = P.length;
      if (L < 2) return;
      const r = K.rngOf(o.id || 'l', this.d);
      const ph1 = r() * 6.283, ph2 = r() * 6.283, ph3 = r() * 6.283, f1 = 0.010 + r() * 0.012, f2 = 0.035 + r() * 0.03;
      const lift = []; // pencil lifts (gaps) on long strokes
      if (o.gaps !== 0 && L * step > 140) {
        const ng = (o.gaps == null ? (r() < 0.55 ? 1 : 0) + (r() < 0.25 ? 1 : 0) : o.gaps);
        for (let g = 0; g < ng; g++) { const a = 0.15 + r() * 0.7; lift.push([a, a + (2.5 + r() * 5) * step / (L * step)]); }
      }
      const pass = (amp, wmul, alp, seedTag) => {
        const rr = seedTag ? K.rngOf(o.id || 'l', seedTag, this.d) : r;
        const q1 = seedTag ? rr() * 6.283 : ph1, q2 = seedTag ? rr() * 6.283 : ph2;
        const left = [], right = [];
        let s = 0;
        for (let i = 0; i < L; i++) {
          const a = P[Math.max(0, i - 1)], b = P[Math.min(L - 1, i + 1)];
          let tx = b[0] - a[0], ty = b[1] - a[1]; const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
          const nx = -ty, ny = tx;
          if (i) s += step;
          const off = amp * (Math.sin(s * f1 + q1) * 0.65 + Math.sin(s * f2 + q2) * 0.35) + (rr() - 0.5) * 0.3 * amp;
          const u = i / (L - 1);
          const tp = o.taper === false ? 1 : K.smooth(Math.min(1, u / 0.14, (1 - u) / 0.2));
          const press = 0.84 + 0.16 * Math.sin(s * 0.027 + ph3);
          const hw = Math.max(0.25, w * wmul * (0.3 + 0.7 * tp) * press) / 2;
          const x = P[i][0] + nx * off, y = P[i][1] + ny * off;
          left.push([x + nx * hw, y + ny * hw]); right.push([x - nx * hw, y - ny * hw]);
        }
        // split at lifts
        const cuts = lift.map(([a, b]) => [Math.floor(a * (L - 1)), Math.ceil(b * (L - 1))]);
        const segs = []; let st = 0;
        for (const [a, b] of cuts.sort((m, n) => m[0] - n[0])) { if (a > st + 1) segs.push([st, a]); st = Math.max(st, b); }
        if (L - 1 > st + 1) segs.push([st, L - 1]);
        ctx.globalAlpha = alp * this.alphaMul;
        ctx.fillStyle = this.pattern(o.color || this.pal.line);
        ctx.beginPath();
        for (const [a, b] of segs) {
          ctx.moveTo(left[a][0], left[a][1]);
          for (let i = a + 1; i <= b; i++) ctx.lineTo(left[i][0], left[i][1]);
          for (let i = b; i >= a; i--) ctx.lineTo(right[i][0], right[i][1]);
          ctx.closePath();
        }
        ctx.fill();
      };
      pass(boil * 1.0, 1, alpha, null);
      if ((o.passes == null ? 2 : o.passes) > 1 && w > 1.1) pass(boil * 1.6, 0.42, alpha * 0.38, 'sk');
      ctx.globalAlpha = 1;
    }

    // closed outline helper
    shape(pts, o = {}) { this.line(pts, Object.assign({ closed: true }, o)); }

    // ---------- hatching (shadow / colored-pencil fill) ----------
    // region: Path2D in current coords, bb: {x,y,w,h}. o: color, angle, gap, w, alpha, id, cross, jitter, p (reveal 0..1 along hatch direction)
    hatch(region, bb, o = {}) {
      const ctx = this.ctx;
      const ang = o.angle == null ? -0.9 : o.angle, gap = o.gap || 7, wb = o.w || 1.6, alpha = o.alpha == null ? 0.7 : o.alpha;
      const prog = o.p == null ? 1 : o.p;
      if (prog <= 0) return;
      ctx.save(); ctx.clip(region);
      const rs = K.rngOf(o.id || 'h', 'stable'), rb = K.rngOf(o.id || 'h', this.d);
      const cx = bb.x + bb.w / 2, cy = bb.y + bb.h / 2, R = Math.hypot(bb.w, bb.h) / 2 + 4;
      const dx = Math.cos(ang), dy = Math.sin(ang), nx = -dy, ny = dx;
      const buckets = [new Path2D(), new Path2D(), new Path2D()];
      const jit = (o.jitter == null ? 1 : o.jitter) * this.boilAmp;
      for (let off = -R; off < R; off += gap * (0.75 + rs() * 0.5)) {
        if ((off + R) / (2 * R) > prog) break;
        let u = -R - rs() * 30;
        while (u < R) {
          const len = (o.len || 70) * (0.45 + rs() * 0.9), u2 = u + len;
          const j1 = (rb() - 0.5) * 1.6 * jit, j2 = (rb() - 0.5) * 1.6 * jit, bend = (rs() - 0.5) * 4 + (rb() - 0.5) * jit;
          const x1 = cx + dx * u + nx * (off + j1), y1 = cy + dy * u + ny * (off + j1);
          const x2 = cx + dx * u2 + nx * (off + j2), y2 = cy + dy * u2 + ny * (off + j2);
          const mx = (x1 + x2) / 2 + nx * bend, my = (y1 + y2) / 2 + ny * bend;
          const b = buckets[Math.floor(rs() * 3)];
          b.moveTo(x1, y1); b.quadraticCurveTo(mx, my, x2, y2);
          u = u2 + rs() * (o.dash || 7);
        }
      }
      ctx.strokeStyle = this.pattern(o.color || this.pal.line); ctx.lineCap = 'round'; ctx.globalAlpha = alpha * this.alphaMul;
      buckets.forEach((b, i) => { ctx.lineWidth = wb * (0.7 + i * 0.3); ctx.stroke(b); });
      ctx.restore(); ctx.globalAlpha = 1;
      if (o.cross) this.hatch(region, bb, Object.assign({}, o, { angle: ang + (o.crossAngle || 1.25), cross: false, id: (o.id || 'h') + 'x', alpha: alpha * 0.8 }));
    }
    // fill a polygon with colored pencil (2 directions) — the «заливка» of this style
    fill(P, o = {}) {
      const path = toPath(P), bb = bbox(P);
      this.hatch(path, bb, Object.assign({ gap: 4.2, w: 2.4, alpha: 0.62, len: 60, cross: true, crossAngle: 0.5 }, o));
      return path;
    }
    // cover what is behind with paper (keeps the texture): occlusion inside the drawing
    paper(P) {
      const ctx = this.ctx, path = P instanceof Path2D ? P : toPath(P);
      ctx.globalAlpha = this.alphaMul; ctx.fillStyle = this.paperPat; ctx.fill(path); ctx.globalAlpha = 1;
      return path;
    }
    solid(P, color, alpha = 1) { const ctx = this.ctx; ctx.globalAlpha = alpha * this.alphaMul; ctx.fillStyle = this.pattern(color); ctx.fill(P instanceof Path2D ? P : toPath(P)); ctx.globalAlpha = 1; }

    // ---------- handwriting / pencil lettering ----------
    // o: size, font ('hand'|'handb'|'code'|'sans'), color, align, p (write-on), id, boil, alpha, letter (extra spacing)
    text(str, x, y, o = {}) {
      const ctx = this.ctx, size = o.size || 48;
      const fam = { hand: "'Hand'", handb: "'HandB'", code: "'Code'", codeb: "'CodeB'", sans: "'Sans'" }[o.font || 'hand'];
      ctx.font = `${size}px ${fam}`;
      ctx.textBaseline = 'alphabetic';
      const chars = Array.from(str), sp = o.letter || 0;
      const xs = [0];
      for (let i = 1; i <= chars.length; i++) xs.push(ctx.measureText(chars.slice(0, i).join('')).width + sp * i);
      const total = xs[chars.length];
      let x0 = x;
      if (o.align === 'center') x0 = x - total / 2; else if (o.align === 'right') x0 = x - total;
      const prog = o.p == null ? 1 : o.p, shown = prog * chars.length;
      const r = K.rngOf(o.id || str, this.d), boil = (o.boil == null ? 1 : o.boil) * this.boilAmp;
      ctx.fillStyle = this.pattern(o.color || this.pal.line);
      ctx.globalAlpha = (o.alpha == null ? 0.95 : o.alpha) * this.alphaMul;
      for (let i = 0; i < chars.length && i < shown; i++) {
        const part = Math.min(1, shown - i);
        const jx = (r() - 0.5) * size * 0.025 * boil, jy = (r() - 0.5) * size * 0.03 * boil, rot = (r() - 0.5) * 0.04 * boil;
        const cw = xs[i + 1] - xs[i];
        ctx.save();
        ctx.translate(x0 + xs[i] + jx, y + jy); ctx.rotate(rot);
        if (part < 1) { ctx.beginPath(); ctx.rect(-2, -size * 1.2, (cw + 4) * part, size * 1.6); ctx.clip(); }
        ctx.fillText(chars[i], 0, 0);
        ctx.restore();
      }
      ctx.globalAlpha = 1;
      return { x: x0, w: total, h: size };
    }
    textW(str, size, font = 'hand') {
      const fam = { hand: "'Hand'", handb: "'HandB'", code: "'Code'", codeb: "'CodeB'", sans: "'Sans'" }[font];
      this.ctx.font = `${size}px ${fam}`;
      return this.ctx.measureText(str).width;
    }
    // where the pencil tip is while writing (for the drawing-hand / sparks)
    // ---------- construction lines: pale guides at the start of a scene, fading out ----------
    guides(items, k, id = 'g') {
      if (k <= 0.01) return;
      for (let i = 0; i < items.length; i++) this.line(items[i], { w: 1.6, color: this.pal.guide, alpha: 0.85 * k, id: id + i, gaps: 0, passes: 1, boil: 0.7 });
    }
  }

  G.PEN = { Pen, resample, polyLen, ellipse, rect, spline, xf, toPath, bbox, svgPts };
})(window);
