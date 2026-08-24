# Рецепт: CAPI без кода через n8n (CRM → Meta Conversions API)

> Источник методологии: курсовой модуль «Пиксель, события, Events Manager» + общеизвестная практика n8n / Meta CAPI.
> ⚠️ Meta признана экстремистской в РФ. Рецепт — для международных / СНГ-проектов. По доступу и оплате Meta из РФ — скилл `meta-ads-launch-ru`.

n8n — рекомендуемый инструмент для CAPI, когда в событиях есть **PII** (email, телефон): self-hosted сервер, данные **не уходят в зарубежное облако** (важно для 152-ФЗ), 0 за объём событий. Здесь — готовый workflow-каркас. Полная методология (зачем server-side, 7 параметров матчинга, дедупликация) — в скилле `capi-no-code-setup`.

## Когда брать этот рецепт

- Передать в Meta **глубокое событие из CRM**: квал-лид, звонок, оплата, LTV — а не только браузерный пиксель.
- Победить потерю событий: блокировщики, iOS 14.5+ ATT, удаление cookies, длинный B2B-цикл сделки.
- PII не должен уходить в зарубежное no-code облако (Zapier/Make) → self-hosted n8n.
- Уже есть сервер n8n (у пользователя — на your-server).

## Структура workflow (последовательность узлов)

```
[Webhook] → [Set: нормализация] → [Crypto: SHA-256] → [HTTP Request: Meta CAPI]
   ↑               ↓                      ↓                       ↓
CRM-триггер   email lowercase,      хеш em/ph/country/      POST на graph.facebook.com
(amoCRM /       phone только цифры,    zp/external_id;         /<API_VERSION>/<PIXEL_ID>/events
HubSpot /     country ISO, zip       FBC/FBP НЕ хешируем     → Events Manager → Test Events
Битрикс24)
```

### Узел 1 — Webhook (триггер)

`n8n-nodes-base.webhook`, метод POST. CRM шлёт событие на смену стадии / оплату:
- **amoCRM** — webhook на смену статуса сделки (через настройки воронки или digital-pipeline).
- **HubSpot** — workflow с действием «Send a webhook» на смену стадии deal.
- **Битрикс24** — исходящий вебхук `ONCRMDEALUPDATE` на смену стадии (настраивается в самой Битрикс24, см. её REST-документацию).

Данные приходят в `{{ $json.body }}` (email, phone, сумма, ID сделки, и — если сохранены при заходе на сайт — `fbc`/`fbp` из cookies `_fbc`/`_fbp`).

### Узел 2 — Set (нормализация полей)

`n8n-nodes-base.set`. Привести PII к формату Meta **перед** хешированием:

```javascript
// email
{{ $json.body.email.trim().toLowerCase() }}
// phone — только цифры, с кодом страны, без + и пробелов
{{ $json.body.phone.replace(/\D/g, '') }}
// country — ISO 3166-1 alpha-2, lowercase ("ru", "us")
{{ $json.body.country.trim().toLowerCase() }}
// zip — lowercase, без пробелов
{{ $json.body.zip.replace(/\s/g, '').toLowerCase() }}
```

External ID — стабильный идентификатор пользователя из CRM (user_id / contact_id), тоже хешируется.

### Узел 3 — Crypto (SHA-256)

`n8n-nodes-base.crypto`, action = Hash, algorithm = SHA256, по одному узлу (или Code-узел) на каждое PII-поле → `em`, `ph`, `country`, `zp`, `external_id`.

```javascript
// в Code-узле, если хешируем все поля разом
const crypto = require('crypto');
const sha = (v) => crypto.createHash('sha256').update(v).digest('hex');
for (const item of $input.all()) {
  const b = item.json;
  item.json.user_data = {
    em: [sha(b.email)],
    ph: [sha(b.phone)],
    country: [sha(b.country)],
    zp: [sha(b.zip)],
    external_id: [sha(b.user_id)],
    fbc: b.fbc,   // НЕ хешируем
    fbp: b.fbp    // НЕ хешируем
  };
}
return $input.all();
```

**FBC и FBP не хешируются** — это уже технические идентификаторы клика/браузера.

### Узел 4 — HTTP Request (Meta Conversions API)

