# Происхождение и правила пака

## Источник

- Репозиторий: https://github.com/heygen-com/hyperframes (HeyGen, Inc.)
- Коммит: `76c634dfa5f9d0119342e0eda80325aee518dff4` (2026-09-30). Навыки в нём совпадают с релизным
  коммитом `04b01342cfcbd79e2962ccdb3cecc28c68fb93ae` (v0.8.98); между ними правки только в
  `packages/studio`.
- Лицензия: Apache-2.0, дословный текст в `LICENSE` («Copyright 2026 HeyGen, Inc.»), копия —
  `LICENSE-heygen-hyperframes`.
- Сторонние материалы внутри навыков (по `CREDITS.md` и NOTICE): `talking-head-recut` адаптирован из
  notedit/vtake-skills (MIT, уведомление сохранено в `skills/talking-head-recut/NOTICE.md`); SFX в
  `skills/media-use/audio/assets/sfx` — Pixabay Content License; шрифты — SIL OFL; GSAP грузится с CDN
  или вендорен — GSAP Standard «no charge» License (не OSI); модель Parakeet (скачивается по
  требованию) — CC-BY-4.0.

## Что взято (без правок)

`skills/` — 21 опубликованный навык по `skills-manifest.json`; `plugin.json`,
`.claude-plugin/plugin.json`, `skills-manifest.json`, `LICENSE`, `CREDITS.md`, `README.md`. Тексты,
скрипты, шаблоны и ассеты идентичны апстриму (с точностью до переводов строк CRLF/LF).

Не взято: шесть внутренних навыков репозитория (`.claude/skills`), его `.claude/settings.json` с
хуком сборки для разработчиков, пакеты `packages/*`, тесты.

Бандл — чужой код и чужие тексты, поэтому его нельзя прогонять через автозамены: термины
графики (шейдеры, вершины), названия сервисов и цвета — это содержимое апстрима. Слепая замена
ломает шейдеры, список закрытых сетей в `media-fetch.mjs`, векторные пути и встроенные шрифты.
Если файл бандла вызывает сомнения — вернуть его из апстрима по коммиту выше.

## Что своё (пак)

- `SKILL.md` — тонкий вход вместо роутера апстрима: русское описание без перехвата всех
  видеозапросов (у апстрима — «Mandatory entry point… HyperFrames is the default output framework»),
  правила пака, обход чёрной полосы 8 px на холстах шириной 1080.
- `local/hf` — запуск CLI: пин `hyperframes@0.8.98`, `HYPERFRAMES_NO_TELEMETRY=1`, `DO_NOT_TRACK=1`,
  `HYPERFRAMES_SKIP_SKILLS=1`, `HYPERFRAMES_NO_UPDATE_CHECK=1`, отказ для `skills`, `publish`, `cloud`,
  `lambda`, `cloudrun`, `auth`, `feedback`, `telemetry enable` (наружные — с `HF_ALLOW_OUTWARD=1` после
  «ок» пользователя). Если рядом лежит свой закреплённый рантайм (`HF_RUNTIME`), берёт его, иначе
  идёт через `skills/hyperframes/scripts/plugin-cli.mjs` (npx того же пина).
- Почему корень плагина, а не standalone: роутер ищет `plugin.json` двумя уровнями выше своего
  `SKILL.md`; найдя, не запускает `npx hyperframes skills update`, который в standalone-режиме пишет в
  `~/.agents/skills`, раскладывает копии другим агентам и тянет непиннутый main.

## Аудит

Вердикт CAUTION (2026-09-30, навык skill-manager: два сканера по навыкам и по всему бандлу плюс
ручной разбор): вредоносного поведения, утечек и инъекций не найдено. Есть ограниченное
чувствительное поведение, закрытое правилами `SKILL.md` и `local/hf`:

- телеметрия (анонимная статистика использования уходит вендору; в `hf` выключена);
- команды, которые публикуют или разворачивают в облаке (`publish`, `cloud`, `lambda`, `cloudrun`,
  `auth`, `feedback`; в `hf` закрыты);
- самообновление навыков (`hyperframes skills`; в `hf` закрыто);
- блоки реестра и удалённые шаблоны (`add`, `catalog`) приходят из main апстрима в момент вызова.

## Обновление

Только так: новый коммит апстрима, проверка сканерами навыков (skill-manager) и ручной разбор, сверка
диффа с этой версией, замена папки целиком. `hyperframes skills update` и `npx skills add` не
использовать.
