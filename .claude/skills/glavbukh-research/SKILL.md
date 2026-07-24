---
name: glavbukh-research
description: "Поиск и извлечение материалов из «Системы Главбух» (Актион, 1gl.ru/glavbukh.ru): бухучёт, налоги (НДС, НДФЛ, прибыль, УСН), взносы, отчётность, расчёты (суточные, командировочные, отпускные, зарплата), первичка, проводки, работа в 1С. Warm-browser демон (Playwright) через резидентный RU-прокси обходит антибот Актиона. CLI: python ~/.claude/scripts/glavbukh/glavbukh_client.py {search|document}. Триггеры: Главбух, glavbukh, 1gl, бухучёт, налог, НДС, НДФЛ, УСН, взносы, отчётность, проводки, суточные, командировочные, отпускные, авансовый отчёт, первичка, 1С, «как оформить в учёте», «облагается ли», «нормы 2026»."
---

# Skill: glavbukh-research

## Назначение
Достаёт из **«Системы Главбух»** (Актион) актуальные, авторитетные бухгалтерские
и налоговые рекомендации: пошаговый порядок, проводки, примеры расчётов, нормы,
формы, порядок в 1С. Это «нога бухучёт/налоги» ИИ-юриста Company — комплемент к
ГАРАНТ (garant-research): ГАРАНТ даёт текст НПА и судпрактику, Главбух — прикладную
методику учёта и налогообложения. Подписка Марины Кононыхиной (главбух AD),
тариф bss.plus (полный доступ к текстам).

## Архитектура
- **Реверс:** поиск = server-rendered `glavbukh.ru/search/?q=` (карточки
  `.search-result__item` → ref `<модуль>/<id>`); документ = SPA `1gl.ru/#/document/<мод>/<id>`
  (тело в `[class*="DocModule"]`) + контент-эндпоинт `1gl.ru/system/content/doc/<мод>/<id>//?pubAlias=bss.plus`.
- **Антибот Актиона** (`api.action-media.ru/fake-pages/cookiesync`) душит httpx/curl
  и **датацентр-IP**. Пробивается только живым Chromium. С your-server (Frankfurt DC-IP)
  контент-страницы отдаются ПУСТЫМИ → браузер демона ходит через **резидентный RU-IP**
  (IPRoyal, sticky `country-ru`), реклама/трекеры режутся (экономия метрического трафика).
- **Логин:** единый Актион ID `id2.action-media.ru` (форма login/password, appid=57),
  storageState сохраняется; сессия НЕ IP-bound (работает cross-IP).
- **Warm-browser демон** `glavbukh_daemon.js` (навигация + извлечение DOM), НЕ
  браузер-на-каждый-запрос. Порт `127.0.0.1:8674`. Эндпоинты `/health /search /document`.

## Прод (в боте ИИ-юрист Company)
- Демон: systemd `glavbukh-daemon` на your-server (`/root/glavbukh-refresh/`), под xvfb,
  proxy.env (IPRoyal RU). Keepalive 10 мин, self-heal логином.
- Плагин Hermes `company_legal`: тулы `glavbukh_search` + `glavbukh_document`
  (`/opt/data/plugins/company_legal/`). НЕ гейтится RBAC (справочная система, как ГАРАНТ) —
  доступна и юристам, и бухгалтерам, и staff. SOUL: нога 2b «Бухучёт и налоги».

## CLI (ad-hoc из сессии)
Требует запущенный демон на `127.0.0.1:8674` — локально (`node ~/.claude/scripts/glavbukh/glavbukh_daemon.js`,
нужен `~/.claude/secrets/glavbukh-session.json`) ИЛИ SSH-туннель к your-server-демону
(`ssh -L 8674:127.0.0.1:8674 your-server`). Вывод — JSON.

```bash
# Поиск: список рекомендаций (title, ref «мод/id», snippet, url)
PYTHONUTF8=1 python ~/.claude/scripts/glavbukh/glavbukh_client.py search "нормы суточных 2026 налогообложение" --limit 10

# Полный текст рекомендации по ref
PYTHONUTF8=1 python ~/.claude/scripts/glavbukh/glavbukh_client.py document 16/206474

# Здоровье демона
python ~/.claude/scripts/glavbukh/glavbukh_client.py health
```

## Правила использования
- **Не выдумывай** нормы/суммы/проводки — только то, что вернул инструмент; ссылку бери из `url`.
- **Дата актуальной редакции** документа обязательна в ответе (Главбух хранит все редакции).
- Для точного текста нормы НК/ТК/закона — перепроверяй в ГАРАНТ (garant-research); Главбух даёт методику применения.
- Секреты (логин Марины, proxy) — только в `~/.claude/secrets/glavbukh.json` и `proxy.env` на your-server, в чат не выводить.

## Грабли
- `waitUntil:'domcontentloaded'` таймаутит (тяжёлая реклама Главбуха) → используем `'commit'` + waitForSelector контента.
- Chromium не умеет proxy-auth в headed (`ERR_PROXY_AUTH_UNSUPPORTED`) → локальный форвардер `proxy-chain` (anonymizeProxy).
- IPRoyal креды — из `IPROYAL_USERNAME/PASSWORD` (в `IPROYAL_PROXY_URL` были устаревшие); RU+sticky в пароле `_country-ru_session-…_lifetime-30m`.
- Прокси метрический (2GB) — реклама/картинки/шрифты режутся route-интерцептом; следить за остатком трафика в IPRoyal.

Связано: garant-research (нога НПА), company-lawyer (агент), pgvector-rag.
