# Impeccable Detector — 59 детерминированных правил (первоисточник)

> Источник: **pbakaus/impeccable** (npm `impeccable`, сайт impeccable.style). Канон правил вытащен из
> `cli/engine/registry/antipatterns.mjs` (реестр 59 записей: `id` / `category` / `name` / `description`)
> и `reference/craft-floor.md` (список Refuse). Страница `/slop` показывает 65 карточек — 6 лишних
> это переформулировки и раскрытые подпункты того же реестра; движок `cli/engine/rules/checks.mjs`
> реализует ровно эти id.
>
> Этот файл — справка и трассировка. Действующие правила уже вписаны в `SKILL.md` (пункты 2, 5, блок 16-28)
> и в `content-rules/SKILL.md`. Сюда лезем, когда надо свериться с оригинальной формулировкой или порогом.

## Категория `slop` — 27 правил (признаки ИИ-генерации)

| id | Что ловит | У нас |
|---|---|---|
| `side-tab` | Толстый цветной бордер с одной стороны карточки — самый узнаваемый признак | content-rules |
| `border-accent-on-rounded` | Толстый акцентный бордер на скруглённой карточке: бордер конфликтует со скруглением | content-rules (родственное) |
| `overused-font` | Inter, Roboto, Fraunces, Geist, Plus Jakarta Sans, Space Grotesk | design-taste #5 |
| `flat-type-hierarchy` | Кегли слишком близко, нет иерархии; шаг рампы ≥1.25 | content-rules (разрыв 2x) |
| `gradient-text` | Градиент на тексте — заголовки, метрики | content-rules ✚ |
| `ai-color-palette` | Фиолет/violet-градиенты, cyan-on-dark | design-taste #3 |
| `cream-palette` | Кремовый/бежевый фон как «безопасный вкусный» дефолт | design-taste #4 |
| `nested-cards` | Карточки внутри карточек | content-rules ✚ |
| `monotonous-spacing` | Один и тот же отступ везде: нет ритма (плотные группы / щедрые разрывы) | design-taste #21 ✚ |
| `bounce-easing` | Bounce/elastic easing; нужен экспоненциальный ease-out (quart/quint/expo) | design-taste #26 ✚ |
| `pulsing-dot` | Пульсирующая точка статуса как декорация | content-rules ✚ |
| `blinking-cursor` | Мигающая каретка в hero — имитация ввода там, где ввода нет | content-rules ✚ |
| `shape-assembled-illustration` | Hero-SVG, собранный из примитивов = клипарт-заглушка | content-rules ✚ |
| `dark-glow` | Цветное гало-тень с нулевым offset (box/text-shadow), и любая цветная размытая тень на тёмном | content-rules ✚ / design-taste #23 |
| `radial-halo` | Насыщенный radial-gradient-мазок как фоновое свечение на тёмной странице | content-rules (градиент-туман) |
| `radial-spotlight-glow` | Полупрозрачный акцентный «прожектор» под hero/секцией | content-rules (градиент-туман) |
| `marquee` | Автопрокрутка/бегущая лента | content-rules ✚ |
| `icon-tile-stack` | Скруглённый квадрат-иконка НАД заголовком = универсальный шаблон feature-карточки | content-rules ✚ |
| `italic-serif-display` | Крупный курсивный serif как главный hero-заголовок (Fraunces, Recoleta, Playfair, Newsreader-italic) | design-taste #5 ✚ |
| `hero-eyebrow-chip` | Мелкая капсовая метка или пилюля-чип прямо над огромным hero-заголовком | design-taste #2 |
| `kicker-above-heading` | Кикер/эйбрау над заголовком — **запрет целиком**, а не лимит на количество | design-taste #2 ✚ (было «1 на 3 секции») |
| `numbered-section-labels` | Мелкая нумерация рядом с заголовками секций | design-taste #12 |
| `em-dash-overuse` | Насыщение em-dash. Advisory: срабатывает от 8 штук при плотности ~1 на 500 знаков | design-taste #1 (у нас строже: полный запрет) |
| `marketing-buzzword` | streamline / empower / supercharge / world-class / enterprise-grade / next-generation / cutting-edge | content-rules ✚ (список расширен) |
| `aphoristic-cadence` | 3+ секции, добитые «X. No Y.» / «Не фича. Платформа.» | content-rules ✚ |
| `oversized-h1` | Заголовок-предложение, набранный display-кеглем, съедает первый экран (короткий заголовок тем же кеглем — норм) | content-rules ✚ (см. ниже) |
| `extreme-negative-tracking` | Трекинг туже, чем точка, где буквы держат форму (пол `-0.04em`) | design-taste #19 ✚ |

## Категория `quality` — 32 правила (общий брак, не только ИИ)

