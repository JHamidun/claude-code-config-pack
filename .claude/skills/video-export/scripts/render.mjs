#!/usr/bin/env node
/**
 * Покадровый рендер HTML-анимации в видео.
 *
 * Механика та же, что у Remotion: открыть страницу в headless-браузере, ставить время
 * вручную, снимать кадры, склеивать ffmpeg. Разница в четырёх местах, каждое из которых
 * подсмотрено в их рендерере и заметно меняет результат:
 *
 * 1. КАДРЫ НЕ ЛОЖАТСЯ НА ДИСК. Идут в ffmpeg через stdin, склейка идёт параллельно
 *    съёмке. Раньше 1800 PNG сначала писались, потом читались — лишний проход по диску
 *    и гигабайты временных файлов.
 * 2. ФОНОВЫЕ ВКЛАДКИ БРАУЗЕР ДУШИТ. При параллельном рендере вкладки, кроме активной,
 *    работают в разы медленнее. Лечится тем, что мы по кругу выводим каждую вперёд
 *    (cycleBrowserTabs у них).
 * 3. СЦЕНА САМА ГОВОРИТ, ЧТО НЕ ГОТОВА. Вместо слепого ожидания «наверное, дорисовалось»
 *    сцена регистрирует метки delayRender, и кадр снимается только когда все сняты.
 *    Без этого шрифт или картинка не успевают, и кадр уходит недорисованным.
 * 4. СНИМОК ЧЕРЕЗ CDP НАПРЯМУЮ. Page.captureScreenshot вместо обёртки — меньше
 *    накладных расходов на кадр, а заодно доступна прозрачность через Emulation.
 *
 * Использование:
 *   node render.mjs scene.html --out out.mp4 --duration 8 --fps 30
 *   node render.mjs scene.html --width 1080 --height 1920 --concurrency 4
 *   node render.mjs scene.html --transparent --out out.webm     # альфа-канал
 *   node render.mjs scene.html --audio voice.mp3 --audio music.mp3
 *
 * Что должна уметь сцена (минимум — первое):
 *   window.__setTime(t)          — поставить таймлайн на t секунд и перерисовать
 *   window.__delayRender(label)  — вернуть id, пока он не снят, кадр не снимается
 *   window.__continueRender(id)  — снять метку
 */
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';

// --- разбор аргументов -------------------------------------------------------------
const argv = process.argv.slice(2);
const positional = [];
const opts = {audio: []};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (!a.startsWith('--')) { positional.push(a); continue; }
  const key = a.slice(2);
  const flags = ['transparent', 'quiet', 'keep-frames'];
  if (flags.includes(key)) { opts[key] = true; continue; }
  const value = argv[++i];
  if (key === 'audio') opts.audio.push(value);
  else opts[key] = value;
}

const input = positional[0];
if (!input) {
  console.error('Укажи html-файл: node render.mjs scene.html [--out out.mp4] [--duration 5] [--fps 30]');
  process.exit(1);
}

const transparent = Boolean(opts.transparent);
const out = opts.out || input.replace(/\.html?$/i, transparent ? '.webm' : '.mp4');
const fps = Number(opts.fps || 30);
const width = Number(opts.width || 1920);
const height = Number(opts.height || 1080);
const scale = Number(opts.scale || 1);
const crf = Number(opts.crf || 18);
// Больше вкладок, чем ядер, только вредит: они начинают отбирать время друг у друга.
const concurrency = Math.max(1, Math.min(Number(opts.concurrency || 4), os.cpus().length));
const readyTimeout = Number(opts['ready-timeout'] || 30000);

const log = (...a) => { if (!opts.quiet) console.log(...a); };

