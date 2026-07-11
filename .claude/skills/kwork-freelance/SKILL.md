---
name: kwork-freelance
description: Freelance marketplace automation (Kwork.ru + Freelancer.com + others) via Chrome DevTools MCP or Playwright MCP. Registration, profile setup, kwork creation, project bidding. Use when user asks about freelance, bidding, creating kworks, earning money. Trigger phrases - "kwork", "кворк", "фриланс", "freelancer", "заработай", "создай кворк", "откликнись на проект", "биржа фриланс", "bid", "proposal".
---

# Freelance Marketplace Automation

Автоматизация работы на фриланс-платформах. Полный цикл: регистрация, профиль, поиск проектов, отправка предложений.

## Инструменты (выбор)

### Chrome DevTools MCP (`mcp__chrome-devtools__*`)
**Когда:** Kwork.ru, сайты с Vue/jQuery, нужен `evaluate_script` для `__vue__` манипуляций.

| Tool | Назначение |
|------|-----------|
| `navigate_page` | Переход по URL |
| `take_snapshot` | A11y дерево (предпочтительнее скриншота) |
| `take_screenshot` | Визуальный снимок (отладка) |
| `click` | Клик по uid элемента |
| `fill` | Заполнение input/select |
| `evaluate_script` | JS на странице (Vue `__vue__`, jQuery) |
| `type_text` | Ввод текста |
| `upload_file` | Загрузка файлов |

### Playwright MCP (`mcp__plugin_playwright_playwright__*`)
**Когда:** Freelancer.com, Angular SPA, сайты с ленивым рендером, нужны `page.evaluate()` для DOM-запросов.

| Tool | Назначение |
|------|-----------|
| `browser_navigate` | Переход по URL |
| `browser_snapshot` | A11y дерево страницы |
| `browser_take_screenshot` | Визуальный снимок |
| `browser_click` | Клик по элементу (ref) |
| `browser_type` | Ввод текста в фокусированный элемент |
| `browser_fill_form` | Заполнение формы |
| `browser_evaluate` | JS на странице |
| `browser_press_key` | Нажатие клавиш |
| `browser_wait_for` | Ожидание элемента/URL |

## Платформы и статусы

| Платформа | Тип | Коннекты/Биды | Пополнение | Статус |
|-----------|-----|---------------|------------|--------|
| Kwork.ru | Проекты | 0/30 | 6 апреля | 30 откликов |
| Freelancer.com | Проекты | 0/6 free | Monthly | 2 бида |
| Upwork | Проекты | — | — | Профиль НЕ настроен |
| PeoplePerHour | Проекты | — | — | На ревью (282K queue) |
| Outlier.ai | Микротаски | ∞ | — | Ждём интервью |
| Alignerr | Микротаски | ∞ | — | 7 заявок, нужно видео-интервью |
| DataAnnotation | Микротаски | ∞ | — | Assessment draft |
| Clickworker | Микротаски | ∞ | — | Нужна 2FA |
| User Interviews | UX Research | ∞ | — | Нужна SMS-верификация |
| Respondent.io | UX Research | ∞ | — | Активен, нужна верификация |

Подробности: `~/.claude/projects/C--Users-hamid/memory/freelance-platforms.md`

---

## Winning Proposal Framework

### Структура (универсальная)

```
1. Приветствие + конкретная привязка к проекту (НЕ generic)
2. Релевантный опыт (2-3 конкретных кейса, цифры)
3. План выполнения (3-5 шагов)
4. Стек технологий
5. Срок + цена
6. Уточняющий вопрос (показывает вовлечённость)
```

### Шаблон RU (Kwork)

```
Здравствуйте! [Конкретная привязка к задаче — что именно сделаю].

Мой релевантный опыт:
— [Кейс 1: что делал + результат]
— [Кейс 2: что делал + результат]
— [Кейс 3: если есть]

План выполнения:
1. [Анализ и уточнение ТЗ]
2. [Основная разработка]
3. [Интеграция / подключение]
4. [Тестирование]
5. [Передача + документация]

Стек: [технологии на РУССКОМ — НодЖС, ПостгреСКЛ, Питон, Докер]

Срок — N дней. Готов обсудить детали в чате.
```

### Шаблон EN (Freelancer.com, Upwork)

```
Hi! I'd like to help with [specific project reference].

Relevant experience:
- [Case 1 with metrics]
- [Case 2 with metrics]

My approach:
1. [Analysis/setup]
2. [Core development]
3. [Testing & deployment]
4. [Documentation & handoff]

Tech stack: [Node.js, Python, PostgreSQL, Docker, etc.]

Timeline: N days. [Clarifying question about the project?]
```

