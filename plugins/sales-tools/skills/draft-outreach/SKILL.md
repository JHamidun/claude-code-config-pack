---
name: draft-outreach
description: "B2B-аутрич с рисёрчем проспекта: email + LinkedIn + Telegram, цепочки касаний под корп-ЛПР. Триггеры: «холодное письмо», «написать ЛПР»."
metadata:
  version: 2.1.0
  updated: 2026-05-29
  ported_from: coreyhaines31/marketingskills (cold-email)
  reuses: linkedin, gmail, outlook, lead-research, zoom
---

# Draft Outreach

Research first, then draft. This skill never sends generic outreach - it always researches the prospect first to personalize the message. Works standalone with web search, supercharged when you connect your tools.

> **RU B2B mode:** For Russian-market cold outreach (продажа AI-воркшопов + консалтинга + B2B-когорт academy корп-ЛПР), jump to **«RU B2B Cold Outreach»** below. It ports the cold-email frameworks/sequences/personalization to the RU market (русский язык, корп-ЛПР, каналы email + LinkedIn + Telegram). Before drafting, read product context: `~/.claude/business-context.md` — разделы «ICP» (персоны, боли), «Продукт» (дифференциаторы), «Цены» (что предлагаем и по чём), «Воронка» и «Учёт и аналитика» (куда класть лид). Файла нет — заведи из `~/.claude/templates/business-context.md`; без него персонализация повиснет в воздухе.

---

## Connectors (Optional)

| Connector | What It Adds |
|-----------|--------------|
| **Enrichment** | Verified email, phone, background details |
| **CRM** | Prior relationship context, existing contacts |
| **Email** | Create draft directly in your inbox |

> **No connectors?** Web research works great. I'll output the email text for you to copy.

---

## Output Format

```markdown
# Outreach Draft: [Person] @ [Company]
**Research Sources:** [Web / Enrichment / CRM]

## Research Summary
Target: [имя, роль, компания] | Hook: [почему пишем именно сейчас] | Goal: [что хотим]

## Email Draft
To: [email или пометка «найти»] | Subject: [персонализированная тема]
[тело письма]
Subject alternatives: 2 варианта

## LinkedIn Message (если email нет)
Connection request (<300 символов, без питча) + follow-up после коннекта

## Why This Approach
| Элемент | На каком факте research'а построен |
| Opening / Hook / Proof / CTA | ... |

## Follow-up Sequence
День 3 — новый угол · День 7 — другой value prop · День 14 — breakup
```

Блок **Why This Approach** обязателен: он заставляет привязать каждый элемент письма к
конкретной находке. Без него персонализация незаметно съезжает в общие слова, и письмо
превращается в шаблон, который отличается от массовой рассылки только именем в шапке.

---

## Execution Flow

### 1. Research — всегда до драфта

Web search (по умолчанию) + enrichment/CRM, если подключены.

**Must find before drafting:**
- Who they are (title, background)
- What the company does
- Recent news or trigger
- Personalization hook

Ни одного триггера не нашлось — не пиши шаблон «на всякий случай». Скажи, чего не хватает,
и предложи либо другой канал, либо другого адресата в той же компании.

### 2. Identify Hook

```
Priority order for hooks:
1. Trigger event (funding, hiring, news) → Most timely
2. Mutual connection → Social proof
3. Their content (post, article, talk) → Shows you did research
4. Company initiative → Relevant to their priorities
5. Role-based pain point → Least personal but still relevant
```

### 3. Draft

**Email Structure (AIDA):**
```
SUBJECT: [Personalized, <50 chars, no spam words]

[Opening: Personal hook - shows you researched them]

[Interest: Their problem/opportunity in 1-2 sentences]

[Desire: Brief proof point - similar company result]

[Action: Clear, low-friction CTA]

[Signature]
```

**LinkedIn.** Connection request — жёсткий лимит **300 символов**, общий знакомый или
конкретный интерес, **без питча**: заявка с оффером внутри режется чаще, чем принимается.
Follow-up шлётся только ПОСЛЕ коннекта: сначала value (наблюдение, статья, инсайт), потом
мягкий переход к цели, в конце вопрос, а не предложение.

### 4. Deliver

Email-коннектор подключён → создать **черновик** (to/subject/body), вернуть ссылку и
сказать «review and send». Отправлять самому нельзя: адресат живой человек, и цена ошибки
в холодном касании — сожжённый контакт. Коннектора нет → выдать текст письма для копирования.

