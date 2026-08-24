---
name: zoom
description: "Zoom через Server-to-Server OAuth: создание и правка встреч, записи. Триггеры: «зум», «создай встречу zoom»."
triggers:
  - zoom
  - зум
  - zoom meeting
  - создай встречу
  - zoom call
  - запланируй зум
  - zoom recording
  - записи зум
---

# Zoom API Skill

## Authentication

Server-to-Server OAuth (no user consent needed).

### Credentials (from ~/.claude/.credentials.master.env)

```
ZOOM_ACCOUNT_ID=
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
```

Шаблон файла — `~/.claude/templates/.credentials.master.env.example`, эти три строки в нём уже есть.

**Откуда взять (10 минут, один раз).** Нужны права **администратора** аккаунта Zoom —
без них Server-to-Server приложение создать нельзя, и это самая частая причина «не получается».

1. `marketplace.zoom.us` → войти своей учёткой Zoom (браузером; пароль в env-файле не хранить).
2. **Develop → Build App → Server-to-Server OAuth**.
3. Имя приложения любое (оно видно только админам аккаунта).
4. Вкладка **App Credentials** → оттуда Account ID, Client ID, Client Secret → в env-файл.
5. Вкладка **Scopes** → добавить только нужные (список в конце файла, «Свой аккаунт — что проверить»).
   Скоупы гранулярные: «дать все» в S2S-приложении нельзя.
6. Вкладка **Activation** → Activate. Без активации токен выдаётся, а вызовы падают.

### Get Access Token

```bash
curl -s -X POST "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=$ZOOM_ACCOUNT_ID" \
  -u "$ZOOM_CLIENT_ID:$ZOOM_CLIENT_SECRET" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
```

Token is valid for **1 hour**. Cache it and refresh when expired.

### Python Helper

```python
import os, requests, time

_token_cache = {"token": None, "expires": 0}

def get_zoom_token():
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]

    resp = requests.post(
        f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={os.getenv('ZOOM_ACCOUNT_ID')}",
        auth=(os.getenv('ZOOM_CLIENT_ID'), os.getenv('ZOOM_CLIENT_SECRET')),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires"] = time.time() + data.get("expires_in", 3600) - 60
    return _token_cache["token"]

def zoom_api(method, endpoint, **kwargs):
    token = get_zoom_token()
    resp = requests.request(
        method,
        f"https://api.zoom.us/v2{endpoint}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        **kwargs
    )
    return resp.json() if resp.content else {"status": resp.status_code}
```

## API Reference

### Meetings

#### Create Meeting

```python
zoom_api("POST", "/users/me/meetings", json={
    "topic": "Team Standup",
    "type": 2,  # 1=instant, 2=scheduled, 3=recurring_no_fixed, 8=recurring_fixed
    "start_time": "2026-03-10T10:00:00Z",
    "duration": 30,  # minutes
    "timezone": "UTC",
    "agenda": "Daily sync",
    "settings": {
        "host_video": True,
        "participant_video": True,
        "join_before_host": True,
        "mute_upon_entry": True,
        "auto_recording": "cloud",  # none, local, cloud
        "waiting_room": False,
        "meeting_authentication": False
    }
})
# Returns: { "id": 123456789, "join_url": "https://us06web.zoom.us/j/...", "start_url": "...", "password": "..." }
```

#### List Meetings

```python
zoom_api("GET", "/users/me/meetings", params={"type": "upcoming", "page_size": 30})
# type: scheduled, live, upcoming, upcoming_meetings, previous_meetings
```

#### Get Meeting

```python
zoom_api("GET", f"/meetings/{meeting_id}")
```

#### Update Meeting

```python
zoom_api("PATCH", f"/meetings/{meeting_id}", json={
    "topic": "Updated Topic",
    "start_time": "2026-03-10T11:00:00Z"
})
```

#### Delete Meeting

```python
zoom_api("DELETE", f"/meetings/{meeting_id}")
```

#### Get Meeting Invitation

```python
zoom_api("GET", f"/meetings/{meeting_id}/invitation")
# Returns text invitation with join link, dial-in numbers
```

### Recordings

#### List Recordings

```python
zoom_api("GET", f"/users/me/recordings", params={
    "from": "2026-03-01",
    "to": "2026-03-08",
    "page_size": 30
})
```

#### Get Meeting Recordings

```python
zoom_api("GET", f"/meetings/{meeting_id}/recordings")
# Returns download URLs for video, audio, transcript
```

#### Download a SHARE recording (чужая запись по ссылке + passcode)

API выше работает только для записей **твоего** аккаунта. Если есть только **share-ссылка + passcode** (чужая запись, прислали в чат) — API не поможет, а **yt-dlp НЕ умеет Zoom share-формат** (`Unable to extract data`). Качай через headless Playwright (перехват сетевого .mp4):

