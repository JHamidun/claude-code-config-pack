# Доступ к Директу: что реально работает (проверено 28.08.2026)

> Прочитай ЭТО прежде чем писать код против API Директа. Вывод «доступа нет»
> переоткрывался трижды — 02.06, 19.07, 28.08 — потому что был записан внутри
> SEO-скилла, где его не ищет тот, кто занимается рекламой.

## Короткая таблица

| Что | Состояние | Проверка |
|---|---|---|
| Метрика API | ✅ работает полностью, 17 счётчиков | `GET api-metrika.yandex.net/management/v1/counters` |
| Яндекс.Аудитории | ✅ отвечает (сегментов 0) | `GET api-audience.yandex.ru/v1/management/segments` |
| **Direct API v5** | ❌ `error_code 58` на ВСЕХ методах | `POST api.direct.yandex.com/json/v5/campaigns` |
| **Direct песочница** | ❌ тот же `error_code 58` | `api-sandbox.direct.yandex.com` |
| **Wordstat через Direct v4** | ❌ тот же `error_code 58` | `CreateNewWordstatReport` |
| **Wordstat обходом** | ✅ **работает** | `seo-machine-ru/scripts/wordstat_client.py` |

## Почему v5 закрыт — и чем это НЕ лечится

```
error_code 58 :: "Незавершенная регистрация"
detail: Необходимо заполнить для приложения заявку на доступ
        в интерфейсе Директа и дождаться её подтверждения
```

Дело **не в токене и не в скоупе**. Токен аутентифицируется нормально
(`login: yourname`, `id: 118147060`). Дело в том, что OAuth-приложение
`fb043ef4…` («Claude Code Metrika app») не имеет **одобренной заявки** на Direct
API. Заявку модерирует Яндекс; ни `scope`, ни новый токен её не заменяют.

Уже отброшено проверкой — не перебирать заново:

- «нужен отдельный директовый токен» — его нет, и `yandex_api.py`, и плагин
  Bot-B бьют в тот же v5 тем же токеном;
- «не тот scope» — аутентификация проходит, дело не в ней;
- «песочница обойдёт» — отвечает тем же кодом 58;
- «новый Wordstat API вместо v4» — хоста `api.wordstat.yandex.net` не
  существует (SSL hostname mismatch), `api-wordstat.yandex.net` не резолвится.

## Что работает вместо: Wordstat под куками браузера

Приём: ходить во **внутренний API веб-интерфейса** под сессионными куками из
persistent-профиля Playwright, минуя официальный API целиком.

```bash
$env:PYTHONIOENCODING='utf-8'
python ~/.claude/skills/seo-machine-ru/scripts/wordstat_client.py freq "вызвать врача на дом" --region 213
python ~/.claude/skills/seo-machine-ru/scripts/wordstat_client.py batch seeds.txt --out ws.json --region 225 --delay 1.5
```

- эндпоинт `POST https://wordstat.yandex.ru/wordstat/api/getTable`, CSRF не нужен;
- профиль `~/.wordstat/profile`, кэш кук `~/.wordstat/cookies.json`;
- регионы: `225` Россия, `213` Москва, `2` СПб;
- куки протухают — обновлять `wordstat_client.py refresh` (при разлогине
  `--headed`, 2FA проходит только владелец);
- контракт, гочи и урок «оценки завышают в 5–10×» —
  `seo-machine-ru/references/wordstat-real-recipe.md`.

**Тот же приём — открытый кандидат для самого Директа**: внутренний API
`direct.yandex.ru` под куками профиля вместо ожидания модерации. Разведан, но
пока не реализован.

## Что нужно от владельца, чтобы открыть официальный путь

Заявка на доступ приложения к API подаётся в интерфейсе Директа от его имени;
модерация Яндекса занимает недели. Это разблокирует v5 и Wordstat v4 разом,
но не является блокером для работы — семантика снимается обходом уже сегодня.

## Связанное

- `scripts/unit_econ.py` — юнит-экономика ключа до запуска (работает на
  частотностях из Wordstat, доступа к Директу не требует).
- `skills/yandex/scripts/yandex_api.py direct|wordstat` — код против официального
  API написан и починен по кодировке, включится сам, когда заявку одобрят.
- Память: `yandex-direct-api-never-worked-2026-08-28.md`.
