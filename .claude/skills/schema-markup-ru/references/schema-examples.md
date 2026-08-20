# JSON-LD примеры под сайты пользователя

Готовые блоки. Подставь реальные значения из `yourname-marketing-context` (`offerings.md` — URL, цены). Цены/даты помеченные `[TODO]` — уточнять, не выдумывать. Все URL — абсолютные, даты — ISO 8601.

## Содержание
- Organization (your-domain.com)
- WebSite + SearchAction (news)
- Person (YourFirstName — обо мне)
- Course (академия и треки)
- Article / новость / статья на /media
- FAQPage (лендинги)
- Event (воркшоп / Tech University ConferenceX / вебинар)
- BreadcrumbList
- @graph (несколько типов)
- Next.js (SSR-вставка)

## Organization

Главная / «Обо мне» на your-domain.com.

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "YourName — AI-консалтинг и обучение",
  "url": "https://your-domain.com",
  "logo": "https://your-domain.com/logo.png",
  "founder": { "@type": "Person", "name": "Your Name" },
  "sameAs": [
    "https://t.me/your_username",
    "https://habr.com/users/[TODO]",
    "https://vc.ru/u/[TODO]"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "contactType": "sales",
    "email": "your-email@gmail.com",
    "areaServed": "RU",
    "availableLanguage": ["Russian"]
  }
}
```

## WebSite + SearchAction

news.your-domain.com — включает sitelinks-поиск.

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "YourName News",
  "url": "https://news.your-domain.com",
  "inLanguage": "ru",
  "potentialAction": {
    "@type": "SearchAction",
    "target": { "@type": "EntryPoint", "urlTemplate": "https://news.your-domain.com/ru/search?q={search_term_string}" },
    "query-input": "required name=search_term_string"
  }
}
```

## Person

Страница «Обо мне» — YourFirstName как эксперт (сигнал авторитета для Яндекс.Нейро/(regional LLM B)).

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Your Name",
  "url": "https://your-domain.com/about",
  "image": "https://your-domain.com/user.jpg",
  "jobTitle": "руководитель ИИ-направления, Your Company · AI-консультант и тренер",
  "worksFor": { "@type": "Organization", "name": "Your Company" },
  "alumniOf": { "@type": "CollegeOrUniversity", "name": "[университет]" },
  "knowsAbout": ["искусственный интеллект", "внедрение AI в бизнес", "корпоративное обучение нейросетям", "цифровая трансформация"],
  "sameAs": ["https://t.me/your_username"]
}
```

## Course

academy.your-domain.com и страницы треков. Ключевая разметка для образования. `provider` обязателен; для платных треков добавляй `offers`, для подписки — `hasCourseInstance` + ценовой ориентир.

```json
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "Claude Code — флагманский трек ExampleProduct",
  "description": "Практический трек по работе с Claude Code: от основ до production. Мульти-модельный доступ через YourProduct включён.",
  "provider": {
    "@type": "Organization",
    "name": "ExampleProduct",
    "sameAs": "https://academy.your-domain.com"
  },
  "url": "https://academy.your-domain.com/tracks/claude-code",
  "inLanguage": "ru",
  "hasCourseInstance": {
    "@type": "CourseInstance",
    "courseMode": "online",
    "courseWorkload": "PT20H"
  },
  "offers": {
    "@type": "Offer",
    "category": "Paid",
    "price": "[ВАША_ЦЕНА]",
    "priceCurrency": "RUB",
    "url": "https://academy.your-domain.com/tracks/claude-code",
    "availability": "https://schema.org/InStock"
  }
}
```

Для подписки academy (Basic/Plus/Pro) разметить как `Course` платформы с несколькими `offers` (X/Y/Z ₽, `priceCurrency: RUB`), упомянуть trial: «7 дней бесплатно» — текстом в `description` (Schema не имеет поля для trial-периода у Offer; для подписок можно `Product` + `Offer` с `eligibleDuration`, но проще — текст).

## Article

Блог your-domain.com, новости news, рерайт-статьи на /media. Для новостей можно `NewsArticle`.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Заголовок статьи]",
  "image": "https://your-domain.com/blog/[slug]/cover.jpg",
  "datePublished": "2026-05-29T09:00:00+03:00",
  "dateModified": "2026-05-29T09:00:00+03:00",
  "author": { "@type": "Person", "name": "Your Name", "url": "https://your-domain.com/about" },
  "publisher": {
    "@type": "Organization",
    "name": "YourName",
    "logo": { "@type": "ImageObject", "url": "https://your-domain.com/logo.png" }
  },
  "description": "[Краткое описание]",
  "inLanguage": "ru",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://your-domain.com/blog/[slug]" }
}
```

