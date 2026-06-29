---
name: figma-write-back
description: Постить изменения в HTML обратно в Figma как комментарии или предложения. Через Figma REST API.
when_to_use: HTML — рабочий source-of-truth, в Figma — оригинал; нужно держать дизайнера в курсе.
---

# Figma write-back

Дизайнер в Figma не следит за GitHub. Если вы правите HTML-прототип, дизайнер не узнаёт. Этот скилл — мост: вы пишете комментарии в Figma программно.

## Что можно

Через Figma REST API (POST):
- ✅ **Комментарии** к фрейму или координате — best способ синхронизации.
- ✅ **Variables** — обновить токены в Figma из HTML (новая фича Figma).
- ⚠ **Стили** — можно создавать/обновлять color/text styles.
- ❌ **Менять frames/components** — официально нет (только Plugin API внутри Figma).

## Token

1. Figma → Settings → Personal access tokens → Generate.
2. Сохрани в env: `export FIGMA_TOKEN=figd_...`
3. **Не коммить** в репо.

Узнай file key из URL: `figma.com/file/<KEY>/<name>`.

## Скрипт: запостить комментарий

`templates/comment.mjs`:

```js
const TOKEN = process.env.FIGMA_TOKEN;
const FILE  = process.argv[2];
const TEXT  = process.argv[3] || 'Update from HTML';
const NODE  = process.argv[4]; // optional: node id, e.g. "1:23"

if (!TOKEN || !FILE || !TEXT) {
  console.error('Usage: FIGMA_TOKEN=... node comment.mjs <fileKey> "<text>" [nodeId]');
  process.exit(1);
}

const body = { message: TEXT };
if (NODE) {
  body.client_meta = { node_id: NODE, node_offset: { x: 0, y: 0 } };
}

const res = await fetch(`https://api.figma.com/v1/files/${FILE}/comments`, {
  method: 'POST',
  headers: {
    'X-Figma-Token': TOKEN,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(body),
});
const data = await res.json();
if (!res.ok) { console.error('✗', data); process.exit(1); }
console.log('✓ Posted:', data.message);
```

## Использование в workflow

После значительной правки в HTML:

```bash
node comment.mjs $FIGMA_FILE "HTML hero обновлён: новый padding 48px, h1 сменили на Fraunces. Скриншот: <link>"
```

Или автоматически в pre-push hook:
```bash
#!/bin/sh
node comment.mjs $FIGMA_FILE "Push на $(git rev-parse --short HEAD): $(git log -1 --pretty=%B)"
```

## Скрипт: обновить Variables

Свежий API. Полезно когда вы пересчитали палитру в `color-system-builder` и хотите обновить Figma:

```js
// templates/update-vars.mjs
const TOKEN = process.env.FIGMA_TOKEN;
const FILE = process.argv[2];
const tokens = JSON.parse(await fs.readFile(process.argv[3], 'utf8'));

// 1. Получить существующие variables
const cur = await fetch(`https://api.figma.com/v1/files/${FILE}/variables/local`, {
  headers: { 'X-Figma-Token': TOKEN }
}).then(r => r.json());

// 2. Подготовить bulk-update
const updates = [];
for (const [name, value] of Object.entries(tokens.color)) {
  const existing = cur.meta.variables.find(v => v.name === `color/${name}`);
  if (!existing) continue;
  updates.push({
    action: 'UPDATE', id: existing.id,
    valuesByMode: { [cur.meta.modes[0].modeId]: { type: 'COLOR', ...hexToRgba(value) } }
  });
}

// 3. Запушить
await fetch(`https://api.figma.com/v1/files/${FILE}/variables`, {
  method: 'POST',
  headers: { 'X-Figma-Token': TOKEN, 'Content-Type': 'application/json' },
  body: JSON.stringify({ variableModeChanges: updates }),
});
```

(Точная схема API меняется; смотри Figma docs.)

## Workflow: HTML как источник правды для бренда

1. Команда правит токены в `tokens.css`.
2. CI запускает `css-to-dtcg.mjs` → `tokens.json` (DTCG).
3. CI запускает `figma-write-back update-vars` → Figma Variables обновлены.
4. Дизайнер открывает Figma, видит свежие цвета.

Обратное направление (Figma → код) — через Token Studio в Figma, отдельно.

## Ограничения

- **Rate limits**: 60 requests/min на token.
- **Только что-то одно**: либо комментарии (любой план Figma), либо Variables (нужен Enterprise или свежие планы).
- **Нет realtime**: дизайнер увидит изменения только когда обновит файл.

## Этика и команда

- Комментарии-флуд раздражает. Группируй по сессии: один комментарий «5 правок: ...» вместо 5 отдельных.
- Не пиши в комментариях содержимое из приватных репо/доков.
- Согласуй с дизайнером, что бот будет писать.

## Антипаттерны

- ❌ Коммитить TOKEN в репо. Используй env / secrets.
- ❌ Постить комментарий на каждый коммит — спам.
- ❌ Перезаписывать Variables без бэкапа — дизайнер потеряет ручные правки.
- ❌ Ждать что Figma подхватит изменения мгновенно — задержка может быть до минут.
