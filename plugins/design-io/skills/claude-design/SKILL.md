---
name: claude-design
description: "Claude Design (claude.ai/design): от AI-мокапа до production-кода, handoff-bundle. Триггеры: «claude design», «перенеси мокап в код»."
---

# claude-design

Production-tested workflow для Claude Design (`claude.ai/design`) — браузерного AI-инструмента дизайн-мокапов от Anthropic. Юзер мокапит UI в HTML/CSS/JS через диалог с AI, экспортирует bundle, coding-agent (я) переношу в production-код.

## Когда использовать

- Юзер говорит «закинь в Claude Design», «дизайн через Claude», «handoff из Claude Design»
- В проекте появилась папка `design-handoff/` или похожая (распакованный zip-bundle)
- Юзер делится URL вида `claude.ai/design/...`
- Юзер просит «нарисуй мокап» и не уточняет инструмент — предложить Claude Design как первый вариант для frontend-задач

## Что такое Claude Design

`claude.ai/design` — отдельный продукт Anthropic. Юзер открывает страницу, общается с AI, тот рисует UI в живом HTML+CSS+JS prototype-формате. Можно итерировать в чате («сделай темнее», «добавь sidebar», «как в Linear»), загружать референсные скриншоты, экспортировать готовое.

**Не путать** с Figma plugin / claude.ai chat / artifacts. Это самостоятельный design-tool.

**Output** — `Handoff` zip-bundle, который юзер скачивает и кладёт в проект.

## Как запустить — пошагово (для юзера)

### 1. Открыть Claude Design
- URL: **`https://claude.ai/design`** (часть подписки Claude — Pro / Max / Team)
- Войти под тем же аккаунтом, что и claude.ai
- Не путать с `claude.ai/new` (это обычный chat) или `claude.ai/artifacts`

### 2. Создать новый проект
- Кнопка `+ New project` (или `Create new`)
- Выбрать тип (вкладки, June 2026): **Prototype**, **Slide deck**, **Template**, **Other**
- Дать имя проекту: `ExampleProduct — Billing Dashboard`

### 2a. Slide deck mode (проверено June 2026)
- Отдельная вкладка «Slide deck» при создании проекта; опция «Use speaker notes»
- Под капотом стартер `deck-stage.js` (~75KB) — канвас-движок слайдов 1920×1080: thumbnails слева, deck controls (prev/next/Reset), кнопка **Present** в шапке, печать в PDF = одна страница на слайд из коробки
- Дека генерится одним self-contained HTML (`<Name>.html`), слайды = `<section class="slide-dark|slide-light">`
- Пайплайн генерации: outline в `scratchpad.md` → styles → слайды по очереди → **само-ревью со скриншотами** (сам находит и чинит overflow/наезды на футер). Полный цикл 5 слайдов ≈ 8–12 минут
- Хорошо ест структурированный бриф: состав слайдов нумерованным списком + палитра hex + шрифты + тёмные/светлые слайды + футер. Мок-цифры делает согласованными (суммы сходятся)

### 3. Первый промпт (структура)
Не «сделай красивый dashboard». Структурированный промпт:

```
Контекст: <что за продукт, кому, на каком языке>
Задача: <что именно за экран>
Бренд: <ключевые цвета, шрифты, тон>
Состав: <какие блоки нужны>
Адаптив: desktop 1440 + tablet 768 + mobile 375
Стиль-референс: <ссылка на скриншот хорошего сайта или название>
Особое: <accessibility, dark mode, états>
```

### Пример промпта
```
Контекст: ExampleProduct — your example AI platform.
Audience: senior-engineers (your demographic).
Задача: страница /dashboard/billing — личный биллинг юзера.
Бренд: основной #3B5BDB, ink #0B1021, акцент cyan #4DABF7, cream #F1F3F5.
Шрифты: Inter Tight (heading), Manrope (body), JetBrains Mono (numbers).
Состав:
  - Hero с текущим тарифом (Plus $X.XX/mo) и датой следующего списания
  - История платежей (таблица с date, amount, status, invoice link)
  - Способ оплаты (карта в маске)
  - Кнопка «Отменить подписку» (модалка confirm)
  - Кнопка «Сменить тариф» (ссылка на /pricing)
Адаптив: desktop 1440 + mobile 375
Dark mode: да
Стиль-референс: как Linear billing, но с нашим брендом.
A11y: focus rings, контраст AA для всех текстов.
Состояния: loading skeleton + empty state (нет истории платежей).
```

