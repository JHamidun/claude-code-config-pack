#!/usr/bin/env node
/**
 * update-vars.mjs — обновить color-Variables в Figma из JSON с токенами.
 *
 * Usage:
 *   FIGMA_ACCESS_TOKEN=figd_... node update-vars.mjs <fileKey> <tokens.json> [--dry-run]
 *
 * Формат tokens.json (минимум):
 *   { "color": { "brand-500": "#3B5BFF", "surface": "#FFFFFF" } }
 * Ищутся переменные с именами `color/brand-500`, `color/surface` — то есть
 * префикс коллекции `color/` + ключ из JSON.
 *
 * ⚠ Variables Write API доступен НЕ на всех тарифах Figma (нужен Enterprise
 *   либо соответствующий свежий план). На бесплатном аккаунте вернётся 403 —
 *   это ограничение тарифа, а не ошибка скрипта.
 * ⚠ По умолчанию идёт --dry-run: печатает, что будет изменено, и ничего не пишет.
 *   Запись включается флагом --apply. Переменные Figma нельзя откатить кнопкой —
 *   дизайнер потеряет ручные правки молча.
 */
import fs from 'node:fs/promises';

const TOKEN = process.env.FIGMA_ACCESS_TOKEN || process.env.FIGMA_TOKEN;
const FILE = process.argv[2];
const TOKENS_PATH = process.argv[3];
const APPLY = process.argv.includes('--apply');

if (!TOKEN || !FILE || !TOKENS_PATH) {
  console.error('Usage: FIGMA_ACCESS_TOKEN=... node update-vars.mjs <fileKey> <tokens.json> [--apply]');
  console.error('Токен: https://www.figma.com/settings -> Personal access tokens (скоуп file_variables:write)');
  process.exit(1);
}

/** "#3B5BFF" | "#3B5BFFCC" -> { r, g, b, a } в диапазоне 0..1, как ждёт Figma */
function hexToRgba(hex) {
  const h = String(hex).trim().replace('#', '');
  const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
  if (!/^[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$/.test(full)) {
    throw new Error(`не похоже на hex-цвет: ${hex}`);
  }
  const n = (i) => parseInt(full.slice(i, i + 2), 16) / 255;
  return { r: n(0), g: n(2), b: n(4), a: full.length === 8 ? n(6) : 1 };
}

const tokens = JSON.parse(await fs.readFile(TOKENS_PATH, 'utf8'));
if (!tokens.color) {
  console.error(`В ${TOKENS_PATH} нет секции "color" — обновлять нечего.`);
  process.exit(1);
}

const headers = { 'X-Figma-Token': TOKEN };
const curRes = await fetch(`https://api.figma.com/v1/files/${FILE}/variables/local`, { headers });
const cur = await curRes.json();
if (!curRes.ok) {
  console.error('✗ Не удалось прочитать variables:', curRes.status, JSON.stringify(cur));
  if (curRes.status === 403) console.error('  403 — тариф без Variables API либо нет скоупа file_variables:write');
  process.exit(1);
}

const variables = Object.values(cur.meta?.variables || {});
const modes = Object.values(cur.meta?.variableCollections || {})[0]?.modes || [];
const modeId = modes[0]?.modeId;
if (!modeId) {
  console.error('✗ В файле нет ни одной коллекции переменных — создай её в Figma руками.');
  process.exit(1);
}

const updates = [];
const skipped = [];
for (const [name, value] of Object.entries(tokens.color)) {
  const existing = variables.find((v) => v.name === `color/${name}`);
  if (!existing) { skipped.push(name); continue; }
  updates.push({
    action: 'UPDATE',
    id: existing.id,
    valuesByMode: { [modeId]: hexToRgba(value) },
  });
  console.log(`  color/${name} -> ${value}`);
}

if (skipped.length) {
  console.log(`\n[skip] нет такой переменной в Figma: ${skipped.join(', ')}`);
  console.log('       переменные создаются в Figma руками — API их не заводит');
}
if (!updates.length) {
  console.log('\nНечего обновлять.');
  process.exit(0);
}

if (!APPLY) {
  console.log(`\n--dry-run: ${updates.length} переменных будет изменено. Запись — с флагом --apply.`);
  process.exit(0);
}

const res = await fetch(`https://api.figma.com/v1/files/${FILE}/variables`, {
  method: 'POST',
  headers: { ...headers, 'Content-Type': 'application/json' },
  body: JSON.stringify({ variables: updates }),
});
const data = await res.json();
if (!res.ok) {
  console.error('✗ Figma ответила', res.status, JSON.stringify(data));
  process.exit(1);
}
console.log(`✓ Обновлено переменных: ${updates.length}`);
