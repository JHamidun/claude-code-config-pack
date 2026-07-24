# Remotion social-UI overlays (Instagram/Telegram chrome) → composite over b-roll

Главный приём референс-рилса (DV08xLPjPOx): реальный футаж притворяется лентой Instagram /
перепиской Telegram за счёт **прозрачных UI-оверлеев**. Делаем их кодом (React→video) через
Remotion, рендерим в **alpha webm**, накладываем ffmpeg-ом.

Проект: `skills/video-generation/remotion-overlays/` (компоненты `InstagramChrome.tsx`,
`TelegramBubble.tsx`, готовые композиции `InstagramStory` / `TelegramForward`).

> Лицензия Remotion = BUSL: бесплатно для личного/OSS и компаний <$1M ARR (наш случай). Платно от $1M ARR.

## Установка (один раз)

```bash
cd ~/.claude/skills/video-generation/remotion-overlays
npm install      # ~500MB node_modules + Chromium при первом рендере
```

## Превью / правка в студии

```bash
npm run preview         # remotion studio — крутилки props в браузере
```

## Рендер прозрачного оверлея (alpha webm)

```bash
# Instagram-story хром (прогресс-бар, ник, pop-сердце, счётчик лайков)
npx remotion render InstagramStory out/ig.webm --codec=vp9 --pixel-format=yuva420p --image-format=png \
  --props='{"username":"@yourchannel","timeAgo":"2h","storySeconds":15,"likes":15000}'

# Telegram forward-бабл (выезжает снизу)
npx remotion render TelegramForward out/tg.webm --codec=vp9 --pixel-format=yuva420p --image-format=png \
  --props='{"name":"Your Name","text":"Смотрите новый выпуск!","time":"14:32"}'
```

Ключи: `--codec=vp9 --pixel-format=yuva420p --image-format=png` = прозрачность (alpha). **`--image-format=png` ОБЯЗАТЕЛЕН** для alpha (иначе `TypeError: Pixel format yuva420p but image format is not PNG`). Длительность — в `Root.tsx` (`durationInFrames`) или `--frames=0-150`. Первый рендер качает Chromium (~150МБ).

## Композит поверх b-roll (ffmpeg)

```bash
ffmpeg -i broll.mp4 -i out/ig.webm \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto[v]" \
  -map "[v]" -map 0:a -c:a copy composite.mp4
```

webm с alpha короче футажа? Зацикли/обрежь: добавь `-stream_loop -1` к `-i out/ig.webm` или
`[1:v]loop=...`. Длиннее — `overlay=...:enable='between(t,0,15)'`.

## Что внутри компонентов (паттерны кинетик-UI)

- **Fade-in** контролов: `interpolate(frame,[0,fps*0.3],[0,1],{extrapolateRight:'clamp'})`.
- **Pop с overshoot** (сердце, баблы): `spring({frame:frame-fps, fps, config:{damping:9,mass:0.6}})` → scale.
- **Прогресс-бар сторис**: `width = (frame/(fps*storySeconds))*100 + '%'`.
- **Счётчик-каунтер**: `interpolate(frame,[fps,fps*4],[0,likes])` + `.toLocaleString()`.
- **Slide-up бабл**: `spring → translateY(120→0)`.

Добавляй свои композиции в `src/Root.tsx` (`<Composition id=... component=... />`) — TikTok-UI,
YouTube-карточки, kinetic-типографику, lower-thirds. Кириллица в Remotion работает из коробки
(в отличие от ffmpeg drawtext).

## Альтернатива без Node (Python) — `motion-graphics.md`

Если Remotion не нужен (или хочется чистый Python): like-counter, progress, lower-third, pop —
через `video-generation/scripts/motion_graphics.py` (ffmpeg+PIL, Cyrillic-safe, dep-free).
Для богатой кифреймовой анимации в Python — `movis` (см. `motion-graphics.md`).
