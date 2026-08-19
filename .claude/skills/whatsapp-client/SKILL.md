---
name: whatsapp-client
description: "CLI к личному WhatsApp (Baileys-мост, wa_client.py): чтение, отправка, группы, анти-бан рассылка. Триггеры: «напиши в whatsapp», «вотсап». НЕ Telegram→tg_client.py."
---

# WhatsApp Client (личный номер, локально)

Двухслойная конструкция: **Node-мост** (Baileys, держит WhatsApp-сокет) + **Python CLI**
(подключился → сделал → напечатал → вышел).

```
~/.claude/tools/wa_client.py        # CLI (Python 3.13, только stdlib)
~/.claude/tools/wa-bridge/          # Node-мост (ESM, express + Baileys 7.0.0-rc.9)
  bridge.js                           # HTTP на 127.0.0.1:<порт>, loopback-only
  .session/                           # креды Baileys (в .gitignore!) — НЕ коммитить
  store/store.json                    # локальный индекс чатов/контактов/сообщений
  bridge.log                          # весь вывод моста, включая ASCII-QR
```

## Когда использовать

- Прочитать переписку/непрочитанные, найти сообщение, выгрузить чат в файл.
- Отправить сообщение или файл себе/контакту/в группу с машины владельца.
- Посмотреть список групп, участников, профиль контакта, скачать присланное медиа.
- Аккуратно разослать личное сообщение по небольшому списку (с задержками и dry-run).

**Не использовать:** для рассылок сотнями адресатов, для чужих номеров без согласия,
для бизнес-рассылок (для этого есть официальный WhatsApp Business Cloud API — тут его нет).

## Установка / настройка

1. Node 18+ (проверено на 22.15) и Python 3.13 — уже есть.
2. Зависимости моста ставятся автоматически при первом `bridge-start`
   (или вручную: `cd ~/.claude/tools/wa-bridge && npm install`).
3. Поднять мост и привязать телефон:

```bash
python ~/.claude/tools/wa_client.py bridge-start
python ~/.claude/tools/wa_client.py login      # покажет ASCII-QR, ждёт сканирования
```

**Процедура QR-логина (делает владелец, телефон обязателен):**
WhatsApp на телефоне → **Настройки → Связанные устройства → Привязка устройства** →
навести камеру на QR в терминале. QR живёт ~20 с и перевыпускается автоматически —
`login` перерисовывает новый, пока не появится `✅ Авторизован`.
После привязки креды лежат в `.session/` и переживают перезапуски; повторный QR нужен,
только если разлогинить устройство с телефона.
> Статус: сама процедура сканирования в этой сборке **не выполнялась** (нужен телефон владельца) —
> проверены только выдача QR мостом и его отрисовка в CLI.

### Переменные окружения (значения владелец задаёт сам, дефолты рабочие)

| Переменная | Назначение |
|---|---|
| `WA_BRIDGE_DIR` | каталог моста (деф. `~/.claude/tools/wa-bridge`) |
| `WA_BRIDGE_PORT` | порт моста (деф. `3000`) |
| `WA_SESSION_DIR` | каталог сессии Baileys (деф. `<bridge>/.session`) |
| `WA_MODE` | `bot` (деф. для CLI, без Hermes-префикса) или `self-chat` |
| `WA_STORE` | `off` — выключить локальный store (тогда chats/search/contacts → 501) |
| `WA_STORE_DIR` | где лежит `store.json` (деф. `<session>/../store`) |
| `WA_STORE_MAX_MESSAGES` | размер индекса сообщений (деф. 5000) |
| `WA_RAW_CACHE_MAX` | сколько «сырых» сообщений держать в памяти для `download-media` (деф. 500) |
| `WA_MEDIA_DIR` | куда складывать скачанное медиа (деф. `<store>/media`) |
| `WHATSAPP_ALLOWED_USERS` | (наследие Hermes) allowlist для очереди `/messages`; CLI не нужен |
| `WHATSAPP_REPLY_PREFIX` | (наследие Hermes) префикс ответов; CLI ставит пустым |
| `WHATSAPP_DEBUG` | `1` — подробный лог событий моста |

Ключей/токенов не требуется: авторизация — только QR-сессия.
Если что-то из перечисленного нужно закрепить — добавь в `~/.claude/.credentials.master.env`
(CLI читает этот файл при старте).

## Команды

Общие флаги (работают и до, и после подкоманды): `--json`, `--port`, `--bridge-dir`, `--session`.

