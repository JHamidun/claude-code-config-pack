/**
 * llm-runner.js — generic codex/claude wrapper for book-post pipeline
 *
 * Wraps two CLIs: `codex` (ChatGPT subscription) and `claude` (Claude subscription).
 * Neither needs an API key — both authenticate through their own CLI login.
 *
 * Usage from other scripts:
 *   import { dispatch, callCodex, callClaude, isCodexQuotaError } from './llm-runner.js';
 *   const { text, elapsed, provider } = await dispatch({ prompt, prefer: 'codex' });
 *
 * CRITICAL nuances (learned from news-orchestrator):
 *   - --output-last-message → file (codex стрим в stdout теряется)
 *   - Уникальный outFile на каждый вызов (concurrent workers перезатрут общий)
 *   - windowsHide: true (иначе cmd-окна на каждый spawn на Windows)
 *   - --skip-git-repo-check (codex без git context)
 *   - timeout 360s+ (codex медленный на больших промптах для voice/proofread)
 *   - Fallback на claude при quota — ловится через result.status !== 0 + error string
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';

// ============ CONFIG ============
export const CLAUDE_CLI = process.env.CLAUDE_CLI || 'claude';
export const CODEX_CLI = process.env.CODEX_CLI || 'codex';
export const CODEX_MODEL = process.env.CODEX_MODEL || 'gpt-5.6';
// For book tasks default to opus (deep reasoning on long prose); override via env
export const CLAUDE_MODEL = process.env.CLAUDE_MODEL || 'opus';

// Once tripped, skip codex for the rest of this process
let codexDisabled = false;

export function isCodexDisabled() { return codexDisabled; }

export function isCodexQuotaError(msg) {
  const s = String(msg || '');
  return (
    s.includes('usage limit') ||
    s.includes('Invalid refresh token') ||
    s.includes('TokenRefreshFailed') ||
    s.includes("You've hit") ||
    s.includes("You’ve hit") ||
    s.includes('invalid_grant') ||
    s.includes('purchase more credits') ||
    s.includes('rate_limit')
  );
}

// ============ LOW-LEVEL ASYNC SPAWN ============
function spawnAsync(cmd, { input, timeoutMs = 360000, maxBufferMB = 50 } = {}) {
  return new Promise((resolve) => {
    const child = spawn(cmd, { shell: true, windowsHide: true });
    let stdout = '';
    let stderr = '';
    let resolved = false;
    const max = maxBufferMB * 1024 * 1024;
    const timer = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        try { child.kill('SIGKILL'); } catch {}
        resolve({ status: null, stdout, stderr: stderr + `\n[timeout ${timeoutMs}ms]`, error: 'ETIMEDOUT' });
      }
    }, timeoutMs);
    child.stdout.on('data', (d) => {
      stdout += d.toString();
      if (stdout.length > max) stdout = stdout.slice(-max);
    });
    child.stderr.on('data', (d) => {
      stderr += d.toString();
      if (stderr.length > max) stderr = stderr.slice(-max);
    });
    child.on('error', (err) => {
      if (!resolved) {
        resolved = true;
        clearTimeout(timer);
        resolve({ status: null, stdout, stderr, error: err.message });
      }
    });
    child.on('close', (code) => {
      if (!resolved) {
        resolved = true;
        clearTimeout(timer);
        resolve({ status: code, stdout, stderr, error: null });
      }
    });
    if (input != null) {
      try { child.stdin.write(input); child.stdin.end(); }
      catch (e) { /* surfaced via error handler */ }
    } else {
      child.stdin.end();
    }
  });
}

// ============ CLAUDE WRAPPER ============
export async function callClaude(prompt, { model = CLAUDE_MODEL, timeoutMs = 360000 } = {}) {
  const start = Date.now();
  const cmd = `${CLAUDE_CLI} -p --model ${model} --output-format json`;
  const result = await spawnAsync(cmd, { input: prompt, timeoutMs });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  if (result.status !== 0) {
    const err = (result.stderr?.slice(0, 400) || result.error || 'unknown').toString();
    throw new Error(`claude -p fail (status=${result.status}, ${elapsed}s): ${err}`);
  }
  try {
    const json = JSON.parse(result.stdout);
    return { text: json.result || json.response || json.content || '', elapsed, provider: 'claude' };
  } catch {
    return { text: result.stdout, elapsed, provider: 'claude' };
  }
}

