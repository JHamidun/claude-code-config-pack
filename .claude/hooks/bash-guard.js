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
 * (your-server runs 44 prod containers — destroyers inside quotes were invisible).
 *
 * 2026-07-19 dcg-port (Dicklesworthstone/destructive_command_guard, Rust, 2.9k*):
 * interpreter inline payloads (python -c / perl -e / node -e / bash -c + heredocs)
 * re-scanned via quote extraction (os.system('rm -rf /') was invisible — the closing
 * quote broke the TERM boundary); fs-nuke sinks on roots/home (shutil.rmtree,
 * fs.rmSync, FileUtils.rm_rf, File::Path remove_tree); decode-and-exec
 * (base64 -d | sh, eval $(base64|curl), bash <(curl), sh -c "$(curl)");
 * powershell -EncodedCommand decoded (UTF-16LE + UTF-8) and re-scanned;
 * wipefs -a; vssadmin/wmic shadowcopy delete.
 *
 * 2026-07-31 infra-destruction gap-fill: the guard knew nothing about tearing down
 * running production infrastructure (your-server: 44 prod containers + pm2 + systemd).
 * Added to the SAME P[] list (so the ssh / interpreter / -EncodedCommand branches
 * re-scan payloads automatically): docker rm -f, docker rm/stop/kill $(docker ps ...),
 * docker compose down (+ -v/--volumes = data loss), docker volume rm, docker * prune,
 * pm2 delete/kill, systemctl stop/disable, service ... stop, kubectl delete.
 * Deliberately NOT sql/txt-gated: a text-display prefix must not open
 * `echo restarting && docker compose down -v`. Read-only ops (docker ps/logs,
 * docker compose up -d, pm2 list, systemctl status) never match.
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

  // Запасной вариант раньше был литералом '${HOME}' — при обезличивании так заменили
  // путь машины автора. Node таких подстановок не делает, и на системе без USERPROFILE
  // (то есть везде кроме Windows) сторож сравнивал команды с каталогом по имени "${HOME}"
  // и не узнавал ни одного домашнего пути — то есть молча переставал стеречь.
  const HOMEwin = (process.env.USERPROFILE || require('os').homedir());
  const HOMEfwd = HOMEwin.replace(/\\/g, '/');
  const HOMEfwdEsc = HOMEfwd.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const HOMEbackEsc = HOMEwin.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Pure text-display / text-processing command? Then SQL mentions are harmless text.
  // (Gates ONLY sql-flagged patterns — gating rm/dd on this would open `echo hi && rm -rf /`.)
  const TEXTDISP = /^\s*(echo|printf|cat|grep|rg|egrep|fgrep|less|more|head|tail|print|type|write-output|write-host|awk|sed|git\s+commit|git\s+log)\b/i;

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
    { id: 'fork-bomb',  re: /:\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:/, why: 'fork bomb' },
    // git destructive force-push to protected branches
    { id: 'git-force-main', re: /\bgit\s+push\b[^\n]*\s(--force\b|-f\b|--force-with-lease\b)[^\n]*\b(main|master|prod|production|release)\b/i, why: 'git push --force в main/master/prod' },
    { id: 'git-plus-main',  re: /\bgit\s+push\b[^\n]*\s\+(main|master|prod|production|release)\b/i, why: 'git push +refspec в защищённую ветку' },
    // git checkout/restore of the ENTIRE working tree (`.`) — discards all uncommitted edits
    { id: 'git-checkout-dot', re: /\bgit\s+(?:-C\s+\S+\s+)?(?:checkout|restore)\s+(?:(?!--)[\w@^~{}\/.:-]+\s+)?(?:--\s+)?\.["']?\s*(?:$|[;&|])/i, why: 'git checkout/restore -- . (сброс ВСЕХ незакоммиченных правок)' },
    // chattr recursive un-immutable (fleet brains on your-server are chattr +i protected)
    { id: 'chattr-unimmute-R', re: /\bchattr\b(?=[^\n]*\s-[a-zA-Z]*R)[^\n]*\s-[a-zA-Z]*i/, why: 'chattr -R -i (рекурсивное снятие immutable-защиты)' },
    // PowerShell recursive-force delete of roots/home
    { id: 'ps-remove-root', re: /remove-item\b[^\n]*-(recurse|force)\b[^\n]*(\bc:\\?(\s|$|\*)|\$env:userprofile|\$home\b|~[\\/](\s|$))/i, why: 'Remove-Item -Recurse -Force корня/home' },
    { id: 'ps-rd-root',     re: /\b(rd|rmdir)\s+\/s\s+\/q\s+(c:\\?(\s|$)|%userprofile%|"?c:\\)/i, why: 'rd /s /q корня/home' },
    // registry hive delete
    { id: 'reg-del-hive', re: /\breg\s+delete\s+(hk(lm|cu|cr|u|cc)\b|hkey_)/i, why: 'reg delete ветки реестра' },
    // chmod -R on root/home
    { id: 'chmod-root', re: /\bchmod\s+(-[a-z]*\s+)*-[a-z]*r[a-z]*\s+[^\n]*\s(\/(\s|$)|~(\/(\s|$)|\s|$)|\$\{?home\}?(\s|$))/i, why: 'chmod -R на корень/home' },
    // download|execute (remote code exec)
    { id: 'curl-pipe-exec', re: /\b(curl|wget|iwr|invoke-webrequest)\b[^\n]*(\||;|&&)\s*(sh|bash|zsh|iex\b|invoke-expression\b|python3?\b|node\b|perl\b)\b/i, why: 'скачать-и-исполнить (curl|sh)' },
    // === 2026-07-31 infra-destruction (снос работающего прода) ===
    // NO sql/txt gate on purpose: TEXTDISP matches only the START of the line, so a txt-flag
    // would open `echo restarting && docker compose down -v`. Cost: `grep "docker rm -f" x.md`
    // is blocked too — same trade-off as the existing rm-root/dd rules.
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
    // === dcg-port 2026-07-19 (8 patterns + 3 scan branches below) ===
    // Interpreter fs-nuke sinks: match the RAW cmd (heredoc bodies and -c payloads are
    // substrings of it). Root/home/sysdir targets only — rmtree('./build'|'/tmp/x') PASS.
    // txt:true — text-display prefix (echo/git commit) makes these harmless mentions;
    // the interpreter branch below still re-scans real payloads, so no echo-prefix bypass.
    { id: 'interp-rmtree-root', re: new RegExp('\\b(?:shutil\\.rmtree|os\\.removedirs|FileUtils\\.rm_rf|FileUtils\\.rm_r|(?:File::Path::)?remove_tree|rmtree)\\s*\\(\\s*(?:r|rb|b)?["\'](?:\\/(?!tmp\\b)[a-z]{0,12}|\\/home\\/[\\w.-]+|~|[a-z]:\\\\{0,4}|' + HOMEfwdEsc + ')\\/?["\']', 'i'), why: 'shutil.rmtree/rm_rf/remove_tree корня, /home или системной папки (python/ruby/perl payload)', txt: true },
    { id: 'js-fs-rm-root', re: new RegExp('\\.\\s*rm(?:Sync|dirSync|dir)?\\s*\\(\\s*["\'](?:\\/(?!tmp\\b)[a-z]{0,12}|\\/home\\/[\\w.-]+|~|[a-z]:\\\\{0,4}|' + HOMEfwdEsc + ')\\/?["\']', 'i'), why: 'fs.rmSync/rmdir корня, /home или системной папки (node payload)', txt: true },
    // decode-and-execute (obfuscated payload — content invisible, execution intent explicit)
    { id: 'decode-pipe-exec', re: /\b(?:base64\s+(?:-d|--decode)|openssl\s+enc\s+[^\n|]*-d|xxd\s+-r)[^\n|]*\|\s*(?:sh|bash|zsh|dash|iex|invoke-expression|python[\w.]*|node(?:js)?|perl|ruby)\b/i, why: 'декодировать-и-исполнить (base64 -d | sh)' },
    { id: 'eval-download-decode', re: /\beval\b[^\n]*\$\([^)\n]*\b(?:base64|curl|wget)\b/i, why: 'eval $(base64/curl/wget ...) — исполнение декодированного/скачанного кода' },
    // pipe-to-shell variations beyond curl|sh
    { id: 'proc-subst-exec', re: /\b(?:sh|bash|zsh|dash|ksh)\s+(?:-\S+\s+)*<\(\s*(?:curl|wget)\b/i, why: 'bash <(curl ...) — исполнение скачанного через process substitution' },
    { id: 'shell-c-download', re: /\b(?:sh|bash|zsh|dash|ksh)\b[^\n]*\s-[a-z]*c[a-z]*\s+["']?\$\([^)\n]*\b(?:curl|wget)\b/i, why: 'sh -c "$(curl ...)" — исполнение скачанного через command substitution' },
    // disk signature wipe + Windows restore-point destruction
    { id: 'wipefs', re: /\bwipefs\s+(?:-[a-z]*a[a-z]*|--all)\b/i, why: 'wipefs -a — стирание сигнатур ФС' },
    { id: 'shadowcopy-delete', re: /\bvssadmin\b[^\n]*\bdelete\s+shadows\b|\bwmic\b[^\n]*\bshadowcopy\b[^\n]*\bdelete\b/i, why: 'удаление Volume Shadow Copies (уничтожение точек восстановления)' },
  ];

  // Scan one command string (top-level command OR the payload of a remote ssh command).
  function findHit(str) {
    const textDisplay = TEXTDISP.test(str);
    for (const p of P) {
      if ((p.sql || p.txt) && textDisplay) continue; // "echo DROP DATABASE" / git commit -m "..." — harmless text
      if (p.re.test(str)) return p;
    }
    return null;
  }

  // Extract quoted substrings (both quote types => one nesting level covered) —
  // used by the interpreter/heredoc branch below; mirrors the ssh-branch extraction.
  function extractQuoted(str) {
    const out = [];
    const dq = str.match(/"(?:[^"\\]|\\.)*"/g) || [];
    for (const seg of dq) out.push(seg.slice(1, -1).replace(/\\(["\\$`])/g, '$1'));
    const sq = str.match(/'[^']*'/g) || [];
    for (const seg of sq) out.push(seg.slice(1, -1));
    return out;
  }

  let hit = findHit(cmd);

  // SSH branch: `ssh host "..."` / `ssh host '...'` / `ssh host cmd...` — the remote payload
  // must pass the SAME destructive patterns (closing quote used to break the TERM boundary,
  // making e.g. `ssh your-server "rm -rf /"` invisible). Only when ssh is in COMMAND position —
  // the word "ssh" inside a commit message must not trigger payload scanning.
  if (!hit && /(^|[;&|(]\s*|\$\(\s*)ssh\s/i.test(cmd)) {
    const inners = [];
    const dq = cmd.match(/"(?:[^"\\]|\\.)*"/g) || [];
    for (const seg of dq) inners.push(seg.slice(1, -1).replace(/\\(["\\$`])/g, '$1'));
    const sq = cmd.match(/'[^']*'/g) || [];
    for (const seg of sq) inners.push(seg.slice(1, -1));
    // unquoted remote command: everything after `ssh [opts] host`
    const m = cmd.match(/\bssh\s+(?:-[a-zA-Z]\S*\s+)*(?:\S+@)?[\w.\-]+\s+([\s\S]+)$/);
    if (m) inners.push(m[1]);
    for (const s of inners) {
      hit = findHit(s);
      if (hit) { hit = { id: hit.id + '@ssh', why: hit.why + ' — внутри ssh-команды (удалённый хост!)', re: hit.re }; break; }
    }
  }

  // Interpreter/heredoc branch (dcg-port): `python -c "..."`, `perl -e`, `node -e`,
  // `ruby -e`, `bash|sh -c`, and `python <<EOF ... EOF` — inline payloads hide
  // destroyers inside quotes (os.system('rm -rf /')) where the closing quote breaks
  // the TERM boundary of the top-level scan. Extract quoted segments, re-scan each.
  // Only fires when the interpreter is in COMMAND position with -c/-e flags or a heredoc.
  if (!hit && /(^|[;&|(]\s*|\$\(\s*)(?:python[\w.]*|perl[\w.]*|node(?:js)?[\w.]*|ruby[\w.]*|php[\w.]*|bash|zsh|dash|ksh|sh)(?:\.exe)?\s+(?:(?:-\S*|--\S+)\s+)*(?:-[a-zA-Z]*[ce][a-zA-Z]*(?:\s|$|["'])|<<)/i.test(cmd)) {
    for (const s of extractQuoted(cmd)) {
      hit = findHit(s);
      if (hit) { hit = { id: hit.id + '@inline', why: hit.why + ' — внутри inline-кода интерпретатора/heredoc', re: hit.re }; break; }
    }
  }

  // PowerShell -EncodedCommand branch (dcg-port): decode the base64 payload
  // (UTF-16LE — PowerShell canon — plus UTF-8 fallback) and re-scan it with the
  // same patterns. Undecodable/garbled payload => fail-open, consistent with the guard.
  if (!hit) {
    const enc = cmd.match(/\b(?:powershell|pwsh)(?:\.exe)?\b[^\n]*?\s[-\/](?:e|ec|en|enc|encodedcommand)[:\s]+["']?([A-Za-z0-9+\/=]{16,})/i);
    if (enc) {
      try {
        const buf = Buffer.from(enc[1], 'base64');
        for (const dec of [buf.toString('utf16le'), buf.toString('utf8')]) {
          hit = findHit(dec);
          if (hit) { hit = { id: hit.id + '@encoded', why: hit.why + ' — внутри base64 -EncodedCommand', re: hit.re }; break; }
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
