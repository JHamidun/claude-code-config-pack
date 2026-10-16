---
description: Настройка database integration для любого фреймворка (тонкая обёртка над skill database-design)
argument-hint: "[database] (postgresql|mysql|mongodb|redis|sqlite) [framework] (fastapi|django|express|nestjs|go)"
---

# 🗄️ Setup Database: $ARGUMENTS

Настраиваю интеграцию базы данных с best practices.

## Supported Databases:

- **postgresql** - PostgreSQL (recommended for production)
- **mysql** - MySQL/MariaDB
- **mongodb** - MongoDB (NoSQL)
- **redis** - Redis (cache/queue)
- **sqlite** - SQLite (dev/testing)

## Supported Frameworks:

- **fastapi** - FastAPI + SQLAlchemy
- **django** - Django ORM
- **express** - Express + Mongoose/TypeORM/Prisma
- **nestjs** - NestJS + TypeORM/Prisma
- **go** - Go + GORM

---

## Инструкции для Claude

1. **Разбери аргументы**: `$ARGUMENTS` = `<database> <framework>`. Если не указаны — спроси или определи по кодбазе (package.json / requirements.txt / go.mod).

2. **Прочитай шаблоны** — весь boilerplate (конфиги подключения, модели, миграции Alembic/Django/TypeORM/Prisma, seed-скрипты, MongoDB/Motor, Redis-кэш, docker-compose, .env.example, best practices, формат вывода) лежит в:
   `~/.claude/skills/database-design/references/framework-db-boilerplate.md`
   Возьми оттуда секцию под выбранную пару database+framework и адаптируй под проект (имена, пути, существующий стек) — не копируй вслепую.

3. **Проектирование схемы, индексы, оптимизация запросов** (если нужно больше, чем подключение) — skill `database-design` (`~/.claude/skills/database-design/SKILL.md`): нормализация, индексные стратегии, миграции для продакшена, N+1, партиционирование, ER-диаграммы через liam.

4. **Выведи результат** в формате из секции «Output:» референса: созданные файлы, команды миграций, next steps.

## Examples:

```
/setup-db postgresql fastapi
/setup-db mongodb express
/setup-db mysql django
/setup-db redis express
/setup-db sqlite fastapi
```