// --- то, что внедряется в страницу до её скриптов -----------------------------------
// Сцена может ничего не знать про delayRender — тогда всё сведётся к «кадр готов сразу».
const PRELUDE = `
(() => {
  const handles = new Map();
  let seq = 0;
  window.__delayRender = (label) => {
    const id = 'h' + (++seq);
    handles.set(id, { label: label || 'без метки', at: Date.now() });
    return id;
  };
  window.__continueRender = (id) => { handles.delete(id); };
  window.__pendingHandles = () => Array.from(handles.entries())
    .map(([id, h]) => id + ' (' + h.label + ', ' + (Date.now() - h.at) + ' мс)');
  window.__isReady = () => handles.size === 0;

  // Шрифты — самая частая причина недорисованного первого кадра.
  if (document.fonts) {
    const id = window.__delayRender('шрифты');
    document.fonts.ready.then(() => window.__continueRender(id));
  }
  // Картинки, которые ещё грузятся, тоже держат кадр.
  addEventListener('DOMContentLoaded', () => {
    for (const img of document.images) {
      if (img.complete) continue;
      const id = window.__delayRender('картинка ' + (img.currentSrc || img.src).slice(-40));
      const done = () => window.__continueRender(id);
      img.addEventListener('load', done, {once: true});
      img.addEventListener('error', done, {once: true});
    }
  });
})();
`;

// --- очередь, которая держит порядок кадров ------------------------------------------
// Кадры готовы вразнобой, а писать в кодировщик надо строго подряд. Кадр N ждёт, пока
// не уйдёт N-1; ждущие держатся обещаниями, никакого опроса в цикле.
function frameOrdering(total) {
  let next = 0;
  const waiting = new Map();
  const release = () => {
    const w = waiting.get(next);
    if (w) { waiting.delete(next); w(); }
  };
  return {
    waitTurn: (frame) => frame === next
      ? Promise.resolve()
      : new Promise((resolve) => { waiting.set(frame, resolve); }),
    done: () => { next++; release(); },
    get finished() { return next >= total; },
  };
}

// --- ffmpeg ---------------------------------------------------------------------------
function startFfmpeg() {
  const args = ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', 'pipe:0'];
  for (const track of opts.audio) args.push('-i', track);

  if (opts.audio.length > 1) {
    // Несколько дорожек сводим одним фильтром: голос и музыка в один поток.
    const inputs = opts.audio.map((_, i) => `[${i + 1}:a]`).join('');
    args.push('-filter_complex', `${inputs}amix=inputs=${opts.audio.length}:normalize=0[aout]`,
              '-map', '0:v', '-map', '[aout]');
  } else if (opts.audio.length === 1) {
    args.push('-map', '0:v', '-map', '1:a');
  }

  if (transparent) {
    // Альфа-канал переживает только VP9 (webm) и подобные; h264 её теряет молча.
    args.push('-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', String(crf));
  } else {
    args.push('-c:v', 'libx264', '-preset', opts.preset || 'medium',
              '-crf', String(crf), '-pix_fmt', 'yuv420p');
  }
  if (opts.audio.length) args.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  args.push(out);

  const proc = spawn('ffmpeg', args, {stdio: ['pipe', 'ignore', 'pipe']});
  let stderr = '';
  proc.stderr.on('data', (d) => { stderr += d.toString(); });
  proc.on('error', (e) => { console.error('ffmpeg не запустился:', e.message); process.exit(1); });
  return {proc, getStderr: () => stderr};
}

