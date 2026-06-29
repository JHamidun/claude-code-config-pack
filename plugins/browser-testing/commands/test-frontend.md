# /test-frontend - Тестирование фронтенда с Playwright

**Назначение:** Автоматизированное тестирование frontend с помощью Playwright MCP - проверка верстки, E2E тесты, скриншоты.

**Когда использовать:**
- Нужно проверить верстку на разных разрешениях
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

## Задача для агента

Используй **Playwright MCP server** для автоматизированного тестирования фронтенда.

**Шаги:**

### 1. Screenshot Testing
```python
# Через Playwright MCP
await playwright_client.screenshot(
    url=url,
    viewports=[
        {"width": 1920, "height": 1080},  # Desktop
        {"width": 768, "height": 1024},   # Tablet
        {"width": 375, "height": 667}     # Mobile
    ],
    full_page=True
)
```

### 2. Layout Testing
```python
# Проверка основных элементов
tests = [
    "header visible",
    "navigation menu accessible",
    "footer present",
    "responsive design works",
    "no horizontal scroll on mobile"
]

for test in tests:
    result = await playwright_client.test_element(url, test)
    print(f"✅ {test}" if result else f"❌ {test}")
```

### 3. E2E Testing
```python
# Типичный user flow
await playwright_client.run_flow([
    {"action": "goto", "url": url},
    {"action": "click", "selector": "#login-button"},
    {"action": "fill", "selector": "#email", "value": "test@example.com"},
    {"action": "fill", "selector": "#password", "value": "password123"},
    {"action": "click", "selector": "#submit"},
    {"action": "waitForSelector", "selector": "#dashboard"}
])
```

### 4. Accessibility Testing
```python
# Проверка доступности
accessibility_report = await playwright_client.check_accessibility(url)
print(f"Issues found: {len(accessibility_report.violations)}")
```

**Формат отчета:**
```markdown
## Frontend Test Report: {url}

### Test Type: {test_type}

### Results:
- ✅ Responsive design: OK
- ✅ Navigation: OK
- ❌ Footer alignment issue on mobile
- ✅ Accessibility score: 92/100

### Screenshots:
- Desktop: [screenshot_desktop.png]
- Mobile: [screenshot_mobile.png]

### Issues Found:
1. **Footer misalignment on mobile** (768px width)
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
- Делай full-page screenshots для context
- Проверяй accessibility (a11y) для production builds
- Указывай конкретные CSS селекторы для найденных багов