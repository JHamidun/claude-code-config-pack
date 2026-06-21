# Scoring — confidence, product-fit, reachability

Three independent scores per lead. Keep them separate (a high-confidence ID can still be a poor fit).

## 1. Identity confidence — "кто это" (1-10)

How sure are we this is the right person/company.

| Signal | Points |
|--------|--------|
| Corporate email domain → company (deterministic) | +4 |
| Name confirmed on ≥2 independent public sources | +3 |
| ЕГРЮЛ/DaData confirms role/company | +2 |
| Single source / inferred / fuzzy name match | +1 |
| Conflicting sources | −2 |

8-10 High · 5-7 Medium · <5 Low (treat as hypothesis, verify before outreach).

## 2. Product-fit (1-10)

Fit for your B2B products. Read your own marketing-context skill (if you have one) for the current ICP/personas; baseline:

| Factor (weight) | What raises it |
|-----------------|----------------|
| Размер/выручка (25%) | mid-large, есть L&D/обучение бюджет |
| Роль (25%) | L&D/HRD/корп. университет/CDTO/директор трансформации = ЛПР под обучение/AI |
| Сигналы «почему сейчас» (20%) | найм AI-навыков, цифровая трансформация, новый CDO, рост штата |
| Отрасль (15%) | банк/телеком/ритейл/промышленность с программами обучения |
| Пейн под продукт (15%) | ваш продукт A (напр. корп. AI) / продукт B (b2b) / продукт C (EdTech) |

## 3. Reachability — «легко достучаться» (1-10)

| Criterion | Weight |
|-----------|--------|
| Публичность (интервью/спикерства 12 мес.) | 20% |
| Общая повестка с вашей компанией | 25% |
| Точка входа (конференция, общий контакт, PR-служба, приёмная) | 20% |
| LinkedIn открыт (→ InMail) | 10% |
| Публичный Telegram / активные комментарии | 10% |
| Размер аудитории (охват партнёрства) | 15% |

Reality check: ~70% RU bank execs closed LinkedIn post-2022 — a "private profile" response is a correct *insight*, not a failure; don't bank on InMail, route via company/PR.

## Color bands (apply to all three in Excel via PatternFill)

- **8-10** green `C6EFCE` — приоритет
- **5-7** yellow `FFEB9C` — нужен тёплый канал / верификация
- **<5** red `FFC7CE` — отложить / искать через сеть

## Verdict (Mode A)

Combine: **qualify** (confidence ≥6 AND fit ≥6) · **hand to manager** (fit ≥6, reachability via warm channel) · **drop** (fit <4 or confidence <4). Always state the reason + the entry point.
