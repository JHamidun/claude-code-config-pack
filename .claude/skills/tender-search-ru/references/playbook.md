# Tender Search Playbook (RU)

## rostender.info extraction (run inside browser_evaluate)

The tender **title** is `a.tender-info__description` (NOT the first `a[href*="/tender"]`, which is the
*category* link). The detail link is that same anchor's href. Drop noise client-side with the
include/exclude regexes (tune per product). Compute `active` from the «Окончание» date.

```js
() => {
  const today = new Date();                       // or pin a date
  const excl = /(книг|издани|литератур|учебник|повышени.{0,3}квалификац|образовательн|хакатон|олимпиад|чемпионат|робототехн|сервер|вычислительн|ускорител|оборудовани|комплект|пособи|благоустрой|колледж|школьн|мебел|строительств| дорог)/i;
  const incl = /(доступ к |нейросет|больш.{0,4}язык|llm|генеративн|чат-?бот|ассистент|gpt|подписк|неисключительн|обработк|аналитик|распознавани|интеллектуальн|речев|голосов|контактн.{0,3}центр|робот)/i;
  const rows = Array.from(document.querySelectorAll('.tender-row'));
  const out = rows.map(r => {
    const a = r.querySelector('a.tender-info__description, a.description');
    const title = a ? a.innerText.replace(/\s+/g,' ').trim() : '';
    const txt = r.innerText.replace(/\s+/g,' ');
    const price = ((txt.match(/[\d  ]{4,}₽/)||[''])[0]).trim();
    const num = (txt.match(/№\s?\d+/)||[''])[0];
    const endM = txt.match(/Окончание[^0-9]*(\d{2}\.\d{2}\.\d{4})/);
    const end = endM ? endM[1] : '';
    let active=false; if(end){const p=end.split('.');active=new Date(`${p[2]}-${p[1]}-${p[0]}`)>=today;}
    const href = a ? new URL(a.getAttribute('href'), location.origin).href : '';
    const relevant = incl.test(title) && !excl.test(title);
    return { num, title:title.slice(0,170), price, end, active, relevant, href };
  });
  return { total:(document.body.innerText.match(/Найдено[^\n]*/)||[''])[0],
           relevantActive: out.filter(x=>x.relevant&&x.active) };
}
```

## rostender mechanics

- Search: homepage textbox (placeholder "Введите ключевые слова…") -> submit -> redirect to
  `rostender.info/extsearch?query=HASH`. The hash is server-side; you must TYPE the query — you
  cannot build the URL from raw keywords.
- Pagination: append `&page=N` to the query URL. 20 rows/page. Block class `.pagination`.
- Multi-word queries become a fuzzy AND match -> few/garbage hits. Use ONE broad phrase + filter.
- Free-tier detail page shows: subject, region, deadline, "Способ размещения". HIDDEN behind
  registration: Организатор/Заказчик, Начальная цена/НМЦК, Документация, Ссылки на источники/ЭТП.
- "Способ размещения: Запросы и мониторинг цен / обоснование НМЦК (с ЭП)" => it is a PRICE REQUEST,
  not a live tender. Treat as entry point: submit a КП to shape the future procurement.
- IP/geo check: navigate to `http://ip-api.com/json/?fields=query,country,countryCode,city`
  (ipapi.co is Cloudflare-challenged in headless).

## zakupki.gov.ru direct search (ONLY from a RU IP)

Extended-search results page accepts GET params with the keyword:
`https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=<urlenc>&morphology=on&fz44=on&fz223=on&af=on&ca=on&sortBy=UPDATE_DATE&recordsPerPage=_50`
- fz44/fz223 = laws; af active, ca completed, pc/pa cancelled/postponed.
- Advantage over rostender: filter by **ОКПД2/КТРУ code** and see customer + НМЦК + docs free.

## Keyword set for AI / LLM products

`доступ к нейросетям`, `большие языковые модели`, `LLM`, `генеративный искусственный интеллект`,
`ИИ-ассистент`, `чат-бот на основе ИИ`, `генеративный контент`, `языковая модель`,
`распознавание речи`, `голосовой робот`, `контактный центр`, `неисключительные права на ПО`.
Broad-recall driver phrase: `искусственный интеллект` (then filter).

## OKPD2 codes for AI / software / SaaS

- 62.01 — Разработка компьютерного ПО (core for SaaS/AI products)
- 63.11.1 — Обработка данных, предоставление инфраструктуры (cloud/hosted AI access)
- 58.29 — Издание прочего ПО / предоставление лицензий
- 62.02 / 62.09 — Консультирование и прочие услуги в области ИТ

## Alternative aggregators (if rostender insufficient)

- synapsenet.ru — aggregator, partial free view
- tenderland.ru — aggregator, demo access
- b2b-center.ru — commercial (223-FZ + B2B) ETP
- roseltorg.ru — largest federal ETP (44/223-FZ)
- sberbank-ast.ru — federal ETP, gov + commercial

zakupki.gov.ru is the single source of truth for 44-FZ/223-FZ; aggregators re-index it plus
commercial ETPs.