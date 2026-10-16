# Meta Ads Core Concepts

## Ad Auction Mechanics

### How Meta Determines Ad Delivery

Every ad impression is an auction. Meta considers three factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Bid** | ~30% | How much you're willing to pay (manual or auto) |
| **Estimated Action Rate** | ~50% | Meta's prediction of user converting |
| **Ad Quality** | ~20% | Relevance, engagement signals, feedback |

**Total Value = Bid × Estimated Action Rate + Ad Quality Score**

The ad with the highest Total Value wins the impression.

### Implications for Analysis

- Low spend ≠ bad ad. May mean high competition in that segment.
- High CTR with low conversions = targeting problem, not creative problem.
- Sudden CPA spikes often correlate with audience saturation, not ad fatigue.

### Формула аукциона в свёрнутом виде и чем Meta отличается от соседей

> Источник блока: эксперт, Meta Ads занятие 1, курс методология (поток N).

На занятии ту же формулу дают в свёрнутом виде: **`Общая ценность = Ставка × Качество объявления`**, где качество = **результативность объявления + релевантность объявления**. Это не другая формула, а та же самая: `Estimated Action Rate` — это и есть результативность, `Ad Quality` — релевантность. Побеждает не самый богатый, а тот, чьё объявление несёт **максимальную ценность для пользователя**.

Неофициально на цену влияют ещё три вещи, которых нет ни в одной формуле: **история и статистика аккаунта**, **время показа**, **размер бюджета**. При диагностике это значит, что одинаковый креатив в новом и старом аккаунте закупается по разной цене — и «мы сделали всё так же, а дороже» не парадокс.

**Чем это отличается от других площадок** (нужно, когда клиент переносит ожидания из Директа):

| Площадка | Механика | Что меняется для диагноста |
|---|---|---|
| **Meta** | ставка × качество (результативность + релевантность) | качество считается **с обеих сторон** — и креатив, и аудитория; дорогой bid не спасает слабый креатив |
| **Яндекс.Директ, поиск** | **VCG-аукцион** | добавляется **релевантность объявления поисковому запросу** — есть внешний якорь (запрос), которого в Meta нет вообще |
| **РСЯ** | **GCC-аукцион** | как и в Meta, запроса нет, но правила списания другие — переносить логику ставок из Директа в Meta напрямую нельзя |
| **Google Ads** | рейтинг = ставка × Quality Score (1-10) | комбинация качества, ставки и контекста; ближе к Директу, чем к Meta |

**Отдельный факт для управления ожиданиями: аукцион постоянно дорожает** (на доске — со ссылкой на earnings presentation Meta, slide 13, ⚠️ проверить актуальность). Поэтому рост CPM год к году сам по себе не диагноз и не повод искать поломку — сравнивать надо с рынком за тот же период, а не с собственными цифрами прошлого года.

## Точка баланса (diminishing returns на уровне аккаунта)

> Источник: экспертная методология. Meta Ads занятие 1; на курсе помечено как сквозной тезис — «транслирую во всех абсолютно модулях».

> При определённом рынке, аудитории и бюджете существует **точка баланса, после которой каждая последующая единица результата будет дороже и дороже**.

Это та же кривая diminishing returns, что в `breakdown_effect.md`, но взятая на уровне всего аккаунта, а не сегмента. Практический смысл — в том, какой вопрос она запрещает. Вопрос «как снизить CPA?» при уже пройденной точке баланса не имеет ответа в настройках кабинета: рынок, аудитория и бюджет заданы, дешёвые конверсии выбраны. Осмысленных ходов остаётся два — согласиться на текущий CPA и расти в объёме (горизонтальное масштабирование: новые аудитории, гео, офферы) или менять сам продукт и экономику.

Числовая иллюстрация с доски: **9 конверсий по $3 = $27** против **8 конверсий по $3,25 = $26**. Смотреть надо на пару «сколько результатов за сколько денег» целиком, а не на CPA отдельно: средняя цена и объём ходят вместе, и решение «взять CPA пониже» почти всегда означает «взять результатов поменьше».

> ⚠️ Пара чисел выписана с доски как есть, и в таком виде арифметика тезис не доказывает: в ней больший объём идёт с **меньшей** средней ценой. Сам тезис о точке баланса от этого не отменяется (он подтверждается кривой в `breakdown_effect.md`), но конкретно эти числа как учебный пример лучше не цитировать — считай на своих.

