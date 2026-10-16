---
description: "Глубокий reasoning через Kimi (модель kimi-k3): алгоритмы, трудные баги, архитектура, математика. Триггеры: «спроси kimi». Агент-обёртка → kimi-algorithm-specialist."
argument-hint: "<problem>"
---

# /kimi-reasoning - Глубокий анализ с Kimi K3

**Назначение:** Используй Kimi (модель `kimi-k3`) для глубокого reasoning и анализа сложных проблем.

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

Ты используешь **Kimi** (модель `kimi-k3` у Moonshot AI) — специализированную модель для reasoning.

**Преимущества Kimi K3:**
- 🎯 Сильна на coding benchmarks. ⚠️ Цифры SWE-bench 65.8% / LiveCodeBench 53.7% —
  замеры **K2**; K3 ими не мерилась, владельцу их как «результаты K3» НЕ приводить
- 🧠 Очень длинный контекст (`kimi-k3` принял 678K prompt-токенов, замер 22.08.2026)
- 💡 Отлично для: coding, debugging, test generation, math reasoning
- 💰 Заметно дешевле флагманов OpenAI на coding-задачах (кратность не сверялась —
  сравнение с GPT-4 устарело, модели в прайсе нет)

**Шаги:**

1. **Получи problem** из аргументов команды
2. **Сформируй запрос** к Kimi K3 API (OpenAI-compatible):
   ```python
   import os
   from openai import OpenAI

   client = OpenAI(
       api_key=os.getenv('KIMI_API_KEY'),
       base_url='https://api.moonshot.ai/v1'
   )

   response = client.chat.completions.create(
       model='kimi-k3',  # reasoning-модель; kimi-k2-thinking снята — на неё API отдаёт 404
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
   ## 🧠 Kimi K3 Reasoning: {problem title}

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