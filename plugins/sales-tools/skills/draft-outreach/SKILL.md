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

> **RU B2B mode:** For Russian-market cold outreach (продажа AI-воркшопов + консалтинга + B2B-когорт academy корп-ЛПР), jump to **«RU B2B Cold Outreach»** below. It ports the cold-email frameworks/sequences/personalization to the RU market (русский язык, корп-ЛПР, каналы email + LinkedIn + Telegram). Before drafting, read product context: заведи собственный навык-контекст продукта (business: персоны, боли, дифференциаторы; offerings: продукты и CTA; funnel: механика воронки и CRM) и читай его первым — в паке такой навык не поставляется, без него персонализация повиснет в воздухе.

## Connectors (Optional)

| Connector | What It Adds |
|-----------|--------------|
| **Enrichment** | Verified email, phone, background details |
| **CRM** | Prior relationship context, existing contacts |
| **Email** | Create draft directly in your inbox |

> **No connectors?** Web research works great. I'll output the email text for you to copy.

---

## How It Works

```
+------------------------------------------------------------------+
|                      DRAFT OUTREACH                               |
|                                                                   |
|  Step 1: RESEARCH (always happens first)                         |
|  - Web search (default)                                           |
|  - + Enrichment (if enrichment tools connected)                  |
|  - + CRM (if CRM connected)                                      |
|                                                                   |
|  Step 2: DRAFT (based on research)                               |
|  - Personalized opening (from research)                          |
|  - Relevant hook (their priorities)                              |
|  - Clear CTA                                                      |
|                                                                   |
|  Step 3: DELIVER (based on connectors)                           |
|  - Email draft (if email connected)                              |
|  - Copy for LinkedIn (always)                                    |
|  - Output to user (always)                                        |
+------------------------------------------------------------------+
```

---

## Output Format

```markdown
# Outreach Draft: [Person] @ [Company]
**Generated:** [Date] | **Research Sources:** [Web, Enrichment, CRM]

---

## Research Summary

**Target:** [Name], [Title] at [Company]
**Hook:** [Why reaching out now - the personalized angle]
**Goal:** [What you want from this outreach]

---

## Email Draft

**To:** [email if known, or "find email" note]
**Subject:** [Personalized subject line]

---

[Email body]

---

**Subject Line Alternatives:**
1. [Option 2]
2. [Option 3]

---

## LinkedIn Message (if no email)

**Connection Request (< 300 chars):**
[Short, no-pitch connection request]

**Follow-up Message (after connected):**
[Value-first message]

---

## Why This Approach

| Element | Based On |
|---------|----------|
| Opening | [Research finding that makes it personal] |
| Hook | [Their priority/pain point] |
| Proof | [Relevant customer story] |
| CTA | [Low-friction ask] |

---

## Email Draft Status

[Draft created - check email]
[Email not connected - copy email above]
[No email found - use LinkedIn approach]

---

## Follow-up Sequence (Optional)

**Day 3 - Follow-up 1:**
[Short, new angle]

**Day 7 - Follow-up 2:**
[Different value prop]

**Day 14 - Break-up:**
[Final attempt]
```

---

## Execution Flow

### Step 1: Parse Request

```
Input patterns:
- "draft outreach to John Smith at Acme" → Person + company
- "write cold email to Acme's CTO" → Role + company
- "reach out to sarah@acme.com" → Email provided
- "LinkedIn message to [LinkedIn URL]" → Profile provided
```

### Step 2: Research First (Always)

**Use research-prospect skill internally:**
```
1. Web search for company + person
2. If Enrichment connected: Get verified contact info, background
3. If CRM connected: Check for prior relationship
```

**Must find before drafting:**
- Who they are (title, background)
- What the company does
- Recent news or trigger
- Personalization hook

### Step 3: Identify Hook

