import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const args = parse(process.argv.slice(2));
const file = args._[0];
if (!file) { console.error('Usage: node verify.mjs <html> [--require-selector S] [--out dir]'); process.exit(2); }

const out = args.out || 'verify-out';
const width  = +(args.width  || 1440);
const height = +(args.height || 900);
const wait   = +(args.wait   || 800);

await fs.mkdir(out, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width, height } });
const page = await ctx.newPage();

const logs = [];
page.on('console',   m => logs.push({ kind: m.type(),     text: m.text() }));
page.on('pageerror', e => logs.push({ kind: 'pageerror',  text: e.message }));
page.on('requestfailed', r => logs.push({ kind: 'reqfail', text: `${r.url()} — ${r.failure()?.errorText}` }));

await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });
await page.waitForTimeout(wait);

let problems = logs.filter(l => l.kind === 'error' || l.kind === 'pageerror' || l.kind === 'reqfail');

if (args['require-selector']) {
  const found = await page.$(args['require-selector']);
  if (!found) problems.push({ kind: 'missing', text: `Не найден селектор: ${args['require-selector']}` });
}

const html = await page.content();
if (html.length < 500) problems.push({ kind: 'empty', text: `Документ подозрительно короткий: ${html.length} байт` });

await page.screenshot({ path: path.join(out, 'screenshot.png'), fullPage: false });
await fs.writeFile(path.join(out, 'console.log'),
  logs.map(l => `[${l.kind}] ${l.text}`).join('\n'));

await browser.close();

if (problems.length) {
  console.error('✗ Проблемы:');
  for (const p of problems) console.error(`  [${p.kind}] ${p.text}`);
  process.exit(1);
} else {
  console.log('✓ Всё чисто. Скриншот: ' + path.join(out, 'screenshot.png'));
}

function parse(argv) {
  const a = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v.startsWith('--')) {
      const k = v.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith('--')) a[k] = true;
      else { a[k] = next; i++; }
    } else a._.push(v);
  }
  return a;
}