### 4. Итерации
В правом side-panel — чат с AI. Уточнения:
- «Hero сделай темнее на 2 ступени, сейчас слишком светлый»
- «Между cards увеличь gap на 50%»
- «Кнопку Cancel сделай secondary, ghost-style»
- «Добавь hover state на строки таблицы»
- «Dark mode toggle в шапке»

Каждое сообщение AI перерисовывает canvas. Можно откатить через History (если запутался).

### 5. Загрузка референсов
- Drag & drop изображение в чат (скриншот Linear / Stripe / Notion)
- Или paste из clipboard (Cmd/Ctrl + V)
- Промпт «Сделай как на референсе, но с нашим брендом»

### 6. Множественные screens
- В одном проекте можно делать **несколько экранов** (вкладки внизу, как страницы в Figma)
- Кнопка `+ Add screen` или `+ New page`
- Удобно: dashboard + billing + checkout одной серией, единые tokens

### 7. Кнопка Handoff (главное)
- В верхнем правом углу canvas → кнопка `Handoff` (или `Export`, иконка ↓)
- Открывается dropdown:
  - **Download bundle** ← это то что нужно для Claude Code
  - Copy link (URL мокапа, для шаринга)
  - Copy code (JSX inline — менее удобно)
- Жми **Download bundle** → скачивается `<project-name>.zip`

### 8. Куда положить bundle в проекте
- Распаковать zip
- Создать `design-handoff/` в корне проекта (если ещё нет)
- Внутри — папка по area: `design-handoff/billing/`, `design-handoff/landing/`, `design-handoff/admin/`
- Положить туда распакованную папку: `design-handoff/billing/your-project-billing/`
- **Опционально** — закоммитить zip-копию рядом, для архива: `design-handoff/billing/your-project-billing.zip`
- Закоммитить в git (handoff = source-of-truth дизайна, держать в репо)

### 9. Сказать Claude Code что handoff готов
Формулировка в чате:
```
В design-handoff/billing/your-project-billing/ лежит handoff
из Claude Design для страницы /dashboard/billing.
Прочитай README + главный HTML целиком, потом перенеси в код проекта,
используя существующие tokens из globals.css и компоненты из
components/academy/. Сначала покажи план — какие файлы создашь,
какие токены добавишь в globals.css. После плана — реализуй.
```

Я (Claude Code) автоматически инициирую этот skill, прочту bundle, дам план, и после твоего «го» реализую.

### 10. Сохранить ссылку на мокап
URL Claude Design мокапа стабильный (`claude.ai/design/<id>`). Стоит сохранять рядом с handoff в `design-handoff/<area>/SOURCE.md`:

```markdown
# Source

- Claude Design URL: https://claude.ai/design/abc123
- Created: see git history
- Author: user@
- Last handoff: see git history
- Iterations: 7
```

Когда нужно поправить дизайн — открыть URL, продолжить работу, новый handoff. Без потери контекста.

## Browser-automation path (когда юзер просит «сам войди»)

Иногда пользователь просит зайти в Claude Design самостоятельно через MCP Playwright и сделать мокап без ручных кликов. Это работает, **но с одной критичной оговоркой**.

### Как технически
```
1. mcp__plugin_playwright_playwright__browser_navigate → claude.ai/design
2. Авторизация через Google OAuth (через cred-store / magic link на Gmail)
3. Кнопка "+ New project" → browser_click
4. Поле промпта → browser_type (передаём весь длинный промпт за раз)
5. Submit → browser_click
6. Wait → browser_wait_for селектора canvas
7. Iteration → browser_type новых сообщений в чат
8. Handoff → browser_click → download zip → файл попадает в Downloads
```

### Pitfall: Cloudflare Turnstile

`claude.ai/design` защищён Cloudflare Turnstile (CAPTCHA «подтвердите что вы человек»). Это **блокирует автоматический логин**. Workflow:

1. Я открываю браузер на странице логина
2. **Останавливаюсь** и говорю юзеру: «Кликни чекбокс "Подтвердите, что вы человек" вручную»
3. Юзер кликает → дальше я продолжаю автоматически