```
Priority order for hooks:
1. Trigger event (funding, hiring, news) → Most timely
2. Mutual connection → Social proof
3. Their content (post, article, talk) → Shows you did research
4. Company initiative → Relevant to their priorities
5. Role-based pain point → Least personal but still relevant
```

### Step 4: Draft Message

**Email Structure (AIDA):**
```
SUBJECT: [Personalized, <50 chars, no spam words]

[Opening: Personal hook - shows you researched them]

[Interest: Their problem/opportunity in 1-2 sentences]

[Desire: Brief proof point - similar company result]

[Action: Clear, low-friction CTA]

[Signature]
```

**LinkedIn Connection Request (<300 chars):**
```
Hi [Name], [Mutual connection/shared interest/genuine compliment].
Would love to connect. [No pitch]
```

**LinkedIn Follow-up Message:**
```
Thanks for connecting! [Value-first: insight, article, observation]

[Soft transition to why you reached out]

[Question, not pitch]
```

### Step 5: Create Email Draft

```
If email connector available:
1. Create draft with to, subject, body
2. Return draft link
3. Note: "Draft created - review and send"

If not available:
1. Output email text
2. Note: "Copy to your email client"
```

---

## Capability by Connector

| Capability | Web Only | + Enrichment | + CRM | + Email |
|------------|----------|--------------|-------|---------|
| Personalized opening | Basic | Deep | With history | Same |
| Verified email | No | Yes | Yes | Yes |
| Background details | Public only | Full | Full | Full |
| Prior relationship | No | No | Yes | Yes |
| Auto-create draft | No | No | No | Yes |

---

## Message Templates by Scenario

### Cold Outreach (No Prior Relationship)

```
Subject: [Their initiative] + [your angle]

Hi [Name],

[Personal hook based on research - news, content, mutual connection].

[1 sentence on their likely challenge based on role/company].

[Brief proof: "We helped [Similar Company] achieve [Result]".]

Worth a 15-min call to see if relevant?

[Signature]
```

### Warm Outreach (Have Met / Mutual Connection)

```
Subject: Following up from [context]

Hi [Name],

[Reference to how you know them / who connected you].

[Why reaching out now - their trigger].

[Specific value you can offer].

[CTA]
```

### Re-Engagement (Went Dark)

```
Subject: [Short, curiosity-driven]

Hi [Name],

[Acknowledge time passed without being guilt-trippy].

[New reason to reconnect - their news or your news].

[Simple question to re-open dialogue].

[Signature]
```

### Post-Event Follow-up

```
Subject: Great meeting you at [Event]

Hi [Name],

[Specific memory from conversation].

[Value-add: article, intro, resource related to what you discussed].

[Soft CTA for next conversation].
```

---

## Email Style Guidelines

1. **Be concise but informative** — Get to the point quickly. Busy people skim.
2. **No markdown formatting** — Never use asterisks, bold (**text**), or other markdown. Write plain text that looks natural in any email client.
3. **Short paragraphs** — 2-3 sentences max per paragraph. White space is your friend.
4. **Simple lists** — If listing items, use plain dashes. No fancy formatting.

**Good:**
```
Here's what I can share:
- Case study from a similar company
- 15-min intro call this week
- Quick demo if helpful
```

**Bad:**
```
**What I Can Offer:**
- **Case study** from a similar company
- **Intro call** this week
```

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

## Company Configuration [CUSTOMIZE]

```markdown
## Outreach Settings

- My name: [Your Name]
- My title: [Your Title]
- My company: [Company Name]
- Value prop: [One sentence - what you help with]

## Signature
[Your preferred email signature]

## Proof Points
- [Customer 1]: [Result]
- [Customer 2]: [Result]
- [Customer 3]: [Result]

## CTA Options
- Default: "Worth a 15-min call?"
- Softer: "Open to learning more?"
- Specific: "Can I send over a quick demo?"

## Tone
- [Professional / Casual / Direct]
- Industry-specific language: [Yes/No]
```

---

## Example

