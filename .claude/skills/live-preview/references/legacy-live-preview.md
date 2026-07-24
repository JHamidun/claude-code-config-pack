<!-- LEGACY: полное тело скилла 'live-preview' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: live-preview
description: Локальный сервер с автоперезагрузкой при изменениях файлов. Vite-style dev experience внутри Claude Code — меняешь HTML/JSX, страница в браузере перерисовывается. Не подделка claude.ai/design canvas, но рядом.
when_to_use: Юзер активно итерирует артефакт, тестит руками. Не каждое изменение перезапускать «open file» — просто пиши в HTML, в браузере перезагружается.
---

# Live preview

Локальный server (port 5500 / 8080) + WebSocket / Server-Sent-Events для auto-reload при file change.

## Самый простой: livereload

```bash
npm i -g browser-sync
browser-sync start --server --files "**/*.{html,css,js,jsx}" --port 8080
```

Запустит:
- HTTP server на http://localhost:8080
- Live-reload при любом изменении файлов
- Открывает в default браузере
- WebSocket overlay уведомляет об изменениях

## Альтернатива: live-server

```bash
npm i -g live-server
cd /path/to/artifact
live-server --port=8080
```

Чуть менее feature-rich чем browser-sync, но проще.

## Альтернатива 3: vite (если артефакт уже React)

```bash
npm create vite@latest artifact -- --template react
cd artifact && npm install
npm run dev
```

Vite быстрее (HMR через ESM), но требует package.json и dependencies. Излишне для простого HTML.

## Альтернатива 4: Python http.server + auto-reload

Без node (на Windows `python3` нет — используй `python -m http.server 8080` или `py -m http.server 8080`):
```bash
# Просто HTTP без auto-reload
python -m http.server 8080   # mac/linux: python3 -m http.server 8080

# С auto-reload — нужен extra script
pip install livereload
python -c "
from livereload import Server
s = Server()
s.watch('*.html')
s.watch('**/*.css')
s.watch('**/*.jsx')
s.serve(port=8080, root='.')
"
```

## Custom auto-reload через WebSocket (если хочется без deps)

`scripts/dev-server.js`:
```js
const http = require('http');
const fs = require('fs');
const path = require('path');
const ws = require('ws');
const chokidar = require('chokidar');

const PORT = 8080;
const ROOT = process.cwd();

// HTTP server
http.createServer((req, res) => {
  let url = req.url === '/' ? '/index.html' : req.url;
  let file = path.join(ROOT, url.split('?')[0]);
  if (!fs.existsSync(file)) { res.writeHead(404); return res.end('Not found'); }
  let content = fs.readFileSync(file);
  // Inject live-reload в HTML
  if (file.endsWith('.html')) {
    content = content.toString().replace('</body>',
      `<script>
         const ws = new WebSocket('ws://localhost:${PORT + 1}');
         ws.onmessage = () => location.reload();
       </script></body>`);
  }
  const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript', '.jsx': 'text/babel' };
  res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'text/plain' });
  res.end(content);
}).listen(PORT);

// WebSocket для broadcast
const wss = new ws.Server({ port: PORT + 1 });

// File watcher
chokidar.watch(ROOT, { ignored: /node_modules|\.git/ }).on('change', () => {
  wss.clients.forEach(c => c.send('reload'));
});

console.log(`Dev server: http://localhost:${PORT}`);
```

```bash
npm i ws chokidar
node scripts/dev-server.js
```

## Browser-sync features

Поверх auto-reload даёт:
- **Cross-device sync** — открой на phone и desktop, скроллы синхронизированы
- **Inject CSS without reload** — стили обновляются без потери state
- **Network access** — `--listen-on-all-ips` для доступа с другого устройства

```bash
browser-sync start --server --files "**/*.{html,css,js}" \
  --port 8080 \
  --no-open \
  --tunnel my-prototype  # ngrok-like — public URL
```

## Best practices

| Что | Браузерный refresh | Через CSS-injection |
|---|---|---|
| Изменил HTML | ✅ нужен reload | — |
| Изменил CSS | ❌ зачем reload | ✅ inject, state preserved |
| Изменил JSX | ✅ нужен reload (Babel компилирует на ходу) | — |
| Изменил .json data | зависит | data fetch'нется при reload |

Browser-sync с `--reload-debounce 500` — group изменения, не reload каждые 50ms.

## Tunneling для шеринга

Чтобы юзер видел prototype со своего устройства без копирования файлов:

```bash
# Через ngrok
ngrok http 8080
# → https://random.ngrok-free.app

# Через cloudflare tunnel (free, persistent)
cloudflared tunnel --url http://localhost:8080
```

Опасно: tunnel exposes localhost public. Не запускай при чувствительных данных.

## Когда НЕ использовать

- Прототип finalize'нут, экспорт в standalone-html → больше не нужен dev server
- Артефакт не имеет live итераций (single static cover) → просто `open file`
- В CI / headless env → используй verifier, не live-preview

## Stack

- `verifier` — финальная проверка после dev (auto-reload не панацея, могут быть console errors которые ты не заметил в Visual)
- `interactive-prototype` — чаще всего dev'ишь именно его
- `tweaks-panel` — комбо с live-reload даёт hot-iteration UX

## Антипаттерны

- Жить в production-build mode во время разработки → 30 сек compile на каждое изменение
- Watch ВСЕ файлы (`**/*`) → false reloads на .git changes
- Не использовать debounce → каждый keystroke в editor → reload
- Tunnel в чувствительный env (production credentials в env) → security risk
- Not добавлять `<base href>` если артефакт под subpath → relative URL'ы ломаются
