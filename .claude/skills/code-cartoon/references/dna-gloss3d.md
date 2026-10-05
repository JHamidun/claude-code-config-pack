# ДНК глянцевого 3D с рисованным героем

Тот же сценарий, те же тайминги и та же раскладка, что в карандаше, но мир собран из глянцевых игрушек
(Three.js r181): пастельная стена на сцену, мягкие тени, а герой — тот же карандашный рисунок из `engine/hero.js`,
вырезанный как стикер с белой каймой. Числа взяты из `<эталон>/gloss/scenes3d.js` и
`gloss/index.html` (прочитаны 05.10.2026, после пятого патча). (с. N) — страница методички (`methodology.md`).
Методичка про 3D говорит мало: камера, свет и объекты через Three.js (с. 2), и 3D кодом — это частицы, геометрия и
логотипы, а не Pixar (с. 22). Остальное здесь — опыт эталона.

## ДНК в девяти правилах

| № | Правило | Где в коде |
| --- | --- | --- |
| 1 | За всем стоит пастельная стена-задник, у каждой сцены свой цвет; стена принимает тени | `wall` z −1,6, `WALL`, `wallFor` |
| 2 | Материал — глянец: clearcoat 1, roughness 0,2, без металла; формы — скруглённые коробки, капсулы, сферы, торы | `gloss()`, `rbox`, `caps`, `sph`, `torus` |
| 3 | Свет — окружение RoomEnvironment, полусфера и один ключевой свет сверху слева с мягкой тенью; тонмаппинг Neutral, не ACES | блок «renderer, camera, light» |
| 4 | Камера FOV 30, расстояние от высоты кадра, лёгкое покачивание 0,16 | `applyCam` |
| 5 | Герой — карандашный рисунок-стикер с белой каймой и тенью-силуэтом, перерисовка на двойках | `class Sprite` |
| 6 | Всё на двойках: позы, камера, покачивание, вращение декора считаются от `tt` | `renderAt`, сцены |
| 7 | Текст — в канвас-текстурах без освещения, шрифты загружены до первой текстуры, длинные слова подогнаны по ширине | `ctex`, `face`, `text` |
| 8 | Стыки сцен — «живой снимок» следующей сцены в рамке или на экране плюс пролёт `zoomTo` | `snapLand`, `snapPoster`, `zoomTo`, `camOnMesh` |
| 9 | Декор — в фиксированных местах вне текста, цвета из палитры | `deco` в s7 |

Проверено (9:16, сервер эталона на :8731, 05.10.2026): кадры 10,0 и 10,0417 с совпадают до пикселя, 10,0833 и
10,125 с — тоже; между 10,0 и 10,0833 с отличаются 6,67 % пикселей. 3D тоже идёт на двойках.

## 1. Страница

- three r181 лежит в `vendor/three/`: `three.module.js`, `three.core.js`, аддоны `environments/RoomEnvironment.js`,
  `geometries/RoundedBoxGeometry.js`. Подключение — через `importmap`.
- Перед модулем грузятся классические скрипты карандаша: `../pencil/timing.js`, `../engine/core.js`,
  `../engine/pencil.js`, `../engine/hero.js`, `../pencil/lib.js`. Из них 3D берёт тайминг, героя, палитру и `LP`.
- ES-модули с `file://` не грузятся: страницу открывают по http (`python -m http.server 8731 --bind 127.0.0.1` из
  корня проекта). Безголовому Chromium нужны флаги GPU: `--use-angle=d3d11 --enable-gpu --ignore-gpu-blocklist
  --enable-unsafe-swiftshader`. Команды и подъём сервера — `workflow.md`.
- Скорость (лог `out/chain_v5.log`, 6 воркеров, 1575 кадров): 3D — 53–54 с (33–34 мс на кадр), карандаш — 91–105 с
  (58–67 мс на кадр).
- Лист звуков `window.CUES` 3D-страница не заполняет: в эталоне `out/gloss_*.cues.json` пустые, звук всех четырёх
  роликов сведён по листу карандашной версии. Проекту только в 3D лист звуков нужно заполнять самому.

## 2. Рендерер и свет

```js
const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(CW, CH, false);
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.85;
scene.add(new THREE.HemisphereLight('#FFF8EE', '#E2C9B2', 0.7));
const key = new THREE.DirectionalLight('#FFFFFF', 2.1);
key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02;
```

- `preserveDrawingBuffer: true` нужен, чтобы рендерер мог забрать кадр через `toDataURL` после `render()`.
- `NeutralToneMapping`: ACES выцветает пастель. Экспозиция 1.
- Отражения на глянце даёт окружение RoomEnvironment через PMREM (размытие 0,04, интенсивность 0,85).
- Ключевой свет следует за целью камеры, поэтому тени остаются чёткими и на крупных планах:

```js
function setKey(tx, ty, zoom) {
  key.position.set(tx - 6, ty + 8, 14); key.target.position.set(tx, ty, 0);    // top-left, in front
  const s = Math.max(PORT ? 10.8 : 19.2, 12) / zoom * 0.75;                     // shadow box shrinks on close-ups
  Object.assign(key.shadow.camera, { left: -s, right: s, top: s, bottom: -s, near: 1, far: 60 });
  key.shadow.camera.updateProjectionMatrix();
}
```

Свет сверху слева, тени уходят вправо вниз на стену — так же, как штрихуется тень в карандаше (`dna-pencil.md`,
раздел 4).

## 3. Стена-задник и цвет сцены

```js
const wallMat = new THREE.MeshStandardMaterial({ color: '#F5E8DA', roughness: 0.95 });
const wall = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), wallMat);
wall.position.z = -1.6; wall.receiveShadow = true;
// every frame: wallMat.color.copy(wallFor(tt)); scene.background.copy(wallMat.color);
```

- Без стены за предметами виден горизонт. Стена матовая (roughness 0,95), фон сцены каждый кадр того же цвета.
- У каждой сцены своя пастель (hex — `palettes.md`). Правила смены в `wallFor(t)`:
  - на простой склейке (s1 → s2, s2 → s3, s5 → s6) стена плавно переходит из цвета прошлой сцены за 0,4 с (`ioQ`);
  - на стыке-снимке (пролёт в миниатюру, отъезд из клипа, пролёт в экран) стена меняется сразу: снимок уже показал
    новую стену;
  - во время пролёта стена заранее перетекает в стену следующей сцены: `PRE = { s3_program: ['s4_sun', 30.12,
    30.62] }`.

```js
const PRE = { s3_program: ['s4_sun', 30.12, 30.62] };      // a dive into a frame of the next scene brings its wall along
function wallFor(t) {
  const i = TIMING.scenes.findIndex(s => t >= s.start && t < s.end), sc = TIMING.scenes[i < 0 ? TIMING.scenes.length - 1 : i];
  const prev = TIMING.scenes[Math.max(0, (i < 0 ? TIMING.scenes.length - 1 : i) - 1)];
  cA.set(WALL[prev.name]); cB.set(WALL[sc.name]);
  const pre = PRE[sc.name]; if (pre) cB.lerp(cC.set(WALL[pre[0]]), E.ioQ(inv(pre[1], pre[2], t)));
  const blend = { s2_oldway: 1, s3_program: 1, s6_academy: 1 }[sc.name];          // plain cuts only
  return cA.lerp(cB, blend ? E.ioQ(inv(sc.start, sc.start + 0.4, t)) : 1);
}
```

Имена сцен должны совпадать в четырёх местах: `SCENES` в `timing/build_timing.py`, `SCENES` в `pencil/scenes.js`,
`SCENES` и `WALL` (а также `PRE` и набор `blend`) в `scenes3d.js`. Пропущенное имя в `SCENES` роняет `renderAt`
(TypeError). Пропущенное имя в `WALL` ничего не роняет: `THREE.Color.set(undefined)` молча оставляет прошлый цвет, и
стена «залипает» на цвете соседней сцены.

## 4. Материалы и примитивы

```js
function gloss(color, o = {}) {        // cached per colour + options
  const k = color + JSON.stringify(o);
  if (!MATS.has(k)) MATS.set(k, new THREE.MeshPhysicalMaterial(Object.assign(
    { color, roughness: 0.2, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.05 }, o)));
  return MATS.get(k);
}
const shadowy = m => { m.castShadow = true; m.receiveShadow = true; return m; };
const rbox = (w, h, d, r, mat) => shadowy(new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 5,
  Math.min(r, w / 2 - 0.001, h / 2 - 0.001, d / 2 - 0.001)), mat));
```

