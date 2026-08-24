#!/usr/bin/env node
/**
 * comment.mjs — запостить комментарий в Figma-файл через REST API.
 *
 * Usage:
 *   FIGMA_ACCESS_TOKEN=figd_... node comment.mjs <fileKey> "<text>" [nodeId]
 *
 * fileKey — из URL: figma.com/design/<FILE_KEY>/Name
 * nodeId  — опционально, чтобы прикрепить комментарий к конкретному фрейму: "1:23"
 *           (в URL он пишется через дефис — node-id=1-23, в API через двоеточие)
 *
 * Токен: свой личный, https://www.figma.com/settings -> Personal access tokens.
 * Нужен скоуп file_comments:write. Бесплатного аккаунта достаточно.
 */

// Принимаем оба имени: FIGMA_ACCESS_TOKEN — канон этого навыка,
// FIGMA_TOKEN — то, что чаще уже стоит в окружении у тех, кто работал с Figma раньше.
const TOKEN = process.env.FIGMA_ACCESS_TOKEN || process.env.FIGMA_TOKEN;
const FILE = process.argv[2];
const TEXT = process.argv[3] || 'Update from HTML';
const NODE = process.argv[4];

if (!TOKEN) {
  console.error('Нужен FIGMA_ACCESS_TOKEN в окружении.');
  console.error('Взять: https://www.figma.com/settings -> Personal access tokens');
  process.exit(1);
}
if (!FILE) {
  console.error('Usage: FIGMA_ACCESS_TOKEN=... node comment.mjs <fileKey> "<text>" [nodeId]');
  process.exit(1);
}

const body = { message: TEXT };
if (NODE) {
  body.client_meta = { node_id: NODE, node_offset: { x: 0, y: 0 } };
}

const res = await fetch(`https://api.figma.com/v1/files/${FILE}/comments`, {
  method: 'POST',
  headers: {
    'X-Figma-Token': TOKEN,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(body),
});

const data = await res.json();
if (!res.ok) {
  console.error('✗ Figma ответила', res.status, JSON.stringify(data));
  if (res.status === 403) console.error('  403 — токен просрочен или без скоупа file_comments:write');
  process.exit(1);
}
console.log('✓ Posted:', data.message);
