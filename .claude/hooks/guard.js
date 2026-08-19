#!/usr/bin/env node
/*
 * guard.js — ОБЪЕДИНЁННЫЙ PreToolUse-хук: bash-guard + security-guard в одном
 * процессе node. Причина слияния — цена, а не логика: на каждый вызов любого
 * инструмента запускались ДВА процесса node (75 мс + 72 мс), тогда как сама
 * логика обоих ~3 мс. Платили за второй спавн, не за работу.
 *
 * Логика НЕ переписана. Оба тела перенесены построчно из своих файлов:
 *   security-guard.js  строки 4-85 (константы и helpers) и 93-147 (тело)
 *   bash-guard.js      строки 1-147 (шапка, killswitch) и 153-846 (тело)
 * Исчезло РОВНО одно: у каждого свой приём stdin. Теперь stdin читается один
 * раз в общей точке входа внизу файла, а tool_name решает, чьи правила
 * применить. Диспетчер повторяет матчеры из settings.json один-в-один:
 *   Write|Edit|MultiEdit -> ветка security-guard
 *   всё остальное (Bash|PowerShell) -> ветка bash-guard
 *
 * Коды выхода прежние: 2 = блок, 0 = пропуск. Fail-open на любой ошибке.
 * Killswitch CC_HOOKS_OFF=1 стоит там же, где стоял, — в ветке Bash
 * (у security-guard его никогда не было; глобальный killswitch ослабил бы
 * защиту Write/Edit, поэтому поведение сохранено как есть).
 *
 * Отступы исходных строк НЕ меняли: так `diff` против оригиналов остаётся
 * читаемым и видно, что перенос дословный.
 *
 * Откат: старые bash-guard.js и security-guard.js лежат рядом нетронутыми —
 * достаточно вернуть в settings.json две прежние записи PreToolUse.
 *
 * Проверки: node bash-guard.test.mjs --guard guard.js   (набор для Bash)
 *           node guard-writeedit.test.mjs               (ветка Write/Edit)
 */
'use strict';
const fs = require('fs');
const path = require('path');

function allow() { process.exit(0); } // fail-open / no match

/* ==========================================================================
 * ВЕТКА Write | Edit | MultiEdit — дословно из security-guard.js
 * ======================================================================== */
const PERSONAL_PATHS = [
  /\.claude[\/\\]/i,
  /\.claude\.json/i,
  /graph-memory[\/\\]/i,
  /personal-intelligence-hub[\/\\]/i,
  /[\/\\]tmp[\/\\]/i,
  /[\/\\]temp[\/\\]/i,
  /[\/\\]scratch[\/\\]/i,
  /[\/\\]Downloads[\/\\]/i,
  /[\/\\]projects[\/\\]tools[\/\\]/i,
  /\.credentials\.master\.env/i,
  /[\/\\]memory[\/\\].*\.md$/i,
  /[\/\\]\.cursor[\/\\]/i,
  /[\/\\]\.vscode[\/\\]/i,
  /[\/\\]node_modules[\/\\]/i,
  /[\/\\]\.git[\/\\]/i,
  /[\/\\]venv[\/\\]/i,
  /[\/\\]__pycache__[\/\\]/i
];

