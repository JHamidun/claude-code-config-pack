# /kimi-reasoning - Глубокий анализ с Kimi K2

**Назначение:** Используй Kimi K2 (k2-thinking модель) для глубокого reasoning и анализа сложных проблем.

**Когда использовать:**
- Сложные алгоритмические задачи
- Debugging трудных багов
- Архитектурные решения
- Математические задачи
- Code optimization стратегии

**Аргументы:**
- `problem` - описание проблемы или задачи (обязательно)

**Пример использования:**
```
/kimi-reasoning Why is my async function deadlocking in Python?
/kimi-reasoning Optimal data structure for real-time chat with 1M users
/kimi-reasoning Best approach to migrate from SQLite to PostgreSQL with zero downtime
```

---

## Задача для агента

Ты используешь **Kimi K2** (k2-thinking модель) - специализированную модель для reasoning с **1 trillion параметров** (MoE архитектура, 32B активных).

**Преимущества Kimi K2:**
- 🎯 Top results на coding benchmarks (SWE-bench: 65.8%, LiveCodeBench: 53.7%)
- 🧠 128K контекстное окно
- 💡 Отлично для: coding, debugging, test generation, math reasoning
- 💰 ~10x дешевле чем GPT-4 для coding tasks

**Шаги:**

1. **Получи problem** из аргументов команды
2. **Сформируй запрос** к Kimi K2 API (OpenAI-compatible):
   ```python
   import os
   from openai import OpenAI

   client = OpenAI(
       api_key=os.getenv('KIMI_API_KEY'),
       base_url='https://api.moonshot.ai/v1'
   )

   response = client.chat.completions.create(
       model='kimi-k2-thinking',  # Включает chain-of-thought reasoning
       messages=[
           {
               'role': 'system',
               'content': 'Ты expert в reasoning и problem-solving. Используй step-by-step анализ для решения сложных проблем.'
           },
           {
               'role': 'user',
               'content': problem
           }
       ],
       temperature=0.7,
       max_tokens=8000
   )

   answer = response.choices[0].message.content
   ```

3. **Верни детальный анализ** в формате:
   ```markdown
   ## 🧠 Kimi K2 Reasoning: {problem title}

   ### Анализ проблемы:
   {step-by-step breakdown}

   ### Рассуждение:
   {reasoning process}

   ### Решение:
   {proposed solution with code examples if applicable}

   ### Альтернативы:
   {other approaches to consider}

   ### Рекомендации:
   {best practices and next steps}
   ```

**ВАЖНО:**
- Используй chain-of-thought reasoning
- Покажи промежуточные шаги
- Объясни "почему", а не только "как"