// scenes3d_template.js — the two sample scenes of pencil/scenes.js in glossy 3D (new_project.py copies it to gloss/scenes3d.js).
// Same voice, TIMING and scene names as the pencil page: «Этот герой нарисован кодом: каждая линия — строчка программы. |
// Скажи одну фразу — и лампочка загорится. Остальной кадр не сдвинется ни на пиксель. Так работает мультик кодом.»
// What it shows:
//  - renderer: NeutralToneMapping (ACES washes pastels out), sRGB output, PCFSoft shadows, RoomEnvironment through PMREM for
//    soft reflections, a wall plane behind everything (without it the horizon shows) with its own pastel per scene;
//  - glossy toys from helpers rbox / sph / cyl / cone / caps / torus, MeshPhysicalMaterial with clearcoat 1;
//  - text on canvas textures, drawn only after the fonts loaded (otherwise a serif), long lines fitted by measureText;
//  - the pencil hero (engine/hero.js) as a sticker: drawn into an offscreen canvas with a margin, white rim, a real shadow
//    through customDepthMaterial, redrawn only when the pose or the drawing number on twos changes;
//  - camera: setKey (light and shadow box follow the target), applyCam (with z and a small sway), zoomTo (a dive without the
//    sideways smear of lerpCam), camOnMesh (frame a flat mesh: fill 'min' | 'w' | 'h'), camKeys;
//  - MATCH CUT: scene 1 holds a framed picture whose face shows a live snapshot of scene 2's first frame; the camera dives
//    into it and the cut is invisible: same props-state function (s2Props), same pose, camera, wall and hero drawing.
// Rules: every time comes from TIMING (W('слово'), K.firstTick / K.lastTick), never from seconds of one voice take;
// everything is a function of tt = K.twos(t) (12 drawings a second, the camera too); renderAt(t) keeps no state between
// frames (any frame order gives the same pixels: still.py --det checks it); no Math.random; objects are never re-parented
// in per-frame code (the reference did, and a frame of an earlier scene then rendered without its props).
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

// ---------------- fonts first ----------------
// canvas textures are drawn with ctx.font: before the font file has loaded the browser silently draws a serif
const FACES = ['Hand', 'HandB', 'Code', 'CodeB', 'Sans', 'SansM'];
await document.fonts.ready;
await Promise.all(FACES.map(f => document.fonts.load(`40px '${f}'`, 'АБВабв{}#>')
  .then(list => { if (!list.length) console.error(`font not loaded: ${f} (check ../fonts/)`); })
  .catch(() => console.error(`font not loaded: ${f} (check ../fonts/)`))));

const { clamp, lerp, inv, E, tw, word: W, mouthAt } = K;
const PORT = FMT === 'port', LP = window.LP, PL = window.PAL;
const U = 100;                                        // 1 world unit = 100 layout px (layout px = pencil coordinates)
const X = x => x / U, Y = y => -y / U;                // layout -> world: layout y goes down, world y goes up
const VW = PORT ? 10.8 : 19.2, VH = PORT ? 19.2 : 10.8;   // world units seen at z = 0 with zoom 1 (= frame px / 100)
const popk = (tt, t0, d = 0.35) => E.outBack(inv(t0, t0 + d, tt));   // pop-in with a small overshoot

// ---------------- timing anchors (all from TIMING) ----------------
const S1_LAST = K.lastTick('s1_intro'), S2_FIRST = K.firstTick('s2_light');   // last / first drawing on each side of the cut
const DIVE0 = S1_LAST - 0.8, DIVE1 = S1_LAST - 1 / 12;   // the dive ends one drawing before the cut: on twos the last drawing
                                                         // is held 2 frames, and a dive still moving there jumps at the cut
const SNAP_AHEAD = S2_FIRST - S1_LAST;                   // 0 or 1/12: the picture runs one drawing ahead (see snapshot())
const PIC_IN = 0.3;                                      // the framed picture pops in right after the start
const TURN = W('загорится').s + 0.25;                    // the click: the bulb lights up (~40 % of the length)
const FREEZE0 = W('Остальной').s - 0.05, FREEZE1 = W('пиксель').e + 0.3;   // «nothing else moved»: the hero stops boiling
const POSTER0 = W('Так').s - 0.1, LAST = W('кодом', 2).e;   // the poster: the last >= 3 s, nothing fast moves
const OUT0 = POSTER0 - 0.5, OUT1 = POSTER0 - 0.05;          // the interface leaves before the poster
// deterministic blinks every 2.4–4.3 s (seeded, not tied to one voice take)
const BLINKS = (() => { const r = K.rngOf('blinks'), out = []; for (let t = 1.3; t < TIMING.duration; t += 2.4 + r() * 1.9) out.push(t); return out; })();
const blinkAt = t => { for (const b of BLINKS) { const d = Math.abs(t - b); if (d < 0.13) return 1 - d / 0.13; } return 0; };

// ---------------- renderer, camera, light, wall ----------------
const cv = document.getElementById('cv');
// preserveDrawingBuffer: render.py reads every frame back with toDataURL, and the snapshot copies the canvas
const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(CW, CH, false);
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.0;   // ACES turns the pastel walls grey
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;   // soft studio reflections on the clearcoat
scene.environmentIntensity = 0.85;
const FOV = 30, D0 = (VH / 2) / Math.tan(FOV / 2 * Math.PI / 180);   // camera distance at which zoom 1 shows VW x VH at z = 0
// near 0.5, not 0.1: depth precision. In 9:16 the camera stands ~36 units away (D0) and a text plate 0.001 in front of its
// slab z-fought — white stripes through the picture, in 9:16 only. Keep decals >= 0.01 in front of their surface.
const camera = new THREE.PerspectiveCamera(FOV, CW / CH, 0.5, 300);
scene.add(new THREE.HemisphereLight('#FFF8EE', '#E2C9B2', 0.7));
const key = new THREE.DirectionalLight('#FFFFFF', 2.1);
key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02;
scene.add(key, key.target);
const wallMat = new THREE.MeshStandardMaterial({ color: '#F5E8DA', roughness: 0.95 });
const wall = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), wallMat);   // the backdrop: catches the shadows, hides the horizon
wall.position.z = -1.6; wall.receiveShadow = true; scene.add(wall);
function setWall(c) { wallMat.color.set(c); scene.background.set(c); }

