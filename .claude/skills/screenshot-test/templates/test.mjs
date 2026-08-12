import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import fs from 'node:fs/promises';
import path from 'node:path';

const cfg = JSON.parse(await fs.readFile('test-screenshots.config.json', 'utf8'));
const isUpdate = process.argv.includes('--update');

const baseDir = 'screenshots/baseline';
const curDir  = 'screenshots/current';
const diffDir = 'screenshots/diff';
await fs.mkdir(curDir, { recursive: true });
await fs.mkdir(diffDir, { recursive: true });

const browser = await chromium.launch();
let failures = 0;

for (const t of cfg.tests) {
  const ctx = await browser.newContext({ viewport: { width: t.viewport[0], height: t.viewport[1] } });
  const page = await ctx.newPage();
  await page.goto(`file://${path.resolve(t.url)}`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts && document.fonts.ready);

  const curPath  = path.join(curDir,  t.name + '.png');
  const basePath = path.join(baseDir, t.name + '.png');

  await page.screenshot({ path: curPath, fullPage: true });
  await ctx.close();

  if (isUpdate) {
    await fs.mkdir(baseDir, { recursive: true });
    await fs.copyFile(curPath, basePath);
    console.log(`✓ Updated baseline: ${t.name}`);
    continue;
  }

  let basePNG;
  try { basePNG = PNG.sync.read(await fs.readFile(basePath)); }
  catch { console.error(`✗ ${t.name}: no baseline. Run with --update.`); failures++; continue; }

  const curPNG = PNG.sync.read(await fs.readFile(curPath));
  if (basePNG.width !== curPNG.width || basePNG.height !== curPNG.height) {
    console.error(`✗ ${t.name}: size mismatch ${basePNG.width}x${basePNG.height} vs ${curPNG.width}x${curPNG.height}`);
    failures++;
    continue;
  }

  const { width, height } = basePNG;
  const diffPNG = new PNG({ width, height });
  const px = pixelmatch(basePNG.data, curPNG.data, diffPNG.data, width, height, { threshold: cfg.threshold });

  if (px > cfg.maxDiffPixels) {
    const diffPath = path.join(diffDir, t.name + '.png');
    await fs.writeFile(diffPath, PNG.sync.write(diffPNG));
    console.error(`✗ ${t.name}: ${px} px differ (max ${cfg.maxDiffPixels}). diff → ${diffPath}`);
    failures++;
  } else {
    console.log(`✓ ${t.name}: ${px} px (within ${cfg.maxDiffPixels})`);
  }
}

await browser.close();
process.exit(failures ? 1 : 0);
