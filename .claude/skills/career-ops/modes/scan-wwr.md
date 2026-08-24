# Modo: scan-wwr — We Work Remotely Scanner (Global Remote)

Сканирует We Work Remotely через RSS-фиды категорий. Простой парсинг XML, нет auth.

## RSS Endpoints

WWR публикует вакансии через отдельные RSS по категориям:

| Категория | URL | Для кого |
|-----------|-----|----------|
| Management & Finance | `https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss` | **CPO / VP / Director** |
| Product | `https://weworkremotely.com/categories/remote-product-jobs.rss` | **Head of Product / Senior PM** |
| Programming | `https://weworkremotely.com/categories/remote-programming-jobs.rss` | Tech roles |
| Devops & SysAdmin | `https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss` | — |
| Design | `https://weworkremotely.com/categories/remote-design-jobs.rss` | — |
| All | `https://weworkremotely.com/remote-jobs.rss` | Полный поток |

## RSS Structure

```xml
<item>
  <title>Acme AI: Head of Product</title>
  <link>https://weworkremotely.com/remote-jobs/acme-ai-head-of-product</link>
  <description><![CDATA[<strong>Headquarters:</strong> USA<br><strong>URL:</strong> https://acme.ai<br><p>Full HTML description...</p>]]></description>
  <pubDate>Sat, 05 Apr 2026 10:00:00 +0000</pubDate>
  <guid>https://weworkremotely.com/remote-jobs/acme-ai-head-of-product</guid>
  <region>Anywhere in the World</region>
  <category>Full-Stack Programming</category>
</item>
```

## Workflow

1. **Read config**: `portals.yml` → `wwr` section
2. **Read dedup**: `data/scan-history.tsv`

3. **Fetch приоритетные категории**:
   - Management & Finance (для CPO/VP)
   - Product (для PM/Head of Product)
   - Optionally Programming (если targeting Senior Eng Manager)

4. **Parse RSS** через WebFetch:
   - Извлечь `<item>` блоки
   - Из каждого: `title`, `link`, `description`, `pubDate`, `region`, `category`
   - Title часто в формате `"Company: Role"` — разделить по `:` для `company` + `position`

5. **Apply filters:**
   - Title positive/negative
   - Published within last 14 days (проверить `pubDate`)
   - Dedup по `link`

6. **Для новых вакансий:**
   - Добавить в `pipeline.md`: `- [ ] {link} | {company} | {position} | {region}`
   - Записать в `scan-history.tsv`

7. **Output:**

```
We Work Remotely Scan — {YYYY-MM-DD}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Categories: Management & Finance, Product, Programming
Found: N total
Filtered: N relevant
Duplicates: N
New: N

  + {company} | {position} | {region}
  ...
```

## WWR-specific notes

- RSS — кеш 5-10 минут, не бомбить
- Зарплата не в структурированном поле — парсить из HTML description
- Region `Anywhere in the World` = глобально (идеально), `USA Only` / `Europe Only` = с ограничением
- Описания содержат `<strong>Headquarters:</strong>` — парсить для истинной локации компании
- Вакансии висят 30 дней и снимаются — свежие RSS содержат только активные
- Нет структурированных тегов — использовать ключевые слова из description для скоринга
