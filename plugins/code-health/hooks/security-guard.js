#!/usr/bin/env node
// Adaptive Security Guard - PreToolUse hook

const PERSONAL_PATHS = [
  /\.claude[\/\\]/i,
  /\.claude\.json/i,
  /graph-memory[\/\\]/i,
  /your-project-name[\/\\]/i,
  /[\/\\]tmp[\/\\]/i,
  /[\/\\]temp[\/\\]/i,
  /[\/\\]scratch[\/\\]/i,
  /[\/\\]Downloads[\/\\]/i,
  /[\/\\]YourProject[\/\\]tools[\/\\]/i,
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

let input = '';
const stdinTimeout = setTimeout(function(){process.exit(0);}, 2000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk){input += chunk;});
process.stdin.on('end', function() {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input || '{}');
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
});
