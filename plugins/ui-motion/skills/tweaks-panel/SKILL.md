---
name: tweaks-panel
description: Sidebar-панель с крутилками (sliders/toggles/color pickers) для живой настройки прототипа. Юзер может менять primary color, font scale, density, theme, не открывая код. Поверх interactive-prototype.
when_to_use: Юзер хочет «дай переключатели для вариантов», «можно покрутить размер шрифта», «слайдер для цвета», «крутилки». Лучше чем плодить N статичных вариантов.
---

# Tweaks panel

Боковая панель с контролами, привязанными к CSS variables через `document.documentElement.style.setProperty()`.

## Каркас

```jsx
function TweaksPanel({ tweaks, onChange }) {
  const [open, setOpen] = useState(true);
  return (
    <aside style={{
      position: 'fixed', top: 0, right: open ? 0 : -300, width: 300, height: '100vh',
      background: '#fff', borderLeft: '1px solid #e5e7eb', padding: 24,
      overflowY: 'auto', transition: 'right .25s', zIndex: 100,
      boxShadow: '-8px 0 24px rgba(0,0,0,0.06)',
      fontFamily: '-apple-system, system-ui, sans-serif',
    }}>
      <button onClick={() => setOpen(!open)} style={{
        position: 'absolute', left: -32, top: 16, width: 32, height: 32,
        background: '#fff', border: '1px solid #e5e7eb', borderRight: 'none',
        borderRadius: '8px 0 0 8px', cursor: 'pointer',
      }}>{open ? '→' : '←'}</button>

      <h3 style={{ margin: '0 0 16px', fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Tweaks</h3>

      {tweaks.map(t => (
        <div key={t.key} style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 6 }}>{t.label}</label>
          {t.type === 'range' && (
            <>
              <input type="range" min={t.min} max={t.max} step={t.step || 1}
                value={t.value} onChange={e => onChange(t.key, +e.target.value)}
                style={{ width: '100%' }} />
              <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>{t.value}{t.unit || ''}</div>
            </>
          )}
          {t.type === 'color' && (
            <input type="color" value={t.value} onChange={e => onChange(t.key, e.target.value)}
              style={{ width: '100%', height: 32, cursor: 'pointer' }} />
          )}
          {t.type === 'toggle' && (
            <button onClick={() => onChange(t.key, !t.value)} style={{
              width: 48, height: 26, borderRadius: 13, border: 'none',
              background: t.value ? '#YOUR_BRAND_COLOR' : '#d1d5db', position: 'relative', cursor: 'pointer',
            }}>
              <div style={{
                position: 'absolute', top: 2, left: t.value ? 24 : 2,
                width: 22, height: 22, borderRadius: '50%', background: '#fff',
                transition: 'left .2s',
              }}/>
            </button>
          )}
          {t.type === 'select' && (
            <select value={t.value} onChange={e => onChange(t.key, e.target.value)}
              style={{ width: '100%', padding: 6, border: '1px solid #e5e7eb', borderRadius: 6 }}>
              {t.options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          )}
        </div>
      ))}
    </aside>
  );
}
window.TweaksPanel = TweaksPanel;
```

## Использование в App

```jsx
function App() {
  const [tw, setTw] = useState({
    primary: '#YOUR_PRIMARY',
    fontScale: 100,
    radius: 12,
    darkMode: false,
    density: 'cozy',
  });

  // Применяем tweaks к CSS variables
  useEffect(() => {
    const r = document.documentElement;
    r.style.setProperty('--h-primary', tw.primary);
    r.style.setProperty('--h-font-scale', tw.fontScale + '%');
    r.style.setProperty('--h-r-md', tw.radius + 'px');
    r.style.setProperty('color-scheme', tw.darkMode ? 'dark' : 'light');
  }, [tw]);

  const tweaks = [
    { key: 'primary',   label: 'Primary color',  type: 'color',  value: tw.primary },
    { key: 'fontScale', label: 'Font scale',     type: 'range',  min: 80, max: 120, step: 5, value: tw.fontScale, unit: '%' },
    { key: 'radius',    label: 'Border radius',  type: 'range',  min: 0, max: 24, value: tw.radius, unit: 'px' },
    { key: 'darkMode',  label: 'Dark mode',      type: 'toggle', value: tw.darkMode },
    { key: 'density',   label: 'Density',        type: 'select', value: tw.density, options: ['compact','cozy','spacious'] },
  ];

  return (
    <>
      <Prototype />
      <TweaksPanel tweaks={tweaks} onChange={(k, v) => setTw(p => ({...p, [k]: v }))} />
    </>
  );
}
```

## Какие тёрлы стоит давать

| Тёрл | Variable | Когда нужен |
|---|---|---|
| Primary color | `--primary` | смена бренда / эксперимент |
| Font family | `--font-body` | сравнение шрифтов |
| Font scale (80-120%) | `--font-scale` | a11y тест на крупный шрифт |
| Border radius | `--r-md` | brutalism (0) vs friendly (16) |
| Density | `--space-base` | compact / cozy / spacious |
| Dark mode | `color-scheme` | a/b dark и light |
| Reduced motion | `--motion` | a11y тест |
| Sidebar collapsed | UI state | desktop vs tablet pattern |

3-7 тёрлов — sweet spot. 10+ → юзер запутается.

## tweaks-persist (если установлен)

Скилл `tweaks-persist` сохраняет состояние тёрл в `localStorage` и восстанавливает при перезагрузке. По умолчанию tweaks-panel этого не делает — каждое открытие = свежий старт.

## Антипаттерны

- 12+ тёрлов → юзер не понимает что менять
- Изменения без visual-feedback → крутишь, ничего не происходит, бросаешь
- Тёрлы для мелочей (`label-letter-spacing`, `box-shadow-y-offset`) → не дают ощутимую разницу
- Тёрл без диапазона (input без min/max) → поломаешь дизайн на крайних значениях
- Сохранять тёрлы в URL (?primary=blue&radius=12) → URL длинный, не читается
- Не показывать текущее значение → не понятно что выбрал
