---
description: Генерация документации из кода с примерами
argument-hint: [путь к файлу или модулю]
---

# 📖 Documentation: $ARGUMENTS

Создай документацию для: **$ARGUMENTS**

## Process:

### 1. Code Analysis
- Читай код и комментарии
- Определи API endpoints, функции, классы
- Найди примеры использования

### 2. Generate Docs
**Для API:**
- API Reference (endpoints, methods, parameters)
- Request/Response examples
- Authentication requirements
- Error codes и descriptions

**Для Modules/Classes:**
- Purpose и overview
- Public API
- Constructor/initialization
- Methods с параметрами
- Usage examples

### 3. Format Output

**Выбери формат:**
- **Markdown** для README
- **.docx** для formal specifications — `python-docx`, готовый пример: `skills/seo-machine-ru/scripts/build_report_docx.py`
- **api-documentation skill** для OpenAPI/Swagger
- **Notion** для team wiki (если Notion MCP настроен)

### 4. Include Examples

```python
# Example usage
from mymodule import MyClass

client = MyClass(api_key="...")
result = client.do_something(param="value")
print(result)
```

```javascript
// Example usage
const client = new MyClass({ apiKey: '...' });
const result = await client.doSomething({ param: 'value' });
console.log(result);
```

```bash
# CLI example
mycli command --param value
```

## Output:

1. **Documentation file(s)** в выбранном формате
2. **Code comments** improvements (если нужно)
3. **README updates** (если есть)
4. **API spec** (OpenAPI/Swagger если API)

## Examples:

```
/docs ./backend/api/main.py
/docs ./telegram-bot/handlers/
/docs ./frontend/src/components/UserProfile.tsx
```

**Создаю документацию! 📖**
