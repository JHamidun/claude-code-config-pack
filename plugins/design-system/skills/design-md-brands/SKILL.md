---
name: design-md-brands
description: "Банк DESIGN.md: 73 бренда (Stripe, Linear, Notion) + 287 сайтов инди-эстетики. Триггеры: «как у Linear», «современный лендинг», «портфолио-стиль». НЕ по URL → brand-extractor."
---

# DESIGN.md brands — банк дизайн-систем

Reference-пак поверх ДВУХ открытых репозиториев, обоих под MIT:
**[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)** (бренды) и
**[educlopez/design-bites](https://github.com/educlopez/design-bites)** (инди-эстетика, 287 сайтов). Не хранит копии брендов локально — тянет актуальный `DESIGN.md` по требованию. Комплементарен нашим дизайн-скиллам, ничего не заменяет.

## Что такое DESIGN.md

Концепт **Google Stitch**: один plain-text markdown-файл в корне проекта, который ИИ-агент читает и по нему генерит консистентный UI. Без тулинга, без токен-JSON — просто разметка, которую понимает и человек, и модель. Репо awesome-design-md — курируемый банк таких файлов, снятых с сайтов известных брендов.

**Когда это нужно нам:** пользователь говорит «сделай в стиле Stripe / как у Linear / эстетика Notion». Раньше выбор был: (а) угадать палитру, (б) `brand-extractor` скрейпит живой сайт (риск anti-bot). Теперь для популярных брендов есть готовая, вычищенная дизайн-система — забрать и применить.

## Два источника, и они про разное

**Не «один больше другого» — разные типы запроса.** Пересечение между ними всего
два слага (`linear.app`, `opencode.ai`), так что берутся оба.

| Источник | Что внутри | Когда брать |
|---|---|---|
| **VoltAgent/awesome-design-md** (73+) | Узнаваемые бренды: Stripe, Vercel, Notion, Apple, BMW, Nintendo | «сделай как у Stripe», «эстетика Notion» — когда назван КОНКРЕТНЫЙ бренд |
| **educlopez/design-bites** (287) | 7 брендов, 84 портфолио и дизайн-студии, 196 инди-продуктов и личных сайтов | «современный лендинг», «портфолио-эстетика», «как делают студии» — когда назван ЖАНР, а не бренд |

Каталог второго лежит рядом: `references/design-bites-catalog.md` — 287 слагов
для мгновенного поиска, сами файлы тянутся по требованию.

```
https://raw.githubusercontent.com/educlopez/design-bites/main/design-mds/<слаг>/DESIGN.md
```

Слаг — это домен целиком: `linear.app`, `stripe.com`, `amie.so`,
`chanhdai.com`, `basement.studio`. Лицензия MIT, как и у первого.

Формат там свой, из девяти разделов: Visual Theme & Atmosphere · Color Palette &
Roles · Typography Rules · Component Stylings · Layout Principles · Depth &
Elevation · Do's and Don'ts · Responsive Behavior · Agent Prompt Guide.
Снят Playwright'ом с вычисленных стилей, поэтому цифры настоящие, а не на глаз:
у Linear это `rgb(8, 9, 10)` фоном, Inter Variable весом **510** (промежуточный
между 400 и 500, возможен только у переменного шрифта) и OpenType-фичи `cv01`,
`ss03`.

## Как достать DESIGN.md конкретного бренда

Файлы лежат по схеме `design-md/<brand>/DESIGN.md`. Забирай raw-версию через WebFetch:

```
https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/<brand>/DESIGN.md
```

Примеры (проверенные пути): `.../design-md/stripe/DESIGN.md`, `.../design-md/linear.app/DESIGN.md`, `.../design-md/vercel/DESIGN.md`, `.../design-md/notion/DESIGN.md`, `.../design-md/apple/DESIGN.md`.

**Гоча — имя папки ≠ всегда чистое имя бренда.** Некоторые с доменом/суффиксом: `linear.app`, `mistral.ai`, `x.ai`, `together.ai`, `opencode.ai`, `cal` (не cal.com), `bmw-m`, `dell-1996`, `nintendo-2001`, `runway ml`. Если прямой путь дал 404 — сперва глянь листинг папок: WebFetch `https://github.com/VoltAgent/awesome-design-md/tree/main/design-md`, найди точное имя, потом тяни raw.

## Каталог брендов (73+, на момент аудита 100+ папок — репо растёт)

| Категория | Бренды (имена ≈ папки) |
|---|---|
| **AI / LLM** | claude, cohere, elevenlabs, mistral.ai, minimax, together.ai, x.ai, ollama, replicate, runway ml, composio, opencode.ai |
| **Dev-tools** | cursor, vercel, warp, raycast, expo, lovable, resend, sentry, hashicorp, voltagent |
| **Backend / DB** | supabase, mongodb, posthog, sanity, clickhouse |
| **SaaS / Productivity** | linear.app, notion, cal, zapier, airtable, intercom, slack, superhuman, clay, miro |
| **Design / Content** | figma, framer, webflow, pinterest, theverge, wired |
| **Fintech / Crypto** | stripe, wise, coinbase, binance, kraken, mastercard, revolut |
| **Consumer / E-com** | airbnb, shopify, starbucks, spotify, uber, nike, meta |
| **Big Tech / Hardware** | apple, ibm, nvidia, hp, spacex, playstation, vodafone |
| **Automotive** | tesla, ferrari, bmw, bmw-m, lamborghini, bugatti, renault |
| **Ретро-веб (стилизация)** | dell-1996, nintendo-2001 |

Список неполный и меняется — источник истины всегда листинг репо. Нет нужного бренда — см. «Брендов нет в банке» ниже.

## Структура файла DESIGN.md (схема Stitch, 9 блоков)

Заголовки чуть плавают от бренда к бренду, но каркас один (пример со Stripe):

1. **Overview** — визуальная тема, атмосфера, философия
2. **Colors** — семантические роли + hex (Brand & Accent / Surface / Text / Semantic)
3. **Typography** — семейства, иерархия, принципы, заметка о шрифтах-заменах
4. **Layout** — spacing-шкала, grid/контейнер, философия воздуха
5. **Elevation & Depth** — тени, слои поверхностей (обычно таблица)
6. **Shapes** — border-radius шкала, геометрия фото/иллюстраций
7. **Components** — buttons, cards, inputs/forms, nav, pills/tags, signature-компоненты (со стейтами)
8. **Do's and Don'ts** — гардрейлы
9. **Responsive Behavior** — брейкпоинты, тач-таргеты, стратегия схлопывания, поведение картинок
   (+ иногда финальный **Iteration / Agent Prompt Guide** — краткая шпаргалка цветов для промпта агенту)

Формат цвета внутри — семантическое имя + токен + hex + где применять, напр.:
`**Indigo** (`{colors.primary}` — `#533afd`): signature CTA. Filled-pill button, link emphasis, gradient anchor.`

## Как применять (workflow)

1. Пользователь назвал бренд-референс → определи имя папки (листинг репо при сомнении).
2. WebFetch raw `DESIGN.md` → получил дизайн-систему.
3. Отдай её как контекст в `design-orchestrator` / нужный артефакт-скилл (`slides`, `interactive-prototype`, `website-creation`). Дальше весь артефакт держи в этой системе — палитра, типографика, радиусы, тени берутся из файла, не выдумываются.
4. Нужен один файл в корень проекта для другого ИИ-агента (Cursor/Stitch/Copilot) — просто положи `DESIGN.md` туда.

## DESIGN.md для презентации — и почему одного его мало

Тот же формат работает для деков, но с важной оговоркой: **для результата «один в один»
агенту нужен исходник презентации, а не скриншоты.** DESIGN.md объясняет стиль словами,
а точную геометрию — поля, переносы, сетку, порядок элементов — хранят только master и
layouts исходного файла. PDF и картинки — запасной вариант: цвета, шрифты и общая
композиция восстановятся, но это будет приближение, а не копия.

Путь к деку «один в один»:

1. **Взять исходник** — PPTX, Google Slides или Figma Slides. Не скриншоты.
2. **Выбрать 8-12 эталонных слайдов**, покрывающих layouts: обложка, текст, график, фото, таблица, разделитель, финал.
3. **Собрать DESIGN.md** только из найденных правил; логотипы, шрифты, иконки и фото сохранить отдельно в `assets/`.
4. **Отдать агенту** исходник + DESIGN.md + assets + текст новой презентации. Переиспользовать исходные layouts, а не рисовать их заново; слайды должны остаться редактируемыми.
5. **Проверить рендером** каждый слайд: поля, переносы, обрезку фото, подписи на графиках.

Что писать в презентационный DESIGN.md (наблюдаемые правила, не «современно и дорого»):
источник-файл · цвета (фон, текст, один акцент) · шрифты (заголовки, текст, цифры) ·
сетка (поля, колонки, выравнивание) · плотность (допустимый объём текста на слайд) ·
типы слайдов · стиль и обрезка изображений · оформление графиков · **запрещено**
(новые цвета и layouts).

Куда идти дальше:

| Где лежит исходник / что нужно | Инструмент |
|---|---|
| Корпоративный PPTX-шаблон, нужен стиль 1-в-1 | `mozlab-deck` — этот принцип в чистом виде: правятся настоящие слайды шаблона (113 типов-блоков), поэтому шрифты, мастера и графика не теряются |
| Чужой PPTX, нужно понять устройство или переверстать в HTML | `pptx-import` (распаковка XML: текст, картинки, координаты) |
| Собрать свой дек с нуля / КП Company | `slides`, `manus-slides`, `kp-deck-factory` |
| Исходник в Figma (Figma Slides, реальные слои и переменные) | `figma-api` + плагин `figma` / Cloud MCP Figma |
| Быстрый первый вариант из текста, точность повтора не важна | `gamma` |
| Ручная доводка и хранение бренд-кита | Canva (Cloud MCP `claude_ai_Canva`) |

Только PDF или скриншоты на входе — скажи об этом прямо: «повторю приближённо, для
точного совпадения нужен master». И переиспользуй только те материалы, на которые есть
право (см. `content-policy`).

## Брендов нет в банке / нужен свой

- **Живой сайт по URL** → `brand-extractor` (Playwright, вытащит цвета/шрифты/копирайт), результат оформи по шаблону `references/design-md-template.md`.
- **С нуля / свой продукт** → `design-system-create` + `color-system-builder` + `type-scale`, финал — в тот же шаблон DESIGN.md.
- Авторский DESIGN.md пиши по `references/design-md-template.md` (9 блоков Stitch).

## Этика / границы

- Репо MIT, файлы существуют для генерации консистентного UI и НЕ передают права на чужую айдентику. Не выдавай брендированную систему чужого продукта за свою — см. `content-policy`.
- Для НАШЕГО бренда (Anthropic look-and-feel) — `brand-guidelines`, не этот скилл.
- Требует только сетевого доступа к github/raw.githubusercontent — прокси/ключи не нужны.

## Соседние скиллы

`design-orchestrator` (диспетчер) · `brand-extractor` (скрейп живого сайта) · `design-system-create` (генерация с нуля) · `color-system-builder` / `type-scale` (сборка палитры/шкалы) · `frontend-design` (выбор эстетики когда системы нет) · `brand-guidelines` (Anthropic).
