---
name: mcp-builder
description: "Разработка MCP-серверов (Python FastMCP / TS SDK) и дизайн инструментов агента. Триггеры: «создай MCP», «спроектируй инструменты агента»."
license: Complete terms in LICENSE.txt
type: actionable
---

# MCP Server Development Guide

Качество MCP-сервера меряется не покрытием API, а тем, насколько хорошо LLM решает через него реальные задачи. Процесс — четыре фазы: research → implementation → review → evaluations.

## Phase 1: Research и план

### Agent-centric design (принципы дизайна инструментов)

- **Воркфлоу, а не эндпоинты.** Не оборачивать API 1:1 — консолидировать связанные операции (`schedule_event` = проверить доступность + создать). Инструмент закрывает задачу целиком, иначе агент тратит контекст на склейку вызовов.
- **Контекст агента — дефицит.** Возвращать high-signal, не дампы; давать режимы «concise/detailed»; человекочитаемые идентификаторы вместо технических кодов (имена, не ID).
- **Ошибки — обучающие.** Сообщение об ошибке подсказывает следующий шаг («Try filter='active_only' to reduce results»), а не только диагностирует — так агент учится правильному использованию из фидбека.
- **Имена по естественным задачам**, связанные инструменты — с общим префиксом для discoverability.
- **Evaluation-driven**: реалистичные эвал-сценарии рано, итерации по фактическому поведению агента.

**Развёрнутые Python-примеры к каждому из этих принципов + production-паттерны tool-loop'а** (implicit args injection, error contract «никогда не raise», idempotency, staged vs auto mode, from_cache, MAX_TOOL_ITERATIONS): [🧰 Agent Tool Design Examples](./reference/agent-tool-design-examples.md) — ex-скилл agent-tool-design.

### Документация (загружать в этом порядке)

1. MCP-протокол: WebFetch `https://modelcontextprotocol.io/llms-full.txt`
2. [📋 MCP Best Practices](./reference/mcp_best_practices.md) — naming, форматы ответов, пагинация, лимиты символов, security.
3. Для Python: WebFetch `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md` + [🐍 Python Guide](./reference/python_mcp_server.md).
4. Для TypeScript: WebFetch `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md` + [⚡ TypeScript Guide](./reference/node_mcp_server.md).
5. API интегрируемого сервиса — читать ВСЮ доступную документацию: auth, rate limits, пагинация, коды ошибок, схемы данных.

### План перед кодом

Выбор инструментов (самые ценные операции и их связки в воркфлоу) · общие утилиты (request helper, пагинация, форматирование) · валидация входов (Pydantic / Zod) · форматы ответов (JSON и Markdown, уровни детализации) · лимит и трюнкация ответа (~25 000 токенов) · стратегия ошибок (естественный язык, actionable, с подсказкой действия).

## Phase 2: Implementation

Сначала общая инфраструктура (request helper, error utils, пагинация, auth), потом инструменты — иначе дублирование расползается по каждому tool.

На каждый инструмент:
- **Схема входа**: Pydantic v2 (Python) / Zod `.strict()` (TS), constraints (min/max, regex), описания полей с примерами.
- **Docstring/description**: краткое резюме + когда использовать и когда НЕ использовать + типы параметров с примерами + схема возврата + как действовать при конкретных ошибках.
- **Логика**: async/await для всего I/O, общие утилиты, оба формата ответа, пагинация, проверка лимита символов.
- **Аннотации**: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`.

Языковые детали (структура проекта, регистрация инструментов, полные рабочие примеры, quality checklist) — в соответствующем гайде: [🐍 Python](./reference/python_mcp_server.md) / [⚡ TypeScript](./reference/node_mcp_server.md).

## Phase 3: Review и тест

Ревью: DRY между инструментами, консистентные форматы похожих операций, error handling на каждом внешнем вызове, полное покрытие типами, docstring у каждого инструмента.

**Гоча запуска:** MCP-сервер — долгоживущий процесс, ждущий запросов по stdio; прямой запуск (`python server.py`, `node dist/index.js`) повесит основной процесс навсегда. Тестировать через eval-harness (он сам управляет сервером при stdio), либо в tmux, либо с таймаутом: `timeout 5s python server.py`. Синтаксис до запуска: `python -m py_compile server.py` / `npm run build` без ошибок.

## Phase 4: Evaluations

Полный гайд (создание вопросов, верификация ответов, запуск скриптами): [✅ Evaluation Guide](./reference/evaluation.md).

Создать **10 вопросов**, каждый: независимый · read-only · сложный (несколько вызовов инструментов) · реалистичный · верифицируемый строковым сравнением · со стабильным во времени ответом. Перед фиксацией решить каждый вопрос самому и сверить ответ.

Формат — XML:

```xml
<evaluation>
  <qa_pair>
    <question>...</question>
    <answer>3</answer>
  </qa_pair>
</evaluation>
```

## Quick Reference - Code Examples

Copy-paste skeletons — FastMCP and TypeScript server scaffolds, a fully documented
tool definition, Pydantic input validation, resources and prompts, `mcp.json` /
`claude_desktop_config.json` client configs, error handling, tests, publishing
commands → [🧩 Quick Code Examples](./reference/quick-code-examples.md).

Load it when you want a skeleton to start from. The language guides above remain the
reference of record for patterns and quality checklists.
