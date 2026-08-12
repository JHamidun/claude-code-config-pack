import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';

const file = process.argv[2];
if (!file) { console.error('Usage: node perf.mjs <file>'); process.exit(1); }

// Поднимем простейший http-сервер для замера (file:// не работает корректно)
const server = http.createServer(async (req, res) => {
  const f = req.url === '/' ? file : '.' + req.url;
  try {
    const buf = await fs.readFile(f);
    res.writeHead(200); res.end(buf);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(r => server.listen(0, r));
const port = server.address().port;

const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
const result = await lighthouse(`http://localhost:${port}/`, {
  port: chrome.port, output: 'json',
  onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
});
await chrome.kill();
server.close();

await fs.writeFile('perf-report.json', JSON.stringify(result.lhr, null, 2));

const cats = result.lhr.categories;
console.log('\nLighthouse:');
for (const [k, v] of Object.entries(cats)) {
  const score = Math.round(v.score * 100);
  const tag = score >= 90 ? '✓' : score >= 50 ? '~' : '✗';
  console.log(`  ${tag} ${k.padEnd(16)} ${score}`);
}

const audits = result.lhr.audits;
console.log('\nВеб-витал:');
for (const k of ['largest-contentful-paint', 'cumulative-layout-shift', 'total-blocking-time']) {
  const a = audits[k];
  console.log(`  ${a.title.padEnd(28)} ${a.displayValue || '—'}`);
}

const fails = Object.values(audits)
  .filter(a => a.score !== null && a.score < 0.9 && a.details)
  .sort((x, y) => x.score - y.score)
  .slice(0, 10);
console.log('\nТоп-10 замечаний:');
for (const a of fails) console.log(`  - ${a.title} (${a.displayValue || ''})`);

process.exit(cats.performance.score >= 0.8 ? 0 : 1);