**Input:** "draft outreach to the Head of Engineering at Example Co"

**Research finds:**
- Name: Example Person
- Recent news: Notion launched AI features
- Hiring: 5 ML engineer roles open
- Background: Ex-Facebook, Stanford CS

**Output:**

```markdown
# Outreach Draft: Example Person @ Notion

## Research Summary
**Target:** Example Person, Head of Engineering at Example Co
**Hook:** They're scaling AI features and hiring ML talent
**Goal:** Intro call about AI infrastructure

---

## Email Draft

**To:** example@example.com
**Subject:** Notion's AI scaling + a thought

---

Hi David,

Saw Notion's AI rollout is gaining serious traction - congrats.
With 5 ML roles open, seems like you're scaling fast.

Curious how you're thinking about inference infrastructure
as usage grows. We helped [Similar Company] cut their AI
serving costs 40% while improving latency.

Worth a 15-min call to see if relevant to your roadmap?

Best,
[Name]

---

**Subject Alternatives:**
1. Notion AI + scaling question
2. Quick thought on Notion's ML hiring

---

## Email Draft Status
Draft created - check email
```

---

# RU B2B Cold Outreach (NEW — русский рынок, Your Name)

> Порт `cold-email` под российский B2B. Цель — холодные касания к корп-ЛПР за **AI-воркшоп / AI-консалтинг / B2B-когорту ExampleProduct**. Кому: HR-директора и руководители L&D, гендиры/владельцы, руководители отделов. Главный CTA — **бесплатная диагностика AI-зрелости команды / бесплатная консультация** (бронь Zoom). Принцип тот же: **сначала research, потом draft**. Голос — равный коллега-эксперт (руководитель ИИ-направления, экс-крупный банк N+ специалистов), не вендор; по-русски, без канцелярита и хайпа.

## Перед написанием

1. Прочитай контекст продукта из своего навыка-контекста (в паке не поставляется — заведи собственный): персоны, боли, дифференциаторы; офферы (воркшоп/консалтинг/academy B2B, CTA = бесплатная консультация); воронка и CRM (`yourname-sales-postgres`, handoff_to_user, дыры воронки).
2. Собери сигналы по компании/ЛПР — делегируй скиллу `lead-research` (RU-источники: Контур.Фокус, Rusprofile, СПАРК, HH, сайт). Не выдумывай факты.
3. Определи: кому пишешь (роль из персон), что хочешь (цель касания → консультация/воркшоп), value под его роль, пруф (руководитель ИИ-направления / ClientCorp3 N+ / academy N+ материалов / корп-кейс), сигнал «почему сейчас».

Хватает сильного сигнала + ясного value — пиши. Не блокируйся на отсутствии полей, отметь что усилило бы письмо.

## Принципы (RU)

- **Пиши как равный эксперт, не как продавец.** Прочитай вслух. Звучит как реклама — переписывай. На «вы», но по-человечески. YourFirstName — практик (руководитель ИИ-направления, экс-крупный банк N+ специалистов), а не инфоцыган.
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
| Контакты/история сделки, запись касания | API твоей CRM (Битрикс24/amoCRM/HubSpot) + academy CRM `yourname-sales-postgres` |
| Контент для ТГ | свой пайплайн постинга (в паке не поставляется) |

После касания — **зафиксируй активность в CRM**: контакт, канал, дата, реакция. Записывай в свою CRM (в Битрикс24 это метод `crm.activity.add`) и/или в academy-CRM `yourname-sales-postgres` (стадии new→interested→qualified→zoom_scheduled). Горячий enterprise эскалируется через `handoff_to_user`. Это вход в воронку (см. `revops-ru`).

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
- [ ] Факты (соцпруф: руководитель ИИ-направления / ClientCorp3 N+ / academy N+ / корп-кейсы) сверены с `business.md`, не выдуманы?
- [ ] Касание записано в CRM (твоя CRM / `yourname-sales-postgres`)?
