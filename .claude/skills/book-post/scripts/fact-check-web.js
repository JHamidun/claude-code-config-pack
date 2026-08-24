#!/usr/bin/env node
/**
 * fact-check-web.js — verify chapter SOURCES against LIVE web content
 *
 * Архитектура (важно — отличается от ai-news-bot):
 *   В книге URL'ы НЕ встречаются в DRAFT'е (книжный стиль без гиперссылок).
 *   URL'ы и связанные с ними claims живут в SOURCES.md глав.
 *
 *   Поэтому fact-check-web парсит SOURCES.md, извлекает (URL, claim_снизу),
 *   fetch'ит каждый URL, LLM сравнивает заявленный claim с реальной страницей.
 *
 *   Результат показывает: какие источники реальные, какие умерли, какие drift'ят.
 *
 * Usage:
 *   node fact-check-web.js --chapter 01-first-chapter
 *   node fact-check-web.js --chapter 02-second-chapter --skip-llm  # только URL alive
 *   node fact-check-web.js --chapter i1-interlude --provider claude
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { dispatch, log } from './llm-runner.js';

const args = process.argv.slice(2);
const arg = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const flag = (name) => args.includes(name);

const CHAPTER = arg('--chapter');
const PROVIDER = arg('--provider', 'codex');
const SKIP_LLM = flag('--skip-llm');
const CONCURRENCY = parseInt(arg('--concurrency', '3'), 10);
const FETCH_TIMEOUT_MS = parseInt(arg('--fetch-timeout', '30000'), 10);
const MAX_CONTENT_KB = parseInt(arg('--max-content-kb', '40'), 10);

if (!CHAPTER) {
  console.error('Usage: node fact-check-web.js --chapter <slug> [--provider codex|claude] [--skip-llm]');
  process.exit(1);
}

const BOOK_ROOT = process.env.BOOK_ROOT
  || path.join(os.homedir(), 'book');
const CHAPTER_DIR = path.join(BOOK_ROOT, 'chapters', CHAPTER);
const SOURCES_FILE = path.join(CHAPTER_DIR, 'SOURCES.md');
const OUT_PATH = path.join(CHAPTER_DIR, 'WEB-FACT-REPORT.md');

// ============ PARSE SOURCES.md ============
// Each entry roughly looks like:
// - **Title** — Author, Year. DOI: ... \n   [URL]\n   **Что важно:** ... \n  **Какой тезис...** ...
// We split by leading "- **" markers and extract URL + the surrounding ~10 lines as claim.
function parseSourcesMd(text) {
  const entries = [];
  // Split into entry blocks by lines that start with "- **" (markdown list with bold title)
  const lines = text.split('\n');
  let cur = null;
  for (const ln of lines) {
    if (/^[-*]\s+\*\*/.test(ln)) {
      if (cur) entries.push(cur);
      cur = { lines: [ln] };
    } else if (cur) {
      cur.lines.push(ln);
    }
  }
  if (cur) entries.push(cur);

  const result = [];
  for (const e of entries) {
    const block = e.lines.join('\n');
    // Skip section headers / sub-bullets that are not source entries
    // Real entries usually have a URL line `[https://...]` or `[URL](https://...)`
    const urlMatches = [];
    const urlRe1 = /\[(https?:\/\/[^\]\s]+)\]/g; // [https://...]
    const urlRe2 = /\]\((https?:\/\/[^)\s]+)\)/g; // [text](https://...)
    const urlRe3 = /(?<![\(\[])(https?:\/\/[^\s)\]"]+)/g; // raw http(s)
    let m;
    while ((m = urlRe1.exec(block)) !== null) urlMatches.push(m[1]);
    while ((m = urlRe2.exec(block)) !== null) urlMatches.push(m[1]);
    while ((m = urlRe3.exec(block)) !== null) urlMatches.push(m[1]);
    const urls = Array.from(new Set(urlMatches.map((u) => u.replace(/[.,;:!?»"']+$/, ''))));
    if (urls.length === 0) continue;
    // Title (first **bold** in first line)
    const title = (block.match(/\*\*(.+?)\*\*/) || [, ''])[1].trim();
    // Cleaned claim: full block, normalized whitespace (~800-2000 chars usually)
    const claim = block.replace(/\s+/g, ' ').trim();
    for (const url of urls) {
      result.push({ url, title, claim });
    }
  }
  return result;
}

// ============ FETCH ============
async function fetchUrl(url) {
  const start = Date.now();
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), FETCH_TIMEOUT_MS);
    const res = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
      },
      redirect: 'follow',
      signal: ctrl.signal,
    });
    clearTimeout(t);
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    if (!res.ok) {
      // 403 / 429 / 503 = anti-bot блок (URL скорее всего жив, просто не пускает headless)
      const blocked = [401, 403, 429, 451, 503].includes(res.status);
      return {
        url,
        status: res.status,
        elapsed,
        dead: !blocked,        // DEAD только если реально 404/410/etc
        blocked,               // отдельный флаг
        content: null,
        finalUrl: res.url,
      };
    }
    const ct = res.headers.get('content-type') || '';
    if (!ct.match(/text\/html|text\/plain|application\/json|application\/xhtml/i)) {
      return { url, status: res.status, elapsed, dead: false, content: null, finalUrl: res.url, contentType: ct, binary: true };
    }
    let text = await res.text();
    text = text
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<style[\s\S]*?<\/style>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, ' ')
      .trim();
    if (text.length > MAX_CONTENT_KB * 1024) {
      text = text.slice(0, MAX_CONTENT_KB * 1024) + '... [truncated]';
    }
    return { url, status: res.status, elapsed, dead: false, content: text, finalUrl: res.url };
  } catch (e) {
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    const msg = e.message || '';
    // Timeout / connection reset / DNS — может быть anti-bot, не обязательно мёртвый
    const probablyBlocked = msg.includes('aborted') || msg.includes('ETIMEDOUT') || msg.includes('ECONNRESET');
    return {
      url,
      status: null,
      elapsed,
      dead: !probablyBlocked,
      blocked: probablyBlocked,
      content: null,
      error: msg.slice(0, 200),
    };
  }
}

