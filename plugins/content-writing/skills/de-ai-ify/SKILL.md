---
name: de-ai-ify
description: Removes AI jargon and cliches from text, making it sound human. Use when user says "убери ИИ стиль", "де-аифай", "humanize text".
---

# De-AI-ify: Remove AI Jargon

**Очисти текст от ИИ-клише и сделай его человечным.**

## Процесс

### Step 1: Найди AI-жаргон

Сканируй текст на наличие следующих категорий:

**Buzzwords (заменить на простые слова):**
| AI-клише | Замена |
|----------|--------|
| leverage | use, apply |
| utilize | use |
| streamline | simplify, speed up |
| harness | use, apply |
| synergy | cooperation, teamwork |
| paradigm shift | major change |
| cutting-edge | modern, new |
| game-changer | important improvement |
| delve into | look at, explore |
| navigate | handle, manage |
| robust | strong, reliable |
| scalable | expandable |
| holistic | complete, full |
| empower | enable, help |
| optimize | improve |
| innovative | new, creative |
| seamless | smooth |
| transformative | significant |
| ecosystem | system, environment |
| actionable | practical, useful |

**Фразы-паразиты (удалить или упростить):**
- "In today's rapidly evolving landscape..."
- "It's important to note that..."
- "At the end of the day..."
- "Moving forward..."
- "In terms of..."
- "With that being said..."
- "It goes without saying..."
- "Needless to say..."
- "As a matter of fact..."
- "By and large..."

**Русские AI-клише:**
| Клише | Замена |
|-------|--------|
| в современном мире | сейчас |
| на сегодняшний день | сейчас |
| данный | этот |
| является | — (тире) |
| осуществлять | делать |
| в рамках | в, при |
| представляет собой | это |
| обеспечивает | даёт, позволяет |
| функционал | функции |
| имплементация | внедрение, реализация |

### Step 2: Проверь структуру

- Убери избыточные заголовки
- Сократи lists до сути
- Убери "водянистые" абзацы без информации
- Проверь: каждое предложение несёт смысл?

### Step 3: Проверь тон

- Звучит как живой человек, а не маркетинговый бот?
- Нет ли повторяющихся конструкций?
- Длина предложений варьируется?
- Есть конкретика вместо абстракций?

### Step 4: Выведи результат

```
## De-AI-ify Report

**Найдено клише:** X
**Заменено:** Y
**Удалено фраз:** Z

### Очищенный текст:
[cleaned text]

### Изменения:
1. "leverage" → "use" (строка N)
2. ...
```

## Примеры

**До:**
> We leverage cutting-edge AI to streamline your workflow, delivering a seamless and transformative experience that empowers teams to navigate complex challenges in today's rapidly evolving landscape.

**После:**
> We use modern AI to simplify your work. Teams handle complex tasks faster.

**До (русский):**
> На сегодняшний день наше решение представляет собой инновационную платформу, которая осуществляет комплексный подход к оптимизации бизнес-процессов в рамках цифровой трансформации.

**После:**
> Наша платформа упрощает бизнес-процессы и помогает перейти на цифровые инструменты.