### Правила написания

- **ПЕРСОНАЛИЗАЦИЯ**: Упоминай конкретные детали из описания проекта
- **ЦИФРЫ**: "обработал 50K записей", "API отдаёт за 200мс", "бот на 10K юзеров"
- **УТОЧНЯЮЩИЙ ВОПРОС**: В конце — показывает что прочитал ТЗ ("Какой формат выгрузки предпочтителен?")
- **Kwork 70% русского**: Транслитерируй технологии — НодЖС, ПостгреСКЛ, Питон, Докер, Плейрайт
- **Freelancer.com**: headline max 50 chars, $ или ₹ зависит от клиента

---

## Матрица выбора проектов

### Приоритет 1 (берём сразу)
- ✅ Deliverable-based (написал код → сдал)
- ✅ Наш стек: Python, Node.js, TypeScript, React, Telegram bots, n8n, AI/ML, парсинг
- ✅ Мало откликов (< 10)
- ✅ Клиент верифицирован, высокий % найма
- ✅ Бюджет адекватный

### Приоритет 2 (берём если есть коннекты)
- ⚠️ Много откликов (10-20) но проект интересный
- ⚠️ Бюджет ниже среднего но быстрый проект (1-3 дня)
- ⚠️ Новый клиент без истории

### НЕ берём
- ❌ Live coding интервью, screen sharing
- ❌ Видео-собеседования, созвоны
- ❌ Долгосрочный full-time (нужна гибкость)
- ❌ Проекты без чёткого ТЗ ("сделайте как-нибудь")
- ❌ Австралийские клиенты (Freelancer.com — требуют Statement by a Supplier tax form)
- ❌ Enterprise с NDA/onboarding

---

## Kwork.ru — детальный workflow

### Поиск проектов

**URL:** `https://kwork.ru/projects`
- Фильтры: категория, бюджет, ключевые слова
- Поиск: `https://kwork.ru/projects?keyword=бот+telegram`
- Оценивай: бюджет, кол-во предложений, % найма, время

### Форма предложения

**URL:** `https://kwork.ru/new_offer?project={project_id}`

1. **Описание** (Trumbowyg, 150-2000 символов)
2. **Стоимость** (input)
3. **Порядок оплаты** — Vue компонент:
   ```javascript
   const wrapper = document.querySelector('.custom-kwork-offer__wrapper');
   const vue = wrapper.__vue__;
   vue.offerPayment = 'all'; // 'all' или 'stages'
   vue.paymentType = 'all';
   vue.isOfferPayment = true;
   vue.offerPaymentError = false;
   ```
4. **Название заказа** (Trumbowyg, max 70 chars, появляется ПОСЛЕ выбора оплаты)
5. **Срок** (v-select dropdown)
6. **Кнопка "Предложить"** — тратит 1 коннект

### Trumbowyg заполнение (3 способа одновременно)

```javascript
// 1. jQuery API
jQuery('textarea[name="fieldname"]').trumbowyg('html', content);
// 2. Прямое значение textarea
document.querySelector('textarea[name="fieldname"]').value = content;
// 3. Обновить contenteditable div через DOM property
const editor = document.querySelector('.trumbowyg-editor');
editor.textContent = ''; // очистить
editor.insertAdjacentHTML('beforeend', content);
```

### Vue Component Hierarchy

```
.new-offer-view (isKworkOffer)
  └── .custom-kwork-offer__wrapper (offerPayment, paymentType, offerName, ...)
      └── .offer-custom (price, duration, offerPayment, categories)
          └── .offer-payment-type (offerPayment: "all"|"stages")
```

Все данные: `wrapper.__vue__.$data`

---

## Freelancer.com — детальный workflow

### Поиск проектов

**URL:** `https://www.freelancer.com/search/projects`

**CRITICAL: Angular SPA рендеринг**

Элементы списка рендерятся лениво — `browser_snapshot` может показать пустые `<li>`. Используй `page.evaluate()`:

```javascript
const projects = Array.from(
  document.querySelectorAll('a[href*="/projects/"]')
).map(a => ({
  title: a.textContent.trim(),
  url: a.href
}));
```

### Форма бида

**URL:** при клике "Bid on this Project" на странице проекта

- **Bid Amount**: spinbutton, `fill()` может не сработать с Angular bindings
  - Workaround: `Control+a` (выделить всё) → `type()` новое значение
- **Delivery time**: select/spinbutton, аналогично
- **Describe your proposal**: textarea, стандартный fill работает
- **Skills**: Angular autocomplete, может потребовать evaluate

