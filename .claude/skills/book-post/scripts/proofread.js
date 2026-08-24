#!/usr/bin/env node
/**
 * proofread.js — corrector pass on one chapter (orthography + punctuation + typography)
 *
 * Usage:
 *   node proofread.js --chapter 01-first-chapter
 *   node proofread.js --chapter 02-second-chapter --input voice-pass --provider codex
 *
 * Input source:
 *   --input draft       (default — chapters/<slug>/DRAFT.md)
 *   --input voice-pass  (chapters/<slug>/DRAFT.voice-pass.md)
 *
 * Output: chapters/<slug>/DRAFT.proofread.md (does NOT overwrite source)
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { dispatch, log } from './llm-runner.js';
import { PROOFREADER_PROMPT } from './prompts.js';

const args = process.argv.slice(2);
const arg = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const flag = (name) => args.includes(name);

const CHAPTER = arg('--chapter');
const PROVIDER = arg('--provider', 'codex');
const INPUT = arg('--input', 'draft'); // draft | voice-pass
const DRY_RUN = flag('--dry-run');

if (!CHAPTER) {
  console.error('Usage: node proofread.js --chapter <slug> [--input draft|voice-pass] [--provider codex|claude]');
  process.exit(1);
}

const BOOK_ROOT = process.env.BOOK_ROOT
  || path.join(os.homedir(), 'book');
const CHAPTER_DIR = path.join(BOOK_ROOT, 'chapters', CHAPTER);

const SOURCE_FILE = INPUT === 'voice-pass'
  ? path.join(CHAPTER_DIR, 'DRAFT.voice-pass.md')
  : path.join(CHAPTER_DIR, 'DRAFT.md');
const OUT_PATH = path.join(CHAPTER_DIR, 'DRAFT.proofread.md');

function readChapterTitle() {
  const outlinePath = path.join(CHAPTER_DIR, 'OUTLINE.md');
  if (!fs.existsSync(outlinePath)) return CHAPTER;
  const text = fs.readFileSync(outlinePath, 'utf-8');
  const m = text.match(/^title:\s*"([^"]+)"/m) || text.match(/^title:\s*(.+)$/m);
  return m ? m[1].trim() : CHAPTER;
}

async function main() {
  if (!fs.existsSync(SOURCE_FILE)) {
    console.error(`Source not found: ${SOURCE_FILE}`);
    process.exit(2);
  }
  const draft = fs.readFileSync(SOURCE_FILE, 'utf-8');
  const chapterTitle = readChapterTitle();

  log(`proofread start: chapter="${CHAPTER}" input=${INPUT} provider=${PROVIDER}`);
  log(`  Source: ${SOURCE_FILE} (${draft.length} chars)`);

  const prompt = PROOFREADER_PROMPT({ draft, chapterTitle });

  if (DRY_RUN) {
    const dumpPath = path.join(os.tmpdir(), `proofread-${CHAPTER}-prompt.txt`);
    fs.writeFileSync(dumpPath, prompt, 'utf-8');
    log(`[DRY-RUN] prompt dumped to ${dumpPath}`);
    return;
  }

  const start = Date.now();
  const result = await dispatch({ prompt, prefer: PROVIDER, timeoutMs: 600000 });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);

  if (!result.text || result.text.length < 500) {
    console.error(`Empty/short result (${result.text?.length || 0} chars)`);
    process.exit(3);
  }

  fs.writeFileSync(OUT_PATH, result.text, 'utf-8');
  log(`proofread done: ${result.provider} (${result.elapsed}s, total ${elapsed}s)`);
  log(`  Output: ${OUT_PATH} (${result.text.length} chars)`);
  log(`  Diff via:  diff "${SOURCE_FILE}" "${OUT_PATH}"`);
}

main().catch((e) => {
  console.error(`proofread FATAL: ${e.message}`);
  if (e.stderr) console.error(`  stderr: ${e.stderr.slice(0, 500)}`);
  process.exit(99);
});
