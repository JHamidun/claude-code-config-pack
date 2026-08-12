#!/usr/bin/env node
import readline from 'node:readline/promises';
import fs from 'node:fs/promises';
import path from 'node:path';

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

console.log('\n  claude-design-init\n');

const KIND = await ask('Что делаем?\n  [1] Лендинг\n  [2] Слайды (дек)\n  [3] Прототип (мобильный)\n  [4] Прототип (десктоп)\n  [5] Анимация\n  [6] Дизайн-система\n  [7] Wireframes\n', '1', /^[1-7]$/);
const NAME = await ask('\nНазвание проекта (slug, kebab-case): ', 'my-design');
const THEME = KIND === '2' ? await ask('Тема дека: minimal / editorial / dark / data / brutalist [minimal]: ', 'minimal') : null;
const TWEAKS = await ask('\nДобавить tweaks-panel? (y/n) [y]: ', 'y') === 'y';

rl.close();

const root = path.resolve(NAME);
await fs.mkdir(root, { recursive: true });
process.chdir(root);

await write('README.md', `# ${NAME}\n\nClaude-собранный ${kindName(KIND)}.\n\n## Запуск\n\n\`\`\`bash\nopen index.html\n\`\`\`\n`);
await write('CLAUDE.md', defaultClaudeMd(KIND));

if (KIND === '1') await scaffoldLanding();
if (KIND === '2') await scaffoldDeck(THEME);
if (KIND === '3') await scaffoldPrototype('ios');
if (KIND === '4') await scaffoldPrototype('desktop');
if (KIND === '5') await scaffoldAnimation();
if (KIND === '6') await scaffoldDesignSystem();
if (KIND === '7') await scaffoldWireframes();

if (TWEAKS && ['1','3','4'].includes(KIND)) await injectTweaks();

console.log(`\n✓ Готово: ${root}`);
console.log(`  cd ${NAME} && open index.html`);

// ----- helpers -----
async function ask(q, def, re) {
  const a = (await rl.question(q + (def?` [${def}]: `:''))).trim() || def;
  if (re && !re.test(a)) { console.log('Неверный ответ.'); return ask(q, def, re); }
  return a;
}
async function write(p, content) {
  await fs.mkdir(path.dirname(p), { recursive: true });
  await fs.writeFile(p, content);
}
function kindName(k) { return ['','лендинг','дек','мобильный прототип','десктоп прототип','анимация','дизайн-система','wireframes'][+k]; }

async function scaffoldLanding() { /* пишет index.html, style.css, минимальный hero+features+cta */ }
async function scaffoldDeck(theme) { /* копирует deck-stage.js + theme-${theme}.css + 5 пустых section */ }
async function scaffoldPrototype(kind) { /* копирует ${kind}_frame + 3 связанных экрана */ }
async function scaffoldAnimation() { /* копирует animations.jsx + Stage с одним Sprite */ }
async function scaffoldDesignSystem() { /* tokens.css + components/ + examples/ */ }
async function scaffoldWireframes() { /* wireframe-grid.html с 4 пустыми вариантами */ }
async function injectTweaks() { /* добавляет tweaks-panel.jsx и подключение */ }

function defaultClaudeMd(kind) {
  return `# CLAUDE.md\n\nЭто ${kindName(kind)}-проект, собранный init-wizard'ом.\n\n## Правила\n- Отвечай по-русски.\n- Перед большими задачами — один раунд уточнений.\n- Используй tokens.css; не вставляй цвета inline.\n\n## Скиллы для этого проекта\n${recommendedSkills(kind).map(s => '- ' + s).join('\n')}\n`;
}
function recommendedSkills(k) {
  const base = ['frontend-design', 'content-rules', 'verifier'];
  const extra = {
    '1': ['design-system-create', 'a11y-audit', 'perf-audit'],
    '2': ['slides', 'deck-themes', 'export-pptx', 'export-pdf'],
    '3': ['interactive-prototype', 'device-frames', 'mobile-overlays', 'tweaks-panel'],
    '4': ['interactive-prototype', 'tweaks-panel'],
    '5': ['animations', 'video-export'],
    '6': ['design-system-create', 'component-playground', 'color-system-builder', 'type-scale'],
    '7': ['wireframe', 'questions-protocol'],
  }[k] || [];
  return [...base, ...extra];
}