### Ценообразование (Freelancer.com)

- Смотри средний бид (Average Bid) на странице проекта
- Ставь **на 20-30% ниже** среднего для конкурентного преимущества
- Компенсируй коротким сроком доставки
- Конвертация валют: ₹ (INR), $ (USD), £ (GBP) — зависит от клиента

---

## Создание кворка (Kwork)

**URL:** `https://kwork.ru/new_kwork`

Многоэтапная форма:

1. **Категория/подкатегория** (select)
2. **Название + описание** (Trumbowyg — см. выше)
3. **Цена** (jQuery Chosen):
   ```javascript
   const select = document.querySelector('select[name="price"]');
   select.value = '5000';
   jQuery(select).trigger('chosen:updated');
   ```
4. **Чекбокс согласия** (может быть скрытый):
   ```javascript
   document.querySelector('input#profile-publication-agreement').click();
   ```
5. **Обложка**: 660x440 px, генерация через PIL

**CRITICAL: 70% русского текста** — транслитерируй все технические термины.

---

## Кросс-платформенные Gotchas

### Vue v-select (Kwork, DataAnnotation)
```javascript
const vSelect = el.__vue__;
vSelect.search = 'query';
// Wait for filteredOptions
vSelect.select(vSelect.filteredOptions[0]);
```
Обычный `fill` НЕ работает.

### Vuetify date picker (DataAnnotation)
Readonly input — overlay блокирует клики.
```javascript
const input = document.querySelector('input[type="date"]');
const vue = input.closest('.v-input').__vue__;
vue.value = '1988-04-05';
vue.$emit('input', '1988-04-05');
```
Если overlay: `Escape` → `evaluate_script`.

### Vuetify checkbox с ripple (DataAnnotation)
Ripple overlay перехватывает клики.
```javascript
document.querySelector('input[type="checkbox"]').click();
```
Используй `evaluate_script`, не Playwright click.

### Angular lazy rendering (Freelancer.com)
`browser_snapshot` показывает пустые элементы. Используй `browser_evaluate` + `document.querySelectorAll`.

### react-international-phone (User Interviews, Respondent)
Сначала выбери страну (`li[data-country="br"]`), потом вводи номер.

### jQuery Chosen dropdowns (Kwork)
```javascript
select.value = 'newValue';
jQuery(select).trigger('chosen:updated');
```
Визуально может не обновиться — проверяй скриншотом.

### Trumbowyg counters
Показывают "0 символов" до клика в редактор. При submit считается реальное значение.

### Angular bid form (Freelancer.com)
`fill()` не триггерит Angular bindings для spinbutton. Workaround: `Control+a` → `type()`.

### PeoplePerHour
`/signup` → 404. Использовать `/site/register#freelancer`.

### Clickworker
2FA через мобильное приложение обязательна для входа.

### Freelancer.com headline
Max 50 chars.

### Australian tax form (Freelancer.com)
Клиенты из Австралии требуют "Statement by a Supplier" — пропускай такие проекты.

---

## Стратегия (3 потока дохода)

| Поток | Платформы | Модель | Доход |
|-------|-----------|--------|-------|
| **Микротаски** | Outlier, Alignerr, DataAnnotation, Clickworker | Taxi — берёшь из очереди | $15-50/hr baseline |
| **Проекты** | Kwork, Freelancer, Upwork, PPH | Marketplace — proposals | $20-200+ per project |
| **UX Research** | User Interviews, Respondent | Участие в исследованиях | $30-200 per study |

### Ключевые принципы

- **Claude Code = speed advantage** — можно брать много проектов параллельно
- **НЕ принимать** live coding, screen sharing, видео-собесы
- **ТОЛЬКО deliverable-based** — написал → сдал → получил
- **Объём > маржа** на старте — набрать рейтинг и отзывы

---

## Данные аккаунтов

При регистрации сохраняй в `freelance-platforms.md`:
- Login/email/password
- Статус (зарегистрирован / профиль / активен)
- Количество коннектов/бидов
- Дата пополнения
- Поданные заявки

При подаче откликов сохраняй в `kwork-proposals.md` (или platform-specific):
- ID проекта
- Название
- Бюджет
- Цена предложения
- Срок

---

## Связанные файлы

- `~/.claude/projects/C--Users-hamid/memory/freelance-platforms.md` — все платформы и креды
- `~/.claude/projects/C--Users-hamid/memory/kwork-proposals.md` — 30 откликов Kwork
- `~/.claude/rules/routing.md` — маршруты (trigger phrases)
