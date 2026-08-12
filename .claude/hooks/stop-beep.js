#!/usr/bin/env node
/*
 * stop-beep.js — короткий сигнал, когда Claude закончил ход.
 *
 * Раньше это была строка `powershell -c "[console]::beep(...)"` прямо в
 * settings.json. На macOS/Linux powershell нет, поэтому Stop-хук падал на КАЖДОМ
 * ответе — сигнала нет, зато есть ошибка. Здесь та же логика, но с проверкой
 * платформы: на Windows остаются те же два тона, на остальных — системный BEL.
 *
 * Глушилка (обе платформы): создать файл /tmp/claude-no-beep.
 * Общая killswitch хуков: CC_HOOKS_OFF=1.
 * Хук ВСЕГДА завершается 0 — сигнал не повод ломать ход.
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

function main() {
  if (process.env.CC_HOOKS_OFF === '1') return;

  // Исторический путь /tmp/... плюс его настоящий эквивалент на Windows,
  // где /tmp не существует и файл-глушилку создать было негде.
  const mutes = [
    '/tmp/claude-no-beep',
    path.join(os.tmpdir(), 'claude-no-beep'),
  ];
  if (mutes.some((p) => { try { return fs.existsSync(p); } catch { return false; } })) return;

  if (process.platform === 'win32') {
    const { spawnSync } = require('child_process');
    spawnSync(
      'powershell',
      ['-NoProfile', '-NonInteractive', '-Command', '[console]::beep(800,200); [console]::beep(1000,200)'],
      { stdio: 'ignore', timeout: 5000 }
    );
    return;
  }
  // macOS/Linux: BEL в stderr — терминал сам решает, звук это или вспышка.
  try { fs.writeSync(2, ''); } catch { /* терминала нет — и не надо */ }
}

try { main(); } catch { /* сигнал не повод ронять ход */ }
process.exit(0);