// --- рендер ----------------------------------------------------------------------------
async function main() {
  const started = Date.now();
  const durationSec = Number(opts.duration || 5);
  const total = Math.max(1, Math.round(durationSec * fps));
  const url = pathToFileURL(path.resolve(input)).href;

  log(`Рендер ${path.basename(input)} → ${out}`);
  log(`  ${width}×${height}, ${fps} к/с, ${durationSec} с = ${total} кадров, вкладок: ${concurrency}`);

  const browser = await chromium.launch({args: ['--autoplay-policy=no-user-gesture-required']});
  const context = await browser.newContext({
    viewport: {width, height},
    deviceScaleFactor: scale,
  });
  await context.addInitScript(PRELUDE);

  // Отдельная вкладка на каждого работника: параллелим по кадрам, а не по времени.
  const pages = [];
  for (let i = 0; i < concurrency; i++) {
    const page = await context.newPage();
    await page.goto(url, {waitUntil: 'load'});
    const cdp = await context.newCDPSession(page);
    if (transparent) {
      await cdp.send('Emulation.setDefaultBackgroundColorOverride',
                     {color: {r: 0, g: 0, b: 0, a: 0}});
    }
    pages.push({page, cdp});
  }

  // Браузер замедляет всё, что не на переднем плане. Гоняем фокус по кругу, иначе
  // выигрыш от вкладок съедается их же торможением.
  let cycling = null;
  if (concurrency > 1) {
    let i = 0;
    cycling = setInterval(() => {
      const p = pages[i++ % pages.length];
      p?.page.bringToFront().catch(() => {});
    }, 200);
  }

  const {proc: ffmpeg, getStderr} = startFfmpeg();
  const order = frameOrdering(total);
  let rendered = 0;

  const renderFrame = async (worker, frame) => {
    const t = frame / fps;
    await worker.page.evaluate((time) => {
      if (typeof window.__setTime === 'function') window.__setTime(time);
    }, t);

    // Ждём, пока сцена снимет свои метки. Слепая пауза здесь и была причиной
    // недорисованных кадров: успело или нет — как повезёт.
    const deadline = Date.now() + readyTimeout;
    for (;;) {
      const ready = await worker.page.evaluate(() => !window.__isReady || window.__isReady());
      if (ready) break;
      if (Date.now() > deadline) {
        const pending = await worker.page.evaluate(() =>
          window.__pendingHandles ? window.__pendingHandles() : []);
        throw new Error(`кадр ${frame}: сцена не готова за ${readyTimeout} мс. Висят: ${pending.join(', ')}`);
      }
      await new Promise((r) => setTimeout(r, 16));
    }

    const shot = await worker.cdp.send('Page.captureScreenshot', {
      format: 'png',
      captureBeyondViewport: false,
      fromSurface: true,
    });
    const buf = Buffer.from(shot.data, 'base64');

    // Кадр готов, но в поток он пойдёт только в свою очередь.
    await order.waitTurn(frame);
    if (!ffmpeg.stdin.write(buf)) {
      await new Promise((r) => ffmpeg.stdin.once('drain', r));
    }
    order.done();

    rendered++;
    if (!opts.quiet && (rendered % Math.max(1, Math.floor(total / 20)) === 0 || rendered === total)) {
      const pct = Math.round((rendered / total) * 100);
      const speed = rendered / ((Date.now() - started) / 1000);
      process.stdout.write(`\r  ${pct}% — ${rendered}/${total} кадров, ${speed.toFixed(1)} к/с   `);
    }
  };

  // Каждая вкладка тянет кадры из общего счётчика: быстрая берёт больше медленной.
  let cursor = 0;
  const workers = pages.map((worker) => (async () => {
    for (;;) {
      const frame = cursor++;
      if (frame >= total) return;
      await renderFrame(worker, frame);
    }
  })());

  try {
    await Promise.all(workers);
  } finally {
    if (cycling) clearInterval(cycling);
    ffmpeg.stdin.end();
    await browser.close();
  }

  const code = await new Promise((resolve) => ffmpeg.on('close', resolve));
  if (!opts.quiet) process.stdout.write('\n');
  if (code !== 0) {
    console.error('ffmpeg завершился с ошибкой:\n' + getStderr().split('\n').slice(-12).join('\n'));
    process.exit(1);
  }

  const size = fs.existsSync(out) ? (fs.statSync(out).size / 1048576).toFixed(1) : '?';
  const secs = ((Date.now() - started) / 1000).toFixed(1);
  log(`Готово: ${out} — ${size} МБ за ${secs} с (${(total / Number(secs)).toFixed(1)} к/с)`);
}

main().catch((err) => {
  console.error('Рендер не удался:', err.message);
  process.exit(1);
});
