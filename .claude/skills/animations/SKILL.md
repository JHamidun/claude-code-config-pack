---
name: animations
description: "Таймлайн-анимации в HTML (React): плеер, скраббер, ease. Триггеры: «анимация в HTML», «motion design», «интро», «transitions для презентации»."
---

# Animations

Минималистичный движок таймлайн-анимаций. Один HTML, React + inline JSX, без сторонних либ кроме Babel.

## Что даёт `templates/anim-engine.jsx`

- `<Stage duration={...}>` — корневой контейнер. Авто-скейлит канвас под viewport, рисует скраббер и play/pause.
- `<Sprite start={s} end={s} ...>` — обёртка с временными границами. Внутри читает `useTime()` и рендерит детей.
- `useTime()` — текущая позиция таймлайна в секундах.
- `useSprite()` — нормализованная позиция внутри спрайта (0..1).
- `Easing` — `linear`, `easeIn`, `easeOut`, `easeInOut`, `expo`, `back`, `bounce`.
- `interpolate(t, [from, to], easing)` — линейная интерполяция чисел или массивов чисел (для transform).
- `entryFade`, `entryRise`, `exitFade` — готовые входы/выходы.

## Структура сцены

```jsx
<Stage duration={8} width={1920} height={1080}>
  <Sprite start={0} end={3}>
    {() => {
      const p = useSprite();
      const y = interpolate(p, [40, 0], Easing.easeOut);
      const o = interpolate(p, [0, 1], Easing.easeOut);
      return <h1 style={{ transform: `translateY(${y}px)`, opacity: o }}>Hello</h1>;
    }}
  </Sprite>

  <Sprite start={2} end={5}>
    {() => <SecondScene />}
  </Sprite>
</Stage>
```

## Принципы

- **Всё происходит в долях секунды.** Не в кадрах. 24/30/60 fps — забота браузера.
- **Перекрытия — благо.** Последние 0.3s одного спрайта пересекаются с первыми 0.3s следующего — глаз не цепляется за стыки.
- **Easing — не декорация.** `easeOut` для входов («падает и тормозит»), `easeIn` для выходов («ускоряется и улетает»), `easeInOut` для одновременных движений, `linear` для камер и пэннингов.
- **Не анимируй всё.** Один-два элемента в кадре движутся, остальные стоят. Иначе каша.
- **Сохраняй позицию плеера.** Если делаешь длинную анимацию для итераций — пиши текущее время в `localStorage`, чтоб рефреш не сбрасывал.

## Экспорт в видео

Если попросят MP4/GIF, дёргай `export-png` для покадрового рендера через Playwright + ffmpeg для склейки.

## Что НЕ делать

- Не имитируй keyframes-CSS через JS-таймауты. Используй `requestAnimationFrame` (он внутри Stage).
- Не используй GSAP / Framer Motion / Popmotion, если задачу решает встроенный движок. Бандл-вес и сложность не оправданы.
- Не пытайся синхронизировать анимацию со звуком через `setTimeout`. Используй `audio.currentTime` как источник правды.
