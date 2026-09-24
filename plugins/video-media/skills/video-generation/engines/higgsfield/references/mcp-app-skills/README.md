# Higgsfield MCP app skills — справка (не активные навыки)

**Источник:** пакет приложения Higgsfield из каталога OpenAI Codex
(`openai-curated-remote/app-6a3293e129088191abf0875820e839da`, версия 2.1.0).
Перенесено 23.09.2026.

**Статус:** контент вендора (Higgsfield); файла лицензии в пакете вендора нет,
источник и версия — как указано выше. Лежит под `references/`, поэтому как навык
Claude Code не загружается: это рецепты, которые открывают по ссылке.

## Что нужно, чтобы рецепты работали

Все 17 рецептов рассчитаны на **MCP-сервер Higgsfield**
`https://mcp.higgsfield.ai/mcp` (HTTP, OAuth: `openid email offline_access`).
Пока сервер не подключён и не авторизован через `/mcp`, рецепты — только чтение:
без MCP нет ни генерации, ни удалённой песочницы.

Подключение: `claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp`,
затем авторизация через `/mcp`.

Инструменты сервера, на которые опираются рецепты:

- генерация — `generate_image` / `generate_video` / `generate_audio` и пакетные
  `generate_*_batch` (группы до шести позиций `{index, params}`);
- ожидание — `jobs_wait` (до восьми задач за вызов), просмотр —
  `show_generation_by_ids`, `show_generations`, `show_medias`;
- медиа — `media_upload` (резерв слота + presigned `upload_url`), `media_confirm`,
  `media_upload_and_confirm`;
- пресеты — `get_presets`, `get_preset_instructions`, `get_faceless_channel_presets`;
- удалённая песочница вендора — `sandbox_exec` (ffmpeg/ffprobe/curl/Higgsedit CLI
  там, а не в локальном шелле; песочница эфемерная). `$HF_WORKFLOWS` (77 упоминаний
  в 11 рецептах: `${HF_WORKFLOWS}/<рецепт>/scripts/…`) — папка **внутри этой песочницы**,
  вендор кладёт туда скрипты рецептов. Локально её нет: команды с `$HF_WORKFLOWS`
  передаются в `sandbox_exec`, а не запускаются в Bash;
- сайты — `website_repo_access`, `website_status`, `website_db`, `website_secrets`.

Каждая генерация тратит кредиты Higgsfield. Локальный путь без MCP — `hf.exe`
из `../../ENGINE.md`; он покрывает генерацию, Soul и Marketing Studio, но не
песочницу и не хостинг сайтов.

## Что изменено при переносе

- убраны разделы `## Activation analytics` (вызов `track_skill_activation` —
  телеметрия хоста Codex) в 16 `SKILL.md`;
- не перенесены `agents/openai.yaml` (карточки Codex UI), `assets/icon.svg`
  (иконки для UI) и `ai-host-video/references/migration-analysis.md` (аудит
  PR вендора, ниоткуда не ссылается);
- разделы «OpenAI runtime contract» / «Runtime contract» **оставлены**: кроме
  ссылок на хост ChatGPT в них описан порядок работы с инструментами
  Higgsfield (`media_upload` → PUT в `sandbox_exec` → `media_confirm`, лимиты
  батчей, ожидание задач), и на их якоря ссылаются файлы `references/`.
  Упоминания `ask_user_input`, «ChatGPT attachment» и «OpenAI host» читать как
  «вопрос в чате» и «вложение пользователя».

## Рецепты

| Папка | О чём |
|-------|-------|
| `higgsfield/` | Разрешение именованных пресетов и слэш-команд Higgsfield, галереи Viral и Marketing Studio |
| `ad-multiplier/` | Несколько независимых правок одного 4–30-секундного ролика с сохранением движения, тайминга и звука |
| `ai-host-video/` | Полный выпуск канала с одним консистентным AI-ведущим, перебивками и финальным монтажом |
| `faceless-video/` | Многосценное видео с закадровым рассказчиком: faceless-канал, объяснялки, документалка, Picture Story |
| `narrator/` | Дубли озвучки под фиксированные окна и оверлей ведущего по фото поверх готового видео |
| `subtitles/` | Прожжённые в кадр субтитры по речи и их рестайл |
| `thumbnail-generation/` | Готовые обложки YouTube/Instagram и их правка |
| `motion-craft/` | Motion-треки для композиций Higgsedit: хореография кадров, появление текста, счётчики |
| `video-editing/` | Монтаж футажа и моушн-графики в Higgsedit: склейки, саундтрек, оверлеи, титры |
| `ugc-product-video/` | UGC только с продуктом и закадровым голосом (руки/POV без лица) |
| `ugc-review-video/` | UGC-отзыв «говорящая голова» с демонстрацией продукта |
| `ugc-try-on-video/` | UGC-примерка одежды, обуви, аксессуаров |
| `ugc-tutorial-video/` | UGC-туториал с пошаговыми плашками «Step N — Heading» |
| `ugc-unboxing-video/` | UGC-распаковка с реакцией на содержимое |
| `ugc-website-video/` | UGC про сайт или веб-приложение по реальным скриншотам |
| `website-builder/` | Сборка и публикация сайта, веб-приложения или браузерной игры на хостинге Higgsfield |
| `youtube-script/` | Полный сценарий YouTube в одном из шести жанров: хуки, таймкоды, карта удержания |

Каждая папка — `SKILL.md` (точка входа) плюс `references/` с деталями, как в
исходном пакете.