Для статей на /media, которые рерайт чужого оригинала — НЕ ставить `canonical` на оригинал (см. memory yourname-landing), но `author`/`publisher` — YourName, плюс в теле ссылка на первоисточник.

## FAQPage

Лендинги услуг/воркшопа/academy с блоком FAQ. Размечать только реально видимые на странице вопросы-ответы.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Подходит ли воркшоп, если сотрудники не пользовались нейросетями?",
      "acceptedAnswer": { "@type": "Answer", "text": "Да. Воркшоп — 100% практика на ваших реальных задачах, стартуем с нуля, доступ к множество моделей включён." }
    },
    {
      "@type": "Question",
      "name": "Можно ли оплатить в рублях по договору с юрлицом?",
      "acceptedAnswer": { "@type": "Answer", "text": "Да. Договор с юрлицом РФ, оплата в рублях, данные в российском контуре." }
    }
  ]
}
```

## Event

Воркшоп, Tech University ConferenceX, вебинар. `eventAttendanceMode` для онлайн.

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "Корпоративный AI-воркшоп с Your Name",
  "startDate": "[TODO ISO 8601]",
  "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": { "@type": "VirtualLocation", "url": "https://your-domain.com/workshop" },
  "description": "Практический воркшоп: команда осваивает нейросети на реальных задачах компании.",
  "performer": [
    { "@type": "Person", "name": "Your Name" },
    { "@type": "Person", "name": "эксперт" }
  ],
  "organizer": { "@type": "Organization", "name": "YourName", "url": "https://your-domain.com" },
  "offers": {
    "@type": "Offer",
    "url": "https://your-domain.com/workshop",
    "priceCurrency": "RUB",
    "price": "[TODO]",
    "availability": "https://schema.org/InStock"
  },
  "inLanguage": "ru"
}
```

## BreadcrumbList

Любая вложенная страница.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Главная", "item": "https://your-domain.com" },
    { "@type": "ListItem", "position": 2, "name": "Услуги", "item": "https://your-domain.com/services" },
    { "@type": "ListItem", "position": 3, "name": "AI-воркшоп", "item": "https://your-domain.com/workshop" }
  ]
}
```

## @graph (несколько типов на странице)

Главная your-domain.com: Organization + Person + WebSite разом.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://your-domain.com/#org", "name": "YourName", "url": "https://your-domain.com" },
    { "@type": "Person", "@id": "https://your-domain.com/#user", "name": "Your Name", "worksFor": { "@id": "https://your-domain.com/#org" } },
    { "@type": "WebSite", "@id": "https://your-domain.com/#site", "url": "https://your-domain.com", "name": "YourName", "publisher": { "@id": "https://your-domain.com/#org" } }
  ]
}
```

## Next.js (SSR-вставка для news / academy)

```jsx
export default function TrackPage({ track }) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Course",
    name: track.name,
    description: track.description,
    provider: { "@type": "Organization", name: "ExampleProduct", sameAs: "https://academy.your-domain.com" },
    inLanguage: "ru",
  };
  return (
    <>
      <script type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
      {/* контент страницы */}
    </>
  );
}
```

На Tilda тот же `<script type="application/ld+json">...</script>` кладётся в блок T123 или в head-зону настроек страницы (деплой — через скилл `tilda`).
