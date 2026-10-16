---
description: "Тест фронтенда через Playwright MCP: скриншоты 3 viewport, layout, E2E, accessibility. Триггеры: «проверь вёрстку», «скриншот страницы». Фреймворк → playwright-automation."
argument-hint: "<url> [screenshot | e2e | layout | accessibility]"
---

# /test-frontend - Тестирование фронтенда

**Назначение:** Автоматизированное тестирование frontend — проверка вёрстки, E2E тесты, скриншоты, accessibility.

**Когда использовать:**
- Нужно проверить вёрстку на разных разрешениях
- Найти баги в UI
- Сделать screenshot для проверки
- E2E тестирование user flows
- Visual regression testing

**Аргументы:**
- `url` - URL для тестирования (обязательно)
- `test_type` - тип теста: screenshot | e2e | layout | accessibility (по умолчанию: layout)

**Примеры:**
```
/test-frontend http://localhost:3000 screenshot
/test-frontend http://localhost:3000/dashboard layout
/test-frontend http://localhost:3000 e2e
```

---

## Реальные инструменты (выбор пути)

| Путь | Когда | Как |
|------|-------|-----|
| **Плагин playwright** (MCP, дефолт) | Интерактивная проверка здесь и сейчас | Тулы `mcp__plugin_playwright_playwright__browser_*` — см. шаги ниже |
| **Skill `webapp-testing`** | Тестирование локального веб-приложения целиком (запуск сервера + прогон) | `Skill(webapp-testing)` |
| **Skill `playwright-automation`** | Написание постоянных e2e-тестов (spec-файлы), daemon-браузер `bdo.py` для параллельной работы, стелс | `Skill(playwright-automation)` |
| **chrome-devtools MCP** | Accessibility/SEO аудит одним вызовом | `mcp__chrome-devtools__lighthouse_audit` |

Плагин playwright — синглтон-браузер: если он занят другой сессией, бери daemon-браузер из `playwright-automation` (bdo.py).

## Шаги (через плагин playwright)

### 1. Screenshot Testing — 3 viewport

Для каждого разрешения: desktop 1920×1080, tablet 768×1024, mobile 375×667.

1. `browser_navigate(url)`
2. `browser_resize(width, height)`
3. `browser_take_screenshot(fullPage=true, filename="shot_<viewport>.png")`
4. **Смотреть скриншоты глазами** (Read файла) — вердикт по пикселям, не по коду

### 2. Layout Testing

1. `browser_navigate(url)` + `browser_resize(...)` на каждом из 3 viewport
2. `browser_snapshot()` — a11y-дерево: проверь наличие header / nav / footer
3. Горизонтальный скролл на mobile — через `browser_evaluate`:
   ```js
   () => document.documentElement.scrollWidth > document.documentElement.clientWidth
   ```
4. Чек-лист: header visible · nav accessible · footer present · responsive works · no horizontal scroll on mobile

### 3. E2E Testing (user flow)

Типичный флоу логина — снимок → действия по uid/target из снимка:

1. `browser_navigate(url)`
2. `browser_snapshot()` — найти элементы
3. `browser_click(target=<login button>)`
4. `browser_fill_form(fields=[{email...}, {password...}])` — батчем, не по одному
5. `browser_click(target=<submit>)`
6. `browser_wait_for(text="Dashboard")` — дождаться результата
7. `browser_console_messages(level="error")` — JS-ошибки после флоу

Тестовые креды — только тестовые аккаунты, не данные реальных людей.

### 4. Accessibility Testing

Одним вызовом: `mcp__chrome-devtools__lighthouse_audit` (mode=navigation, device=desktop и mobile) — accessibility + SEO + best practices score.
Дополнительно: `browser_snapshot()` — проверка ролей/имён элементов (кнопки без label, картинки без alt).

## Формат отчёта

```markdown
## Frontend Test Report: {url}

### Test Type: {test_type}

### Results:
- ✅ Responsive design: OK
- ✅ Navigation: OK
- ❌ Footer alignment issue on mobile
- ✅ Accessibility score: 92/100

### Screenshots:
- Desktop: [shot_desktop.png]
- Mobile: [shot_mobile.png]

### Issues Found:
1. **Footer misalignment on mobile** (375px width)
   - Element: footer.main-footer
   - Issue: Right padding overflow
   - Fix: Add `padding-right: 0` for mobile

### Recommendations:
1. Fix footer padding on mobile
2. Add alt text to logo image
3. Increase button contrast for accessibility
```

**ВАЖНО:**
- Всегда тестируй на 3 разрешениях: desktop (1920px), tablet (768px), mobile (375px)
- Делай full-page screenshots для context и СМОТРИ их глазами
- Проверяй accessibility (a11y) для production builds
- Указывай конкретные CSS-селекторы для найденных багов