| Примитив | Геометрия | Где в эталоне |
| --- | --- | --- |
| `rbox(w, h, d, r)` | `RoundedBoxGeometry`, 5 сегментов, радиус меньше половины любой стороны | корпуса, листы, плашки, клавиша, ноутбуки |
| `sph(r, mat, seg = 48)` | `SphereGeometry(r, 48, 24)`; сплюснутые сферы — холмы | головы, краски на палитре, солнце, декор |
| `cyl(r1, r2, h, mat, seg = 40)` | `CylinderGeometry` | ножки, ручки, валики свитка, чашка |
| `caps(r, len, mat)` | `CapsuleGeometry(r, len, 8, 24)` | тела человечков, крестики, лучи, столбики звуковой волны |
| `torus(R, r, mat)` | `TorusGeometry(R, r, 20, 64)` | кольца-пометки, вспышка щелчка, кольца звуков |
| `ExtrudeGeometry` с фаской | плоская фигура с толщиной | палитра художника, крыша дома |
| `TubeGeometry` по `CatmullRomCurve3` | трубка по кривой | галочка |

Варианты рецепта `gloss()`:

- «бумажные» и матовые поверхности — roughness 0,25–0,35: лист программы 0,3, листы стопки 0,35, холмы 0,25;
  доска — roughness 0,35 и clearcoat 0,6;
- металл — metalness 0,5–0,7, roughness 0,2–0,25: рычаг, кольца календаря, корпус ноутбука;
- светящееся — `emissive` того же оттенка: солнце 0,55, окно дома 0,3, вспышка щелчка 1, кольца звуков 0,8,
  лампочки сервера `MeshStandardMaterial` 2 (мигают на двойках: 2,2 / 0,15);
- стекло — `transmission`: линза лупы 1 (thickness 0,4, roughness 0,02, ior 1,4), плашка промпта 0,25;
- без света и тонмаппинга — `MeshBasicMaterial({ toneMapped: false })`: бегущая линия скана, лазеры монтажки, вспышка
  кадра.

Декор плаката (s7) — шесть игрушек цветов палитры, шары и скруглённые кубики по очереди. Места заданы списком
на каждый формат вне текстового блока, z = −0,3 (за плакатом на z = 0,2). Каждая игрушка появляется через `popk`
с шагом 0,12 с от 57,9 с, покачивается на ±12 px и медленно вращается. Время для этого упирается в 62,0 с.

Единицы: `U = 100`, одна единица мира — 100 px раскладки; `X(x) = x / 100`, `Y(y) = -y / 100` (ось y
переворачивается). Раскладка — те же числа, что в карандаше, через `LP(land, port)`. Появление предмета — равномерный
масштаб `show(o, k)` с `popk = E.outBack`, по умолчанию за 0,35 с.

## 5. Камера

```js
const VH = PORT ? 19.2 : 10.8, FOV = 30, D0 = (VH / 2) / Math.tan(FOV / 2 * Math.PI / 180);   // 20.15 / 35.83
function applyCam(c, tt) {               // call every frame; c.x, c.y in layout px, c.z in world units
  const tx = X(c.x), ty = Y(c.y), tz = c.z || 0, d = D0 / c.zoom;
  const sway = (c.sway == null ? 1 : c.sway) * 0.16;
  camera.position.set(tx + Math.sin(tt * 0.35) * sway, ty + 0.25 * sway + Math.cos(tt * 0.27) * sway * 0.4, tz + d);
  camera.lookAt(tx, ty, tz);
  setKey(tx, ty, c.zoom);
}
```

- При zoom 1 плоскость z = 0 ложится в кадр один к одному: видно 10,8 ед. по высоте в 16:9 и 19,2 ед. в 9:16.
- Что выдвинуто вперёд, то крупнее: видимый масштаб `D0 / (D0 - z)`. При z = 0,35 (место героя по умолчанию)
  предмет крупнее на 1,8 % в 16:9 и на 1,0 % в 9:16, при z = 1,6 — на 8,6 % и 4,7 %.
- Покачивание — 0,16 ед. по x, по y 0,04 ед. плюс ±0,064 ед.; периоды ≈ 18 и 23 с. Покачивание больше 0,16
  выталкивало раскладку за край кадра (обрезался терминал).
