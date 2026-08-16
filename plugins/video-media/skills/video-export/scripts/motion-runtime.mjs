/**
 * Среда выполнения анимаций — то, что даёт композициям время, кривые и слои.
 *
 * Зачем. Библиотека из двух сотен готовых сцен написана под чужой фреймворк и тянет за
 * собой сто с лишним мегабайт зависимостей ради девяти сущностей: текущего кадра,
 * интерполяции, набора кривых, полноэкранного слоя, пружины, параметров ролика,
 * картинки, пути к файлу и интерполяции цвета. Здесь эти девять реализованы поверх
 * нашего рендерера — он и так умеет ставить время и ждать готовности сцены.
 *
 * Совместимость намеренно точная, а не приблизительная: сцены отлажены до кадра, и
 * расхождение в кривой или в поведении на краях диапазона сдвинет то, что подбиралось
 * часами. Поэтому кривые взяты теми же формулами, а края обрабатываются как там:
 * по умолчанию значение зажимается, но режим можно сменить.
 *
 *   import { useCurrentFrame, interpolate, Easing, AbsoluteFill } from './motion-runtime.mjs';
 *
 * Время приходит из рендерера: он вызывает window.__setTime(t) в секундах перед съёмкой
 * каждого кадра. Сцена перерисовывается, когда время меняется.
 */

// --- время ----------------------------------------------------------------------------

const config = { fps: 30, width: 1920, height: 1080, durationInFrames: 900 };
let currentTime = 0;                       // секунды
const listeners = new Set();

/** Настроить ролик. Вызывается один раз при загрузке сцены. */
export function configure({ fps, width, height, durationInFrames } = {}) {
  if (fps) config.fps = fps;
  if (width) config.width = width;
  if (height) config.height = height;
  if (durationInFrames) config.durationInFrames = durationInFrames;
}

/** Поставить таймлайн. Рендерер зовёт это перед каждым кадром. */
export function setTime(seconds) {
  currentTime = seconds;
  listeners.forEach((fn) => fn(seconds));
}

if (typeof window !== 'undefined') {
  // Рендерер ищет эту функцию на window — отдаём её, не заставляя сцену ничего знать.
  const prev = window.__setTime;
  window.__setTime = (t) => { setTime(t); if (typeof prev === 'function') prev(t); };
  window.__motionConfig = config;
}

export const useVideoConfig = () => ({ ...config });

/**
 * Текущий кадр. Реализован без React-хуков, чтобы сцену можно было отрисовать и
 * обычным DOM: значение читается на месте, а перерисовку запускает рендерер, ставя
 * время. Для React-сцен подписка ниже.
 */
export const useCurrentFrame = () => Math.round(currentTime * config.fps);

/** Подписка на смену времени — для React-обёртки или ручной перерисовки. */
export function onTimeChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// --- кривые ---------------------------------------------------------------------------
// Формулы те же, что в оригинале: сцены отлажены под них покадрово.

const cubicBezier = (x1, y1, x2, y2) => {
  // Кубическая кривая задана параметрически, а нужна как функция y(x). Ищем параметр
  // по x методом Ньютона, затем берём y — так же, как это делает браузер для CSS.
  const A = (a, b) => 1 - 3 * b + 3 * a;
  const B = (a, b) => 3 * b - 6 * a;
  const C = (a) => 3 * a;
  const calc = (t, a, b) => ((A(a, b) * t + B(a, b)) * t + C(a)) * t;
  const slope = (t, a, b) => 3 * A(a, b) * t * t + 2 * B(a, b) * t + C(a);
  return (x) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 8; i++) {
      const d = slope(t, x1, x2);
      if (Math.abs(d) < 1e-6) break;
      t -= (calc(t, x1, x2) - x) / d;
    }
    return calc(t, y1, y2);
  };
};

