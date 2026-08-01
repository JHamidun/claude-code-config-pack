<!-- LEGACY: полное тело скилла 'onboarding-ux' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: onboarding-ux
description: Паттерны первого запуска — welcome screens, permissions request, empty states которые учат, progressive disclosure, time-to-value. Чтобы юзер прошёл первые 5 минут и не отвалился.
when_to_use: Прототипишь mobile app или web app где юзер впервые открывает интерфейс. Перед interactive-prototype если юзер прошёл регистрацию.
---

# Onboarding UX

Первые 5 минут юзера решают всё. 60% mobile users удаляют app в первый день. Onboarding — главное оружие против churn.

## 4 типа онбординга

| Тип | Когда | Пример |
|---|---|---|
| **Tour** (тур) | Простой UI, пара ключевых фич | Slack: 3 экрана с описанием панели |
| **Setup wizard** | Нужны данные от юзера до старта | Notion: workspace name, team size |
| **Sample data** | Сразу показать ценность | Linear: импорт примера задач |
| **Doing** | Учим делая, а не объясняя | Duolingo: первый урок без объяснения |

**Правило:** «Doing» бьёт «Tour» в 4 раза по retention. Только если нельзя — тогда tour.

## Структура экранов

### Минимальный onboarding
```
1. Welcome (логотип + value prop)
2. Personal info (имя, цель)
3. Permissions (notifications, camera, location)
4. First action (создать проект / урок / задачу)
5. Done!
```

4-5 экранов max. Каждый дополнительный = -10% completion.

### Анти-минимальный
```
❌ 12 экранов с tooltips
❌ Видео на 2 минуты «как пользоваться»
❌ Tutorial который нельзя skip
```

## Permissions — когда просить

| Permission | Когда просить |
|---|---|
| Notifications | После первой ценности (после 1-го действия), а не на старте |
| Camera | Когда юзер тапает на «Add photo» — контекстуально |
| Location | Когда нужна (на screen «Find nearby») |
| Contacts | Когда юзер хочет invite — не раньше |
| Microphone | Когда тапает на mic-icon |

**Никогда** не запрашивай permissions wall при старте. Iconic anti-pattern.

## Time-to-value (TTV)

Сколько времени от «открыл app» до «увидел ценность»? Меряй и оптимизируй.

| App type | Хороший TTV |
|---|---|
| Social | < 30 сек (увидел feed) |
| SaaS tool | < 2 мин (создал первый artifact) |
| Game | < 1 мин (первое действие) |
| Edtech | < 5 мин (первый урок) |
| Health | < 30 сек (первый трекинг) |

Для дашборда / админки: **показывай sample data** до того как юзер залил свои. Иначе пустой UI = «не понимаю ценности».

## Progressive disclosure

Не показывай 200 настроек сразу. Открывай по мере необходимости.

```
Старт: 3 настройки visible (что критично знать)
↓
После 1-го использования: показываем 2 advanced
↓
В Settings: ещё 8 для power users
↓
В Developer mode: ещё 12
```

**Hide** не значит **delete** — просто defer.

## Empty states которые учат

Empty state — последний шанс onboard'нуть. Используй:

```
[Иллюстрация]
Заголовок: «Здесь будут ваши проекты»
Текст: «Создайте первый — это займёт минуту»
[+ Создать проект]
[или Загрузить из Figma]

Бонус: 3 sample-проекта чтобы посмотреть пример
```

### Sample data
- Покажи 3-5 sample-карточек/строк
- Помечены: «📌 Пример. Удалить можно в любой момент»
- Юзер видит как выглядит populated UI и что туда положить

## Specific onboarding patterns

### 1. Welcome screen
```jsx
<div style={{ padding: 48, textAlign: 'center' }}>
  <Logo size={64} />
  <h1>Добро пожаловать</h1>
  <p>Один-два предложения про что это и зачем юзеру.</p>
  <Button>Начать</Button>
  <a>Уже есть аккаунт? Войти</a>
</div>
```

### 2. Goal selection
Спроси цель — настрой UI.
```
Зачем вы здесь?
☐ Учиться чему-то новому
☐ Решить конкретную задачу
☐ Просто посмотреть
```

### 3. Setup wizard (multi-step)
```
Step 1 / 4: Workspace name
Step 2 / 4: Команда (size, roles)
Step 3 / 4: Импорт данных (skip or...)
Step 4 / 4: Notifications
```

Прогресс-индикатор всегда! Юзер должен видеть «где я» и «сколько осталось».

### 4. Completion screen
```
🎉 Готово!
Что вы достигли:
- ✓ Создали аккаунт
- ✓ Настроили workspace
- ✓ Загрузили 5 проектов

Дальше: [Создать первый проект]
```

## Skip vs обязательное

| Можно skip | Обязательно |
|---|---|
| Tutorial | Email + password |
| Permissions | Возрастной gate (если требуется) |
| Welcome tour | TOS / privacy policy |
| Sample data | Stripe Connect для marketplace |
| Onboarding survey | KYC для финансов |

**Если можно skip — давай skip явный, не «X в углу».**

## Antipattern: «You must complete this»

Когда форма не даёт перейти дальше пока юзер не заполнил все поля. Только если правда обязательно. Иначе → 30% drop-off.

## Метрики (для тех кто меряет)

- **Activation rate** — % юзеров прошедших onboarding до конца
- **TTV** — median time to first value action
- **Day-1 retention** — % вернувшихся на следующий день
- **Funnel drop-off** — где именно теряем юзеров

## Антипаттерны

- Видео-туториал > 60 сек → никто не смотрит
- Forced sign-up до показа value → 70% drop
- Permissions всё сразу → 80% deny
- Tooltip-tour > 7 шагов → юзер забывает первые
- Пустой dashboard без sample data → юзер не понимает ценности
- Skip спрятан в углу → выглядит как dark pattern
- Onboarding для returning users → раздражает существующих юзеров
- Слова «Welcome» / «Get started» как hero → клише, не отличает от 1000 других apps
