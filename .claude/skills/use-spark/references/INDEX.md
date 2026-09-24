# Spark: индекс рецептов и персон

Зеркало раздела из `../SKILL.md` на случай, если `spark skill > SKILL.md` его затрёт.
Ссылки ниже — относительно этой папки.

## Рецепты и персоны (из spark-cli-skills 1.3.0, Readdle)

Справочники, а не отдельные навыки: листинг не растёт. Под задачу открыть нужный файл
целиком и идти по шагам; команды и синтаксис фильтров — в `../SKILL.md`. Первая строка
каждого файла — сводка (имя, версия, уровень доступа). Лицензия MIT, Spark Mail Limited →
`LICENSE-spark-cli-skills` (рядом). Поля `accessLevel` — уровни из Spark → Settings →
AI Agents: ни одному рецепту не нужен `send`.

**✎ — меняет состояние ящика.** Такие рецепты (отписка, чистка, разбор новых отправителей,
архив и перенос, блоки контактов и доменов, выброс черновиков в корзину) сначала показывают
список действий и выполняют его **только после явного «да» владельца** на этот список;
молчание или общее «разбери почту» — не согласие. Ссылки отписки из футеров открывать только
по одобренному списку. **Почту рецепты не отправляют никогда:** отправка в `spark`
есть (`action send`, уровень доступа `send`), но ни одному рецепту она не нужна — рецепты
доходят до `draft`, отправляет владелец (в Spark или отдельным «отправь» на конкретное письмо). Персоны смешивают чтение, черновики
и действия — те же правила.

Рецепты:

| Файл | Доступ | Что делает |
|---|---|---|
| [calendar-audit](recipes/recipe-calendar-audit.md) | read-only | нагрузка встречами за период: часы, пиковые дни, встречи подряд, свободные окна |
| [delegate-and-track](recipes/recipe-delegate-and-track.md) | triage ✎ | назначить письма коллегам с контекстом и следить за статусом делегирования |
| [draft-batch](recipes/recipe-draft-batch.md) | triage ✎ | разобрать пачку черновиков: дописать, оставить или выбросить в корзину |
| [end-of-day](recipes/recipe-end-of-day.md) | read-only | итог дня: хвосты, закреплённое, календарь на завтра |
| [inbox-by-category](recipes/recipe-inbox-by-category.md) | read-only | входящие по умным категориям: priority → люди → приглашения → уведомления → рассылки |
| [inbox-zero](recipes/recipe-inbox-zero.md) | triage ✎ | входящие до нуля: по категориям, потом архив, перенос, done, snooze |
| [invitation-manager](recipes/recipe-invitation-manager.md) | read-only | приглашения в календарь: сверка занятости и список решений с рекомендацией |
| [label-organize](recipes/recipe-label-organize.md) | triage ✎ | метки и папки: навесить, снять ошибочные, перенести не туда положенное |
| [meeting-followup](recipes/recipe-meeting-followup.md) | triage, черновики | по расшифровке встречи — черновики писем участникам с action items |
| [meeting-prep](recipes/recipe-meeting-prep.md) | read-only | подготовка к встрече: повестка, контекст из писем, участники, открытые треды |
| [morning-standup](recipes/recipe-morning-standup.md) | read-only | утренний брифинг: события дня, непрочитанное от людей и priority, назначения команды |
| [multi-account-review](recipes/recipe-multi-account-review.md) | read-only | сводка по нескольким ящикам и общие приоритеты |
| [new-sender-review](recipes/recipe-new-sender-review.md) | triage ✎ | очередь GateKeeper: принять своих отправителей, заблокировать лишних |
| [newsletter-cleanup](recipes/recipe-newsletter-cleanup.md) | triage ✎ | рассылки: блок, отписка, AI-саммари для тех, что оставляем |
| [notification-hygiene](recipes/recipe-notification-hygiene.md) | triage ✎ | шумные уведомления: переклассифицировать, сгруппировать, массово архивировать |
| [priority-tuning](recipes/recipe-priority-tuning.md) | triage ✎ | настройка категории Priority: ключевые контакты в primary/important |
| [schedule-meeting](recipes/recipe-schedule-meeting.md) | read-only | общие свободные слоты участников и варианты времени |
| [shared-inbox-status](recipes/recipe-shared-inbox-status.md) | read-only | здоровье общего ящика: open/done, без исполнителя, нагрузка по людям |
| [shared-inbox-triage](recipes/recipe-shared-inbox-triage.md) | triage ✎ | разбор общего ящика: назначить, ответить черновиком, закрыть |
| [stakeholder-brief](recipes/recipe-stakeholder-brief.md) | read-only | досье на человека: все встречи и переписка с ним в одну справку |
| [team-workload](recipes/recipe-team-workload.md) | read-only | распределение назначений в команде: перекосы и неназначенное |
| [topic-timeline](recipes/recipe-topic-timeline.md) | read-only | хронология темы: выдержки расшифровок встреч вперемешку с саммари тредов |
| [unsubscribe-audit](recipes/recipe-unsubscribe-audit.md) | triage ✎ | полный аудит отписок: три пула, вовлечённость, фишинг, дубли; отписка после одобрения списка |
| [vacation-catchup](recipes/recipe-vacation-catchup.md) | triage ✎ | разбор завала после отпуска: массовый архив шума, что требует внимания |
| [weekly-digest](recipes/recipe-weekly-digest.md) | read-only | недельная сводка: встречи, непрочитанное по категориям, статус команды |

Персоны (перекрываются со своими навыками `daily-briefing`, `call-prep`, `promise-tracker`):

| Файл | Доступ | Что делает |
|---|---|---|
| [exec-assistant](personas/persona-exec-assistant.md) | triage | ассистент руководителя: брифинги, черновики ответов, расписание, контакты |
| [founder](personas/persona-founder.md) | triage | основатель/CEO: быстрый триаж, делегирование, надзор за командами |
| [freelancer](personas/persona-freelancer.md) | triage | фрилансер: несколько клиентов, напоминания по счетам, доступность |
| [meeting-manager](personas/persona-meeting-manager.md) | triage | встречи: подготовка, расшифровки, черновики фоллоу-апов, расписание |
| [project-manager](personas/persona-project-manager.md) | triage | проектный менеджер: треды проекта, апдейты стейкхолдерам, action items |
| [sales-rep](personas/persona-sales-rep.md) | triage | продажи и аккаунт-менеджмент: клиенты, пайплайн, ритм фоллоу-апов |
| [support-agent](personas/persona-support-agent.md) | triage | поддержка: общий ящик, назначения, шаблонные ответы, эскалация |
| [team-lead](personas/persona-team-lead.md) | triage | тимлид: нагрузка команды, распределение, подготовка к стендапу |

> Обновление через `spark skill > SKILL.md` затирает этот раздел целиком. Копия —
> `references/INDEX.md`, вернуть оттуда после обновления.