async function fetchAll(items) {
  const results = [];
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const my = i++;
      const it = items[my];
      log(`  fetch [${my + 1}/${items.length}]: ${it.url}`);
      const r = await fetchUrl(it.url);
      results[my] = { ...it, ...r };
      log(`    → status=${r.status} dead=${r.dead} ${r.binary ? '(binary)' : ''} ${r.elapsed}s`);
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  return results;
}

// ============ LLM VERIFICATION ============
const VERIFY_PROMPT = ({ url, finalUrl, title, claim, pageContent }) => `\
Ты fact-checker non-fiction книги. Проверяешь одну запись из SOURCES.md книги против реального контента веб-страницы.

URL: ${url}
${finalUrl && finalUrl !== url ? `РЕАЛЬНЫЙ URL ПОСЛЕ РЕДИРЕКТОВ: ${finalUrl}` : ''}
TITLE В SOURCES.md: ${title}

ЧТО SOURCES.md ЗАЯВЛЯЕТ ПРО ЭТОТ ИСТОЧНИК (полная запись):
"""
${claim}
"""

РЕАЛЬНЫЙ КОНТЕНТ СТРАНИЦЫ (без HTML, до ${MAX_CONTENT_KB}KB):
"""
${pageContent}
"""

ЗАДАНИЕ:
Проверь, поддерживает ли реальная страница то, что заявлено в SOURCES.md.

Особое внимание на:
- Конкретные цифры (проценты, суммы, выборки) — должны совпадать с реальной страницей
- Имя автора / организации — должно совпадать
- Год публикации — должен совпадать
- Главный тезис ("что важно") — должен опираться на реальный контент

ВЕРДИКТ (выбрать ОДИН):
- PASS — SOURCES.md корректно отражает источник
- DRIFT — близко, но цифра/деталь искажена (укажи какая)
- NOT_FOUND — заявленный факт НЕ найден на странице (источник возможно не тот)
- WRONG_PAGE — страница про что-то совсем другое
- UNCLEAR — недостаточно контента (paywall, JS-only, пустая страница)

ВЫХОД (СТРОГО, чтобы я распарсил):

VERDICT: <PASS|DRIFT|NOT_FOUND|WRONG_PAGE|UNCLEAR>
EXPECTED: <одна строка — что заявлено в SOURCES.md>
ACTUAL: <одна строка — что найдено на странице>
NOTE: <одна короткая строка — оценка и что исправить если DRIFT>
`;

