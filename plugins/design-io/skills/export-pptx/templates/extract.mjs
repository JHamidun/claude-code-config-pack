// Режим editable, шаг 1: HTML → slides.json (координаты, текст, стили).
// Шаг 2 — build_pptx.py собирает из этого JSON настоящий PPTX.
//
// playwright импортируется динамически, ПОСЛЕ разбора аргументов:
// иначе `--help` падал бы с ERR_MODULE_NOT_FOUND там, где зависимости не поставлены.
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';

const USAGE = `Usage: node extract.mjs <html> [options]

  --slide-selector <css>   селектор слайдов (default: "deck-stage > section")
  --width  <px>            ширина viewport (default: 1920)
  --height <px>            высота viewport (default: 1080)
  --out <file>             куда писать JSON (default: <html> с расширением .json)
  -h, --help               эта справка

Далее: python build_pptx.py <out.json> deck.pptx`;

function parse(argv) {
  const a = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v.startsWith('--')) {
      const k = v.slice(2), n = argv[i + 1];
      if (!n || n.startsWith('--')) a[k] = true; else { a[k] = n; i++; }
    } else if (v === '-h') a.help = true;
    else a._.push(v);
  }
  return a;
}

const args = parse(process.argv.slice(2));
if (args.help) { console.log(USAGE); process.exit(0); }

const file = args._[0];
if (!file) { console.error(USAGE); process.exit(1); }

const sel = args['slide-selector'] || 'deck-stage > section';
const width = +(args.width || 1920);
const height = +(args.height || 1080);
const out = args.out || file.replace(/\.html?$/, '.json');

const { chromium } = await import('playwright');

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width, height } });
const page = await ctx.newPage();
await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);

const slides = await page.$$eval(sel, (nodes) => {
  function rgbToHex(rgb) {
    const m = rgb.match(/\d+/g);
    if (!m) return null;
    return '#' + m.slice(0, 3).map(n => (+n).toString(16).padStart(2, '0')).join('');
  }
  function visible(el) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }
  // Берём только листья: у элемента-обёртки текст тот же, что у детей,
  // и без этой проверки один заголовок попал бы в PPTX несколько раз.
  function isTextLeaf(el) {
    if (!el.childNodes.length) return false;
    return [...el.childNodes].every(n =>
      n.nodeType === Node.TEXT_NODE ||
      (n.nodeType === Node.ELEMENT_NODE && ['B', 'I', 'EM', 'STRONG', 'SPAN', 'BR', 'A'].includes(n.tagName))
    );
  }

  return nodes.map(slide => {
    const sr = slide.getBoundingClientRect();
    const items = [];

    // Тексты
    slide.querySelectorAll('*').forEach(el => {
      if (!visible(el)) return;
      if (!el.textContent || !el.textContent.trim()) return;
      if (!isTextLeaf(el)) return;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      items.push({
        kind: 'text',
        x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
        text: el.innerText,
        fontFamily: cs.fontFamily.split(',')[0].replace(/"/g, '').trim(),
        fontSize: parseFloat(cs.fontSize),
        fontWeight: cs.fontWeight,
        italic: cs.fontStyle === 'italic',
        color: rgbToHex(cs.color),
        align: cs.textAlign,
        lineHeight: cs.lineHeight,
        letterSpacing: cs.letterSpacing,
      });
    });

    // Картинки
    slide.querySelectorAll('img').forEach(el => {
      if (!visible(el)) return;
      const r = el.getBoundingClientRect();
      items.push({
        kind: 'image',
        x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
        src: el.currentSrc || el.src,
      });
    });

    // Прямоугольники с фоном (карточки, плашки)
    slide.querySelectorAll('div, section, article, header, footer').forEach(el => {
      if (!visible(el)) return;
      const cs = getComputedStyle(el);
      const bg = cs.backgroundColor;
      if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') return;
      const r = el.getBoundingClientRect();
      items.push({
        kind: 'rect',
        x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height,
        fill: rgbToHex(bg),
        radius: parseFloat(cs.borderRadius),
        z: -1,
      });
    });

    // z: -1 у плашек — чтобы фон лёг ПОД текст. PPTX рисует в порядке добавления,
    // сортировка здесь и есть весь z-index, которым мы располагаем.
    const sCs = getComputedStyle(slide);
    return {
      width: sr.width, height: sr.height,
      bg: rgbToHex(sCs.backgroundColor),
      items: items.sort((a, b) => (a.z || 0) - (b.z || 0)),
    };
  });
});

await browser.close();

if (!slides.length) {
  console.error(`✗ селектор "${sel}" не нашёл ни одного слайда — проверь --slide-selector`);
  process.exit(2);
}

await fs.writeFile(out, JSON.stringify({ width, height, slides }, null, 2));
console.log('✓', out, '—', slides.length, 'слайдов');
