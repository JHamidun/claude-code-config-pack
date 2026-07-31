<!-- LEGACY: полное тело скилла 'tweaks-persist' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: tweaks-persist
description: Сохранение состояния `tweaks-panel` в файл tokens.css или sidecar JSON, чтобы при перезагрузке прототипа крутилки не сбрасывались. Опционально: пишет финальное значение обратно в tokens.css при «Save tweaks».
when_to_use: Активный экспериментальный режим с tweaks-panel, юзер крутит и хочет сохранить итог. Перед dev-handoff (фиксирует выбранные значения в tokens.css).
---

# Tweaks persist

`tweaks-panel` без persist — каждое открытие свежий старт. Persist фиксирует значения 2 способами:
1. `localStorage` — между перезагрузками браузера
2. `tokens.css` — одним кликом «save» переписывает CSS variables

## localStorage tier (auto)

Расширение `tweaks-panel` каркаса:
```jsx
function App() {
  const [tw, setTw] = useState(() => {
    const stored = localStorage.getItem('tweaks-panel');
    return stored ? JSON.parse(stored) : DEFAULTS;
  });

  useEffect(() => {
    localStorage.setItem('tweaks-panel', JSON.stringify(tw));
    applyToCSSVars(tw);
  }, [tw]);

  return <>...<TweaksPanel tweaks={tw} onChange={setTw} /></>;
}
```

Юзер двигает слайдер → reload страницы → значения те же.

## CSS file tier (manual «Save»)

Кнопка `[Save to tokens.css]` в TweaksPanel посылает текущие значения в backend:

```jsx
function SaveButton({ tw }) {
  const save = async () => {
    const r = await fetch('/api/save-tokens', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tw),
    });
    if (r.ok) toast('Saved to tokens.css');
  };
  return <button onClick={save}>💾 Save</button>;
}
```

Backend (`scripts/save-tokens-server.js`):
```js
const http = require('http');
const fs = require('fs');

const TOKENS_PATH = './styles/tokens.css';

http.createServer((req, res) => {
  if (req.url === '/api/save-tokens' && req.method === 'POST') {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      const tw = JSON.parse(body);
      let css = fs.readFileSync(TOKENS_PATH, 'utf-8');

      // Заменить CSS variables на новые значения
      const map = {
        primary:    '--h-primary',
        radius:     '--h-r-md',
        fontScale:  '--h-font-scale',
        density:    '--h-density',
      };

      for (const [key, value] of Object.entries(tw)) {
        const cssVar = map[key];
        if (!cssVar) continue;
        const re = new RegExp(`(${cssVar}:\\s*)([^;]+);`);
        if (re.test(css)) {
          css = css.replace(re, `$1${value};`);
        } else {
          css = css.replace(/^:root\s*\{/, `:root {\n  ${cssVar}: ${value};`);
        }
      }

      fs.writeFileSync(TOKENS_PATH, css);
      res.end(JSON.stringify({ ok: true }));
    });
  }
}).listen(8082);
```

```bash
node scripts/save-tokens-server.js
```

## Sidecar JSON (без overwrite tokens.css)

Для osторожных юзеров — не переписывать tokens.css, а сохранять отдельно:

```
.tweaks/
├── current.json          # текущее состояние
└── history/              # снапшоты
    ├── (see git history)-warm-cream.json
    └── (see git history)-dark-cyan.json
```

current.json:
```json
{
  "primary": "#YOUR_PRIMARY",
  "radius": 12,
  "fontScale": 105,
  "density": "cozy",
  "darkMode": false,
  "saved": "(see git history)T11:23:00Z"
}
```

При load HTML — JS читает `.tweaks/current.json` через fetch, применяет к CSS variables перед render.

## Multi-state (compare versions)

Если юзер хочет сравнить 2 версии:
1. Save current as `warm-v1.json`
2. Tweak knobs → Save as `dark-v2.json`
3. URL `?tweaks=warm-v1` или `?tweaks=dark-v2` → переключение

```jsx
const variant = new URL(location).searchParams.get('tweaks') || 'current';
useEffect(() => {
  fetch(`.tweaks/${variant}.json`).then(r => r.json()).then(setTw);
}, [variant]);
```

## Reset to defaults

Кнопка `[Reset]` в TweaksPanel:
```jsx
function ResetButton() {
  return <button onClick={() => {
    localStorage.removeItem('tweaks-panel');
    location.reload();
  }}>↺ Reset</button>;
}
```

## Stack

- `tweaks-panel` — обязательно, это его расширение
- `version-snapshots` — каждое «Save tokens» создаёт snapshot
- `live-preview` — после save tokens.css → reload в браузере

## Антипаттерны

- Auto-save tokens.css на каждый change → файл записывается 100 раз/мин
- LocalStorage без `try/catch` для quota → краш на старых браузерах
- Хранить tweaks вместе с данными app → конфликт ключей
- Не уведомлять юзера о save → не понятно сработало или нет
- Save tokens.css без backup → невозможно откатить
- Sidecar JSON в git → конфликты merge при collaborate
