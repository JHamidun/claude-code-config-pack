---
name: sms-twilio
description: Отправка SMS через Twilio REST API — одиночные и массовые (bulk с dry-run/джиттером), статус доставки, история сообщений, баланс, номера аккаунта. CLI: python ${WORKSPACE}/tools/sms_client.py. Триггеры: «отправь SMS», «смс», «sms», «twilio», «рассылка по телефонам», «статус доставки смс», «баланс twilio». НЕ для: сообщений в Telegram → tg_client.py/tg-bot-publish; WhatsApp; email-рассылок → gmail/outlook; звонков/телефонии.
---

# SMS via Twilio

CLI-коннектор к Twilio REST API (`https://api.twilio.com/2010-04-01`). Без twilio-SDK — `requests` (стоит) или stdlib urllib fallback. Подключился → сделал → напечатал → вышел.

**Файл:** `${WORKSPACE}/tools/sms_client.py`

## Когда использовать

- Отправить SMS одному получателю или списку (bulk с анти-спам гардами)
- Проверить статус доставки (queued/sent/delivered/failed)
- Посмотреть историю сообщений, баланс, номера аккаунта
- Понять, как принять входящие SMS (webhook-инструкция)

## Установка / настройка

**Креды у владельца ПОКА НЕ ЗАВЕДЕНЫ.** Нужно добавить в `~/.claude/.credentials.master.env` (значения НЕ заполнять здесь — только владелец):

- `TWILIO_ACCOUNT_SID` — начинается с `AC`, Twilio Console → Account Info
- `TWILIO_AUTH_TOKEN` — там же
- `TWILIO_PHONE_NUMBER` — купленный SMS-capable номер в E.164 (`+1555...`)

Без кредов CLI не падает — печатает, что именно добавить (exit 2). Зависимостей ставить не нужно (`requests` уже есть; без него — urllib).

Регистрация: https://console.twilio.com → купить SMS-capable номер (~$1-1.15/мес US).

## Команды

| Команда | Что делает |
|---------|-----------|
| `send <to> <text> [--from +1...] [--json]` | Одно SMS. `to` в E.164. Печатает SID |
| `bulk <file> <text> [--rate 2.0] [--limit 50] [--confirm] [--json]` | Рассылка по файлу (1 номер/строка, `#`=коммент). **По умолчанию DRY-RUN**; реальная отправка только с `--confirm`. Джиттер `rate + 0..50%`, cap `--limit` (деф. 50), дедуп номеров |
| `status <sid> [--json]` | Статус доставки по Message SID (SM…) + error_code если fail |
| `list [--limit 20] [--to +...] [--from +...] [--json]` | Последние сообщения (входящие+исходящие) с ценой |
| `balance [--json]` | Баланс аккаунта |
| `numbers [--json]` | Номера аккаунта с capabilities (sms/voice/mms) |
| `receive-webhook` | Инструкция как поднять приём входящих (сервер НЕ стартует) |

## Примеры

```bash
# одно SMS (from = TWILIO_PHONE_NUMBER)
python ${WORKSPACE}/tools/sms_client.py send +55 XX XXXXX-XXXX "Тест"

# рассылка: сначала dry-run (дефолт), потом реальная
python ${WORKSPACE}/tools/sms_client.py bulk numbers.txt "Текст всем"
python ${WORKSPACE}/tools/sms_client.py bulk numbers.txt "Текст всем" --confirm --rate 3

# статус и история
python ${WORKSPACE}/tools/sms_client.py status SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
python ${WORKSPACE}/tools/sms_client.py list --limit 10 --json
```

## Стоимость и согласие получателей

- **Оплата за сегмент**: GSM-7 — 160 симв./сегмент, **кириллица = UCS-2 — 70 симв./сегмент**. Русский текст в 3 раза «дороже на символ». Ориентиры: US ~$0.0083, ваш регион ~$0.03-0.06, РФ дороже и часто фильтруется операторами (точные цены — twilio.com/sms/pricing, меняются).
- **Trial-аккаунт**: слать можно ТОЛЬКО на verified-номера (ошибка 21608), к тексту добавляется префикс «Sent from your Twilio trial account».
- **Согласие (opt-in) обязательно**: слать только тем, кто дал согласие на SMS; включать способ отписки (STOP). Массовый спам = блок аккаунта Twilio + нарушение TCPA (США)/LGPD (ваш регион)/152-ФЗ (РФ). A2P 10DLC-регистрация нужна для массовых отправок на US-номера.
- Бразильские/российские мобильные принимают SMS с международных номеров нестабильно (операторские фильтры) — «требует проверки» на реальном номере.

## Гочи

- Номера ТОЛЬКО в E.164 (`+<код страны><номер>`, напр. `+15551234567`) — без плюса Twilio вернёт 21211.
- `bulk` без `--confirm` = всегда dry-run; это фича, не баг. Cap 50 получателей — поднимать `--limit` осознанно.
- Error 21608 = trial + неверифицированный получатель; 21606 = From-номер не SMS-capable.
- `status` сразу после `send` часто показывает `queued`/`sent` — `delivered` приходит через секунды-минуты, перепроверить позже.
- Кириллица режет лимит сегмента до 70 симв. — длинный русский текст = много сегментов = дороже.
- Приём входящих требует публичный HTTPS-webhook + валидацию `X-Twilio-Signature` (HMAC-SHA1) — готовый адаптер есть в Hermes gateway (sms.py), не писать новый сервер.
- Endpoints `Balance.json` и `IncomingPhoneNumbers.json` — стандартные Twilio 2010-04-01; живой ответ на реальном аккаунте пока не проверялся (кредов нет) — «требует проверки» при первом запуске.

## Чек-лист

- [ ] Креды в `~/.claude/.credentials.master.env` (3 переменные выше)
- [ ] `numbers` — убедиться что есть SMS-capable номер
- [ ] `balance` — хватает ли денег
- [ ] Для bulk: список = только opt-in получатели, есть STOP-механика
- [ ] Bulk: сначала dry-run, глазами проверить список, потом `--confirm`
- [ ] После отправки: `status <sid>` → дождаться `delivered`
