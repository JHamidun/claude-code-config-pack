# Глоссарий метрик

## Сделки

| Метрика | Формула | Что значит |
|---------|---------|-----------|
| Total deals | `count(deals where ASSIGNED_BY_ID = X)` | Все сделки менеджера в периоде |
| WON | `count where STAGE_ID in ['WON', 'CN:WON']` | Успешные закрытия |
| LOSE | `count where STAGE_ID in ['LOSE', 'CN:LOSE']` | Неуспешные |
| Active | `total - WON - LOSE` | В работе |
| Win rate | `WON / (WON + LOSE) * 100` | % успеха от закрытых |
| Win rate от всех | `WON / total * 100` | % успеха от всех сделок |
| LOSE rate | `LOSE / total * 100` | % отказов |
| Средний чек | `sum(OPPORTUNITY of WON) / count(WON)` | Средний размер сделки |
| Средний цикл | `avg(CLOSEDATE - DATE_CREATE) для WON` | Скорость закрытия в днях |

## Pipeline

| Метрика | Формула | Что значит |
|---------|---------|-----------|
| Pipeline value | `sum(OPPORTUNITY) для active` | Потенциальная выручка |
| Weighted pipeline | `sum(OPPORTUNITY * stage_probability)` | Взвешенный прогноз |
| Coverage | `pipeline / (target - closed)` | Покрытие плана |
| Deal freshness | `now - DATE_MODIFY` | Дней без активности |
| Stagnant deals | `count(active where freshness > 90d)` | Застрявшие сделки |

## Звонки

| Метрика | Формула | Что значит |
|---------|---------|-----------|
| Total calls | `count(voximplant.statistic)` | Всего звонков |
| Answered | `CALL_DURATION > 0` | Дозвон |
| Answer rate | `answered / total * 100` | Дозваниваемость |
| Total talk time | `sum(CALL_DURATION)` | Общее время разговоров |
| Avg call duration | `sum(dur) / count(answered)` | Средняя длительность |
| Unique numbers | `count(distinct PHONE_NUMBER)` | Уникальных контактов |
| Calls per day | `total / active_days` | Средняя интенсивность |
| Repeat rate | `sum(count-1 for phones) / total` | % повторных звонков |

### Статус-коды звонков (voximplant)

| Код | Значение |
|-----|----------|
| 200 | OK (успешно) |
| 603 | Отклонено абонентом |
| 603-S | Отклонено SIP |
| 304 | Занято / нет ответа |
| 480 | Абонент временно недоступен |
| 486 | Занято |

## Активности (TODO)

| Метрика | Формула | Что значит |
|---------|---------|-----------|
| TODO total | `count(activity where PROVIDER_ID='CRM_TODO')` | Всего задач |
| TODO done | `where COMPLETED = 'Y'` | Выполнено |
| TODO pending | `where COMPLETED = 'N'` | Ожидает |
| TODO overdue | `pending and DEADLINE < now` | Просрочено |
| TODO done rate | `done / total * 100` | Процент выполнения |
| TODO overdue rate | `overdue / pending * 100` | Процент просрочки |

## Качество данных

| Метрика | Формула | Норма |
|---------|---------|-------|
| No company % | `count(without COMPANY_ID) / total * 100` | <20% для B2B |
| No contact % | `count(without CONTACT_ID) / total * 100` | <10% |
| No amount in WON % | `count(WON where OPPORTUNITY=0) / count(WON)` | <5% |
| Reason filled % | `count(with UF_REASON_FOR_REFUSAL) / count(LOSE)` | >80% (сейчас <5%) |

## Конверсия по стадиям

### «Прошло через стадию N» (cumulative)

Т.к. Битрикс хранит только текущую стадию:
```
reached(N) = current(N) + sum(current(K)) для всех K после N + WON
```

### «Конверсия N→N+1»

```
conv(N→N+1) = reached(N+1) / reached(N) * 100
drop(N→N+1) = reached(N) - reached(N+1)
```

## Классификация менеджеров (роли)

Функция `classify_role()` в `compare_managers.py`:

| Роль | Критерий |
|------|----------|
| Closer / Account manager | `WON >= 2 AND avg_call_dur >= 100с` |
| SDR / Callcenter | `calls/day > 30 AND WON = 0` |
| Воронка-чистильщик | `LOSE_rate > 60%` |
| Hunter (сбалансированный) | `WON > 0 AND calls/day > 15` |
| Junior / развивается | остальные |

## Норма для оценки

Ориентировочные бенчмарки для отдела продаж Company (июнь 2026):

| Метрика | Норма | Что критично |
|---------|-------|--------------|
| Дозваниваемость | >65% | <50% — плохая база |
| Средний разговор | >60с | <30с — не идут диалоги |
| Звонков/активный день | 10-30 (Closer), 30-60 (SDR) | — |
| TODO done rate | >70% | <50% — плохая дисциплина |
| TODO overdue rate | <30% | >60% — критично |
| Win rate от закрытых | >20% (B2B), >5% (B2C) | <10% B2B — проблема |
| LOSE rate | 40-60% (нормально) | >80% — плохая квалификация или чистка |
| No company % | <30% (B2B) | >70% — невозможен ABS |
| Стажирующиеся сделки >90д | <20% | >50% — воронка мертвит |
