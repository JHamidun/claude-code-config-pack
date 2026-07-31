<!-- Бывший отдельный скилл tweaks-persist (новое дерево @2026-05-03), поглощён tweaks-panel при консолидации 2026-07-18.
     Диск-персистенс: EDITMODE-маркеры в HTML + WebSocket-сервер :5175, пишет tweaks обратно в исходник. -->

---
name: tweaks-persist
version: 1.0.0
description: Дополнение к tweaks-panel — сохранять изменения обратно в файл, не только в localStorage.
when_to_use: Когда нужно, чтобы tweaks-state переживал refresh и попадал в исходник.
---

# Tweaks persist

`tweaks-panel` по умолчанию хранит state в `localStorage`. Этот скилл добавляет персистенс **на диск**.

## Каркас

В исходнике HTML обернуть defaults JSON в маркеры:

```html
<script>
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "primary": "#D97757",
  "fontSize": 16,
  "dark": false
}/*EDITMODE-END*/;
</script>
```

При изменении tweaks-panel шлёт `{type:'__edit_mode_set_keys', edits:{...}}` по WebSocket → локальный сервер парсит JSON между маркерами, мерджит, пишет обратно.

## Сервер

`templates/tweaks-server.mjs`:

```js
import { WebSocketServer } from 'ws';
import fs from 'node:fs/promises';

const file = process.argv[2];
if (!file) { console.error('Usage: node tweaks-server.mjs <file>'); process.exit(1); }

const wss = new WebSocketServer({ port: 5175 });
const re = /\/\*EDITMODE-BEGIN\*\/([\s\S]*?)\/\*EDITMODE-END\*\//;

wss.on('connection', ws => {
  ws.on('message', async raw => {
    const msg = JSON.parse(raw);
    if (msg.type !== '__edit_mode_set_keys') return;
    let html = await fs.readFile(file, 'utf8');
    const m = html.match(re);
    if (!m) { ws.send(JSON.stringify({error:'no markers'})); return; }
    const cur = JSON.parse(m[1]);
    const next = { ...cur, ...msg.edits };
    html = html.replace(re,
      `/*EDITMODE-BEGIN*/${JSON.stringify(next, null, 2)}/*EDITMODE-END*/`);
    await fs.writeFile(file, html);
    ws.send(JSON.stringify({ ok: true, keys: Object.keys(msg.edits) }));
    console.log('✓', Object.keys(msg.edits).join(', '));
  });
});
console.log('tweaks-persist on :5175 →', file);
```

## Браузерная сторона

В `tweaks-panel` хук `useTweaks(defaults)` → при изменении делает:

```js
fetch('http://localhost:5175', { method: 'POST', body: JSON.stringify({...}) });
```

или через WebSocket:

```js
const ws = new WebSocket('ws://localhost:5175');
function setTweak(key, value) {
  state[key] = value; render();
  ws.send(JSON.stringify({type: '__edit_mode_set_keys', edits: {[key]: value}}));
}
```

## Запуск

```bash
node tweaks-server.mjs index.html  # терминал 1
node live.mjs index.html           # терминал 2
```

При сохранении в tweaks-panel — файл переписывается, live-preview перезагружает страницу с новыми defaults.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-tweaks-persist.md`. Секции там: localStorage tier (auto), CSS file tier (manual «Save»), Sidecar JSON (без overwrite tokens.css), Multi-state (compare versions), Reset to defaults, Stack, Антипаттерны.
