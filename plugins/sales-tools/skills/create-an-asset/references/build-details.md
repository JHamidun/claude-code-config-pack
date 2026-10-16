# Build details: шаблоны контента, workflow-демо, дизайн-система

Справочник к `create-an-asset`. Открывать на фазе сборки, когда нужен точный формат.

## Шаблоны секций (контент)

### Hero / Intro
```
Headline: "[Цель проспекта] with [Продукт селлера]"
Subhead: привязка к их заявленному приоритету или топ-проблеме индустрии
Metrics: 3-4 факта о проспекте (показывает, что сделали домашку)
```

### Their Priorities (discovery follow-up)
- Их боли их же словами (цитаты из транскриптов)
- Показать, что услышали → связать каждую с тем, как помогаем

### Solution Mapping (на каждую боль)
```
├── The challenge (их словами)
├── How [Product] addresses it
├── Proof point / пример
└── Outcome / benefit
```

### Use Cases: 3-5 кейсов, каждый = мокап/демо + квантифицированный импакт + «как работает» в 3-4 шага + релевантность их индустрии/роли.

### ROI-калькулятор
Inputs из research (число юзеров, текущие затраты, ожидаемое улучшение %) →
Outputs: годовая экономия, стоимость решения, net ROI, payback period.
Допущения показать явно и сделать редактируемыми.

### Why Us: дифференциаторы vs альтернативы, security/compliance, модель поддержки, логотипы/цитаты клиентов.

### Next Steps / CTA: конкретное действие (не «давайте созвонимся»), контакты, таймлайн, что случится после.

## Deck-style: скелет

```
1. Title (логотипы проспекта + селлера, partnership framing)
2. Agenda
3-N. Секция на слайд (2-3 слайда для плотных)
N+1. Summary  ·  N+2. Next steps / CTA  ·  N+3. Appendix
```
Один месседж на слайд, визуал > текст, спикер-ноты обязательны.

## One-pager: скелет

```
HERO: "[Цель проспекта] with [Продукт]"
3 KEY POINTS (иконка + 2-3 предложения каждый)
PROOF POINT (метрика, цитата или кейс)
CTA + контакты
```

## Workflow / Architecture demo

### Структура по сложности
| Компонентов | Структура |
|---|---|
| 3-5 | Одна диаграмма с аннотациями шагов |
| 5-10 | Zoomable canvas + пошаговый walkthrough |
| 10+ | Multi-layer (overview → detail) + guided tour |

### Стандартные элементы
Title bar `[Scenario] — Powered by [Product]` · ноды компонентов · анимированные стрелки потока · sidebar с объяснением текущего шага · контролы Play/Pause/Step/Reset · callout-аннотации на решениях · превью данных на каждом шаге.

### Определение компонента
```yaml
component:
  id: "snowflake"
  label: "Snowflake Data Warehouse"
  type: "database"  # human | document | ai | database | api | middleware | output
  icon: "database"
  description: "Financial performance data"
  brand_color: "#29B5E8"
```

### Определение шага
```yaml
step:
  number: 1
  from: "human"
  to: "claude"
  action: "Initiates performance review"
  description: "Sarah, a Brand Analyst at [Prospect], kicks off..."
  data_example: "Review request: Nike brand, Q4 2025"
  duration: "~1 second"
  value_note: "No manual data gathering required"
```

Нарратив сценария писать конкретно: именованный персонаж, реальные цифры в данных, ✓/⚠️ в сравнениях actuals vs obligations.

### Иконки компонентов
| Type | Icon |
|------|------|
| human | 👤 / person SVG |
| document | 📄 / file SVG |
| ai | 🤖 / brain SVG |
| database | 🗄️ / cylinder SVG |
| api | 🔌 / plug SVG |
| middleware | ⚡ / hub SVG |
| output | 📊 / screen SVG |

## Дизайн-система (dark theme + бренд проспекта)

```css
:root {
    --brand-primary: #[из research];
    --brand-secondary: #[из research];
    --brand-primary-rgb: [r, g, b];
    --bg-primary: #0a0d14;  --bg-elevated: #0f131c;
    --bg-surface: #161b28;  --bg-hover: #1e2536;
    --text-primary: #fff;
    --text-secondary: rgba(255,255,255,0.7);
    --text-muted: rgba(255,255,255,0.5);
    --accent: var(--brand-primary);
    --accent-glow: rgba(var(--brand-primary-rgb), 0.3);
    --success: #12b886; --warning: #f59e0b; --error: #ef4444;
}
```

Шрифт: Inter / system sans. h1 2.5rem/700, h2 1.75rem/600, h3 1.25rem/600, body 1rem/1.6.

Карточки: bg-surface, border 1px rgba(255,255,255,0.1), radius 12px, hover — elevation + border glow. Transitions 200-300ms ease.

Ноды workflow-демо: border 2px brand, radius 12px; `.active` — box-shadow 0 0 20px accent-glow; human-ноды — тёплый border #f59e0b. Активные стрелки: stroke accent, `stroke-dasharray: 8 4` + бегущая dash-анимация. Canvas: radial-gradient + subtle grid.

## Fallback-цвета, если бренд не извлёкся

| Industry | Primary | Secondary |
|----------|---------|-----------|
| Technology | #2563eb | #7c3aed |
| Finance | #0f172a | #3b82f6 |
| Healthcare | #0891b2 | #06b6d4 |
| Manufacturing | #ea580c | #f97316 |
| Retail | #db2777 | #ec4899 |
| Energy | #16a34a | #22c55e |
| Default | #3b82f6 | #8b5cf6 |
