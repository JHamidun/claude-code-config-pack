<!-- LEGACY: полное тело скилла 'video-export' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: video-export
description: HTML-анимация → MP4 / GIF через FFmpeg. Запись Playwright, затем encoding. Для social-explainer (15-30 сек), product demo, animated explainer.
when_to_use: Артефакт через `animations` skill готов, нужно отправить как video file. После `animations` если результат должен быть посланным в TG/Twitter/YouTube Shorts.
---

# Video export

HTML → series of frames → FFmpeg encode → MP4/GIF/WebM. Качество и контроль над framerate.

## Зависимости

```bash
brew install ffmpeg          # mac
sudo apt-get install ffmpeg  # linux
choco install ffmpeg         # windows

npm i -D playwright
```

## Метод 1: Playwright video recording (простой)

```js
const { chromium } = require('playwright');

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  recordVideo: { dir: './videos/', size: { width: 1920, height: 1080 } },
});
const page = await ctx.newPage();
await page.goto('file:///abs/animation.html');
await page.waitForTimeout(10000);  // record 10 sec
await ctx.close();   // обязательно — сохраняет видео
await browser.close();
// → videos/<random>.webm
```

WebM → конвертить в MP4 для широкой совместимости:
```bash
ffmpeg -i videos/animation.webm -c:v libx264 -preset slow -crf 18 \
       -pix_fmt yuv420p -movflags +faststart out.mp4
```

## Метод 2: Frame-by-frame screenshot (точный)

Контроль над каждым кадром:

```js
const fps = 60;
const duration = 5;  // sec
const frames = fps * duration;

for (let i = 0; i < frames; i++) {
  const t = i / fps;  // time in seconds
  // Установить state на момент времени (если animations завязаны на JS time)
  await page.evaluate((t) => {
    window.__animTime = t;
    window.dispatchEvent(new Event('frame'));
  }, t);
  await page.screenshot({
    path: `frames/frame-${String(i).padStart(5, '0')}.png`,
  });
}
```

В animations.jsx использовать `window.__animTime` вместо `Date.now()`:
```js
function useTime() {
  const [t, setT] = useState(0);
  useEffect(() => {
    const tick = () => setT(window.__animTime ?? performance.now() / 1000);
    window.addEventListener('frame', tick);
    return () => window.removeEventListener('frame', tick);
  }, []);
  return t;
}
```

Затем FFmpeg:
```bash
ffmpeg -framerate 60 -i frames/frame-%05d.png \
       -c:v libx264 -preset slow -crf 18 \
       -pix_fmt yuv420p -movflags +faststart out.mp4
```

Метод 2 даёт **deterministic** видео — кадры идентичны на каждом запуске. Хорошо для CI / regenerable.

## GIF export

GIF — большие файлы, ограниченная палитра. Для коротких циклов (~5 сек) ОК:

```bash
# Two-pass: palette generate → encode
ffmpeg -i frames/frame-%05d.png -vf "fps=30,scale=720:-1:flags=lanczos,palettegen" palette.png
ffmpeg -framerate 30 -i frames/frame-%05d.png -i palette.png \
       -filter_complex "fps=30,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse" out.gif
```

GIF size mistakes:
- Высота >720px → файл огромный
- Длительность >10 сек → файл huge
- 60 fps → большая часть кадров избыточна, 30 fps хватает

## Размеры под платформы

| Платформа | Resolution | FPS | Codec | Длительность |
|---|---|---|---|---|
| YouTube Shorts | 1080×1920 | 30/60 | H.264 | < 60s |
| Instagram Reels / TikTok | 1080×1920 | 30 | H.264 | 15-90s |
| Twitter video | 1280×720 | 30 | H.264 | < 140s |
| LinkedIn video | 1920×1080 | 30 | H.264 | < 10min |
| Telegram | 1920×1080 max | 30 | H.264 | unlimited |
| Email GIF | 600×400 max | 15-30 | GIF | < 6MB |

## Quality settings

| `-crf` | Quality | Размер |
|---|---|---|
| 17 | Visually lossless | максимум |
| 18-22 | Good | high |
| 23 (default) | Standard | medium |
| 28-30 | Lower | small |
| > 35 | Bad | tiny |

Для финального deliverable: `-crf 18` + `-preset slow`.
Для preview / debug: `-crf 28` + `-preset ultrafast`.

## Audio overlay

Добавить музыку:
```bash
ffmpeg -i out.mp4 -i music.mp3 -c:v copy -c:a aac -b:a 192k -shortest out-with-audio.mp4
```

`-shortest` — обрежется по кратчайшему трекy. Без `-shortest` — видео loops пока музыка играет.

## Loop seamless

Чтобы GIF / видео плавно зацикливалось, последний кадр === первому. В animations.jsx:
```js
function useLoopTime(duration) {
  const t = useTime();
  return (t % duration);  // 0 → duration → 0 → ...
}
```

## Stack

- `animations` skill — каркас анимации (anim-engine.jsx)
- `verifier` — проверить что HTML открывается без errors
- `placeholders` — для статичных элементов внутри анимации

## Антипаттерны

- 60 fps на complex анимации без deterministic time → frame drops, дёрганое видео
- GIF 1920×1080 → 50MB, не отправишь никуда
- Видео без `-pix_fmt yuv420p` → не работает на Apple devices
- Без `-movflags +faststart` → видео грузит всё перед началом проигрывания (web-плохо)
- Записывать через screen capture с курсором → курсор в финале
- Использовать `Date.now()` вместо deterministic time → каждый запуск разный
- Качать H.265 (HEVC) → не воспроизводится на старых устройствах. Лучше H.264
