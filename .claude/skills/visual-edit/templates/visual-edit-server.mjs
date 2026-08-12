import { WebSocketServer } from 'ws';
import fs from 'node:fs/promises';

const wss = new WebSocketServer({ port: 5174 });
wss.on('connection', ws => {
  ws.on('message', async (raw) => {
    const { selector, prop, value } = JSON.parse(raw);
    const file = process.argv[2];
    let css = await fs.readFile(file, 'utf8');
    const rule = `${selector} { ${prop}: ${value}; }`;
    css = css.replace(/\/\* visual-edit \*\/[\s\S]*?\/\* \/visual-edit \*\//,
      `/* visual-edit */\n${rule}\n/* /visual-edit */`);
    if (!css.includes('/* visual-edit */')) css += `\n/* visual-edit */\n${rule}\n/* /visual-edit */`;
    await fs.writeFile(file, css);
    console.log('✓ patched', selector, prop, value);
  });
});
console.log('visual-edit server on :5174 — patches', process.argv[2]);
