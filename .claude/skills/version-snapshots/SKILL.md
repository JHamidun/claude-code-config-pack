---
name: version-snapshots
version: 1.0.0
description: "Копии одного файла в .snapshots/ + MANIFEST.md — откат правки без git. Триггеры: «сделай снапшот», «откати к baseline». НЕ откат упавшей фазы→rollback-changes."
---

# Version snapshots

Заменяет «сохрани сначала на всякий случай» — Claude должен делать это автоматически.

## Граница с `rollback-changes`: что лежит на диске

На «откати изменения» / «верни как было» подходят оба скилла, и выбирают их не по
формулировке просьбы, а по тому, **чем откатывать**. Посмотри в проект:

- есть `.snapshots/` с копиями файла — этот скилл, откат это `cp` одной копии поверх
  оригинала;
- есть `.bug-changes.json` / `.rollback/` — `rollback-changes`, там откат по журналу:
  вернуть файлы из бэкапов, снести созданные, отревертить коммиты, почистить артефакты;
- нет ни того ни другого — откатывать нечем ни тем, ни другим, остаётся `git`.

Разница глубже, чем «один файл против многих». Снапшот снимается **осознанно и
заранее**, человеком или Claude, перед конкретной правкой одного артефакта, и хранит
целиковое состояние файла. Журнал `rollback-changes` ведёт **воркер по ходу фазы**,
он не хранит состояние проекта — только список того, что фаза натворила, и обратные
действия к нему. Поэтому снапшот вернёт макет ровно к тому виду, что ты видел, а
журнал вернёт проект к состоянию «фаза не запускалась», и это разные результаты.

## Когда снимать снапшот

- Перед большой правкой (рефактор разметки, смена темы).
- После завершения фичи / экрана.
- Перед экспортом.

Каждый раз — копия в `.snapshots/<filename>.<ISO-timestamp>.html`.

## Скрипт

`templates/snapshot.mjs`:

```js
import fs from 'node:fs/promises';
import path from 'node:path';
import { execSync } from 'node:child_process';
import crypto from 'node:crypto';

const file = process.argv[2];
const note = process.argv.slice(3).join(' ') || '(без подписи)';
if (!file) { console.error('Usage: node snapshot.mjs <file> [note]'); process.exit(1); }

const dir = '.snapshots';
await fs.mkdir(dir, { recursive: true });

const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const ext = path.extname(file);
const base = path.basename(file, ext);
const dest = path.join(dir, `${base}.${ts}${ext}`);
await fs.copyFile(file, dest);

// миниатюра, если есть playwright
let thumb = '';
try {
  const thumbPath = path.join(dir, `${base}.${ts}.png`);
  execSync(`node -e "
    import('playwright').then(async ({chromium}) => {
      const b = await chromium.launch();
      const p = await b.newPage({viewport:{width:1280,height:800}});
      await p.goto('file://${path.resolve(file)}');
      await p.screenshot({path:'${thumbPath}'});
      await b.close();
    })
  "`, { stdio: 'ignore' });
  thumb = `![](${path.basename(thumbPath)})`;
} catch {}

const manifest = path.join(dir, 'MANIFEST.md');
const line = `\n### ${ts}  \n**${path.basename(dest)}** — ${note}  \n${thumb}\n`;
await fs.appendFile(manifest, line);
console.log('✓', dest);
```

## Использование

```bash
node snapshot.mjs index.html "до смены темы на dark"
```

## Откат

```bash
cp .snapshots/index.2026-04-28T15-32-00.html index.html
```

## Чистка

`.snapshots/` может разрастись. Раз в неделю:
```bash
find .snapshots -mtime +30 -delete
```

## Что НЕ делать

- Не коммить `.snapshots/` в git — добавь в `.gitignore`.
- Не используй вместо git. Git делает то же самое лучше. Snapshots — для тех, кто без git, или внутри одной сессии.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-version-snapshots.md`. Секции там: Структура, Snapshot trigger, Snapshot script, List snapshots, Restore, Diff между snapshots, Cleanup, .gitignore, Когда НЕ нужно, Stack, Антипаттерны.
