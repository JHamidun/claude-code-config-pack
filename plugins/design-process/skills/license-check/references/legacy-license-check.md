<!-- LEGACY: полное тело скилла 'license-check' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: license-check
description: Проверка лицензий шрифтов, изображений, иконок, npm-пакетов в артефакте. Чтобы не отправить юзеру дизайн с GPL-шрифтом или Getty-картинкой без апрува.
when_to_use: Перед dev-handoff, особенно если артефакт пойдёт в коммерческий продукт. Также если использовал ассеты из неизвестных источников.
---

# License check

Дизайн с украденными ассетами = юридическая мина. Проверь перед handoff.

## 4 категории ассетов

### 1. Шрифты

| Источник | Лицензия | OK для коммерции? |
|---|---|---|
| Google Fonts (open) | OFL / Apache 2.0 | ✅ Да |
| Adobe Fonts (Creative Cloud) | Adobe Fonts EULA | ✅ Только при активной подписке |
| MyFonts / Fonts.com purchased | Per-license | Зависит от тарифа (web/desktop/app) |
| MyFonts free trial | NOT FOR PRODUCTION | ❌ Нет |
| Скачанный с torrent / pirate | none | ❌ Лицензионный риск |
| Inter / Manrope / JetBrains Mono | OFL | ✅ Да |
| Helvetica Neue | Linotype proprietary | ❌ Без лицензии — нет |
| SF Pro (Apple) | Apple SDK only | ❌ Web-использование запрещено |

**Правило для prototype:** только OFL/Apache. Список безопасных:
- Inter, Inter Tight (OFL)
- Manrope, Geist, Geist Mono (OFL)
- JetBrains Mono (OFL)
- Roboto, Open Sans, Lato (Apache 2.0)
- Space Grotesk, IBM Plex (OFL)
- Noto Sans, Noto Serif (OFL)

**Helvetica / SF Pro заменяй** на:
- Helvetica → Inter / Manrope (Helvetica-like)
- SF Pro → Inter (free SF-replacement)

### 2. Изображения

| Источник | OK? | Условие |
|---|---|---|
| Unsplash | ✅ | Free, attribution не требуется. Но проверь model release для people-shots |
| Pexels | ✅ | Free, attribution не требуется |
| Pixabay | ✅ | Free для commercial |
| Stock Photo Hands (Stocksnap, Burst) | ✅ | Free |
| Getty Images | ❌ | Watermarked = piracy. Купленные — OK |
| Shutterstock | ❌ | Аналогично |
| **Pinterest screenshots** | ❌ | НЕ источник, это reference |
| Reverse image search → unknown source | ⚠️ | Не использовать в prod |
| AI-generated (DALL-E, Midjourney, Gemini Image) | ⚠️ | Зависит от tariff и contract |
| Figma Community freebies | ⚠️ | Per-asset license — проверять |

### 3. Иконки

| Источник | Лицензия |
|---|---|
| Lucide / Lucide-react | ISC ✅ |
| Heroicons | MIT ✅ |
| Phosphor Icons | MIT ✅ |
| Feather Icons | MIT ✅ |
| Tabler Icons | MIT ✅ |
| Iconify | per-icon (mix) |
| FontAwesome (free tier) | OFL + MIT ✅ для free-tier |
| FontAwesome Pro | требует подписку |
| Material Symbols | Apache 2.0 ✅ |
| Custom SVG из Figma Community | per-component |

### 4. npm dependencies

Проверка через:
```bash
npx license-checker --production --summary
# или
npx license-checker --production --excludePrivatePackages --json > licenses.json
```

Категории:
- ✅ Permissive (MIT, Apache 2.0, BSD, ISC) — OK для commercial
- ⚠️ Copyleft (GPL, AGPL, LGPL) — может потребовать open-sourcing
- ❌ Custom / unknown → проверять вручную

## Output отчёт

`licenses.md` или комментарий рядом с handoff:

```markdown
# License audit — ExampleProduct Landing

## Fonts
- Inter Tight — OFL ✅
- Manrope — OFL ✅
- JetBrains Mono — OFL ✅
- (нет Helvetica или SF Pro)

## Images
- uploads/user_portrait.jpeg — own (юзер прислал) ✅
- uploads/hero_main.png — own ✅
- (нет stock без апрува)

## Icons
- Все иконки в components/icons.jsx — кастомные SVG (own) ✅
- Если использовать Lucide — добавить attribution в LICENSE-NOTICES.txt

## Dependencies (если артефакт идёт в build)
- React 18 — MIT ✅
- ReactDOM — MIT ✅
- Babel standalone — MIT ✅

## Risks
- Нет.

## Action items
- Нет.
```

## Когда нашёл проблему

```markdown
## Risks (FIX BEFORE HANDOFF)

1. uploads/stock-business-meeting.jpg — Shutterstock watermark visible
   → Заменить на Unsplash equivalent или собственное фото
2. Шрифт Helvetica Neue в tokens.css
   → Заменить на Inter (free, Helvetica-like): уже в `--font-body`
3. Иконка GitHub из неизвестного источника (uploads/gh-logo.svg)
   → Использовать GitHub Brand SVG из их Brand Toolkit (надо link)
```

## Привязка к dev-handoff

В `dev-handoff` пакете обязательно `LICENSES.md`:
```markdown
This bundle uses third-party assets:
- Inter Tight — © 2018 The Inter Project Authors. SIL Open Font License
- Manrope — © 2018 OSS Author. SIL Open Font License
- Lucide icons — © 2020 Lucide Contributors. ISC License
```

## Антипаттерны

- Использовать «бесплатные ресурсы» с torrent-сайтов → юр. риск
- Adobe Fonts в demo, но клиент не платит CC subscription → demo ≠ prod
- Скриншоты конкурентов как ассеты → copyright infringement
- AI-generated без прочтения terms (DALL-E, Imagen, Gemini) → каждый tariff разный
- Не сохранять source / прямую ссылку у каждого ассета → теряется provenance
- Не делать license-check на длинных проектах → накапливается legacy с риском
- Использовать MyFonts trial-licenses в production → trial expires, всё блокирует