- Покачивание обнуляется:
  - на первом кадре после стыка-снимка (камера должна совпасть со снимком);
  - на пролёте (`zoomTo` гасит его);
  - на финальном плакате: в s7 оно нарастает 57,7–58,4 с и уходит 61,8–62,3 с, а время для покачивания и вращения
    декора упирается в 62,3 и 62,0 с, поэтому последние ≈ 3,3 с ничего не плывёт (с. 17).
- `camKeys` интерполирует ключи так же, как в карандаше, и отдельно плавно меняет `sway` между ключами.

Пролёт и кадровка по мешу:

```js
// zoom-through: the target slides linearly to the frame centre in screen space while the zoom grows exponentially
function zoomTo(c0, tg, k) {
  const z = Math.exp(lerp(Math.log(c0.zoom), Math.log(tg.zoom), k));
  const ox = (tg.x - c0.x) * c0.zoom * (1 - k), oy = (tg.y - c0.y) * c0.zoom * (1 - k);
  return { x: tg.x - ox / z, y: tg.y - oy / z, zoom: z, z: lerp(c0.z || 0, tg.z || 0, k), sway: (c0.sway == null ? 1 : c0.sway) * (1 - k) };
}
// a camera that frames a flat mesh of w x h world units: 'w' fills the width, 'h' the height, 'min' fits inside
function camOnMesh(mesh, w, h, fill = 'min') {
  scene.updateMatrixWorld(); mesh.getWorldPosition(_v);
  const zw = (PORT ? 10.8 : 19.2) / w, zh = (PORT ? 19.2 : 10.8) / h;
  return { x: _v.x * U, y: -_v.y * U, z: _v.z, zoom: fill === 'w' ? zw : fill === 'h' ? zh : Math.min(zw, zh), sway: 0 };
}
```

- `K.lerpCam` (зум по логарифму, позиция линейно) на пролёте уводит цель вбок посередине пути. `zoomTo` держит
  смещение цели на экране линейно убывающим, и цель приходит в центр без заноса.
- Цель брать из мировой позиции меша вместе с z (`getWorldPosition`), а не из раскладки: рамка может быть
  вложена в группу, повёрнута и выдвинута.
- Заполнение по формату: миниатюра — `'min'`; экран ноутбука — `'w'` в 16:9 и `'h'` в 9:16; клип монтажки при
  отъезде — `'min'` в 16:9 и `'w'` в 9:16.

## 6. Герой-стикер: `class Sprite`

```js
class Sprite {
  constructor(id, w = 1400, h = 1200, feet = [700, 1150], s = 2.4) {   // canvas size, feet point, drawing scale
    this.A = ctex(w, h); this.B = ctex(w, h); this.w = w; this.h = h; this.feet = feet; this.cs = s;
    this.pen = new PEN.Pen(this.A.x, w, h, PL);
    const mat = new THREE.MeshBasicMaterial({ map: this.B.t, transparent: true, alphaTest: 0.05, toneMapped: false, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), mat);
    this.mesh.castShadow = true;
    this.mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: this.B.t, alphaTest: 0.5 });
    this.lastKey = null;
  }
  update(t, keyStr, draw, x, y, s, z = 0.35) {
    const k = keyStr + '|' + Math.floor(t * 12 + 1e-6);              // redraw at most 12 times a second
    if (k !== this.lastKey) {
      this.lastKey = k;
      const A = this.A, B = this.B;
      A.x.setTransform(1, 0, 0, 1, 0, 0); A.x.clearRect(0, 0, this.w, this.h);
      this.pen.frame(t);
      draw(this.pen, this.feet[0], this.feet[1], this.cs);
      B.x.setTransform(1, 0, 0, 1, 0, 0); B.x.clearRect(0, 0, this.w, this.h); B.x.globalCompositeOperation = 'source-over';
      const rim = 9;                                                   // white sticker rim: 16 offset copies
      for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2; B.x.drawImage(A.c, Math.cos(a) * rim, Math.sin(a) * rim); }
      B.x.globalCompositeOperation = 'source-in'; B.x.fillStyle = '#FFFFFF'; B.x.fillRect(0, 0, this.w, this.h);
      B.x.globalCompositeOperation = 'source-over'; B.x.drawImage(A.c, 0, 0);
      B.t.needsUpdate = true;
    }
    const upc = s / (100 * this.cs) * 1.0;                              // world units per sprite px
    this.mesh.scale.set(this.w * upc, this.h * upc, 1);
    this.mesh.position.set(X(x) + (this.w / 2 - this.feet[0]) * upc, Y(y) + (this.feet[1] - this.h / 2) * upc, z);
    this.mesh.visible = s > 0.001;
  }
}
const heroDraw = pose => (pen, cx, cy, cs) => HERO.draw(pen, Object.assign({ blink: 0, mouth: 0, id: 'hero' }, pose, { x: cx, y: cy, s: cs }));
```

