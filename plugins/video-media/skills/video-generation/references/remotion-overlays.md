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

### 🚨 Выбор контейнера для альфы: webm ≠ универсально

`webm/vp9` выше годится для **композита через ffmpeg и для веба**. Но если оверлей уходит
человеку в монтажную программу — **Premiere, Final Cut, DaVinci, CapCut и After Effects
WebM с альфой не открывают** (либо открывают без альфа-канала). Монтажёр получит файл,
который «не вставляется», и вернёт его тебе.

| Куда отдаём | Формат | Команда |
| ----------- | ------ | ------- |
| ffmpeg-композит у себя, веб | webm/vp9 | `--codec=vp9 --pixel-format=yuva420p --image-format=png` |
| **монтажёру в Premiere/FCP/DaVinci** | **MOV ProRes 4444** | `--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png` |
| CapCut, мобильный монтаж | PNG-секвенция | `out/png/frame-%04d.png --image-format=png` |
| полная сцена без прозрачности | MP4 H.264 | `--codec=h264 --crf=18` |

**MP4/H.264 альфу не хранит в принципе** — если нужен прозрачный фон, MP4 отпадает сразу.
В превью плеера альфа выглядит чёрным или шахматкой: это нормально, канал в файле есть.

Для прозрачности корневой `AbsoluteFill` не должен иметь заливки на весь кадр.

### Приём «окно-маска»

Нужен экран с заливкой, но с прозрачной дырой внутри (чтобы в монтаже подложить видео):
вырезаем отверстие в заливке через `clip-path: path(evenodd, "…")` — внешний прямоугольник
кадра плюс внутренний контур окна. Рендер только в MOV с альфой.

### Быстрая проверка до полного рендера

```bash
npx remotion still <CompId> out/preview.png --frame=90   # один кадр вместо всего клипа
npx remotion compositions src/index.ts                    # список композиций и их id
```

Показать кадр на утверждение дешевле, чем ждать рендер целиком и переделывать.

## Правило редактируемости в Studio

> Параметр появляется в правой панели Remotion Studio и правится **без кода** тогда и только
> тогда, когда он объявлен в `schema` (zod) как проп. Всё, что зашито в код-константы,
> меняется исключительно правкой файла.

Поэтому тексты, цвета, тайминги и флаги, которые кто-то захочет крутить мышкой, **выводи
в схему**, а не в константы. Массивы (`z.array(z.object({...}))`) Studio показывает с
кнопками добавления и удаления элементов — удобно для списков буллетов, тезисов, участников.

## Принципы анимации — что отличает аккуратную графику от любительской

- **Полный вход И выход.** Элемент появляется, держится, затем уходит до конца клипа.
  Обрыв движения на середине — главный признак самоделки. (Исключение: пользователь явно
  просит «обрыв в конце» — тогда оставляем вход, убираем выход.)
- **Никакой линейщины.** `spring` или `interpolate` + `Easing`; лёгкое предвкушение и
  небольшой overshoot с оседанием вместо равномерного движения.
- **Каскад (stagger).** Элементы входят друг за другом через несколько кадров, не разом.
- **Живость на удержании.** Пока графика висит — мягкий флоат, лёгкая пульсация свечения,
  медленный проход блика. Статичная «висящая» плашка выглядит мёртвой.
- **Title-safe.** Ключевой текст держать в пределах ~10% отступов от краёв; над видео
  обязателен контраст — подложка, скрим или тень. Длинный текст ужимать или переносить,
  чтобы не вылезал за контейнер.
- **Тайминг под содержание.** Ориентир — около секунды на короткую строку для чтения.

**Анимация строится на номере кадра, а не на времени:** `useCurrentFrame()`, `interpolate`,
`spring`, `Easing`. CSS-анимации (`animation: …`, `transition`) с покадровым рендером
**не синхронизируются** — в файле они либо застынут, либо поедут. Любое движение переводи в кадры.

## Грабли установки

- **TypeScript закреплять на 5.x** (`npm i -D typescript@5`). Более новые ветки ломают
  бандлер Remotion.
- Первый рендер тянет headless-Chromium — это ожидаемо, не считать за сбой.
- `remotion render` и `remotion still` окон **не открывают**, это headless. Визуальный
  интерфейс появляется только у `remotion studio`.

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
