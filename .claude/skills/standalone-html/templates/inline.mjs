import fs from 'node:fs/promises';
import path from 'node:path';

const [, , input, output] = process.argv;
if (!input) { console.error('Usage: node inline.mjs <input.html> [output.html]'); process.exit(1); }

const out = output || input.replace(/\.html?$/, '.standalone.html');
const dir = path.dirname(input);
let html = await fs.readFile(input, 'utf8');

// <link rel="stylesheet" href="..."> → <style>
html = await replaceAsync(html, /<link\s+[^>]*rel=["']stylesheet["'][^>]*>/gi, async (tag) => {
  const m = tag.match(/href=["']([^"']+)["']/);
  if (!m || /^https?:|\/\//.test(m[1])) return tag;
  const css = await fs.readFile(path.join(dir, m[1]), 'utf8');
  return `<style>\n${css}\n</style>`;
});

// <script src="..."> → <script>...</script>
html = await replaceAsync(html, /<script\s+[^>]*src=["']([^"']+)["'][^>]*>\s*<\/script>/gi, async (tag, src) => {
  if (/^https?:|\/\//.test(src)) return tag;
  const code = await fs.readFile(path.join(dir, src), 'utf8');
  const typeMatch = tag.match(/type=["']([^"']+)["']/);
  const type = typeMatch ? ` type="${typeMatch[1]}"` : '';
  return `<script${type}>\n${code}\n</script>`;
});

// <img src="..."> → data URL
html = await replaceAsync(html, /<img\s+[^>]*src=["']([^"']+)["'][^>]*>/gi, async (tag, src) => {
  if (/^https?:|\/\/|data:/.test(src)) return tag;
  try {
    const buf = await fs.readFile(path.join(dir, src));
    const ext = path.extname(src).slice(1).toLowerCase() || 'png';
    const mime = { svg: 'svg+xml', jpg: 'jpeg', jpeg: 'jpeg', png: 'png', webp: 'webp', gif: 'gif' }[ext] || 'octet-stream';
    const data = `data:image/${mime};base64,${buf.toString('base64')}`;
    return tag.replace(src, data);
  } catch { return tag; }
});

// url(...) внутри инлайн-CSS — тоже data URL
html = await replaceAsync(html, /url\(["']?([^"')]+)["']?\)/g, async (m, src) => {
  if (/^https?:|\/\/|data:/.test(src)) return m;
  try {
    const buf = await fs.readFile(path.join(dir, src));
    const ext = path.extname(src).slice(1).toLowerCase();
    const mime = ({ woff2: 'font/woff2', woff: 'font/woff', ttf: 'font/ttf',
      svg: 'image/svg+xml', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg' })[ext] || 'application/octet-stream';
    return `url("data:${mime};base64,${buf.toString('base64')}")`;
  } catch { return m; }
});

await fs.writeFile(out, html);
console.log('✓', out);

async function replaceAsync(str, re, fn) {
  const promises = [];
  str.replace(re, (...args) => { promises.push(fn(...args)); return ''; });
  const results = await Promise.all(promises);
  let i = 0;
  return str.replace(re, () => results[i++]);
}
