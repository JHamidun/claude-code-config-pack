#!/usr/bin/env node
/**
 * voice-pass.js — apply voice-keeper to one chapter DRAFT.md via codex (default) or claude
 *
 * Usage:
 *   node voice-pass.js --chapter 01-first-chapter
 *   node voice-pass.js --chapter 02-second-chapter --provider claude
 *   node voice-pass.js --chapter i1-interlude --dry-run
 *
 * Output: writes DRAFT.voice-pass.md alongside DRAFT.md (does NOT overwrite).
 *         Also writes EDIT-NOTES section that codex/claude generated.
 *
 * Single chapter at a time. For batch use voice-loop.sh.
 *
 * Code-side guarantees:
 *   - Read DRAFT.md, OUTLINE.md (for chapter title), STYLE_GUIDE.md,
 *     ~/.claude/voice-sample.md (author's voice) and ~/.claude/author-profile.md
 *   - Build prompt via prompts.js VOICE_KEEPER_PROMPT
 *   - Dispatch codex → claude fallback on quota
 *   - Write result to DRAFT.voice-pass.md (so original DRAFT.md остаётся для diff)
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';
import { dispatch, log } from './llm-runner.js';
import { VOICE_KEEPER_PROMPT } from './prompts.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============ ARGS ============
const args = process.argv.slice(2);
const arg = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const flag = (name) => args.includes(name);

const CHAPTER = arg('--chapter');
const PROVIDER = arg('--provider', 'codex'); // codex | claude
const DRY_RUN = flag('--dry-run');
const VOICE_CORPUS_LINES = parseInt(arg('--corpus-lines', '500'), 10);

if (!CHAPTER) {
  console.error('Usage: node voice-pass.js --chapter <slug> [--provider codex|claude] [--dry-run]');
  process.exit(1);
}

const BOOK_ROOT = process.env.BOOK_ROOT
  || path.join(os.homedir(), 'book');

const CHAPTER_DIR = path.join(BOOK_ROOT, 'chapters', CHAPTER);
const DRAFT_PATH = path.join(CHAPTER_DIR, 'DRAFT.md');
const OUT_PATH = path.join(CHAPTER_DIR, 'DRAFT.voice-pass.md');
const STYLE_GUIDE_PATH = path.join(BOOK_ROOT, 'STYLE_GUIDE.md');

// Голос автора и сведения о нём лежат в его конфиге, не в этом навыке.
// Шаблоны для заполнения — ~/.claude/templates/{voice-sample,author-profile}.md
const CLAUDE_HOME = process.env.CLAUDE_HOME || path.join(os.homedir(), '.claude');
const VOICE_SAMPLE_PATH = process.env.VOICE_SAMPLE || path.join(CLAUDE_HOME, 'voice-sample.md');
const AUTHOR_PROFILE_PATH = process.env.AUTHOR_PROFILE || path.join(CLAUDE_HOME, 'author-profile.md');
// Необязательно: папка с собственными опубликованными текстами (*.md) как доп. образцы
const EXTRA_SAMPLES_DIR = process.env.VOICE_SAMPLES_DIR || '';

function readIfExists(p) {
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf-8') : '';
}

// Voice corpus = голос автора (обязательно) + решения этой книги + свои опубликованные тексты
function loadVoiceCorpus() {
  const fragments = [];
  const sample = readIfExists(VOICE_SAMPLE_PATH);
  if (sample) {
    fragments.push('--- voice-sample.md (голос автора — источник истины) ---\n' + sample);
  } else {
    console.warn(`[voice-pass] WARNING: ${VOICE_SAMPLE_PATH} не найден.`);
    console.warn('[voice-pass] Без образцов голоса проход выдаст усреднённый «экспертный» текст.');
    console.warn('[voice-pass] Заполни его из ~/.claude/templates/voice-sample.md и запусти снова.');
  }
  const styleGuide = readIfExists(STYLE_GUIDE_PATH);
  if (styleGuide) {
    fragments.push('--- STYLE_GUIDE.md (решения по этой книге) ---\n' + styleGuide);
  }
  if (EXTRA_SAMPLES_DIR && fs.existsSync(EXTRA_SAMPLES_DIR)) {
    const files = fs.readdirSync(EXTRA_SAMPLES_DIR).filter((f) => f.endsWith('.md')).slice(0, 4);
    for (const f of files) {
      const lines = fs.readFileSync(path.join(EXTRA_SAMPLES_DIR, f), 'utf-8').split('\n');
      const excerpt = lines.slice(0, VOICE_CORPUS_LINES).join('\n');
      fragments.push(`--- ${f} (первые ${VOICE_CORPUS_LINES} строк) ---\n${excerpt}`);
    }
  }
  return fragments.join('\n\n');
}

function readChapterTitle() {
  const outlinePath = path.join(CHAPTER_DIR, 'OUTLINE.md');
  if (!fs.existsSync(outlinePath)) return CHAPTER;
  const text = fs.readFileSync(outlinePath, 'utf-8');
  const m = text.match(/^title:\s*"([^"]+)"/m) || text.match(/^title:\s*(.+)$/m);
  return m ? m[1].trim() : CHAPTER;
}

async function main() {
  if (!fs.existsSync(DRAFT_PATH)) {
    console.error(`DRAFT.md not found: ${DRAFT_PATH}`);
    process.exit(2);
  }
  const draft = fs.readFileSync(DRAFT_PATH, 'utf-8');
  const chapterTitle = readChapterTitle();
  const voiceCorpus = loadVoiceCorpus();

  log(`voice-pass start: chapter="${CHAPTER}" title="${chapterTitle}" provider=${PROVIDER}`);
  log(`  DRAFT length: ${draft.length} chars (~${Math.round(draft.split(/\s+/).length)} words)`);
  log(`  VOICE_CORPUS length: ${voiceCorpus.length} chars`);

  const authorProfile = readIfExists(AUTHOR_PROFILE_PATH);
  if (!authorProfile) {
    console.warn(`[voice-pass] WARNING: ${AUTHOR_PROFILE_PATH} не найден — промпт пойдёт без профиля автора.`);
  }
  const prompt = VOICE_KEEPER_PROMPT({ voiceCorpus, draft, chapterTitle, authorProfile });
  log(`  Prompt length: ${prompt.length} chars`);

  if (DRY_RUN) {
    const dumpPath = path.join(os.tmpdir(), `voice-pass-${CHAPTER}-prompt.txt`);
    fs.writeFileSync(dumpPath, prompt, 'utf-8');
    log(`[DRY-RUN] prompt dumped to ${dumpPath}`);
    return;
  }

  const start = Date.now();
  const result = await dispatch({ prompt, prefer: PROVIDER, timeoutMs: 600000 });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);

  if (!result.text || result.text.length < 500) {
    console.error(`Empty/short result (${result.text?.length || 0} chars) — likely quota or API error`);
    process.exit(3);
  }

  fs.writeFileSync(OUT_PATH, result.text, 'utf-8');
  log(`voice-pass done: ${result.provider} (${result.elapsed}s, total ${elapsed}s)`);
  log(`  Output: ${OUT_PATH} (${result.text.length} chars)`);
  log(`  Diff with original via:  diff "${DRAFT_PATH}" "${OUT_PATH}"`);
}

main().catch((e) => {
  console.error(`voice-pass FATAL: ${e.message}`);
  if (e.stderr) console.error(`  stderr: ${e.stderr.slice(0, 500)}`);
  process.exit(99);
});
