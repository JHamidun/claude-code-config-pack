# Довести вид example-queryового приложения: 8 приёмов Google AI Studio и наши аналоги

Источник: Google AI Studio Build Guide, «AI UI design: 8 ways to make vibe-coded apps look
better», Geneviève Huskens, 16.09.2026 —
https://aistudio.google.com/learn/ai-ui-design-google-ai-studio (страница рендерится
JavaScript, обычный fetch отдаёт пустую оболочку; снята через браузер 17.09.2026, сырой
текст — `~/.claude/docs/sources/aistudio-ai-ui-design-2026-09-16.raw.json`).

Главная мысль статьи: сделать приложение, которое **работает**, проще, чем сделать
**красивое**. Модель, предоставленная сама себе, выдаёт интерфейс «generic, cliché, or
cluttered». Исправляется связкой: точное стилевое направление в первом промпте плюс ручная
доводка визуальными инструментами вместо длинных текстовых просьб.

Когда читать: пользователь собирает приложение в Google AI Studio Build и просит «сделать
красивее»; или наш собственный прототип выглядит как example-query и нужен порядок доводки.

## Сводка: приём → в AI Studio → у нас

| # | Приём | В AI Studio Build | Наш аналог |
|---|---|---|---|
| 1 | Задать стиль скриншотом-референсом или извлечь дизайн-язык словами | Приложить 1+ скриншот к первому промпту; или в Playground попросить описать стиль и вставить описание в промпт Build | `moodboard` → «Скриншот → описание стиля»; по URL — `brand-extractor`; бренд словом — `design-md-brands` |
| 2 | Сразу генерировать связные картинки вместо заглушек и битых стоков | Инструмент `generate_image` (Nano Banana) внутри Build, из первого же промпта | `image-generation` (NB2 — дефолт), одна стилевая формула на все картинки приложения |
| 3 | Точечно править готовую картинку | Edit → клик по картинке → волшебная палочка: правка Nano Banana, новая картинка на месте или своя с диска | `nano-banana-pro` (перерендер/правка), `openai-dalle` (edit с референсами), замена файла руками |
| 4 | Перебирать шрифты на живой вёрстке, а не перегенерацией | Edit → клик по тексту → поиск по Google Fonts → Submit; для всего приложения — «Change all fonts to …» | `tweaks-panel` (крутилка шрифта), `type-scale`, кириллица — `fonts-bundle` |
| 5 | Рестайл без потери логики: пачка вариантов бок-о-бок | Edit → Design: несколько полных HTML/CSS-редизайнов, тексты, формы и логика сохраняются | `design-canvas` → «Рестайл рабочего экрана»; безопасность логики — `design-guardrails` |
| 6 | Отступы и размеры — прямой правкой элемента, а не фразой «добавь 8px второму контейнеру слева» | Edit → клик по DOM-элементу → padding/margin/размер/hex → Submit | `visual-edit` (мышкой), `comment-injector` (адресовать правку) |
| 7 | Убрать мусор: обвести лишнее и одной командой удалить | Edit → Annotate → обвести → «Remove all circled elements» | `comment-injector` → «Пачка пометок»; что считать мусором — `content-rules` |
| 8 | Начать не с пустого листа, а с хорошего образца | App Gallery → Remix → редактируемая копия в Build: видно промпты и устройство UI | `moodboard` (таблица библиотек, строка App Gallery), `cookbook` |

## Приёмы подробно

### 1. Референс-скриншот или извлечённый дизайн-язык

По статье, Gemini разбирает на скриншоте раскладку, палитру и плотность отступов.
**Gemini 3.8 Flash и 3.7 Flash** Google называет особенно сильными в воссоздании UI по
скриншоту (оба ID есть в `models.list` на 17.09.2026: `gemini-3.8-flash`, `gemini-3.7-flash`).

Если копировать чужую раскладку не нужно, лучше описать стиль правильными терминами. Для
этого — промпт извлечения (дословно из статьи; рабочая копия и русская версия —
`moodboard`):