Это нормальное поведение, не баг. Не пытаться обходить — Turnstile отлично детектит автоматизацию.

### Когда browser-automation оправдан
- Юзер хочет «один промпт → готовый handoff» без ручных шагов
- Нужно создать сразу 3+ проекта с единой brand system (я делаю каждый по очереди)
- Длинный детальный промпт удобнее доставить целиком, чем юзеру копипастить
- Юзер хочет посмотреть как «вживую» AI диалогом строит интерфейс

### Когда НЕ оправдан
- Маленький быстрый мокап — юзеру быстрее самому
- Нужно тонкое визуальное чутьё на каждой итерации — я слепой к canvas без screenshot
- Cloudflare блокирует первый раз и юзер не отвечает — лучше сразу делегировать ему

## Реальные примеры промптов (из production)

Эти промпты сработали — оставляю как референс структуры. Не копировать дословно, а использовать как шаблон формы.

### Пример 1: Шаблонизированная система обложек (вебинары пользователя)

**Цель:** не один экран, а **система** где можно подставлять данные → получать варианты.

```
Нужен кастомизируемый HTML-шаблон обложки для вебинаров Your Name.
Цель — единая система, где я могу подставить данные (название, дата, логотип
партнёра, акцентный цвет) и получить уникальную обложку за секунду.
Размер ровно 1200×675 px.

ПАЛИТРА БРЕНДА (your-domain.com):
• #0b1021 — глубокая navy (основной фон)
• #3B5BDB — насыщенный синий (primary accent)
• #4DABF7 — cyan (secondary accent / подчёркивания)
• #FFFFFF — белый (текст)
• #9CA3AF — средний серый (второстепенный текст)

ОБЩИЙ ПАТТЕРН (из референсов, прикладываю ref_1…ref_6):
1. Тёмный фон с графическими акцентами в углу (лучи/линии/dots/grid)
2. СВЕРХУ СЛЕВА: pill-бейдж категории (dark grey фон, белый текст)
3. СЛЕВА: крупный заголовок (Inter bold ~68-80px), снизу cyan линия
4. Под заголовком: короткий подзаголовок (~24-28px, светло-серый)
5. СПРАВА 40-45%: вырезанный портрет (cut-out без фона)
6. СВЕРХУ СПРАВА: лого партнёра (placeholder)
7. ВНИЗУ СЛЕВА: pill-бейдж «Ведущий · Your Name»
8. НИЗ-ЛЕВЫЙ УГОЛ: подпись «your-domain.com» (~18px)

ВАРИАТИВНОСТЬ (6 вариантов):
— A «Вебинар» — navy + cyan diagonal lines, YourFirstName справа
— B «Подкаст» — фиолетово-чёрный градиент, YourFirstName 60% справа
— C «Прямой эфир» — место для 2 портретов
— D «Код/агенты» — const title = "…" в monospace
— E «Сравнение нейросетей» — грид иконок
— F «Промпт-инжиниринг» — синий градиент + окно промпта

ТЗ:
Один HTML-файл с CSS, принимает параметры через CSS variables:
  --title, --subtitle, --badge-top, --badge-bottom,
  --accent-color, --pattern (lines|dots|grid|chevrons|gradient|clean),
  --portrait-url, --logo-url

Шрифт Inter через Google Fonts. Сделай сначала ВАРИАНТ A
(«Мастер-класс "ИИ-агенты", спикер — YourFirstName») — посмотрю и скажу ок.
Потом добавим остальные варианты.
```

**Что хорошо:**
- Чёткие brand tokens вначале
- Структура из 8 пронумерованных пунктов (ничего не пропустишь)
- Вариативность списком A–F — AI делает первый, потом расширяет
- Технические параметры (CSS variables) → код параметризован
- «Сделай сначала А — посмотрю и скажу ок» — итерация

### Пример 2: Лендинг с референсами на соседний проект

**Цель:** новый экран в той же brand system, что уже есть.

```
Сделай hi-fi design полного лендинга ExampleProduct по прикреплённой
спеке (14 секций). Соблюдай brand tokens, используй референсы соседнего
проекта "YourName News Portal" и Figma `YOUR_FIGMA_FILE_ID`
(H-mark node 340:99, Final design node 230:16).
Output — один HTML canvas `ExampleProduct Landing.html`
по образцу `YourName News Redesign.html`.
```

