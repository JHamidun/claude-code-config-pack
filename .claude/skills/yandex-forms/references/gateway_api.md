# Yandex Forms — внутренний gateway API (реверс)

Endpoint: `POST https://forms.yandex.ru/admin/gateway/root/form/<МЕТОД>`

Заголовки (обязательны):
```
content-type: application/json
x-csrf-token: <window.__DATA__.csrfToken>   // берётся на любой странице /admin/
x-sdk: 1
x-use-collab: 1
```
Аутентификация: `credentials: 'include'` (cookies залогиненного Яндекс-аккаунта).
Статического API-ключа нет — нужен живой вход в браузере (chrome-devtools MCP).

## Методы (проверены)
| Метод | Назначение | Тело | Ответ |
|---|---|---|---|
| `createFormFromTemplate` | создать пустую форму | `{templateId:'empty_form_v2'}` | `{id}` (surveyId) |
| `getSurveyData` | данные формы (name, isPublished, …) | `{surveyId}` | объект формы |
| `updateSurveyData` | сменить имя/настройки | `{surveyId, survey:<полный объект getSurveyData с изменённым name>}` | 200. ⚠️ оборачивать в `survey:`, НЕ `data:` (иначе 500) |
| `surveyQuestionsLA` | вопросы+страницы | `{surveyId}` | `{nodes, deletedPages, questionsMap}` |
| `addPage` | добавить страницу | `{surveyId}` | `{id}` (pageId) |
| `addSurveyQuestion` | добавить вопрос | `{surveyId, page:<pageId>, position:<int>, question:<см.ниже>}` | 200 + созданный вопрос |
| `updateSurveyQuestion` | изменить вопрос | `{surveyId, question:<полный объект>}` | 200 (но `view` коэрсится — менять тип лучше пересозданием) |
| `deleteSurveyQuestion` | удалить вопрос | `{surveyId, questionId}` | 200 |
| `publishSurvey` | опубликовать | `{surveyId}` | 200 |
| `deleteSurvey` | удалить форму | `{surveyId}` | 200 |

Неизвестный метод → HTTP 404 (UNKNOWN_SERVICE_ACTION). Существующий с плохим телом → 400/500.

## Создание формы: последовательность
1. `createFormFromTemplate {templateId:'empty_form_v2'}` → `id`
2. `getSurveyData {surveyId:id}` → `sd`; `sd.name = 'Заголовок'`; `updateSurveyData {surveyId:id, survey:sd}`
3. `surveyQuestionsLA {surveyId:id}` → найти `nodes.find(n=>n.type==='page').id` = `pageId`
   (в шаблоне уже есть 1 страница — добавляй вопросы в неё, НЕ создавай вторую через addPage)
4. для каждого вопроса: `addSurveyQuestion {surveyId:id, page:pageId, position:i, question}`
5. `publishSurvey {surveyId:id}`
6. Ссылка для заполнения: `https://forms.yandex.ru/u/<id>/`
   Редактор: `https://forms.yandex.ru/admin/<id>/edit`

## Схема объекта `question`
Общие поля: `id` (int, уникальный), `key` (string с префиксом по типу), `type`, `view`,
`title` (строка; перенос строки `\n` для подсказки/подписи шкалы), `required` (bool).

| Тип вопроса | type | view | widget | префикс key | options |
|---|---|---|---|---|---|
| Блок-заголовок (display) | `text` | `textinput` | — | `statement_` | — |
| Короткий текст | `text` | `textinput` | — | `answer_short_text_` | — |
| Абзац (длинный текст) | `text` | `textarea` | — | `answer_long_text_` | — |
| Один вариант (radio) | `choices` | `radio` | `radio` | `answer_choices_` | да |
| **Несколько вариантов** | `choices` | **`checks`** | `checkbox` | `answer_choices_` | да |
| Выпадающий список | `choices` | `select` | `select` | `answer_choices_` | да |
| Шкала 1–5 | `choices` | `radio` | `radio` | `answer_choices_` | опции '1'..'5' |

`options`: массив `{id:<int>, text:<string>, key:<числовая строка, без префикса>, hidden:false}`.
Доп. поле у choices: `sort:'natural'`.

### ⚠️ Критичные грабли
1. **Несколько вариантов = `view:'checks'`** (именно "checks", не "checkbox"). При `'checkbox'`
   сервер молча создаёт `radio`. Обнаружено реверсом UI: тип «Несколько вариантов» в
   конструкторе сохраняет `view:"checks", widget:"checkbox"`.
2. **Заголовок-секция** отличается от короткого текста ТОЛЬКО префиксом ключа `statement_`.
   Тип/представление одинаковые (`text`/`textinput`). Префикс делает поле display-only.
3. `addSurveyQuestion` всегда создаёт `radio` для choices независимо от переданного `view`,
   КРОМЕ случая `view:'checks'` (и, предположительно, `'select'`). Менять уже созданный
   radio→checks через `updateSurveyQuestion` не работает (коэрсится обратно) — задавай
   правильный `view` сразу при создании.

## Чтение существующей формы (для копирования формата)
`surveyQuestionsLA {surveyId}` → `questionsMap` (объект ключ→вопрос) + `nodes` (порядок/страницы).
Так был снят эталон формата «ИИ-амбассадоры».

## Типы вопросов в UI-конструкторе (combobox «Тип вопроса»)
«Один вариант» / «Несколько вариантов» / «Выпадающий список» / «Данные из других сервисов».
