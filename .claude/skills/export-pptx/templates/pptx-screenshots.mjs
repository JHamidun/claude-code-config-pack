// Режим screenshots: каждый слайд -> PNG -> фон слайда PPTX. Pixel-perfect, текст не правится.
//
// pptxgenjs и playwright импортируются динамически, ПОСЛЕ разбора аргументов:
// иначе `--help` падал бы с ERR_MODULE_NOT_FOUND там, где зависимости не поставлены.
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const USAGE = `Usage: node pptx-screenshots.mjs <html> [out.pptx]

  html        HTML-дек (ожидается кастомный элемент <deck-stage> с .total и .go(i))
  out.pptx    куда писать (default: deck.pptx)
  -h, --help  эта справка`;

const argv = process.argv.slice(2);
if (argv[0] === '-h' || argv[0] === '--help') { console.log(USAGE); process.exit(0); }

const [file, out = 'deck.pptx'] = argv;
if (!file) { console.error(USAGE); process.exit(1); }

const { default: pptxgen } = await import('pptxgenjs');
const { chromium } = await import('playwright');

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

// Без этой проверки отсутствующий <deck-stage> давал "Cannot read properties of null"
// на строке ниже — сообщение, по которому не догадаться, что дек просто не той разметки.
const total = await page.evaluate(() => {
  const st = document.querySelector('deck-stage');
  if (!st) return null;
  st.setAttribute('noscale', '');
  return st.total;
});
if (!total) {
  await browser.close();
  console.error('✗ в HTML нет <deck-stage> с .total/.go(i) — этот режим рассчитан на деки скилла `slides`');
  process.exit(2);
}

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