**Что хорошо:**
- Прямая ссылка на готовый соседний проект как brand reference
- Указан Figma file + конкретные node IDs (если знаешь — давай)
- Output format: один HTML canvas с конкретным именем
- Образец-аналог (`YourName News Redesign.html`) — AI берёт точно тот же tone

### Пример 3: Multi-project pipeline

Когда нужны 3+ связанных проекта (Landing + Platform + Admin):

**Промпт-1 (design-system foundation):**
```
Создай design system для ExampleProduct.
Brand: #3B5BDB / #0B1021 / #4DABF7 / #F1F3F5.
Шрифты: Inter Tight (display), Manrope (body), JetBrains Mono (numbers).
Output: один styles.css файл с tokens (colors / spacing / radii / shadows /
type scale / fonts) + components.jsx с базовыми атомами
(HMark logo, Button, Input, Card, Badge, Icon).
Это будет shared library для 3 проектов: Landing, Platform, Admin.
```

**Промпт-2 (Landing) — после готовой DS:**
```
На основе только что созданной design system сделай лендинг
ExampleProduct. Состав: hero / proof / features / pricing /
testimonials / FAQ / footer. Адаптив desktop+mobile.
Используй атомы из components.jsx, токены из styles.css.
```

**Промпт-3 (Platform) — referencing предыдущее:**
```
Используя ту же design system что в предыдущем проекте,
сделай Platform (личный кабинет) ExampleProduct:
sidebar + topbar + dashboard / tracks / track-detail /
lesson-reader / simulator / community / settings.
Reference для mobile screens: Telegram Mini App
проект YOUR_CLAUDE_DESIGN_PROJECT_ID.
```

**Промпт-4 (Admin):**
```
Используя ту же DS, сделай Admin ExampleProduct:
sidebar + topbar + tracks CRUD / lessons CRUD / users /
cohorts / organizations / submissions / live sessions /
analytics. Поддержка multi-tenancy (несколько корпоративных
заказчиков) — в структуре orgs → cohorts → users.
```

После каждого — handoff отдельным bundle'ом. Получаешь 3 zip с единой DS, но разной функциональностью.

## Reference-driven design (продвинутый паттерн)

Когда у юзера уже есть Figma file / готовый соседний сайт / inspiring product:

### С Figma file
1. Я (через Figma plugin) читаю файл, извлекаю tokens, ключевые node screenshots
2. Передаю в Claude Design промпт + screenshots как референсы (drag-drop)
3. AI копирует визуальный язык, но в Claude Design canvas

### С существующим сайтом
1. Делаю screenshots ключевых страниц через Playwright
2. Загружаю в Claude Design как референсы
3. Промпт: «Сделай в этом стиле, но для нашего домена»

### С multi-source brand
Часто бренд распределён: Figma + основной сайт + лендинг конференции + соцсети. В промпт дать **все источники**, а не один:
```
Бренд распределён в 3 местах:
1. Figma `YOUR_FIGMA_FILE_ID` (главный source)
2. Лендинг your-domain.com (визуальная реальность)
3. Презентация industry conference 2025 (тон выступления)
Реши конфликты в пользу Figma.
```

## Когда обновлять этот skill

- Claude Design выкатывает новый формат bundle (например, теперь TypeScript + React сразу)
- Меняется структура `README.md` в bundle
- Появляется новый паттерн взаимодействия (например, live-link на claude.ai вместо zip)
- Найдены новые анти-паттерны на практике
- Новые рабочие промпт-шаблоны — добавлять в раздел «Реальные примеры»

Update сюда — это коллективная память между сессиями.

## Pipeline (4 фазы)

```
[1] Юзер мокапит в claude.ai/design
        ↓ кнопка "Handoff"
[2] Скачивается zip → юзер кладёт в `design-handoff/<area>/`
        ↓
[3] Coding agent (я) читает bundle и переносит pixel-perfect в стек проекта
        ↓
[4] Verification: сверка с прототипом + интеграция с дизайн-системой проекта
```

## Handoff bundle structure (что приходит)