async function verifyOne({ url, finalUrl, title, claim, content }) {
  if (!content || content.length < 200) {
    return { verdict: 'UNCLEAR', expected: 'n/a', actual: 'page returned <200 chars of text', note: 'paywall / SPA / JS-only' };
  }
  const prompt = VERIFY_PROMPT({ url, finalUrl, title, claim, pageContent: content });
  try {
    const result = await dispatch({ prompt, prefer: PROVIDER, timeoutMs: 240000 });
    const text = result.text || '';
    const verdict = (text.match(/VERDICT:\s*(\S+)/i) || [])[1] || 'UNKNOWN';
    const expected = (text.match(/EXPECTED:\s*(.+?)(?=\n|$)/i) || [])[1] || '';
    const actual = (text.match(/ACTUAL:\s*(.+?)(?=\n|$)/i) || [])[1] || '';
    const note = (text.match(/NOTE:\s*(.+?)(?=\n|$)/i) || [])[1] || '';
    return { verdict: verdict.toUpperCase().trim(), expected: expected.trim(), actual: actual.trim(), note: note.trim(), provider: result.provider, elapsed: result.elapsed };
  } catch (e) {
    return { verdict: 'ERROR', expected: '', actual: '', note: `LLM error: ${e.message.slice(0, 200)}` };
  }
}