// ---------------- camera helpers ----------------
// the key light and its shadow box follow the camera target, so shadows stay sharp at any zoom
function setKey(tx, ty, zoom) {
  key.position.set(tx - 6, ty + 8, 14); key.target.position.set(tx, ty, 0);
  const s = Math.max(VW, VH) / zoom * 0.75;
  Object.assign(key.shadow.camera, { left: -s, right: s, top: s, bottom: -s, near: 1, far: 60 });
  key.shadow.camera.updateProjectionMatrix();
}
// c = {x, y (layout px), z (world, the plane the camera looks at), zoom, sway 0..1 (default 1)}. Sway is a slow hand-held
// drift of 0.16 units; bigger pushes the layout out of the frame. Called every frame with tt, so it moves on twos too.
function applyCam(c, tt) {
  const tx = X(c.x), ty = Y(c.y), tz = c.z || 0, d = D0 / c.zoom;
  const sway = (c.sway == null ? 1 : c.sway) * 0.16;
  camera.position.set(tx + Math.sin(tt * 0.35) * sway, ty + 0.25 * sway + Math.cos(tt * 0.27) * sway * 0.4, tz + d);
  camera.lookAt(tx, ty, tz);
  setKey(tx, ty, c.zoom);
}
// dive: the zoom grows exponentially while the target slides LINEARLY to the frame centre in screen space
// (K.lerpCam — log zoom + linear world position — smears sideways half-way through a deep dive)
function zoomTo(c0, tg, k) {
  const z = Math.exp(lerp(Math.log(c0.zoom), Math.log(tg.zoom), k));
  const ox = (tg.x - c0.x) * c0.zoom * (1 - k), oy = (tg.y - c0.y) * c0.zoom * (1 - k);   // target's screen offset, shrinking
  return { x: tg.x - ox / z, y: tg.y - oy / z, zoom: z, z: lerp(c0.z || 0, tg.z || 0, k), sway: (c0.sway == null ? 1 : c0.sway) * (1 - k) };
}
// a camera that frames a flat mesh of w x h world units, taken from its WORLD position (z included):
// 'w' fills the width, 'h' the height, 'min' fits it inside. A tilted screen needs ~4 % more zoom, or its frame shows.
const _v = new THREE.Vector3();
function camOnMesh(mesh, w, h, fill = 'min') {
  scene.updateMatrixWorld(); mesh.getWorldPosition(_v);
  const zw = VW / w, zh = VH / h;
  return { x: _v.x * U, y: -_v.y * U, z: _v.z, zoom: fill === 'w' ? zw : fill === 'h' ? zh : Math.min(zw, zh), sway: 0 };
}
const camOnRect = (cx, cy, w, h) => ({ x: cx, y: cy, zoom: Math.min(VW * U / w, VH * U / h), sway: 0 });
// [[time, cam], ...] -> cam at t (log zoom, linear position and sway)
const camKeys = (t, keys, ease = E.ioC) => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const a = keys[i - 1][1], b = keys[i][1], k = ease(inv(keys[i - 1][0], keys[i][0], t));
    return Object.assign(K.lerpCam(a, b, k), { z: lerp(a.z || 0, b.z || 0, k), sway: lerp(a.sway == null ? 1 : a.sway, b.sway == null ? 1 : b.sway, k) });
  }
  return keys[keys.length - 1][1];
};

// ---------------- materials and primitives ----------------
// materials are cached by colour + options and SHARED: never change one per frame — switch mesh.material instead
const MATS = new Map();
function gloss(color, o = {}) {
  const k = color + JSON.stringify(o);
  if (!MATS.has(k)) MATS.set(k, new THREE.MeshPhysicalMaterial(Object.assign({ color, roughness: 0.2, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.05 }, o)));
  return MATS.get(k);
}
const METAL = gloss('#C9CED6', { metalness: 0.7, roughness: 0.25 });
const shadowy = m => { m.castShadow = true; m.receiveShadow = true; return m; };
const rbox = (w, h, d, r, mat) => shadowy(new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 5, Math.min(r, w / 2 - 0.001, h / 2 - 0.001, d / 2 - 0.001)), mat));
const sph = (r, mat, seg = 48) => shadowy(new THREE.Mesh(new THREE.SphereGeometry(r, seg, seg / 2), mat));
const cyl = (r1, r2, h, mat, seg = 40) => shadowy(new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, seg), mat));
const cone = (r, h, mat, seg = 40) => shadowy(new THREE.Mesh(new THREE.ConeGeometry(r, h, seg), mat));   // apex at +h/2
const caps = (r, len, mat) => shadowy(new THREE.Mesh(new THREE.CapsuleGeometry(r, len, 8, 24), mat));   // len = straight part
const torus = (R, r, mat) => shadowy(new THREE.Mesh(new THREE.TorusGeometry(R, r, 20, 64), mat));
function group(...kids) { const g = new THREE.Group(); kids.forEach(k => g.add(k)); return g; }
function place(o, x, y, z = 0) { o.position.set(X(x), Y(y), z); return o; }   // x, y in layout px, z in world units
function show(o, k, base = 1) { o.visible = k > 0.001; if (o.visible) o.scale.setScalar(Math.max(0.001, k) * base); }

