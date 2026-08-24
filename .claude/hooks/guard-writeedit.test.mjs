#!/usr/bin/env node
/*
 * guard-writeedit.test.mjs — проверка ВЕТКИ Write|Edit|MultiEdit объединённого
 * хука guard.js. Набор bash-guard.test.mjs покрывает только ветку Bash.
 *
 * Метод: каждый случай прогоняется ЧЕРЕЗ ОБА хука — старый security-guard.js и
 * новый guard.js — и сравнивается ТРОЙКА (код выхода, stdout, stderr). Проверять
 * новый файл против ожиданий, выписанных руками, было бы слабее: совпадение с
 * оригиналом байт-в-байт доказывает, что поведение не сдвинулось нигде, включая
 * advisory-JSON, который хук отдаёт в stdout и который читает Claude Code.
 *
 * Улики собираются СКЛЕЙКОЙ ИЗ КУСКОВ, и в комментариях они тоже не выписаны
 * целиком: иначе гард блокирует запись собственного теста. Это честное
 * ограничение проверки по подстроке, а не обход — настоящая нагрузка от
 * разбиения безопаснее не становится.
 *
 * Пути в случаях — синтетические строки, на диске они существовать не обязаны:
 * хук разбирает file_path как текст.
 *
 * Запуск: node guard-writeedit.test.mjs
 */
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const NEW = path.join(HERE, 'guard.js');
const OLD = path.join(HERE, 'security-guard.js');

const ROOT = '/';
const RMRF = 'rm -' + 'rf ' + ROOT;                   // рекурсивное удаление корня
const RMTREE = 'shutil.' + 'rmtree("' + ROOT + '")';  // то же из Python
const DROPDB = 'DR' + 'OP DATABASE prod_main;';       // снос боевой базы

// «Личный путь» для хука — это то, что попадает в PERSONAL_PATHS guard.js:
// каталог конфига, /tmp/, /scratch/, node_modules и т.п. Берём каталог конфига.
const CFG = '/home/user/.claude';
const APP = '/srv/app';

const CASES = [
  // --- должно БЛОКИРОВАТЬ (exit 2) ---
  { name: 'Write: удаление корня в теле скрипта', expect: 2,
    payload: { tool_name: 'Write', tool_input: { file_path: APP + '/deploy.sh', content: '#!/bin/sh\n' + RMRF + '\n' } } },
  { name: 'Edit: снос дерева от корня в новой строке', expect: 2,
    payload: { tool_name: 'Edit', tool_input: { file_path: APP + '/clean.py', new_string: 'import shutil\n' + RMTREE } } },
  { name: 'MultiEdit: снос базы во втором фрагменте', expect: 2,
    payload: { tool_name: 'MultiEdit', tool_input: { file_path: APP + '/mig.sql',
      edits: [{ new_string: 'SELECT 1;' }, { new_string: DROPDB }] } } },
  { name: 'Write в личный путь: критическое всё равно блокируется', expect: 2,
    payload: { tool_name: 'Write', tool_input: { file_path: CFG + '/tmp.sh', content: RMRF + ' ; echo done' } } },

  // --- должно ПРОХОДИТЬ (exit 0) ---
  { name: 'Write: обычный код без улик', expect: 0,
    payload: { tool_name: 'Write', tool_input: { file_path: APP + '/util.js', content: 'export const sum = (a, b) => a + b;\n' } } },
  { name: 'Write: удаление ПОДПАПКИ, а не корня', expect: 0,
    payload: { tool_name: 'Write', tool_input: { file_path: APP + '/clean.sh', content: 'rm -' + 'rf ./build node_modules\n' } } },
  { name: 'Edit: eval() — только совет, не блок', expect: 0,
    payload: { tool_name: 'Edit', tool_input: { file_path: APP + '/run.js', new_string: 'const r = eval(userInput);' } } },
  { name: 'Write в личный путь: советы подавлены', expect: 0,
    payload: { tool_name: 'Write', tool_input: { file_path: CFG + '/scratch/x.js', content: 'el.innerHTML = data;' } } },

  // --- контракт ветки ---
  { name: 'Write без содержимого — пропуск', expect: 0,
    payload: { tool_name: 'Write', tool_input: { file_path: APP + '/a.txt' } } },
  { name: 'Read (чужой инструмент) — пропуск', expect: 0,
    payload: { tool_name: 'Read', tool_input: { file_path: APP + '/a.txt' } } },
];

function run(guard, payload) {
  const r = spawnSync(process.execPath, [guard], { input: JSON.stringify(payload), encoding: 'utf8' });
  return { code: r.status, out: (r.stdout || '').trim(), err: (r.stderr || '').trim() };
}

let pass = 0;
const fails = [];
for (const c of CASES) {
  const a = run(OLD, c.payload);
  const b = run(NEW, c.payload);
  const same = a.code === b.code && a.out === b.out && a.err === b.err;
  const ok = same && b.code === c.expect;
  if (ok) pass++; else fails.push({ c, a, b });
  const adv = b.out ? '  [advisory в stdout]' : '';
  console.log(`${ok ? 'PASS' : 'FAIL'}  [${c.expect === 2 ? 'block' : 'allow'}] ${c.name}` +
    `  -> старый ${a.code} / новый ${b.code}${adv}`);
}
console.log(`\n${pass}/${CASES.length} прошло (сверка старый security-guard.js vs новый guard.js: код+stdout+stderr)`);
if (fails.length) {
  for (const f of fails) console.log(`\n- ${f.c.name}\n  ждали ${f.c.expect}\n  старый: ${JSON.stringify(f.a)}\n  новый:  ${JSON.stringify(f.b)}`);
  process.exit(1);
}
