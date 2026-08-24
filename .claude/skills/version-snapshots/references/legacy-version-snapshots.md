<!-- LEGACY: полное тело скилла 'version-snapshots' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: version-snapshots
description: История версий артефакта — снимок при каждом save, можно откатиться, сравнить два момента. Не git (тяжело для прототипа), а лёгкая sidecar папка `.snapshots/`.
when_to_use: Юзер итерирует, делает 5-10 ревизий за сессию, риск что-то сломать. Или хочет сравнить «как было утром vs сейчас». Параллельно с visual-edit / tweaks-panel.
---

# Version snapshots

Лёгкая system-of-record для итераций. Не для production (там git), а для design exploration.

## Структура

```
<project>/
├── artifact.html
├── styles/tokens.css
├── components/...
└── .snapshots/
    ├── (see git history)T10-15-32.zip      # компактный snapshot
    ├── (see git history)T10-22-48.zip
    ├── (see git history)T10-45-12.zip
    └── INDEX.json                    # metadata + tags
```

INDEX.json:
```json
{
  "snapshots": [
    {
      "id": "(see git history)T10-15-32",
      "tag": "first-draft",
      "note": "Initial scaffold — hero + 3 features",
      "size_kb": 124,
      "files_changed": ["artifact.html", "styles/tokens.css"]
    },
    {
      "id": "(see git history)T10-22-48",
      "tag": "warm-palette",
      "note": "Changed palette на warm cream",
      "size_kb": 128
    }
  ]
}
```

## Snapshot trigger

Авто:
- На каждый save файла (если live-preview running) — debounced 30 сек
- Перед запуском `tweaks-panel` (snapshot before destructive change)
- Перед export (PDF / PNG) — фиксация финала

Ручной:
- Юзер: «зафиксируй текущее как baseline», «сделай snapshot»
- Перед рискованной правкой («перепиши hero полностью»)

## Snapshot script

`scripts/snapshot.js`:
```js
const fs = require('fs');
const path = require('path');
const archiver = require('archiver');
const ROOT = '.';
const SNAPS = path.join(ROOT, '.snapshots');

async function snapshot(tag = '', note = '') {
  if (!fs.existsSync(SNAPS)) fs.mkdirSync(SNAPS);
  const id = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const out = path.join(SNAPS, `${id}.zip`);

  const archive = archiver('zip', { zlib: { level: 9 } });
  const stream = fs.createWriteStream(out);
  archive.pipe(stream);

  // Архивим всё, кроме .snapshots, node_modules, .git
  archive.glob('**/*', {
    cwd: ROOT,
    ignore: ['.snapshots/**', 'node_modules/**', '.git/**', '*.log'],
  });
  await archive.finalize();
  await new Promise(r => stream.on('close', r));

  // Update INDEX
  const idxPath = path.join(SNAPS, 'INDEX.json');
  const idx = fs.existsSync(idxPath) ? JSON.parse(fs.readFileSync(idxPath)) : { snapshots: [] };
  idx.snapshots.unshift({
    id, tag, note,
    size_kb: Math.round(fs.statSync(out).size / 1024),
    timestamp: new Date().toISOString(),
  });
  fs.writeFileSync(idxPath, JSON.stringify(idx, null, 2));
  return id;
}

if (require.main === module) {
  snapshot(process.argv[2], process.argv[3]).then(id => console.log(`✓ ${id}`));
}

module.exports = { snapshot };
```

```bash
npm i archiver
node scripts/snapshot.js "warm-palette" "Changed palette на warm cream"
```

## List snapshots

```bash
node scripts/list-snapshots.js
```
```js
const idx = JSON.parse(fs.readFileSync('.snapshots/INDEX.json'));
idx.snapshots.forEach((s, i) => {
  console.log(`${i+1}. ${s.id}  [${s.tag||'-'}]  ${s.note||''}  (${s.size_kb}KB)`);
});
```

```
1. (see git history)T10-45-12  [final-v1]  CTA добавлена  (132KB)
2. (see git history)T10-22-48  [warm-palette]  Changed palette  (128KB)
3. (see git history)T10-15-32  [first-draft]  Initial scaffold  (124KB)
```

## Restore

```bash
node scripts/restore.js (see git history)T10-22-48
```
```js
// Перед restore — auto-snapshot текущего state
await snapshot('pre-restore', `Auto before restore to ${targetId}`);
// Извлечь zip
const extract = require('extract-zip');
await extract(path.join(SNAPS, `${targetId}.zip`), { dir: ROOT });
console.log(`✓ restored to ${targetId}`);
```

⚠️ Restore overwrite-ит текущие файлы. Auto-snapshot перед restore — спасение.

## Diff между snapshots

```bash
node scripts/diff.js (see git history)T10-15-32 (see git history)T10-22-48
```

Расшаривает оба zip во временные папки, делает `diff -r` или Git-стиле line-diff на ключевых файлах.

## Cleanup

Snapshot'ы накапливаются. Auto-cleanup:
- Хранить max 20 последних
- Снапы старше 7 дней — удалять, кроме помеченных tag'ом
- Total size > 50MB — удалять самые старые

```js
function cleanup() {
  const idx = JSON.parse(fs.readFileSync('.snapshots/INDEX.json'));
  const week = 7 * 24 * 60 * 60 * 1000;
  const now = Date.now();
  const keep = idx.snapshots.filter((s, i) => {
    if (i < 20) return true;                                 // last 20
    if (s.tag) return true;                                  // tagged
    if (now - new Date(s.timestamp).getTime() < week) return true;  // recent
    return false;
  });
  // Delete files not in keep
  // ...
}
```

## .gitignore

```
.snapshots/
```

Не коммить snapshots в git — это локальная история. Если нужно sharing — экспорт конкретный snapshot zip отдельно.

## Когда НЕ нужно

- Маленькие правки → undo в editor хватит
- Артефакт уже под git → git history достаточно
- Headless / CI → snapshots accumulate без cleanup

## Stack

- `visual-edit` / `tweaks-panel` — снапы перед каждым destructive change
- `live-preview` — auto-snapshot после save
- `dev-handoff` — last snapshot включить в bundle как «previous version»

## Антипаттерны

- Snapshot на каждый keystroke → 1000 файлов в `.snapshots/`
- Не делать cleanup → 500MB locally
- Включать `node_modules` в snapshot → 50MB на каждый snap
- Restore без auto-snapshot текущего → потеряешь свежие изменения
- Не использовать tags → через 30 snapshots не помнишь что где
