#!/usr/bin/env node
/**
 * Собрать готовую сцену из библиотеки в страницу, которую умеет снимать наш рендерер.
 *
 * Зачем. В библиотеке две сотни отлаженных сцен, но написаны они под чужой фреймворк и
 * тянут его целиком — сто с лишним мегабайт зависимостей ради девяти функций. Эти девять
 * у нас есть (motion-runtime.mjs), поэтому сцену достаточно СОБРАТЬ, подменив импорт:
 * ни одна строка самой сцены не меняется.
 *
 * Подмена делается на этапе сборки, а не правкой файлов: библиотека остаётся такой,
 * какой пришла, и её можно обновлять поверх, не теряя наших изменений.
 *
 *   node build-scene.mjs <путь-к-сцене.tsx> -o out/
 *   node build-scene.mjs ../../video-shotcraft/demos/typography/blur-slide/BlurSlide.tsx -o build/
 *   node build-scene.mjs <сцена> -o build/ --width 1080 --height 1920   # вертикаль
 *
 * На выходе: index.html + scene.js рядом. Дальше — обычный рендер:
 *   node render.mjs build/index.html -o out.mp4 --duration 4 --fps 30
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// --- разбор аргументов ------------------------------------------------------------------

const argv = process.argv.slice(2);
const src = argv.find((a) => !a.startsWith('-'));
const opt = (name, def) => {
  const i = argv.indexOf('--' + name);
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : def;
};
const outDir = opt('o', null) || argv[argv.indexOf('-o') + 1] || 'build';
const width = Number(opt('width', 1920));
const height = Number(opt('height', 1080));
const fps = Number(opt('fps', 30));
const background = opt('background', '#000');

if (!src) {
  console.error('нужен путь к сцене: node build-scene.mjs <сцена.tsx> -o build/');
  process.exit(1);
}
if (!fs.existsSync(src)) {
  console.error(`сцены нет: ${src}`);
  process.exit(1);
}

// --- подмена фреймворка ------------------------------------------------------------------
// Сцены импортируют чужой пакет по имени. Вместо правки двух сотен файлов подставляем
// свой модуль под тем же именем — сборщик разрешает импорт в него.

const shimDir = path.join(outDir, '_shim');
fs.mkdirSync(shimDir, { recursive: true });

const runtimeSrc = path.join(HERE, 'motion-runtime.mjs');
if (!fs.existsSync(runtimeSrc)) {
  console.error(`нет слоя выполнения: ${runtimeSrc}`);
  process.exit(1);
}
fs.copyFileSync(runtimeSrc, path.join(shimDir, 'motion-runtime.mjs'));

// Модуль-заместитель: отдаёт наружу то же, что чужой пакет, но берёт из нашего слоя.
// Отдельным файлом, а не псевдонимом напрямую, потому что часть сцен импортирует
// то, чего у нас нет, — здесь это можно заглушить, не трогая сцену.
fs.writeFileSync(path.join(shimDir, 'remotion.mjs'), `
// Заместитель чужого пакета. Математика и время берутся из слоя, а вот компоненты
// объявлены здесь: слой намеренно не знает про React, чтобы его можно было применять и
// без него, а компоненты без React объявить нельзя.
import React from 'react';
export {
  useCurrentFrame, useVideoConfig, interpolate, interpolateColors, Easing, spring,
  staticFile, random,
} from './motion-runtime.mjs';
import { useCurrentFrame as __frame, ABSOLUTE_FILL_STYLE } from './motion-runtime.mjs';

export const AbsoluteFill = ({ style, children, ...rest }) =>
  React.createElement('div', { ...rest, style: { ...ABSOLUTE_FILL_STYLE, ...(style || {}) } }, children);

// Картинка, о загрузке которой знает рендерер: пока она не готова, кадр не снимается —
// иначе первые кадры выходят пустыми.
export const Img = ({ onLoad, ...rest }) => {
  const handle = React.useRef(null);
  React.useEffect(() => {
    if (globalThis.__delayRender) handle.current = globalThis.__delayRender('картинка');
    return () => { if (handle.current != null && globalThis.__continueRender) globalThis.__continueRender(handle.current); };
  }, []);
  return React.createElement('img', {
    ...rest,
    onLoad: (e) => {
      if (handle.current != null && globalThis.__continueRender) { globalThis.__continueRender(handle.current); handle.current = null; }
      if (onLoad) onLoad(e);
    },
  });
};

// Отрезок таймлайна: то, что внутри, показывается только в своём окне.
export const Sequence = ({ from = 0, durationInFrames = Infinity, children }) => {
  const f = __frame();
  const inside = f - from;
  if (inside < 0 || inside >= durationInFrames) return null;
  return React.createElement('div', { style: ABSOLUTE_FILL_STYLE }, children);
};

// Прочее из чужого пакета — заглушки, чтобы сборка не падала на одном импорте.
export const Series = ({ children }) => children ?? null;
export const Freeze = ({ children }) => children ?? null;
export const Loop = ({ children }) => children ?? null;
export const Audio = () => null;
export const Video = () => null;
export const OffthreadVideo = () => null;
export const continueRender = (h) => { if (globalThis.__continueRender) globalThis.__continueRender(h); };
export const delayRender = (label) => (globalThis.__delayRender ? globalThis.__delayRender(label) : 0);
export const prefetch = () => ({ free: () => {}, waitUntilDone: () => Promise.resolve() });
export const getInputProps = () => ({});
export const registerRoot = () => {};
export const Composition = () => null;
`, 'utf8');

// --- сборка ------------------------------------------------------------------------------

const entry = path.join(outDir, '_entry.jsx');
const sceneRel = path.relative(outDir, path.resolve(src)).replace(/\\/g, '/');

// Точка входа: находит в сцене экспортируемый компонент и монтирует его. Имя компонента
// в файлах разное, поэтому берём первый подходящий экспорт, а не угадываем по имени.
fs.writeFileSync(entry, `
import React from 'react';
import { createRoot } from 'react-dom/client';
import * as scene from '${sceneRel}';
import { configure, onTimeChange } from './_shim/motion-runtime.mjs';

configure({ fps: ${fps}, width: ${width}, height: ${height} });

const pick = () => {
  // Экспорт у сцен именованный; default есть не всегда — это норма.
  if (typeof scene['default'] === 'function') return scene['default'];
  for (const [name, v] of Object.entries(scene)) {
    if (typeof v === 'function' && /^[A-Z]/.test(name)) return v;
  }
  throw new Error('в сцене не нашёлся экспортируемый компонент');
};
const Scene = pick();

const root = createRoot(document.getElementById('root'));
// Перерисовываем на каждой смене времени: рендерер ставит время перед съёмкой кадра.
const draw = () => root.render(React.createElement(Scene));
draw();
onTimeChange(draw);
`, 'utf8');

const bundle = path.join(outDir, 'scene.js');
console.log(`  сцена: ${path.basename(src)}`);
console.log(`  подмена фреймворка: remotion → motion-runtime`);

try {
  execFileSync('npx', [
    '--yes', 'esbuild', entry,
    '--bundle',
    '--outfile=' + bundle,
    '--format=iife',
    '--jsx=automatic',
    '--loader:.tsx=tsx',
    '--loader:.ts=ts',
    '--alias:remotion=' + path.resolve(shimDir, 'remotion.mjs'),
    // Сборка идёт в папке пользователя, а React стоит рядом со скиллом. Флага для
    // списка путей поиска в этой версии сборщика нет, поэтому указываем пакеты прямо.
    '--alias:react=' + path.resolve(HERE, '..', 'node_modules', 'react'),
    '--alias:react-dom=' + path.resolve(HERE, '..', 'node_modules', 'react-dom'),
    '--log-level=warning',
    '--target=chrome110',
  ], { stdio: 'inherit', shell: process.platform === 'win32' });
} catch (e) {
  console.error('\n  сборка не прошла. Частые причины:');
  console.error('   • сцена тянет то, чего нет в заместителе — допиши экспорт в _shim/remotion.mjs');
  console.error('   • нет react/react-dom — поставь: npm i react react-dom');
  process.exit(1);
}

const html = `<!doctype html>
<meta charset="utf-8">
<title>${path.basename(src, path.extname(src))}</title>
<style>
  html, body { margin: 0; padding: 0; background: ${background}; overflow: hidden; }
  #root { width: ${width}px; height: ${height}px; position: relative; overflow: hidden; }
</style>
<div id="root"></div>
<script src="./scene.js"></script>
`;
fs.writeFileSync(path.join(outDir, 'index.html'), html, 'utf8');
fs.rmSync(entry, { force: true });

const size = fs.statSync(bundle).size;
console.log(`  собрано: ${path.join(outDir, 'index.html')}  (${(size / 1024).toFixed(0)} КБ)`);
console.log(`  снять видео: node ${path.relative(process.cwd(), path.join(HERE, 'render.mjs'))} `
  + `${path.join(outDir, 'index.html')} -o out.mp4 --fps ${fps}`);
