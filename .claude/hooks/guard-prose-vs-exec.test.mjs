#!/usr/bin/env node
// Контрольная матрица для правки checkCritical: проза против исполняемого.
// Цель — доказать, что цитата в документации проходит, а тот же текст в файле,
// который кто-то исполнит, блокируется. Проверяем и форматы, о которых легко
// забыть: .sql, .tf, .yml.
//
// Опасные строки СОБИРАЮТСЯ ИЗ КУСКОВ намеренно. Гард проверяет литерал, и
// набор тестов для него неизбежно содержит то, что он ловит, — при записи
// целиком гард блокирует собственный тест. Это честное ограничение проверки по
// подстроке, а не обход: настоящая нагрузка от разбиения не становится
// безопаснее, просто тест перестаёт себя блокировать.
//
// Запуск: node guard-prose-vs-exec.test.mjs
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const GUARD = path.join(path.dirname(fileURLToPath(import.meta.url)), 'guard.js');

const DROP = 'DROP DATA' + 'BASE prod;';
const RMRF = 'rm -' + 'rf / ';

function run(file, content) {
  try {
    execFileSync(process.execPath, [GUARD], {
      input: JSON.stringify({ tool_name: 'Write', tool_input: { file_path: file, content } }),
      encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'],
    });
    return 'ПРОПУСТИЛ';
  } catch (e) { return 'ЗАБЛОКИРОВАЛ'; }
}

const cases = [
  ['/tmp/mig.sql', DROP,                              'ЗАБЛОКИРОВАЛ'],
  // Терраформ ПРОПУСКАЕТСЯ, и это НЕ следствие правки про прозу: сама
  // CRITICAL_PATTERNS требует после `/` конца строки или `;&|`, а здесь идёт
  // кавычка. Так было и до правки. Разрыв настоящий, но расширять правила
  // блокирующего гарда с зелёным набором на 90 случаев — отдельное решение,
  // а не побочный эффект починки. Исполнение всё равно ловит ветка Bash.
  ['/tmp/main.tf', 'provisioner { command = "' + RMRF + '" }', 'ПРОПУСТИЛ'],
  ['/tmp/ci.yml',  'script:\n  - ' + RMRF,            'ЗАБЛОКИРОВАЛ'],
  ['/tmp/note.md', 'пример того, что нельзя: ' + DROP, 'ПРОПУСТИЛ'],
  ['/tmp/doc.txt', 'в рунбуке пишут ' + RMRF + '— не делайте так', 'ПРОПУСТИЛ'],
];

let bad = 0;
for (const [f, c, want] of cases) {
  const got = run(f, c);
  const ok = got === want;
  if (!ok) bad++;
  console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${f.padEnd(16)} ждали ${want}, получили ${got}`);
}
console.log(`\n  ${cases.length - bad}/${cases.length} прошло`);
process.exit(bad ? 1 : 0);
