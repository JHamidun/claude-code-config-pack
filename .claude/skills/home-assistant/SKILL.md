---
name: home-assistant
description: "Home Assistant CLI — управление умным домом через REST + WebSocket API: состояния сущностей, вызов сервисов (свет/климат/медиа), on/off/toggle, история состояний, live-поток событий, конфиг, areas/devices. Триггеры: «home assistant», «HA», «hass», «включи/выключи свет через HA», «состояние датчика», «entity_id», «вызови сервис HA», «события умного дома», «history сенсора». НЕ для: Яндекс умный дом / Алиса / устройства из Яндекс-экосистемы → skill yandex (секция IoT); генерация ботов для HA → agent-builder tooling."
---

# Home Assistant CLI

Коннектор к Home Assistant: подключился → сделал → напечатал → вышел.
CLI: `python ${WORKSPACE}/tools/ha_client.py <command>`.

## Когда использовать

- Прочитать/изменить состояние устройств в Home Assistant (свет, розетки, климат, сенсоры).
- Вызвать любой HA-сервис (`light.turn_on`, `climate.set_temperature`, `media_player.play_media`...).
- Посмотреть историю состояний сенсора, live-поток событий, конфиг инстанса, комнаты/устройства.

### HA vs Яндекс умный дом (skill `yandex`)

| Критерий | Home Assistant (этот skill) | Яндекс IoT (skill yandex) |
|----------|------------------------------|---------------------------|
| Где живёт | Локально (свой сервер/RPi/Docker), работает без интернета | Облако Яндекса |
| Устройства | 2000+ интеграций: Zigbee, Z-Wave, MQTT, ESPHome, Xiaomi, и Яндекс-устройства тоже подключаемы | Только устройства, привязанные к аккаунту Яндекса |
| Автоматизации | Полноценные (triggers/conditions/scripts), история, дашборды | Сценарии Алисы, проще |
| Голос | Опционально (в т.ч. проброс в Алису) | Алиса нативно |
| Когда брать | Нужен локальный контроль, не-Яндекс устройства, history/events, сложные автоматизации | Устройства уже в Яндекс-экосистеме и нужен быстрый доступ/Алиса |

У владельца сейчас есть Яндекс умный дом; HA-инстанса **пока нет** — CLI при отсутствии кредов сам печатает, что настроить.

## Установка / настройка

1. Нужен работающий HA-инстанс (Home Assistant OS на RPi/mini-PC или Docker:
   `docker run -d --name homeassistant --network=host ghcr.io/home-assistant/home-assistant:stable`).
2. Токен: HA web UI → профиль (слева внизу) → вкладка Security → Long-lived access tokens → Create Token.
3. Env-переменные в `~/.claude/.credentials.master.env` (значения заполняет владелец):
   - `HA_URL` — базовый URL, например `http://homeassistant.local:8123` или `http://192.168.x.x:8123`
   - `HA_TOKEN` — long-lived access token
4. Зависимости: `requests` (REST), `websockets` (events/areas/devices) — обе уже установлены локально (websockets 15.0.1).

## Команды

| Команда | Что делает | API |
|---------|-----------|-----|
| `ping` | Жив ли API | `GET /api/` |
| `states [--domain light]` | Все состояния, фильтр по домену | `GET /api/states` |
| `get <entity_id>` | Одна сущность + атрибуты | `GET /api/states/<id>` |
| `call <domain> <service> [--entity id] [--data '{...}']` | Любой сервис | `POST /api/services/<d>/<s>` |
| `on <entity_id>` / `off <entity_id>` / `toggle <entity_id>` | Быстрые шорткаты | `homeassistant.turn_on/turn_off/toggle` |
| `history <entity_id> [--hours 24]` | История состояний | `GET /api/history/period/<ts>` |
| `events [--type state_changed] [--limit 50]` | Live-поток событий (WS), остановка по лимиту или Ctrl+C | WS `subscribe_events` |
| `config` | Версия, локация, компоненты | `GET /api/config` |
| `areas` / `devices` | Комнаты / устройства | WS `config/area_registry/list`, `config/device_registry/list` — **внутренний frontend-API**, не гарантирован между версиями; CLI честно сообщит, если команда недоступна |

У каждой команды есть `--json` (машинный вывод) и `--help`.

## Примеры

```bash
# Проверка связи
python ${WORKSPACE}/tools/ha_client.py ping

# Весь свет в доме
python ${WORKSPACE}/tools/ha_client.py states --domain light

# Включить свет на кухне на 50% яркости
python ${WORKSPACE}/tools/ha_client.py call light turn_on --entity light.kitchen --data '{"brightness_pct": 50}'

# Просто вкл/выкл/переключить
python ${WORKSPACE}/tools/ha_client.py on switch.heater
python ${WORKSPACE}/tools/ha_client.py toggle light.bedroom

# Температура за 12 часов
python ${WORKSPACE}/tools/ha_client.py history sensor.living_room_temperature --hours 12

# Следить за изменениями состояний (20 событий и выход)
python ${WORKSPACE}/tools/ha_client.py events --type state_changed --limit 20

# JSON для скриптов
python ${WORKSPACE}/tools/ha_client.py states --domain sensor --json
```

## Гочи

- **Креды не заданы** → exit 2 + печать инструкции по настройке (не трейсбек). Так и задумано, пока HA-инстанса нет.
- `on`/`off`/`toggle` идут через универсальный домен `homeassistant.*` — работают для light/switch/fan/media_player и т.п.; для доменных параметров (яркость, цвет, температура) — используй `call` с `--data`.
- `--data` — строго JSON в одинарных кавычках снаружи (PowerShell: `--data '{\"brightness\": 128}'` или через Git Bash без экранирования).
- `history` использует UTC-таймстамп в URL (закодированный `+00:00`) — окно задаётся `--hours`, не датами.
- `events` без `--type` подписывается на ВСЕ события — на живом инстансе это шумно; обычно нужен `--type state_changed`.
- `areas`/`devices` — WebSocket-команды внутреннего API реестров (их использует frontend HA). В официальной REST-документации их нет; стабильны годами, но формально «требуют проверки» на конкретной версии HA — при недоступности CLI сообщит об этом явно.
- 401 → токен отозван/невалиден: создать новый long-lived token; 404 на `get` → сущности не существует (проверь `states`).
- POST `/api/services/...` возвращает список состояний, изменившихся **за время вызова** — пустой список не значит «не сработало» (например, устройство уже было в целевом состоянии).

## Чек-лист

- [ ] `HA_URL` + `HA_TOKEN` в `~/.claude/.credentials.master.env`
- [ ] `ping` отвечает `API running.`
- [ ] `states` показывает сущности → entity_id для дальнейших команд брать отсюда
- [ ] Перед `call` с нестандартным сервисом — проверить его существование в HA (Developer Tools → Services); CLI не валидирует имена сервисов
- [ ] Для скриптов/агентов — всегда `--json`
