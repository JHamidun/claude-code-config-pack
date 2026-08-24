---
name: tweaks-panel
description: "Панель крутилок в прототипе: цвета, шрифты, варианты; localStorage + запись в исходник. Триггеры: «крутилки в прототипе», «запиши в tokens.css»."
---

# Tweaks panel

Готовые React-компоненты для in-design панели настроек: ползунки, переключатели, цвета, варианты-радио.

## Файлы

- `templates/tweaks-panel.jsx` — `<TweaksPanel>`, хук `useTweaks`, контролы `TweakSlider`, `TweakToggle`, `TweakRadio`, `TweakSelect`, `TweakColor`, `TweakText`, `TweakNumber`.
- `templates/example.html` — рабочий пример: цвет, размер шрифта, текст заголовка, тёмная тема и три раскладки. Открывается двойным кликом, сборка не нужна (React/Babel с CDN). Начинай с него — быстрее, чем собирать панель с нуля.
- `templates/tweaks-server.mjs` — крошечный WebSocket-сервер для записи значений обратно в исходник, нужен только для режима из `references/tweaks-persist-file-writeback.md`.

## Использование

```jsx
function App() {
  const [tweaks, setTweak] = useTweaks({
    primary: '#D97757',
    fontSize: 16,
    dark: false,
    layout: 'A',
  });

  return (
    <div style={{
      background: tweaks.dark ? '#111' : '#fff',
      color: tweaks.dark ? '#fff' : '#111',
      fontSize: tweaks.fontSize,
    }}>
      ...макет...

      <TweaksPanel>
        <TweakSection title="Цвет">
          <TweakColor label="Primary" value={tweaks.primary} onChange={v => setTweak('primary', v)} />
        </TweakSection>
        <TweakSection title="Текст">
          <TweakSlider label="Размер" min={12} max={24} step={1}
            value={tweaks.fontSize} onChange={v => setTweak('fontSize', v)} />
        </TweakSection>
        <TweakSection title="Тема">
          <TweakToggle label="Тёмная" value={tweaks.dark} onChange={v => setTweak('dark', v)} />
        </TweakSection>
        <TweakSection title="Layout">
          <TweakRadio value={tweaks.layout} options={['A', 'B', 'C']}
            onChange={v => setTweak('layout', v)} />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}
```

## Persistence

`useTweaks` пишет состояние в `localStorage` под ключом `tweaks.<page-path>`. Рефреш страницы — состояние остаётся. Чтобы сбросить: кнопка «Reset» в углу панели или `localStorage.clear()`.

### Persistence на диск (бывший скилл tweaks-persist)

Если нужно, чтобы значения переживали не только refresh, но и попадали в исходник (EDITMODE-маркеры + WebSocket-сервер на :5175) — полная инструкция в `references/tweaks-persist-file-writeback.md`. Прежняя расширенная версия (запись в tokens.css через HTTP :8082, sidecar JSON `.tweaks/`, multi-state сравнение версий, reset, антипаттерны) — `references/legacy-tweaks-persist.md`.

## Когда добавлять

- Если пользователь явно просит варианты, а сразу делать N HTML-файлов — оверкилл.
- Если хочется дать манагеру/клиенту повертеть прототип самому.
- Если в дизайне есть параметры, которые трудно решить без живого превью (плотность, цвет, копирайт).

## Чего не делать

- Не пихай в Tweaks ВСЕ возможные параметры. Это не настройки приложения. 4–8 ключевых тумблеров — потолок.
- Не делай Tweaks основным UI. Это инструмент дизайнера, не пользователя.
- Если параметров много — группируй в секции, не вали в один длинный список.

## Если короткого описания не хватило

Прежняя, более длинная версия навыка лежит целиком в `references/legacy-tweaks-panel.md`. Секции там: Каркас, Использование в App, Какие тёрлы стоит давать, tweaks-persist, Антипаттерны.