---

## Email Style Guidelines

1. **Be concise but informative** — Get to the point quickly. Busy people skim.
2. **No markdown formatting** — Never use asterisks, bold (**text**), or other markdown. Write plain text that looks natural in any email client.
3. **Short paragraphs** — 2-3 sentences max per paragraph. White space is your friend.
4. **Simple lists** — If listing items, use plain dashes. No fancy formatting.

**Good:** `- Case study from a similar company`
**Bad:** `- **Case study** from a similar company`

---

## What NOT to Do

**Generic openers:**
- "I hope this email finds you well"
- "I'm reaching out because..."
- "I wanted to introduce myself"

**Feature dumps:**
- Long paragraphs about your product
- Multiple value props at once
- No clear CTA

**Fake personalization:**
- "I noticed you work at [Company]" (obviously)
- "Congrats on your role" (without context)

**Markdown in emails:**
- Using **bold** or *italic* asterisks
- Headers or formatted lists that won't render

**Instead:**
- Lead with something specific you learned
- One clear value prop
- One clear ask
- Plain text formatting only

---

## Channel Selection

```
IF verified email available:
  → Email preferred (higher response rate)
  → Also provide LinkedIn backup

IF no email:
  → LinkedIn connection request
  → Follow-up message template for after connection

IF warm intro possible:
  → Suggest mutual connection outreach first
```

---

## Настройки аутрича (заполнить один раз)

Имя, должность, компания, value prop, подпись, пруф-поинты, варианты CTA и тон —
шаблон в **`references/outreach-config-template.md`**. Заполнить перед первым письмом:
без пруф-поинтов блок Desire в AIDA нечем закрыть, и письмо остаётся обещанием без основания.

---

# RU B2B Cold Outreach (NEW — русский рынок, Your Name)

> Порт `cold-email` под российский B2B. Цель — холодные касания к корп-ЛПР за **AI-воркшоп / AI-консалтинг / B2B-когорту обучающей программы**. Кому: HR-директора и руководители L&D, гендиры/владельцы, руководители отделов. Главный CTA — **бесплатная диагностика AI-зрелости команды / бесплатная консультация** (бронь Zoom). Принцип тот же: **сначала research, потом draft**. Голос — равный коллега-эксперт (практик, который сам внедряет AI в командах), не вендор; по-русски, без канцелярита и хайпа.

## Перед написанием

1. **Прочитай `~/.claude/business-context.md`** — разделы «ICP» (персоны, боль их словами, триггер покупки), «Продукт» (чем отличаешься и что альтернативы делают лучше — это половина работы с возражениями), «Воронка» (какой CTA у касания) и «Учёт и аналитика» (куда записывать касание). Файла нет — заведи из `~/.claude/templates/business-context.md`. Без него письмо получится «про нас», а не про адресата: пруфы придётся выдумать, а выдуманный пруф в холодном письме — это конец переписки.
2. Собери сигналы по компании/ЛПР — делегируй скиллу `lead-research` (RU-источники: Контур.Фокус, Rusprofile, СПАРК, HH, сайт). Не выдумывай факты.
3. Определи: кому пишешь (роль из персон), что хочешь (цель касания → консультация/воркшоп), value под его роль, пруф ([ваша роль] / [N корп-клиентов] / [N материалов] / [корп-кейс]), сигнал «почему сейчас».

Хватает сильного сигнала + ясного value — пиши. Не блокируйся на отсутствии полей, отметь что усилило бы письмо.

## Принципы (RU)

- **Пиши как равный эксперт, не как продавец.** Прочитай вслух. Звучит как реклама — переписывай. На «вы», но по-человечески. Автор — практик (сам внедряет AI в командах, а не пересказывает чужое), а не инфоцыган.
- **Каждое предложение зарабатывает место.** Холодное письмо безжалостно короткое. 50–90 слов оптимум для русского.
- **Персонализация связана с проблемой.** Убрал первую строку — письмо рассыпалось? Тогда персонализация работает. Иначе это просто «attention hack».
- **Веди их миром, а не своим.** «Вы/ваш» доминирует над «мы/наш». Не открывай тем, кто ты и что делает твоя компания.
- **Один запрос, низкое трение.** CTA на бесплатную консультацию/диагностику AI-зрелости («Имеет смысл 20 минут разобрать, где AI даст команде быстрый результат?») бьёт прямой питч воркшопа. Один CTA на письмо.

