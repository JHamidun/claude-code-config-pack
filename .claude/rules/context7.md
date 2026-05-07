# Context7 AUTO-INVOKE

Когда спрашивают про:
- Библиотеки/фреймворки (React, FastAPI, Django, etc.)
- API документацию
- Генерацию кода с конкретными библиотеками
- Настройку и конфигурацию

Always use the Context7 plugin (`mcp__plugin_context7_context7__*`) for current docs:
1. `mcp__plugin_context7_context7__resolve-library-id` для библиотеки
2. `mcp__plugin_context7_context7__get-library-docs` для документации
3. Только потом отвечай с актуальным кодом

Training data may be outdated for library-specific code — Context7 returns current documentation.