Распакованный zip всегда содержит:

```
<project-slug>/
├── README.md                    ← read-this-first для coding agent (важно!)
└── project/
    ├── <Name>.html              ← главный файл мокапа (читать целиком)
    ├── design-canvas.jsx        ← JSX-версия канваса (опционально)
    ├── components.jsx           ← shared атомы (HMark, Icon, Button, ...)
    ├── chrome.jsx               ← chrome платформы (sidebar, topbar) если применимо
    ├── styles.css               ← design tokens + base styles
    ├── components/              ← пустые директории (заглушки export'а)
    ├── screens/
    ├── styles/
    ├── fonts/
    └── uploads/                 ← пользовательские референсы
```

**Главный файл** — тот HTML, который юзер «имел открытым» когда нажал Handoff. Его и нужно читать первым.

## Workflow — pixel-perfect implementation

### Шаг 1. Прочитать README.md в bundle
Там обращение к coding-agent с инструкцией. **Не пропускать** — там часто специфичные пометки от юзера.

### Шаг 2. Прочитать главный HTML целиком
- НЕ skim, НЕ first-100-lines. **Top to bottom**.
- Заметить inline `<style>` блоки, `<script>` блоки, импорты CSS.
- Заметить `data-*` атрибуты — это намеки на интерактивность.

### Шаг 3. Прочитать всё что главный HTML импортирует
- `styles.css` (полностью — там design tokens)
- `components.jsx`, `chrome.jsx`, `design-canvas.jsx`
- Любой imported font
- НЕ читать пустые папки (`components/`, `screens/` — это zip-export артефакты)

### Шаг 4. Извлечь дизайн-систему
Из bundle вытащить:
- **Tokens** — цвета (`--primary`, `--deep`, `--cream`), spacing, radii, shadows, type scale
- **Atoms** — кнопки, инпуты, badges, иконки
- **Layouts** — grid систему, breakpoints
- **Patterns** — карточки, табы, модалки
- **Brand** — лого, шрифты, тоны

### Шаг 5. Сравнить с дизайн-системой проекта
- Уже есть похожие токены? → переиспользовать существующие имена
- Уже есть Button компонент? → не делать новый, обновить существующий
- Похожий паттерн уже использовался? → следовать конвенции
- Конфликт между прототипом и проектом — спросить юзера

### Шаг 6. Перенести в стек проекта
- **НЕ копировать структуру прототипа** дословно
- HTML/CSS/JS прототипа = **референс**, не production code
- Recreate **визуальный output** в нативной технологии (React + CSS-in-JS / Tailwind / styled-components — что в проекте)
- Использовать существующие компоненты проекта где возможно
- Tokens прототипа → CSS variables проекта (в `globals.css` или дизайн-системе)

### Шаг 7. Quality gates
- ✅ Visual diff: открыл прототип в IDE-предпросмотре + свою реализацию рядом, сравнил
- ✅ Responsive: проверил breakpoints (если в прототипе есть)
- ✅ Dark mode: если в прототипе есть, перенёс
- ✅ Hover/active states: если кодились в прототипе, перенёс
- ✅ A11y: контраст, focus rings, semantic HTML, aria-label

## Анти-паттерны (НЕ делать)

| Анти-паттерн | Почему плохо | Как правильно |
|---|---|---|
| Запустить HTML в браузере и сделать скриншот | Тратит время; всё нужное **в коде** | Читать HTML+CSS как source-of-truth |
| Skim главный HTML | Пропустишь критичные детали (поведение, transitions) | Читать целиком |
| Скопировать `<div>` структуру прототипа в React 1-в-1 | Прототип не учитывает реактивность и props | Воссоздать **визуальный output** в идиомах проекта |
| Создать новые токены вместо существующих | Дизайн-система проекта станет фрагментированной | Сначала проверить существующие, потом дополнять |
| Не спрашивать про двусмысленности | Сделаешь не то, потеряешь время | Уточнить у юзера ДО старта реализации |
| Игнорировать `README.md` bundle | Там обычно ключевая инструкция | Читать первым |
| Реализовать ВСЁ за один раз без согласования | Долго, риск переделок | Реализовать 1 экран, показать, получить feedback, продолжать |

## Адаптация под существующий дизайн (важно)

