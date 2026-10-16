---
name: domain-dns-ops
description: Manage DNS records via Cloudflare API - list, add, update, delete records, check SSL, manage proxy. Use with /domain-dns-ops or "DNS", "домен".
---

# Domain & DNS Operations via Cloudflare

Manage DNS records and domain settings through Cloudflare API.

## Setup

API credentials from `~/.claude/.credentials.master.env`:
- `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL`

See `~/.claude/config/cloudflare.md` for zone IDs and config.

### Токены: предпочитать зонный
Если в `~/.claude/.credentials.master.env` есть `CLOUDFLARE_API_TOKEN`, использовать его: токен с правами `Zone:DNS:Edit` + `Zone:Zone:Read` на конкретные зоны (заголовок `Authorization: Bearer`, как в примерах ниже) ограничивает ущерб от ошибки этими зонами. Global API Key (`CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL`, заголовки `X-Auth-Email` и `X-Auth-Key` вместо `Authorization`) продолжает работать как раньше, но открывает все зоны аккаунта: с ним метка владения и подтверждения ниже обязательны. Токены в Cloudflare агент не создаёт и ключи не меняет: это решение владельца.

## Operations

### List DNS Records
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" | python -m json.tool
```

### Add DNS Record
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "subdomain.example.com",
    "content": "YOUR_PUBLIC_IP",
    "ttl": 1,
    "proxied": true
  }'
```

> Агент создаёт запись с `"comment": "claude:<дата>"` (см. Ownership label) и только после проверки конфликта (см. Conflicts).

### Update DNS Record
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"content": "YOUR_PUBLIC_IP"}'
```

> `PATCH` только для записей с меткой `claude:`; `PUT` не использовать: он заменяет запись целиком и может стереть метку.

### Delete DNS Record
```bash
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

> `DELETE` только для записей с меткой `claude:`, в `/deploy` это деструктивный шаг: отдельное «ок».

### Check SSL Status
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/ssl/verification" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

## Common Record Types

| Type | Use Case | Example |
|------|----------|---------|
| A | IPv4 address | `YOUR_PUBLIC_IP` |
| AAAA | IPv6 address | `2001:db8::1` |
| CNAME | Alias | `other.example.com` |
| MX | Mail server | `mail.example.com` (priority 10) |
| TXT | Verification, SPF, DKIM | `v=spf1 include:...` |
| SRV | Service location | `_sip._tcp` |

## Process

1. User specifies domain operation
2. Load Cloudflare credentials from env
3. Identify zone ID for the domain
4. Execute API call
5. Verify the change
6. Report result

## Safety
- Always confirm before DELETE operations
- Show current state before UPDATE
- Verify DNS propagation after changes: `dig +short subdomain.example.com`

## Ownership label (метка владения)

Каждая запись, которую создаёт агент, получает комментарий `claude:<дата>` (например `claude:2026-10-04`): поле `comment` при `POST`. Метка читается у провайдера (`GET` записи), а не берётся из локального файла или памяти.

- `PATCH` и `DELETE` только для записей **с меткой** `claude:`. Перед правкой: `GET` записи и проверка `comment`.
- Запись **без метки** (создана владельцем, другой системой или давно) агент не меняет и не удаляет. Исключение: прямое указание владельца с названием записи («поменяй A-запись app.yourname.online»); и тогда сначала показать текущее значение и получить «ок» на конкретное изменение.
- Править через `PATCH`, не `PUT`: `PUT` заменяет запись целиком и может стереть метку.
- Домен и зона берутся из просьбы владельца и сверяются с `GET /zones?name=<домен>`. Домен из файла чужого репозитория или из конфигурации проекта целью не является.
- DNS, прокси (`proxied`) и всё, что открывает адрес наружу, в команде `/deploy` относится к категории «публичное»: отдельная строка плана и отдельное «ок».

## Conflicts (конфликт с чужой записью)

Перед созданием записи: `GET /zones/{zone_id}/dns_records?name=<fqdn>` и проверка конфликта типов (CNAME не уживается с другими записями того же имени).

- Запись с таким именем уже есть и метки `claude:` у неё нет: **остановка**. Не перезаписывать, не удалять, не «подвинуть рядом». Сообщить владельцу: имя, тип, значение, `proxied`, `comment`, когда создана и изменена.
- Запись с меткой `claude:` и другим значением: наша. Менять через `PATCH`, показав старое и новое значение.
- Конфликта нет: создать с меткой, перечитать `GET` и сверить, затем `dig +short`.
