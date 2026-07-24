<!-- LEGACY: полное тело скилла 'perf-audit' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: perf-audit
description: Lighthouse-based performance audit. Меряет LCP / CLS / TBT / FCP / TTI на artifact'е, выдаёт actionable советы. Перед production-deploy или когда юзер жалуется на «медленно».
when_to_use: Перед dev-handoff если артефакт пойдёт в prod, после крупных изменений с тяжёлыми ассетами, когда юзер говорит «оптимизируй». Параллельно с a11y-audit на финале.
---

# Perf audit

Lighthouse через CLI или programmatic API. Меряет Core Web Vitals + говорит что чинить.

## Установка

```bash
npm i -g lighthouse
# или programmatic:
npm i -D lighthouse playwright
```

## CLI quick-check

```bash
# Запустить локальный сервер (если артефакт не self-contained)
python3 -m http.server 8080 &

# Проверить
lighthouse http://localhost:8080/artifact.html \
  --output html \
  --output-path ./perf-report.html \
  --only-categories=performance \
  --form-factor=desktop \
  --quiet \
  --chrome-flags="--headless"

# Mobile
lighthouse http://localhost:8080/artifact.html \
  --form-factor=mobile \
  --output json --output-path ./perf-mobile.json \
  --quiet --chrome-flags="--headless"
```

HTML report — для визуального ревью (открыть в браузере). JSON — для программного парсинга.

## Programmatic через Playwright + Lighthouse

```js
const { chromium } = require('playwright');
const lighthouse = require('lighthouse');

async function audit(url, opts = {}) {
  const browser = await chromium.launch({ args: ['--remote-debugging-port=9222'] });
  const result = await lighthouse(url, {
    port: 9222,
    output: 'json',
    onlyCategories: ['performance'],
    formFactor: opts.mobile ? 'mobile' : 'desktop',
    screenEmulation: { disabled: true },
  });
  await browser.close();

  const lhr = result.lhr;
  return {
    score: Math.round(lhr.categories.performance.score * 100),
    metrics: {
      LCP: lhr.audits['largest-contentful-paint'].numericValue,
      CLS: lhr.audits['cumulative-layout-shift'].numericValue,
      TBT: lhr.audits['total-blocking-time'].numericValue,
      FCP: lhr.audits['first-contentful-paint'].numericValue,
      TTI: lhr.audits['interactive'].numericValue,
      SpeedIndex: lhr.audits['speed-index'].numericValue,
    },
    opportunities: lhr.categories.performance.auditRefs
      .filter(a => a.group === 'load-opportunities')
      .map(a => lhr.audits[a.id])
      .filter(a => a.score < 1)
      .map(a => ({ title: a.title, savings: a.details?.overallSavingsMs })),
  };
}
```

## Core Web Vitals — пороги

| Метрика | Хорошо | Норма | Плохо |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5-4s | > 4s |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1-0.25 | > 0.25 |
| **TBT** (Total Blocking Time) | < 200ms | 200-600ms | > 600ms |
| **FCP** (First Contentful Paint) | < 1.8s | 1.8-3s | > 3s |
| **TTI** (Time to Interactive) | < 3.8s | 3.8-7.3s | > 7.3s |

Lighthouse score:
- 90-100: green
- 50-89: yellow (надо смотреть)
- 0-49: red (production-стоп)

## Типовые проблемы prototype'ов

### 1. Огромные unoptimized images
```bash
# Найти > 500KB в uploads/
find uploads/ -type f -size +500k
# Решение: convert + resize через imagemagick / sharp
sharp -i source.png -o source-1200.webp --resize 1200 --quality 80
```

### 2. React+Babel через CDN — не тащи в prod
- В prototype OK (быстрая итерация)
- В prod — заменить на bundle (Vite/webpack/Next), Babel-transform в build-time

### 3. Шрифты грузятся блокирующе
```html
<!-- Плохо -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">

<!-- Лучше -->
<link rel="preload" as="font" href="/fonts/inter-var.woff2" type="font/woff2" crossorigin>
<style>
  @font-face { font-family: 'Inter'; font-display: swap;
              src: url('/fonts/inter-var.woff2') format('woff2-variations'); }
</style>
```

`font-display: swap` → текст показывается в fallback пока Inter грузится. Иначе FOIT (text invisible).

### 4. CLS от изображений без size
```html
<!-- Плохо: layout прыгает когда картинка догружается -->
<img src="hero.jpg">

<!-- Хорошо: размер зарезервирован -->
<img src="hero.jpg" width="1200" height="675" alt="...">
```

### 5. Animations без will-change или transform
```css
/* Плохо */
.card { transition: top .3s; }
.card:hover { top: -4px; }    /* перерасчёт layout каждый кадр */

/* Хорошо */
.card { transition: transform .3s; }
.card:hover { transform: translateY(-4px); }   /* GPU compositor only */
```

## Output — actionable отчёт

После audit пишешь summary юзеру:

```markdown
# Perf audit: artifact.html

**Score:** 87/100 (mobile) | 95/100 (desktop)

## Core Web Vitals
- LCP: 2.3s ✅
- CLS: 0.08 ✅
- TBT: 340ms ⚠️ (норма 200ms)

## Quick wins (savings ~500ms)
1. uploads/hero_main.png — 1.2MB. Сжать до 200KB через webp.
2. Babel standalone — 1.5MB. Если идём в prod, пересобрать с Vite.
3. JetBrains Mono — грузится 4 weights, нужно 2.

## Не критично
- Третий-сторонние: нет
- Cache headers: file:// (relevant только для prod)
```

## Когда НЕ делать perf-audit

- На прототипе для презентации (не идёт в prod) — потеря времени
- Артефакт уже imported в реальный проект — там perf будет другой
- На ранней итерации — сначала структура, потом перформанс

## Антипаттерны

- Гнаться за 100/100 → переоптимизация, теряешь читабельность кода
- Оптимизировать CDN скрипты которых не контролируешь → бесполезно
- Меряет на powerful laptop, не на throttled CPU → реальный mobile хуже
- Не различать LCP-image и LCP-text → разная стратегия
- Игнорировать CLS («оно мелкое») → юзер на mobile его чувствует
- Не сохранять report.html в git → не видно регрессий между deploys