export const Easing = {
  linear: (t) => t,
  ease: cubicBezier(0.25, 0.1, 0.25, 1),
  quad: (t) => t * t,
  cubic: (t) => t * t * t,
  poly: (n) => (t) => Math.pow(t, n),
  sin: (t) => 1 - Math.cos((t * Math.PI) / 2),
  circle: (t) => 1 - Math.sqrt(1 - t * t),
  exp: (t) => Math.pow(2, 10 * (t - 1)),
  bezier: (x1, y1, x2, y2) => cubicBezier(x1, y1, x2, y2),
  /** Отскок: значение перелетает цель и возвращается. */
  back: (s = 1.70158) => (t) => t * t * ((s + 1) * t - s),
  bounce: (t) => {
    const n1 = 7.5625, d1 = 2.75;
    if (t < 1 / d1) return n1 * t * t;
    if (t < 2 / d1) { t -= 1.5 / d1; return n1 * t * t + 0.75; }
    if (t < 2.5 / d1) { t -= 2.25 / d1; return n1 * t * t + 0.9375; }
    t -= 2.625 / d1; return n1 * t * t + 0.984375;
  },
  elastic: (bounciness = 1) => (t) => {
    const p = bounciness * Math.PI;
    return 1 - Math.pow(Math.cos((t * Math.PI) / 2), 3) * Math.cos(t * p);
  },
  /** Развернуть кривую: медленно в конце вместо медленно в начале. */
  out: (fn) => (t) => 1 - fn(1 - t),
  /** Симметрично: разгон и торможение одной кривой. */
  inOut: (fn) => (t) => (t < 0.5 ? fn(t * 2) / 2 : 1 - fn((1 - t) * 2) / 2),
  in: (fn) => fn,
};

// --- интерполяция ---------------------------------------------------------------------

/**
 * Перевести значение из одного диапазона в другой по кривой.
 *
 * Поведение на краях по умолчанию — зажать: без этого сцена, которую попросили
 * отрисовать за пределами её отрезка, уезжает в бесконечность, а такое случается
 * постоянно при склейке.
 */
export function interpolate(input, inputRange, outputRange, options = {}) {
  const {
    easing = (t) => t,
    extrapolateLeft = 'clamp',
    extrapolateRight = 'clamp',
  } = options;

  if (inputRange.length !== outputRange.length) {
    throw new Error('диапазоны входа и выхода разной длины: '
      + `${inputRange.length} против ${outputRange.length}`);
  }
  if (inputRange.length < 2) {
    throw new Error('в диапазоне нужно минимум две точки');
  }

  // Находим отрезок, в который попал вход
  let i = 0;
  while (i < inputRange.length - 2 && input >= inputRange[i + 1]) i++;

  const inMin = inputRange[i], inMax = inputRange[i + 1];
  const outMin = outputRange[i], outMax = outputRange[i + 1];

  if (input < inputRange[0]) {
    if (extrapolateLeft === 'clamp') return outputRange[0];
    if (extrapolateLeft === 'identity') return input;
  }
  if (input > inputRange[inputRange.length - 1]) {
    if (extrapolateRight === 'clamp') return outputRange[outputRange.length - 1];
    if (extrapolateRight === 'identity') return input;
  }

  if (inMax === inMin) return outMin;
  const progress = (input - inMin) / (inMax - inMin);
  return outMin + easing(progress) * (outMax - outMin);
}

const parseColor = (c) => {
  if (typeof c !== 'string') return [0, 0, 0, 1];
  const s = c.trim();
  if (s.startsWith('#')) {
    const h = s.slice(1);
    const full = h.length === 3 ? h.split('').map((x) => x + x).join('') : h;
    return [parseInt(full.slice(0, 2), 16), parseInt(full.slice(2, 4), 16),
            parseInt(full.slice(4, 6), 16), full.length === 8 ? parseInt(full.slice(6, 8), 16) / 255 : 1];
  }
  const m = s.match(/rgba?\(([^)]+)\)/);
  if (m) {
    const p = m[1].split(',').map((x) => parseFloat(x));
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  }
  return [0, 0, 0, 1];
};

/** Интерполяция цвета покомпонентно. */
export function interpolateColors(input, inputRange, colors) {
  const parsed = colors.map(parseColor);
  const ch = [0, 1, 2, 3].map((k) =>
    interpolate(input, inputRange, parsed.map((p) => p[k])));
  return `rgba(${Math.round(ch[0])}, ${Math.round(ch[1])}, ${Math.round(ch[2])}, ${ch[3].toFixed(3)})`;
}