| id | Что ловит | У нас |
|---|---|---|
| `broken-image` | `<img>` с пустым/отсутствующим/placeholder-значением src | content-rules (серый «Image») |
| `script-error` | Непойманное исключение при загрузке — убивает reveal-ы и интерактив | design-guardrails (0 console-ошибок) |
| `content-hidden-at-rest` | Большая доля текста осталась `opacity: 0` после всех reveal-обработчиков | design-taste #25 ✚ |
| `edge-flush-cards` | Карточки в горизонтальном скроллере прижаты к краю контейнера, срезаются скругления | — (узкое) |
| `text-occlusion` | Текст закрыт непрозрачным слоем | design-taste #28 (родственное) |
| `first-viewport-column-overflow` | Одна колонка первого экрана уходит далеко за фолд, вторая помещается | — (узкое) |
| `gray-on-color` | Серый текст на цветном фоне | design-taste #22 ✚ |
| `low-contrast` | WCAG AA: 4.5:1 тело, 3:1 крупное | frontend-design / design-taste #22 |
| `layout-transition` | Анимация width/height/padding/margin | design-taste #24 ✚ |
| `line-length` | Строки шире ~80 символов; max-width 65-75ch | design-taste #16 ✚ |
| `cramped-padding` | Паддинг мал для кегля / дети упираются в видимую границу. Пол 8px, норма 12-16px | design-taste #20 ✚ |
| `body-text-viewport-edge` | Абзацы прижаты к краю вьюпорта. Пол 16px, норма 24-32px | design-taste #20 ✚ |
| `tight-leading` | line-height ниже 1.3; норма тела 1.5-1.7 | design-taste #17 ✚ |
| `skipped-heading` | h1 → h3 без h2 | design-taste #28 ✚ |
| `heading-rhythm` | Отступ над заголовком должен превышать отступ под ним | design-taste #21 ✚ |
| `justified-text` | Выключка по формату без переносов = «реки» | design-taste #20-блок (см. ниже) |
| `tiny-text` | Тело ниже 12px; ≥14px, идеал 16px | design-taste #18 ✚ |
| `undersized-ui-text` | Функциональный UI-текст ниже 11px. Пол держится даже в футере; «есть в рампе DESIGN.md» не освобождает. Исключения: sup/sub, sr-only, код | design-taste #18 ✚ |
| `all-caps-body` | Длинные абзацы капсом | content-rules / design-taste (см. ниже) |
| `wide-tracking` | Трекинг тела выше 0.05em | design-taste #19 ✚ |
| `text-overflow` | Контент шире контейнера, горизонтальный скролл | design-guardrails / design-taste #28 |
| `repeated-container-text` | Один и тот же текст 3+ раза в разных слотах одной карточки | content-rules ✚ |
| `clipped-overflow-container` | `overflow: hidden/clip` режет абсолютно спозиционированные тултипы и меню | design-taste #28 ✚ |
| `design-system-font` | Шрифт вне DESIGN.md | design-taste (хвост блока 2b) |
| `design-system-color` | Литеральный цвет вне палитры DESIGN.md и её тональных рамп | design-taste (хвост блока 2b) |
| `design-system-radius` | Радиус вне задокументированной шкалы | design-taste (хвост блока 2b) |
| `design-system-font-size` | Кегль между ступенями задокументированной рампы | design-taste (хвост блока 2b) |
| `gpt-thin-border-wide-shadow` | Волосяной бордер + широкая диффузная тень одновременно | content-rules ✚ / design-taste #23 |
| `repeating-stripes-gradient` | `repeating-gradient`-полоски как фактура | content-rules ✚ |
| `codex-grid-background` | Декоративная сетка из hairline-градиентов, тайлинг фиксированной ячейкой. Разрешена только на настоящем канвасе/карте/чертеже | content-rules ✚ |
| `theater-slop-phrase` | «X — это театр» как отмашка | content-rules ✚ |
| `image-hover-transform` | Scale/rotate картинки на hover | content-rules ✚ |

## Не из реестра: `craft-floor.md` → Refuse

Отдельный список «дефолтов категории» (не баны — бриф может их отыграть, но тянуться к ним рефлексом значит не решать):

**Каркасы страницы:** одинаковые карточки «иконка + заголовок + текст» как структура страницы · hero-метрика (большая цифра, мелкая подпись, статы, акцент) · кикер над заголовком (**это именно бан, брифом не отыгрывается**) · нумерация секций 01/02/03 без информационной нагрузки · модалка для задачи, которой не нужны ни прерывание, ни защищённый фокус.

**Привычки поверхности:** градиент-текст · стекло и блюр как декорация, а не как конкретный эффект · цветной `border-left/right` толще 1px на карточках, пунктах списка, callout-ах, алертах · жёсткие смещённые тени `4px 4px 0` вне настоящего необрутализма · спарклайны, кольца прогресса и скруглённые прямоугольники с мягкой тенью вместо содержимого · mono как костюм «технологичности» · системное display-лицо (Impact, Arial Black, платформенный sans) как голос заголовков · эмодзи/юникод-глиф вместо иконки · геометрические маски вместо органического контура фото · светлая/тёмная тема, выбранная по категории, а не по сцене использования.

**Verify (пороги craft-floor):** display максимум 6rem · пол трекинга -0.04em · мера 65-75ch · тень несёт offset и blur · над заголовком места больше, чем под ним · одно авторское движение вместо одинакового входа у каждой секции · браузерные поверхности (выделение, каретка, скроллбар, focus-ring, underline-offset, tabular-nums) покрашены от палитры.

## Соседние разделы источника (для контекста, не правила)

- `/docs` — 23 команды-директивы (`shape`, `audit`, `critique`, `animate`, `bolder`, `colorize`, `delight`, `layout`, `overdrive`, `quieter`, `typeset`, `adapt`, `clarify`, `distill`, `harden`, `onboard`, `optimize`, `polish`, `document`, `extract`, `live`, `init`, `impeccable`). **У нас намеренно не заводятся**: описания команд делят общий бюджет системного промпта, а функционально это те же режимы, что уже покрыты дизайн-семьёй (`design-orchestrator` → `frontend-design`/`design-taste` → `design-guardrails`).
- `/designing` — режимы по намерению посетителя: Persuade (лендинг) · Operate (интерфейс приложения) · Read (документация) · Experience (портфолио). Совпадает с нашим Design Read.
- **Live Mode** — локальный сервер на :4321: выбрать элемент в браузере, оставить комментарий, получить 3 варианта, принять один — правка уезжает в исходник.
- **Detector CLI** — `npx impeccable detect <path>`, сканирует HTML/CSS/JSX/TSX/Vue/Svelte плюс браузерный движок по URL (вычисленные стили, скриншот-контраст).