// ---------------- canvas textures and text ----------------
function ctex(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return { c, x: c.getContext('2d'), t };
}
// an unlit plane showing a canvas texture with exact colours (toneMapped: false): text, labels, screens
function face(tex, w, h, z, o = {}) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex.t, transparent: !!o.transparent, toneMapped: false, depthWrite: !o.transparent }));
  m.position.z = z; return m;
}
// text on a 2D context; o.p = 0..1 reveals characters (typing); o.font = CSS family in quotes
function text(x, str, px, py, size, o = {}) {
  x.font = `${size}px ${o.font || "'Sans'"}`; x.fillStyle = o.color || '#1E1B2E'; x.textAlign = o.align || 'left'; x.textBaseline = 'alphabetic';
  const ch = Array.from(str), n = o.p == null ? ch.length : Math.floor(ch.length * clamp(o.p) + 1e-6);
  x.fillText(ch.slice(0, n).join(''), px, py);
}
// the largest size <= size at which str fits into maxW (long words otherwise run off the plate)
function fit(x, str, size, maxW, font) { x.font = `${size}px ${font}`; const w = x.measureText(str).width; return w > maxW ? size * maxW / w : size; }
const measureCtx = document.createElement('canvas').getContext('2d');
const textW = (str, size, font) => { measureCtx.font = `${size}px ${font}`; return measureCtx.measureText(str).width; };
// a text plate w x h layout px (canvas at res x for crisp letters). paint() redraws it only when the content key changes:
// the texture is a pure function of the key, so skipping a redraw never changes a frame
function plate(w, h, z, o = {}) {
  const res = o.res || 1.5, tx = ctex(Math.round(w * res), Math.round(h * res));
  const m = face(tx, w / U, h / U, z, { transparent: o.transparent !== false });
  m.userData.plate = { tx, res, w, h, key: null };
  return m;
}
function paint(m, key, draw) {
  const P = m.userData.plate;
  if (P.key === key) return;
  P.key = key;
  const x = P.tx.x;
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, P.tx.c.width, P.tx.c.height);
  x.setTransform(P.res, 0, 0, P.res, 0, 0);                // draw() works in layout px of the plate
  draw(x, P.w, P.h);
  P.tx.t.needsUpdate = true;
}
// words written with the voice: items [[shown text, timing word, occurrence]] -> visible characters of each item
const wordChars = (tt, items) => items.map(([s, w, n]) => { const d = W(w, n || 1); return Math.floor(Array.from(s).length * tw(tt, d.s - 0.05, Math.max(0.25, d.e - d.s + 0.05), E.lin) + 1e-6); });
// each word is drawn at its FINAL position, so the line does not shift while it is being written
function drawWords(x, items, chars, ax, y, size, font, color, align = 'center') {
  x.font = `${size}px ${font}`; x.fillStyle = color; x.textAlign = 'left'; x.textBaseline = 'alphabetic';
  const gap = x.measureText(' ').width, ws = items.map(([s]) => x.measureText(s).width);
  let px = align === 'center' ? ax - (ws.reduce((a, b) => a + b, 0) + gap * (items.length - 1)) / 2 : ax;
  items.forEach(([s], i) => { if (chars[i] > 0) x.fillText(Array.from(s).slice(0, chars[i]).join(''), px, y); px += ws[i] + gap; });
}

// ---------------- the hand-drawn hero as a sticker ----------------
// HERO.draw paints into canvas A with a margin around the figure (on a tight 1024 canvas raised arms and props were cut off).
// Canvas B = A drawn 16 times shifted by `rim` px, filled white (source-in) = the white sticker border, then A on top.
// The mesh is unlit (exact pencil colours); customDepthMaterial with alphaTest makes the shadow follow the sticker outline.
// It redraws only when the pose or the drawing number changes: 12 times a second at most.
class Sprite {
  constructor(w = 1400, h = 1200, feet = [700, 1150], cs = 2.4, rim = 9) {
    this.w = w; this.h = h; this.feet = feet; this.cs = cs; this.rim = rim;
    this.A = document.createElement('canvas'); this.A.width = w; this.A.height = h; this.ax = this.A.getContext('2d');
    this.B = ctex(w, h);
    this.pen = new PEN.Pen(this.ax, w, h, PL);
    const mat = new THREE.MeshBasicMaterial({ map: this.B.t, transparent: true, alphaTest: 0.05, toneMapped: false, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
    this.mesh.castShadow = true;
    this.mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: this.B.t, alphaTest: 0.5 });
    this.mesh.visible = false;
    this.key = null;
  }
  // t = time of the drawing (boil = floor(t*12)); keyStr = everything else the drawing depends on (the pose);
  // draw(pen, cx, cy, cs) paints in sprite px; x, y = feet in layout px; s = layout scale (the same number as HERO s)
  update(t, keyStr, draw, x, y, s, z = 0.35) {
    const k = keyStr + '|' + Math.floor(t * 12 + 1e-6);
    if (k !== this.key) {
      this.key = k;
      const a = this.ax, b = this.B.x;
      a.setTransform(1, 0, 0, 1, 0, 0); a.clearRect(0, 0, this.w, this.h);
      this.pen.frame(t);
      draw(this.pen, this.feet[0], this.feet[1], this.cs);
      b.setTransform(1, 0, 0, 1, 0, 0); b.globalCompositeOperation = 'source-over'; b.clearRect(0, 0, this.w, this.h);
      for (let i = 0; i < 16; i++) { const ang = i / 16 * Math.PI * 2; b.drawImage(this.A, Math.cos(ang) * this.rim, Math.sin(ang) * this.rim); }
      b.globalCompositeOperation = 'source-in'; b.fillStyle = '#FFFFFF'; b.fillRect(0, 0, this.w, this.h);
      b.globalCompositeOperation = 'source-over'; b.drawImage(this.A, 0, 0);
      this.B.t.needsUpdate = true;
    }
    const upc = s / (U * this.cs);                     // world units per sprite px (hero px * cs = sprite px, * s = layout px)
    this.mesh.scale.set(this.w * upc, this.h * upc, 1);
    this.mesh.position.set(X(x) + (this.w / 2 - this.feet[0]) * upc, Y(y) + (this.feet[1] - this.h / 2) * upc, z);
    this.mesh.visible = s > 0.001;
  }
}
const heroDraw = pose => (pen, cx, cy, cs) => HERO.draw(pen, Object.assign({ blink: 0, mouth: 0, id: 'hero' }, pose, { x: cx, y: cy, s: cs }));
const HERO_Z = 0.35;

