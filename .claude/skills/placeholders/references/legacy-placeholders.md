<!-- LEGACY: полное тело скилла 'placeholders' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: placeholders
description: Стандартные плейсхолдеры для иллюстраций, аватаров, графиков, изображений в дизайне. НЕ генерируй stock-картинки и сложный SVG — используй понятные плейсхолдеры с подписью.
when_to_use: В прототипе/слайдах/лендинге нужно изображение которого нет, или иконка/график. Перед animations / interactive-prototype если макеты пустые.
---

# Placeholders

Не пытайся рисовать сложный SVG руками или генерировать AI-stock. Используй унифицированные плейсхолдеры. Они быстрее, чище читаются и не отвлекают от структуры.

## Базовый image placeholder

```css
.ph-img {
  background:
    linear-gradient(135deg, #ddd 25%, transparent 25%, transparent 75%, #ddd 75%, #ddd) 0 0/16px 16px,
    linear-gradient(135deg, #ddd 25%, transparent 25%, transparent 75%, #ddd 75%, #ddd) 8px 8px/16px 16px,
    #f5f5f5;
  display: flex; align-items: center; justify-content: center;
  color: #999; font: 12px/1 monospace;
  border-radius: 8px;
  aspect-ratio: 16 / 9;
}
```

```html
<div class="ph-img" style="aspect-ratio: 4/3">
  [Скриншот dashboard · 1200×900]
</div>
```

**Подпиши** что должно быть, не молчи.

## Аватары

Цветные круги с инициалами — никаких avatar-as-a-service:

```jsx
function Avatar({ name, size = 40 }) {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#A29BFE', '#FD79A8'];
  const idx = name.charCodeAt(0) % colors.length;
  const initials = name.split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase();
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: colors[idx], color: '#fff', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      fontWeight: 600, fontSize: size * 0.4,
    }}>{initials}</div>
  );
}
```

```jsx
<Avatar name="Your Name" size={48} />  // → "ЖХ"
```

## Logo placeholder

Не вставляй настоящие лого Stripe/Apple — делай плейсхолдер:

```html
<div style="
  padding: 8px 16px; border: 1px dashed #999; border-radius: 4px;
  font: 600 12px/1 monospace; color: #666;
">[ACME LOGO]</div>
```

Для «trusted by» секций:
```html
<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; opacity: 0.6;">
  <div class="logo-ph">[ClientCorp1]</div>
  <div class="logo-ph">[ClientCorp5]</div>
  <div class="logo-ph">[ClientCorp3]</div>
  <div class="logo-ph">[ClientCorp4]</div>
  <div class="logo-ph">[ClientCorp2]</div>
</div>
```

## Charts placeholder

Не рисуй сложные графики — простой SVG-каркас:

```jsx
function ChartPlaceholder({ kind = 'line', label = 'Chart' }) {
  if (kind === 'line') return (
    <svg viewBox="0 0 200 80" style={{ width: '100%' }}>
      <polyline points="0,60 25,55 50,50 75,40 100,35 125,30 150,20 175,15 200,5"
        stroke="#3b82f6" strokeWidth="2" fill="none" />
      <text x="10" y="75" fontSize="10" fill="#999">{label}</text>
    </svg>
  );
  if (kind === 'bars') return (
    <svg viewBox="0 0 200 80">
      {[40, 60, 30, 70, 50, 80, 45, 65].map((h, i) => (
        <rect key={i} x={i * 25 + 5} y={80 - h} width={20} height={h} fill="#3b82f6" />
      ))}
    </svg>
  );
  if (kind === 'donut') return (
    <svg viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="40" stroke="#e5e7eb" strokeWidth="12" fill="none" />
      <circle cx="50" cy="50" r="40" stroke="#3b82f6" strokeWidth="12" fill="none"
        strokeDasharray="180 251" transform="rotate(-90 50 50)" />
    </svg>
  );
}
```

## Иконки

Не генерируй кастомные SVG — используй **lucide-react стиль** через Babel-friendly inline:

```jsx
function Icon({ name, size = 20 }) {
  const icons = {
    check: <path d="M20 6L9 17l-5-5" />,
    arrow: <path d="M5 12h14m-7-7l7 7-7 7" />,
    user:  <><circle cx="12" cy="8" r="4" /><path d="M4 21v-2a4 4 0 014-4h8a4 4 0 014 4v2" /></>,
    plus:  <path d="M12 5v14m-7-7h14" />,
    x:     <path d="M18 6L6 18M6 6l12 12" />,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
}
```

10 базовых иконок покрывают 80% UI. Если нужна редкая (вроде «database», «git-branch») — копируй из [lucide.dev](https://lucide.dev) и вставляй в этот же объект.

## User-uploaded references

Если юзер скинул свой скриншот / логотип / hero-image — клади в `uploads/` и используй напрямую:

```html
<img src="uploads/hero_main.png" alt="Hero" style="width: 100%; border-radius: 12px">
```

Не превращай в плейсхолдер!

## Антипаттерны

- AI-сгенерированный stock через DALL-E на каждый пустой блок → дорого, выглядит generic
- Lorem-pixum / picsum.photos → внешние URL, ломаются в offline
- Делать сложный SVG-портрет руками → 200 строк кода, плохо читается
- Реальные лого партнёров без апрува → юридический риск
- Плейсхолдер без подписи (просто пустой div) → не понятно что должно быть
- Картинки слишком похожие на финальные → junior-разраб может решить что финальные и не заменить