## Каналы (RU multi-touch)

| Канал | Когда | Чем шлём | Нюанс |
|---|---|---|---|
| **Email** | есть рабочий email ЛПР/корп-домен | `gmail` или `outlook` (черновик) | основной для B2B; маркировка рекламы если применимо (см. ниже) |
| **LinkedIn** | есть профиль, нет email | `linkedin` (connection request <300 симв + value-first follow-up) | работает по топам/иннов-директорам; внутренние правила LinkedIn, не 38-ФЗ |
| **Telegram** | ЛПР активен в проф-ТГ, тёплый контекст | вручную; контент для прогрева — своим пайплайном постинга | уместен после касания на конференции/в чате; не холодный спам |

Channel-mix под топов: **email → LinkedIn → (опц.) Telegram**, чередуя углы. Деталь по углам и каденсу — `references/sequences-ru.md`.

## Что делегировать (НЕ дублировать)

| Нужно | Скилл |
|---|---|
| Сигналы/фирмографика по компании и ЛПР | `lead-research` (RU-источники) |
| Отправка email / черновик | `gmail`, `outlook` |
| LinkedIn касания | `linkedin` |
| Бронь созвона / диагностики | `zoom` (бесплатная консультация) |
| Контакты/история сделки, запись касания | API твоей CRM (Битрикс24/amoCRM/HubSpot) — какая у тебя, смотри `~/.claude/business-context.md` → «Учёт и аналитика» |
| Контент для ТГ | свой пайплайн постинга (в паке не поставляется) |

После касания — **зафиксируй активность в CRM**: контакт, канал, дата, реакция. Записывай в свою CRM (в Битрикс24 это метод `crm.activity.add`, в amoCRM — примечание к сделке) и/или в свою продуктовую БД, если лиды живут там. Горячий enterprise эскалируется через `handoff_to_user`. Это вход в воронку (см. `revops-ru`).

## References (RU)

| Файл | Что внутри |
|---|---|
| `references/frameworks-ru.md` | копирайт-фреймворки (PAS/BAB/QVC/AIDA + Mouse Trap/Vanilla Ice Cream) с RU-примерами под воркшоп/консалтинг |
| `references/subject-lines-ru.md` | тема письма по-русски: коротко, «внутренне», без продажности; данные + примеры |
| `references/sequences-ru.md` | мульти-тач каденс (5 касаний), ротация углов, breakup-письмо, фразы-убийцы — RU |
| `references/personalization-ru.md` | 4 уровня персонализации + стек RU-сигналов (откуда брать: Контур/HH/новости/ТГ) |

## Комплаенс (холодные касания, РФ)

- **152-ФЗ «О персональных данных».** Контакт ЛПР — публичный рабочий канал (корп-email, профиль). Личные email/телефоны — повышенный риск, не использовать без основания. Храни источник + дату (собирает `lead-research`, фиксируй в своей CRM).
- **38-ФЗ «О рекламе».** Холодное B2B-письмо «приглашаю на бесплатную диагностику» — деловая переписка, не реклама. Но если письмо = рекламная рассылка (оффер/акция массово, например цены на когорту) → нужна маркировка/согласие + механизм отписки. Один email конкретному ЛПР с деловым предложением обычно вне рекламного контура — но при массовости консультируйся.
- **LinkedIn / Telegram** регулируются правилами площадок, не 38-ФЗ.

## Чеклист качества (RU)

- [ ] Звучит как человек? (прочитай вслух)
- [ ] Ответил бы сам на такое?
- [ ] «Вы/ваш» доминирует над «мы/наш»?
- [ ] Персонализация связана с болью корп-команды (сотрудники не используют AI / нет практического результата / зоопарк инструментов)?
- [ ] Один ясный CTA с низким трением (бесплатная консультация/диагностика)?
- [ ] Нет канцелярита, хайпа («революционный»), AI-следов («надеюсь, письмо застало вас»)?
- [ ] Факты (соцпруф: [ваша роль] / [N корп-клиентов] / [N материалов] / [корп-кейсы]) сверены с `business.md`, не выдуманы?
- [ ] Касание записано там, где ты ведёшь лиды (CRM или таблица — раздел «Учёт и аналитика» в `business-context.md`)?
