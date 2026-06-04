---
name: project-init
description: Интерактивный wizard скаффолда дизайн-проекта. Собирает project name, тип артефакта, целевую платформу, бренд, output формат, и инициализирует папочную структуру с конфигом.
when_to_use: Юзер начинает новый дизайн-проект и говорит «инициализируй», «scaffold», «начни с нуля». Перед любой реализацией если структуры папок ещё нет.
---

# Project init

Один проход вопросов → готовая структура папок + базовый HTML каркас + конфиг.

## Wizard flow

Задаёшь 5 вопросов одним сообщением:

```
1. Имя проекта (slug, для папки): _____
2. Тип артефакта: slides | landing | prototype | dashboard | print | other
3. Целевая платформа: web (desktop/tablet/mobile)? iOS? print?
4. Стиль: используем preset из frontend-design (editorial / brutalism /
   premium-dark / warm / data-dense)? или есть Figma/токены?
5. Output: один HTML / handoff zip / standalone / pptx / pdf?
```

Если юзер ответил частично — берёшь дефолты и явно фиксируешь:
```
«Не уточнил тип артефакта — иду как landing. Если нужно другое — скажи.»
```

## Структура папок

```
<project-slug>/
├── README.md                    # для coding agent / напоминание себе
├── design.config.json           # машиночитаемый конфиг
├── styles/
│   └── tokens.css               # CSS variables (через design-system-create)
├── components/                  # JSX-атомы
│   ├── icons.jsx
│   └── shared.jsx
├── sections/                    # JSX-секции
├── assets/                      # картинки, шрифты, лого
├── uploads/                     # пользовательские референсы
└── <ProjectName>.html           # главный файл
```

## design.config.json

Машиночитаемый снимок решений, чтобы следующая сессия не задавала те же вопросы:

```json
{
  "name": "ExampleProduct Landing",
  "slug": "your-project-landing",
  "type": "landing",
  "platform": "web",
  "viewports": [1440, 768, 375],
  "preset": "warm",
  "tokens_source": "figma:YOUR_FIGMA_FILE_ID",
  "brand": {
    "primary": "#YOUR_PRIMARY",
    "deep": "#YOUR_INK",
    "cyan": "#YOUR_ACCENT",
    "cream": "#YOUR_CREAM"
  },
  "fonts": {
    "head": "Inter Tight",
    "body": "Manrope",
    "mono": "JetBrains Mono"
  },
  "output": "standalone-html",
  "skills_used": ["frontend-design", "design-system-create", "design-canvas"],
  "created": "(see git history)",
  "iterations": 0
}
```

## Главный HTML — каркас

Минимальный стартовый `<ProjectName>.html`:

```html
<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title><Project Name></title>
<link rel="stylesheet" href="styles/tokens.css">
</head>
<body>
  <div id="root"></div>

  <!-- Если интерактив нужен (interactive-prototype): -->
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin></script>

  <script type="text/babel" src="components/shared.jsx"></script>
  <script type="text/babel" data-presets="env,react">
    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body></html>
```

Если артефакт — слайды или статика без React, выбрось React-теги.

## README.md шаблон

```markdown
# <Project Name>

<Type>: <landing | slides | prototype | ...>

## Запустить локально

Открыть `<Project Name>.html` в браузере. Или:
```bash
python3 -m http.server 8080
# открыть http://localhost:8080/<Project Name>.html
```

## Файлы

- `styles/tokens.css` — design tokens (см. дизайн-систему проекта)
- `components/` — JSX-атомы (если используется React)
- `sections/` — JSX-секции (если используется React)
- `<Project Name>.html` — главный файл

## Стек

<если React+Babel: React 18 + Babel standalone через CDN>
<если static: чистый HTML+CSS>
```

## Антипаттерны

- Создать папку и забыть про config → следующая сессия задаёт те же 5 вопросов
- Скаффолд без README → coding-agent на handoff не понимает что происходит
- Положить все JSX в один файл «main.jsx» → невозможно работать секциями
- Не зафиксировать viewports → ответственный за адаптив каждый раз спрашивает
- Создать project-init на каждое мелкое изменение → не каждое требует отдельной папки

## Когда НЕ инициализировать

- Мелкая правка существующего HTML — просто редактируй
- Один эксперимент на быструю проверку идеи — не нужна структура
- Уже есть проект, юзер просит добавить экран — кладёшь рядом, не плодишь скаффолды
