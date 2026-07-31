---
name: ad-spy
description: "Ad Library intelligence: Facebook, Google, LinkedIn, Reddit — мониторинг рекламы конкурентов, креативы, бюджеты via Scraping API. Российские каналы: Яндекс.Директ, Google Transparency Center, Telegram Ads (TGMaps/TGSpice), VK, Meta через Atria. Триггеры: реклама конкурентов, ad spy, ad library, competitor ads, креативы конкурентов, vk ads spy, admobispy, TGMaps, Atria, tryatria."
allowed-tools: Bash, Read, Write, WebSearch
---

# Ad Spy — Competitor Ad Intelligence

> Cross-platform ad monitoring via a 3rd-party scraping API.
> Key: `SCRAPER_API_KEY` from `~/.claude/.credentials.master.env`

## When to Use

- "что рекламируют конкуренты" — обзор рекламной активности
- "реклама [компания] в Facebook/Google/LinkedIn"
- "ad spy [бренд]" — полный анализ рекламы
- "креативы конкурентов" — сбор рекламных материалов
- "мониторинг рекламы" — периодический трекинг
- Your Tracker: мониторинг рекламы конкурентов строительных смесей
- YourProduct: что рекламируют AI-конкуренты
- "spy за Яндекс Директом / VK / Telegram Ads" — российские каналы (см. references)
- "лучшие креативы конкурентов в FB", "бюджет конкурента", "Atria" — Meta-креативный спай

## Российские каналы и Meta-креативы (экспертные материалы курса)

Scraping API хорошо покрывает FB/Google/LinkedIn/Reddit, но российские каналы и
продвинутый Meta-креативный анализ требуют отдельных инструментов. Подробности — в references:

| Reference | Что внутри |
|-----------|-----------|
| `references/russian-channels-spy.md` | Яндекс.Директ (нет полноценного spy — ручной reverse-engineering через ключи), Google Transparency Center (adstransparency.google.com) + keywordtoolcollector.io, Telegram Ads (TGMaps + TGSpice — наценки CPM/эмодзи/таргетинг), VK (Admobispy устарел до 2024, спикер VK Ads за актуальным + «защита от копирования» — вычитать конкурентов-таргетологов) |
| `references/meta-creative-spy-atria.md` | Поиск по точному имени FB-страницы (не по компании), workflow analyze→company_ads→ad_details→longest running, **Atria (tryatria.com)** — клонирование креативов + оценка бюджета + рейтинг A+/High iteration/Underperforming |

**Связанные скиллы:** `meta-ads-launch-ru` (запуск своих Meta-кампаний на основе разведки), `ai-creative-factory-ru` (декомпозиция найденных виральных креативов), `telegram-ads-pro-ru` / `vk-ads-pro-ru` (запуск в найденных каналах), `ad-benchmarks-ru` (нормы для оценки увиденных кампаний).

## API Endpoints

```
BASE = https://api.your-scraper.example
AUTH: x-api-key: $SCRAPER_API_KEY
```

### Facebook Ad Library (основной — самый большой объём рекламы)

| Endpoint | Path | Input | Returns |
|----------|------|-------|---------|
| Search Ads | `/v1/facebook/adLibrary/search/ads` | `?query=keyword` | Креативы, тексты, статус, даты |
| Company Ads | `/v1/facebook/adLibrary/company/ads` | `?company_id=ID` | Все объявления компании |
| Ad Details | `/v1/facebook/adLibrary/ad` | `?ad_id=ID` | Полная информация об объявлении |
| Search Companies | `/v1/facebook/adLibrary/search/companies` | `?query=company_name` | Найти company_id для дальнейшего поиска |

### Google Ad Library

| Endpoint | Path | Input | Returns |
|----------|------|-------|---------|
| Company Ads | `/v1/google/company/ads` | `?company=name` | Контекстная реклама компании |
| Ad Details | `/v1/google/ad` | `?ad_id=ID` | Детали объявления |
| Search Advertisers | `/v1/google/adLibrary/advertisers/search` | `?query=keyword` | Поиск рекламодателей |

### LinkedIn Ad Library

| Endpoint | Path | Input | Returns |
|----------|------|-------|---------|
| Search Ads | `/v1/linkedin/ads/search` | `?query=keyword` | B2B реклама по ключевому слову |
| Ad Details | `/v1/linkedin/ad` | `?id=AD_ID` | Детали конкретного объявления |

### Reddit Ads

| Endpoint | Path | Input | Returns |
|----------|------|-------|---------|
| Search Ads | `/v1/reddit/ads/search` | `?query=keyword` | Нативная реклама Reddit |
| Ad Details | `/v1/reddit/ad` | `?ad_id=ID` | Детали объявления |

## Workflow: Competitor Ad Audit

### Step 1: Find competitors in ad libraries

```bash
source ~/.claude/.credentials.master.env
API="https://api.your-scraper.example"
H="x-api-key: $SCRAPER_API_KEY"

# Find company in Facebook Ad Library
curl -s "$API/v1/facebook/adLibrary/search/companies?query=COMPETITOR_NAME" -H "$H" | python3 -m json.tool
```

