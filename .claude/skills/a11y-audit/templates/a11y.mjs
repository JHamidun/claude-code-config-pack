import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const file = process.argv[2];
if (!file) { console.error('Usage: node a11y.mjs <file>'); process.exit(1); }

const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });

const results = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
  .analyze();

await browser.close();

await fs.writeFile('a11y-report.json', JSON.stringify(results, null, 2));

const v = results.violations;
if (!v.length) {
  console.log('✓ Нет нарушений WCAG AA');
  process.exit(0);
}

console.error(`\n✗ ${v.length} категорий нарушений:\n`);
for (const violation of v) {
  console.error(`  [${violation.impact}] ${violation.id} — ${violation.help}`);
  console.error(`    ${violation.helpUrl}`);
  for (const node of violation.nodes.slice(0, 3)) {
    console.error(`    → ${node.target.join(' ')}`);
    console.error(`      ${node.failureSummary.split('\n')[0]}`);
  }
  if (violation.nodes.length > 3) console.error(`    ...и ещё ${violation.nodes.length - 3}`);
  console.error('');
}
process.exit(1);
