---
name: live-preview
version: 1.0.0
description: "Локальный сервер с auto-reload для итеративной работы над HTML/CSS — браузер обновляется при сохранении. Триггеры: «live reload», «browser-sync»."
---

# Live preview

Запусти `live.mjs <path>` — он поднимет http-сервер на 5173, откроет браузер и будет реактивно перезагружать страницу при изменении файлов.

```bash
node ./skills/live-preview/templates/live.mjs index.html
# → открыто http://localhost:5173/
# редактируй файлы — браузер обновится сам
```

Зависимости: `npm i -D chokidar ws`.

## Как работает

1. Простейший HTTP-сервер отдаёт файлы из текущей директории.
2. WebSocket-канал на `/_lp` — клиент в каждой странице слушает.
3. При сохранении файла chokidar шлёт `reload` всем клиентам.
4. В страницы инжектится 6-строчный snippet перед `</body>`.

## Когда не использовать

- Если артефакт уже использует свой dev-server (Vite, Next).
- Если работаешь с production-сборкой без перезагрузок.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-live-preview.md`. Секции там: Самый простой: livereload, Альтернатива: live-server, Альтернатива 3: vite (если артефакт уже React), Альтернатива 4: Python http.server + auto-reload, Custom auto-reload через WebSocket (если хочется без deps), Browser-sync features, Best practices, Tunneling для шеринга, Когда НЕ использовать, Stack, Антипаттерны.