| Команда | Что делает |
|---|---|
| `bridge-start [--mode bot\|self-chat] [--timeout 40]` | Поднять мост в фоне (+ `npm install` при первом запуске) |
| `bridge-stop` | Остановить мост по pid-файлу |
| `status` | `/health`: подключение, аккаунт, uptime, охват store |
| `login [--timeout 180]` | Показать QR и ждать сканирования |
| `chats [--limit N] [--unread] [--groups]` | Чаты с последним сообщением и непрочитанными |
| `unread [--limit N]` | Только чаты с непрочитанными |
| `read-chat <jid> [--limit N] [--ids]` | История чата из store (`--ids` — показать messageId) |
| `send <jid> <text\|@file.txt>` | Отправить текст (длинный режется мостом на части) |
| `send-media <jid> <file> [--caption] [--type] [--filename]` | Отправить image/video/audio/document |
| `edit <jid> <messageId> <text>` | Отредактировать своё сообщение |
| `typing <jid>` | Индикатор набора |
| `contacts [--q ...] [--limit N]` | Контакты, известные мосту |
| `groups` | Группы аккаунта (живой запрос к WhatsApp) |
| `search <q> [--chat jid] [--limit N]` | Поиск по локальному индексу сообщений |
| `mark-read <jid> [--limit N]` | Отметить последние входящие прочитанными |
| `download-media <messageId> [--dir]` | Скачать медиа сообщения на диск |
| `profile <jid>` | Аватар, статус, бизнес-профиль / метаданные группы |
| `export-chat <jid> [--out file] [--format txt\|json] [--limit N]` | Выгрузка чата |
| `broadcast <file> <text> [--confirm] ...` | Рассылка по списку с гардами (**dry-run по умолчанию**) |

**JID:** можно `+55 XX XXXXX-XXXX`, `5581900000000` или полный `5581900000000@s.whatsapp.net`.
Группы — полный JID `120363...@g.us` (или `120363...-123456@g.us`).

### Эндпоинты моста (для отладки, `127.0.0.1` only)

Существовавшие: `GET /messages` (дренит очередь!), `POST /send`, `POST /edit`,
`POST /send-media`, `POST /typing`, `GET /chat/:id`, `GET /health`.
Добавленные: `GET /qr`, `GET /chats`, `GET /chat/:id/messages`, `GET /contacts`,
`GET /groups`, `GET /search?q=`, `POST /mark-read`, `GET /media/:messageId`, `GET /profile/:jid`.

## Примеры

```bash
# Старт и проверка
python ~/.claude/tools/wa_client.py bridge-start
python ~/.claude/tools/wa_client.py status

# Что накопилось
python ~/.claude/tools/wa_client.py unread
python ~/.claude/tools/wa_client.py read-chat "+55 XX XXXXX-XXXX" --limit 30

# Написать и приложить файл
python ~/.claude/tools/wa_client.py send "+55 XX XXXXX-XXXX" "Готово, скинул отчёт"
python ~/.claude/tools/wa_client.py send-media "+55 XX XXXXX-XXXX" "${WORKSPACE}/report.pdf" --caption "Отчёт за июль"

# Длинный текст из файла
python ~/.claude/tools/wa_client.py send "+55 XX XXXXX-XXXX" "@${WORKSPACE}/msg.txt"

# Поиск и экспорт
python ~/.claude/tools/wa_client.py search "договор" --limit 20
python ~/.claude/tools/wa_client.py export-chat "120363011111111111@g.us" --out ${WORKSPACE}/chat.txt

# Машинный вывод для скриптов
python ~/.claude/tools/wa_client.py --json chats --limit 10

# Рассылка: сначала ВСЕГДА dry-run
python ~/.claude/tools/wa_client.py broadcast ${WORKSPACE}/list.txt "Привет, {name}! ..."
# и только потом, осознанно:
python ~/.claude/tools/wa_client.py broadcast ${WORKSPACE}/list.txt "Привет, {name}! ..." --confirm --max 20
```

Формат файла для `broadcast` (плейсхолдеры `{name}`, `{jid}`, `{number}`):

```
# комментарии допустимы
+55 XX XXXXX-XXXX,Имя
79161234567,Катя
```

## ⚠️ Риск бана номера (обязательно прочитать)

Baileys — **неофициальный** клиент WhatsApp Web. Массовая/шаблонная рассылка нарушает
**Terms of Service Meta** и приводит к временной или **перманентной блокировке личного номера**.
Гарды в `broadcast` снижают риск, но не устраняют его:

