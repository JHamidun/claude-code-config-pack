---
name: video-export
description: Покадровый рендер HTML-анимации в MP4 / GIF через Playwright + ffmpeg.
when_to_use: Пользователь сделал анимацию (см. animations) и просит "выгрузи как видео / гифку".
---

# Video export

Алгоритм: открыть страницу с анимацией, попросить движок встать на t=0, t=1/fps, t=2/fps, …, снять каждый кадр как PNG, затем склеить в видео через ffmpeg.

## Зависимости

```bash
npm i -D playwright
npx playwright install chromium
brew install ffmpeg     # mac
sudo apt-get install ffmpeg  # linux
```

## Как Stage должен помогать

В `animations/anim-engine.jsx` Stage должен предоставить `window.__setTime(t)` для внешнего управления. Если у тебя своя анимационная сцена — добавь такой хук:

```js
window.__setTime = (t) => { /* ставит таймлайн на t секунд и форсит ререндер */ };
```

Если анимация управляется CSS-keyframes — это не сработает, нужно конвертировать в JS-управляемую.

## Скрипт

`templates/render-video.mjs`:

```js
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const args = parse(process.argv.slice(2));
const file = args._[0];
if (!file) { console.error('Usage: node render-video.mjs <html> [--out video.mp4] [--duration 5] [--fps 30] [--width 1920] [--height 1080]'); process.exit(1); }

const out = args.out || file.replace(/\.html?$/, '.mp4');
const duration = +(args.duration || 5);
const fps      = +(args.fps      || 30);
const width    = +(args.width    || 1920);
const height   = +(args.height   || 1080);

const tmp = '_video_frames';
await fs.rm(tmp, { recursive: true, force: true });
await fs.mkdir(tmp, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
const page = await ctx.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

const total = Math.ceil(duration * fps);
for (let i = 0; i <= total; i++) {
  const t = i / fps;
  await page.evaluate(time => window.__setTime && window.__setTime(time), t);
  await page.waitForTimeout(20); // пусть рендер устаканится
  const num = String(i).padStart(5, '0');
  await page.screenshot({ path: `${tmp}/frame-${num}.png`, fullPage: false });
}

await browser.close();

console.log('→ Склеиваю через ffmpeg…');
if (out.endsWith('.gif')) {
  // Качественный GIF через двухпроходную палитру
  execSync(`ffmpeg -y -framerate ${fps} -i ${tmp}/frame-%05d.png -vf "fps=${fps},split[a][b];[a]palettegen[p];[b][p]paletteuse" "${out}"`, { stdio: 'inherit' });
} else {
  execSync(`ffmpeg -y -framerate ${fps} -i ${tmp}/frame-%05d.png -c:v libx264 -pix_fmt yuv420p -crf 18 "${out}"`, { stdio: 'inherit' });
}
await fs.rm(tmp, { recursive: true, force: true });
console.log('✓', out);

function parse(argv) {
  const a = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v.startsWith('--')) {
      const k = v.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith('--')) a[k] = true; else { a[k] = next; i++; }
    } else a._.push(v);
  }
  return a;
}
```

## Использование

```bash
node render-video.mjs anim.html --duration 5 --fps 30
# → anim.mp4

node render-video.mjs anim.html --out anim.gif --fps 24 --width 800 --height 450
# → anim.gif
```

## Подсказки

- **MP4 для качества и размера**, GIF для месенджеров и где не работает видео.
- **Для GIF снижай ширину** до 600-1000px и fps до 24 — иначе файл огромный.
- **Прозрачный фон:** ни MP4, ни обычный GIF не поддерживают альфу. Для прозрачного видео — WebM (vp9) с `-pix_fmt yuva420p`.
- **Звук:** добавь после рендера через ffmpeg: `ffmpeg -i video.mp4 -i audio.mp3 -shortest output.mp4`.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-video-export.md`. Секции там: Зависимости, Метод 1: Playwright video recording (простой), Метод 2: Frame-by-frame screenshot (точный), GIF export, Размеры под платформы, Quality settings, Audio overlay, Loop seamless, Stack, Антипаттерны.