```text
Analyze this website screenshot and describe its visual design system in 5-6 concise
sentences. Return your answer as a prompt that I can directly put into an AI coding tool
like AI Studio. Include specific details on its color palette (with hex approximations),
typography hierarchy, card border treatments, spacing density, and overall aesthetic mood
(e.g., editorial minimalist, dark glassmorphism, or neo-brutalist).
```

Полученное описание вставляется в промпт сборки **дословно**.

Граница: воспроизводить чужой UI один-в-один нельзя — `content-policy`. Извлечённое
описание — это язык решений, а не разрешение на копию.

### 2. Картинки — частью первого промпта

«Generic placeholder images or broken stock image links can ruin an app's first
impression.» В Build это инструмент `generate_image` на Nano Banana.

⚠️ Грабля AI Studio: генерация картинок в Build идёт **за платный ключ**. Шестерёнка →
Usage → «You're currently using free tier requests» → выбрать платный API-ключ; после
генерации можно вернуться на бесплатные запросы.

У нас: заглушка с подписью уместна только на стадии вайрфрейма. Прототип, который увидит
человек, получает сгенерированные картинки **одним стилем на всё приложение** — одна
стилевая формула в каждом промпте `image-generation`, а не случайные стоки.

### 3. Правка картинки на месте

Три варианта из инспектора картинок: правка словами («change the backdrop from wood to
white marble»), новая картинка на том же месте, загрузка своей (логотип, фото продукта).

### 4. Шрифты — на реальной вёрстке

Шрифт меняют на живом экране, а не перегенерацией приложения; пару проверяют на настоящем
макете до фиксации.

⚠️ Примеры шрифтов из статьи **не переносить**: Space Grotesk и Playfair Display у нас в
списке заезженных ИИ-лиц (`content-rules`, `design-taste` п.5). Переносится приём — перебор
на живой вёрстке, — а не конкретные гарнитуры. Для русского текста сначала проверка
кириллицы.

### 5. Design Variations — рестайл с сохранением логики

Движок берёт существующий код и выдаёт несколько полных HTML/CSS-редизайнов, «strictly
preserving all of your text, forms, and interactive logic». Направление можно задать
промптом — три примера из статьи:

- Editorial & Refined: «Restyle with serif headers, generous whitespace, and a bright white background.»
- Technical & Systematic: «Restyle as a high-density data terminal with monospace metadata and visible grid borders.»
- Warm & Approachable: «Restyle with soft pastel cards, pill-shaped buttons, and friendly rounded corners.»

У нас это `design-canvas` → «Рестайл рабочего экрана».

### 6. Прямая правка элемента

Текстовые просьбы про пиксели «tedious and imprecise». Выбрать элемент и крутить
padding/margin/размер/цвет. «Пять минут на отступы и выравнивание» — самый дешёвый
переход от прототипа к продукту. Выделенный элемент заодно адресует крупную правку:
«This container should take up 70% of the landing page. Adjust the sizing of all other
elements accordingly.»

### 7. Annotate — чистка лишнего

«The fastest way to spot a vibe-coded app is when there are lots of chips and text
elements that serve no purpose.» Модели «go overboard»: лишние чипсы, дублирующие
статус-бейджи, ненужные виджеты. Порядок: критически осмотреть экран → обвести всё
лишнее → одной командой удалить. Тот же приём чинит визуальные баги: обведённый наезд
текста показывает модели, куда смотреть.

### 8. Remix из App Gallery

Галерея AI Studio — витрина апплетов Google, «we do our best to make them look really
good». Remix даёт редактируемую копию в Build с видимыми промптами. Шаблон промпта:
«Keep this exact visual style and layout, but turn it into an applet about [your topic].»

## Порядок доводки (по статье)

Стиль задаётся **до** генерации (1, 2, 8), доводка — визуальными инструментами **после**
(3–7). Длинный текстовый промпт с перечислением пикселей и элементов проигрывает прямому
указанию на экране.
