# Workflow: Intro (Знакомство)

> Познакомить двух людей или представить себя кому-то

## Keywords
`intro`, `познакомить`, `представить`, `connect`, `introduction`

## Inputs
- **task**: описание задачи из Todoist
- **person_a**: кого знакомим (или себя)
- **person_b**: с кем знакомим
- **context**: почему это знакомство нужно

## Steps

### 1. Research Both Parties (Parallel)
```
Tool: Perplexity AI или LinkedIn scraping
Output: Background на обоих людей
- Current role, company
- Recent achievements
- Shared interests/connections
- Communication style preference
```

### 2. Find Connection Points
```
Tool: AI Analysis
Output: 2-3 точки соприкосновения
- Common interests
- Mutual benefit
- Shared contacts
```

### 3. Draft Introduction Message
```
Tool: AI Text Generation
Template:

Subject: [Person A] <> [Person B] - [Reason]

Hi [Person B],

Wanted to introduce you to [Person A] - [brief description].

[Why they should connect - 1-2 sentences]

[Person A], meet [Person B] - [brief description].

[Specific suggestion for next step]

Best,
[Name]
```

### 4. Send Message
```
Tool: Email/Telegram/LinkedIn depending on context
- Check preferred channel for both parties
- Send via appropriate platform
```

### 5. Track & Follow Up
```
Tool: Todoist
- Create follow-up task in 3-5 days
- Add note about intro sent
```

## Quality Checks
- [ ] Research на обоих сторон завершён
- [ ] Точки соприкосновения найдены и релевантны
- [ ] Сообщение персонализировано (не generic)
- [ ] Правильный канал коммуникации выбран
- [ ] Follow-up запланирован

## Completion Criteria
- Intro сообщение отправлено
- Follow-up task создан в Todoist
- Context сохранён в Memory для будущих взаимодействий

## Time Estimate
- **Typical**: 10-15 minutes
- **Max**: 30 minutes (если нужен deep research)

## Examples

### Simple Intro
**Task**: "Познакомить Васю с Петей по поводу инвестиций"
**Output**: Персонализированное письмо + follow-up через 5 дней

### Self-Introduction
**Task**: "Написать intro CEO Acme Corp"
**Output**: Cold intro email + research file + follow-up

## Notes
- Для VIP интро - добавить warm-up через mutual connection
- Если нет mutual connection - использовать cold_outreach workflow вместо этого
- Всегда сохранять context в Memory для future reference