// ---------------- scene groups ----------------
// everything of a scene lives in its group (lights too: a light in a hidden group does not shine)
const ALL = [];
function sceneGroup(name) { const g = new THREE.Group(); g.name = name; scene.add(g); ALL.push(g); return g; }
function only(name) { ALL.forEach(g => (g.visible = g.name === name)); }
const hero = new Sprite();       // the hero of the frame being rendered
const narr = new Sprite();       // the hero INSIDE the snapshot: its own canvas, so the main one is not redrawn twice a frame
scene.add(hero.mesh, narr.mesh);
function hidePeople() { hero.mesh.visible = false; narr.mesh.visible = false; }

// ======================= MATCH CUT: the picture in scene 1 = scene 2's first frame =======================
// How: scene 2 at its first drawing is rendered into the canvas exactly like a final frame, and the canvas is copied into a
// texture (copyFramebufferToTexture). The face shows that texture raw (no colour conversion, no second tone mapping). At the
// end of the dive the face fills the frame 1:1, so the last frame of scene 1 and the first frame of scene 2 are the same pixels.
// Why not the reference way (HalfFloat WebGLRenderTarget shown with MeshBasicMaterial({toneMapped: true})): three.js renders
// into a target without tone mapping, and the face then tone-maps EVERYTHING — also what is toneMapped: false in the direct
// render (the hero sticker, text plates). Measured in the template test: the sticker came out 11 levels darker on average
// (white rim 255 -> ~240, pencil lines darker), i.e. the hero visibly changed at the cut; the lit props matched.
// Mipmaps are rebuilt after every copy: a big texture shown small without mipmaps shimmers.
const snapTex = new THREE.FramebufferTexture(CW, CH);
snapTex.generateMipmaps = true; snapTex.minFilter = THREE.LinearMipmapLinearFilter; snapTex.magFilter = THREE.LinearFilter;
const snapMat = new THREE.ShaderMaterial({
  uniforms: { map: { value: snapTex } }, toneMapped: false,
  // final-frame pixels go out as they are: no colorspace_fragment / tonemapping_fragment includes on purpose
  vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader: 'uniform sampler2D map; varying vec2 vUv; void main() { gl_FragColor = texture2D(map, vUv); }',
});

// ======================= S1 objects: the hero is drawn, a code card, the framed picture =======================
const g1 = sceneGroup('s1_intro');
// layout: every number through LP(landscape, portrait); text stays above the 85 % line (land y < 378, port y < 672) and
// inside the 5 % margins even at the camera's push-in zoom
const S1H = { x: LP(-600, -250), y: LP(380, 830), s: LP(1.35, 1.2) };                     // hero: feet + scale
const PIC = LP({ x: 300, y: -90, w: 720 }, { x: 0, y: -230, w: 440 });                    // picture: centre + face width
PIC.h = PIC.w * CH / CW;                                                                  // face aspect = frame aspect
const CARD = LP({ x: -800, y: -470, w: 600, h: 140, size: 68 }, { x: -470, y: -820, w: 940, h: 130, size: 66 });
const TITLE = LP({ x: 300, y: 270, size: 112 }, { x: 0, y: 300, size: 92 });             // baseline centre
const picFace = new THREE.Mesh(new THREE.PlaneGeometry(X(PIC.w), X(PIC.h)), snapMat);
picFace.position.z = 0.1;                                    // 0.02 in front of the frame's face (0.08): no z-fighting
const picture = group(rbox(X(PIC.w) + 0.44, X(PIC.h) + 0.44, 0.16, 0.08, gloss('#FFFFFF', { roughness: 0.25 })), picFace);
g1.add(picture);
const card = group(rbox(X(CARD.w), X(CARD.h), 0.3, 0.2, gloss('#1D2140', { roughness: 0.15 })), plate(CARD.w * 0.94, CARD.h * 0.8, 0.16));
g1.add(card);
const cardText = card.children[1];
const title1 = plate(LP(1240, 1000), 190, 0); g1.add(title1);                            // text baseline at y = 135 inside
// a glossy pencil: capsule body, wooden cone, graphite tip, ferrule, eraser. Local origin = the graphite tip, axis +y.
const pencil = (() => {
  const g = new THREE.Group();
  const lead = cone(0.06, 0.18, gloss('#2D2B2A')); lead.rotation.z = Math.PI; lead.position.y = 0.09; g.add(lead);
  const wood = cone(0.16, 0.55, gloss('#E9C58F', { roughness: 0.45 })); wood.rotation.z = Math.PI; wood.position.y = 0.275; g.add(wood);
  const body = caps(0.16, 2.4, gloss('#F2C314')); body.position.y = 0.55 + 1.2; g.add(body);
  const ferrule = cyl(0.17, 0.17, 0.2, METAL); ferrule.position.y = 2.95; g.add(ferrule);
  const eraser = cyl(0.16, 0.16, 0.22, gloss('#EE8FA6', { roughness: 0.5 })); eraser.position.y = 3.16; g.add(eraser);
  return g;
})();
g1.add(pencil);
// decor: fixed places outside the text block, never random (random decor drifts into the text when the layout changes)
const DECO1 = LP([[820, -400, 0.42, '#F2C314', 's'], [-870, 430, 0.32, '#2F6FD6', 's'], [870, 60, 0.36, '#E5483A', 'c']],
  [[390, -480, 0.38, '#F2C314', 's'], [-430, 140, 0.3, '#2F6FD6', 's'], [380, 420, 0.34, '#E5483A', 'c']]);