- Холст с запасом: 1400×1200, ступни в (700, 1150), масштаб рисунка 2,4. На холсте 1024 обрезались свиток и
  лопатка в поднятой руке.
- Кайма — 16 копий рисунка со сдвигом 9 px по кругу, залитых белым (`source-in`), и сам рисунок поверх.
- Материал без света (`MeshBasicMaterial`, `toneMapped: false`): карандашные цвета остаются ровно такими, как
  нарисованы.
- Тень — силуэт героя, а не прямоугольник: `customDepthMaterial` с той же картой и `alphaTest 0.5`.
- Ключ перерисовки — `JSON.stringify(pose)` плюс номер двойки. Рот и моргание входят в позу, поэтому герой
  перерисовывается не чаще 12 раз в секунду и кипит как в карандаше.
- Заморозка «больше ничего не изменилось» в 3D: в s4 спрайт получает постоянное время `td = CLICK + 0.45`, а в позе
  рот и моргание стоят в 0. Номер двойки в ключе не меняется, поэтому рисунок не кипит.
- Размер меша подобран так, что масштаб `s` в раскладке равен `s` героя в карандашной версии; ступни стоят в (x, y).
- z героя: 0,35 по умолчанию (s1–s3); 1,6 в s4, чтобы стоять перед холмами; 0,5–0,6 в s5–s7; ученики 0,9.
- Экземпляры: `hero` — главный; `mini` (900×800, ступни (450, 770), масштаб 1,6); `narr` — для снимков и для
  рассказчика в 9:16; ученики (360×360, ступни (180, 340), масштаб 2,2). В снимке — всегда отдельный экземпляр
  (`narr`): иначе главный спрайт перерисовывается дважды за кадр.

## 7. Текст и 2D внутри 3D

```js
// fonts first: canvas textures are drawn at build time; an unloaded face silently falls back to a default serif
await document.fonts.ready;
await Promise.all(['Hand', 'HandB', 'Code', 'CodeB', 'Sans', 'SansM'].map(f => document.fonts.load(`40px '${f}'`, 'АБВабв{}#>')));

function ctex(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return { c, x: c.getContext('2d'), t };
}
function face(tex, w, h, z, o = {}) {    // unlit textured plane: exact colours, no tone mapping
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex.t, transparent: !!o.transparent, toneMapped: false, depthWrite: !o.transparent }));
  m.position.z = z; return m;
}
```

- В строке образца для `fonts.load` есть кириллица (`'АБВабв{}#>'`): если шрифт разбит по `unicode-range`, без неё
  кириллический набор не подгрузится. В эталоне `@font-face` без `unicode-range`, файл грузится целиком.
- Разрешение текстур — 1,4–2 px текстуры на 1 px раскладки (лист программы ×1,6, промпт ×1,5, доска ×1,4,
  терминал ×2), поэтому текст остаётся чётким и при наезде.
- `text(ctx, str, px, py, size, o)` проявляет строку по числу букв (`o.p`).
- Подгонка длинных слов («автоматизация»): кегль `min(76, 76 × 520 / measureText(s).width)` — слово влезает в 520
  px холста шириной 600. Под подписью — светлая плашка `rgba(255,255,255,0.94)` со скруглением в половину кегля,
  поэтому подпись читается на любой стене.
- Текстуру перерисовывать только когда меняется содержимое (календарь сравнивает метку, экраны — состояние плюс
  номер двойки), затем `tex.t.needsUpdate = true`.
- Карандаш внутри 3D: `frameSlab(id, w, h)` — белая плита с лицевой текстурой и своим `PEN.Pen`. В ней рисуется
  карандашный герой («испорченные» кадры генератора), на экранах ноутбуков — свой `Pen`.
- Текстура, нужная нескольким сценам, рисуется функцией, которая сама проверяет, нарисовано ли (`drawMoon` с
  флагом), а не побочным эффектом прошлой сцены. Иначе стоп-кадр s6 без отрисованной перед ним s5 выйдет пустым.

