---
description: "Инициализация проекта под выбранный стек: от scaffold (папки, конфиги, Dockerfile) до deps, CI/CD, тестов. Триггеры: «каркас проекта», «новый проект»."
argument-hint: "[stack] [project-name]"
---

# Init Project: $ARGUMENTS

Первый аргумент — стек, второй — имя проекта.

**Стеки.** Backend: `django` `fastapi` `flask` `express` `nest` `gin` `fiber`
`actix` `spring` `laravel` `rails`. Frontend: `react` (Vite) `next` `vue`
`nuxt` `svelte` `angular` `remix`. Full-stack: `mern` `t3` `django-react`
`rails-react`. Прочее: `telegram-bot` (Python) `cli` (Python, Click/Typer).

**Лёгкий режим** (бывш. `/scaffold`): просят «каркас/структуру» — сделай
структуру папок, базовые файлы с рабочим кодом и `git init`, БЕЗ установки
зависимостей и CI/CD. Имя не назвали — спроси. В конце выведи команды запуска
(venv+pip / npm install + npm run dev).

## Полный режим — по шагам

1. **Структура и манифесты** по конвенции стека, `git init`.
   Для `telegram-bot`: `bot/{main,config}.py` + `handlers/`, `keyboards/`,
   `services/`, `utils/` — под эту раскладку заточены `/bot-deploy` и
   `/bot-debug`.
2. **Зависимости** родным менеджером (pip/poetry, npm/pnpm, go mod, cargo,
   maven/gradle). Версии не выдумывай — ставь и фиксируй то, что реально
   встало.
3. **Линт и формат**: Python — black + flake8 + mypy · JS/TS — ESLint +
   Prettier · Go — golangci-lint · Rust — rustfmt + clippy · Java — Checkstyle.
4. **Git-хуки**: pre-commit формат+линт, pre-push тесты, commit-msg на
   Conventional Commits.
5. **БД** (если нужна): сервис в docker-compose, конфиг подключения, первая
   миграция, сид-данные.
6. **Тесты**: unit + integration (+ e2e для фронта), конфиг покрытия.
7. **CI** `.github/workflows/ci.yml` на push и pull_request: setup → lint →
   test → build под конкретный стек.
8. **Docker**: multi-stage Dockerfile (сборка отдельно от рантайма — иначе в
   образ уезжают компиляторы и dev-зависимости), docker-compose с приложением
   и БД.
9. **Окружение**: `.env.example` с ПУСТЫМИ значениями и `.env` в `.gitignore`.
   Реальные ключи в примеры не попадают никогда.
10. **README**: обзор, стек, установка, рабочий процесс, деплой, API-доки.

`.gitignore` минимум — Python: `__pycache__/`, `*.py[cod]`, `.env`, `.venv/`,
`*.egg-info/`, `dist/`, `build/`, `.pytest_cache/`, `.coverage`;
Node: `node_modules/`, `.env`, `.env.local`, `dist/`, `build/`, `.next/`,
`coverage/`.

## Отдай в конце

Имя и стек, что настроено (зависимости, тесты, Docker, CI, доки) и следующие
шаги: `cd`, скопировать `.env.example` → `.env` и заполнить, команда запуска,
адрес с портом, команды тестов/формата/сборки.