const deco1 = DECO1.map(([x, y, r, c, kind]) => { const m = kind === 'c' ? rbox(r * 1.8, r * 1.8, r * 1.8, r * 0.4, gloss(c)) : sph(r, gloss(c)); place(m, x, y, -0.4); g1.add(m); return m; });

// ======================= S2 objects: the bulb, the prompt, the scan, the poster =======================
const g2 = sceneGroup('s2_light');
const S2H = { x: LP(-560, -260), y: LP(390, 820), s: LP(1.35, 1.25) };
const BULB = { x: LP(430, 40), y: LP(-60, -240), s: LP(1.0, 1.0) };                       // glass centre, scale
const PROMPT = LP({ x: -820, y: -470, w: 860, h: 130, size: 70 }, { x: -390, y: -800, w: 780, h: 130, size: 66 });
const POSTER = LP({ x: -790, y: -360, size: 112, align: 'left' }, { x: 0, y: -660, size: 96, align: 'center' });
const S2_CAM0 = { x: 0, y: 0, zoom: 1, sway: 0 };                                        // = the snapshot's camera
const S2_CAM1 = { x: 0, y: LP(-10, -20), zoom: 1.03, sway: 0 };                          // after the push-in
const glassOff = gloss('#F3EFE6', { roughness: 0.32 });                                   // frosted, unlit
const glassOn = new THREE.MeshPhysicalMaterial({ color: '#FFE48A', emissive: '#FFC21A', emissiveIntensity: 1.1, roughness: 0.3, clearcoat: 1 });
const bulb = (() => {                                       // local origin = glass centre; ~4.8 units tall
  const g = new THREE.Group();
  const glass = sph(1, glassOff, 64); glass.scale.set(1.55, 1.7, 1.55); g.add(glass);
  const neck = cyl(0.78, 0.62, 0.8, gloss('#E8E4DA', { roughness: 0.3 })); neck.position.y = -1.75; g.add(neck);
  const core = cyl(0.6, 0.6, 0.75, METAL); core.position.y = -2.44; g.add(core);
  for (let k = 0; k < 3; k++) { const band = torus(0.62, 0.09, METAL); band.rotation.x = Math.PI / 2; band.position.y = -2.2 - k * 0.24; g.add(band); }
  const tip = cyl(0.42, 0.22, 0.3, gloss('#2D2B2A')); tip.position.y = -2.95; g.add(tip);
  const stand = rbox(2.6, 0.45, 1.5, 0.16, gloss('#FFFFFF', { roughness: 0.3 })); stand.position.y = -3.32; g.add(stand);
  g.userData.glass = glass;
  return g;
})();
place(bulb, BULB.x, BULB.y, 0.1); bulb.scale.setScalar(BULB.s); g2.add(bulb);
const bulbLight = new THREE.PointLight('#FFC24A', 0, 14, 2); bulbLight.position.set(X(BULB.x), Y(BULB.y), 1.2); g2.add(bulbLight);
const rayMat = gloss('#FFC21A', { emissive: '#FFB000', emissiveIntensity: 0.9 });
const rays = Array.from({ length: 10 }, () => { const r = caps(0.07, 0.42, rayMat); g2.add(r); return r; });
const burst = torus(1, 0.05, gloss('#FFB347', { emissive: '#FF9A1F', emissiveIntensity: 1.2 })); g2.add(burst);
const promptBar = group(rbox(X(PROMPT.w), X(PROMPT.h), 0.25, 0.3, gloss('#FFFFFF', { roughness: 0.15 })), plate(PROMPT.w * 0.95, PROMPT.h * 0.86, 0.135));
g2.add(promptBar);
const promptText = promptBar.children[1];
const scanBar = new THREE.Mesh(new THREE.BoxGeometry(0.06, 30, 0.06), new THREE.MeshBasicMaterial({ color: PL.accent1, toneMapped: false }));
g2.add(scanBar);
const pills = [0, 1, 2].map(() => {
  const p = group(rbox(2.3, 1.0, 0.16, 0.45, gloss(PL.accent1)), plate(220, 90, 0.09));
  paint(p.children[1], '0 px', (x, w, h) => text(x, '0 px', w / 2, h * 0.73, 68, { align: 'center', color: '#FFFFFF' }));
  g2.add(p); return p;
});
const title2 = plate(LP(1120, 1000), 200, 0); g2.add(title2);                            // baseline at y = 140 inside
const TITLE2_W = textW('Мультик кодом', POSTER.size, "'Sans'");
const underline = rbox(X(TITLE2_W), 0.13, 0.12, 0.06, gloss(PL.warm2)); g2.add(underline);
underline.castShadow = false;                                // its shadow read as a stray line across the empty wall
const DECO2 = LP([[800, 330, 0.36, '#36A852', 'c'], [-880, -60, 0.3, '#EE8FA6', 's'], [260, -440, 0.26, '#7B5BD6', 's']],
  [[380, 420, 0.32, '#36A852', 'c'], [-420, -40, 0.28, '#EE8FA6', 's'], [380, -520, 0.24, '#7B5BD6', 's']]);
DECO2.forEach(([x, y, r, c, kind]) => { const m = kind === 'c' ? rbox(r * 1.8, r * 1.8, r * 1.8, r * 0.4, gloss(c)) : sph(r, gloss(c)); place(m, x, y, -0.4); m.rotation.set(0.5, 0.6, 0); g2.add(m); });

