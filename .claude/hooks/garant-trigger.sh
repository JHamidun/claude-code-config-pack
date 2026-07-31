#!/usr/bin/env bash
# UserPromptSubmit hook: авто-активация garant-research по ключевым словам
# Парсинг JSON через Node.js (гарантированно есть вместе с Claude Code)

INPUT=$(cat)

node -e "
const input = $(echo "$INPUT" | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.stringify(JSON.parse(d)))))");
const data = JSON.parse(input);
const prompt = (data.prompt || '').toLowerCase();

const triggers = [
  'гарант','garant','закон','законод','кодекс','нпа',
  'нормативно-правов','нормативный акт','федеральный закон',
  'постановлен','приказ минист',
  'судебная практика','судебной практик',
  'арбитраж','верховный суд','конституционный суд',
  'апелляци','кассаци',
  'правовая база','правовой портал','юридическ','russian law'
];
const articlePattern = /(ст\.\s*\d|статья\s+\d)/i;
const matched = triggers.some(t => prompt.includes(t)) || articlePattern.test(prompt);

if (matched) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: 'АВТОМАТИЧЕСКИЙ ТРИГГЕР: запрос содержит правовую тематику. Используй skill garant-research: открой ГАРАНТ через Playwright, выполни поиск, извлеки документ. Учётные данные: ~/.claude/secrets/garant.json. Пароль не выводить в чат.'
    }
  }));
}
" 2>/dev/null

exit 0
