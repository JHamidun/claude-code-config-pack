import fs from 'node:fs/promises';
import path from 'node:path';
import { JSDOM } from 'jsdom';

const file = process.argv[2];
if (!file) { console.error('Usage: node license-check.mjs <file>'); process.exit(1); }

const html = await fs.readFile(file, 'utf8');
const dom = new JSDOM(html);
const doc = dom.window.document;

const issues = [];

// Картинки без alt
doc.querySelectorAll('img').forEach((img, i) => {
  if (!img.hasAttribute('alt')) {
    issues.push({ kind: 'a11y', el: 'img', index: i, msg: `<img src="${img.getAttribute('src')}"> без alt` });
  }
});

// Stock-источники без указания
const stockHosts = ['images.unsplash.com', 'images.pexels.com', 'cdn.shutterstock.com', 'getty'];
doc.querySelectorAll('img').forEach((img) => {
  const src = img.getAttribute('src') || '';
  for (const h of stockHosts) {
    if (src.includes(h) && !img.hasAttribute('data-credit')) {
      issues.push({ kind: 'license', el: 'img', msg: `Stock-картинка без data-credit: ${src}` });
    }
  }
});

// Шрифты Google Fonts
doc.querySelectorAll('link[href*="fonts.googleapis.com"]').forEach(l => {
  const href = l.getAttribute('href');
  issues.push({
    kind: 'info', el: 'link',
    msg: `Google Fonts: ${href} — проверь, что у выбранных шрифтов SIL Open Font License`
  });
});

// Видео без credits
doc.querySelectorAll('video, iframe[src*="youtube"], iframe[src*="vimeo"]').forEach(v => {
  if (!v.hasAttribute('data-credit')) {
    issues.push({ kind: 'license', el: v.tagName.toLowerCase(), msg: 'Видео без data-credit' });
  }
});

if (!issues.length) { console.log('✓ Лицензии в порядке'); process.exit(0); }
console.error(`\n✗ ${issues.length} замечаний:\n`);
for (const i of issues) console.error(`  [${i.kind}] ${i.msg}`);
process.exit(issues.filter(i => i.kind !== 'info').length ? 1 : 0);