// the «0 px» marks: where the scan line passes and when (shared by the picture and the cue sheet)
function scanMarks() {
  const x0 = LP(-1000, -580), x1 = LP(1000, 580), t0 = W('Остальной').s, t1 = W('пиксель').s + 0.2;
  const pts = LP([[S2H.x + 230, S2H.y - 330 * S2H.s], [BULB.x - 300, 230], [BULB.x + 330, -280]],
    [[S2H.x + 220, S2H.y - 330 * S2H.s], [BULB.x - 330, -300], [BULB.x + 300, 60]]);
  return pts.map(([x, y]) => ({ x, y, t: lerp(t0, t1, clamp((x - x0) / (x1 - x0))) }));
}

// ======================= S1: the hero is drawn by code =======================
function s1(tt) {
  const pk = popk(tt, PIC_IN, 0.5);
  if (pk > 0.001) snapshot(tt);                    // first: it renders scene 2 into the canvas; then this scene sets itself up
  only('s1_intro');
  // the framed picture pops in with a half turn, then hangs still (the dive needs scale 1 and no rotation)
  show(picture, pk); place(picture, PIC.x, PIC.y, 0.25); picture.rotation.y = (1 - pk) * 0.8;
  // the code card: pops in on «каждая», the line is typed while «каждая линия» is said
  const ca = W('каждая').s - 0.15;
  show(card, popk(tt, ca, 0.4)); place(card, CARD.x + CARD.w / 2, CARD.y + CARD.h / 2, 0.3);
  const code = 'hero.draw()', cn = Math.floor(code.length * tw(tt, W('каждая').s, W('линия').e - W('каждая').s, E.lin) + 1e-6);
  paint(cardText, 'c' + cn, (x, w, h) => {                           // the key = what is visible, nothing else
    text(x, '>', 26, h * 0.7, CARD.size, { font: "'Code'", color: '#7FB2FF' });
    text(x, code.slice(0, cn), 26 + textW('> ', CARD.size, "'Code'"), h * 0.7, CARD.size, { font: "'Code'", color: '#EDEFFF' });
  });
  // the title, word by word with the voice
  const items = [['нарисован', 'нарисован'], ['кодом', 'кодом', 1]], chars = wordChars(tt, items);
  title1.visible = chars.some(c => c > 0);
  place(title1, TITLE.x, TITLE.y - 135 + 95, 0.25);
  paint(title1, chars.join(','), (x, w) => drawWords(x, items, chars, w / 2, 135, TITLE.size, "'Hand'", PL.accent1));
  // the pencil draws the hero (tip loops near the head on twos), then flies to its place and lies there
  const fly = E.ioQ(inv(1.6, 2.1, tt)), a = tt * 8;
  const drawTip = [S1H.x + 40 * S1H.s + Math.cos(a) * 70, S1H.y - 250 * S1H.s + Math.sin(a) * 50];
  const rest = LP([-300, -250], [140, 560]), restAng = LP(Math.PI / 2 + 0.12, -(Math.PI / 2 + 0.2));
  place(pencil, lerp(drawTip[0], rest[0], fly), lerp(drawTip[1], rest[1], fly) - Math.sin(fly * Math.PI) * 120, lerp(0.9, 0.25, fly));
  pencil.rotation.set(0, 0, lerp(-0.5, restAng, fly) + Math.sin(tt * 1.7) * 0.03 * fly);
  pencil.scale.setScalar(LP(1.0, 0.9));
  deco1.forEach((m, i) => { m.position.y = Y(DECO1[i][1]) + Math.sin(tt * 1.3 + i) * 0.08; m.rotation.set(tt * 0.4 + i, tt * 0.6 + i, 0); });
  // camera: a slow push, then the dive into the picture (zoomTo onto the face's world position)
  let cam = camKeys(tt, [[0, { x: 0, y: 0, zoom: 1, sway: 0.6 }], [DIVE0, { x: LP(30, 0), y: LP(-10, -20), zoom: 1.04, sway: 0.6 }]], E.lin);
  const dk = E.ioC(inv(DIVE0, DIVE1, tt));
  if (dk > 0) cam = zoomTo(cam, camOnMesh(picFace, X(PIC.w), X(PIC.h), 'min'), dk);   // aspect is equal: 'min' fills it exactly
  applyCam(cam, tt);
  // the hero: drawn on (the cover frame is not empty: the sketch is under way at t = 0), talks, points at the code card
  const point = E.outBack(tw(tt, W('каждая').s, 0.35)) * (1 - tw(tt, DIVE0 - 0.35, 0.3));
  const pose = {
    reveal: lerp(0.45, 1, tw(tt, 0, 1.6, E.outQ)), mouth: mouthAt(tt), blink: blinkAt(tt), squash: 0.012 * Math.sin(tt * 2.4),
    look: tt < PIC_IN + 0.4 ? [0.2, -0.1] : point > 0.5 ? LP([-0.5, -0.9], [0.1, -1]) : [0.9, -0.3],
    // the arm swings through the LEFT (2.2 -> 4.25 rad = up-left); lerp to -2.0 would swing it through the front and right
    armL: { sh: lerp(2.2, LP(4.25, 4.5), point), el: lerp(-0.35, 0.25, point) },
  };
  hero.update(tt, JSON.stringify(pose), heroDraw(pose), S1H.x, S1H.y, S1H.s, HERO_Z);
}

