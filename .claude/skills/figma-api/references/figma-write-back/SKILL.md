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

1. Figma → Settings → Personal access tokens → Generate. Свой, личный.
2. Сохрани в env: `export FIGMA_ACCESS_TOKEN=figd_...`
   (скрипты понимают и старое имя `FIGMA_TOKEN` — принимаются оба).
3. Скоупы: `file_comments:write` для комментариев, `file_variables:write` для Variables.
4. **Не коммить** в репо.

Узнай file key из URL: `figma.com/design/<KEY>/<name>`.

## Скрипт: запостить комментарий

Готовый файл: **`templates/comment.mjs`** (Node 18+, без зависимостей).

```bash
FIGMA_ACCESS_TOKEN=figd_... node templates/comment.mjs <fileKey> "<text>" [nodeId]
```

`nodeId` необязателен: без него комментарий висит в файле, с ним — прикреплён
к конкретному фрейму. В URL нода пишется через дефис (`node-id=1-23`),
в API — через двоеточие (`1:23`).

## Использование в workflow

После значительной правки в HTML:

```bash
node templates/comment.mjs $FIGMA_FILE "HTML hero обновлён: padding 48px, h1 сменили на Fraunces. Скриншот: <link>"
```

Или автоматически в pre-push hook:
```bash
#!/bin/sh
node templates/comment.mjs $FIGMA_FILE "Push на $(git rev-parse --short HEAD): $(git log -1 --pretty=%B)"
```

## Скрипт: обновить Variables

Готовый файл: **`templates/update-vars.mjs`**. Полезно, когда пересчитал палитру
в `color-system-builder` и хочешь обновить Figma:

```bash
# сперва всегда сухой прогон — печатает, что изменится, и ничего не пишет
FIGMA_ACCESS_TOKEN=figd_... node templates/update-vars.mjs <fileKey> tokens.json
# запись — только явным флагом
FIGMA_ACCESS_TOKEN=figd_... node templates/update-vars.mjs <fileKey> tokens.json --apply
```

Формат входа: `{ "color": { "brand-500": "#3B5BFF" } }` → ищет переменную `color/brand-500`.
Новых переменных API не создаёт — их заводит дизайнер в Figma, скрипт только обновляет
значения существующих.

⚠ **Variables Write API есть не на всех тарифах Figma.** На бесплатном вернётся 403 —
это ограничение плана, а не поломка. Комментарии при этом работают на любом тарифе.

⚠ Точная схема Variables API у Figma меняется — при 400 сверься с актуальными доками.

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
