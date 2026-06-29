---
description: Инициализация нового проекта с выбранным стеком
argument-hint: [stack] [project-name]
---

# 🚀 Init Project: $ARGUMENTS

Создаю новый проект с полной автоматизацией!

## Supported Stacks:

### Backend:
- **django** - Django 5.x (Python)
- **fastapi** - FastAPI (Python async)
- **flask** - Flask (Python micro)
- **express** - Express.js (Node.js)
- **nest** - Nest.js (Node.js TypeScript)
- **gin** - Gin (Go)
- **fiber** - Fiber (Go)
- **actix** - Actix-web (Rust)
- **spring** - Spring Boot (Java)
- **laravel** - Laravel (PHP)
- **rails** - Ruby on Rails

### Frontend:
- **react** - React + Vite
- **next** - Next.js 14 (App Router)
- **vue** - Vue 3 + Vite
- **nuxt** - Nuxt 3
- **svelte** - SvelteKit
- **angular** - Angular 17+
- **remix** - Remix

### Full-Stack:
- **mern** - MongoDB + Express + React + Node
- **t3** - T3 Stack (Next.js + tRPC + Prisma)
- **django-react** - Django + React
- **rails-react** - Rails + React

## Process:

### 1. Parse Arguments
```bash
STACK=$(echo "$ARGUMENTS" | awk '{print $1}')
PROJECT_NAME=$(echo "$ARGUMENTS" | awk '{print $2}')
```

### 2. Create Project Structure
Based on selected stack, create:
- Directory structure
- Configuration files
- Package manifests
- Git repository
- Docker setup

### 3. Install Dependencies
Run appropriate package manager:
- Python: pip / poetry
- Node.js: npm / yarn / pnpm
- Go: go mod
- Rust: cargo
- Java: maven / gradle

### 4. Setup Development Tools

**Linting & Formatting:**
- Python: black, flake8, mypy
- JavaScript/TypeScript: ESLint, Prettier
- Go: golangci-lint
- Rust: rustfmt, clippy
- Java: Checkstyle

**Git Hooks:**
- Pre-commit: format + lint
- Pre-push: tests
- Commit-msg: conventional commits

### 5. Database Setup (if applicable)
- Create docker-compose.yml with DB service
- Add connection configuration
- Create initial migrations
- Add seed data

### 6. Testing Framework
- Unit tests setup
- Integration tests
- E2E tests (if frontend)
- Coverage configuration

### 7. CI/CD Pipeline
Create `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup
        # Stack-specific setup
      - name: Lint
        run: # Stack-specific linting
      - name: Test
        run: # Stack-specific tests
      - name: Build
        run: # Stack-specific build
```

### 8. Documentation
Create README.md with:
- Project overview
- Tech stack
- Setup instructions
- Development workflow
- Deployment guide
- API documentation (if applicable)

### 9. Docker Configuration
**Dockerfile:**
```dockerfile
# Multi-stage build for production
FROM base-image AS builder
# Build steps...

FROM base-image AS runtime
# Runtime configuration
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "PORT:PORT"
    environment:
      - ENV_VAR
    depends_on:
      - db
  db:
    image: postgres:15
    # DB configuration
```

### 10. Environment Configuration
Create `.env.example`:
```bash
# Application
APP_NAME=project-name
APP_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgres://...

# API Keys
API_KEY=your_key_here
```

## Stack-Specific Templates:

### Django Template
```
project-name/
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── .github/workflows/
├── project/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   └── core/
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       └── tests/
└── static/
```

### FastAPI Template
```
project-name/
├── pyproject.toml
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── items.py
│   ├── services/
│   ├── utils/
│   └── tests/
│       ├── test_api.py
│       └── conftest.py
└── alembic/
```

### MERN Template
```
project-name/
├── package.json
├── .env.example
├── docker-compose.yml
├── client/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── api/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── tests/
└── server/
    ├── package.json
    ├── tsconfig.json
    ├── src/
    │   ├── controllers/
    │   ├── models/
    │   ├── routes/
    │   ├── middleware/
    │   ├── utils/
    │   ├── types/
    │   └── server.ts
    └── tests/
```

### Next.js 14 Template
```
project-name/
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts
├── .env.local
├── Dockerfile
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   ├── api/
│   │   └── [...route]/route.ts
│   └── (routes)/
│       ├── dashboard/
│       └── auth/
├── components/
│   ├── ui/
│   └── shared/
├── lib/
│   ├── utils.ts
│   ├── db.ts
│   └── api.ts
├── public/
└── __tests__/
```

## Output:

После выполнения команды:

```bash
✅ Project created: project-name
📁 Stack: [selected-stack]
🔧 Configuration complete
📦 Dependencies installed
🧪 Tests configured
🐳 Docker ready
📝 Documentation generated

Next steps:
1. cd project-name
2. Copy .env.example to .env and configure
3. [stack-specific start command]
4. Open http://localhost:[PORT]

Development:
- Run tests: [test command]
- Format code: [format command]
- Build: [build command]
```

## Examples:

```bash
/init-project django my-blog
/init-project next ecommerce-store
/init-project fastapi api-service
/init-project mern social-network
/init-project gin microservice
```

**Let's build! 🚀**