- `--dry-run` включён по умолчанию, реальная отправка **только** с `--confirm`;
- пауза между адресатами **45–120 с** со случайным джиттером (`--min-delay` < 20 с запрещён);
- суточный лимит `--max 50`;
- файл состояния (`<bridge>/.broadcast/<список>.json`) — повторно тем же людям не уйдёт,
  рассылку можно прервать и продолжить;
- стоп-файл `<bridge>/.broadcast/STOP` — создай его, и цикл остановится перед следующей отправкой;
- перед каждым сообщением шлётся индикатор набора + пауза 2–6 с (`--no-typing` отключает).

Здравый смысл поверх гардов: пиши только тем, кто ждёт сообщения; варьируй текст;
не шли ссылки первым сообщением незнакомым; новый номер не годится для рассылок вовсе.

## Гочи

- **`/messages` дренит очередь.** Это эндпоинт Hermes-шлюза; CLI его не использует. Не дёргай
  руками, если параллельно работает Hermes-адаптер — украдёшь у него входящие.
- **Один мост на одну сессию.** Второй процесс на тот же `.session` ломает креды. Порт занят →
  `bridge-stop`, потом `bridge-start`. Для экспериментов — другой `--port` + другой `--session`.
- **Store ≠ история телефона.** Baileys 7.x выпилил `makeInMemoryStore`, поэтому мост ведёт
  собственный индекс: только то, что он видел вживую, плюс что отдал history-sync
  (в `bridge.js` `syncFullHistory: false` → недавнее). `chats`/`search`/`read-chat` честно
  печатают охват. Первый запуск = почти пусто, это норма, а не поломка.
- **`download-media` работает только для недавних сообщений** — «сырые» сообщения держатся
  в памяти процесса (`WA_RAW_CACHE_MAX`, деф. 500) и теряются при рестарте моста. Входящее
  медиа при этом автоматически сохраняется мостом в `~/.hermes/{image,document,audio}_cache`.
- **Режим `self-chat` добавляет префикс `⚕ Hermes Agent`** ко ВСЕМ исходящим. Для CLI дефолт
  `--mode bot` — префикса нет. Если запустил мост в self-chat, сообщения уйдут с баннером.
- **LID vs номер.** WhatsApp отдаёт часть JID в формате `...@lid` вместо `...@s.whatsapp.net`.
  CLI/мост подбирают чат и по «голому» номеру, но если чат не нашёлся — возьми точный JID
  из `chats` / `--json`.
- **`/chat/:id` для группы у неподключённого моста раньше висел бесконечно** (ждал ответа
  WhatsApp) — добавлен гард `connectionState === 'connected'`. Если ловишь таймаут на любой
  «живой» команде — сначала `status`.
- **Windows:** мост стартует detached (`DETACHED_PROCESS`), переживает закрытие терминала;
  останавливать — `bridge-stop` (внутри `taskkill /T /F`), не Ctrl+C в чужом окне.
- **Голосовые:** `send-media` для mp3/wav/m4a конвертит в ogg/opus через `ffmpeg`, чтобы вышло
  нативное голосовое. Нет ffmpeg — уйдёт обычным файлом.
- **Сессия — это доступ к аккаунту.** `.session/` уже в `.gitignore`; не копировать, не заливать,
  перед публикацией репо прогонять `leak-scan`.

### Требует проверки (честно: не проверено локально)

- Реальные отправка/редактирование/mark-read/скачивание медиа/профили/группы — требуют
  привязанного аккаунта; в этой сборке мост тестировался **без пары** (все такие команды
  корректно возвращают «WhatsApp не подключён»).
- Лимит редактирования сообщений на стороне WhatsApp (обычно ~15 минут после отправки).
- Формы ответов `fetchStatus` / `getBusinessProfile` / `onWhatsApp` в Baileys `7.0.0-rc.9`
  нормализуются защитно (`Array` / объект / отсутствие метода → понятная ошибка в поле `*Error`).
- Объём, который реально приезжает через history-sync на аккаунте владельца.

## Чек-лист

- [ ] `node --version` ≥ 18, `python --version` 3.13
- [ ] `bridge-start` → «Мост запущен», лог без ошибок
- [ ] `login` → QR отсканирован телефоном → `status` показывает `connected` и аккаунт
- [ ] `chats` отдаёт список (после нескольких входящих/исходящих)
- [ ] `send` себе → сообщение пришло без лишнего префикса
- [ ] `.session/`, `store/`, `.broadcast/`, `node_modules/` не попали в git
- [ ] Перед любой рассылкой: dry-run прочитан глазами → `--max` выставлен → стоп-файл известен
- [ ] После работы (если мост не нужен): `bridge-stop`
