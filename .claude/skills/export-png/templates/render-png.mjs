import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const args = parseArgs(process.argv.slice(2));
const [file, outArg] = args._;
if (!file) {
  console.error('Usage: node render-png.mjs <html> <out-dir-or-file> [--selector S] [--width N] [--height N] [--scale 2] [--delay 600]');
  process.exit(1);
}

const url = pathToFileURL(path.resolve(file)).href;
const width  = +(args.width  || 1920);
const height = +(args.height || 1080);
const scale  = +(args.scale  || 2);
const delay  = +(args.delay  || 600);

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width, height },
  deviceScaleFactor: scale,
});
const page = await ctx.newPage();
await page.goto(url, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

const isDeck = await page.evaluate(() => !!document.querySelector('deck-stage'));

if (isDeck) {
  await fs.mkdir(outArg, { recursive: true });
  const total = await page.evaluate(() => document.querySelector('deck-stage').total);
  await page.evaluate(() => document.querySelector('deck-stage').setAttribute('noscale', ''));
  for (let i = 0; i < total; i++) {
    await page.evaluate(idx => document.querySelector('deck-stage').go(idx), i);
    await page.waitForTimeout(delay);
    const num = String(i + 1).padStart(2, '0');
    await page.screenshot({ path: path.join(outArg, `slide-${num}.png`), fullPage: false });
    console.log(`  ✓ slide-${num}.png`);
  }
} else if (args.selector) {
  await fs.mkdir(outArg, { recursive: true });
  const handles = await page.$$(args.selector);
  for (const [i, h] of handles.entries()) {
    const num = String(i + 1).padStart(2, '0');
    await h.screenshot({ path: path.join(outArg, `${num}.png`), omitBackground: !!args['omit-background'] });
    console.log(`  ✓ ${num}.png`);
  }
} else {
  const out = outArg.endsWith('.png') ? outArg : path.join(outArg, 'screen.png');
  if (!out.endsWith('.png') || out.includes('/')) {
    await fs.mkdir(path.dirname(out), { recursive: true });
  }
  await page.screenshot({ path: out, fullPage: !!args['full-page'] });
  console.log('✓', out);
}

await browser.close();

function parseArgs(argv) {
  const a = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v.startsWith('--')) {
      const k = v.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith('--')) { a[k] = true; }
      else { a[k] = next; i++; }
    } else a._.push(v);
  }
  return a;
}