## 8. Живые снимки для стыков

Рамка, экран или клип показывают следующую сцену ровно такой, какой она начнётся (или какой кончилась прошлая).
Камера ныряет в рамку, и склейка проходит без вспышки и без скачка.

```js
// HalfFloat: the lit scene is HDR before tone mapping; an 8-bit target clips the pastel wall to grey.
// Mipmaps: small thumbnails shimmer without them.
const RT_OPT = { samples: 4, type: THREE.HalfFloatType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter };
const RT = {};
['plain', 'broken', 'green'].forEach(k => (RT[k] = new THREE.WebGLRenderTarget(1920, 1080, RT_OPT)));
function snapLand(mode, tt) {
  const vis = ALL.map(g => g.visible), extra = [mini.mesh, hero.mesh], ev = extra.map(o => o.visible);
  only('s4'); extra.forEach(o => (o.visible = false));               // only the next scene, no main sprites
  const broken = mode === 'broken', green = mode === 'green';
  s4Props(green ? S4_END : S4_START);                                 // the SAME state function the scene calls
  // (mode 'broken' swaps the round sun for a square one here — the «mistake» frame)
  const pose = { color: 1, look: green ? [0.9, -0.8] : [0.7, -0.6], brow: green ? 0.8 : 0.2, armR: { sh: -1.1, el: -0.6 }, laurel: !broken, id: 'narr' };
  narr.update(tt, 'snap' + mode, heroDraw(pose), lx(S4H.u), ly(S4H.v), S4H.s * LAND.h / 1080, 1.6);   // own sprite
  const wc = wallMat.color.clone(); wallMat.color.set(WALL.s4_sun); scene.background.copy(wallMat.color);
  const cx = X(LAND.x + LAND.w / 2), cy = Y(LAND.y + LAND.h / 2), d = (LAND.h / U / 2) / Math.tan(FOV / 2 * Math.PI / 180);
  rtCam.position.set(cx, cy, d); rtCam.lookAt(cx, cy, 0); setKey(cx, cy, 1920 / LAND.w);   // exactly the next frame
  renderer.setRenderTarget(RT[mode]); renderer.render(scene, rtCam); renderer.setRenderTarget(null);
  ALL.forEach((g, i) => (g.visible = vis[i])); extra.forEach((o, i) => (o.visible = ev[i]));
  wallMat.color.copy(wc); scene.background.copy(wc); narr.mesh.visible = false;
  return RT[mode].texture;
}
// display: the renderer writes linear colour WITHOUT tone mapping into a target, so the screen material applies it once
// (shortened from the s3 thumbnails code; names simplified)
const thumbFace = thumbSlab.children[1];                     // the textured front of a frame slab
thumbFace.material = new THREE.MeshBasicMaterial({ toneMapped: true });
setMap(thumbFace, snapLand('plain', tt));   // m.map = tex; m.needsUpdate = true (a material without a map needs it)
```

Порядок снимка:

1. Запомнить видимость и цвет стены.
2. Оставить видимой только следующую сцену, главные спрайты спрятать.
3. Поставить реквизит той же функцией, что зовёт сама сцена (`s4Props(T)`). T — `tt` её первого или последнего
   кадра на двойках: `twos(ceil(start·fps) / fps)` и `twos((ceil(end·fps) − 1) / fps)`. В эталоне это
   `S4_START = 30.833` и `S4_END = 37.75`. Тогда первый кадр сцены совпадает со снимком.
4. Героя в снимке рисовать отдельным спрайтом (`narr`).
5. Поставить стену следующей сцены.
6. Камеру снимка поставить так, чтобы её видимая область совпала с кадром следующей сцены: расстояние
   `(h / U / 2) / tan 15°`.
7. Отрендерить в цель и вернуть всё как было.

Цели эталона: три снимка пейзажа 1920×1080 (`plain`, `broken`, `green`) и снимок плаката 1920×1160 — в пропорции
экрана ноутбука `SCR_A = 2.4 / 1.45`.

Стыки 3D эталона:

