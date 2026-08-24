# Яндекс.Диск REST — рабочий рецепт заливки пакета

Канон Диска раздвоен намеренно, чтобы не держать две расходящиеся копии:

- **Доступы, полный список эндпоинтов, обновление протухшего токена** → скилл `yandex`
  (тело + `references/api-endpoints.md`, раздел «4. Disk API»). Туда же — гоча
  «upload двухшаговый и PUT только RAW BODY»: `requests.put(href, files={...})`
  создаёт ПУСТОЙ файл и при этом возвращает 201 OK.
- **Здесь** — последовательность вызовов под задачу «залить пакет вебинара папкой и
  отдать публичную ссылку»: чего в таблице эндпоинтов не видно, потому что таблица
  описывает методы поштучно, а не сценарий.

Токен `YANDEX_OAUTH_TOKEN` — свой, из переменных окружения (как получить — скилл `yandex`).
API `https://cloud-api.yandex.net/v1/disk`, заголовок `Authorization: OAuth <token>`.

```python
H={"Authorization":f"OAuth {os.getenv('YANDEX_OAUTH_TOKEN')}"}; API="https://cloud-api.yandex.net/v1/disk"
# mkdir (рекурсии нет — создавать родителя, потом подпапки): 201 создано / 409 уже есть — оба ОК
requests.put(f"{API}/resources", headers=H, params={"path":"/Папка"})
# upload: получить href → PUT файл СЫРЫМ ТЕЛОМ (не files=, иначе размер 0)
href=requests.get(f"{API}/resources/upload",headers=H,params={"path":"/Папка/файл.pdf","overwrite":"true"}).json()["href"]
requests.put(href, data=open("file.pdf","rb"))
# publish папку → публичная ссылка (public_url приходит НЕ из publish, а следующим GET)
requests.put(f"{API}/resources/publish",headers=H,params={"path":"/Папка"})
url=requests.get(f"{API}/resources",headers=H,params={"path":"/Папка","limit":0}).json()["public_url"]
# удалить навсегда, мимо корзины: 202 = принято асинхронно, это успех
requests.delete(f"{API}/resources",headers=H,params={"path":"/Папка/Подпапка","permanently":"true"})
# обойти дерево: GET /resources → _embedded.items[] (поле type: dir | file)
```

Проверка после заливки обязательна: `GET /resources?path=...&fields=size,mime_type`.
`size: 0` означает, что файл ушёл не сырым телом — перезалить.

Кириллица в путях работает, экранировать вручную не нужно.
