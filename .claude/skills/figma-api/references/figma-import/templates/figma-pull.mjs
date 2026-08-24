#!/usr/bin/env node
/**
 * figma-pull.mjs
 *
 * Тянет структуру Figma-файла, превью фреймов и стили.
 * Использование:
 *   FIGMA_TOKEN=... node figma-pull.mjs "https://www.figma.com/design/KEY/...?node-id=10-20"
 *
 * Создаёт ./figma-refs/ с:
 *   - frames/*.png — превью верхнеуровневых фреймов
 *   - tokens.json — извлечённые цвета и текстовые стили
 *   - tokens.css  — те же токены как CSS-переменные
 *   - structure.md — карта файла
 */

import fs from 'node:fs/promises';
import path from 'node:path';

// Оба имени: FIGMA_ACCESS_TOKEN — канон навыка figma-api, FIGMA_TOKEN — частое legacy.
const TOKEN = process.env.FIGMA_ACCESS_TOKEN
  || process.env.FIGMA_TOKEN
  || (await fs.readFile(`${process.env.HOME || process.env.USERPROFILE}/.figma-token`, 'utf8').catch(() => '')).trim();

if (!TOKEN) {
  console.error('Нужен FIGMA_ACCESS_TOKEN в env (или ~/.figma-token).');
  console.error('Взять: https://www.figma.com/settings -> Personal access tokens');
  process.exit(1);
}

const url = process.argv[2];
if (!url) {
  console.error('Передай URL Figma-файла или фрейма');
  process.exit(1);
}

const { fileKey, nodeId } = parseUrl(url);
const OUT = 'figma-refs';
await fs.mkdir(`${OUT}/frames`, { recursive: true });

const headers = { 'X-Figma-Token': TOKEN };
const api = (p) => fetch(`https://api.figma.com/v1${p}`, { headers }).then(r => r.json());

console.log('→ Получаю структуру файла…');
const file = await api(`/files/${fileKey}?depth=3${nodeId ? `&ids=${nodeId}` : ''}`);

const frames = collectFrames(file.document, nodeId);
console.log(`Найдено ${frames.length} фреймов`);

if (frames.length) {
  console.log('→ Получаю превью…');
  const ids = frames.map(f => f.id).join(',');
  const images = await api(`/images/${fileKey}?ids=${ids}&format=png&scale=2`);
  for (const f of frames) {
    const u = images.images?.[f.id];
    if (!u) continue;
    const buf = Buffer.from(await (await fetch(u)).arrayBuffer());
    const safe = f.name.replace(/[^\w\d-]+/g, '-').slice(0, 60);
    await fs.writeFile(`${OUT}/frames/${safe}.png`, buf);
    console.log(`  ✓ ${safe}.png`);
  }
}

console.log('→ Получаю стили…');
const styles = await api(`/files/${fileKey}/styles`);
const styleIds = (styles.meta?.styles || []).map(s => s.node_id).join(',');
const tokens = { colors: {}, text: {} };

if (styleIds) {
  const nodes = await api(`/files/${fileKey}/nodes?ids=${styleIds}`);
  for (const s of styles.meta.styles) {
    const n = nodes.nodes?.[s.node_id]?.document;
    if (!n) continue;
    if (s.style_type === 'FILL') {
      const fill = n.fills?.[0];
      if (fill?.type === 'SOLID') tokens.colors[s.name] = rgbaToCss(fill.color, fill.opacity);
    } else if (s.style_type === 'TEXT') {
      tokens.text[s.name] = {
        fontFamily: n.style?.fontFamily,
        fontSize: n.style?.fontSize,
        fontWeight: n.style?.fontWeight,
        lineHeight: n.style?.lineHeightPx,
        letterSpacing: n.style?.letterSpacing,
      };
    }
  }
}

await fs.writeFile(`${OUT}/tokens.json`, JSON.stringify(tokens, null, 2));
await fs.writeFile(`${OUT}/tokens.css`, tokensToCss(tokens));
await fs.writeFile(`${OUT}/structure.md`, buildStructureMd(file.document));
console.log(`✓ Готово. Смотри ${OUT}/`);

// ---------- helpers ----------

function parseUrl(input) {
  const u = new URL(input);
  const m = u.pathname.match(/\/(file|design|proto)\/([A-Za-z0-9]+)/);
  if (!m) throw new Error('Не похоже на Figma URL');
  return {
    fileKey: m[2],
    nodeId: u.searchParams.get('node-id')?.replace(/-/g, ':') || null,
  };
}

function collectFrames(node, rootId, acc = []) {
  if (!node) return acc;
  if (node.type === 'FRAME' || node.type === 'COMPONENT' || node.type === 'COMPONENT_SET') {
    acc.push({ id: node.id, name: node.name });
    return acc;
  }
  for (const c of node.children || []) collectFrames(c, rootId, acc);
  return acc;
}

function rgbaToCss({ r, g, b }, a = 1) {
  const n = (x) => Math.round(x * 255);
  return a >= 1 ? `rgb(${n(r)}, ${n(g)}, ${n(b)})` : `rgba(${n(r)}, ${n(g)}, ${n(b)}, ${a})`;
}

function tokensToCss(t) {
  const lines = [':root {'];
  for (const [name, val] of Object.entries(t.colors)) {
    lines.push(`  --color-${slug(name)}: ${val};`);
  }
  lines.push('}');
  for (const [name, s] of Object.entries(t.text)) {
    lines.push(`.text-${slug(name)} {`);
    if (s.fontFamily)    lines.push(`  font-family: "${s.fontFamily}", sans-serif;`);
    if (s.fontSize)      lines.push(`  font-size: ${s.fontSize}px;`);
    if (s.fontWeight)    lines.push(`  font-weight: ${s.fontWeight};`);
    if (s.lineHeight)    lines.push(`  line-height: ${s.lineHeight}px;`);
    if (s.letterSpacing) lines.push(`  letter-spacing: ${s.letterSpacing}px;`);
    lines.push('}');
  }
  return lines.join('\n');
}

function slug(s) {
  return String(s).toLowerCase().replace(/[^\w\d]+/g, '-').replace(/(^-|-$)/g, '');
}

function buildStructureMd(doc, depth = 0, lines = ['# Figma file structure', '']) {
  if (!doc) return lines.join('\n');
  const pad = '  '.repeat(depth);
  const tag = doc.type === 'CANVAS' ? '📄' : doc.type === 'FRAME' ? '🖼' : '·';
  lines.push(`${pad}- ${tag} **${doc.name}** \`${doc.type}\` ${doc.id ? `(\`${doc.id}\`)` : ''}`);
  for (const c of doc.children || []) {
    if (depth < 3) buildStructureMd(c, depth + 1, lines);
  }
  return lines.join('\n');
}