Если в проекте уже есть дизайн-система — приоритет за ней. Прототип Claude Design — **направление**, не догма. Примеры:

- В прототипе кнопка `border-radius: 14px`, в проекте все кнопки `--r-md: 12px` → берём `12px`, не `14px`
- В прототипе `font-family: 'Manrope'`, в проекте уже есть `--h-font-body: Inter` → ставим в `globals.css` ОДИН раз и заменяем на единый
- В прототипе цвет `#3B5BDB`, в проекте `--h-primary: #3B5BDB` → используем токен, не хардкод
- В прототипе компонент Card по своему, в проекте есть `<ACard>` → расширяем `ACard` props, не делаем новый

Если расхождение **визуально критичное** — спросить юзера, не молчать.

## Tips для пользователя (как делать эффективные мокапы)

Это шпаргалка, чтобы юзер получал лучший output из Claude Design:

### 1. Начинать с дизайн-системы
Первый промпт: «Создай design tokens (цвета, шрифты, spacing, radii) для edtech-платформы про AI, аудитория your target users, тон премиум, бренд your-domain.com (#3B5BDB / #0B1021)». Получаешь `styles.css` фундамент. Потом — экраны на этих tokens.

### 2. Просить варианты
Не «сделай dashboard», а «сделай 3 варианта dashboard: (а) карточный grid, (б) список с metrics в шапке, (в) split с sidebar metrics + main feed». Дешевле, дальше выбираешь.

### 3. Загружать референсы
Скриншоты Linear / Stripe / Vercel / etc. → «как в этом, но с нашими tokens». AI отлично копирует стиль.

### 4. Итерировать на конкретике
Не «сделай круче», а «увеличь spacing между card на 50%», «hero сделай темнее на 2 шага», «эту кнопку перекрась в `--cyan`».

### 5. Просить responsive сразу
В первом промпте указывать «desktop 1440 + tablet 768 + mobile 375». Иначе AI делает только desktop, потом дороже добавлять.

### 6. Просить states
«Кнопка с hover/active/disabled/loading». Иначе будет только default.

### 7. Просить dark mode сразу
Если в проекте поддерживается dark — указывать в промпте, AI сделает оба + отметит токены.

### 8. Не делать gigantic экраны
Один screen = один экран. Если нужно 5 экранов — 5 отдельных мокапов. AI лучше фокусируется на узкой задаче.

### 9. Handoff чаще
Не копить 10 экранов, потом handoff. Делать handoff после 1–2 экранов, пробовать имплементацию, понять расхождения с дизайн-системой проекта, продолжать.

### 10. Сохранять URL мокапа
Claude Design URL остаются — после handoff можно вернуться, доработать, новый handoff. URL стоит коммитить в `design-handoff/<area>/SOURCE.md`.

## Когда уточнять у юзера до старта

- В прототипе есть копи на английском, но проект русский → переводить буквально или адаптировать?
- В прототипе есть состояния которые в БД нет (например, «notifications center») → реализовывать UI на mock-данных или сначала backend?
- Прототип конфликтует с существующим UI проекта (стиль, токены, паттерны) → к какому стандарту приводим?
- Прототип игнорирует accessibility (контраст < 4.5, нет focus rings) → исправлять при переносе?
- В прототипе data-vis (charts) на mock-данных → подключать реальные queries сразу или после?
- В прототипе анимации/transitions сложные → реализовывать (CSS transitions / Framer Motion / etc.)?

## Структура коммита handoff в проект

После реализации одного handoff'а коммит должен быть:
```
feat(<area>): implement Claude Design handoff for <screen>

- Imported tokens from design-handoff/<area>/styles.css → globals.css
- Added <ComponentName> in components/<area>/
- Wired to existing <ProjectComponent> where applicable
- A11y: added focus rings + aria-label
- Responsive: desktop + tablet + mobile

Source: design-handoff/<area>/<bundle>/
```

## Когда обновлять этот skill

- Claude Design выкатывает новый формат bundle (например, теперь TypeScript + React сразу)
- Меняется структура `README.md` в bundle
- Появляется новый паттерн взаимодействия (например, live-link на claude.ai вместо zip)
- Найдены новые анти-паттерны на практике

Update сюда — это коллективная память между сессиями.
