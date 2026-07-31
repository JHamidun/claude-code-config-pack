import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const [, , file, outArg] = process.argv;
if (!file) {
  console.error('Usage: node print-pdf.mjs <html> [out.pdf]');
  process.exit(1);
}

const out = outArg || file.replace(/\.html?$/, '.pdf');
const url = pathToFileURL(path.resolve(file)).href;

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(url, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

const dims = await page.evaluate(() => {
  const ds = document.querySelector('deck-stage');
  return ds ? {
    w: +ds.getAttribute('width')  || 1920,
    h: +ds.getAttribute('height') || 1080,
  } : null;
});

if (dims) {
  await page.evaluate(() => document.querySelector('deck-stage').setAttribute('noscale', ''));
  await page.pdf({
    path: out,
    width:  dims.w + 'px',
    height: dims.h + 'px',
    printBackground: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
    preferCSSPageSize: true,
  });
} else {
  await page.pdf({ path: out, format: 'A4', printBackground: true });
}

await browser.close();
console.log('✓', out);
