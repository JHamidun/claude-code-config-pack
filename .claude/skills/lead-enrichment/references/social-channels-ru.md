# Social channels — RU + Western coverage map

Person-leg of Mode A. For a name / handle / phone / company, search across all networks.
`scripts/social_discover.py` emits the per-network plan; run the connector commands / searches it lists.

## Coverage

| Network | Audience | Connector / method | Search by |
|---------|----------|--------------------|-----------|
| **VK** (vk.com) | RU mass + pro | `vk_lookup.py` (`users.search`/`users.get`, token LIVE) · public profile · `WebSearch site:vk.com` | name+city+company, screen_name |
| **Сетка** (setka by VK) | RU professional (LinkedIn-rival) | public profile via WebFetch · `WebSearch site:setka.ru` (or сетка.рф) | name, company |
| **TenChat** (tenchat.ru) | RU business / personal brand | public profile `tenchat.ru/<username>` via WebFetch · `WebSearch site:tenchat.ru` | name, skills, geo |
| **MAX** (max.ru / oneme) | RU messenger | `max_client.py` (`public-search`, `search-phone`, `user-info`) | phone, username, name |
| **Telegram** | RU + global | `tg_client.py` (`search`, `user-info`, `mentions`); `phone_identify.py` for a phone the lead gave you | @username, name, phone (consented) |
| **Odnoklassniki** (ok.ru) | RU mass (older) | public profile via WebFetch · `WebSearch site:ok.ru` | name |
| **Habr / vc.ru** | RU tech/business authors | `WebSearch site:habr.com`, `site:vc.ru` "<name>" | author name |
| **hh.ru** | RU resumes/employers | `headhunter` skill | name, role, city |
| LinkedIn / Instagram / Facebook / X / TikTok / YouTube / Threads / Bluesky | Western + global | `social-intel`, `linkedin` (ScraperVendor) | handle, name |

## VK access — LIVE (`VK_ACCESS_TOKEN` stored, non-expiring)

`scripts/vk_lookup.py` calls `users.search` (q=name, +city/company/position) and `users.get` (by
screen_name/id), returning city, occupation, career, education, screen_name. Token obtained via the
Kate-Mobile implicit flow (app_id 2685278, scope `friends groups offline`), saved as `VK_ACCESS_TOKEN`.
Public profiles only — VK enforces each user's privacy.

```bash
python scripts/vk_lookup.py --q "John Doe" --company "крупный банк" --city Москва
python scripts/vk_lookup.py --screen-name durov
```

## Search patterns (no-API networks)

```
WebSearch '"<ФИО>" site:vk.com'
WebSearch '"<ФИО>" <компания> site:tenchat.ru'
WebSearch '"<ФИО>" site:setka.ru OR site:сетка.рф'
WebSearch '"<ФИО>" site:ok.ru'
WebSearch '"<ФИО>" <компания>'        # generic — catches личный сайт, СМИ, конференции
```

When a public profile URL is found → WebFetch it for role/bio/contacts → feed into the dossier and `scoring.md`.

## Order

1. Programmatic first (cheap, exact): MAX (`search-phone`/`public-search`), Telegram (`search`/`user-info`), hh (`headhunter`), Western (`social-intel`).
2. RU no-API (VK/Сетка/TenChat/OK): `WebSearch site:` → WebFetch the profile.
3. Cross-check: same person across ≥2 networks → High confidence (`scoring.md`).
