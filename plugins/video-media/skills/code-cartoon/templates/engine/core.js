// core.js — deterministic helpers shared by every scene: seeded random, easing, timing lookups, camera.
// Everything is a function of time t. No Math.random, no clocks: a re-render gives the same pixels.
// Template version of <эталон>/engine/core.js: word() also strips leading quotes/brackets,
// plus K.firstTick / K.lastTick (first/last drawing of a scene on twos, for chained transitions).
(function (G) {
  'use strict';

  function hashStr(s) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function hash(...parts) {
    let h = 0x811c9dc5;
    for (const p of parts) {
      const v = typeof p === 'number' ? (p * 2654435761) >>> 0 : hashStr(String(p));
      h = Math.imul(h ^ v, 0x01000193) >>> 0;
      h ^= h >>> 13;
    }
    return h >>> 0;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  // seeded generator: same parts -> same sequence. Draw ALL numbers you need first, then skip invisible items
  // (drawing inside an `if` shifts the sequence and makes neighbours jump).
  const rngOf = (...parts) => mulberry32(hash(...parts));

  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const inv = (a, b, v) => clamp((v - a) / (b - a));           // 0..1 progress of v in [a,b]
  const smooth = k => k * k * (3 - 2 * k);
  const E = {
    lin: k => k,
    inQ: k => k * k, outQ: k => 1 - (1 - k) * (1 - k), ioQ: k => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2),
    outC: k => 1 - Math.pow(1 - k, 3), inC: k => k * k * k, ioC: k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
    outBack: k => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(k - 1, 3) + c1 * Math.pow(k - 1, 2); },
    outElastic: k => (k === 0 || k === 1 ? k : Math.pow(2, -10 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI) / 3) + 1),
    smooth,
  };
  // progress of t inside [a, a+d] with easing
  const tw = (t, a, d, ease = E.ioQ) => ease(inv(a, a + d, t));
  // hand-drawn timing: animation pose changes only 12 times a second ("on twos" at 24 fps)
  const twos = t => Math.floor(t * 12 + 1e-6) / 12;

  // timing lookups from window.TIMING (built by timing/build_timing.py or timing/fake_timing.py)
  // word('кодом', 2) = the 2nd «кодом». A timing word keeps its punctuation ('Code.', 'вышло —', '«Привет'):
  // a bare query matches the word without leading quotes/brackets and trailing punctuation ('тоже' finds 'тоже' and
  // 'тоже.'), a query with punctuation matches only that exact token ('тоже.' skips a bare 'тоже'). Occurrence n counts
  // matching words only. timing/timing_common.py uses the same rule.
  const normWord = s => String(s).split(' ')[0].replace(/^[«"'(\[„“]+/, '').replace(/[.,:;!?…»"')\]—–-]+$/, '');
  function word(text, n = 1) {
    let k = 0;
    for (const w of G.TIMING.words) if (w.w === text || normWord(w.w) === text) { if (++k === n) return w; }
    throw new Error('word not in timing: ' + text + ' #' + n + ' (found ' + k + ')');
  }
  function scene(name) {
    const s = G.TIMING.scenes.find(x => x.name === name);
    if (!s) throw new Error('scene not in timing: ' + name);
    return s;
  }
  // first / last drawing (tick on twos) that renderAt shows for a scene: a camera move into the next scene must
  // finish by lastTick - 1/12 (on twos the last drawing is held for two frames), the next scene starts at firstTick
  const firstTick = name => twos(Math.ceil(scene(name).start * G.TIMING.fps - 1e-6) / G.TIMING.fps);
  const lastTick = name => twos((Math.ceil(scene(name).end * G.TIMING.fps - 1e-6) - 1) / G.TIMING.fps);
  function mouthAt(t) {
    const m = G.TIMING.mouth, i = Math.floor(twos(t) * G.TIMING.fps);
    return m[Math.max(0, Math.min(m.length - 1, i))] || 0;
  }

  // camera: world -> screen. zoom 1 in landscape == 1920 world units across the frame (1080 in portrait).
  function applyCamera(ctx, W, H, cam, base) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.translate(W / 2, H / 2);
    ctx.scale(base * cam.zoom, base * cam.zoom);
    if (cam.rot) ctx.rotate(cam.rot);
    ctx.translate(-cam.x, -cam.y);
  }
  // log-zoom + linear position. In a long dive the target drifts sideways mid-way; for deep dives slide the target
  // linearly in screen space instead (see gloss zoomTo).
  const lerpCam = (a, b, k) => ({ x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), zoom: Math.exp(lerp(Math.log(a.zoom), Math.log(b.zoom), k)), rot: lerp(a.rot || 0, b.rot || 0, k) });

  G.K = { hash, hashStr, mulberry32, rngOf, clamp, lerp, inv, smooth, E, tw, twos, word, normWord, scene, firstTick, lastTick, mouthAt, applyCamera, lerpCam };
})(window);