// ======================= S2: one phrase lights the bulb; nothing else moves =======================
// every S2 prop as it stands at time tt: called by s2() and by the snapshot (with S2_FIRST), so they cannot drift apart.
// It sets EVERYTHING it ever changes on every call (position, scale, visibility, material, texture) — no leftovers.
function s2Props(tt) {
  const lit = tt >= TURN, light = lit ? E.outBack(inv(TURN, TURN + 0.3, tt)) : 0;
  const out = 1 - E.inQ(inv(OUT0, OUT1, tt));                          // the interface leaves before the poster
  bulb.userData.glass.material = lit ? glassOn : glassOff;
  bulbLight.intensity = 26 * clamp(light);
  const cx = X(BULB.x), cy = Y(BULB.y);
  rays.forEach((r, i) => {
    const ang = i / rays.length * Math.PI * 2 + 0.31, R = 2.35 * BULB.s;
    r.visible = light > 0.01; r.position.set(cx + Math.cos(ang) * R, cy + Math.sin(ang) * R * 1.05, 0.3);
    r.rotation.set(0, 0, ang - Math.PI / 2); r.scale.setScalar(Math.max(0.001, light) * BULB.s);
  });
  const f = lit ? 1 - inv(TURN, TURN + 0.55, tt) : 0;                  // the click: a ring flies out of the bulb
  burst.visible = f > 0; burst.position.set(cx, cy, 0.6); const br = (1.9 + (1 - f) * 1.6) * BULB.s; burst.scale.set(br, br, 1);
  // the prompt: pops right AFTER the cut (so the snapshot = scene 2's first frame has no interface), typed with the phrase
  show(promptBar, popk(tt, S2_FIRST + 0.15, 0.4) * out);
  place(promptBar, PROMPT.x + PROMPT.w / 2, PROMPT.y + PROMPT.h / 2 - (1 - out) * LP(320, 420), 0.4);
  const str = '> лампочка: жёлтая', typed = W('фразу').e + 0.2, pp = tw(tt, W('Скажи').s, typed - W('Скажи').s, E.lin);
  const n = Math.floor(Array.from(str).length * pp + 1e-6), cursor = tt > typed && !lit && Math.floor(tt * 12 + 1e-6) % 2 === 0;
  paint(promptText, n + '|' + cursor + '|' + lit, (x, w, h) => {
    const size = fit(x, str, PROMPT.size, w - 70, "'Code'");          // a longer prompt shrinks instead of running off the bar
    text(x, str, 30, h * 0.7, size, { font: "'Code'", color: lit ? '#D9730D' : '#1E1B2E', p: n / Array.from(str).length });
    if (cursor) { x.font = `${size}px 'Code'`; x.fillStyle = '#1E1B2E'; x.fillRect(30 + x.measureText(str).width + 10, h * 0.2, 8, h * 0.6); }
  });
  // «остальной кадр не сдвинется ни на пиксель»: a scan line, «0 px» where it passed
  const t0 = W('Остальной').s, t1 = W('пиксель').s + 0.2, sk = E.ioQ(inv(t0, t1, tt));
  scanBar.visible = tt > t0 && sk < 1; place(scanBar, lerp(LP(-1000, -580), LP(1000, 580), sk), 0, 1.2);
  scanMarks().forEach((m, i) => {
    show(pills[i], (tt >= m.t ? popk(tt, m.t, 0.3) : 0) * out, LP(1.0, 0.9));
    place(pills[i], m.x, m.y - (1 - out) * LP(320, 420), 1.0);
  });
  // the poster: the title is written with the last sentence, then nothing fast moves
  const items = [['Мультик', 'мультик'], ['кодом', 'кодом', 2]], chars = wordChars(tt, items);
  title2.visible = chars.some(c => c > 0);
  const tx = POSTER.align === 'left' ? POSTER.x - 20 + LP(1120, 1000) / 2 : POSTER.x;
  place(title2, tx, POSTER.y - 140 + 100, 0.3);
  paint(title2, chars.join(','), (x, w) => drawWords(x, items, chars, POSTER.align === 'left' ? 20 : w / 2, 140, POSTER.size, "'Sans'", '#1E1B2E', POSTER.align));
  const ul = tw(tt, W('кодом', 2).s, 0.45);
  underline.visible = ul > 0.001; underline.scale.set(Math.max(0.001, ul), 1, 1);
  const ux0 = POSTER.align === 'left' ? POSTER.x : POSTER.x - TITLE2_W / 2;
  place(underline, ux0 + TITLE2_W * ul / 2, POSTER.y + 28, 0.3);
  return { lit, light };
}
// the S2 hero pose (also shared with the snapshot): talks, arms up on the click, relaxes BEFORE the freeze (a frozen frame
// must not move), waves with the last sentence and stands still on the poster
function s2Pose(tt) {
  const lit = tt >= TURN, freeze = tt >= FREEZE0 && tt < FREEZE1;
  const pop = E.outBack(inv(TURN, TURN + 0.3, tt));
  const relaxEnd = Math.max(TURN + 0.35, Math.min(TURN + 1.15, FREEZE0 - 0.05)), relax = E.ioQ(inv(relaxEnd - 0.4, relaxEnd, tt));
  const raise = E.outBack(inv(POSTER0, POSTER0 + 0.35, tt)), upL = pop * (1 - relax), upR = Math.max(upL, raise);
  const wave = Math.sin((tt - POSTER0) * 9) * 0.3 * Math.sin(Math.PI * inv(POSTER0, LAST, tt));
  return {
    color: tw(tt, TURN, 0.5), mouth: freeze ? 0 : mouthAt(tt), blink: freeze ? 0 : blinkAt(tt), brow: lit ? 0.7 : 0.1,
    look: lit ? [0.85, -0.9] : tt < W('лампочка').s ? [0.4, -0.5] : [0.85, -0.8], shape: lit && tt < TURN + 0.7 ? 'o' : 'smile',
    armR: { sh: lerp(0.94, -1.25, upR) + wave, el: lerp(0.35, -0.55, upR) }, armL: { sh: lerp(2.2, 4.2, upL), el: lerp(-0.35, 0.5, upL) },
    squash: lit && tt < TURN + 0.3 ? -0.08 * Math.sin(Math.PI * inv(TURN, TURN + 0.3, tt)) : 0,
  };
}
function s2(tt) {
  only('s2_light');
  // opens exactly like the snapshot (zoom 1, no sway), pushes in a little until the click, then holds still to the end
  applyCam(camKeys(tt, [[S2_FIRST, S2_CAM0], [TURN, S2_CAM1]]), tt);
  s2Props(tt);
  const freeze = tt >= FREEZE0 && tt < FREEZE1;
  const pose = s2Pose(tt);
  hero.update(freeze ? FREEZE0 : tt, JSON.stringify(pose), heroDraw(pose), S2H.x, S2H.y, S2H.s, HERO_Z);   // frozen boil
}

