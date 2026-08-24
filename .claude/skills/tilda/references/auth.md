# Tilda — авторизация

## Логин

Логин пользователя — на `https://tilda.cc/login/`. После успеха идёт редирект на `tilda.ru/projects/`.

Креды берутся из переменных окружения (или своего `~/.claude/.credentials.master.env`,
образец — `~/.claude/templates/.credentials.master.env.example`):
```
TILDA_EMAIL      — свой email от аккаунта Tilda
TILDA_PASSWORD   — свой пароль
```
В коде читать через `os.getenv('TILDA_EMAIL')` / `os.getenv('TILDA_PASSWORD')`.

## Как залогиниться через Playwright

```javascript
await page.goto('https://tilda.cc/login/');
// Если поля уже автозаполнены (Edge/Chrome):
await page.click('button:has-text("Войти")');
// Иначе вводи вручную перед кликом
```

## Капча

Иногда появляется Yandex SmartCaptcha — программно не решается. Если попалась — лучше оставить открытое окно браузера и попросить пользователя пройти капчу руками.

## Домены

Tilda — двойной домен: `tilda.cc` (международный) и `tilda.ru` (РФ). Сессия после `tilda.cc/login/` действует для обоих, но иногда страница говорит «В предыдущий раз вы работали на домене tilda.ru» — просто продолжай, всё работает.

## Session cookies

После логина сессионные куки хранятся для:
- `tilda.cc` / `tilda.ru` — основные операции
- `feeds.tilda.ru` — Потоки/Feeds API
- `upload.tildacdn.com` — загрузка файлов на CDN

Если делаешь запросы из Playwright `evaluate` на странице feeds.tilda.ru — `credentials:'include'` автоматически берёт куки. В Python придётся передавать `cookies` руками после логина.

## ⚠️ Handshake-цепочка для feeds.tilda.ru (RELOGIN gotcha)

**Симптом:** залогинен на tilda.cc/login → tilda.ru/projects/ работает, но `feeds.tilda.ru/submit/` отвечает `{"error": "RELOGIN"}` или `feeds.tilda.ru/posts/?feeduid=...` редиректит обратно на `tilda.ru/projects/`.

**Причина:** просто `tilda.cc` PHPSESSID + `feeds.tilda.ru` PHPSESSID недостаточно — feeds-сессия валидна только после прогрева через page editor. Tilda устанавливает feeds-куки в момент когда ты открываешь конкретную страницу проекта.

**Лечение — handshake перед любым `feeds.tilda.ru` запросом (порядок важен):**

```python
HANDSHAKE_URLS = [
    f'https://tilda.cc/projects/projectinfo/?projectid={PROJECTID}',
    f'https://tilda.cc/projects/manage/?projectid={PROJECTID}',
    f'https://tilda.cc/page/?pageid={ANY_PAGEID}&projectid={PROJECTID}',  # КЛЮЧЕВОЙ шаг
    f'https://feeds.tilda.ru/feeds/?projectid={PROJECTID}',
    f'https://feeds.tilda.ru/posts/?feeduid={FEEDUID}&projectid={PROJECTID}',
]
for url in HANDSHAKE_URLS:
    page.goto(url, wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(1500)
    if 'feeds.tilda.ru/posts' in page.url and 'feeduid' in page.url:
        break  # ✓ session propagated
```

Без шага через `tilda.cc/page/?pageid=...` (любой реальный pageid проекта) feeds.tilda.ru не доверяет сессии. Это вероятно потому что page editor вызывает внутренний bridge что устанавливает feeds-cookies.

**Альтернатива в Python через requests:** не работает. Cookies для feeds.tilda.ru, полученные после логина в Playwright, RELOGIN-ятся при использовании в `requests.Session`. Только in-page `fetch('/submit/', credentials:'include')` из feeds.tilda.ru origin работает надёжно.

**Проверено:** 2026-04-25 на webinar covers v6 pipeline. 46 постов МЕРОПРИЯТИЯ обновлены через этот handshake.

## Python — сохранить cookies после логина

```python
import os
import requests

s = requests.Session()
# Сначала GET логин-страницу для CSRF (может потребоваться)
s.get('https://tilda.cc/login/')
# Логин (внимание — формат POST может меняться, рекомендую снять реальный запрос)
r = s.post('https://tilda.cc/login/', data={
    'email': os.getenv('TILDA_EMAIL'),
    'password': os.getenv('TILDA_PASSWORD'),
}, allow_redirects=True)
# Если капча — сюда придёт HTML с капчей и логин не пройдёт
print(r.url)  # ожидаем tilda.ru/projects/

# Теперь s используется для всех остальных запросов
list_resp = s.post('https://feeds.tilda.ru/submit/', data={
    'action': 'posts_GetList',
    'feeduid': '100000000001',
    'partuid': '',
    'page': 1,
    'items': 50,
})
```

**Альтернатива:** скопировать куки из браузера после ручного логина. Самый надёжный способ когда есть капча.

```python
# Cookies dict из DevTools → Application → Cookies
COOKIES = {
    'tildauid': '...',
    'PHPSESSID': '...',
    # ...
}
s = requests.Session()
s.cookies.update(COOKIES)
```

## Ограничения сессии

- Сессия живёт ~30 дней при regular использовании
- При неактивности 7+ дней — может потребоваться повторный логин
- Капча может появиться рандомно (особенно из новых IP)

## Через Playwright — самый надёжный путь

Если нужна стабильная автоматизация — держи Playwright sesesion открытой 24/7 в фоне, делай все API-вызовы через `page.evaluate(async () => fetch('/submit/', ...))` — куки автоматически.
