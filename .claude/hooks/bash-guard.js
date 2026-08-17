#!/usr/bin/env node
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
 * (the prod server runs dozens of containers — destroyers inside quotes were invisible).
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
 * 2026-08-17 intent-vs-text (замер владельца: `python - <<EOF`, внутри ТЕКСТА
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
 * ГРАНИЦЫ (осознанные):
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
 *    не разбирается (fail-open).
 *
 * Проверки: bash-guard.test.mjs рядом (36 команд + 5 контрактных).
 * Запуск: node bash-guard.test.mjs   ·   замер: node bash-guard.test.mjs --bench
 */
'use strict';
const fs = require('fs');
const path = require('path');

function allow() { process.exit(0); } // fail-open / no match

try {
  if (process.env.CC_HOOKS_OFF === '1') allow();

  let raw = '';
  try { raw = fs.readFileSync(0, 'utf8'); } catch (e) { allow(); }
  if (!raw || !raw.trim()) allow();

  let data; try { data = JSON.parse(raw); } catch (e) { allow(); }
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

  const P = [
    // Tier 1: root / home / drive roots (subpaths ALLOWED)
    { id: 'rm-root',    re: new RegExp(RM + Q + '(?:\\/|c:\\\\?|\\/c)' + TERM, 'i'), why: 'rm -rf корня / C:\\ / /c/' },
    { id: 'rm-home',    re: new RegExp(RM + Q + '(?:~|\\$\\{?home\\}?|\\$\\{?userprofile\\}?)' + TERM, 'i'), why: 'rm -rf $HOME/~' },
    { id: 'rm-homeabs', re: new RegExp(RM + Q + '(?:' + HOMEfwdEsc + '|' + HOMEbackEsc + ')' + TERM, 'i'), why: 'rm -rf домашней папки (абс. путь)' },
    // Tier 2: system dirs (dir AND subpaths blocked — не пользовательские данные)
    { id: 'rm-sysdir',  re: new RegExp(RM + Q + '\\/(?:etc|usr|bin|sbin|boot|lib|sys|dev|proc|root)(?:\\/\\S*?)?\\1(?:\\s|$|;|&|\\|)', 'i'), why: 'rm -rf системной папки (/etc,/usr,/bin,...)' },
    { id: 'find-delete-root', re: /\bfind\s+(\/|~|\$\{?home\}?)\s+.*-delete\b/i, why: 'find / -delete' },
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
    // chattr recursive un-immutable (fleet brains on the prod server are chattr +i protected)
    { id: 'chattr-unimmute-R', re: /\bchattr\b(?=[^\n]*\s-[a-zA-Z]*R)[^\n]*\s-[a-zA-Z]*i/, why: 'chattr -R -i (рекурсивное снятие immutable-защиты)' },
    // PowerShell recursive-force delete of roots/home
    { id: 'ps-remove-root', re: /remove-item\b[^\n]*-(recurse|force)\b[^\n]*(\bc:\\?(\s|$|\*)|\$env:userprofile|\$home\b|~[\\/](\s|$))/i, why: 'Remove-Item -Recurse -Force корня/home' },
    { id: 'ps-rd-root',     re: /\b(rd|rmdir)\s+\/s\s+\/q\s+(c:\\?(\s|$)|%userprofile%|"?c:\\)/i, why: 'rd /s /q корня/home' },
    // registry hive delete
    { id: 'reg-del-hive', re: /\breg\s+delete\s+(hk(lm|cu|cr|u|cc)\b|hkey_)/i, why: 'reg delete ветки реестра' },
    // chmod -R on root/home
    { id: 'chmod-root', re: /\bchmod\s+(-[a-z]*\s+)*-[a-z]*r[a-z]*\s+[^\n]*\s(\/(\s|$)|~(\/(\s|$)|\s|$)|\$\{?home\}?(\s|$))/i, why: 'chmod -R на корень/home' },
    // download|execute (remote code exec)
    // span: правило-конвейер — обязано видеть строку целиком (улика в связке
    // «скачать | исполнить», разрезание по | её уничтожает).
    { id: 'curl-pipe-exec', span: true, re: /\b(curl|wget|iwr|invoke-webrequest)\b[^\n]*(\||;|&&)\s*(sh|bash|zsh|iex\b|invoke-expression\b|python3?\b|node\b|perl\b)\b/i, why: 'скачать-и-исполнить (curl|sh)' },
    // === 2026-07-31 infra-destruction (снос работающего прода) ===
    { id: 'docker-rm-force', re: new RegExp(DKR + 'rm\\b(?=[^\\n;&|]*\\s(?:-[a-zA-Z]*f[a-zA-Z]*|--force)\\b)', 'i'),
      why: 'docker rm -f/--force — принудительное удаление контейнера' },
    { id: 'docker-mass-wipe', re: /\bdocker\b[^\n]*\s(?:rm|stop|kill)\b[^\n]*(?:\$\(|`)\s*docker\s+ps\b/i,
      why: 'docker rm/stop/kill $(docker ps ...) — массовый снос ВСЕХ контейнеров' },
    { id: 'compose-down-volumes', re: new RegExp(DKRC + 'compose\\b[^\\n;&|]*\\sdown\\b[^\\n;&|]*\\s(?:-[a-zA-Z]*v[a-zA-Z]*|--volumes)\\b', 'i'),
      why: 'docker compose down -v/--volumes — удаление томов = ПОТЕРЯ ДАННЫХ' },
    { id: 'compose-down', re: new RegExp(DKRC + 'compose\\b[^\\n;&|]*\\sdown(?=\\s|$|[;&|])', 'i'),
      why: 'docker compose down — остановка и удаление стека контейнеров' },
    { id: 'docker-volume-rm', re: new RegExp(DKR + 'volume\\s+(?:rm|remove)\\b', 'i'),
      why: 'docker volume rm — удаление тома с данными' },
    { id: 'docker-prune', re: new RegExp(DKR + '(?:system|volume|image|container|network|builder)\\s+prune\\b', 'i'),
      why: 'docker prune — массовое удаление контейнеров/томов/образов' },
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
    { id: 'decode-pipe-exec', span: true, re: /\b(?:base64\s+(?:-d|--decode)|openssl\s+enc\s+[^\n|]*-d|xxd\s+-r)[^\n|]*\|\s*(?:sh|bash|zsh|dash|iex|invoke-expression|python[\w.]*|node(?:js)?|perl|ruby)\b/i, why: 'декодировать-и-исполнить (base64 -d | sh)' },
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
  const SSH_TRIG    = /(^|[;&|(]\s*|\$\(\s*)ssh\s/i;
  // SQL-клиент + признак исполняемого SQL: -c/-e/-f/--command/--execute, heredoc
  // или закавыченный позиционный аргумент (sqlite3 "..."). Пустые пары кавычек
  // от вырезанных строк в code сохраняются — признак работает.
  const SQLCLI_TRIG = /\b(?:psql|mysql|mariadb|sqlite3|sqlcmd|clickhouse-client|mongosh?)(?:\.exe)?\b[^\n;&|]*(?:\s(?:-c|-e|-f|--command|--execute|--file)\b|<<|["'])/i;
  const SHELL_TRIG  = /(^|[;&|(]\s*|\$\(\s*)(?:bash|zsh|dash|ksh|sh|eval)(?:\.exe)?\s+(?:(?:-\S*|--\S+)\s+)*(?:-[a-zA-Z]*c[a-zA-Z]*(?:\s|$|["'])|<<|["'])/i;
  const INTERP_TRIG = /(^|[;&|(]\s*|\$\(\s*)((?:python|perl|node(?:js)?|ruby|php)[\w.]*)(?:\.exe)?\s+(?:(?:-\S*|--\S+)\s+)*(?:-[a-zA-Z]*[ce][a-zA-Z]*(?:\s|$|["'])|<<)/i;
  // Exec-стоки: только при их наличии строки-литералы интерпретаторного кода
  // сканируются как команды. Литералы без стока — данные (доказанный кейс
  // владельца: анализ-скрипт с опасными словами в строках, стоков нет).
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

  // Рекурсивный скан: код → каналы-исполнители. Глубина ≤ 3 (bash -c "ssh ...").
  function scanCommand(cmdStr, depth) {
    if (depth > 3 || typeof cmdStr !== 'string' || !cmdStr.trim()) return null;
    const t = tokenize(cmdStr);

    // 1) Исполняемый код команды
    let h = findHit(t.code);
    if (h) return h;

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

    // 3) ssh: нагрузка исполняется удалённым шеллом (прод-сервер = десятки контейнеров)
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
        h = scanInterpreterPayload(p, im[2]);
        if (h) return h;
      }
    }

    return null;
  }

  let hit = scanCommand(cmd, 0);

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
