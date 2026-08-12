import fs from 'node:fs/promises';
const file = process.argv[2];
const data = JSON.parse(await fs.readFile(file, 'utf8'));

let html = `<!doctype html><html><head><meta charset="utf-8"><title>Imported</title>
<script src="deck-stage.js"></script>
<style>
  body { margin: 0; }
  .slide-content { position: absolute; }
</style></head><body><deck-stage>`;

for (const sl of data.slides) {
  html += `\n<section data-screen-label="${String(sl.index+1).padStart(2,'0')}">`;
  for (const it of sl.items) {
    const style = `left:${it.x}px;top:${it.y}px;width:${it.w}px;height:${it.h}px;`;
    if (it.kind === 'text') {
      const txt = (it.paragraphs || []).map(p =>
        p.runs.map(r => {
          let t = `<span`;
          if (r.size) t += ` style="font-size:${r.size}px;`;
          if (r.bold) t += `font-weight:bold;`;
          if (r.color) t += `color:#${r.color};`;
          t += `"`;
          return t + `>${r.text}</span>`;
        }).join('')
      ).join('<br>');
      html += `\n<div class="slide-content" style="${style}">${txt}</div>`;
    } else if (it.kind === 'image' && it.data_b64) {
      html += `\n<img class="slide-content" src="data:image/${it.ext};base64,${it.data_b64}" style="${style}">`;
    } else {
      html += `\n<div class="slide-content" style="${style};outline:1px dashed #aaa;"></div>`;
    }
  }
  html += `\n</section>`;
}
html += `\n</deck-stage></body></html>`;

await fs.writeFile(file.replace('.json', '.html'), html);
console.log('✓', file.replace('.json', '.html'));