```python
# 1) page.goto(share_url) → page.wait_for_selector('#passcode') → fill(passcode) → click('#passcode_btn')
# 2) page.on('response'): копить url, где есть 'ssrweb.zoom.us' + '.mp4' (сам файл),
#    и 'rec/play/vtt?type=cc' (авто-субтитры VTT). Реальный mp4 — на ssrweb.zoom.us (4K ~1.5 ГБ / 3 ч).
# 3) ctx.cookies() → requests.get(mp4_url, cookies=..., headers={'Referer':'https://us06web.zoom.us/'}, stream=True)
# Селекторы Vue-страницы пароля: поле #passcode, кнопка #passcode_btn (дождись рендера wait_for_selector).
```
Рабочий референс: `presentations/company-mastermind/_download_zoom.py` + `_dl_mp4.py`. Дальше — транскрипт через skill `deepgram` (REST); сборка пакета по спикерам делается своим скриптом (в пак не входит).

#### Delete Recording

```python
zoom_api("DELETE", f"/meetings/{meeting_id}/recordings")
```

### Users

#### Get Current User

```python
zoom_api("GET", "/users/me")
# Returns: email, first_name, last_name, pmi, timezone, etc.
```

#### List Users

```python
zoom_api("GET", "/users", params={"status": "active", "page_size": 30})
```

### Reports

#### Meeting Report

```python
zoom_api("GET", f"/report/meetings/{meeting_id}")
# Participants, duration, etc.
```

#### Meeting Participants Report

```python
zoom_api("GET", f"/report/meetings/{meeting_id}/participants", params={"page_size": 30})
```

### Dashboard

#### Meeting Live Status

```python
zoom_api("GET", "/metrics/meetings", params={"type": "live"})
```

## Meeting Types

| Type | Description |
|------|-------------|
| 1 | Instant meeting |
| 2 | Scheduled meeting |
| 3 | Recurring meeting (no fixed time) |
| 8 | Recurring meeting (fixed time) |

## Recurrence

```python
"recurrence": {
    "type": 2,       # 1=daily, 2=weekly, 3=monthly
    "repeat_interval": 1,
    "weekly_days": "2,4",  # 1=Sun..7=Sat (Mon+Wed)
    "end_times": 10   # end after N occurrences
}
```

## Timezones

Use IANA format: `Europe/Moscow`, `Europe/Berlin`, `America/New_York`, `Asia/Almaty`, `UTC`.

Свой пояс — тот, в котором думают участники, а не тот, в котором стоит сервер: Zoom печатает
время приглашения именно в `timezone` встречи. Пропустишь поле — возьмётся пояс из профиля
владельца токена (`GET /users/me` → `timezone`), и встреча уедет на несколько часов.

## Common Patterns

### Quick Meeting (instant)

```bash
# One-liner to create and get join URL
source ~/.claude/.credentials.master.env
TOKEN=$(curl -s -X POST "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=$ZOOM_ACCOUNT_ID" \
  -u "$ZOOM_CLIENT_ID:$ZOOM_CLIENT_SECRET" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -X POST "https://api.zoom.us/v2/users/me/meetings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"topic":"Quick Meeting","type":1}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'Join: {d[\"join_url\"]}')"
```

### Schedule Weekly Standup

```python
zoom_api("POST", "/users/me/meetings", json={
    "topic": "Weekly Standup",
    "type": 8,
    "start_time": "2026-03-10T10:00:00",
    "duration": 30,
    "timezone": "UTC",
    "recurrence": {
        "type": 2,
        "repeat_interval": 1,
        "weekly_days": "2,3,4,5,6",  # Mon-Fri
        "end_times": 52
    },
    "settings": {
        "join_before_host": True,
        "auto_recording": "cloud"
    }
})
```

## Rate Limits

- Light: 30 req/sec (GET list)
- Medium: 20 req/sec (GET single)
- Heavy: 10 req/sec (POST/PATCH/DELETE)
- Resource-intensive: 5 req/sec (reports)

## Свой аккаунт — что проверить

Всё ниже узнаётся из своего же кабинета, наизусть держать не надо.

- **Кто я для API:** `zoom_api("GET", "/users/me")` → email, PMI, `timezone`, тип лицензии.
  Первый вызов после настройки делай именно этот: он же и проверка креденшелов.
- **Лимиты тарифа** (сколько участников, сколько длится встреча, есть ли облачная запись)
  — `marketplace.zoom.us` → Account → Plans. На бесплатном тарифе **облачной записи нет**,
  и половина рецептов ниже (`cloud_recording:*`, `auto_recording: "cloud"`) молча не сработает.
- **Ссылка на своё приложение:** `https://marketplace.zoom.us/develop/apps/<app_id>` —
  app_id виден в адресной строке, когда приложение открыто.

**Скоупы — гранулярные, «выдать все» нельзя.** Минимальный набор под этот навык:

```
meeting:write:meeting:admin        meeting:read:meeting:admin
meeting:delete:meeting:admin       meeting:read:list_meetings:admin
meeting:read:invitation:admin      user:read:user:admin
cloud_recording:read:list_recording_files:admin
cloud_recording:read:list_user_recordings:admin
```

⚠️ **Гоча.** Ответ `4711 does not contain scopes` означает ровно одно: у приложения нет
нужного скоупа — креденшелы и токен тут ни при чём. Починка: marketplace.zoom.us (вход
браузером под админом аккаунта) → своё приложение → **Scopes → Add Scopes** → искать
**по точному id из ошибки**, а не по названию раздела → чекбокс → Done. Изменение
сохраняется само, переактивация приложения не нужна, новый токен — нужен.
