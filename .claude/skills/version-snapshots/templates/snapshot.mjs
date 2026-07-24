import fs from 'node:fs/promises';
import path from 'node:path';

const file = process.argv[2];
const note = process.argv.slice(3).join(' ') || '(без подписи)';
if (!file) { console.error('Usage: node snapshot.mjs <file> [note]'); process.exit(1); }

const dir = '.snapshots';
await fs.mkdir(dir, { recursive: true });

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const ext = path.extname(file);
const base = path.basename(file, ext);
const dest = path.join(dir, `${base}.${ts}${ext}`);
await fs.copyFile(file, dest);

const manifest = path.join(dir, 'MANIFEST.md');
const line = `\n### ${ts}  \n**${path.basename(dest)}** — ${note}\n`;
await fs.appendFile(manifest, line);
console.log('✓', dest);
