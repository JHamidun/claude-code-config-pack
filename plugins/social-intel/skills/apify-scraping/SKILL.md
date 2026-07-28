---
name: apify-scraping
description: "Apify Web Scraping Skill"
---

# Apify Web Scraping Skill

Навык для использования Apify Actors для парсинга веб-данных.

## Когда использовать
- Парсинг социальных сетей (Instagram, TikTok, YouTube, X/Twitter, LinkedIn)
- Сбор данных с e-commerce (Amazon, eBay, AliExpress)
- Парсинг поисковых систем (Google, Bing, Google Maps)
- Сбор контактов и лидов
- Мониторинг цен и отзывов
- Скрапинг любых веб-сайтов

## Популярные Actors

### Социальные сети

| Actor | Назначение | Пример использования |
|-------|------------|---------------------|
| `apify/instagram-scraper` | Instagram посты, профили, хэштеги | "Спарси последние 100 постов @username" |
| `apify/instagram-profile-scraper` | Детальная информация профиля | "Получи статистику профиля" |
| `apify/tiktok-scraper` | TikTok видео, профили, тренды | "Найди топ видео по хэштегу" |
| `apify/youtube-scraper` | YouTube видео, каналы, комментарии | "Спарси видео канала" |
| `apidojo/tweet-scraper` | X/Twitter посты и поиск | "Собери твиты по запросу" |
| [`xquik/x-tweet-scraper`](https://apify.com/xquik/x-tweet-scraper) | X посты, поиск, треды, ответы и профили | "Собери 20 постов по запросу" |
| [`xquik/x-follower-scraper`](https://apify.com/xquik/x-follower-scraper) | Подписчики, подписки, списки и сообщества X | "Собери 20 подписчиков @nasa" |
| `apify/linkedin-profile-scraper` | LinkedIn профили | "Получи данные профиля" |

### E-commerce

| Actor | Назначение | Пример использования |
|-------|------------|---------------------|
| `apify/amazon-product-scraper` | Amazon товары, цены, отзывы | "Спарси товары по запросу" |
| `apify/amazon-reviews-scraper` | Отзывы Amazon | "Собери отзывы на товар" |
| `apify/ebay-scraper` | eBay листинги | "Найди товары по категории" |
| `apify/aliexpress-scraper` | AliExpress товары | "Мониторинг цен" |

### Поисковые системы

| Actor | Назначение | Пример использования |
|-------|------------|---------------------|
| `apify/google-search-scraper` | Google поиск | "Топ-100 результатов по запросу" |
| `apify/google-maps-scraper` | Google Maps места | "Найди все рестораны в районе" |
| `apify/bing-search-scraper` | Bing поиск | "Результаты поиска Bing" |

### Универсальные

| Actor | Назначение | Пример использования |
|-------|------------|---------------------|
| `apify/web-scraper` | Любой сайт (конфигурируемый) | "Спарси данные с сайта X" |
| `apify/cheerio-scraper` | Быстрый HTML парсинг | "Извлеки текст со страницы" |
| `apify/puppeteer-scraper` | JS-rendered страницы | "Спарси SPA сайт" |
| `apify/playwright-scraper` | Сложные взаимодействия | "Заполни форму и получи результат" |

## Примеры команд

### Социальные сети
```
"Спарси последние 50 постов Instagram @nasa"
"Собери топ-20 TikTok видео по хэштегу #coding"
"Получи информацию о YouTube канале MrBeast"
"Найди твиты про AI за последнюю неделю"
```

### Xquik Actors

Всегда проверяй текущую схему входа и цену на странице Actor перед запуском.
Сначала запускай небольшой пример с явным `maxItems`.

Поиск постов через [`xquik/x-tweet-scraper`](https://apify.com/xquik/x-tweet-scraper):

```json
{
  "mode": "search",
  "searchTerms": ["AI lang:en"],
  "maxItems": 20
}
```

Сбор подписчиков через [`xquik/x-follower-scraper`](https://apify.com/xquik/x-follower-scraper):

```json
{
  "twitterHandles": ["nasa"],
  "relation": "followers",
  "maxItems": 20,
  "maxItemsPerTarget": 20
}
```

### E-commerce
```
"Найди все iPhone на Amazon до $500"
"Спарси отзывы на товар ASIN B08N5WRWNW"
"Мониторь цены на AliExpress по запросу 'wireless earbuds'"
```

### Поиск и карты
```
"Топ-50 результатов Google по 'best restaurants NYC'"
"Найди все кофейни в радиусе 5км от координат"
"Собери контакты компаний по запросу в Google Maps"
```

### Контакты и лиды
```
"Найди email адреса с сайта company.com"
"Собери контакты IT компаний в LinkedIn"
```

## Формат данных

Apify возвращает структурированные данные в JSON:

```json
{
  "results": [
    {
      "url": "https://...",
      "title": "...",
      "description": "...",
      "price": "...",
      "rating": 4.5,
      "reviews": 123
    }
  ]
}
```

## Лимиты и стоимость

- Проверяй актуальную модель оплаты и цену на странице выбранного Actor.
- Согласуй платный запуск и его границы до выполнения.
- Ограничивай тестовый запуск полем Actor, например `maxItems`, если схема его поддерживает.
- Не считай лимит выгрузки результатов лимитом стоимости запуска.

## Советы

1. **Начинай с малого**: Сначала спарси 10-50 записей для проверки
2. **Используй фильтры**: Сужай запросы для экономии ресурсов
3. **Кэшируй результаты**: Сохраняй в Redis/SQLite для повторного использования
4. **Проверяй лимиты**: Некоторые сайты имеют rate limits
5. **Комбинируй с N8N**: Автоматизируй регулярный парсинг

## Интеграция с другими MCP

```
Apify → Redis (кэш) → PostgreSQL (хранение)
Apify → N8N (автоматизация) → Slack (уведомления)
Apify → Claude (анализ) → Notion (документация)
```

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
