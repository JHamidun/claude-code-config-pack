<!-- LEGACY: полное тело скилла 'states-checklist' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: states-checklist
description: Чеклист состояний на каждый экран — empty, loading, error, success, disabled, partial-data, no-permission, offline. Не пропускай ни одно. UI без этих состояний — не UI.
when_to_use: Перед финализацией любого interactive-prototype или dashboard. Проверь каждый экран по чеклисту, добавь недостающие состояния как варианты в design-canvas.
---

# States checklist

Любой UI имеет минимум 4 состояния. Большинство дизайнов показывают только «happy path». Это плохо.

## 8 обязательных состояний

| # | Состояние | Пример | Что показать |
|---|---|---|---|
| 1 | **Empty** | Список пустой | Иллюстрация + текст «У вас пока нет X» + CTA «Создать первый» |
| 2 | **Loading** | Грузится данные | Skeleton (см. microinteractions), не спиннер для предсказуемой формы |
| 3 | **Loaded (happy path)** | Всё ОК | Финальный UI |
| 4 | **Error** | API не ответил | Иконка + «Что-то пошло не так» + кнопка «Повторить» |
| 5 | **Partial data** | Часть полей null | Заглушки на null'ах: «—», «не указано» |
| 6 | **No permission** | Юзер не имеет доступа | «У вас нет прав. Запросите у админа» |
| 7 | **Disabled / Read-only** | Subscription expired | Серый UI + tooltip «Купите Pro чтобы редактировать» |
| 8 | **Offline** | Нет сети | Banner вверху «Нет интернета. Покажу cached данные» |

## Чеклист на экран

Пройди по списку: на этом экране **возможно** ли это состояние?

### Dashboard
```
☐ Empty: первый день, ещё ничего нет
☐ Loading: пока грузится из API
☐ Loaded: 5+ карточек метрик
☐ Error: API down
☐ Partial: одна карточка не загрузилась
☐ No-permission: free tier vs pro tier
☐ Offline: показываем последний cached snapshot
```

### Form
```
☐ Empty: пустая форма
☐ Filled: юзер заполнил
☐ Validation error: одно поле не прошло
☐ Submit pending: «Отправляем...» + disabled-кнопка
☐ Submit success: тост / redirect / inline confirmation
☐ Submit error: «Ошибка сервера, попробуйте ещё раз»
☐ Partial: успели сохранить частично, остальное нет
☐ Disabled: read-only режим
```

### List / Table
```
☐ Empty: 0 строк
☐ Loading: skeleton 5 rows
☐ Loaded: реальные данные
☐ Filtered to zero: фильтры применены, ничего не подошло
☐ Pagination loading: грузим следующую страницу
☐ Sorted: визуально отмечена колонка
☐ Selection: одна / несколько строк выделены
☐ Bulk-action: что показать если выделено 100 строк
```

### Modal / Form-step
```
☐ Empty: открыли, ещё ничего не нажали
☐ Filling: процесс заполнения
☐ Validating: «Проверяем...»
☐ Success: подтверждение
☐ Error: что не так
☐ Closing animation: убрать backdrop плавно
```

## Empty state design

Empty — самое забываемое. И самое важное (это ПЕРВОЕ что видит новый юзер).

### Хороший empty
```
[Иллюстрация]
Заголовок: «У вас пока нет проектов»
Текст: «Создайте первый — это займёт минуту»
CTA: [+ Создать проект]
Доп ссылка: «Или импортируйте из Figma»
```

### Плохой empty
- Просто пустой div → юзер думает что баг
- «No data» без CTA → юзер не знает что делать
- Та же иконка как для error → путаешь сигналы

## Error state design

Error — второе самое забываемое.

### Хороший error
```
[⚠ иконка]
Заголовок: «Не получилось загрузить»
Текст: «Сервер не отвечает. Это временно.»
CTA: [Повторить] [Связаться с поддержкой]
Технический details: <small>error code: NETWORK_TIMEOUT</small>
```

### Плохой error
- Просто красный текст «Error» → не понятно что делать
- «Internal Server Error 500» → юзер не разработчик
- Нет CTA «Повторить» → юзер думает что навсегда сломалось

## Loading state — когда что показывать

| Длительность | Что показать |
|---|---|
| < 200ms | Ничего, просто перерисовать |
| 200ms - 1s | Spinner (если форма не предсказуема) или Skeleton (если контент known shape) |
| 1s - 3s | Skeleton + progress bar (если знаешь %) |
| 3s - 10s | Progress bar + текст «Это займёт пару минут...» |
| > 10s | Email-when-ready: «Покажу когда будет готово» (не блокировать UI) |

## Disabled vs read-only vs locked

| | Когда | Как выглядит |
|---|---|---|
| Disabled | Нельзя нажать сейчас (нет данных, нет прав) | grey, не кликается, tooltip почему |
| Read-only | Можно видеть, не редактировать | normal contrast, без edit affordances |
| Locked (paywall) | Нужна подписка | overlay 🔒 + «Pro feature», CTA «Купить» |

Не путай. Читается по-разному.

## Куда сложить варианты состояний

Через `design-canvas` — каждое состояние отдельным артбордом:
```
[A] Dashboard — empty
[B] Dashboard — loading
[C] Dashboard — loaded
[D] Dashboard — error
[E] Dashboard — offline
```

Юзер видит сразу все, выбирает что отрисовывать в финальном prototype.

## Антипаттерны

- Только happy path → дизайн ломается на проде в 30% сценариев
- Empty без CTA → юзер не понимает что делать
- Error без retry → юзер уходит навсегда
- Disabled без объяснения → юзер думает что баг
- Loading > 3 сек без progress → юзер думает что зависло
- Использовать одну иконку (😢) для всех негативных состояний → сигналы смешаны
- Partial data без обработки null → видны JavaScript-ошибки