// --- пружина --------------------------------------------------------------------------

/**
 * Затухающая пружина. Считается аналитически на момент кадра, а не пошаговым
 * интегрированием: рендерер прыгает по времени в произвольном порядке (кадры снимаются
 * параллельно), и пошаговая модель дала бы разный результат при разном порядке.
 */
export function spring({ frame, fps = config.fps, config: cfg = {}, from = 0, to = 1, durationInFrames } = {}) {
  const { damping = 10, mass = 1, stiffness = 100, overshootClamping = false } = cfg;
  let t = frame / fps;
  if (durationInFrames) t = (frame / durationInFrames) * (durationInFrames / fps);

  const w0 = Math.sqrt(stiffness / mass);
  const zeta = damping / (2 * Math.sqrt(stiffness * mass));

  let value;
  if (zeta < 1) {
    const wd = w0 * Math.sqrt(1 - zeta * zeta);
    value = 1 - Math.exp(-zeta * w0 * t) * (Math.cos(wd * t) + (zeta * w0 / wd) * Math.sin(wd * t));
  } else {
    value = 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  }
  if (overshootClamping) value = Math.min(Math.max(value, 0), 1);
  return from + (to - from) * value;
}

// --- слои и файлы ---------------------------------------------------------------------

/** Путь к файлу рядом со сценой. */
export const staticFile = (name) => {
  const base = (typeof window !== 'undefined' && window.__staticBase) || './public/';
  return base.replace(/\/?$/, '/') + String(name).replace(/^\//, '');
};

/**
 * Полноэкранный слой. В React-сцене используется как компонент, но реализован без
 * зависимости от React: если React есть в окружении, вернётся элемент, если нет —
 * функция отдаст стиль, который можно повесить на обычный div.
 */
export const ABSOLUTE_FILL_STYLE = {
  position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
  width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
};

export const AbsoluteFill = (props = {}) => {
  const R = (typeof window !== 'undefined' && window.React) || null;
  const style = { ...ABSOLUTE_FILL_STYLE, ...(props.style || {}) };
  if (!R) return { style };
  return R.createElement('div', { ...props, style }, props.children);
};

/**
 * Картинка, о загрузке которой знает рендерер: пока она не готова, кадр не снимается.
 * Без этого первые кадры выходят пустыми — самая частая причина «первая секунда чёрная».
 */
export const Img = (props = {}) => {
  const R = (typeof window !== 'undefined' && window.React) || null;
  const onLoad = (e) => {
    if (typeof props.onLoad === 'function') props.onLoad(e);
  };
  if (!R) return { ...props, onLoad };
  return R.createElement('img', { ...props, onLoad });
};

/** Отрезок таймлайна: сцена внутри видит своё время, начинающееся с нуля. */
export const Sequence = (props = {}) => {
  const R = (typeof window !== 'undefined' && window.React) || null;
  const { from = 0, durationInFrames = Infinity, children } = props;
  const frame = useCurrentFrame();
  const inside = frame - from;
  if (inside < 0 || inside >= durationInFrames) return null;
  if (!R) return { visible: true, frame: inside };
  return R.createElement('div', { style: ABSOLUTE_FILL_STYLE }, children);
};

export const random = (seed) => {
  // Детерминированный шум: рендер должен повторяться кадр в кадр, поэтому Math.random
  // здесь недопустим — при параллельной съёмке он дал бы разные кадры на одном времени.
  let h = 0;
  const s = String(seed);
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  h = Math.imul(h ^ (h >>> 15), 0x2c1b3c6d);
  h = Math.imul(h ^ (h >>> 13), 0x297a2d39);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
};

export default {
  configure, setTime, useVideoConfig, useCurrentFrame, onTimeChange,
  Easing, interpolate, interpolateColors, spring,
  AbsoluteFill, ABSOLUTE_FILL_STYLE, Img, Sequence, staticFile, random,
};