## Pacing Algorithm

### How Meta Spends Your Budget

Meta doesn't spend budget evenly. It uses **pacing** to:
1. Find cheapest opportunities first (front-loading efficiency)
2. Spread delivery across the day to find optimal times
3. Accelerate when it finds high-converting segments
4. Slow down when approaching diminishing returns

### Pacing States

| State | What's Happening | What to Do |
|-------|-----------------|------------|
| **Under-pacing** | Not spending full budget | Audience too small, bid too low, or ad quality issues |
| **On-pace** | Spending roughly on budget | Normal operation |
| **Over-pacing** | Spending faster than expected | Found high-converting segment, may exhaust budget early |

### Budget vs Spend Analysis

| Spend Pattern | Likely Cause | Recommendation |
|--------------|-------------|----------------|
| <50% budget used | Audience too narrow, low bids | Expand audience or increase bid |
| 50-90% budget | Normal pacing variance | Monitor, no action needed |
| 100% budget, CPA rising | Audience saturation | Expand audience or reduce budget |
| Budget spikes at certain hours | Algorithm found peak times | Consider dayparting if pattern is consistent |

## Learning Phase

### What It Is

Meta needs ~50 conversions per ad set per week to optimize delivery. During learning phase, performance is volatile and CPA is typically higher.

### Learning Phase Lifecycle

| Phase | Conversions | CPA Behavior | Action |
|-------|-------------|-------------|--------|
| **Initial (0-10)** | Very few | Very high, volatile | Do NOT touch settings |
| **Learning (10-50)** | Growing | High but stabilizing | Monitor, no changes |
| **Optimized (50+/week)** | Steady | Stable, near target | Optimize cautiously |
| **Learning Limited** | <50/week | Stuck, not improving | Consolidate or restructure |

### Critical Rules During Learning

1. **No edits** to budget, bid, targeting, or creative during learning
2. **No pausing/restarting** — resets learning
3. **Budget changes**: Only ±20% at a time after learning phase
4. **Creative changes**: Add new ads, don't edit existing ones

### Learning Limited Resolution

| Cause | Solution |
|-------|----------|
| Budget too low | Increase budget or consolidate ad sets |
| Audience too small | Expand targeting or remove exclusions |
| Too many ad sets | Consolidate into fewer ad sets |
| Conversion event too rare | Switch to higher-funnel event temporarily |
| Too many creative variants | Reduce to 3-6 per ad set |

## Attribution Windows

### Default Attribution Settings

| Event Type | Default Window | What It Means |
|------------|---------------|---------------|
| Click-through | 7 days | Conversion within 7 days of click |
| View-through | 1 day | Conversion within 1 day of seeing ad |

### Attribution Analysis Rules

1. **Compare apples to apples**: Same attribution window across all campaigns
2. **View-through inflation**: 1-day view is often 30-60% of reported conversions. Consider click-only for conservative analysis.
3. **Cross-campaign attribution**: Same user may be attributed to multiple campaigns. Deduplicate using external analytics.

## Ad Fatigue vs Audience Saturation

| Signal | Ad Fatigue | Audience Saturation |
|--------|-----------|-------------------|
| Frequency | Rising (>3) | Rising (>5) |
| CTR | Declining | Declining |
| CPA | Rising | Rising |
| Reach | Same audience | Audience exhausted |
| Solution | New creatives | New audience |
| Indicator | Same ads, same audience | New ads, same CPA |

### Diagnosis Flow

1. Check frequency. If <3, neither fatigue nor saturation.
2. If frequency >3, introduce new creatives.
3. If new creatives don't help, it's audience saturation → expand targeting.
4. If new creatives help temporarily, it's ad fatigue → creative rotation strategy.

## Campaign Structure Best Practices

### Recommended Structure

| Level | Purpose | Typical Count |
|-------|---------|---------------|
| Campaign | Objective grouping | 3-5 per account |
| Ad Set | Audience/placement grouping | 3-7 per campaign |
| Ad | Creative variants | 3-6 per ad set |

### Consolidation Principles

- Fewer ad sets = more data per ad set = faster learning
- Combine similar audiences into one ad set
- Use Advantage+ placements instead of placement-specific ad sets
- Budget at campaign level (CBO) when possible
