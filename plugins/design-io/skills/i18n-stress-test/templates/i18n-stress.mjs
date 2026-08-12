import { chromium } from 'playwright';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const file = process.argv[2];
if (!file) { console.error('Usage: node i18n-stress.mjs <file>'); process.exit(1); }

const samples = {
  de: ['Anwendungseinstellungen', 'Benachrichtigungseinstellungen', 'Bestätigungs-E-Mail'],
  ar: ['إعدادات الإشعارات', 'احفظ التغييرات', 'تسجيل الدخول'],
  ja: ['通知設定をカスタマイズ', '保存', 'サインイン'],
  emoji: ['🌟⭐✨💫🌠☄️', '🎉🎊🥳', '👨👩👧👦'],
};

const browser = await chromium.launch();
for (const [lang, words] of Object.entries(samples)) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto(pathToFileURL(path.resolve(file)).href);

  // RTL для арабского
  if (lang === 'ar') await page.evaluate(() => document.documentElement.setAttribute('dir', 'rtl'));

  // Заменим текстовые узлы
  await page.evaluate((words) => {
    function walk(node) {
      if (node.nodeType === 3 && node.textContent.trim().length > 3) {
        node.textContent = words[Math.floor(Math.random() * words.length)];
      }
      for (const c of node.childNodes) walk(c);
    }
    walk(document.body);
  }, words);

  // Найдём переполнения
  const overflows = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('*').forEach(el => {
      if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
        out.push({ tag: el.tagName, text: el.textContent.slice(0, 40), w: el.scrollWidth, cw: el.clientWidth });
      }
    });
    return out.slice(0, 20);
  });

  await page.screenshot({ path: `i18n-${lang}.png` });
  await page.close();

  console.log(`\n[${lang.toUpperCase()}] screenshot → i18n-${lang}.png`);
  if (overflows.length) {
    console.log('  Переполнения:');
    for (const o of overflows) console.log(`    ${o.tag} (${o.cw}px < ${o.w}px): "${o.text}"`);
  } else {
    console.log('  ✓ нет переполнений');
  }
}
await browser.close();
