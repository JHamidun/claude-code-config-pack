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