const ADVISORY_PATTERNS = [
  { name: 'eval_inj', regex: /\beval\s*\(/i, message: 'eval() detected' },
  { name: 'new_func', regex: /\bnew\s+Function\s*\(/i, message: 'new Function() detected' },
  { name: 'inner_html', regex: /\.innerHTML\s*=/i, message: 'innerHTML= XSS risk' },
  { name: 'dangerous_html', regex: /dangerouslySetInnerHTML/i, message: 'dangerouslySetInnerHTML XSS' },
  { name: 'doc_write', regex: /document\.write\s*\(/i, message: 'document.write XSS' },
  { name: 'cp_exec', regex: /child_process\.exec\s*\(/i, message: 'child_process.exec shell inj' },
  { name: 'os_system', regex: /\bos\.system\s*\(/i, message: 'os.system command inj' },
  { name: 'pickle', regex: /\bpickle\.(loads?|Unpickler)\b/i, message: 'pickle code exec' },
];

const CRITICAL_PATTERNS = [
  { name: 'rm_rf_root', regex: /\brm\s+-rf\s+\/\s*($|[;&|])/, message: 'CRITICAL: rm -rf /' },
  { name: 'rmtree_root', regex: /shutil\.rmtree\s*\(\s*[^)]{0,5}\//, message: 'CRITICAL: rmtree(/)' },
  { name: 'drop_db', regex: /DROP\s+DATABASE\s+\w+\s*;/i, message: 'CRITICAL: DROP DATABASE' },
];

const INJECTION_PATTERNS = [
  /ignore\s+(all\s+)?previous\s+instructions/i,
  /ignore\s+(all\s+)?above\s+instructions/i,
  /disregard\s+(all\s+)?previous/i,
  /forget\s+(all\s+)?(your\s+)?instructions/i,
  /override\s+(system|previous)\s+(prompt|instructions)/i,
  /you\s+are\s+now\s+(?:a|an|the)\s+/i,
  /pretend\s+(?:you(?:'re| are)\s+|to\s+be\s+)/i,
  /from\s+now\s+on,?\s+you\s+(?:are|will|should|must)/i,
  /(?:print|output|reveal|show|display|repeat)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions)/i,
  /<\/?(?:system|assistant|human)>/i,
  /\[SYSTEM\]/i,
  /\[INST\]/i,
  /<<\s*SYS\s*>>/i,
];

function isPersonalPath(p) {
  if (!p) return true;
  return PERSONAL_PATHS.some(re => re.test(p));
}

function checkCritical(content) {
  for (const p of CRITICAL_PATTERNS) {
    if (p.regex.test(content)) return p;
  }
  return null;
}

function checkAdvisory(content) {
  const findings = [];
  for (const p of ADVISORY_PATTERNS) {
    if (p.regex.test(content)) findings.push(p);
  }
  return findings;
}

function extractContent(toolName, toolInput) {
  if (toolName === 'Write') return (toolInput && toolInput.content) || '';
  if (toolName === 'Edit') return (toolInput && toolInput.new_string) || '';
  if (toolName === 'MultiEdit') {
    const edits = (toolInput && toolInput.edits) || [];
    return edits.map(function(e){return e.new_string || '';}).join(' ');
  }
  return '';
}

// Тело бывшего обработчика process.stdin.on("end", ...). Аргумент data —
// уже разобранный JSON: раньше он получался тут же из накопленного stdin.
function runSecurityGuard(data) {
  try {
    const toolName = data.tool_name || '';
    const toolInput = data.tool_input || {};
    const filePath = toolInput.file_path || '';

    if (['Write', 'Edit', 'MultiEdit'].indexOf(toolName) === -1) process.exit(0);

    const content = extractContent(toolName, toolInput);
    if (!content) process.exit(0);

    const critical = checkCritical(content);
    if (critical) {
      console.error('BLOCKED: ' + critical.message);
      console.error('File: ' + filePath);
      process.exit(2);
    }

    if (isPersonalPath(filePath)) process.exit(0);

    const pathMod = require('path');

    // Check for invisible Unicode characters (injection obfuscation)
    if (filePath.indexOf('.planning') !== -1 && /[\u200B-\u200F\u2028-\u202F\uFEFF\u00AD]/.test(content)) {
      const out = {
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          additionalContext: 'Invisible Unicode detected in ' + require('path').basename(filePath) + ' - possible injection obfuscation',
        },
      };
      process.stdout.write(JSON.stringify(out));
      process.exit(0);
    }

    if (filePath.indexOf('.planning') !== -1) {
      for (const re of INJECTION_PATTERNS) {
        if (re.test(content)) {
          const out = { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: 'Prompt injection in ' + pathMod.basename(filePath) } };
          process.stdout.write(JSON.stringify(out));
          process.exit(0);
        }
      }
    }

    const advisories = checkAdvisory(content);
    if (advisories.length > 0) {
      const msgs = advisories.map(function(a){return '- ' + a.name + ': ' + a.message;}).join('\n');
      const out = { hookSpecificOutput: { hookEventName: 'PreToolUse', additionalContext: 'Security advisory for ' + pathMod.basename(filePath) + ':\n' + msgs } };
      process.stdout.write(JSON.stringify(out));
    }

    process.exit(0);
  } catch (e) {
    process.exit(0);
  }
}

/* ==========================================================================
 * ВЕТКА Bash | PowerShell — дословно из bash-guard.js
 * ======================================================================== */
/*
 * bash-guard.js — PreToolUse guard against CATASTROPHIC shell commands.
 * Replaces 4 fake matchers (Bash(rm -rf)/Bash(DROP DATABASE)/... which never fired:
 * matcher = tool-NAME regex, not command content; and `exit 1` never blocked).
 *
 * Fires on tool Bash|PowerShell (matcher in settings.json). Reads hook JSON on stdin,
 * inspects tool_input.command, blocks (exit 2 + stderr) only UNAMBIGUOUS destroyers.
 * Conservative: legit `rm -rf ./subdir`, `rm -rf ~/scratch/x`, `rm -rf node_modules` PASS.
 * fail-open (any error/no-match => allow). Killswitch: env CC_HOOKS_OFF=1.
 * Logs blocks to ~/.claude/hooks-logs/YYYY-MM-DD.jsonl.
 *
 * 2026-07-19 gap-fill (T1-6 roadmap): del /s on roots/home, robocopy /MIR to roots,
 * DELETE FROM without WHERE, git checkout/restore -- ., chattr -R -i,
 * quoted-target rm (`rm -rf "/"`), and an SSH branch: the remote command inside
 * `ssh host "..."` is re-scanned with the SAME destructive patterns
 * (a production host may sit behind that quote — destroyers inside quotes were invisible).
 *
 * 2026-07-19 dcg-port (Dicklesworthstone/destructive_command_guard, Rust, 2.9k*):
 * interpreter inline payloads (python -c / perl -e / node -e / bash -c + heredocs)
 * re-scanned; decode-and-exec (base64 -d | sh, eval $(base64|curl), bash <(curl),
 * sh -c "$(curl)"); powershell -EncodedCommand decoded (UTF-16LE + UTF-8) and
 * re-scanned; wipefs -a; vssadmin/wmic shadowcopy delete.
 *
 * 2026-07-31 infra-destruction gap-fill: docker rm -f, docker rm/stop/kill
 * $(docker ps ...), docker compose down (+ -v/--volumes = data loss),
 * docker volume rm, docker * prune, pm2 delete/kill, systemctl stop/disable,
 * service ... stop, kubectl delete. Read-only ops never match.
 *
 * 2026-08-17 intent-vs-text (проверено на практике: `python - <<EOF`, внутри ТЕКСТА
 * скрипта строка-литерал с "DROP TABLE" — гард заблокировал запуск [drop-table]).
 * Причина: все паттерны прикладывались к СЫРОЙ строке команды — вместе с телами
 * heredoc, содержимым кавычек и комментариями. Подстрока «нашлась» — блок,
 * хотя шелл эту подстроку никогда не исполняет.
 *
 * Лекарство — не ослабление паттернов, а сопоставление с тем, что РЕАЛЬНО
 * исполняется. Команда токенизируется на 4 слоя:
 *   КОД        — то, что видит шелл как команды/аргументы;
 *   СТРОКИ     — содержимое '...' и "..." (данные, не команды);
 *   HEREDOC    — тела <<TAG ... TAG (stdin-данные для потребителя);
 *   КОММЕНТЫ   — от невзятого в кавычки # до конца строки (выбрасываются).
 * Паттерны прикладываются к КОДУ. Строки и heredoc-тела сканируются ОТДЕЛЬНО
 * и только когда у полезной нагрузки есть ИСПОЛНИТЕЛЬ:
 *   - ssh host "..."           → нагрузка исполняется удалённым шеллом;
 *   - bash|sh -c / eval / bash <<EOF → нагрузка = команды;
 *   - psql|mysql|sqlite3 -c/-e/heredoc → нагрузка = исполняемый SQL;
 *   - python|node|perl -c/-e/heredoc  → нагрузка = код; его строки-литералы
 *     проверяются ТОЛЬКО при наличии exec-стока (os.system/subprocess/spawn...)
 *     — литерал без стока это данные, печать, анализ;
 *   - $(...) и `...` внутри ДВОЙНЫХ кавычек → шелл подставляет и исполняет.
 * Однословные закавыченные токены (без пробелов и метасимволов) вклеиваются
 * обратно в КОД: цель команды остаётся целью и в кавычках — `rm -rf "/"`,
 * `git push --force origin "main"`, `"mkfs.ext4" /dev/sda` не спрячутся.
 *
 * Почему это устойчиво: решение принимает не «нашлась подстрока», а «паттерн
 * совпал в исполняемой позиции». Текст без исполнителя (литерал, комментарий,
 * heredoc в cat, сообщение коммита) физически не может ничего разрушить —
 * его пропуск не открывает дыру. А у настоящего разрушителя исполнитель есть
 * всегда: либо сам код команды, либо один из каналов выше — и все каналы
 * рекурсивно проходят через те же паттерны (глубина ≤ 3).
 *
 * 2026-08-17 (вторая правка): одной токенизации не хватило — остался класс
 * ложных блокировок на ОДНОСЛОВНЫХ литералах. Токенизатор нарочно вклеивает
 * однословную закавыченную цель обратно в код (иначе спрячется `rm -rf "/"`),
 * но вместе с целью возвращается и безобидное слово: `grep 'mkfs' ops.md`
 * блокировался как форматирование диска. Гейт «команда только показывает
 * текст» (TEXTDISP) закрывал лишь SQL-правила, потому что проверялся на всей
 * строке: `echo hi && rm -rf /` тоже начинается с echo.
 * Лечение — сегментация: код режется по НЕВЗЯТЫМ в кавычки разделителям
 * (; && || | перевод строки), и каждый сегмент оценивается сам по себе.
 * Тогда гейт можно распространить на ВСЕ правила: в `echo hi && rm -rf /`
 * второй сегмент показывалкой не является и блокируется, а `grep 'mkfs' f`
 * состоит из одного сегмента-показывалки и проходит.
 * Правила, чья улика САМА состоит из разделителей (curl | sh, форк-бомба),
 * помечены span:true и по-прежнему смотрят строку целиком.
 * Плюс: код интерпретатора сканируется узким набором INTERP_ONLY (там `mkfs`
 * или `drop table` — слово языка, а не команда), а список-форма
 * subprocess.run(["rm","-rf","/"]) ловится склейкой аргументов стока.
 *
 * 2026-08-18 состязательный прогон (три атаки, 134 пробы): пролезло 39
 * исполнимых разрушителей по шести причинам. Закрыто в этой правке:
 *   1) ЯКОРЬ ИСПОЛНИТЕЛЯ был слишком строгим — интерпретатор требовался в
 *      начале строки или сразу после разделителя. `sh -c "…"` блокировался,
 *      `timeout 5 sh -c "…"`, `sudo sh -c "…"`, `/bin/sh -c "…"`,
 *      `docker exec app sh -c "…"` — нет (15 пролазов). Лечение: WRAP —
 *      закрытый список обёрток, которые сами ничего не делают, + PATHPFX;
 *   2) POWERSHELL -Command не разбирался вовсе, декодировался только
 *      -EncodedCommand. Это основной шелл машины (PS_TRIG + ps-remove-root,
 *      где цель могла стоять до флагов и упираться в кавычку);
 *   3) ОБФУСКАЦИЯ РАСКРЫТИЕМ: `r\m`, `"r"m`, `$'rm'`, `X=rm; $X -rf /`,
 *      `rm -rf $X`, `rm${IFS}-rf${IFS}/`, `$(echo rm)` — bash раскрывает всё
 *      это ДО исполнения, а гард видел исходный текст. Лечение: expandRaw —
 *      второй проход по нормализованной копии (см. там же);
 *   4) ИСПОЛНИТЕЛЬ ВНЕ МОДЕЛИ: `find / -exec rm`, `echo / | xargs rm -rf`,
 *      `docker run -v /:/host … rm -rf /host` (псевдоним корня);
 *   5) СПИСОК ДЕКОДЕРОВ был перечислимым (base64/openssl/xxd): `printf`
 *      с восьмеричными и `tr` в конвейере к шеллу проходили;
 *   6) ФАЙЛОВАЯ КОСВЕННОСТЬ — не чинится, см. ГРАНИЦЫ.
 * Проверки-пары: на каждую правку в набор добавлен и блокируемый случай,
 * и соседний из обычной работы, который правка не должна была задеть.
 *
 * ГРАНИЦЫ (осознанные — честная граница лучше ложного чувства защищённости):
 *  - токенизатор приближённый, не bash. Незакрытая кавычка съедает остаток
 *    строки, и код за ней в скан не попадает — но такую команду и сам bash
 *    не выполнит (syntax error), так что дыры нет; в PowerShell правила
 *    цитирования иные, там это ослабление реально;
 *  - список TEXTDISP держать чистым: туда можно добавлять только команды,
 *    физически неспособные разрушить (никаких xargs/find/sudo/env — они
 *    исполняют чужое, и целый сегмент перестал бы проверяться);
 *  - разделители ищутся в УЖЕ токенизированном коде, поэтому `;` внутри
 *    строки сегмент не режет; но однословная вклейка не может их содержать
 *    (SIMPLE_TOKEN это запрещает) — значит найденный разделитель настоящий;
 *  - глубина рекурсии по каналам ≤ 3: `ssh a "ssh b \"ssh c ...\""` глубже
 *    не разбирается (fail-open);
 *  - ПОДСТАНОВКА КОМАНД раскручивается только для $(echo …) и $(printf …),
 *    склейка литералов ('Rem'+'ove-Item') — снимается. НЕ раскручивается то,
 *    что вычисляется в рантайме: `$(cat name.txt) -rf /`, `$(curl …)`,
 *    `iex (Get-Content x.ps1 -Raw)`, значение переменной из окружения
 *    (`rm -rf $EXTERNAL_ROOT`, где присваивания в этой же команде нет).
 *    Воспроизвести это без интерпретатора нельзя, а «починить» регэкспом =
 *    позвать настоящий шелл на этапе хука, то есть исполнить проверяемое;
 *  - ФАЙЛОВАЯ КОСВЕННОСТЬ вне модели: `base64 -d > p.sh && sh p.sh`,
 *    `psql -f drop.sql`, `echo … > x.py && python x.py`. Гард видит команду,
 *    а не диск, и намеренно НЕ читает файлы: содержимое литерала — данные
 *    (ровно тот дефект, который чинили 17.08), а чтение произвольных путей
 *    на каждый вызов Bash — и цена, и новый источник сюрпризов;
 *  - СОСТОЯНИЕ ШЕЛЛА недоступно: `alias x='…'`/функция/`export X=/` из
 *    ПРЕДЫДУЩЕГО вызова Bash не видны — хук получает одну команду, а не
 *    сессию. Подстановка переменных работает только внутри одной команды;
 *  - ЮНИКОД-ГОМОГЛИФЫ (кир. «рm») и zero-width внутри имени пролезают, но и
 *    настоящий шелл их не исполнит — это не дыра, а безвредный текст;
 *  - НЕ-КОРНЕВЫЕ, но ценные цели (`rm -rf /opt/app`) пропускаются намеренно:
 *    субпути разрешены, иначе гард встанет поперёк ежедневной работы.
 *    Исключение — системные папки (rm-sysdir) и выход наверх через «..».
 *
 * Проверки: bash-guard.test.mjs рядом (85 команд + 5 контрактных).
 * Запуск: node bash-guard.test.mjs   ·   замер: node bash-guard.test.mjs --bench
 */
function runBashGuard(data) {
try {
  if (process.env.CC_HOOKS_OFF === '1') allow();

  const ti = (data && data.tool_input) || {};
  const cmd = (ti.command || ti.script || '');
  if (typeof cmd !== 'string' || !cmd.trim()) allow();

  // Запасное значение не должно быть чьей-то конкретной папкой: на чужой машине
  // такого пути нет, и защита молча перестаёт срабатывать.
  const HOMEwin = (process.env.USERPROFILE || process.env.HOME || 'C:/Users/Default');
  const HOMEfwd = HOMEwin.replace(/\\/g, '/');
  const HOMEfwdEsc = HOMEfwd.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const HOMEbackEsc = HOMEwin.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Команда-«показывалка»: только читает/печатает/ищет текст и сама ничего
  // не разрушает. Упоминание опасного слова в её аргументах — данные.
  // Раньше этот гейт закрывал ТОЛЬКО sql-паттерны, потому что проверялся на
  // всей сырой строке: `echo hi && rm -rf /` тоже начинается с echo. После
  // введения сегментации (см. SEP_RE ниже) проверка идёт по КАЖДОМУ командному
  // сегменту отдельно, поэтому гейт безопасно распространить на ВСЕ правила:
  // во втором сегменте `rm -rf /` показывалки нет и он будет заблокирован.
  // В список входят только команды, физически неспособные разрушить систему
  // (никаких xargs/find/sudo/env — они исполняют чужое).
  const TEXTDISP = /^\s*(echo|printf|cat|grep|rg|egrep|fgrep|less|more|head|tail|print|type|write-output|write-host|awk|sed|man|which|whereis|whatis|apropos|stat|file|wc|sort|uniq|nl|cut|tr|column|jq|diff|ls|dir|pwd|date|vim?|nano|nvim|code|git\s+commit|git\s+log|git\s+show|git\s+diff|git\s+grep)\b/i;

  // Разделители командных сегментов. Применяются к УЖЕ токенизированному коду:
  // многословные строки оттуда вырезаны, а однословные вклейки не могут
  // содержать ; & | (это запрещено SIMPLE_TOKEN) — значит любой найденный
  // здесь разделитель настоящий, а не буква внутри текста.
  const SEP_RE = /\|\||&&|[;&|\n]/;

  // rm root-target: block ONLY the whole root/home/drive (exact, or trailing / or /*), NOT subpaths.
  const RM = /\brm\s+(?:-[a-z]*\s+)*-[a-z]*[rf][a-z]*\s+(?:-[a-z]*\s+)*/i.source;
  // Q captures an optional opening quote; TERM requires the SAME quote (backref \1) closed
  // before the boundary — so `rm -rf "/"` blocks, while `echo "rm -rf /"` still passes.
  const Q = "([\"']?)";
  const TERM = '(?:\\/|\\/\\*|\\*)?\\1(?:\\s|$|;|&|\\|)';
  // Windows path tail for del/robocopy targets: optional \ or /, optional *, closing backref quote, boundary.
  const WINEND = '[\\\\/]?\\*?\\1(?:\\s|$|;|&|\\|)';

  // docker prefix + optional GLOBAL flags before the subcommand (`docker -H tcp://h:2375 rm -f x`,
  // `docker --context prod compose down`). Each optional token must start with a dash, so the
  // subcommand word itself can never be swallowed by the group.
  const DKRFLAGS = '(?:(?:-[a-zA-Z]|--[a-z][\\w-]*)(?:[=\\s]+[^\\s;&|]+)?\\s+)*';
  const DKR  = '\\bdocker(?:\\.exe)?\\s+' + DKRFLAGS;          // `docker <sub>`
  const DKRC = '\\bdocker(?:\\.exe)?[\\s-]+' + DKRFLAGS;       // `docker compose` AND `docker-compose`

  // Префикс шелл-стока в конвейере. Все правила «скачать/декодировать | шелл»
  // якорили сток на ГОЛОЕ имя (sh|bash|…), поэтому `curl … | /bin/sh`,
  // `base64 -d | sudo bash`, `printf … | env sh` пролезали — классический
  // install-script RCE и его вариации (состязательный прогон 2026-08-18, вторая
  // партия). Триггер-сторона это уже учитывала (WRAP/PATHPFX); симметрично
  // добавляем СТОК-сторону: необязательная цепочка безобидных обёрток, которые
  // сами ничего не делают, лишь запускают следующий аргумент, плюс путь до имени.
  // Обёртки-исполнители чужого (xargs/find/sudo -в TEXTDISP-смысле) тут наоборот
  // НУЖНЫ — мы ищем шелл ЗА ними, а не пропускаем сегмент.
  // Внешний повтор ОГРАНИЧЕН {0,3}: без границы обёртка-слово могла разбираться и
  // как аргумент предыдущей обёртки, а безграничный внешний `*` на входе вида
  // `sudo sudo … sudo` давал катастрофический бэктрекинг (ReDoS вешал хук на
  // КАЖДЫЙ вызов Bash). Реальные цепочки — 1-2 обёртки, {0,3} с запасом.
  const SHWRAP = '(?:(?:sudo|doas|env|nohup|timeout|stdbuf|setsid|command|exec|nice|ionice|unbuffer|time)(?:\\s+[^\\s;&|]{1,64}){0,4}\\s+){0,3}';
  const SHPFX  = '(?:[\\w.$~-]*\\/)*';   // /bin/, /usr/bin/, ./
  const P = [
    // Tier 1: root / home / drive roots (subpaths ALLOWED)
    { id: 'rm-root',    re: new RegExp(RM + Q + '(?:\\/|c:\\\\?|\\/c)' + TERM, 'i'), why: 'rm -rf корня / C:\\ / /c/' },
    { id: 'rm-home',    re: new RegExp(RM + Q + '(?:~|\\$\\{?home\\}?|\\$\\{?userprofile\\}?)' + TERM, 'i'), why: 'rm -rf $HOME/~' },
    { id: 'rm-homeabs', re: new RegExp(RM + Q + '(?:' + HOMEfwdEsc + '|' + HOMEbackEsc + ')' + TERM, 'i'), why: 'rm -rf домашней папки (абс. путь)' },
    // Выход наверх через «..» от дома, корня или абсолютной системной точки —
    // это обратная дорога к родителю дома/корня, а не соседняя папка. Обычный
    // относительный «../build» безопасен и сюда НЕ попадает: якорь обязателен —
    // цель начинается с ~ , /  или абсолютного home, и в ней есть «..».
    { id: 'rm-updir',   re: new RegExp(RM + Q + '(?:~|\\$\\{?home\\}?|\\$\\{?userprofile\\}?|' + HOMEfwdEsc + '|\\/[\\w.-]*)\\/\\.\\.(?:\\/|\\1|\\s|$|;|&|\\|)', 'i'), why: 'rm -rf с выходом наверх от дома/корня через ".." (~/.., /home/..)' },
    // Tier 2: system dirs (dir AND subpaths blocked — не пользовательские данные)
    { id: 'rm-sysdir',  re: new RegExp(RM + Q + '\\/(?:etc|usr|bin|sbin|boot|lib|sys|dev|proc|root)(?:\\/\\S*?)?\\1(?:\\s|$|;|&|\\|)', 'i'), why: 'rm -rf системной папки (/etc,/usr,/bin,...)' },
    // find по корню/дому: разрушает не сам find, а его исполнитель — -delete,
    // -exec rm или конвейер в xargs rm. Ловилась только первая форма.
    // Якорь — КОРЕНЬ в позиции пути find: `find /var/log … -delete` не матчится.
    { id: 'find-delete-root', re: /\bfind\s+(?:-[\w-]+\s+)*["']?(?:\/|~|\$\{?home\}?|\$\{?userprofile\}?)["']?\s+[^\n]*(?:-delete\b|-exec(?:dir)?\s+(?:\S*\/)?(?:rm|shred|unlink|truncate)\b)/i, why: 'find / -delete / -exec rm' },
    { id: 'find-pipe-rm-root', span: true, re: /\bfind\s+(?:-[\w-]+\s+)*["']?(?:\/|~|\$\{?home\}?)["']?\s[^\n]*\|\s*(?:[^|\n]*\|\s*)?xargs\b[^\n]*\b(?:rm|shred)\b/i, why: 'find / … | xargs rm — удаление всего дерева от корня' },
    // Цель приходит на stdin, поэтому в сегменте `xargs rm -rf` корня не видно.
    // Улика — производитель, печатающий именно корень (`echo / | xargs rm -rf`).
    // Обычный `find . -name '*.pyc' | xargs rm -f` под правило не подпадает.
    { id: 'xargs-rm-root', span: true, re: /(?:^|[;&|]\s*)(?:echo|printf|ls)\b[^|\n]*(?:^|\s)["']?(?:\/|~|\$\{?HOME\}?)["']?\s*\|\s*(?:[^|\n]*\|\s*)?xargs\b[^\n]*\b(?:rm|shred)\b/i, why: 'echo / | xargs rm — корень приходит на stdin' },
    // Windows cmd recursive delete of drive roots / home (del /s ... C:\ | %USERPROFILE% | home)
    { id: 'del-tree-root', re: new RegExp('\\bdel\\s+(?=(?:\\/[a-z]\\s+)*\\/s\\b)(?:\\/[a-z]\\s+)+' + Q +
        '(?:[a-z]:|%userprofile%|%homedrive%|%homepath%|' + HOMEfwdEsc + '|' + HOMEbackEsc + ')' + WINEND, 'i'),
      why: 'del /s корня диска или home' },
    // robocopy /MIR with a bare drive root or home as an argument (mirror wipes the destination)
    { id: 'robocopy-mir-root', re: new RegExp('\\brobocopy\\b(?=[^\\n]*\\s\\/mir\\b)[^\\n]*\\s' + Q +
        '(?:[a-z]:|' + HOMEfwdEsc + '|' + HOMEbackEsc + ')[\\\\/]?\\1(?=\\s|$|;|&|\\|)', 'i'),
      why: 'robocopy /MIR на корень диска/home' },
    // SQL drops / truncate / unfiltered delete (skipped if text-display)
    { id: 'drop-db',    re: /\bdrop\s+(database|schema)\b/i, why: 'DROP DATABASE/SCHEMA', sql: true },
    { id: 'drop-table', re: /\bdrop\s+table\b/i, why: 'DROP TABLE', sql: true },
    // Mongo пишет снос базы вызовом метода, а не SQL: db.dropDatabase(),
    // db.<coll>.drop(), db.getSiblingDB("x").dropDatabase(). SQL-правила их не видят.
    { id: 'mongo-drop', re: /\bdb(?:\.\w+|\.getSiblingDB\s*\([^)]*\))*\.drop(?:Database)?\s*\(/i, why: 'Mongo dropDatabase()/drop()', sql: true },
    { id: 'truncate',   re: /\btruncate\s+table\b/i, why: 'TRUNCATE TABLE', sql: true },
    { id: 'sql-delete-nowhere', re: /\bdelete\s+from\s+[\w"'`.\[\]]+\s*(?![^;]*\bwhere\b)/i, why: 'DELETE FROM без WHERE (сотрёт всю таблицу)', sql: true },
    // disk / filesystem destroyers
    { id: 'mkfs',       re: /\b(mkfs|mke2fs)\b/i, why: 'mkfs — форматирование ФС' },
    { id: 'dd-disk',    re: /\bdd\b[^\n]*\bof=\s*\/dev\/(sd|nvme|disk|hd|mmcblk)/i, why: 'dd на дисковое устройство' },
    { id: 'format-vol', re: /\bformat-volume\b|\bformat\s+[a-z]:\s|\bdiskpart\b[^\n]*\bclean\b|\bclear-disk\b/i, why: 'Format-Volume/format/diskpart clean' },
    // power
    { id: 'shutdown',   re: /\bshutdown\s+\/(s|r)\b|\bstop-computer\b|\brestart-computer\b/i, why: 'shutdown/Stop-Computer' },
    // fork bomb
    // span: сигнатура форк-бомбы САМА состоит из ; | & — по сегментам её не собрать.
    { id: 'fork-bomb',  span: true, re: /:\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:/, why: 'fork bomb' },
    // git destructive force-push to protected branches
    { id: 'git-force-main', re: /\bgit\s+push\b[^\n]*\s(--force\b|-f\b|--force-with-lease\b)[^\n]*\b(main|master|prod|production|release)\b/i, why: 'git push --force в main/master/prod' },
    { id: 'git-plus-main',  re: /\bgit\s+push\b[^\n]*\s\+(main|master|prod|production|release)\b/i, why: 'git push +refspec в защищённую ветку' },
    // git checkout/restore of the ENTIRE working tree (`.`) — discards all uncommitted edits
    { id: 'git-checkout-dot', re: /\bgit\s+(?:-C\s+\S+\s+)?(?:checkout|restore)\s+(?:(?!--)[\w@^~{}\/.:-]+\s+)?(?:--\s+)?\.["']?\s*(?:$|[;&|])/i, why: 'git checkout/restore -- . (сброс ВСЕХ незакоммиченных правок)' },
    // chattr recursive un-immutable (critical files may be chattr +i protected)
    { id: 'chattr-unimmute-R', re: /\bchattr\b(?=[^\n]*\s-[a-zA-Z]*R)[^\n]*\s-[a-zA-Z]*i/, why: 'chattr -R -i (рекурсивное снятие immutable-защиты)' },
    // PowerShell recursive-force delete of roots/home
    // Порядок аргументов в PowerShell свободный (`-Path C:\ -Recurse`), а цель
    // может упираться в закрывающую кавычку (`"… C:\"`) — поэтому флаги ищутся
    // отдельным lookahead'ом, а к границам цели добавлены кавычки.
    { id: 'ps-remove-root', re: /\b(?:remove-item|ri|rm|del|erase)\b(?=[^\n]*\s-(?:recurse|force|r|f)\b)[^\n]*?(?:\bc:[\\/]?(?=\s|$|\*|["'])|\$env:(?:userprofile|systemdrive|homepath)\b|\$home\b|~[\\/](?=\s|$|["']))/i, why: 'Remove-Item -Recurse -Force корня/home' },
    { id: 'ps-rd-root',     re: /\b(rd|rmdir)\s+\/s\s+\/q\s+(c:\\?(\s|$)|%userprofile%|"?c:\\)/i, why: 'rd /s /q корня/home' },
    // registry hive delete
    { id: 'reg-del-hive', re: /\breg\s+delete\s+(hk(lm|cu|cr|u|cc)\b|hkey_)/i, why: 'reg delete ветки реестра' },
    // chmod -R on root/home
    { id: 'chmod-root', re: /\bchmod\s+(-[a-z]*\s+)*-[a-z]*r[a-z]*\s+[^\n]*\s(\/(\s|$)|~(\/(\s|$)|\s|$)|\$\{?home\}?(\s|$))/i, why: 'chmod -R на корень/home' },
    // download|execute (remote code exec)
    // span: правило-конвейер — обязано видеть строку целиком (улика в связке
    // «скачать | исполнить», разрезание по | её уничтожает).
    { id: 'curl-pipe-exec', span: true, re: new RegExp('\\b(curl|wget|iwr|invoke-webrequest)\\b[^\\n]*(\\||;|&&)\\s*' + SHWRAP + SHPFX + '(sh|bash|zsh|iex\\b|invoke-expression\\b|python3?\\b|node\\b|perl\\b)\\b', 'i'), why: 'скачать-и-исполнить (curl|sh)' },
    // === 2026-07-31 infra-destruction (снос работающего окружения) ===
    { id: 'docker-rm-force', re: new RegExp(DKR + 'rm\\b(?=[^\\n;&|]*\\s(?:-[a-zA-Z]*f[a-zA-Z]*|--force)\\b)', 'i'),
      why: 'docker rm -f/--force — принудительное удаление контейнера' },
    { id: 'docker-mass-wipe', re: /\bdocker\b[^\n]*\s(?:rm|stop|kill)\b[^\n]*(?:\$\(|`)\s*docker\s+ps\b/i,
      why: 'docker rm/stop/kill $(docker ps ...) — массовый снос ВСЕХ контейнеров' },
    { id: 'compose-down-volumes', re: new RegExp(DKRC + 'compose\\b[^\\n;&|]*\\sdown\\b[^\\n;&|]*\\s(?:-[a-zA-Z]*v[a-zA-Z]*|--volumes)\\b', 'i'),
      why: 'docker compose down -v/--volumes — удаление томов = ПОТЕРЯ ДАННЫХ' },
    // Голый `compose down` — ежедневная операция разработки: останавливает стек,
    // тома НЕ трогает, поднимается обратно одной командой. Блокировать его значит
    // мешать работе каждый день ради предотвращения обратимого действия. Опасен
    // именно вариант с томами — он выше, и он остаётся заблокированным.
    { id: 'docker-volume-rm', re: new RegExp(DKR + 'volume\\s+(?:rm|remove)\\b', 'i'),
      why: 'docker volume rm — удаление тома с данными' },
    // Так же с очисткой: образы и слои сборки перекачиваются и пересобираются,
    // а тома — нет. Поэтому режем только те очистки, что уносят данные.
    { id: 'docker-prune', re: new RegExp(DKR + '(?:system|volume)\\s+prune\\b', 'i'),
      why: 'docker system/volume prune — удаление томов с данными' },
    { id: 'docker-prune-vol', re: new RegExp(DKR + '\\w+\\s+prune\\b[^\\n;&|]*--volumes\\b', 'i'),
      why: 'docker prune --volumes — удаление томов с данными' },
    { id: 'pm2-delete', re: /\bpm2(?:\.exe)?\s+(?:(?:-[a-zA-Z]|--[a-z][\w-]*)(?:[=\s]+[^\s;&|]+)?\s+)*(?:delete|del|kill)\b/i,
      why: 'pm2 delete/kill — снятие процесса с продакшена' },
    { id: 'systemctl-stop', re: /\bsystemctl\b(?:\s+--?[\w][\w=.:@-]*)*\s+(?:stop|disable)\b/i,
      why: 'systemctl stop/disable — остановка/отключение системного сервиса' },
    { id: 'service-stop', re: /\bservice\s+[\w.@-]+\s+stop\b/i,
      why: 'service ... stop — остановка системного сервиса' },
    { id: 'kubectl-delete', re: /\bkubectl\b[^\n;&|]*\sdelete(?=\s|$)/i,
      why: 'kubectl delete — удаление ресурсов кластера' },
    // === dcg-port 2026-07-19: interpreter fs-nuke sinks ===
    // Эти паттерны совпадают в КОДЕ интерпретаторной нагрузки: однословный
    // закавыченный путь-цель вклеен обратно, поэтому вызов rmtree с корнем,
    // /home или системной папкой в аргументе виден. Субпути вида ./build — PASS.
    { id: 'interp-rmtree-root', re: new RegExp('\\b(?:shutil\\.rmtree|os\\.removedirs|FileUtils\\.rm_rf|FileUtils\\.rm_r|(?:File::Path::)?remove_tree|rmtree)\\s*\\(\\s*(?:r|rb|b)?["\'](?:\\/(?!tmp\\b)[a-z]{0,12}|\\/home\\/[\\w.-]+|~|[a-z]:\\\\{0,4}|' + HOMEfwdEsc + ')\\/?["\']', 'i'), why: 'shutil.rmtree/rm_rf/remove_tree корня, /home или системной папки (python/ruby/perl payload)', txt: true },
    { id: 'js-fs-rm-root', re: new RegExp('\\.\\s*rm(?:Sync|dirSync|dir)?\\s*\\(\\s*["\'](?:\\/(?!tmp\\b)[a-z]{0,12}|\\/home\\/[\\w.-]+|~|[a-z]:\\\\{0,4}|' + HOMEfwdEsc + ')\\/?["\']', 'i'), why: 'fs.rmSync/rmdir корня, /home или системной папки (node payload)', txt: true },
    // decode-and-execute (obfuscated payload — content invisible, execution intent explicit)
    // Список декодеров был перечислимым (base64/openssl/xxd) — любой другой
    // трансформер в конвейере к шеллу проходил: `printf '\162\155…' | sh`,
    // `echo … | tr … | sh`. Хвост сужен до ГОЛОГО шелла в конце конвейера,
    // иначе под правило попал бы обычный `cat data | tr -d '\r' | python x.py`.
    //
    // 2026-08-18 (состязательный прогон): якорь printf был слишком узким —
    // требовал бэкслеш-код В ПЕРВОМ закавыченном токене сразу после `printf `.
    // Пролезали: `printf $'\162…' | sh` ($ перед кавычкой ломал `printf\s+["']`)
    // и `printf '%b' '\162…' | sh` (коды во ВТОРОМ аргументе). Гарду не нужно
    // ДЕКОДИРОВАТЬ payload — достаточно факта «printf с бэкслеш-октал/hex кодом
    // где-либо в аргументах, уходящий в шелл» = блок. Ключ: `\\[0-7x]` обязан
    // стоять ДО конвейера (класс [^\n|] не пускает за `|`), а хвост по-прежнему
    // требует голый sh/bash в конце — printf со спецификатором (`%s\n`) без
    // октал/hex кода или без трубы к шеллу не матчится (n∉[0-7x], трубы нет).
    { id: 'obfus-pipe-exec', span: true,
      re: new RegExp('\\b(?:base32\\s+(?:-d|--decode)|uudecode|rev|tr\\s+[^\\n|]{1,80}|gunzip|zcat|bzcat|xzcat|gzip\\s+-d|printf\\b[^\\n|]*\\\\[0-7x])[^\\n|]*\\|\\s*(?:[^|\\n]{0,80}\\|\\s*)?' + SHWRAP + SHPFX + '(?:sh|bash|zsh|dash|ksh)\\b(?:\\s+-\\w+)*\\s*(?:$|[;&|\\n])', 'i'),
      why: 'обфусцированный конвейер в шелл (printf/tr/rev/… | sh)' },
    { id: 'decode-pipe-exec', span: true, re: new RegExp('\\b(?:base64\\s+(?:-d|--decode)|openssl\\s+enc\\s+[^\\n|]*-d|xxd\\s+-r)[^\\n|]*\\|\\s*' + SHWRAP + SHPFX + '(?:sh|bash|zsh|dash|iex|invoke-expression|python[\\w.]*|node(?:js)?|perl|ruby)\\b', 'i'), why: 'декодировать-и-исполнить (base64 -d | sh)' },
    { id: 'eval-download-decode', re: /\beval\b[^\n]*\$\([^)\n]*\b(?:base64|curl|wget)\b/i, why: 'eval $(base64/curl/wget ...) — исполнение декодированного/скачанного кода' },
    // pipe-to-shell variations beyond curl|sh
    { id: 'proc-subst-exec', re: /\b(?:sh|bash|zsh|dash|ksh)\s+(?:-\S+\s+)*<\(\s*(?:curl|wget)\b/i, why: 'bash <(curl ...) — исполнение скачанного через process substitution' },
    { id: 'shell-c-download', re: /\b(?:sh|bash|zsh|dash|ksh)\b[^\n]*\s-[a-z]*c[a-z]*\s+["']?\$\([^)\n]*\b(?:curl|wget)\b/i, why: 'sh -c "$(curl ...)" — исполнение скачанного через command substitution' },
    // Тот же случай, но увиденный уже ИЗНУТРИ: содержимое кавычек вырезано
    // токенизатором, поэтому предыдущее правило на коде не срабатывает —
    // зато нагрузка `$(curl ...)` приходит в скан отдельной строкой, и там
    // подстановка стоит в позиции команды, т.е. её вывод будет исполнен.
    { id: 'subst-download-exec', re: /^\s*["']?\$\(\s*(?:curl|wget|iwr|invoke-webrequest)\b/i, why: 'исполнение вывода curl/wget через $(...) в позиции команды' },
    // disk signature wipe + Windows restore-point destruction
    { id: 'wipefs', re: /\bwipefs\s+(?:-[a-z]*a[a-z]*|--all)\b/i, why: 'wipefs -a — стирание сигнатур ФС' },
    { id: 'shadowcopy-delete', re: /\bvssadmin\b[^\n]*\bdelete\s+shadows\b|\bwmic\b[^\n]*\bshadowcopy\b[^\n]*\bdelete\b/i, why: 'удаление Volume Shadow Copies (уничтожение точек восстановления)' },
  ];

  // Правила, осмысленные только внутри КОДА интерпретатора (python/node/…):
  // вызов rmtree/fs.rmSync с корнем. Помечены флагом txt.
  const INTERP_ONLY = new Set(P.filter(p => p.txt).map(p => p.id));

  // Скан одной ИСПОЛНЯЕМОЙ строки набором правил.
  // opts.noSql — SQL-слова здесь данные (литералы интерпретатора), не команда;
  //              для настоящего SQL-канала (psql -c, sql-heredoc) не ставится.
  // opts.only  — ограничить набор правил этими id (код интерпретатора: там
  //              «mkfs» или «drop table» в литерале — просто слово, а вот
  //              rmtree('/') — реальный вызов).
  //
  // Порядок важен: сначала конвейерные (span) правила по строке целиком,
  // затем — посегментно, пропуская сегменты-показывалки. Именно вторая часть
  // отделяет НАМЕРЕНИЕ от ТЕКСТА: `grep 'mkfs' ops.md` — один сегмент, и он
  // только ищет по файлу; `echo ok && rm -rf /` — два сегмента, и второй
  // показывалкой не является.
  // `docker run -v /:/host alpine rm -rf /host` стирает РЕАЛЬНЫЙ хост, а для
  // правил это «rm субпапки /host» — корень спрятан за псевдонимом монтирования.
  // Правило узкое нарочно: одного монтирования корня мало (бывают легитимные
  // backup/rescue-контейнеры) — нужен И корень в источнике, И удаление точки
  // монтирования в ТОМ ЖЕ сегменте.
  const ROOTSRC = /^(?:\/|~|\$\{?HOME\}?|[A-Za-z]:[\\/]?)$/;
  function mountAliasHit(seg) {
    if (!/\bdocker(?:\.exe)?\b/i.test(seg) || !/(?:-v|--volume|--mount)\b/i.test(seg)) return null;
    const dests = [];
    let m;
    const vre = /(?:-v|--volume)[=\s]+["']?([^\s:"']{0,80}):([^\s:,"']{1,80})/gi;
    while ((m = vre.exec(seg)) !== null && dests.length < 8) if (ROOTSRC.test(m[1])) dests.push(m[2]);
    const mre = /--mount[=\s]+["']?([^\s"']{1,160})/gi;
    while ((m = mre.exec(seg)) !== null && dests.length < 8) {
      const src = /(?:^|,)(?:src|source)=([^,]+)/i.exec(m[1]);
      const dst = /(?:^|,)(?:dst|destination|target)=([^,]+)/i.exec(m[1]);
      if (src && dst && ROOTSRC.test(src[1])) dests.push(dst[1]);
    }
    for (const d of dests) {
      const esc = d.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      if (new RegExp(RM + '["\']?' + esc + '(?:\\/\\*?|\\*)?["\']?(?:\\s|$|;|&|\\|)', 'i').test(seg)) {
        return { id: 'docker-mount-root-rm', why: 'docker run -v ' + ' корня в контейнер + rm точки монтирования (' + d + ') — стирание ХОСТА' };
      }
    }
    return null;
  }

  function findHit(str, opts) {
    opts = opts || {};
    const only = opts.only || null;
    const noSql = !!opts.noSql;
    for (const p of P) {
      if (!p.span) continue;
      if (only && !only.has(p.id)) continue;
      if (noSql && p.sql) continue;
      if (p.re.test(str)) return p;
    }
    for (const seg of str.split(SEP_RE)) {
      if (!seg.trim()) continue;
      if (TEXTDISP.test(seg)) continue;
      if (!only) { const mh = mountAliasHit(seg); if (mh) return mh; }
      for (const p of P) {
        if (p.span) continue;
        if (only && !only.has(p.id)) continue;
        if (noSql && p.sql) continue;
        if (p.re.test(seg)) return p;
      }
    }
    return null;
  }

  // ===== 2026-08-17: шелл-токенизатор (приближённый, bash-флейвор) =====
  // Возвращает { code, dq[], sq[], heredocs[{tag,body}] }.
  // code = команда МИНУС содержимое кавычек, тела heredoc и #-комментарии.
  // Однословный закавыченный токен (нет пробелов и ;&|<>()`"' — метасимволов,
  // которые сделали бы его НЕ одним словом-целью) вклеивается обратно вместе
  // с кавычками: `rm -rf "/"`, `rm -rf "$HOME"`, `"mkfs.ext4" /dev/sda`,
  // `git push --force origin "main"` остаются видимыми паттернам с Q-бэкрефом.
  // Многословное содержимое ("DROP TABLE users", прозаический текст) — данные,
  // в code остаётся пустая пара кавычек.
  const SIMPLE_TOKEN = /^[^\s;&|<>()`"']{1,128}$/;
  function tokenize(str) {
    let code = '';
    const dq = [], sq = [], heredocs = [];
    const pending = []; // heredoc-теги, ждущие тела после ближайшего невзятого в кавычки \n
    let i = 0;
    const n = str.length;
    while (i < n) {
      const c = str[i];
      if (c === '\\') { code += c + (str[i + 1] || ''); i += 2; continue; }
      if (c === "'") {
        let j = i + 1, buf = '';
        while (j < n && str[j] !== "'") { buf += str[j]; j++; }
        sq.push(buf);
        code += SIMPLE_TOKEN.test(buf) ? "'" + buf + "'" : "''";
        i = j + 1; continue;
      }
      if (c === '"') {
        let j = i + 1, buf = '';
        while (j < n && str[j] !== '"') {
          if (str[j] === '\\' && j + 1 < n) { buf += str[j] + str[j + 1]; j += 2; continue; }
          buf += str[j]; j++;
        }
        const un = buf.replace(/\\(["\\$`])/g, '$1');
        dq.push(un);
        code += SIMPLE_TOKEN.test(un) ? '"' + un + '"' : '""';
        i = j + 1; continue;
      }
      // Комментарий: невзятый в кавычки # в начале слова — до конца строки.
      // (`foo#bar` — не комментарий, поэтому требуем границу слева.)
      if (c === '#' && (code === '' || /[\s;&|(]$/.test(code))) {
        while (i < n && str[i] !== '\n') i++;
        continue;
      }
      // Heredoc-оператор <<[-~]? ['"]TAG['"] (но не herestring <<<)
      if (c === '<' && str[i + 1] === '<' && str[i + 2] !== '<') {
        const m = /^<<[-~]?\s*(["']?)([A-Za-z_]\w*)\1/.exec(str.slice(i));
        if (m) { pending.push(m[2]); code += str.slice(i, i + m[0].length); i += m[0].length; continue; }
        code += '<<'; i += 2; continue;
      }
      // Конец командной строки: если объявлены heredoc'и — забрать их тела.
      if (c === '\n' && pending.length) {
        code += '\n'; i++;
        while (pending.length) {
          const tag = pending.shift();
          let body = '', done = false;
          while (i < n) {
            let eol = str.indexOf('\n', i);
            if (eol === -1) eol = n;
            const line = str.slice(i, eol);
            i = (eol === n) ? n : eol + 1;
            if (line.replace(/^\t+/, '').replace(/\r$/, '') === tag) { done = true; break; }
            body += line + '\n';
          }
          heredocs.push({ tag, body });
          if (!done) break; // незакрытый heredoc: остаток съеден как тело
        }
        continue;
      }
      code += c; i++;
    }
    return { code, dq, sq, heredocs };
  }

  // Закавыченные сегменты строки (для exec-стоков внутри интерпретаторного кода).
  function extractQuoted(str) {
    const out = [];
    const dq2 = str.match(/"(?:[^"\\]|\\.)*"/g) || [];
    for (const seg of dq2) out.push(seg.slice(1, -1).replace(/\\(["\\$`])/g, '$1'));
    const sq2 = str.match(/'[^']*'/g) || [];
    for (const seg of sq2) out.push(seg.slice(1, -1));
    return out;
  }

  // Исполнители полезной нагрузки. Триггеры проверяются по КОДУ (не по сырой
  // строке): упоминание "ssh"/"psql" внутри литерала исполнителем не является.
  //
  // 2026-08-18 (состязательный прогон): якорь исполнителя был слишком строгим —
  // имя требовалось в начале строки или сразу после разделителя. `sh -c "…"`
  // и `; sh -c "…"` блокировались, а `timeout 5 sh -c "…"`, `sudo sh -c "…"`,
  // `/bin/sh -c "…"`, `docker exec app sh -c "…"` — нет: имя выпадало из
  // триггер-позиции, нагрузка в кавычках не сканировалась вовсе (15 из 22
  // пролезших разрушителей той партии). Лечение — не «любое слово перед sh»
  // (тогда исполнителем стало бы что угодно), а ЗАКРЫТЫЙ список обёрток,
  // которые сами ничего не делают, а лишь запускают следующий аргумент,
  // плюс необязательный путь до имени.
  // ВАЖНО не путать с TEXTDISP: там список нужен, чтобы ПРОПУСТИТЬ сегмент, и
  // xargs/env/sudo в нём смертельны. Здесь наоборот — список нужен, чтобы НАЙТИ
  // исполнителя за обёрткой, то есть проверить БОЛЬШЕ, а не меньше.
  const CMDSTART = '(?:^|[;&|(]\\s*|\\$\\(\\s*)';
  const WRAPWORD = '(?:sudo|doas|env|nohup|timeout|stdbuf|setsid|command|exec|nice|ionice|time|unbuffer|proxychains4?|xargs|wsl|winpty|script|runuser|su)';
  const WRAPARGS = '(?:\\s+[^\\s;&|]{1,64}){0,6}';   // -u user, 5, -I{}, VAR=val
  const WRAP =
    '(?:(?:' + WRAPWORD + WRAPARGS +
    '|docker(?:\\.exe)?(?:\\s+[^\\s;&|]{1,64}){0,4}\\s+exec(?:\\s+[^\\s;&|]{1,64}){0,6}' +
    '|kubectl(?:\\s+[^\\s;&|]{1,64}){1,8}\\s+--' +
    ')\\s+){0,3}';
  const PATHPFX  = '(?:[\\w.$~-]*\\/)*';             // /bin/sh, /usr/bin/env, ./run
  const SSH_TRIG    = new RegExp(CMDSTART + WRAP + PATHPFX + 'ssh(?:\\.exe)?\\s', 'i');
  // SQL-клиент + признак исполняемого SQL: -c/-e/-f/--command/--execute, heredoc
  // или закавыченный позиционный аргумент (sqlite3 "..."). Пустые пары кавычек
  // от вырезанных строк в code сохраняются — признак работает.
  // Mongo передаёт скрипт через --eval, а не -c/-e. Флаг и кавычку ищем по
  // отдельности (через lookahead), иначе жадный «всё до конца» съедал бы --eval
  // и mongo --eval 'db.dropDatabase()' не распознавался как SQL-клиент.
  // «mongosh?» — ловушка: на входе «mongo» движок берёт «mongos», ждёт опц. «h»,
  // упирается в «\b» после «mongos…o» и НЕ откатывается к «mongo». Нужна явная
  // альтернация, иначе `mongo --eval` (без sh) проходит мимо.
  const SQLCLI_NAME = /\b(?:psql|mysql|mariadb|sqlite3|sqlcmd|clickhouse-client|mongosh|mongo)(?:\.exe)?\b/i;
  const SQLCLI_TRIG = new RegExp(SQLCLI_NAME.source +
    '(?=[^\\n;&|]*(?:\\s(?:-c|-e|-f|--command|--execute|--file|--eval)\\b|<<|["\']))', 'i');
  const SHELL_TRIG  = new RegExp(CMDSTART + WRAP + PATHPFX +
    '(?:bash|zsh|dash|ksh|sh|eval)(?:\\.exe)?\\s+(?:(?:-\\S*|--\\S+)\\s+)*(?:-[a-zA-Z]*c[a-zA-Z]*(?:\\s|$|["\'])|<<|["\'])', 'i');
  const INTERP_TRIG = new RegExp(CMDSTART + WRAP + PATHPFX +
    '((?:python|perl|node(?:js)?|ruby|php)[\\w.]*)(?:\\.exe)?\\s+(?:(?:-\\S*|--\\S+)\\s+)*(?:-[a-zA-Z]*[ce][a-zA-Z]*(?:\\s|$|["\'])|<<)', 'i');
  // PowerShell — основной шелл этой машины, и хук ловит его наравне с Bash,
  // но разбиралась только форма -EncodedCommand. Нативный
  // `powershell -Command "Remove-Item -Recurse -Force C:\"` уходил в кавычки
  // и не сканировался ничем. Нагрузка -Command/-c = команды PowerShell.
  const PS_TRIG     = new RegExp(CMDSTART + WRAP + PATHPFX +
    '(?:powershell|pwsh)(?:\\.exe)?(?=[^\\n]*\\s[-\\/](?:c|command)\\b)', 'i');
  const IEX_TRIG    = /\b(?:iex|invoke-expression)\b/i;   // eval PowerShell'а
  // Exec-стоки: только при их наличии строки-литералы интерпретаторного кода
  // сканируются как команды. Литералы без стока — данные (доказанный случай: анализ-скрипт с опасными словами в строках, стоков нет).
  const SINK_RE     = /\b(?:os\.system|subprocess\.\w+|popen|proc_open|shell_exec|passthru|exec(?:v[pe]*|l[pe]*|Sync|File)?\s*\(|spawn(?:Sync)?\s*\(|child_process|Runtime\.getRuntime|IO\.popen|Kernel\.(?:system|exec)|system\s*\()/i;
  const SINK_ARGS   = /\b(?:os\.system|subprocess\.\w+|popen|proc_open|shell_exec|passthru|exec\w*|spawn\w*|IO\.popen|system)\s*\(([^)\n]*)/gi;

  function tagHit(h, suffix, note) { return { id: h.id + suffix, why: h.why + ' — ' + note }; }

  // Нагрузка интерпретатора (python/node/perl/ruby/php): это КОД, не шелл.
  // 1) его собственный код (минус литералы) — ловит вызовы rmtree корня и т.п.;
  // 2) литералы — ТОЛЬКО из аргументов exec-стоков (os.system/subprocess/...).
  function scanInterpreterPayload(p, interpName) {
    const pt = tokenize(p);
    // Код интерпретатора — НЕ шелл: `mkfs`, `drop table`, `shutdown` внутри него
    // это слова языка или литералы, а не команды. Поэтому здесь работает только
    // узкий набор INTERP_ONLY — вызовы, которые сносят ФС средствами самого
    // языка (rmtree('/'), fs.rmSync('/')). Всё остальное опасное в скриптовом
    // коде обязано пройти через exec-сток — он проверяется ниже.
    let h = findHit(pt.code, { noSql: true, only: INTERP_ONLY });
    if (h) return tagHit(h, '@inline', 'код интерпретатора (' + interpName + ')');
    let m;
    SINK_ARGS.lastIndex = 0;
    while ((m = SINK_ARGS.exec(p)) !== null) {
      const quoted = extractQuoted(m[1]);
      // Список-форма (subprocess.run(["rm","-rf","/"])) разложена на отдельные
      // литералы — по одному они безобидны, поэтому проверяется и склейка.
      const candidates = quoted.length > 1 ? quoted.concat([quoted.join(' ')]) : quoted;
      for (const s of candidates) {
        h = findHit(s, { noSql: true });
        if (h) return tagHit(h, '@inline', 'строка в exec-стоке (' + m[0].slice(0, 30) + '...)');
      }
    }
    // perl/ruby: `...` — исполнение шеллом
    if (/^(perl|ruby)/i.test(interpName)) {
      for (const bt of (p.match(/`([^`]*)`/g) || [])) {
        h = findHit(bt.slice(1, -1));
        if (h) return tagHit(h, '@inline', 'backtick-команда в ' + interpName);
      }
    }
    return null;
  }

  // ===== 2026-08-18: снятие обфускации (второй, отдельный проход) ===========
  // Состязательный прогон показал класс, который токенизатор не закрывает:
  // bash раскрывает кавычки, экранирование, $'…', ${IFS}, $(echo …) и
  // переменные ДО исполнения, а гард видит исходный текст. `r\m -rf /`,
  // `"r"m -rf /`, `X=rm; $X -rf /`, `X=/; rm -rf $X` исполнялись как удаление
  // корня, но в тексте команды подстроки «rm … /» просто нет.
  //
  // Лечение — не ослабление правил, а ВТОРОЙ прогон по нормализованной копии:
  // приводим текст к тому, что увидит шелл после раскрытия, и сканируем ещё
  // раз тем же набором. Копия нужна именно отдельная: нормализация огрубляет
  // (снимает кавычки внутри слов), и делать её основным взглядом нельзя.
  // Полную раскрутку $(…) воспроизвести нельзя без интерпретатора — см. ГРАНИЦЫ.
  const EXPAND_LIMIT = 16384;
  function decodePrintfEscapes(s) {
    return s.replace(/\\([0-7]{1,3})/g, (_, o) => String.fromCharCode(parseInt(o, 8)))
            .replace(/\\x([0-9a-fA-F]{2})/g, (_, x) => String.fromCharCode(parseInt(x, 16)));
  }
  function expandRaw(str) {
    if (str.length > EXPAND_LIMIT) return str;
    let s = str;
    // склейка литералов: 'Remove-I' + 'tem' → 'Remove-Item' (PowerShell/JS-обфускация)
    s = s.replace(/(['"])\s*\+\s*\1/g, '');
    // $(echo X) / `echo X` / $(printf 'X') — самые ходовые «сборщики слова»
    s = s.replace(/\$\(\s*echo\s+(?:-[neE]+\s+)?([^()`;&|]{0,120}?)\s*\)/gi, '$1');
    s = s.replace(/`\s*echo\s+(?:-[neE]+\s+)?([^`;&|]{0,120}?)\s*`/gi, '$1');
    s = s.replace(/\$\(\s*printf\s+(['"])([^'"\n]{0,120})\1\s*\)/gi, (_, q, body) => decodePrintfEscapes(body));
    // $'rm' — ANSI-C кавычки дают ровно одно слово, кавычки можно снять
    s = s.replace(/\$'([^'\s;&|]{0,64})'/g, '$1');
    // ${IFS} — классический разделитель-невидимка; $@/$* обычно пусты
    s = s.replace(/\$\{IFS\}|\$IFS\b/g, ' ');
    s = s.replace(/\$\{[@*]\}|\$[@*]/g, '');
    // кавычки ВНУТРИ слова: "r"m, r""m, r''m → rm. Содержимое с пробелами
    // не трогаем — иначе вернётся исходный дефект (текст станет кодом).
    s = s.replace(/(\w)(['"])([^'"\s;&|]{0,64})\2/g, '$1$3');
    s = s.replace(/(['"])([^'"\s;&|]{0,64})\1(?=\w)/g, '$2');
    // экранирование внутри слова: r\m → rm
    s = s.replace(/\\([A-Za-z0-9])/g, '$1');
    // простые присваивания: X=rm; $X -rf /   ·   X=/; rm -rf ${X}
    const vars = new Map();
    const asg = /(?:^|[;&|\s(])([A-Za-z_]\w{0,31})=([^\s;&|"'`$]{0,64})(?=\s|$|[;&|])/g;
    let m, guard = 0;
    while ((m = asg.exec(s)) !== null && guard++ < 24) vars.set(m[1], m[2]);
    if (vars.size) {
      s = s.replace(/\$\{([A-Za-z_]\w{0,31})\}|\$([A-Za-z_]\w{0,31})/g,
        (whole, a, b) => { const k = a || b; return vars.has(k) ? vars.get(k) : whole; });
    }
    return s;
  }

  // Снятие PowerShell-обфускации для payload'ов iex/-Command. Отдельно от
  // expandRaw, потому что применяется ТОЛЬКО к PS-нагрузке: глобально трогать
  // backtick нельзя — в bash `...` это подстановка команды, а не экранирование.
  // Два приёма из состязательного прогона:
  //   1) склейка литералов через + :  'Remove-It' + 'em … C:'  → 'Remove-Item … C:'
  //      (в т.ч. цепочки 'a'+'b'+'c' и смешанные кавычки 'a'+"b");
  //   2) backtick-экранирование имени:  R`emove-Item  →  Remove-Item
  //      (PowerShell снимает ` перед символом; для нас это разрывало слово-команду
  //      и правило ps-remove-root не срабатывало).
  // Результат сканируется findHit'ом БЕЗ ре-токенизации: деструктивная команда
  // живёт внутри кавычек, отдаваемых iex, — токенизатор счёл бы её данными,
  // но iex её ИСПОЛНЯЕТ. Гейт TEXTDISP в findHit по-прежнему отделяет
  // показывалки (Write-Output '…') от исполнения (iex '…').
  function psDeobf(s) {
    let out = s, prev, guard = 0;
    do {
      prev = out;
      out = out.replace(/(['"])([^'"]*)\1\s*\+\s*(['"])([^'"]*)\3/g, (_, q, a, __, b) => q + a + b + q);
      out = out.replace(/`(.)/g, '$1');
    } while (out !== prev && ++guard < 20);
    return out;
  }

  // ===== 2026-08-18 (второй состязательный прогон): пробел в printf-аргументе ==
  // obfus-pipe-exec — span-правило, проверяемое по t.code (после токенизации).
  // Токенизатор вырезает ЛЮБОЙ многословный закавыченный токен в '' ДО того, как
  // правило увидит октал/hex-коды. Пробел внутри аргумента делает токен
  // многословным — и `printf 'rm -rf \057' | sh` (шелл печатает "rm -rf /" и
  // отдаёт sh) проходил: коды исчезали из t.code вместе с кавычкой. Проба
  // 2026-08-18: пролезло 5 форм с литеральным пробелом.
  //
  // Тестировать сырую строку целиком нельзя — вернётся дефект 17.08:
  // `echo "printf '\162' | sh"` (данные в echo) заблокировался бы ложно.
  // Отличие настоящего разрушителя: труба к ГОЛОМУ шеллу НЕ закавычена. Поэтому
  // режем сырую строку по НЕВЗЯТЫМ в кавычки трубам (splitPipesRaw, bash-правила
  // кавычек) и требуем И стадию-producer `printf … \NNN/\xNN` (коды берём из
  // СЫРОГО текста стадии — там кавычки целы), И следующую стадию, начинающуюся
  // с голого sh/bash/zsh/dash/ksh. В echo-данных труба внутри кавычек не режет —
  // стадия одна, sink-стадии нет, ложного блока нет.
  function splitPipesRaw(str) {
    const stages = [];
    let cur = '', q = null;
    for (let i = 0; i < str.length; i++) {
      const c = str[i];
      if (q === "'") { cur += c; if (c === "'") q = null; continue; }   // в '' backslash литерал
      if (c === '\\') { cur += c + (str[i + 1] || ''); i++; continue; }
      if (q === '"') { cur += c; if (c === '"') q = null; continue; }
      if (c === "'" || c === '"') { q = c; cur += c; continue; }
      if (c === '|' && str[i + 1] !== '|' && str[i - 1] !== '|') { stages.push(cur); cur = ''; continue; }
      cur += c;
    }
    stages.push(cur);
    return stages;
  }
  const BARE_SHELL_SINK = new RegExp('^\\s*' + SHWRAP + SHPFX + '(?:sh|bash|zsh|dash|ksh)\\b', 'i');
  const PRINTF_ENC_STAGE = /\bprintf\b[^\n]*?\\(?:[0-7]|x[0-9a-fA-F])/i;
  function printfEncPipeShell(str) {
    const stages = splitPipesRaw(str);
    if (stages.length < 2) return false;
    let sawEnc = false;
    for (const stage of stages) {
      if (sawEnc && BARE_SHELL_SINK.test(stage)) return true;
      if (PRINTF_ENC_STAGE.test(stage)) sawEnc = true;
    }
    return false;
  }

  // Рекурсивный скан: код → каналы-исполнители. Глубина ≤ 3 (bash -c "ssh ...").
  function scanCommand(cmdStr, depth) {
    if (depth > 3 || typeof cmdStr !== 'string' || !cmdStr.trim()) return null;
    const t = tokenize(cmdStr);

    // 1) Исполняемый код команды
    let h = findHit(t.code);
    if (h) return h;

    // 1b) printf-энкодинг с пробелом в аргументе: токенизатор стёр коды из t.code,
    //     но труба к голому шеллу настоящая (см. printfEncPipeShell выше).
    if (printfEncPipeShell(cmdStr)) {
      return { id: 'obfus-pipe-exec', why: 'обфусцированный конвейер в шелл (printf с бэкслеш-кодом и пробелом | sh)' };
    }

    // 2) $(...) и `...` внутри ДВОЙНЫХ кавычек шелл исполняет (в одинарных — нет)
    for (const s of t.dq) {
      for (const sub of (s.match(/\$\(([^()]*)\)/g) || [])) {
        h = scanCommand(sub.slice(2, -1), depth + 1);
        if (h) return tagHit(h, '@subst', 'внутри $(...) в двойных кавычках');
      }
      for (const bt of (s.match(/`([^`]*)`/g) || [])) {
        h = scanCommand(bt.slice(1, -1), depth + 1);
        if (h) return tagHit(h, '@subst', 'внутри `...` в двойных кавычках');
      }
    }

    const strings = t.dq.concat(t.sq);

    // 3) ssh: нагрузка исполняется удалённым шеллом (your-server = 44 prod-контейнера)
    if (SSH_TRIG.test(t.code)) {
      const payloads = strings.slice();
      const m = cmdStr.match(/\bssh\s+(?:-[a-zA-Z]\S*\s+)*(?:\S+@)?[\w.\-]+\s+([\s\S]+)$/);
      if (m) payloads.push(m[1]);
      for (const s of payloads) {
        h = scanCommand(s, depth + 1);
        if (h) return tagHit(h, '@ssh', 'внутри ssh-команды (удалённый хост!)');
      }
    }

    // 4) SQL-клиент: его аргумент/heredoc — ИСПОЛНЯЕМЫЙ SQL (sql-паттерны активны)
    if (SQLCLI_TRIG.test(t.code)) {
      for (const s of strings) {
        h = findHit(s);
        if (h) return tagHit(h, '@sqlcli', 'аргумент SQL-клиента (psql/mysql/sqlite3)');
      }
      for (const hd of t.heredocs) {
        h = findHit(hd.body);
        if (h) return tagHit(h, '@sqlcli', 'heredoc, скормленный SQL-клиенту');
      }
    }

    // 5) bash|sh -c / eval / shell-heredoc: нагрузка = КОМАНДЫ (рекурсивный скан)
    if (SHELL_TRIG.test(t.code)) {
      for (const s of strings) {
        h = scanCommand(s, depth + 1);
        if (h) return tagHit(h, '@inline', 'payload шелла (-c/eval/heredoc)');
      }
      for (const hd of t.heredocs) {
        h = scanCommand(hd.body, depth + 1);
        if (h) return tagHit(h, '@inline', 'shell-heredoc');
      }
    }

    // 6) python/node/perl/ruby/php -c/-e/heredoc: нагрузка = код интерпретатора
    const im = INTERP_TRIG.exec(t.code);
    if (im) {
      const payloads = strings.concat(t.heredocs.map(x => x.body));
      for (const p of payloads) {
        h = scanInterpreterPayload(p, im[1]);
        if (h) return h;
      }
    }

    // 7) powershell/pwsh -Command "…" и iex '…': нагрузка = команды PowerShell.
    //    iex — это eval PowerShell'а, и без него `iex('Remove-It' + 'em … C:\')`
    //    прятал нагрузку во вложенной строке. Каждый payload проверяется дважды:
    //    scanCommand (уже развёрнутые/вложенные команды) И findHit(psDeobf(...)) —
    //    после снятия склейки 'a'+'b' и backtick-экранирования R`emove→Remove,
    //    без ре-токенизации (иначе команда внутри кавычек iex снова стала бы
    //    «данными»). psDeobf добавляет то, чего expandRaw не умеет — backtick.
    const scanPS = (s, tag, note) => {
      let h = scanCommand(s, depth + 1);
      if (h) return tagHit(h, tag, note);
      const deob = psDeobf(s);
      if (deob !== s) { h = findHit(deob); if (h) return tagHit(h, tag, note + ' (деобфускация)'); }
      return null;
    };
    if (IEX_TRIG.test(t.code)) {
      for (const s of strings) {
        h = scanPS(s, '@iex', 'аргумент iex/Invoke-Expression');
        if (h) return h;
      }
    }
    if (PS_TRIG.test(t.code)) {
      for (const s of strings) {
        h = scanPS(s, '@ps', 'payload powershell -Command');
        if (h) return h;
      }
    }

    return null;
  }

  let hit = scanCommand(cmd, 0);

  // Второй взгляд — по копии со снятой обфускацией (см. expandRaw).
  if (!hit) {
    const ex = expandRaw(cmd);
    if (ex !== cmd) {
      const h = scanCommand(ex, 1);
      if (h) hit = tagHit(h, '@expand', 'после снятия обфускации (кавычки/экранирование/переменные)');
    }
  }

  // PowerShell -EncodedCommand: декодировать (UTF-16LE канон + UTF-8 fallback)
  // и прогнать через тот же рекурсивный скан. Не декодится => fail-open.
  if (!hit) {
    const enc = cmd.match(/\b(?:powershell|pwsh)(?:\.exe)?\b[^\n]*?\s[-\/](?:e|ec|en|enc|encodedcommand)[:\s]+["']?([A-Za-z0-9+\/=]{16,})/i);
    if (enc) {
      try {
        const buf = Buffer.from(enc[1], 'base64');
        for (const dec of [buf.toString('utf16le'), buf.toString('utf8')]) {
          const h = scanCommand(dec, 1);
          if (h) { hit = tagHit(h, '@encoded', 'внутри base64 -EncodedCommand'); break; }
        }
      } catch (e) { /* decode error => fail-open */ }
    }
  }

  if (hit) {
    try {
      const logDir = path.join(HOMEwin, '.claude', 'hooks-logs');
      fs.mkdirSync(logDir, { recursive: true });
      const day = new Date().toISOString().slice(0, 10);
      fs.appendFileSync(path.join(logDir, day + '.jsonl'),
        JSON.stringify({ ts: new Date().toISOString(), id: hit.id, why: hit.why, cmd: cmd.slice(0, 400) }) + '\n');
    } catch (e) { /* logging must never break the guard */ }
    process.stderr.write('BLOCKED by bash-guard [' + hit.id + ']: ' + hit.why +
      '. Команда заблокирована как деструктивная. Если осознанно и безопасно — CC_HOOKS_OFF=1 или уточни путь.');
    process.exit(2); // exit 2 = block PreToolUse
  }
  allow();
} catch (e) {
  allow(); // fail-open on any unexpected error
}
}

/* ==========================================================================
 * ТОЧКА ВХОДА — единственное, что здесь новое.
 * Раньше каждый хук читал stdin сам: bash-guard синхронно (fs.readFileSync(0)),
 * security-guard событиями с таймаутом 2 с. Оставлен синхронный приём —
 * он на один оборот цикла событий короче и уже отработал в проде, а на
 * стороне вызывающего stdin закрывается сразу.
 * ======================================================================== */
try {
  let raw = '';
  try { raw = fs.readFileSync(0, 'utf8'); } catch (e) { allow(); }
  if (!raw || !raw.trim()) allow();          // пустой stdin  -> пропуск

  let data; try { data = JSON.parse(raw); } catch (e) { allow(); } // битый JSON -> пропуск
  const tool = (data && data.tool_name) || '';

  if (tool === 'Write' || tool === 'Edit' || tool === 'MultiEdit') runSecurityGuard(data);
  else runBashGuard(data);   // Bash | PowerShell и всё, что придёт по матчеру
  allow();
} catch (e) {
  allow(); // fail-open on any unexpected error
}
