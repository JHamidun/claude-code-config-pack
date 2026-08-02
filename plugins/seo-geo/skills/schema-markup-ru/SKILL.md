---
name: schema-markup-ru
description: "Schema.org / JSON-LD разметка: шаблоны Organization, Course, FAQPage, Article, Person, Event; Яндекс читает JSON-LD — кормит AEO/GEO. Триггеры: «микроразметка», «rich snippets», «звёздочки в выдаче». НЕ: SEO-контент→seo-machine-ru; CRO→*-cro-ru."
metadata:
  version: 1.0.0
  updated: 2026-05-29
  ported_from: coreyhaines31/marketingskills (schema)
  reuses: seo-machine-ru, tilda, yourname-marketing-context
---

# Микроразметка Schema.org / JSON-LD (RU)

Реализация структурированных данных schema.org на сайтах пользователя, чтобы поисковики (Яндекс, Google) лучше понимали контент и показывали расширенные сниппеты, а AI-поверхности (Яндекс.Нейро, Alice, (regional LLM B)) точнее цитировали. Порт `schema` из marketingskills: вокабуляр schema.org международный, адаптированы примеры под реальные сущности (YourFirstName, академия, воркшоп, news, блог) и заметка про Яндекс.

**Перед началом прочитай контекст:** `yourname-marketing-context` — `skills/yourname-marketing-context/references/business.md` (сущности: кто YourFirstName, что за продукты), `skills/yourname-marketing-context/references/offerings.md` (URL и цены). Не выдумывай факты — `[TODO]` уточнять.

**AEO/GEO связка:** JSON-LD — один из сильнейших сигналов для попадания в AI-ответы. После разметки сверяйся с `seo-machine-ru` → `skills/seo-machine-ru/references/aeo-geo.md` (цитируемость в Яндекс.Нейро/Alice/(regional LLM B)/ChatGPT/Perplexity).

## Принципы

1. **Точность прежде всего.** Разметка обязана соответствовать видимому контенту. Не размечать то, чего нет на странице. Обновлять при изменении контента.
2. **Используй JSON-LD.** Рекомендуемый формат (и Google, и Яндекс). Скрипт `<script type="application/ld+json">` в `<head>` или конце `<body>`.
3. **Только то, что поддерживается.** Без спам-тактик. Проверять требования к rich-результатам.
4. **Валидируй всё.** Тест перед деплоем, мониторинг в Вебмастере.

## Заметка про Яндекс (важно для RU-рынка)

- Яндекс читает JSON-LD и микроформаты; расширенные сниппеты в выдаче формируются по разметке (товары, организации, FAQ, хлебные крошки, события).
- Проверка: **Яндекс.Вебмастер → Инструменты → Валидатор микроразметки** (а не только Google Rich Results Test). Дёргать через скилл `yandex` (Вебмастер) либо вручную.
- Для бизнеса/локалки — карточка в **Яндекс.Бизнес** (отдельно от JSON-LD), но `Organization`/`Person` всё равно ставим на сайт.
- AI-цитируемость: чёткий `Person` (YourFirstName как эксперт), `Organization`, `FAQPage`, `Course` помогают Яндекс.Нейро/(regional LLM B) понять, кто автор и что за продукт.

## Типы под сайты пользователя

| Тип | Где ставить | Обязательные поля |
|-----|-------------|-------------------|
| Organization | your-domain.com (главная/обо мне) | name, url |
| WebSite (+SearchAction) | главная / news (поиск по сайту) | name, url |
| Person | страница «Обо мне» (YourFirstName как эксперт) | name |
| Course | academy.your-domain.com и страницы треков | name, description, provider |
| Article | блог, статьи на /media, новости news | headline, image, datePublished, author |
| FAQPage | лендинги услуг/воркшопа/academy с FAQ | mainEntity (Q&A) |
| Event | воркшоп, Tech University ConferenceX, вебинар | name, startDate, location |
| BreadcrumbList | любая страница с навигацией/крошками | itemListElement |

Полные JSON-LD примеры под каждую сущность — `references/schema-examples.md`.

## Объединение типов на странице (@graph)

Несколько типов на одной странице — через `@graph`:

```json
{ "@context": "https://schema.org", "@graph": [
  { "@type": "Organization", "@id": "https://your-domain.com/#org", "...": "..." },
  { "@type": "Person", "@id": "https://your-domain.com/#user", "...": "..." },
  { "@type": "BreadcrumbList", "...": "..." }
]}
```

## Валидация и тестирование

- **Яндекс.Вебмастер** — валидатор микроразметки + раздел «Структурированные данные» (через `yandex`).
- **Google Rich Results Test** — search.google.com/test/rich-results.
- **Schema.org Validator** — validator.schema.org.

Типичные ошибки: нет обязательных полей; даты не в ISO 8601; URL не абсолютные; значения enum неточные (`https://schema.org/InStock`); разметка не совпадает с видимым контентом.

## Реализация на стеке пользователя

- **Tilda** (your-domain.com, лендинги): JSON-LD вставляется в блок T123 (custom HTML) или в настройки страницы (head). Деплой и публикация — через скилл `tilda`. Учти граблины T123 (scope, лимит кода) — см. `tilda`.
- **news.your-domain.com / academy** (Next.js, Express): рендерить `<script type="application/ld+json">` на сервере (SSR), сериализуя данные в JSON-LD на каждой странице (статья → Article, лендинг → Course/FAQPage).

## Связки

| Нужно | Скилл |
|------|-------|
| Контекст сущностей, URL, цены | `yourname-marketing-context` |
| AEO/GEO (цитируемость в AI) | `seo-machine-ru` (`skills/seo-machine-ru/references/aeo-geo.md`) |
| Валидация в Вебмастере | `yandex` |
| Вставка JSON-LD на Tilda + публикация | `tilda` |
| SEO-контент страницы целиком | `seo-machine-ru` |

## Формат вывода

1. Полный JSON-LD блок (готов к вставке).
2. Куда вставлять (Tilda T123 / head / SSR-компонент).
3. Чеклист: валидируется в Вебмастере + Rich Results; нет ошибок/предупреждений; совпадает с контентом; все обязательные поля; даты ISO 8601; URL абсолютные.

## Вопросы под задачу

1. Какой тип страницы (главная / обо мне / трек academy / статья / лендинг воркшопа / новость)?
2. Какой rich-результат целевой (FAQ-аккордеон, карточка организации, событие, курс)?
3. Какие данные есть на странице для заполнения (цены, даты, автор, изображения)?
4. Есть ли уже разметка (не дублировать)?
5. Стек страницы — Tilda или Next.js/Express?