| Стык | Как устроен |
| --- | --- |
| s1 → s2 | ластика нет: реквизит s1 сжимается и исчезает за 7,33–7,57 с, до склейки |
| s3 → s4 | лист миниатюр — живые снимки s4; кадр № 6 показывает его как есть, остальные — сдвинутые кадрировки того же снимка (u0 = 0,12·i/7, v0 = 0,06, ширина 0,88), как панорама по кадру. Пролёт `zoomTo(cam, camOnMesh(face, w, h), ioC(30.12…30.62))`. Соседние миниатюры сжимаются за 30,12–30,4 с, кольцо и галочка уходят первыми (30,02–30,3 с), белая рамка кадра № 6 ужимается до лица (30,12–30,5 с), стена перетекает в стену s4. s4 начинается на 30,81 с с камерой `{x: 0, y: 0, zoom: 1, sway: 0}` |
| s4 → s5 | под конец s4 интерфейс уходит (37,2–37,55 с) и кадр становится чистым клипом 1. s5 открывается крупно на клипе (снимок `green`) и отъезжает: `zoomTo(cam, camOnMesh(clip, …), 1 − ioC(37.8…38.75))`, покачивание растёт вместе с отъездом |
| s5 → s6 | монтажка уезжает вниз за 47,45–47,93 с, ночная карточка переворачивается и становится доской (47,96–48,55 с, поворот по y на π) |
| s6 → s7 | экран ноутбука № 4 показывает снимок начала s7. Пролёт `zoomTo` с запасом `OVERSCAN = 1.04` за 57,05–57,5 с; запас стоит и на камере пролёта, и на видимой высоте камеры снимка, иначе видна рамка наклонённого экрана |

- Пролёт заканчивается минимум за 2 кадра до стыка: в эталоне 30,62 против 30,81 с и 57,5 против 57,665 с.
- Камера следующей сцены стартует ровно в кадровке снимка, с покачиванием 0.

## 9. Чего не делать

| Не делать | Что будет | Как надо |
| --- | --- | --- |
| тонмаппинг ACES | пастель выцветает | `NeutralToneMapping`, экспозиция 1 |
| 8-битная цель снимка | освещённая стена в снимке уходит в серый | `HalfFloatType`, `samples: 4` |
| показывать снимок материалом с `toneMapped: false` | снимок светлее и бледнее кадра, стык виден | `MeshBasicMaterial({ toneMapped: true })` |
| снимок без мипмапов | мелкие миниатюры мерцают | `generateMipmaps: true`, `LinearMipmapLinearFilter` |
| покачивание больше 0,16 | раскладка уезжает за край кадра | 0,16, а на стыках и плакате 0 |
| `K.lerpCam` для пролёта | цель уходит вбок посередине пролёта | `zoomTo` + `camOnMesh` |
| сцена без стены-задника | виден горизонт | плоскость 300×300 на z = −1,6, принимает тени |
| случайные места декора | шарик садится на текст | фиксированные места по формату вне текстового блока |
| один спрайт героя на сцену и снимок | главный спрайт перерисовывается дважды за кадр | отдельный экземпляр (`narr`) |
| канвас-текстуры до загрузки шрифтов | текст засечным шрифтом по умолчанию | `await document.fonts.load(...)` для всех семейств до сборки |
| текст на освещённом материале | цвет текста меняется от света | `face()`: `MeshBasicMaterial`, `toneMapped: false` |
| перевешивать объекты между группами в покадровом коде (s3 эталона делает `g3.add(team, …)`, s2 их не возвращает) | `renderAt` начинает зависеть от прошлых кадров: стоп-кадры s2 после кадра s3 теряют реквизит | раздать объекты по группам один раз при сборке, в кадре только показывать и прятать |
| текстура рисуется побочным эффектом прошлой сцены | прямой стоп-кадр выходит с пустой текстурой | функция, которая сама проверяет «уже нарисовано» |
| плавная смена стены на стыке-снимке | стена меняется дважды | на стыке-снимке менять сразу |

## 10. Как проверять 3D-кадры

Общий чеклист — `frame-checks.md`. Специально для 3D:

- кадры 2n и 2n+1 совпадают до пикселя (двойки);
- последний кадр пролёта и первый кадр следующей сцены совпадают по раскладке, стене и герою: снять оба кадра
  `still.py` и сравнить;
- тень героя на стене — силуэт, а не прямоугольник;
- на самом крупном наезде текст в текстурах не мылится;
- в снимке миниатюры стена того же цвета, что в самой сцене, а не серая;
- декор и подписи не наезжают на текст и не лезут в нижние 15 % кадра (с. 18, 23).
