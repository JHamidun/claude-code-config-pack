---
description: "Каркас проекта по шаблону: fastapi, react, nextjs, telegram-bot, cli — папки, конфиги, Dockerfile. Триггеры: «каркас проекта». Полная инициализация → /init-project."
argument-hint: "[fastapi | react | nextjs | telegram-bot | cli]"
---

# Project Scaffolding

**Аргументы:** $ARGUMENTS (тип проекта: fastapi, react, nextjs, telegram-bot, cli)

## Задача

Создай структуру нового проекта по выбранному шаблону.

## Доступные шаблоны

### fastapi
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   └── __init__.py
│   │   └── deps.py          # Dependencies
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

### react
```
project/
├── src/
│   ├── components/
│   ├── hooks/
│   ├── pages/
│   ├── services/
│   ├── utils/
│   ├── App.tsx
│   └── index.tsx
├── public/
├── tests/
├── .env.example
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### nextjs
```
project/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── api/
│   ├── components/
│   ├── lib/
│   └── types/
├── public/
├── .env.example
├── .gitignore
├── next.config.js
├── package.json
├── tailwind.config.js
└── README.md
```

### telegram-bot
```
project/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Settings
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py
│   │   └── commands.py
│   ├── keyboards/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

### cli
```
project/
├── src/
│   ├── __init__.py
│   ├── cli.py               # Click/Typer CLI
│   ├── commands/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
├── .gitignore
├── pyproject.toml
└── README.md
```

## Действия

1. Спроси название проекта если не указано
2. Создай директории и файлы по шаблону
3. Заполни базовые файлы рабочим кодом
4. Инициализируй git репозиторий
5. Установи зависимости (опционально)

## Базовые файлы для каждого шаблона

### .gitignore (Python)
```
__pycache__/
*.py[cod]
.env
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
```

### .gitignore (Node)
```
node_modules/
.env
.env.local
dist/
build/
.next/
coverage/
```

### .env.example
```
# Copy to .env and fill values
DEBUG=true
DATABASE_URL=
API_KEY=
```

## После создания

Выведи инструкции для запуска:
```bash
cd project-name
# Для Python:
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Для Node:
npm install
npm run dev
```
