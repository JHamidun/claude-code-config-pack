# No-code платформы для CAPI — пошагово

> Источник: методология курса («CAPI без кода через Zapier / Albato / Make / n8n / готовая интеграция CRM») + общеизвестная практика.

Логика **одинаковая на всех платформах**, меняется только инструмент:

```
Триггер в CRM (новый лид / смена статуса на «квалифицирован» / оплата)
   → нормализация полей (email lowercase, phone только цифры, country ISO, zip)
   → хеширование SHA-256 (em, ph, country, zp, external_id) — FBC/FBP НЕ хешируем
   → отправка в Conversions API (event_name + event_time + event_id + user_data)
   → проверка в Events Manager → Test Events
```

Выбор инструмента — `SKILL.md`. Параметры и хеширование — `meta-capi.md`. Ниже — конкретные сценарии.

---

## 1. Zapier (облако, проще всего)

Готовые коннекторы и **Facebook Conversions** action (хеширует PII сам).

**Сценарий «новый квал-лид → Meta CAPI»:**
1. **Trigger:** `your CRM / HubSpot / Your CRM → New/Updated Deal` (или Webhook from CRM).
2. **Filter:** только если стадия = «Квалифицирован» (Zapier Filter step).
3. **Action:** `Facebook Conversions → Send Conversion Event`:
   - Event Name: `Lead` (или кастомная);
   - Event Time: время события из CRM;
   - Event ID: ID сделки (для дедупликации);
   - User Data: email, phone, country, zip, External ID (Zapier хеширует);
   - FBC/FBP: из полей сделки (если сохранены при заходе).
4. Проверить в **Test Events**.

**Плюсы:** меньше всего ручной работы, хеширование из коробки.
**Минусы:** платный по объёму задач (tasks); зарубежная оплата (проблема для РФ-юрлица → Albato).

---

## 2. Make (Integromat) — гибкий маппинг

Визуальные сценарии; для CAPI чаще через **HTTP / JSON** модуль (полный контроль payload) или готовый Facebook-модуль.

**Сценарий «оплата → Meta CAPI (Purchase)»:**
1. **Webhook** (Custom webhook) ← CRM/платёжка шлёт POST на оплату.
2. **Tools → Set variables:** нормализация (lowercase email, цифры телефона).
3. **Crypto / встроенная функция:** SHA-256 для em/ph/country/zp/external_id.
4. **HTTP → Make a request:** POST на `graph.facebook.com/<API_VERSION>/<PIXEL_ID>/events?access_token=...` с JSON:
   ```
   { "data": [ { "event_name":"Purchase", "event_time":<unix>,
     "event_id":"<order_id>", "action_source":"website",
     "user_data": { "em":["<hash>"], "ph":["<hash>"], "fbc":"...", "fbp":"..." },
     "custom_data": { "value":4900, "currency":"RUB" } } ] }
   ```
5. **Test Events** — проверить, что `Purchase` пришёл 1 раз и совпал с браузерным по `event_id`.

**Плюсы:** дешевле Zapier на объёме; полный контроль JSON.
**Минусы:** хеширование настраиваешь сам; зарубежный биллинг.

---

## 3. n8n (self-hosted — рекомендуется для PII)

**Свой сервер** (у пользователя n8n на your-server), 0 за объём, данные **не уходят в зарубежное облако** (важно для 152-ФЗ). Cross-link: скилл `n8n` (готовые workflow).

**Сценарий «CRM webhook → нормализация → хеш → Meta CAPI + Google Enhanced Conversions»:**
1. **Webhook node** ← Битрикс24/Postgres-триггер/ЮKassa шлёт событие.
2. **Function / Set node:** нормализация (email lowercase trim, phone `\D`-strip с кодом страны).
3. **Crypto node** (SHA-256) на каждое PII-поле → `em`, `ph`, `country`, `zp`, `external_id`. **FBC/FBP не хешируем.**
4. **HTTP Request node (POST):** Meta Conversions API endpoint (см. payload в `meta-capi.md`).
5. Параллельная ветка: **HTTP Request** на Google Ads (Enhanced Conversions / офлайн-импорт).
6. **Test Events** проверка.

**Плюсы:** бесплатно по объёму, данные дома, любая логика; готовые шаблоны в скилле `n8n`.
**Минусы:** нужен сервер и базовая настройка (но у пользователя уже есть).

> **Worked example пользователя** (academy.your-domain.com): `Оплата ЮKassa → webhook → n8n (your-server) → hash(email/phone)+External ID(user_id)+FBC/FBP → Meta CAPI Purchase + Google Enhanced Conversions → Test Events`. Подробно — `SKILL.md`.

---

## 4. Albato (российская альтернатива)

RU-аналог Zapier — для клиентов с **РФ-юрлицом** (зарубежная оплата Zapier/Make недоступна из-за санкций). RU-коннекторы CRM: **your CRM, Битрикс24**.

**Сценарий «your CRM смена статуса → Meta CAPI»:**
1. **Триггер:** your CRM → смена статуса сделки на «Квалифицирован» / «Оплачено».
2. **Обработка:** маппинг полей сделки (email, phone, сумма) в формат CAPI; нормализация.
3. **Действие:** отправка в Facebook Conversions API (Event Name, Event ID = ID сделки, user_data, value).
4. **Test Events** проверка.

**Плюсы:** RU-биллинг и поддержка, готовые RU-CRM коннекторы.
**Минусы:** меньше интеграций, чем у Zapier; меньше гибкости JSON, чем у Make/n8n.

---

## 5. CRM-нативные интеграции (без отдельного no-code слоя)

Если коннектор есть из коробки — он **проще** любого no-code слоя.

| CRM | Что есть |
|-----|----------|
| **HubSpot** | нативный коннектор к Meta CAPI — события из воронки уходят на сервер Meta автоматически |
| **your CRM** | интеграции/виджеты передачи статусов сделки в CAPI |
| **Битрикс24** | вебхуки на смену стадии → no-code слой (n8n/Make/Albato) → CAPI; см. скилл `crm` |

> **Когда брать no-code, а не нативный коннектор:** нестандартная логика — фильтр по конкретной стадии, обогащение FBC/FBP из сохранённых cookies, кастомная нормализация полей, отправка сразу в Meta + Google + Яндекс из одного триггера.

---

## 6. Сравнение

| Критерий | Zapier | Make | n8n | Albato |
|----------|--------|------|-----|--------|
| Хостинг | облако | облако | **self-hosted** | облако |
| Стоимость по объёму | $$ (tasks) | $ | **0** | ₽ |
| RU-биллинг | нет | нет | — | **да** |
| Гибкость JSON payload | средняя | **высокая** | **высокая** | средняя |
| Хеширование из коробки | **да** | сам | сам | частично |
| PII не уходит наружу | нет | нет | **да** | нет |
| Порог входа | низкий | средний | выше (нужен сервер) | низкий |

**Выбор:**
- быстрый старт, не жалко платить → **Zapier**;
- гибкий маппинг, дешевле → **Make**;
- PII дома / 0 за объём / уже есть сервер → **n8n**;
- РФ-юрлицо, зарубежная оплата недоступна → **Albato**;
- CRM = HubSpot/your CRM/Битрикс24 со встроенным коннектором → **нативная интеграция**.

## Cross-links
- `meta-capi.md` — 7 параметров, хеширование, Event ID, payload, Test Events.
- `attribution.md` — офлайн-конверсии и атрибуция поверх собранных событий.
- `n8n` (скилл) — готовые self-hosted workflow.
- `crm` (скилл) — вебхуки на смену стадии.