// ============ CODEX WRAPPER ============
// ChatGPT subscription via OAuth (`codex login` once)
export async function callCodex(prompt, { model = CODEX_MODEL, timeoutMs = 360000 } = {}) {
  const start = Date.now();
  const outFile = path.join(
    os.tmpdir(),
    `codex-out-${process.pid}-${start}-${Math.random().toString(36).slice(2, 8)}.txt`
  );
  try {
    const cmd = `${CODEX_CLI} exec --model ${model} --skip-git-repo-check --output-last-message ${outFile} -`;
    const result = await spawnAsync(cmd, { input: prompt, timeoutMs });
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    if (result.status !== 0) {
      const stderrFull = (result.stderr || '').toString();
      const stdoutFull = (result.stdout || '').toString();
      const err = (stderrFull + '\n' + stdoutFull).slice(0, 800) || result.error || 'unknown';
      const e = new Error(`codex exec fail (status=${result.status}, ${elapsed}s): ${err}`);
      e.stderr = stderrFull;
      e.stdout = stdoutFull;
      throw e;
    }
    const text = fs.existsSync(outFile) ? fs.readFileSync(outFile, 'utf-8') : '';
    return { text, elapsed, provider: 'codex' };
  } finally {
    try { if (fs.existsSync(outFile)) fs.unlinkSync(outFile); } catch {}
  }
}

// ============ DISPATCH ============
// dispatch({ prompt, prefer: 'codex' | 'claude', timeoutMs, claudeModel, codexModel })
// codex → tries codex, falls back to claude on quota / failure (UNLESS BOOK_NO_CLAUDE=1)
// claude → always claude (UNLESS BOOK_NO_CLAUDE=1, then throws)
// auto → codex if available, else claude
//
// Env:
//   BOOK_NO_CLAUDE=1    — никогда не использовать claude (даже в fallback). Если codex
//                         упал — пробрасываем ошибку наверх. Полезно когда мы намеренно
//                         бережём claude-лимит на финальную литературную полировку.
export async function dispatch({ prompt, prefer = 'codex', timeoutMs = 360000, claudeModel, codexModel } = {}) {
  const noClaude = process.env.BOOK_NO_CLAUDE === '1' || process.env.BOOK_NO_CLAUDE === 'true';
  const wantCodex = prefer === 'codex' || prefer === 'auto';
  if (wantCodex && !codexDisabled) {
    try {
      return await callCodex(prompt, { timeoutMs, model: codexModel });
    } catch (e) {
      const msg = String(e.message || '') + ' ' + String(e.stderr || '');
      if (isCodexQuotaError(msg)) {
        if (!codexDisabled) {
          console.log(`[llm-runner] Codex quota exhausted — ${noClaude ? 'BOOK_NO_CLAUDE=1, throwing (no fallback)' : 'falling back to Claude'}`);
          codexDisabled = true;
        }
        if (noClaude) throw e;
      } else if (noClaude) {
        console.log(`[llm-runner] Codex error (${e.message.slice(0, 200)}) — BOOK_NO_CLAUDE=1, no fallback, throwing`);
        throw e;
      } else {
        console.log(`[llm-runner] Codex error (${e.message.slice(0, 200)}) — falling back to Claude for this call`);
      }
    }
  }
  if (noClaude && prefer === 'claude') {
    throw new Error('BOOK_NO_CLAUDE=1 set, but prefer=claude was passed — refusing to call Claude');
  }
  if (noClaude) {
    throw new Error('BOOK_NO_CLAUDE=1 set and codex unavailable — no fallback path');
  }
  return callClaude(prompt, { timeoutMs, model: claudeModel });
}

// Convenience: log timestamp prefix
export function ts() { return new Date().toISOString().replace('T', ' ').slice(0, 19); }
export function log(...args) { console.log(`[${ts()}]`, ...args); }
export function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }
