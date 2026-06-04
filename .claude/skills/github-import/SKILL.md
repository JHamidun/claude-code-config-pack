---
name: github-import
description: Github репо → исходники как контекст для дизайна. Скачивает дизайн-систему, компоненты, CSS-токены из репо, чтобы новый прототип использовал существующие конвенции проекта. Не клонирование — выборочный pull нужных файлов.
when_to_use: Юзер указал GitHub репо, прототип делается ДЛЯ существующего проекта (не green-field). Перед design-system-create когда уже есть код.
---

# Github import

Цель — понять что у проекта уже есть (tokens, компоненты, конвенции), не конфликтовать, а продолжить.

## Использование

```bash
# Через gh CLI (если auth настроен)
gh repo view YourUsername/your-project --json name
gh repo clone YourUsername/your-project /tmp/repo

# Точечный pull без клонирования
gh api repos/YourUsername/your-project/contents/apps/web/src/styles/globals.css \
  -H "Accept: application/vnd.github.raw" > tokens-from-project.css
```

Или через `git clone --depth 1` если уже есть git auth.

## Что искать в существующем проекте

### 1. Design tokens (CSS variables)
Типичные файлы:
- `globals.css`, `tokens.css`, `vars.css`
- `tailwind.config.{js,ts}` (если Tailwind)
- `theme.{js,ts}` (Material UI / Chakra / styled-components)

```bash
# Найти tokens файлы
find /tmp/repo -name "*.css" -path "*styles*" | head
find /tmp/repo -name "tailwind.config.*"
grep -r "design tokens\|css variables\|--color-" /tmp/repo/src --include="*.css" -l
```

Извлечь все `--*: value` пары → это токены проекта. **Используй ИХ имена**, не свои.

### 2. UI компоненты
```bash
# Найти shared компоненты
ls /tmp/repo/src/components/
ls /tmp/repo/components/
ls /tmp/repo/packages/ui/  # если monorepo
```

Какие atoms уже есть? `Button`, `Input`, `Card`, `Badge`, `Avatar`?
Если есть — **расширяй существующие props**, не создавай дубликаты.

### 3. Type system
```bash
# Найти size scale
grep -rE "fontSize:|font-size:" /tmp/repo/src --include="*.{ts,tsx,css}" | head
```

### 4. Routing / pages
```bash
ls /tmp/repo/src/app/        # Next.js 13+ app router
ls /tmp/repo/src/pages/      # Next.js pages router
ls /tmp/repo/src/routes/     # React Router / TanStack
```

Понять структуру URL'ов чтобы прототип использовал реальные пути.

### 5. Stack / dependencies
```bash
cat /tmp/repo/package.json | jq '.dependencies'
```

Tailwind? styled-components? CSS Modules? Это влияет на то как переноситься handoff.

## Output: project-context.md

После анализа — пишешь summary который потом используется в любых прототипах:

```markdown
# Project context: your-project

## Stack
- Next.js 14 (app router)
- TypeScript
- Tailwind CSS + custom CSS variables
- shadcn/ui компоненты

## Tokens (use these names)
- `--h-primary: #YOUR_PRIMARY`
- `--h-deep: #YOUR_INK`
- `--h-cyan: #YOUR_ACCENT`
- `--h-cream: #YOUR_CREAM`
- (см. apps/web/src/app/globals.css)

## Components (use these instead of building new)
- `<Button>` — variants: default, secondary, ghost (см. components/ui/button.tsx)
- `<Card>`, `<CardHeader>`, `<CardContent>`
- `<Avatar>` — берёт image + fallback initials

## Conventions
- Cyrillic UI text on production
- Animations через framer-motion
- Forms через react-hook-form + zod
- Icons из lucide-react

## Routes
- `/` landing
- `/dashboard/*` authed
- `/admin/*` admin only
```

Этот файл живёт в `design-handoff/<area>/PROJECT_CONTEXT.md` рядом с handoff'ом, чтобы coding agent читал перед имплементацией.

## Что НЕ копировать

- Бизнес-логику (auth, db, API) — не дизайнерский concern
- node_modules / build артефакты
- .env / credentials
- Большие assets (видео, .psd) — только если правда нужны

## Multi-repo контекст

Если проект split на репо (FE / BE / mobile), бери только relevant:
```
your-project-web        — берём styles + components
your-project-api        — игнорируем
your-project-mobile     — берём design tokens только если shared
```

## Антипаттерны

- Клонировать full репо в Claude context → лишние мегабайты
- Игнорировать существующие компоненты → дублирование
- Использовать свои имена токенов вместо проектных → переписка после handoff
- Пропустить `tailwind.config` если проект на Tailwind → теряешь screen breakpoints, custom colors
- Не зафиксировать commit hash → следующая сессия вытаскивает другую версию
- Не положить PROJECT_CONTEXT.md рядом с handoff → coding-agent на handoff не знает о tokens
