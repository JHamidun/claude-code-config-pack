import pptxgen from 'pptxgenjs';
import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const [, , file, out = 'deck.pptx'] = process.argv;
if (!file) {
  console.error('Usage: node pptx-screenshots.mjs <html> [out.pptx]');
  process.exit(1);
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

const total = await page.evaluate(() => document.querySelector('deck-stage').total);
await page.evaluate(() => document.querySelector('deck-stage').setAttribute('noscale', ''));

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';

for (let i = 0; i < total; i++) {
  await page.evaluate(idx => document.querySelector('deck-stage').go(idx), i);
  await page.waitForTimeout(600);
  const buf = await page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1920, height: 1080 } });
  const slide = pres.addSlide();
  slide.background = { data: 'data:image/png;base64,' + buf.toString('base64') };
  console.log(`  ✓ slide ${i + 1}/${total}`);
}

await pres.writeFile({ fileName: out });
await browser.close();
console.log('✓', out);