// ============ MAIN ============
async function main() {
  if (!fs.existsSync(SOURCES_FILE)) {
    console.error(`SOURCES.md not found: ${SOURCES_FILE}`);
    process.exit(2);
  }
  const sourcesText = fs.readFileSync(SOURCES_FILE, 'utf-8');
  const items = parseSourcesMd(sourcesText);
  log(`fact-check-web start: chapter="${CHAPTER}" provider=${PROVIDER}`);
  log(`  SOURCES.md: ${SOURCES_FILE} (${sourcesText.length} chars)`);
  log(`  Parsed ${items.length} (URL, claim) pairs from SOURCES.md`);

  if (items.length === 0) {
    fs.writeFileSync(OUT_PATH, `# WEB-FACT-REPORT — ${CHAPTER}\n\nGenerated: ${new Date().toISOString()}\n\n**No URL entries parsed from SOURCES.md.** Check format.\n`, 'utf-8');
    log(`No URLs — wrote empty report`);
    return;
  }

  log(`Fetching ${items.length} URLs (concurrency=${CONCURRENCY}, timeout=${FETCH_TIMEOUT_MS}ms)...`);
  const fetched = await fetchAll(items);

  let verifications = new Array(fetched.length).fill(null);
  if (!SKIP_LLM) {
    const llmable = fetched.filter((f) => !f.dead && !f.binary && f.content);
    log(`Verifying ${llmable.length}/${fetched.length} alive HTML URLs via ${PROVIDER}...`);
    let vi = 0;
    async function vWorker() {
      while (vi < fetched.length) {
        const my = vi++;
        const f = fetched[my];
        if (f.dead || f.binary || !f.content) {
          continue;
        }
        log(`  verify [${my + 1}/${fetched.length}]: ${f.url}`);
        const v = await verifyOne(f);
        verifications[my] = v;
        log(`    → ${v.verdict} ${v.elapsed ? `(${v.elapsed}s)` : ''}`);
      }
    }
    const llmConcurrency = Math.min(2, CONCURRENCY);
    await Promise.all(Array.from({ length: llmConcurrency }, () => vWorker()));
  }

  // Build report
  const counts = { PASS: 0, DRIFT: 0, NOT_FOUND: 0, WRONG_PAGE: 0, UNCLEAR: 0, ERROR: 0, DEAD: 0, BLOCKED: 0, BINARY: 0, SKIPPED: 0 };
  const lines = [];
  lines.push(`# WEB-FACT-REPORT — ${CHAPTER}`);
  lines.push('');
  lines.push(`Generated: ${new Date().toISOString()}`);
  lines.push(`Source file: SOURCES.md (${sourcesText.length} chars, ${items.length} URL entries)`);
  lines.push(`Provider for LLM verification: ${SKIP_LLM ? 'SKIPPED' : PROVIDER}`);
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push('## Per-source results');
  lines.push('');
  for (let i = 0; i < fetched.length; i++) {
    const f = fetched[i];
    const v = verifications[i];
    let line = `### ${i + 1}. ${f.title || '(no title)'}`;
    line += `\n   - URL: ${f.url}`;
    if (f.finalUrl && f.finalUrl !== f.url) line += `\n   - ↳ redirected to: ${f.finalUrl}`;
    line += `\n   - HTTP: ${f.status ?? 'no-response'} (${f.elapsed}s)`;
    if (f.dead) {
      line += `\n   - **DEAD URL** ${f.error ? `(${f.error})` : ''}`;
      counts.DEAD++;
    } else if (f.blocked) {
      line += `\n   - **BLOCKED** (anti-bot / status=${f.status ?? 'timeout'} / ${f.error || ''}) — URL вероятно жив, но не пускает headless. Проверить вручную.`;
      counts.BLOCKED++;
    } else if (f.binary) {
      line += `\n   - **BINARY** content-type=${f.contentType} (LLM-проверка пропущена; URL жив)`;
      counts.BINARY++;
    } else if (SKIP_LLM) {
      line += `\n   - LLM verification skipped (--skip-llm)`;
      counts.SKIPPED++;
    } else if (v) {
      line += `\n   - **VERDICT: ${v.verdict}**`;
      if (v.expected) line += `\n   - expected: ${v.expected}`;
      if (v.actual) line += `\n   - actual: ${v.actual}`;
      if (v.note) line += `\n   - note: ${v.note}`;
      counts[v.verdict] = (counts[v.verdict] || 0) + 1;
    }
    lines.push(line);
    lines.push('');
  }
  lines.push('---');
  lines.push('');
  lines.push('## Summary');
  lines.push('');
  for (const [k, v] of Object.entries(counts)) {
    if (v > 0) lines.push(`- ${k}: ${v}`);
  }
  lines.push('');
  const critical = (counts.DRIFT || 0) + (counts.NOT_FOUND || 0) + (counts.WRONG_PAGE || 0) + (counts.DEAD || 0);
  const needsManual = (counts.BLOCKED || 0);
  if (critical > 0) {
    lines.push(`⚠️ **${critical} критических проблем** (DRIFT / NOT_FOUND / WRONG_PAGE / DEAD) — требует ревью.`);
  } else {
    lines.push(`✅ Критических проблем не обнаружено.`);
  }
  if (needsManual > 0) {
    lines.push(`ℹ️  ${needsManual} URL'ов помечены BLOCKED (anti-bot защита) — проверь вручную в браузере.`);
  }

  fs.writeFileSync(OUT_PATH, lines.join('\n'), 'utf-8');
  log(`fact-check-web done: ${OUT_PATH}`);
  log(`  Counts: ${JSON.stringify(counts)}`);
}

main().catch((e) => {
  console.error(`fact-check-web FATAL: ${e.message}`);
  if (e.stack) console.error(e.stack);
  process.exit(99);
});