`n8n-nodes-base.httpRequest`, метод POST:
- URL: `https://graph.facebook.com/<API_VERSION>/<PIXEL_ID>/events?access_token=<ACCESS_TOKEN>`
- Body (JSON):

```json
{
  "data": [
    {
      "event_name": "Lead",
      "event_time": 1718900000,
      "event_id": "{{ $json.body.deal_id }}",
      "action_source": "website",
      "user_data": {
        "em": ["<hash>"],
        "ph": ["<hash>"],
        "country": ["<hash>"],
        "zp": ["<hash>"],
        "external_id": ["<hash>"],
        "fbc": "{{ $json.user_data.fbc }}",
        "fbp": "{{ $json.user_data.fbp }}"
      },
      "custom_data": { "value": 4900, "currency": "RUB" }
    }
  ]
}
```

- `event_name` — стандартное (`Lead`, `Purchase`, `InitiateCheckout`) или кастомная конверсия.
- `event_id` — **ID сделки/заказа из CRM**: ключ дедупликации браузерного пикселя и серверного CAPI (один и тот же event_id с обеих сторон → Meta засчитывает как одно событие).
- `event_time` — Unix-время события (не время обработки workflow).
- `custom_data.value` / `currency` — для Purchase и LTV.

### Узел 5 — проверка (Test Events)

Открыть Events Manager → Test Events, прогнать тестовое событие. Проверить:
- событие пришло **1 раз** (нет дублей);
- совпало с браузерным по `event_id` (дедупликация работает);
- качество матчинга по `user_data` — чем больше параметров, тем выше Event Match Quality.

## Параллельная ветка: Google Enhanced Conversions

От того же триггера можно добавить вторую ветку `[HTTP Request]` на Google Ads (Enhanced Conversions / офлайн-импорт) — один webhook кормит сразу Meta + Google. Маппинг полей и хеширование — те же. Детали Google-стороны — `capi-no-code-setup` (`attribution.md`).

## Worked example (academy.your-domain.com)

```
Оплата ЮKassa → Webhook node → Set (нормализация email/phone) →
Crypto SHA-256 (+ External ID = user_id, FBC/FBP из сохранённых cookies) →
HTTP Request → Meta CAPI Purchase + параллельно Google Enhanced Conversions →
Test Events
```

## Альтернативы (тот же mapping, другой инструмент)

Логика одинаковая на всех платформах — меняется только инструмент. Выбирай по биллингу и требованиям к PII:

| Инструмент | Когда брать | Особенность |
|------------|-------------|-------------|
| **n8n** (этот рецепт) | PII дома, 0 за объём, уже есть сервер | self-hosted, любая логика, хеширование настраиваешь сам |
| **Zapier** | быстрый старт, не жалко платить | `Facebook Conversions` action **хеширует PII сам**; зарубежная оплата |
| **Make (Integromat)** | гибкий маппинг, дешевле Zapier | через HTTP/JSON-модуль — полный контроль payload; зарубежный биллинг |
| **Albato** (RU) | РФ-юрлицо, зарубежная оплата недоступна | RU-биллинг, готовые RU-коннекторы amoCRM / Битрикс24 |
| CRM-нативный коннектор | HubSpot / amoCRM со встроенной интеграцией CAPI | проще любого no-code слоя — события уходят из воронки автоматически |

Брать no-code (а не нативный коннектор), когда нужна нестандартная логика: фильтр по конкретной стадии, обогащение FBC/FBP из cookies, кастомная нормализация, отправка сразу в Meta + Google + Яндекс из одного триггера.

## Cross-links

- `capi-no-code-setup` (скилл) — полная методология: зачем server-side, **7 параметров матчинга**, хеширование SHA-256, **Event ID дедупликация**, Test Events, офлайн-конверсии, атрибуция. Эталонный payload — там в `references/meta-capi.md`.
- Твоя CRM — исходящие вебхуки на смену стадии сделки (настраиваются в CRM, не в n8n).
- `meta-ads-launch-ru` (скилл) — запуск Meta, доступ и оплата из РФ, аукционная логика.
- `ai-seo-agent-pipeline` (скилл) — другой n8n-рецепт из того же курса: программатическая AI-SEO фабрика (n8n + Perplexity + OpenAI).
