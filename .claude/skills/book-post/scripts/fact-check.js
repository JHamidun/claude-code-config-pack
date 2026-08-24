#!/usr/bin/env node
/**
 * fact-check.js — verify chapter against SOURCES.md + MATERIALS.md via codex/claude
 *
 * Usage:
 *   node fact-check.js --chapter 01-first-chapter
 *   node fact-check.js --chapter 02-second-chapter --input proofread --provider claude
 *
 * Input source:
 *   --input draft       (chapters/<slug>/DRAFT.md)
 *   --input voice-pass  (chapters/<slug>/DRAFT.voice-pass.md)
 *   --input proofread   (chapters/<slug>/DRAFT.proofread.md)
 *
 * Output: chapters/<slug>/FACT-REPORT.md
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { dispatch, log } from './llm-runner.js';
import { FACT_CHECKER_PROMPT } from './prompts.js';

const args = process.argv.slice(2);
const arg = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const flag = (name) => args.includes(name);

const CHAPTER = arg('--chapter');
const PROVIDER = arg('--provider', 'codex');
const INPUT = arg('--input', 'draft');
const DRY_RUN = flag('--dry-run');

if (!CHAPTER) {
  console.error('Usage: node fact-check.js --chapter <slug> [--input draft|voice-pass|proofread] [--provider codex|claude]');
  process.exit(1);
}

const BOOK_ROOT = process.env.BOOK_ROOT
  || path.join(os.homedir(), 'book');
const CHAPTER_DIR = path.join(BOOK_ROOT, 'chapters', CHAPTER);

const SOURCE_MAP = {
  draft: path.join(CHAPTER_DIR, 'DRAFT.md'),
  'voice-pass': path.join(CHAPTER_DIR, 'DRAFT.voice-pass.md'),
  proofread: path.join(CHAPTER_DIR, 'DRAFT.proofread.md'),
};
const SOURCE_FILE = SOURCE_MAP[INPUT];
const SOURCES_FILE = path.join(CHAPTER_DIR, 'SOURCES.md');
const MATERIALS_FILE = path.join(CHAPTER_DIR, 'MATERIALS.md');
const OUT_PATH = path.join(CHAPTER_DIR, 'FACT-REPORT.md');

function readChapterTitle() {
  const outlinePath = path.join(CHAPTER_DIR, 'OUTLINE.md');
  if (!fs.existsSync(outlinePath)) return CHAPTER;
  const text = fs.readFileSync(outlinePath, 'utf-8');
  const m = text.match(/^title:\s*"([^"]+)"/m) || text.match(/^title:\s*(.+)$/m);
  return m ? m[1].trim() : CHAPTER;
}

async function main() {
  if (!SOURCE_FILE || !fs.existsSync(SOURCE_FILE)) {
    console.error(`Source not found: ${SOURCE_FILE}`);
    process.exit(2);
  }
  if (!fs.existsSync(SOURCES_FILE) || !fs.existsSync(MATERIALS_FILE)) {
    console.error('SOURCES.md and/or MATERIALS.md missing');
    process.exit(2);
  }
  const draft = fs.readFileSync(SOURCE_FILE, 'utf-8');
  const sources = fs.readFileSync(SOURCES_FILE, 'utf-8');
  const materials = fs.readFileSync(MATERIALS_FILE, 'utf-8');
  const chapterTitle = readChapterTitle();

  log(`fact-check start: chapter="${CHAPTER}" input=${INPUT} provider=${PROVIDER}`);
  log(`  Draft: ${draft.length} chars, Sources: ${sources.length}, Materials: ${materials.length}`);

  const prompt = FACT_CHECKER_PROMPT({ draft, sources, materials, chapterTitle });

  if (DRY_RUN) {
    const dumpPath = path.join(os.tmpdir(), `fact-check-${CHAPTER}-prompt.txt`);
    fs.writeFileSync(dumpPath, prompt, 'utf-8');
    log(`[DRY-RUN] prompt dumped to ${dumpPath}`);
    return;
  }

  const start = Date.now();
  const result = await dispatch({ prompt, prefer: PROVIDER, timeoutMs: 600000 });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);

  if (!result.text || result.text.length < 200) {
    console.error(`Empty/short result (${result.text?.length || 0} chars)`);
    process.exit(3);
  }

  // Wrap result with metadata header
  const header = `# FACT-REPORT — ${chapterTitle}\n\n` +
    `Generated: ${new Date().toISOString()}\n` +
    `Provider: ${result.provider} (${result.elapsed}s)\n` +
    `Source: ${path.basename(SOURCE_FILE)}\n\n` +
    `---\n\n`;
  fs.writeFileSync(OUT_PATH, header + result.text, 'utf-8');
  log(`fact-check done: ${result.provider} (${result.elapsed}s, total ${elapsed}s)`);
  log(`  Report: ${OUT_PATH} (${result.text.length} chars)`);
}

main().catch((e) => {
  console.error(`fact-check FATAL: ${e.message}`);
  if (e.stderr) console.error(`  stderr: ${e.stderr.slice(0, 500)}`);
  process.exit(99);
});
