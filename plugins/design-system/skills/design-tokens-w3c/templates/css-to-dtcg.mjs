import fs from 'node:fs/promises';
import postcss from 'postcss';

const file = process.argv[2] || 'tokens.css';
const css = await fs.readFile(file, 'utf8');
const root = postcss.parse(css);

const tokens = {};

root.walkRules(':root', rule => {
  rule.walkDecls(decl => {
    if (!decl.prop.startsWith('--')) return;
    const name = decl.prop.slice(2);
    const value = decl.value.trim();
    const path = name.split('-');     // primary-500 → ['primary', '500']

    let cur = tokens;
    for (let i = 0; i < path.length - 1; i++) {
      cur[path[i]] = cur[path[i]] || {};
      cur = cur[path[i]];
    }

    let type = 'other';
    if (/^#|rgb|hsl|oklch/.test(value)) type = 'color';
    else if (/^\d+(\.\d+)?(px|rem|em|%)$/.test(value)) type = 'dimension';
    else if (/^\d+(\.\d+)?$/.test(value)) type = 'number';
    else if (/^['"]/.test(value) || /^[A-Z][a-zA-Z\s,]+$/.test(value)) type = 'fontFamily';

    cur[path.at(-1)] = { '$value': value, '$type': type };
  });
});

await fs.writeFile(file.replace(/\.css$/, '.tokens.json'), JSON.stringify(tokens, null, 2));
console.log('✓', file.replace(/\.css$/, '.tokens.json'));
