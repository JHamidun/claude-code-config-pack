import { chromium } from 'playwright';
import fs from 'node:fs/promises';

const url = process.argv[2];
if (!url) { console.error('Usage: node extract.mjs <url>'); process.exit(1); }

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

const data = await page.evaluate(() => {
  const get = (sel, prop) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    return getComputedStyle(el)[prop];
  };

  // Цвета — пробежать по видимым элементам и посчитать частоту
  const colors = new Map();
  document.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (r.width < 30 || r.height < 30) return;
    [cs.backgroundColor, cs.color].forEach(c => {
      if (!c || c === 'rgba(0, 0, 0, 0)' || c === 'transparent') return;
      colors.set(c, (colors.get(c) || 0) + 1);
    });
  });
  const topColors = [...colors.entries()].sort((a,b) => b[1]-a[1]).slice(0, 10);

  // Шрифты по hierarchy
  const fonts = {
    h1:    { family: get('h1', 'fontFamily'), weight: get('h1', 'fontWeight'), size: get('h1', 'fontSize') },
    h2:    { family: get('h2', 'fontFamily'), weight: get('h2', 'fontWeight'), size: get('h2', 'fontSize') },
    body:  { family: get('p',  'fontFamily'), weight: get('p',  'fontWeight'), size: get('p',  'fontSize') },
    button:{ family: get('button, .button, .btn', 'fontFamily'), weight: get('button, .button, .btn', 'fontWeight'), size: get('button, .button, .btn', 'fontSize') },
  };

  // Копирайт
  const copy = {
    title:    document.querySelector('h1')?.innerText?.slice(0, 100),
    subtitle: document.querySelector('h1 + p, h1 ~ p')?.innerText?.slice(0, 200),
    cta:      [...document.querySelectorAll('button, .button, .btn, a.cta')]
      .map(b => b.innerText.trim()).filter(Boolean).slice(0, 5),
  };

  return { topColors, fonts, copy };
});

await page.screenshot({ path: 'brand-snapshot.png', fullPage: false });
await browser.close();

await fs.writeFile('brand.json', JSON.stringify(data, null, 2));
console.log('✓ brand.json + brand-snapshot.png');
console.log('\nTop colors:'); data.topColors.forEach(([c, n]) => console.log(`  ${c.padEnd(28)} ×${n}`));
console.log('\nFonts:'); console.table(data.fonts);
console.log('\nCopy:'); console.log(data.copy);