// tt = the current drawing of scene 1. The picture boils live, one drawing ahead (SNAP_AHEAD), so on the last frame of scene 1
// it shows exactly the drawing scene 2 opens with. Everything else in it is scene 2 at S2_FIRST.
let snapKey = null;
function snapshot(tt) {
  const tb = tt + SNAP_AHEAD, k = Math.floor(tb * 12 + 1e-6);
  if (k === snapKey) return;                       // the texture already holds this frame (a pure function of k)
  snapKey = k;
  const vis = ALL.map(g => g.visible), wc = wallMat.color.clone();
  only('s2_light'); hidePeople();
  s2Props(S2_FIRST);
  const pose = s2Pose(S2_FIRST);
  narr.update(tb, JSON.stringify(pose), heroDraw(pose), S2H.x, S2H.y, S2H.s, HERO_Z);
  setWall(wallFor('s2_light', S2_FIRST));
  applyCam(S2_CAM0, S2_FIRST);
  renderer.setRenderTarget(null); renderer.render(scene, camera);   // the canvas now holds scene 2's first frame
  renderer.copyFramebufferToTexture(snapTex);
  snapTex.needsUpdate = true; renderer.initTexture(snapTex);       // rebuilds the mipmaps from the fresh copy
  ALL.forEach((g, i) => (g.visible = vis[i])); narr.mesh.visible = false; setWall(wc);
}

// ---------------- walls ----------------
// each scene has its own pastel wall. BLEND: scenes whose wall blends in over 0.4 s after a plain cut. PRE: a dive into a
// picture of the next scene brings that scene's wall along (here the whole cut). WARM: the payoff — after the turn the
// cool wall warms up (before the turn quiet and cold, after it bright and warm).
const WALL = { s1_intro: '#F6E3CF', s2_light: '#D6EAF8' };
const BLEND = {};
const PRE = { s1_intro: ['s2_light', DIVE0, DIVE1] };
const WARM = { s2_light: ['#FBEBCF', TURN, 0.7] };
function wallFor(name, tt) {
  const i = TIMING.scenes.findIndex(s => s.name === name), c = new THREE.Color(WALL[name]);
  if (BLEND[name] && i > 0) c.copy(new THREE.Color(WALL[TIMING.scenes[i - 1].name]).lerp(c, E.ioQ(inv(TIMING.scenes[i].start, TIMING.scenes[i].start + 0.4, tt))));
  const pre = PRE[name]; if (pre) c.lerp(new THREE.Color(WALL[pre[0]]), E.ioQ(inv(pre[1], pre[2], tt)));
  const w = WARM[name]; if (w) c.lerp(new THREE.Color(w[0]), E.ioQ(inv(w[1], w[1] + w[2], tt)));
  return c;
}

// ---------------- sound cue sheet (render.py dumps window.CUES; sound/synth.py turns it into the SFX track) ----------------
// Same constants as the picture: when a beat moves, its sound moves with it. The picture changes on the twos grid, so an
// event at t becomes visible at ceil(t*12)/12 — the sound goes there too (otherwise it leads the drawing by up to 83 ms).
// Every page has its own sheet: the 3D version pops and types where the pencil version draws.
const CUES = []; window.CUES = CUES;
const cue = (t, k, g = 1, extra) => CUES.push(Object.assign({ t: +(Math.ceil(t * 12 - 1e-6) / 12).toFixed(3), k, g }, extra || {}));
{
  cue(0, 'pencil_long', 0.55);                                         // the pencil draws the hero
  cue(PIC_IN, 'pop', 0.5);
  cue(W('нарисован').s, 'scribble', 0.5); cue(W('кодом').s, 'scribble', 0.45);
  cue(1.6, 'whoosh', 0.35);                                            // the pencil flies to its place
  cue(W('каждая').s - 0.15, 'pop', 0.5); cue(W('каждая').s, 'type_run', 0.6);
  cue(DIVE0, 'zoom', 0.8);
  cue(S2_FIRST + 0.15, 'pop', 0.45); cue(W('Скажи').s, 'type_run', 0.7);
  cue(TURN, 'click', 1.0); cue(TURN + 0.02, 'shine', 0.9); cue(TURN + 0.05, 'color_fill', 0.6);
  cue(W('Остальной').s, 'scan', 0.6);
  scanMarks().forEach(m => cue(m.t, 'tick', 0.6));
  cue(OUT0, 'slide', 0.5);
  cue(W('мультик').s, 'type_run', 0.5); cue(LAST, 'chime', 0.9);
  CUES.sort((a, b) => a.t - b.t);
}

// ---------------- scene table and the render entry point ----------------
// names must match TIMING.scenes (timing/timing_config.json) and the pencil page
const SCENES = { s1_intro: s1, s2_light: s2 };
window.renderAt = function (t) {
  const tt = K.twos(t);
  const sc = TIMING.scenes.find(s => t >= s.start && t < s.end) || TIMING.scenes[TIMING.scenes.length - 1];
  const fn = SCENES[sc.name];
  if (!fn) throw new Error(`no scene function for «${sc.name}»: TIMING.scenes and SCENES must list the same names`);
  hidePeople();
  setWall(wallFor(sc.name, tt));      // by the scene chosen from the raw t: tt of a first frame can still be inside the old scene
  fn(tt, t);
  renderer.setRenderTarget(null);
  renderer.render(scene, camera);
};
window.renderAt(window.__hfThreeTime || 0);
window.__ready = true;
