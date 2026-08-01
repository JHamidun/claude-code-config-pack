# Telegram Bot API — детальный справочник всех методов

**Всего методов в справочнике: 173 · покрыто в CLI: 173 · вне CLI: 0**
> Полный разбор каждого метода: назначение, версия, все параметры, что возвращает, грабли.

> Сгенерировано из официальной доки core.telegram.org/bots/api (Bot API 10.1, 2026-06).

> Колонка статуса: ✅ покрыто в [`tg_bot.py`](./tg_bot.py) (CLI-команда) / ⚪ вне CLI (см. почему — в TG_BOT_API_REFERENCE.md §3).


## Оглавление

- [Обновления и вебхуки](#updates-webhooks) — 4 методов
- [Отправка — базовый контент](#send-core) — 10 методов
- [Отправка — медиа-группы, гео, опросы, платное](#send-extra) — 10 методов
- [Rich-сообщения и черновики](#rich-and-drafts) — 4 методов
- [Редактирование сообщений](#updating-messages) — 7 методов
- [Удаление, копирование, пересылка, реакции](#delete-copy-forward-react) — 9 методов
- [Участники и модерация](#members-moderation) — 9 методов
- [Инвайт-ссылки и заявки](#invites-joinrequests) — 8 методов
- [Свойства и информация чата](#chat-info-properties) — 15 методов
- [Форум-топики](#forum-topics) — 12 методов
- [Конфигурация и профиль бота](#bot-config-profile) — 18 методов
- [Файлы, inline, callback](#files-inline-callback) — 8 методов
- [Платежи и Telegram Stars](#payments-stars) — 8 методов
- [Подарки](#gifts) — 8 методов
- [Стикер-сеты](#stickers) — 15 методов
- [Бизнес-аккаунты, игры, верификация, прочее](#business-games-misc) — 28 методов

---


<a name="updates-webhooks"></a>
## Обновления и вебхуки

### `getUpdates` — ✅ CLI: `updates / listen`

Получает входящие обновления методом long polling (pull-модель): бот сам опрашивает серверы Telegram. Несовместим с активным webhook — если установлен webhook, метод вернёт ошибку.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `offset` | Integer | — | Идентификатор первого возвращаемого обновления. Должен быть на 1 больше максимального update_id из уже полученных обновлений. Отрицательное значение отсчитывает с конца очереди. Не передавать при первом запросе. |
| `limit` | Integer | — | Максимальное число возвращаемых обновлений, от 1 до 100. По умолчанию 100. |
| `timeout` | Integer | — | Таймаут в секундах для long polling. По умолчанию 0 (short polling). Для продакшена рекомендуется положительное значение (например, 30). Short polling не рекомендуется — только для тестирования. |
| `allowed_updates` | Array of String | — | JSON-сериализованный список типов обновлений, которые должен получать бот (например, ["message","callback_query"]). Пустой массив — получать все типы, кроме chat_member, message_reaction, message_reaction_count. Если параметр не передан, настройки из предыдущего вызова сохраняются. Типы chat_member, message_reaction и message_reaction_count нужно указывать явно. |

**Возвращает:** Array of Update

**⚠️ Грабли:** Подтверждение получения обновления происходит не сразу, а при следующем вызове getUpdates с offset = последний update_id + 1. Если не обновлять offset, одни и те же обновления будут приходить снова. Обновления хранятся на сервере не более 24 часов. Метод полностью несовместим с webhook: если webhook установлен, getUpdates вернёт ошибку 409 Conflict.

### `setWebhook` — ✅ CLI: `webhook-set`

Указывает HTTPS-URL, на который Telegram будет отправлять POST-запросы с JSON-сериализованными обновлениями (push-модель). После вызова getUpdates перестаёт работать.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `url` | String | ✅ | HTTPS-адрес для получения обновлений. Передача пустой строки удаляет webhook (аналог deleteWebhook). Поддерживаются только порты 443, 80, 88, 8443. |
| `certificate` | InputFile | — | Публичный ключ сертификата в формате PEM для самоподписанных сертификатов. Позволяет серверам Telegram верифицировать корень цепочки. Не нужен для сертификатов от доверенных CA. |
| `ip_address` | String | — | Фиксированный IP-адрес для отправки запросов вместо того, что разрешается через DNS по url. Полезно при наличии нескольких IP за одним доменом. |
| `max_connections` | Integer | — | Максимальное число одновременных HTTPS-соединений для доставки обновлений, от 1 до 100. По умолчанию 40. Большее значение увеличивает пропускную способность за счёт нагрузки на сервер. |
| `allowed_updates` | Array of String | — | JSON-сериализованный список типов обновлений для подписки. Пустой массив — все типы, кроме chat_member, message_reaction, message_reaction_count. Если не передан, сохраняется предыдущая настройка. Типы chat_member, message_reaction и message_reaction_count нужно указывать явно. |
| `drop_pending_updates` | Boolean | — | Передать True, чтобы сбросить все накопившиеся необработанные обновления в очереди при установке нового webhook. |
| `secret_token` | String | — | Секретный токен (1–256 символов; допустимы A-Z, a-z, 0-9, _, -). Telegram будет передавать его в заголовке X-Telegram-Bot-Api-Secret-Token каждого webhook-запроса. Позволяет убедиться, что запрос пришёл именно от Telegram, а не от стороннего источника. Добавлен в Bot API 6.0. |

**Возвращает:** True on success

**⚠️ Грабли:** Webhook принимает запросы только на портах 443, 80, 88 или 8443 — любой другой порт приведёт к ошибке. При использовании самоподписанного сертификата обязательно передавать certificate (публичный ключ), иначе Telegram не сможет установить TLS. После успешного setWebhook вызов getUpdates будет возвращать ошибку 409 Conflict до удаления webhook.

### `deleteWebhook` — ✅ CLI: `webhook-delete`

Удаляет webhook и позволяет вернуться к получению обновлений через getUpdates (poll-режим). Без этого вызова переключиться на polling невозможно.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `drop_pending_updates` | Boolean | — | Передать True, чтобы сбросить все накопившиеся необработанные обновления из очереди при удалении webhook. По умолчанию очередь сохраняется. |

**Возвращает:** True on success

**⚠️ Грабли:** Если не передать drop_pending_updates=True, все обновления, накопленные за время работы webhook (в том числе за периоды недоступности сервера), будут доставлены через getUpdates после переключения. Это может вызвать неожиданный «flood» старых сообщений.

### `getWebhookInfo` — ✅ CLI: `webhook-info`

Возвращает текущий статус webhook: URL, наличие кастомного сертификата, число ожидающих обновлений, последнюю ошибку доставки и другие диагностические данные. Параметров не принимает.

**Возвращает:** WebhookInfo — объект со следующими полями: url (String, always), has_custom_certificate (Boolean, always), pending_update_count (Integer, always), ip_address (String, optional), last_error_date (Integer Unix timestamp, optional), last_error_message (String, optional), last_synchronization_error_date (Integer Unix timestamp, optional), max_connections (Integer, optional), allowed_updates (Array of String, optional)

**⚠️ Грабли:** Если webhook не установлен (бот работает в режиме polling), метод всё равно возвращает объект WebhookInfo, но поле url будет пустой строкой. Это не ошибка — так и задумано. Поле last_error_message не очищается автоматически после успешных доставок; чтобы понять, актуальна ли ошибка, нужно сравнивать last_error_date с временем последней успешной доставки.


<a name="send-core"></a>
## Отправка — базовый контент

### `sendMessage` — ✅ CLI: `send`

Отправляет текстовое сообщение в указанный чат. Возвращает объект Message отправленного сообщения.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения; сообщение будет отправлено от имени аккаунта бизнеса |
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы/канала |
| `message_thread_id` | Integer | — | ID топика форума; только для форум-супергрупп и приватных чатов с включённым forum topic mode |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages; обязателен при отправке в direct messages чат |
| `text` | String | ✅ | Текст сообщения, 1–4096 символов после применения парсинга |
| `parse_mode` | String | — | Режим форматирования: Markdown, MarkdownV2 или HTML |
| `entities` | Array of MessageEntity | — | Список спецсущностей (bold, italic, link…); альтернатива parse_mode — нельзя использовать оба |
| `link_preview_options` | LinkPreviewOptions | — | Опции генерации превью ссылок (включить/выключить, URL для превью, позиция над/под текстом) |
| `disable_notification` | Boolean | — | true — отправить без звука (silent) |
| `protect_content` | Boolean | — | Запрещает пересылку и сохранение сообщения |
| `allow_paid_broadcast` | Boolean | — | Разрешает до 1000 сообщений/с в обход лимитов рассылки; 0.1 Telegram Star за сообщение списывается с баланса бота |
| `message_effect_id` | String | — | ID эффекта (анимации), добавляемого к сообщению; только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста; только для direct messages чатов; если сообщение — ответ на другой suggested post, тот автоматически отклоняется |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение (message_id, цитата, cross-chat reply) |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры или инлайн-кнопок |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** parse_mode и entities нельзя передавать одновременно. При использовании MarkdownV2 спецсимволы (_, *, [, ], (, ), ~, `, >, #, +, -, =, |, {, }, ., !) обязательно экранировать обратным слешем, иначе запрос упадёт с ошибкой.

### `sendPhoto` — ✅ CLI: `send --photo`

Отправляет фотографию в чат. Возвращает объект Message отправленного сообщения.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `photo` | InputFile or String | ✅ | Фото: file_id существующего файла на серверах Telegram, HTTP URL или загрузка через multipart/form-data. Макс. 10 МБ, соотношение сторон не более 20:1, сумма ширины и высоты не более 10 000 |
| `caption` | String | — | Подпись к фото, 0–1024 символа после парсинга |
| `parse_mode` | String | — | Режим форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Спецсущности в подписи; альтернатива parse_mode |
| `show_caption_above_media` | Boolean | — | true — показывать подпись над фото, а не под ним |
| `has_spoiler` | Boolean | — | true — фото закрывается анимацией-спойлером |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста; только для direct messages |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Telegram сжимает фото при загрузке через URL или upload; если нужно сохранить оригинальное качество — используйте sendDocument. Миниатюры в ответе (поле photo[]) — массив PhotoSize разных размеров, сгенерированных сервером, а не оригинал.

### `sendAudio` — ✅ CLI: `send --audio`

Отправляет аудиофайл в формате MP3 или M4A — Telegram отобразит его в музыкальном плеере. Для голосовых сообщений (ogg/opus) используется sendVoice.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `audio` | InputFile or String | ✅ | Аудиофайл: file_id, HTTP URL или multipart/form-data. Макс. 50 МБ. Формат MP3 или M4A |
| `caption` | String | — | Подпись, 0–1024 символа |
| `parse_mode` | String | — | Режим форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Спецсущности в подписи |
| `duration` | Integer | — | Длительность аудио в секундах — используется клиентом для отображения |
| `performer` | String | — | Исполнитель — отображается в плеере |
| `title` | String | — | Название трека — отображается в плеере |
| `thumbnail` | InputFile or String | — | Обложка альбома. JPEG, < 200 КБ, не более 320×320. Нельзя повторно использовать file_id обложки — только upload |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Если файл не в формате MP3/M4A, Telegram отправит его как Document, а не как аудио в плеере. thumbnail нельзя повторно использовать по file_id — его нужно загружать каждый раз заново через multipart.

### `sendDocument` — ✅ CLI: `send --document`

Отправляет произвольный файл (документ) любого типа. Ботам доступна отправка файлов до 50 МБ; лимит может быть изменён в будущем.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `document` | InputFile or String | ✅ | Файл: file_id, HTTP URL или multipart/form-data |
| `thumbnail` | InputFile or String | — | Превью документа. JPEG, < 200 КБ, до 320×320. Thumbnail нельзя переиспользовать — только upload через multipart |
| `caption` | String | — | Подпись, 0–1024 символа |
| `parse_mode` | String | — | Режим форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Спецсущности в подписи |
| `disable_content_type_detection` | Boolean | — | Отключает автоопределение типа контента на сервере (файл всегда будет документом, а не фото/видео) |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста; только для direct messages |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Если передать фото или видео без disable_content_type_detection=true, сервер может автоматически переклассифицировать файл в photo/video, и сообщение не будет Document. При отправке в альбоме (sendMediaGroup) disable_content_type_detection всегда True.

### `sendVideo` — ✅ CLI: `send --video`

Отправляет видеофайл (MPEG4). Другие форматы могут быть отправлены как Document. Лимит 50 МБ.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `video` | InputFile or String | ✅ | Видео: file_id, HTTP URL или multipart/form-data |
| `duration` | Integer | — | Длительность в секундах |
| `width` | Integer | — | Ширина видео |
| `height` | Integer | — | Высота видео |
| `thumbnail` | InputFile or String | — | Превью (обложка) видео. JPEG, < 200 КБ, до 320×320. Только upload, не переиспользуется |
| `cover` | InputFile or String | — | Обложка видео в сообщении (новый параметр). file_id, HTTP URL или multipart upload |
| `start_timestamp` | Integer | — | Временная метка начала воспроизведения видео в секундах |
| `caption` | String | — | Подпись, 0–1024 символа |
| `parse_mode` | String | — | Режим форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Спецсущности в подписи |
| `show_caption_above_media` | Boolean | — | true — подпись над видео |
| `has_spoiler` | Boolean | — | true — видео закрыто спойлером |
| `supports_streaming` | Boolean | — | true — видео пригодно для стриминга (H.264, прогрессивная загрузка) |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста; только для direct messages |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Без supports_streaming=true клиент скачает файл целиком перед воспроизведением. thumbnail нельзя переиспользовать по file_id. Не-MPEG4 форматы (AVI, MOV и т.д.) Telegram конвертирует или доставит как Document.

### `sendAnimation` — ✅ CLI: `send --animation`

Отправляет анимацию (GIF или H.264/MPEG-4 AVC без звука). Лимит 50 МБ.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `animation` | InputFile or String | ✅ | Анимация: file_id, HTTP URL или multipart/form-data |
| `duration` | Integer | — | Длительность в секундах |
| `width` | Integer | — | Ширина анимации |
| `height` | Integer | — | Высота анимации |
| `thumbnail` | InputFile or String | — | Превью. JPEG, < 200 КБ, до 320×320. Только upload |
| `caption` | String | — | Подпись, 0–1024 символа |
| `parse_mode` | String | — | Режим форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Спецсущности в подписи |
| `show_caption_above_media` | Boolean | — | true — подпись над анимацией |
| `has_spoiler` | Boolean | — | true — анимация закрыта спойлером |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста; только для direct messages |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** GIF-файлы Telegram конвертирует в MP4 без звука — возвращённый объект будет Animation, а не «настоящий» GIF. Если отправить файл MP4 со звуком этим методом, звук будет проигнорирован; используйте sendVideo.

### `sendVoice` — ✅ CLI: `send --voice`

Отправляет голосовое сообщение (воспроизводится встроенным плеером). Аудио должно быть в формате OGG (OPUS), MP3 или M4A.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `voice` | InputFile or String | ✅ | Голосовой файл: file_id, HTTP URL или multipart/form-data. Макс. 50 МБ. Формат: OGG/OPUS, MP3 или M4A |
| `caption` | String | — | Подпись, 0–1024 символа |
| `parse_mode` | String | — | Режим форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Спецсущности в подписи |
| `duration` | Integer | — | Длительность голосового сообщения в секундах |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста; только для direct messages |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Отличие от sendAudio: sendVoice отображает сообщение как голосовое (с волнограммой), а не как трек в плеере. Файлы не в OGG/OPUS формате Telegram примет, но волнограмма может не отображаться корректно.

### `sendVideoNote` — ✅ CLI: `send --video-note`  · _Bot API 4.0_

Отправляет видеосообщение в виде круглого MPEG4-ролика длиной до 1 минуты (видеокружок). Введено в Bot API 4.0.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `video_note` | InputFile or String | ✅ | Видео: file_id, HTTP URL или multipart/form-data. Должно быть квадратным MPEG4 до 1 минуты |
| `duration` | Integer | — | Длительность в секундах |
| `length` | Integer | — | Размер стороны видеокружка (ширина = высота); если не указан — определяется автоматически |
| `thumbnail` | InputFile or String | — | Превью кадра. JPEG, < 200 КБ, до 320×320. Только upload, не переиспользуется |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Видеокружок обязательно должен быть квадратным. Прямоугольное видео Telegram отклонит или обрежет. Загрузка через HTTP URL не поддерживается для видеокружков — только file_id или multipart upload.

### `sendSticker` — ✅ CLI: `send --sticker`

Отправляет стикер (статичный .WEBP, анимированный .TGS или видео-стикер .WEBM). Возвращает объект Message.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика direct messages |
| `sticker` | InputFile or String | ✅ | Стикер: file_id, HTTP URL или multipart upload. Анимированные и видео-стикеры нельзя загружать по HTTP URL — только file_id или upload |
| `emoji` | String | — | Эмодзи, связанный со стикером; используется при отправке обычного эмодзи-стикера |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | До 1000 сообщений/с за Stars |
| `message_effect_id` | String | — | ID эффекта; только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Разметка клавиатуры |

**Возвращает:** Message — объект отправленного сообщения

**⚠️ Грабли:** Анимированные (.TGS) и видео (.WEBM) стикеры нельзя загрузить через HTTP URL — только через file_id или multipart upload. Статичные WEBP через URL — можно. При отправке стикера из чужого набора используйте file_id, а не URL.

### `sendChatAction` — ✅ CLI: `action`

Сообщает пользователю, что бот выполняет действие (например, «печатает…» или «загружает фото»). Статус отображается не более 5 секунд и сбрасывается при получении любого сообщения от бота.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения |
| `chat_id` | Integer or String | ✅ | ID чата или @username. Каналы и их direct messages чаты не поддерживаются |
| `message_thread_id` | Integer | — | ID топика форума или топика приватного чата с включённым forum topic mode |
| `action` | String | ✅ | Тип действия: typing (текст), upload_photo, record_video, upload_video, record_voice, upload_voice, upload_document, choose_sticker, find_location, record_video_note, upload_video_note |

**Возвращает:** True при успехе

**⚠️ Грабли:** Статус автоматически сбрасывается через 5 секунд или сразу после отправки сообщения ботом — нужно вызывать метод повторно в цикле для длительных операций. Метод не работает в каналах (только в группах и личных чатах).


<a name="send-extra"></a>
## Отправка — медиа-группы, гео, опросы, платное

### `sendMediaGroup` — ✅ CLI: `album`  · _Bot API 3.5_

Отправляет группу фото, видео, документов или аудио как альбом. Возвращает массив из 2–10 отправленных Message.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала |
| `media` | Array of InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo, InputMediaLivePhoto | ✅ | 2–10 элементов; тип всех должен быть одинаковым (или только photo+video вместе); caption задаётся только на первом элементе |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за 0.1 Stars каждое |
| `message_effect_id` | String | — | ID эффекта сообщения, только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |

**Возвращает:** Array of Message (от 2 до 10 объектов)

**⚠️ Грабли:** reply_markup у sendMediaGroup отсутствует — нельзя прикрепить клавиатуру. Начиная с Bot API 10.0 в массив можно включать InputMediaLivePhoto.

### `sendLocation` — ✅ CLI: `location`  · _Bot API 1.0_

Отправляет геолокацию (точку на карте). Если задан live_period, создаёт «живую» геолокацию, которую бот может обновлять через editMessageLiveLocation.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала |
| `latitude` | Float | ✅ | Широта |
| `longitude` | Float | ✅ | Долгота |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `horizontal_accuracy` | Float | — | Радиус неопределённости в метрах, 0–1500 |
| `live_period` | Integer | — | Период обновления живой геолокации в секундах (60–86400), или 0x7FFFFFFF для бессрочной |
| `heading` | Integer | — | Направление движения пользователя в градусах, 1–360. Только для живой геолокации |
| `proximity_alert_radius` | Integer | — | Максимальная дистанция для proximity-алертов в метрах, 1–100000. Только для живой геолокации |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста в чате прямых сообщений |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |

**Возвращает:** Message

**⚠️ Грабли:** heading и proximity_alert_radius допустимы только при наличии live_period. Для бессрочной живой геолокации указывают live_period = 2147483647 (0x7FFFFFFF).

### `sendVenue` — ✅ CLI: `venue`  · _Bot API 1.0_

Отправляет информацию о заведении (место на карте с названием и адресом). Поддерживает идентификаторы Foursquare и Google Places.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала |
| `latitude` | Float | ✅ | Широта заведения |
| `longitude` | Float | ✅ | Долгота заведения |
| `title` | String | ✅ | Название заведения |
| `address` | String | ✅ | Адрес заведения |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `foursquare_id` | String | — | Идентификатор заведения в Foursquare |
| `foursquare_type` | String | — | Тип заведения в Foursquare, например «food/icecream» |
| `google_place_id` | String | — | Идентификатор заведения в Google Places |
| `google_place_type` | String | — | Тип заведения по классификации Google Places |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста в чате прямых сообщений |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |

**Возвращает:** Message

**⚠️ Грабли:** foursquare_id/foursquare_type и google_place_id/google_place_type взаимозаменяемы — Telegram отображает иконку места только если передан один из них, но не требует. Передавать оба источника сразу не рекомендуется.

### `sendContact` — ✅ CLI: `contact`  · _Bot API 1.0_

Отправляет телефонный контакт. Контакт не обязан быть пользователем Telegram; данные задаются явно в параметрах.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала |
| `phone_number` | String | ✅ | Номер телефона контакта |
| `first_name` | String | ✅ | Имя контакта |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `last_name` | String | — | Фамилия контакта |
| `vcard` | String | — | Дополнительные данные в формате vCard, 0–2048 байт |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста в чате прямых сообщений |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |

**Возвращает:** Message

**⚠️ Грабли:** phone_number — просто строка, Telegram не валидирует её формат. Для отображения контакта с аватаром нужно передать корректный vcard с PHOTO-полем.

### `sendPoll` — ✅ CLI: `poll`  · _Bot API 4.0_

Отправляет опрос (regular) или викторину (quiz) в чат. С Bot API 9.6 значительно расширен: поддерживает медиа, описание, множественные правильные ответы и ограничение по стране.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username; нельзя отправить в канальные личные сообщения |
| `question` | String | ✅ | Вопрос опроса, 1–300 символов после парсинга |
| `options` | Array of InputPollOption | ✅ | Варианты ответа, 1–12 элементов |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `question_parse_mode` | String | — | Режим парсинга сущностей в вопросе; допускаются только custom emoji |
| `question_entities` | Array of MessageEntity | — | Альтернатива question_parse_mode |
| `is_anonymous` | Boolean | — | По умолчанию True — анонимный опрос |
| `type` | String | — | «quiz» или «regular», по умолчанию «regular» |
| `allows_multiple_answers` | Boolean | — | Разрешить несколько ответов; не работает для quiz |
| `correct_option_ids` | Array of Integer | — | 0-based ID правильных вариантов для quiz; заменяет устаревший correct_option_id (Bot API 9.6) |
| `explanation` | String | — | Текст объяснения при неверном ответе в quiz, 0–200 символов |
| `explanation_parse_mode` | String | — | Режим парсинга в объяснении |
| `explanation_entities` | Array of MessageEntity | — | Альтернатива explanation_parse_mode |
| `explanation_media` | InputPollMedia | — | Медиа для объяснения quiz (добавлено в Bot API 10.0) |
| `open_period` | Integer | — | Время активности опроса в секундах, 5–2628000; взаимоисключает close_date |
| `close_date` | Integer | — | Unix timestamp закрытия, 5–2628000 сек от текущего момента; взаимоисключает open_period |
| `is_closed` | Boolean | — | Передать True для немедленного закрытия (удобно для превью) |
| `allows_revoting` | Boolean | — | Разрешить менять ответ (Bot API 9.6) |
| `shuffle_options` | Boolean | — | Случайный порядок вариантов (Bot API 9.6) |
| `allow_adding_options` | Boolean | — | Позволить пользователям добавлять варианты; не работает для анонимных и quiz (Bot API 9.6) |
| `hide_results_until_closes` | Boolean | — | Скрыть результаты до закрытия опроса (Bot API 9.6) |
| `description` | String | — | Описание опроса, 0–1024 символа (Bot API 9.6) |
| `description_parse_mode` | String | — | Режим парсинга в описании (Bot API 9.6) |
| `description_entities` | Array of MessageEntity | — | Альтернатива description_parse_mode (Bot API 9.6) |
| `media` | InputPollMedia | — | Медиа для описания опроса (Bot API 10.0) |
| `members_only` | Boolean | — | Только для каналов: ограничить голосование участниками 24+ ч (Bot API 9.6) |
| `country_codes` | Array of String | — | ISO 3166-1 alpha-2 коды стран; только участники из этих стран могут голосовать; 0–12 элементов; только для каналов (Bot API 9.6) |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |
| `correct_option_id` | Integer | — | УСТАРЕЛ в Bot API 9.6 — использовать correct_option_ids |
| `allow_user_suggestions` | Boolean | — | Устаревший псевдоним allow_adding_options |

**Возвращает:** Message

**⚠️ Грабли:** correct_option_id (единственный) устарел с Bot API 9.6 — нужно использовать correct_option_ids (массив). members_only и country_codes работают только в каналах, не в группах. allow_adding_options несовместим с is_anonymous=True и type=«quiz».

### `sendDice` — ✅ CLI: `dice`  · _Bot API 4.7_

Отправляет анимированный эмодзи, значение которого генерируется случайно сервером Telegram. Бот не может контролировать выпавшее значение.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `emoji` | String | — | Один из: 🎲 (1–6), 🎯 (1–6), 🏀 (1–5), ⚽ (1–5), 🎳 (1–6), 🎰 (1–64). По умолчанию 🎲 |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста в чате прямых сообщений |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |

**Возвращает:** Message (поле dice содержит emoji и случайное value)

**⚠️ Грабли:** Значение (value) генерирует сервер — бот получает его только из возвращённого Message или обновления, не может задать заранее. Диапазон значений зависит от emoji: 🎰 даёт 1–64 (64 = джекпот).

### `sendPaidMedia` — ✅ CLI: `paid-media`  · _Bot API 7.6_

Отправляет платный медиаконтент (фото или видео) в чат или канал. Пользователь должен купить доступ за указанное количество Telegram Stars.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала |
| `star_count` | Integer | ✅ | Цена доступа в Telegram Stars, 1–25000 |
| `media` | Array of InputPaidMediaPhoto or InputPaidMediaVideo | ✅ | Массив медиафайлов, до 10 элементов |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `payload` | String | — | Произвольная строка-метка, 0–128 байт; не видна пользователям, передаётся в successful_payment |
| `caption` | String | — | Подпись к медиа, 0–1024 символа |
| `parse_mode` | String | — | Режим парсинга сущностей в подписи |
| `caption_entities` | Array of MessageEntity | — | Альтернатива parse_mode |
| `show_caption_above_media` | Boolean | — | Показывать подпись над медиа |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста в чате прямых сообщений |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |

**Возвращает:** Message

**⚠️ Грабли:** Работает только в каналах и приватных чатах; нельзя отправить в обычные группы и супергруппы без разрешения платежей. payload не шифруется — не хранить в нём секреты.

### `sendLivePhoto` — ✅ CLI: `live-photo`  · _Bot API 10.0_

Отправляет «живое фото» — статическое изображение с прикреплённым коротким видеоклипом (до 10 секунд). Аналог Live Photos в iOS.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала |
| `live_photo` | InputFile or String | ✅ | Видеоклип живого фото, не длиннее 10 секунд и не более 10 МБ; file_id, URL или загрузка через multipart |
| `photo` | InputFile or String | ✅ | Статическое изображение живого фото; file_id, URL или загрузка через multipart |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений |
| `caption` | String | — | Подпись, 0–1024 символа |
| `parse_mode` | String | — | Режим парсинга сущностей в подписи |
| `caption_entities` | Array of MessageEntity | — | Альтернатива parse_mode |
| `show_caption_above_media` | Boolean | — | Показывать подпись над медиа |
| `has_spoiler` | Boolean | — | Добавить спойлер-анимацию |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предлагаемого поста в чате прямых сообщений |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура |

**Возвращает:** Message

**⚠️ Грабли:** Требуется передать ОБА файла — live_photo (видео) и photo (статика). Метод появился в Bot API 10.0 (май 2026) и поддерживается также в sendMediaGroup и editMessageMedia.

### `sendChecklist` — ✅ CLI: `send-checklist`  · _Bot API 9.1_

Отправляет чеклист от имени бизнес-аккаунта. Метод доступен только через бизнес-соединение (business_connection_id обязателен).


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения, от имени которого отправляется чеклист |
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `checklist` | InputChecklist | ✅ | JSON-сериализованный объект чеклиста с заданиями |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup | — | Только инлайн-клавиатура |

**Возвращает:** Message

**⚠️ Грабли:** Метод работает исключительно через business_connection_id — обычный бот без бизнес-аккаунта не сможет его вызвать. Добавлен в Bot API 9.1 (июль 2025).

### `sendGame` — ✅ CLI: `send-game`  · _Bot API 2.4_

Отправляет игру (Telegram Games) в чат. Игра идентифицируется коротким именем, которое задаётся через @BotFather.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username; игры нельзя отправлять в прямые сообщения каналов |
| `game_short_name` | String | ✅ | Короткое имя игры, уникальный идентификатор зарегистрированной в @BotFather игры |
| `business_connection_id` | String | — | Идентификатор бизнес-соединения |
| `message_thread_id` | Integer | — | ID топика форума |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | Разрешить рассылку до 1000 сообщений/сек за Stars |
| `message_effect_id` | String | — | ID эффекта, только для приватных чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup | — | Только InlineKeyboardMarkup. Если передан пустой — Telegram автоматически добавляет кнопку «Play game_title». Если передан непустой — первая кнопка должна запускать игру |

**Возвращает:** Message

**⚠️ Грабли:** reply_markup принимает только InlineKeyboardMarkup (не ReplyKeyboard). Если передать непустую клавиатуру, первой кнопкой обязана идти кнопка с callback_game или url запуска игры — иначе Telegram вернёт ошибку.


<a name="rich-and-drafts"></a>
## Rich-сообщения и черновики

### `sendRichMessage` — ✅ CLI: `rich`  · _Bot API Bot API 10.1_

Отправляет «богатое» (rich) сообщение в чат. Rich-сообщение — это структурированный документ с блоками (заголовки, параграфы, изображения, списки и т.д.), описываемый объектом InputRichMessage через HTML или Markdown.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Идентификатор чата или username (@channel). Поддерживаются личные чаты, группы, супергруппы, каналы |
| `rich_message` | InputRichMessage | ✅ | Объект с содержимым rich-сообщения; содержит ровно одно из полей html или markdown |
| `business_connection_id` | String | — | Идентификатор бизнес-подключения; требуется для отправки от имени бизнес-аккаунта |
| `message_thread_id` | Integer | — | ID топика (thread) в форуме-супергруппе |
| `direct_messages_topic_id` | Integer | — | ID топика в разделе Direct Messages; обязателен, если чат — Direct Messages |
| `disable_notification` | Boolean | — | True — сообщение придёт без звука |
| `protect_content` | Boolean | — | True — запрещает пересылку и сохранение |
| `allow_paid_broadcast` | Boolean | — | True — разрешает до 1000 сообщений/сек с оплатой Звёздами (снимает broadcasting-лимиты) |
| `message_effect_id` | String | — | Идентификатор эффекта сообщения (например, 🔥) |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предложенного поста (используется при предложении контента в каналы) |
| `reply_parameters` | ReplyParameters | — | Описание сообщения, на которое нужно ответить |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Дополнительная разметка интерфейса |

**Возвращает:** Message

**⚠️ Грабли:** Rich-сообщения поддерживают только rich-ориентированный HTML/Markdown (описан в разделе rich message formatting options), а не обычный Telegram-форматированный текст. InputRichMessage требует ровно одно из полей html или markdown — передавать оба нельзя.

### `sendRichMessageDraft` — ✅ CLI: `rich-draft`  · _Bot API Bot API 10.1_

Отправляет частичное (потоковое) rich-сообщение как черновик — временный предпросмотр длительностью 30 секунд, видимый пользователю пока сообщение «генерируется». После завершения необходимо вызвать sendRichMessage с тем же draft_id для сохранения финального варианта.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer | ✅ | Идентификатор личного чата (только private chat); rich-черновики поддерживаются исключительно в личных переписках |
| `draft_id` | Integer | ✅ | Уникальный положительный идентификатор черновика; должен быть ненулевым. Повторные вызовы с одним draft_id анимированно обновляют черновик на стороне клиента |
| `rich_message` | InputRichMessage | ✅ | Частичное содержимое rich-сообщения для стриминга |
| `message_thread_id` | Integer | — | ID топика в private chat с включёнными темами (topics) |

**Возвращает:** Boolean (True при успехе)

**⚠️ Грабли:** Черновик автоматически исчезает через 30 секунд если не завершить его через sendRichMessage. Работает только в личных чатах (private chat). Не следует путать draft_id между разными пользователями — черновик привязан к конкретному chat_id + draft_id.

### `sendMessageDraft` — ✅ CLI: `msg-draft`  · _Bot API Bot API 9.3_

Отправляет потоковый черновик текстового сообщения — временный предпросмотр, отображаемый пользователю пока бот генерирует ответ. Позволяет передавать пустой текст (начиная с Bot API 9.6 / апрель 2026) для показа плейсхолдера «Thinking…».


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer | ✅ | Идентификатор личного чата назначения (только private chat) |
| `draft_id` | Integer | ✅ | Уникальный положительный идентификатор черновика; повторные вызовы с одним draft_id анимированно обновляют черновик |
| `message_thread_id` | Integer | — | ID топика, если чат — private chat с включёнными темами |
| `text` | String | — | Текст черновика; 0–4096 символов после парсинга. Пустая строка показывает плейсхолдер «Thinking…» (допустимо с Bot API 9.6) |
| `parse_mode` | String | — | Режим парсинга сущностей: Markdown, MarkdownV2, HTML |
| `entities` | Array of MessageEntity | — | Список сущностей; взаимоисключающий с parse_mode |

**Возвращает:** Boolean (True при успехе)

**⚠️ Грабли:** Черновик видим только в личном чате и исчезает автоматически — его нужно завершить финальным sendMessage с тем же chat_id. Передача и text, и entities одновременно с parse_mode запрещена. До Bot API 9.6 пустой text вызывал ошибку; начиная с 9.6 — показывает «Thinking…».

### `editMessageChecklist` — ✅ CLI: `edit-checklist`  · _Bot API Bot API 9.1_

Редактирует существующий чеклист, отправленный от имени бизнес-аккаунта. Позволяет полностью заменить содержимое чеклиста новым объектом InputChecklist.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-подключения; метод работает исключительно через бизнес-аккаунт |
| `chat_id` | Integer or String | ✅ | Идентификатор чата, в котором находится сообщение с чеклистом |
| `message_id` | Integer | ✅ | Идентификатор сообщения с чеклистом, которое нужно отредактировать |
| `checklist` | InputChecklist | ✅ | Новое содержимое чеклиста, включающее заголовок и список задач |
| `reply_markup` | InlineKeyboardMarkup | — | Новая инлайн-клавиатура для сообщения |

**Возвращает:** Message

**⚠️ Грабли:** Метод доступен только через бизнес-подключение (business_connection_id обязателен). Нельзя редактировать чеклист обычным sendMessage/editMessageText — для этого существует отдельный метод. При обновлении задач через InputChecklist все идентификаторы задач (InputChecklistTask.id) должны быть уникальными в рамках нового чеклиста; если нужно сохранить уже выполненные задачи, их состояние не переносится автоматически.


<a name="updating-messages"></a>
## Редактирование сообщений

### `editMessageText` — ✅ CLI: `edit / edit --rich`

Редактирует текст, rich-сообщение или сообщение игры. При успехе возвращает отредактированный объект Message (если сообщение не inline), иначе True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено редактируемое сообщение |
| `chat_id` | Integer or String | — | Обязателен, если не указан inline_message_id. ID чата или @username |
| `message_id` | Integer | — | Обязателен, если не указан inline_message_id. ID редактируемого сообщения |
| `inline_message_id` | String | — | Обязателен, если не указаны chat_id и message_id. ID inline-сообщения |
| `text` | String | — | Новый текст сообщения, 1–4096 символов после разбора сущностей; обязателен, если не указан rich_message |
| `parse_mode` | String | — | Режим парсинга форматирования: HTML, Markdown, MarkdownV2 |
| `entities` | Array of MessageEntity | — | Список сущностей форматирования; альтернатива parse_mode, нельзя использовать одновременно |
| `link_preview_options` | LinkPreviewOptions | — | Настройки превью ссылок для сообщения |
| `rich_message` | InputRichMessage | — | Новое rich-содержимое сообщения; обязателен, если не указан text (добавлен в Bot API 9.6 / 10.1) |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура для сообщения |

**Возвращает:** Message (если не inline-сообщение) или True (если inline-сообщение)

**⚠️ Грабли:** Бизнес-сообщения, не отправленные ботом и не содержащие inline-клавиатуры, можно редактировать только в течение 48 часов с момента отправки. Параметры text и rich_message взаимоисключающие: нужно передать ровно один из них.

### `editMessageCaption` — ✅ CLI: `edit`

Редактирует подпись (caption) медиасообщения. При успехе возвращает отредактированный Message (если не inline) или True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено редактируемое сообщение |
| `chat_id` | Integer or String | — | Обязателен, если не указан inline_message_id. ID чата или @username |
| `message_id` | Integer | — | Обязателен, если не указан inline_message_id. ID редактируемого сообщения |
| `inline_message_id` | String | — | Обязателен, если не указаны chat_id и message_id. ID inline-сообщения |
| `caption` | String | — | Новая подпись, 0–1024 символа после разбора сущностей |
| `parse_mode` | String | — | Режим парсинга форматирования подписи |
| `caption_entities` | Array of MessageEntity | — | Список сущностей форматирования подписи; альтернатива parse_mode |
| `show_caption_above_media` | Boolean | — | True — показывать подпись над медиа (только для animation, photo, video) |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура для сообщения |

**Возвращает:** Message (если не inline-сообщение) или True (если inline-сообщение)

**⚠️ Грабли:** Бизнес-сообщения без inline-клавиатуры доступны для редактирования только 48 часов. Передача пустой строки в caption удалит подпись полностью.

### `editMessageMedia` — ✅ CLI: `edit-media`

Заменяет медиафайл (анимацию, аудио, документ, фото, live photo или видео) в существующем сообщении, либо заменяет текстовое или rich-сообщение медиафайлом. При успехе возвращает Message или True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено редактируемое сообщение |
| `chat_id` | Integer or String | — | Обязателен, если не указан inline_message_id. ID чата или @username |
| `message_id` | Integer | — | Обязателен, если не указан inline_message_id. ID редактируемого сообщения |
| `inline_message_id` | String | — | Обязателен, если не указаны chat_id и message_id. ID inline-сообщения |
| `media` | InputMedia | ✅ | JSON-объект с новым медиасодержимым: InputMediaAnimation, InputMediaAudio, InputMediaDocument, InputMediaPhoto или InputMediaVideo |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура для сообщения |

**Возвращает:** Message (если не inline-сообщение) или True (если inline-сообщение)

**⚠️ Грабли:** В inline-сообщениях нельзя загрузить новый файл — только file_id или URL. Если сообщение входит в медиагруппу (альбом), тип медиа ограничен: аудиоальбом → только audio, документальный альбом → только document, остальные → photo, live photo или video.

### `editMessageLiveLocation` — ✅ CLI: `edit-live-loc`

Обновляет координаты в live location-сообщении. Редактирование доступно до истечения live_period или до явной остановки через stopMessageLiveLocation. При успехе возвращает Message или True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено редактируемое сообщение |
| `chat_id` | Integer or String | — | Обязателен, если не указан inline_message_id. ID чата или @username |
| `message_id` | Integer | — | Обязателен, если не указан inline_message_id. ID редактируемого сообщения |
| `inline_message_id` | String | — | Обязателен, если не указаны chat_id и message_id. ID inline-сообщения |
| `latitude` | Float | ✅ | Новая широта местоположения |
| `longitude` | Float | ✅ | Новая долгота местоположения |
| `live_period` | Integer | — | Новый период в секундах, в течение которого можно обновлять локацию, отсчитывается от даты отправки. 0x7FFFFFFF = бессрочно. Новое значение не может превышать текущее более чем на одни сутки; срок окончания должен оставаться в пределах 90 дней. Если не указан — период не меняется |
| `horizontal_accuracy` | Float | — | Радиус погрешности местоположения в метрах; 0–1500 |
| `heading` | Integer | — | Направление движения пользователя в градусах; 1–360 |
| `proximity_alert_radius` | Integer | — | Максимальное расстояние для оповещений о приближении другого участника чата, в метрах; 1–100000 |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура для сообщения |

**Возвращает:** Message (если не inline-сообщение) или True (если inline-сообщение)

**⚠️ Грабли:** Новый live_period не может превышать текущий более чем на одни сутки, а дата истечения не должна выходить за пределы 90 дней от момента вызова. Попытка редактировать истёкшую или остановленную live location вернёт ошибку.

### `editMessageReplyMarkup` — ✅ CLI: `edit`

Изменяет только inline-клавиатуру (reply markup) существующего сообщения, не затрагивая содержимое. При успехе возвращает Message или True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено редактируемое сообщение |
| `chat_id` | Integer or String | — | Обязателен, если не указан inline_message_id. ID чата или @username |
| `message_id` | Integer | — | Обязателен, если не указан inline_message_id. ID редактируемого сообщения |
| `inline_message_id` | String | — | Обязателен, если не указаны chat_id и message_id. ID inline-сообщения |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура. Если не передать — клавиатура будет удалена |

**Возвращает:** Message (если не inline-сообщение) или True (если inline-сообщение)

**⚠️ Грабли:** Бизнес-сообщения без inline-клавиатуры редактируются только в течение 48 часов. Если передать пустой объект reply_markup или не передать его вовсе — клавиатура удаляется с сообщения.

### `stopMessageLiveLocation` — ✅ CLI: `stop-live-loc`

Останавливает трансляцию live location до истечения live_period. После вызова обновления координат невозможны. При успехе возвращает Message или True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено редактируемое сообщение |
| `chat_id` | Integer or String | — | Обязателен, если не указан inline_message_id. ID чата или @username |
| `message_id` | Integer | — | Обязателен, если не указан inline_message_id. ID сообщения с live location |
| `inline_message_id` | String | — | Обязателен, если не указаны chat_id и message_id. ID inline-сообщения |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура для сообщения после остановки |

**Возвращает:** Message (если не inline-сообщение) или True (если inline-сообщение)

**⚠️ Грабли:** Если live_period уже истёк, вызов вернёт ошибку — нельзя остановить уже завершённую трансляцию. Остановка необратима: запустить live location заново в том же сообщении нельзя.

### `stopPoll` — ✅ CLI: `stop-poll`

Останавливает опрос, отправленный ботом. Принимать голоса после остановки невозможно. При успехе возвращает объект Poll с финальными результатами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-подключения, от имени которого было отправлено сообщение с опросом |
| `chat_id` | Integer or String | ✅ | ID чата или @username суперgruппы/канала, где размещён опрос |
| `message_id` | Integer | ✅ | ID сообщения с опросом, который нужно остановить |
| `reply_markup` | InlineKeyboardMarkup | — | Новая inline-клавиатура для сообщения с опросом после остановки |

**Возвращает:** Poll — объект остановленного опроса с финальным распределением голосов

**⚠️ Грабли:** Остановить можно только опрос, отправленный самим ботом; чужие опросы недоступны. В отличие от других методов раздела, chat_id и message_id являются обязательными (нет поддержки inline_message_id). Остановка необратима.


<a name="delete-copy-forward-react"></a>
## Удаление, копирование, пересылка, реакции

### `forwardMessage` — ✅ CLI: `forward`

Пересылает сообщение любого типа из одного чата в другой. Сервисные сообщения и сообщения с защищённым контентом пересылать нельзя; при успехе возвращает отправленное сообщение Message.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID целевого чата или @username |
| `message_thread_id` | Integer | — | ID топика форума в супергруппе или в личном чате бота с включённым режимом топиков |
| `direct_messages_topic_id` | Integer | — | ID топика прямых сообщений; обязателен, если сообщение пересылается в чат прямых сообщений |
| `from_chat_id` | Integer or String | ✅ | ID исходного чата, откуда берётся оригинальное сообщение |
| `message_id` | Integer | ✅ | ID сообщения в чате from_chat_id |
| `video_start_timestamp` | Integer | — | Новый стартовый таймкод для пересылаемого видео |
| `disable_notification` | Boolean | — | Отправить без звукового уведомления |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение содержимого |
| `message_effect_id` | String | — | ID эффекта сообщения; только для пересылки в личные чаты |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предложенного поста; только для чатов прямых сообщений |

**Возвращает:** Message

**⚠️ Грабли:** Нельзя переслать сообщения с protect_content, сервисные сообщения и invoice/giveaway; метод пересылает ровно одно сообщение — для массовой пересылки используйте forwardMessages.

### `forwardMessages` — ✅ CLI: `forward-batch`  · _Bot API 7.0_

Пересылает сразу несколько сообщений (до 100) из одного чата в другой за один запрос, сохраняя группировку альбомов. Сообщения, которые нельзя переслать, пропускаются без ошибки.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID целевого чата или @username |
| `message_thread_id` | Integer | — | ID топика форума в супергруппе или в личном чате бота с включённым режимом топиков |
| `direct_messages_topic_id` | Integer | — | ID топика прямых сообщений; обязателен при пересылке в чат прямых сообщений |
| `from_chat_id` | Integer or String | ✅ | ID исходного чата |
| `message_ids` | Array of Integer | ✅ | JSON-список из 1–100 ID сообщений в строго возрастающем порядке |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Запретить пересылку и сохранение содержимого |

**Возвращает:** Array of MessageId

**⚠️ Грабли:** Идентификаторы в message_ids должны быть в строго возрастающем порядке; сообщения с protected content и сервисные сообщения пропускаются без возврата ошибки.

### `copyMessage` — ✅ CLI: `copy`  · _Bot API 5.0_

Копирует сообщение любого типа в другой чат без ссылки на оригинал — аналог forwardMessage, но без плашки «Переслано от». Позволяет заменить подпись к медиа.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID целевого чата или @username |
| `message_thread_id` | Integer | — | ID топика форума или личного чата с топик-режимом |
| `direct_messages_topic_id` | Integer | — | ID топика прямых сообщений; обязателен при отправке в чат прямых сообщений |
| `from_chat_id` | Integer or String | ✅ | ID чата-источника оригинального сообщения |
| `message_id` | Integer | ✅ | ID копируемого сообщения в from_chat_id |
| `video_start_timestamp` | Integer | — | Новый стартовый таймкод для копируемого видео |
| `caption` | String | — | Новая подпись к медиа, 0–1024 символа; если не указана — сохраняется оригинальная |
| `parse_mode` | String | — | Режим форматирования новой подписи (HTML, Markdown и т.д.) |
| `caption_entities` | Array of MessageEntity | — | Специальные сущности для новой подписи вместо parse_mode |
| `show_caption_above_media` | Boolean | — | Показывать подпись над медиа; игнорируется, если новая подпись не задана |
| `disable_notification` | Boolean | — | Без звукового уведомления |
| `protect_content` | Boolean | — | Защитить содержимое от пересылки и сохранения |
| `allow_paid_broadcast` | Boolean | — | Разрешить до 1000 сообщений/сек за 0.1 Stars/сообщение (списывается с баланса бота) |
| `message_effect_id` | String | — | ID эффекта; только для копирования в личные чаты |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры предложенного поста; только для чатов прямых сообщений. Если отправляется как ответ на другой suggested post, тот автоматически отклоняется |
| `reply_parameters` | ReplyParameters | — | Описание сообщения, на которое делается ответ |
| `reply_markup` | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | — | Клавиатура или инструкция по управлению reply keyboard |

**Возвращает:** MessageId

**⚠️ Грабли:** Сервисные сообщения, платные медиа, giveaway, giveaway winners и invoice скопировать нельзя; quiz-опрос можно скопировать только если боту известен correct_option_id — иначе метод вернёт ошибку.

### `copyMessages` — ✅ CLI: `copy-batch`  · _Bot API 7.0_

Копирует несколько сообщений (до 100) за один запрос без ссылки на оригинал, сохраняя группировку альбомов. Недоступные или неподдерживаемые сообщения пропускаются.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID целевого чата или @username |
| `message_thread_id` | Integer | — | ID топика форума или личного чата с топик-режимом |
| `direct_messages_topic_id` | Integer | — | ID топика прямых сообщений; обязателен при отправке в чат прямых сообщений |
| `from_chat_id` | Integer or String | ✅ | ID чата-источника |
| `message_ids` | Array of Integer | ✅ | JSON-список из 1–100 ID в строго возрастающем порядке |
| `disable_notification` | Boolean | — | Без звука |
| `protect_content` | Boolean | — | Защитить скопированные сообщения от пересылки и сохранения |
| `remove_caption` | Boolean | — | Передайте True, чтобы скопировать без подписей |

**Возвращает:** Array of MessageId

**⚠️ Грабли:** Не позволяет задать новую подпись для каждого сообщения по отдельности — используйте copyMessage в цикле если нужно переписать caption; платные медиа, giveaway и invoice копировать нельзя.

### `setMessageReaction` — ✅ CLI: `react`  · _Bot API 7.0_

Устанавливает или убирает реакцию бота на сообщение. Боты-не-премиум могут ставить не более одной реакции на сообщение; платные реакции ботам недоступны.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_id` | Integer | ✅ | ID целевого сообщения; если сообщение входит в медиагруппу, реакция ставится на первое неудалённое сообщение группы |
| `reaction` | Array of ReactionType | — | Список реакций для установки; чтобы убрать все реакции — передайте пустой список |
| `is_big` | Boolean | — | Передайте True для анимации «большой реакции» |

**Возвращает:** True

**⚠️ Грабли:** На некоторые типы сервисных сообщений реагировать нельзя; кастомный emoji можно использовать только если он уже есть на сообщении или явно разрешён администраторами чата.

### `deleteMessage` — ✅ CLI: `delete`

Удаляет одно сообщение в чате с учётом ограничений (возраст, тип, права бота). При успехе возвращает True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_id` | Integer | ✅ | ID сообщения для удаления |

**Возвращает:** True

**⚠️ Грабли:** Сообщение можно удалить только если оно моложе 48 часов; сообщение с dice в личном чате — только если оно старше 24 часов; сервисное сообщение о создании супергруппы, канала или топика форума удалить нельзя. Бот должен иметь соответствующие права: can_delete_messages в супергруппе/канале, can_manage_direct_messages в прямых сообщениях канала.

### `deleteMessages` — ✅ CLI: `delete`  · _Bot API 7.0_

Удаляет до 100 сообщений одновременно в одном чате. Недоступные сообщения пропускаются без ошибки.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username |
| `message_ids` | Array of Integer | ✅ | JSON-список из 1–100 ID сообщений; все должны быть из одного чата. Действуют те же ограничения, что и для deleteMessage |

**Возвращает:** True

**⚠️ Грабли:** Все сообщения должны быть из одного чата (chat_id); метод не сообщает, какие именно сообщения не удалось удалить — они молча пропускаются.

### `deleteMessageReaction` — ✅ CLI: `react-del`  · _Bot API 10.0_

Удаляет реакцию конкретного пользователя или чата на сообщение в группе или супергруппе. Бот должен иметь право can_delete_messages.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID супергруппы или @username |
| `message_id` | Integer | ✅ | ID целевого сообщения |
| `user_id` | Integer | — | ID пользователя, чья реакция удаляется; используется если реакция была добавлена пользователем |
| `actor_chat_id` | Integer | — | ID чата, чья реакция удаляется; используется если реакция была добавлена от имени чата |

**Возвращает:** True

**⚠️ Грабли:** Необходимо передать ровно один из двух параметров: user_id или actor_chat_id — в зависимости от того, кем была добавлена реакция (пользователем или чатом).

### `deleteAllMessageReactions` — ✅ CLI: `react-clear`  · _Bot API 10.0_

Массово удаляет до 10 000 последних реакций, добавленных конкретным пользователем или чатом в группе или супергруппе. Бот должен иметь право can_delete_messages.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID супергруппы или @username |
| `user_id` | Integer | — | ID пользователя, чьи реакции удаляются; используется если реакции добавлены пользователем |
| `actor_chat_id` | Integer | — | ID чата, чьи реакции удаляются; используется если реакции добавлены от имени чата |

**Возвращает:** True

**⚠️ Грабли:** Лимит — 10 000 последних реакций; более старые реакции не затрагиваются. Необходимо передать ровно один из двух параметров: user_id или actor_chat_id.


<a name="members-moderation"></a>
## Участники и модерация

### `banChatMember` — ✅ CLI: `ban`  · _Bot API Bot API 5.0_

Банит пользователя в группе, супергруппе или канале. В супергруппах и каналах забаненный не сможет вернуться самостоятельно — ни по ссылкам, ни иначе — до снятия блокировки.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы/канала |
| `user_id` | Integer | ✅ | Telegram ID блокируемого пользователя |
| `until_date` | Integer | — | Unix-время снятия бана. Если меньше 30 секунд или больше 366 дней от текущего момента — бан считается перманентным. Работает только для супергрупп и каналов |
| `revoke_messages` | Boolean | — | True — удалить все сообщения пользователя из чата. Для супергрупп и каналов всегда True |

**Возвращает:** True при успехе

**⚠️ Грабли:** В обычных группах until_date игнорируется — бан там всегда перманентный. Если пользователь ещё не состоит в чате, он всё равно будет забанен и не сможет вступить.

### `unbanChatMember` — ✅ CLI: `unban`  · _Bot API Bot API 5.0_

Снимает бан с ранее заблокированного пользователя в супергруппе или канале. Пользователь не возвращается автоматически — он должен вступить сам по ссылке.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы/канала |
| `user_id` | Integer | ✅ | Telegram ID пользователя, с которого снимается бан |
| `only_if_banned` | Boolean | — | True — ничего не делать, если пользователь не забанен. Без этого флага текущий участник чата будет удалён из него |

**Возвращает:** True при успехе

**⚠️ Грабли:** Без флага only_if_banned метод удалит пользователя из чата даже если он не был забанен — он гарантирует отсутствие пользователя в чате, а не просто снятие блокировки.

### `restrictChatMember` — ✅ CLI: `restrict`  · _Bot API Bot API 4.0_

Ограничивает права конкретного пользователя в супергруппе: можно запретить отправку сообщений, медиа, стикеров и т.д. Передача True во все поля ChatPermissions снимает все ограничения.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы |
| `user_id` | Integer | ✅ | Telegram ID ограничиваемого пользователя |
| `permissions` | ChatPermissions | ✅ | JSON-объект с новыми правами пользователя. Все поля объекта ChatPermissions: can_send_messages, can_send_audios, can_send_documents, can_send_photos, can_send_videos, can_send_video_notes, can_send_voice_notes, can_send_polls, can_send_other_messages, can_add_web_page_previews, can_react_to_messages, can_change_info, can_invite_users, can_pin_messages, can_manage_topics |
| `use_independent_chat_permissions` | Boolean | — | True — права применяются независимо друг от друга. Без этого флага can_send_other_messages и can_add_web_page_previews подразумевают разрешение отправки всех типов медиа, а can_send_polls подразумевает can_send_messages |
| `until_date` | Integer | — | Unix-время снятия ограничений. Если 0 или не указано — ограничения бессрочны |

**Возвращает:** True при успехе

**⚠️ Грабли:** Метод работает только для супергрупп, не для обычных групп и каналов. При use_independent_chat_permissions=False (по умолчанию) разрешение can_send_messages является «мастер-переключателем»: его запрет автоматически блокирует большинство остальных прав.

### `promoteChatMember` — ✅ CLI: `promote`  · _Bot API Bot API 4.0_

Повышает или понижает пользователя в правах администратора супергруппы или канала. Передача False во все булевы параметры лишает пользователя всех прав администратора.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username канала/супергруппы |
| `user_id` | Integer | ✅ | Telegram ID повышаемого/понижаемого пользователя |
| `is_anonymous` | Boolean | — | True — присутствие администратора в чате скрыто (анонимный admin) |
| `can_manage_chat` | Boolean | — | Доступ к журналу событий, списку бустов, скрытым участникам, отчётам о спаме, игнорирование slow mode, отправка сообщений без оплаты Stars. Минимальное право — подразумевается любым другим правом администратора |
| `can_delete_messages` | Boolean | — | Удаление сообщений других пользователей |
| `can_manage_video_chats` | Boolean | — | Управление видеочатами и голосовыми трансляциями |
| `can_restrict_members` | Boolean | — | Ограничение, бан и разбан участников, доступ к статистике супергруппы. При повышении администраторов каналов для обратной совместимости по умолчанию True |
| `can_promote_members` | Boolean | — | Назначение новых администраторов с подмножеством собственных прав или понижение администраторов, назначенных этим пользователем (прямо или транзитивно) |
| `can_change_info` | Boolean | — | Изменение названия, фото и других настроек чата |
| `can_invite_users` | Boolean | — | Приглашение новых пользователей в чат |
| `can_post_stories` | Boolean | — | Публикация историй от имени чата |
| `can_edit_stories` | Boolean | — | Редактирование историй других пользователей, публикация историй на странице чата, закрепление историй, доступ к архиву историй |
| `can_delete_stories` | Boolean | — | Удаление историй, опубликованных другими пользователями |
| `can_post_messages` | Boolean | — | Публикация сообщений в канале, подтверждение предложенных постов, доступ к статистике канала. Только для каналов |
| `can_edit_messages` | Boolean | — | Редактирование сообщений других пользователей и закрепление сообщений. Только для каналов |
| `can_pin_messages` | Boolean | — | Закрепление сообщений. Только для супергрупп |
| `can_manage_topics` | Boolean | — | Создание, переименование, закрытие и открытие форум-топиков. Только для супергрупп |
| `can_manage_direct_messages` | Boolean | — | Управление личными сообщениями внутри канала и отклонение предложенных постов. Только для каналов |
| `can_manage_tags` | Boolean | — | Редактирование тегов обычных участников. Только для групп и супергрупп |

**Возвращает:** True при успехе

**⚠️ Грабли:** Бот может выдать администратору только те права, которыми сам обладает (нельзя делегировать права, которых нет). Понизить можно только тех администраторов, которых этот бот сам повысил.

### `setChatAdministratorCustomTitle` — ✅ CLI: `set-admin-title`  · _Bot API Bot API 4.7_

Устанавливает кастомное звание администратору супергруппы, которого повысил сам бот. Звание видно рядом с именем пользователя в чате.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы |
| `user_id` | Integer | ✅ | Telegram ID администратора |
| `custom_title` | String | ✅ | Новое звание; от 0 до 16 символов, эмодзи запрещены. Пустая строка снимает звание |

**Возвращает:** True при успехе

**⚠️ Грабли:** Работает только с администраторами, которых повысил именно этот бот. Для администраторов, назначенных через клиент Telegram или другим ботом, метод вернёт ошибку. Эмодзи в тексте звания не поддерживаются.

### `banChatSenderChat` — ✅ CLI: `ban-channel`  · _Bot API Bot API 5.6_

Банит канал-чат в супергруппе или канале. После бана владелец заблокированного канала не сможет отправлять сообщения от имени любого из своих каналов в данном чате.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username целевой супергруппы/канала, куда вводится блокировка |
| `sender_chat_id` | Integer | ✅ | ID канала, который блокируется как отправитель |

**Возвращает:** True при успехе

**⚠️ Грабли:** Бан распространяется на весь аккаунт владельца: он не сможет писать от имени НИ ОДНОГО из своих каналов в этот чат, а не только от заблокированного. Бан бессрочный — снимается только через unbanChatSenderChat.

### `unbanChatSenderChat` — ✅ CLI: `unban-channel`  · _Bot API Bot API 5.6_

Снимает бан с ранее заблокированного канала-отправителя в супергруппе или канале. После разбана владелец снова сможет писать от имени своих каналов.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username целевой супергруппы/канала |
| `sender_chat_id` | Integer | ✅ | ID ранее заблокированного канала-отправителя |

**Возвращает:** True при успехе

**⚠️ Грабли:** Метод снимает именно блокировку отправителя-канала; не влияет на обычный бан пользователя-владельца (если таковой был наложен отдельно).

### `setChatPermissions` — ✅ CLI: `perms`  · _Bot API Bot API 4.4_

Устанавливает права по умолчанию для всех участников группы или супергруппы. Применяется как «потолок» прав для всех незаблокированных участников.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы |
| `permissions` | ChatPermissions | ✅ | JSON-объект с новыми правами по умолчанию для всех участников. Поля ChatPermissions: can_send_messages, can_send_audios, can_send_documents, can_send_photos, can_send_videos, can_send_video_notes, can_send_voice_notes, can_send_polls, can_send_other_messages, can_add_web_page_previews, can_react_to_messages, can_change_info, can_invite_users, can_pin_messages, can_manage_topics |
| `use_independent_chat_permissions` | Boolean | — | True — права устанавливаются независимо. Без флага can_send_other_messages и can_add_web_page_previews подразумевают разрешение всех типов медиа; can_send_polls подразумевает can_send_messages |

**Возвращает:** True при успехе

**⚠️ Грабли:** Метод задаёт только права по умолчанию — индивидуальные ограничения, наложенные через restrictChatMember, не снимаются. Работает только для групп и супергрупп, не для каналов.

### `setChatMemberTag` — ✅ CLI: `set-member-tag`  · _Bot API Bot API 10.0_

Устанавливает кастомный тег обычному участнику группы или супергруппы. Тег отображается рядом с именем участника аналогично тому, как у администраторов отображается звание.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username супергруппы |
| `user_id` | Integer | ✅ | Telegram ID участника, которому устанавливается тег |
| `tag` | String | — | Новый тег участника; от 0 до 16 символов, эмодзи запрещены. Пустая строка или отсутствие параметра снимает тег |

**Возвращает:** True при успехе

**⚠️ Грабли:** Бот должен обладать правом can_manage_tags (выдаётся через promoteChatMember). Тег можно ставить только обычным участникам, не администраторам — у тех своё поле custom_title.


<a name="invites-joinrequests"></a>
## Инвайт-ссылки и заявки

### `exportChatInviteLink` — ✅ CLI: `invite-export`  · _Bot API 5.5_

Генерирует новую основную (primary) инвайт-ссылку для чата; при этом любая ранее сгенерированная основная ссылка автоматически отзывается. Бот должен быть администратором с соответствующими правами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |

**Возвращает:** String — новая инвайт-ссылка

**⚠️ Грабли:** Каждый администратор генерирует свои личные инвайт-ссылки — бот не может использовать ссылки, созданные другими администраторами. Каждый вызов отзывает предыдущую primary-ссылку бота и создаёт новую; если нужно просто получить текущую ссылку — используй getChat, а не exportChatInviteLink.

### `createChatInviteLink` — ✅ CLI: `invite-create`  · _Bot API 5.5_

Создаёт дополнительную (non-primary) инвайт-ссылку для чата с возможностью задать срок действия, лимит участников или режим одобрения заявок. Возвращает объект ChatInviteLink.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |
| `name` | String | — | Название ссылки; от 0 до 32 символов |
| `expire_date` | Integer | — | Unix-timestamp момента истечения ссылки |
| `member_limit` | Integer | — | Максимальное количество одновременных участников чата, которые могут вступить по этой ссылке; от 1 до 99999. Нельзя использовать вместе с creates_join_request |
| `creates_join_request` | Boolean | — | Если True — вступающие по ссылке должны быть одобрены администраторами. Несовместимо с member_limit |

**Возвращает:** ChatInviteLink — объект новой инвайт-ссылки

**⚠️ Грабли:** Параметры member_limit и creates_join_request взаимоисключающие — нельзя задать оба одновременно, иначе вернётся ошибка.

### `editChatInviteLink` — ✅ CLI: `invite-edit`  · _Bot API 5.5_

Редактирует non-primary инвайт-ссылку, созданную ботом: можно изменить название, срок действия, лимит участников или режим одобрения заявок. Возвращает обновлённый объект ChatInviteLink.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |
| `invite_link` | String | ✅ | Редактируемая инвайт-ссылка |
| `name` | String | — | Новое название ссылки; от 0 до 32 символов |
| `expire_date` | Integer | — | Unix-timestamp нового момента истечения ссылки |
| `member_limit` | Integer | — | Новый максимум одновременных участников чата; от 1 до 99999. Нельзя использовать вместе с creates_join_request |
| `creates_join_request` | Boolean | — | Если True — вступающие должны быть одобрены администраторами. Несовместимо с member_limit |

**Возвращает:** ChatInviteLink — объект отредактированной ссылки

**⚠️ Грабли:** Метод работает только с non-primary ссылками, созданными самим ботом — нельзя редактировать primary-ссылку или ссылки, созданные другими администраторами. Попытка редактировать чужую ссылку вернёт ошибку.

### `revokeChatInviteLink` — ✅ CLI: `invite-revoke`  · _Bot API 5.5_

Отзывает инвайт-ссылку, созданную ботом. Если отзывается primary-ссылка — автоматически генерируется новая. Возвращает объект ChatInviteLink с информацией об отозванной ссылке.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |
| `invite_link` | String | ✅ | Отзываемая инвайт-ссылка |

**Возвращает:** ChatInviteLink — объект отозванной ссылки

**⚠️ Грабли:** После отзыва ссылка перестаёт работать немедленно, но объект ChatInviteLink для неё по-прежнему возвращается (с полем is_revoked: true). Отозвать можно только ссылку, созданную самим ботом.

### `createChatSubscriptionInviteLink` — ✅ CLI: `sub-invite-create`  · _Bot API 7.9_

Создаёт инвайт-ссылку с платной подпиской (Telegram Stars) для канала. Пользователь, вступивший по такой ссылке, регулярно списывает звёзды для сохранения членства. Возвращает объект ChatInviteLink.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор целевого канала или его username в формате @username; только каналы (channel), не группы |
| `name` | String | — | Название ссылки; от 0 до 32 символов |
| `subscription_period` | Integer | ✅ | Период подписки в секундах. В настоящее время единственное допустимое значение — 2592000 (ровно 30 дней) |
| `subscription_price` | Integer | ✅ | Стоимость подписки в Telegram Stars за один период; от 1 до 10000 |

**Возвращает:** ChatInviteLink — объект новой подписочной ссылки

**⚠️ Грабли:** Работает только для каналов (channel), не для групп. Период подписки на данный момент жёстко зафиксирован на 2592000 секунд (30 дней) — передача любого другого значения вернёт ошибку. Изменить цену уже созданной подписочной ссылки нельзя — только название.

### `editChatSubscriptionInviteLink` — ✅ CLI: `sub-invite-edit`  · _Bot API 7.9_

Редактирует подписочную инвайт-ссылку, созданную ботом. Единственный редактируемый параметр — название ссылки; цена и период подписки изменить нельзя. Возвращает объект ChatInviteLink.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |
| `invite_link` | String | ✅ | Редактируемая подписочная инвайт-ссылка |
| `name` | String | — | Новое название ссылки; от 0 до 32 символов |

**Возвращает:** ChatInviteLink — объект отредактированной подписочной ссылки

**⚠️ Грабли:** В отличие от editChatInviteLink, у подписочной ссылки можно изменить только название — subscription_price и subscription_period не редактируются. Попытка передать expire_date или member_limit вернёт ошибку.

### `approveChatJoinRequest` — ✅ CLI: `join-approve`  · _Bot API 5.5_

Одобряет заявку пользователя на вступление в чат, если чат использует режим одобрения заявок (creates_join_request). Бот должен быть администратором с правом can_invite_users.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |
| `user_id` | Integer | ✅ | Уникальный идентификатор пользователя, заявку которого нужно одобрить |

**Возвращает:** True при успехе

**⚠️ Грабли:** Одобрение заявки отправляет пользователю уведомление и добавляет его в чат. Если заявка уже была одобрена или отклонена другим администратором — метод вернёт ошибку. Требуется именно право can_invite_users, а не произвольные права администратора.

### `declineChatJoinRequest` — ✅ CLI: `join-decline`  · _Bot API 5.5_

Отклоняет заявку пользователя на вступление в чат. Бот должен быть администратором с правом can_invite_users. Пользователь может подать заявку повторно.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или username канала в формате @username |
| `user_id` | Integer | ✅ | Уникальный идентификатор пользователя, заявку которого нужно отклонить |

**Возвращает:** True при успехе

**⚠️ Грабли:** Отклонение не блокирует пользователя — он может подать заявку заново. Если заявка уже была обработана (одобрена или отклонена), метод вернёт ошибку. Нет параметра для отправки пользователю причины отказа.


<a name="chat-info-properties"></a>
## Свойства и информация чата

### `setChatPhoto` — ✅ CLI: `set-photo`  · _Bot API Bot API 1.0_

Устанавливает новую фотографию профиля для чата. Не работает для приватных чатов; бот должен быть администратором с соответствующими правами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |
| `photo` | InputFile | ✅ | Новое фото чата; передаётся через multipart/form-data |

**Возвращает:** True on success

**⚠️ Грабли:** Метод не работает для приватных чатов — попытка вернёт ошибку. Требуется именно право на изменение информации о чате (can_change_info).

### `deleteChatPhoto` — ✅ CLI: `del-photo`  · _Bot API Bot API 1.0_

Удаляет текущую фотографию чата. Не работает для приватных чатов; бот должен быть администратором с соответствующими правами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |

**Возвращает:** True on success

**⚠️ Грабли:** Как и setChatPhoto, не применим к приватным чатам. Если фото и так не установлено, метод вернёт ошибку.

### `setChatTitle` — ✅ CLI: `set-title`  · _Bot API Bot API 1.0_

Изменяет название чата (группы, супергруппы или канала). Не работает для приватных чатов; бот должен быть администратором с соответствующими правами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |
| `title` | String | ✅ | Новое название чата, от 1 до 128 символов |

**Возвращает:** True on success

**⚠️ Грабли:** Не работает для приватных чатов. Название не может быть пустой строкой — минимум 1 символ.

### `setChatDescription` — ✅ CLI: `set-desc`  · _Bot API Bot API 3.0_

Изменяет описание группы, супергруппы или канала. Бот должен быть администратором с соответствующими правами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |
| `description` | String | — | Новое описание, от 0 до 255 символов. Если не передано или пустая строка — описание сбрасывается. |

**Возвращает:** True on success

**⚠️ Грабли:** Параметр description помечен Optional: передача пустой строки или его отсутствие очищает описание чата, а не вызывает ошибку.

### `pinChatMessage` — ✅ CLI: `pin`  · _Bot API Bot API 2.0_

Закрепляет сообщение в чате. В личных чатах и direct-сообщениях каналов можно закрепить любое несервисное сообщение; в группах и каналах требуются права администратора.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | Идентификатор бизнес-соединения; если указан, закрепление выполняется от имени бизнес-аккаунта |
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |
| `message_id` | Integer | ✅ | Идентификатор закрепляемого сообщения |
| `disable_notification` | Boolean | — | Передайте True, чтобы не уведомлять участников. В каналах и приватных чатах уведомление всегда отключено. |

**Возвращает:** True on success

**⚠️ Грабли:** В группах нужно право can_pin_messages, в каналах — can_edit_messages. Закрепить сервисное сообщение нельзя даже в личном чате.

### `unpinChatMessage` — ✅ CLI: `unpin`  · _Bot API Bot API 2.0_

Снимает закрепление сообщения в чате. Если message_id не указан — снимается самое последнее по дате закреплённое сообщение.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | Идентификатор бизнес-соединения; если указан, message_id становится обязательным |
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |
| `message_id` | Integer | — | Идентификатор сообщения для открепления. Обязателен, если передан business_connection_id. Если не указан — открепляется самое последнее закреплённое. |

**Возвращает:** True on success

**⚠️ Грабли:** Если business_connection_id передан, message_id становится фактически обязательным — без него запрос завершится ошибкой. В группах нужно can_pin_messages, в каналах — can_edit_messages.

### `unpinAllChatMessages` — ✅ CLI: `unpin-all`  · _Bot API Bot API 5.0_

Снимает закрепление со всех сообщений в чате. В личных чатах и direct-сообщениях каналов дополнительных прав не требуется; в группах и каналах — нужны права администратора.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |

**Возвращает:** True on success

**⚠️ Грабли:** В группах нужно can_pin_messages, в каналах — can_edit_messages. Метод необратим: восстановить список закреплённых сообщений нельзя.

### `leaveChat` — ✅ CLI: `leave`  · _Bot API Bot API 1.0_

Бот покидает группу, супергруппу или канал.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы/канала. Direct-сообщения канала не поддерживаются — нужно покидать сам канал. |

**Возвращает:** True on success

**⚠️ Грабли:** Direct-сообщения канала (channel direct messages chats) не поддерживаются — передайте chat_id самого канала. После выхода бот не получает обновления из чата.

### `getChat` — ✅ CLI: `link (внутри)`  · _Bot API Bot API 1.0_

Возвращает актуальную информацию о чате в виде объекта ChatFullInfo, включая расширенные поля (описание, количество участников, права по умолчанию и т.д.).


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы/канала |

**Возвращает:** ChatFullInfo object on success

**⚠️ Грабли:** Возвращает ChatFullInfo (расширенный объект), а не Chat. Для приватных чатов часть полей (например, описание или число участников) будет отсутствовать.

### `getChatAdministrators` — ✅ CLI: `admins`  · _Bot API Bot API 1.0_

Возвращает список администраторов чата. По умолчанию боты (кроме самого запрашивающего) из списка исключены; передайте return_bots=True, чтобы включить их.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы/канала |
| `return_bots` | Boolean | — | Передайте True, чтобы получить в ответе также всех ботов-администраторов (кроме текущего бота). Добавлено в Bot API 10.0. |

**Возвращает:** Array of ChatMember objects

**⚠️ Грабли:** Метод не работает для приватных чатов и групп. Текущий бот всегда отсутствует в результате. Параметр return_bots появился только в Bot API 10.0 — до этого боты-администраторы не возвращались.

### `getChatMemberCount` — ✅ CLI: `count`  · _Bot API Bot API 1.0_

Возвращает количество участников чата в виде целого числа.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы/канала |

**Возвращает:** Int on success

**⚠️ Грабли:** Для больших публичных групп/каналов значение может быть приблизительным. Метод ранее назывался getChatMembersCount (с «s»), переименован в 6.3 — устаревшее имя в актуальной документации отсутствует.

### `getChatMember` — ✅ CLI: `member`  · _Bot API Bot API 1.0_

Возвращает информацию об участнике чата в виде объекта ChatMember. Гарантированно работает только если бот является администратором чата.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы/канала |
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя |

**Возвращает:** ChatMember object on success

**⚠️ Грабли:** Метод гарантированно работает только если бот — администратор. Для обычных участников без прав администратора запрос может вернуть ошибку или неполные данные.

### `setChatStickerSet` — ✅ CLI: `set-chat-stickers`  · _Bot API Bot API 3.0_

Устанавливает набор стикеров для супергруппы. Бот должен быть администратором с соответствующими правами; применимо только к супергруппам.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор супергруппы или её @username |
| `sticker_set_name` | String | ✅ | Имя набора стикеров (short name), который будет установлен как групповой |

**Возвращает:** True on success

**⚠️ Грабли:** Работает только для супергрупп — не для обычных групп и не для каналов. Перед вызовом проверьте поле can_set_sticker_set из ответа getChat: если оно False или отсутствует, бот не может применить метод.

### `deleteChatStickerSet` — ✅ CLI: `del-chat-stickers`  · _Bot API Bot API 3.0_

Удаляет ранее установленный набор стикеров супергруппы. Бот должен быть администратором с соответствующими правами.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор супергруппы или её @username |

**Возвращает:** True on success

**⚠️ Грабли:** Как и setChatStickerSet, работает только для супергрупп. Проверяйте can_set_sticker_set из getChat до вызова.

### `getUserChatBoosts` — ✅ CLI: `user-boosts`  · _Bot API Bot API 7.0_

Возвращает список бустов, добавленных конкретным пользователем в чат. Требует прав администратора в чате.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала |
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя |

**Возвращает:** UserChatBoosts object

**⚠️ Грабли:** Метод возвращает UserChatBoosts (объект-обёртку со списком), а не массив напрямую. Работает только для каналов и супергрупп с включёнными бустами; для обычных групп и приватных чатов вернёт ошибку.


<a name="forum-topics"></a>
## Форум-топики

### `getForumTopicIconStickers` — ✅ CLI: `forum-icons`  · _Bot API 6.3_

Возвращает список кастомных эмодзи-стикеров, которые может использовать любой пользователь в качестве иконки топика форума. Параметров не требует.

**Возвращает:** Array of Sticker

**⚠️ Грабли:** Метод не требует аутентификации чата и возвращает единый глобальный список разрешённых эмодзи — он не зависит от конкретного чата или прав бота.

### `createForumTopic` — ✅ CLI: `forum-create`  · _Bot API 6.3_

Создаёт топик в форум-супергруппе или в личном чате бота с пользователем (если у бота включён forum topic mode). В супергруппе бот должен быть администратором с правом can_manage_topics.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `name` | String | ✅ | Название топика, 1–128 символов |
| `icon_color` | Integer | — | Цвет иконки топика в формате RGB. Допустимые значения: 7322096 (0x6FB9F0), 16766590 (0xFFD67E), 13338331 (0xCB86DB), 9367192 (0x8EEE98), 16749490 (0xFF93B2), 16478047 (0xFB6F5F) |
| `icon_custom_emoji_id` | String | — | Идентификатор кастомного эмодзи для иконки топика; допустимые значения получают через getForumTopicIconStickers |

**Возвращает:** ForumTopic

**⚠️ Грабли:** Метод работает в двух принципиально разных контекстах: супергруппа (форум) требует прав администратора, тогда как личный чат бота с пользователем работает без прав, если у бота включён forum topic mode. Набор допустимых icon_color строго фиксирован — любое другое числовое значение вернёт ошибку.

### `editForumTopic` — ✅ CLI: `forum-edit`  · _Bot API 6.3_

Редактирует название и/или иконку существующего топика форума в супергруппе или личном чате бота. Бот должен быть администратором с can_manage_topics, либо являться создателем топика.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `message_thread_id` | Integer | ✅ | Идентификатор треда сообщений (thread) — он же ID топика форума |
| `name` | String | — | Новое название топика, 0–128 символов. Если не передан или пустая строка — текущее название сохраняется |
| `icon_custom_emoji_id` | String | — | Новый идентификатор кастомного эмодзи иконки. Передайте пустую строку, чтобы удалить иконку. Если не передан — текущая иконка сохраняется |

**Возвращает:** True

**⚠️ Грабли:** Обратите внимание: в editForumTopic нельзя изменить icon_color — только кастомный эмодзи. Чтобы убрать иконку, нужно передать icon_custom_emoji_id как пустую строку ""; если параметр вовсе не передан, иконка не тронется.

### `closeForumTopic` — ✅ CLI: `forum-close`  · _Bot API 6.3_

Закрывает открытый топик форума в супергруппе. Бот должен быть администратором с can_manage_topics, либо являться создателем топика.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `message_thread_id` | Integer | ✅ | Идентификатор треда (ID топика форума) |

**Возвращает:** True

**⚠️ Грабли:** Вызов на уже закрытом топике не вернёт ошибку — Telegram обрабатывает это идемпотентно.

### `reopenForumTopic` — ✅ CLI: `forum-reopen`  · _Bot API 6.3_

Открывает закрытый топик форума в супергруппе. Бот должен быть администратором с can_manage_topics, либо являться создателем топика.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `message_thread_id` | Integer | ✅ | Идентификатор треда (ID топика форума) |

**Возвращает:** True

**⚠️ Грабли:** Нельзя переоткрыть скрытый General-топик через этот метод — для него используется reopenGeneralForumTopic, который дополнительно автоматически делает его видимым.

### `deleteForumTopic` — ✅ CLI: `forum-delete`  · _Bot API 6.3_

Удаляет топик форума вместе со всеми его сообщениями в супергруппе или личном чате бота. В супергруппе требует права администратора can_delete_messages.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `message_thread_id` | Integer | ✅ | Идентификатор треда (ID топика форума) |

**Возвращает:** True

**⚠️ Грабли:** Операция необратима: удаляются абсолютно все сообщения топика. Требуется can_delete_messages, а не can_manage_topics — это отличает её от остальных методов управления топиками.

### `unpinAllForumTopicMessages` — ✅ CLI: `forum-unpin-all`  · _Bot API 6.3_

Снимает закрепление со всех закреплённых сообщений в указанном топике форума. В супергруппе бот должен быть администратором с правом can_pin_messages.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `message_thread_id` | Integer | ✅ | Идентификатор треда (ID топика форума) |

**Возвращает:** True

**⚠️ Грабли:** Требует can_pin_messages, а не can_manage_topics. Снимает закрепление сразу со всех сообщений топика — нет возможности сделать это выборочно через этот метод.

### `editGeneralForumTopic` — ✅ CLI: `gen-edit`  · _Bot API 6.3_

Изменяет название топика «General» в форум-супергруппе. Бот должен быть администратором с правом can_manage_topics.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |
| `name` | String | ✅ | Новое название General-топика, 1–128 символов |

**Возвращает:** True

**⚠️ Грабли:** У General-топика нельзя изменить иконку или цвет — только название. В отличие от editForumTopic, параметр name здесь обязателен.

### `closeGeneralForumTopic` — ✅ CLI: `gen-close`  · _Bot API 6.3_

Закрывает открытый топик «General» в форум-супергруппе. Бот должен быть администратором с правом can_manage_topics.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |

**Возвращает:** True

**⚠️ Грабли:** General-топик не имеет message_thread_id — его не нужно передавать. Закрытие General не скрывает его; для скрытия используется hideGeneralForumTopic.

### `reopenGeneralForumTopic` — ✅ CLI: `gen-reopen`  · _Bot API 6.3_

Открывает закрытый топик «General» в форум-супергруппе. Если топик был скрыт, он автоматически становится видимым. Бот должен быть администратором с can_manage_topics.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |

**Возвращает:** True

**⚠️ Грабли:** Метод автоматически делает топик видимым, если тот был скрыт — то есть он неявно выполняет и unhide. Это единственный способ одновременно и открыть, и показать General-топик одним вызовом.

### `hideGeneralForumTopic` — ✅ CLI: `gen-hide`  · _Bot API 6.3_

Скрывает топик «General» в форум-супергруппе из списка топиков. Если топик был открыт, он автоматически закрывается. Бот должен быть администратором с can_manage_topics.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |

**Возвращает:** True

**⚠️ Грабли:** Скрытие автоматически закрывает General-топик, если он был открыт — два побочных эффекта одним вызовом. Скрыть можно только General; обычные топики скрыть через API нельзя.

### `unhideGeneralForumTopic` — ✅ CLI: `gen-unhide`  · _Bot API 6.3_

Делает скрытый топик «General» видимым в форум-супергруппе. Бот должен быть администратором с can_manage_topics.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username супергруппы |

**Возвращает:** True

**⚠️ Грабли:** unhideGeneralForumTopic только показывает топик, но не открывает его — если General был закрыт до скрытия, он останется закрытым. Чтобы одновременно показать и открыть — используйте reopenGeneralForumTopic.


<a name="bot-config-profile"></a>
## Конфигурация и профиль бота

### `getMe` — ✅ CLI: `me`  · _Bot API Bot API 1.0_

Простой метод для проверки токена авторизации бота. Возвращает базовую информацию о боте в виде объекта User.

**Возвращает:** User

**⚠️ Грабли:** Поля объекта User для бота отличаются от пользовательских: всегда заполнены username, is_bot=true; дополнительно возвращаются can_join_groups, can_read_all_group_messages, supports_inline_queries, can_connect_to_business, has_main_web_app.

### `logOut` — ✅ CLI: `logout`  · _Bot API Bot API 5.0_

Выполняет выход бота из облачного сервера Bot API — обязательный шаг перед запуском бота на локальном сервере Bot API. После успешного вызова можно немедленно войти на локальный сервер.

**Возвращает:** True

**⚠️ Грабли:** После вызова повторный вход на облачный Bot API будет заблокирован на 10 минут. Если бот уже работает локально и вы вызываете этот метод, нет гарантии что он продолжит получать обновления.

### `close` — ✅ CLI: `close-bot`  · _Bot API Bot API 5.0_

Закрывает экземпляр бота на локальном сервере перед его переносом на другой локальный сервер. Перед вызовом необходимо удалить webhook.

**Возвращает:** True

**⚠️ Грабли:** Метод возвращает ошибку 429 (Too Many Requests) в течение первых 10 минут после запуска бота. Также перед вызовом необходимо удалить webhook (deleteWebhook), иначе бот может быть автоматически перезапущен после рестарта сервера.

### `setMyCommands` — ✅ CLI: `set-commands`  · _Bot API Bot API 3.3_

Устанавливает список команд бота для заданного scope и языка. Позволяет настраивать разные наборы команд для разных аудиторий (личка, группы, администраторы и т.д.).


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `commands` | Array of BotCommand | ✅ | JSON-сериализованный список команд. Каждый BotCommand содержит поля command (String, 1-32 символа, только строчные латинские буквы, цифры и подчёркивания) и description (String, 1-256 символов). Максимум 100 команд. |
| `scope` | BotCommandScope | — | JSON-сериализованный объект, описывающий область пользователей, для которых актуальны команды. По умолчанию BotCommandScopeDefault. Типы: BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats, BotCommandScopeAllChatAdministrators, BotCommandScopeChat (требует chat_id), BotCommandScopeChatAdministrators (требует chat_id), BotCommandScopeChatMember (требует chat_id и user_id). |
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1. Если пустой — команды применяются ко всем пользователям в рамках указанного scope, для которых не задан специфический набор команд по языку. |

**Возвращает:** True

**⚠️ Грабли:** Scope и language_code образуют составной ключ: команды с более узким scope перекрывают более широкие. Если задать команды только для scope=chat без language_code, они применятся ко всем языкам именно в этом чате, перекрыв глобальные настройки.

### `deleteMyCommands` — ✅ CLI: `del-commands`  · _Bot API Bot API 5.3_

Удаляет список команд бота для заданного scope и языка. После удаления для затронутых пользователей будут отображаться команды из более широкого scope (согласно иерархии).


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `scope` | BotCommandScope | — | JSON-сериализованный объект, описывающий scope. По умолчанию BotCommandScopeDefault. |
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1. Если пустой — удаляются команды для всех пользователей указанного scope без специфического языкового набора. |

**Возвращает:** True

**⚠️ Грабли:** Удаление команд для конкретного scope не затрагивает команды в других scope. Если нужно полностью убрать все команды — необходимо вызвать метод последовательно для каждого scope, который был установлен.

### `getMyCommands` — ✅ CLI: `get-commands`  · _Bot API Bot API 3.3_

Возвращает текущий список команд бота для заданного scope и языка пользователя. Если команды не установлены — возвращает пустой массив.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `scope` | BotCommandScope | — | JSON-сериализованный объект scope. По умолчанию BotCommandScopeDefault. |
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1 или пустая строка. |

**Возвращает:** Array of BotCommand

**⚠️ Грабли:** Метод возвращает команды строго для указанной комбинации scope+language_code. Чтобы получить «реально отображаемые» команды для конкретного пользователя, нужно самостоятельно обойти иерархию scope от наиболее узкого к широкому.

### `setMyName` — ✅ CLI: `set-name`  · _Bot API Bot API 6.7_

Изменяет отображаемое имя бота. Поддерживает локализацию: можно задать разные имена для разных языков пользователей.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `name` | String | — | Новое имя бота, 0-64 символа. Передайте пустую строку, чтобы удалить специализированное имя для данного языка и откатиться к имени по умолчанию. |
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1. Если пустой — имя будет показано всем пользователям, для языка которых не задано специфическое имя. |

**Возвращает:** True

**⚠️ Грабли:** Изменение имени через API не мгновенно отражается в интерфейсе Telegram у всех пользователей — возможно кэширование на стороне клиента. Изменение видно в BotFather-профиле сразу.

### `getMyName` — ✅ CLI: `get-name`  · _Bot API Bot API 6.7_

Возвращает текущее имя бота для заданного языка пользователя в виде объекта BotName.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1 или пустая строка (вернёт имя по умолчанию). |

**Возвращает:** BotName

### `setMyDescription` — ✅ CLI: `set-bot-desc`  · _Bot API Bot API 6.7_

Изменяет описание бота, которое отображается в чате с ботом, когда чат пуст. Поддерживает локализацию по языку пользователя.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `description` | String | — | Новое описание бота, 0-512 символов. Передайте пустую строку, чтобы удалить специализированное описание для данного языка. |
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1. Если пустой — описание применяется ко всем пользователям, для языка которых не задано специфическое описание. |

**Возвращает:** True

**⚠️ Грабли:** description (setMyDescription) и short_description (setMyShortDescription) — разные поля. Description показывается только при первом открытии пустого чата; short_description — на странице профиля бота и при шаринге ссылки.

### `getMyDescription` — ✅ CLI: `get-bot-desc`  · _Bot API Bot API 6.7_

Возвращает текущее описание бота для заданного языка пользователя в виде объекта BotDescription.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1 или пустая строка (вернёт описание по умолчанию). |

**Возвращает:** BotDescription

### `setMyShortDescription` — ✅ CLI: `set-bot-short`  · _Bot API Bot API 6.7_

Изменяет краткое описание бота, которое отображается на странице профиля бота и отправляется вместе со ссылкой при шаринге бота пользователями.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `short_description` | String | — | Новое краткое описание, 0-120 символов. Передайте пустую строку, чтобы удалить специализированное краткое описание для данного языка. |
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1. Если пустой — краткое описание применяется ко всем пользователям, для языка которых не задано специфическое. |

**Возвращает:** True

### `getMyShortDescription` — ✅ CLI: `get-bot-short`  · _Bot API Bot API 6.7_

Возвращает текущее краткое описание бота для заданного языка пользователя в виде объекта BotShortDescription.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `language_code` | String | — | Двухбуквенный код языка ISO 639-1 или пустая строка (вернёт краткое описание по умолчанию). |

**Возвращает:** BotShortDescription

### `setChatMenuButton` — ✅ CLI: `menu-button`  · _Bot API Bot API 6.0_

Изменяет кнопку меню бота в конкретном приватном чате или дефолтную кнопку меню для всех приватных чатов. Позволяет настроить MenuButtonCommands, MenuButtonWebApp или MenuButtonDefault.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer | — | Уникальный идентификатор целевого приватного чата. Если не указан — изменяется дефолтная кнопка меню бота. |
| `menu_button` | MenuButton | — | JSON-сериализованный объект кнопки меню. Один из: MenuButtonCommands (type='commands', открывает список команд), MenuButtonWebApp (type='web_app', требует text и web_app:WebAppInfo), MenuButtonDefault (type='default', сбрасывает к поведению по умолчанию). Если не указан — устанавливается MenuButtonDefault. |

**Возвращает:** True

**⚠️ Грабли:** Работает только для приватных чатов (chat_id должен быть ID приватного чата). Передача group/supergroup/channel chat_id вернёт ошибку. При использовании MenuButtonWebApp Web App сможет отправлять произвольные сообщения от имени пользователя через answerWebAppQuery.

### `getChatMenuButton` — ✅ CLI: `get-menu-button`  · _Bot API Bot API 6.0_

Возвращает текущее значение кнопки меню бота для конкретного приватного чата или дефолтную кнопку меню.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer | — | Уникальный идентификатор целевого приватного чата. Если не указан — возвращается дефолтная кнопка меню бота. |

**Возвращает:** MenuButton

### `setMyDefaultAdministratorRights` — ✅ CLI: `set-default-rights`  · _Bot API Bot API 5.3_

Изменяет права администратора по умолчанию, запрашиваемые ботом при добавлении в группы или каналы. Эти права предлагаются пользователям, но они могут их изменить перед добавлением.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `rights` | ChatAdministratorRights | — | JSON-сериализованный объект с новыми дефолтными правами администратора. Если не указан — дефолтные права очищаются. Объект включает поля: is_anonymous, can_manage_chat, can_delete_messages, can_manage_video_chats, can_restrict_members, can_promote_members, can_change_info, can_invite_users, can_post_stories, can_edit_stories, can_delete_stories, и опциональные can_post_messages, can_edit_messages, can_pin_messages, can_manage_topics, can_manage_direct_messages, can_manage_tags. |
| `for_channels` | Boolean | — | Передайте True, чтобы изменить дефолтные права администратора бота в каналах. Иначе изменяются права для групп и супергрупп. |

**Возвращает:** True

**⚠️ Грабли:** Права для каналов и для групп/супергрупп хранятся и устанавливаются отдельно — параметр for_channels разграничивает их. Установленные права лишь предлагаются пользователю при добавлении бота, принятие не гарантировано.

### `getMyDefaultAdministratorRights` — ✅ CLI: `get-default-rights`  · _Bot API Bot API 5.3_

Возвращает текущие дефолтные права администратора бота для групп/супергрупп или каналов в виде объекта ChatAdministratorRights.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `for_channels` | Boolean | — | Передайте True, чтобы получить дефолтные права для каналов. Иначе возвращаются права для групп и супергрупп. |

**Возвращает:** ChatAdministratorRights

### `setMyProfilePhoto` — ✅ CLI: `set-bot-photo`  · _Bot API Bot API 7.3_

Изменяет фото профиля бота. Принимает статическое (JPG) или анимированное (MPEG4) фото через объект InputProfilePhoto.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `photo` | InputProfilePhoto | ✅ | Новое фото профиля. Один из двух подтипов: InputProfilePhotoStatic (type='static', поле photo — файл JPG, только новая загрузка через attach://<name>) или InputProfilePhotoAnimated (type='animated', поле animation — файл MPEG4, только новая загрузка; опционально main_frame_timestamp Float — таймстемп кадра для статичного превью, по умолчанию 0.0). Фото профиля нельзя переиспользовать через file_id — только загрузка нового файла. |

**Возвращает:** True

**⚠️ Грабли:** Фотографии профиля нельзя переиспользовать через file_id (в отличие от обычных медиа). Файл нужно загружать заново каждый раз через multipart/form-data с attach://<file_attach_name>.

### `removeMyProfilePhoto` — ✅ CLI: `del-bot-photo`  · _Bot API Bot API 7.3_

Удаляет текущее фото профиля бота. Параметры не требуются.

**Возвращает:** True

**⚠️ Грабли:** Удаляет только текущее (последнее) фото профиля. Если у бота несколько фотографий профиля в истории, предыдущие не затрагиваются и могут остаться видимыми в истории фотографий.


<a name="files-inline-callback"></a>
## Файлы, inline, callback

### `getFile` — ✅ CLI: `get-file`

Получает базовую информацию о файле и готовит его к загрузке (боты могут скачивать файлы размером до 20 МБ). При успехе возвращает объект File, из которого формируется прямая ссылка для скачивания.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `file_id` | String | ✅ | Идентификатор файла, информацию о котором нужно получить |

**Возвращает:** File

**⚠️ Грабли:** Метод не гарантирует сохранение оригинального имени файла и MIME-типа — их следует сохранять самостоятельно в момент получения объекта File. Ссылка на скачивание действительна минимум 1 час, после чего нужно снова вызвать getFile.

### `getUserProfilePhotos` — ✅ CLI: `user-photos`

Возвращает список фотографий профиля пользователя в виде объекта UserProfilePhotos. Поддерживает постраничную навигацию через offset.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя |
| `offset` | Integer | — | Порядковый номер первой возвращаемой фотографии; по умолчанию возвращаются все фото |
| `limit` | Integer | — | Ограничение количества возвращаемых фото; допустимые значения 1–100, по умолчанию 100 |

**Возвращает:** UserProfilePhotos

### `getUserProfileAudios` — ✅ CLI: `user-audios`  · _Bot API 9.5_

Возвращает список аудиозаписей профиля пользователя в виде объекта UserProfileAudios. Метод симметричен getUserProfilePhotos, но работает с аудио-профилями, появившимися в Bot API 9.5.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя |
| `offset` | Integer | — | Порядковый номер первого возвращаемого аудио; по умолчанию возвращаются все аудио |
| `limit` | Integer | — | Ограничение количества возвращаемых аудио; допустимые значения 1–100, по умолчанию 100 |

**Возвращает:** UserProfileAudios

### `answerCallbackQuery` — ✅ CLI: `listen (внутри)`  · _Bot API 2.3_

Отправляет ответ на callback-запрос, полученный от inline-клавиатуры; результат отображается пользователю как уведомление вверху экрана или как alert. При успехе возвращает True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `callback_query_id` | String | ✅ | Уникальный идентификатор запроса, на который даётся ответ |
| `text` | String | — | Текст уведомления (0–200 символов); если не указан, уведомление не показывается |
| `show_alert` | Boolean | — | Если True — клиент отображает alert вместо уведомления вверху экрана; по умолчанию false |
| `url` | String | — | URL, который откроет клиент пользователя; для игровых кнопок (callback_game) — URL игры через @BotFather; для обычных кнопок можно использовать t.me/your_bot?start=XXXX |
| `cache_time` | Integer | — | Максимальное время в секундах, в течение которого результат запроса может кэшироваться на стороне клиента; по умолчанию 0 |

**Возвращает:** True

**⚠️ Грабли:** Telegram-клиенты показывают индикатор загрузки до получения ответа, поэтому answerCallbackQuery нужно вызывать всегда — даже если никакого уведомления пользователю не нужно. cache_time поддерживается только начиная с Telegram 3.14+.

### `answerInlineQuery` — ✅ CLI: `answer-inline`  · _Bot API 6.7_

Отправляет ответ на inline-запрос (InlineQuery) с массивом результатов. При успехе возвращает True. Ограничение: не более 50 результатов на один запрос.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `inline_query_id` | String | ✅ | Уникальный идентификатор отвечаемого inline-запроса |
| `results` | Array of InlineQueryResult | ✅ | JSON-сериализованный массив результатов; максимум 50 элементов |
| `cache_time` | Integer | — | Максимальное время в секундах кэширования результатов на сервере Telegram; по умолчанию 300 |
| `is_personal` | Boolean | — | Если True — результаты кэшируются только для конкретного пользователя; по умолчанию false (кэш общий) |
| `next_offset` | String | — | Смещение для следующей страницы результатов; пустая строка означает, что результатов больше нет; максимум 64 байта |
| `button` | InlineQueryResultsButton | — | JSON-сериализованный объект, описывающий кнопку, отображаемую над результатами inline-запроса (появился в Bot API 6.7, заменил параметры switch_pm_text/switch_pm_parameter) |

**Возвращает:** True

**⚠️ Грабли:** Параметры switch_pm_text и switch_pm_parameter устарели начиная с Bot API 6.7 и заменены параметром button типа InlineQueryResultsButton — не использовать оба способа одновременно.

### `answerWebAppQuery` — ✅ CLI: `answer-webapp`  · _Bot API 6.0_

Устанавливает результат взаимодействия с Web App и отправляет соответствующее сообщение от имени пользователя в чат, из которого пришёл запрос. При успехе возвращает объект SentWebAppMessage.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `web_app_query_id` | String | ✅ | Уникальный идентификатор запроса Web App, на который даётся ответ |
| `result` | InlineQueryResult | ✅ | JSON-сериализованный объект, описывающий сообщение для отправки |

**Возвращает:** SentWebAppMessage

**⚠️ Грабли:** Работает только в приватных чатах между пользователем и ботом; не поддерживается для сообщений, отправленных от имени бизнес-аккаунта.

### `savePreparedInlineMessage` — ✅ CLI: `prep-inline`  · _Bot API 8.0_

Сохраняет сообщение, которое пользователь Mini App сможет впоследствии отправить в выбранный чат через метод shareMessage объекта WebApp. Возвращает объект PreparedInlineMessage.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя, который сможет использовать подготовленное сообщение |
| `result` | InlineQueryResult | ✅ | JSON-сериализованный объект, описывающий сообщение для отправки |
| `allow_user_chats` | Boolean | — | Передайте True, если сообщение можно отправить в приватные чаты с пользователями |
| `allow_bot_chats` | Boolean | — | Передайте True, если сообщение можно отправить в приватные чаты с ботами |
| `allow_group_chats` | Boolean | — | Передайте True, если сообщение можно отправить в группы и супергруппы |
| `allow_channel_chats` | Boolean | — | Передайте True, если сообщение можно отправить в каналы |

**Возвращает:** PreparedInlineMessage

**⚠️ Грабли:** Ни один из параметров allow_* не является обязательным, но если не передан ни один из них, пользователь не сможет выбрать ни один чат для отправки — сообщение окажется бесполезным.

### `savePreparedKeyboardButton` — ✅ CLI: `save-kbd-button`  · _Bot API 9.6_

Сохраняет кнопку клавиатуры, которую пользователь Mini App сможет использовать для запроса данных о пользователях, чатах или управляемых ботах. Возвращает объект PreparedKeyboardButton.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя, который сможет использовать кнопку |
| `button` | KeyboardButton | ✅ | JSON-сериализованный объект кнопки; кнопка должна быть одного из трёх типов: request_users, request_chat или request_managed_bot — другие типы не поддерживаются |

**Возвращает:** PreparedKeyboardButton

**⚠️ Грабли:** Принимаются только кнопки типов request_users, request_chat или request_managed_bot — попытка передать кнопку другого типа приведёт к ошибке.


<a name="payments-stars"></a>
## Платежи и Telegram Stars

### `sendInvoice` — ✅ CLI: `invoice`  · _Bot API Bot API 2.0_

Отправляет инвойс (счёт на оплату) пользователю или в чат. При успехе возвращает отправленное сообщение Message.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | ID чата или @username группы/канала, которому отправляется инвойс |
| `message_thread_id` | Integer | — | ID треда (топика) форума для форум-супергрупп и личных чатов с включённым режимом тем |
| `direct_messages_topic_id` | Integer | — | ID топика в чате прямых сообщений; обязателен при отправке в direct messages chat |
| `title` | String | ✅ | Название продукта, 1–32 символа |
| `description` | String | ✅ | Описание продукта, 1–255 символов |
| `payload` | String | ✅ | Внутренний payload для бота, 1–128 байт; пользователю не отображается |
| `provider_token` | String | — | Токен платёжного провайдера из @BotFather. Для оплаты в Telegram Stars — передать пустую строку |
| `currency` | String | ✅ | Трёхбуквенный код валюты ISO 4217. Для Telegram Stars — "XTR" |
| `prices` | Array of LabeledPrice | ✅ | Разбивка стоимости (товар, налог, скидка и т.д.). Для Stars — ровно один элемент |
| `max_tip_amount` | Integer | — | Максимальный размер чаевых в минимальных единицах валюты. Не поддерживается для Stars. По умолчанию 0 |
| `suggested_tip_amounts` | Array of Integer | — | До 4 предложенных сумм чаевых; должны быть положительными, в строго возрастающем порядке и не превышать max_tip_amount |
| `start_parameter` | String | — | Deep-link параметр. Если пустой — пересланные копии имеют кнопку Pay; если задан — URL-кнопку с deep link |
| `provider_data` | String | — | JSON-сериализованные данные для платёжного провайдера (специфика провайдера) |
| `photo_url` | String | — | URL фото товара или маркетингового изображения |
| `photo_size` | Integer | — | Размер фото в байтах |
| `photo_width` | Integer | — | Ширина фото в пикселях |
| `photo_height` | Integer | — | Высота фото в пикселях |
| `need_name` | Boolean | — | True — требовать полное имя пользователя. Игнорируется для Stars |
| `need_phone_number` | Boolean | — | True — требовать номер телефона. Игнорируется для Stars |
| `need_email` | Boolean | — | True — требовать email. Игнорируется для Stars |
| `need_shipping_address` | Boolean | — | True — требовать адрес доставки. Игнорируется для Stars |
| `send_phone_number_to_provider` | Boolean | — | True — отправить номер телефона провайдеру. Игнорируется для Stars |
| `send_email_to_provider` | Boolean | — | True — отправить email провайдеру. Игнорируется для Stars |
| `is_flexible` | Boolean | — | True — итоговая цена зависит от способа доставки. Игнорируется для Stars |
| `disable_notification` | Boolean | — | True — отправить сообщение без звука |
| `protect_content` | Boolean | — | True — защитить сообщение от пересылки и сохранения |
| `allow_paid_broadcast` | Boolean | — | True — разрешить до 1000 сообщений/сек в обход лимитов за 0.1 Stars за сообщение |
| `message_effect_id` | String | — | ID визуального эффекта сообщения; только для личных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры suggested post для direct messages чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на другое сообщение |
| `reply_markup` | InlineKeyboardMarkup | — | Если не задан — показывается кнопка 'Pay <сумма>'. Если задан — первая кнопка ОБЯЗАНА быть Pay-кнопкой |

**Возвращает:** Message — отправленное сообщение с инвойсом

**⚠️ Грабли:** Для Telegram Stars (currency="XTR"): массив prices должен содержать ровно один элемент, а все параметры, связанные с данными пользователя (need_name, need_email, need_phone_number, need_shipping_address, send_*_to_provider, is_flexible), игнорируются. provider_token для Stars — пустая строка, а не отсутствие параметра.

### `createInvoiceLink` — ✅ CLI: `invoice-link`  · _Bot API Bot API 6.1_

Создаёт ссылку на инвойс и возвращает её в виде строки. Пользователь открывает ссылку и оплачивает без отправки сообщения в чат.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | — | ID бизнес-соединения, от имени которого создаётся ссылка. Только для оплаты в Stars |
| `title` | String | ✅ | Название продукта, 1–32 символа |
| `description` | String | ✅ | Описание продукта, 1–255 символов |
| `payload` | String | ✅ | Внутренний payload для бота, 1–128 байт |
| `provider_token` | String | — | Токен платёжного провайдера. Для Stars — пустая строка |
| `currency` | String | ✅ | Код валюты ISO 4217 или "XTR" для Stars |
| `prices` | Array of LabeledPrice | ✅ | Разбивка стоимости. Для Stars — ровно один элемент |
| `suggested_tip_amounts` | Array of Integer | — | До 4 предложенных сумм чаевых в строго возрастающем порядке, не превышающих max_tip_amount |
| `start_parameter` | String | — | Deep-link параметр; определяет поведение кнопки в пересланных сообщениях |
| `provider_data` | String | — | JSON-данные для платёжного провайдера |
| `photo_url` | String | — | URL фото товара |
| `photo_size` | Integer | — | Размер фото в байтах |
| `photo_width` | Integer | — | Ширина фото |
| `photo_height` | Integer | — | Высота фото |
| `need_name` | Boolean | — | Требовать полное имя. Игнорируется для Stars |
| `need_phone_number` | Boolean | — | Требовать номер телефона. Игнорируется для Stars |
| `need_email` | Boolean | — | Требовать email. Игнорируется для Stars |
| `need_shipping_address` | Boolean | — | Требовать адрес доставки. Игнорируется для Stars |
| `send_phone_number_to_provider` | Boolean | — | Отправить номер телефона провайдеру. Игнорируется для Stars |
| `send_email_to_provider` | Boolean | — | Отправить email провайдеру. Игнорируется для Stars |
| `is_flexible` | Boolean | — | Цена зависит от доставки. Игнорируется для Stars |
| `disable_notification` | Boolean | — | Отправить без звука |
| `protect_content` | Boolean | — | Защитить от пересылки и сохранения |
| `allow_paid_broadcast` | Boolean | — | Разрешить массовую рассылку за 0.1 Stars/сообщение |
| `message_effect_id` | String | — | ID визуального эффекта; только для личных чатов |
| `suggested_post_parameters` | SuggestedPostParameters | — | Параметры suggested post для direct messages чатов |
| `reply_parameters` | ReplyParameters | — | Параметры ответа на сообщение |
| `reply_markup` | InlineKeyboardMarkup | — | Инлайн-клавиатура; если не задана — кнопка 'Pay <сумма>'; если задана — первая кнопка обязана быть Pay |

**Возвращает:** String — созданная ссылка на инвойс

**⚠️ Грабли:** Метод не отправляет сообщение — только генерирует ссылку. Параметр business_connection_id поддерживается исключительно для Stars-платежей. Ссылку нельзя переиспользовать после оплаты.

### `answerShippingQuery` — ✅ CLI: `answer-shipping`  · _Bot API Bot API 2.0_

Отвечает на shipping-запрос от Telegram: подтверждает возможность доставки по указанному адресу или сообщает об ошибке. Вызывается только когда sendInvoice был с is_flexible=True.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `shipping_query_id` | String | ✅ | Уникальный ID запроса на доставку из объекта ShippingQuery |
| `ok` | Boolean | ✅ | True — доставка по указанному адресу возможна; False — невозможна |
| `shipping_options` | Array of ShippingOption | — | Обязателен если ok=True. JSON-массив доступных вариантов доставки с ценами |
| `error_message` | String | — | Обязателен если ok=False. Сообщение об ошибке, которое Telegram покажет пользователю (например, 'Доставка в этот регион недоступна') |

**Возвращает:** True при успехе

**⚠️ Грабли:** Метод игнорируется и никогда не вызывается для платежей в Telegram Stars (XTR), так как Stars-инвойсы не поддерживают is_flexible и ShippingQuery. Если ok=False и error_message не передан, запрос зависнет без ответа.

### `answerPreCheckoutQuery` — ✅ CLI: `answer-precheckout`  · _Bot API Bot API 2.0_

Финальное подтверждение или отклонение заказа после того, как пользователь подтвердил оплату. Telegram Bot API отправляет pre_checkout_query боту, бот обязан ответить в течение 10 секунд.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `pre_checkout_query_id` | String | ✅ | Уникальный ID pre-checkout запроса из объекта PreCheckoutQuery |
| `ok` | Boolean | ✅ | True — всё в порядке, товар доступен, бот готов обработать заказ; False — есть проблема |
| `error_message` | String | — | Обязателен если ok=False. Человекочитаемое сообщение об ошибке, которое Telegram покажет пользователю |

**Возвращает:** True при успехе

**⚠️ Грабли:** Ответ ОБЯЗАН быть отправлен не позднее чем через 10 секунд после получения запроса — иначе платёж автоматически отменяется. Деньги/Stars списываются только после ответа ok=True.

### `getMyStarBalance` — ✅ CLI: `star-balance`  · _Bot API Bot API 7.4_

Возвращает текущий баланс Telegram Stars бота. Параметры не требуются.

**Возвращает:** StarAmount — объект с полем amount (Integer): количество Telegram Stars на балансе бота

**⚠️ Грабли:** Метод возвращает баланс только самого бота, а не бизнес-аккаунта. Для баланса управляемого бизнес-аккаунта используется getBusinessAccountStarBalance (с параметром business_connection_id).

### `getStarTransactions` — ✅ CLI: `star-tx`  · _Bot API Bot API 7.4_

Возвращает список транзакций Telegram Stars бота в хронологическом порядке. Поддерживает пагинацию через offset и limit.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `offset` | Integer | — | Количество транзакций, которые нужно пропустить в ответе (для пагинации) |
| `limit` | Integer | — | Максимальное количество транзакций в ответе, от 1 до 100 включительно. По умолчанию 100 |

**Возвращает:** StarTransactions — объект со списком транзакций

**⚠️ Грабли:** Транзакции возвращаются строго в хронологическом (не обратном) порядке. Для полной выгрузки нужна пагинация: увеличивай offset на limit до тех пор, пока ответ не вернёт меньше limit транзакций.

### `refundStarPayment` — ✅ CLI: `refund`  · _Bot API Bot API 7.4_

Возвращает Stars пользователю за ранее успешно совершённый платёж. Требует ID пользователя и Telegram-идентификатор платежа.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Telegram ID пользователя, которому нужно вернуть Stars |
| `telegram_payment_charge_id` | String | ✅ | Telegram-идентификатор платежа (поле telegram_payment_charge_id из объекта SuccessfulPayment) |

**Возвращает:** True при успехе

**⚠️ Грабли:** Работает только с платежами в Telegram Stars (XTR). Рефанд реального провайдера (Stripe и др.) через этот метод невозможен — для обычных валют возврат делается на стороне платёжного провайдера. Нельзя вернуть уже возвращённый платёж.

### `editUserStarSubscription` — ✅ CLI: `star-sub`  · _Bot API Bot API 8.0_

Отменяет или возобновляет продление подписки пользователя, оплаченной в Telegram Stars. Позволяет боту управлять жизненным циклом Stars-подписок.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Telegram ID пользователя, чья подписка редактируется |
| `telegram_payment_charge_id` | String | ✅ | Telegram-идентификатор платежа по подписке |
| `is_canceled` | Boolean | ✅ | True — отменить продление подписки (подписка остаётся активной до конца оплаченного периода); False — восстановить продление ранее отменённой ботом подписки |

**Возвращает:** True при успехе

**⚠️ Грабли:** is_canceled=True не прекращает подписку немедленно — она действует до конца текущего периода. Повторная отмена уже отменённой или восстановление уже активной подписки вернёт ошибку. Метод управляет только подписками, отменёнными именно ботом, а не самим пользователем.


<a name="gifts"></a>
## Подарки

### `getAvailableGifts` — ✅ CLI: `gifts`  · _Bot API 8.0_

Возвращает список подарков, которые бот может отправить пользователям и каналам. Не требует никаких параметров.

**Возвращает:** Gifts

### `sendGift` — ✅ CLI: `gift`  · _Bot API 8.0_

Отправляет подарок пользователю или чату-каналу от имени бота. Стоимость подарка списывается с баланса Telegram Stars бота.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | — | Уникальный идентификатор пользователя-получателя. Обязателен, если не указан chat_id; бот и пользователь должны были обменяться сообщениями либо пользователь должен разрешить отправку подарков. |
| `chat_id` | Integer or String | — | Идентификатор чата или @username канала-получателя. Обязателен, если не указан user_id; ограниченные (limited) подарки нельзя отправлять в каналы. |
| `gift_id` | String | ✅ | Идентификатор подарка, полученный из getAvailableGifts. |
| `pay_for_upgrade` | Boolean | — | Передайте True, чтобы оплатить апгрейд подарка до уникального из баланса бота, делая его бесплатным для получателя. |
| `text` | String | — | Текст, который будет показан вместе с подарком; 0–128 символов. |
| `text_parse_mode` | String | — | Режим форматирования текста (Markdown, HTML и т.д.); поддерживаются только сущности bold, italic, underline, strikethrough, spoiler, custom_emoji и date_time. |
| `text_entities` | Array of MessageEntity | — | JSON-сериализованный список специальных сущностей текста подарка; альтернатива text_parse_mode. Поддерживаются только: bold, italic, underline, strikethrough, spoiler, custom_emoji, date_time. |

**Возвращает:** Boolean (True on success)

**⚠️ Грабли:** Необходимо указать ровно один из двух параметров: user_id или chat_id — не оба и не ни одного. Ограниченные (limited) подарки нельзя отправлять в каналы. Получатель не сможет конвертировать подарок, отправленный с pay_for_upgrade=True, в Telegram Stars.

### `giftPremiumSubscription` — ✅ CLI: `gift-premium`  · _Bot API 9.0_

Дарит пользователю подписку Telegram Premium, оплачивая её Telegram Stars с баланса бота. Бот должен иметь достаточный баланс Stars.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор пользователя, которому отправляется Premium. |
| `month_count` | Integer | ✅ | Количество месяцев подписки; допустимые значения: 3, 6 или 12. |
| `star_count` | Integer | ✅ | Количество Telegram Stars для оплаты подписки; должно строго соответствовать: 1000 за 3 месяца, 1500 за 6 месяцев, 2500 за 12 месяцев. |
| `text` | String | — | Текст, отображаемый вместе с сервисным сообщением о подписке; 0–128 символов. |
| `text_parse_mode` | String | — | Режим форматирования текста подарка; поддерживаются только: bold, italic, underline, strikethrough, spoiler, custom_emoji, date_time. |
| `text_entities` | Array of MessageEntity | — | JSON-сериализованный список сущностей текста; альтернатива text_parse_mode. Поддерживаются только: bold, italic, underline, strikethrough, spoiler, custom_emoji, date_time. |

**Возвращает:** Boolean (True on success)

**⚠️ Грабли:** Значения star_count жёстко привязаны к month_count и не могут быть произвольными — любое несоответствие вернёт ошибку. На момент Bot API 9.0 метод доступен только для подарка Premium живому пользователю, не каналу.

### `getUserGifts` — ✅ CLI: `user-gifts`  · _Bot API 9.3_

Возвращает список подарков, полученных и принадлежащих указанному пользователю. Поддерживает фильтрацию по типу подарка и пагинацию.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор пользователя, чьи подарки запрашиваются. |
| `exclude_unlimited` | Boolean | — | Передайте True, чтобы исключить подарки, которые можно купить неограниченное количество раз. |
| `exclude_limited_upgradable` | Boolean | — | Передайте True, чтобы исключить лимитированные подарки, которые можно апгрейдить до уникальных. |
| `exclude_limited_non_upgradable` | Boolean | — | Передайте True, чтобы исключить лимитированные подарки, которые нельзя апгрейдить до уникальных. |
| `exclude_from_blockchain` | Boolean | — | Передайте True, чтобы исключить подарки, назначенные из блокчейна TON и недоступные для перепродажи или передачи в Telegram. |
| `exclude_unique` | Boolean | — | Передайте True, чтобы исключить уникальные подарки. |
| `sort_by_price` | Boolean | — | Передайте True, чтобы отсортировать результаты по цене подарка, а не по дате отправки. Сортировка применяется до пагинации. |
| `offset` | String | — | Смещение первой возвращаемой записи, полученное из предыдущего запроса (поле next_offset); передайте пустую строку или не передавайте для получения первой страницы. |
| `limit` | Integer | — | Максимальное количество подарков в ответе; допустимые значения 1–100, по умолчанию 100. |

**Возвращает:** OwnedGifts

**⚠️ Грабли:** offset — строка (String), а не число; значение берётся из поля next_offset предыдущего ответа. Передача числового смещения вызовет ошибку.

### `getChatGifts` — ✅ CLI: `chat-gifts`  · _Bot API 9.3_

Возвращает список подарков, полученных и принадлежащих указанному чату (каналу). Поддерживает фильтрацию по типу и сохранённости подарка, а также пагинацию.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Уникальный идентификатор чата или @username канала, чьи подарки запрашиваются. |
| `exclude_unsaved` | Boolean | — | Передайте True, чтобы исключить подарки, не сохранённые на странице профиля чата. |
| `exclude_saved` | Boolean | — | Передайте True, чтобы исключить подарки, сохранённые на странице профиля чата. |
| `exclude_unlimited` | Boolean | — | Передайте True, чтобы исключить подарки, которые можно купить неограниченное количество раз. |
| `exclude_limited_upgradable` | Boolean | — | Передайте True, чтобы исключить лимитированные подарки, доступные для апгрейда до уникальных. |
| `exclude_limited_non_upgradable` | Boolean | — | Передайте True, чтобы исключить лимитированные подарки без возможности апгрейда. |
| `exclude_from_blockchain` | Boolean | — | Передайте True, чтобы исключить подарки из блокчейна TON, недоступные для перепродажи или передачи. |
| `exclude_unique` | Boolean | — | Передайте True, чтобы исключить уникальные подарки. |
| `sort_by_price` | Boolean | — | Передайте True, чтобы отсортировать результаты по цене подарка вместо даты отправки. |
| `offset` | String | — | Строковое смещение из поля next_offset предыдущего ответа; пустая строка или отсутствие параметра — первая страница. |
| `limit` | Integer | — | Максимальное количество подарков; допустимые значения 1–100, по умолчанию 100. |

**Возвращает:** OwnedGifts

**⚠️ Грабли:** В отличие от конвертации и апгрейда подарков, этот метод не требует business_connection_id — он работает напрямую с chat_id канала, которым управляет бот.

### `convertGiftToStars` — ✅ CLI: `gift-convert`  · _Bot API 9.0_

Конвертирует обычный (не уникальный) подарок, полученный бизнес-аккаунтом через управляемое бизнес-соединение, в Telegram Stars. Требует соответствующего бизнес-права бота.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Уникальный идентификатор бизнес-соединения, через которое управляется аккаунт. |
| `owned_gift_id` | String | ✅ | Уникальный идентификатор конкретного обычного подарка, который нужно конвертировать в Stars. |

**Возвращает:** Boolean (True on success)

**⚠️ Грабли:** Требует бизнес-права can_convert_gifts_to_stars. Конвертировать можно только обычные подарки (не уникальные); попытка конвертировать уникальный подарок вернёт ошибку.

### `upgradeGift` — ✅ CLI: `gift-upgrade`  · _Bot API 9.0_

Апгрейдит обычный подарок, принадлежащий бизнес-аккаунту, до уникального подарка за Telegram Stars. Если стоимость апгрейда уже предоплачена отправителем, апгрейд может быть бесплатным.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Уникальный идентификатор бизнес-соединения, через которое управляется аккаунт-владелец подарка. |
| `owned_gift_id` | String | ✅ | Уникальный идентификатор обычного подарка, который нужно апгрейднуть до уникального. |
| `keep_original_details` | Boolean | — | Передайте True, чтобы сохранить в уникальном подарке оригинальный текст, отправителя и получателя. |
| `star_count` | Integer | — | Количество Telegram Stars для оплаты апгрейда с баланса бизнес-аккаунта. Передайте 0, если апгрейд предоплачен отправителем; иначе передайте требуемое количество Stars (требует прав can_transfer_stars). |

**Возвращает:** Boolean (True on success)

**⚠️ Грабли:** Если передаётся ненулевое star_count, требуется бизнес-право can_transfer_stars. При star_count=0 право не нужно, но только если апгрейд действительно предоплачен — иначе вернётся ошибка.

### `transferGift` — ✅ CLI: `gift-transfer`  · _Bot API 9.0_

Передаёт уникальный подарок, принадлежащий бизнес-аккаунту, другому пользователю или чату. Требует соответствующих бизнес-прав, если передача платная.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Уникальный идентификатор бизнес-соединения, через которое управляется аккаунт-владелец подарка. |
| `owned_gift_id` | String | ✅ | Уникальный идентификатор уникального подарка, который нужно передать. |
| `new_owner_chat_id` | Integer | ✅ | Уникальный идентификатор чата, который станет новым владельцем подарка. Чат должен быть активен в течение последних 24 часов. |
| `star_count` | Integer | — | Количество Telegram Stars, которое будет списано с баланса бизнес-аккаунта за передачу. Если значение положительное, требуется бизнес-право can_transfer_stars. |

**Возвращает:** Boolean (True on success)

**⚠️ Грабли:** Получатель (new_owner_chat_id) должен быть активен в последние 24 часа — иначе метод вернёт ошибку. При платной передаче (star_count > 0) требуется право can_transfer_stars.


<a name="stickers"></a>
## Стикер-сеты

### `uploadStickerFile` — ✅ CLI: `sticker-upload`  · _Bot API Bot API 1.0_

Загружает файл с изображением или анимацией в облако Telegram для последующего использования в createNewStickerSet / addStickerToSet. Возвращает загруженный File, который можно использовать многократно в течение 72 часов.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | ID пользователя-владельца набора стикеров; именно от его имени будет создан стикер-сет |
| `sticker` | InputFile | ✅ | Файл стикера для загрузки. Допустимые форматы зависят от sticker_format |
| `sticker_format` | String | ✅ | Формат стикера: «static» (PNG/WEBP), «animated» (TGS), «video» (WEBM) |

**Возвращает:** File

**⚠️ Грабли:** Возвращённый file_id пригоден для stickers только в течение 72 часов; для обычной отправки файлов он не подходит. Формат sticker_format должен строго соответствовать типу переданного файла.

### `createNewStickerSet` — ✅ CLI: `stickerset-create`  · _Bot API Bot API 1.0_

Создаёт новый набор стикеров, принадлежащий указанному пользователю. Метод создаёт набор с одним или несколькими стикерами, переданными сразу в списке.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | ID пользователя Telegram, который станет владельцем набора |
| `name` | String | ✅ | Краткое имя набора (1–64 символа, только a–z, 0–9 и _); автоматически добавляется суффикс _by_<bot_username> |
| `title` | String | ✅ | Заголовок набора, отображаемый пользователям (1–64 символа) |
| `stickers` | Array of InputSticker | ✅ | Список стикеров для добавления в набор (1–50 штук в один вызов) |
| `sticker_type` | String | — | Тип стикеров: «regular», «mask» или «custom_emoji»; по умолчанию «regular» |
| `needs_repainting` | Boolean | — | Только для custom_emoji: перекрашивать ли стикер под цвет текста/кнопок; по умолчанию false |

**Возвращает:** True

**⚠️ Грабли:** Имя набора (name) после создания изменить нельзя; суффикс _by_<bot_username> добавляется автоматически и не должен передаваться вручную. Все стикеры в списке должны быть одного формата (static/animated/video).

### `addStickerToSet` — ✅ CLI: `sticker-add`  · _Bot API Bot API 1.0_

Добавляет новый стикер в существующий набор, созданный ботом. Набор не может содержать более 120 стикеров (50 для анимированных/видео).


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | ID пользователя-владельца набора стикеров |
| `name` | String | ✅ | Краткое имя набора стикеров (без суффикса _by_<bot>, он уже содержится в name) |
| `sticker` | InputSticker | ✅ | Объект InputSticker с файлом, списком эмодзи и опциональными настройками маски/ключевых слов |

**Возвращает:** True

**⚠️ Грабли:** Стикер добавляется в конец набора. Формат нового стикера должен совпадать с форматом существующих стикеров в наборе, иначе вернётся ошибка.

### `setStickerPositionInSet` — ✅ CLI: `sticker-pos`  · _Bot API Bot API 1.0_

Перемещает стикер на заданную позицию (начиная с 0) внутри набора стикеров, созданного ботом.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `sticker` | String | ✅ | File identifier стикера, позицию которого нужно изменить |
| `position` | Integer | ✅ | Новая позиция стикера (0-based) в наборе |

**Возвращает:** True

**⚠️ Грабли:** Позиция отсчитывается с нуля. Попытка переместить стикер за пределы текущего числа стикеров в наборе приведёт к ошибке.

### `deleteStickerFromSet` — ✅ CLI: `sticker-del`  · _Bot API Bot API 1.0_

Удаляет стикер из набора, созданного ботом. Если в наборе остался последний стикер, набор не удаляется — он становится пустым.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `sticker` | String | ✅ | File identifier стикера, который нужно удалить из набора |

**Возвращает:** True

**⚠️ Грабли:** Удаление последнего стикера НЕ удаляет сам набор; набор остаётся с нулём стикеров и может мешать повторному использованию имени. Используйте deleteStickerSet для полного удаления.

### `replaceStickerInSet` — ✅ CLI: `sticker-replace`  · _Bot API Bot API 7.2_

Заменяет существующий стикер в наборе новым, сохраняя его позицию. Позволяет обновить изображение стикера без удаления и повторного добавления.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | ID пользователя-владельца набора стикеров |
| `name` | String | ✅ | Краткое имя набора стикеров |
| `old_sticker` | String | ✅ | File identifier стикера, который нужно заменить |
| `sticker` | InputSticker | ✅ | Новый стикер (InputSticker), который встанет на место старого |

**Возвращает:** True

**⚠️ Грабли:** Новый стикер занимает ту же позицию, что и заменяемый. Формат нового стикера должен совпадать с форматом набора.

### `setStickerEmojiList` — ✅ CLI: `sticker-emojis`  · _Bot API Bot API 6.6_

Изменяет список эмодзи, связанных со стикером, созданным ботом. Эмодзи используются при поиске стикера по символам.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `sticker` | String | ✅ | File identifier стикера, список эмодзи которого изменяется |
| `emoji_list` | Array of String | ✅ | Новый список эмодзи (1–20 штук), ассоциированных с данным стикером |

**Возвращает:** True

**⚠️ Грабли:** Список должен содержать от 1 до 20 эмодзи. Передача пустого массива вернёт ошибку.

### `setStickerKeywords` — ✅ CLI: `sticker-keywords`  · _Bot API Bot API 6.6_

Задаёт поисковые ключевые слова для стикера, созданного ботом. Ключевые слова помогают найти стикер при поиске по тексту в панели выбора стикеров.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `sticker` | String | ✅ | File identifier стикера, которому задаются ключевые слова |
| `keywords` | Array of String | — | Список ключевых слов (0–20 штук); каждое слово до 64 символов; передача пустого массива или отсутствие поля удаляет ключевые слова |

**Возвращает:** True

**⚠️ Грабли:** Поле опциональное: если не передать его или передать пустой массив, ключевые слова стикера будут удалены. Ключевые слова работают только для regular и custom_emoji стикеров.

### `setStickerMaskPosition` — ✅ CLI: `sticker-mask`  · _Bot API Bot API 6.6_

Задаёт или изменяет позицию маски (MaskPosition) для стикера-маски, созданного ботом. Определяет, к какой части лица/тела прикрепляется маска.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `sticker` | String | ✅ | File identifier стикера-маски, позицию которого нужно задать |
| `mask_position` | MaskPosition | — | Новая позиция маски; если не передать или передать null — позиция маски удаляется |

**Возвращает:** True

**⚠️ Грабли:** Работает только для стикеров типа «mask». Передача mask_position без поля (или null) очищает текущую позицию маски.

### `setStickerSetTitle` — ✅ CLI: `stickerset-title`  · _Bot API Bot API 6.6_

Изменяет заголовок набора стикеров, созданного ботом. Заголовок — это человекочитаемое название, видимое в интерфейсе Telegram.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `name` | String | ✅ | Краткое имя набора (системный идентификатор, не изменяемый) |
| `title` | String | ✅ | Новый заголовок набора (1–64 символа) |

**Возвращает:** True

**⚠️ Грабли:** Изменяется только отображаемый заголовок; системное имя (name/short_name) после создания набора изменить невозможно.

### `setStickerSetThumbnail` — ✅ CLI: `stickerset-thumb`  · _Bot API Bot API 6.6_

Задаёт или удаляет миниатюру (thumbnail) набора стикеров, созданного ботом. Миниатюра отображается в интерфейсе выбора набора.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `name` | String | ✅ | Краткое имя набора стикеров |
| `user_id` | Integer | ✅ | ID пользователя-владельца набора стикеров |
| `thumbnail` | InputFile or String | — | Файл миниатюры: .WEBP/.PNG (до 128 КБ, 100×100 пкс) для статичных, .TGS для анимированных, .WEBM для видео-наборов; если не передать — миниатюра удаляется |
| `format` | String | ✅ | Формат миниатюры: «static», «animated» или «video»; должен совпадать с форматом стикеров набора |

**Возвращает:** True

**⚠️ Грабли:** Формат thumbnail (format) обязателен и должен совпадать с форматом стикеров набора. Если thumbnail не передан — миниатюра сбрасывается до автоматически генерируемой.

### `setCustomEmojiStickerSetThumbnail` — ✅ CLI: `emoji-set-thumb`  · _Bot API Bot API 6.6_

Задаёт миниатюру набора стикеров типа custom_emoji с помощью одного из эмодзи набора. Отличается от setStickerSetThumbnail тем, что принимает custom_emoji_id, а не файл.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `name` | String | ✅ | Краткое имя набора custom_emoji стикеров |
| `custom_emoji_id` | String | — | Идентификатор custom emoji из этого набора, который станет миниатюрой; если не передать — миниатюра удаляется и выбирается автоматически |

**Возвращает:** True

**⚠️ Грабли:** Работает исключительно для наборов типа custom_emoji. Для regular и mask наборов используйте setStickerSetThumbnail.

### `deleteStickerSet` — ✅ CLI: `stickerset-del`  · _Bot API Bot API 7.2_

Полностью удаляет набор стикеров, созданный ботом. После удаления имя набора освобождается и может быть использовано повторно.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `name` | String | ✅ | Краткое имя набора стикеров, который нужно удалить |

**Возвращает:** True

**⚠️ Грабли:** После удаления набора все его стикеры становятся недоступны для новых сообщений, но уже отправленные стикеры в чатах отображаются по-прежнему. Имя набора после удаления можно повторно использовать в createNewStickerSet.

### `getStickerSet` — ✅ CLI: `stickerset-get`  · _Bot API Bot API 1.0_

Возвращает объект StickerSet с полной информацией о наборе стикеров по его краткому имени. Доступен для любых наборов, не только созданных ботом.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `name` | String | ✅ | Краткое имя набора стикеров (поле name объекта StickerSet) |

**Возвращает:** StickerSet

**⚠️ Грабли:** Имя передаётся без суффикса _by_<bot_username>: нужно передавать полное name так, как оно есть в объекте StickerSet (суффикс уже включён). Метод работает и для наборов, созданных другими ботами/пользователями.

### `getCustomEmojiStickers` — ✅ CLI: `custom-emoji`  · _Bot API Bot API 6.0_

Возвращает информацию об одном или нескольких custom emoji по их идентификаторам в виде массива объектов Sticker. Используется для получения file_id и других свойств эмодзи.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `custom_emoji_ids` | Array of String | ✅ | Список идентификаторов custom emoji (до 200 штук за один запрос) |

**Возвращает:** Array of Sticker

**⚠️ Грабли:** Максимум 200 идентификаторов за один вызов. Возвращает только эмодзи, которые реально существуют; несуществующие ID молча игнорируются, а не вызывают ошибку.


<a name="business-games-misc"></a>
## Бизнес-аккаунты, игры, верификация, прочее

### `getBusinessConnection` — ✅ CLI: `biz-get`  · _Bot API 7.2_

Получает информацию о подключении бота к бизнес-аккаунту. Используется для проверки активности соединения и прав бота в этом соединении.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Уникальный идентификатор бизнес-соединения |

**Возвращает:** BusinessConnection

**⚠️ Грабли:** Идентификатор соединения приходит только через обновления типа business_connection; его нельзя получить иным способом.

### `readBusinessMessage` — ✅ CLI: `biz-read`  · _Bot API 9.0_

Помечает входящее сообщение как прочитанное от имени бизнес-аккаунта. Требует права can_read_messages у бота в данном соединении.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения, от имени которого помечается сообщение |
| `chat_id` | Integer | ✅ | Идентификатор чата, в котором получено сообщение; чат должен быть активен в последние 24 часа |
| `message_id` | Integer | ✅ | Идентификатор сообщения, которое нужно пометить как прочитанное |

**Возвращает:** True

**⚠️ Грабли:** Чат должен быть активен в последние 24 часа — иначе вернёт ошибку. Работает только для входящих сообщений.

### `deleteBusinessMessages` — ✅ CLI: `biz-delete`  · _Bot API 9.0_

Удаляет сообщения от имени бизнес-аккаунта. Для удаления собственных сообщений бота нужно право can_delete_sent_messages, для удаления любых сообщений — can_delete_all_messages.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения, от имени которого удаляются сообщения |
| `message_ids` | Array of Integer | ✅ | JSON-сериализованный список из 1–100 идентификаторов сообщений; все сообщения должны быть из одного чата |

**Возвращает:** True

**⚠️ Грабли:** Все message_ids должны принадлежать одному и тому же чату. Применяются те же ограничения на удаляемые сообщения, что и у deleteMessage.

### `setBusinessAccountName` — ✅ CLI: `biz-set-name`  · _Bot API 9.0_

Изменяет имя и фамилию управляемого бизнес-аккаунта. Требует право can_change_name у бота в данном соединении.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `first_name` | String | ✅ | Новое значение имени; 1–64 символа |
| `last_name` | String | — | Новое значение фамилии; 0–64 символа. Передать пустую строку — удалить фамилию. |

**Возвращает:** True

### `setBusinessAccountUsername` — ✅ CLI: `biz-set-username`  · _Bot API 9.0_

Изменяет имя пользователя (username) управляемого бизнес-аккаунта. Требует право can_change_username.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `username` | String | — | Новый username; 0–32 символа. Передать пустую строку — удалить username. |

**Возвращает:** True

**⚠️ Грабли:** Параметр помечен Optional, но по сути обязателен для смены username; передача пустой строки удаляет его.

### `setBusinessAccountBio` — ✅ CLI: `biz-set-bio`  · _Bot API 9.0_

Изменяет описание (bio) управляемого бизнес-аккаунта. Требует право can_change_bio.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `bio` | String | — | Новый текст bio; 0–140 символов. Пустая строка — очистить bio. |

**Возвращает:** True

### `setBusinessAccountProfilePhoto` — ✅ CLI: `biz-set-photo`  · _Bot API 9.0_

Устанавливает фото профиля управляемого бизнес-аккаунта. Требует право can_edit_profile_photo.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `photo` | InputProfilePhoto | ✅ | Новое фото профиля для установки |
| `is_public` | Boolean | — | Передать True, чтобы установить публичное фото — видимое даже если основное фото скрыто настройками приватности. Аккаунт может иметь только одно публичное фото. |

**Возвращает:** True

**⚠️ Грабли:** Публичное фото (is_public=True) видно всегда, независимо от настроек приватности бизнес-аккаунта, но может быть только одно.

### `removeBusinessAccountProfilePhoto` — ✅ CLI: `biz-del-photo`  · _Bot API 9.0_

Удаляет текущее фото профиля управляемого бизнес-аккаунта. Требует право can_edit_profile_photo.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `is_public` | Boolean | — | Передать True, чтобы удалить публичное фото. После удаления основного фото предыдущее фото (при наличии) становится основным. |

**Возвращает:** True

**⚠️ Грабли:** Если is_public не передан, удаляется основное (не публичное) фото, и предыдущее в истории становится новым основным.

### `setBusinessAccountGiftSettings` — ✅ CLI: `biz-gift-settings`  · _Bot API 9.0_

Изменяет настройки конфиденциальности для входящих подарков в управляемом бизнес-аккаунте. Требует право can_change_gift_settings.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `show_gift_button` | Boolean | ✅ | Передать True, чтобы кнопка отправки подарка всегда отображалась в поле ввода |
| `accepted_gift_types` | AcceptedGiftTypes | ✅ | Объект, описывающий типы подарков, принимаемых бизнес-аккаунтом |

**Возвращает:** True

### `getBusinessAccountStarBalance` — ✅ CLI: `biz-star-balance`  · _Bot API 9.0_

Возвращает количество Telegram Stars на балансе управляемого бизнес-аккаунта. Требует право can_view_gifts_and_stars.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |

**Возвращает:** StarAmount

### `transferBusinessAccountStars` — ✅ CLI: `biz-transfer-stars`  · _Bot API 9.0_

Переводит Telegram Stars с баланса бизнес-аккаунта на баланс бота. Требует право can_transfer_stars.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `star_count` | Integer | ✅ | Количество Telegram Stars для перевода; от 1 до 10 000 |

**Возвращает:** True

**⚠️ Грабли:** Максимум за один вызов — 10 000 Stars. Перевод идёт только на баланс самого бота, не на произвольный аккаунт.

### `getBusinessAccountGifts` — ✅ CLI: `biz-gifts`  · _Bot API 9.0_

Возвращает список подарков, полученных и принадлежащих управляемому бизнес-аккаунту. Требует право can_view_gifts_and_stars. Поддерживает пагинацию и множество фильтров.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `exclude_unsaved` | Boolean | — | True — исключить подарки, не сохранённые на странице профиля аккаунта |
| `exclude_saved` | Boolean | — | True — исключить подарки, сохранённые на странице профиля |
| `exclude_unlimited` | Boolean | — | True — исключить подарки, которые можно купить неограниченное число раз |
| `exclude_limited_upgradable` | Boolean | — | True — исключить лимитированные подарки, доступные для апгрейда до уникальных |
| `exclude_limited_non_upgradable` | Boolean | — | True — исключить лимитированные подарки без возможности апгрейда до уникальных |
| `exclude_unique` | Boolean | — | True — исключить уникальные подарки |
| `exclude_from_blockchain` | Boolean | — | True — исключить подарки, назначенные через TON blockchain и не подлежащие перепродаже или передаче в Telegram |
| `sort_by_price` | Boolean | — | True — сортировать результаты по цене вместо даты отправки. Сортировка применяется до пагинации. |
| `offset` | String | — | Смещение для пагинации — значение, полученное из предыдущего запроса; пустая строка для получения первой страницы |
| `limit` | Integer | — | Максимальное количество подарков в ответе; 1–100, по умолчанию 100 |

**Возвращает:** OwnedGifts

**⚠️ Грабли:** sort_by_price применяется до пагинации — если сортировка включена, offset должен быть получен из ответа с той же сортировкой.

### `postStory` — ✅ CLI: `story-post`  · _Bot API 9.0_

Публикует историю (story) от имени управляемого бизнес-аккаунта. Требует право can_manage_stories.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `content` | InputStoryContent | ✅ | Содержимое истории (фото или видео) |
| `active_period` | Integer | ✅ | Время в секундах до перемещения истории в архив; допустимые значения: 6*3600 (6ч), 12*3600 (12ч), 86400 (24ч), 2*86400 (48ч) |
| `caption` | String | — | Подпись к истории; 0–2048 символов после обработки entities |
| `parse_mode` | String | — | Режим разбора сущностей в подписи (Markdown, HTML и т.д.) |
| `caption_entities` | Array of MessageEntity | — | Список специальных сущностей в подписи; альтернатива parse_mode |
| `areas` | Array of StoryArea | — | Список кликабельных областей, отображаемых поверх истории (ссылки, геолокации и т.д.) |
| `post_to_chat_page` | Boolean | — | Передать True, чтобы история оставалась доступной после истечения срока |
| `protect_content` | Boolean | — | Передать True, чтобы запретить пересылку и скриншоты контента истории |

**Возвращает:** Story

**⚠️ Грабли:** active_period принимает только четыре строго фиксированных значения в секундах; произвольное число вызовет ошибку.

### `editStory` — ✅ CLI: `story-edit`  · _Bot API 9.0_

Редактирует ранее опубликованную историю от имени управляемого бизнес-аккаунта. Требует право can_manage_stories.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `story_id` | Integer | ✅ | Уникальный идентификатор истории, которую нужно отредактировать |
| `content` | InputStoryContent | ✅ | Новое содержимое истории |
| `caption` | String | — | Новая подпись к истории; 0–2048 символов |
| `parse_mode` | String | — | Режим разбора сущностей в подписи |
| `caption_entities` | Array of MessageEntity | — | Список специальных сущностей в подписи; альтернатива parse_mode |
| `areas` | Array of StoryArea | — | Новый список кликабельных областей поверх истории |

**Возвращает:** Story

**⚠️ Грабли:** Поле content обязательно — редактировать только caption/areas без замены медиа нельзя.

### `deleteStory` — ✅ CLI: `story-delete`  · _Bot API 9.0_

Удаляет ранее опубликованную историю от имени управляемого бизнес-аккаунта. Требует право can_manage_stories.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `business_connection_id` | String | ✅ | Идентификатор бизнес-соединения |
| `story_id` | Integer | ✅ | Уникальный идентификатор истории для удаления |

**Возвращает:** True

### `setGameScore` — ✅ CLI: `game-score`

Устанавливает счёт указанного пользователя в игровом сообщении. Если сообщение не является inline-сообщением, возвращает изменённый Message; иначе True. Возвращает ошибку, если новый счёт не превышает текущий и force не установлен.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Идентификатор пользователя |
| `score` | Integer | ✅ | Новый счёт; должен быть неотрицательным |
| `force` | Boolean | — | Передать True, чтобы разрешить уменьшение счёта (например, для исправления ошибок или бана читеров) |
| `disable_edit_message` | Boolean | — | Передать True, чтобы игровое сообщение НЕ обновлялось автоматически с текущей таблицей лидеров |
| `chat_id` | Integer | — | Обязателен, если inline_message_id не указан. Идентификатор чата. |
| `message_id` | Integer | — | Обязателен, если inline_message_id не указан. Идентификатор сообщения. |
| `inline_message_id` | String | — | Обязателен, если chat_id и message_id не указаны. Идентификатор inline-сообщения. |

**Возвращает:** Message или True

**⚠️ Грабли:** По умолчанию метод запрещает снижение счёта и вернёт ошибку. Нужно явно передать force=True для уменьшения. Необходимо указать либо пару (chat_id + message_id), либо inline_message_id.

### `getGameHighScores` — ✅ CLI: `game-scores`

Возвращает данные для таблицы рекордов: счёт указанного пользователя и нескольких его соседей по рейтингу в игре.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Идентификатор целевого пользователя |
| `chat_id` | Integer | — | Обязателен, если inline_message_id не указан. Идентификатор чата. |
| `message_id` | Integer | — | Обязателен, если inline_message_id не указан. Идентификатор сообщения. |
| `inline_message_id` | String | — | Обязателен, если chat_id и message_id не указаны. Идентификатор inline-сообщения. |

**Возвращает:** Array of GameHighScore

**⚠️ Грабли:** Возвращает не полную таблицу лидеров, а только несколько строк вокруг целевого пользователя — точное количество не гарантировано.

### `verifyUser` — ✅ CLI: `verify-user`  · _Bot API 8.2_

Верифицирует пользователя от имени организации, представленной ботом. Бот должен быть настроен как организационный верификатор.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя |
| `custom_description` | String | — | Пользовательское описание верификации; 0–70 символов. Должно быть пустым, если организации не разрешено указывать описание. |

**Возвращает:** True

**⚠️ Грабли:** Передача custom_description при отсутствии соответствующего разрешения у организации вернёт ошибку — поле нужно оставлять пустым в этом случае.

### `verifyChat` — ✅ CLI: `verify-chat`  · _Bot API 8.2_

Верифицирует чат от имени организации, представленной ботом. Чаты прямых сообщений каналов не могут быть верифицированы.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Идентификатор чата или username бота/супергруппы/канала в формате @username. Чаты прямых сообщений канала не поддерживаются. |
| `custom_description` | String | — | Пользовательское описание верификации; 0–70 символов. Должно быть пустым, если организации не разрешено указывать описание. |

**Возвращает:** True

**⚠️ Грабли:** Channel direct messages chats явно исключены и вернут ошибку — верифицировать можно только супергруппы и каналы (не их чаты ЛС).

### `removeUserVerification` — ✅ CLI: `unverify-user`  · _Bot API 8.2_

Снимает верификацию с пользователя, верифицированного от имени организации, представленной ботом.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Уникальный идентификатор целевого пользователя |

**Возвращает:** True

### `removeChatVerification` — ✅ CLI: `unverify-chat`  · _Bot API 8.2_

Снимает верификацию с чата, верифицированного от имени организации, представленной ботом.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer or String | ✅ | Идентификатор чата или username бота/канала в формате @username |

**Возвращает:** True

### `answerGuestQuery` — ✅ CLI: `answer-guest`  · _Bot API 10.0_

Отвечает на полученный гостевой запрос (сообщение от гостя). Используется в контексте Guest Mode — анонимного режима обращения к ботам.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `guest_query_id` | String | ✅ | Уникальный идентификатор запроса для ответа |
| `result` | InlineQueryResult | ✅ | JSON-сериализованный объект, описывающий отправляемое сообщение |

**Возвращает:** SentGuestMessage

**⚠️ Грабли:** Результат имеет тип InlineQueryResult (как в inline-режиме), а не обычный Message — структура ответа специфична для гостевого режима.

### `answerChatJoinRequestQuery` — ✅ CLI: `answer-joinreq-query`  · _Bot API 10.1_

Обрабатывает полученный запрос на вступление в чат (chat join request query). Позволяет одобрить, отклонить или поставить в очередь заявку на вступление.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_join_request_query_id` | String | ✅ | Уникальный идентификатор запроса на вступление |
| `result` | String | ✅ | Результат обработки: "approve" — разрешить вступление, "decline" — отклонить, "queue" — оставить решение другим администраторам |

**Возвращает:** True

**⚠️ Грабли:** Значение result строго ограничено тремя вариантами: approve, decline, queue — любое другое значение вернёт ошибку.

### `sendChatJoinRequestWebApp` — ✅ CLI: `join-webapp`  · _Bot API 10.1_

Обрабатывает запрос на вступление в чат, показывая пользователю Mini App перед принятием решения. После взаимодействия с Mini App нужно вызвать answerChatJoinRequestQuery для финального решения.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_join_request_query_id` | String | ✅ | Уникальный идентификатор запроса на вступление |
| `web_app_url` | String | ✅ | URL Mini App, которое будет открыто пользователю |

**Возвращает:** True

**⚠️ Грабли:** Этот метод не завершает обработку запроса — после него обязательно нужно вызвать answerChatJoinRequestQuery, иначе запрос останется необработанным.

### `approveSuggestedPost` — ✅ CLI: `post-approve`  · _Bot API 9.2_

Одобряет предложенный пост в чате прямых сообщений (direct messages chat). Бот должен иметь право can_post_messages в соответствующем канале.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer | ✅ | Уникальный идентификатор чата прямых сообщений (DM-чата) |
| `message_id` | Integer | ✅ | Идентификатор сообщения с предложенным постом, который нужно одобрить |
| `send_date` | Integer | — | Unix timestamp ожидаемой публикации поста; не более чем через 2 678 400 секунд (30 дней). Не указывать, если дата уже была задана при создании предложенного поста. |

**Возвращает:** True

**⚠️ Грабли:** chat_id здесь — это DM-чат канала, а не сам канал. Право проверяется на соответствующем канале, но метод оперирует идентификатором DM-чата.

### `declineSuggestedPost` — ✅ CLI: `post-decline`  · _Bot API 9.2_

Отклоняет предложенный пост в чате прямых сообщений. Бот должен иметь право can_manage_direct_messages в соответствующем канале.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `chat_id` | Integer | ✅ | Уникальный идентификатор чата прямых сообщений |
| `message_id` | Integer | ✅ | Идентификатор сообщения с предложенным постом, который нужно отклонить |
| `comment` | String | — | Комментарий для автора предложенного поста; 0–128 символов |

**Возвращает:** True

**⚠️ Грабли:** Для одобрения нужно can_post_messages, а для отклонения — can_manage_direct_messages. Это разные права.

### `getManagedBotAccessSettings` — ✅ CLI: `managed-get`  · _Bot API 10.0_

Возвращает настройки доступа управляемого бота. Позволяет владельцу управляемого бота узнать, ограничен ли доступ к нему и кто имеет к нему доступ.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Идентификатор пользователя (управляемого бота), чьи настройки доступа запрашиваются |

**Возвращает:** BotAccessSettings

### `setManagedBotAccessSettings` — ✅ CLI: `managed-set`  · _Bot API 10.0_

Изменяет настройки доступа управляемого бота. Позволяет ограничить доступ к боту только выбранными пользователями.


| Параметр | Тип | Обяз. | Примечание |
|---|---|:---:|---|
| `user_id` | Integer | ✅ | Идентификатор пользователя (управляемого бота), чьи настройки будут изменены |
| `is_access_restricted` | Boolean | ✅ | Передать True, чтобы только выбранные пользователи могли обращаться к боту. Владелец бота всегда имеет доступ. |
| `added_user_ids` | Array of Integer | — | Список идентификаторов до 10 пользователей, которым будет разрешён доступ к боту помимо владельца. Игнорируется, если is_access_restricted=false. |

**Возвращает:** True

**⚠️ Грабли:** added_user_ids полностью игнорируется, если is_access_restricted=false. Максимум 10 дополнительных пользователей в списке.
