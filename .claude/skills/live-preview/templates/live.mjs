import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';
import chokidar from 'chokidar';
import { WebSocketServer } from 'ws';

const root = process.cwd();
const entry = process.argv[2] || 'index.html';
const PORT = +(process.env.PORT || 5173);

const inject = `
<script>
(function () {
  const ws = new WebSocket('ws://' + location.host + '/_lp');
  ws.onmessage = (e) => { if (e.data === 'reload') location.reload(); };
})();
</script>
</body>`;

const types = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.jsx': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.woff2': 'font/woff2',
};

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(url.parse(req.url).pathname);
  if (p === '/') p = '/' + entry;
  const file = path.join(root, p);
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end('Not found'); return;
  }
  const ext = path.extname(file).toLowerCase();
  const type = types[ext] || 'application/octet-stream';
  let body = fs.readFileSync(file);
  if (ext === '.html') body = body.toString().replace(/<\/body>/i, inject);
  res.writeHead(200, { 'content-type': type });
  res.end(body);
});

const wss = new WebSocketServer({ server, path: '/_lp' });

chokidar.watch(root, {
  ignored: /(^|[\/\\])\.|node_modules/, ignoreInitial: true,
}).on('all', () => {
  wss.clients.forEach(c => c.readyState === 1 && c.send('reload'));
});

server.listen(PORT, () => {
  console.log(`live-preview → http://localhost:${PORT}/  (entry: ${entry})`);
});
