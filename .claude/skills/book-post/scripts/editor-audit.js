#!/usr/bin/env node
/**
 * editor-audit.js — AUDIT-ONLY editor pass (no rewriting, just verdict)
 *
 * Usage:
 *   node editor-audit.js --chapter 01-first-chapter
 *   node editor-audit.js --chapter 02-second-chapter --provider codex
 *
 * Reads chapters/<slug>/DRAFT.proofread.md
 * Output: chapters/<slug>/EDITOR-NOTES.md  (verdict + checklist, no rewritten text)
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { dispatch, log } from './llm-runner.js';

const args = process.argv.slice(2);
const arg = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };

const CHAPTER = arg('--chapter');
const PROVIDER = arg('--provider', 'codex');
const INPUT = arg('--input', 'proofread');

if (!CHAPTER) {
  console.error('Usage: node editor-audit.js --chapter <slug> [--provider codex|claude]');
  process.exit(1);
}

const BOOK_ROOT = process.env.BOOK_ROOT
  || path.join(os.homedir(), 'book');
const CHAPTER_DIR = path.join(BOOK_ROOT, 'chapters', CHAPTER);

const SOURCE_FILE = INPUT === 'proofread'
  ? path.join(CHAPTER_DIR, 'DRAFT.proofread.md')
  : path.join(CHAPTER_DIR, 'DRAFT.md');
const OUT_PATH = path.join(CHAPTER_DIR, 'EDITOR-NOTES.md');

function readChapterTitle() {
  const outlinePath = path.join(CHAPTER_DIR, 'OUTLINE.md');
  if (!fs.existsSync(outlinePath)) return CHAPTER;
  const text = fs.readFileSync(outlinePath, 'utf-8');
  const m = text.match(/^title:\s*"([^"]+)"/m) || text.match(/^title:\s*(.+)$/m);
  return m ? m[1].trim() : CHAPTER;
}

const AUDIT_PROMPT = ({ draft, chapterTitle }) => `\
Ты редактор non-fiction книги. Это AUDIT-ONLY проход — ты НЕ переписываешь текст, только даёшь вердикт по структурно-литературному чек-листу.

ЧЕК-ЛИСТ (10 пунктов):
1. Заголовок главы — не маркетинговый, не вопросительный, отражает содержание
2. Заголовки разделов — соответствуют структуре «6 частей HBR-style» (Зачин / Разбор / Фреймворк / Применение / Side-block / Закрытие). Допустимы вариации формулировок, но логика должна быть видна.
3. В разделе «Фреймворк» есть один именованный принцип, выделенный жирным (например, **разрыв 70/70** или **принцип лестницы 2026**)
4. Один pull-quote (самая сильная фраза автора, может быть в виде >блок-цитаты или жирным выделением)
5. Side-block «Если вы не руководитель» присутствует (или эквивалентный side-block для другой целевой аудитории)
6. Закрытие — личное наблюдение или мост к следующей главе, НЕ «выводы»/«итак, мы рассмотрели»
7. Ритм абзацев — большинство 4-7 строк, без длинных «полотен» >12 строк подряд
8. Переходы между разделами — естественные, НЕ через «итак» / «во-первых, во-вторых» / «таким образом»
9. Цитаты внешних людей (исследователей, CEO, экспертов) — не более одной на спикера в главе
10. Упоминания собственного продукта/компании автора в теле главы — не более двух

================================================================
ИСХОДНЫЙ ТЕКСТ ГЛАВЫ «${chapterTitle}»:
================================================================

${draft}

================================================================
ЗАДАНИЕ:

Выдай отчёт строго в таком формате:

# EDITOR-AUDIT: ${chapterTitle}

## VERDICT: PASS / PASS-WITH-NOTES / NEEDS-EDIT

## CHECKLIST

| # | Пункт | Status | Комментарий |
|---|-------|--------|-------------|
| 1 | Заголовок главы | ✅/⚠️/❌ | <одно предложение> |
| 2 | Структура разделов HBR | ✅/⚠️/❌ | <одно предложение> |
| ... (все 10) |

## КРИТИЧЕСКИЕ НАХОДКИ

(только если есть NEEDS-EDIT items, иначе раздел пропускаем)

1. **Пункт N**: что именно не так, цитата из текста, рекомендация что поправить
2. ...

## РЕКОМЕНДАЦИИ (опционально)

Литературные/структурные улучшения, которые НЕ блокируют публикацию, но усилят главу:
- ...

## SUMMARY
Кратко: x/10 пунктов прошли, что блокирует публикацию (если что-то), общее впечатление от главы.

================================================================
ВАЖНО: НЕ ПЕРЕПИСЫВАЙ текст главы. Только вердикт + чек-лист + рекомендации.
`;

async function main() {
  if (!fs.existsSync(SOURCE_FILE)) {
    console.error(`Source not found: ${SOURCE_FILE}`);
    process.exit(2);
  }
  const draft = fs.readFileSync(SOURCE_FILE, 'utf-8');
  const chapterTitle = readChapterTitle();

  log(`editor-audit start: chapter="${CHAPTER}" input=${INPUT} provider=${PROVIDER}`);
  log(`  Source: ${SOURCE_FILE} (${draft.length} chars)`);

  const prompt = AUDIT_PROMPT({ draft, chapterTitle });

  const start = Date.now();
  const result = await dispatch({ prompt, prefer: PROVIDER, timeoutMs: 600000 });
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);

  if (!result.text || result.text.length < 200) {
    console.error(`Empty/short result (${result.text?.length || 0} chars)`);
    process.exit(3);
  }

  fs.writeFileSync(OUT_PATH, result.text, 'utf-8');
  log(`editor-audit done: ${result.provider} (${result.elapsed}s, total ${elapsed}s)`);
  log(`  Output: ${OUT_PATH} (${result.text.length} chars)`);
}

main().catch((e) => {
  console.error(`editor-audit FATAL: ${e.message}`);
  if (e.stderr) console.error(`  stderr: ${e.stderr.slice(0, 500)}`);
  process.exit(99);
});