### Step 2: Pull all their ads (parallel across platforms)

```bash
source ~/.claude/.credentials.master.env
API="https://api.your-scraper.example"
H="x-api-key: $SCRAPER_API_KEY"

# Facebook ads
curl -s "$API/v1/facebook/adLibrary/company/ads?company_id=COMPANY_ID" -H "$H" > /tmp/ads_fb.json &

# Google ads
curl -s "$API/v1/google/company/ads?company=COMPETITOR_NAME" -H "$H" > /tmp/ads_google.json &

# LinkedIn ads
curl -s "$API/v1/linkedin/ads/search?query=COMPETITOR_NAME" -H "$H" > /tmp/ads_linkedin.json &

# Reddit ads
curl -s "$API/v1/reddit/ads/search?query=COMPETITOR_NAME" -H "$H" > /tmp/ads_reddit.json &

wait
echo "All ad data fetched"
```

### Step 3: Analyze & synthesize

Read all JSON results and create structured report:

```markdown
# Ad Intelligence Report: [Competitor]
Generated: [date] | Sources: Facebook, Google, LinkedIn, Reddit

## Summary
- **Total active ads:** [count by platform]
- **Primary platforms:** [where they spend most]
- **Ad types:** [video, image, carousel, text]
- **Key messages:** [top 3 themes/value props]

## Facebook Ads
| Creative | Copy (first line) | CTA | Status | Running Since |
|----------|-------------------|-----|--------|---------------|
| [image/video desc] | [text] | [button] | Active | [date] |

## Google Ads
| Headline | Description | Landing Page | Keywords (estimated) |
|----------|-------------|-------------|---------------------|
| [text] | [text] | [url] | [inferred] |

## LinkedIn Ads
| Format | Copy | Target (estimated) | Engagement |
|--------|------|-------------------|------------|
| [type] | [text] | [audience hints] | [reactions] |

## Reddit Ads
| Subreddit | Title | Copy | Engagement |
|-----------|-------|------|------------|
| r/xxx | [title] | [text] | [upvotes, comments] |

## Insights & Recommendations
1. **Messaging gaps:** What competitors say that we don't
2. **Channel gaps:** Where they advertise that we don't
3. **Creative patterns:** What formats perform best for them
4. **Timing:** When they launch new campaigns
5. **Recommended actions:** [specific suggestions]
```

### Step 4: Save report

```bash
mkdir -p ~/Documents/Ad-Intel
# Write report to markdown file with date in filename
```

## Use Case: Your Tracker

Competitors to monitor:
- Your-Brand (ClientCorp3) — own brand awareness
- [Competitor1], [Competitor2], [Competitor3]

```bash
# Example: monitor all Your-Brand competitors
for company in "Comp1" "Comp2" "Comp3" "Comp4"; do
  curl -s "$API/v1/facebook/adLibrary/search/ads?query=$company your-industry" \
    -H "$H" > "/tmp/ads_${company// /_}.json"
  sleep 1
done
```

## Use Case: YourProduct Competitive Intel

AI competitors to monitor:
- ChatGPT, Claude, Gemini

## Credit Budget

| Operation | Credits |
|-----------|---------|
| Find company in FB Ad Library | 1 |
| Pull company's FB ads | 1 |
| Pull Google ads | 1 |
| Pull LinkedIn ads | 1 |
| Pull Reddit ads | 1 |
| **Full competitor audit (4 platforms)** | **5** |
| **N competitors (Your-Brand scope)** | **~35** |

## Periodic Monitoring

Combine with `/loop` or `/schedule` for recurring checks:
```
/loop 24h ad-spy YourCompetitor your-industry
```

Or integrate into Your Tracker cron collectors on your-server.

## Если банят: прямой скрап Ad Library в обход API

ScraperVendor — основной путь (не требует обхода защит). Но при прямом скрапе Ad Library
(FB/Google/TikTok) или витрин конкурентов, когда встаёт анти-бот (Cloudflare/Datadome,
«Access denied», капча, пустой ответ на `requests`):

- **Лёгкий скрап без браузера:** `curl_cffi` с `impersonate="chrome"` — подделывает TLS/JA3
  под реальный Chrome, requests-совместимый API. Первый выбор для JSON/HTML-эндпоинтов.
- **Полный браузер под анти-ботом:** **patchright** вместо `playwright` (drop-in импорт,
  `channel="chrome"` + persistent context) — скрывает `navigator.webdriver` и CDP-утечки.

Рецепты + таблица «симптом бана → инструмент»: `../playwright-automation/references/stealth-scraping.md`.

## Integration

| Next Step | Tool |
|-----------|------|
| Deep competitor analysis | `competitive-analysis` skill |
| Campaign planning | `campaign-planning` skill |
| Meta Ads optimization | `meta-ads-analyzer` skill |
| Content inspiration | `content-creation` skill |
| Report to stakeholders | `stakeholder-comms` skill |
| Save to radar DB | Your Tracker PostgreSQL (your-server) |
